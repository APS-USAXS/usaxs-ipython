
"""
Linkam temperature controllers
"""

__all__ = [
    'linkam_ci94',
    'linkam_tc1',
    ]

from ..session_logs import logger
logger.info(__file__)

from apstools.devices import ProcessController
from bluesky import plan_stubs as bps
from ophyd import Component, Device, DeviceStatus
from ophyd import EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV, Signal
import time

from ..framework import specwriter


class UsaxsProcessController(ProcessController):
    """
    temporary override

    see https://github.com/APS-USAXS/ipython-usaxs/issues/292
    """

    # override in subclass with EpicsSignal as appropriate
    rate = Component(Signal, kind="omitted")     # temperature change per minute
    speed = Component(Signal, kind="omitted")    # rotational speed (RPM) of pump

    @property
    def settled(self):
        """Is signal close enough to target?"""
        diff = abs(self.signal.get() - self.target.get())
        return diff <= self.tolerance.get()

    def wait_until_settled(self, timeout=None, timeout_fail=False):
        """
        plan: wait for controller signal to reach target within tolerance
        """
        # see: https://stackoverflow.com/questions/2829329/catch-a-threads-exception-in-the-caller-thread-in-python
        t0 = time.time()
        _st = DeviceStatus(self.signal)

        if self.settled:
            # just in case signal already at target
            _st._finished(success=True)
        else:
            started = False

            def changing_cb(*args, **kwargs):
                if started and self.settled:
                    _st._finished(success=True)

            token = self.signal.subscribe(changing_cb)
            started = True
            report = 0
            while not _st.done and not self.settled:
                elapsed = time.time() - t0
                if timeout is not None and elapsed > timeout:
                    _st._finished(success=self.settled)
                    msg = f"{self.controller_name} Timeout after {elapsed:.2f}s"
                    msg += f", target {self.target.get():.2f}{self.units.get()}"
                    msg += f", now {self.signal.get():.2f}{self.units.get()}"
                    print(msg)
                    if timeout_fail:
                        raise TimeoutError(msg)
                    continue
                if elapsed >= report:
                    report += self.report_interval_s
                    msg = f"Waiting {elapsed:.1f}s"
                    msg += f" to reach {self.target.get():.2f}{self.units.get()}"
                    msg += f", now {self.signal.get():.2f}{self.units.get()}"
                    print(msg)
                yield from bps.sleep(self.poll_s)

            self.signal.unsubscribe(token)

        self.record_signal()
        elapsed = time.time() - t0
        print(f"Total time: {elapsed:.3f}s, settled:{_st.success}")


class Linkam_CI94(UsaxsProcessController):
    """
    Linkam model CI94 temperature controller

    EXAMPLE::

        In [1]: linkam_ci94 = Linkam_CI94("9idcLAX:ci94:", name="ci94")

        In [2]: linkam_ci94.settled
        Out[2]: False

        In [3]: linkam_ci94.settled
        Out[3]: True

        linkam_ci94.record_signal()
        yield from (linkam_ci94.set_target(50))

    """
    controller_name = "Linkam CI94"
    signal = Component(EpicsSignalRO, "temp")
    target = Component(EpicsSignal, "setLimit", kind="omitted")
    units = Component(Signal, kind="omitted", value="C")

    temperature_in = Component(EpicsSignalRO, "tempIn", kind="omitted")
    # DO NOT USE: temperature2_in = Component(EpicsSignalRO, "temp2In", kind="omitted")
    # DO NOT USE: temperature2 = Component(EpicsSignalRO, "temp2")
    pump_speed = Component(EpicsSignalRO, "pumpSpeed", kind="omitted")

    rate = Component(EpicsSignal, "setRate", kind="omitted")    # RPM
    speed = Component(EpicsSignal, "setSpeed", kind="omitted")  # deg/min, speed 0 = automatic control
    end_after_profile = Component(EpicsSignal, "endAfterProfile", kind="omitted")
    end_on_stop = Component(EpicsSignal, "endOnStop", kind="omitted")
    start_control = Component(EpicsSignal, "start", kind="omitted")
    stop_control = Component(EpicsSignal, "stop", kind="omitted")
    hold_control = Component(EpicsSignal, "hold", kind="omitted")
    pump_mode = Component(EpicsSignal, "pumpMode", kind="omitted")

    error_byte = Component(EpicsSignalRO, "errorByte", kind="omitted")
    status = Component(EpicsSignalRO, "status", kind="omitted")
    status_in = Component(EpicsSignalRO, "statusIn", kind="omitted")
    gen_stat = Component(EpicsSignalRO, "genStat", kind="omitted")
    pump_speed_in = Component(EpicsSignalRO, "pumpSpeedIn", kind="omitted")
    dsc_in = Component(EpicsSignalRO, "dscIn", kind="omitted")

    # clear_buffer = Component(EpicsSignal, "clearBuffer", kind="omitted")          # bo
    # scan_dis = Component(EpicsSignal, "scanDis", kind="omitted")                  # bo
    # test = Component(EpicsSignal, "test", kind="omitted")                         # longout
    # d_cmd = Component(EpicsSignalRO, "DCmd", kind="omitted")                      # ai
    # t_cmd = Component(EpicsSignalRO, "TCmd", kind="omitted")                      # ai
    # dsc = Component(EpicsSignalRO, "dsc", kind="omitted")                         # calc

    def record_signal(self):
        """write signal to the logger AND SPEC file"""
        global specwriter
        msg = f"{self.controller_name} signal: {self.get():.2f}{self.units.get()}"
        logger.info(msg)
        specwriter._cmt("event", msg)
        return msg


