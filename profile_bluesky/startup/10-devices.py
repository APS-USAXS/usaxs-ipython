print(__file__)

"""Set up custom or complex devices"""


class UsaxsMotor(EpicsMotorLimitsMixin, EpicsMotor): pass

class UsaxsMotorTunable(AxisTunerMixin, UsaxsMotor): pass


# move to apstools.synApps_ophyd.busy
class BusyStatus(str, Enum):
    busy = "Busy"
    done = "Done"


# superceded by: apstools.synApps_ophyd.busy.BusyRecord
class BusyRecord(Device):
    """a busy record sets the fly scan into action"""
    state = Component(EpicsSignal, "")
    output_link = Component(EpicsSignal, ".OUT")
    forward_link = Component(EpicsSignal, ".FLNK")


class MyCalc(Device):
    """swait record simulates a signal"""
    result = Component(EpicsSignal, "")
    calc = Component(EpicsSignal, ".CALC")
    proc = Component(EpicsSignal, ".PROC")


class MyWaveform(Device):
    """waveform records store fly scan data"""
    wave = Component(EpicsSignalRO, "")
    number_elements = Component(EpicsSignalRO, ".NELM")
    number_read = Component(EpicsSignalRO, ".NORD")


# superceded by: APS_devices.EpicsOnOffShutter
#class InOutShutter(Device):
#    """
#    In/Out shutter
#
#    * In/Out shutters have the same bit PV for open and close
#
#    Otherwise, they should have the same interface as other
#    shutters such as the `ApsPssShutter`.
#
#    USAGE:
#
#        shutter = InOutShutter("48bmc:bit12", name="shutter")
#
#    """
#    control_bit = Component(EpicsSignal, "")
#    delay_s = 0
#    open_value = 1
#    close_value = 0
#    valid_open_values = [open_value, "open"]   # lower-case strings ONLY
#    valid_close_values = [close_value, "close"]
#    busy = Component(Signal, value=False)
#
#    def open(self):
#        """request shutter to open, interactive use"""
#        return self.set(self.open_value)
#
#    def close(self):
#        """request shutter to close, interactive use"""
#        return self.set(self.close_value)
#
#    @property
#    def is_opened(self):
#        return self.control_bit.value == self.open_value
#
#    @property
#    def is_closed(self):
#        return self.control_bit.value == self.close_value
#
#    def set(self, value, **kwargs):
#        """request the shutter to open or close, BlueSky plan use"""
#        # ensure numerical additions to lists are now strings
#        def input_filter(v):
#            return str(v).lower()
#        self.valid_open_values = list(map(input_filter, self.valid_open_values))
#        self.valid_close_values = list(map(input_filter, self.valid_close_values))
#
#        if self.busy.value:
#            raise RuntimeError("shutter is operating")
#
#        acceptables = self.valid_open_values + self.valid_close_values
#        if input_filter(value) not in acceptables:
#            msg = "value should be one of " + " | ".join(acceptables)
#            msg += " : received " + str(value)
#            raise ValueError(msg)
#
#        status = DeviceStatus(self)
#
#        def move_shutter():
#            """BLOCKING: no need to yield since this is run inside a thread"""
#            if input_filter(value) in self.valid_open_values:
#                self.control_bit.put(self.open_value)
#            elif input_filter(value) in self.valid_close_values:
#                self.control_bit.put(self.close_value)
#
#        @APS_plans.run_in_thread
#        def run_and_delay():
#            """BLOCKING: no need to yield since this is run inside a thread"""
#            self.busy.put(True)
#            move_shutter()
#            # sleep, since we don't *know* when the shutter has moved
#            time.sleep(self.delay_s)
#            self.busy.put(False)
#            status._finished(success=True)
#
#        run_and_delay()
#        return status


# superceded by APS_devices.DualPf4FilterBox
class DualPf4FilterBox(Device):
    """Dual Xia PF4 filter boxes using support from synApps"""
    fPosA = Component(EpicsSignal, "fPosA", put_complete=True)
    fPosB = Component(EpicsSignal, "fPosB", put_complete=True)
    bankA = Component(EpicsSignalRO, "bankA")
    bankB = Component(EpicsSignalRO, "bankB")
    bitFlagA = Component(EpicsSignalRO, "bitFlagA")
    bitFlagB = Component(EpicsSignalRO, "bitFlagB")
    transmission = Component(EpicsSignalRO, "trans")
    transmission_a = Component(EpicsSignalRO, "transA")
    transmission_b = Component(EpicsSignalRO, "transB")
    inverse_transmission = Component(EpicsSignalRO, "invTrans")
    thickness_Al_mm = Component(EpicsSignalRO, "filterAl")
    thickness_Ti_mm = Component(EpicsSignalRO, "filterTi")
    thickness_glass_mm = Component(EpicsSignalRO, "filterGlass")
    energy_keV_local = Component(EpicsSignal, "E:local")
    energy_keV_mono = Component(EpicsSignal, "displayEnergy")
    mode = Component(EpicsSignal, "useMono", string=True)


