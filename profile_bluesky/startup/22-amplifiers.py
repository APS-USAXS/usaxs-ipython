print(__file__)

"""amplifiers"""

from ophyd.device import DynamicDeviceComponent
from ophyd.device import FormattedComponent


class CurrentAmplifierDevice(Device):
    gain = Component(EpicsSignalRO, "gain")


class FemtoAmplifierDevice(CurrentAmplifierDevice):
    gainindex = Component(EpicsSignal, "gainidx")
    description = Component(EpicsSignal, "femtodesc")


class DiodeRangeDevice(Device):
    _default_configuration_attrs = ('gain', 'background', 'background_error')
    _default_read_attrs = ('gain', 'background', 'background_error')

    gain = FormattedComponent(EpicsSignal, '{self.prefix}gain{self._ch_num}')
    background = FormattedComponent(EpicsSignal, '{self.prefix}bkg{self._ch_num}')
    background_error = FormattedComponent(EpicsSignal, '{self.prefix}bkgErr{self._ch_num}')

    def __init__(self, prefix, ch_num, **kwargs):
        self._ch_num = ch_num

        super().__init__(prefix, **kwargs)


class DiodeControlsDevice(Device):
    reqrange = Component(EpicsSignal, "reqrange")
    mode = Component(EpicsSignal, "mode")
    selected = Component(EpicsSignal, "selected")
    gainU = Component(EpicsSignal, "gainU")
    gainD = Component(EpicsSignal, "gainD")
    range0 = Component(DiodeRangeDevice, '', ch_num=0)
    range1 = Component(DiodeRangeDevice, '', ch_num=1)
    range2 = Component(DiodeRangeDevice, '', ch_num=2)
    range3 = Component(DiodeRangeDevice, '', ch_num=3)
    range4 = Component(DiodeRangeDevice, '', ch_num=4)
    counts_per_volt = Component(EpicsSignal, "vfc")
    gain = Component(EpicsSignal, "gain")
    status = Component(EpicsSignalRO, "updating")
    lurange = Component(EpicsSignalRO, "lurange")
    lucounts = Component(EpicsSignalRO, "lucounts")
    lurate = Component(EpicsSignalRO, "lurate")
    lucurrent = Component(EpicsSignalRO, "lucurrent")
    


I_femto = FemtoAmplifierDevice('9idcUSX:fem01:seq01:', name='I_femto')
I0_femto = FemtoAmplifierDevice('9idcUSX:fem02:seq01:', name='I0_femto')
I00_femto = FemtoAmplifierDevice('9idcUSX:fem03:seq01:', name='I00_femto')
I000_femto = FemtoAmplifierDevice('9idcUSX:fem04:seq01:', name='I000_femto')

femto200_controls = DiodeControlsDevice("9idcUSX:pd01:seq01:", name="femto200_controls")
femto300_controls = DiodeControlsDevice("9idcUSX:pd01:seq02:", name="femto300_controls")
