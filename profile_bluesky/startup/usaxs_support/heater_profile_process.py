#!/usr/bin/env python

"""
Kickoff a temperature profile on the sample heater as a Bluesky plan.

This program is started/stopped/restarted from
``heater_profile_manager.sh``), in directory
``~/.ipython/profile/bluesky/usaxs_support/``.

Imports ``~/.ipython/user/heater_profile.py``.

This file watches an EPICS PV to trigger a heater schedule
as defined in ``heater_profile.planHeaterProcess()``.  The schedule
is executed as a Bluesky plan with a local RunEngine.  Since
no documents are collected here (no subscriptions to the local RE),
the only output from this program is via EPICS PVs and log files.

All configuration is communicated via EPICS PVs
which are interfaced here as ophyd EpicsSignal objects.

See https://github.com/APS-USAXS/ipython-usaxs/issues/482 for details.
"""

from bluesky import plan_stubs as bps
from bluesky import plans as bp
from bluesky import RunEngine
from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal

import os
import stdlogpj
import sys
import threading
import time


path = os.path.join("/home/beams/USAXS", ".ipython")
if path not in sys.path:
    sys.path.append(path)
path = os.path.join(path, "profile_bluesky/startup")
if path not in sys.path:
    sys.path.append(path)

# setup logging
# TODO: move to subdir of user's pwd?
path = os.path.join("/share1/USAXS_data", "heater_profile_process")
if not os.path.exists(path):
    print(f"Creating directory {path} for logging...")
    os.makedirs(path, mode=0o775)
os.chdir(path)
logger = stdlogpj.standard_logging_setup("process_logger")
logger.info(__file__)


from user.heater_profile import planHeaterProcess


# keep in sync with instrument.devices.general_terms
class Parameters_HeaterProcess(Device):
    # tell heater process to exit
    linkam_exit = Component(EpicsSignal, "9idcLAX:bit14")

    # heater process increments at 10 Hz
    linkam_pulse = Component(EpicsSignal, "9idcLAX:long16")

    # heater process is ready
    linkam_ready = Component(EpicsSignal, "9idcLAX:bit15")

    # heater process should start
    linkam_trigger = Component(EpicsSignal, "9idcLAX:bit16")


def run_in_thread(func):
    """(decorator) run ``func`` in thread"""

    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        # https://docs.python.org/3/library/threading.html#threading.Thread.daemon
        thread.daemon = True
        thread.start()
        return thread

    return wrapper


process_control = Parameters_HeaterProcess(name="process_control")
PULSE_MAX = 10000  # avoid int overflow
RE = RunEngine({})  # use our own RE, with no subscriptions


def countProcessesRunning():
    """Watch the pulse and count how many 10 Hz processes running."""
    pulse0 = process_control.linkam_pulse.get()
    time.sleep(10)  # watch for 10 s
    pulses = (process_control.linkam_pulse.get() - pulse0) % PULSE_MAX
    return round(pulses / PULSE_MAX)


@run_in_thread
def start10HzPulse():
    """
    Start the 10 Hz pulse incrementer.

    Also, this program manages a *pulse* PV that increments when
    the program is ready for operations.  The pulse increments at 10 Hz.
    This is useful in several ways:

    1. Pulse of ca. 0 Hz indicates *no* process is running.
    1. Pulse of ca. 10 Hz indicates the process is running.
    1. Pulse of n*10 Hz indicates n processes are running (an error condition).
    """
    logger.info("Starting the 10 Hz pulse...")
    tPulse = time.time()
    while True:
        if time.time() >= tPulse:
            tPulse = time.time() + 0.1
            process_control.linkam_pulse.put(
                (process_control.linkam_pulse.get() +1) % PULSE_MAX
            )
        time.sleep(0.01)


def main():
    process_control.wait_for_connection()
    process_control.linkam_exit.put(False)
    process_control.linkam_ready.put(False)

    logger.info("10s Check if another process is running...")
    nproc = countProcessesRunning()
    if nproc > 0:
        raise ValueError(
            f"Cannot start since {nproc} such process(es) already running."
        )

    start10HzPulse()

    print(f"{__file__} starting ...")
    logger.info("Watch for the EPICS trigger to start heater profile.")
    process_control.linkam_ready.put(True)
    while True:  # must run in main thread
        if process_control.linkam_exit.get():
            # TODO: how to break infinite loop in user's plan?
            #    Use the terminating suspender?
            process_control.linkam_exit.put(False)
            process_control.linkam_ready.put(False)
            logger.info("Exit signal received from EPICS.")
            break
        elif process_control.linkam_trigger.get():
            logger.debug("Calling user heater plan")
            process_control.linkam_ready.put(False)
            process_control.linkam_trigger.put(False)
            try:
                RE(planHeaterProcess())
            except Exception as exc:
                logger.error(
                    "RE(planHeaterProcess()) raised exception: %s", exc
                )
            logger.debug("Returned from RE(planHeaterProcess())")
            process_control.linkam_ready.put(True)
        time.sleep(0.1)


if __name__ == "__main__":
    main()
