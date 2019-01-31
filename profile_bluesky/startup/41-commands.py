print(__file__)

"""USAXS commands"""

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
    while terms.PauseBeforeNextScan.value:
        msg = pv_txt % (time.time() - t0)
        print(msg)
        yield from user_data.set_state_plan(msg)
        yield from bps.sleep(1)
        open_the_shutter = True

    if terms.StopBeforeNextScan.value:
        msg = "User requested stop data collection before next scan"
        print(msg)
        yield from bps.mv(
            ti_filter_shutter,                  "close",
            terms.StopBeforeNextScan,           0,
            user_data.collection_in_progress,   0,
        )
        RE.pause_msg = "DEBUG: stopped the scans, ignore the (informative) exception trace"
        RE.abort(reason=msg)        # this gonna work?

    if open_the_shutter:
        yield from bps.mv(mono_shutter, "open")     # waits until complete
        # yield from bps.sleep(2)         # so, sleep not needed


def confirmUsaxsSaxsOutOfBeam():
    """raise ValueError if not"""
    if terms.SAXS.UsaxsSaxsMode.value != UsaxsSaxsModes["out of beam"]:
        print("Found UsaxsSaxsMode = %s " % terms.SAXS.UsaxsSaxsMode.value)
        msg = "Incorrect UsaxsSaxsMode mode found."
        msg += " If SAXS, WAXS, and USAXS are out of beam, terms.SAXS.UsaxsSaxsMode.put(%d)"
        raise ValueError(msg % UsaxsSaxsModes["out of beam"])


def move_WAXSOut():
    # yield from plc_protect.stop_if_tripped()
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    print("Moving WAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["dirty"])

    # move the WAXS X away from sample
    yield from bps.mv(waxsx, terms.WAXS.x_out.value)

    yield from waxsx.set_lim(
        waxsx.soft_limit_lo.value,
        terms.WAXS.x_out.value + terms.WAXS.x_limit_offset.value)

    print("Removed WAXS from beam position")
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["out of beam"])


def move_WAXSIn():
    # yield from plc_protect.stop_if_tripped()
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    print("Moving to WAXS mode")

    confirmUsaxsSaxsOutOfBeam()
    yield from plc_protect.wait_for_interlock()

    # in case there is an error in moving, it is NOT SAFE to start a scan
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["dirty"])

    # first move USAXS out of way
    yield from waxsx.set_lim(
        waxsx.soft_limit_lo.value,
        terms.WAXS.x_in.value + terms.WAXS.x_limit_offset.value)

    yield from bps.mv(
        guard_slit.v_size, terms.SAXS.guard_v_size.value,
        guard_slit.h_size, terms.SAXS.guard_h_size.value,
        waxsx,             terms.WAXS.x_in.value,
        usaxs_slit.v_size, terms.SAXS.v_size.value,
        usaxs_slit.h_size, terms.SAXS.h_size.value,
    )

    print("WAXS is in position")
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["WAXS in beam"])


def move_SAXSOut():
    # yield from plc_protect.stop_if_tripped()
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    print("Moving SAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["dirty"])

    # move the pin_z away from sample
    yield from bps.mv(saxs_stage.z, terms.SAXS.z_out.value)

    yield from saxs_stage.z.set_lim(
        terms.SAXS.z_out.value - terms.SAXS.z_limit_offset.value,
        saxs_stage.z.soft_limit_hi.value,  # don't change this value
        )

    # move pinhole up to out of beam position
    yield from bps.mv(saxs_stage.y, terms.SAXS.y_out.value)

    yield from saxs_stage.y.set_lim(
        terms.SAXS.y_out.value - terms.SAXS.y_limit_offset.value,
        saxs_stage.y.soft_limit_hi.value,  # don't change this value
        )

    print("Removed SAXS from beam position")
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["out of beam"])


