print(__file__)

"""amplifiers"""


class CurrentAmplifier(Device):
	gain = Component(EpicsSignalRO, "gain")


class FemtoAmplifier(CurrentAmplifier):
	gainindex = Component(EpicsSignal, "gainidx")
	description = Component(EpicsSignal, "femtodesc")

I0_femto = FemtoAmplifier('9idcUSX:fem02:seq01:', name='I0_femto')
I00_femto = FemtoAmplifier('9idcUSX:fem03:seq01:', name='I00_femto')
I000_femto = FemtoAmplifier('9idcUSX:fem04:seq01:', name='I000_femto')
