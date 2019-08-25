logger.info(__file__)
logger.debug(resource_usage(os.path.split(__file__)[-1]))

"""
USAXS mode change procedures

FUNCTIONS

    areaDetectorAcquire()
    confirm_instrument_mode()
    DCMfeedbackON()
    insertRadiographyFilters()
    insertSaxsFilters()
    insertScanFilters()
    insertTransmissionFilters()
    insertWaxsFilters()
    measure_SAXS_Transmission()
    measure_USAXS_Transmission()
    mode_imaging()
    mode_OpenBeamPath()
    mode_Radiography()
    mode_SAXS()
    mode_SBUAXS()
    mode_USAXS()
    mode_WAXS()
    remaining_time_reporter()

INTERNAL

    _insertFilters_()

"""



def DCMfeedbackON():
    """plan: could send email"""
    yield from bps.mv(monochromator.feedback.on, MONO_FEEDBACK_ON)
    monochromator.feedback.check_position()


def _insertFilters_(a, b):
    """plan: insert the EPICS-specified filters"""
    yield from bps.mv(pf4_AlTi.fPosA, int(a), pf4_AlTi.fPosB, int(b))
    yield from bps.sleep(0.5)       # allow all blades to re-position


def insertRadiographyFilters():
    """plan: insert the EPICS-specified filters"""
    yield from _insertFilters_(
        terms.USAXS.img_filters.Al.value,    # Bank A: Al
        terms.USAXS.img_filters.Ti.value,    # Bank B: Ti
    )


def insertSaxsFilters():
    """plan: insert the EPICS-specified filters"""
    yield from _insertFilters_(
        terms.SAXS.filters.Al.value,    # Bank A: Al
        terms.SAXS.filters.Ti.value,    # Bank B: Ti
    )


def insertScanFilters():
    """plan: insert the EPICS-specified filters"""
    yield from _insertFilters_(
        terms.USAXS.scan_filters.Al.value,    # Bank A: Al
        terms.USAXS.scan_filters.Ti.value,    # Bank B: Ti
    )


def insertWaxsFilters():
    """plan: insert the EPICS-specified filters"""
    yield from _insertFilters_(
        terms.WAXS.filters.Al.value,    # Bank A: Al
        terms.WAXS.filters.Ti.value,    # Bank B: Ti
    )


def insertTransmissionFilters():
    """
    set filters to reduce diode damage when measuring tranmission on guard slits etc
    """
    if monochromator.dcm.energy.value < 12.1:
        al_filters = 0
    elif monochromator.dcm.energy.value < 18.1:
        al_filters = 3
    else:
        al_filters = 8
    yield from _insertFilters_(al_filters, 0)


def confirm_instrument_mode(mode_name):
    """
    True if instrument is in the named mode

    Parameter

    mode_name (str) :
        One of the strings defined in ``UsaxsSaxsModes``
    """
    expected_mode = UsaxsSaxsModes[mode_name]
    return terms.SAXS.UsaxsSaxsMode.value == expected_mode


