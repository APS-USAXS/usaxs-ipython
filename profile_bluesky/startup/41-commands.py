print(__file__)

"""USAXS commands"""

USAXSSAXSMODE = EpicsSignal("9idcLAX:USAXS_Pin:USAXSSAXSMode", name="USAXSSAXSMODE")
        # values for USAXSSAXSMode:
        # -1  dirty, prior move did not finish correctly
        #  1  SAXS and USAXS out of beam
        #  2  USAXS in beam
        #  3  SAXS in beam
        #  4  WAXS in the beam
        #  5  Imaging in
        #  6  Imaging tuning mode. 


PauseBeforeNextScan = EpicsSignal("9idcLAX:USAXS:PauseBeforeNextScan", name="PauseBeforeNextScan")
StopBeforeNextScan = EpicsSignal("9idcLAX:USAXS:StopBeforeNextScan", name="StopBeforeNextScan")
EmergencyProtectionOn = EpicsSignal("9idcLAX:plc:Y0", name="EmergencyProtectionOn")

# dataCollectionInProgress: for GUI (and other tools) to know that user is collecting data
# (1-not running, 0 running)
dataColInProgress = EpicsSignal("9idcLAX:dataColInProgress", name="dataColInProgress")


def StopIfPLCEmergencyProtectionOn():   # TODO: should be a Bluesky suspender?
    if EmegencyProtectionOn < 1:
        print("Equipment protection is engaged, no power on motors.")
        print("Fix PLC protection before any move. Stopping now.")
        print("Call bealine scientists if you do not understand. DO NOT TRY TO FIX YOURSELF  !!!!!!")
        ti_filter_shutter.close()
        dataColInProgress.put(0)


def IfRequestedStopBeforeNextScan():
    open_the_shutter = False
    t0 = time.time()
    elapsed_time = time.time() - t0

    txt = "User requested pause, sleeping and waiting for change in Pause PV for %g s\r"
    pv_txt = "Pausing for user for %g s"
    while PauseBeforeNextScan.value > 0.5:
        print(txt % elapsed_time)
        user_data.state.put(pv_txt % elapsed_time))
        time.sleep(1)
        elapsed_time = time.time() - t0
        open_the_shutter = True

    txt = "User requested pause, sleeping and waiting for change in Pause PV for %g s\r"
    if StopBeforeNextScan.value:
        print("User requested stop before next scan, stopping data collection")
        ti_filter_shutter.close()
        StopBeforeNextScan.put(0)
        dataColInProgress.put(0)
        open_the_shutter = False

    if open_the_shutter:
        mono_shutter.open()
        # time.sleep(2)       # not needed since mono_shutter.open() waits until complete
