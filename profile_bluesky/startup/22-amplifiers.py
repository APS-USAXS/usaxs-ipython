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


NUM_AUTORANGE_GAINS = 5		# common to all autorange sequence programs

def _gain_to_str_(gain):    # convenience function
    return ("%.0e" % gain).replace("+", "").replace("e0", "e")


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

        # assume gain labels are formatted "{float} {other_text}"
        s = acceptable[0]
        self.gain_suffix = s[s.find(" "):]
        for i, s in enumerate(acceptable[:num_gains]):
            # verify all gains use same suffix text
            msg = "gainindex[{}] = {}, expected ending '{}'".format(i, s, self.gain_suffix)
            assert s[s.find(" "):] == self.gain_suffix
        
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
                target = _gain_to_str_(target) + self.gain_suffix
            self.gainindex.put(target)
        else:
            msg = "could not set gain to {}, ".format(target)
            msg += "must be one of these: {}".format(self.acceptable_gain_values)
            raise ValueError(msg)


class AmplfierGainDevice(Device):
    _default_configuration_attrs = ()
    _default_read_attrs = ('gain', 'background', 'background_error')

    gain = FormattedComponent(EpicsSignal, '{self.prefix}gain{self._ch_num}')
    background = FormattedComponent(EpicsSignal, '{self.prefix}bkg{self._ch_num}')
    background_error = FormattedComponent(EpicsSignal, '{self.prefix}bkgErr{self._ch_num}')

    def __init__(self, prefix, ch_num=None, **kwargs):
        assert ch_num is not None, "Must provide `ch_num=` keyword argument."
        self._ch_num = ch_num
        super().__init__(prefix, **kwargs)
    
    def measure_background(self, parent, scaler, channel, numReadings):
        assert numReadings > 0, "numReadings ({}) must be >0".format(numReadings)
        assert isinstance(scaler, (EpicsScaler, ScalerCH))
        assert isinstance(channel, EpicsSignalRO)
        parent.setGain(self.gain.value) # use our own gain
        stage_sigs = {}
        stage_sigs["scaler"] = scaler.stage_sigs

        scaler.stage_sigs["preset_time"] = parent.background_count_time.value
        readings = []
        for i in range(numReadings):
            counting = scaler.trigger()    # start counting
            ophyd.status.wait(
                counting, 
                timeout=parent.background_count_time.value+1.0)
            readings.append(channel.value)
        self.background.put(np.mean(readings))
        self.background_error.put(np.std(readings))

        scaler.stage_sigs = stage_sigs["scaler"]
        msg = "gain = {} V/A, ".format(_gain_to_str_(self.gain.value))
        msg += "dark current = {} +/- {}".format(
            self.background.value,
            self.background_error.value,
        )
        print(msg)


class AutorangeSettings(object):
    """values allowed for sequence program's ``reqrange`` PV"""
    automatic = "automatic"
    auto_background = "auto+background"
    manual = "manual"


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
            AmplfierGainDevice, 'gain', 'suffix', range(NUM_AUTORANGE_GAINS)))
    counts_per_volt = Component(EpicsSignal, "vfc")
    status = Component(EpicsSignalRO, "updating")
    lurange = Component(EpicsSignalRO, "lurange")
    lucounts = Component(EpicsSignalRO, "lucounts")
    lurate = Component(EpicsSignalRO, "lurate")
    lucurrent = Component(EpicsSignalRO, "lucurrent")
    updating = Component(EpicsSignalRO, "updating")

    autoscale_count_time = Component(Signal, value=0.5)
    background_count_time = Component(Signal, value=1.0)

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
        
        # assume gain labels are formatted "{float} {other_text}"
        s = acceptable[0]
        self.gain_suffix = s[s.find(" "):]
        for i, s in enumerate(acceptable[:num_gains]):
            # verify all gains use same suffix text
            msg = "reqrange[{}] = {}, expected ending: '{}'".format(i, s, self.gain_suffix)
            assert s[s.find(" "):] == self.gain_suffix
        
        self._gain_info_known = True

    def setGain(self, target):
        """
        request the gain on the autorange controls
        
        Since the gain values are available from EPICS, 
        we use that to provide a method that can request the 
        gain by any of these values:
        
        * gain text value (from EPICS)
        * integer index number
        * desired gain floating-point value
        
        Assumptions:
        
        * gain label (from EPICS) is ALWAYS: "{float} {self.gain_suffix}"
        * float mantissa is always one digit
        """
        if not self._gain_info_known:
            self.__init_gains__(self.reqrange.enum_strs)
        if target in self.acceptable_gain_values:
            if isinstance(target, (int, float)) and target > self.num_gains:
                # gain value specified, rewrite as str
                # assume mantissa is only 1 digit
                target = _gain_to_str_(target) + self.gain_suffix
            if isinstance(target, str) and str(target) in self.reqrange.enum_strs:
                # must set reqrange by index number, rewrite as int
                target = self.reqrange.enum_strs.index(target)
            self.reqrange.put(target)
        else:
            msg = "could not set gain to {}, ".format(target)
            msg += "must be one of these: {}".format(self.acceptable_gain_values)
            raise ValueError(msg)

    def measure_dark_currents(self, scaler, signal, numReadings=8, shutter=None):
        """
        measure the dark current background on each gain
        
        note: Should this be a plan? No.  Can always launch in a thread.
        """
        starting = dict(
            gain = self.reqrange.value,
            mode = self.mode.value,
        )
        if shutter is not None:
            shutter.close()
        self.mode.put(AutorangeSettings.manual)
        for range_name in sorted(self.ranges.read_attrs):
            if range_name.find(".") >= 0 or not range_name.startswith("gain"):
                continue
            # tell each gain to measure its own background
            print(range_name)
            gain = self.ranges.__getattr__(range_name)
            print(gain)
            gain.measure_background(self, scaler, signal, numReadings)
        self.reqrange.put(starting["gain"])
        self.mode.put(starting["mode"])

    def autoscale(self, scaler, shutter=None):
        """
        set the amplifier to autoscale+background, settle to the best gain
        """
        stage_sigs = {}
        stage_sigs["scaler"] = scaler.stage_sigs

        scaler.stage_sigs["preset_time"] = self.autoscale_count_time.value
        if shutter is not None:
            shutter.open()

        self.mode.put(AutorangeSettings.auto_background)
        for _ignore_number_ in range(NUM_AUTORANGE_GAINS):
            counting = scaler.trigger()    # start counting
            ophyd.status.wait(
                counting, 
                timeout=self.autoscale_count_time.value+1.0)
            print("gain = {} V/A".format(_gain_to_str_(self.gain.value)))

        scaler.stage_sigs = stage_sigs["scaler"]

    @property
    def isUpdating(self):
        v = self.mode.value in (1, AutorangeSettings.auto_background)
        if v:
            v = self.updating.value in (1, "Updating")
        return v


