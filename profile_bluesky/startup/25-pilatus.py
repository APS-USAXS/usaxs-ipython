print(__file__)

"""Pilatus detector"""


# root path for HDF5 files (for databroker filestore)
# This is the path BlueSky can see.
DATABROKER_ROOT_PATH_PILATUS = "/"

# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# This is the path the detector can see
HDF5_FILE_PATH_PILATUS = "/mnt/usaxscontrol/USAXS_data/test/pilatus/%Y/%m/%d/"

if not HDF5_FILE_PATH_PILATUS.startswith(DATABROKER_ROOT_PATH_PILATUS):
    msg = "error in file {}:\n  path '{}' must start with '{}".format(
        __file__,
        HDF5_FILE_PATH_PILATUS,
        DATABROKER_ROOT_PATH_PILATUS
    )
    raise ValueError(msg)
    

class MyPilatusHDF5Plugin(HDF5Plugin, FileStoreHDF5IterativeWrite):
    """adapt HDF5 plugin for Pilatus detector"""
    

class MyPilatusDetector(SingleTrigger, AreaDetector):
    """Pilatus detector(s) as used by 9-ID-C USAXS"""
    
    cam = ADComponent(PilatusDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    
    hdf1 = ADComponent(
        MyPilatusHDF5Plugin, 
        suffix = "HDF1:", 
        root = DATABROKER_ROOT_PATH_PILATUS,
        write_path_template = HDF5_FILE_PATH_PILATUS,
        )


try:
    nm = "Pilatus 100k"
    prefix = area_detector_EPICS_PV_prefix[nm]
    saxs_det = MyPilatusDetector(prefix, name="saxs_det")
except TimeoutError as exc_obj:
    msg = "Timeout connecting with {} ({})".format(nm, prefix)
    print(msg)

try:
    nm = "Pilatus 200kw"
    prefix = area_detector_EPICS_PV_prefix[nm]
    waxs_det = MyPilatusDetector(prefix, name="waxs_det")
except TimeoutError as exc_obj:
    msg = "Timeout connecting with {} ({})".format(nm, prefix)
    print(msg)
