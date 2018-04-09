print(__file__)

"""Pilatus detector"""

from ophyd import AreaDetector, PilatusDetectorCam, PointGreyCam
from ophyd import SingleTrigger, ImagePlugin, HDF5Plugin


area_detector_EPICS_PV_prefix = {
    'Pilatus 100k' : 'usaxs_pilatus1:',
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
    

class MyHDF5Plugin(HDF5Plugin, FileStoreHDF5IterativeWrite):
#class MyHDF5Plugin(HDF5Plugin):
    """custom support for detector HDF5 plugin (AD 2.5+)"""
    
    file_number_sync = None
    # FIXME:  .put() works OK but .value returns numpy object metadata
    # In [48]: pco_edge.hdf1.xml_layout_file.get()
    # Out[48]: '<array size=21, type=time_char>'
    # FIXME: xml_layout_file = Component(EpicsSignalWithRBV, "XMLFileName", string=True)
    xml_layout_file = ADComponent(EpicsSignal, "XMLFileName", string=True)    # use as WRITE-ONLY for now due to error above
    xml_layout_valid = ADComponent(EpicsSignalRO, "XMLValid_RBV")
    xml_layout_error_message = ADComponent(EpicsSignalRO, "XMLErrorMsg_RBV", string=True)
    
    def get_frames_per_point(self):
        return self.parent.cam.num_images.get()


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


class MyPointGreyDetector(SingleTrigger, AreaDetector):
    """PointGrey Black Fly detector(s) as used by 9-ID-C USAXS"""
    # TODO: configure the "root" and "write_path_template" attributes
    # TODO: consider each detector separately?
    
    cam = ADComponent(PointGreyCam, "cam1:")
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


# saxs_det = MyPilatusDetector(area_detector_EPICS_PV_prefix["Pilatus 100k"], name="saxs_det")
# waxs_det = MyPointGreyDetector(area_detector_EPICS_PV_prefix["PointGrey BlackFly"], name="waxs_det")
