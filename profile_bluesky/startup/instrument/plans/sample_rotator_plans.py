
"""
rotate the sample with PI C867 motor
"""

__all__ = """
    PI_off
    PI_onF
    PI_onR
""".split()

from ..session_logs import logger
logger.info(__file__)

from ..devices import pi_c867
from bluesky import plan_stubs as bps


def PI_off(sleep_time=1):
    """plan: stop rotating sample in either direction"""
    yield from bps.mv(pi_c867.jog_forward, 0)
    yield from bps.sleep(sleep_time)
    yield from bps.mv(pi_c867.jog_reverse, 0)
    yield from bps.sleep(sleep_time)

def PI_onF(sleep_time=10):
    """plan: start rotating sample in forward direction"""
    yield from bps.mv(pi_c867.home_forward, 1)
    yield from bps.sleep(sleep_time)
    yield from bps.mv(pi_c867.jog_forward, 1)

def PI_onR(sleep_time=10):
    """plan: start rotating sample in reverse direction"""
    yield from bps.mv(pi_c867.home_reverse, 1)
    yield from bps.sleep(sleep_time)
    yield from bps.mv(pi_c867.jog_reverse, 1)