def mode_USAXS():
    # plc_protect.stop_if_tripped()
    yield from user_data.set_state_plan("Moving USAXS to USAXS mode")
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
        d_stage.x, terms.USAXS.diode.dx.value,
        d_stage.y, terms.USAXS.diode.dy.value,
        guard_slit.h_size,  terms.SAXS.usaxs_guard_h_size.value,
        guard_slit.v_size,  terms.SAXS.usaxs_guard_v_size.value,
        usaxs_slit.h_size,  terms.SAXS.usaxs_h_size.value,
        usaxs_slit.v_size,  terms.SAXS.usaxs_v_size.value,
    )
    yield from DCMfeedbackON()
    retune_needed = False

    if not confirm_instrument_mode("USAXS in beam"):
        mode_now = terms.SAXS.UsaxsSaxsMode.get(as_string=True)
        logger.info(f"Found UsaxsSaxsMode = {mode_now}")
        logger.info("Moving to proper USAXS mode")
        yield from move_WAXSOut()
        yield from move_SAXSOut()
        yield from move_USAXSIn()
        retune_needed = True

    logger.info("Preparing for USAXS mode ... please wait ...")
    yield from bps.mv(
        # set scalar to autocount mode for USAXS
        scaler0.count_mode, SCALER_AUTOCOUNT_MODE,
    )

    if not ccd_shutter.isClosed:
        logger.info("!!!CCD shutter failed to close!!!")
    else:
        # mono_shutter.open()

        # print("Change TV input selector to show image in hutch")
        # print("Turn off BLUE switch on CCD controller")
        yield from insertScanFilters()
        yield from bps.mv(ccd_shutter, "close")

        logger.info("Prepared for USAXS mode")
        yield from user_data.set_state_plan("USAXS Mode")
        ts = str(datetime.datetime.now())
        yield from bps.mv(
            user_data.time_stamp, ts,
            user_data.macro_file_time, ts,
            user_data.scanning, 0,
        )

    if retune_needed:
        # don't tune here
        # Instead, set a signal to be caught by the plan in the RunEngine
        yield from bps.mv(terms.USAXS.retune_needed, True)


# def mode_SBUSAXS():  # TODO:
mode_SBUSAXS = mode_USAXS       # for now


def mode_SAXS():
    # plc_protect.stop_if_tripped()
    yield from user_data.set_state_plan("Moving USAXS to SAXS mode")
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    if not confirm_instrument_mode("SAXS in beam"):
        mode_now = terms.SAXS.UsaxsSaxsMode.get(as_string=True)
        logger.info(f"Found UsaxsSaxsMode = {mode_now}")
        logger.info("Moving to proper SAXS mode")
        yield from move_WAXSOut()
        yield from move_USAXSOut()
        yield from move_SAXSIn()

    logger.info("Prepared for SAXS mode")
    #insertScanFilters
    yield from user_data.set_state_plan("SAXS Mode")
    ts = str(datetime.datetime.now())
    yield from bps.mv(
        user_data.time_stamp, ts,
        user_data.macro_file_time, ts,
        user_data.scanning, 0,
    )


def mode_WAXS():
    # plc_protect.stop_if_tripped()
    yield from user_data.set_state_plan("Moving USAXS to WAXS mode")
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    if confirm_instrument_mode("WAXS in beam"):
        logger.debug("WAXS is in beam")
    else:
        mode_now = terms.SAXS.UsaxsSaxsMode.get(as_string=True)
        logger.info(f"Found UsaxsSaxsMode = {mode_now}")
        logger.info("Moving to proper WAXS mode")
        yield from move_SAXSOut()
        yield from move_USAXSOut()
        yield from move_WAXSIn()

    # move SAXS slits in, used for WAXS mode also
    v_diff = abs(guard_slit.v_size.value - terms.SAXS.guard_v_size.value)
    h_diff = abs(guard_slit.h_size.value - terms.SAXS.guard_h_size.value)
    logger.debug("guard slits horizontal difference = %g" % h_diff)
    logger.debug("guard slits vertical difference = %g" % v_diff)

    if max(v_diff, h_diff) > 0.03:
        logger.info("changing Guard slits")
        yield from bps.mv(
            guard_slit.h_size, terms.SAXS.guard_h_size.value,
            guard_slit.v_size, terms.SAXS.guard_v_size.value,
        )
        # TODO: need completion indication
        #  guard_slit is calculated by a database
        #  support needs a handler that does this wait for us.
        yield from bps.sleep(0.5)           # TODO: needed now?

    v_diff = abs(usaxs_slit.v_size.position - terms.SAXS.v_size.value)
    h_diff = abs(usaxs_slit.h_size.position - terms.SAXS.h_size.value)
    logger.debug("USAXS slits horizontal difference = %g" % h_diff)
    logger.debug("USAXS slits vertical difference = %g" % v_diff)

    if max(v_diff, h_diff) > 0.02:
       logger.info("Moving Beam defining slits")
       yield from bps.mv(
           usaxs_slit.h_size, terms.SAXS.h_size.value,
           usaxs_slit.v_size, terms.SAXS.v_size.value,
       )
       yield from bps.sleep(2)     # wait for backlash, seems these motors are slow and spec gets ahead of them?

    logger.info("Prepared for WAXS mode")
    #insertScanFilters
    yield from user_data.set_state_plan("WAXS Mode")
    ts = str(datetime.datetime.now())
    yield from bps.mv(
        user_data.time_stamp, ts,
        user_data.macro_file_time, ts,
        user_data.scanning, 0,
    )


    """
  comment "Ready for Radiography mode"
  print "TV should now show Radiography CCD image. If not, check: TV on? Right TV input? Camera on (Blue button)?"
  print "Beam on? Shutters opened? Sample/holder out of beam? - if all is OK, try running preUSAXStune."
  print "preUSAXStune worked? Run useModeRadiography. Still not working? Call Jan, Ivan or Matt."
  print "But before calling - are you REALLY sure the sample is not blocking the beam? Move it out and try preUSAXStune again."
  epics_put ("9idcLAX:USAXS:timeStamp",   date())
  epics_put ("9idcLAX:USAXS:state",       "Radiography Mode")
  epics_put ("9idcLAX:USAXS:macroFileTime",      date())
  epics_put ("9idcLAX:USAXS:scanning",    0)
}'
    """


