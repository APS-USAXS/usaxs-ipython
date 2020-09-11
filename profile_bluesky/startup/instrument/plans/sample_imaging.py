
"""
take an image of the sample
"""

__all__ = ["no_run_trigger_and_wait",]

from ..session_logs import logger
logger.info(__file__)

from ..devices import blackfly_optical
from ..utils.setup_new_user import techniqueSubdirectory
from bluesky import plan_stubs as bps
import os


def record_sample_image_on_demand(technique_name, _md):
    """
    take an image of the sample
    """
    if blackfly_optical.should_save_jpeg:
        uascan_path = techniqueSubdirectory(technique_name)
        yield from bps.mv(
            blackfly_optical.jpeg1.file_path,
            "/mnt" + os.path.abspath(uascan_path) + "/"  # MUST end with "/"
            )
        yield from blackfly_optical.take_image()
        jpeg_name = blackfly_optical.jpeg1.full_file_name.get()
        if jpeg_name.startswith("/mnt/share1"):
            jpeg_name = jpeg_name[4:]
        if os.path.exists(jpeg_name):
            _md["sample_image_jpeg"] = jpeg_name
    else:
        yield from bps.null()
