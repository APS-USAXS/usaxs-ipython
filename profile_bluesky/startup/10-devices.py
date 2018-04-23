print(__file__)

from ophyd import Component, Device, DeviceStatus
from ophyd import EpicsMotor, EpicsScaler, MotorBundle
from ophyd import EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV
from ophyd import PVPositioner, PVPositionerPC
from ophyd.scaler import ScalerCH
from APS_BlueSky_tools.devices import userCalcsDevice
from APS_BlueSky_tools.devices import AxisTunerMixin
from APS_BlueSky_tools.plans import TuneAxis
from APS_BlueSky_tools.synApps_ophyd import swaitRecord

from collections import deque, OrderedDict
import os
import subprocess
from ophyd.utils import OrderedDefaultDict
from enum import Enum
import threading
import time


# Set up custom or complex devices

class TunableEpicsMotor(EpicsMotor, AxisTunerMixin):
    pass


class BusyStatus(str, Enum):
    busy = "Busy"
    done = "Done"


class BusyRecord(Device):
    """a busy record sets the fly scan into action"""
    state = Component(EpicsSignal, "")
    output_link = Component(EpicsSignal, ".OUT")
    forward_link = Component(EpicsSignal, ".FLNK")


class MyCalc(Device):
    """swait record simulates a signal"""
    result = Component(EpicsSignal, "")
    calc = Component(EpicsSignal, ".CALC")
    proc = Component(EpicsSignal, ".PROC")


class MyWaveform(Device):
    """waveform records store fly scan data"""
    wave = Component(EpicsSignalRO, "")
    number_elements = Component(EpicsSignalRO, ".NELM")
    number_read = Component(EpicsSignalRO, ".NORD")
