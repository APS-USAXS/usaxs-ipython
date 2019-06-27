print(__file__)
print(resource_usage(os.path.split(__file__)[-1]))

"""Pilatus detector"""



# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# path seen by detector IOC
WRITE_HDF5_FILE_PATH_PILATUS = "/mnt/usaxscontrol/USAXS_data/test/pilatus/%Y/%m/%d/"
# path seen by databroker
READ_HDF5_FILE_PATH_PILATUS = "/share1/USAXS_data/test/pilatus/%Y/%m/%d/"

_validate_AD_HDF5_path_(WRITE_HDF5_FILE_PATH_PILATUS, DATABROKER_ROOT_PATH)
    

class MyPilatusHDF5Plugin(HDF5Plugin, FileStoreHDF5IterativeWrite):
    """adapt HDF5 plugin for Pilatus detector"""
    

class MyPilatusDetector(SingleTrigger, AreaDetector):
    """Pilatus detector(s) as used by 9-ID-C USAXS"""
    
    cam = ADComponent(PilatusDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    
    hdf1 = ADComponent(
        EpicsDefinesHDF5FileNames, 
        suffix = "HDF1:", 
        root = DATABROKER_ROOT_PATH,
        write_path_template = WRITE_HDF5_FILE_PATH_PILATUS,
        read_path_template = READ_HDF5_FILE_PATH_PILATUS,
        )


try:
    nm = "Pilatus 100k"
    prefix = area_detector_EPICS_PV_prefix[nm]
    saxs_det = MyPilatusDetector(prefix, name="saxs_det")
    saxs_det.read_attrs.append("hdf1")
except TimeoutError as exc_obj:
    msg = f"Timeout connecting with {nm} ({prefix})"
    print(msg)

try:
    nm = "Pilatus 200kw"
    prefix = area_detector_EPICS_PV_prefix[nm]
    waxs_det = MyPilatusDetector(prefix, name="waxs_det")
    waxs_det.read_attrs.append("hdf1")
except TimeoutError as exc_obj:
    msg = f"Timeout connecting with {nm} ({prefix})"
    print(msg)
