print(__file__)

"""
detectors, amplifiers, and related support

#            Define local PD address:
 if(Use_DLPCA300){
     PDstring = "pd01:seq02"
     UPD_PV    =    "9idcUSX:pd01:seq02"    
  }else{
     PDstring = "pd01:seq01"
     UPD_PV    =    "9idcUSX:pd01:seq01"  
  }

========  =================  ====================  ===================  ===========
detector  scaler             amplifier             autorange sequence   Femto model
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
and then use it with inline dictionaries to pick the right PVs.
"""


logger = logging.getLogger(os.path.split(__file__)[-1])


NUM_AUTORANGE_GAINS = 5     # common to all autorange sequence programs
AMPLIFIER_MINIMUM_SETTLING_TIME = 0.01    # reasonable?


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
    
    # gain settling time for the device is <150ms
    settling_time = Component(Signal, value=0.08)

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
            yield from bps.mv(self.gainindex, target)
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
    
    max_count_rate = Component(Signal, value=950000)

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
        plan: set the gain on the autorange controls
        
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
            yield from bps.mv(self.reqrange, target)
        else:
            msg = "could not set gain to {}, ".format(target)
            msg += "must be one of these: {}".format(self.acceptable_gain_values)
            raise ValueError(msg)

    @property
    def isUpdating(self):
        v = self.mode.value in (1, AutorangeSettings.auto_background)
        if v:
            v = self.updating.value in (1, "Updating")
        return v


#class ComputedScalerAmplifierSignal(SynSignal):
#    """
#    Scales signal from counter by amplifier gain.
#    """
#
#    def __init__(self, name, parent, **kwargs):
#
#        def func():		# runs only when Device is triggered
#            counts = parent.signal.s.value
#            volts = counts / parent.auto.counts_per_volt.value
#            volts_per_amp = parent.femto.gain.value
#            return volts / volts_per_amp
#
#        super().__init__(func=func, name=name, **kwargs)


class DetectorAmplifierAutorangeDevice(Device):
    """
    Coordinate the different objects that control a diode or ion chamber
    
    This is a convenience intended to simplify tasks such
    as measuring simultaneously the backgrounds of all channels.
    """

    def __init__(self, nickname, scaler, signal, amplifier, auto, **kwargs):
        assert isinstance(nickname, str)
        assert isinstance(scaler, ScalerCH)      # dropped EpicsScaler
        assert isinstance(signal, ScalerChannel) # dropped EpicsSignalRO
        assert isinstance(amplifier, FemtoAmplifierDevice)
        assert isinstance(auto, AmplifierAutoDevice)
        self.nickname = nickname
        self.scaler = scaler
        self.signal = signal
        self.femto = amplifier
        self.auto = auto
        super().__init__("", **kwargs)


def group_controls_by_scaler(controls):
    """
    return dictionary of [controls] keyed by common scaler support
    
    controls [obj]
        list (or tuple) of ``DetectorAmplifierAutorangeDevice``
    """
    assert isinstance(controls, (tuple, list)), "controls must be a list"
    scaler_dict = OrderedDefaultDict(list)    # sort the list of controls by scaler
    for i, control in enumerate(controls):
        # each item in list MUST be instance of DetectorAmplifierAutorangeDevice
        msg = "controls[{}] must be".format(i)
        msg += " instance of 'DetectorAmplifierAutorangeDevice'"
        msg += ", provided: {}".format(control)
        assert isinstance(control, DetectorAmplifierAutorangeDevice), msg

        k = control.scaler.name       # key by scaler's ophyd device name
        scaler_dict[k].append(control)  # group controls by scaler
    return scaler_dict