class DetectorAmplifierAutorangeDevice(Device):
    """
    Coordinate the different objects that control a diode or ion chamber
    
    This is a convenience intended to simplify tasks such
    as measuring simultaneously the backgrounds of all channels.
    """

    def __init__(self, nickname, scaler, signal, amplifier, auto, **kwargs):
        assert isinstance(nickname, str)
        assert isinstance(scaler, (EpicsScaler, ScalerCH))
        assert isinstance(signal, EpicsSignalRO)
        assert isinstance(amplifier, FemtoAmplifierDevice)
        assert isinstance(auto, AmplifierAutoDevice)
        self.nickname = nickname
        self.scaler = scaler
        self.signal = signal
        self.femto = amplifier
        self.auto = auto
        super().__init__("", **kwargs)

    def measure_dark_currents(self, numReadings=8, shutter=None):
        print("Measure dark current backgrounds for: " + self.nickname)
        self.auto.measure_dark_currents(self.scaler, self.signal, numReadings, shutter)

    def autoscale(self, shutter=None):
        """
        set the amplifier to autoscale+background, settle to the best gain
        """
        print("Autoscaling for: " + self.nickname)
        self.auto.autoscale(self.scaler, shutter)


# ------------

_amplifier_id_upd = epics.caget("9idcLAX:femto:model", as_string=True)

if _amplifier_id_upd == "DLCPA200":
    _upd_femto_prefix = "9idcLAX:fem01:seq01:"
    _upd_auto_prefix  = "9idcLAX:pd01:seq01:"
elif _amplifier_id_upd == "DDPCA300":
    _upd_femto_prefix = "9idcLAX:fem09:seq02:"
    _upd_auto_prefix  = "9idcLAX:pd01:seq02:"

upd_femto_amplifier  = FemtoAmplifierDevice(_upd_femto_prefix, name="upd_femto_amplifier")
trd_femto_amplifier  = FemtoAmplifierDevice("9idcRIO:fem05:seq01:", name="trd_femto_amplifier")
I0_femto_amplifier   = FemtoAmplifierDevice("9idcRIO:fem02:seq01:", name="I0_femto_amplifier")
I00_femto_amplifier  = FemtoAmplifierDevice("9idcRIO:fem03:seq01:", name="I00_femto_amplifier")
I000_femto_amplifier = FemtoAmplifierDevice("9idcRIO:fem04:seq01:", name="I000_femto_amplifier")

upd_autorange = AmplifierAutoDevice(_upd_auto_prefix, name="upd_autorange")
trd_autorange = AmplifierAutoDevice("9idcLAX:pd05:seq01:", name="trd_autorange")
I0_autorange = AmplifierAutoDevice("9idcLAX:pd02:seq01:", name="I0_autorange")
I00_autorange = AmplifierAutoDevice("9idcLAX:pd03:seq01:", name="I00_autorange")

upd_controls = DetectorAmplifierAutorangeDevice(
    "PD_USAXS",
    scaler0,
    UPD_SIGNAL,
    upd_femto_amplifier,
    upd_autorange,
    name="upd_controls",
)

trd_controls = DetectorAmplifierAutorangeDevice(
    "TR diode",
    scaler0,
    TRD_SIGNAL,
    trd_femto_amplifier,
    trd_autorange,
    name="trd_controls",
)

I0_controls = DetectorAmplifierAutorangeDevice(
    "I0_USAXS",
    scaler0,
    I0_SIGNAL,
    I0_femto_amplifier,
    I0_autorange,
    name="I0_controls",
)

I00_controls = DetectorAmplifierAutorangeDevice(
    "I0_USAXS",
    scaler0,
    I00_SIGNAL,
    I00_femto_amplifier,
    I00_autorange,
    name="I00_controls",
)

