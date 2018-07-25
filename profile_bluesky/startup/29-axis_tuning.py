print(__file__)

"""
configure per-axis tuning

A tunable axis has these attributes::

    tuner : obj (function reference)
        reference to tuning method, such as `APS_BlueSky_tools.plans.TuneAxis()`,
        Default value is `None` -- this *must* be set before axis can be tuned.

    pre_tune_method : obj (function reference)
        function to be called before tuning starts, 
        the default prints status.  
        Use this to stage various components for the tune.

    pre_tune_method : obj (function reference)
        function to be called after tuning ends, 
        the default prints status.  
        Use this to unstage various components after the tune.

For reference, `APS_BlueSky_tools.plans.TuneAxis().tune()` uses these default attributes::

    width : float
        full range that axis will be scanned, default = 1

    num : int 
        full range that axis will be scanned, default = 10

    peak_choice : str
        either "cen" (default: peak value) or "com" (center of mass)

These attributes, set internally, are available for reference::

    axis : instance of `EpicsMotor` (or other positioner with `AxisTunerMixin`)
        positioner to be used

    signals : list of instances of `ScalerCH`, `EpicsScaler`, or similar
        list of detectors to be used

    signal_name : str 
        name of specific detector signal (must be in `signals`) to use for tuning

These attributes, set internally, are results of the tune scan::

    tune_ok : bool 
        status of most recent tune

    peaks : instance of `bluesky.callbacks.fitting.PeakStats`
        with results from most recent tune scan

    stats : [peaks]
        list of peak summary statistics from all previous tune scans

    center : float
        value of tune result: `if tune_ok: axis.move(center)` 

"""

# use center-of-mass, and not peak value: "com"
TUNE_METHOD_PEAK_CHOICE = "com"

USING_MS_STAGE = False


# use I00 (if MS stage is used, use I0)
if USING_MS_STAGE:
    TUNING_DET_SIGNAL = I00_SIGNAL
else:
    TUNING_DET_SIGNAL = I0_SIGNAL


# -------------------------------------------

def mr_pretune_hook():
    msg = "Tuning axis {}, current position is {}"
    print(msg.format(m_stage.r.name, m_stage.r.position))
    scaler0.stage_sigs["preset_time"] = 0.1
     
 
def mr_posttune_hook():
    msg = "Tuning axis {}, final position is {}"
    print(msg.format(m_stage.r.name, m_stage.r.position))
    yield from bps.mv(mr_val_center, m_stage.r.position)
 

# TODO: EpicsScaler would not count the detector when detectors=[TUNING_DET_SIGNAL]

def _getScalerSignalName_(scaler, signal):
    if isinstance(scaler, ScalerCH):
        return signal.chname.value
    elif isinstance(scaler, EpicsScaler):
        return signal.name    
        
m_stage.r.tuner = TuneAxis([scaler0], m_stage.r, signal_name=_getScalerSignalName_(scaler0, TUNING_DET_SIGNAL))
m_stage.r.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
m_stage.r.tuner.num = 31
m_stage.r.tuner.width = 0.005

m_stage.r.pre_tune_method = mr_pretune_hook
m_stage.r.post_tune_method = mr_posttune_hook


def tune_mr():
    """
    plan for simple tune and report
    
    satisfies: report of tuning OK/not OK on console
    """
    mr_start = m_stage.r.position
    yield from bps.mv(ti_filter_shutter, "open")
    yield from m_stage.r.tune()
    yield from bps.mv(
        ti_filter_shutter, "close",
        scaler0.count_mode, "AutoCount",
    )

    found = m_stage.r.tuner.peak_detected()
    print("starting mr position:", m_stage.r.position)
    print("peak detected:", found)
    if found:
        print("  center:", m_stage.r.tuner.peaks.cen)
        print("  centroid:", m_stage.r.tuner.peaks.com)
        print("  fwhm:", m_stage.r.tuner.peaks.fwhm)
    print("final mr position:", m_stage.r.position)


# -------------------------------------------


def m2rp_pretune_hook():
    msg = "Tuning axis {}, current position is {}"
    print(msg.format(m_stage.r2p.name, m_stage.r2p.position))
    scaler0.stage_sigs["preset_time"] = 0.1
    yield from bps.mv(scaler0.delay, 0.02)
    

def m2rp_posttune_hook():
    #
    # TODO: first, re-position piezo considering hysteresis?
    #
    msg = "Tuning axis {}, final position is {}"
    print(msg.format(m_stage.r2p.name, m_stage.r2p.position))
    yield from bps.mv(scaler0.delay, 0.05)


