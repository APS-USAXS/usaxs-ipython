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


# FIXME: raises Exception due to my attempt to override filenaming
"""
.In [18]: RE(bp.count([blackfly_det]))
Transient Scan ID: 31     Time: 2018/04/20 11:51:57
Persistent Unique Scan ID: '3b20c56a-0f39-4d3f-851f-d1abe2244635'
Transient Scan ID: 31 at 2018-04-20T11:51:57.019840
Persistent Unique Scan ID: '3b20c56a-0f39-4d3f-851f-d1abe2244635'
New stream: 'primary'                                                                                                                                                                                                                                               
+-----------+------------+
|   seq_num |       time |
+-----------+------------+
+-----------+------------+
generator count ['3b20c56a'] (scan num: 31)



exit status: fail
# descriptor(s): 1
---------------------------------------------------------------------------
IndexError                                Traceback (most recent call last)
<ipython-input-18-01764b7a804f> in <module>()
----> 1 RE(bp.count([blackfly_det]))

..
/APSshare/anaconda3/BlueSky/lib/python3.6/site-packages/bluesky/utils.py in __call__(self, *args, **kwargs)
    367             mtd = self.func
    368         # invoke the callable and return the result
--> 369         return mtd(*args, **kwargs)
    370 
    371     def __eq__(self, other):

/APSshare/anaconda3/BlueSky/lib/python3.6/site-packages/APS_BlueSky_tools/filewriters.py in receiver(self, key, document)
    207         if key in xref:
    208             self._datetime = datetime.datetime.fromtimestamp(document["time"])
--> 209             xref[key](document)
    210         else:
    211             msg = "custom_callback encountered: {} : {}".format(key, document)

/APSshare/anaconda3/BlueSky/lib/python3.6/site-packages/APS_BlueSky_tools/filewriters.py in descriptor(self, doc)
    293                 det_name = list(self.detectors.keys())[0]
    294                 if det_name not in self.data:
--> 295                     det_name = list(doc["data_keys"].keys())[0]
    296                 if det_name in self.data:
    297                     self.data.move_to_end(det_name)

IndexError: list index out of range
"""


class MyPointGreyDetector(SingleTrigger, AreaDetector):
    """PointGrey Black Fly detector(s) as used by 9-ID-C USAXS"""
    # TODO: configure the "root" and "write_path_template" attributes
    # TODO: consider each detector separately?
    
    cam = ADComponent(PointGreyDetectorCam, "cam1:")
    image = ADComponent(ImagePlugin, "image1:")
    # root : the path BlueSky can see
    # write_path_template : the path the detector can see (starts with root)


saxs_det = MyPilatusDetector(area_detector_EPICS_PV_prefix["Pilatus 100k"], name="saxs_det")
waxs_det = MyPilatusDetector(area_detector_EPICS_PV_prefix["Pilatus 200kw"], name="waxs_det")
blackfly_det = MyPointGreyDetector(area_detector_EPICS_PV_prefix["PointGrey BlackFly"], name="blackfly_det")
