print(__file__)

"""Pilatus detector"""


"""
file systems on Pilatus detectors need more work

saxs:  /mnt/usaxscontrol/USAXS_data/yyyy-mm/user_working_folder_saxs/
waxs:  /mnt/usaxscontrol/USAXS_data/yyyy-mm/user_working_folder_waxs/

PointGrey does not write out to file typically.  Do not care about HDF5 plugin
"""


area_detector_EPICS_PV_prefix = {
    'Pilatus 100k' : 'usaxs_pilatus1:',
    'Pilatus 200kw' : 'usaxs_pilatus2:',
    'PointGrey BlackFly' : '9idFLY1:',
    'Alta' : '9idalta:',
}


class MyPilatusCam(PilatusDetectorCam):
    """custom support for detector cam plugin"""
    # # FIXME: ophyd has problem with trying to unstage the RBV value inside RE()
    # image_mode = ADComponent(EpicsSignal, "ImageMode")
    # num_images = ADComponent(EpicsSignal, "NumImages")
    # acquire_time = ADComponent(EpicsSignal, "AcquireTime")
    # frame_type = ADComponent(EpicsSignal, "FrameType")
    

class MyPilatusDetector(SingleTrigger, AreaDetector):
    """Pilatus detector(s) as used by 9-ID-C USAXS"""
    # TODO: configure the "root" and "write_path_template" attributes
    # TODO: consider each detector separately?
    
    cam = ADComponent(MyPilatusCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    
    # root : the path BlueSky can see
    # write_path_template : the path the detector can see (starts with root)
    hdf1 = ADComponent(
        MyHDF5Plugin, 
        "HDF1:", 
        root="/",                   # TODO: root path for HDF5 files (for databroker filestore)
        write_path_template="/tmp", # TODO: path for HDF5 files (for EPICS area detector)
        reg=db.reg,
        )


class MyPointGreyDetector(SingleTrigger, AreaDetector):
    """PointGrey Black Fly detector(s) as used by 9-ID-C USAXS"""
    
    cam = ADComponent(PointGreyDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")


saxs_det = MyPilatusDetector(area_detector_EPICS_PV_prefix["Pilatus 100k"], name="saxs_det")
waxs_det = MyPilatusDetector(area_detector_EPICS_PV_prefix["Pilatus 200kw"], name="waxs_det")
blackfly_det = MyPointGreyDetector(area_detector_EPICS_PV_prefix["PointGrey BlackFly"], name="blackfly_det")
