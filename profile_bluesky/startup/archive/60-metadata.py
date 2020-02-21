logger.info(__file__)
# logger.debug(resource_usage(os.path.split(__file__)[-1]))

"""Set up default metadata"""


RE.md['beamline_id'] = 'APS USAXS 9-ID-C'
RE.md['proposal_id'] = 'testing Bluesky installation'
RE.md['pid'] = os.getpid()

# Add a callback that prints scan IDs at the start of each scan.


HOSTNAME = socket.gethostname() or 'localhost'
USERNAME = getpass.getuser() or 'APS USAXS user'
RE.md['login_id'] = USERNAME + '@' + HOSTNAME
RE.md['versions'] = {}
RE.md['versions']['bluesky'] = bluesky.__version__
RE.md['versions']['ophyd'] = ophyd.__version__
from apstools import __version__ as apstools_version
from databroker import __version__ as db_version
RE.md['versions']['databroker'] = db_version
RE.md['versions']['apstools'] = apstools_version
del apstools_version
del db_version
RE.md['versions']['epics'] = epics.__version__

_skip_these_ = "EPICS_BASE EPICS_BASE_PVT EPICS_DISPLAY_PATH EPICS_EXTENSIONS".split()
for key, value in os.environ.items():
    if key.startswith("EPICS") and key not in _skip_these_:
        RE.md[key] = value

print_RE_md()
