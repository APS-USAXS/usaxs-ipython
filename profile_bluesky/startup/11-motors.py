print(__file__)

"""motors, stages, positioners, ..."""


dx = EpicsMotor('9idcLAX:m58:c2:m3', name='dx')
#unused_olddy = EpicsMotor('9idcLAX:m58:c2:m4', name='unused_olddy')


class SampleStageDevice(Device):
	"""USAXS sample stage"""
	x = Component(EpicsMotor, '9idcLAX:m58:c2:m1')
	y = Component(EpicsMotor, '9idcLAX:m58:c2:m2')

sample_stage = SampleStageDevice('', name='sample_stage')


class UsaxsSlitDevice(Device):
	"""USAXS slit just before the sample"""
	v0 = Component(EpicsMotor, '9idcLAX:m58:c2:m5')
	h0 = Component(EpicsMotor, '9idcLAX:m58:c2:m6')
	v_size = Component(EpicsMotor, '9idcLAX:m58:c2:m7')
	h_size = Component(EpicsMotor, '9idcLAX:m58:c2:m8')

usaxs_slit = UsaxsSlitDevice('', name='usaxs_slit')
