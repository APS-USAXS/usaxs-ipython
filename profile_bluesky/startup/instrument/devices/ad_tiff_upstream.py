
"""Support for AD TIFF plugin."""

__all__ = [
    "AD_EpicsTiffFileName",
    ]

from ..session_logs import logger
logger.info(__file__)

import itertools
from ophyd.areadetector.filestore_mixins import FileStoreBase
from ophyd.areadetector.filestore_mixins import FileStorePluginBase
from ophyd.utils import set_and_wait


class AD_EpicsTiffFileName(FileStorePluginBase):    # lgtm [py/missing-call-to-init]

    """
    custom class to define image file name from EPICS
    .. caution:: *Caveat emptor* applies here.  You assume expertise!
    Replace standard Bluesky algorithm where file names
    are defined as UUID strings, virtually guaranteeing that
    no existing images files will ever be overwritten.
    Also, this method decouples the data files from the databroker,
    which needs the files to be named by UUID.
    .. autosummary::
        ~make_filename
        ~generate_datum
        ~get_frames_per_point
        ~stage
    Patterned on ``apstools.devices.AD_EpicsHdf5FileName()``.
    (Follow that documentation from this point.)
    """

    def __init__(self, *args, **kwargs):
        FileStorePluginBase.__init__(self, *args, **kwargs)
        # TODO: taking a guess here, it's needed if databroker is to *read* the image file
        # If we get this wrong, we have to update any existing runs before
        # databroker can read them into memory.  If there is not such symbol
        # defined, it's up to somone who wants to read these images with databroker.
        self.filestore_spec = 'AD_TIFF'  # spec name stored in resource doc
        self.stage_sigs.update([
            ('file_template', '%s%s_%4.4d.tif'),
            ('file_write_mode', 'Stream'),
            ('capture', 1)
        ])

    def make_filename(self):
        """
        overrides default behavior: Get info from EPICS TIFF plugin.
        """
        # start of the file name, file number will be appended per template
        filename = self.file_name.get()

        # this is where the TIFF plugin will write the image,
        # relative to the IOC's filesystem
        write_path = self.file_path.get()

        # this is where the DataBroker will find the image,
        # on a filesystem accessible to Bluesky
        read_path = write_path

        return filename, read_path, write_path

    def generate_datum(self, key, timestamp, datum_kwargs):
        """Generate a uid and cache it with its key for later insertion."""
        template = self.file_template.get()
        filename, read_path, write_path = self.make_filename()
        file_number = self.file_number.get()
        tiff_file_name = template % (read_path, filename, file_number)

        # inject the actual name of the TIFF file here into datum_kwargs
        datum_kwargs["TIFF_file_name"] = tiff_file_name

        logger.debug("make_filename: %s", tiff_file_name)
        logger.debug("write_path: %s", write_path)
        return super().generate_datum(key, timestamp, datum_kwargs)

    def get_frames_per_point(self):
        """Overrides default behavior."""
        return self.num_capture.get()

    def stage(self):
        """
        overrides default behavior
        Set EPICS items before device is staged, then copy EPICS
        naming template (and other items) to ophyd after staging.
        """
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
            raise IOError("Path {} does not exist on IOC.".format(
                          self.file_path.get()))

        self._point_counter = itertools.count()

        # from FileStoreHDF5.stage()
        res_kwargs = {'frame_per_point': self.get_frames_per_point()}
        self._generate_resource(res_kwargs)
