print(__file__)

"""Set up custom or complex devices"""


# simple enumeration used by DCM_Feedback()
MONO_FEEDBACK_OFF, MONO_FEEDBACK_ON = range(2)


class DCM_Feedback(Device):
    """
    monochromator EPID-record-based feedback program: fb_epid
    """
    control = Component(EpicsSignal, "")
    on = Component(EpicsSignal, ":on")
    drvh = Component(EpicsSignal, ".DRVH")
    drvl = Component(EpicsSignal, ".DRVL")
    oval = Component(EpicsSignal, ".OVAL")

    @property
    def is_on(self):
        return self.on.value == 1

    def check_position(self):
        diff_hi = self.drvh.value - self.oval.value
        diff_lo = self.oval.value - self.drvl.value
        if min(diff_hi, diff_lo) < 0.2:
            if email_notices.notify_on_feedback:
                subject = "USAXS Feedback problem"
                message = "Feedback is very close to its limits."
                # TODO: must call in thread
                #email_notices.send(subject, message)
                print("!"*15)
                print(subject, message)
                print("!"*15)


class ApsPssShutterWithStatus(APS_devices.ApsPssShutterWithStatus):
    """
    temporary override to fix https://github.com/BCDA-APS/apstools/issues/113
    """

    def wait_for_state(self, target, timeout=10, poll_s=0.01):
        """
        wait for the PSS state to reach a desired target
        
        PARAMETERS
        
        target : [str]
            list of strings containing acceptable values
        
        timeout : non-negative number
            maximum amount of time (seconds) to wait for PSS state to reach target
        
        poll_s : non-negative number
            Time to wait (seconds) in first polling cycle.
            After first poll, this will be increased by ``_poll_factor_``
            up to a maximum time of ``_poll_s_max_``.
        """
        if timeout is not None:
            expiration = time.time() + max(timeout, 0)  # ensure non-negative timeout
        else:
            expiration = None
        
        # ensure the poll delay is reasonable
        if poll_s > self._poll_s_max_:
            poll_s = self._poll_s_max_
        elif poll_s < self._poll_s_min_:
            poll_s = self._poll_s_min_

        # t0 = time.time()
        while self.pss_state.get() not in target:
            time.sleep(poll_s)
            # elapsed = time.time() - t0
            # print(f"waiting {elapsed}s : value={self.pss_state.value}")
            if poll_s < self._poll_s_max_:
                poll_s *= self._poll_factor_   # progressively longer
            if expiration is not None and time.time() > expiration:
                msg = f"Timeout ({timeout} s) waiting for shutter state"
                msg += f" to reach a value in {target}"
                raise TimeoutError(msg)


class xxSimulatedApsPssShutterWithStatus(APS_devices.SimulatedApsPssShutterWithStatus):
    """
    temporary override to fix https://github.com/BCDA-APS/apstools/issues/98
    """
    @property
    def state(self):
        """is shutter "open", "close", or "unknown"?"""
        if self.pss_state.value in self.pss_state_open_values:
            result = self.valid_open_values[0]
        elif self.pss_state.value in self.pss_state_closed_values:
            result = self.valid_close_values[0]
        else:
            result = self.unknown_state
        return result


class UsaxsMotor(EpicsMotorLimitsMixin, EpicsMotor): pass

class UsaxsMotorTunable(AxisTunerMixin, UsaxsMotor): pass


# TODO: override for https://github.com/BCDA-APS/apstools/issues/124
MAX_EPICS_STRINGOUT_LENGTH = 40
def trim_string_for_EPICS(msg):
    """string must not be too long for EPICS PV"""
    if len(msg) > MAX_EPICS_STRINGOUT_LENGTH:
        msg = msg[:MAX_EPICS_STRINGOUT_LENGTH-1]
    return msg


