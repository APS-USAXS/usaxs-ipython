
"""
move the parts of the instrument in and out
"""

__all__ = """
    mode_USAXS
    UsaxsSaxsModes
""".split()

from ..session_logs import logger
logger.info(__file__)

from bluesky import plan_stubs as bps

from ..devices import a_stage, d_stage, saxs_stage
from ..devices import ccd_shutter, ti_filter_shutter
from ..devices import guard_slit, usaxs_slit
from ..devices import plc_protect
from ..devices import terms
from ..devices import user_data
from ..devices import waxsx
from ..utils import angle2q, q2angle
from ..utils import becplot_prune_fifo


UsaxsSaxsModes = {
    "dirty": -1,        # moving or prior move did not finish correctly
    "out of beam": 1,   # SAXS, WAXS, and USAXS out of beam
    "USAXS in beam": 2,
    "SAXS in beam": 3,
    "WAXS in beam": 4,
    "Imaging in": 5,
    "Imaging tuning": 6,
}

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
