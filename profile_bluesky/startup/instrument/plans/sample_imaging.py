
"""
take an image of the sample
"""

__all__ = ["record_sample_image_on_demand",]

from ..session_logs import logger
logger.info(__file__)

from ..devices import blackfly_optical
from ..devices import terms
from ..utils.setup_new_user import techniqueSubdirectory
from bluesky import plan_stubs as bps
import os


def record_sample_image_on_demand(technique_name, title, _md):
    """
    take an image of the sample

    If a sample image is taken, the full path to the image
    is added to the (RunEngine) metadata.

    PARAMETERS

    technique_name
        *str* :
        Used to pick the subdirectory.  One of "saxs", "usaxs", or "waxs"
    _md
        *dict* :
        Metadata dictionary additions from the calling plan.
    """
    if blackfly_optical.should_save_jpeg:
        uascan_path = techniqueSubdirectory(technique_name)
        yield from bps.mv(
            blackfly_optical.jpeg1.file_path,
            "/mnt" + os.path.abspath(uascan_path) + "/",  # MUST end with "/"
            
            blackfly_optical.jpeg1.file_name, title,
            blackfly_optical.jpeg1.file_number, terms.FlyScan.order_number,
            )
        yield from blackfly_optical.take_image()
        jpeg_name = blackfly_optical.jpeg1.full_file_name.get()
        if jpeg_name.startswith("/mnt/share1"):
            jpeg_name = jpeg_name[4:]
        if os.path.exists(jpeg_name):
            _md["sample_image_jpeg"] = jpeg_name
    else:
        yield from bps.null()
