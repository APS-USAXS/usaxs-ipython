
"""
Support the different instrument modes
"""

### This file is work-in-progress
# see: https://subversion.xray.aps.anl.gov/spec/beamlines/USAXS/trunk/macros/local/usaxs_commands.mac
# 2020-02-24,PRJ:  or is it no longer?

__all__ = """
    mode_USAXS
""".split()

from ..session_logs import logger
logger.info(__file__)

from bluesky import plan_stubs as bps

# from ..devices import a_stage, d_stage, saxs_stage
# from ..devices import ccd_shutter, ti_filter_shutter
# from ..devices import guard_slit, usaxs_slit
# from ..devices import plc_protect
# from ..devices import terms
# from ..devices import user_data
# from ..devices import waxsx
from .move_instrument import UsaxsSaxsModes
# from ..utils import angle2q, q2angle
# from ..utils import becplot_prune_fifo


def mode_USAXS(): ...  # TODO:
