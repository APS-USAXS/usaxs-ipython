print(__file__)

"""filters & shutters"""

FE_shutter = MyApsPssShutterWithStatus(
    "9ida:rShtrA:", 
    "PA:09ID:STA_A_FES_OPEN_PL.VAL", 
    name="FE_shutter")

mono_shutter = MyApsPssShutterWithStatus(
    "9ida:rShtrB:", 
    "PA:09ID:STA_B_SBS_OPEN_PL.VAL",
    name="mono_shutter")

#usaxs_shutter = InOutShutter("9idb:BioEnc2B3", name="usaxs_shutter")
#ti_filter_shutter = usaxs_shutter       # alias
## a bit more complex to open ti_filter_shutter: open ALL blades

usaxs_shutter = APS_devices.EpicsOnOffShutter("9idcLAX:userTran3.A", name="usaxs_shutter")
ti_filter_shutter = usaxs_shutter       # alias


ccd_shutter = InOutShutter("9idcRIO:Galil2Bo0_CMD", name="ccd_shutter")


pf4_AlTi = DualPf4FilterBox("9idcRIO:pf4:", name="pf4_AlTi")
pf4_glass = DualPf4FilterBox("9idcRIO:pf42:", name="pf4_glass")
