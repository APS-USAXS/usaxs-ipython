"""
local, custom Device definitions
"""

from .aps_source import *
from .permit import *

from .constants import *
from .general_terms import *
from .sample_data import *
from .user_data import *

# do these first
from .scalers import *
from .shutters import *
from .stages import *

# then these
from .amplifiers import *
from .autosave import *
from .axis_tuning import *
from .diagnostics import *
from .emails import *
from .filters import *
from .linkam import *
from .miscellaneous import *
from .monochromator import *
from .protection_plc import *
from .sample_rotator import *
from .slits import *
from .struck3820 import *
from .suspenders import *
from .trajectories import *
from .usaxs_fly_scan import *
from .laser import *

# finally these area detectors
from .alta_module import *
from .blackfly_module import *
from .dexela_module import *
from .pilatus_module import *
# from .simdetector import *

# and only when all devices are defined
from .autocollect import *

