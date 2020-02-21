
"""
sample stage
"""

__all__ = [
    's_stage',
    ]

from ..session_logs import logger
logger.info(__file__)

from ophyd import Component, MotorBundle
from .usaxs_motor import UsaxsMotor

class UsaxsSampleStageDevice(MotorBundle):
    """USAXS sample stage"""
    x = Component(
        UsaxsMotor, 
        '9idcLAX:m58:c2:m1', 
        labels=("sample",))
    y = Component(
        UsaxsMotor, 
        '9idcLAX:m58:c2:m2', 
        labels=("sample",))

s_stage = UsaxsSampleStageDevice('', name='s_stage')
