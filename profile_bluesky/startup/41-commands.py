print(__file__)

"""USAXS commands"""

### This file is work-in-progress
# see: https://subversion.xray.aps.anl.gov/spec/beamlines/USAXS/trunk/macros/local/usaxs_commands.mac

UsaxsSaxsMode = EpicsSignal("9idcLAX:USAXS_Pin:USAXSSAXSMode", name="UsaxsSaxsMode")
UsaxsSaxsMode_dict{
    "dirty": -1,        # prior move did not finish correctly
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
    while PauseBeforeNextScan.value > 0.5:
        msg = pv_txt % (time.time() - t0)
        print(msg)
        user_data.state.put(msg)
        time.sleep(1)
        open_the_shutter = True

    if StopBeforeNextScan.value:
        print("User requested stop data collection before next scan")
        ti_filter_shutter.close()
        StopBeforeNextScan.put(0)
        user_data.collection_in_progress.put(0)
        open_the_shutter = False

    if open_the_shutter:
        mono_shutter.open()     # waits until complete
        # time.sleep(2)         # so, sleep not needed


def checkUsaxsSaxsOutOfBeam():
    """raise ValueError if not"""
    if UsaxsSaxsMode.value != UsaxsSaxsMode_dict["out of beam"]:
        print("Found UsaxsSaxsMode = %s " % UsaxsSaxsMode.value)
        msg = "Incorrect UsaxsSaxsMode mode found."
        msg += " If SAXS, WAXS, and USAXS are out of beam, UsaxsSaxsMode.put(%d)" 
        raise ValueError(msg % UsaxsSaxsMode_dict["out of beam"])


def move_WAXSOut():
    plc_protect.stop_if_emergency_ON()
    ccd_shutter.close()
    ti_filter_shutter.close()

    print ("Moving WAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["dirty"])

    # move the pin_z away from sample
    waxsx.move(WAXS_Xout)               # FIXME: WAXS_Xout

    waxsx.set_lim(
        waxsx.soft_limit_hi.value, 
        WAXS_Xout + WAXS_XLimOffset)  # FIXME: and TEST

    print "Removed WAXS from beam position"
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["out of beam"])


def move_WAXSIn():
    plc_protect.stop_if_emergency_ON()
    ccd_shutter.close()
    ti_filter_shutter.close()
    print("Moving to WAXS mode")

    checkUsaxsSaxsOutOfBeam()

    plc_protect.wait_for_interlock()
    # in case there is an error in moving, it is NOT SAFE to start a scan
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["dirty"])

    # first move USAXS out of way
    waxsx.set_lim(
        waxsx.soft_limit_hi.value, 
        WAXS_XIn + WAXS_XLimOffset)  # FIXME: and TEST
    
    move_motors(
        guard_slit.v_size, SAXS_VGSlit,
        guard_slit.h_size, SAXS_HGSlit,
        waxsx, WAXS_XIn,
        usaxs_slit.v_size, SAXS_VSlit,
        usaxs_slit.h_size, SAXS_HSlit,
    )

    print("WAXS is in position")
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["WAXS in beam"])


def move_SAXSOut():
    plc_protect.stop_if_emergency_ON()
    ccd_shutter.close()
    ti_filter_shutter.close()

    print("Moving SAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["dirty"])
    
    pin_y = saxs_stage.y
    pin_z = saxs_stage.z
    # move the pin_z away from sample
    pin_z.move(PIN_ZOut)               # FIXME: 

    pin_z.set_lim(
        pin_z.soft_limit_hi.value, 
        PIN_ZOut - PIN_ZLimOffset)  # FIXME:
    
    # move pinhole up to out of beam position
    pin_y.y.move(PIN_YOut)               # FIXME: 

    pin_y.set_lim(
        PIN_YOut - PIN_YLimOffset),
        pin_y.soft_limit_lo.value)  # FIXME:

    print("Removed SAXS from beam position")
    ###sleep(1)    
    #waxs seems to be getting ahead of saxs limit switch
    # - should not be needed, we have plc_protect.wait_for_interlock() now. 
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["out of beam"])


def move_SAXSIn():
    plc_protect.stop_if_emergency_ON()
    ccd_shutter.close()
    ti_filter_shutter.close()
    print("Moving to Pinhole SAXS mode")

    checkUsaxsSaxsOutOfBeam()

    plc_protect.wait_for_interlock()
    # in case there is an error in moving, it is NOT SAFE to start a scan
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["dirty"])

    # first move USAXS out of way
    pin_y = saxs_stage.y
    pin_z = saxs_stage.z
    pin_y.set_lim(
        PIN_YIn - PIN_YLimOffset),
        pin_y.soft_limit_lo.value)  # FIXME:

    move_motors(
        guard_slit.v_size, SAXS_VGSlit,
        guard_slit.h_size, SAXS_HGSlit,
        pin_y, WAXS_XIn,
        usaxs_slit.v_size, SAXS_VSlit,
        usaxs_slit.h_size, SAXS_HSlit,
    )

    pin_z.set_lim(
        pin_z.soft_limit_hi.value, 
        PIN_ZIn - PIN_ZLimOffset)  # FIXME:

    # move Z _AFTER_ the others finish moving
    pin_z.move(PIN_ZIn)

    print("Pinhole SAXS is in position")
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["SAXS in beam"])


def move_USAXSOut():
    plc_protect.stop_if_emergency_ON()
    ccd_shutter.close()
    ti_filter_shutter.close()

    print("Moving USAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["dirty"])

    ax = a_stage.x
    dx = d_stage.x
    move_motors(
        ax, AX_Out,  # FIXME:
        dx, DX_Out,  # FIXME:
    )

    # now Main stages are out of place, 
    # so we can now set the limits and then move pinhole in place.
    ax.set_lim(
        AX_Out - AX_LimOffset,
        ax.soft_limit_hi.value)      # FIXME: and TEST
    dx.set_lim(
        DX_Out + DX_LimOffset,
        dx.soft_limit_hi.value)      # FIXME: and TEST

    print("Removed USAXS from beam position")
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["out of beam"])


def move_USAXSIn():
    plc_protect.stop_if_emergency_ON()
    ccd_shutter.close()
    ti_filter_shutter.close()
    print("Moving to USAXS mode")

    checkUsaxsSaxsOutOfBeam()

    plc_protect.wait_for_interlock()
    # in case there is an error in moving, it is NOT SAFE to start a scan
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["dirty"])

    # move USAXS in the beam
    # set the limits so we can move pinhole in place.
    ax = a_stage.x
    dx = d_stage.x
    ax.set_lim(
        AX_In - AX_LimOffset,
        ax.soft_limit_hi.value)      # FIXME: and TEST
    dx.set_lim(
        dx.soft_limit_hi.value),
        usaxs_terms.diode.dx.value + DX_LimOffset)  # FIXME: and TEST

    guard_slit.set_size(h=USAXS_HGSlit, v=USAXS_VGSlit)

    move_motors(
        usaxs_slit.vap = USAXS_VSlit,
        usaxs_slit.hap = USAXS_HSlit,
        a_stage.y = usaxs_terms.AY0.value,
        a_stage.x = AX_In,
        d_stage.x = DX_In,
        d_stage.y = usaxs_terms.DY0.value,
    )

    print("USAXS is in position")
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["USAXS in beam"])
