print(__file__)

"""Apogee Alta detector"""


# root path for HDF5 files (for databroker filestore)
# This is the path BlueSky can see.
# For the DataBroker, this should be the leading part
# of `alta_file_template_root` that is common.
databroker_alta_root_path = "/"

# path for HDF5 files (as seen by EPICS area detector HDF5 plugin)
# This is the path the detector can see
# It must start with the path defined in `databroker_alta_root_path`
alta_file_template_root = databroker_alta_root_path + "mnt/usaxscontrol/USAXS_data/"

# 2018-07-20:  from working PG3 at 2-BM-B
HDF5_FILE_PATH_ALTA = "/mnt/share1/USAXS_data/alta/%Y/%m/%d/"



class MyAltaCam(CamBase):
    """support for Apogee Alta detector"""
    _html_docs = []
    temperature = Component(EpicsSignalWithRBV, 'Temperature')


class MyAltaHDF5Plugin(HDF5Plugin, FileStoreHDF5IterativeWrite):
    """adapt HDF5 plugin for Alta detector"""
    
#class MyAltaHDF5Plugin(HDF5Plugin, MyFileStoreHDF5IterativeWrite):
#    """adapt HDF5 plugin for Alta detector"""
#    
#    file_number_sync = None
#    capture_VAL = ADComponent(EpicsSignal, "Capture")
#    file_template_VAL = ADComponent(EpicsSignal, "FileTemplate", string=True)
#    num_capture = ADComponent(EpicsSignal, "NumCapture")
#    array_counter = ADComponent(EpicsSignal, "ArrayCounter")
#
#    # FIXME:  .put() works OK but .value returns numpy object metadata
#    # In [48]: pco_edge.hdf1.xml_layout_file.get()
#    # Out[48]: '<array size=21, type=time_char>'
#    # FIXME: xml_layout_file = ADComponent(EpicsSignalWithRBV, "XMLFileName", string=True)
#    xml_layout_file = ADComponent(EpicsSignal, "XMLFileName", string=True)    # use as WRITE-ONLY for now due to error above
#    xml_layout_valid = ADComponent(EpicsSignalRO, "XMLValid_RBV")
#    xml_layout_error_message = ADComponent(EpicsSignalRO, "XMLErrorMsg_RBV", string=True)
#    
#    def get_frames_per_point(self):
#        return self.parent.cam.num_images.get()


class MyAltaDetector(SingleTrigger, AreaDetector):
    """Alta detector(s) as used by 9-ID-C USAXS Imaging"""
    
    cam = ADComponent(MyAltaCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    
    #hdf1 = ADComponent(
    #    MyAltaHDF5Plugin, 
    #    "HDF1:", 
    #    root = databroker_alta_root_path,
    #    write_path_template = alta_file_template_root,
    #    reg=db.reg,
    #    )
    hdf1 = ADComponent(
        MyAltaHDF5Plugin, 
        suffix = "HDF1:", 
        root = databroker_alta_root_path,
        write_path_template = HDF5_FILE_PATH_ALTA,
        )


try:
    nm = "Alta"
    prefix = area_detector_EPICS_PV_prefix[nm]
    alta_det = MyAltaDetector(prefix, name="alta_det")
except TimeoutError as exc_obj:
    msg = "Timeout connecting with {} ({})".format(nm, prefix)
    print(msg)
