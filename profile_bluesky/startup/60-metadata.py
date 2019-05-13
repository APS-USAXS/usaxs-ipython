print(__file__)


# Set up default metadata

RE.md['beamline_id'] = 'APS USAXS 9-ID-C'
RE.md['proposal_id'] = 'testing Bluesky installation'
RE.md['pid'] = os.getpid()

# Add a callback that prints scan IDs at the start of each scan.


HOSTNAME = socket.gethostname() or 'localhost'
USERNAME = getpass.getuser() or 'APS USAXS user'
RE.md['login_id'] = USERNAME + '@' + HOSTNAME
RE.md['BLUESKY_VERSION'] = bluesky.__version__
RE.md['OPHYD_VERSION'] = ophyd.__version__
from apstools import __version__ as apstools_version
RE.md['APSTOOLS_VERSION'] = apstools_version
del apstools_version

_skip_these_ = "EPICS_BASE EPICS_BASE_PVT EPICS_DISPLAY_PATH EPICS_EXTENSIONS".split()
for key, value in os.environ.items():
    if key.startswith("EPICS") and key not in _skip_these_:
        RE.md[key] = value

print("Metadata dictionary (RE.md):")
_t = pyRestTable.Table()
_t.addLabel("key")
_t.addLabel("value")
for k, v in sorted(RE.md.items()):
    # print("RE.md['%s']" % k, "=", v)
    _t.addRow((k, v))
print(_t)
del _t
