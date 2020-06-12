
"""
motor customizations
"""

__all__ = [
    'UsaxsMotor',
    'UsaxsMotorTunable',
]

from ..session_logs import logger
logger.info(__file__)

from apstools.devices import AxisTunerMixin
from ophyd import Component, EpicsMotor, Signal

# custom for any overrides (none now)

# FIXME: https://github.com/APS-USAXS/ipython-usaxs/issues/341
# class UsaxsMotor(EpicsMotor): ...

# TODO: fix the set_lim() method
class MyEpicsMotor(EpicsMotor):

    def set_lim(self, low, high):
        '''
        Sets the low and high travel limits of motor

        * No action taken if motor is moving.
        * Low limit is set to lesser of (low, high)
        * High limit is set to greater of (low, high)

        Included here for compatibility with similar with SPEC command.

        Parameters
        ----------
        high : float
           Limit of travel in the positive direction.
        low : float
           Limit of travel in the negative direction.
        '''
        if not self.moving:
            # update EPICS
            lo = min(low, high)
            hi = max(low, high)
            if lo <= self.position <= hi:
                # fix is here! (ophyd sets hi limit to lo and low limit to hi)
                self.high_limit_travel.put(hi)
                self.low_limit_travel.put(lo)
                # and ophyd metadata dictionary will update via CA monitor
            else:
                logger.debug(
                    "Could not set motor limits to (%f, %f) at position %g", 
                    lo, 
                    self.position, 
                    hi
                    )


class UsaxsMotor(MyEpicsMotor): ...

class UsaxsMotorTunable(AxisTunerMixin, UsaxsMotor):
    width = Component(Signal, value=0)
