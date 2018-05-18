print(__file__)

"""ADSimDetector"""


# root path for HDF5 files (for databroker filestore)
# This is the path BlueSky can see.
# For the DataBroker, this should be the leading part
# of `simdetector_file_template_root` that is common.
databroker_simdetector_root_path = "/share1/USAXS_data/"

# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# This is the path the detector can see
# It must start with the path defined in `databroker_simdetector_root_path`
simdetector_file_template_root = "/share1/USAXS_data/"



# class MyPilatusCam(PilatusDetectorCam):
#     """custom support for detector cam plugin"""
#     # # FIXME: ophyd has problem with trying to unstage the RBV value inside RE()
#     # image_mode = ADComponent(EpicsSignal, "ImageMode")
#     # num_images = ADComponent(EpicsSignal, "NumImages")
#     # acquire_time = ADComponent(EpicsSignal, "AcquireTime")
#     # frame_type = ADComponent(EpicsSignal, "FrameType")
    

class MySimDetector(SingleTrigger, AreaDetector):
    """ADSimDetector instance used by 9-ID-C USAXS"""
    
    cam = ADComponent(SimDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    hdf1 = ADComponent(HDF5Plugin, "HDF1:")
    #hdf1 = ADComponent(
    #    MyHDF5Plugin, 
    #    "HDF1:", 
    #    root=databroker_simdetector_root_path,
    #    write_path_template = simdetector_file_template_root,
    #    reg=db.reg,
    #    )


try:
    nm = "SimDetector"
    prefix = area_detector_EPICS_PV_prefix[nm]
    adsim = MySimDetector(prefix, name="adsim")
except TimeoutError as exc_obj:
    msg = "Timeout connecting with {} ({})".format(nm, prefix)
    print(msg)
