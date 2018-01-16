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
