print(__file__)

from ophyd import Component, Device, DeviceStatus, Signal
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

from APS_BlueSky_tools.devices import ApsPssShutter
from APS_BlueSky_tools.devices import EpicsMotorShutter

# Set up custom or complex devices

class TunableEpicsMotor(EpicsMotor, AxisTunerMixin):
    pass


class MyApsPssShutter(ApsPssShutter):
    # our shutters use upper case for Open & Close
    open_bit = Component(EpicsSignal, ":Open")
    close_bit = Component(EpicsSignal, ":Close")


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


class InOutShutter(Device):
    """
    In/Out shutter
    
    * In/Out shutters have the same bit PV for open and close
    
    Otherwise, they should have the same interface as other 
    shutters such as the `ApsPssShutter`.
    
    USAGE:
    
        shutter = InOutShutter("48bmc:bit12", name="shutter")
    
    """
    control_bit = Component(EpicsSignal, "")
    delay_s = 0
    open_value = 1
    close_value = 0
    valid_open_values = ["open",]   # lower-case strings ONLY
    valid_close_values = ["close",]
    busy = Signal(value=False, name="busy")
    
    def open(self):
        """request shutter to open, interactive use"""
        self.control_bit.put(self.open_value)
    
    def close(self):
        """request shutter to close, interactive use"""
        self.control_bit.put(self.close_value)
    
    def set(self, value, **kwargs):
        """request the shutter to open or close, BlueSky plan use"""
        # ensure numerical additions to lists are now strings
        def input_filter(v):
            return str(v).lower()
        self.valid_open_values = list(map(input_filter, self.valid_open_values))
        self.valid_close_values = list(map(input_filter, self.valid_close_values))
        
        if self.busy.value:
            raise RuntimeError("shutter is operating")

        acceptables = self.valid_open_values + self.valid_close_values
        if input_filter(value) not in acceptables:
            msg = "value should be one of " + " | ".join(acceptables)
            msg += " : received " + str(value)
            raise ValueError(msg)
        
        status = DeviceStatus(self)
        
        def move_shutter():
            if input_filter(value) in self.valid_open_values:
                self.open()     # no need to yield inside a thread
            elif input_filter(value) in self.valid_close_values:
                self.close()
        
        def run_and_delay():
            self.busy.put(True)
            move_shutter()
            # sleep, since we don't *know* when the shutter has moved
            time.sleep(self.delay_s)
            self.busy.put(False)
            status._finished(success=True)
        
        threading.Thread(target=run_and_delay, daemon=True).start()
        return status
