
"""
manage the user foler
"""

__all__ = [
    "matchUserInApsbss",
    "newUser",
    "techniqueSubdirectory"
]

from ..session_logs import logger
logger.info(__file__)

from ..devices import apsbss as apsbss_object
from ..framework import RE
from ..framework import specwriter
from .check_file_exists import filename_exists
from apstools.utils import cleanupText
import apstools.beamtime.apsbss
import datetime
import os


APSBSS_SECTOR = "09"
APSBSS_BEAMLINE = "9-ID-B,C"


def matchUserInApsbss(user):
    """
    pull information from apsbss matching on user name and date
    """
    dt = datetime.datetime.now()
    now = str(dt)
    cycle = apstools.beamtime.apsbss.getCurrentCycle()
    esafs = [
        esaf
        for esaf in apstools.beamtime.apsbss.getCurrentEsafs(
            APSBSS_SECTOR)
        if esaf["experimentStartDate"] <= now <= esaf["experimentEndDate"]
        if user in [
            entry["lastName"]
            for entry in esaf["experimentUsers"]
        ]
    ]
    proposals = [
        p
        for p in apstools.beamtime.apsbss.api_bss.listProposals(
            beamlineName=APSBSS_BEAMLINE, 
            runName=cycle)
        if p["startTime"] <= now <= p["endTime"]
        if user in [
            entry["lastName"]
            for entry in p["experimenters"]
        ]
    ]

    if len(esafs) > 2:
        logger.warning(
            "%d ESAF(s) match user %s at this time",
            len(esafs), user)
    if len(proposals) > 2:
        logger.warning(
            "%d proposal(s) match user %s at this time",
            len(proposals), user)
    if len(esafs) == 1 and len(proposals) == 1:
        # update the local apsbss PVs
        logger.info("ESAF %s", str(esafs[0]))
        logger.info("Proposal %s", str(proposals[0]))

        prefix = apsbss_object.prefix
        apstools.beamtime.apsbss.epicsSetup(
            prefix,
            APSBSS_BEAMLINE,
            cycle
            )
        apstools.beamtime.apsbss.epicsClear(prefix)

        apsbss_object.esaf.esaf_id.put(esafs[0]["esafId"])
        apsbss_object.proposal.proposal_id.put(proposals[0]["id"])

        apstools.beamtime.apsbss.epicsUpdate(prefix)


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
