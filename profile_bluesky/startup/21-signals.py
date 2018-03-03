print(__file__)

"""other signals"""

aps_current = EpicsSignalRO("S:SRcurrentAI", name="aps_current")

userCalcs_lax = userCalcsDevice("9idcLAX:", name="userCalcs_lax")

usaxs_q_calc = swaitRecord("9idcLAX:USAXS:Q", name="usaxs_q_calc")

mr_val_center = EpicsSignal("9idcLAX:USAXS:MRcenter", name="mr_val_center")
msr_val_center = EpicsSignal("9idcLAX:USAXS:MSRcenter", name="msr_val_center")
ar_val_center = EpicsSignal("9idcLAX:USAXS:ARcenter", name="ar_val_center")
asr_val_center = EpicsSignal("9idcLAX:USAXS:ASRcenter", name="asr_val_center")
