
"""
manage the user foler
"""

__all__ = [
    "newUser",
    "techniqueSubdirectory"
]

from ..session_logs import logger
logger.info(__file__)

from ..callbacks import specwriter
from .check_file_exists import filename_exists
from .initialize import RE
from apstools.beamtime import apsbss
from apstools.utils import cleanupText
import datetime
import os


APSBSS_SECTOR = "09"
APSBSS_BEAMLINE = "9-ID-B,C"


def matchUserInApsbss(user):
    """
    pull information from apsbss matching on user name and date
    """
    dt = datetime.datetime.now()
    cycle = apsbss.getCurrentCycle()
    esafs = apsbss.getCurrentEsafs(APSBSS_SECTOR)
    proposals = apsbss.api_bss.listProposals(
        beamlineName=APSBSS_BEAMLINE, 
        runName=cycle)
    # TODO: search for user and match date
    # TODO: report if not unique
    # TODO: get unique esaf_id
    # TODO: get unique proposal_id
    # TODO: if unique both, update the local apsbss PVs


def _setSpecFileName(path, scan_id=1):
    """
    SPEC file name
    """
    stub = os.path.basename(path)
    # TODO: full path?
    fname = f"{stub}.dat"
    if filename_exists(fname):
        logger.warning(">>> file already exists: %s <<<", fname)
        specwriter.newfile(fname, RE=RE)
        handled = "appended"
    else:
        specwriter.newfile(fname, scan_id=scan_id, RE=RE)
        handled = "created"
    logger.info(f"SPEC file name : {specwriter.spec_filename}")
    logger.info(f"File will be {handled} at end of next bluesky scan.")


def newUser(user, scan_id=1, month=None, day=None):
    """
    setup for a new user

    Create (if necessary) new user directory in
    current working directory with month, day, and
    given user name as shown in the following table.
    Each technique (SAXS, USAXS, WAXS) will be
    reponsible for creating its subdirectory
    as needed.

    ======================  ========================
    purpose                 folder
    ======================  ========================
    user data folder base   <CWD>/MM_DD_USER
    SPEC data file          <CWD>/MM_DD_USER/MM_DD_USER.dat
    AD folder - SAXS        <CWD>/MM_DD_USER/MM_DD_USER_saxs/
    folder - USAXS          <CWD>/MM_DD_USER/MM_DD_USER_usaxs/
    AD folder - WAXS        <CWD>/MM_DD_USER/MM_DD_USER_waxs/
    ======================  ========================
    """
    global specwriter

    dt = datetime.datetime.now()
    month = month or dt.month
    day = day or dt.day

    clean = cleanupText(user)
    stub = f"{month:02d}_{day:02d}_{clean}"
    path = os.path.join(os.getcwd(), stub)

    if not os.path.exists(path):
        logger.info("Creating user directory: %s", path)
        os.mkdir(path)

    # SPEC file name
    _setSpecFileName(path, scan_id=scan_id)

    # TODO: where to save this path for general use?
    # TODO: pull info from apsbss matching user name (#360)
    matchUserInApsbss(user)

    return path


def techniqueSubdirectory(technique):
    """
    Create a technique-based subdirectory per table in ``newUser()``.

    NOTE: Assumes CWD is now the directory returned by ``newFile()``
    """
    pwd = os.getcwd()
    stub = os.path.basename(pwd)
    path = os.path.join(pwd, f"{stub}_{technique}")

    if not os.path.exists(path):
        logger.info("Creating technique directory: %s", path)
        os.mkdir(path)

    return path
