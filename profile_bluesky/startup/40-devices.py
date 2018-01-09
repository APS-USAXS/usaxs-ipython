print(__file__)


# Set up default complex devices

# FIXME: how to get the PVs to the inner parts?
# TODO: How to build this up from previously-configured motors?

#class SlitAxis(Device):
#	lo = Cpt(EpicsMotor, '')
#	hi = Cpt(EpicsMotor, '')

#class XY_Slit(Device):
#	h = Cpt(SlitAxis, '')
#	v = Cpt(SlitAxis, '')

#slit1 = XY_Slit()


class SampleStageDevice(Device):
	"""USAXS sample stage"""
	x = Cpt(EpicsMotor, '9idcLAX:m58:c2:m1')
	y = Cpt(EpicsMotor, '9idcLAX:m58:c2:m2')

sample_stage = SampleStageDevice('', name='sample_stage')


class UsaxsSlitDevice(Device):
	"""USAXS slit just before the sample"""
	v0 = Cpt(EpicsMotor, '9idcLAX:m58:c2:m5')
	h0 = Cpt(EpicsMotor, '9idcLAX:m58:c2:m6')
	v_size = Cpt(EpicsMotor, '9idcLAX:m58:c2:m7')
	h_size = Cpt(EpicsMotor, '9idcLAX:m58:c2:m8')

usaxs_slit = UsaxsSlitDevice('', name='usaxs_slit')
