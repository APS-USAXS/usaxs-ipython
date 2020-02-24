
"""
run batch of scans from command list
"""

__all__ = [
    'beforeScanComputeOtherStuff',
]

from ..session_logs import logger
logger.info(__file__)

from bluesky import plan_stubs as bps


def beforeScanComputeOtherStuff():
    """
    things to be computed and set before each data collection starts
    """
    yield from bps.null()       # TODO: remove this once you add the "other stuff"
