print(__file__)

from ophyd import (EpicsScaler, EpicsSignal, EpicsSignalRO,
                   Device, DeviceStatus)
from ophyd import Component as Cpt

import time

aps_current = EpicsSignalRO("S:SRcurrentAI", name="aps_current")

## Beam Monitor Counts
#bs_bm2 = EpicsSignalRO('BL14B:Det:BM2', name='bs_bm2')
noisy = EpicsSignalRO('9idcLAX:userCalc1', name='noisy')
scaler0 = EpicsScaler('9idcLAX:vsc:c0', name='scaler0')
scaler1 = EpicsScaler('9idcLAX:vsc:c1', name='scaler1')
scaler2 = EpicsScaler('9idcLAX:vsc:c2', name='scaler2')
