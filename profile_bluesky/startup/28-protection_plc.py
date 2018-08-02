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
    
    emergency_ON = Component(EpicsSignal, 'Y0')


plc_protect = PlcProtectionDevice('9idcLAX:plc:', name='plc_protect')


def __usaxs_wait_for_Interlock():
    """
    waits for the three stages to reach safe position
    
    original::
    
        def __usaxs_wait_for_Interlock'{
           # this function waits for the three 
           local Waiting_1234, Waiting_1235, Waiting_1236, __timer9876
           Waiting_1234 = epics_get("9idcLAX:plc:X13","short")
           Waiting_1235 = epics_get("9idcLAX:plc:X13","short")
           Waiting_1236 = epics_get("9idcLAX:plc:X13","short")
           __timer9876 = 1
            while (Waiting_1234==0 || Waiting_1235==0 || Waiting_1236==0) {
                sleep(0.1)
                Waiting_1234 = epics_get("9idcLAX:plc:X13","short")
                Waiting_1235 = epics_get("9idcLAX:plc:X13","short")
                Waiting_1236 = epics_get("9idcLAX:plc:X13","short")
                printf("Waiting for Interlock  %g sec, check limit switches\r", (__timer9876/10))
              __timer9876++
           }
        }'
    """
    t0 = time.time()
    while 0 in (plc_protect.SAXS_Y.value, plc_protect.WAXS_X.value, plc_protect.AX.value):
        sleep(0.1)
        printf("Waiting for Interlock  %g sec, check limit switches\r" % time.time()-t0)


def StopIfPLCEmergencyProtectionOn():   # TODO: should be a Bluesky suspender?
    if plc_protect.emergency_ON.value < 1:
        print("Equipment protection is engaged, no power on motors.")
        print("Fix PLC protection before any move. Stopping now.")
        print("Call bealine scientists if you do not understand. DO NOT TRY TO FIX YOURSELF  !!!!!!")
        ti_filter_shutter.close()
        user_data.collection_in_progress.put(0)     # notify the GUI and others
