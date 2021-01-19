"""Dexela area detector(s)."""

__all__ = [
    "dexela_det",
]

from ..session_logs import logger

logger.info(__file__)

from ophyd import AreaDetector
from ophyd import DexelaDetectorCam
from ophyd import EpicsSignalWithRBV
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


class MyDexelaHDF5Plugin(EpicsDefinesHDF5FileNames, FileStoreHDF5IterativeWrite):
    """Adapt HDF5 plugin for Dexela detector(s)."""

    create_directory = ADComponent(EpicsSignalWithRBV, "CreateDirectory")
    lazy_open = ADComponent(EpicsSignalWithRBV, "LazyOpen")


class MyDexelaDetector(SingleTrigger, AreaDetector):
    """Dexela detector(s) as used by 9-ID-C USAXS."""

    cam = ADComponent(DexelaDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    proc1 = ADComponent(ProcessPlugin, "Proc1:")

    hdf1 = ADComponent(
        MyDexelaHDF5Plugin,
        suffix="HDF1:",
        root=DATABROKER_ROOT_PATH,
        write_path_template=WRITE_HDF5_FILE_PATH_DEXELA,
        read_path_template=READ_HDF5_FILE_PATH_DEXELA,
        path_semantics="windows",
    )


try:
    nm = "Dexela 2315"
    prefix = area_detector_EPICS_PV_prefix[nm]
    dexela_det = MyDexelaDetector(
        prefix, name="dexela_det", labels=["camera", "area_detector"]
    )
    dexela_det.read_attrs.append("hdf1")

    # configure the processing plugin into the chain for file writing
    proc_port = dexela_det.proc1.port_name.get()
    dexela_det.hdf1.nd_array_port.put(proc_port)
    # dexela_det.image.nd_array_port.put(proc_port)

    # avoid the need to prime the plugin
    dexela_det.hdf1.lazy_open.put(1)
    dexela_det.hdf1.create_directory.put(-5)

except TimeoutError as exc_obj:
    logger.warning(
        "Timeout connecting with %s (%s): %s", nm, prefix, exc_obj
    )
    dexela_det = None


def acquire_Dexela_N(target_acquire_time_s):
    """
    Save N frames from the Dexela as one image in an HDF file.

    ophyd code: NOT a bluesky plan
    """
    det = dexela_det
    fixed_acq_time = det.cam.acquire_time.get()
    num_frames = round(target_acquire_time_s / fixed_acq_time)

    # remember the original staging
    original_sigs = dict(
        cam=dict(**det.cam.stage_sigs),
        hdf1=dict(**det.hdf1.stage_sigs),
        proc1=dict(**det.proc1.stage_sigs),
    )

    # configure for acquisition
    det.proc1.stage_sigs["enable"] = 1  # Enable
    det.proc1.stage_sigs["enable_filter"] = 1  # Enable
    det.proc1.stage_sigs["num_filter"] = num_frames
    det.proc1.stage_sigs["filter_type"] = "Average"
    det.proc1.stage_sigs["reset_filter"] = 1
    det.proc1.stage_sigs["auto_reset_filter"] = 1
    det.proc1.stage_sigs["filter_callbacks"] = "Array N only"

    # HDF plugin should get processed image
    det.hdf1.nd_array_port.put(det.proc1.port_name.get())
    # other staging on HDF plugin is OK

    # COUNT
    det.stage()
    det.unstage()

    # restore the staging back to original
    for k, v in original_sigs.items():
        getattr(det, k).stage_sigs = dict(**v)
