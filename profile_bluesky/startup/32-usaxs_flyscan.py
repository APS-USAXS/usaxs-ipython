print(__file__)

"""
USAXS Fly Scan setup
"""

logger = logging.getLogger(os.path.split(__file__)[-1])

# from usaxs_support.saveFlyData import SaveFlyScan


class UsaxsFlyScanDevice(Device, ApsBusyFlyScanDeviceMixin):
    busy = Component(BusyRecord, '9idcLAX:USAXSfly:Start')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ApsBusyFlyScanDeviceMixin().__init__()
        self.t0 = None
        self.update_time = None
        self.update_interval_s = 5
        self.ar0 = None
        self.ay0 = None
        self.dy0 = None

    def hook_flyscan_plan(self):
        pass

    def hook_pre_flyscan_plan(self):
        """
        Customize: called before the fly scan
        """
        logger.debug("hook_pre_flyscan() : no-op default")
        self.t0 = time.time()
        self.update_time = self.t0 + self.update_interval_s
        self.ar0 = a_stage.r.position
        self.ay0 = a_stage.y.position
        self.dy0 = d_stage.y.position

    def hook_flyscan_wait_scanning(self):
        """
        Customize: called from ``flyscan_wait(True)``
        """
        # logger.debug("hook_flyscan_wait_scanning() : no-op default")
        t = time.time()
        if t > self.update_time:
            self.update_time = t + self.update_interval_s
            msg = "flying %.2f s" % (t - self.t0)
            msg += "  ar = %.5f" % a_stage.r.position
            msg += "  ay = %.5f" % a_stage.y.position
            msg += "  dy = %.5f" % d_stage.y.position
            print(msg)

    def hook_post_flyscan_plan(self):
        """
        Customize: called after the fly scan
        """
        print("return ar, ay, dy to original positions")
        
        a_stage.r.user_setpoint.set(self.ar0)
        a_stage.y.user_setpoint.set(self.ay0)
        d_stage.y.user_setpoint.set(self.dy0)
        
        # FIXME: these cause this entire method to not be run - what gives?
        # bps.mv(a_stage.r.user_setpoint, self.ar0)
        # yield from bps.abs_set(a_stage.y.user_setpoint, self.ay0, group="reset")
        # yield from bps.abs_set(d_stage.y.user_setpoint, self.dy0, group="reset")
        # yield from bps.wait(group="reset")

        # yield from bps.mv(
        #     a_stage.r.user_setpoint, self.ar0, 
        #     a_stage.y.user_setpoint, self.ay0, 
        #     d_stage.y.user_setpoint, self.dy0)

        print("Fly scan complete, normally, would save data at this time")

        t = time.time()
        msg = "fly scan finished in {} s".format(t - self.t0)
        print(msg)


usaxs_flyscan = UsaxsFlyScanDevice(name="usaxs_flyscan")


def fix_faulty():
    # a_stage.r.move(8.761986)
    # a_stage.y.move(0)
    # d_stage.y.move(13.35)
    
    a_stage.r.user_setpoint.set(8.761986)
    a_stage.y.user_setpoint.set(0)
    d_stage.y.user_setpoint.set(13.35)


# RE(usaxs_flyscan.flyscan_plan())
