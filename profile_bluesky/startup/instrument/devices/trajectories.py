
"""
USAXS Fly Scan trajectories
"""

__all__ = [
    'flyscan_trajectories',
    ]

from ..session_logs import logger
logger.info(__file__)

from ophyd import Component, Device, EpicsSignal


class Trajectories(Device):
    """fly scan trajectories"""
    ar = Component(EpicsSignal, "9idcLAX:traj1:M1Traj")
    ay = Component(EpicsSignal, "9idcLAX:traj3:M1Traj")
    dy = Component(EpicsSignal, "9idcLAX:traj2:M1Traj")
    num_pulse_positions = Component(EpicsSignal, "9idcLAX:traj1:NumPulsePositions")

flyscan_trajectories = Trajectories(name="flyscan_trajectories")
