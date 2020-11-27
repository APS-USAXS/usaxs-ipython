
"""
support USAXS area detectors

replace BlueSky file name scheme when used with area detector

file systems on some area detectors need more work

* saxs:  /mnt/share1/USAXS_data/yyyy-mm/user_working_folder_saxs/
* waxs:  /mnt/usaxscontrol/USAXS_data/yyyy-mm/user_working_folder_waxs/
* PointGrey BlackFly does not write out to file typically.  No use of HDF5 plugin.
* PointGrey BlackFly Optical: /mnt/share1/USAXS_data/...
* Alta: /mnt/share1/USAXS_data/...
"""

__all__ = """
    _validate_AD_FileWriter_path_
    area_detector_EPICS_PV_prefix
    DATABROKER_ROOT_PATH
    EpicsDefinesHDF5FileNames
    EpicsDefinesJpegFileNames
    myHdf5EpicsIterativeWriter
    myHDF5FileNames
    myJpegEpicsIterativeWriter
    myJpegFileNames
    """.split()



from ..session_logs import logger
logger.info(__file__)

from apstools.devices import AD_EpicsHdf5FileName
from apstools.devices import AD_EpicsJpegFileName
# TODO: from apstools.devices import AD_EpicsTiffFileName
from .ad_tiff_upstream import AD_EpicsTiffFileName
from ophyd import HDF5Plugin
from ophyd import JPEGPlugin
from ophyd import TIFFPlugin
from ophyd.areadetector.filestore_mixins import FileStoreBase
from ophyd.areadetector.filestore_mixins import FileStoreIterativeWrite
from ophyd.utils import set_and_wait
import itertools

DATABROKER_ROOT_PATH = "/"

area_detector_EPICS_PV_prefix = {
    'Pilatus 100k' : 'usaxs_pilatus1:',
    'Pilatus 200kw' : 'usaxs_pilatus2:',
    'PointGrey BlackFly' : '9idFLY1:',      # radiography
    'PointGrey BlackFly Optical' : '9idFLY2:',
    'Alta' : '9idalta:',
    'SimDetector' : '9idcSIM1:',
}


def _validate_AD_FileWriter_path_(path, root_path):
    if not path.startswith(root_path):
        raise ValueError((
            f"error in file {__file__}:\n"
            f"  path '{path}' must start with '{root_path}"
        ))


class Override_AD_EpicsHdf5FileName(AD_EpicsHdf5FileName):

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

        if not write_path.endswith("/"):    # TODO: need to add into apstools!
            write_path += "/"

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


class myHdf5EpicsIterativeWriter(Override_AD_EpicsHdf5FileName,
                                 FileStoreIterativeWrite): ...
class myHDF5FileNames(HDF5Plugin, myHdf5EpicsIterativeWriter): ...
class EpicsDefinesHDF5FileNames(HDF5Plugin,
                                myHdf5EpicsIterativeWriter): ...

class myJpegEpicsIterativeWriter(AD_EpicsJpegFileName,
                                 FileStoreIterativeWrite): ...
class myJpegFileNames(JPEGPlugin, myJpegEpicsIterativeWriter): ...
class EpicsDefinesJpegFileNames(JPEGPlugin,
                                myJpegEpicsIterativeWriter): ...

class myTiffEpicsIterativeWriter(AD_EpicsTiffFileName,
                                 FileStoreIterativeWrite): ...
class myTiffFileNames(TIFFPlugin, myTiffEpicsIterativeWriter): ...
class EpicsDefinesTiffFileNames(TIFFPlugin,
                                myTiffEpicsIterativeWriter): ...
