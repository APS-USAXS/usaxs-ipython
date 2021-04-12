
"""
detector protection PLC
"""

__all__ = [
    'plc_protect',
    ]

from ..session_logs import logger
logger.info(__file__)

from bluesky.suspenders import SuspendWhenChanged
from bluesky import plan_stubs as bps
from ophyd import Component, Device, EpicsSignal
import time

from .emails import email_notices
from ..framework import RE, sd
from .shutters import ti_filter_shutter
from .user_data import user_data


class PlcProtectionDevice(Device):
    """
    Detector Protection PLC interface

    motion limit switches:
    * SAXS_Y, WAXS_X, AX
    * zero when OFF
    * two limits must be ON to allow safe move of the third
    """
    SAXS_Y = Component(EpicsSignal, 'X11')
    WAXS_X = Component(EpicsSignal, 'X12')
    AX = Component(EpicsSignal, 'X13')

    operations_status = Component(EpicsSignal, 'Y0')     # 0=not good, 1=good

    SLEEP_POLL_s = 0.1
    _tripped_message = None

    tripped_text = """
    Equipment protection is engaged, no power on motors.
    Fix PLC protection before any move. Stopping now.
    Call beamline scientists if you do not understand.

    !!!!!!  DO NOT TRY TO FIX THIS YOURSELF  !!!!!!

    """
    suspender = None

    @property
    def interlocked(self):
        return not 0 in (
            self.SAXS_Y.get(),
            self.WAXS_X.get(),
            self.AX.get())

    def wait_for_interlock(self, verbose=True):
        t0 = time.time()
        msg = "Waiting %g for PLC interlock, check limit switches"
        while not self.interlocked:
            yield from bps.sleep(self.SLEEP_POLL_s)
            if verbose:
                elapsed = time.time()-t0
                logger.info(msg, elapsed)
        yield from bps.null()   # always yield at least one Msg

    def stop_if_tripped(self, verbose=True):
        if self.operations_status.get() == 1:
            self._tripped_message = None
        else:
            msg = self.tripped_text
            if verbose:
                logger.warning(msg)
            yield from bps.mv(
                ti_filter_shutter, "close",
                user_data.collection_in_progress, 0,     # notify the GUI and others
            )
            if self.suspender is not None:
                msg += f"\n P.S. Can resume Bluesky scan: {self.suspender.allow_resume}\n"

            # send email to staff ASAP!!!
            msg += f"\n P.S. Can resume Bluesky scan: {suspend_plc_protect.allow_resume}\n"
            self._tripped_message = msg
            email_notices.send("!!! PLC protection Y0 tripped !!!", msg)

    def stop_in_suspender(self):
        if self.operations_status.get() == 1:
            msg = None
        else:
            msg = self.tripped_text
            if self.suspender is not None:
                msg += f"\n P.S. Can resume Bluesky scan: {self.suspender.allow_resume}\n"
            ti_filter_shutter.close()
            user_data.collection_in_progress.put(0)     # notify the GUI and others
        return msg


class PlcProtectSuspendWhenChanged(SuspendWhenChanged):
    """
    Customize for PLC that protects against detector collisions

    Watch the PLC's Y0 bit that signals if the PLC internal checks
    are active and OK.  Suspend the RunEngine if this ever goes bad.
    Force the user to quit the bluesky session and call the staff
    to resolve the problem.

    See the simulation test here:
    https://github.com/APS-USAXS/ipython-usaxs/blob/master/profile_bluesky/startup/notebooks/2018-12-05-USAXS-sim-plc-protect.ipynb
    """

    justification_text = """
    Significant equipment problem.  Do these steps:
    1. ^C twice      # interrupt the ipython kernel
    2. RE.abort()    # finalize current data streams (if any)
    3. exit          # quit bluesky session
    4. call beamline scientists

    """

    def _get_justification(self):
        """override default method to call plc_protect.stop_if_tripped()"""
        if not self.tripped:
            return ''

        self._tripped_message = None
        just = f'Signal {self._sig.name},'
        just += f' got "{self._sig.get()}",'
        just += f' expected "{self.expected_value}"'
        if not self.allow_resume:
            just += self.justification_text
            self._tripped_message = plc_protect.stop_in_suspender()

        return '\n----\n'.join(
            s for s in (just, self._tripped_message) if s)


plc_protect = PlcProtectionDevice('9idcLAX:plc:', name='plc_protect')

# Important for routine operations
# see: https://github.com/APS-USAXS/ipython-usaxs/issues/82#issuecomment-444187217
suspend_plc_protect = PlcProtectSuspendWhenChanged(
    plc_protect.operations_status,
    expected_value=1)
# this will suspend whenever PLC Y0 = 0 ("not good") -- we want that!
RE.install_suspender(suspend_plc_protect)
