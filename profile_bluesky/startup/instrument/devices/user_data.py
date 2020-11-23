
"""
EPICS data about the user
"""

__all__ = [
    'apsbss',
    'bss_user_info',
    'user_data',
    ]

from ..session_logs import logger
logger.info(__file__)

from bluesky import plan_stubs as bps
from apstools.devices import ApsBssUserInfoDevice
from apstools.beamtime.apsbss_ophyd import EpicsBssDevice
from apstools.utils import trim_string_for_EPICS
from ophyd import Component, Device, EpicsSignal

from ..framework import sd




class EpicsSampleNameDevice(EpicsSignal):
    """
    Enable the user to supply a function that modifies
    the sample name during execution of a plan.

    see: https://github.com/APS-USAXS/ipython-usaxs/issues/428

    EXAMPLE:

        >>> def handler(title):
        ...     return f"USAXS sample: {title}"

        >>> user_data.sample_title.register_handler(handler)

        >>> RE(bps.mv(user_data.sample_title, "Glassy Carbon"))
        >>> user_data.sample_title.get()
        USAXS sample: Glassy Carbon

    """

    _handler = None

    def set(self, value, **kwargs):
        """Modify value per user function before setting the PV"""
        logger.info("self._handler: %s", self._handler)
        if self._handler is not None:
            value = self._handler(value)
        return super().set(value, **kwargs)

    def register_handler(self, handler_function=None):
        """
        Register the supplied function to be called
        when this signal is to be written.  The function
        accepts the default sample title as the only argument
        and *must* return a string value (as shown in the
        example above).
        """
        if handler_function is None:
            # clear the handler
            self._handler = None
        else:
            # Test the proposed handler before accepting it.
            # Next call will raise exception if user code has an error.
            test = handler_function("test")

            # User function must return a str result.
            if not isinstance(test, str):
                raise ValueError(
                    f"Sample name function '{handler_function.__name__}'"
                    "must return 'string' type,"
                    f" received {type(test).__name__}"
                )

            logger.debug(
                "Accepted Sample name handler function: %s",
                handler_function.__name__
            )
            self._handler = handler_function


class UserDataDevice(Device):
    GUP_number = Component(EpicsSignal,         "9idcLAX:GUPNumber")
    macro_file = Component(EpicsSignal,         "9idcLAX:USAXS:macroFile")
    macro_file_time = Component(EpicsSignal,    "9idcLAX:USAXS:macroFileTime")
    run_cycle = Component(EpicsSignal,          "9idcLAX:RunCycle")
    sample_thickness = Component(EpicsSignal,   "9idcLAX:sampleThickness")
    sample_title = Component(EpicsSampleNameDevice, "9idcLAX:sampleTitle", string=True)
    scanning = Component(EpicsSignal,           "9idcLAX:USAXS:scanning")
    scan_macro = Component(EpicsSignal,         "9idcLAX:USAXS:scanMacro")
    spec_file = Component(EpicsSignal,          "9idcLAX:USAXS:specFile", string=True)
    spec_scan = Component(EpicsSignal,          "9idcLAX:USAXS:specScan", string=True)
    state = Component(EpicsSignal,              "9idcLAX:state", string=True, write_timeout=0.1)
    time_stamp = Component(EpicsSignal,         "9idcLAX:USAXS:timeStamp")
    user_dir = Component(EpicsSignal,           "9idcLAX:userDir", string=True)
    user_name = Component(EpicsSignal,          "9idcLAX:userName", string=True)

    # for GUI to know if user is collecting data: 0="On", 1="Off"
    collection_in_progress = Component(EpicsSignal, "9idcLAX:dataColInProgress")

    def set_state_plan(self, msg, confirm=True):
        """plan: tell EPICS about what we are doing"""
        msg = trim_string_for_EPICS(msg)
        yield from bps.abs_set(self.state, msg, wait=confirm)

    def set_state_blocking(self, msg):
        """ophyd: tell EPICS about what we are doing"""
        msg = trim_string_for_EPICS(msg)
        try:
            if len(msg) > 39:
                logger.info("truncating long status message: %s", msg)
                msg = msg[:35] + " ..."
            self.state.put(msg)
        except Exception as exc:
            logger.error(
                "Could not put message (%s) to USAXS state PV: %s",
                msg,
                exc)


class CustomEpicsBssDevice(EpicsBssDevice):

    def update_MD(self, md=None):
        """
        add select Proposal and ESAF terms to given metadata dictionary
        """
        _md = md or {}
        _md.update(
            dict(
                bss_aps_cycle=apsbss.esaf.aps_cycle.get(),
                bss_beamline_name=apsbss.proposal.beamline_name.get(),
                esaf_id=apsbss.esaf.esaf_id.get(),
                esaf_title=apsbss.esaf.title.get(),
                mail_in_flag=apsbss.proposal.mail_in_flag.get(),
                principal_user=apsbss.get_PI() or "not identified",
                proposal_id=apsbss.proposal.proposal_id.get(),
                proposal_title=apsbss.proposal.title.get(),
                proprietary_flag=apsbss.proposal.proprietary_flag.get(),
            )
        )
        return _md

    def get_PI(self):
        """return last name of principal investigator or 1st user"""
        if self.proposal.number_users_in_pvs.get() == 0:
            return "no users listed"
        else:
            for i in range(9):
                user = getattr(self.proposal, f"user{i+1}")
                if user.pi_flag.get() in ('ON', 1):
                    return user.last_name.get()


bss_user_info = ApsBssUserInfoDevice(
    "9id_bss:", name="bss_user_info")
# sd.baseline.append(bss_user_info)

# eventually, apsbss will replace bss_user_info
apsbss = CustomEpicsBssDevice("9idc:bss:", name="apsbss")
sd.baseline.append(apsbss.proposal.raw)
sd.baseline.append(apsbss.esaf.raw)

user_data = UserDataDevice(name="user_data")
sd.baseline.append(user_data)
