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
    pass


def mode_WAXS():
    pass


def mode_radiography():
    pass


def mode_imaging():
    pass


def mode_pinSAXS():
    pass


def mode_OpenBeamPath():
    StopIfPLCEmergencyProtectionOn()
    user_data.state.put("Moving USAXS to OpenBeamPath mode")
    ccd_shutter.close()
    ti_filter_shutter.close()
    if UsaxsSaxsMode.value != 1:
        print("Found UsaxsSaxsMode = {}".format(UsaxsSaxsMode.value))
        print("Opening the beam path, moving all components out")
        move_SAXSOut()
        move_WAXSOut()
        move_USAXSOut()
        user_data.state.put("USAXS moved to OpenBeamPath mode")


use_mode.add(mode_USAXS, "USAXS")
use_mode.add(mode_SBUSAXS, "SBUSAXS")
use_mode.add(mode_SAXS, "SAXS")
use_mode.add(mode_WAXS, "WAXS")
use_mode.add(mode_radiography, "radiography")
use_mode.add(mode_imaging, "imaging")
use_mode.add(mode_pinSAXS, "pinSAXS")
use_mode.add(mode_OpenBeamPath, "OpenBeamPath")
use_mode.dir