class UserDataDevice(Device):
    GUP_number = Component(EpicsSignal,         "9idcLAX:GUPNumber")
    macro_file_time = Component(EpicsSignal,    "9idcLAX:USAXS:macroFileTime")
    run_cycle = Component(EpicsSignal,          "9idcLAX:RunCycle")
    sample_thickness = Component(EpicsSignal,   "9idcLAX:USAXS:SampleThickness")
    saxs_sample_thickness = Component(EpicsSignal,   "9idcLAX:sampleThickness")         # TODO: temporary
    sample_title = Component(EpicsSignal,       "9idcLAX:USAXS:sampleTitle", string=True)
    scanning = Component(EpicsSignal,           "9idcLAX:USAXS:scanning")
    scan_macro = Component(EpicsSignal,         "9idcLAX:USAXS:scanMacro")
    spec_file = Component(EpicsSignal,          "9idcLAX:USAXS:specFile", string=True)
    spec_scan = Component(EpicsSignal,          "9idcLAX:USAXS:specScan", string=True)
    state = Component(EpicsSignal,              "9idcLAX:USAXS:state", string=True)
    time_stamp = Component(EpicsSignal,         "9idcLAX:USAXS:timeStamp")
    user_dir = Component(EpicsSignal,           "9idcLAX:USAXS:userDir", string=True)
    user_name = Component(EpicsSignal,          "9idcLAX:UserName", string=True)

    # for GUI to know if user is collecting data: 0="On", 1="Off"
    collection_in_progress = Component(EpicsSignal, "9idcLAX:dataColInProgress")

    def set_state_plan(self, msg):
        """plan: tell EPICS about what we are doing"""
        # TODO: msg = APS_utils.trim_string_for_EPICS(msg)
        msg = trim_string_for_EPICS(msg)
        yield from bps.mv(self.state, msg)

    def set_state_blocking(self, msg):
        """ophyd: tell EPICS about what we are doing"""
        # TODO: msg = APS_utils.trim_string_for_EPICS(msg)
        msg = trim_string_for_EPICS(msg)
        self.state.put(msg)


class PSS_Parameters(Device):
    c_shutter_closed_chain_A = Component(EpicsSignalRO, "PA:09ID:SCS_PS_CLSD_LS", string=True)
    c_shutter_closed_chain_B = Component(EpicsSignalRO, "PB:09ID:SCS_PS_CLSD_LS", string=True)

    @property
    def c_station_enabled(self):
        """look at the switches: are we allowed to operate?"""
        enabled = self.c_shutter_closed_chain_A.value == "OFF" or \
           self.c_shutter_closed_chain_A.value == "OFF"
        return enabled



# these are the global settings PVs for various parts of the instrument
# NOTE: avoid using any PV more than once!


class FlyScanParameters(Device):
    """FlyScan values"""
    number_points = Component(EpicsSignal, "9idcLAX:USAXS:FS_NumberOfPoints")
    scan_time = Component(EpicsSignal, "9idcLAX:USAXS:FS_ScanTime")
    use_flyscan = Component(EpicsSignal, "9idcLAX:USAXS:UseFlyscan")
    asrp_calc_SCAN = Component(EpicsSignal, "9idcLAX:userStringCalc2.SCAN")
    order_number = Component(EpicsSignal, "9idcLAX:USAXS:FS_OrderNumber")
    elapsed_time = Component(EpicsSignal, "9idcLAX:USAXS:FS_ElapsedTime")

    setpoint_up = Component(Signal, value=6000)     # decrease range
    setpoint_down = Component(Signal, value=850000)    # increase range


class PreUsaxsTuneParameters(Device):
    """preUSAXStune handling"""
    num_scans_last_tune = Component(EpicsSignal, "9idcLAX:USAXS:NumScansFromLastTune")
    epoch_last_tune = Component(EpicsSignal, "9idcLAX:USAXS:EPOCHTimeOfLastTune")
    req_num_scans_between_tune = Component(EpicsSignal, "9idcLAX:USAXS:ReqNumScansBetweenTune")
    req_time_between_tune = Component(EpicsSignal, "9idcLAX:USAXS:ReqTimeBetweenTune")
    run_tune_on_qdo = Component(EpicsSignal, "9idcLAX:USAXS:RunPreUSAXStuneOnQdo")
    run_tune_next = Component(EpicsSignal, "9idcLAX:USAXS:RunPreUSAXStuneNext")
    
    @property
    def needed(self):
        """
        is a tune needed?
        
        EXAMPLE::
        
            if terms.preUSAXStune.needed:
                yield from tune_usaxs_optics()
                # TODO: and then reset terms as approriate
        
        """
        result = self.run_tune_next.value
        # TODO: next test if not in SAXS or WAXS mode
        result = result or self.num_scans_last_tune.value  > self.req_num_scans_between_tune.value
        time_limit = self.epoch_last_tune.value + self.req_time_between_tune.value
        result = result or time.time() > time_limit
        self.run_tune_next.put(0)
        return result


