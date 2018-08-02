print(__file__)

"""USAXS commands"""

### This file is work-in-progress

UsaxsSaxsMode = EpicsSignal("9idcLAX:USAXS_Pin:USAXSSAXSMode", name="UsaxsSaxsMode")
UsaxsSaxsMode_dict{
    "dirty": -1,        # prior move did not finish correctly
    "out of beam": 1,   # SAXS, WAXS, and USAXS out of beam
    "USAXS in beam": 2,
    "SAXS in beam": 3,
    "WAXS in beam": 4,
    "Imaging in": 5,
    "Imaging tuning": 6,
}


PauseBeforeNextScan = EpicsSignal("9idcLAX:USAXS:PauseBeforeNextScan", name="PauseBeforeNextScan")
StopBeforeNextScan = EpicsSignal("9idcLAX:USAXS:StopBeforeNextScan", name="StopBeforeNextScan")
EmergencyProtectionOn = EpicsSignal("9idcLAX:plc:Y0", name="EmergencyProtectionOn")

# dataCollectionInProgress: for GUI (and other tools) to know that user is collecting data
# (1-not running, 0 running)
dataColInProgress = EpicsSignal("9idcLAX:dataColInProgress", name="dataColInProgress")

plc_X13 = EpicsSignal("9idcLAX:plc:X13", name="plc_X13")

# TODO: Shouldn't these be part of a motor stage? Guard slit?
GSlit1V = EpicsSignal("9idcLAX:GSlit1V:size.VAL", name="GSlit1V")
GSlit1H = EpicsSignal("9idcLAX:GSlit1H:size.VAL", name="GSlit1H")


def __usaxs_wait_for_Interlock():       # TODO: explain why?
    # this function waits for the three 
    waiting_1234 = plc_X13.value
    waiting_1235 = plc_X13.value
    waiting_1236 = plc_X13.value
    t0 = time.time()
    while waiting_1234 == 0 or waiting_1235 == 0 or waiting_1236 == 0:
        sleep(0.1)
        waiting_1234 = plc_X13.value
        waiting_1235 = plc_X13.value
        waiting_1236 = plc_X13.value
        printf("Waiting for Interlock  %g sec, check limit switches\r" % time.time()-t0)



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


"""
get_lim(motor, flag)
    Returns the dial limit of motor number motor. 
    If flag > 0, returns the high limit. 
    If flag < 0, returns the low limit. 
    Resets to command level if not configured for motor. 

set_lim(motor, low, high)
    Sets the low and high limits of motor number motor. 
    low and high are in dial units. 
    It does not actually matter in which order the limits are given. 
    Returns nonzero if not configured for motor or if the protection 
    flags prevent the user from changing the limits on this motor. 
    Resets to command level if any motors are moving. 

"""

def get_lim(motor, flag):
    """
    Returns the dial limit of motor
    
    flag > 0: returns high limit
    flag < 0: returns low limit
    flag == 0: returns None
    """
    if flag > 0:
        return motor.high_limit # TODO: dial?
    else:
        return motor.low_limit  # TODO: dial?

def set_lim(motor, low, high):
    """
    Sets the low and high limits of motor number motor
    
    low and high are in dial units
    
    It does not actually matter in which order the limits are given. 

    !Returns nonzero if not configured for motor or if the protection 
    !flags prevent the user from changing the limits on this motor. 
    !Resets to command level if any motors are moving. 
    """


def move_WAXSOut():
    StopIfPLCEmergencyProtectionOn()
    ccd_shutter.close()
    ti_filter_shutter.close()

    print ("Moving WAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["dirty"])

    # move the pin_z away from sample
    waxsx.move(WAXS_Xout)               # FIXME: WAXS_Xout

    # TODO: set_lim() function
    set_lim(waxsx,get_lim(waxsx,1),dial(waxsx,WAXS_Xout + WAXS_XLimOffset))

    print "Removed WAXS from beam position"
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["out of beam"])


def move_WAXSIn():
    StopIfPLCEmergencyProtectionOn()
    ccd_shutter.close()
    ti_filter_shutter.close()
    print("Moving to WAXS mode")
    if UsaxsSaxsMode.value != 1:
        print("Found UsaxsSaxsMode = %s " % UsaxsSaxsMode.value)
        msg = "Incorrect UsaxsSaxsMode mode found."
        msg += " If SAXS, WAXS, and USAXS are out of beam, UsaxsSaxsMode.put(%d)" 
        raise ValueError(msg % UsaxsSaxsMode_dict["out of beam"])

    __usaxs_wait_for_Interlock()
    # in case there is an error in moving, it is NOT SAFE to start a scan
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["dirty"])
    # first move USAXS out of way
    set_lim(waxsx,get_lim(waxsx,1),dial(waxsx,WAXS_XIn + WAXS_XLimOffset))
    GSlit1V.put(SAXS_VGSlit)   # change slits
    GSlit1H.put(SAXS_HGSlit)   # change slits
    A[waxsx] = WAXS_XIn
    A[uslvap] = SAXS_VSlit
    A[uslhap] = SAXS_HSlit
    move_em; waitmove
    print("WAXS is in position")
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["WAXS in beam"])


