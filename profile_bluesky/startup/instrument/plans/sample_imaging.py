
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
        det = blackfly_optical  # define once here, in case it ever changes
        path = techniqueSubdirectory(technique_name)
        yield from bps.mv(
            det.jpeg1.file_path,
            "/mnt" + os.path.abspath(path) + "/",  # MUST end with "/"

            det.jpeg1.file_name, title,
            det.jpeg1.file_number, terms.FlyScan.order_number.get(),
            )

        yield from det.take_image()

        jpeg_name = det.jpeg1.full_file_name.get()
        if jpeg_name.startswith("/mnt/share1"):
            jpeg_name = jpeg_name[4:]
        if os.path.exists(jpeg_name):
            _md["sample_image_jpeg"] = jpeg_name
    else:
        yield from bps.null()
