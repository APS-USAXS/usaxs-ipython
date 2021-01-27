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

# import os
# import sys


# sys.path.append(
#     os.path.join(
#         "/home/beams/USAXS",
#         ".ipython",
#         "profile_bluesky/startup",
#     )
# )

# TODO: logger.info(__file__)

from bluesky import plan_stubs as bps
from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal
# from ophyd import EpicsSignalRO
# from ophyd import EpicsSignalWithRBV

# Can't call the instrument package in this module.
# Thus, we must re-define these devices here

# class Linkam_T96_Device(Device):


linkam_exit = EpicsSignal("9idcLAX:bit14", name="linkam_exit")
# linkam_tc1 = Linkam_T96_Device("9idcLINKAM:tc1:", name="linkam_tc1")


def planHeaterProcess():
    """BS plan: Run a temperature profile on the sample heater."""
    # run the desired temperature profile
    # -----------------------------------
    # TODO: user will modify as a Bluesky plan
    t_sleep = 1.54
    print(f"sleep for {t_sleep} second(s)")
    yield from bps.sleep(t_sleep)  # simulated do-nothing profile

    # DEMO: signal for an orderly exit after first run
    yield from bps.mv(linkam_exit, True)
    # -----------------------------------
