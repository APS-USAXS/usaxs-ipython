
"""
APS only: connect with facility information
"""

__all__ = [
    'aps', 
    'undulator',
    ]

from ..session_logs import logger
logger.info(__file__)

import apstools.devices

from ..framework import sd

class ApsSpecialMode(apstools.devices.ApsMachineParametersDevice):

    @property
    def inUserOperations(self):
        valid_modes = (
            1,
            "USER OPERATIONS",
            "Bm Ln Studies",
        )
        verdict = self.machine_status.get() in valid_modes
        return verdict


aps = ApsSpecialMode(name="aps")
sd.baseline.append(aps)

undulator = apstools.devices.ApsUndulatorDual(
    "ID09", name="undulator")
sd.baseline.append(undulator)