class GeneralParametersCCD(Device):
    "part of GeneralParameters Device"
    dx = Component(EpicsSignal, "dx")
    dy = Component(EpicsSignal, "dy")


class GeneralUsaxsParametersDiode(Device):
    "part of GeneralParameters Device"
    dx = Component(EpicsSignal, "Diode_dx")
    dy = Component(EpicsSignal, "DY0")


class GeneralUsaxsParametersCenters(Device):
    "part of GeneralParameters Device"
    AR = Component(EpicsSignal,  "ARcenter")
    ASR = Component(EpicsSignal, "ASRcenter")
    MR = Component(EpicsSignal,  "MRcenter")
    MSR = Component(EpicsSignal, "MSRcenter")


class Parameters_Al_Ti_Filters(Device):
    Al = Component(EpicsSignal,  "Al_Filter")
    Ti = Component(EpicsSignal,  "Ti_Filter")


class Parameters_Al_Ti_Filters_Imaging(Device):
    # because there is one in every crowd!
    Al = Component(EpicsSignal,  "Al_Filters")
    Ti = Component(EpicsSignal,  "Ti_Filters")


class Parameters_transmission(Device):
    # measure transmission in USAXS using pin diode
    measure = Component(EpicsSignal, "9idcLAX:USAXS:TR_MeasurePinTrans")

    # Ay to hit pin diode
    ay = Component(EpicsSignal, "9idcLAX:USAXS:TR_AyPosition")
    count_time = Component(EpicsSignal, "9idcLAX:USAXS:TR_MeasurementTime")
    diode_counts = Component(EpicsSignal, "9idcLAX:USAXS:TR_pinCounts")
    diode_gain = Component(EpicsSignal, "9idcLAX:USAXS:TR_pinGain") # I00 amplifier
    I0_counts = Component(EpicsSignal, "9idcLAX:USAXS:TR_I0Counts")
    I0_gain = Component(EpicsSignal, "9idcLAX:USAXS:TR_I0Gain")


class Parameters_USAXS(Device):
    """internal values shared with EPICS"""
    AY0 = Component(EpicsSignal,                      "9idcLAX:USAXS:AY0")
    DY0 = Component(EpicsSignal,                      "9idcLAX:USAXS:DY0")
    ASRP0 = Component(EpicsSignal,                    "9idcLAX:USAXS:ASRcenter")
    SAD = Component(EpicsSignal,                      "9idcLAX:USAXS:SAD")
    SDD = Component(EpicsSignal,                      "9idcLAX:USAXS:SDD")
    ar_val_center = Component(EpicsSignal,            "9idcLAX:USAXS:ARcenter")
    asr_val_center = Component(EpicsSignal,           "9idcLAX:USAXS:ASRcenter")
    center = Component(GeneralUsaxsParametersCenters, "9idcLAX:USAXS:")
    ccd = Component(GeneralParametersCCD,             "9idcLAX:USAXS:CCD_")
    diode = Component(GeneralUsaxsParametersDiode,    "9idcLAX:USAXS:")
    img_filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS:Img_")
    finish = Component(EpicsSignal,                   "9idcLAX:USAXS:Finish")
    is2DUSAXSscan = Component(EpicsSignal,            "9idcLAX:USAXS:is2DUSAXSscan")
    motor_prescaler_wait = Component(EpicsSignal,     "9idcLAX:USAXS:Prescaler_Wait")
    mr_val_center = Component(EpicsSignal,            "9idcLAX:USAXS:MRcenter")
    msr_val_center = Component(EpicsSignal,           "9idcLAX:USAXS:MSRcenter")
    num_points = Component(EpicsSignal,               "9idcLAX:USAXS:NumPoints")
    sample_y_step = Component(EpicsSignal,            "9idcLAX:USAXS:Sample_Y_Step")
    scan_filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS:Scan_")
    start_offset = Component(EpicsSignal,             "9idcLAX:USAXS:StartOffset")
    uaterm = Component(EpicsSignal,                   "9idcLAX:USAXS:UATerm")
    usaxs_minstep = Component(EpicsSignal,            "9idcLAX:USAXS:MinStep")
    usaxs_time = Component(EpicsSignal,               "9idcLAX:USAXS:CountTime")
    useMSstage = Component(Signal,                    value=False)
    useSBUSAXS = Component(Signal,                    value=False)

    retune_needed = Component(Signal, value=False)     # does not *need* an EPICS PV

    # TODO: these are particular to the amplifier
    setpoint_up = Component(Signal, value=4000)     # decrease range
    setpoint_down = Component(Signal, value=650000)    # increase range

    transmission = Component(Parameters_transmission)

    def UPDRange(self):
        return upd_controls.auto.lurange.value  # TODO: check return value is int


