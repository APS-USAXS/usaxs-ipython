print(__file__)

"""filters & shutters"""

if aps.inUserOperations:
    FE_shutter = ApsPssShutterWithStatus(
        "9ida:rShtrA:", 
        "PA:09ID:STA_A_FES_OPEN_PL.VAL", 
        name="FE_shutter")

    mono_shutter = ApsPssShutterWithStatus(
        "9ida:rShtrB:", 
        "PA:09ID:STA_B_SBS_OPEN_PL.VAL",
        name="mono_shutter")
else:
    print("!"*30)
    print("Session started when APS not operating")
    print("using simulator for FE_shutter and mono_shutter")
    print("!"*30)
    FE_shutter = APS_devices.SimulatedApsPssShutterWithStatus(name="FE_shutter")
    mono_shutter = APS_devices.SimulatedApsPssShutterWithStatus(name="mono_shutter")


#usaxs_shutter = InOutShutter("9idb:BioEnc2B3", name="usaxs_shutter")
#ti_filter_shutter = usaxs_shutter       # alias

usaxs_shutter = APS_devices.EpicsOnOffShutter("9idcLAX:userTran3.A", name="usaxs_shutter")
ti_filter_shutter = usaxs_shutter       # alias
ti_filter_shutter.delay_s = 0.2         # shutter needs some recovery time
## a bit more complex to open ti_filter_shutter: open ALL blades


# ccd_shutter = InOutShutter("9idcRIO:Galil2Bo0_CMD", name="ccd_shutter")
# also in 43-procedures.py:
#    if not ccd_shutter.is_closed:
# is changed to
#    if not ccd_shutter.isClosed:
ccd_shutter = APS_devices.EpicsOnOffShutter("9idcRIO:Galil2Bo0_CMD", name="ccd_shutter")


pf4_AlTi = DualPf4FilterBox("9idcRIO:pf4:", name="pf4_AlTi")
pf4_glass = DualPf4FilterBox("9idcRIO:pf42:", name="pf4_glass")
