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


class AutorangeSettings(object):
    """values allowed for ``AmplifierSequenceControlsDevice.reqrange``"""
    automatic = "automatic"
    auto_background = "auto+background"
    manual = "manual"


class AmplifierSequenceControlsDevice(CurrentAmplifierDevice):
    """
    Ophyd support for amplifier sequence program
    
    TODO: resolve this question
    Since the sequence program knows (from st.cmd) to which
    amplifier and scaler it is using (and this configuration
    is not available in any EPICS PVs), must we need 
    coordinate that here as well?
    """
    reqrange = Component(EpicsSignal, "reqrange")
    mode = Component(EpicsSignal, "mode")
    selected = Component(EpicsSignal, "selected")
    gainU = Component(EpicsSignal, "gainU")
    gainD = Component(EpicsSignal, "gainD")
    # number of ranges dependent on amplifier, must be easily defined
    # TODO: use DynamicDeviceComponent and supply range dict in constructor
    # ranges = DynamicDeviceComponent(...)
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
    updating = Component(EpicsSignalRO, "updating")

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
    
    @property
    def isUpdating(self):
        v = self.mode.value in (1, AutorangeSettings.auto_background)
        if v:
            v = self.updating.value in (1, "Updating")
        return v
    
    def _decode_gain_target(self, target):
        """
        returns gain setting from requested converts ``target`` value
        
        Should override in subclass to customize for different 
        amplifiers.  These are for USAXS photodiode.
        
        PARAMETERS
    
        target : int
            one of (4, 6, 8, 10, 12)
            corresponding, respectively, to gains of (1e4, 1e6, 1e8, 1e10, 1e12)

        
        EXAMPLE CONTENT::

            gain_list = (4, 6, 8, 10, 12)
            err_msg = "supplied value ({}) not one of these: {}".format(
                target, gain_list)
            assert target in gain_list, err_msg
            return gain_list.index(target)

        """
        raise NotImplementedError("Must define in subclass")

    def set_gain_plan(self, target):
        """
        set gain on amplifier during a BlueSky plan

        Only use low noise gains; those are the only ones which actually work
        """
        yield from bps.abs_set(self.mode, AutorangeSettings.manual)
        yield from bps.abs_set(self.reqrange, self._decode_gain_target(target))

    def set_gain_cmd(self, target):
        """
        set gain on amplifier directly, do not use during a BlueSky plan

        Only use low noise gains; those are the only ones which actually work
        """
        self.mode.put(AutorangeSettings.manual)
        self.reqrange.put(self._decode_gain_target(target))


class UPD_AmplifierSequenceControlsDevice(AmplifierSequenceControlsDevice):

    def _decode_gain_target(self, target):
        """
        converts ``target`` value to gain (index) value for USAXS photodiode
        
        PARAMETERS
    
        target : int
            one of (4, 6, 8, 10, 12)
            corresponding, respectively, to gains of (1e4, 1e6, 1e8, 1e10, 1e12)

        """
        gain_list = (4, 6, 8, 10, 12)
        err_msg = "`target` must be one of these values: {}".format(gain_list)
        assert target in gain_list, err_msg
        return gain_list.index(target)


class TRD_AmplifierSequenceControlsDevice(AmplifierSequenceControlsDevice):

    def _decode_gain_target(self, target):
        gain_list = (5, 6, 7, 8, 9, 10)
        err_msg = "`target` must be one of these values: {}".format(gain_list)
        assert target in gain_list, err_msg
        if target < 10:
            fmt = "1e{} low noise"
        else:
            fmt = "1e{} high speed"
        return fmt.format(target)


# use one or the other of these:
#UPD_AMPLIFIER_ID = "DLPC200"
UPD_AMPLIFIER_ID = "DLPCA300"

UPD_femto  = FemtoAmplifierDevice('9idcUSX:fem01:seq01:', name='upd_femto')
I0_femto   = FemtoAmplifierDevice('9idcUSX:fem02:seq01:', name='I0_femto')
I00_femto  = FemtoAmplifierDevice('9idcUSX:fem03:seq01:', name='I00_femto')
I000_femto = FemtoAmplifierDevice('9idcUSX:fem04:seq01:', name='I000_femto')
trd_femto  = FemtoAmplifierDevice('9idcUSX:fem05:seq01:', name='trd_femto')

UPD_seq = UPD_AmplifierSequenceControlsDevice(
    dict(
        DLPC200  = "9idcUSX:pd01:seq01:",
        DLPCA300 = "9idcUSX:pd01:seq02:",
    )[UPD_AMPLIFIER_ID],
    name="UPD_seq")
I0_seq  = AmplifierSequenceControlsDevice("9idcUSX:pd02:seq01:", name="I0_seq")
I00_seq = AmplifierSequenceControlsDevice("9idcUSX:pd03:seq01:", name="I00_seq")
TRD_seq = TRD_AmplifierSequenceControlsDevice("9idcUSX:pd05:seq01:", name="TRD_seq")
