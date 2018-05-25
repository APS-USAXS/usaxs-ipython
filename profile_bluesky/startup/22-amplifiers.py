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


NUM_AUTORANGE_GAINS = 5     # common to all autorange sequence programs

def _gain_to_str_(gain):    # convenience function
    return ("%.0e" % gain).replace("+", "").replace("e0", "e")


class AutorangeSettings(object):
    """values allowed for sequence program's ``reqrange`` PV"""
    automatic = "automatic"
    auto_background = "auto+background"
    manual = "manual"


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


def _gains_subgroup_(cls, nm, gains, **kwargs):
    """internal: used in AmplifierAutoDevice"""
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
            AmplfierGainDevice, 'gain', range(NUM_AUTORANGE_GAINS)))
    counts_per_volt = Component(EpicsSignal, "vfc")
    status = Component(EpicsSignalRO, "updating")
    lurange = Component(EpicsSignalRO, "lurange")
    lucounts = Component(EpicsSignalRO, "lucounts")
    lurate = Component(EpicsSignalRO, "lurate")
    lucurrent = Component(EpicsSignalRO, "lucurrent")
    updating = Component(EpicsSignalRO, "updating")

    autoscale_count_time = Component(Signal, value=0.5)

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

    def autoscale(self, shutter=None):
        """
        set the amplifier to autoscale+background, settle to the best gain
        """
        print("Autoscaling for: " + self.nickname)
        self.auto.autoscale(self.scaler, shutter)


def _common_scaler_measurement_(control_list, count_time=1.0, num_readings=8):
    """internal: measure backgrounds from signals sharing a common scaler"""
    scaler = control_list[0].scaler
    signals = [c.signal for c in control_list]
    
    stage_sigs = {}
    stage_sigs["scaler"] = scaler.stage_sigs
    scaler.stage_sigs["preset_time"] = count_time

    for n in range(NUM_AUTORANGE_GAINS):
        # set gains
        for control in control_list:
            control.auto.setGain(n)
        readings = {s.pvname: [] for s in signals}
        
        for m in range(num_readings):
            # count and wait to complete
            counting = scaler.trigger()
            ophyd.status.wait(counting, timeout=count_time+1.0)
            
            for s in signals:
                readings[s.pvname].append(s.value)
    
        s_range_name = "gain{}".format(n)
        for c in control_list:
            g = c.auto.ranges.__getattr__(s_range_name)
            g.background.put(np.mean(readings[c.signal.pvname]))
            g.background_error.put(np.std(readings[c.signal.pvname]))

    scaler.stage_sigs = stage_sigs["scaler"]


def measure_background(controls, shutter=None, count_time=1.0, num_readings=8):
    """
    interactive function to measure detector backgrounds simultaneously
    
    controls [obj]
        list (or tuple) of ``DetectorAmplifierAutorangeDevice``
    """
    assert isinstance(controls, (tuple, list)), "controls must be a list"
    scaler_dict = {}    # sort the list of controls by scaler
    for i, control in enumerate(controls):
        msg = "controls[{}] must be".format(i)
        msg += " instance of 'DetectorAmplifierAutorangeDevice'"
        msg += ", provided: {}".format(control)
        assert isinstance(control, DetectorAmplifierAutorangeDevice), msg
        k = control.scaler.prefix
        if k not in scaler_dict:
            scaler_dict[k] = []
        scaler_dict[k].append(control)
    
    if shutter is not None:
        shutter.close()

    for control_list in scaler_dict.values():
        # TODO: could do each of these in parallel threads
        # for now, in sequence
        _common_scaler_measurement_(control_list, count_time, num_readings)


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

controls_list_I0_I00_TRD = [I0_controls, I00_controls, trd_controls]
controls_list_UPD_I0_I00_TRD = [upd_controls] + controls_list_I0_I00_TRD
