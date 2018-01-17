print(__file__)

"""various detectors and other signals"""

aps_current = EpicsSignalRO("S:SRcurrentAI", name="aps_current")

userCalcs_lax = userCalcsDevice("9idcLAX:", name="userCalcs_lax")

scaler0 = EpicsScaler('9idcLAX:vsc:c0', name='scaler0')
scaler1 = EpicsScaler('9idcLAX:vsc:c1', name='scaler1')
scaler2 = EpicsScaler('9idcLAX:vsc:c2', name='scaler2')
