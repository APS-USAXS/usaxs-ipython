
"""
control the monochromator feedback
"""

__all__ = ["DCMfeedbackON",]

from ..session_logs import logger
logger.info(__file__)

from bluesky import plan_stubs as bps

from ..devices.monochromator import monochromator, MONO_FEEDBACK_ON

def DCMfeedbackON():
    """plan: could send email"""
    yield from bps.mv(monochromator.feedback.on, MONO_FEEDBACK_ON)
    monochromator.feedback.check_position()