class Parameters_SBUSAXS(Device):
    pass


class Parameters_SAXS(Device):
    z_in = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_z_in")
    z_out = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_z_out")
    z_limit_offset = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_z_limit_offset")

    y_in = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_y_in")
    y_out = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_y_out")
    y_limit_offset = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_y_limit_offset")

    ax_in = Component(EpicsSignal, "9idcLAX:SAXS:ax_in")
    ax_out = Component(EpicsSignal, "9idcLAX:SAXS:ax_out")
    ax_limit_offset = Component(EpicsSignal, "9idcLAX:SAXS:ax_limit_offset")

    dx_in = Component(EpicsSignal, "9idcLAX:SAXS:dx_in")
    dx_out = Component(EpicsSignal, "9idcLAX:SAXS:dx_out")
    dx_limit_offset = Component(EpicsSignal, "9idcLAX:SAXS:dx_limit_offset")

    usaxs_h_size = Component(EpicsSignal, "9idcLAX:SAXS:USAXS_hslit_ap")
    usaxs_v_size = Component(EpicsSignal, "9idcLAX:SAXS:USAXS_vslit_ap")
    v_size = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_vslit_ap")
    h_size = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_hslit_ap")

    usaxs_guard_h_size = Component(EpicsSignal, "9idcLAX:SAXS:USAXS_hgslit_ap")
    usaxs_guard_v_size = Component(EpicsSignal, "9idcLAX:SAXS:USAXS_vgslit_ap")
    guard_v_size = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_vgslit_ap")
    guard_h_size = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_hgslit_ap")

    filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:SAXS:Exp_")

    diode_transmission = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_TrPD")
    I0_transmission = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_TrI0")
    diode_gain = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_TrPDgain")
    I0_gain = Component(EpicsSignal, "9idcLAX:SAXS:SAXS_TrI0gain")

    base_dir = Component(EpicsSignal, "9idcLAX:SAXS:directory", string=True)

    UsaxsSaxsMode = Component(EpicsSignal, "9idcLAX:SAXS:USAXSSAXSMode", put_complete=True)
    num_images = Component(EpicsSignal, "9idcLAX:SAXS:NumImages")
    acquire_time = Component(EpicsSignal, "9idcLAX:SAXS:AcquireTime")
    start_exposure_time = Component(EpicsSignal, "9idcLAX:SAXS:StartExposureTime")
    end_exposure_time = Component(EpicsSignal, "9idcLAX:SAXS:EndExposureTime")

    # this is Io value from gates scalar in LAX for Nexus file
    I0 = Component(EpicsSignal, "9idcLAX:SAXS:I0")


class Parameters_WAXS(Device):
    x_in = Component(EpicsSignal, "9idcLAX:SAXS:WAXS_x_in")
    x_out = Component(EpicsSignal, "9idcLAX:SAXS:WAXS_x_out")
    x_limit_offset = Component(EpicsSignal, "9idcLAX:SAXS:WAXS_x_limit_offset")
    filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS_WAXS:Exp_")
    base_dir = Component(EpicsSignal, "9idcLAX:USAXS_WAXS:directory", string=True)
    num_images = Component(EpicsSignal, "9idcLAX:USAXS_WAXS:NumImages")
    acquire_time = Component(EpicsSignal, "9idcLAX:USAXS_WAXS:AcquireTime")


