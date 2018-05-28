print(__file__)

"""filters & shutters"""

FE_shutter = MyApsPssShutter("9ida:rShtrA", name="FE_shutter")
# FE shutter state PV = PA:09ID:STA_A_FES_OPEN_PL.VAL

mono_shutter = MyApsPssShutter("9ida:rShtrB", name="mono_shutter")
# mono_shutter_state PV = PA:09ID:STA_B_SBS_OPEN_PL.VAL

usaxs_shutter = InOutShutter("9idb:BioEnc2B3", name="usaxs_shutter")
ti_filter_shutter = usaxs_shutter       # alias
# a bit more complex to open ti_filter_shutter: open ALL blades

ccd_shutter = InOutShutter("9idcRIO:Galil2Bo0_CMD", name="ccd_shutter")


pf4_filter_bank_A = EpicsSignal('9idcRIO:pf4:fPosA', name='pf4_filter_bank_A')
pf4_filter_bank_B = EpicsSignal('9idcRIO:pf4:fPosB', name='pf4_filter_bank_B')
