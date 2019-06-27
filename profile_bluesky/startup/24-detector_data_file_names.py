print(__file__)
print(resource_usage(os.path.split(__file__)[-1]))

"""
replace BlueSky file name scheme when used with area detector
"""

DATABROKER_ROOT_PATH = "/"


def _validate_AD_HDF5_path_(path, root_path):
    if not path.startswith(root_path):
        msg = f"error in file {__file__}:\n  path '{path}' must start with '{root_path}"
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