def _scaler_background_measurement_(control_list, count_time=0.2, num_readings=8):
    """plan: internal: measure amplifier backgrounds for signals sharing a common scaler"""
    scaler = control_list[0].scaler
    signals = [c.signal for c in control_list]
    
    stage_sigs = {}
    stage_sigs["scaler"] = scaler.stage_sigs   # benign
    original = {}
    original["scaler.preset_time"] = scaler.preset_time.value
    original["scaler.auto_count_delay"] = scaler.auto_count_delay.value
    yield from bps.mv(
        scaler.preset_time, count_time,
        scaler.auto_count_delay, 0
        )

    for control in control_list:
        yield from bps.mv(control.auto.mode, AutorangeSettings.manual)

    for n in range(NUM_AUTORANGE_GAINS-1, -1, -1):  # reverse order
        # set gains
        settling_time = AMPLIFIER_MINIMUM_SETTLING_TIME
        for control in control_list:
            yield from control.auto.setGain(n)
            settling_time = max(settling_time, control.femto.settling_time.value)
        yield from bps.sleep(settling_time)
        
        def getScalerChannelPvname(scaler_channel):
            try:
                return scaler_channel.pvname        # EpicsScaler channel
            except AttributeError:
                return scaler_channel.chname.value  # ScalerCH channel
        
        # readings is a PV-keyed dictionary
        readings = {getScalerChannelPvname(s): [] for s in signals}
        
        for m in range(num_readings):
            # count and wait to complete
            yield from bps.trigger(scaler, wait=True)        #timeout=count_time+1.0)
            
            for s in signals:
                pvname = getScalerChannelPvname(s)
                try:
                    value = s.value     # EpicsScaler channels
                except AttributeError:
                    value = s.s.value     # ScalerCH channels
                readings[pvname].append(value)
    
        s_range_name = "gain{}".format(n)
        for control in control_list:
            g = control.auto.ranges.__getattr__(s_range_name)
            pvname = getScalerChannelPvname(control.signal)
            yield from bps.mv(
                g.background, np.mean(readings[pvname]),
                g.background_error, np.std(readings[pvname]),
            )
            msg = "{} range={} gain={}  bkg={}  +/- {}".format(
                control.nickname, 
                n,
                _gain_to_str_(control.auto.gain.value), 
                g.background.value, 
                g.background_error.value)
            logger.info(msg)
            print(msg)

    scaler.stage_sigs = stage_sigs["scaler"]
    yield from bps.mv(
        scaler.preset_time, original["scaler.preset_time"],
        scaler.auto_count_delay, original["scaler.auto_count_delay"],
        )


def measure_background(controls, shutter=None, count_time=0.2, num_readings=5):
    """
    plan: measure detector backgrounds simultaneously
    
    controls [obj]
        list (or tuple) of ``DetectorAmplifierAutorangeDevice``
    """
    assert isinstance(controls, (tuple, list)), "controls must be a list"
    scaler_dict = group_controls_by_scaler(controls)
    
    if shutter is not None:
        yield from bps.mv(shutter, "close")

    for control_list in scaler_dict.values():
        # do these in sequence, just in case same hardware used multiple times
        if len(control_list) > 0:
            msg = "Measuring background for: " + control_list[0].nickname
            logger.info(msg)
            yield from _scaler_background_measurement_(control_list, count_time, num_readings)


_last_autorange_gain_ = OrderedDefaultDict(dict)

def _scaler_autoscale_(controls, count_time=0.05, max_iterations=9):
    """plan: internal: autoscale amplifiers for signals sharing a common scaler"""
    global _last_autorange_gain_

    scaler = controls[0].scaler
    originals = {}

    originals["preset_time"] = scaler.preset_time.value
    originals["delay"] = scaler.delay.value
    originals["count_mode"] = scaler.count_mode.value
    yield from bps.mv(
        scaler.preset_time, count_time,
        scaler.delay, 0.2,
        scaler.count_mode, "OneShot",
    )

    last_gain_dict = _last_autorange_gain_[scaler.name]

    settling_time = AMPLIFIER_MINIMUM_SETTLING_TIME
    for control in controls:
        yield from bps.mv(control.auto.mode, AutorangeSettings.auto_background)
        # faster if we start from last known autoscale gain
        gain = last_gain_dict.get(control.auto.gain.name)
        if gain is not None:    # be cautious, might be unknown
            yield from control.auto.setGain(gain)
        last_gain_dict[control.auto.gain.name] = control.auto.gain.value
        settling_time = max(settling_time, control.femto.settling_time.value)
    
    yield from bps.sleep(settling_time)

    # How many times to let autoscale work?
    # Number of possible gains is one choice - NUM_AUTORANGE_GAINS
    # consider: could start on one extreme, end on the other
    max_iterations = min(max_iterations, NUM_AUTORANGE_GAINS)

    # Better to let caller set a higher possible number
    # Converge if no gains change
    # Also, make sure no detector count rates are stuck at max
    
    for iteration in range(max_iterations):
        converged = []      # append True is convergence criteria is satisfied
        yield from bps.trigger(scaler, wait=True)        #timeout=count_time+1.0)
        
        # amplifier sequence program (in IOC) will adjust the gain now
        
        for control in controls:
            # any gains changed?
            gain_now = control.auto.gain.value
            gain_previous = last_gain_dict[control.auto.gain.name]
            converged.append(gain_now == gain_previous)
            last_gain_dict[control.auto.gain.name] = gain_now
        
            # are we topped up on any detector?
            max_rate = control.auto.max_count_rate.value
            if isinstance(control.signal, ScalerChannel):
                actual_rate = control.signal.s.value
            elif isinstance(control.signal, EpicsSignalRO):
                actual_rate = control.signal.value
            else:
                raise ValueError("unexpected control.signal: {}".format(control.signal))
            converged.append(actual_rate <= max_rate)
        
        if False not in converged:      # all True?
            complete = True
            for control in controls:
                yield from bps.mv(control.auto.mode, "manual")
            break   # no changes
        logger.debug("converged: {}".format(converged))

    # scaler.stage_sigs = stage_sigs["scaler"]
    # restore starting conditions
    yield from bps.mv(
        scaler.preset_time, originals["preset_time"],
        scaler.delay, originals["delay"],
        scaler.count_mode, originals["count_mode"],
    )

    if not complete:        # bailed out early from loop
        print(f"converged={converged}")
        msg = f"FAILED TO FIND CORRECT GAIN IN {max_iterations} AUTOSCALE ITERATIONS"
        raise RuntimeError(msg)     # FIXME: may false fail during summarize_plan()


