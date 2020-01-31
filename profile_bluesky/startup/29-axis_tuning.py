logger.info(__file__)
# logger.debug(resource_usage(os.path.split(__file__)[-1]))

"""
configure per-axis tuning

A tunable axis has these attributes::

    tuner : obj (function reference)
        reference to tuning method, such as `apstools.plans.TuneAxis()`,
        Default value is `None` -- this *must* be set before axis can be tuned.

    pre_tune_method : obj (function reference)
        function to be called before tuning starts,
        the default prints status.
        Use this to stage various components for the tune.

    pre_tune_method : obj (function reference)
        function to be called after tuning ends,
        the default prints status.
        Use this to unstage various components after the tune.

For reference, `apstools.plans.TuneAxis().tune()` uses these default attributes::

    width : float
        full range that axis will be scanned, default = 1

    num : int
        full range that axis will be scanned, default = 10

    peak_choice : str
        either "cen" (default: peak value) or "com" (center of mass)

These attributes, set internally, are available for reference::

    axis : instance of `EpicsMotor` (or other positioner with `APS_devices.AxisTunerMixin`)
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
TUNING_DET_SIGNAL = {True: I00_SIGNAL, False: I0_SIGNAL}[USING_MS_STAGE]


class TuneRanges(Device):
    """
    width of tuning for each axis

    TODO: placeholder until #232 is resolved
    see: https://github.com/APS-USAXS/ipython-usaxs/issues/232
    """
    ar   = Component(EpicsSignal, "9idcLAX:USAXS:tune_ar_range")
    a2rp = Component(EpicsSignal, "9idcLAX:USAXS:tune_a2rp_range")
    asrp = Component(EpicsSignal, "9idcLAX:USAXS:tune_asrp_range")
    mr   = Component(EpicsSignal, "9idcLAX:USAXS:tune_mr_range")
    m2rp = Component(EpicsSignal, "9idcLAX:USAXS:tune_m2rp_range")
    msrp = Component(EpicsSignal, "9idcLAX:USAXS:tune_msrp_range")
    dx = Component(EpicsSignal, "9idcLAX:USAXS:tune_dx_range")
    dy = Component(EpicsSignal, "9idcLAX:USAXS:tune_dy_range")

axis_tune_range = TuneRanges(name="axis_tune_range")


# -------------------------------------------

def mr_pretune_hook():
    stage = m_stage.r
    logger.info(f"Tuning axis {stage.name}, current position is {stage.position}")
    yield from bps.mv(scaler0.preset_time, 0.1)
    scaler0.select_channels([TUNING_DET_SIGNAL.chname.get()])
    scaler0.channels.chan01.kind = Kind.config
    stage.tuner.width = axis_tune_range.mr.get()


def mr_posttune_hook():
    msg = "Tuning axis {}, final position is {}"
    logger.info(msg.format(m_stage.r.name, m_stage.r.position))

    if m_stage.r.tuner.tune_ok:
        yield from bps.mv(terms.USAXS.mr_val_center, m_stage.r.position)

    scaler0.select_channels(None)


def _getScalerSignalName_(scaler, signal):
    if isinstance(scaler, ScalerCH):
        return signal.chname.get()
    elif isinstance(scaler, EpicsScaler):
        return signal.name

m_stage.r.tuner = APS_plans.TuneAxis([scaler0], m_stage.r, signal_name=_getScalerSignalName_(scaler0, TUNING_DET_SIGNAL))
m_stage.r.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
m_stage.r.tuner.num = 31
m_stage.r.tuner.width = axis_tune_range.mr.get()     # -0.004

m_stage.r.pre_tune_method = mr_pretune_hook
m_stage.r.post_tune_method = mr_posttune_hook


def _tune_base_(axis, md={}):
    """
    plan for simple tune and report

    satisfies: report of tuning OK/not OK on console
    """
    yield from IfRequestedStopBeforeNextScan()
    logger.info(f"tuning axis: {axis.name}")
    axis_start = axis.position
    yield from bps.mv(
        mono_shutter, "open",
        ti_filter_shutter, "open",
    )
    yield from autoscale_amplifiers([upd_controls, I0_controls, I00_controls])
    yield from axis.tune(md=md)
    yield from bps.mv(
        ti_filter_shutter, "close",
        scaler0.count_mode, "AutoCount",
    )

    found = axis.tuner.peak_detected()
    logger.info(f"axis: {axis.name}")
    logger.info(f"starting position: {axis_start}")
    logger.info(f"peak detected: {found}")
    if found:
        logger.info(f"  max: {axis.tuner.peaks.max}")
        logger.info(f"  center: {axis.tuner.peaks.cen}")
        logger.info(f"  centroid: {axis.tuner.peaks.com}")
        logger.info(f"  fwhm: {axis.tuner.peaks.fwhm}")
    logger.info(f"final position: {axis.position}")


def tune_mr(md={}):
    yield from bps.mv(scaler0.preset_time, 0.1)
    md['plan_name'] = "tune_mr"
    # print(f"metadata={md}")  # TOO much data to print
    yield from _tune_base_(m_stage.r, md=md)


# -------------------------------------------


def m2rp_pretune_hook():
    stage = m_stage.r2p
    logger.info(f"Tuning axis {stage.name}, current position is {stage.position}")
    yield from bps.mv(scaler0.preset_time, 0.1)
    yield from bps.mv(scaler0.delay, 0.02)
    scaler0.select_channels([TUNING_DET_SIGNAL.chname.get()])
    scaler0.channels.chan01.kind = Kind.config
    stage.tuner.width = axis_tune_range.m2rp.get()


def m2rp_posttune_hook():
    #
    # TODO: first, re-position piezo considering hysteresis?
    #
    msg = "Tuning axis {}, final position is {}"
    logger.info(msg.format(m_stage.r2p.name, m_stage.r2p.position))
    yield from bps.mv(scaler0.delay, 0.05)

    if m_stage.r2p.tuner.tune_ok:
        pass    # #165: update center when/if we get a PV for that

    scaler0.select_channels(None)


# use I00 (if MS stage is used, use I0)
m_stage.r2p.tuner = APS_plans.TuneAxis([scaler0], m_stage.r2p, signal_name=_getScalerSignalName_(scaler0, TUNING_DET_SIGNAL))
m_stage.r2p.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
m_stage.r2p.tuner.num = 21
m_stage.r2p.tuner.width = axis_tune_range.m2rp.get()     -8

m_stage.r2p.pre_tune_method = m2rp_pretune_hook
m_stage.r2p.post_tune_method = m2rp_posttune_hook


def tune_m2rp(md={}):
    yield from bps.sleep(0.2)   # piezo is fast, give the system time to react
    yield from bps.mv(scaler0.preset_time, 0.1)
    md['plan_name'] = "tune_m2rp"
    yield from _tune_base_(m_stage.r2p, md=md)
    yield from bps.sleep(0.1)   # piezo is fast, give the system time to react


def empty_plan(*args, **kwargs):
    logger.info(f"Doing nothing: args={args}, kwargs={kwargs}")
    yield from bps.null()


if m_stage.isChannelCut:
    m_stage.r2p.tuner = empty_plan      # TODO: should mimic APS_plans.TuneAxis()?
    m_stage.r2p.pre_tune_method = empty_plan
    m_stage.r2p.post_tune_method = empty_plan


# -------------------------------------------


def msrp_pretune_hook():
    stage = ms_stage.rp
    logger.info(f"Tuning axis {stage.name}, current position is {stage.position}")
    yield from bps.mv(scaler0.preset_time, 0.1)
    scaler0.select_channels([TUNING_DET_SIGNAL.chname.get()])
    scaler0.channels.chan01.kind = Kind.config
    stage.tuner.width = axis_tune_range.msrp.get()


def msrp_posttune_hook():
    msg = "Tuning axis {}, final position is {}"
    logger.info(msg.format(ms_stage.rp.name, ms_stage.rp.position))

    if ms_stage.rp.tuner.tune_ok:
        yield from bps.mv(terms.USAXS.msr_val_center, ms_stage.rp.position)

    scaler0.select_channels(None)


# use I00 (if MS stage is used, use I0)
ms_stage.rp.tuner = APS_plans.TuneAxis([scaler0], ms_stage.rp, signal_name=_getScalerSignalName_(scaler0, TUNING_DET_SIGNAL))
ms_stage.rp.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
ms_stage.rp.tuner.num = 21
ms_stage.rp.tuner.width = axis_tune_range.msrp.get()     # 6

ms_stage.rp.pre_tune_method = msrp_pretune_hook
ms_stage.rp.post_tune_method = msrp_posttune_hook


def tune_msrp(md={}):
    yield from bps.mv(scaler0.preset_time, 0.1)
    md['plan_name'] = "tune_msrp"
    yield from _tune_base_(ms_stage.rp, md=md)


# -------------------------------------------


def ar_pretune_hook():
    stage = a_stage.r
    logger.info(f"Tuning axis {stage.name}, current position is {stage.position}")
    yield from bps.mv(scaler0.preset_time, 0.1)
    scaler0.select_channels([UPD_SIGNAL.chname.get()])
    scaler0.channels.chan01.kind = Kind.config
    stage.tuner.width = axis_tune_range.ar.get()


def ar_posttune_hook():
    msg = "Tuning axis {}, final position is {}"
    logger.info(msg.format(a_stage.r.name, a_stage.r.position))

    if a_stage.r.tuner.tune_ok:
        yield from bps.mv(terms.USAXS.ar_val_center, a_stage.r.position)
        # remember the Q calculation needs a new 2theta0
        # use the current AR encoder position
        yield from bps.mv(
            usaxs_q_calc.channels.B.input_value, terms.USAXS.ar_val_center.get(),
            a_stage.r, terms.USAXS.ar_val_center.get(),
        )
    scaler0.select_channels(None)


a_stage.r.tuner = APS_plans.TuneAxis([scaler0], a_stage.r, signal_name=_getScalerSignalName_(scaler0, UPD_SIGNAL))
a_stage.r.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
a_stage.r.tuner.num = 35
a_stage.r.tuner.width = axis_tune_range.ar.get()     # -0.004

a_stage.r.pre_tune_method = ar_pretune_hook
a_stage.r.post_tune_method = ar_posttune_hook


def tune_ar(md={}):
    yield from bps.mv(ti_filter_shutter, "open")
    ##redundant## yield from autoscale_amplifiers([upd_controls])
    yield from bps.mv(scaler0.preset_time, 0.1)
    yield from bps.mv(upd_controls.auto.mode, "manual")
    md['plan_name'] = "tune_ar"
    yield from _tune_base_(a_stage.r, md=md)
    yield from bps.mv(upd_controls.auto.mode, "auto+background")


# -------------------------------------------


def asrp_pretune_hook():
    stage = as_stage.rp
    logger.info(f"Tuning axis {stage.name}, current position is {stage.position}")
    yield from bps.mv(scaler0.preset_time, 0.1)
    scaler0.select_channels([UPD_SIGNAL.chname.get()])
    scaler0.channels.chan01.kind = Kind.config
    stage.tuner.width = axis_tune_range.asrp.get()


def asrp_posttune_hook():
    msg = "Tuning axis {}, final position is {}"
    logger.info(msg.format(as_stage.rp.name, as_stage.rp.position))
    yield from bps.mv(terms.USAXS.asr_val_center, as_stage.rp.position)

    if as_stage.rp.tuner.tune_ok:
        pass    # #165: update center when/if we get a PV for that

    scaler0.select_channels(None)


# use I00 (if MS stage is used, use I0)
as_stage.rp.tuner = APS_plans.TuneAxis([scaler0], as_stage.rp, signal_name=_getScalerSignalName_(scaler0, UPD_SIGNAL))
as_stage.rp.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
as_stage.rp.tuner.num = 21
as_stage.rp.tuner.width = axis_tune_range.asrp.get()     # 6

as_stage.rp.pre_tune_method = asrp_pretune_hook
as_stage.rp.post_tune_method = asrp_posttune_hook


def tune_asrp(md={}):
    yield from bps.mv(ti_filter_shutter, "open")
    ##redundant## yield from autoscale_amplifiers([upd_controls])
    yield from bps.mv(scaler0.preset_time, 0.1)
    yield from bps.mv(upd_controls.auto.mode, "manual")
    md['plan_name'] = "tune_asrp"
    yield from _tune_base_(as_stage.rp, md=md)
    yield from bps.mv(upd_controls.auto.mode, "auto+background")


# -------------------------------------------


def a2rp_pretune_hook():
    stage = a_stage.r2p
    logger.info(f"Tuning axis {stage.name}, current position is {stage.position}")
    yield from bps.mv(scaler0.preset_time, 0.1)
    yield from bps.mv(scaler0.delay, 0.02)
    scaler0.select_channels([UPD_SIGNAL.chname.get()])
    scaler0.channels.chan01.kind = Kind.config
    stage.tuner.width = axis_tune_range.a2rp.get()


def a2rp_posttune_hook():
    #
    # TODO: first, re-position piezo considering hysteresis?
    #
    msg = "Tuning axis {}, final position is {}"
    logger.info(msg.format(a_stage.r2p.name, a_stage.r2p.position))
    yield from bps.mv(scaler0.delay, 0.05)

    if a_stage.r2p.tuner.tune_ok:
        pass    # #165: update center when/if we get a PV for that

    scaler0.select_channels(None)


a_stage.r2p.tuner = APS_plans.TuneAxis([scaler0], a_stage.r2p, signal_name=_getScalerSignalName_(scaler0, UPD_SIGNAL))
a_stage.r2p.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
a_stage.r2p.tuner.num = 31
a_stage.r2p.tuner.width = axis_tune_range.a2rp.get()     # -8
a_stage.r2p.pre_tune_method = a2rp_pretune_hook
a_stage.r2p.post_tune_method = a2rp_posttune_hook


def tune_a2rp(md={}):
    yield from bps.mv(ti_filter_shutter, "open")
    yield from bps.sleep(0.1)   # piezo is fast, give the system time to react
    ##redundant## yield from autoscale_amplifiers([upd_controls])
    yield from bps.mv(scaler0.preset_time, 0.1)
    yield from bps.mv(upd_controls.auto.mode, "manual")
    md['plan_name'] = "tune_a2rp"
    yield from _tune_base_(a_stage.r2p, md=md)
    yield from bps.mv(upd_controls.auto.mode, "auto+background")
    yield from bps.sleep(0.1)   # piezo is fast, give the system time to react


# -------------------------------------------


def dx_pretune_hook():
    stage = d_stage.x
    logger.info(f"Tuning axis {stage.name}, current position is {stage.position}")
    yield from bps.mv(scaler0.preset_time, 0.1)
    scaler0.select_channels([UPD_SIGNAL.chname.get()])
    scaler0.channels.chan01.kind = Kind.config
    stage.tuner.width = axis_tune_range.dx.get()


def dx_posttune_hook():
    stage = d_stage.x
    logger.info(f"Tuning axis {stage.name}, final position is {stage.position}")

    if stage.tuner.tune_ok:
        yield from bps.mv(terms.SAXS.dx_in, stage.position)

    scaler0.select_channels(None)


d_stage.x.tuner = APS_plans.TuneAxis([scaler0], d_stage.x, signal_name=_getScalerSignalName_(scaler0, UPD_SIGNAL))
d_stage.x.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
d_stage.x.tuner.num = 35
d_stage.x.tuner.width = axis_tune_range.dx.get()     # 10

d_stage.x.pre_tune_method = dx_pretune_hook
d_stage.x.post_tune_method = dx_posttune_hook


def tune_dx(md={}):
    yield from bps.mv(ti_filter_shutter, "open")
    ##redundant## yield from autoscale_amplifiers([upd_controls])
    yield from bps.mv(scaler0.preset_time, 0.1)
    yield from bps.mv(upd_controls.auto.mode, "manual")
    md['plan_name'] = "tune_dx"
    yield from _tune_base_(d_stage.x, md=md)
    yield from bps.mv(upd_controls.auto.mode, "auto+background")


# -------------------------------------------


def dy_pretune_hook():
    stage = d_stage.y
    logger.info(f"Tuning axis {stage.name}, current position is {stage.position}")
    yield from bps.mv(scaler0.preset_time, 0.1)
    scaler0.select_channels([UPD_SIGNAL.chname.get()])
    scaler0.channels.chan01.kind = Kind.config
    stage.tuner.width = axis_tune_range.dy.get()


def dy_posttune_hook():
    stage = d_stage.y
    logger.info(f"Tuning axis {stage.name}, final position is {stage.position}")

    if stage.tuner.tune_ok:
        yield from bps.mv(terms.USAXS.DY0, stage.position)

    scaler0.select_channels(None)


d_stage.y.tuner = APS_plans.TuneAxis([scaler0], d_stage.y, signal_name=_getScalerSignalName_(scaler0, UPD_SIGNAL))
d_stage.y.tuner.peak_choice = TUNE_METHOD_PEAK_CHOICE
d_stage.y.tuner.num = 35
d_stage.y.tuner.width = axis_tune_range.dx.get()     # 10

d_stage.y.pre_tune_method = dy_pretune_hook
d_stage.y.post_tune_method = dy_posttune_hook


def tune_dy(md={}):
    yield from bps.mv(ti_filter_shutter, "open")
    ##redundant## yield from autoscale_amplifiers([upd_controls])
    yield from bps.mv(scaler0.preset_time, 0.1)
    yield from bps.mv(upd_controls.auto.mode, "manual")
    md['plan_name'] = "tune_dy"
    yield from _tune_base_(d_stage.y, md=md)
    yield from bps.mv(upd_controls.auto.mode, "auto+background")


def tune_diode(md={}):
    yield from tune_dx(md=md)
    yield from tune_dy(md=md)


# -------------------------------------------


def tune_usaxs_optics(side=False, md={}):
    """
    tune all the instrument optics currently in configuration
    
    This plan is for staff use.
    Users are advised to use preUSAXStune() instead.
    """
    yield from mode_USAXS()

    suspender_preinstalled = suspend_BeamInHutch in RE.suspenders
    if not suspender_preinstalled:
        yield from bps.install_suspender(suspend_BeamInHutch)

    yield from tune_mr(md=md)
    yield from tune_m2rp(md=md)
    if side:
        yield from tune_msrp(md=md)
        yield from tune_asrp(md=md)
    yield from tune_ar(md=md)
    yield from tune_a2rp(md=md)

    if not suspender_preinstalled:
        yield from bps.remove_suspender(suspend_BeamInHutch)

    yield from bps.mv(
        terms.preUSAXStune.num_scans_last_tune, 0,
        terms.preUSAXStune.epoch_last_tune, time.time(),
    )


def tune_saxs_optics(md={}):
    yield from tune_mr(md=md)
    yield from tune_m2rp(md=md)
    yield from bps.mv(
        #terms.preUSAXStune.num_scans_last_tune, 0,
        terms.preUSAXStune.epoch_last_tune, time.time(),
    )


def tune_after_imaging(md={}):
    epics_ar_tune_range = axis_tune_range.ar.get()  # remember

    # tune_ar with custom tune range if that is larger
    custom_range = 0.005
    if epics_ar_tune_range > custom_range:
        yield from bps.mv(axis_tune_range.ar, custom_range)
        yield from tune_ar(md=md)

    # finally, tune_ar with standard tune range
    yield from bps.mv(axis_tune_range.ar, epics_ar_tune_range)
    yield from tune_ar(md=md)
    yield from tune_a2rp(md=md)


def instrument_default_tune_ranges():
    """
    plan: (re)compute tune ranges for each of the tunable axes
    """
    yield from bps.null()

    d_stage.x.tuner.width = 10
    d_stage.x.tuner.width = 10

    if monochromator.dcm.energy.get() < 10.99:  # ~ 10 keV for Si 220 crystals
        m_stage.r.tuner.width = 0.003
        a_stage.r.tuner.width = 0.002
        m_stage.r2p.tuner.width = 10
        a_stage.r2p.tuner.width = 7
        ms_stage.rp.tuner.width = 5
        as_stage.rp.tuner.width = 3
        yield from bps.mv(terms.USAXS.usaxs_minstep, 0.000045)

    elif 10.99 <= monochromator.dcm.energy.get() < 12.99:   # Si 220 crystals
        m_stage.r.tuner.width = 0.003
        a_stage.r.tuner.width = 0.0015
        m_stage.r2p.tuner.width = 9
        a_stage.r2p.tuner.width = 5
        ms_stage.rp.tuner.width = 3
        as_stage.rp.tuner.width = 3
        yield from bps.mv(terms.USAXS.usaxs_minstep, 0.000035)

    elif 12.99 <= monochromator.dcm.energy.get() < 18.1:   # Si 220 crystals
        m_stage.r.tuner.width = 0.0030
        a_stage.r.tuner.width = 0.0014
        m_stage.r2p.tuner.width = 8
        a_stage.r2p.tuner.width = 5
        ms_stage.rp.tuner.width = 3
        as_stage.rp.tuner.width = 3
        yield from bps.mv(terms.USAXS.usaxs_minstep, 0.000025)

    elif 18.1 <= monochromator.dcm.energy.get() < 20.8:   # Si 220 crystals
        m_stage.r.tuner.width = 0.0026
        a_stage.r.tuner.width = 0.0012
        m_stage.r2p.tuner.width = 8
        a_stage.r2p.tuner.width = 6
        ms_stage.rp.tuner.width = 3
        as_stage.rp.tuner.width = 3
        yield from bps.mv(terms.USAXS.usaxs_minstep, 0.000025)

    elif 20.8 <= monochromator.dcm.energy.get():   # Si 220 crystals
        m_stage.r.tuner.width = 0.0025
        a_stage.r.tuner.width = 0.0010
        m_stage.r2p.tuner.width = 8
        a_stage.r2p.tuner.width = 5
        ms_stage.rp.tuner.width = 3
        as_stage.rp.tuner.width = 3
        yield from bps.mv(terms.USAXS.usaxs_minstep, 0.000025)


def update_EPICS_tuning_widths():
    """
    plan: update the tuning widths in EPICS PVs from local settings
    """
    yield from bps.mv(
        axis_tune_range.mr,     m_stage.r.tuner.width,
        axis_tune_range.ar,     a_stage.r.tuner.width,
        axis_tune_range.m2rp,   m_stage.r2p.tuner.width,
        axis_tune_range.a2rp,   a_stage.r2p.tuner.width,
        axis_tune_range.msrp,   ms_stage.rp.tuner.width,
        axis_tune_range.asrp,   as_stage.rp.tuner.width,
        axis_tune_range.dx,     d_stage.x.tuner.width,
        axis_tune_range.dy,     d_stage.y.tuner.width,
        )


def user_defined_settings():
    """
    plan: users may redefine this function to override any instrument defaults

    This is called from beforePlan() (in 50-plans.py) at the start of
    every batch set of measurements.  Among the many things a user might
    override could be the default ranges for tuning various optical axes.
    Such as::

        a_stage.r.tuner.width = 0.01

    NOTE:  Don't use blocking calls here

        It is important that the user not use any blocking calls
        such as setting or getting PVs in EPICS.  Blocking calls
        will *block* the python interpreter for long periods
        (such as ``time.sleep()``) or make direct calls
        for EPICS or file I/O that interrupt how the Bluesky
        RunEngine operates.

        It is OK to set local python variables since these do not block.

        Write this routine like any other bluesky plan code,
        using ``yield from bps.mv(...)``,  ``yield from bps.sleep(...)``, ...
    """
    yield from bps.null()
