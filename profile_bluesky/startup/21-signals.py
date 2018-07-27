print(__file__)

"""other signals"""

APS = ApsMachineParametersDevice(name="APS")
aps_current = APS.current

mono_energy = EpicsSignal('9ida:BraggERdbkAO', name='mono_energy', write_pv="9ida:BraggEAO")
und_us_energy = EpicsSignal('ID09us:Energy', name='und_us_energy', write_pv="ID09us:EnergySet")
und_ds_energy = EpicsSignal('ID09ds:Energy', name='und_ds_energy', write_pv="ID09ds:EnergySet")

mono_feedback = DCM_Feedback("9idcLAX:fbe:omega", name="mono_feedback")
mono_temperature = EpicsSignal("9ida:DP41:s1:temp", name="mono_temperature")
cryo_level = EpicsSignal("9idCRYO:MainLevel:val", name="cryo_level")


userCalcs_lax = userCalcsDevice("9idcLAX:", name="userCalcs_lax")

usaxs_q_calc = swaitRecord("9idcLAX:USAXS:Q", name="usaxs_q_calc")
usaxs_q = usaxs_q_calc.val

mr_val_center = EpicsSignal("9idcLAX:USAXS:MRcenter", name="mr_val_center")
msr_val_center = EpicsSignal("9idcLAX:USAXS:MSRcenter", name="msr_val_center")
ar_val_center = EpicsSignal("9idcLAX:USAXS:ARcenter", name="ar_val_center")
asr_val_center = EpicsSignal("9idcLAX:USAXS:ASRcenter", name="asr_val_center")


class UserDataDevice(Device):
    run_cycle = Component(EpicsSignal, "RunCycle")
    user_name = Component(EpicsSignal, "UserName")
    GUP_number = Component(EpicsSignal, "GUPNumber")
    sample_title = Component(EpicsSignal, "USAXS:sampleTitle")
    spec_file = Component(EpicsSignal, "USAXS:specFile")
    spec_scan = Component(EpicsSignal, "USAXS:specScan")
    FS_order_number = Component(EpicsSignal, "USAXS:FS_OrderNumber")
    user_dir = Component(EpicsSignal, "USAXS:userDir")
    time_stamp = Component(EpicsSignal, "USAXS:timeStamp")
    state = Component(EpicsSignal, "USAXS:state")

user_data = UserDataDevice("9idcLAX:", name="user_data")
