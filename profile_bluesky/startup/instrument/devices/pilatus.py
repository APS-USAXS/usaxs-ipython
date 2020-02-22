
"""
Dectris Pilatus area detectors
"""

__all__ = [
    'saxs_det',
    'waxs_det',
    ]

from ..session_logs import logger
logger.info(__file__)

from .area_detector_common import area_detector_EPICS_PV_prefix
from .area_detector_common import DATABROKER_ROOT_PATH
from .area_detector_common import EpicsDefinesHDF5FileNames
from .area_detector_common import _validate_AD_HDF5_path_
from ophyd import AreaDetector
from ophyd import PilatusDetectorCam
from ophyd import Component, Device, EpicsSignalWithRBV
from ophyd import SingleTrigger, ImagePlugin, HDF5Plugin
from ophyd.areadetector import ADComponent
from ophyd.areadetector.filestore_mixins import FileStoreHDF5IterativeWrite


# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# path seen by detector IOC
WRITE_HDF5_FILE_PATH_PILATUS = "/mnt/usaxscontrol/USAXS_data/test/pilatus/%Y/%m/%d/"
# path seen by databroker
READ_HDF5_FILE_PATH_PILATUS = "/share1/USAXS_data/test/pilatus/%Y/%m/%d/"

_validate_AD_HDF5_path_(WRITE_HDF5_FILE_PATH_PILATUS, DATABROKER_ROOT_PATH)
    

class MyPilatusHDF5Plugin(HDF5Plugin, FileStoreHDF5IterativeWrite):
    """adapt HDF5 plugin for Pilatus detector"""
    

class MyPilatusDetector(SingleTrigger, AreaDetector):
    """Pilatus detector(s) as used by 9-ID-C USAXS"""
    
    cam = ADComponent(PilatusDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    
    hdf1 = ADComponent(
        EpicsDefinesHDF5FileNames, 
        suffix = "HDF1:", 
        root = DATABROKER_ROOT_PATH,
        write_path_template = WRITE_HDF5_FILE_PATH_PILATUS,
        read_path_template = READ_HDF5_FILE_PATH_PILATUS,
        )


try:
    nm = "Pilatus 100k"
    prefix = area_detector_EPICS_PV_prefix[nm]
    saxs_det = MyPilatusDetector(prefix, name="saxs_det")
    saxs_det.read_attrs.append("hdf1")
except TimeoutError as exc_obj:
    msg = f"Timeout connecting with {nm} ({prefix})"
    logger.warning(msg)
    saxs_det = None

try:
    nm = "Pilatus 200kw"
    prefix = area_detector_EPICS_PV_prefix[nm]
    waxs_det = MyPilatusDetector(prefix, name="waxs_det")
    waxs_det.read_attrs.append("hdf1")
except TimeoutError as exc_obj:
    msg = f"Timeout connecting with {nm} ({prefix})"
    logger.warning(msg)
    waxs_det = None
