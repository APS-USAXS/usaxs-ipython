
"""
Support the different instrument modes
"""

### This file is work-in-progress
# see: https://subversion.xray.aps.anl.gov/spec/beamlines/USAXS/trunk/macros/local/usaxs_commands.mac

__all__ = """
    mode_imaging
    mode_OpenBeamPath
    mode_Radiography
    mode_SAXS
    mode_SBUSAXS
    mode_USAXS
    mode_WAXS
""".split()

from ..session_logs import logger
logger.info(__file__)

from apstools.devices import SCALER_AUTOCOUNT_MODE
from bluesky import plan_stubs as bps
import datetime

from ..devices import a_stage, d_stage, saxs_stage
from ..devices import aps
from ..devices import ccd_shutter, mono_shutter, ti_filter_shutter
from ..devices import guard_slit, usaxs_slit
from ..devices import monochromator, MONO_FEEDBACK_ON
from ..devices import plc_protect
from ..devices import scaler0
from ..devices import terms
from ..devices import user_data
from .filters import insertRadiographyFilters
from .filters import insertScanFilters
from .mono_feedback import DCMfeedbackON
from .move_instrument import *


def confirm_instrument_mode(mode_name):
    """
    True if instrument is in the named mode

    Parameter

    mode_name (str) :
        One of the strings defined in ``UsaxsSaxsModes``
    """
    expected_mode = UsaxsSaxsModes[mode_name]
    return terms.SAXS.UsaxsSaxsMode.get() in (expected_mode, mode_name)


def mode_USAXS():
    # plc_protect.stop_if_tripped()
    yield from user_data.set_state_plan("Moving USAXS to USAXS mode")
    yield from bps.mv(
        ccd_shutter,        "close",
        ti_filter_shutter,  "close",
        d_stage.x, terms.USAXS.diode.dx.get(),
        d_stage.y, terms.USAXS.diode.dy.get(),
        guard_slit.h_size,  terms.SAXS.usaxs_guard_h_size.get(),
        guard_slit.v_size,  terms.SAXS.usaxs_guard_v_size.get(),
        usaxs_slit.h_size,  terms.SAXS.usaxs_h_size.get(),
        usaxs_slit.v_size,  terms.SAXS.usaxs_v_size.get(),
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
    v_diff = abs(guard_slit.v_size.get() - terms.SAXS.guard_v_size.get())
    h_diff = abs(guard_slit.h_size.get() - terms.SAXS.guard_h_size.get())
    logger.debug("guard slits horizontal difference = %g" % h_diff)
    logger.debug("guard slits vertical difference = %g" % v_diff)

    if max(v_diff, h_diff) > 0.03:
        logger.info("changing Guard slits")
        yield from bps.mv(
            guard_slit.h_size, terms.SAXS.guard_h_size.get(),
            guard_slit.v_size, terms.SAXS.guard_v_size.get(),
        )
        # TODO: need completion indication
        #  guard_slit is calculated by a database
        #  support needs a handler that does this wait for us.
        yield from bps.sleep(0.5)           # TODO: needed now?

    v_diff = abs(usaxs_slit.v_size.position - terms.SAXS.v_size.get())
    h_diff = abs(usaxs_slit.h_size.position - terms.SAXS.h_size.get())
    logger.debug("USAXS slits horizontal difference = %g" % h_diff)
    logger.debug("USAXS slits vertical difference = %g" % v_diff)

    if max(v_diff, h_diff) > 0.02:
       logger.info("Moving Beam defining slits")
       yield from bps.mv(
           usaxs_slit.h_size, terms.SAXS.h_size.get(),
           usaxs_slit.v_size, terms.SAXS.v_size.get(),
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
        ccd_shutter, "close",
    )
  
    yield from bps.mv(
        # move to ccd position 
        d_stage.x, terms.USAXS.ccd.dx.get(),
        d_stage.y, terms.USAXS.ccd.dy.get(),
        # make sure slits are in place
        usaxs_slit.v_size,  terms.SAXS.usaxs_v_size.get(),
        usaxs_slit.h_size,  terms.SAXS.usaxs_h_size.get(),
        guard_slit.v_size,  terms.SAXS.usaxs_guard_v_size.get(),
        guard_slit.h_size,  terms.SAXS.usaxs_guard_h_size.get(),
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

    if aps.shutter_permit.get() in (1, 'PERMIT'):
        yield from bps.mv(
            mono_shutter, "open",
        )

    if mono_shutter.state == "open":
        msg = "TV should now show Radiography CCD image."
    else:
        msg = "The mono shutter is closed now.  APS beam dump?"

    msg += """
    
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
