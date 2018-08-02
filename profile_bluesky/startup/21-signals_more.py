print(__file__)

"""more signals"""
# TODO: eventually merge with 21-signals.py

# these are the global settings PVs for various parts of the instrument

"""

### These functions make original global spec variables - now in EPICS
### accessible by name. 
	CCD_DX		9idcLAX:USAXS:CCD_dx	
	CCD_DY		9idcLAX:USAXS:CCD_dy	
	DIODE_DY		9idcLAX:USAXS:DY0	
	DIODE_DX		9idcLAX:USAXS:Diode_dx	
	USAXS_TIME		9idcLAX:USAXS:CountTime	
	NUMPNTS		9idcLAX:USAXS:NumPoints	
	UATERM		9idcLAX:USAXS:UATerm	
	SAMPLE_Y_STEP		9idcLAX:USAXS:Sample_Y_Step	
	AY0		9idcLAX:USAXS:AY0	
	DY0		9idcLAX:USAXS:DY0	
	SAD		9idcLAX:USAXS:SAD	
	SDD		9idcLAX:USAXS:SDD	
	USAXS_MINSTEP		9idcLAX:USAXS:MinStep	
	AR_VAL_CENTER		9idcLAX:USAXS:ARcenter	
	ASR_VAL_CENTER		9idcLAX:USAXS:ASRcenter	
	MR_VAL_CENTER		9idcLAX:USAXS:MRcenter	
	MSR_VAL_CENTER		9idcLAX:USAXS:MSRcenter	
	IMG_AL_FILTER		9idcLAX:USAXS:Img_Al_Filter	
	IMG_TI_FILTER		9idcLAX:USAXS:Img_Ti_Filter	
	SCAN_AL_FILTER		9idcLAX:USAXS:Scan_Al_Filter	
	SCAN_TI_FILTER		9idcLAX:USAXS:Scan_Ti_Filter	
	ASRP0		9idcLAX:USAXS:ASRcenter	
	START_OFFSET		9idcLAX:USAXS:StartOffset	
	FINISH		9idcLAX:USAXS:Finish	
	MOTOR_PRESCALER_WAIT		9idcLAX:USAXS:Prescaler_Wait	
	UPDRange	epics_get(sprintf("%s:lurange",UPD_PV),"short	


#And these functions make the pinhole globals work...

	PIN_ZIn		9idcLAX:USAXS_Pin:Pin_z_in	
	PIN_ZOut		9idcLAX:USAXS_Pin:Pin_z_out	
	PIN_ZLimOffset		9idcLAX:USAXS_Pin:Pin_z_limit_offset	
	PIN_YIn		9idcLAX:USAXS_Pin:Pin_y_in	
	PIN_YOut		9idcLAX:USAXS_Pin:Pin_y_out	
	PIN_YLimOffset		9idcLAX:USAXS_Pin:Pin_y_limit_offset	
	AX_In		9idcLAX:USAXS_Pin:ax_in	
	AX_Out		9idcLAX:USAXS_Pin:ax_out	
	AX_LimOffset		9idcLAX:USAXS_Pin:ax_limit_offset	
	DX_In		9idcLAX:USAXS:Diode_dx	
	DX_Out		9idcLAX:USAXS_Pin:dx_out	
	DX_LimOffset		9idcLAX:USAXS_Pin:dx_limit_offset	
	USAXS_HSlit		9idcLAX:USAXS_Pin:USAXS_hslit_ap	
	USAXS_VSlit		9idcLAX:USAXS_Pin:USAXS_vslit_ap	
	SAXS_VSlit 		9idcLAX:USAXS_Pin:Pin_vslit_ap	
	SAXS_HSlit		9idcLAX:USAXS_Pin:Pin_hslit_ap	

	USAXS_HGSlit		9idcLAX:USAXS_Pin:USAXS_hgslit_ap	
	USAXS_VGSlit		9idcLAX:USAXS_Pin:USAXS_vgslit_ap	
	SAXS_VGSlit 		9idcLAX:USAXS_Pin:Pin_vgslit_ap	
	SAXS_HGSlit		9idcLAX:USAXS_Pin:Pin_hgslit_ap	


	PIN_AL_FILTER		9idcLAX:USAXS_Pin:Exp_Al_Filter	
	PIN_TI_FILTER		9idcLAX:USAXS_Pin:Exp_Ti_Filter	

	PIN_TRPD		9idcLAX:USAXS_Pin:Pin_TrPD	
	PIN_TRI0		9idcLAX:USAXS_Pin:Pin_TrI0	
	PIN_TRPDGain		9idcLAX:USAXS_Pin:Pin_TrPDgain	
	PIN_TRI0Gain		9idcLAX:USAXS_Pin:Pin_TrI0gain	

	PIN_IMAGE_BASEDIR		9idcLAX:USAXS_Pin:directory	

	USAXSSAXSMODE		9idcLAX:USAXS_Pin:USAXSSAXSMode	
	PIN_NumImages		9idcLAX:USAXS_Pin:NumImages	
	PIN_AcquireTime		9idcLAX:USAXS_Pin:AcquireTime	
	PIN_EXP_TIME		9idcLAX:USAXS_Pin:AcquireTime	

	USAXS_MEASURE_PIN_TRANS		9idcLAX:USAXS:TR_MeasurePinTrans	             # measure transmission in USAXS using pin diode
	USAXSPinT_AyPosition		9idcLAX:USAXS:TR_AyPosition	      		# Ay to hit pin diode
	USAXSPinT_MeasurementTime		9idcLAX:USAXS:TR_MeasurementTime		        # How long to count
	USAXSPinT_pinCounts		9idcLAX:USAXS:TR_pinCounts			        # How many counts were on pin diode
	USAXSPinT_pinGain		9idcLAX:USAXS:TR_pinGain					# gain of pin diode (note, we are using I00 amplifier here)
	USAXSPinT_I0Counts		9idcLAX:USAXS:TR_I0Counts					# How many counts were on I0 
	USAXSPinT_I0Gain		9idcLAX:USAXS:TR_I0Gain					# gain of I0

	
# this is Io value from gates scalar in LAX for Nexus file
	PIN_I0		9idcLAX:USAXS_Pin:I0	
# WAXS
	WAXS_XIn		9idcLAX:USAXS_Pin:waxs_x_in	
	WAXS_Xout		9idcLAX:USAXS_Pin:waxs_x_out	
	WAXS_XLimOffset		9idcLAX:USAXS_Pin:waxs_x_limit_offset	
	WEXP_AL_FILTER		9idcLAX:USAXS_WAXS:Exp_Al_Filter	
	WEXP_TI_FILTER		9idcLAX:USAXS_WAXS:Exp_Ti_Filter	
	WAXS_IMAGE_BASEDIR		9idcLAX:USAXS_WAXS:directory	
	WAXS_NumImages		9idcLAX:USAXS_WAXS:NumImages	
	WAXS_AcquireTime		9idcLAX:USAXS_WAXS:AcquireTime	
	WAXS_EXP_TIME		9idcLAX:USAXS_WAXS:AcquireTime	

# USAXS Imaging
	UImg_ImageKey		9idcLAX:USAXS_Img:ImageKey	 
##  UImg_ImageKey: "0-image, 1-flat field, 2-dark field")
	UImg_ExposureTime		9idcLAX:USAXS_Img:ExposureTime	

	UImg_Tomo_Rot_Angle		9idcLAX:USAXS_Img:Tomo_Rot_Angle	
	UImg_Img_I0_value		9idcLAX:USAXS_Img:Img_I0_value	
	UImg_Img_I0_gain		9idcLAX:USAXS_Img:Img_I0_gain	

	UImg_AxPosition		9idcLAX:USAXS_Img:ax_in	
	UImg_WaxsXPosition		9idcLAX:USAXS_Img:waxs_x_in	

	UImg_FlatFieldImage		9idcLAX:USAXS_Img:FlatFieldImage	
	UImg_DarkFieldImage		9idcLAX:USAXS_Img:DarkFieldImage	
	UImg_ExperimentTitle		9idcLAX:USAXS_Img:ExperimentTitle	

	UImg_ImgHorApperture		9idcLAX:USAXS_Img:ImgHorApperture	 
	UImg_ImgVertApperture		9idcLAX:USAXS_Img:ImgVertApperture	 
	UImg_ImgGuardHorApperture		9idcLAX:USAXS_Img:ImgGuardHorApperture	 
	UImg_ImgGuardVertApperture		9idcLAX:USAXS_Img:ImgGuardVertApperture	 
	UImg_Img_Al_Filters		9idcLAX:USAXS_Img:Img_Al_Filters	
	UImg_Img_Ti_Filters		9idcLAX:USAXS_Img:Img_Ti_Filters	
	UImg_FilterTransmision	epics_get(9idcLAX:USAXS_Img:Img_FilterTransmission	

# preUSAXStune handling
	NumScansFromLastTune		9idcLAX:USAXS:NumScansFromLastTune	
	EPOCHTimeOfLastTune		9idcLAX:USAXS:EPOCHTimeOfLastTune	
	ReqNumScansBetweenTune		9idcLAX:USAXS:ReqNumScansBetweenTune	
	ReqTimeBetweenTune		9idcLAX:USAXS:ReqTimeBetweenTune	
	RunPreUSAXStuneOnQdo		9idcLAX:USAXS:RunPreUSAXStuneOnQdo	
	RunPreUSAXStuneNext		9idcLAX:USAXS:RunPreUSAXStuneNext	

	set_NumScansFromLastTune		9idcLAX:USAXS:NumScansFromLastTune	
	set_EPOCHTimeOfLastTune		9idcLAX:USAXS:EPOCHTimeOfLastTune	
	set_ReqNumScansBetweenTune		9idcLAX:USAXS:ReqNumScansBetweenTune	
	set_ReqTimeBetweenTune		9idcLAX:USAXS:ReqTimeBetweenTune	
	set_RunPreUSAXStuneOnQdo		9idcLAX:USAXS:RunPreUSAXStuneOnQdo	
	set_RunPreUSAXStuneNext		9idcLAX:USAXS:RunPreUSAXStuneNext	

# set commands 

## USAXS Imaging set commands:
	set_UImg_ImageKey		9idcLAX:USAXS_Img:ImageKey	 
##  "0-image, 1-flat field, 2-dark field")
	set_UImg_ExposureTime		9idcLAX:USAXS_Img:ExposureTime	

	set_UImg_Tomo_Rot_Angle		9idcLAX:USAXS_Img:Tomo_Rot_Angle	
	set_UImg_Img_I0_value		9idcLAX:USAXS_Img:Img_I0_value	
	set_UImg_Img_I0_gain		9idcLAX:USAXS_Img:Img_I0_gain	

	set_UImg_AxPosition		9idcLAX:USAXS_Img:ax_in"v)'
	set_UImg_WaxsXPosition		9idcLAX:USAXS_Img:waxs_x_in	

	set_UImg_FlatFieldImage		9idcLAX:USAXS_Img:FlatFieldImage
	set_UImg_DarkFieldImage		9idcLAX:USAXS_Img:DarkFieldImage
	set_UImg_ExperimentTitle		9idcLAX:USAXS_Img:ExperimentTitle

	set_UImg_ImgHorApperture		9idcLAX:USAXS_Img:ImgHorApperture	 
	set_UImg_ImgVertApperture		9idcLAX:USAXS_Img:ImgVertApperture	 
	set_UImg_ImgVertApperture		9idcLAX:USAXS_Img:ImgVertApperture	 
	set_UImg_ImgGuardVertApperture		9idcLAX:USAXS_Img:ImgGuardVertApperture	 
	set_UImg_Img_Al_Filters		9idcLAX:USAXS_Img:Img_Al_Filters	
	set_UImg_Img_Ti_Filters		9idcLAX:USAXS_Img:Img_Ti_Filters	
	set_UImg_FilterTransmision		9idcLAX:USAXS_Img:Img_FilterTransmission	


## standard set commands... 

	set_CCD_DX		9idcLAX:USAXS:CCD_dx	
	set_CCD_DY		9idcLAX:USAXS:CCD_dy	
	set_DIODE_DY		9idcLAX:USAXS:DY0	
	set_DIODE_DX		9idcLAX:USAXS:Diode_dx	
	set_USAXS_TIME		9idcLAX:USAXS:CountTime	
	set_NUMPNTS		9idcLAX:USAXS:NumPoints	
	set_UATERM		9idcLAX:USAXS:UATerm	
	set_SAMPLE_Y_STEP		9idcLAX:USAXS:Sample_Y_Step	
	set_AY0		9idcLAX:USAXS:AY0	
	set_DY0		9idcLAX:USAXS:DY0	
	set_SAD		9idcLAX:USAXS:SAD	
	set_SDD		9idcLAX:USAXS:SDD	
	set_USAXS_MINSTEP		9idcLAX:USAXS:MinStep	
	set_AR_VAL_CENTER		9idcLAX:USAXS:ARcenter	
	set_ASR_VAL_CENTER		9idcLAX:USAXS:ASRcenter	
	set_MR_VAL_CENTER		9idcLAX:USAXS:MRcenter	
	set_MSR_VAL_CENTER		9idcLAX:USAXS:MSRcenter	
	set_IMG_AL_FILTER		9idcLAX:USAXS:Img_Al_Filter	
	set_IMG_TI_FILTER		9idcLAX:USAXS:Img_Ti_Filter	
	set_SCAN_AL_FILTER		9idcLAX:USAXS:Scan_Al_Filter	
	set_SCAN_TI_FILTER		9idcLAX:USAXS:Scan_Ti_Filter	
	set_ASRP0		9idcLAX:USAXS:ASRcenter	
	set_START_OFFSET		9idcLAX:USAXS:StartOffset	
	set_FINISH		9idcLAX:USAXS:Finish	
	set_MOTOR_PRESCALER_WAIT		9idcLAX:USAXS:Prescaler_Wait	

	set_PIN_ZIn		9idcLAX:USAXS_Pin:Pin_z_in	
	set_PIN_ZOut		9idcLAX:USAXS_Pin:Pin_z_out	
	set_PIN_ZLimOffset		9idcLAX:USAXS_Pin:Pin_z_limit_offset	
	set_PIN_YIn		9idcLAX:USAXS_Pin:Pin_y_in	
	set_PIN_YOut		9idcLAX:USAXS_Pin:Pin_y_out	
	set_PIN_YLimOffset		9idcLAX:USAXS_Pin:Pin_y_limit_offset	
	set_AX_In		9idcLAX:USAXS_Pin:ax_in	
	set_AX_Out		9idcLAX:USAXS_Pin:ax_out	
	set_AX_LimOffset		9idcLAX:USAXS_Pin:ax_limit_offset	
	set_DX_In		9idcLAX:USAXS:Diode_dx	
	set_DX_Out		9idcLAX:USAXS_Pin:dx_out	
	set_DX_LimOffset		9idcLAX:USAXS_Pin:dx_limit_offset	
	set_USAXS_HSlit		9idcLAX:USAXS_Pin:USAXS_hslit_ap	
	set_USAXS_VSlit		9idcLAX:USAXS_Pin:USAXS_vslit_ap	
	set_SAXS_VSlit 		9idcLAX:USAXS_Pin:Pin_vslit_ap	
	set_SAXS_HSlit		9idcLAX:USAXS_Pin:Pin_hslit_ap	

	set_USAXS_HGSlit		9idcLAX:USAXS_Pin:USAXS_hgslit_ap	
	set_USAXS_VGSlit		9idcLAX:USAXS_Pin:USAXS_vgslit_ap	
	set_SAXS_VGSlit 		9idcLAX:USAXS_Pin:Pin_vgslit_ap	
	set_SAXS_HGSlit		9idcLAX:USAXS_Pin:Pin_hgslit_ap	

	set_PIN_AL_FILTER		9idcLAX:USAXS_Pin:Exp_Al_Filter	
	set_PIN_TI_FILTER		9idcLAX:USAXS_Pin:Exp_Ti_Filter	
	set_PIN_NumImages		9idcLAX:USAXS_Pin:NumImages	

	set_PIN_AcquireTime		9idcLAX:USAXS_Pin:AcquireTime	
	set_PIN_EXP_TIME		9idcLAX:USAXS_Pin:AcquireTime	
	set_PIN_TRPD		9idcLAX:USAXS_Pin:Pin_TrPD	
	set_PIN_TRI0		9idcLAX:USAXS_Pin:Pin_TrI0	
	set_PIN_TRPDGain		9idcLAX:USAXS_Pin:Pin_TrPDgain	
	set_PIN_TRI0Gain		9idcLAX:USAXS_Pin:Pin_TrI0gain	

	set_PIN_IMAGE_BASEDIR		9idcLAX:USAXS_Pin:directory	


# WAXS
	set_WAXS_IMAGE_BASEDIR		9idcLAX:USAXS_WAXS:directory	

	set_WAXS_XIn		9idcLAX:USAXS_Pin:waxs_x_in	
	set_WAXS_Xout		9idcLAX:USAXS_Pin:waxs_x_out	
	set_WAXS_XLimOffset		9idcLAX:USAXS_Pin:waxs_x_limit_offset	
	set_WEXP_AL_FILTER		9idcLAX:USAXS_WAXS:Exp_Al_Filter	
	set_WEXP_TI_FILTER		9idcLAX:USAXS_WAXS:Exp_Ti_Filter	
	set_WAXS_AcquireTime		9idcLAX:USAXS_WAXS:AcquireTime	
	set_WAXS_EXP_TIME		9idcLAX:USAXS_WAXS:AcquireTime	
	set_WAXS_NumImages		9idcLAX:USAXS_WAXS:NumImages	

#transmission
 	set_USAXS_MEASURE_PIN_TRANS		9idcLAX:USAXS:TR_MeasurePinTrans	      # measure transmission in USAXS using pin diode
 	set_USAXSPinT_AyPosition		9idcLAX:USAXS:TR_AyPosition	      		 # Ay to hit pin diode
 	set_USAXSPinT_MeasurementTime		9idcLAX:USAXS:TR_MeasurementTime		# How long to count
 	set_USAXSPinT_pinCounts		9idcLAX:USAXS:TR_pinCounts				# How many counts were on pin diode
 	set_USAXSPinT_pinGain		9idcLAX:USAXS:TR_pinGain					# gain of pin diode (note, we are using I00 amplifier here)
 	set_USAXSPinT_I0Counts		9idcLAX:USAXS:TR_I0Counts				# How many counts were on I0
 	set_USAXSPinT_I0Gain		9idcLAX:USAXS:TR_I0Gain					# gain of I0
"""


# TODO: this belongs somewhere else, but where?
is2DUSAXSscan = EpicsSignal("9idcLAX:USAXS:is2DUSAXSscan", name="is2DUSAXSscan")


class FlyScanParameters(Device):
    """FlyScan values"""
    number_points = Component(EpicsSignal, "9idcLAX:USAXS:FS_NumberOfPoints")
    scan_time = Component(EpicsSignal, "9idcLAX:USAXS:FS_ScanTime")
    use_flyscan = Component(EpicsSignal, "9idcLAX:USAXS:UseFlyscan")
    asrp_calc_SCAN = Component(EpicsSignal, "9idcLAX:userStringCalc2.SCAN")
    order_number = Component(EpicsSignal, "9idcLAX:USAXS:FS_OrderNumber")
    
    def enable_ASRP(self):
        if is2DUSAXSscan.value: # TODO: check return value here
            self.asrp_calc_SCAN.put(9)
    
    def disable_ASRP(self):
        self.asrp_calc_SCAN.put(0)
    
    def increment_order_number(self):
        self.order_number.put(self.order_number.value+1)


FS_terms = FlyScanParameters(name="FS_terms")
