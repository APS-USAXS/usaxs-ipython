print(__file__)

"""detector protection PLC"""


class PlcProtectionDevice(Device):
    """
    Detector Protection PLC interface
    
    motion limit switches: 
    * SAXS_Y, WAXS_X, AX
    * zero when OFF
    * two limits must be ON to allow safe move of the third
    """
    SAXS_Y = Component(EpicsSignal, 'X11')
    WAXS_X = Component(EpicsSignal, 'X12')
    AX = Component(EpicsSignal, 'X13')
    
    operations_status = Component(EpicsSignal, 'Y0')     # 0=not good, 1=good
    
    SLEEP_POLL_s = 0.1
    _tripped_message = None
    
    @property
    def interlocked(self):
        return not 0 in (self.SAXS_Y.value, self.WAXS_X.value, self.AX.value)
    
    def wait_for_interlock(self, verbose=True):
        t0 = time.time()
        msg = "Waiting %g for PLC interlock, check limit switches"
        while not self.interlocked:
            yield from bps.sleep(self.SLEEP_POLL_s)
            if verbose:
                print(msg % time.time()-t0)
        yield from bps.null()   # always yield at least one Msg
    
    def stop_if_tripped(self, verbose=True):
        if self.operations_status.value == 1:
            self._tripped_message = None
        else:
            msg = """
            Equipment protection is engaged, no power on motors.
            Fix PLC protection before any move. Stopping now.
            Call beamline scientists if you do not understand.
            
            !!!!!!  DO NOT TRY TO FIX THIS YOURSELF  !!!!!!
            
            """
            if verbose:
                print(msg)
            yield from bps.mv(
                ti_filter_shutter, "close",
                user_data.collection_in_progress, 0,     # notify the GUI and others
            )
            # send email to staff ASAP!!!
            msg +="\n P.S. Can resume Bluesky scan: {}\n".format(
                suspend_plc_protect.allow_resume)
            self._tripped_message = msg
            email_notices.send("!!! PLC protection Y0 tripped !!!", msg)


class PlcProtectSuspendWhenChanged(APS_suspenders.SuspendWhenChanged):
    
    def _get_justification(self):
        """override default method to call plc_protect.stop_if_tripped()"""
        if not self.tripped:
            return ''

        just = 'Signal {}, got "{}", expected "{}"'.format(
            self._sig.name,
            self._sig.get(),
            self.expected_value)
        if not self.allow_resume:
            just += '.  '
            just += '"RE.abort()" to finalize current data streams (if any)'
            just += ' and then restart bluesky session to clear this.'
            just += "\n"
            just += "\n Equipment protection is engaged, no power on motors."
            just += "\n Fix PLC protection before any move. Stopping now."
            just += "\n Call beamline scientists if you do not understand."
            just += "\n !!!!!!  DO NOT TRY TO FIX YOURSELF  !!!!!!\n"

        plc_protect.stop_if_tripped()       # TODO: test this

        return ': '.join(s for s in (just, self._tripped_message)
                         if s)


plc_protect = PlcProtectionDevice('9idcLAX:plc:', name='plc_protect')

suspend_plc_protect = PlcProtectSuspendWhenChanged(
    plc_protect.operations_status, 
    expected_value=1)
# this will suspend whenever PLC Y0 = 0 -- we want that
RE.install_suspender(suspend_plc_protect)

