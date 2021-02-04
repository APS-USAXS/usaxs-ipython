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
import os
import time


SECOND = 1
MINUTE = 60*SECOND
HOUR = 60*MINUTE

# write output to log file in userDir, name=MMDD-HHmm-heater-log.txt
user_dir = EpicsSignalRO("9idcLAX:userDir", name="user_dir", string=True)
user_dir.wait_for_connection()
log_file_name = os.path.join(
    user_dir.get(),
    datetime.datetime.now().strftime("%m%d-%H%M-heater-log.txt")
)

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
    actuate = Component(EpicsSignal, "start.PROC", kind="omitted")
    actuate_value = 1
    stop_signal = Component(EpicsSignal, "stop.PROC", kind="omitted")
    stop_value = 1
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
    actuate = Component(EpicsSignalWithRBV, "heating", kind="config", string=True)
    actuate_value = "On"
    stop_signal = Component(EpicsSignalWithRBV, "heating", kind="config", string=True)
    stop_value = "Off"


linkam_exit = EpicsSignal("9idcLAX:bit14", name="linkam_exit")
linkam_ci94 = Linkam_CI94_Device("9idcLAX:ci94:", name="linkam_ci94", egu="C")
linkam_tc1 = Linkam_T96_Device("9idcLINKAM:tc1:", name="linkam_tc1", egu="C")

for o in (linkam_ci94, linkam_exit, linkam_tc1):
    o.wait_for_connection()

#linkam = linkam_tc1     # choose which one
linkam = linkam_ci94     # choose which one


def isotime():
    """ISO-8601 format time, ms precision."""
    return datetime.datetime.now().isoformat(sep=" ", timespec='milliseconds')


def log_it(text):
    """Cheap, lazy way to add to log file.  Gotta be better way..."""
    if not os.path.exists(log_file_name):
        # create the file and header
        with open(log_file_name, "w") as f:
            f.write(f"# file: {log_file_name}\n")
            f.write(f"# created: {datetime.datetime.now()}\n")
            f.write(f"# from: {__file__}\n")
    with open(log_file_name, "a") as f:
        # write the payload
        f.write(f"{isotime()}: {text}\n")


def report():
    """Report current values for selected controller."""
    c = linkam
    log_it(
        f"{c.name}"
        f" T={c.readback.get():.1f}{c.egu}"
        f" setpoint={c.setpoint.get():.1f}{c.egu}"
        f" ramp:{c.ramp.get()}"
        f" settled: {c.settled}"
        f" done: {c.done.get()}"
    )


def planHeaterProcess():
    """BS plan: Run one temperature profile on the sample heater."""
    log_it(f"Starting planHeaterProcess() for {linkam.name}")
    report()

    yield from bps.mv(
        linkam.ramp, 3,
    )
    log_it(
        f"Change {linkam.name.get()} rate to {linkam.ramp.get():.0f} C/min"
    )

    t0 = time.time()
    # note: bps.mv waits until OBJECT.done.get() == 1 (just like a motor)
    # bps.abs_set only _sets_ the setpoint, must wait in a later step
    yield from bps.abs_set(
        linkam, 1083,
    )
    log_it(
        f"Change {linkam.name.get()} setpoint to {linkam.setpoint.get():.2f} C"
    )
    while linkam.done.get() not in (1, "Done"):
        if linkam_exit.get():  # Watch for user exit while waiting
            yield from bps.abs_set(linkam.stop_signal, linkam_stop_value)
            log_it(
                "User requested exit during set"
                f" after {(time.time()-t0)/60:.2f}m."
                " Stopping the heater."
            )
            report()
            return
        yield from bps.sleep(1)
    log_it(f"Done, that took {time.time()-t0:.2f}s")
    report()

    # two hours = 2 * HOUR, two minutes = 2 * MINUTE
    log_it("{linkam.name.get()} holding for 3 hours")
    t0 = time.time()
    time_expires = t0 + 3 * HOUR
    while time.time() < time_expires:
        if linkam_exit.get():
            yield from bps.abs_set(linkam.stop_signal, linkam_stop_value)
            log_it(
                "User requested exit during hold"
                f" after {(time.time()-t0)/60:.2f}m."
                " Stopping the heater."
            )
            report()
            return
        yield from bps.sleep(1)
    log_it("{linkam.name.get()} holding period ended")
    report()

     # Change rate to 3 C/min :
    yield from bps.mv(
        linkam.ramp, 3,
    )
    log_it(f"Change {linkam.name.get()} rate to {linkam.ramp.get():.0f} C/min")
    t0 = time.time()
    yield from bps.abs_set(
        linkam, 40,
    )
    log_it(f"Change {linkam.name.get()} setpoint to {linkam.setpoint.get():.2f} C")
    while linkam.done.get() not in (1, "Done"):
        if linkam_exit.get():  # Watch for user exit while waiting
            yield from bps.abs_set(linkam.stop_signal, linkam_stop_value)
            log_it(
                "User requested exit during set"
                f" after {(time.time()-t0)/60:.2f}m."
                " Stopping the heater."
            )
            report()
            return
        yield from bps.sleep(1)
    # note: bps.mv waits until OBJECT.done.get() == 1 (just like a motor)
    log_it(f"Done, that took {time.time()-t0:.2f}s")
    report()

    # DEMO: signal for an orderly exit after first run
    yield from bps.mv(linkam_exit, True)
    # -----------------------------------


