
"""
test if file name exists, Windows-unique

see: https://github.com/APS-USAXS/ipython-usaxs/issues/343
"""

__all__ = ["filename_exists",]

from ..session_logs import logger
logger.info(__file__)

import os

def filename_exists(fname, case_insensitive=True):
    """
    test if a file name exists, even case-insensitive
    """
    exists = os.path.exists(fname)
    if not case_insensitive:
        return exists

    # TODO: check all filenames for case-insensitive match
    # see: https://github.com/APS-USAXS/ipython-usaxs/issues/343
    path, filename = os.path.split(fname)
    fn_lower = fname.lower

    return exists
