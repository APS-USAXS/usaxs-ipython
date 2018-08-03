print(__file__)

"""
USAXS mode change procedures

see: https://subversion.xray.aps.anl.gov/spec/beamlines/USAXS/trunk/macros/local/usaxs_commands.mac

each mode is defined by a setup function that takes no arguments
and returns only when it complete

EXAMPLE::

    def demo():
        print(1)
        m1.move(5)
        print(2)
        time.sleep(2)
        print(3)
        m1.move(0)
        print(4)


    use_mode.add(demo)

"""



def mode_USAXS():
    pass


def mode_SBUSAXS():
    pass


def mode_SAXS():
    plc_protect.stop_if_emergency_ON()
    epics_put ("9idcLAX:USAXS:state", sprintf("%s", "Moving USAXS to SAXS mode" ))
    ccd_shutter.close()
    ti_filter_shutter.close()

    if terms.SAXS.UsaxsSaxsMode.value != UsaxsSaxsModes["SAXS in beam"]:
        print("Found UsaxsSaxsMode = {}".format(UsaxsSaxsMode.value))
        print("Moving to proper SAXS mode")
        move_WAXSOut()
        move_USAXSOut()
        move_SAXSIn()
        
    print("Prepared for SAXS mode")
    #insertScanFilters
    user_data.set_state("SAXS Mode")
    ts = str(datetime.now()
    user_data.time_stamp.put(ts)
    user_data.macro_file_time.put(ts)
    user_data.scanning.put(0)


def mode_WAXS():
    plc_protect.stop_if_emergency_ON()
    epics_put ("9idcLAX:USAXS:state", sprintf("%s", "Moving USAXS to WAXS mode" ))
    ccd_shutter.close()
    ti_filter_shutter.close()

    if terms.SAXS.UsaxsSaxsMode.value != UsaxsSaxsModes["WAXS in beam"]:
        print("Found UsaxsSaxsMode = {}".format(UsaxsSaxsMode.value))
        print("Moving to proper WAXS mode")
        move_SAXSOut()
        move_USAXSOut()
        move_WAXSIn()

    # move SAXS slits in, used for WAXS mode also
    v_diff = abs(guard_slit.v_size.value - terms.SAXS.guard_v_size.value)
    h_diff = abs(guard_slit.h_size.value - terms.SAXS.guard_h_size.value)

    if max(v_diff, h_diff) > 0.03:
        print("changing G slits")
        guard_slit.set_size(h=terms.SAXS.guard_h_size.value, v=terms.SAXS.guard_v_size.value)
        time.sleep(0.5)  
        while max(v_diff, h_diff) > 0.02:
            time.sleep(0.5)
            v_diff = abs((guard_slit.top.value-guard_slit.bot.value) - terms.SAXS.guard_v_size.value)
            h_diff = abs((guard_slit.outb.value-guard_slit.inb.value) - terms.SAXS.guard_h_size.value)
       
    v_diff = abs(usaxs_slit.v_size.value- terms.SAXS.v_size.value)
    h_diff = abs(usaxs_slit.h_size.value-terms.SAXS.h_size.value)
    if max(v_diff, h_diff) > 0.02:
       print "Moving Beam defining slits"
       usaxs_slit.set_size(h=terms.SAXS.h_size.value, v=terms.SAXS.v_size.value)
       time.sleep(2)     # wait for backlash, seems these motors are slow and spec gets ahead of them?

    print("Prepared for WAXS mode")
    #insertScanFilters
    user_data.set_state("WAXS Mode")
    ts = str(datetime.now()
    user_data.time_stamp.put(ts)
    user_data.macro_file_time.put(ts)
    user_data.scanning.put(0)


def mode_radiography():
    pass


def mode_imaging():
    pass


def mode_pinSAXS():
    pass


def mode_OpenBeamPath():
    plc_protect.stop_if_emergency_ON()
    user_data.set_state("Moving USAXS to OpenBeamPath mode")
    ccd_shutter.close()
    ti_filter_shutter.close()
    if terms.SAXS.UsaxsSaxsMode.value != UsaxsSaxsModes["out of beam"]:
        print("Found UsaxsSaxsMode = {}".format(UsaxsSaxsMode.value))
        print("Opening the beam path, moving all components out")
        move_SAXSOut()
        move_WAXSOut()
        move_USAXSOut()
        user_data.set_state("USAXS moved to OpenBeamPath mode")


use_mode.add(mode_USAXS, "USAXS")
use_mode.add(mode_SBUSAXS, "SBUSAXS")
use_mode.add(mode_SAXS, "SAXS")
use_mode.add(mode_WAXS, "WAXS")
use_mode.add(mode_radiography, "radiography")
use_mode.add(mode_imaging, "imaging")
use_mode.add(mode_pinSAXS, "pinSAXS")
use_mode.add(mode_OpenBeamPath, "OpenBeamPath")
use_mode.dir
