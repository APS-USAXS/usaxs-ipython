
"""
User can Set a PV to request scanning to stop

Scanning will stop between scans at next loop through scan sequence.
"""

__all__ = [
    'IfRequestedStopBeforeNextScan', 
    # 'undulator',
    ]

from ..session_logs import logger
logger.info(__file__)

def IfRequestedStopBeforeNextScan(): ...  # TODO: 41-commands
