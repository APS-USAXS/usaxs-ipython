
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
from ophyd import Component, EpicsMotor, Signal

# custom for any overrides (none now)
class UsaxsMotor(EpicsMotor): ...

class UsaxsMotorTunable(AxisTunerMixin, UsaxsMotor):
    width = Component(Signal, value=0)
