
"""
ADsimdetector area detector
"""

__all__ = [
    'adsimdet', 
    ]

from ..session_logs import logger
logger.info(__file__)

from .area_detector_common import area_detector_EPICS_PV_prefix
from .area_detector_common import DATABROKER_ROOT_PATH
from .area_detector_common import EpicsDefinesHDF5FileNames
from .area_detector_common import _validate_AD_HDF5_path_
from ophyd import AreaDetector
from ophyd import SimDetectorCam
from ophyd import Component, Device, EpicsSignalWithRBV
from ophyd import SingleTrigger, ImagePlugin, HDF5Plugin
from ophyd.areadetector import ADComponent
from ophyd.areadetector.filestore_mixins import FileStoreHDF5IterativeWrite


# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# path seen by detector IOC
WRITE_HDF5_FILE_PATH_ADSIMDET = "/share1/USAXS_data/test/adsimdet/%Y/%m/%d/"
# path seen by databroker
READ_HDF5_FILE_PATH_ADSIMDET = WRITE_HDF5_FILE_PATH_ADSIMDET

_validate_AD_HDF5_path_(WRITE_HDF5_FILE_PATH_ADSIMDET, DATABROKER_ROOT_PATH)
_validate_AD_HDF5_path_(READ_HDF5_FILE_PATH_ADSIMDET, DATABROKER_ROOT_PATH)


class MySimDetector(SingleTrigger, AreaDetector):
    """ADSimDetector instance used by 9-ID-C USAXS"""
    
    cam = ADComponent(SimDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    hdf1 = ADComponent(
        EpicsDefinesHDF5FileNames, 
        suffix = "HDF1:", 
        root = DATABROKER_ROOT_PATH,
        write_path_template = WRITE_HDF5_FILE_PATH_ADSIMDET,
        read_path_template = READ_HDF5_FILE_PATH_ADSIMDET,
        )


try:
    nm = "SimDetector"
    prefix = area_detector_EPICS_PV_prefix[nm]
    adsimdet = MySimDetector(prefix, name="adsimdet")
except TimeoutError as exc_obj:
    msg = f"Timeout connecting with {nm} ({prefix})"
    logger.warning(msg)
    adsimdet = None
