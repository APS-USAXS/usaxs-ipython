print(__file__)

from ophyd import Component, Device, DeviceStatus
from ophyd import EpicsMotor, EpicsScaler
from ophyd import EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV
from ophyd import PVPositioner, PVPositionerPC
from APS_BlueSky_tools.devices import userCalcsDevice


# Set up custom or complex devices


class MotorDialValues(Device):
	value = Component(EpicsSignalRO, ".DRBV")
	setpoint = Component(EpicsSignal, ".DVAL")


class MyEpicsMotorWithDial(EpicsMotor):
	"""
	add motor record's dial coordinates to EpicsMotor
	
	USAGE::
	
		m1 = MyEpicsMotorWithDial('xxx:m1', name='m1')
	
	"""
	dial = Component(MotorDialValues, "")


class SampleStageDevice(Device):
	"""USAXS sample stage"""
	x = Component(EpicsMotor, '9idcLAX:m58:c2:m1')
	y = Component(EpicsMotor, '9idcLAX:m58:c2:m2')


class UsaxsSlitDevice(Device):
	"""USAXS slit just before the sample"""
	v0 = Component(EpicsMotor, '9idcLAX:m58:c2:m5')
	h0 = Component(EpicsMotor, '9idcLAX:m58:c2:m6')
	v_size = Component(EpicsMotor, '9idcLAX:m58:c2:m7')
	h_size = Component(EpicsMotor, '9idcLAX:m58:c2:m8')
