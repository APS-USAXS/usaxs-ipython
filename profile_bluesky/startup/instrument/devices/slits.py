
"""
slits
"""

__all__ = [
    'guard_slit',
    'usaxs_slit',
    ]

from ..session_logs import logger
logger.info(__file__)

from bluesky import plan_stubs as bps
from ophyd import Component, EpicsSignal, MotorBundle

from ..framework import sd
from .general_terms import terms
from .usaxs_motor_devices import UsaxsMotor
from ..utils import move_motors


class UsaxsSlitDevice(MotorBundle):
    """
    USAXS slit just before the sample

    * center of slit: (x, y)
    * aperture: (h_size, v_size)
    """
    h_size = Component(UsaxsMotor, '9idcLAX:m58:c2:m8', labels=("uslit",))
    x      = Component(UsaxsMotor, '9idcLAX:m58:c2:m6', labels=("uslit",))
    v_size = Component(UsaxsMotor, '9idcLAX:m58:c2:m7', labels=("uslit",))
    y      = Component(UsaxsMotor, '9idcLAX:m58:c2:m5', labels=("uslit",))

    def set_size(self, *args, h=None, v=None):
        """move the slits to the specified size"""
        if h is None:
            raise ValueError("must define horizontal size")
        if v is None:
            raise ValueError("must define vertical size")
        move_motors(self.h_size, h, self.v_size, v)


class GuardSlitMotor(UsaxsMotor):
    status_update = Component(EpicsSignal, ".STUP")


class GSlitDevice(MotorBundle):
    """
    guard slit

    * aperture: (h_size, v_size)
    """
    bot  = Component(GuardSlitMotor, '9idcLAX:mxv:c0:m6', labels=("gslit",))
    inb  = Component(GuardSlitMotor, '9idcLAX:mxv:c0:m4', labels=("gslit",))
    outb = Component(GuardSlitMotor, '9idcLAX:mxv:c0:m3', labels=("gslit",))
    top  = Component(GuardSlitMotor, '9idcLAX:mxv:c0:m5', labels=("gslit",))
    x    = Component(UsaxsMotor, '9idcLAX:m58:c1:m5', labels=("gslit",))
    y    = Component(UsaxsMotor, '9idcLAX:m58:c0:m6', labels=("gslit",))

    h_size = Component(EpicsSignal, '9idcLAX:GSlit1H:size')
    v_size = Component(EpicsSignal, '9idcLAX:GSlit1V:size')

    h_sync_proc = Component(EpicsSignal, '9idcLAX:GSlit1H:sync.PROC')
    v_sync_proc = Component(EpicsSignal, '9idcLAX:GSlit1V:sync.PROC')

    gap_tolerance = 0.02        # actual must be this close to desired
    scale_factor = 1.2    # 1.2x the size of the beam should be good guess for guard slits.
    h_step_away = 0.2     # 0.2mm step away from beam
    v_step_away = 0.1     # 0.1mm step away from beam
    h_step_into = 1.1     # 1.1mm step into the beam (blocks the beam)
    v_step_into = 0.4     # 0.4mm step into the beam (blocks the beam)
    tuning_intensity_threshold = 500

    def set_size(self, *args, h=None, v=None):
        """move the slits to the specified size"""
        if h is None:
            raise ValueError("must define horizontal size")
        if v is None:
            raise ValueError("must define vertical size")
        move_motors(self.h_size, h, self.v_size, v)

    @property
    def h_gap_ok(self):
        gap = self.outb.position - self.inb.position
        return abs(gap - terms.SAXS.guard_h_size.get()) <= self.gap_tolerance

    @property
    def v_h_gap_ok(self):
        gap = self.top.position - self.bot.position
        return abs(gap - terms.SAXS.guard_v_size.get()) <= self.gap_tolerance

    @property
    def gap_ok(self):
        return self.h_gap_ok and self.v_h_gap_ok

    def status_update(self):
        # This code triggers a later exception when this code is called the next time.
        # It times out since writing 1 to this PV results in the PV ending up at 0.
        # The status object waits until it gets to 1.
        # TODO: If we .put to these fields, can we can avoid the dropped status timeouts?
        # That would need a special plan that does the .put()s
        yield from bps.abs_set(self.top.status_update, 1)
        yield from bps.sleep(0.05)
        yield from bps.abs_set(self.bot.status_update, 1)
        yield from bps.sleep(0.05)
        yield from bps.abs_set(self.outb.status_update, 1)
        yield from bps.sleep(0.05)
        yield from bps.abs_set(self.inb.status_update, 1)
        yield from bps.sleep(0.05)

        # clear a problem for now (removes the dropped status message)
        #  RuntimeError: Another set() call is still in progress
        # TODO: fix the root cause
        # https://github.com/APS-USAXS/ipython-usaxs/issues/253#issuecomment-678503301
        # https://github.com/bluesky/ophyd/issues/757#issuecomment-678524271
        self.top.status_update._set_thread = None
        self.bot.status_update._set_thread = None
        self.outb.status_update._set_thread = None
        self.inb.status_update._set_thread = None


guard_slit = GSlitDevice('', name='guard_slit')
usaxs_slit = UsaxsSlitDevice('', name='usaxs_slit')
sd.baseline.append(guard_slit)
sd.baseline.append(usaxs_slit)
