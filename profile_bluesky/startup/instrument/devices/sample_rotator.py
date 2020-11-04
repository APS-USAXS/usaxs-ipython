
"""
rotate the sample with PI C867 motor
"""

__all__ = [
    "pi_c867",
    ]

from ..session_logs import logger
logger.info(__file__)

from ophyd import Component, Device, EpicsSignal


class SampleRotator(Device):
    """
    Use an EPICS motor to rotate sample while collecting data.

    Rotate sample with appropriate speed while collecting data
    to integrate over same area on sample for each point.

    Do not interface with normal motor API.

    This motor is intentionally NOT controlled by spec and
    presumably also is not in BS (as a motor). Pushing jog button
    starts rotation at speed which is setup in epics. Switching off
    and on (with resets) is needed since else epics runs out of
    counters and stops mid way.
    """
    home_forward = Component(EpicsSignal, ".HOMF")
    home_reverse = Component(EpicsSignal, ".HOMR")
    jog_forward = Component(EpicsSignal, ".JOGF")
    jog_reverse = Component(EpicsSignal, ".JOGR")

    speed = Component(EpicsSignal, ".S")
    velocity = Component(EpicsSignal, ".VELO")


pi_c867 = SampleRotator("9idcPI:c867:c0:m1", name="pi_c867")
