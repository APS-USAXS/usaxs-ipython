print(__file__)

"""other signals"""

aps_current = EpicsSignalRO("S:SRcurrentAI", name="aps_current")

FE_shutter = MyApsPssShutter("9ida:rShtrA", name="FE_shutter")
mono_shutter = MyApsPssShutter("9ida:rShtrB", name="mono_shutter")
usaxs_shutter = InOutShutter("9idb:BioEnc2B3", name="usaxs_shutter")
ccd_shutter = InOutShutter("9idcRIO:Galil2Bo0_CMD", name="ccd_shutter")

mono_energy = EpicsSignal('9ida:BraggERdbkAO', name='mono_energy', write_pv="9ida:BraggEAO")
und_us_energy = EpicsSignal('ID09us:Energy', name='und_us_energy', write_pv="ID09us:EnergySet")
und_ds_energy = EpicsSignal('ID09ds:Energy', name='und_ds_energy', write_pv="ID09ds:EnergySet")


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
    sepc_scan = Component(EpicsSignal, "USAXS:specScan")
    FS_order_number = Component(EpicsSignal, "USAXS:FS_OrderNumber")
    user_dir = Component(EpicsSignal, "USAXS:userDir")
    time_stamp = Component(EpicsSignal, "USAXS:timeStamp")
    state = Component(EpicsSignal, "USAXS:state")

user_data = UserDataDevice("9idcLAX:", name="user_data")

mono_temperature = EpicsSignal("9ida:DP41:s1:temp", name="mono_temperature")
cryo_level = EpicsSignal("9idCRYO:MainLevel:val", name="cryo_level")


class APS_Machine_Parameters_Device(Device):
    machine_status = Component(EpicsSignalRO, "S:DesiredMode")
    operating_mode = Component(EpicsSignalRO, "S:ActualMode")
    current = Component(EpicsSignalRO, "S:SRcurrentAI")
    shutter_permit = Component(EpicsSignalRO, "ACIS:ShutterPermit")


APS_machine_parameters = APS_Machine_Parameters_Device(name="APS_operator_messages")


class APS_Operator_Messages_Device(Device):
    operator = Component(EpicsSignalRO, "OPS:message1")
    on_call = Component(EpicsSignalRO, "OPS:message2")
    message3 = Component(EpicsSignalRO, "OPS:message3")
    message4 = Component(EpicsSignalRO, "OPS:message4")
    message5 = Component(EpicsSignalRO, "OPS:message5")
    message6 = Component(EpicsSignalRO, "OPS:message6")
    message7 = Component(EpicsSignalRO, "OPS:message7")
    message8 = Component(EpicsSignalRO, "OPS:message8")


APS_operator_messages = APS_Operator_Messages_Device(name="APS_operator_messages")
