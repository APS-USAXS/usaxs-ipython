print(__file__)

"""Set up custom or complex devices"""


def run_in_thread(func):
    """run ``func`` in thread"""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


def pairwise(iterable):
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return zip(a, a)


class EpicsMotorLimitsMixin(Device):
    """
    add motor record HLM & LLM fields & compatibility get_lim() and set_lim()
    """
    
    soft_limit_lo = Component(EpicsSignal, ".LLM")
    soft_limit_hi = Component(EpicsSignal, ".HLM")
    
    def get_lim(self, flag):
        """
        Returns the user limit of motor
        
        flag > 0: returns high limit
        flag < 0: returns low limit
        flag == 0: returns None
        """
        if flag > 0:
            return self.high_limit
        else:
            return self.low_limit
    
    def set_lim(self, low, high):
        """
        Sets the low and high limits of motor
        
        * Low limit is set to lesser of (low, high)
        * High limit is set to greater of (low, high)
        * No action taken if motor is moving. 
        """
        if not self.moving:
            self.soft_limit_lo.put(min(low, high))
            self.soft_limit_hi.put(max(low, high))


class UsaxsMotor(EpicsMotor, EpicsMotorLimitsMixin): pass


class UsaxsMotorTunable(UsaxsMotor, APS_devices.AxisTunerMixin):
    pass


class MyApsPssShutterWithStatus(ApsPssShutterWithStatus):
    # our shutters use upper case for Open & Close
    open_bit = Component(EpicsSignal, "Open")
    close_bit = Component(EpicsSignal, "Close")


class BusyStatus(str, Enum):
    busy = "Busy"
    done = "Done"


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


class InOutShutter(Device):
    """
    In/Out shutter
    
    * In/Out shutters have the same bit PV for open and close
    
    Otherwise, they should have the same interface as other 
    shutters such as the `ApsPssShutter`.
    
    USAGE:
    
        shutter = InOutShutter("48bmc:bit12", name="shutter")
    
    """
    control_bit = Component(EpicsSignal, "")
    delay_s = 0
    open_value = 1
    close_value = 0
    valid_open_values = [open_value, "open"]   # lower-case strings ONLY
    valid_close_values = [close_value, "close"]
    busy = Component(Signal, value=False)
    
    def open(self):
        """request shutter to open, interactive use"""
        return self.set(self.open_value)
    
    def close(self):
        """request shutter to close, interactive use"""
        return self.set(self.close_value)
    
    @property
    def is_opened(self):
        return self.control_bit.value == self.open_value
    
    @property
    def is_closed(self):
        return self.control_bit.value == self.close_value

    def set(self, value, **kwargs):
        """request the shutter to open or close, BlueSky plan use"""
        # ensure numerical additions to lists are now strings
        def input_filter(v):
            return str(v).lower()
        self.valid_open_values = list(map(input_filter, self.valid_open_values))
        self.valid_close_values = list(map(input_filter, self.valid_close_values))
        
        if self.busy.value:
            raise RuntimeError("shutter is operating")

        acceptables = self.valid_open_values + self.valid_close_values
        if input_filter(value) not in acceptables:
            msg = "value should be one of " + " | ".join(acceptables)
            msg += " : received " + str(value)
            raise ValueError(msg)
        
        status = DeviceStatus(self)
        
        def move_shutter():
            if input_filter(value) in self.valid_open_values:
                self.control_bit.put(self.open_value)     # no need to yield inside a thread
            elif input_filter(value) in self.valid_close_values:
                self.control_bit.put(self.close_value)     # no need to yield inside a thread
        
        @run_in_thread
        def run_and_delay():
            self.busy.put(True)
            move_shutter()
            # sleep, since we don't *know* when the shutter has moved
            time.sleep(self.delay_s)
            self.busy.put(False)
            status._finished(success=True)
        
        run_and_delay()
        return status

    
class DualPf4FilterBox(Device):
    """Dual Xia PF4 filter boxes using support from synApps"""
    fPosA = Component(EpicsSignal, "fPosA")
    fPosB = Component(EpicsSignal, "fPosB")
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


