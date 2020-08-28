
"""
support USAXS area detectors

replace BlueSky file name scheme when used with area detector

file systems on some area detectors need more work

* saxs:  /mnt/share1/USAXS_data/yyyy-mm/user_working_folder_saxs/
* waxs:  /mnt/usaxscontrol/USAXS_data/yyyy-mm/user_working_folder_waxs/
* PointGrey BlackFly does not write out to file typically.  No use of HDF5 plugin.
* Alta: /mnt/share1/USAXS_data/...
"""

__all__ = [
    'area_detector_EPICS_PV_prefix',
    'DATABROKER_ROOT_PATH', 
    'EpicsDefinesHDF5FileNames',
    'myHdf5EpicsIterativeWriter',
    'myHDF5FileNames',
    '_validate_AD_FileWriter_path_',
    ]

from ..session_logs import logger
logger.info(__file__)

from apstools.devices import AD_EpicsHdf5FileName
from ophyd import HDF5Plugin
from ophyd.areadetector.filestore_mixins import FileStoreIterativeWrite

DATABROKER_ROOT_PATH = "/"

area_detector_EPICS_PV_prefix = {
    'Pilatus 100k' : 'usaxs_pilatus1:',
    'Pilatus 200kw' : 'usaxs_pilatus2:',
    'PointGrey BlackFly Radiography' : '9idFLY:',
    'PointGrey BlackFly' : '9idFLY1:',
    'PointGrey BlackFly Optical' : '9idFLY2:',
    'Alta' : '9idalta:',
    'SimDetector' : '9idcSIM1:',
}


def _validate_AD_FileWriter_path_(path, root_path):
    if not path.startswith(root_path):
        raise ValueError((
            f"error in file {__file__}:\n"
            f"  path '{path}' must start with '{root_path}"
        ))

# custom support is in AD_EpicsHdf5FileName
class myHdf5EpicsIterativeWriter(AD_EpicsHdf5FileName, FileStoreIterativeWrite): ...
class myHDF5FileNames(HDF5Plugin, myHdf5EpicsIterativeWriter): ...
class EpicsDefinesHDF5FileNames(HDF5Plugin, myHdf5EpicsIterativeWriter): ...