class Parameters_Radiography(Device):
    pass


class Parameters_Imaging(Device):
    image_key = Component(EpicsSignal, "9idcLAX:USAXS_Img:ImageKey")
    # 0=image, 1=flat field, 2=dark field

    exposure_time = Component(EpicsSignal, "9idcLAX:USAXS_Img:ExposureTime")

    tomo_rotation_angle = Component(EpicsSignal, "9idcLAX:USAXS_Img:Tomo_Rot_Angle")
    I0 = Component(EpicsSignal, "9idcLAX:USAXS_Img:Img_I0_value")
    I0_gain = Component(EpicsSignal, "9idcLAX:USAXS_Img:Img_I0_gain")

    ax_in = Component(EpicsSignal, "9idcLAX:USAXS_Img:ax_in")
    waxs_x_in = Component(EpicsSignal, "9idcLAX:USAXS_Img:waxs_x_in")

    flat_field = Component(EpicsSignal, "9idcLAX:USAXS_Img:FlatFieldImage")
    dark_field = Component(EpicsSignal, "9idcLAX:USAXS_Img:DarkFieldImage")
    title = Component(EpicsSignal, "9idcLAX:USAXS_Img:ExperimentTitle", string=True)

    h_size = Component(EpicsSignal, "9idcLAX:USAXS_Img:ImgHorApperture")
    v_size = Component(EpicsSignal, "9idcLAX:USAXS_Img:ImgVertApperture")
    guard_h_size = Component(EpicsSignal, "9idcLAX:USAXS_Img:ImgGuardHorApperture")
    guard_v_size = Component(EpicsSignal, "9idcLAX:USAXS_Img:ImgGuardVertApperture")

    filters = Component(Parameters_Al_Ti_Filters_Imaging, "9idcLAX:USAXS_Img:Img_")
    filter_transmission = Component(EpicsSignal, "9idcLAX:USAXS_Img:Img_FilterTransmission")


class Parameters_OutOfBeam(Device):
    pass


class GeneralParameters(Device):
    """
    cache of parameters to share with/from EPICS
    """
    USAXS = Component(Parameters_USAXS)
    SBUSAXS = Component(Parameters_SBUSAXS)
    SAXS = Component(Parameters_SAXS)
    WAXS = Component(Parameters_WAXS)
    Radiography = Component(Parameters_Radiography)
    Imaging = Component(Parameters_Imaging)
    OutOfBeam = Component(Parameters_OutOfBeam)

    PauseBeforeNextScan = Component(EpicsSignal, "9idcLAX:USAXS:PauseBeforeNextScan")
    StopBeforeNextScan = Component(EpicsSignal,  "9idcLAX:USAXS:StopBeforeNextScan")

    # consider refactoring
    FlyScan = Component(FlyScanParameters)
    preUSAXStune = Component(PreUsaxsTuneParameters)


