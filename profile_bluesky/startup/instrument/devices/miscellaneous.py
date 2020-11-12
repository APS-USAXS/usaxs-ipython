
"""
miscellaneous signals and other
"""

__all__ = [
    'ar_start',
    'camy',
    'fuel_spray_bit',
    'tcam',
    'tension',
    'usaxs_q_calc',
    'userCalcs_lax',
    ]

from ..session_logs import logger
logger.info(__file__)

from ophyd import EpicsSignal
from .usaxs_motor_devices import UsaxsMotor

camy = UsaxsMotor('9idcLAX:m58:c1:m7', name='camy', labels=("motor",))
tcam = UsaxsMotor('9idcLAX:m58:c1:m6', name='tcam', labels=("motor",))
tension = UsaxsMotor('9idcLAX:m58:c1:m8', name='tens', labels=("motor",))

fuel_spray_bit = EpicsSignal(
    "9idcLAX:bit1",
    name="fuel_spray_bit")

from apstools.synApps.swait import SwaitRecord, UserCalcsDevice
userCalcs_lax = UserCalcsDevice("9idcLAX:", name="userCalcs_lax")

usaxs_q_calc = SwaitRecord("9idcLAX:USAXS:Q", name="usaxs_q_calc")
# usaxs_q = usaxs_q_calc.get()

ar_start = EpicsSignal("9idcLAX:USAXS:ARstart", name="ar_start")
# no PV : ay_start = EpicsSignal("9idcLAX:USAXS:AYstart", name="ay_start")
# no PV : dy_start = EpicsSignal("9idcLAX:USAXS:DYstart", name="dy_start")
