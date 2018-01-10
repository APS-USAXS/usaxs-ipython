print(__file__)

"""various detectors"""

aps_current = EpicsSignalRO("S:SRcurrentAI", name="aps_current")

## Beam Monitor Counts
#bs_bm2 = EpicsSignalRO('BL14B:Det:BM2', name='bs_bm2')
userCalc1_lax = EpicsSignalRO('9idcLAX:userCalc1', name='userCalc1_lax')
scaler0 = EpicsScaler('9idcLAX:vsc:c0', name='scaler0')
scaler1 = EpicsScaler('9idcLAX:vsc:c1', name='scaler1')
scaler2 = EpicsScaler('9idcLAX:vsc:c2', name='scaler2')