# use I00 (if MS stage is used, use I0)
m_stage.r2p.tuner = TuneAxis([scaler0], m_stage.r2p, signal_name=TUNING_DET_SIGNAL.name)
m_stage.r2p.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
m_stage.r2p.tuner.num = 21
m_stage.r2p.tuner.width = 6

m_stage.r2p.pre_tune_method = m2rp_pretune_hook
m_stage.r2p.post_tune_method = m2rp_posttune_hook


# -------------------------------------------


def msrp_pretune_hook():
    msg = "Tuning axis {}, current position is {}"
    print(msg.format(ms_stage.rp.name, ms_stage.rp.position))
    scaler0.stage_sigs["preset_time"] = 0.1
     
 
def msrp_posttune_hook():
    msg = "Tuning axis {}, final position is {}"
    print(msg.format(ms_stage.rp.name, ms_stage.rp.position))
    yield from bps.mv(msr_val_center, ms_stage.rp.position)
 
 
# use I00 (if MS stage is used, use I0)
ms_stage.rp.tuner = TuneAxis([scaler0], ms_stage.rp, signal_name=TUNING_DET_SIGNAL.name)
ms_stage.rp.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
ms_stage.rp.tuner.num = 21
ms_stage.rp.tuner.width = 6

ms_stage.rp.pre_tune_method = msrp_pretune_hook
ms_stage.rp.post_tune_method = msrp_posttune_hook


# -------------------------------------------


def ar_pretune_hook():
    msg = "Tuning axis {}, current position is {}"
    print(msg.format(a_stage.r.name, a_stage.r.position))
    scaler0.stage_sigs["preset_time"] = 0.1


def ar_posttune_hook():
    msg = "Tuning axis {}, final position is {}"
    print(msg.format(a_stage.r.name, a_stage.r.position))

    if a_stage.r.tuner.tune_ok:
        yield from bps.mv(ar_val_center, a_stage.r.position)
        # remember the Q calculation needs a new 2theta0
        # use the current AR encoder position
        yield from bps.mv(usaxs_q_calc.channels.B, usaxs_q_calc.channels.A.value)


a_stage.r.tuner = TuneAxis([scaler0], a_stage.r, signal_name=UPD_SIGNAL.name)
a_stage.r.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
a_stage.r.tuner.num = 35
a_stage.r.tuner.width = 0.004

a_stage.r.pre_tune_method = ar_pretune_hook
a_stage.r.post_tune_method = ar_posttune_hook


# -------------------------------------------


def asrp_pretune_hook():
    msg = "Tuning axis {}, current position is {}"
    print(msg.format(as_stage.rp.name, as_stage.rp.position))
    scaler0.stage_sigs["preset_time"] = 0.1
     
 
def asrp_posttune_hook():
    msg = "Tuning axis {}, final position is {}"
    print(msg.format(as_stage.rp.name, as_stage.rp.position))
    yield from bps.mv(msr_val_center, as_stage.rp.position)
 
 
# use I00 (if MS stage is used, use I0)
as_stage.rp.tuner = TuneAxis([scaler0], as_stage.rp, signal_name=UPD_SIGNAL.name)
as_stage.rp.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
as_stage.rp.tuner.num = 21
as_stage.rp.tuner.width = 6

as_stage.rp.pre_tune_method = asrp_pretune_hook
as_stage.rp.post_tune_method = asrp_posttune_hook

# -------------------------------------------


def a2rp_pretune_hook():
    msg = "Tuning axis {}, current position is {}"
    print(msg.format(a_stage.r2p.name, a_stage.r2p.position))
    scaler0.stage_sigs["preset_time"] = 0.1
    yield from bps.mv(scaler0.delay, 0.02)


def a2rp_posttune_hook():
    #
    # TODO: first, re-position piezo considering hysteresis?
    #
    msg = "Tuning axis {}, final position is {}"
    print(msg.format(a_stage.r2p.name, a_stage.r2p.position))

    if a_stage.r2p.tuner.tune_ok:
        # remember the Q calculation needs a new 2theta0
        # use the current AR encoder position
        yield from bps.mv(usaxs_q_calc.channels.B, usaxs_q_calc.channels.A.value)
    yield from bps.mv(scaler0.delay, 0.05)


a_stage.r2p.tuner = TuneAxis([scaler0], a_stage.r2p, signal_name=UPD_SIGNAL.name)
a_stage.r2p.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
a_stage.r2p.tuner.num = 31
a_stage.r2p.tuner.width = 6
a_stage.r2p.pre_tune_method = a2rp_pretune_hook
a_stage.r2p.post_tune_method = a2rp_posttune_hook



def tune_usaxs_optics():
    yield from m_stage.r.tuner.tune()
    yield from m_stage.r2p.tuner.tune()
    yield from a_stage.r.tuner.tune()
    yield from a_stage.r2p.tuner.tune()
