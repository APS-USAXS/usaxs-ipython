
"""
laser distance meter AR500 support
"""

__all__ = [
    'laser',
    ]

from ..session_logs import logger
logger.info(__file__)


from ophyd import Component, Device, EpicsSignal, EpicsSignalRO



class LaserAR500(Device):
    """
    temporary support for laser distacne meter AR500
    uses analog in and digital out from Galil
    uses userCalc7 in LAX to convert to real distace
    uses Galil userAve (2 seconds long) to average noise out.
    to read distace use laser.distance.get()
    laser.enable(1)
    laser.enable(0)
    """
    distance    = Component(EpicsSignalRO, "9idcLAX:userCalc7.VAL")
    enable      = Component(EpicsSignal, "9idcRIO:Galil2bo1_CMD")
    dx_in       = Component(EpicsSignalRO, "9idcLAX:USAXS:Laser_dx")    
    dy_in       = Component(EpicsSignalRO, "9idcLAX:USAXS:Laser_dy")


laser = LaserAR500("", name="laser")


