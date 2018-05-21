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
    _default_configuration_attrs = ()
    _default_read_attrs = ('gain', 'background', 'background_error')

    gain = FormattedComponent(EpicsSignal, '{self.prefix}gain{self._ch_num}')
    background = FormattedComponent(EpicsSignal, '{self.prefix}bkg{self._ch_num}')
    background_error = FormattedComponent(EpicsSignal, '{self.prefix}bkgErr{self._ch_num}')

    def __init__(self, prefix, ch_num=None, **kwargs):
        assert ch_num is not None, "Must provide `ch_num=` keyword argument."
        self._ch_num = ch_num
        super().__init__(prefix, **kwargs)


class AutorangeSettings(class):
    """values allowed for ``DiodeControlsDevice.reqrange``"""
    automatic = "automatic"
    auto_background = "auto+background"
    manual = "manual"


class DiodeControlsDevice(CurrentAmplifierDevice):
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
    status = Component(EpicsSignalRO, "updating")
    lurange = Component(EpicsSignalRO, "lurange")
    lucounts = Component(EpicsSignalRO, "lucounts")
    lurate = Component(EpicsSignalRO, "lurate")
    lucurrent = Component(EpicsSignalRO, "lucurrent")

    def __init__(self, prefix, **kwargs):
        self.scaler = None
        super().__init__(prefix, **kwargs)
    
    def measure_dark_currents(self, numReadings=8):     # TODO: part of #16
        """
        """
        assert self.scaler is not None, "Must define the `scaler`."
        pass
    
    def autoscale(self):                                # TODO: #16
        """
        """
        assert self.scaler is not None, "Must define the `scaler`."
        pass
    
    def isUpdating(self):
        return self.mode.value in (1, "updating")


class UPD_FemtoAmplifierDevice(FemtoAmplifierDevice):
    
    def _decode_gain_target(self, target):
        gain_list = (4, 6, 8, 10, 12)
        assert target in gain_list, "`target` must be one of these values: {}".format(gain_list)
        return gain_list(target)

    def set_gain_plan(self, target):
        """
        set gain on USAXS photodiode amplifier during a BlueSky plan
        
        PARAMETERS
    
        target : int
            one of (4, 6, 8, 10, 12)
            corresponding, respectively, to gains of (1e4, 1e6, 1e8, 1e10, 1e12)
        
        Only use low noise gains; those are the only ones which actually work
        """
        yield from bps.abs_set(self.reqrange, self._decode_gain_target(target))

    def set_gain_cmd(self, target):
        """
        set gain on USAXS photodiode amplifier directly, do not use during a BlueSky plan
        
        PARAMETERS
    
        target : int
            one of (4, 6, 8, 10, 12)
            corresponding, respectively, to gains of (1e4, 1e6, 1e8, 1e10, 1e12)
        
        Only use low noise gains; those are the only ones which actually work
        """
        self.reqrange.set(self._decode_gain_target(target))


I_femto = UPD_FemtoAmplifierDevice('9idcUSX:fem01:seq01:', name='I_femto')
I0_femto = FemtoAmplifierDevice('9idcUSX:fem02:seq01:', name='I0_femto')
I00_femto = FemtoAmplifierDevice('9idcUSX:fem03:seq01:', name='I00_femto')
I000_femto = FemtoAmplifierDevice('9idcUSX:fem04:seq01:', name='I000_femto')

femto200_controls = DiodeControlsDevice("9idcUSX:pd01:seq01:", name="femto200_controls")
femto300_controls = DiodeControlsDevice("9idcUSX:pd01:seq02:", name="femto300_controls")
