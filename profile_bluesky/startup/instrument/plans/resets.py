
"""
Reset the instrument.
"""

__all__ = [
    'reset_USAXS', 
    ]

from ..session_logs import logger
logger.info(__file__)

from apstools.devices import SCALER_AUTOCOUNT_MODE
from bluesky import plan_stubs as bps

from ..devices import a_stage, as_stage, d_stage
from ..devices import AutorangeSettings
from ..devices import email_notices, NOTIFY_ON_RESET
from ..devices import I0_controls, I00_controls, trd_controls, upd_controls
from ..devices import scaler0
from ..devices import terms
from ..devices import ti_filter_shutter
from ..devices import user_data
from .mono_feedback import DCMfeedbackON


def reset_USAXS():  
    """
    bluesky plan to set USAXS instrument in safe configuration
    """
    logger.info("Resetting USAXS")
    yield from user_data.set_state_plan("resetting motors")
    yield from DCMfeedbackON()
    yield from bps.mv(
        scaler0.count_mode, SCALER_AUTOCOUNT_MODE,
        upd_controls.auto.mode, AutorangeSettings.auto_background,
        I0_controls.auto.mode, AutorangeSettings.manual,
        I00_controls.auto.mode, AutorangeSettings.manual,
        ti_filter_shutter, "close",
        user_data.scanning, "no",
    )
    move_list = [
        d_stage.y, terms.USAXS.DY0.get(),
        a_stage.y, terms.USAXS.AY0.get(),
        a_stage.r, terms.USAXS.ar_val_center.get(),
    ]
    if terms.USAXS.useSBUSAXS.get():
        move_list += [
            as_stage.rp, terms.USAXS.ASRP0.get(),
            ]
    yield from bps.mv(*move_list)  # move all motors at once
    # TITLE = SPEC_STD_TITLE

    yield from user_data.set_state_plan("USAXS reset complete")
    if NOTIFY_ON_RESET:
        email_notices.send(
            "USAXS has reset",
            "spec has encountered a problem and reset the USAXS."
            )

    yield from bps.mv(
        user_data.collection_in_progress, 0,    #despite the label, 0 means not collecting
    )
