print(__file__)

"""ADSimDetector"""

# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# path seen by detector IOC
WRITE_HDF5_FILE_PATH_ADSIMDET = "/share1/USAXS_data/test/adsimdet/%Y/%m/%d/"
# path seen by databroker
READ_HDF5_FILE_PATH_ADSIMDET = WRITE_HDF5_FILE_PATH_ADSIMDET

_validate_AD_HDF5_path_(WRITE_HDF5_FILE_PATH_ADSIMDET, DATABROKER_ROOT_PATH)
_validate_AD_HDF5_path_(READ_HDF5_FILE_PATH_ADSIMDET, DATABROKER_ROOT_PATH)


class MySimDetector(SingleTrigger, AreaDetector):
    """ADSimDetector instance used by 9-ID-C USAXS"""
    
    cam = ADComponent(SimDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    hdf1 = ADComponent(
        EpicsDefinesHDF5FileNames, 
        suffix = "HDF1:", 
        root = DATABROKER_ROOT_PATH,
        write_path_template = WRITE_HDF5_FILE_PATH_ADSIMDET,
        read_path_template = READ_HDF5_FILE_PATH_ADSIMDET,
        )


try:
    nm = "SimDetector"
    prefix = area_detector_EPICS_PV_prefix[nm]
    adsimdet = MySimDetector(prefix, name="adsimdet")
except TimeoutError as exc_obj:
    msg = f"Timeout connecting with {nm} ({prefix})"
    print(msg)
