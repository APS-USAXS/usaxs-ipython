
"""
shutters
"""

__all__ = [
    'ccd_shutter',
    'FE_shutter',
    'mono_shutter',
    'ti_filter_shutter',
    'usaxs_shutter',
]

from ..session_logs import logger
logger.info(__file__)


from apstools.devices import ApsPssShutterWithStatus
from apstools.devices import EpicsOnOffShutter
from apstools.devices import SimulatedApsPssShutterWithStatus
import time

from .aps_source import aps
from .permit import operations_in_9idc


if aps.inUserOperations and operations_in_9idc():
    FE_shutter = ApsPssShutterWithStatus(
        "9ida:rShtrA:",
        "PA:09ID:STA_A_FES_OPEN_PL.VAL",
        name="FE_shutter")

    mono_shutter = ApsPssShutterWithStatus(
        "9ida:rShtrB:",
        "PA:09ID:STA_B_SBS_OPEN_PL.VAL",
        name="mono_shutter")

    usaxs_shutter = EpicsOnOffShutter(
        "9idcLAX:userTran3.A",
        name="usaxs_shutter")

else:
    logger.warning("!"*30)
    if operations_in_9idc():
        logger.warning("Session started when APS not operating.")
    else:
        logger.warning("Session started when 9ID-C is not operating.")
    logger.warning("Using simulators for all shutters.")
    logger.warning("!"*30)
    FE_shutter = SimulatedApsPssShutterWithStatus(name="FE_shutter")
    mono_shutter = SimulatedApsPssShutterWithStatus(name="mono_shutter")
    usaxs_shutter = SimulatedApsPssShutterWithStatus(name="usaxs_shutter")


ti_filter_shutter = usaxs_shutter       # alias
ti_filter_shutter.delay_s = 0.2         # shutter needs some recovery time

ccd_shutter = EpicsOnOffShutter("9idcRIO:Galil2Bo0_CMD", name="ccd_shutter")


connect_delay_s = 1
while not mono_shutter.pss_state.connected:
    logger.info(f"Waiting {connect_delay_s}s for mono shutter PV to connect")
    time.sleep(connect_delay_s)
