print(__file__)

"""
USAXS Fly Scan setup
"""

import enum
import uuid
from usaxs_support.saveFlyData import SaveFlyScan
logger = logging.getLogger(os.path.split(__file__)[-1])


"""
sfs = SaveFlyScan("/tmp/sfs.h5", config_file="usaxs_support/saveFlyData.xml")
sfs.preliminaryWriteFile()
sfs.saveFile()
"""

class BusyStatus(str, enum.Enum):
    busy = "Busy"
    done = "Done"


class UsaxsFlyScanDevice(Device):
    busy = Component(EpicsSignal, '9idcLAX:USAXSfly:Start', string=True, put_complete=True)
    scan_time = Component(EpicsSignal, "9idcLAX:USAXS:FS_ScanTime")
    num_points = Component(EpicsSignal, "9idcLAX:USAXS:FS_NumberOfPoints")
    flying = Component(Signal, value=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t0 = None
        self.update_time = None
        self.update_interval_s = 5
        self.ar0 = None
        self.ay0 = None
        self.dy0 = None
        self.saveFlyData = None
    
    def plan(self):

        def report(t):
            msg = "%.02fs - flying " % t
            msg += "  ar = %.5f" % a_stage.r.position
            msg += "  ay = %.5f" % a_stage.y.position
            msg += "  dy = %.5f" % d_stage.y.position
            # msg += "  flying = {}".format(self.flying.value)
            return msg

        def waiter():
            logger.debug("waiter has arrived")
            t = time.time()
            timeout = t + self.scan_time.value + 20 # extra padded time
            startup = t + self.update_interval_s/2
            while t < startup and not  self.flying.value:    # wait for flyscan to start
                time.sleep(0.01)
            while t < timeout and self.flying.value:
                if t > self.update_time:
                    self.update_time = t + self.update_interval_s
                    msg = report(t - self.t0)
                    print(msg)
                    logger.debug(msg)
                time.sleep(0.01)
                t = time.time()
            if t > timeout:
                logger.error("{}s - waiter timeout!!".format(time.time()-self.t0))
            else:
                logger.debug("{}s - waiter is done".format(time.time()-self.t0))
            msg = report(time.time() - self.t0)
            print(msg)
            logger.debug(msg)

        self.ar0 = a_stage.r.position
        self.ay0 = a_stage.y.position
        self.dy0 = d_stage.y.position

        self.t0 = time.time()
        g = uuid.uuid4()
        self.update_time = self.t0 + self.update_interval_s
        self.flying.put(False)
        
        # TODO: launch this in a thread
        # TODO: sfs = SaveFlyScan(?filename?, config_file="usaxs_support/saveFlyData.xml")
        # TODO: sfs.preliminaryWriteFile()


        yield from bps.abs_set(self.busy, BusyStatus.busy, group=g) # waits until done
        thread = threading.Thread(target=waiter, daemon=True)
        thread.start()
        self.flying.put(True)

        yield from bps.wait(group=g)
        self.flying.put(False)
        
        # TODO: launch this in a thread
        # TODO: sfs.saveFile()

        yield from bps.mv(
            a_stage.r.user_setpoint, self.ar0, 
            a_stage.y.user_setpoint, self.ay0, 
            d_stage.y.user_setpoint, self.dy0)
        logger.debug("after return", time.time() - self.t0)


# #21 : w-i-p
usaxs_flyscan = UsaxsFlyScanDevice(name="usaxs_flyscan")


def fix_faulty():
    a_stage.r.user_setpoint.set(8.7628359)
    a_stage.y.user_setpoint.set(0)
    d_stage.y.user_setpoint.set(13.2833635)


# RE(usaxs_flyscan.flyscan_plan())
