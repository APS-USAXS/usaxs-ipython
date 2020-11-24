
"""
run batch of scans from command list
"""

__all__ = """
    after_command_list
    after_plan
    before_command_list
    before_plan
    beforeScanComputeOtherStuff
    command_list_as_table
    execute_command_list
    get_command_list
    parse_Excel_command_file
    parse_text_command_file
    postCommandsListfile2WWW
    run_command_file
    run_python_file
    summarize_command_file
    sync_order_numbers
""".split()


from ..session_logs import logger
logger.info(__file__)

from apstools.utils import ExcelDatabaseFileGeneric
from apstools.utils import rss_mem
from bluesky import plan_stubs as bps
from IPython import get_ipython
from usaxs_support.nexus import reset_manager
from usaxs_support.surveillance import instrument_archive
import datetime
import os
import pyRestTable

from ..devices import constants
from ..devices import measure_background
from ..devices import saxs_det, waxs_det
from ..devices import terms
from ..devices import ti_filter_shutter
from ..devices import upd_controls, I0_controls, I00_controls, trd_controls
from ..devices import user_data
from ..utils.quoted_line import split_quoted_line
from .axis_tuning import instrument_default_tune_ranges
from .axis_tuning import update_EPICS_tuning_widths
from .axis_tuning import user_defined_settings
from .doc_run import documentation_run
from .mode_changes import mode_BlackFly
from .mode_changes import mode_Radiography
from .mode_changes import mode_SAXS
from .mode_changes import mode_USAXS
from .mode_changes import mode_WAXS
from .sample_rotator_plans import PI_Off, PI_onF, PI_onR


def beforeScanComputeOtherStuff():
    """Actions before each data collection starts."""
    yield from bps.null()       # TODO: remove this once you add the "other stuff"


def postCommandsListfile2WWW(commands):
    """Post list of commands to WWW and archive the list for posterity."""
    tbl_file = "commands.txt"
    tbl = command_list_as_table(commands)
    timestamp = datetime.datetime.now().isoformat().replace("T", " ")
    file_contents = "bluesky command sequence\n"
    file_contents += f"written: {timestamp}\n"
    file_contents += str(tbl.reST())

    # post for livedata page
    # path = "/tmp"
    path = "/share1/local_livedata"
    with open(os.path.join(path, tbl_file), "w") as fp:
        fp.write(file_contents)

    # post to EPICS
    yield from bps.mv(
        user_data.macro_file, os.path.split(tbl_file)[-1],
        user_data.macro_file_time, timestamp,
        )

    # keep this list for posterity
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = "/share1/log/macros"
    posterity_file = f"{timestamp}-{tbl_file}"
    with open(os.path.join(path, posterity_file), "w") as fp:
        fp.write(file_contents)



def before_command_list(md=None, commands=None):
    """Actions before a command list is run."""
    from .scans import preUSAXStune

    if md is None:
        md = {}

    yield from bps.mv(
        user_data.time_stamp, str(datetime.datetime.now()),
        user_data.state, "Starting data collection",
        user_data.collection_in_progress, 1,
        ti_filter_shutter, "close",
        terms.SAXS.collecting, 0,
        terms.WAXS.collecting, 0,
    )
    if constants["MEASURE_DARK_CURRENTS"]:
        yield from measure_background(
            [upd_controls, I0_controls, I00_controls, trd_controls],
        )

    # reset the ranges to be used when tuning optical axes (issue #129)
    # These routines are defined in file: 29-axis-tuning.py
    yield from instrument_default_tune_ranges()
    yield from user_defined_settings()
    yield from update_EPICS_tuning_widths()

    yield from beforeScanComputeOtherStuff()        # 41-commands.py

    if terms.preUSAXStune.run_tune_on_qdo.get():
        logger.info(
            "Running preUSAXStune as requested at start of measurements"
        )
        yield from preUSAXStune(md=md)

    if constants["SYNC_ORDER_NUMBERS"]:
        yield from sync_order_numbers()

    if commands is not None:
        yield from postCommandsListfile2WWW(commands)

    # force the next FlyScan to reload the metadata configuration
    # which forces a (re)connection to the EPICS PVs
    reset_manager()


def after_command_list(md=None):
    """Actions after a command list is run."""
    if md is None:
        md = {}
    yield from bps.mv(
        user_data.time_stamp, str(datetime.datetime.now()),
        user_data.state, "USAXS macro file done",  # exact text triggers the music
        user_data.collection_in_progress, 0,
        ti_filter_shutter, "close",
    )


