
"""
miscellaneous signals and other
"""

__all__ = [
    'camy',
    'tcam',
    'tension',
    'waxsx',
    ]

from ..session_logs import logger
logger.info(__file__)

from .usaxs_motor import UsaxsMotor

camy = UsaxsMotor('9idcLAX:m58:c1:m7', name='camy')
tcam = UsaxsMotor('9idcLAX:m58:c1:m6', name='tcam')
tension = UsaxsMotor('9idcLAX:m58:c1:m8', name='tens')
waxsx = UsaxsMotor(
    '9idcLAX:m58:c0:m4', 
    name='waxsx', 
    labels=("waxs",))  # WAXS X
