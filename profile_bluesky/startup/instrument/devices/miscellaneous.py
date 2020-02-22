
"""
miscellaneous signals and other
"""

__all__ = [
    'camy',
    'fuel_spray_bit',
    'tcam',
    'tension',
    'waxsx',
    ]

from ..session_logs import logger
logger.info(__file__)

from ophyd import EpicsSignal
from .usaxs_motor import UsaxsMotor

camy = UsaxsMotor('9idcLAX:m58:c1:m7', name='camy', labels=("motor",))
tcam = UsaxsMotor('9idcLAX:m58:c1:m6', name='tcam', labels=("motor",))
tension = UsaxsMotor('9idcLAX:m58:c1:m8', name='tens', labels=("motor",))
waxsx = UsaxsMotor(
    '9idcLAX:m58:c0:m4', 
    name='waxsx', 
    labels=("waxs", "motor"))  # WAXS X

fuel_spray_bit = EpicsSignal(
    "9idcLAX:bit1", 
    name="fuel_spray_bit")
