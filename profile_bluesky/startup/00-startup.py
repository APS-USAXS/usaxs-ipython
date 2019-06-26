print(__file__)

# issue #284: start logging console to file
# https://ipython.org/ipython-doc/3/interactive/magics.html#magic-logstart
from IPython import get_ipython
ipython = get_ipython()
# %logstart -o -t .ipython_console.log "rotate"
ipython.magic("logstart -o -t .ipython_console.log rotate")

from bluesky import RunEngine
from bluesky.utils import get_history
RE = RunEngine(get_history())

# Import matplotlib and put it in interactive mode.
import matplotlib.pyplot as plt
plt.ion()

# Make plots update live while scans run.
from bluesky.utils import install_qt_kicker
install_qt_kicker()

# Optional: set any metadata that rarely changes. in 60-metadata.py

# convenience imports
from bluesky.callbacks import *
from bluesky.plan_tools import print_summary
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import numpy as np
import bluesky.magics



# TODO: 2019-02-22: deprecate, remove
# def append_wa_motor_list(*motorlist):
#     """add motors to report in the `wa` command"""
#     BlueskyMagics.positioners += motorlist


# Uncomment the following lines to turn on 
# verbose messages for debugging.
import logging
# ophyd.logger.setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)


# diagnostics
from bluesky.utils import ts_msg_hook
#RE.msg_hook = ts_msg_hook
from bluesky.simulators import summarize_plan

import psutil
import resource

def resource_usage(title=None, vmem=False):
    """
    report on current resource usage
    """
    usage=resource.getrusage(resource.RUSAGE_SELF)
    msg = ""
    if title is not None:
        msg += f"{title}:"
    msg += f" user:{usage[0]:.3f}s"
    msg += f" sys:{usage[1]:.3f}s"
    msg += f" mem:{usage[2]/1000:.2f}MB"
    msg += f" cpu:{psutil.cpu_percent()}%"
    if vmem:
        msg += f" {psutil.virtual_memory()}"
    return msg.strip()