class Linkam_T96(UsaxsProcessController):
    """
    Linkam model T96 temperature controller

    EXAMPLE::

        linkam_tc1 = Linkam_T96("9idcLINKAM:tc1:", name="linkam_tc1")

    """
    controller_name = "Linkam T96"
    signal = Component(EpicsSignalRO, "temperature_RBV")  # ai
    target = Component(EpicsSignalWithRBV, "rampLimit", kind="omitted")
    units = Component(Signal, kind="omitted", value="C")

    vacuum = Component(EpicsSignal, "vacuum", kind="omitted")

    heating = Component(EpicsSignalWithRBV, "heating", kind="omitted")
    lnp_mode = Component(EpicsSignalWithRBV, "lnpMode", kind="omitted")
    lnp_speed = Component(EpicsSignalWithRBV, "lnpSpeed", kind="omitted")
    rate = Component(EpicsSignalWithRBV, "rampRate", kind="omitted")
    vacuum_limit_readback = Component(EpicsSignalWithRBV, "vacuumLimit", kind="omitted")

    controller_config = Component(EpicsSignalRO, "controllerConfig_RBV", kind="omitted")
    controller_error = Component(EpicsSignalRO, "controllerError_RBV", kind="omitted")
    controller_status = Component(EpicsSignalRO, "controllerStatus_RBV", kind="omitted")
    heater_power = Component(EpicsSignalRO, "heaterPower_RBV", kind="omitted")
    lnp_status = Component(EpicsSignalRO, "lnpStatus_RBV", kind="omitted")
    pressure = Component(EpicsSignalRO, "pressure_RBV", kind="omitted")
    ramp_at_limit = Component(EpicsSignalRO, "rampAtLimit_RBV", kind="omitted")
    stage_config = Component(EpicsSignalRO, "stageConfig_RBV", kind="omitted")
    status_error = Component(EpicsSignalRO, "statusError_RBV", kind="omitted")
    vacuum_at_limit = Component(EpicsSignalRO, "vacuumAtLimit_RBV", kind="omitted")
    vacuum_status = Component(EpicsSignalRO, "vacuumStatus_RBV", kind="omitted")

    def record_signal(self):
        """write signal to the logger AND SPEC file"""
        global specwriter
        msg = (
            f"{self.controller_name} signal:"
            f" {self.value:.2f}{self.units.get()}"
        )
        logger.info(msg)
        specwriter._cmt("event", msg)
        return msg

    def set_target(self, target, wait=True, timeout=None, timeout_fail=False):
        """change controller to new temperature set point"""
        global specwriter

        yield from bps.mv(self.target, target)
        yield from bps.sleep(0.1)   # settling delay for slow IOC
        yield from bps.mv(self.heating, 1)

        msg = f"Set {self.controller_name} to {self.target.setpoint:.2f}{self.units.get()}"
        specwriter._cmt("event", msg)
        logger.info(msg)

        if wait:
            yield from self.wait_until_settled(
                timeout=timeout,
                timeout_fail=timeout_fail)

    # @property
    # def settled(self):
    #     """Is signal close enough to target?"""
    #     print(f"{self.get()} C, in position? {self.ramp_at_limit.get()}")
    #     return self.ramp_at_limit.get() in (True, 1, "Yes")


linkam_ci94 = Linkam_CI94("9idcLAX:ci94:", name="ci94")
linkam_tc1 = Linkam_T96("9idcLINKAM:tc1:", name="linkam_tc1")