def move_SAXSIn():
    # yield from plc_protect.stop_if_tripped()
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    print("Moving to Pinhole SAXS mode")

    confirmUsaxsSaxsOutOfBeam()
    yield from plc_protect.wait_for_interlock()

    # in case there is an error in moving, it is NOT SAFE to start a scan
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["dirty"])

    # first move USAXS out of way
    yield from saxs_stage.y.set_lim(
        terms.SAXS.y_in.value - terms.SAXS.y_limit_offset.value,
        saxs_stage.y.soft_limit_hi.value,
        )

    yield from bps.mv(
        guard_slit.v_size, terms.SAXS.guard_v_size.value,
        guard_slit.h_size, terms.SAXS.guard_h_size.value,
        saxs_stage.y,      terms.SAXS.y_in.value,
        usaxs_slit.v_size, terms.SAXS.v_size.value,
        usaxs_slit.h_size, terms.SAXS.h_size.value,
    )

    yield from saxs_stage.z.set_lim(
        terms.SAXS.z_in.value - terms.SAXS.z_limit_offset.value,
        saxs_stage.z.soft_limit_hi.value   # do NOT change the hi value
        )

    # move Z _AFTER_ the others finish moving
    yield from bps.mv(saxs_stage.z, terms.SAXS.z_in.value)

    print("Pinhole SAXS is in position")
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["SAXS in beam"])


def move_USAXSOut():
    # yield from plc_protect.stop_if_tripped()
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    print("Moving USAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["dirty"])

    yield from bps.mv(
        a_stage.x, terms.SAXS.ax_out.value,
        d_stage.x, terms.SAXS.dx_out.value,
    )

    # now Main stages are out of place,
    # so we can now set the limits and then move pinhole in place.
    yield from a_stage.x.set_lim(
        terms.SAXS.ax_out.value - terms.SAXS.ax_limit_offset.value,
        a_stage.x.soft_limit_hi.value)
    yield from da_stage.x.set_lim(
        d_stage.x.soft_limit_lo.value,
        terms.SAXS.dx_out.value + terms.SAXS.dx_limit_offset.value)

    print("Removed USAXS from beam position")
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["out of beam"])


def move_USAXSIn():
    yield from plc_protect.stop_if_tripped()
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
    )

    print("Moving to USAXS mode")

    confirmUsaxsSaxsOutOfBeam()
    yield from plc_protect.wait_for_interlock()

    # in case there is an error in moving, it is NOT SAFE to start a scan
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["dirty"])

    # move USAXS in the beam
    # set the limits so we can move pinhole in place.
    yield from a_stage.x.set_lim(
        terms.SAXS.ax_in.value - terms.SAXS.ax_limit_offset.value,
        a_stage.x.soft_limit_hi.value)
    yield from d_stage.x.set_lim(
        d_stage.x.soft_limit_lo.value,
        terms.SAXS.dx_in.value + terms.SAXS.dx_limit_offset.value)

    yield from bps.mv(
        guard_slit.h_size,  terms.SAXS.usaxs_guard_h_size.value,
        guard_slit.v_size,  terms.SAXS.usaxs_guard_v_size.value,
        usaxs_slit.h_size,  terms.SAXS.usaxs_h_size.value,
        usaxs_slit.v_size,  terms.SAXS.usaxs_v_size.value,
        a_stage.y,          terms.USAXS.AY0.value,
        a_stage.x,          terms.SAXS.ax_in.value,
        d_stage.x,          terms.SAXS.dx_in.value,
        d_stage.y,          terms.USAXS.DY0.value,
    )

    print("USAXS is in position")
    yield from bps.mv(terms.SAXS.UsaxsSaxsMode, UsaxsSaxsModes["USAXS in beam"])


# TODO: necessary to keep this?
def set_USAXS_slits():
    """move the USAXS slits to expected values"""
    usaxs_slit.v_size,  terms.SAXS.usaxs_v_size.value,
    usaxs_slit.h_size,  terms.SAXS.usaxs_h_size.value,
    guard_slit.v_size,  terms.SAXS.usaxs_guard_v_size.value,
    guard_slit.h_size,  terms.SAXS.usaxs_guard_h_size.value,
