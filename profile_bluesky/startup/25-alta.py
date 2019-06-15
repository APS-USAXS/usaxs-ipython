print(__file__)

"""Apogee Alta detector"""


# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# path seen by detector IOC
WRITE_HDF5_FILE_PATH_ALTA = "/mnt/share1/USAXS_data/test/alta/%Y/%m/%d/"

# path seen by databroker
READ_HDF5_FILE_PATH_ALTA = "/share1/USAXS_data/test/alta/%Y/%m/%d/"


_validate_AD_HDF5_path_(WRITE_HDF5_FILE_PATH_ALTA, DATABROKER_ROOT_PATH)
_validate_AD_HDF5_path_(READ_HDF5_FILE_PATH_ALTA, DATABROKER_ROOT_PATH)


class MyAltaCam(CamBase):
    """support for Apogee Alta detector"""
    _html_docs = []
    temperature = Component(EpicsSignalWithRBV, 'Temperature')


class MyAltaDetector(SingleTrigger, AreaDetector):
    """Alta detector as used by 9-ID-C USAXS Imaging"""
    
    cam = ADComponent(MyAltaCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    
    hdf1 = ADComponent(
        EpicsDefinesHDF5FileNames,
        suffix = "HDF1:", 
        root = DATABROKER_ROOT_PATH,
        write_path_template = WRITE_HDF5_FILE_PATH_ALTA,
        read_path_template = READ_HDF5_FILE_PATH_ALTA,
        )


try:
    nm = "Alta"
    prefix = area_detector_EPICS_PV_prefix[nm]
    alta_det = MyAltaDetector(prefix, name="alta_det")
    alta_det.read_attrs.append("hdf1")
except TimeoutError as exc_obj:
    msg = f"Timeout connecting with {nm} ({prefix})"
    print(msg)
