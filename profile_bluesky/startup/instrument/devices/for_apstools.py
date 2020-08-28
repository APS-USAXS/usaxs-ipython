
"""
support that _will_ move into apstools, eventually

"""

__all__ = [
    "AD_EpicsJpegFileName",
    "AD_plugin_primed",
    "AD_prime_plugin",
    ]

from ..session_logs import logger
logger.info(__file__)

from ophyd import JPEGPlugin
from ophyd.areadetector.filestore_mixins import FileStoreBase
from ophyd.areadetector.filestore_mixins import FileStoreIterativeWrite
from ophyd.areadetector.filestore_mixins import FileStorePluginBase
from ophyd.utils import set_and_wait
import itertools


def AD_plugin_primed(detector_plugin):
    """
    Has area detector pushed an NDarray to the file writer plugin?  True or False

    PARAMETERS

    detector_plugin
        *obj* :
        area detector plugin to be *primed* (such as ``detector.hdf1``)

    EXAMPLE::

        AD_plugin_primed(detector.hdf1)

    Works around an observed issue: #598
    https://github.com/NSLS-II/ophyd/issues/598#issuecomment-414311372

    If detector IOC has just been started and has not yet taken an image
    with the file writer plugin, then a TimeoutError will occur as the
    file writer plugin "Capture" is set to 1 (Start).  In such case,
    first acquire at least one image with the file writer plugin enabled.
    """
    old_capture = detector_plugin.capture.get()
    old_file_write_mode = detector_plugin.file_write_mode.get()
    if old_capture == 1:
        return True

    detector_plugin.file_write_mode.put(1)
    detector_plugin.capture.put(1)
    verdict = detector_plugin.capture.get() == 1
    detector_plugin.capture.put(old_capture)
    detector_plugin.file_write_mode.put(old_file_write_mode)
    return verdict


def AD_prime_plugin(detector, detector_plugin):
    """
    Prime this area detector's file writer plugin.

    Collect and push an NDarray to the file writer plugin.

    Works with HDF and JPEG file writers, maybe others.

    PARAMETERS

    detector
        *obj* :
        area detector (such as ``detector``)

    detector_plugin
        *obj* :
        area detector plugin to be *primed* (such as ``detector.hdf1``)

    EXAMPLE::

        AD_prime_plugin(detector, detector.hdf1)
    """
    old_enable = detector_plugin.enable.get()
    old_mode = detector_plugin.file_write_mode.get()

    detector_plugin.enable.put(1)
    # next step is important:   
    # SET the write mode to "Single" (0) or plugin's Capture=1 won't stay
    detector_plugin.file_write_mode.put(0)
    detector_plugin.jpeg1.capture.put(1)
    detector.cam.acquire.put(1)

    # reset things
    detector_plugin.file_write_mode.put(old_mode)
    detector_plugin.enable.put(old_enable)


class AD_EpicsJpegFileName(FileStorePluginBase):    # lgtm [py/missing-call-to-init]

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
        self.filestore_spec = 'AD_JPEG'  # spec name stored in resource doc
        self.stage_sigs.update([
            ('file_template', '%s%s_%4.4d.jpg'),
            ('file_write_mode', 'Stream'),
            ('capture', 1)
        ])

    def make_filename(self):
        """
        overrides default behavior: Get info from EPICS JPEG plugin.
        """
        # start of the file name, file number will be appended per template
        filename = self.file_name.get()

        # this is where the JPEG plugin will write the image,
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
        jpeg_file_name = template % (read_path, filename, file_number)

        # inject the actual name of the JPEG file here into datum_kwargs
        datum_kwargs["JPEG_file_name"] = jpeg_file_name

        logger.debug("make_filename: %s", jpeg_file_name)
        logger.debug("write_path: %s", write_path)
        return super().generate_datum(key, timestamp, datum_kwargs)

    def get_frames_per_point(self):
        """overrides default behavior"""
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

        # from FileStoreIterativeWrite.stage()
        self._point_counter = itertools.count()

        # from FileStoreHDF5.stage()
        res_kwargs = {'frame_per_point': self.get_frames_per_point()}
        self._generate_resource(res_kwargs)
