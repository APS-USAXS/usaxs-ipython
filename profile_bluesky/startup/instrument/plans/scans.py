
"""
user-facing scans
"""

__all__ = """
    preSWAXStune
    preUSAXStune
    SAXS
    USAXSscan
    WAXS
""".split()

from ..session_logs import logger
logger.info(__file__)

from apstools.devices import SCALER_AUTOCOUNT_MODE
from bluesky import plan_stubs as bps
from collections import OrderedDict
import datetime
import os
import time

from ..devices import a_stage, as_stage
from ..devices import apsbss
from ..devices import ar_start
from ..devices import autoscale_amplifiers
from ..devices import ccd_shutter, mono_shutter, ti_filter_shutter
from ..devices import constants
from ..devices import d_stage, s_stage
from ..devices import email_notices, NOTIFY_ON_RESET, NOTIFY_ON_BADTUNE
from ..devices import flyscan_trajectories
from ..devices import guard_slit, usaxs_slit
from ..devices import lax_autosave
from ..devices import m_stage, ms_stage
from ..devices import monochromator, MONO_FEEDBACK_OFF, MONO_FEEDBACK_ON
from ..devices import NOTIFY_ON_BAD_FLY_SCAN
from ..devices import saxs_det
from ..devices import saxs_stage
from ..devices import scaler0, scaler1
from ..devices import struck
from ..devices import terms
from ..devices import upd_controls, I0_controls, I00_controls, trd_controls
from ..devices import usaxs_flyscan
from ..devices import usaxs_q_calc
from ..devices import user_data
from ..devices import waxsx, waxs_det
from ..devices.suspenders import suspend_BeamInHutch
from ..framework import RE, specwriter
from ..framework.metadata import USERNAME
from ..utils.cleanup_text import cleanupText
from .area_detector import areaDetectorAcquire
from .axis_tuning import tune_ar, tune_a2rp, tune_asrp
from .axis_tuning import tune_mr, tune_m2rp, tune_msrp
from .filters import insertSaxsFilters
from .filters import insertWaxsFilters
from .mode_changes import mode_SAXS
from .mode_changes import mode_USAXS
from .mode_changes import mode_WAXS
from .requested_stop import IfRequestedStopBeforeNextScan
from .sample_transmission import measure_SAXS_Transmission
from .sample_transmission import measure_USAXS_Transmission
from .uascan import uascan
from ..utils.a2q_q2a import angle2q, q2angle


