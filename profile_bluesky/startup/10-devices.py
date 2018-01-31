print(__file__)

from ophyd import Component, Device, DeviceStatus
from ophyd import EpicsMotor, EpicsScaler
from ophyd import EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV
from ophyd import PVPositioner, PVPositionerPC
from APS_BlueSky_tools.devices import userCalcsDevice


# Set up custom or complex devices


class UsaxsSampleStageDevice(Device):
	"""USAXS sample stage"""
	x = Component(EpicsMotor, '9idcLAX:m58:c2:m1')
	y = Component(EpicsMotor, '9idcLAX:m58:c2:m2')


class UsaxsSlitDevice(Device):
	"""USAXS slit just before the sample"""
	v0 = Component(EpicsMotor, '9idcLAX:m58:c2:m5')
	h0 = Component(EpicsMotor, '9idcLAX:m58:c2:m6')
	v_size = Component(EpicsMotor, '9idcLAX:m58:c2:m7')
	h_size = Component(EpicsMotor, '9idcLAX:m58:c2:m8')
