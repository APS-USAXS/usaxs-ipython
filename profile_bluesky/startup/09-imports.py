logger.info(__file__)
logger.debug(resource_usage(os.path.split(__file__)[-1]))

"""gather all the imports here"""


from collections import deque, OrderedDict, defaultdict
import datetime
from enum import Enum
import getpass
import IPython
import itertools
import os
from pathlib import PurePath
import socket
import subprocess
import threading
import time
import uuid

from ophyd import Component, Device, DeviceStatus, Signal
from ophyd import EpicsMotor, EpicsScaler, MotorBundle
from ophyd import EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV
from ophyd import PVPositioner, PVPositionerPC
from ophyd.mca import EpicsMCARecord
from ophyd.device import DynamicDeviceComponent
from ophyd.device import FormattedComponent
from ophyd.scaler import ScalerCH, ScalerChannel
from ophyd.signal import Kind
from ophyd.sim import SynSignal
from ophyd.utils import OrderedDefaultDict
from ophyd.utils import set_and_wait

from ophyd import AreaDetector
from ophyd import PilatusDetectorCam
from ophyd import PointGreyDetectorCam
from ophyd import SimDetectorCam
from ophyd import CamBase
from ophyd import SingleTrigger, ImagePlugin, HDF5Plugin
from ophyd.areadetector import ADComponent
from ophyd.areadetector.filestore_mixins import FileStoreBase
from ophyd.areadetector.filestore_mixins import FileStoreHDF5
from ophyd.areadetector.filestore_mixins import FileStorePluginBase
from ophyd.areadetector.filestore_mixins import FileStoreIterativeWrite
from ophyd.areadetector.filestore_mixins import FileStoreHDF5IterativeWrite
from ophyd.areadetector.filestore_mixins import new_short_uid

import apstools.callbacks as APS_callbacks
import apstools.devices as APS_devices
import apstools.filewriters as APS_filewriters
import apstools.plans as APS_plans
import apstools.synApps_ophyd as APS_synApps_ophyd
import apstools.suspenders as APS_suspenders
import apstools.utils as APS_utils

# import specific methods by name, we need to customize them sometimes
from apstools.callbacks import DocumentCollectorCallback
from apstools.devices import ApsPssShutterWithStatus
from apstools.devices import SimulatedApsPssShutterWithStatus
from apstools.devices import AxisTunerMixin
from apstools.devices import DualPf4FilterBox
from apstools.devices import EpicsMotorLimitsMixin
from apstools.devices import EpicsMotorShutter
from apstools.devices import Struck3820
from apstools.filewriters import SpecWriterCallback, spec_comment
from apstools.synApps_ophyd.busy import BusyStatus

req_version = (1,1,7)
cur_version = apstools.__version__
if cur_version < req_version:
    ver_str = '.'.join((map(str,req_version)))
    msg = (
        f'Requires apstools {req_version}+'
        f' you have {cur_version}'
        '\n\n'
        'You should type `exit` now and update apstools'
        )
    raise RuntimeError(msg)

from usaxs_support.nexus import reset_manager, get_manager
from usaxs_support.saveFlyData import SaveFlyScan
from usaxs_support.surveillance import instrument_archive

import pyRestTable

sys.path.append(IPython.paths.get_ipython_dir())
