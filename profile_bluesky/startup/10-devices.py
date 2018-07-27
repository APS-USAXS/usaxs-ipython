print(__file__)

"""Set up custom or complex devices"""


def run_in_thread(func):
    """run ``func`` in thread"""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


class TunableEpicsMotor(EpicsMotor, AxisTunerMixin):
    pass


class MyApsPssShutterWithStatus(ApsPssShutterWithStatus):
    # our shutters use upper case for Open & Close
    open_bit = Component(EpicsSignal, "Open")
    close_bit = Component(EpicsSignal, "Close")


class BusyStatus(str, Enum):
    busy = "Busy"
    done = "Done"


class BusyRecord(Device):
    """a busy record sets the fly scan into action"""
    state = Component(EpicsSignal, "")
    output_link = Component(EpicsSignal, ".OUT")
    forward_link = Component(EpicsSignal, ".FLNK")


class MyCalc(Device):
    """swait record simulates a signal"""
    result = Component(EpicsSignal, "")
    calc = Component(EpicsSignal, ".CALC")
    proc = Component(EpicsSignal, ".PROC")


class MyWaveform(Device):
    """waveform records store fly scan data"""
    wave = Component(EpicsSignalRO, "")
    number_elements = Component(EpicsSignalRO, ".NELM")
    number_read = Component(EpicsSignalRO, ".NORD")


class InOutShutter(Device):
    """
    In/Out shutter
    
    * In/Out shutters have the same bit PV for open and close
    
    Otherwise, they should have the same interface as other 
    shutters such as the `ApsPssShutter`.
    
    USAGE:
    
        shutter = InOutShutter("48bmc:bit12", name="shutter")
    
    """
    control_bit = Component(EpicsSignal, "")
    delay_s = 0
    open_value = 1
    close_value = 0
    valid_open_values = [open_value, "open"]   # lower-case strings ONLY
    valid_close_values = [close_value, "close"]
    busy = Signal(value=False, name="busy")
    
    def open(self):
        """request shutter to open, interactive use"""
        return self.set(self.open_value)
    
    def close(self):
        """request shutter to close, interactive use"""
        return self.set(self.close_value)
    
    def set(self, value, **kwargs):
        """request the shutter to open or close, BlueSky plan use"""
        # ensure numerical additions to lists are now strings
        def input_filter(v):
            return str(v).lower()
        self.valid_open_values = list(map(input_filter, self.valid_open_values))
        self.valid_close_values = list(map(input_filter, self.valid_close_values))
        
        if self.busy.value:
            raise RuntimeError("shutter is operating")

        acceptables = self.valid_open_values + self.valid_close_values
        if input_filter(value) not in acceptables:
            msg = "value should be one of " + " | ".join(acceptables)
            msg += " : received " + str(value)
            raise ValueError(msg)
        
        status = DeviceStatus(self)
        
        def move_shutter():
            if input_filter(value) in self.valid_open_values:
                self.control_bit.put(self.open_value)     # no need to yield inside a thread
            elif input_filter(value) in self.valid_close_values:
                self.control_bit.put(self.close_value)     # no need to yield inside a thread
        
        @run_in_thread
        def run_and_delay():
            self.busy.put(True)
            move_shutter()
            # sleep, since we don't *know* when the shutter has moved
            time.sleep(self.delay_s)
            self.busy.put(False)
            status._finished(success=True)
        
        run_and_delay()
        return status

    
class DualPf4FilterBox(Device):
    """Dual Xia PF4 filter boxes using support from synApps"""
    fPosA = Component(EpicsSignal, "fPosA")
    fPosB = Component(EpicsSignal, "fPosB")
    bankA = Component(EpicsSignalRO, "bankA")
    bankB = Component(EpicsSignalRO, "bankB")
    bitFlagA = Component(EpicsSignalRO, "bitFlagA")
    bitFlagB = Component(EpicsSignalRO, "bitFlagB")
    transmission = Component(EpicsSignalRO, "trans")
    transmission_a = Component(EpicsSignalRO, "transA")
    transmission_b = Component(EpicsSignalRO, "transB")
    inverse_transmission = Component(EpicsSignalRO, "invTrans")
    thickness_Al_mm = Component(EpicsSignalRO, "filterAl")
    thickness_Ti_mm = Component(EpicsSignalRO, "filterTi")
    thickness_glass_mm = Component(EpicsSignalRO, "filterGlass")
    energy_keV_local = Component(EpicsSignal, "E:local")
    energy_keV_mono = Component(EpicsSignal, "displayEnergy")
    mode = Component(EpicsSignal, "useMono", string=True)