class TemperatureController_Base(Device):
    """
    common parts of temperature controller support
    
    EXAMPLE::
    
        class MyLinkam(TemperatureController_Base):
            controller_name = "MyLinkam"
            temperature = Component(EpicsSignalRO, "temp")
            set_point = Component(EpicsSignal, "setLimit", kind="omitted")
        
        controller = MyLinkam("my:linkam:", name="controller")
        RE(controller.wait_until_settled(timeout=10))
    
        controller.record_temperature()
        print(f"{controller.controller_name} controller settled? {controller.settled}")
    
        def rampUp_rampDown():
            '''ramp temperature up, then back down'''
            yield from controller.set_temperature(25, timeout=180)
            controller.report_interval = 10    # change report interval to 10s
            for i in range(10, 0, -1):
                print(f"hold at (self.value:.2f)C, time remaining: {i}s")
                yield from bps.sleep(1)
            yield from controller.set_temperature(0, timeout=180)
        
        RE(test_plan())

    """
    
    controller_name = "TemperatureController_Base"
    temperature = Component(Signal)                 # override in subclass
    set_point = Component(Signal, kind="omitted")   # override in subclass

    controller_name = "Linkam_Base"
    tolerance  = 1          # requirement: |T - target| must be <= this, degree C
    report_interval  = 5    # time between reports during loop, s
    poll_s = 0.02           # time to wait during polling loop, s

    def record_temperature(self):
        """write temperatures as comment"""
        global specwriter
        msg = f"{self.controller_name} Temperature: {self.value:.2f} C"
        specwriter._cmt("event", msg)
        print(msg)

    def set_temperature(self, set_point, wait=True, timeout=None, timeout_fail=False):
        """change controller to new temperature set point"""
        global specwriter

        yield from bps.mv(self.set_point, set_point)

        msg = f"Set {self.controller_name} Temperature to {set_point:.2f} C"
        print(msg)
        specwriter._cmt("event", msg)
        
        if wait:
            yield from self.wait_until_settled(
                timeout=timeout, 
                timeout_fail=timeout_fail)
    
    @property
    def value(self):
        """shortcut to self.temperature.value"""
        return self.temperature.value

    @property
    def settled(self):
        """Is temperature close enough to target?"""
        diff = abs(self.temperature.get() - self.set_point.value)
        return diff <= self.tolerance

    def wait_until_settled(self, timeout=None, timeout_fail=False):
        """
        wait for controller to reach target temperature
        """
        # see: https://stackoverflow.com/questions/2829329/catch-a-threads-exception-in-the-caller-thread-in-python
        t0 = time.time()
        _st = DeviceStatus(self.temperature)
        started = False

        def changing_cb(value, timestamp, **kwargs):
            if started and self.settled:
                _st._finished(success=True)

        token = self.temperature.subscribe(changing_cb)
        started = True
        
        report = 0
        while not _st.done and not self.settled:
            elapsed = time.time() - t0
            if timeout is not None and elapsed > timeout:
                _st._finished(success=self.settled)
                msg = f"Temperature Controller Timeout after {elapsed:.2f}s"
                msg += f", target {self.set_point.value:.2f}C"
                msg += f", now {self.temperature.get():.2f}C"
                # msg += f", status={_st}"
                print(msg)
                if timeout_fail:
                    raise TimeoutError(msg)
                continue
            if elapsed >= report:
                report += self.report_interval
                msg = f"Waiting {elapsed:.1f}s"
                msg += f" to reach {self.set_point.value:.2f}C"
                msg += f", now {self.temperature.get():.2f}C"
                print(msg)
            yield from bps.sleep(self.poll_s)

        if not _st.done and self.settled:
            # just in case self.temperature already at temperature
            _st._finished(success=True)

        self.temperature.unsubscribe(token)
        self.record_temperature()
        elapsed = time.time() - t0
        print(f"Total time: {elapsed:.3f}s, settled:{_st.success}")


