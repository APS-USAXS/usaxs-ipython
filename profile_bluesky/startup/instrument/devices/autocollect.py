
"""
automated data collection

To start the automatic data collection plan:

    RE(auto_collect.remote_ops())
"""

__all__ = [
    'AutoCollectDataDevice', 
    'auto_collect',
    ]

from ..session_logs import logger
logger.info(__file__)

from bluesky import plan_stubs as bps
from ophyd import Component, Device, EpicsSignal, EpicsSignalRO
import os

from ..plans import preUSAXStune
from ..plans import useModeRadiography
from ..plans import run_command_file


class AutoCollectDataDevice(Device):
    trigger = Component(EpicsSignal, "Start", string=True)
    commands = Component(EpicsSignal, "StrInput", string=True)
    permit = Component(EpicsSignal, "Permit", string=True)
    idle_interval = 2       # seconds

    def remote_ops(self, *args, **kwargs):
        """
        Bluesky plan to enable PV-directed data collection

        The plan will exit when:

        * `permit` is not "enable" or 1
        * user types `^C` twice (user types `RE.abort()` then)
        * unhandled exception

        The plan will collect data when `trigger` goes to "start" or 1.
        `trigger` immediately goes back to "stop" or 0.

        The command to be run is in `commands` which is:

        * a named command defined here
        * a command file in the present working directory
        """
        yield from bps.mv(self.permit, "enable")
        yield from bps.sleep(1)

        logger.info("waiting for user commands")
        while self.permit.get() in (1, "enable"):
            if self.trigger.get() in (1, "start"):
                logger.debug("starting user commands")
                yield from bps.mv(self.trigger, 0)

                command = self.commands.get()
                if command == "preUSAXStune":
                    yield from preUSAXStune()
                elif command == "useModeRadiography":
                    yield from useModeRadiography()
                elif os.path.exists(command):
                    yield from run_command_file(command)
                else:
                    logger.warning("unrecognized command: %s", command)
                logger.info("waiting for next user command")
            else:
                yield from bps.sleep(self.idle_interval)


auto_collect = AutoCollectDataDevice(
    "9idcLAX:AutoCollection", 
    name="auto_collect")
