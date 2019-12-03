logger.info(__file__)
# logger.debug(resource_usage(os.path.split(__file__)[-1]))

"""filters & shutters"""


if aps.inUserOperations and operations_in_9idc():
    FE_shutter = ApsPssShutterWithStatus(
        "9ida:rShtrA:", 
        "PA:09ID:STA_A_FES_OPEN_PL.VAL", 
        name="FE_shutter")

    mono_shutter = ApsPssShutterWithStatus(
        "9ida:rShtrB:", 
        "PA:09ID:STA_B_SBS_OPEN_PL.VAL",
        name="mono_shutter")

    usaxs_shutter = APS_devices.EpicsOnOffShutter(
        "9idcLAX:userTran3.A", 
        name="usaxs_shutter")

else:
    logger.warning("!"*30)
    if operations_in_9idc():
        logger.warning("Session started when APS not operating.")
    else:
        logger.warning("Session started when 9ID-C is not operating.")
    logger.warning("Using simulators for FE_shutter and mono_shutter.")
    logger.warning("!"*30)
    FE_shutter = SimulatedApsPssShutterWithStatus(name="FE_shutter")
    mono_shutter = SimulatedApsPssShutterWithStatus(name="mono_shutter")
    usaxs_shutter = SimulatedApsPssShutterWithStatus(name="usaxs_shutter")


ti_filter_shutter = usaxs_shutter       # alias
ti_filter_shutter.delay_s = 0.2         # shutter needs some recovery time


ccd_shutter = APS_devices.EpicsOnOffShutter("9idcRIO:Galil2Bo0_CMD", name="ccd_shutter")


pf4_AlTi = DualPf4FilterBox("9idcRIO:pf4:", name="pf4_AlTi")
pf4_glass = DualPf4FilterBox("9idcRIO:pf42:", name="pf4_glass")