def autoscale_amplifiers(controls, shutter=None, count_time=0.05, max_iterations=9):
    """
    bluesky plan: autoscale detector amplifiers simultaneously
    
    controls [obj]
        list (or tuple) of ``DetectorAmplifierAutorangeDevice``
    """
    assert isinstance(controls, (tuple, list)), "controls must be a list"
    scaler_dict = group_controls_by_scaler(controls)
    
    if shutter is not None:
        yield from bps.mv(shutter, "open")

    for control_list in scaler_dict.values():
        # do these in sequence, just in case same hardware used multiple times
        if len(control_list) > 0:
            msg = "Autoscaling amplifier for: " + control_list[0].nickname
            logger.info(msg)
            yield from _scaler_autoscale_(
                control_list, 
                count_time=count_time, 
                max_iterations=max_iterations)


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

upd_autorange_controls = AmplifierAutoDevice(_upd_auto_prefix, name="upd_autorange_controls")
trd_autorange_controls = AmplifierAutoDevice("9idcLAX:pd05:seq01:", name="trd_autorange_controls")
I0_autorange_controls = AmplifierAutoDevice("9idcLAX:pd02:seq01:", name="I0_autorange_controls")
I00_autorange_controls = AmplifierAutoDevice("9idcLAX:pd03:seq01:", name="I00_autorange_controls")

upd_controls = DetectorAmplifierAutorangeDevice(
    "PD_USAXS",
    scaler0,
    UPD_SIGNAL,
    upd_femto_amplifier,
    upd_autorange_controls,
    name="upd_controls",
)
#upd_photocurrent = ComputedScalerAmplifierSignal(
#    name="upd_photocurrent", parent=upd_controls)
upd_photocurrent_calc = APS_synApps_ophyd.swaitRecord(
    "9idcLAX:USAXS:upd", 
    name="upd_photocurrent_calc")
upd_photocurrent = upd_photocurrent_calc.val

trd_controls = DetectorAmplifierAutorangeDevice(
    "TR diode",
    scaler0,
    TRD_SIGNAL,
    trd_femto_amplifier,
    trd_autorange_controls,
    name="trd_controls",
)
#trd_photocurrent = ComputedScalerAmplifierSignal(
#    name="trd_photocurrent", parent=trd_controls)
trd_photocurrent_calc = APS_synApps_ophyd.swaitRecord(
    "9idcLAX:USAXS:trd", 
    name="trd_photocurrent_calc")
trd_photocurrent = trd_photocurrent_calc.val

I0_controls = DetectorAmplifierAutorangeDevice(
    "I0_USAXS",
    scaler0,
    I0_SIGNAL,
    I0_femto_amplifier,
    I0_autorange_controls,
    name="I0_controls",
)
#I0_photocurrent = ComputedScalerAmplifierSignal(
#    name="I0_photocurrent", parent=I0_controls)
I0_photocurrent_calc = APS_synApps_ophyd.swaitRecord(
    "9idcLAX:USAXS:I0", 
    name="I0_photocurrent_calc")
I0_photocurrent = I0_photocurrent_calc.val

I00_controls = DetectorAmplifierAutorangeDevice(
    "I00_USAXS",
    scaler0,
    I00_SIGNAL,
    I00_femto_amplifier,
    I00_autorange_controls,
    name="I00_controls",
)
#I00_photocurrent = ComputedScalerAmplifierSignal(
#    name="I00_photocurrent", parent=I00_controls)
I00_photocurrent_calc = APS_synApps_ophyd.swaitRecord(
    "9idcLAX:USAXS:I00", 
    name="I00_photocurrent_calc")
I00_photocurrent = I00_photocurrent_calc.val


I000_photocurrent_calc = APS_synApps_ophyd.swaitRecord(
    "9idcLAX:USAXS:I000", 
    name="I000_photocurrent_calc")
I000_photocurrent = I000_photocurrent_calc.val


controls_list_I0_I00_TRD = [I0_controls, I00_controls, trd_controls]
controls_list_UPD_I0_I00_TRD = [upd_controls] + controls_list_I0_I00_TRD