def before_plan(md=None):
    """Actions before every data collection plan."""
    if md is None:
        md = {}
    from .scans import preSWAXStune, preUSAXStune

    if terms.preUSAXStune.needed:
        # tune at previous sample position
        # don't overexpose the new sample position
        # select between positions
        mode_now = terms.SAXS.UsaxsSaxsMode.get(as_string=True)
        if mode_now == "USAXS in beam" :
            yield from preUSAXStune(md=md)
        else:
            yield from preSWAXStune(md=md)


def after_plan(weight=1, md=None):
    """Actions after every data collection plan."""
    from .scans import preUSAXStune

    if md is None:
        md = {}

    yield from bps.mv(      # increment it
        terms.preUSAXStune.num_scans_last_tune,
        terms.preUSAXStune.num_scans_last_tune.get() + weight
        )


def parse_Excel_command_file(filename):
    """
    Parse an Excel spreadsheet with commands, return as command list.

    TEXT view of spreadsheet (Excel file line numbers shown)::

        [1] List of sample scans to be run
        [2]
        [3]
        [4] scan    sx  sy  thickness   sample name
        [5] FlyScan 0   0   0   blank
        [6] FlyScan 5   2   0   blank

    PARAMETERS

    filename : str
        Name of input Excel spreadsheet file.  Can be relative or absolute path,
        such as "actions.xslx", "../sample.xslx", or
        "/path/to/overnight.xslx".

    RETURNS

    list of commands : list[command]
        List of command tuples for use in ``execute_command_list()``

    RAISES

    FileNotFoundError
        if file cannot be found

    """
    full_filename = os.path.abspath(filename)
    assert os.path.exists(full_filename)
    xl = ExcelDatabaseFileGeneric(full_filename)

    commands = []

    if len(xl.db) > 0:
        for i, row in enumerate(xl.db.values()):
            action, *values = list(row.values())

            # trim off any None values from end
            while len(values) > 0:
                if values[-1] is not None:
                    break
                values = values[:-1]

            commands.append((action, values, i+1, list(row.values())))

    return commands


def parse_text_command_file(filename):
    """
    Parse a text file with commands, return as command list.

    * The text file is interpreted line-by-line.
    * Blank lines are ignored.
    * A pound sign (#) marks the rest of that line as a comment.
    * All remaining lines are interpreted as commands with arguments.

    Example of text file (no line numbers shown)::

        #List of sample scans to be run
        # pound sign starts a comment (through end of line)

        # action  value
        mono_shutter open

        # action  x y width height
        uslits 0 0 0.4 1.2

        # action  sx  sy  thickness   sample name
        FlyScan 0   0   0   blank
        FlyScan 5   2   0   "empty container"

        # action  sx  sy  thickness   sample name
        SAXS 0 0 0 blank

        # action  value
        mono_shutter close

    PARAMETERS

    filename : str
        Name of input text file.  Can be relative or absolute path,
        such as "actions.txt", "../sample.txt", or
        "/path/to/overnight.txt".

    RETURNS

    list of commands : list[command]
        List of command tuples for use in ``execute_command_list()``

    RAISES

    FileNotFoundError
        if file cannot be found
    """
    full_filename = os.path.abspath(filename)
    assert os.path.exists(full_filename)
    with open(full_filename, "r") as fp:
        buf = fp.readlines()

    commands = []
    for i, raw_command in enumerate(buf):
        row = raw_command.strip()
        if row == "" or row.startswith("#"):
            continue                    # comment or blank

        else:                           # command line
            action, *values = split_quoted_line(row)
            commands.append((action, values, i+1, raw_command.rstrip()))

    return commands


def command_list_as_table(commands):
    """Format a command list as a :class:`pyRestTable.Table()` object."""
    tbl = pyRestTable.Table()
    tbl.addLabel("line #")
    tbl.addLabel("action")
    tbl.addLabel("parameters")
    for command in commands:
        action, args, line_number = command[:3]
        row = [line_number, action, ", ".join(map(str, args))]
        tbl.addRow(row)
    return tbl


def get_command_list(filename):
    """Return command list from either text or Excel file."""
    full_filename = os.path.abspath(filename)
    assert os.path.exists(full_filename)
    try:
        commands = parse_Excel_command_file(filename)
    except Exception:          # TODO: XLRDError
        commands = parse_text_command_file(filename)
    return commands


def summarize_command_file(filename):
    """Print the command list from a text or Excel file."""
    commands = get_command_list(filename)
    logger.info(
        "Command file: %s\n%s",
        command_list_as_table(commands), filename
    )


def run_command_file(filename, md=None):
    """
    Plan: execute a list of commands from a text or Excel file.

    * Parse the file into a command list
    * yield the command list to the RunEngine (or other)
    """
    if md is None:
        md = {}
    commands = get_command_list(filename)
    yield from execute_command_list(filename, commands)


