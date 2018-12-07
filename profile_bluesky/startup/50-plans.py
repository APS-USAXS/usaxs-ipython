print(__file__)

# Bluesky plans (scans)


def uascan():
    """
    USAXS step scan
    
    https://github.com/APS-USAXS/ipython-usaxs/issues/8
    """
    # TODO: needs proper args & kwargs matching SPEC's signature


def preUSAXStune():
    """
    tune the USAXS optics *only* if in USAXS mode
    
    USAGE:  ``RE(preUSAXStune())``
    """
    yield from bps.mv(
        monochromator.feedback.on, 1,
        mono_shutter, "open",
        ccd_shutter, "close",
    )
    yield from IfRequestedStopBeforeNextScan()         # stop if user chose to do so.

    yield from bps.mv(
        # TODO: BLOCKING    use_mode, "USAXS",      # Must be in USAXS mode to tune

        # ensure diode in place (Radiography puts it elsewhere)
        d_stage.x, terms.USAXS.diode.dx.value,
        d_stage.y, terms.USAXS.diode.dy.value,

        user_data.time_stamp, str(datetime.datetime.now()),
        user_data.state, "pre-USAXS optics tune",

        # Is this covered by user_mode, "USAXS"?
        usaxs_slit.v_size,  terms.SAXS.usaxs_v_size.value,
        usaxs_slit.h_size,  terms.SAXS.usaxs_h_size.value,
        guard_slit.v_size,  terms.SAXS.usaxs_guard_v_size.value,
        guard_slit.h_size,  terms.SAXS.usaxs_guard_h_size.value,
    )
    # when all that is complete, then ...
    yield from bps.mv(ti_filter_shutter, "open")
    
    # TODO: install suspender using usaxs_CheckBeamStandard.value

    yield from tune_mr()                   # tune M stage to monochromator
    yield from tune_m2rp()                 # tune M stage paralelity
    if terms.USAXS.useMSstage.value:
        yield from tune_msrp()             # tune msrp stage
    if terms.USAXS.useSBUSAXS.value:
        yield from tune_asrp()             # tune asrp stage and set ASRP0 value
    yield from tune_ar()                   # tune up the analyzer crystal pair
    yield from tune_a2rp()                 # tune up the analyzer crystal pair
    print("USAXS count time: {} second(s)".format(terms.USAXS.usaxs_time.value))
    yield from bps.mv(
        scaler0.preset_time,        terms.USAXS.usaxs_time.value,
        user_data.time_stamp,       str(datetime.datetime.now()),
        user_data.state,            "pre-USAXS optics tuning done",
        
        terms.preUSAXStune.num_scans_last_tune, 0,
        terms.preUSAXStune.run_tune_next,       0,
        terms.preUSAXStune.epoch_last_tune,     time.time(),
    )


# TODO: make this look less like a mode
use_mode.add(IfRequestedStopBeforeNextScan, "IfRequestedStopBeforeNextScan")


def Flyscan(pos_X, pos_Y, thickness, scan_title):
    yield from bps.mv(use_mode, "IfRequestedStopBeforeNextScan")
    yield from bps.mv(
        s_stage.x, pos_X,
        s_stage.y, pos_Y,
        # TODO: use_mode, "USAXS",
        # USAXS and guard slits by mode_USAXS command on previous line
        usaxs_slit.usaxs_v_size, terms.SAXS.usaxs_v_size.value,
        usaxs_slit.usaxs_h_size, terms.SAXS.usaxs_h_size.value,
        guard_slit.v_size, terms.SAXS.usaxs_guard_v_size.value,
        guard_slit.h_size, terms.SAXS.usaxs_guard_h_size.value,
    )
    if terms.USAXS.retune_needed.value:
        pass    # implement run_preUSAXStuneIfNeeded(called_from_where)
    
    # TODO: scan_title = __get_clean_user_string(scan_title)
    
    ts = str(datetime.datetime.now())
    yield from bps.mv(
        user_data.sample_title, scan_title,
        user_data.macro_file_time, ts,
        user_data.state, "starting USAXS Flyscan",
        user_data.sample_thickness, thickness,
        user_data.user_name, USERNAME,
        user_data.user_dir, os.getcwd(),
        user_data.spec_file, "-tba-",   # TODO: 
        user_data.spec_scan, "-tba-",   # TODO: 
        user_data.time_stamp, ts,
        user_data.scan_macro, "FlyScan",
    )
    
    # offset the calc from exact zero so can plot log(|Q|)
    ar0_calc_offset = terms.USAXS.ar_val_center.value - 0.00005
    yield from bps.mv(
        a_stage.r, terms.USAXS.ar_val_center.value,
        # these two were moved by mode_USAXS()
        # d_stage.y, terms.USAXS.diode.dy.value,
        # a_stage.y, terms.USAXS.AY0.value,
        # sample stage already moved to pos_X, pos_Y
        user_data.state, "Moving to Q=0 ",
        usaxs_q_calc.channels.B, ar0_calc_offset,
    )

    # TODO: what to do with USAXSScanUp?
    # it's used to cal Finish_in_Angle and START
    # both of which get passed to EPICS
    # That happens outside of this code.  completely.
    """
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
    """

    # measure transmission values using pin diode if desired
    # TODO: measure_USAXS_PinT

    # TODO: #49
    # yield from bps.mv(monochromator.feedback.on, 0)

    # enable asrp link to ar for 2D USAXS
    # FS_enableASRP
    if terms.USAXS.is2DUSAXSscan.value:
        yield from bps.mv(self.asrp_calc_SCAN, 9)

    yield from bps.mv(
        upd_controls.femto.change_gain_up, terms.FlyScan.setpoint_up.value,
        upd_controls.femto.change_gain_down, terms.FlyScan.setpoint_down.value,
        ti_filter_shutter, "open",
    )
    APS_plans.run_blocker_in_plan(
        # must run in thread since this is not a plan
        autoscale_amplifiers([upd_controls, I0_controls, I00_controls])
    )



# TODO: #45 Flyscan
"""
def Flyscan '{

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
