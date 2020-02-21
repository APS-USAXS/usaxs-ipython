logger.info(__file__)
# logger.debug(resource_usage(os.path.split(__file__)[-1]))

"""
USAXS commands

FUNCTIONS

    angle2q()
    becplot_prune_fifo()
    beforeScanComputeOtherStuff()
    cleanupText()
    confirmUsaxsSaxsOutOfBeam()
    IfRequestedStopBeforeNextScan()
    move_SAXSIn()
    move_SAXSOut()
    move_USAXSIn()
    move_USAXSOut()
    move_WAXSIn()
    move_WAXSOut()
    q2angle()

"""


### This file is work-in-progress
# see: https://subversion.xray.aps.anl.gov/spec/beamlines/USAXS/trunk/macros/local/usaxs_commands.mac

UsaxsSaxsModes = {
    "dirty": -1,        # moving or prior move did not finish correctly
    "out of beam": 1,   # SAXS, WAXS, and USAXS out of beam
    "USAXS in beam": 2,
    "SAXS in beam": 3,
    "WAXS in beam": 4,
    "Imaging in": 5,
    "Imaging tuning": 6,
}


def q2angle(q, wavelength):
    # angle is in 2theta
    return np.arcsin(wavelength*q/4/np.pi)*180*2/np.pi


def angle2q(angle, wavelength):
    # angle is in 2theta
    return (4*np.pi/wavelength) * np.sin(angle*np.pi/2/180)


def becplot_prune_fifo(n, y, x):
    """
    find the plot with axes x and y and replot with only the last *n* lines

    Note: this is not a bluesky plan.  Call it as normal Python function.

    EXAMPLE::

        becplot_prune_fifo(1, noisy, m1)

    PARAMETERS
    
    n : int
        number of plots to keep
    
    y : object
        ophyd Signal object on dependent (y) axis
    
    x : object
        ophyd Signal object on independent (x) axis
    """
    for liveplot in bec._live_plots.values():
        lp = liveplot.get(y.name)
        if lp is None:
            logging.debug(f"no LivePlot with name {y.name}")
            continue
        if lp.x != x.name or lp.y != y.name:
            logging.debug(f"no LivePlot with axes ('{x.name}', '{y.name}')")
            continue
        # print(lp.x, lp.y)
        if len(lp.ax.lines) > n:
            logging.debug(f"limiting LivePlot({y.name}) to {n} traces")
            lp.ax.lines = lp.ax.lines[-n:]
            lp.update_plot()


def cleanupText(text):
    """
    given some input text string, return a clean version

    remove troublesome characters, perhaps other cleanup as well

    this is best done with regular expression pattern matching
    """
    import re
    pattern = "[a-zA-Z0-9_]"

    def mapper(c):
        if re.match(pattern, c) is not None:
            return c
        return "_"

    return "".join([mapper(c) for c in text])


def IfRequestedStopBeforeNextScan():
    """plan: wait if requested"""
    global RE
    open_the_shutter = False
    t0 = time.time()
    
    RE.pause_msg = bluesky.run_engine.PAUSE_MSG     # sloppy

    pv_txt = "Pausing for user for %g s"
    while terms.PauseBeforeNextScan.get():
        msg = pv_txt % (time.time() - t0)
        logger.info(msg)
        yield from user_data.set_state_plan(msg)
        yield from bps.sleep(1)
        open_the_shutter = True

    if terms.StopBeforeNextScan.get():
        msg = "User requested stop data collection before next scan"
        logger.info(msg)
        yield from bps.mv(
            ti_filter_shutter,                  "close",
            terms.StopBeforeNextScan,           0,
            user_data.collection_in_progress,   0,
            user_data.time_stamp, str(datetime.datetime.now()),
            user_data.state, "Aborted data collection",
       )
 
        # RE.pause_msg = "DEBUG: stopped the scans, ignore the (informative) exception trace"
        raise RequestAbort(msg)        # long exception trace?
        # To make the exception trace brief, `%xmode Minimal`
        """
        example:
        
        In [8]: def plan(): 
           ...:     raise RequestAbort("Aborted from plan because user requested") 
        In [9]: RE(plan())                                                                                                                          
        ---------------------------------------------------------------------------
        RequestAbort                              Traceback (most recent call last)
        <ipython-input-9-a6361a080fc0> in <module>
        ----> 1 RE(plan())

        <ipython-input-8-7178eb5f1267> in plan()
              1 def plan():
        ----> 2     raise RequestAbort("Aborted from plan because user requested")
              3 
              4 

        RequestAbort: Aborted from plan because user requested
        In [12]: %xmode Minimal                                                                                                                     
        Exception reporting mode: Minimal

        In [13]: RE(plan())                                                                                                                         
        RequestAbort: Aborted from plan because user requested
        """

    if open_the_shutter:
        yield from bps.mv(mono_shutter, "open")     # waits until complete
        # yield from bps.sleep(2)         # so, sleep not needed


