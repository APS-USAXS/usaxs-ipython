"""
Run a temperature profile on the sample heater as a Bluesky plan.

This file defines a function named ``planHeaterProcess()``
that runs the desired temperature profile schedule.
All configuration is communicated via EPICS PVs
which are interfaced here as ophyd EpicsSignal objects.

Called (via ``import``) from ``heater_profile_process.py``
(which is started/stopped/restarted from ``heater_profile_manager.sh``),
both of which are in directory ``~/.ipython/profile/bluesky/usaxs_support/``.

See https://github.com/APS-USAXS/ipython-usaxs/issues/482 for details.
"""

from bluesky import plan_stubs as bps
from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO
from ophyd import EpicsSignalWithRBV
from ophyd import PVPositioner
from ophyd import Signal
import datetime
import time


# FIXME: not important now, use print()
# import logging
# logger = logging.getLogger(__name__)
# logger.info(__file__)
# logger.setLevel("INFO")

# Can't call the instrument package in this module.
# Thus, we must re-define these devices here


class FeatureMixin(Device):

    @property
    def settled(self):
        return self.done.get() == self.done_value

class Linkam_CI94_Device(FeatureMixin, PVPositioner):
    """The old Linkam controller."""
    readback = Component(EpicsSignalRO, "temp", kind="normal")
    setpoint = Component(EpicsSignal, "setLimit", kind="omitted")
    ramp = Component(EpicsSignal, "setRate", kind="config")
    done = Component(Signal, value=1, kind="omitted")
    done_value = True
    tolerance = Component(Signal, value=1, kind="config")
    start_button = Component(EpicsSignal, "start.PROC", kind="omitted")
    stop_button = Component(EpicsSignal, "stop.PROC", kind="omitted")
    status_message = Component(EpicsSignalRO, "status", kind="config")

    def cb_done(self, *args, **kwargs):
        """Is readback close enough to setpoint?"""
        diff = self.readback.get() - self.setpoint.get()
        decision = abs(diff) <= abs(self.tolerance.get())
        self.done.put(decision)

    def __init__(self, prefix="", *, egu="", **kwargs):
        PVPositioner.__init__(self, prefix, egu=egu, **kwargs)
        self.readback.subscribe(self.cb_done)
        self.setpoint.subscribe(self.cb_done)


class Linkam_T96_Device(FeatureMixin, PVPositioner):
    """The newer Linkam controller."""
    readback = Component(EpicsSignalRO, "temperature_RBV", kind="normal")
    setpoint = Component(EpicsSignalWithRBV, "rampLimit", kind="omitted")
    ramp = Component(EpicsSignalWithRBV, "rampRate", kind="config")
    done = Component(EpicsSignalRO, "rampAtLimit_RBV", kind="omitted")
    heating_switch = Component(EpicsSignalWithRBV, "heating", kind="config")


def isotime():
    return datetime.datetime.now().isoformat(sep=" ", timespec='milliseconds')


def report():
    for c in (linkam_ci94, linkam_tc1):
        print(
            f"{isotime()}:"
            f" {c.name}"
            f" T={c.readback.get():.1f}{c.egu}"
            f" ramp:{c.ramp.get()}"
            f" settled: {c.settled}"
            f" done: {c.done.get()}"
        )


def planHeaterProcess():
    """BS plan: Run a temperature profile on the sample heater."""
    # run a temperature profile
    # -----------------------------------
    # this is an example:
    # go to 43 C and hold for 30 s
    # go to 48 C and hold for 30 s
    # go to 40 C and hold for 30 s
    # exit

    report()

    for temp in (43, 48, 40):
        print(f"{isotime()}: Setting to {temp} C")
        t0 = time.time()
        yield from bps.mv(
            linkam_ci94, temp,
            linkam_tc1, temp,
        )
        # note: bps.mv waits until OBJECT.done.get() == 1 (just like a motor)
        print(f"{isotime()}: Done, that took {time.time()-t0:.2f}s")
        report()
        print(f"{isotime()}: Holding for 30 s")
        yield from bps.sleep(30)
        report()

    # DEMO: signal for an orderly exit after first run
    yield from bps.mv(linkam_exit, True)
    # -----------------------------------


linkam_exit = EpicsSignal("9idcLAX:bit14", name="linkam_exit")
linkam_ci94 = Linkam_CI94_Device("9idcLAX:ci94:", name="linkam_ci94", egu="C")
linkam_tc1 = Linkam_T96_Device("9idcLINKAM:tc1:", name="linkam_tc1", egu="C")

for o in (linkam_ci94, linkam_exit, linkam_tc1):
    o.wait_for_connection()