def execute_command_list(filename, commands, md=None):
    """
    Plan: execute the command list.

    The command list is a tuple described below.

    * Only recognized commands will be executed.
    * Unrecognized commands will be reported as comments.

    PARAMETERS

    filename : str
        Name of input text file.  Can be relative or absolute path,
        such as "actions.txt", "../sample.txt", or
        "/path/to/overnight.txt".
    commands : list[command]
        List of command tuples for use in ``execute_command_list()``

    where

    command : tuple
        (action, OrderedDict, line_number, raw_command)
    action: str
        names a known action to be handled
    parameters: list
        List of parameters for the action.
        The list is empty of there are no values
    line_number: int
        line number (1-based) from the input text file
    raw_command: obj (str or list(str)
        contents from input file, such as:
        ``SAXS 0 0 0 blank``
    """
    from .scans import preUSAXStune, SAXS, USAXSscan, WAXS

    if md is None:
        md = {}

    full_filename = os.path.abspath(filename)

    if len(commands) == 0:
        yield from bps.null()
        return

    text = f"Command file: {filename}\n"
    text += str(command_list_as_table(commands))
    logger.info(text)
    logger.info("memory report: %s", rss_mem())

    # save the command list as a separate Bluesky run for documentation purposes
    yield from documentation_run(text)

    instrument_archive(text)

    yield from before_command_list(md=md, commands=commands)
    for command in commands:
        action, args, i, raw_command = command
        logger.info("file line %d: %s", i, raw_command)

        _md = {}
        _md["full_filename"] = full_filename
        _md["filename"] = filename
        _md["line_number"] = i
        _md["action"] = action
        _md["parameters"] = args    # args is shorter than parameters, means the same thing here
        _md["iso8601"] = datetime.datetime.now().isoformat(" ")

        _md.update(md or {})      # overlay with user-supplied metadata

        simple_actions = dict(
            # command names MUST be lower case!
            # TODO: all these should accept a `md` kwarg
            mode_blackfly = mode_BlackFly,
            mode_radiography = mode_Radiography,
            mode_saxs = mode_SAXS,
            mode_usaxs = mode_USAXS,
            mode_waxs = mode_WAXS,
            pi_off = PI_Off,
            pi_onf = PI_onF,
            pi_onr = PI_onR,
            preusaxstune = preUSAXStune,
        )

        action = action.lower()
        if action in ("flyscan", "usaxsscan"):
            sx = float(args[0])
            sy = float(args[1])
            sth = float(args[2])
            snm = args[3]
            _md.update(dict(sx=sx, sy=sy, thickness=sth, title=snm))
            yield from USAXSscan(sx, sy, sth, snm, md=_md)  # either step or fly scan

        elif action in ("saxs", "saxsexp"):
            sx = float(args[0])
            sy = float(args[1])
            sth = float(args[2])
            snm = args[3]
            _md.update(dict(sx=sx, sy=sy, thickness=sth, title=snm))
            yield from SAXS(sx, sy, sth, snm, md=_md)

        elif action in ("waxs", "waxsexp"):
            sx = float(args[0])
            sy = float(args[1])
            sth = float(args[2])
            snm = args[3]
            _md.update(dict(sx=sx, sy=sy, thickness=sth, title=snm))
            yield from WAXS(sx, sy, sth, snm, md=_md)

        elif action in ("run_python", "run"):
            filename = float(args[0])
            yield from run_python_file(filename, md={})

        elif action in simple_actions:
            yield from simple_actions[action](md=_md)

        else:
            logger.info("no handling for line %d: %s", i, raw_command)
        logger.info("memory report: %s", rss_mem())

    yield from after_command_list(md=md)
    logger.info("memory report: %s", rss_mem())


def sync_order_numbers():
    """
    Synchronize the order numbers between the various detectors.

    Pick the maximum order number from each detector (or
    supported scan technique) and set them all to that number.
    """
    order_number = max(
        terms.FlyScan.order_number.get(),
        saxs_det.hdf1.file_number.get(),
        waxs_det.hdf1.file_number.get(),
    )
    logger.info("Synchronizing detector order numbers to %d", order_number)
    yield from bps.mv(
        terms.FlyScan.order_number, order_number,
        saxs_det.hdf1.file_number, order_number,
        waxs_det.hdf1.file_number, order_number,
    )


def run_python_file(filename, md=None):
    """
    Plan: load and run a Python file using the IPython `%mov` magic.

    * Parse the file into a command list
    * yield the command list to the RunEngine (or other)
    """
    if md is None:
        md = {}
    logger.info("Running Python file: %s", filename)
    get_ipython().run_line_magic("run", f"-i {filename}")
    yield from bps.null()

