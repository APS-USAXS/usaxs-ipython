
"""
support area detector
"""

__all__ = [
    'areaDetectorAcquire',
]

from ..session_logs import logger
logger.info(__file__)

from bluesky import plans as bp
from bluesky import plan_stubs as bps
import time

from ..devices import user_data
from ..framework import RE
from ..utils.reporter import remaining_time_reporter


def areaDetectorAcquire(det, md=None):
    """
    acquire image(s) from the named area detector
    """
    _md = md or {}
    acquire_time = det.cam.acquire_time.get()
    # Note: AD's HDF File Writer can use up to 5 seconds to finish writing the file

    t0 = time.time()
    yield from bps.mv(
        user_data.scanning, "scanning",          # we are scanning now (or will be very soon)
    )
    logger.debug(f"areaDetectorAcquire(): {det.hdf1.stage_sigs}")
    _md["method"] = "areaDetectorAcquire"
    _md["area_detector_name"] = det.name
    if _md.get("plan_name") is None:
        _md["plan_name"] = "image"

    if RE.state != "idle":
        remaining_time_reporter(_md["plan_name"], acquire_time)

    yield from bp.count([det], md=_md)          # TODO: SPEC showed users incremental progress (1 Hz updates) #175

    yield from bps.mv(user_data.scanning, "no",)  # we are done
    elapsed = time.time() - t0
    logger.info(f"Finished SAXS/WAXS data collection in {elapsed} seconds.")
