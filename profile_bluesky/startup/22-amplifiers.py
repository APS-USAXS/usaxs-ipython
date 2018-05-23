print(__file__)

"""
detectors, amplifiers, and related support

========  =================  ====================  ===================  ===========
detector  scaler             amplifier             sequence             Femto model
========  =================  ====================  ===================  ===========
UPD       9idcLAX:vsc:c0.S4  9idcLAX:fem01:seq01:  9idcLAX:pd01:seq01:  DLPCA200
UPD       9idcLAX:vsc:c0.S4  9idcLAX:fem09:seq02:  9idcLAX:pd01:seq02:  DDPCA300
I0        9idcLAX:vsc:c0.S2  9idcRIO:fem02:seq01:  9idcLAX:pd02:seq01:
I00       9idcLAX:vsc:c0.S3  9idcRIO:fem03:seq01:  9idcLAX:pd03:seq01:
I000      9idcLAX:vsc:c0.S6  9idcRIO:fem04:seq01:  None
TRD       9idcLAX:vsc:c0.S5  9idcRIO:fem05:seq01:  9idcLAX:pd05:seq01:
========  =================  ====================  ===================  ===========

A PV (``9idcLAX:femto:model``) tells which UPD amplifier and sequence 
programs we're using now.  This PV is read-only since it is set when 
IOC boots, based on a soft link that configures the IOC.  The soft 
link may be changed using the ``use200pd``  or  ``use300pd`` script.

We only need to get this once, get it via one-time call with PyEpics
and then use it with inline dictionaries use_EPICS_scaler_channels(scaler0)to pick the right PVs.
"""


from ophyd.device import DynamicDeviceComponent
from ophyd.device import FormattedComponent


class CurrentAmplifierDevice(Device):
    gain = Component(EpicsSignalRO, "gain")


class FemtoAmplifierDevice(CurrentAmplifierDevice):
    gainindex = Component(EpicsSignal, "gainidx")
    description = Component(EpicsSignal, "femtodesc")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._gain_info_known = False
        self.num_gains = 0
        self.acceptable_gain_values = ()
        
    def __init_gains__(self, enum_strs):
        """
        learn range (gain) values from EPICS database
        
        provide a list of acceptable gain values for later use
        """
        acceptable = [s for s in enum_strs if s != 'UNDEF']
        num_gains = len(acceptable)
        # assume labels are ALWAYS formatted: "{float} V/A"
        acceptable += [float(s.split()[0]) for s in acceptable]
        acceptable += range(num_gains)
        self.num_gains = num_gains
        self.acceptable_range_values = acceptable
        self._gain_info_known = True

    def setGain(self, target):
        """
        set the gain on the amplifier
        
        Since the gain values are available from EPICS, 
        we use that to provide a method that can set the 
        gain by any of these values:
        
        * gain text value (from EPICS)
        * integer index number
        * desired gain floating-point value
        
        Assumptions:
        
        * gain label (from EPICS) is ALWAYS: "{float} V/A"
        * float mantissa is always one digit
        """
        if not self._gain_info_known:
            self.__init_gains__(self.gainindex.enum_strs)
        if target in self.acceptable_gain_values:
            if isinstance(target, (int, float)) and target > self.num_gains:
                # gain value specified, rewrite as str
                # assume mantissa is only 1 digit
                target = ("%.0e V/A" % target).replace("+", "").replace("e0", "e")
            self.gainindex.put(target)
        else:
            msg = "could not set gain to {}, ".format(target)
            msg += "must be one of these: {}".format(self.acceptable_gain_values)
            raise ValueError(msg)


class DiodeGainDevice(Device):
    _default_configuration_attrs = ()
    _default_read_attrs = ('gain', 'background', 'background_error')

    gain = FormattedComponent(EpicsSignal, '{self.prefix}gain{self._ch_num}')
    background = FormattedComponent(EpicsSignal, '{self.prefix}bkg{self._ch_num}')
    background_error = FormattedComponent(EpicsSignal, '{self.prefix}bkgErr{self._ch_num}')

    def __init__(self, prefix, ch_num=None, **kwargs):
        assert ch_num is not None, "Must provide `ch_num=` keyword argument."
        self._ch_num = ch_num
        super().__init__(prefix, **kwargs)


def _gains_subgroup_(cls, nm, suffix, gains, **kwargs):
    defn = OrderedDict()
    for i in gains:
        key = '{}{}'.format(nm, i)
        defn[key] = (cls, '', dict(ch_num=i))

    return defn


