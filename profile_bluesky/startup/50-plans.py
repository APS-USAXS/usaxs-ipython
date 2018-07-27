print(__file__)

# Bluesky plans (scans)


def uascan():
    """
    USAXS step scan
    
    https://github.com/APS-USAXS/ipython-usaxs/issues/8
    """
    # TODO: needs proper args & kwargs matching SPEC's signature


# TODO: #47
def preUSAXStune():
    """
    yield from bps.mv(mono_feedback.on, 1)
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