def mode_Radiography():
    """
    put in USAXS Radiography mode

    USAGE:  ``RE(mode_Radiography())``
    """
    
    yield from mode_USAXS()
    
    yield from bps.mv(
        monochromator.feedback.on, MONO_FEEDBACK_ON,
        mono_shutter, "open",
        ccd_shutter, "close",
    )
  
    yield from bps.mv(
        # move to ccd position 
        d_stage.x, terms.USAXS.ccd.dx.value,
        d_stage.y, terms.USAXS.ccd.dy.value,
        # make sure slits are in place
        usaxs_slit.v_size,  terms.SAXS.usaxs_v_size.value,
        usaxs_slit.h_size,  terms.SAXS.usaxs_h_size.value,
        guard_slit.v_size,  terms.SAXS.usaxs_guard_v_size.value,
        guard_slit.h_size,  terms.SAXS.usaxs_guard_h_size.value,
    )
    
    yield from insertRadiographyFilters()
    
    # when all that is complete, then ...
    ts = str(datetime.datetime.now())
    yield from bps.mv(
        ti_filter_shutter, "open",
        ccd_shutter, "open",
        user_data.time_stamp, ts,
        user_data.macro_file_time, ts,
        user_data.scanning, 0,
        )

    yield from user_data.set_state_plan("Radiography Mode")
    msg = """
    TV should now show Radiography CCD image. 
    
    But before calling - are you REALLY sure the sample is not blocking the beam? 
       Move sample out and try RE(preUSAXStune()) again.

    If still no image on the CCD, check: 
    
    * TV on? Right TV input? 
    * Camera on (Blue button)?
    * Beam on? 
    * Shutters opened? 
    * Sample/holder out of beam? 
    
    - if all is OK, try running RE(preUSAXStune()).
    preUSAXStune worked? Run RE(mode_Radiography()). 
    
    Still not working? Call Jan, Ivan or Matt.
    """
    print(msg)


def mode_imaging():
    """
    prepare the instrument for USAXS imaging
    """
    # see: /share1/USAXS_data/2019-02/USAXS_user_macros.mac
    # there it calls useModeUSAXS so that's what we'll do here
    yield from user_data.set_state_plan("Moving USAXS to Imaging mode (same as USAXS mode now)")
    yield from mode_USAXS()


