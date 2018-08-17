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


class BusyStatus(str, Enum):
    busy = "Busy"
    done = "Done"


class UsaxsFlyScanDevice(Device):
    busy = Component(EpicsSignal, '9idcLAX:USAXSfly:Start', string=True, put_complete=True)
    scan_time = Component(EpicsSignal, "9idcLAX:USAXS:FS_ScanTime")
    num_points = Component(EpicsSignal, "9idcLAX:USAXS:FS_NumberOfPoints")
    flying = Component(Signal, value=False)

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
    
    def plan(self):

        def _report_(t):
            msg = "%.02fs - flying " % t
            msg += "  ar = %.7f" % a_stage.r.position
            msg += "  ay = %.5f" % a_stage.y.position
            msg += "  dy = %.5f" % d_stage.y.position
            # msg += "  flying = {}".format(self.flying.value)
            return msg

        @APS_plans.run_in_thread
        def progress_reporting():
            logger.debug("progress_reporting has arrived")
            t = time.time()
            timeout = t + self.scan_time.value + 20 # extra padded time
            startup = t + self.update_interval_s/2
            while t < startup and not  self.flying.value:    # wait for flyscan to start
                time.sleep(0.01)
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
            user_data.set_state("flying: " + msg.split()[0])
            if t > timeout:
                logger.error("{}s - progress_reporting timeout!!".format(time.time()-self.t0))
            else:
                logger.debug("{}s - progress_reporting is done".format(time.time()-self.t0))

        @APS_plans.run_in_thread
        def prepare_HDF5_file():
            fname = os.path.abspath(self.saveFlyData_HDF5_dir)
            if not os.path.exists(fname):
                msg = "Must save fly scan data to an existing directory."
                msg += "  Gave {}".format(fname)
                fname = os.path.abspath(self.fallback_dir)
                msg += "  Using fallback directory {}".format(self.fallback_dir)
                logger.error(msg)

            s = self.saveFlyData_HDF5_file
            _s_ = os.path.join(fname, s)      # for testing here
            if os.path.exists(_s_):
                msg = "File {} exists.  Will not overwrite.".format(_s_)
                s = datetime.datetime.isoformat(datetime.datetime.now(), sep="_").split(".")[0]
                s = s.replace(":", "").replace("-", "")
                s = "flyscan_" + s + ".h5"
                _s_ = os.path.join(fname, s)
                msg += "  Using fallback file name {}".format(_s_)
                logger.error(msg)
            fname = os.path.join(fname, s)

            print("HDF5 config: {}".format(self.saveFlyData_config))
            print("HDF5 output: {}".format(fname))
            self._output_HDF5_file_ = fname
            #user_data.set_state("HDF5 file:" + fname)

            self.saveFlyData = SaveFlyScan(
                fname,
                config_file=self.saveFlyData_config)
            self.saveFlyData.preliminaryWriteFile()

        @APS_plans.run_in_thread
        def finish_HDF5_file():
            if self.saveFlyData is None:
                raise RuntimeError("Must first call prepare_HDF5_file()")
            self.saveFlyData.saveFile()

            print("HDF5 output complete: {}".format(self._output_HDF5_file_))
            self.saveFlyData = None

        self.ar0 = a_stage.r.position
        self.ay0 = a_stage.y.position
        self.dy0 = d_stage.y.position

        self.t0 = time.time()
        self.update_time = self.t0 + self.update_interval_s
        yield from bps.aps_set(self.flying, False)
        
        prepare_HDF5_file()      # prepare HDF5 file to save fly scan data (background thread)

        g = uuid.uuid4()
        yield from bps.abs_set(self.busy, BusyStatus.busy, group=g) # waits until done
        progress_reporting()
        yield from bps.aps_set(self.flying, True)

        yield from bps.wait(group=g)
        yield from bps.aps_set(self.flying, False)
        
        yield from user_data.set_state_plan("writing fly scan HDF5 file")
        finish_HDF5_file()    # finish saving data to HDF5 file (background thread)

        yield from bps.mv(
            a_stage.r.user_setpoint, self.ar0, 
            a_stage.y.user_setpoint, self.ay0, 
            d_stage.y.user_setpoint, self.dy0)
        logger.debug("after return", time.time() - self.t0)
        yield from user_data.set_state_plan("fly scan finished")


# #21 : w-i-p
usaxs_flyscan = UsaxsFlyScanDevice(name="usaxs_flyscan")
# development locations
usaxs_flyscan.saveFlyData_config = "usaxs_support/saveFlyData.xml"
usaxs_flyscan.saveFlyData_HDF5_dir ="/share1/USAXS_data/test"
usaxs_flyscan.saveFlyData_HDF5_file ="sfs.h5"


def fix_faulty():
    a_stage.r.user_setpoint.set(8.7628359)
    a_stage.y.user_setpoint.set(0)
    d_stage.y.user_setpoint.set(13.2833635)


# RE(usaxs_flyscan.plan())