class Linkam_CI94(TemperatureController_Base):
    """
    Linkam model CI94 temperature controller
    
    EXAMPLE::
    
        In [1]: linkam_ci94 = Linkam_CI94("9idcLAX:ci94:", name="ci94")

        In [2]: linkam_ci94.settled                                                                                                                                         
        Out[2]: False

        In [3]: linkam_ci94.settled                                                                                                                                         
        Out[3]: True
        
        linkam_ci94.record_temperature()
        yield from (linkam_ci94.set_temperature(50))

    """
    controller_name = "Linkam CI94"
    temperature = Component(EpicsSignalRO, "temp")
    set_point = Component(EpicsSignal, "setLimit", kind="omitted")

    temperature_in = Component(EpicsSignalRO, "tempIn", kind="omitted")
    # DO NOT USE: temperature2_in = Component(EpicsSignalRO, "temp2In", kind="omitted")
    # DO NOT USE: temperature2 = Component(EpicsSignalRO, "temp2")
    pump_speed = Component(EpicsSignalRO, "pumpSpeed", kind="omitted")

    set_rate = Component(EpicsSignal, "setRate", kind="omitted")
    set_speed = Component(EpicsSignal, "setSpeed", kind="omitted")
    end_after_profile = Component(EpicsSignal, "endAfterProfile", kind="omitted")
    end_on_stop = Component(EpicsSignal, "endOnStop", kind="omitted")
    start_control = Component(EpicsSignal, "start", kind="omitted")
    stop_control = Component(EpicsSignal, "stop", kind="omitted")
    hold_control = Component(EpicsSignal, "hold", kind="omitted")
    pump_mode = Component(EpicsSignal, "pumpMode", kind="omitted")

    error_byte = Component(EpicsSignalRO, "errorByte", kind="omitted")
    status = Component(EpicsSignalRO, "status", kind="omitted")
    status_in = Component(EpicsSignalRO, "statusIn", kind="omitted")
    gen_stat = Component(EpicsSignalRO, "genStat", kind="omitted")
    pump_speed_in = Component(EpicsSignalRO, "pumpSpeedIn", kind="omitted")
    dsc_in = Component(EpicsSignalRO, "dscIn", kind="omitted")

    # clear_buffer = Component(EpicsSignal, "clearBuffer", kind="omitted")          # bo
    # scan_dis = Component(EpicsSignal, "scanDis", kind="omitted")                  # bo
    # test = Component(EpicsSignal, "test", kind="omitted")                         # longout
    # d_cmd = Component(EpicsSignalRO, "DCmd", kind="omitted")                      # ai
    # t_cmd = Component(EpicsSignalRO, "TCmd", kind="omitted")                      # ai
    # dsc = Component(EpicsSignalRO, "dsc", kind="omitted")                         # calc


class Linkam_T96(TemperatureController_Base):
    """
    Linkam model T96 temperature controller
    
    EXAMPLE::
    
        linkam_tc1 = Linkam_T96("9idcLINKAM:tc1:", name="linkam_tc1")

    """
    controller_name = "Linkam T96"
    temperature = Component(EpicsSignalRO, "temperature_RBV")  # ai
    set_point = Component(EpicsSignalWithRBV, "rampLimit", kind="omitted")

    vacuum = Component(EpicsSignal, "vacuum", kind="omitted")

    heating = Component(EpicsSignalWithRBV, "heating", kind="omitted")
    lnp_mode = Component(EpicsSignalWithRBV, "lnpMode", kind="omitted")
    lnp_speed = Component(EpicsSignalWithRBV, "lnpSpeed", kind="omitted")
    ramp_rate = Component(EpicsSignalWithRBV, "rampRate", kind="omitted")
    vacuum_limit_readback = Component(EpicsSignalWithRBV, "vacuumLimit", kind="omitted")

    controller_config = Component(EpicsSignalRO, "controllerConfig_RBV", kind="omitted")
    controller_error = Component(EpicsSignalRO, "controllerError_RBV", kind="omitted")
    controller_status = Component(EpicsSignalRO, "controllerStatus_RBV", kind="omitted")
    heater_power = Component(EpicsSignalRO, "heaterPower_RBV", kind="omitted")
    lnp_status = Component(EpicsSignalRO, "lnpStatus_RBV", kind="omitted")
    pressure = Component(EpicsSignalRO, "pressure_RBV", kind="omitted")
    ramp_at_limit = Component(EpicsSignalRO, "rampAtLimit_RBV", kind="omitted")
    stage_config = Component(EpicsSignalRO, "stageConfig_RBV", kind="omitted")
    status_error = Component(EpicsSignalRO, "statusError_RBV", kind="omitted")
    vacuum_at_limit = Component(EpicsSignalRO, "vacuumAtLimit_RBV", kind="omitted")
    vacuum_status = Component(EpicsSignalRO, "vacuumStatus_RBV", kind="omitted")

    def set_temperature(self, set_point, wait=True, timeout=None, timeout_fail=False):
        """change controller to new temperature set point"""
        global specwriter
        
        yield from bps.mv(self.set_point, set_point)
        yield from bps.sleep(0.1)   # settling delay for slow IOC
        yield from bps.mv(self.heating, 1)

        msg = f"Set {self.controller_name} Temperature to {set_point:.2f} C"
        specwriter._cmt("event", msg)
        print(msg)
        
        if wait:
            yield from self.wait_until_settled(
                timeout=timeout, 
                timeout_fail=timeout_fail)