class Struck3820(Device):
    """Struck/SIS 3820 Multi-Channel Scaler (as used by USAXS)"""
    start_all = Component(EpicsSignal, "StartAll")
    stop_all = Component(EpicsSignal, "StopAll")
    erase_start = Component(EpicsSignal, "EraseStart")
    erase_all = Component(EpicsSignal, "EraseAll")
    mca1 = Component(EpicsMCARecord, "mca1")
    mca2 = Component(EpicsMCARecord, "mca2")
    mca3 = Component(EpicsMCARecord, "mca3")
    # mca1Name = Component(EpicsSignal, "scaler1.NM1", string=True)
    # mca2Name = Component(EpicsSignal, "scaler1.NM2", string=True)
    # mca3Name = Component(EpicsSignal, "scaler1.NM3", string=True)
    clock_frequency = Component(EpicsSignalRO, "clock_frequency")
    current_channel = Component(EpicsSignalRO, "CurrentChannel")
    channel_max = Component(EpicsSignalRO, "MaxChannels")
    channels_used = Component(EpicsSignal, "NuseAll")
    elapsed_real_time = Component(EpicsSignalRO, "ElapsedReal")
    preset_real_time = Component(EpicsSignal, "PresetReal")
    dwell_time = Component(EpicsSignal, "Dwell")
    prescale = Component(EpicsSignal, "Prescale")
    acquiring = Component(EpicsSignalRO, "Acquiring", string=True)
    acquire_mode = Component(EpicsSignalRO, "AcquireMode", string=True)
    model = Component(EpicsSignalRO, "Model", string=True)
    firmware = Component(EpicsSignalRO, "Firmware")
    channel_advance = Component(EpicsSignal, "ChannelAdvance")
    count_on_start = Component(EpicsSignal, "CountOnStart")
    channel_advance = Component(EpicsSignal, "SoftwareChannelAdvance")
    channel1_source = Component(EpicsSignal, "Channel1Source")
    user_led = Component(EpicsSignal, "UserLED")
    mux_output = Component(EpicsSignal, "MUXOutput")
    input_mode = Component(EpicsSignal, "InputMode")
    output_mode = Component(EpicsSignal, "OutputMode")
    output_polarity = Component(EpicsSignal, "OutputPolarity")
    read_rate = Component(EpicsSignal, "ReadAll.SCAN")
    do_readl_all = Component(EpicsSignal, "DoReadAll")


class DCM_Feedback(Device):
    """
    monochromator feedback program
    
    TODO: #49
    Add support for set() so that we can implement "on" & "off" values
    and also apply additional checks when turning feedback on.
    
    from SPEC code

        diff_hi = drvh - oval
        diff_lo = oval - drvl
        if diff<0.2 or diff_lo<0.2:
            if email_notices.notify_on_feedback:
                subject = "USAXS Feedback problem"
                message = "Feedback is very close to its limits."
                email_notices.send(subject, message)
        }

    """
    control = Component(EpicsSignal, "")
    on = Component(EpicsSignal, ":on")
    drvh = Component(EpicsSignal, ".DRVH")
    drvl = Component(EpicsSignal, ".DRVL")
    oval = Component(EpicsSignal, ".OVAL")
    
    @property
    def is_on(self):
        return self.on.value == 1


# TODO: #48 send email
class EmailNotifications(object):
    """
    send email notifications when requested
    
    use default OS mail utility (so no credentials needed)
    """
    
    def __init__(self):
        self.addresses = []
        self.notify_on_feedback = True
    
    def add_addresses(self, *args):
        for address in args:
            self.addresses.append(address)

    def send(self, subject, message):
        """send ``message`` to all addresses"""
        for address in self.addresses:
            command = """echo "{}" | mail -s "{}" {}""".format(
                message,
                subject,
                address
            )
            # TODO: unix(command)
