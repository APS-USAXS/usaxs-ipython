
"""
permission to operate with X-rays
"""

__all__ = [
    'operations_in_9idc',
    ]

from ..session_logs import logger
logger.info(__file__)


from .diagnostics import diagnostics


def operations_in_9idc():
    """
    returns True if allowed to use X-ray beam in 9-ID-C station
    """
    return diagnostics.PSS.c_station_enabled
