
"""
emails
"""

__all__ = [
    'email_notices',
    'NOTIFY_ON_RESET',
    'NOTIFY_ON_SCAN_DONE',
    'NOTIFY_ON_BEAM_LOSS',
    'NOTIFY_ON_BAD_FLY_SCAN',
    'NOTIFY_ON_FEEDBACK',
    'NOTIFY_ON_BADTUNE',
    ]

from ..session_logs import logger
logger.info(__file__)

from apstools.utils import EmailNotifications

# user will write code to check the corresponding symbol to send EmailNotifications
NOTIFY_ON_RESET = True
NOTIFY_ON_SCAN_DONE = False
NOTIFY_ON_BEAM_LOSS = True
NOTIFY_ON_BAD_FLY_SCAN = True
NOTIFY_ON_FEEDBACK = True
NOTIFY_ON_BADTUNE = True

email_notices = EmailNotifications("usaxs@aps.anl.gov")
email_notices.add_addresses(
    "ilavsky@aps.anl.gov",
    "kuzmenko@aps.anl.gov",
    "mfrith@anl.gov",
)
