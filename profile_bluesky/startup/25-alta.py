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
`MyAltaFileStorePlugin`              `FileStoreBase`
`MyAltaHDF5FileStore`                `MyAltaFileStorePlugin`
`MyAltaFileStoreHDF5IterativeWrite`  `MyAltaHDF5FileStore`, `FileStoreIterativeWrite`
`MyAltaHDF5Plugin`                   `HDF5Plugin`, `MyAltaFileStoreHDF5IterativeWrite`
===================================  ============================
"""


class MyAltaFileStorePlugin(FileStoreBase):
    """custom class to give users control of image file name"""

    def make_filename(self):
        """
        overrides default behavior: Get info from EPICS HDF5 plugin.
        
        Make a filename.  Get the info from EPICS HDF5 plugin.

        This is a hook so that the read and write paths can either be modified
        or created on disk prior to configuring the areaDetector plugin.

        Returns
        -------
        filename : str
            The start of the filename
        read_path : str
            Path that ophyd can read from
        write_path : str
            Path that the IOC can write to
        """
        # trust EPICS to have these right
        print("File path: " + self.file_path.value)
        print("File name: " + self.file_name.value)
        print("File template: " + self.file_template.value)
        
        # start of the file name, file number will be appended per template
        filename = self.file_name.value
        
        # this is where the HDF5 plugin will write the image, 
        # relative to the IOC's filesystem
        write_path = self.file_path.value
        
        # this is where the DataBroker will find the image, 
        #on a filesystem accessible to BlueSky
        read_path = write_path.replace("/mnt/", "/").replace("/usaxscontrol/", "/share1/")
        
        msg = "make_filename() filename={}, read_path={}, write_path={}".format(
            filename, read_path, write_path
        )
        print(msg)
        
        return filename, read_path, write_path


class MyAltaHDF5FileStore(MyAltaFileStorePlugin):
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
        write_path_template = HDF5_FILE_PATH_ALTA,
        )


try:
    nm = "Alta"
    prefix = area_detector_EPICS_PV_prefix[nm]
    alta_det = MyAltaDetector(prefix, name="alta_det")
except TimeoutError as exc_obj:
    msg = "Timeout connecting with {} ({})".format(nm, prefix)
    print(msg)
