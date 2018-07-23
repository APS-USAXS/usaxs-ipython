print(__file__)

"""Apogee Alta detector"""


# root path for HDF5 files (for databroker filestore)
# This is the path Bluesky can see.
DATABROKER_ROOT_PATH_ALTA = "/"

# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# This is the path the detector can see
HDF5_FILE_PATH_ALTA = "/mnt/share1/USAXS_data/test/alta/%Y/%m/%d/"

if not HDF5_FILE_PATH_ALTA.startswith(DATABROKER_ROOT_PATH_ALTA):
    msg = "error in file {}:\n  path '{}' must start with '{}".format(
        __file__,
        HDF5_FILE_PATH_ALTA,
        DATABROKER_ROOT_PATH_ALTA
    )
    raise ValueError(msg)


class MyAltaCam(CamBase):
    """support for Apogee Alta detector"""
    _html_docs = []
    temperature = Component(EpicsSignalWithRBV, 'Temperature')


class MyAltaHDF5Plugin(HDF5Plugin, FileStoreHDF5IterativeWrite):
    """adapt HDF5 plugin for Alta detector"""
    

class MyAltaDetector(SingleTrigger, AreaDetector):
    """Alta detector as used by 9-ID-C USAXS Imaging"""
    
    cam = ADComponent(MyAltaCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    
    hdf1 = ADComponent(
        MyAltaHDF5Plugin, 
        suffix = "HDF1:", 
        root = DATABROKER_ROOT_PATH_ALTA,
        write_path_template = HDF5_FILE_PATH_ALTA,
        )


try:
    nm = "Alta"
    prefix = area_detector_EPICS_PV_prefix[nm]
    alta_det = MyAltaDetector(prefix, name="alta_det")
except TimeoutError as exc_obj:
    msg = "Timeout connecting with {} ({})".format(nm, prefix)
    print(msg)
