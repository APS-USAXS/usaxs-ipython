
"""
rotate the sample with PI C867 motor
"""

__all__ = """
    PI_Off
    PI_onF
    PI_onR
""".split()

from ..session_logs import logger
logger.info(__file__)

from ..devices import pi_c867
from bluesky import plan_stubs as bps


def PI_Off(timeout=1, md=None):
    """plan: stop rotating sample in either direction"""
    yield from bps.abs_set(pi_c867.motor_stop, 1, timeout=timeout)

def PI_onF(timeout=10, md=None):
    """plan: start rotating sample in forward direction"""
    yield from bps.mv(pi_c867.home, "forward", timeout=timeout)
    yield from bps.abs_set(pi_c867.jog_forward, 1)

def PI_onR(timeout=10, md=None):
    """plan: start rotating sample in reverse direction"""
    yield from bps.mv(pi_c867.home, "reverse", timeout=timeout)
    yield from bps.abs_set(pi_c867.jog_reverse, 1)
