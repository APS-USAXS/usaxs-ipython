from ipykernel.tests.test_connect import sample_info
print(__file__)

# Bluesky plans (scans)


def uascan():
    """
    USAXS step scan

    https://github.com/APS-USAXS/ipython-usaxs/issues/8
    """
    # TODO: needs proper args & kwargs matching SPEC's signature


def preUSAXStune():
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

    yield from bps.mv(
        # ensure diode in place (Radiography puts it elsewhere)
        d_stage.x, terms.USAXS.diode.dx.value,
        d_stage.y, terms.USAXS.diode.dy.value,

        user_data.time_stamp, str(datetime.datetime.now()),
        user_data.state, "pre-USAXS optics tune",

        # Is this covered by user_mode, "USAXS"?
        usaxs_slit.v_size,  terms.SAXS.usaxs_v_size.value,
        usaxs_slit.h_size,  terms.SAXS.usaxs_h_size.value,
        guard_slit.v_size,  terms.SAXS.usaxs_guard_v_size.value,
        guard_slit.h_size,  terms.SAXS.usaxs_guard_h_size.value,

        scaler0.preset_time,  0.1,
    )
    # when all that is complete, then ...
    yield from bps.mv(ti_filter_shutter, "open")

    # TODO: install suspender using usaxs_CheckBeamStandard.value

    tuners = OrderedDict()                 # list the axes to tune
    tuners[m_stage.r] = tune_mr            # tune M stage to monochromator
    tuners[m_stage.r2p] = tune_m2rp        # make M stage crystals parallel
    if terms.USAXS.useMSstage.value:
        tuners[ms_stage.rp] = tune_msrp    # align MSR stage with M stage
    if terms.USAXS.useSBUSAXS.value:
        tuners[as_stage.rp] = tune_asrp    # align ASR stage with MSR stage and set ASRP0 value
    tuners[a_stage.r] = tune_ar            # tune A stage to M stage
    tuners[a_stage.r2p] = tune_a2rp        # make A stage crystals parallel

    # now, tune the desired axes, bail out if a tune fails
    for axis, tune in tuners.items():
        yield from bps.mv(ti_filter_shutter, "open")
        yield from tune()
        if axis.tuner.tune_ok:
            # If we don't wait, the next tune often fails
            # intensity stays flat, statistically
            # TODO: Why is that?
            yield from bps.sleep(1)
        else:
            print("!!! tune failed for axis {} !!!".format(axis.name))
            break

    print("USAXS count time: {} second(s)".format(terms.USAXS.usaxs_time.value))
    yield from bps.mv(
        scaler0.preset_time,        terms.USAXS.usaxs_time.value,
        user_data.time_stamp,       str(datetime.datetime.now()),
        user_data.state,            "pre-USAXS optics tuning done",

        terms.preUSAXStune.num_scans_last_tune, 0,
        terms.preUSAXStune.run_tune_next,       0,
        terms.preUSAXStune.epoch_last_tune,     time.time(),
    )


