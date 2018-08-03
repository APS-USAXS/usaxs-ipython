print(__file__)

"""
signals

from: https://subversion.xray.aps.anl.gov/spec/beamlines/USAXS/trunk/macros/local/usaxs_commands.mac
"""


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
    collection_in_progress = Component(EpicsSignal, "dataColInProgress")
    
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


class Parameters_USAXS(Device):
    """internal values shared with EPICS"""
    AY0 = Component(EpicsSignal,                      "9idcLAX:USAXS:AY0")
    DY0 = Component(EpicsSignal,                      "9idcLAX:USAXS:DY0")
    ASRP0 = Component(EpicsSignal,                    "9idcLAX:USAXS:ASRP0")
    SAD = Component(EpicsSignal,                      "9idcLAX:USAXS:SAD")
    SDD = Component(EpicsSignal,                      "9idcLAX:USAXS:SDD")
    center = Component(GeneralUsaxsParametersCenters, "9idcLAX:USAXS:")
    ccd = Component(GeneralUsaxsParametersCCD,        "9idcLAX:USAXS:CCD_")
    diode = Component(GeneralUsaxsParametersDiode,    "9idcLAX:USAXS:")
    img_filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS:Img_")
    finish = Component(EpicsSignal,                   "9idcLAX:USAXS:Finish")
    motor_prescaler_wait = Component(EpicsSignal,     "9idcLAX:USAXS:Prescaler_Wait")
    num_points = Component(EpicsSignal,               "9idcLAX:USAXS:NumPoints")
    sample_y_step = Component(EpicsSignal,            "9idcLAX:USAXS:Sample_Y_Step")
    scan_filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS:Scan_")
    start_offset = Component(EpicsSignal,             "9idcLAX:USAXS:StartOffset")
    uaterm = Component(EpicsSignal,                   "9idcLAX:USAXS:UATerm")
    usaxs_minstep = Component(EpicsSignal,            "9idcLAX:USAXS:MinStep")
    usaxs_time = Component(EpicsSignal,               "9idcLAX:USAXS:CountTime")
    is2DUSAXSscan = Component(EpicsSignal,            "9idcLAX:USAXS:is2DUSAXSscan")

    
    def UPDRange(self):
        return upd_controls.auto.lurange.value  # TODO: check return value is int


class Parameters_SBUSAXS(Device):
    pass


class Parameters_SAXS(Device):
    z_in = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_z_in")
    z_out = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_z_out")
    z_lim_offset = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_z_limit_offset")

    y_in = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_y_in")
    y_out = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_y_out")
    y_lim_offset = Component(EpicsSignal, "9idcLAX:USAXS_Pin:Pin_y_limit_offset")

    ax_in = Component(EpicsSignal, "9idcLAX:USAXS_Pin:ax_in")
    ax_out = Component(EpicsSignal, "9idcLAX:USAXS_Pin:ax_out")
    ax_lim_offset = Component(EpicsSignal, "9idcLAX:USAXS_Pin:ax_limit_offset")

    dx_in = Component(EpicsSignal, "9idcLAX:USAXS:Diode_dx")
    dx_out = Component(EpicsSignal, "9idcLAX:USAXS_Pin:dx_out")
    dx_lim_offset = Component(EpicsSignal, "9idcLAX:USAXS_Pin:dx_limit_offset")

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
    exposure_time = Component(EpicsSignal, "9idcLAX:USAXS_Pin:AcquireTime")      # FIXME: redundant!
	
    # this is Io value from gates scalar in LAX for Nexus file
    I0 = Component(EpicsSignal, "9idcLAX:USAXS_Pin:I0")
    
    transmission = Component(Parameters_transmission)

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


