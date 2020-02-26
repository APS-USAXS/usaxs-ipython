
"""
Point Grey Blackfly area detector

note: this is one of the easiest area detector setups in Ophyd
"""

__all__ = [
    'blackfly_det', 
    ]

from ..session_logs import logger
logger.info(__file__)

from ophyd import AreaDetector
from ophyd import PointGreyDetectorCam
from ophyd import SingleTrigger, ImagePlugin
from ophyd.areadetector import ADComponent

from .area_detector_common import area_detector_EPICS_PV_prefix
from .area_detector_common import _validate_AD_HDF5_path_


class MyPointGreyDetector(SingleTrigger, AreaDetector):
    """PointGrey Black Fly detector(s) as used by 9-ID-C USAXS"""
    
    cam = ADComponent(PointGreyDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")

try:
    nm = "PointGrey BlackFly"
    prefix = area_detector_EPICS_PV_prefix[nm]
    blackfly_det = MyPointGreyDetector(prefix, name="blackfly_det")
except TimeoutError as exc_obj:
    msg = f"Timeout connecting with {nm} ({prefix})"
    logger.warning(msg)
    blackfly_det = None
