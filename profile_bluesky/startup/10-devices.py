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

# Set up custom or complex devices

class TunableEpicsMotor(EpicsMotor, AxisTunerMixin):
    pass
