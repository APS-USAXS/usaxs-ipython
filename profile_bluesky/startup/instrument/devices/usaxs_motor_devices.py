
"""
motor customizations
"""

__all__ = [
    'UsaxsMotor',
    'UsaxsMotorTunable',
]

from ..session_logs import logger
logger.info(__file__)

from apstools.devices import AxisTunerMixin
from apstools.devices import EpicsMotorLimitsMixin
from ophyd import Component, EpicsMotor, Signal

class UsaxsMotor(EpicsMotorLimitsMixin, EpicsMotor): ...

class UsaxsMotorTunable(AxisTunerMixin, UsaxsMotor):
    width = Component(Signal, value=0)