class DCM_Feedback(Device):
    """
    monochromator feedback program
    
    TODO: #49
    Add support for set() so that we can implement "on" & "off" values
    and also apply additional checks when turning feedback on.
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
        diff_hi = self.drvh - self.oval
        diff_lo = self.oval - self.drvl
        if min(diff_hi, diff_lo) < 0.2:
            if email_notices.notify_on_feedback:
                subject = "USAXS Feedback problem"
                message = "Feedback is very close to its limits."
                email_notices.send(subject, message)


class UserDataDevice(Device):
    FS_order_number = Component(EpicsSignal,    "9idcLAX:USAXS:FS_OrderNumber")
    GUP_number = Component(EpicsSignal,         "9idcLAX:GUPNumber")
    macro_file_time = Component(EpicsSignal,    "9idcLAX:USAXS:macroFileTime")
    run_cycle = Component(EpicsSignal,          "9idcLAX:RunCycle")
    sample_thickness = Component(EpicsSignal,   "9idcLAX:USAXS:SampleThickness")
    sample_title = Component(EpicsSignal,       "9idcLAX:USAXS:sampleTitle")
    spec_file = Component(EpicsSignal,          "9idcLAX:USAXS:specFile")
    spec_scan = Component(EpicsSignal,          "9idcLAX:USAXS:specScan")
    state = Component(EpicsSignal,              "9idcLAX:USAXS:state")
    time_stamp = Component(EpicsSignal,         "9idcLAX:USAXS:timeStamp")
    user_dir = Component(EpicsSignal,           "9idcLAX:USAXS:userDir")
    user_name = Component(EpicsSignal,          "9idcLAX:UserName")
    
    # for GUI to know if user is collecting data: 0="On", 1="Off"
    collection_in_progress = Component(EpicsSignal, "9idcLAX:dataColInProgress")
    
    def set_state(self, msg):
        if len(msg) > MAX_EPICS_STRINGOUT_LENGTH:
            msg = msg[:MAX_EPICS_STRINGOUT_LENGTH]
        self.state.put(msg)


# these are the global settings PVs for various parts of the instrument
# NOTE: avoid using any PV more than once!


class FlyScanParameters(Device):
    """FlyScan values"""
    number_points = Component(EpicsSignal, "9idcLAX:USAXS:FS_NumberOfPoints")
    scan_time = Component(EpicsSignal, "9idcLAX:USAXS:FS_ScanTime")
    use_flyscan = Component(EpicsSignal, "9idcLAX:USAXS:UseFlyscan")
    asrp_calc_SCAN = Component(EpicsSignal, "9idcLAX:userStringCalc2.SCAN")
    order_number = Component(EpicsSignal, "9idcLAX:USAXS:FS_OrderNumber")
    
    def enable_ASRP(self):
        if is2DUSAXSscan.value: # TODO: check return value here
            self.asrp_calc_SCAN.put(9)
    
    def disable_ASRP(self):
        self.asrp_calc_SCAN.put(0)
    
    def increment_order_number(self):
        self.order_number.put(self.order_number.value+1)


class PreUsaxsTuneParameters(Device):
    """preUSAXStune handling"""
    num_scans_last_tune = Component(EpicsSignal, "9idcLAX:USAXS:NumScansFromLastTune")
    epoch_last_tune = Component(EpicsSignal, "9idcLAX:USAXS:EPOCHTimeOfLastTune")
    req_num_scans_between_tune = Component(EpicsSignal, "9idcLAX:USAXS:ReqNumScansBetweenTune")
    req_time_between_tune = Component(EpicsSignal, "9idcLAX:USAXS:ReqTimeBetweenTune")
    run_tune_on_qdo = Component(EpicsSignal, "9idcLAX:USAXS:RunPreUSAXStuneOnQdo")
    run_tune_next = Component(EpicsSignal, "9idcLAX:USAXS:RunPreUSAXStuneNext")


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

    def UPDRange(self):
        return upd_controls.auto.lurange.value  # TODO: check return value is int


class Parameters_SBUSAXS(Device):
    pass


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

    dx_in = Component(EpicsSignal, "9idcLAX:USAXS:Diode_dx")
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

    UsaxsSaxsMode = Component(EpicsSignal, "9idcLAX:USAXS_Pin:USAXSSAXSMode")
    num_images = Component(EpicsSignal, "9idcLAX:USAXS_Pin:NumImages")
    acquire_time = Component(EpicsSignal, "9idcLAX:USAXS_Pin:AcquireTime")
	
    # this is Io value from gates scalar in LAX for Nexus file
    I0 = Component(EpicsSignal, "9idcLAX:USAXS_Pin:I0")
    
    transmission = Component(Parameters_transmission)


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


# TODO: #48 send email
# TODO: move all below to APR_BlueSky_Tools project
import subprocess
def unix_cmd(command_list):
    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout, stderr


class EmailNotifications(object):
    """
    send email notifications when requested
    
    use default OS mail utility (so no credentials needed)
    """
    
    def __init__(self):
        self.addresses = []
        self.notify_on_feedback = True
    
    def add_addresses(self, *args):
        for address in args:
            self.addresses.append(address)

    def send(self, subject, message):
        """send ``message`` to all addresses"""
        for address in self.addresses:
            command = [
                "mail",
                message,
                "-s",
                subject,
                address,
            ]
            #command = """echo "{}" | mail -s "{}" {}""".format(
            #    message,
            #    subject,
            #    address
            #)
            unix_cmd(command)
