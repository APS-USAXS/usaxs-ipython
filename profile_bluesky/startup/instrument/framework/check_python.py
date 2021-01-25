"""
make sure we have the software packages we need
"""

__all__ = []

from ..session_logs import logger
import sys

logger.info(__file__)


# ensure Python 3.6+

req_version = (3, 6)
cur_version = sys.version_info
if cur_version < req_version:
    ver_str = ".".join((map(str, req_version)))
    raise RuntimeError(
        (
            f"Requires Python {ver_str} with BlueSky packages,"
            f" you have {sys.version}"
            f" from directory {sys.prefix}"
            "\n\n"
            "You should type 'exit' now and"
            " find the ipython with Bluesky."
        )
    )