def confirmUsaxsSaxsOutOfBeam():
    """raise ValueError if not"""
    if terms.SAXS.UsaxsSaxsMode.get() != UsaxsSaxsModes["out of beam"]:
        logger.warning("Found UsaxsSaxsMode = %s " % terms.SAXS.UsaxsSaxsMode.get())
        msg = "Incorrect UsaxsSaxsMode mode found."
        msg += " If SAXS, WAXS, and USAXS are out of beam, terms.SAXS.UsaxsSaxsMode.put(%d)"
        raise ValueError(msg % UsaxsSaxsModes["out of beam"])


def move_WAXSOut():
    # yield from plc_protect.stop_if_tripped()
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    logger.info("Moving WAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["dirty"])

    # move the WAXS X away from sample
    yield from bps.mv(waxsx, terms.WAXS.x_out.get())

    yield from waxsx.set_lim(
        waxsx.soft_limit_lo.get(),
        terms.WAXS.x_out.get() + terms.WAXS.x_limit_offset.get())

    logger.info("Removed WAXS from beam position")
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["out of beam"])


def move_WAXSIn():
    # yield from plc_protect.stop_if_tripped()
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    logger.info("Moving to WAXS mode")

    confirmUsaxsSaxsOutOfBeam()
    yield from plc_protect.wait_for_interlock()

    # in case there is an error in moving, it is NOT SAFE to start a scan
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["dirty"])

    # first move USAXS out of way
    yield from waxsx.set_lim(
        waxsx.soft_limit_lo.get(),
        terms.WAXS.x_in.get() + terms.WAXS.x_limit_offset.get())

    yield from bps.mv(
        guard_slit.v_size, terms.SAXS.guard_v_size.get(),
        guard_slit.h_size, terms.SAXS.guard_h_size.get(),
        waxsx,             terms.WAXS.x_in.get(),
        usaxs_slit.v_size, terms.SAXS.v_size.get(),
        usaxs_slit.h_size, terms.SAXS.h_size.get(),
    )

    logger.info("WAXS is in position")
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["WAXS in beam"])


def move_SAXSOut():
    # yield from plc_protect.stop_if_tripped()
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    logger.info("Moving SAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["dirty"])

    # move the pin_z away from sample
    yield from bps.mv(saxs_stage.z, terms.SAXS.z_out.get())

    yield from saxs_stage.z.set_lim(
        terms.SAXS.z_out.get() - terms.SAXS.z_limit_offset.get(),
        saxs_stage.z.soft_limit_hi.get(),  # don't change this value
        )

    # move pinhole up to out of beam position
    yield from bps.mv(saxs_stage.y, terms.SAXS.y_out.get())

    yield from saxs_stage.y.set_lim(
        terms.SAXS.y_out.get() - terms.SAXS.y_limit_offset.get(),
        saxs_stage.y.soft_limit_hi.get(),  # don't change this value
        )

    logger.info("Removed SAXS from beam position")
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["out of beam"])


def move_SAXSIn():
    # yield from plc_protect.stop_if_tripped()
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    logger.info("Moving to Pinhole SAXS mode")

    confirmUsaxsSaxsOutOfBeam()
    yield from plc_protect.wait_for_interlock()

    # in case there is an error in moving, it is NOT SAFE to start a scan
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["dirty"])

    # first move USAXS out of way
    yield from saxs_stage.y.set_lim(
        terms.SAXS.y_in.get() - terms.SAXS.y_limit_offset.get(),
        saxs_stage.y.soft_limit_hi.get(),
        )

    yield from bps.mv(
        guard_slit.v_size, terms.SAXS.guard_v_size.get(),
        guard_slit.h_size, terms.SAXS.guard_h_size.get(),
        saxs_stage.y,      terms.SAXS.y_in.get(),
        usaxs_slit.v_size, terms.SAXS.v_size.get(),
        usaxs_slit.h_size, terms.SAXS.h_size.get(),
    )

    yield from saxs_stage.z.set_lim(
        terms.SAXS.z_in.get() - terms.SAXS.z_limit_offset.get(),
        saxs_stage.z.soft_limit_hi.get()   # do NOT change the hi value
        )

    # move Z _AFTER_ the others finish moving
    yield from bps.mv(saxs_stage.z, terms.SAXS.z_in.get())

    logger.info("Pinhole SAXS is in position")
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["SAXS in beam"])


def move_USAXSOut():
    # yield from plc_protect.stop_if_tripped()
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    logger.info("Moving USAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["dirty"])

    yield from bps.mv(
        a_stage.x, terms.SAXS.ax_out.get(),
        d_stage.x, terms.SAXS.dx_out.get(),
    )

    # now Main stages are out of place,
    # so we can now set the limits and then move pinhole in place.
    yield from a_stage.x.set_lim(
        terms.SAXS.ax_out.get() - terms.SAXS.ax_limit_offset.get(),
        a_stage.x.soft_limit_hi.get())
    yield from d_stage.x.set_lim(
        d_stage.x.soft_limit_lo.get(),
        terms.SAXS.dx_out.get() + terms.SAXS.dx_limit_offset.get())

    logger.info("Removed USAXS from beam position")
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["out of beam"])


def move_USAXSIn():
    yield from plc_protect.stop_if_tripped()
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    logger.info("Moving to USAXS mode")

    confirmUsaxsSaxsOutOfBeam()
    yield from plc_protect.wait_for_interlock()

    # in case there is an error in moving, it is NOT SAFE to start a scan
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["dirty"])

    # move USAXS in the beam
    # set the limits so we can move pinhole in place.
    yield from a_stage.x.set_lim(
        terms.SAXS.ax_in.get() - terms.SAXS.ax_limit_offset.get(),
        a_stage.x.soft_limit_hi.get())
    yield from d_stage.x.set_lim(
        d_stage.x.soft_limit_lo.get(),
        terms.SAXS.dx_in.get() + terms.SAXS.dx_limit_offset.get())

    yield from bps.mv(
        guard_slit.h_size,  terms.SAXS.usaxs_guard_h_size.get(),
        guard_slit.v_size,  terms.SAXS.usaxs_guard_v_size.get(),
        usaxs_slit.h_size,  terms.SAXS.usaxs_h_size.get(),
        usaxs_slit.v_size,  terms.SAXS.usaxs_v_size.get(),
        a_stage.y,          terms.USAXS.AY0.get(),
        a_stage.x,          terms.SAXS.ax_in.get(),
        d_stage.x,          terms.SAXS.dx_in.get(),
        d_stage.y,          terms.USAXS.DY0.get(),
    )

    logger.info("USAXS is in position")
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["USAXS in beam"])


def beforeScanComputeOtherStuff():
    """
    things to be computed and set before each data collection starts
    """
    yield from bps.null()       # TODO: remove this once you add the "other stuff"
