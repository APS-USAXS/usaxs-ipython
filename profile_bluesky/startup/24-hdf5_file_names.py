print(__file__)

"""
EPICS-controlled HDF5 file names #33

The single reason for *ALL* this code is to override
the **ONE** line in ``ApsFileStoreHDF5.make_filename()``::

        read_path = write_path.replace("/mnt/", "/").replace("/usaxscontrol/", "/share1/")

"""




class ApsFileStoreHDF5(FileStorePluginBase):
    """
    custom class to define image file name from EPICS
    To allow users to control the file name,
    we override the ``make_filename()`` method here
    and we need to override some intervening classes.
    To allow users to control the file number,
    we override the ``stage()`` method here
    and triple-comment out that line, and bring in
    sections from the methods we are replacing here.
    The image file name is set in `FileStoreBase.make_filename()` 
    from `ophyd.areadetector.filestore_mixins`.  This is called 
    (during device staging) from `FileStoreBase.stage()`
    To use this custom class, we need to connect it to some
    intervening structure:
    ====================================  ============================
    custom class                          superclass(es)
    ====================================  ============================
    ``ApsFileStoreHDF5``                  ``FileStorePluginBase`
    ``ApsFileStoreHDF5IterativeWrite``    ``ApsFileStoreHDF5`, `FileStoreIterativeWrite`
    ``ApsHDF5Plugin``                     ``HDF5Plugin`, `ApsFileStoreHDF5IterativeWrite`
    ====================================  ============================
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filestore_spec = 'AD_HDF5'  # spec name stored in resource doc
        self.stage_sigs.update([
            ('file_template', '%s%s_%4.4d.h5'),
            ('file_write_mode', 'Stream'),
            ('capture', 1)
        ])

    def make_filename(self):
        """
        overrides default behavior: Get info from EPICS HDF5 plugin.
        """
        # start of the file name, file number will be appended per template
        filename = self.file_name.value
        
        # this is where the HDF5 plugin will write the image, 
        # relative to the IOC's filesystem
        write_path = self.file_path.value
        
        # this is where the DataBroker will find the image, 
        # on a filesystem accessible to BlueSky
        read_path = write_path.replace("/mnt/", "/").replace("/usaxscontrol/", "/share1/")

        return filename, read_path, write_path

    def get_frames_per_point(self):
        return self.num_capture.get()

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
        ### set_and_wait(self.file_number, 0)
        
        # get file number now since it is incremented during stage()
        file_number = self.file_number.get()
        # Must avoid parent's stage() since it sets file_number to 0
        # Want to call grandparent's stage()
        #super().stage()     # avoid this - sets `file_number` to zero
        # call grandparent.stage()
        FileStoreBase.stage(self)

        # AD does the file name templating in C
        # We can't access that result until after acquisition
        # so we apply the same template here in Python.
        template = self.file_template.get()
        self._fn = template % (read_path, filename, file_number)
        self._fp = read_path
        if not self.file_path_exists.get():
            raise IOError("Path %s does not exist on IOC."
                          "" % self.file_path.get())

        # from FileStoreIterativeWrite.stage()
        self._point_counter = itertools.count()
        
        # from FileStoreHDF5.stage()
        res_kwargs = {'frame_per_point': self.get_frames_per_point()}
        self._generate_resource(res_kwargs)


class ApsFileStoreHDF5IterativeWrite(ApsFileStoreHDF5, FileStoreIterativeWrite):
    """custom class to enable users to control image file name"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        FileStoreIterativeWrite.__init__(self, *args, **kwargs)


class ApsHDF5Plugin(HDF5Plugin, ApsFileStoreHDF5IterativeWrite):
    """
    custom class to take image file names from EPICS
    
    NOTE: replaces standard Bluesky algorithm where file names
       are defined as UUID strings, virtually guaranteeing that 
       no existing images files will ever be overwritten.
       *Caveat emptor* applies here.  You assume some expertise!
    
    USAGE::
        class MySimDetector(SingleTrigger, SimDetector):
            '''SimDetector with HDF5 file names specified by EPICS'''
            
            cam = ADComponent(MyAltaCam, "cam1:")
            image = ADComponent(ImagePlugin, "image1:")
            
            hdf1 = ADComponent(
                ApsHDF5Plugin, 
                suffix = "HDF1:", 
                root = "/",
                write_path_template = "/local/data",
                )
        simdet = MySimDetector("13SIM1:", name="simdet")
        # remove this so array counter is not set to zero each staging
        del simdet.hdf1.stage_sigs["array_counter"]
        simdet.hdf1.stage_sigs["file_template"] = '%s%s_%3.3d.h5'
        simdet.hdf1.file_path.put("/local/data/demo/")
        simdet.hdf1.file_name.put("test")
        simdet.hdf1.array_counter.put(0)
        RE(bp.count([simdet]))
    """
