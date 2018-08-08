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


def IfRequestedStopBeforeNextScan():
    open_the_shutter = False
    t0 = time.time()

    pv_txt = "Pausing for user for %g s"
    while terms.PauseBeforeNextScan.value > 0.5:
        msg = pv_txt % (time.time() - t0)
        print(msg)
        user_data.set_state(msg)
        time.sleep(1)
        open_the_shutter = True

    if terms.StopBeforeNextScan.value:
        print("User requested stop data collection before next scan")
        ti_filter_shutter.close()
        terms.StopBeforeNextScan.put(0)
        user_data.collection_in_progress.put(0)
        open_the_shutter = False

    if open_the_shutter:
        mono_shutter.open()     # waits until complete
        # time.sleep(2)         # so, sleep not needed


def confirmUsaxsSaxsOutOfBeam():
    """raise ValueError if not"""
    if terms.SAXS.UsaxsSaxsMode.value != UsaxsSaxsModes["out of beam"]:
        print("Found UsaxsSaxsMode = %s " % terms.SAXS.UsaxsSaxsMode.value)
        msg = "Incorrect UsaxsSaxsMode mode found."
        msg += " If SAXS, WAXS, and USAXS are out of beam, UsaxsSaxsMode.put(%d)" 
        raise ValueError(msg % UsaxsSaxsModes["out of beam"])


def move_WAXSOut():
    plc_protect.stop_if_tripped()
    ccd_shutter.close()
    ti_filter_shutter.close()

    print("Moving WAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    terms.SAXS.UsaxsSaxsMode.put(UsaxsSaxsModes["dirty"])

    # move the WAXS X away from sample
    waxsx.move(terms.WAXS.x_out.value)

    waxsx.set_lim(
        waxsx.soft_limit_hi.value, 
        terms.WAXS.x_out.value + terms.WAXS.x_limit_offset.value)

    print("Removed WAXS from beam position")
    terms.SAXS.UsaxsSaxsMode.put(UsaxsSaxsModes["out of beam"])


def move_WAXSIn():
    plc_protect.stop_if_tripped()
    ccd_shutter.close()
    ti_filter_shutter.close()
    print("Moving to WAXS mode")

    confirmUsaxsSaxsOutOfBeam()
    plc_protect.wait_for_interlock()

    # in case there is an error in moving, it is NOT SAFE to start a scan
    terms.SAXS.UsaxsSaxsMode.put(UsaxsSaxsModes["dirty"])

    # first move USAXS out of way
    waxsx.set_lim(
        waxsx.soft_limit_hi.value, 
        terms.WAXS.x_in.value + terms.WAXS.x_limit_offset.value)
    
    move_motors(
        guard_slit.v_size, terms.SAXS.guard_v_size.value,
        guard_slit.h_size, terms.SAXS.guard_h_size.value,
        waxsx,             terms.WAXS.x_in.value,
        usaxs_slit.v_size, terms.SAXS.v_size.value,
        usaxs_slit.h_size, terms.SAXS.h_size.value,
    )

    print("WAXS is in position")
    terms.SAXS.UsaxsSaxsMode.put(UsaxsSaxsModes["WAXS in beam"])


def move_SAXSOut():
    plc_protect.stop_if_tripped()
    ccd_shutter.close()
    ti_filter_shutter.close()

    print("Moving SAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    terms.SAXS.UsaxsSaxsMode.put(UsaxsSaxsModes["dirty"])
    
    pin_y = saxs_stage.y
    pin_z = saxs_stage.z
    # move the pin_z away from sample
    pin_z.move(terms.SAXS.z_out.value)

    pin_z.set_lim(
        pin_z.soft_limit_hi.value, 
        terms.SAXS.z_out.value - terms.SAXS.z_limit_offset.value,
        )
    
    # move pinhole up to out of beam position
    pin_y.y.move(terms.SAXS.y_out.value)

    pin_y.set_lim(
        terms.SAXS.y_out.value - terms.SAXS.y_limit_offset.value,
        pin_y.soft_limit_lo.value,
        )

    print("Removed SAXS from beam position")
    ###sleep(1)    
    #waxs seems to be getting ahead of saxs limit switch
    # - should not be needed, we have plc_protect.wait_for_interlock() now. 
    terms.SAXS.UsaxsSaxsMode.put(UsaxsSaxsModes["out of beam"])


def move_SAXSIn():
    plc_protect.stop_if_tripped()
    ccd_shutter.close()
    ti_filter_shutter.close()
    print("Moving to Pinhole SAXS mode")

    confirmUsaxsSaxsOutOfBeam()
    plc_protect.wait_for_interlock()

    # in case there is an error in moving, it is NOT SAFE to start a scan
    terms.SAXS.UsaxsSaxsMode.put(UsaxsSaxsModes["dirty"])

    # first move USAXS out of way
    pin_y = saxs_stage.y
    pin_z = saxs_stage.z
    pin_y.set_lim(
        terms.SAXS.y_in.value - terms.SAXS.y_limit_offset.value,
        pin_y.soft_limit_lo.value,
        )

    move_motors(
        guard_slit.v_size, terms.SAXS.guard_v_size.value,
        guard_slit.h_size, terms.SAXS.guard_h_size.value,
        pin_y,             terms.SAXS.y_in.value,
        usaxs_slit.v_size, terms.SAXS.v_size.value,
        usaxs_slit.h_size, terms.SAXS.h_size.value,
    )

    pin_z.set_lim(
        pin_z.soft_limit_hi.value, 
        terms.SAXS.z_in.value - terms.SAXS.z_limit_offset.value)

    # move Z _AFTER_ the others finish moving
    pin_z.move(terms.SAXS.z_in.value)

    print("Pinhole SAXS is in position")
    terms.SAXS.UsaxsSaxsMode.put(UsaxsSaxsModes["SAXS in beam"])


def move_USAXSOut():
    plc_protect.stop_if_tripped()
    ccd_shutter.close()
    ti_filter_shutter.close()

    print("Moving USAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    terms.SAXS.UsaxsSaxsMode.put(UsaxsSaxsModes["dirty"])

    ax = a_stage.x
    dx = d_stage.x
    move_motors(
        ax, terms.SAXS.ax_out.value,
        dx, terms.SAXS.dx_out.value,
    )

    # now Main stages are out of place, 
    # so we can now set the limits and then move pinhole in place.
    ax.set_lim(
        terms.SAXS.ax_out.value - terms.SAXS.ax_limit_offset.value,
        ax.soft_limit_hi.value)
    dx.set_lim(
        terms.SAXS.dx_out.value + terms.SAXS.dx_limit_offset.value,
        dx.soft_limit_hi.value)

    print("Removed USAXS from beam position")
    terms.SAXS.UsaxsSaxsMode.put(UsaxsSaxsModes["out of beam"])


def move_USAXSIn():
    plc_protect.stop_if_tripped()
    ccd_shutter.close()
    ti_filter_shutter.close()
    print("Moving to USAXS mode")

    confirmUsaxsSaxsOutOfBeam()
    plc_protect.wait_for_interlock()

    # in case there is an error in moving, it is NOT SAFE to start a scan
    terms.SAXS.UsaxsSaxsMode.put(UsaxsSaxsModes["dirty"])

    # move USAXS in the beam
    # set the limits so we can move pinhole in place.
    ax = a_stage.x
    dx = d_stage.x
    ax.set_lim(
        terms.SAXS.ax_in.value - terms.SAXS.ax_limit_offset.value,
        ax.soft_limit_hi.value)
    dx.set_lim(
        dx.soft_limit_hi.value,
        terms.USAXS.diode.dx.value + terms.SAXS.dx_limit_offset.value)

    guard_slit.set_size(
        h = terms.SAXS.usaxs_guard_h_size.value, 
        v = terms.SAXS.usaxs_guard_v_size.value,
    )

    move_motors(
        usaxs_slit.vap, terms.SAXS.usaxs_v_size.value,
        usaxs_slit.hap, terms.SAXS.usaxs_h_size.value,
        a_stage.y,      terms.USAXS.AY0.value,
        a_stage.x,      terms.SAXS.ax_in.value,
        d_stage.x,      terms.SAXS.dx_in.value,
        d_stage.y,      terms.USAXS.DY0.value,
    )

    print("USAXS is in position")
    terms.SAXS.UsaxsSaxsMode.put(UsaxsSaxsModes["USAXS in beam"])


def set_USAXS_Slits():
    #diffs = [
    #    abs(usaxs_slit.vap.value - terms.SAXS.usaxs_v_size.value),
    #    abs(usaxs_slit.hap.value - terms.SAXS.usaxs_h_size.value),
    #    abs(guard_slit.v_size.value - terms.SAXS.usaxs_guard_v_size.value),
    #    abs(guard_slit.h_size.value - terms.SAXS.usaxs_guard_h_size.value),
    #]
    # if max(diffs) > 0.01:
    comment "Moving USAXS slits and guard slits to correct place"
    # move USAXS slits and guard slits in place
    move_motors(
        usaxs_slit.vap, terms.SAXS.usaxs_v_size.value,
        usaxs_slit.hap, terms.SAXS.usaxs_h_size.value,
        guard_slit.v_size, terms.SAXS.usaxs_guard_v_size.value,
        guard_slit.h_size, terms.SAXS.usaxs_guard_h_size.value,
    )
