print(__file__)

"""
USAXS Fly Scan setup
"""

logger = logging.getLogger(os.path.split(__file__)[-1])


"""
sfs = SaveFlyScan("/tmp/sfs.h5", config_file="usaxs_support/saveFlyData.xml")
sfs.preliminaryWriteFile()
sfs.saveFile()
"""

FALLBACK_DIR = "/share1/USAXS_data"


class UsaxsFlyScanDevice(Device):
    busy = Component(EpicsSignal, '9idcLAX:USAXSfly:Start', string=True, put_complete=True)
    scan_time = Component(EpicsSignal, "9idcLAX:USAXS:FS_ScanTime")
    num_points = Component(EpicsSignal, "9idcLAX:USAXS:FS_NumberOfPoints")
    flying = Component(Signal, value=False)
    timeout_s = 120

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t0 = None
        self.update_time = None
        self.update_interval_s = 5
        self.ar0 = None
        self.ay0 = None
        self.dy0 = None
        self.saveFlyData = None
        self.saveFlyData_config = "usaxs_support/saveFlyData.xml"
        self.saveFlyData_HDF5_dir ="/tmp"
        self.fallback_dir = FALLBACK_DIR
        self.saveFlyData_HDF5_file ="sfs.h5"
        self._output_HDF5_file_ = None

    def plan(self, md={}):
        """
        run the USAXS fly scan
        """
        bluesky_runengine_running = RE.state != "idle"

        def _report_(t):
            elapsed = struck.elapsed_real_time.get()
            channel = None
            if elapsed is not None:
                channel = struck.current_channel.get()
                if elapsed > t:     # looking at previous fly scan
                    elapsed = 0
                    channel = 0
                terms.FlyScan.elapsed_time.put(elapsed)  # for our GUI display

            values = [f"{t:.2f}",]
            values.append(f"{a_stage.r.position:.7f}")
            values.append(f"{a_stage.y.position:.5f}")
            values.append(f"{d_stage.y.position:.5f}")
            missing = "-missing-"
            if channel is None:
                values.append(missing)
            else:
                values.append(f"{channel}")
            if elapsed is None:
                values.append(missing)
            else:
                values.append(f"{elapsed:.2f}")
            return "  ".join([f"{s:11}" for s in values])

        @APS_plans.run_in_thread
        def progress_reporting():
            logger.debug("progress_reporting has arrived")
            t = time.time()
            timeout = t + self.scan_time.value + self.timeout_s # extra padded time
            startup = t + self.update_interval_s/2
            while t < startup and not  self.flying.value:    # wait for flyscan to start
                time.sleep(0.01)
            labels = ("flying, s", "ar, deg", "ay, mm", "dy, mm", "channel", "elapsed, s")
            print("  ".join([f"{s:11}" for s in labels]))
            while t < timeout and self.flying.value:
                if t > self.update_time:
                    self.update_time = t + self.update_interval_s
                    msg = _report_(t - self.t0)
                    print(msg)
                    logger.debug(msg)
                time.sleep(0.01)
                t = time.time()
            msg = _report_(time.time() - self.t0)
            print(msg)
            logger.debug(msg)
            user_data.set_state_blocking(msg.split()[0])
            if t > timeout:
                logger.error(f"{time.time()-self.t0}s - progress_reporting timeout!!")
            else:
                logger.debug(f"{time.time()-self.t0}s - progress_reporting is done")

        @APS_plans.run_in_thread
        def prepare_HDF5_file():
            fname = os.path.abspath(self.saveFlyData_HDF5_dir)
            if not os.path.exists(fname):
                msg = f"Must save fly scan data to an existing directory.  Gave {fname}"
                fname = os.path.abspath(self.fallback_dir)
                msg += f"  Using fallback directory {self.fallback_dir}"
                logger.error(msg)

            s = self.saveFlyData_HDF5_file
            _s_ = os.path.join(fname, s)      # for testing here
            if os.path.exists(_s_):
                msg = f"File {_s_} exists.  Will not overwrite."
                s = datetime.datetime.isoformat(datetime.datetime.now(), sep="_").split(".")[0]
                s = s.replace(":", "").replace("-", "")
                s = "flyscan_" + s + ".h5"
                _s_ = os.path.join(fname, s)
                msg += f"  Using fallback file name {_s_}"
                logger.error(msg)
            fname = os.path.join(fname, s)

            print(f"HDF5 config: {self.saveFlyData_config}")
            print(f"HDF5 output: {fname}")
            self._output_HDF5_file_ = fname
            user_data.set_state_blocking("FlyScanning: " + os.path.split(fname)[-1])

            self.saveFlyData = SaveFlyScan(
                fname,
                config_file=self.saveFlyData_config)
            self.saveFlyData.preliminaryWriteFile()

        @APS_plans.run_in_thread
        def finish_HDF5_file():
            if self.saveFlyData is None:
                raise RuntimeError("Must first call prepare_HDF5_file()")
            self.saveFlyData.saveFile()

            print(f"HDF5 output complete: {self._output_HDF5_file_}")
            self.saveFlyData = None

        ######################################################################
        # plan starts here
        global specwriter

        # remember our starting conditions
        self.ar0 = a_stage.r.position
        self.ay0 = a_stage.y.position
        self.dy0 = d_stage.y.position

        _md = OrderedDict()
        _md.update(md or {})
        _md["hdf5_file"] = self.saveFlyData_HDF5_file
        _md["hdf5_path"] = self.saveFlyData_HDF5_dir
        
        yield from bps.open_run(md=_md)
        specwriter._cmt("start", "start USAXS Fly scan")
        yield from bps.mv(
            upd_controls.auto.mode, AutorangeSettings.auto_background,
        )

        self.t0 = time.time()
        self.update_time = self.t0 + self.update_interval_s
        yield from bps.abs_set(self.flying, False)

        if bluesky_runengine_running:
            prepare_HDF5_file()      # prepare HDF5 file to save fly scan data (background thread)
        # path = os.path.abspath(self.saveFlyData_HDF5_dir)
        specwriter._cmt("start", f"HDF5 configuration file: {self.saveFlyData_config}")

        g = uuid.uuid4()
        yield from bps.abs_set(self.busy, BusyStatus.busy, group=g) # waits until done
        if bluesky_runengine_running:
            progress_reporting()
        yield from bps.abs_set(self.flying, True)

        yield from bps.wait(group=g)
        yield from bps.abs_set(self.flying, False)
        elapsed = time.time() - self.t0
        specwriter._cmt("stop", f"fly scan completed in {elapsed} s")

        if bluesky_runengine_running:
            msg = f"writing fly scan HDF5 file: {self._output_HDF5_file_}"
            print(msg)
            logger.debug(msg)
            try:
                yield from user_data.set_state_plan("writing fly scan HDF5 file")
            except Exception as exc:
                # do not fail the scan just because of updating program state
                emsg = f"Error: {msg} - {exc}"
                logger.debug(emsg)
                print(emsg)
            finish_HDF5_file()    # finish saving data to HDF5 file (background thread)
            specwriter._cmt("stop", f"finished {msg}")
            print(f"finished {msg}")

        yield from bps.mv(
            a_stage.r.user_setpoint, self.ar0,
            a_stage.y.user_setpoint, self.ay0,
            d_stage.y.user_setpoint, self.dy0,
            upd_controls.auto.mode,  AutorangeSettings.auto_background,
            ti_filter_shutter, "close",
            )

        # add an event with our MCA data in the "mca" stream
        yield from addDeviceDataAsStream([struck.mca1, struck.mca2, struck.mca3], "mca")

        logger.debug("after return", time.time() - self.t0)
        yield from user_data.set_state_plan("fly scan finished")
        yield from bps.close_run()


usaxs_flyscan = UsaxsFlyScanDevice(name="usaxs_flyscan")
# production locations
usaxs_flyscan.saveFlyData_config = "/share1/AreaDetectorConfig/FlyScan_config/saveFlyData.xml"
# Flyscan() will override these and set them in the way the isntrument prefers.
usaxs_flyscan.saveFlyData_HDF5_dir ="/share1/USAXS_data/test"   # developer
usaxs_flyscan.saveFlyData_HDF5_file ="sfs.h5"

# RE(usaxs_flyscan.plan())
