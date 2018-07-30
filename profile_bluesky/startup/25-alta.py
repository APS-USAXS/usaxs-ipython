print(__file__)

"""Apogee Alta detector"""


# root path for HDF5 files (for databroker filestore)
# This is the path Bluesky can see.
DATABROKER_ROOT_PATH_ALTA = "/"

# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# This is the path the detector can see
WRITE_HDF5_FILE_PATH_ALTA = "/mnt/share1/USAXS_data/test/alta/%Y/%m/%d/"
READ_HDF5_FILE_PATH_ALTA = "/share1/USAXS_data/test/alta/%Y/%m/%d/"


def _validate_AD_HDF5_path_(path, root_path):
    if not path.startswith(root_path):
        msg = "error in file {}:\n  path '{}' must start with '{}".format(
            __file__,
            path,
            root_path
        )
        raise ValueError(msg)


_validate_AD_HDF5_path_(WRITE_HDF5_FILE_PATH_ALTA, DATABROKER_ROOT_PATH_ALTA)
_validate_AD_HDF5_path_(READ_HDF5_FILE_PATH_ALTA, DATABROKER_ROOT_PATH_ALTA)


class MyAltaCam(CamBase):
    """support for Apogee Alta detector"""
    _html_docs = []
    temperature = Component(EpicsSignalWithRBV, 'Temperature')


class MyAltaDetector(SingleTrigger, AreaDetector):
    """Alta detector as used by 9-ID-C USAXS Imaging"""
    
    cam = ADComponent(MyAltaCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    
    hdf1 = ADComponent(
        ApsHDF5Plugin,
        suffix = "HDF1:", 
        root = DATABROKER_ROOT_PATH_ALTA,
        write_path_template = WRITE_HDF5_FILE_PATH_ALTA,
        read_path_template = READ_HDF5_FILE_PATH_ALTA,
        )


try:
    nm = "Alta"
    prefix = area_detector_EPICS_PV_prefix[nm]
    alta_det = MyAltaDetector(prefix, name="alta_det")
    alta_det.read_attrs.append("hdf1")
except TimeoutError as exc_obj:
    msg = "Timeout connecting with {} ({})".format(nm, prefix)
    print(msg)
