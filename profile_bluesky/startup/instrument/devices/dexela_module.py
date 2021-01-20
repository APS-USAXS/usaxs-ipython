"""Dexela area detector(s)."""

__all__ = [
    "dexela_det",
]

from collections import OrderedDict
from ophyd import ADComponent
from ophyd import DexelaDetector
# from ophyd import HDF5Plugin
from ophyd import ImagePlugin
from ophyd import ProcessPlugin
from ophyd import SingleTrigger
from ophyd.areadetector.filestore_mixins import FileStoreHDF5IterativeWrite
# from ophyd.areadetector.filestore_mixins import new_short_uid
from ophyd.areadetector.plugins import HDF5Plugin_V34
import datetime
import time
from ..session_logs import logger

logger.info(__file__)

from .area_detector_common import area_detector_EPICS_PV_prefix
from .area_detector_common import _validate_AD_FileWriter_path_


# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# path seen by detector IOC
WRITE_HDF5_FILE_PATH_DEXELA = r"W:\\USAXS_data\\test\\dexela\\%Y\\%m\\%d\\"
# path seen by databroker
READ_HDF5_FILE_PATH_DEXELA = "/share1/USAXS_data/test/dexela/%Y/%m/%d/"

# usually, 2nd argument is DATABROKER_ROOT_PATH
# but this is Windows IOC which needs this change
_validate_AD_FileWriter_path_(
    WRITE_HDF5_FILE_PATH_DEXELA, r"W:\\USAXS_data",
)


class MyHDF5Plugin(FileStoreHDF5IterativeWrite, HDF5Plugin_V34):
    def make_filename(self):
        """Override from AD.filestore_mixins.FileStorePluginBase."""
        # filename = new_short_uid()
        filename = self.file_name.get()  # get name from EPICS PV
        now = datetime.datetime.now()
        write_path = now.strftime(self.write_path_template) + "\\"  # the FIX!
        read_path = now.strftime(self.read_path_template)
        return filename, read_path, write_path


class MyProcessPlugin(ProcessPlugin):

    pool_max_buffers = None


class MyDexelaDetector(SingleTrigger, DexelaDetector):
    """Dexela detector(s) as used by 9-ID-C USAXS."""

    hdf1 = ADComponent(
        MyHDF5Plugin,
        "HDF1:",
        write_path_template=WRITE_HDF5_FILE_PATH_DEXELA,
        read_path_template=READ_HDF5_FILE_PATH_DEXELA,
        path_semantics="windows",
    )
    image = ADComponent(ImagePlugin, "image1:")
    proc1 = ADComponent(MyProcessPlugin, "Proc1:")


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

    # MUST come before staging writes file_path
    dexela_det.hdf1.create_directory.put(-5)

    dexela_det.hdf1.file_name.put("bluesky")


except TimeoutError as exc_obj:
    logger.warning("Timeout connecting with %s (%s): %s", nm, prefix, exc_obj)
    dexela_det = None


def _acquire_Dexela_N(target_acquire_time_s):
    """
    Save N frames from the Dexela as one image in an HDF file.

    ophyd code: NOT a bluesky plan
    """
    det = dexela_det
    fixed_acq_time = det.cam.acquire_time.get()
    num_frames = round(target_acquire_time_s / fixed_acq_time)
    logger.info(
        "acquire time of %f s, will acquire %d frames",
        target_acquire_time_s,
        num_frames,
    )

    # remember the original staging
    # fmt: off
    original_sigs = {
        k: dict(**getattr(det, k).stage_sigs)
        for k in "cam hdf1 proc1".split()
    }
    # fmt: on

    # configure for acquisition
    det.proc1.stage_sigs["enable"] = 1  # Enable
    det.proc1.stage_sigs["enable_filter"] = 1  # Enable
    det.proc1.stage_sigs["num_filter"] = num_frames
    det.proc1.stage_sigs["filter_type"] = "Average"
    det.proc1.stage_sigs["reset_filter"] = 1
    det.proc1.stage_sigs["auto_reset_filter"] = 1
    det.proc1.stage_sigs["filter_callbacks"] = "Array N only"

    det.hdf1.stage_sigs = OrderedDict()
    det.hdf1.stage_sigs["enable"] = 1
    det.hdf1.stage_sigs["blocking_callbacks"] = "Yes"
    det.hdf1.stage_sigs["parent.cam.array_callbacks"] = 1
    det.hdf1.stage_sigs["auto_increment"] = "Yes"
    det.hdf1.stage_sigs["array_counter"] = 0
    det.hdf1.stage_sigs["auto_save"] = "Yes"
    det.hdf1.stage_sigs["num_capture"] = 0
    det.hdf1.stage_sigs["file_template"] = "%s%s_%6.6d.h5"
    det.hdf1.stage_sigs["file_write_mode"] = "Capture"
    # avoid the need to prime the plugin
    det.hdf1.stage_sigs["lazy_open"] = 1
    det.hdf1.stage_sigs["compression"] = "LZ4"
    det.hdf1.stage_sigs["capture"] = 1

    # HDF plugin should get processed image
    det.hdf1.nd_array_port.put(det.proc1.port_name.get())
    # other staging on HDF plugin is OK

    logger.debug("staging ...")
    det.stage()
    t0 = time.time()
    logger.debug("triggering ...")
    det.trigger()
    logger.info("sleep: %f s", target_acquire_time_s)
    time.sleep(target_acquire_time_s)
    while det.cam.acquire.get() not in (0, "Stop", "Done"):
        time.sleep(0.02)
    logger.info("acquire time: %.2f s", (time.time() - t0))
    logger.debug("unstaging ...")
    det.unstage()

    # restore the staging back to original
    for k, v in original_sigs.items():
        getattr(det, k).stage_sigs = dict(**v)
    logger.debug("acquire complete")
