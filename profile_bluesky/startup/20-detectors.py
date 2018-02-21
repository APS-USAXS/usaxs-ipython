print(__file__)

"""various detectors and other signals"""

aps_current = EpicsSignalRO("S:SRcurrentAI", name="aps_current")

userCalcs_lax = userCalcsDevice("9idcLAX:", name="userCalcs_lax")

scaler0 = EpicsScaler('9idcLAX:vsc:c0', name='scaler0')
scaler1 = EpicsScaler('9idcLAX:vsc:c1', name='scaler1')     # ? used
scaler2 = EpicsScaler('9idcLAX:vsc:c2', name='scaler2')     # ? used

"""
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


scaler0 = ScalerCH('9idcLAX:vsc:c0', name='scaler0')
# chan01 : sec (seconds)
# chan02 : I0 (I0)
# chan03 : I00 (I00)
# chan04 : upd2 (USAXS_PD)
# chan05 : trd (TR_diode)
# chan06 : I000 (I000)
scaler0.channels.read_attrs = ['chan01', 'chan02', 'chan03', 'chan04', 'chan05', 'chan06']
