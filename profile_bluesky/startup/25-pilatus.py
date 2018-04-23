print(__file__)

"""Pilatus detector"""


# root path for HDF5 files (for databroker filestore)
# This is the path BlueSky can see.
# For the DataBroker, this should be the leading part
# of `pilatus_file_template_root` that is common.
databroker_pilatus_root_path = "/"

# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# This is the path the detector can see
# It must start with the path defined in `databroker_pilatus_root_path`
pilatus_file_template_root = "/mnt/usaxscontrol/USAXS_data/"



# class MyPilatusCam(PilatusDetectorCam):
#     """custom support for detector cam plugin"""
#     # # FIXME: ophyd has problem with trying to unstage the RBV value inside RE()
#     # image_mode = ADComponent(EpicsSignal, "ImageMode")
#     # num_images = ADComponent(EpicsSignal, "NumImages")
#     # acquire_time = ADComponent(EpicsSignal, "AcquireTime")
#     # frame_type = ADComponent(EpicsSignal, "FrameType")
    

class MyPilatusDetector(SingleTrigger, AreaDetector):
    """Pilatus detector(s) as used by 9-ID-C USAXS"""
    
    cam = ADComponent(PilatusDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    
    hdf1 = ADComponent(
        MyHDF5Plugin, 
        "HDF1:", 
        root=databroker_pilatus_root_path,
        write_path_template = pilatus_file_template_root,
        reg=db.reg,
        )


saxs_det = MyPilatusDetector(area_detector_EPICS_PV_prefix["Pilatus 100k"], name="saxs_det")
waxs_det = MyPilatusDetector(area_detector_EPICS_PV_prefix["Pilatus 200kw"], name="waxs_det")
