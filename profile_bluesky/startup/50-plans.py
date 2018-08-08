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
    tune the USAXS optics *only* if in USAXS mode
    
    USAGE:  ``RE(preUSAXStune())``
    """
    yield from bps.mv(
        mono_feedback.on, 1,
        ccd_shutter, "close",
    )
    IfRequestedStopBeforeNextScan()         # stop if user chose to do so.
    if not confirm_instrument_mode("USAXS in beam"):
        raise ValueError("Must be in USAXS mode to tune!")

    yield from bps.mv(
        use_mode, "USAXS",      # Must be in USAXS mode to tune

        # ensure diode in place (Radiography puts it elsewhere)
        d_stage.x, terms.USAXS.diode.dx.value,    
        d_stage.y, terms.USAXS.diode.dy.value,

        user_data.time_stamp, str(datetime.now()),
        user_data.state, "pre-USAXS optics tune",
    )
    mono_shutter.open()
    
    # TODO: install suspender using usaxs_CheckBeamStandard.value

    set_USAXS_Slits()                      # BLOCKING: make sure USAXS slits are set correctly...
    autoscale_amplifiers()                 # BLOCKING: set ranges for all amplifiers
    yield from tune_mr()                   # tune M stage to monochromator
    yield from tune_m2rp()                 # tune M stage paralelity
    #tune_m2rp_fbe()                       # tune M stage parallelism using feedback
    if terms.useSBUSAXS.value:
        if terms.useMSstage.value:
            yield from tune_msrp()         # tune msrp stage
        yield from tune_asrp()             # tune asrp stage and set ASRP0 value
    autoscale_amplifiers()                 # BLOCKING: set ranges for all amplifiers
    yield from tune_ar()                   # tune up the analyzer crystal pair
    autoscale_amplifiers()                 # BLOCKING: set ranges for all amplifiers
    yield from tune_a2rp()                 # tune up the analyzer crystal pair
    #yield from tune_a2rp_fbe()            # using the feedback    
    print("USAXS count time: {} second(s)".format(terms.USAXS.usaxs_time.value))
    yield from bps.mv(
        scaler0.preset_time, terms.USAXS.usaxs_time.value,
        user_data.time_stamp, str(datetime.now()),
        user_data.state, "pre-USAXS optics tuning done",
        
        terms.preUSAXStune.num_scans_last_tune, 0,
        terms.preUSAXStune.run_tune_next, 0,
        terms.preUSAXStune.epoch_last_tune, time(),
    )


# TODO: #45 Flyscan
"""
def Flyscan '{
   local pos_X pos_Y scan_title Finish_in_Angle 

   global ARenc_CENTER
   global SPEC_STD_TITLE
   global USAXS_SAMPLE_THICKNESS
   global useSBUSAXS
   global USAXS_MEASURE_DARK_CURENTS
   global USAXSScanUp
   global TITLE
   global FSScanFailed
   global FS_UPD_OldUpRangeChange  
   global FS_UPD_UpRangeChange  
   global FS_UPD_OldDownRangeChange  
   global FS_UPD_DownRangeChange  
   local _USAXS_Lambda

   #####################################################
   if( $# != 4) {
        printf ("Flyscan pos_X pos_Y thickness_mm scan_title\n");
        exit;
   }
   pos_X = $1
   pos_Y = $2
   USAXS_SAMPLE_THICKNESS = $3
   scan_title = __returnSampleName("$4")
   #comment "Sample Name is %s" scan_title ##  <<< comment out
   #exit                                  ##  <<< comment out
    IfRequestedStopBeforeNextScan
   
   #####################################################
   # need to check pos_X and pos_Y against soft limits before proceeding
   _bad_lim = 0
   _chk_lim sx pos_X
   _chk_lim sy pos_Y
   if (_bad_lim) {
     printf("sample position (%.3f,%.3f) exceeds soft limits\n", pos_X, pos_Y)
     exit;
   }
   #####################################################
   # make sure we are in USAXS mode, cannot run otherwise. 
   useModeUSAXS  
   ##################################################### 
   set_USAXS_Slits  			  # make sure USAXS slits are set correctly...
   #####################################################
   # check if we are ready to run preUSAXStune and run if requested. 
   run_preUSAXStuneIfNeeded  2
   # done tuning, if requested by user or by number of scans recently done...     
   ##################################################### 
   ## clean the user name and append any information needed
   scan_title  = __get_clean_user_string(scan_title) 
   #####################################################
   SPEC_STD_TITLE = TITLE		# what is TITLE here???
   TITLE      = scan_title
   epics_put ("9idcLAX:USAXS:sampleTitle", scan_title)
   epics_put ("9idcLAX:USAXS:macroFileTime",      date())
   epics_put ("9idcLAX:USAXS:state",       sprintf("starting USAXS Flyscan"))
   epics_put ("9idcLAX:USAXS:userName",    USER)
   epics_put ("9idcLAX:USAXS:userDir",     CWD)
   epics_put ("9idcLAX:USAXS:specFile",    DATAFILE)
   epics_put ("9idcLAX:USAXS:specScan",    SCAN_N+1)
   epics_put ("9idcLAX:USAXS:timeStamp",   date())
   epics_put ("9idcLAX:USAXS:SampleThickness",    USAXS_SAMPLE_THICKNESS)
   if (useSBUSAXS) {
    epics_put ("9idcLAX:USAXS:scanMacro",   "FlyScan")
  } else {
    epics_put ("9idcLAX:USAXS:scanMacro",   "FlyScan")
  }
   #####################################################
   # is this necessary for measurement of transmission using pindiode
   get_angles
   A[ar] = AR_VAL_CENTER
   A[dy] = DY0
   A[ay] = AY0
   A[sx] = pos_X
   A[sy] = pos_Y
   epics_put ("9idcLAX:USAXS:state",  sprintf("Moving to Q=0 "))
   ###moveSample pos_X pos_Y
   comment "Moving AR motor to %g degrees (beam center)" AR_VAL_CENTER
   move_em; waitmove; get_angles;
   ARenc_CENTER = AR_VAL_CENTER
   comment "for next scan: encoder ARenc_CENTER  = %7.4f" ARenc_CENTER
              # Set the center for the Q calculation for plotting here
   epics_put("9idcLAX:USAXS:Q.B", ARenc_CENTER-0.00005)
   #####################################################
   #####################################################
   #####################################################
   #Calculate Finish in angle, since now it is in Q units
   #use en as energy in keV, 
   _USAXS_Lambda = 12.4 / A[en]
   ########################################################################
   # decide if we are scaning up or down...
   if(USAXSScanUp) {
        # scanning up, new method
        Finish_in_Angle = AR_VAL_CENTER + (360/PI)*asin( FINISH * _USAXS_Lambda / (4*PI))
        START = AR_VAL_CENTER + (360/PI)*asin( START_OFFSET * _USAXS_Lambda / (4*PI))
   } else {
        # scanning down, old method
        Finish_in_Angle = AR_VAL_CENTER - (360/PI)*asin( FINISH * _USAXS_Lambda / (4*PI))
        START = AR_VAL_CENTER - (360/PI)*asin( START_OFFSET * _USAXS_Lambda / (4*PI))
   }
   #####################################################
   # measure transmission values using pin diode if desired 
   measure_USAXS_PinT
   #####################################################
   # define cleanup macro for ^C usage
   rdef _cleanup3 \'resetFlyScan\'      
   #####################################################
   DCMfeedbackOFF 
   #####################################################
   # enable asrp link to ar for 2D USAXS
   FS_enableASRP
   #####################################################
   ### change sequence program limits for FS
   epics_put("9idcUSX:pd01:seq02:gainU",FS_UPD_UpRangeChange )
   epics_put("9idcUSX:pd01:seq02:gainD",FS_UPD_DownRangeChange )
   #####################################################
   # autorange upd/I0/I00
   openTiFilterShutter
   autorange_UPDI0I00
   #modeAutoBRange_I0
   #modeAutoBRange_I00
   set_UPD_gain 6            ## start with higher gain than needed in center position. 
   modeAutoBRange_UPD
  #####################################################
   # setup upd amplifier to autorange  
   local FLyScanAUtoscaleTime 
   FLyScanAUtoscaleTime = 0.025
   epics_put ("9idcLAX:vsc:c0.RATE",0) 
   epics_put ("9idcLAX:vsc:c0.RAT1",0) 
   epics_put ("9idcUSX:pd01:seq02:mode",2)
   epics_put ("9idcLAX:vsc:c0.TP1", FLyScanAUtoscaleTime)
   epics_put ("9idcLAX:vsc:c0.TP", FLyScanAUtoscaleTime)
   epics_put ("9idcLAX:vsc:c0.DLY1", FLyScanAUtoscaleTime)
   epics_put ("9idcLAX:vsc:c0.DLY", 0)
   epics_put ("9idcLAX:vsc:c0.CONT", 1)   
   #####################################################
   # Pause autosave on LAX to prevent delays in PVs processing.
   epics_put ("9idcLAX:SR_disable",1)			## this disables autosave
   epics_put ("9idcLAX:SR_disableMaxSecs",FS_ScanTime+9)   ##this sets max time of autosave disable
   #####################################################
   # and here we really scan 
   epics_put ("9idcLAX:USAXS:state",  sprintf("Running Flyscan"))
   ### scanning...
   
   _flyscanInternal START AR_VAL_CENTER Finish_in_Angle
   
   ### done
   epics_put ("9idcLAX:USAXS:state",  sprintf("Flyscan finished"))
   comment "FlyScan finished"
   #####################################################
   # UnPause autosave on LAX to prevent delays in PVs processing.
   epics_put ("9idcLAX:SR_disable",0)			## this enables autosave
   epics_put ("9idcLAX:SR_disableMaxSecs",0)    ## this sets max user_datatime of autosave disable
   #####################################################
   closeTiFilterShutter
   DCMfeedbackON
   epics_put ("9idcLAX:vsc:c0.RATE",5) 
   epics_put ("9idcLAX:vsc:c0.DLY1", 0.25)
   epics_put ("9idcLAX:vsc:c0.DLY", 0.05)
   epics_put ("9idcLAX:vsc:c0.TP", 1)
   epics_put ("9idcLAX:vsc:c0.CONT", 1)   
   #####################################################
   ### change sequence program limits for FS
   epics_put("9idcUSX:pd01:seq02:gainU",FS_UPD_OldUpRangeChange )
   epics_put("9idcUSX:pd01:seq02:gainD",FS_UPD_OldDownRangeChange )
   #####################################################
   # Move to start conditions... 
   # move back to starting conditions while saving data...
   epics_put ("9idcLAX:USAXS:state", sprintf("Moving USAXS back and saving data"))
   A[ar] = AR_VAL_CENTER
   A[dy] = DY0
   A[ay] = AY0
   comment "Moving AR motor back to %g degrees (beam center)" AR_VAL_CENTER
   move_em; waitmove; get_angles
   #####################################################
   # disable asrp link to ar for 2D USAXS
   FS_disableASRP
   #####################################################
   if (USAXS_MEASURE_DARK_CURENTS) { 
       epics_put ("9idcLAX:USAXS:state",  sprintf("measuring dark currents"))
   #    measure_USAXS_PD_dark_currents
   }
   #####################################################
   # normal cleanup macro for ^C usage
   rdef _cleanup3 \'\'
   comment %s scan_title
   TITLE = SPEC_STD_TITLE
   epics_put ("9idcLAX:USAXS:state",   sprintf("USAXS Flyscan done"))
   # turn on the photodiode to auto+bkg mode. I0 and I00 to manual mode
   modeAutoBRange_UPD
   modeManualRange_I0
   modeManualRange_I00
}'
"""

def Flyscan(pos_X, pos_Y, thickness_mm, scan_title):
    user_data.sample_thickness = thickness_mm
    user_data.sample_title = scan_title     # TODO: clean it up, first?
    # TODO: #45


"""
# /home/beams/USAXS/spec/macros/local/usaxs_flyscan.mac
def _flyscanInternal '{
  if ($# != 3) {
    printf("Usage: flyscanInternal %s\n",         \
       "start center finish")  
    exit
  } 
  local _sFly ; local _fFly ; local _dFly ; local _centerFly
  local _asrp0 ; local _ms ; local _dy0 ; local _sad
  local _ay0 ; local _sdd  ; local _exp ; local _n1
  local _ctime, _NumStruckChannels
  local _ScanTimeTotal
  local _FSWritingTimer
  local _UnixCommand    
         # read header into internal (local) parameters. 
  _sFly = $1; _centerFly = $2; _fFly = $3; 
         # these are global parameters, so just copy them here... 

  _ms     = USAXS_MINSTEP ;
  _dy0    = DY0 ;
  _sdd    = SDD ;
  _ay0    = AY0 ;
  _sad    = SAD ;
  _exp    = UATERM ;
  _n1     = int(FS_NumberOfPoints) ;
  _ScanTimeTotal = FS_ScanTime
  _ctime  = _ScanTimeTotal /_n1 ;
   global TITLE 

  ### Flyscan vars ###
  local _i
  local _flyPV 
  local _flynumpts 
  local _flystat
  local array _flyArPos[400] 
  local array _flyDyPos[400] 
  local array _flyAyPos[400] 
  global FlyScan_ArPosArray

  local array _flydata[4][100000]
  local _EPD
  local _EPDsaveFlyData
  local _EPDcfgFlyData
  local _FlyDataFile
  local _SampleTitle
  local _DataCollectionTimer
  local LocalFldrName 
  local __FS_HangedScanFound
  local __tmp_234
  global FSScanFailed
  global FSToleratePoints
  global FSRetryUpToFlyScans
  FSScanFailed = 0

   #####################################################
  ###_SampleTitle = __get_clean_user_string(epics_get ("9idcLAX:USAXS:sampleTitle"))
  _SampleTitle = epics_get ("9idcLAX:USAXS:sampleTitle")
  _flynumpts = FS_NumberOfPoints 
  _trajPV = "9idcLAX:traj1:"
  _flyPV  = "9idcLAX:USAXSfly:"
  _EPD = "/APSshare/anaconda/x86_64/bin/python"
  _EPDsaveFlyData = "/home/beams/USAXS/Documents/eclipse/USAXS/tools/saveFlyData.py"
  _EPDcfgFlyData = "/home/beams/USAXS/Documents/eclipse/USAXS/tools/saveFlyData.xml"
   TITLE  =_SampleTitle
   #####################################################
   _NumStruckChannels =(fabs(_fFly - _sFly)/_ms)
		   	# test if number of channels on Struck is sufficient. 
	 		#  if(_NumStruckChannels>159999){
	 		#     printf("Too Many Struck channels used: %g, reduce Q range or increase MinStep \n", _NumStruckChannels)
	 		##     exit; 
	 		# }
   #####################################################
   # create spec scan record...
   # set heading for scans to show if we are running USAXS or SBUSAXS
	HEADING = (useSBUSAXS) ?  "sbFlyScan " : "FlyScan "
	HEADING=sprintf("%s%s",HEADING,sprintf(" %s %g %g %g %g ",\
		"ar",START ,_AR_VAL_CENTER , Finish_in_Angle , _ms))
	FPRNT=PPRNT=VPRNT=""
	FPRNT=sprintf("%s%s  ",FPRNT,motor_name(ar))
	PPRNT=sprintf("%s%8.8s ",PPRNT,motor_name(ar))start
	VPRNT=sprintf("%s%9.9s ",VPRNT,motor_name(ar))start
	scan_head
	PFMT=sprintf("%%s%%8.%df ",UP)
	VFMT=sprintf("%%s%%9.%df ",UP)
	# UP is user precision, defined in standard.mac as 4
    # it can be redefined to show more decimal places if needed
    # done with spec scan record...
    #####################################################
    #####################################################
    ### move to start conditions... 
    A[ay]=_ay0
    A[ar]=_sFly 
    A[dy]=_dy0
    move_em; waitmove
    #####################################################
    ###  setup trajectory parameters
    epics_put("9idcLAX:USAXS:ARstart.VAL", _sFly)
    epics_put("9idcLAX:USAXS:ARstart.PREC", 6)
    epics_put("9idcLAX:USAXS:ARstart.DESC", "AR_start of fly scan")
    epics_put("9idcLAX:USAXS:ARstart.EGU",  "degrees")
   #####################################################
   # create name for the folder for data and full path to future Nexus file for the data. 
   LocalFldrName  = USAXS_CleanupFileName (DATAFILE , "usaxs") 
   _FlyDataFile =sprintf("./%s/%s_%04d.h5", LocalFldrName, _SampleTitle, FS_orderNumber)
   # and increase the order number
   FS_increaseOrderNumber
   #####################################################   
    ### Call epics to start fly scan... and wait for done
    __tmp_234 =_ctime*_flynumpts + 15
    comment "FlyScan #%d started" SCAN_N
    comment "FlyScan file name = %s"  _FlyDataFile
    comment "Please wait approximately %gs to complete FlyScan." __tmp_234 
    #####################################################   
    			### store max expected time for python code to read PVs so it will not hang for too long.  
    			###				epics_put("9idcLAX:USAXS:FS_timeout", 20)
   			### set our scan to not failed
    			#__FS_HangedScanFound = 0
   #####################################################   
   ###  collect the data using epics fly scan.... 
   set_FS_ElapsedTime 0
   # set the user bit to indicate FlyScan scan is running
   epics_put ("9idcLAX:USAXS:scanning",  1)
   #####################################################
   #SaveStruck data using unix command
   _UnixCommand = sprintf("mkdir.sh %s/%s", CWD, LocalFldrName) ";"  sprintf("%s %s %s %s", _EPD, _EPDsaveFlyData, _FlyDataFile, _EPDcfgFlyData) " &"
   			# print _UnixCommand 
   			# unix( sprintf("mkdir.sh %s/%s", CWD, LocalFldrName))
   			# unix( sprintf("%s %s %s %s", _EPD, _EPDsaveFlyData, _FlyDataFile, _EPDcfgFlyData))
   # Collect data and wait for it to finish... 
   epics_par(sprintf("%sStart",_flyPV), "monitor_set")
   #this starts the FLyscan itself:
   epics_put(sprintf("%sStart",_flyPV), "Busy")	
   # set the flag of Python code that it needs to save data
   epics_put("9idcLAX:USAXS:FlyScanNotSaved", 1)
   # timeout to make sure flyscan started... 
   sleep(5)
   unix (_UnixCommand)   # this should start the Python program in the background
   _DataCollectionTimer = 5
   
   while (epics_get(sprintf("%sStart",_flyPV)) != "Done") {
        sleep(1)
        _DataCollectionTimer++
        set_FS_ElapsedTime _DataCollectionTimer
        printf("Waiting for Flyscan to collect data %g sec\r", _DataCollectionTimer)
        # Josh added this to collect uvvis data
       
        epics_put ("9idcLAX:USAXS:state", sprintf("Running Flyscan for %gs",_DataCollectionTimer))
        wait(0x28)
   }
   epics_par(sprintf("%sStart",_flyPV), "monitor_clear")
   #####################################################
   # return to Q=0 while waiting for data to be written (that should take only second)
   ### move to Q=0 conditions... 
   A[dy] = DY0
   A[ay] = AY0
   A[ar] = AR_VAL_CENTER
   move_em; waitmove
   #####################################################
   # if still necessary, wait for Python to finish writing the data
   _FSWritingTimer = 0
   while(epics_get("9idcLAX:USAXS:FlyScanNotSaved")>0.5){
        sleep(1)
        _FSWritingTimer++
        set_FS_ElapsedTime (_DataCollectionTimer+_FSWritingTimer)
        printf("Waiting for Flyscan to save data %g sec\r", _FSWritingTimer)
        epics_put ("9idcLAX:USAXS:state", sprintf("Saving Flyscan data for %gs",_FSWritingTimer))
        wait(0x28)
   }
   # clear the user bit to indicate FlyScan scan is not running
   epics_put ("9idcLAX:USAXS:scanning",  0)
   #####################################################
   comment "Flyscan done after %gs." (_DataCollectionTimer+_FSWritingTimer)
   #####################################################
   set_FS_ElapsedTime 0
   #####################################################
   ##Check if we had bad number of PSO pulses  #########
   local __tmpDIffInPnts 
   local __FSErromsg
   __tmpDIffInPnts = epics_get("9idcLAX:traj1:NumPulsePositions") - epics_get("9idcLAX:3820:CurrentChannel")
   ## if OK, the difference should be 1 point (due to 1 based and 0 based 8k points). 
   if( __tmpDIffInPnts > 5 ){
   	comment "WARNING: Flyscan finished with %g less points." __tmpDIffInPnts
        __FSErromsg = sprintf("Flyscan finished with %g less points.", __tmpDIffInPnts)
   	if(NOTIFY_ON_BADFSSCAN) { sendNotifications("FlyScan had wrong number of points",__FSErromsg);}
   }
   #####################################################
}'
"""

def _flyscanInternal(start, center, finish, scan_time):
    """-tba-"""