def move_SAXSOut():
    StopIfPLCEmergencyProtectionOn()
    ccd_shutter.close()
    ti_filter_shutter.close()

    print("Moving SAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["dirty"])
    
    # move the pin_z away from sample
    saxs_stage.z.move(PIN_ZOut)               # FIXME: 

    set_lim(pin_z,get_lim(pin_z,1),dial(pin_z,PIN_ZOut - PIN_ZLimOffset))
    
    # move pinhole up to out of beam position
    saxs_stage.y.move(PIN_YOut)               # FIXME: 

    # TODO: set_lim() function
    set_lim(pin_y,dial(pin_y,(PIN_YOut-PIN_YLimOffset)),get_lim(pin_y,-1))

    print("Removed SAXS from beam position")
    ###sleep(1)    #waxs seems to be getting ahead of saxs limit switch - should not be needed, we have __usaxs_wait_for_Interlock now. 
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["out of beam"])


def move_SAXSIn():
    StopIfPLCEmergencyProtectionOn()
    ccd_shutter.close()
    ti_filter_shutter.close()
    print("Moving to Pinhole SAXS mode")
    if UsaxsSaxsMode.value != 1:
        print("Found UsaxsSaxsMode = %s " % UsaxsSaxsMode.value)
        msg = "Incorrect UsaxsSaxsMode mode found."
        msg += " If USAXS is out of beam, UsaxsSaxsMode.put(%d)" 
        raise ValueError(msg % UsaxsSaxsMode_dict["out of beam"])

    __usaxs_wait_for_Interlock()
    # in case there is an error in moving, it is NOT SAFE to start a scan
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["dirty"])
    # first move USAXS out of way
    set_lim(pin_y,dial(pin_y,PIN_YIn - PIN_YLimOffset),get_lim(pin_y,-1))

    GSlit1V.put(SAXS_VGSlit)   # change slits
    GSlit1H.put(SAXS_HGSlit)   # change slits

    A[pin_y]=PIN_YIn
    A[uslvap] = SAXS_VSlit
    A[uslhap] = SAXS_HSlit
    move_em; waitmove
    set_lim(pin_z,get_lim(pin_z,1), dial(pin_z,PIN_ZIn - PIN_ZLimOffset))
    A[pin_z] = PIN_ZIn
    move_em; waitmove
    print("Pinhole SAXS is in position")
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["SAXS in beam"])


def move_USAXSOut():
    StopIfPLCEmergencyProtectionOn()
    ccd_shutter.close()
    ti_filter_shutter.close()

    print("Moving USAXS out of beam")
    # in case there is an error in moving, it is NOT SAFE to start a scan
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["dirty"])
    move_motors(
        a_stage.x, AX_Out,  # FIXME:
        d_stage.x, DX_Out,  # FIXME:
    )

    # now Main stages are out of place, 
    # so we can now set the limits and then move pinhole in place.
    set_lim(ax,dial(ax,AX_Out - AX_LimOffset),get_lim(ax,1))
    set_lim(dx,get_lim(dx,1),dial(dx,(DX_Out + DX_LimOffset)))

    print("Removed USAXS from beam position")
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["out of beam"])


def move_USAXSIn():
    StopIfPLCEmergencyProtectionOn()
    ccd_shutter.close()
    ti_filter_shutter.close()
    print("Moving to USAXS mode")
    if UsaxsSaxsMode.value != 1:
        print("Found UsaxsSaxsMode = %s " % UsaxsSaxsMode.value)
        msg = "Incorrect UsaxsSaxsMode mode found."
        msg += " If SAXS is out of beam, UsaxsSaxsMode.put(%d)" 
        raise ValueError(msg % UsaxsSaxsMode_dict["out of beam"])

    __usaxs_wait_for_Interlock()
    # in case there is an error in moving, it is NOT SAFE to start a scan
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["dirty"])

    # move USAXS in the beam
    # set the limits so we can move pinhole in place.
    set_lim(ax,dial(ax,AX_In - AX_LimOffset),get_lim(ax,1))
    set_lim(dx,get_lim(dx,1),dial(dx,DIODE_DX + DX_LimOffset))

    GSlit1V.put(USAXS_VGSlit)   # change slits
    GSlit1H.put(USAXS_HGSlit)   # change slits

    move_motors(
        usaxs_slit.vap = USAXS_VSlit,
        usaxs_slit.hap = USAXS_HSlit,
        a_stage.y = AY0,
        a_stage.x = AX_In,
        d_stage.x = DX_In,
        d_stage.y = DY0,
    )

    print("USAXS is in position")
    UsaxsSaxsMode.put(UsaxsSaxsMode_dict["USAXS in beam"])
