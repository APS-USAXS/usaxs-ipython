print(__file__)
from ophyd import (PVPositioner, EpicsMotor, EpicsSignal, EpicsSignalRO,
                   PVPositionerPC, Device)
from ophyd import Component as Cpt

c0m1 = EpicsMotor('9idcLAX:m58:c0:m1', name='c0m1')
#svc = EpicsMotor('9idcLAX:m58:c2:m5', name='svc')
#shc = EpicsMotor('9idcLAX:m58:c2:m6', name='shc')
#sva = EpicsMotor('9idcLAX:m58:c2:m7', name='sva')
#sha = EpicsMotor('9idcLAX:m58:c2:m8', name='sha')

class SomeSlit(Device):
    vc = Cpt(EpicsMotor, 'm5')
    hc = Cpt(EpicsMotor, 'm6')
    va = Cpt(EpicsMotor, 'm7')
    ha = Cpt(EpicsMotor, 'm8')

slit = SomeSlit('9idcLAX:m58:c2:', name='slit')


class UsaxsSampleStage(Device):
    x = Cpt(EpicsMotor, 'm1')
    y = Cpt(EpicsMotor, 'm2')

sample_stage = UsaxsSampleStage('9idcLAX:m58:c2:', name='sample_stage')

#usaxs@usaxscontrol .../profile_usaxs/startup $ caget 9idcLAX:m58:c{0,1,2}:m{1,2,3,4,5,6,7,8}.DESC
#9idcLAX:m58:c0:m1.DESC         unused
#9idcLAX:m58:c0:m2.DESC         mx
#9idcLAX:m58:c0:m3.DESC         my
#9idcLAX:m58:c0:m4.DESC         WAXS_X
#9idcLAX:m58:c0:m5.DESC         ax
#9idcLAX:m58:c0:m6.DESC         Gslit & I0 Y
#9idcLAX:m58:c0:m7.DESC         az
#9idcLAX:m58:c0:m8.DESC         unused
#9idcLAX:m58:c1:m1.DESC         msx
#9idcLAX:m58:c1:m2.DESC         msy
#9idcLAX:m58:c1:m3.DESC         ART-100
#9idcLAX:m58:c1:m4.DESC         asy
#9idcLAX:m58:c1:m5.DESC         Gslit & I0 X
#9idcLAX:m58:c1:m6.DESC         USAXS tcam
#9idcLAX:m58:c1:m7.DESC         USAXS CAM Y
#9idcLAX:m58:c1:m8.DESC         Camera Focus
#9idcLAX:m58:c2:m1.DESC         sx
#9idcLAX:m58:c2:m2.DESC         sy
#9idcLAX:m58:c2:m3.DESC         dx
#9idcLAX:m58:c2:m4.DESC         unused_olddy
#9idcLAX:m58:c2:m5.DESC         Slit vert cent
#9idcLAX:m58:c2:m6.DESC         Slit hor center
#9idcLAX:m58:c2:m7.DESC         Slit vert aperture
#9idcLAX:m58:c2:m8.DESC         Slit hor aperture