def mode_OpenBeamPath():
    # plc_protect.stop_if_tripped()
    yield from user_data.set_state_plan("Moving USAXS to OpenBeamPath mode")
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    if not confirm_instrument_mode("out of beam"):
        mode_now = terms.SAXS.UsaxsSaxsMode.get(as_string=True)
        logger.info(f"Found UsaxsSaxsMode = {mode_now}")
        logger.info("Opening the beam path, moving all components out")
        yield from move_SAXSOut()
        yield from move_WAXSOut()
        yield from move_USAXSOut()
        yield from user_data.set_state_plan("USAXS moved to OpenBeamPath mode")


def measure_USAXS_Transmission(md={}):
    """
    measure the sample transmission in USAXS mode
    """
    trmssn = terms.USAXS.transmission   # for convenience
    yield from user_data.set_state_plan("Measure USAXS transmission")
    if trmssn.measure.value:
        yield from mode_USAXS()
        ay_target = terms.USAXS.AY0.value + constants["USAXS_AY_OFFSET"] + 12*np.sin(terms.USAXS.ar_val_center.value * np.pi/180)
        yield from bps.mv(
            trmssn.ay, ay_target,
            a_stage.y, ay_target,
            ti_filter_shutter, "open",
        )
        yield from insertTransmissionFilters()

        yield from autoscale_amplifiers([I0_controls, trd_controls])

        yield from bps.mv(
            scaler0.preset_time, trmssn.count_time.value
        )
        md["plan_name"] = "measure_USAXS_Transmission"
        scaler0.select_channels(["I0_USAXS", "TR diode"])
        yield from bp.count([scaler0], md=md)
        scaler0.select_channels(None)
        s = scaler0.read()
        secs = s["scaler0_time"]["value"]
        _tr_diode = s["TR diode"]["value"]
        _I0 = s["I0_USAXS"]["value"]
        
        if _tr_diode > secs*constants["TR_MAX_ALLOWED_COUNTS"]  or _I0 > secs*constants["TR_MAX_ALLOWED_COUNTS"] :
            yield from autoscale_amplifiers([I0_controls, trd_controls])
            
            yield from bps.mv(
                scaler0.preset_time, trmssn.count_time.value
            )
            scaler0.select_channels(["I0_USAXS", "TR diode"])
            yield from bp.count([scaler0], md=md)
            scaler0.select_channels(None)
            s = scaler0.read()

        yield from bps.mv(
            a_stage.y, terms.USAXS.AY0.value,
            ti_filter_shutter, "close",
        )
        yield from insertScanFilters()
        yield from bps.mv(
            trmssn.diode_counts, s["TR diode"]["value"],
            trmssn.diode_gain, trd_controls.femto.gain.value,
            trmssn.I0_counts, s["I0_USAXS"]["value"],
            trmssn.I0_gain, I0_controls.femto.gain.value,
        )
        tbl = pyRestTable.Table()
        tbl.addLabel("detector")
        tbl.addLabel("counts")
        tbl.addLabel("gain")
        tbl.addRow(("pinDiode", f"{trmssn.diode_counts.value:f}", f"{trmssn.diode_gain.value}"))
        tbl.addRow(("I0", f"{trmssn.I0_counts.value:f}", f"{trmssn.I0_gain.value}"))
        msg = "Measured USAXS transmission values:\n"
        msg += str(tbl.reST())
        logger.info(msg)

    else:
        yield from bps.mv(
            trmssn.diode_counts, 0,
            trmssn.diode_gain, 0,
            trmssn.I0_counts, 0,
            trmssn.I0_gain, 0,
        )
        logger.info("Did not measure USAXS transmission.")
    


