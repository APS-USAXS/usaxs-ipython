print(__file__)

"""Apogee Alta detector"""


# root path for HDF5 files (for databroker filestore)
# This is the path Bluesky can see.
DATABROKER_ROOT_PATH_ALTA = "/"

# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# This is the path the detector can see
WRITE_HDF5_FILE_PATH_ALTA = "/mnt/share1/USAXS_data/test/alta/%Y/%m/%d/"
READ_HDF5_FILE_PATH_ALTA = "/share1/USAXS_data/test/alta/%Y/%m/%d/"


def _validate_HDF5_path_(path, root_path):
    if not path.startswith(root_path):
        msg = "error in file {}:\n  path '{}' must start with '{}".format(
            __file__,
            path,
            root_path
        )
        raise ValueError(msg)


_validate_HDF5_path_(WRITE_HDF5_FILE_PATH_ALTA, DATABROKER_ROOT_PATH_ALTA)
_validate_HDF5_path_(READ_HDF5_FILE_PATH_ALTA, DATABROKER_ROOT_PATH_ALTA)


class MyAltaCam(CamBase):
    """support for Apogee Alta detector"""
    _html_docs = []
    temperature = Component(EpicsSignalWithRBV, 'Temperature')


"""
To allow users to control the file name,
we need to override some underlying code.

The image file name is set in `FileStoreBase.make_filename()` from 
`ophyd.areadetector.filestore_mixins`.  This is called (during device
staging) from `FileStoreBase.stage()`

To use this custom class, we need to connect it to some
intervening structure:

===================================  ============================
custom class                         superclass(es)
===================================  ============================
`MyAltaFileStoreHDF5`                `FileStoreHDF5`
`MyAltaHDF5FileStore`                `MyAltaFileStoreHDF5`
`MyAltaFileStoreHDF5IterativeWrite`  `MyAltaHDF5FileStore`, `FileStoreIterativeWrite`
`MyAltaHDF5Plugin`                   `HDF5Plugin`, `MyAltaFileStoreHDF5IterativeWrite`
===================================  ============================
"""


class MyAltaFileStoreHDF5(FileStoreHDF5):
    """
    custom class to define image file name from EPICS
    """

    def make_filename(self):
        """
        overrides default behavior: Get info from EPICS HDF5 plugin.
        """
        # start of the file name, file number will be appended per template
        filename = self.file_name.value
        
        # this is where the HDF5 plugin will write the image, 
        # relative to the IOC's filesystem
        write_path = self.file_path.value
        
        # this is where the DataBroker will find the image, 
        # on a filesystem accessible to BlueSky
        read_path = write_path.replace("/mnt/", "/").replace("/usaxscontrol/", "/share1/")

        return filename, read_path, write_path


class MyAltaHDF5FileStore(MyAltaFileStoreHDF5):
    """custom class to enable users to control image file name"""


class MyAltaFileStoreHDF5IterativeWrite(MyAltaHDF5FileStore, FileStoreIterativeWrite):
    """custom class to enable users to control image file name"""


class MyAltaHDF5Plugin(HDF5Plugin, MyAltaFileStoreHDF5IterativeWrite):
    """custom features for HDF5 plugin for Alta detector"""
    

class MyAltaDetector(SingleTrigger, AreaDetector):
    """Alta detector as used by 9-ID-C USAXS Imaging"""
    
    cam = ADComponent(MyAltaCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    
    hdf1 = ADComponent(
        MyAltaHDF5Plugin, 
        suffix = "HDF1:", 
        root = DATABROKER_ROOT_PATH_ALTA,
        write_path_template = WRITE_HDF5_FILE_PATH_ALTA,
        read_path_template = READ_HDF5_FILE_PATH_ALTA,
        )


try:
    nm = "Alta"
    prefix = area_detector_EPICS_PV_prefix[nm]
    alta_det = MyAltaDetector(prefix, name="alta_det")
except TimeoutError as exc_obj:
    msg = "Timeout connecting with {} ({})".format(nm, prefix)
    print(msg)