class Parameters_WAXS(Device):
    x_in = Component(EpicsSignal, "9idcLAX:USAXS_Pin:waxs_x_in")
    x_out = Component(EpicsSignal, "9idcLAX:USAXS_Pin:waxs_x_out")
    x_limit_offset = Component(EpicsSignal, "9idcLAX:USAXS_Pin:waxs_x_limit_offset")
    filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS_WAXS:Exp_")
    base_dir = Component(EpicsSignal, "9idcLAX:USAXS_WAXS:directory")
    num_images = Component(EpicsSignal, "9idcLAX:USAXS_WAXS:NumImages")
    acquire_time = Component(EpicsSignal, "9idcLAX:USAXS_WAXS:AcquireTime")
    exposure_time = Component(EpicsSignal, "9idcLAX:USAXS_WAXS:AcquireTime")      # FIXME: redundant!


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

    filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS_Img:Img_")
    filter_transmission = Component(EpicsSignal, "9idcLAX:USAXS_Img:Img_FilterTransmission")


class Parameters_OutOfBeam(Device):
    pass


class GeneralParameters(Device):
    """
    cache of parameters to share with/from EPICS
    """
    USAXS = Component(GeneralUsaxsParameters)
    SBUSAXS = Component(Parameters_SBUSAXS)
    SAXS = Component(Parameters_SAXS)
    WAXS = Component(Parameters_WAXS)
    Radiography = Component(Parameters_Radiography)
    Imaging = Component(Parameters_Imaging)
    OutOfBeam = Component(Parameters_OutOfBeam)
    
    # consider refactoring
    FlyScan = Component(FlyScanParameters)
    preUSAXStune = Component(PreUsaxsTuneParameters)


MAX_EPICS_STRINGOUT_LENGTH = 40

APS = APS_devices.ApsMachineParametersDevice(name="APS")
aps_current = APS.current

mono_energy = EpicsSignal('9ida:BraggERdbkAO', name='mono_energy', write_pv="9ida:BraggEAO")
und_us_energy = EpicsSignal('ID09us:Energy', name='und_us_energy', write_pv="ID09us:EnergySet")
und_ds_energy = EpicsSignal('ID09ds:Energy', name='und_ds_energy', write_pv="ID09ds:EnergySet")

mono_feedback = DCM_Feedback("9idcLAX:fbe:omega", name="mono_feedback")
mono_temperature = EpicsSignal("9ida:DP41:s1:temp", name="mono_temperature")
cryo_level = EpicsSignal("9idCRYO:MainLevel:val", name="cryo_level")


userCalcs_lax = APS_devices.userCalcsDevice("9idcLAX:", name="userCalcs_lax")

usaxs_q_calc = APS_synApps_ophyd.swaitRecord("9idcLAX:USAXS:Q", name="usaxs_q_calc")
usaxs_q = usaxs_q_calc.val

# TODO: should these signals go into "terms" somewhere?
mr_val_center = EpicsSignal("9idcLAX:USAXS:MRcenter", name="mr_val_center")
msr_val_center = EpicsSignal("9idcLAX:USAXS:MSRcenter", name="msr_val_center")
ar_val_center = EpicsSignal("9idcLAX:USAXS:ARcenter", name="ar_val_center")
asr_val_center = EpicsSignal("9idcLAX:USAXS:ASRcenter", name="asr_val_center")


user_data = UserDataDevice(name="user_data")

email_notices = EmailNotifications()
email_notices.add_addresses(
    "ilavsky@aps.anl.gov",
    "kuzmenko@aps.anl.gov",
    "mfrith@anl.gov",
)

# TODO: should these two signals go into "terms" somewhere?
PauseBeforeNextScan = EpicsSignal("9idcLAX:USAXS:PauseBeforeNextScan", name="PauseBeforeNextScan")
StopBeforeNextScan = EpicsSignal("9idcLAX:USAXS:StopBeforeNextScan", name="StopBeforeNextScan")

# NOTE: ALL referenced PVs **MUST** exist or get() operations will fail!
terms = GeneralParameters(name="terms")

# terms.summary() to see all the fields
# terms.read() to read all the fields from EPICS