def measure_SAXS_Transmission(md={}):
    """
    measure the sample transmission in SAXS mode
    """
    # FIXME: this failed when USAXS was already in position
    yield from user_data.set_state_plan("Measure SAXS transmission")
    yield from mode_SAXS()
    yield from insertTransmissionFilters()
    pinz_target = terms.SAXS.z_in.value + constants["SAXS_PINZ_OFFSET"]
    piny_target = terms.SAXS.y_in.value + constants["SAXS_TR_PINY_OFFSET"]
    # z has to move before y can move.
    yield from bps.mv(saxs_stage.z, pinz_target)
    #now y can put diode in the beam, open shutter... 
    yield from bps.mv(
        saxs_stage.y, piny_target,
        ti_filter_shutter, "open",
    )
 
    yield from autoscale_amplifiers([I0_controls, trd_controls])
    yield from bps.mv(
        scaler0.preset_time, constants["SAXS_TR_TIME"],
    )
    md["plan_name"] = "measure_SAXS_Transmission"
    yield from bp.count([scaler0], md=md)
    s = scaler0.read()
    secs = s["scaler0_time"]["value"]
    _tr_diode = s["TR diode"]["value"]
    _I0 = s["I0_USAXS"]["value"]
    
    if _tr_diode > secs*constants["TR_MAX_ALLOWED_COUNTS"] or _I0 > secs*constants["TR_MAX_ALLOWED_COUNTS"] :
        yield from autoscale_amplifiers([I0_controls, trd_controls])
        
        yield from bps.mv(
            scaler0.preset_time, constants["SAXS_TR_TIME"],
        )
        yield from bp.count([scaler0], md=md)
        s = scaler0.read()

    # y has to move before z, close shutter... 
    yield from bps.mv(
        saxs_stage.y, terms.SAXS.y_in.value,
        ti_filter_shutter, "close",
    )
    # z can move.
    yield from bps.mv(saxs_stage.z, terms.SAXS.z_in.value)
    
    yield from insertScanFilters()
    yield from bps.mv(
        terms.SAXS_WAXS.diode_transmission, s["TR diode"]["value"],
        terms.SAXS_WAXS.diode_gain, trd_controls.femto.gain.value,
        terms.SAXS_WAXS.I0_transmission, s["I0_USAXS"]["value"],
        terms.SAXS_WAXS.I0_gain, I0_controls.femto.gain.value,
    )
    msg = "Measured SAXS transmission values, pinDiode cts =%f with gain %g and I0 cts =%f with gain %g" % (
        terms.USAXS.transmission.diode_counts.value, 
        terms.USAXS.transmission.diode_gain.value, 
        terms.USAXS.transmission.I0_counts.value,
        terms.USAXS.transmission.I0_gain.value
        )
    logger.info(msg)


@APS_utils.run_in_thread
def remaining_time_reporter(title, duration_s, interval_s=5, poll_s=0.05):
    if duration_s < interval_s:
        return
    t = time.time()
    expires = t + duration_s
    update = t + interval_s
    # print()
    while time.time() < expires:
        remaining = expires - t
        if t > update:
            update += interval_s
            logger.info(f"{title}: {remaining:.1f}s remaining")
        time.sleep(poll_s)
        t = time.time()


def areaDetectorAcquire(det, md={}):
    """
    acquire image(s) from the named area detector
    """
    acquire_time = det.cam.acquire_time.value
    # Note: AD's HDF File Writer can use up to 5 seconds to finish writing the file
    
    t0 = time.time()
    yield from bps.mv(
        user_data.scanning, "scanning",          # we are scanning now (or will be very soon)
    )
    logger.debug(f"areaDetectorAcquire(): {det.hdf1.stage_sigs}")
    md["method"] = "areaDetectorAcquire"
    md["area_detector_name"] = det.name
    if md.get("plan_name") is None:
        md["plan_name"] = "image"

    if RE.state != "idle":
        remaining_time_reporter(md["plan_name"], acquire_time)

    yield from bp.count([det], md=md)          # TODO: SPEC showed users incremental progress (1 Hz updates) #175

    yield from bps.mv(user_data.scanning, "no",)  # we are done
    elapsed = time.time() - t0
    logger.info(f"Finished SAXS/WAXS data collection in {elapsed} seconds.")
