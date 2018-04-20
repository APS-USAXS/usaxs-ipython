print(__file__)

"""
USAXS Fly Scan setup
"""

logger = logging.getLogger(os.path.split(__file__)[-1])



class UsaxsFlyScanDevice(Device, ApsBusyFlyScanDeviceMixin):
	busy = Component(BusyRecord, '9idcLAX:USAXSfly:Start')


usaxs_flyscan = UsaxsFlyScanDevice(name="usaxs_flyscan")


# RE(usaxs_flyscan.flyscan_plan())
