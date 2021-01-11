"""
"""

__all__ = [
    "RE",
]

from ..session_logs import logger

import apstools
import bluesky
import databroker
import epics
import getpass
import h5py
import matplotlib
import numpy
import ophyd
import os
import pymongo
import pyRestTable
import socket
import spec2nexus

logger.info(__file__)

from .initialize import RE

# Set up default metadata

RE.md["beamline_id"] = "APS 9-ID-C USAXS"
RE.md["proposal_id"] = "testing"
RE.md["pid"] = os.getpid()

HOSTNAME = socket.gethostname() or "localhost"
USERNAME = getpass.getuser() or "APS 9-ID-C USAXS user"
RE.md["login_id"] = USERNAME + "@" + HOSTNAME

# useful diagnostic to record with all data
RE.md["versions"] = dict(
    bluesky=bluesky.__version__,
    ophyd=ophyd.__version__,
    databroker=databroker.__version__,
    apstools=apstools.__version__,
    epics=epics.__version__,
    h5py=h5py.__version__,
    numpy=numpy.__version__,
    matplotlib=matplotlib.__version__,
    spec2nexus=spec2nexus.__version__,
    pyRestTable=pyRestTable.__version__,
    pymongo=pymongo.__version__,
)