def preUSAXStune(md={}):
    """
    tune the USAXS optics *only* if in USAXS mode

    USAGE:  ``RE(preUSAXStune())``
    """
    yield from bps.mv(
        monochromator.feedback.on, MONO_FEEDBACK_ON,
        mono_shutter, "open",
        ccd_shutter, "close",
    )
    yield from IfRequestedStopBeforeNextScan()         # stop if user chose to do so.

    yield from mode_USAXS()

    if terms.preUSAXStune.use_specific_location.get() in (1, "yes"):
        yield from bps.mv(
            s_stage.x, terms.preUSAXStune.sx.get(),
            s_stage.y, terms.preUSAXStune.sy.get(),
            )

    yield from bps.mv(
        # ensure diode in place (Radiography puts it elsewhere)
        d_stage.x, terms.USAXS.diode.dx.get(),
        d_stage.y, terms.USAXS.diode.dy.get(),

        user_data.time_stamp, str(datetime.datetime.now()),
        user_data.state, "pre-USAXS optics tune",

        # Is this covered by user_mode, "USAXS"?
        usaxs_slit.v_size,  terms.SAXS.usaxs_v_size.get(),
        usaxs_slit.h_size,  terms.SAXS.usaxs_h_size.get(),
        guard_slit.v_size,  terms.SAXS.usaxs_guard_v_size.get(),
        guard_slit.h_size,  terms.SAXS.usaxs_guard_h_size.get(),

        scaler0.preset_time,  0.1,
    )
    # when all that is complete, then ...
    yield from bps.mv(ti_filter_shutter, "open")

    # TODO: install suspender using usaxs_CheckBeamStandard.get()

    tuners = OrderedDict()                 # list the axes to tune
    tuners[m_stage.r] = tune_mr            # tune M stage to monochromator
    if not m_stage.isChannelCut:
        tuners[m_stage.r2p] = tune_m2rp        # make M stage crystals parallel
    if terms.USAXS.useMSstage.get():
        tuners[ms_stage.rp] = tune_msrp    # align MSR stage with M stage
    if terms.USAXS.useSBUSAXS.get():
        tuners[as_stage.rp] = tune_asrp    # align ASR stage with MSR stage and set ASRP0 value
    tuners[a_stage.r] = tune_ar            # tune A stage to M stage
    tuners[a_stage.r2p] = tune_a2rp        # make A stage crystals parallel

    # now, tune the desired axes, bail out if a tune fails
    yield from bps.install_suspender(suspend_BeamInHutch)
    for axis, tune in tuners.items():
        yield from bps.mv(ti_filter_shutter, "open")
        yield from tune(md=md)
        if not axis.tuner.tune_ok:
            logger.warning("!!! tune failed for axis %s !!!", axis.name)
            if NOTIFY_ON_BADTUNE:
                email_notices.send(
                    f"USAXS tune failed for axis {axis.name}",
                    f"USAXS tune failed for axis {axis.name}"
                    )

        # If we don't wait, the next tune often fails
        # intensity stays flat, statistically
        # We need to wait a short bit to allow EPICS database
        # to complete processing and report back to us.
        yield from bps.sleep(1)
    yield from bps.remove_suspender(suspend_BeamInHutch)

    logger.info("USAXS count time: {terms.USAXS.usaxs_time.get()} second(s)")
    yield from bps.mv(
        scaler0.preset_time,        terms.USAXS.usaxs_time.get(),
        user_data.time_stamp,       str(datetime.datetime.now()),
        user_data.state,            "pre-USAXS optics tuning done",

        terms.preUSAXStune.num_scans_last_tune, 0,
        terms.preUSAXStune.run_tune_next,       0,
        terms.preUSAXStune.epoch_last_tune,     time.time(),
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def preSWAXStune(md={}):
    """
    tune the SAXS & WAXS optics in any mode, is safe

    USAGE:  ``RE(preSWAXStune())``
    """
    yield from bps.mv(
        monochromator.feedback.on, MONO_FEEDBACK_ON,
        mono_shutter, "open",
        ccd_shutter, "close",
    )
    yield from IfRequestedStopBeforeNextScan()         # stop if user chose to do so.

    if terms.preUSAXStune.use_specific_location.get() in (1, "yes"):
        yield from bps.mv(
            s_stage.x, terms.preUSAXStune.sx.get(),
            s_stage.y, terms.preUSAXStune.sy.get(),
            )

    yield from bps.mv(
        user_data.time_stamp, str(datetime.datetime.now()),
        user_data.state, "pre-SWAXS optics tune",

        scaler0.preset_time,  0.1,
    )
    # when all that is complete, then ...
    yield from bps.mv(ti_filter_shutter, "open")

    # TODO: install suspender using usaxs_CheckBeamStandard.get()

    tuners = OrderedDict()                 # list the axes to tune
    tuners[m_stage.r] = tune_mr            # tune M stage to monochromator
    if not m_stage.isChannelCut:
        tuners[m_stage.r2p] = tune_m2rp        # make M stage crystals parallel
    if terms.USAXS.useMSstage.get():
        tuners[ms_stage.rp] = tune_msrp    # align MSR stage with M stage

    # now, tune the desired axes, bail out if a tune fails
    yield from bps.install_suspender(suspend_BeamInHutch)
    for axis, tune in tuners.items():
        yield from bps.mv(ti_filter_shutter, "open")
        yield from tune(md=md)
        if axis.tuner.tune_ok:
            # If we don't wait, the next tune often fails
            # intensity stays flat, statistically
            # We need to wait a short bit to allow EPICS database
            # to complete processing and report back to us.
            yield from bps.sleep(1)
        else:
            logger.warning("!!! tune failed for axis %s !!!", axis.name)
            # break
    yield from bps.remove_suspender(suspend_BeamInHutch)

    logger.info("USAXS count time: {terms.USAXS.usaxs_time.get()} second(s)")
    yield from bps.mv(
        scaler0.preset_time,        terms.USAXS.usaxs_time.get(),
        user_data.time_stamp,       str(datetime.datetime.now()),
        user_data.state,            "pre-SWAXS optics tuning done",

        terms.preUSAXStune.num_scans_last_tune, 0,
        terms.preUSAXStune.run_tune_next,       0,
        terms.preUSAXStune.epoch_last_tune,     time.time(),
    )


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def USAXSscan(x, y, thickness_mm, title, md=None):
    """
    general scan macro for fly or step USAXS with 1D or 2D collimation
    """
    _md = apsbss.update_MD(md or {})
    _md["sample_thickness_mm"] = thickness_mm
    _md["title"] = title
    if terms.FlyScan.use_flyscan.get():
        yield from Flyscan(x, y, thickness_mm, title, md=_md)
    else:
        yield from USAXSscanStep(x, y, thickness_mm, title, md=_md)


def USAXSscanStep(pos_X, pos_Y, thickness, scan_title, md=None):
    """
    general scan macro for step USAXS for both 1D & 2D collimation
    """
    _md = apsbss.update_MD(md or {})
    _md["sample_thickness_mm"] = thickness
    _md["title"] = scan_title

    from .command_list import after_plan, before_plan

    # bluesky_runengine_running = RE.state != "idle"

    yield from IfRequestedStopBeforeNextScan()

    yield from mode_USAXS()

    yield from bps.mv(
        usaxs_slit.v_size, terms.SAXS.usaxs_v_size.get(),
        usaxs_slit.h_size, terms.SAXS.usaxs_h_size.get(),
        guard_slit.v_size, terms.SAXS.usaxs_guard_v_size.get(),
        guard_slit.h_size, terms.SAXS.usaxs_guard_h_size.get(),
    )
    yield from before_plan()

    yield from bps.mv(
        s_stage.x, pos_X,
        s_stage.y, pos_Y,
    )

    scan_title_clean = cleanupText(scan_title)  # TODO: why unused?

    # SPEC-compatibility symbols
    SCAN_N = RE.md["scan_id"]+1     # the next scan number (user-controllable)
    # use our specwriter to get a pseudo-SPEC file name
    DATAFILE = os.path.split(specwriter.spec_filename)[-1]  # TODO: why unused?

    ts = str(datetime.datetime.now())
    yield from bps.mv(
        user_data.sample_title, scan_title,
        user_data.state, "starting USAXS step scan",
        user_data.sample_thickness, thickness,
        user_data.user_name, USERNAME,
        user_data.spec_scan, str(SCAN_N),
        # or terms.FlyScan.order_number.get()
        user_data.time_stamp, ts,
        user_data.scan_macro, "uascan",    # TODO: is this the right keyword?
    )

    yield from bps.mv(
        user_data.user_dir, os.getcwd(),
        user_data.spec_file, os.path.split(specwriter.spec_filename)[-1],
    )

    # offset the calc from exact zero so can plot log(|Q|)
    # q_offset = terms.USAXS.start_offset.get()
    # angle_offset = q2angle(q_offset, monochromator.dcm.wavelength.get())
    # ar0_calc_offset = terms.USAXS.ar_val_center.get() + angle_offset

    yield from bps.mv(
        a_stage.r, terms.USAXS.ar_val_center.get(),
        # these two were moved by mode_USAXS(), belt & suspenders here
        d_stage.y, terms.USAXS.diode.dy.get(),
        a_stage.y, terms.USAXS.AY0.get(),
    )
    yield from user_data.set_state_plan("Moving to Q=0")
    yield from bps.mv(
        usaxs_q_calc.channels.B.input_value, terms.USAXS.ar_val_center.get(),
    )

    # TODO: what to do with USAXSScanUp?
    # 2019-01-25, prj+jil: this is probably not used now, only known to SPEC
    # it's used to cal Finish_in_Angle and START
    # both of which get passed to EPICS
    # That happens outside of this code.  completely.

    # measure transmission values using pin diode if desired
    yield from bps.install_suspender(suspend_BeamInHutch)
    yield from measure_USAXS_Transmission(md=_md)

    yield from bps.mv(
        monochromator.feedback.on, MONO_FEEDBACK_OFF,
        )

    # enable asrp link to ar for 2D USAXS
    if terms.USAXS.is2DUSAXSscan.get():
        RECORD_SCAN_INDEX_10x_per_second = 9
        yield from bps.mv(terms.FlyScan.asrp_calc_SCAN, RECORD_SCAN_INDEX_10x_per_second)

    # we'll reset these after the scan is done
    old_femto_change_gain_up = upd_controls.auto.gainU.get()
    old_femto_change_gain_down = upd_controls.auto.gainD.get()

    yield from bps.mv(
        upd_controls.auto.gainU, terms.USAXS.setpoint_up.get(),
        upd_controls.auto.gainD, terms.USAXS.setpoint_down.get(),
        ti_filter_shutter, "open",
    )
    yield from autoscale_amplifiers([upd_controls, I0_controls, I00_controls])

    yield from user_data.set_state_plan("Running USAXS step scan")

    SCAN_N = RE.md["scan_id"]+1     # update with next number
    yield from bps.mv(
        terms.FlyScan.order_number, terms.FlyScan.order_number.get() + 1,  # increment it
        user_data.scanning, "scanning",          # we are scanning now (or will be very soon)
        user_data.spec_scan, str(SCAN_N),
    )

    _md['plan_name'] = "uascan"
    _md['plan_args'] = dict(
        pos_X = pos_X,
        pos_Y = pos_Y,
        thickness = thickness,
        scan_title = scan_title,
        )

    startAngle = terms.USAXS.ar_val_center.get()- q2angle(terms.USAXS.start_offset.get(),monochromator.dcm.wavelength.get())
    endAngle = terms.USAXS.ar_val_center.get()-q2angle(terms.USAXS.finish.get(),monochromator.dcm.wavelength.get())
    yield from uascan(
        startAngle,
        terms.USAXS.ar_val_center.get(),
        endAngle,
        terms.USAXS.usaxs_minstep.get(),
        terms.USAXS.uaterm.get(),
        terms.USAXS.num_points.get(),
        terms.USAXS.usaxs_time.get(),
        terms.USAXS.DY0.get(),
        terms.USAXS.SDD.get(),
        terms.USAXS.AY0.get(),
        terms.USAXS.SAD.get(),
        useDynamicTime=True,
        md=_md
    )
    #uascan(
    #    start, reference, finish, minStep,
    #    exponent, intervals, count_time,
    #    dy0, SDD_mm, ay0, SAD_mm,
    #    useDynamicTime=True,
    #    md={}
    #):

    #class Parameters_USAXS(Device):
    #"""internal values shared with EPICS"""
    #AY0 = Component(EpicsSignal,                      "9idcLAX:USAXS:AY0")
    #DY0 = Component(EpicsSignal,                      "9idcLAX:USAXS:DY0")
    #ASRP0 = Component(EpicsSignal,                    "9idcLAX:USAXS:ASRcenter")
    #SAD = Component(EpicsSignal,                      "9idcLAX:USAXS:SAD")
    #SDD = Component(EpicsSignal,                      "9idcLAX:USAXS:SDD")
    #ar_val_center = Component(EpicsSignal,            "9idcLAX:USAXS:ARcenter")
    #asr_val_center = Component(EpicsSignal,           "9idcLAX:USAXS:ASRcenter")
    #asrp_degrees_per_VDC = Component(Signal,          value=(0.000570223 + 0.000585857)/2)
    #center = Component(GeneralUsaxsParametersCenters, "9idcLAX:USAXS:")
    #ccd = Component(GeneralParametersCCD,             "9idcLAX:USAXS:CCD_")
    #diode = Component(GeneralUsaxsParametersDiode,    "9idcLAX:USAXS:")
    #img_filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS:Img_")
    #finish = Component(EpicsSignal,                   "9idcLAX:USAXS:Finish")
    #is2DUSAXSscan = Component(EpicsSignal,            "9idcLAX:USAXS:is2DUSAXSscan")
    #motor_prescaler_wait = Component(EpicsSignal,     "9idcLAX:USAXS:Prescaler_Wait")
    #mr_val_center = Component(EpicsSignal,            "9idcLAX:USAXS:MRcenter")
    #msr_val_center = Component(EpicsSignal,           "9idcLAX:USAXS:MSRcenter")
    #num_points = Component(EpicsSignal,               "9idcLAX:USAXS:NumPoints")
    #sample_y_step = Component(EpicsSignal,            "9idcLAX:USAXS:Sample_Y_Step")
    #scan_filters = Component(Parameters_Al_Ti_Filters, "9idcLAX:USAXS:Scan_")
    #scanning = Component(EpicsSignal,                 "9idcLAX:USAXS:scanning")
    #start_offset = Component(EpicsSignal,             "9idcLAX:USAXS:StartOffset")
    #uaterm = Component(EpicsSignal,                   "9idcLAX:USAXS:UATerm")
    #usaxs_minstep = Component(EpicsSignal,            "9idcLAX:USAXS:MinStep")
    #usaxs_time = Component(EpicsSignal,               "9idcLAX:USAXS:CountTime")
    #useMSstage = Component(Signal,                    value=False)
    #useSBUSAXS = Component(Signal,                    value=False)
    #retune_needed = Component(Signal, value=False)     # does not *need* an EPICS PV
    # TODO: these are particular to the amplifier
    #setpoint_up = Component(Signal, value=4000)     # decrease range
    #setpoint_down = Component(Signal, value=650000)    # increase range

    yield from bps.mv(
        user_data.scanning, "no",          # for sure, we are not scanning now
    )
    yield from bps.remove_suspender(suspend_BeamInHutch)

    yield from user_data.set_state_plan("USAXS step scan finished")

    yield from bps.mv(

        ti_filter_shutter, "close",
        monochromator.feedback.on, MONO_FEEDBACK_ON,

        scaler0.update_rate, 5,
        scaler0.auto_count_delay, 0.25,
        scaler0.delay, 0.05,
        scaler0.preset_time, 1,
        scaler0.auto_count_time, 1,

        upd_controls.auto.gainU, old_femto_change_gain_up,
        upd_controls.auto.gainD, old_femto_change_gain_down,
        )

    yield from user_data.set_state_plan("Moving USAXS back and saving data")
    yield from bps.mv(
        a_stage.r, terms.USAXS.ar_val_center.get(),
        a_stage.y, terms.USAXS.AY0.get(),
        d_stage.y, terms.USAXS.DY0.get(),
        )

    # TODO: make this link for side-bounce
    # disable asrp link to ar for 2D USAXS
    # FS_disableASRP

    # measure_USAXS_PD_dark_currents    # used to be here, not now
    yield from after_plan(weight=3)


def Flyscan(pos_X, pos_Y, thickness, scan_title, md=None):
    """
    do one USAXS Fly Scan
    """
    plan_name = "Flyscan"
    _md = apsbss.update_MD(md or {})
    _md["sample_thickness_mm"] = thickness
    _md["title"] = scan_title

    from .command_list import after_plan, before_plan

    bluesky_runengine_running = RE.state != "idle"

    yield from IfRequestedStopBeforeNextScan()

    yield from mode_USAXS()

    yield from bps.mv(
        usaxs_slit.v_size, terms.SAXS.usaxs_v_size.get(),
        usaxs_slit.h_size, terms.SAXS.usaxs_h_size.get(),
        guard_slit.v_size, terms.SAXS.usaxs_guard_v_size.get(),
        guard_slit.h_size, terms.SAXS.usaxs_guard_h_size.get(),
    )
    yield from before_plan()

    yield from bps.mv(
        s_stage.x, pos_X,
        s_stage.y, pos_Y,
    )

    scan_title_clean = cleanupText(scan_title)

    # SPEC-compatibility symbols
    SCAN_N = RE.md["scan_id"]+1     # the next scan number (user-controllable)
    # use our specwriter to get a pseudo-SPEC file name
    DATAFILE = os.path.split(specwriter.spec_filename)[-1]

    # directory is pwd + DATAFILE + "_usaxs"
    flyscan_path = os.path.join(os.getcwd(), os.path.splitext(DATAFILE)[0] + "_usaxs")
    if not os.path.exists(flyscan_path) and bluesky_runengine_running:
        # must create this directory if not exists
        os.mkdir(flyscan_path)
    flyscan_file_name = (
        f"{scan_title_clean}"
        f"_{plan_name}"
        f"_{terms.FlyScan.order_number.get():04d}"
        ".h5"
    )

    usaxs_flyscan.saveFlyData_HDF5_dir = flyscan_path
    usaxs_flyscan.saveFlyData_HDF5_file = flyscan_file_name

    ts = str(datetime.datetime.now())
    yield from bps.mv(
        user_data.sample_title, scan_title,
        user_data.state, "starting USAXS Flyscan",
        user_data.sample_thickness, thickness,
        user_data.user_name, USERNAME,
        user_data.spec_scan, str(SCAN_N),
        # or terms.FlyScan.order_number.get()
        user_data.time_stamp, ts,
        user_data.scan_macro, "FlyScan",    # note camel-case
    )
    yield from bps.mv(
        user_data.user_dir, os.getcwd(),
        user_data.spec_file, os.path.split(specwriter.spec_filename)[-1],
    )

    # offset the calc from exact zero so can plot log(|Q|)
    # q_offset = terms.USAXS.start_offset.get()
    # angle_offset = q2angle(q_offset, monochromator.dcm.wavelength.get())
    # ar0_calc_offset = terms.USAXS.ar_val_center.get() + angle_offset

    yield from bps.mv(
        a_stage.r, terms.USAXS.ar_val_center.get(),
        # these two were moved by mode_USAXS(), belt & suspenders here
        d_stage.y, terms.USAXS.diode.dy.get(),
        a_stage.y, terms.USAXS.AY0.get(),
    )
    yield from user_data.set_state_plan("Moving to Q=0")
    yield from bps.mv(
        usaxs_q_calc.channels.B.input_value, terms.USAXS.ar_val_center.get(),
    )

    # TODO: what to do with USAXSScanUp?
    # 2019-01-25, prj+jil: this is probably not used now, only known to SPEC
    # it's used to cal Finish_in_Angle and START
    # both of which get passed to EPICS
    # That happens outside of this code.  completely.

    # measure transmission values using pin diode if desired
    usaxs_flyscan.saveFlyData_HDF5_dir = flyscan_path
    usaxs_flyscan.saveFlyData_HDF5_file = flyscan_file_name
    yield from bps.install_suspender(suspend_BeamInHutch)
    yield from measure_USAXS_Transmission(md=_md)

    yield from bps.mv(
        monochromator.feedback.on, MONO_FEEDBACK_OFF,
        )

    # enable asrp link to ar for 2D USAXS
    if terms.USAXS.is2DUSAXSscan.get():
        RECORD_SCAN_INDEX_10x_per_second = 9
        yield from bps.mv(terms.FlyScan.asrp_calc_SCAN, RECORD_SCAN_INDEX_10x_per_second)

    # we'll reset these after the scan is done
    old_femto_change_gain_up = upd_controls.auto.gainU.get()
    old_femto_change_gain_down = upd_controls.auto.gainD.get()

    yield from bps.mv(
        upd_controls.auto.gainU, terms.FlyScan.setpoint_up.get(),
        upd_controls.auto.gainD, terms.FlyScan.setpoint_down.get(),
        ti_filter_shutter, "open",
    )
    yield from autoscale_amplifiers([upd_controls, I0_controls, I00_controls])


    FlyScanAutoscaleTime = 0.025
    yield from bps.mv(
        scaler0.update_rate, 0,
        scaler0.auto_count_update_rate, 0,
        upd_controls.auto.mode, "auto+background",
        scaler0.preset_time, FlyScanAutoscaleTime,
        scaler0.auto_count_time, FlyScanAutoscaleTime,
        scaler0.auto_count_delay, FlyScanAutoscaleTime,
        scaler0.delay, 0,
        scaler0.count_mode, SCALER_AUTOCOUNT_MODE,
        )

   # Pause autosave on LAX to prevent delays in PVs processing.
    yield from bps.mv(
        lax_autosave.disable, 1,
        # autosave will restart after this interval (s)
        lax_autosave.max_time, usaxs_flyscan.scan_time.get()+9,
        )

    yield from user_data.set_state_plan("Running Flyscan")

    ### move the stages to flyscan starting values from EPICS PVs
    yield from bps.mv(
        a_stage.r, flyscan_trajectories.ar.get()[0],
        a_stage.y, flyscan_trajectories.ay.get()[0],
        d_stage.y, flyscan_trajectories.dy.get()[0],
        ar_start, flyscan_trajectories.ar.get()[0],
        # ay_start, flyscan_trajectories.ay.get()[0],
        # dy_start, flyscan_trajectories.dy.get()[0],
    )

    SCAN_N = RE.md["scan_id"]+1     # update with next number
    yield from bps.mv(
        terms.FlyScan.order_number, terms.FlyScan.order_number.get() + 1,  # increment it
        user_data.scanning, "scanning",          # we are scanning now (or will be very soon)
        user_data.spec_scan, str(SCAN_N),
    )

    _md = {}
    _md.update(md)
    _md['plan_name'] = plan_name
    _md['plan_args'] = dict(
        pos_X = pos_X,
        pos_Y = pos_Y,
        thickness = thickness,
        scan_title = scan_title,
        )
    _md['fly_scan_time'] = usaxs_flyscan.scan_time.get()
        #'detectors': [det.name for det in detectors],
        #'num_points': num,
        #'num_intervals': num_intervals,
        #'hints': {}

    yield from usaxs_flyscan.plan(md=_md)        # DO THE FLY SCAN

    yield from bps.mv(
        user_data.scanning, "no",          # for sure, we are not scanning now
        terms.FlyScan.elapsed_time, 0,  # show the users there is no more time
    )
    yield from bps.remove_suspender(suspend_BeamInHutch)

    # Check if we had bad number of PSO pulses
    diff = flyscan_trajectories.num_pulse_positions.get() - struck.current_channel.get()
    if diff > 5 and bluesky_runengine_running:
        msg = "WARNING: Flyscan finished with %g less points" % diff
        logger.warning(msg)
        if NOTIFY_ON_BAD_FLY_SCAN:
            subject = "!!! bad number of PSO pulses !!!"
            email_notices.send(subject, msg)

    yield from user_data.set_state_plan("Flyscan finished")

    yield from bps.mv(
        lax_autosave.disable, 0,    # enable
        lax_autosave.max_time, 0,   # start right away

        ti_filter_shutter, "close",
        monochromator.feedback.on, MONO_FEEDBACK_ON,

        scaler0.update_rate, 5,
        scaler0.auto_count_delay, 0.25,
        scaler0.delay, 0.05,
        scaler0.preset_time, 1,
        scaler0.auto_count_time, 1,

        upd_controls.auto.gainU, old_femto_change_gain_up,
        upd_controls.auto.gainD, old_femto_change_gain_down,
        )

    yield from user_data.set_state_plan("Moving USAXS back and saving data")
    yield from bps.mv(
        a_stage.r, terms.USAXS.ar_val_center.get(),
        a_stage.y, terms.USAXS.AY0.get(),
        d_stage.y, terms.USAXS.DY0.get(),
        )

    # TODO: make this link for side-bounce
    # disable asrp link to ar for 2D USAXS
    # FS_disableASRP

    # measure_USAXS_PD_dark_currents    # used to be here, not now
    yield from after_plan(weight=3)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def SAXS(pos_X, pos_Y, thickness, scan_title, md=None):
    """
    collect SAXS data
    """
    _md = apsbss.update_MD(md or {})
    _md["sample_thickness_mm"] = thickness
    _md["title"] = scan_title

    from .command_list import after_plan, before_plan

    yield from IfRequestedStopBeforeNextScan()

    yield from before_plan()    # MUST come before mode_SAXS since it might tune

    yield from mode_SAXS()

    pinz_target = terms.SAXS.z_in.get() + constants["SAXS_PINZ_OFFSET"]
    yield from bps.mv(
        usaxs_slit.v_size, terms.SAXS.v_size.get(),
        usaxs_slit.h_size, terms.SAXS.h_size.get(),
        guard_slit.v_size, terms.SAXS.guard_v_size.get(),
        guard_slit.h_size, terms.SAXS.guard_h_size.get(),
        saxs_stage.z, pinz_target,      # MUST move before sample stage moves!
        user_data.sample_thickness, thickness,
        terms.SAXS.collecting, 1,
    )

    yield from bps.mv(
        s_stage.x, pos_X,
        s_stage.y, pos_Y,
    )

    scan_title_clean = cleanupText(scan_title)

    # SPEC-compatibility symbols
    SCAN_N = RE.md["scan_id"]+1     # the next scan number (user-controllable)
    # use our specwriter to get a pseudo-SPEC file name
    DATAFILE = os.path.split(specwriter.spec_filename)[-1]

    # these two templates match each other, sort of
    ad_file_template = "%s%s_%4.4d.hdf"
    local_file_template = "%s_%04d.hdf"

    # directory is pwd + DATAFILE + "_usaxs"
    # path on local file system
    SAXSscan_path = os.path.join(os.getcwd(), os.path.splitext(DATAFILE)[0] + "_saxs")
    SAXS_file_name = local_file_template % (scan_title_clean, saxs_det.hdf1.file_number.get())
    # NFS-mounted path as the Pilatus detector sees it
    pilatus_path = os.path.join("/mnt/usaxscontrol", *SAXSscan_path.split(os.path.sep)[2:])
    # area detector will create this path if needed ("Create dir. depth" setting)
    if not pilatus_path.endswith("/"):
        pilatus_path += "/"        # area detector needs this
    local_name = os.path.join(SAXSscan_path, SAXS_file_name)
    logger.info(f"Area Detector HDF5 file: {local_name}")
    pilatus_name = os.path.join(pilatus_path, SAXS_file_name)
    logger.info(f"Pilatus computer Area Detector HDF5 file: {pilatus_name}")

    yield from bps.mv(
        saxs_det.hdf1.file_name, scan_title_clean,
        saxs_det.hdf1.file_path, pilatus_path,
        saxs_det.hdf1.file_template, ad_file_template,
    )

    ts = str(datetime.datetime.now())
    yield from bps.mv(
        user_data.sample_title, scan_title,
        user_data.state, "starting SAXS collection",
        user_data.sample_thickness, thickness,
        user_data.user_name, USERNAME,
        user_data.spec_scan, str(SCAN_N),
        user_data.time_stamp, ts,
        user_data.scan_macro, "SAXS",       # match the value in the scan logs
    )
    yield from bps.mv(
        user_data.user_dir, os.getcwd(),        # TODO: watch out for string too long for EPICS! (make it an EPICS waveform string)
        user_data.spec_file, os.path.split(specwriter.spec_filename)[-1],
   )

    yield from bps.install_suspender(suspend_BeamInHutch)
    yield from measure_SAXS_Transmission()
    yield from insertSaxsFilters()

    yield from bps.mv(
        mono_shutter, "open",
        monochromator.feedback.on, MONO_FEEDBACK_OFF,
        ti_filter_shutter, "open",
        saxs_det.cam.num_images, terms.SAXS.num_images.get(),
        saxs_det.cam.acquire_time, terms.SAXS.acquire_time.get(),
        saxs_det.cam.acquire_period, terms.SAXS.acquire_time.get() + 0.004,
    )
    old_det_stage_sigs = OrderedDict()
    for k, v in saxs_det.hdf1.stage_sigs.items():
        old_det_stage_sigs[k] = v
    if saxs_det.hdf1.stage_sigs.get("capture") is not None:
        del saxs_det.hdf1.stage_sigs["capture"]
    saxs_det.hdf1.stage_sigs["file_template"] = ad_file_template
    saxs_det.hdf1.stage_sigs["file_write_mode"] = "Single"
    saxs_det.hdf1.stage_sigs["blocking_callbacks"] = "No"

    yield from bps.sleep(0.2)
    yield from autoscale_amplifiers([I0_controls])

    yield from bps.mv(
        ti_filter_shutter, "close",
    )

    SCAN_N = RE.md["scan_id"]+1     # update with next number
    old_delay = scaler0.delay.get()
    yield from bps.mv(
        scaler1.preset_time, terms.SAXS.acquire_time.get() + 1,
        scaler0.preset_time, 1.2*terms.SAXS.acquire_time.get() + 1,
        scaler0.count_mode, "OneShot",
        scaler1.count_mode, "OneShot",

        # update as fast as hardware will allow
        # this is needed to make sure we get as up to date I0 number as possible for AD software.
        scaler0.display_rate, 60,
        scaler1.display_rate, 60,

        scaler0.delay, 0,
        terms.SAXS_WAXS.start_exposure_time, ts,
        user_data.state, f"SAXS collection for {terms.SAXS.acquire_time.get()} s",
        user_data.spec_scan, str(SCAN_N),
    )

    yield from bps.mv(
        scaler0.count, 1,
        scaler1.count, 1,
    )

    _md['plan_name'] = "SAXS"
    _md["hdf5_file"] = SAXS_file_name
    _md["hdf5_path"] = SAXSscan_path

    yield from areaDetectorAcquire(saxs_det, md=_md)
    ts = str(datetime.datetime.now())
    yield from bps.remove_suspender(suspend_BeamInHutch)

    saxs_det.hdf1.stage_sigs = old_det_stage_sigs    # TODO: needed? not even useful?

    yield from bps.mv(
        scaler0.count, 0,
        scaler1.count, 0,
        terms.SAXS_WAXS.I0, scaler1.channels.chan02.s.get(),
        scaler0.display_rate, 5,
        scaler1.display_rate, 5,
        terms.SAXS_WAXS.end_exposure_time, ts,
        scaler0.delay, old_delay,

        terms.SAXS.collecting, 0,
        user_data.state, "Done SAXS",
        user_data.time_stamp, ts,
    )
    logger.info(f"I0 value: {terms.SAXS_WAXS.I0.get()}")
    yield from after_plan()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def WAXS(pos_X, pos_Y, thickness, scan_title, md=None):
    """
    collect WAXS data
    """
    _md = apsbss.update_MD(md or {})
    _md["sample_thickness_mm"] = thickness
    _md["title"] = scan_title

    from .command_list import after_plan, before_plan

    yield from IfRequestedStopBeforeNextScan()

    logger.debug(f"waxsx start collection ={waxsx.position}")

    yield from before_plan()    # MUST come before mode_WAXS since it might tune

    logger.debug(f"waxsx after before plan ={waxsx.position}")

    yield from mode_WAXS()

    logger.debug(f"waxsx after mode_WAXS ={waxsx.position}")

    yield from bps.mv(
        usaxs_slit.v_size, terms.SAXS.v_size.get(),
        usaxs_slit.h_size, terms.SAXS.h_size.get(),
        guard_slit.v_size, terms.SAXS.guard_v_size.get(),
        guard_slit.h_size, terms.SAXS.guard_h_size.get(),
        user_data.sample_thickness, thickness,
        terms.WAXS.collecting, 1,
    )

    yield from bps.mv(
        s_stage.x, pos_X,
        s_stage.y, pos_Y,
    )

    scan_title_clean = cleanupText(scan_title)

    # SPEC-compatibility symbols
    SCAN_N = RE.md["scan_id"]+1     # the next scan number (user-controllable)
    # use our specwriter to get a pseudo-SPEC file name
    DATAFILE = os.path.split(specwriter.spec_filename)[-1]

    # these two templates match each other, sort of
    ad_file_template = "%s%s_%4.4d.hdf"
    local_file_template = "%s_%04d.hdf"

    # directory is pwd + DATAFILE + "_usaxs"
    # path on local file system
    WAXSscan_path = os.path.join(os.getcwd(), os.path.splitext(DATAFILE)[0] + "_waxs")
    WAXS_file_name = local_file_template % (scan_title_clean, waxs_det.hdf1.file_number.get())
    # NFS-mounted path as the Pilatus detector sees it
    pilatus_path = os.path.join("/mnt/usaxscontrol", *WAXSscan_path.split(os.path.sep)[2:])
    # area detector will create this path if needed ("Create dir. depth" setting)
    if not pilatus_path.endswith("/"):
        pilatus_path += "/"        # area detector needs this
    local_name = os.path.join(WAXSscan_path, WAXS_file_name)
    logger.info(f"Area Detector HDF5 file: {local_name}")
    pilatus_name = os.path.join(pilatus_path, WAXS_file_name)
    logger.info(f"Pilatus computer Area Detector HDF5 file: {pilatus_name}")

    yield from bps.mv(
        waxs_det.hdf1.file_name, scan_title_clean,
        waxs_det.hdf1.file_path, pilatus_path,
        waxs_det.hdf1.file_template, ad_file_template,
    )

    ts = str(datetime.datetime.now())
    yield from bps.mv(
        user_data.sample_title, scan_title,
        user_data.state, "starting WAXS collection",
        user_data.sample_thickness, thickness,
        user_data.user_name, USERNAME,
        user_data.spec_scan, str(SCAN_N),
        user_data.time_stamp, ts,
        user_data.scan_macro, "WAXS",       # match the value in the scan logs
    )
    yield from bps.mv(
        user_data.user_dir, os.getcwd(),        # TODO: watch out for string too long for EPICS! (make it an EPICS waveform string)
        user_data.spec_file, os.path.split(specwriter.spec_filename)[-1],
   )

    #yield from measure_SAXS_Transmission()
    yield from insertWaxsFilters()

    yield from bps.mv(
        mono_shutter, "open",
        monochromator.feedback.on, MONO_FEEDBACK_OFF,
        ti_filter_shutter, "open",
        waxs_det.cam.num_images, terms.WAXS.num_images.get(),
        waxs_det.cam.acquire_time, terms.WAXS.acquire_time.get(),
        waxs_det.cam.acquire_period, terms.WAXS.acquire_time.get() + 0.004,
    )
    yield from bps.install_suspender(suspend_BeamInHutch)
    old_det_stage_sigs = OrderedDict()
    for k, v in waxs_det.hdf1.stage_sigs.items():
        old_det_stage_sigs[k] = v
    if waxs_det.hdf1.stage_sigs.get("capture") is not None:
        del waxs_det.hdf1.stage_sigs["capture"]
    waxs_det.hdf1.stage_sigs["file_template"] = ad_file_template
    waxs_det.hdf1.stage_sigs["file_write_mode"] = "Single"
    waxs_det.hdf1.stage_sigs["blocking_callbacks"] = "No"

    yield from bps.sleep(0.2)
    yield from autoscale_amplifiers([I0_controls, trd_controls])

    yield from bps.mv(
        ti_filter_shutter, "close",
    )

    old_delay = scaler0.delay.get()
    yield from bps.mv(
        scaler1.preset_time, terms.WAXS.acquire_time.get() + 1,
        scaler0.preset_time, 1.2*terms.WAXS.acquire_time.get() + 1,
        scaler0.count_mode, "OneShot",
        scaler1.count_mode, "OneShot",

        # update as fast as hardware will allow
        # this is needed to make sure we get as up to date I0 number as possible for AD software.
        scaler0.display_rate, 60,
        scaler1.display_rate, 60,

        scaler0.delay, 0,
        terms.SAXS_WAXS.start_exposure_time, ts,
        user_data.state, f"WAXS collection for {terms.WAXS.acquire_time.get()} s",
    )

    yield from bps.mv(
        scaler0.count, 1,
        scaler1.count, 1,
    )

    _md['plan_name'] = "WAXS"
    _md["hdf5_file"] = WAXS_file_name
    _md["hdf5_path"] = WAXSscan_path

    logger.debug(f"waxsx before Image collection={waxsx.position}")

    yield from areaDetectorAcquire(waxs_det, md=_md)
    ts = str(datetime.datetime.now())

    waxs_det.hdf1.stage_sigs = old_det_stage_sigs    # TODO: needed? not even useful?

    yield from bps.mv(
        scaler0.count, 0,
        scaler1.count, 0,
        # WAXS uses same PVs for normalization and transmission as SAXS, should we aliased it same to terms.WAXS???
        terms.SAXS_WAXS.I0, scaler1.channels.chan02.s.get(),
        terms.SAXS_WAXS.diode_transmission, scaler0.channels.chan04.s.get(),
        terms.SAXS_WAXS.diode_gain, trd_controls.femto.gain.get(),
        terms.SAXS_WAXS.I0_transmission, scaler0.channels.chan02.s.get(),
        terms.SAXS_WAXS.I0_gain, I0_controls.femto.gain.get(),
        scaler0.display_rate, 5,
        scaler1.display_rate, 5,
        terms.SAXS_WAXS.end_exposure_time, ts,
        scaler0.delay, old_delay,

        terms.WAXS.collecting, 0,
        user_data.state, "Done WAXS",
        user_data.time_stamp, ts,
    )
    yield from bps.remove_suspender(suspend_BeamInHutch)
    logger.info(f"I0 value: {terms.SAXS_WAXS.I0.get()}")
    yield from after_plan()
