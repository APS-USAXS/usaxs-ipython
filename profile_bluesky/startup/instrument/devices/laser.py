
"""
laser distance meter AR500 support
"""

__all__ = [
    'laser_distacne_meter',
    ]

from ..session_logs import logger
logger.info(__file__)


from ophyd import Component, Device, EpicsSignal



class LaserAR500(Device):
     """
    temporary support for laser distacne meter AR500
    uses analog in and digital out from Galil 
    uses userCalc7 in LAX to convert to real distace
    uses Galil userAve (2 seocnds long) to average noise out. 
    read dsiatce use laser_distance_meter.distance.get()
    laser_distance_meter.enable(1)
    laser_distance_meter.enable(0)
    """
    distance    = Component(EpicsSignalRO, "9idcLAX:userCalc7.VAL")
    enable      = Component(EpicsSignal, "9idcRIO:Galil2bo1_CMD")


laser_distance_meter = LaserAR500("", name="LaserAR500")


