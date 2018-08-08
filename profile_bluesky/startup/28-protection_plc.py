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
    
    @property
    def interlocked(self):
        return not 0 in (self.SAXS_Y.value, self.WAXS_X.value, self.AX.value)
    
    def wait_for_interlock(self, verbose=True):
        t0 = time.time()
        msg = "Waiting %g for PLC interlock, check limit switches"
        while not self.interlocked:
            time.sleep(self.SLEEP_POLL_s)
            if verbose:
                print(msg % time.time()-t0)
    
    def stop_if_tripped(self, verbose=True):   # TODO: should be a Bluesky suspender?
        if self.operations_status.value < 1:
            if verbose:
                print("Equipment protection is engaged, no power on motors.")
                print("Fix PLC protection before any move. Stopping now.")
                print("Call beamline scientists if you do not understand.")
                print("!!!!!!  DO NOT TRY TO FIX YOURSELF  !!!!!!")
            ti_filter_shutter.close()
            user_data.collection_in_progress.put(0)     # notify the GUI and others


plc_protect = PlcProtectionDevice('9idcLAX:plc:', name='plc_protect')

