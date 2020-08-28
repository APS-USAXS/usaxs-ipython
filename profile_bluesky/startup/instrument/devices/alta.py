
"""
Apogee Alta area detector
"""

__all__ = [
    'alta_det', 
    ]

from ..session_logs import logger
logger.info(__file__)

from ophyd import AreaDetector
from ophyd import CamBase
from ophyd import Component, Device, EpicsSignalWithRBV
from ophyd import SingleTrigger, ImagePlugin
from ophyd.areadetector import ADComponent

from .area_detector_common import area_detector_EPICS_PV_prefix
from .area_detector_common import DATABROKER_ROOT_PATH
from .area_detector_common import EpicsDefinesHDF5FileNames
from .area_detector_common import _validate_AD_HDF5_path_

# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# path seen by detector IOC
WRITE_HDF5_FILE_PATH_ALTA = "/mnt/share1/USAXS_data/test/alta/%Y/%m/%d/"

# path seen by databroker
READ_HDF5_FILE_PATH_ALTA = "/share1/USAXS_data/test/alta/%Y/%m/%d/"


_validate_AD_HDF5_path_(WRITE_HDF5_FILE_PATH_ALTA, DATABROKER_ROOT_PATH)
_validate_AD_HDF5_path_(READ_HDF5_FILE_PATH_ALTA, DATABROKER_ROOT_PATH)

class MyAltaCam(CamBase):
    """support for Apogee Alta detector"""
    _html_docs = []
    temperature = Component(EpicsSignalWithRBV, 'Temperature')


class MyAltaDetector(SingleTrigger, AreaDetector):
    """Alta detector as used by 9-ID-C USAXS Imaging"""
    
    cam = ADComponent(MyAltaCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    
    hdf1 = ADComponent(
        EpicsDefinesHDF5FileNames,
        suffix = "HDF1:", 
        root = DATABROKER_ROOT_PATH,
        write_path_template = WRITE_HDF5_FILE_PATH_ALTA,
        read_path_template = READ_HDF5_FILE_PATH_ALTA,
        )


try:
    nm = "Alta"
    prefix = area_detector_EPICS_PV_prefix[nm]
    alta_det = MyAltaDetector(
        prefix, name="alta_det",
        labels=["camera", "area_detector"])
    alta_det.read_attrs.append("hdf1")
except TimeoutError as exc_obj:
    msg = f"Timeout connecting with {nm} ({prefix})"
    logger.warning(msg)
    alta_det = None