def Flyscan(pos_X, pos_Y, thickness, scan_title):
    """
    do one USAXS Fly Scan
    """
    yield from IfRequestedStopBeforeNextScan()

    yield from mode_USAXS()

    yield from bps.mv(
        usaxs_slit.v_size, terms.SAXS.usaxs_v_size.value,
        usaxs_slit.h_size, terms.SAXS.usaxs_h_size.value,
        guard_slit.v_size, terms.SAXS.usaxs_guard_v_size.value,
        guard_slit.h_size, terms.SAXS.usaxs_guard_h_size.value,
    )

    if terms.preUSAXStune.needed:
        # tune at previous sample position 
        # don't overexpose the new sample position
        yield from tune_usaxs_optics()

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
    if not os.path.exists(flyscan_path):
        # must create this directory if not exists
        os.mkdir(flyscan_path)
    flyscan_file_name = "%s_%04d.h5" % (scan_title_clean, terms.FlyScan.order_number.value)
    # flyscan_full_filename = os.path.join(flyscan_path, flyscan_file_name)

    usaxs_flyscan.saveFlyData_HDF5_dir = flyscan_path
    usaxs_flyscan.saveFlyData_HDF5_file = flyscan_file_name

    ts = str(datetime.datetime.now())
    yield from bps.mv(
        user_data.sample_title, scan_title,
        user_data.macro_file_time, ts,      # does not really apply to bluesky
        user_data.state, "starting USAXS Flyscan",
        user_data.sample_thickness, thickness,
        user_data.user_name, USERNAME,
        user_data.spec_scan, SCAN_N,
        # or terms.FlyScan.order_number.value
        user_data.time_stamp, ts,
        user_data.scan_macro, "FlyScan",    # note camel-case
    )
    yield from bps.mv(
        user_data.user_dir, os.getcwd(),        # TODO: watch out for string too long for EPICS! (make it an EPICS waveform string)
        user_data.spec_file, os.path.split(specwriter.spec_filename)[-1],
   )

    # offset the calc from exact zero so can plot log(|Q|)
    q_offset = terms.USAXS.start_offset.value
    angle_offset = q2angle(q_offset, monochromator.dcm.wavelength.value)
    ar0_calc_offset = terms.USAXS.ar_val_center.value + angle_offset

    print("DEBUG: preparing to move AR, AY, & DY")
    yield from bps.mv(
        a_stage.r, terms.USAXS.ar_val_center.value,
        # these two were moved by mode_USAXS(), belt & suspenders here
        d_stage.y, terms.USAXS.diode.dy.value,
        a_stage.y, terms.USAXS.AY0.value,
    )
    print("DEBUG: setting state")
    yield from user_data.set_state_plan("Moving to Q=0")
    print("DEBUG: setting Q calc AR0 (channel B)")
    yield from bps.mv(
        usaxs_q_calc.channels.B.value, terms.USAXS.ar_val_center.value,
    )
    print("DEBUG: moved AR, AY & DY")

    # TODO: what to do with USAXSScanUp?
    # 2019-01-25, prj+jil: this is probably not used now, only known to SPEC
    # it's used to cal Finish_in_Angle and START
    # both of which get passed to EPICS
    # That happens outside of this code.  completely.

    # measure transmission values using pin diode if desired

    usaxs_flyscan.saveFlyData_HDF5_dir = flyscan_path
    usaxs_flyscan.saveFlyData_HDF5_file = flyscan_file_name
    yield from measure_USAXS_Transmission()
    print("DEBUG: measure transmission done")

    yield from bps.mv(
        mono_shutter, "open",
        monochromator.feedback.on, MONO_FEEDBACK_OFF,
        )
    print("DEBUG: mono shutter opened")

    # enable asrp link to ar for 2D USAXS
    if terms.USAXS.is2DUSAXSscan.value:
        RECORD_SCAN_INDEX_10x_per_second = 9
        yield from bps.mv(terms.FlyScan.asrp_calc_SCAN, RECORD_SCAN_INDEX_10x_per_second)

    # we'll reset these after the scan is done
    old_femto_change_gain_up = upd_controls.auto.gainU.value
    old_femto_change_gain_down = upd_controls.auto.gainD.value

    yield from bps.mv(
        upd_controls.auto.gainU, terms.FlyScan.setpoint_up.value,
        upd_controls.auto.gainD, terms.FlyScan.setpoint_down.value,
        ti_filter_shutter, "open",
    )
    yield from bps.sleep(0.2)
    APS_plans.run_blocker_in_plan(
        # must run in thread since this is not a plan
        autoscale_amplifiers([upd_controls, I0_controls, I00_controls])
    )
    print("DEBUG: amplifiers autoscaled")

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
    print("DEBUG: scalers configured")

   # Pause autosave on LAX to prevent delays in PVs processing.
    yield from bps.mv(
        lax_autosave.disable, 1,
        # autosave will restart after this interval (s)
        lax_autosave.max_time, usaxs_flyscan.scan_time.value+9,
        )
    print("DEBUG: autosave off on LAX")

    yield from user_data.set_state_plan("Running Flyscan")

    ### move the stages to flyscan starting values from EPICS PVs
    yield from bps.mv(
        a_stage.r, flyscan_trajectories.ar.value[0],
        a_stage.y, flyscan_trajectories.ay.value[0],
        d_stage.y, flyscan_trajectories.dy.value[0],
        ar_start, flyscan_trajectories.ar.value[0],
        # ay_start, flyscan_trajectories.ay.value[0],
        # dy_start, flyscan_trajectories.dy.value[0],
    )
    print("DEBUG: moved motors to start position")

    yield from bps.mv(
        terms.FlyScan.order_number, terms.FlyScan.order_number.value + 1,  # increment it
        user_data.scanning, 1,          # we are scanning now (or will be very soon)
    )

    print("DEBUG: starting fly scan")
    yield from usaxs_flyscan.plan()        # DO THE FLY SCAN
    print("DEBUG: done with fly scan")

    yield from bps.mv(
        user_data.scanning, 0,          # for sure, we are not scanning now
        terms.FlyScan.elapsed_time, 0,  # show the users there is no more time
    )

    # Check if we had bad number of PSO pulses
    diff = flyscan_trajectories.num_pulse_positions.value - struck.current_channel.value
    if diff > 5:
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
        a_stage.r, terms.USAXS.ar_val_center.value,
        a_stage.y, terms.USAXS.AY0.value,
        d_stage.y, terms.USAXS.DY0.value,
        )

    # TODO: make this link for side-bounce
    # disable asrp link to ar for 2D USAXS
    # FS_disableASRP

    # measure_USAXS_PD_dark_currents    # used to be here, not now


def my_Excel_plan(xl_file):
    """
    example of reading a list of samples from Excel spreadsheet
    
    TEXT view of spreadsheet (Excel file line numbers shown)::
    
        [1] List of sample scans to be run              
        [2]                 
        [3]                 
        [4] scan    sx  sy  thickness   sample name
        [5] FlyScan 0   0   0   blank
        [6] FlyScan 5   2   0   blank

    """
    assert os.path.exists(xl_file)
    xl = ExcelDatabaseFileGeneric(os.path.abspath(xl_file))
    for row in xl.db.values():
        if row["scan"].lower() == "flyscan":
            yield from Flyscan(row["sx"], row["sy"], row["thickness"], row["sample name"]) 
