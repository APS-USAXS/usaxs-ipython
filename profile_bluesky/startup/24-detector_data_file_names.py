print(__file__)

"""
replace BlueSky file name scheme when used with area detector
"""

from ophyd import AreaDetector, PilatusDetectorCam, PointGreyDetectorCam
from ophyd import SingleTrigger, ImagePlugin, HDF5Plugin
from ophyd.utils import set_and_wait
from ophyd.areadetector import ADComponent
from ophyd.areadetector.filestore_mixins import FileStoreBase
from ophyd.areadetector.filestore_mixins import FileStoreIterativeWrite
from ophyd.areadetector.filestore_mixins import FileStoreHDF5IterativeWrite
from ophyd.areadetector.filestore_mixins import new_short_uid

from pathlib import PurePath


logger = logging.getLogger(__name__)


# FIXME: RE(bp.count([saxs_det], num=5)) raises an exception
"""
In [33]: RE(bp.count([saxs_det], num=5))
Transient Scan ID: 32     Time: 2018/04/20 12:05:01
Persistent Unique Scan ID: 'a96897a0-4ddd-4f57-ac99-fcc312e92e25'
Transient Scan ID: 32 at 2018-04-20T12:05:01.166467
Persistent Unique Scan ID: 'a96897a0-4ddd-4f57-ac99-fcc312e92e25'
New stream: 'primary'                                                                                                                                                                                                                                               
+-----------+------------+
|   seq_num |       time |
+-----------+------------+
+-----------+------------+
generator count ['a96897a0'] (scan num: 32)



exit status: fail
# descriptor(s): 1
---------------------------------------------------------------------------
IndexError                                Traceback (most recent call last)
<ipython-input-33-fccab7a10f08> in <module>()
----> 1 RE(bp.count([saxs_det], num=5))

...
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

class MyFileStorePluginBase(FileStoreBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.update([('auto_increment', 'Yes'),
                                ('array_counter', 0),
                                ('auto_save', 'Yes'),
                                ('num_capture', 0),
                                ])
        self._fn = None

    def make_filename(self):
        '''Make a filename.

        This is a hook so that the read and write paths can either be modified
        or created on disk prior to configuring the areaDetector plugin.

        Returns
        -------
        filename : str
            The start of the filename
        read_path : str
            Path that ophyd can read from
        write_path : str
            Path that the IOC can write to
        '''
        filename = new_short_uid()
        formatter = datetime.now().strftime
        write_path = formatter(self.write_path_template)
        read_path = formatter(self.read_path_template)
        return filename, read_path, write_path

    def stage(self):
        # Make a filename.
        filename, read_path, write_path = self.make_filename()

        # Ensure we do not have an old file open.
        set_and_wait(self.capture, 0)
        # These must be set before parent is staged (specifically
        # before capture mode is turned on. They will not be reset
        # on 'unstage' anyway.
        set_and_wait(self.file_path, write_path)
        set_and_wait(self.file_name, filename)
        #set_and_wait(self.file_number, 0)
        super().stage()

        # AD does this same templating in C, but we can't access it
        # so we do it redundantly here in Python.
        self._fn = self.file_template.get() % (read_path,
                                               filename,
                                               self.file_number.get() - 1)
                                               # file_number is *next* iteration
        self._fp = read_path
        if not self.file_path_exists.get():
            raise IOError("Path %s does not exist on IOC."
                          "" % self.file_path.get())


class MyFileStoreHDF5(MyFileStorePluginBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filestore_spec = 'AD_HDF5'  # spec name stored in resource doc
        self.stage_sigs.update([('file_template', '%s%s_%6.6d.h5'),
                                ('file_write_mode', 'Stream'),
                                ('capture', 1)
                                ])

    def get_frames_per_point(self):
        return self.num_capture.get()

    def stage(self):
        super().stage()
        res_kwargs = {'frame_per_point': self.get_frames_per_point()}
        logger.debug("Inserting resource with filename %s", self._fn)
        fn = PurePath(self._fn).relative_to(self.reg_root)
        self._resource = self._reg.register_resource(
            self.filestore_spec,
            str(self.reg_root), str(fn),
            res_kwargs)


class MyFileStoreHDF5IterativeWrite(MyFileStoreHDF5, FileStoreIterativeWrite):
    pass


class MyHDF5Plugin(HDF5Plugin, MyFileStoreHDF5IterativeWrite):
    """adapt HDF5 plugin for AD 2.5+"""
    
    file_number_sync = None
    capture_VAL = ADComponent(EpicsSignal, "Capture")
    file_template_VAL = ADComponent(EpicsSignal, "FileTemplate", string=True)
    num_capture = ADComponent(EpicsSignal, "NumCapture")
    array_counter = ADComponent(EpicsSignal, "ArrayCounter")

    # FIXME:  .put() works OK but .value returns numpy object metadata
    # In [48]: pco_edge.hdf1.xml_layout_file.get()
    # Out[48]: '<array size=21, type=time_char>'
    # FIXME: xml_layout_file = ADComponent(EpicsSignalWithRBV, "XMLFileName", string=True)
    xml_layout_file = ADComponent(EpicsSignal, "XMLFileName", string=True)    # use as WRITE-ONLY for now due to error above
    xml_layout_valid = ADComponent(EpicsSignalRO, "XMLValid_RBV")
    xml_layout_error_message = ADComponent(EpicsSignalRO, "XMLErrorMsg_RBV", string=True)
    
    def get_frames_per_point(self):
        return self.parent.cam.num_images.get()
