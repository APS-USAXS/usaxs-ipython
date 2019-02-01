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

    yield from bps.mv(
        a_stage.r, terms.USAXS.ar_val_center.value,
        # these two were moved by mode_USAXS(), belt & suspenders here
        d_stage.y, terms.USAXS.diode.dy.value,
        a_stage.y, terms.USAXS.AY0.value,
    )
    yield from user_data.set_state_plan("Moving to Q=0")
    yield from bps.mv(
        usaxs_q_calc.channels.B.value, terms.USAXS.ar_val_center.value,
    )

    # TODO: what to do with USAXSScanUp?
    # 2019-01-25, prj+jil: this is probably not used now, only known to SPEC
    # it's used to cal Finish_in_Angle and START
    # both of which get passed to EPICS
    # That happens outside of this code.  completely.

    # measure transmission values using pin diode if desired
    usaxs_flyscan.saveFlyData_HDF5_dir = flyscan_path
    usaxs_flyscan.saveFlyData_HDF5_file = flyscan_file_name
    yield from measure_USAXS_Transmission()

    yield from bps.mv(
        mono_shutter, "open",
        monochromator.feedback.on, MONO_FEEDBACK_OFF,
        )

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
        lax_autosave.max_time, usaxs_flyscan.scan_time.value+9,
        )

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

    yield from bps.mv(
        terms.FlyScan.order_number, terms.FlyScan.order_number.value + 1,  # increment it
        user_data.scanning, "scanning",          # we are scanning now (or will be very soon)
    )

    yield from usaxs_flyscan.plan()        # DO THE FLY SCAN

    yield from bps.mv(
        user_data.scanning, "no",          # for sure, we are not scanning now
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
    xl = APS_utils.ExcelDatabaseFileGeneric(os.path.abspath(xl_file))
    for row in xl.db.values():
        if row["scan"].lower() == "flyscan":
            yield from Flyscan(row["sx"], row["sy"], row["thickness"], row["sample name"]) 


def SAXS(pos_X, pos_Y, thickness, scan_title):
    """
    collect SAXS data
     """
    yield from IfRequestedStopBeforeNextScan()

    yield from mode_SAXS()

    pinz_target = terms.SAXS.z_in.value + constants["SAXS_PINZ_OFFSET"]
    yield from bps.mv(
        usaxs_slit.v_size, terms.SAXS.v_size.value,
        usaxs_slit.h_size, terms.SAXS.h_size.value,
        guard_slit.v_size, terms.SAXS.guard_v_size.value,
        guard_slit.h_size, terms.SAXS.guard_h_size.value,
        saxs_stage.z, pinz_target,      # MUST move before sample stage moves!
    )

    if terms.preUSAXStune.needed:
        # tune at previous sample position 
        # don't overexpose the new sample position
        yield from tune_saxs_optics()

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
    SAXS_file_name = local_file_template % (scan_title_clean, saxs_det.hdf1.file_number.value)
    # NFS-mounted path as the Pilatus detector sees it
    pilatus_path = os.path.join("/mnt/usaxscontrol", *SAXSscan_path.split(os.path.sep)[2:])
    # area detector will create this path if needed ("Create dir. depth" setting)
    if not pilatus_path.endswith("/"):
        pilatus_path += "/"        # area detector needs this
    local_name = os.path.join(SAXSscan_path, SAXS_file_name)
    print(f"Area Detector HDF5 file: {local_name}")
    pilatus_name = os.path.join(pilatus_path, SAXS_file_name)
    print(f"Pilatus computer Area Detector HDF5 file: {pilatus_name}")
    
    yield from bps.mv(
        saxs_det.hdf1.file_name, scan_title_clean,
        saxs_det.hdf1.file_path, pilatus_path,
        saxs_det.hdf1.file_template, ad_file_template,
    )

    ts = str(datetime.datetime.now())
    yield from bps.mv(
        user_data.sample_title, scan_title,
        user_data.macro_file_time, ts,      # does not really apply to bluesky
        user_data.state, "starting SAXS collection",
        user_data.sample_thickness, thickness,
        user_data.user_name, USERNAME,
        user_data.spec_scan, SCAN_N,
        user_data.time_stamp, ts,
        user_data.scan_macro, "SAXS",       # match the value in the scan logs
    )
    yield from bps.mv(
        user_data.user_dir, os.getcwd(),        # TODO: watch out for string too long for EPICS! (make it an EPICS waveform string)
        user_data.spec_file, os.path.split(specwriter.spec_filename)[-1],
   )

    yield from measure_SAXS_Transmission()
    yield from insertSaxsFilters()

    yield from bps.mv(
        mono_shutter, "open",
        monochromator.feedback.on, MONO_FEEDBACK_OFF,
        ti_filter_shutter, "open",
        saxs_det.cam.num_images, terms.SAXS.num_images.value,
        saxs_det.cam.acquire_time, terms.SAXS.acquire_time.value,
        saxs_det.cam.acquire_period, terms.SAXS.acquire_time.value + 0.004,
    )
    # print(f"DEBUG: SAXS(1): {saxs_det.hdf1.stage_sigs}")
    old_det_stage_sigs = OrderedDict()
    for k, v in saxs_det.hdf1.stage_sigs.items():
        old_det_stage_sigs[k] = v
    del saxs_det.hdf1.stage_sigs["capture"]
    saxs_det.hdf1.stage_sigs["file_template"] = ad_file_template
    saxs_det.hdf1.stage_sigs["file_write_mode"] = "Single"
    saxs_det.hdf1.stage_sigs["blocking_callbacks"] = "No"
    # print(f"DEBUG: SAXS(2): {saxs_det.hdf1.stage_sigs}")

    yield from bps.sleep(0.2)
    APS_plans.run_blocker_in_plan(
        # must run in thread since this is not a plan
        autoscale_amplifiers([I0_controls])
    )

    yield from bps.mv(
        ti_filter_shutter, "close",
    )

    old_delay = scaler0.delay.value
    yield from bps.mv(
        scaler1.preset_time, terms.SAXS.acquire_time.value + 1,
        scaler0.preset_time, 1.2*terms.SAXS.acquire_time.value + 1,
        scaler0.count_mode, "OneShot",
        scaler1.count_mode, "OneShot",
        
        # update as fast as hardware will allow
        # this is needed to make sure we get as up to date I0 number as possible for AD software. 
        scaler0.display_rate, 60,
        scaler1.display_rate, 60,
        
        scaler0.delay, 0,
        terms.SAXS.start_exposure_time, ts,
        user_data.state, f"SAXS collection for {terms.SAXS.acquire_time.value} s",
    )

    yield from bps.mv(
        scaler0.count, 1,
        scaler1.count, 1,
    )
    
    # print(f"DEBUG: SAXS(3): {saxs_det.hdf1.stage_sigs}")
    yield from areaDetectorAcquire(saxs_det)
    ts = str(datetime.datetime.now())

    saxs_det.hdf1.stage_sigs = old_det_stage_sigs    # TODO: needed? not even useful?
    # print(f"DEBUG: SAXS(4): {saxs_det.hdf1.stage_sigs}")

    yield from bps.mv(
        scaler0.count, 0,
        scaler1.count, 0,
        terms.SAXS.I0, scaler1.channels.chan02.s.value, 
        scaler0.display_rate, 5,
        scaler1.display_rate, 5,
        terms.SAXS.end_exposure_time, ts,
        scaler0.delay, old_delay,

        user_data.state, "Done SAXS",
        user_data.macro_file_time, ts,      # does not really apply to bluesky
        user_data.time_stamp, ts,
    )
    logger.info(f"I0 value: {terms.SAXS.I0.value}")