# move to APS_devices
class Struck3820(Device):
    """Struck/SIS 3820 Multi-Channel Scaler (as used by USAXS)"""
    start_all = Component(EpicsSignal, "StartAll")
    stop_all = Component(EpicsSignal, "StopAll")
    erase_start = Component(EpicsSignal, "EraseStart")
    erase_all = Component(EpicsSignal, "EraseAll")
    mca1 = Component(EpicsMCARecord, "mca1")
    mca2 = Component(EpicsMCARecord, "mca2")
    mca3 = Component(EpicsMCARecord, "mca3")
    # mca1Name = Component(EpicsSignal, "scaler1.NM1", string=True)
    # mca2Name = Component(EpicsSignal, "scaler1.NM2", string=True)
    # mca3Name = Component(EpicsSignal, "scaler1.NM3", string=True)
    clock_frequency = Component(EpicsSignalRO, "clock_frequency")
    current_channel = Component(EpicsSignalRO, "CurrentChannel")
    channel_max = Component(EpicsSignalRO, "MaxChannels")
    channels_used = Component(EpicsSignal, "NuseAll")
    elapsed_real_time = Component(EpicsSignalRO, "ElapsedReal")
    preset_real_time = Component(EpicsSignal, "PresetReal")
    dwell_time = Component(EpicsSignal, "Dwell")
    prescale = Component(EpicsSignal, "Prescale")
    acquiring = Component(EpicsSignalRO, "Acquiring", string=True)
    acquire_mode = Component(EpicsSignalRO, "AcquireMode", string=True)
    model = Component(EpicsSignalRO, "Model", string=True)
    firmware = Component(EpicsSignalRO, "Firmware")
    channel_advance = Component(EpicsSignal, "ChannelAdvance")
    count_on_start = Component(EpicsSignal, "CountOnStart")
    channel_advance = Component(EpicsSignal, "SoftwareChannelAdvance")
    channel1_source = Component(EpicsSignal, "Channel1Source")
    user_led = Component(EpicsSignal, "UserLED")
    mux_output = Component(EpicsSignal, "MUXOutput")
    input_mode = Component(EpicsSignal, "InputMode")
    output_mode = Component(EpicsSignal, "OutputMode")
    output_polarity = Component(EpicsSignal, "OutputPolarity")
    read_rate = Component(EpicsSignal, "ReadAll.SCAN")
    do_readl_all = Component(EpicsSignal, "DoReadAll")


# move to APS_devices
class KohzuSeqCtl_Monochromator(Device):
    """
    synApps Kohzu double-crystal monochromator sequence control program
    """
    # lambda is reserved word in Python, can't use it
    wavelength = Component(EpicsSignal, "BraggLambdaRdbkAO", write_pv="BraggLambdaAO")
    energy = Component(EpicsSignal, "BraggERdbkAO", write_pv="BraggEAO")
    theta = Component(EpicsSignal, "BraggThetaRdbkAO", write_pv="BraggThetaAO")
    message1 = Component(EpicsSignalRO, "KohzuSeqMsg1SI")
    message2 = Component(EpicsSignalRO, "KohzuSeqMsg2SI")
    operator_acknowledge = Component(EpicsSignal, "KohzuOperAckBO")
    use_set = Component(EpicsSignal, "KohzuUseSetBO")
    mode = Component(EpicsSignal, "KohzuModeBO")
    move_button = Component(EpicsSignal, "KohzuPutBO")
    y_offset = Component(EpicsSignal, "Kohzu_yOffsetAO")

    crystal_mode = Component(EpicsSignal, "KohzuMode2MO")
    crystal_h = Component(EpicsSignal, "BraggHAO")
    crystal_k = Component(EpicsSignal, "BraggKAO")
    crystal_l = Component(EpicsSignal, "BraggLAO")
    crystal_lattice_constant = Component(EpicsSignal, "BraggAAO")
    crystal_mode = Component(EpicsSignal, "Bragg2dSpacingAO")
    crystal_type = Component(EpicsSignal, "BraggTypeMO")


# this makes an enumeration
MONO_FEEDBACK_OFF, MONO_FEEDBACK_ON = range(2)


