
"""
scaler
"""

__all__ = """
    scaler0
    scaler1
    clock  I0  I00  upd2  trd  I000
    scaler2_I000_counts
    scaler2_I000_cps
    """.split()

from ..session_logs import logger
logger.info(__file__)

from apstools.devices import use_EPICS_scaler_channels
from ophyd import Component, EpicsSignal, EpicsScaler, EpicsSignalRO
from ophyd.scaler import ScalerCH


class myScalerCH(ScalerCH):
    display_rate = Component(EpicsSignal, ".RATE")


scaler0 = myScalerCH('9idcLAX:vsc:c0', name='scaler0')
scaler1 = myScalerCH('9idcLAX:vsc:c1', name='scaler1')     # used by softGlue for SAXS transmission
# scaler2 = ScalerCH('9idcLAX:vsc:c2', name='scaler2')     # used by upstream feedback
scaler2_I000_counts = EpicsSignalRO("9idcLAX:vsc:c2.S2", name="scaler2_I000_counts")
scaler2_I000_cps = EpicsSignalRO("9idcLAX:vsc:c2_cts1.B", name="scaler2_I000_counts")


for s in (scaler0, scaler1):
    use_EPICS_scaler_channels(s)

I0_SIGNAL = scaler0.channels.chan02
I00_SIGNAL = scaler0.channels.chan03
UPD_SIGNAL = scaler0.channels.chan04
TRD_SIGNAL = scaler0.channels.chan05

clock = scaler0.channels.chan01.s
I0 = scaler0.channels.chan02.s
I00 = scaler0.channels.chan03.s
upd2 = scaler0.channels.chan04.s
trd = scaler0.channels.chan05.s
I000 = scaler0.channels.chan06.s

for item in (clock, I0, I00, upd2, trd, I000):
    item._ophyd_labels_ = set(["channel", "counter",])

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

"""
REFERENCE

usaxs@usaxscontrol ~/.../startup/spec $ caget 9idcLAX:vsc:c{0,1,2}.NM{1,2,3,4,5,6,7,8}
9idcLAX:vsc:c0.NM1             seconds
9idcLAX:vsc:c0.NM2             I0_USAXS
9idcLAX:vsc:c0.NM3             I00_USAXS
9idcLAX:vsc:c0.NM4             PD_USAXS
9idcLAX:vsc:c0.NM5             TR diode
9idcLAX:vsc:c0.NM6             I000
9idcLAX:vsc:c0.NM7             
9idcLAX:vsc:c0.NM8             
9idcLAX:vsc:c1.NM1             10MHz_ref
9idcLAX:vsc:c1.NM2             I0
9idcLAX:vsc:c1.NM3             TR diode
9idcLAX:vsc:c1.NM4             
9idcLAX:vsc:c1.NM5             
9idcLAX:vsc:c1.NM6             
9idcLAX:vsc:c1.NM7             
9idcLAX:vsc:c1.NM8             
9idcLAX:vsc:c2.NM1             time
9idcLAX:vsc:c2.NM2             I000
9idcLAX:vsc:c2.NM3             
9idcLAX:vsc:c2.NM4             
9idcLAX:vsc:c2.NM5             
9idcLAX:vsc:c2.NM6             
9idcLAX:vsc:c2.NM7             
9idcLAX:vsc:c2.NM8             
"""
