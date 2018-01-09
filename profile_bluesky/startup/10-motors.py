print(__file__)
from ophyd import (PVPositioner, EpicsMotor, EpicsSignal, EpicsSignalRO,
                   PVPositionerPC, Device)
from ophyd import Component as Cpt

class MotorDialValues(Device):
	value = Cpt(EpicsSignalRO, ".DRBV")
	setpoint = Cpt(EpicsSignal, ".DVAL")

class MyEpicsMotorWithDial(EpicsMotor):
	dial = Cpt(MotorDialValues, "")

# m1 = MyEpicsMotorWithDial('xxx:m1', name='m1')

# note: see 40-devices.py for stages and slits
#sx = EpicsMotor('9idcLAX:m58:c2:m1', name='sx')
#sy = EpicsMotor('9idcLAX:m58:c2:m2', name='sy')
#dx = EpicsMotor('9idcLAX:m58:c2:m3', name='dx')
#unused_olddy = EpicsMotor('9idcLAX:m58:c2:m4', name='unused_olddy')

#usaxs_slit_v0 = EpicsMotor('9idcLAX:m58:c2:m5', name='usaxs_slit_v0')
#usaxs_slit_h0 = EpicsMotor('9idcLAX:m58:c2:m6', name='usaxs_slit_h0')
#usaxs_slit_v_size = EpicsMotor('9idcLAX:m58:c2:m7', name='usaxs_slit_v_size')
#usaxs_slit_h_size = EpicsMotor('9idcLAX:m58:c2:m8', name='usaxs_slit_h_size')