class AmplifierAutoDevice(CurrentAmplifierDevice):
    """
    Ophyd support for amplifier sequence program
    """
    reqrange = Component(EpicsSignal, "reqrange")
    mode = Component(EpicsSignal, "mode")
    selected = Component(EpicsSignal, "selected")
    gainU = Component(EpicsSignal, "gainU")
    gainD = Component(EpicsSignal, "gainD")
    ranges = DynamicDeviceComponent(
        _gains_subgroup_(
            DiodeGainDevice, 'range', 'suffix', range(5)))
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

        self._gain_info_known = False
        self.num_gains = 0
        self.acceptable_gain_values = ()

    def __init_gains__(self, enum_strs):
        """
        learn range (gain) values from EPICS database
        
        provide a list of acceptable gain values for later use
        """
        acceptable = list(enum_strs)
        num_gains = len(acceptable)
        # assume labels are ALWAYS formatted: "{float} V/A"
        acceptable += [float(s.split()[0]) for s in acceptable]
        acceptable += range(num_gains)
        self.num_gains = num_gains
        self.acceptable_gain_values = acceptable
        self._gain_info_known = True

    def setGain(self, target):
        """
        set the gain on the autorange controls
        
        Since the gain values are available from EPICS, 
        we use that to provide a method that can set the 
        gain by any of these values:
        
        * gain text value (from EPICS)
        * integer index number
        * desired gain floating-point value
        
        Assumptions:
        
        * gain label (from EPICS) is ALWAYS: "{float} V/A gain"
        * float mantissa is always one digit
        """
        if not self._gain_info_known:
            self.__init_gains__(self.reqrange.enum_strs)
        if target in self.acceptable_gain_values:
            if isinstance(target, (int, float)) and target > self.num_gains:
                # gain value specified, rewrite as str
                # assume mantissa is only 1 digit
                target = ("%.0e V/A gain" % target).replace("+", "").replace("e0", "e")
            if isinstance(target, str) and str(target) in self.reqrange.enum_strs:
                # must set reqrange by index number, rewrite as int
                target = self.reqrange.enum_strs.index(target)
            self.reqrange.put(target)
        else:
            msg = "could not set gain to {}, ".format(target)
            msg += "must be one of these: {}".format(self.acceptable_gain_values)
            raise ValueError(msg)

    def measure_dark_currents(self, scaler, numReadings=8):     # TODO: part of #16
        """
        """
        pass

    def autoscale(self, scaler):                                # TODO: #16
        """
        """
        pass

    @property
    def isUpdating(self):
        v = self.mode.value in (1, AutorangeSettings.auto_background)
        if v:
            v = self.updating.value in (1, "Updating")
        return v


class DetectorAmplifierAutorangeDevice(Device):
    scaler = FormattedComponent(EpicsSignal, '{self.scaler_channel_pv}')
    femto = FormattedComponent(FemtoAmplifierDevice, '{self.amplifier_pv}')
    auto = FormattedComponent(AmplifierAutoDevice, '{self.autorange_pv}')
    
    def __init__(self, autorange_pv, scaler_channel_pv, amplifier_pv, **kwargs):
        self.autorange_pv = autorange_pv
        self.scaler_channel_pv = scaler_channel_pv
        self.amplifier_pv = amplifier_pv
        super().__init__("", **kwargs)


# ------------

_amplifier_id_upd = epics.caget("9idcLAX:femto:model", as_string=True)

upd_struct = DetectorAmplifierAutorangeDevice(
    dict(
            DLPCA200 = "9idcLAX:pd01:seq01:",
            DDPCA300 = "9idcLAX:pd01:seq02:",
        )[_amplifier_id_upd],
    "9idcLAX:vsc:c0.S4",
    dict(
            DLPCA200 = "9idcLAX:fem01:seq01:",
            DDPCA300 = "9idcLAX:fem09:seq02:",
        )[_amplifier_id_upd],
    name="upd_struct",
)

trd_struct = DetectorAmplifierAutorangeDevice(
    "9idcLAX:pd05:seq01:",
    "9idcLAX:vsc:c0.S5",
    "9idcRIO:fem05:seq01:",
    name="trd_struct",
)

I0_struct = DetectorAmplifierAutorangeDevice(
    "9idcLAX:pd02:seq01:",
    "9idcLAX:vsc:c0.S2",
    "9idcRIO:fem02:seq01:",
    name="I0_struct",
)

I00_struct = DetectorAmplifierAutorangeDevice(
    "9idcLAX:pd03:seq01:",
    "9idcLAX:vsc:c0.S3",
    "9idcRIO:fem03:seq01:",
    name="I00_struct",
)

# no autorange controls here
I000_femto = FemtoAmplifierDevice("9idcRIO:fem04:seq01:", name="I000_femto")