# move to APS_devices
class DCM_Feedback(Device):
    """
    monochromator feedback program
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


class UserDataDevice(Device):
    GUP_number = Component(EpicsSignal,         "9idcLAX:GUPNumber")
    macro_file_time = Component(EpicsSignal,    "9idcLAX:USAXS:macroFileTime")
    run_cycle = Component(EpicsSignal,          "9idcLAX:RunCycle")
    sample_thickness = Component(EpicsSignal,   "9idcLAX:USAXS:SampleThickness")
    sample_title = Component(EpicsSignal,       "9idcLAX:USAXS:sampleTitle")
    scanning = Component(EpicsSignal,           "9idcLAX:USAXS:scanning")
    scan_macro = Component(EpicsSignal,         "9idcLAX:USAXS:scanMacro")
    spec_file = Component(EpicsSignal,          "9idcLAX:USAXS:specFile")
    spec_scan = Component(EpicsSignal,          "9idcLAX:USAXS:specScan")
    state = Component(EpicsSignal,              "9idcLAX:USAXS:state")
    time_stamp = Component(EpicsSignal,         "9idcLAX:USAXS:timeStamp")
    user_dir = Component(EpicsSignal,           "9idcLAX:USAXS:userDir")
    user_name = Component(EpicsSignal,          "9idcLAX:UserName")

    # for GUI to know if user is collecting data: 0="On", 1="Off"
    collection_in_progress = Component(EpicsSignal, "9idcLAX:dataColInProgress")

    def set_state_plan(self, msg):
        """plan: tell EPICS about what we are doing"""
        yield from bps.mv(self.state, APS_utils.trim_string_for_EPICS(msg))


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
    z_in = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_z_in")
    z_out = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_z_out")
    z_limit_offset = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_z_limit_offset")

    y_in = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_y_in")
    y_out = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_y_out")
    y_limit_offset = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_y_limit_offset")

    ax_in = Component(EpicsSignal, "9idcLAX:USAXS_Pin:ax_in")
    ax_out = Component(EpicsSignal, "9idcLAX:USAXS_Pin:ax_out")
    ax_limit_offset = Component(EpicsSignal, "9idcLAX:USAXS_Pin:ax_limit_offset")

    dx_in = Component(EpicsSignal, "9idcLAX:USAXS_Pin:dx_in")
    dx_out = Component(EpicsSignal, "9idcLAX:USAXS_Pin:dx_out")
    dx_limit_offset = Component(EpicsSignal, "9idcLAX:USAXS_Pin:dx_limit_offset")

    usaxs_h_size = Component(EpicsSignal, "9idcLAX:USAXS_Pin:USAXS_hslit_ap")
    usaxs_v_size = Component(EpicsSignal, "9idcLAX:USAXS_Pin:USAXS_vslit_ap")
    v_size = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_vslit_ap")
    h_size = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_hslit_ap")

    usaxs_guard_h_size = Component(EpicsSignal, "9idcLAX:USAXS_Pin:USAXS_hgslit_ap")
    usaxs_guard_v_size = Component(EpicsSignal, "9idcLAX:USAXS_Pin:USAXS_vgslit_ap")
    guard_v_size = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_vgslit_ap")
    guard_h_size = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_hgslit_ap")

    filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS_Pin:Exp_")

    diode_transmission = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_TrPD")
    I0_transmission = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_TrI0")
    diode_gain = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_TrPDgain")
    I0_gain = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_TrI0gain")

    base_dir = Component(EpicsSignal, "9idcLAX:USAXS_Pin:directory")

    UsaxsSaxsMode = Component(EpicsSignal, "9idcLAX:USAXS_Pin:USAXSSAXSMode", put_complete=True)
    num_images = Component(EpicsSignal, "9idcLAX:USAXS_Pin:NumImages")
    acquire_time = Component(EpicsSignal, "9idcLAX:USAXS_Pin:AcquireTime")
    start_exposure_time = Component(EpicsSignal, "9idcLAX:USAXS_Pin:StartExposureTime")
    end_exposure_time = Component(EpicsSignal, "9idcLAX:USAXS_Pin:EndExposureTime")

    # this is Io value from gates scalar in LAX for Nexus file
    I0 = Component(EpicsSignal, "9idcLAX:USAXS_Pin:I0")


class Parameters_WAXS(Device):
    x_in = Component(EpicsSignal, "9idcLAX:USAXS_Pin:waxs_x_in")
    x_out = Component(EpicsSignal, "9idcLAX:USAXS_Pin:waxs_x_out")
    x_limit_offset = Component(EpicsSignal, "9idcLAX:USAXS_Pin:waxs_x_limit_offset")
    filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS_WAXS:Exp_")
    base_dir = Component(EpicsSignal, "9idcLAX:USAXS_WAXS:directory")
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
    title = Component(EpicsSignal, "9idcLAX:USAXS_Img:ExperimentTitle")

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
