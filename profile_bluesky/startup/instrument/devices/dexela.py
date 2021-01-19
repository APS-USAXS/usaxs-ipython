"""Dexela area detector(s)."""

__all__ = [
    "dexela_det",
]

from ..session_logs import logger

logger.info(__file__)

from ophyd import AreaDetector
from ophyd import DexelaDetectorCam
from ophyd import HDF5Plugin
from ophyd import ImagePlugin
from ophyd import ProcessPlugin
from ophyd import SingleTrigger
from ophyd.areadetector import ADComponent
from ophyd.areadetector.filestore_mixins import FileStoreHDF5IterativeWrite

from .area_detector_common import area_detector_EPICS_PV_prefix
from .area_detector_common import DATABROKER_ROOT_PATH
from .area_detector_common import EpicsDefinesHDF5FileNames
from .area_detector_common import _validate_AD_FileWriter_path_


# FIXME: can this be correct?
# Dexela IOC is on Windows.
# Is the file store drive mapped to usaxscontrol?
# ---
# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# path seen by detector IOC
WRITE_HDF5_FILE_PATH_DEXELA = (
    "W:\\USAXS_data\\test\\dexela\\%Y\\%m\\%d\\"
)
# path seen by databroker
READ_HDF5_FILE_PATH_DEXELA = "/share1/USAXS_data/test/dexela/%Y/%m/%d/"

_validate_AD_FileWriter_path_(
    # usually, 2nd argument is DATABROKER_ROOT_PATH
    # but this is Windows IOC and that needs this change
    WRITE_HDF5_FILE_PATH_DEXELA, "W:\\USAXS_data"
)


class MyDexelaHDF5Plugin(HDF5Plugin, FileStoreHDF5IterativeWrite):
    """Adapt HDF5 plugin for Dexela detector(s)."""


class MyDexelaDetector(SingleTrigger, AreaDetector):
    """Dexela detector(s) as used by 9-ID-C USAXS."""

    cam = ADComponent(DexelaDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    proc = ADComponent(ProcessPlugin, "Proc:")

    hdf1 = ADComponent(
        EpicsDefinesHDF5FileNames,
        suffix="HDF1:",
        root=DATABROKER_ROOT_PATH,
        write_path_template=WRITE_HDF5_FILE_PATH_DEXELA,
        read_path_template=READ_HDF5_FILE_PATH_DEXELA,
    )


try:
    nm = "Dexela 2315"
    prefix = area_detector_EPICS_PV_prefix[nm]
    dexela_det = MyDexelaDetector(
        prefix, name="dexela_det", labels=["camera", "area_detector"]
    )
    dexela_det.read_attrs.append("hdf1")
except TimeoutError as exc_obj:
    logger.warning(
        "Timeout connecting with %s (%s): %s", nm, prefix, exc_obj
    )
    dexela_det = None
