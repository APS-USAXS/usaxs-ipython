print(__file__)

# Bluesky plans (scans)


def uascan():
    """
    USAXS step scan
    
    https://github.com/APS-USAXS/ipython-usaxs/issues/8
    """
    # TODO: needs proper args & kwargs matching SPEC's signature


# TODO: #48 send email
"""
# /home/beams/USAXS/spec/macros/local/usaxs_commands.mac
def sendNotifications(subject, message) '{
    global NOTIFICATION_ADDRESSES
    global NOTIFICATION_ADDRESSES_COUNT
    for(i=0;i<NOTIFICATION_ADDRESSES_COUNT;i++) {
    USER_EMAIL=NOTIFICATION_ADDRESSES[i]
    command = "echo \""message"\" | mail -s \""subject"\" "USER_EMAIL
    unix(command);  
    }
}'


221.USAXS> p NOTIFY_ON_FEEDBACK
1

222.USAXS> p NOTIFICATION_ADDRESSES
NOTIFICATION_ADDRESSES["0"] = "ilavsky@aps.anl.gov"
NOTIFICATION_ADDRESSES["1"] = "kuzmenko@aps.anl.gov"
NOTIFICATION_ADDRESSES["2"] = "mfrith@anl.gov"
"""


class DCM_Feedback(Device):
    """
    monochromator feedback program
    
    Add support for set() so that we can implement "on" & "off" values
    and also apply additional checks when turning feedback on.
    
    from SPEC code

        diff_hi = drvh - oval
        diff_lo = oval - drvl
        if diff<0.2 or diff_lo<0.2:
            if NOTIFY_ON_FEEDBACK:
                sendNotifications("USAXS Feedback problem","Feedback is very close to its limits.");
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

dcm_omega2_feedback = DCM_Feedback("9idcLAX:fbe:omega", name="dcm_omega2_feedback")


"""
# /home/beams/USAXS/spec/macros/local/usaxs_commands.mac
def DCMfeedbackON '{
      epics_put("9idcLAX:fbe:omega:on",1)
}'
"""


# TODO: #47
def preUSAXStune():
    """
    yield from bps.mv(dcm_omega2_feedback.on, 1)
    ccd_shutter.close()
!   IfRequestedStopBeforeNextScan           # stop if user chose to do so. 
!   useModeUSAXS                            # should be done only in USAXS mode. 
    yield from bps.mv(          # if user was in Radiography mode, move diode in place
!       d_stage.x, DIODE_DX,
!       d_stage.y, DIODE_DY,
    
    )
!   global useSBUSAXS 
    global useMSstage
!   epics_put ("9idcLAX:USAXS:timeStamp",   date())
!   epics_put ("9idcLAX:USAXS:state",       "pre-USAXS optics tune")
    mono_shutter.open()
!   usaxs_CheckBeamStandard
!   chk_beam_on
!   set_USAXS_Slits                        # make sure USAXS slits are set correctly...
    autoscale_amplifiers()                 # set ranges for all amplifiers
    yield from tune_mr()                   # tune M stage to monochromator
    yield from tune_m2rp()                 # tune M stage paralelity
    #tune_m2rp_fbe()                       # tune M stage parallelism using feedback
!   if useSBUSAXS == 1:
!       if useMSstage == 1:
            yield from tune_msrp()         # tune msrp stage
        yield from tune_asrp()             # tune asrp stage and set ASRP0 value
    autoscale_amplifiers()                 # set ranges for all amplifiers
    yield from tune_ar()                   # tune up the analyzer crystal pair
    autoscale_amplifiers()                 # set ranges for all amplifiers
    yield from tune_a2rp()                 # tune up the analyzer crystal pair
!   #yield from tune_a2rp_fbe()            # using the feedback    
!   printf ("USAXS count time: {} second(s)".format(USAXS_TIME))
!   scaler0.preset_time.put(USAXS_TIME)
!   epics_put ("9idcLAX:USAXS:timeStamp",   date())
!   epics_put ("9idcLAX:USAXS:state",       "pre-USAXS optics tuning done")
!   set_NumScansFromLastTune 0
!   set_RunPreUSAXStuneNext 0
!   set_EPOCHTimeOfLastTune time()
  """
