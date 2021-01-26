
"""
Turn off dynamic time in uascan.

%run -i user/uascan_dynamic_time_off.py
"""

from instrument.session_logs import logger
logger.info(__file__)

from instrument.devices import terms


terms.USAXS.useDynamicTime.put(False)
logger.info(
    "terms.USAXS.useDynamicTime = %s",
    terms.USAXS.useDynamicTime.get()
)
