print(__file__)

"""
replace BlueSky file name scheme when used with area detector
"""

logger = logging.getLogger(__name__)
DATABROKER_ROOT_PATH = "/"


def _validate_AD_HDF5_path_(path, root_path):
    if not path.startswith(root_path):
        msg = "error in file {}:\n  path '{}' must start with '{}".format(
            __file__,
            path,
            root_path
        )
        raise ValueError(msg)


"""
file systems on some area detectors need more work

saxs:  /mnt/share1/USAXS_data/yyyy-mm/user_working_folder_saxs/
waxs:  /mnt/usaxscontrol/USAXS_data/yyyy-mm/user_working_folder_waxs/

PointGrey BlackFly does not write out to file typically.  No use of HDF5 plugin.

Alta: /mnt/share1/USAXS_data/...
"""


area_detector_EPICS_PV_prefix = {
    'Pilatus 100k' : 'usaxs_pilatus1:',
    'Pilatus 200kw' : 'usaxs_pilatus2:',
    'PointGrey BlackFly' : '9idFLY1:',
    'Alta' : '9idalta:',
    'SimDetector' : '9idcSIM1:',
}
