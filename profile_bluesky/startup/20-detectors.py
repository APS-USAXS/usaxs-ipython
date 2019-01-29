print(__file__)

"""various detectors"""

# Struck/SIS 3820 Multi-channel scaler
# used with USAXS fly scans
struck = Struck3820("9idcLAX:3820:", name="struck")


SCALER_AUTOCOUNT_MODE = 1       # TODO: move to apstools

scaler0 = ScalerCH('9idcLAX:vsc:c0', name='scaler0')
# scaler1 = ScalerCH('9idcLAX:vsc:c1', name='scaler1')     # used by softGlue for SAXS transmission
# scaler2 = ScalerCH('9idcLAX:vsc:c2', name='scaler2')     # used by upstream feedback

#scaler0 = ScalerCH('9idcLAX:vsc:c0', name='scaler0')
# chan01 : sec (seconds)
# chan02 : I0 (I0)
# chan03 : I00 (I00)
# chan04 : upd2 (USAXS_PD)
# chan05 : trd (TR_diode)
# chan06 : I000 (I000)
APS_devices.use_EPICS_scaler_channels(scaler0)


# use introspection to identify channel names
if isinstance(scaler0, ScalerCH):
    for ch_attr in scaler0.channels.read_attrs:
        if ch_attr.find(".") >= 0:
            continue
        if hasattr(scaler0.channels, ch_attr):
            ch = scaler0.channels.__getattribute__(ch_attr)
            if ch.chname.value == "I0_USAXS":
                I0_SIGNAL = ch
            elif ch.chname.value == "I00_USAXS":
                I00_SIGNAL = ch
            elif ch.chname.value == "PD_USAXS":
                UPD_SIGNAL = ch
            elif ch.chname.value == "TR diode":
                TRD_SIGNAL = ch
elif isinstance(scaler0, EpicsScaler):
    for ch_attr in scaler0.channels.read_attrs:
        if hasattr(scaler0.channels, ch_attr):
            ch = scaler0.channels.__getattribute__(ch_attr)
            pv, n = ch.pvname.split(".")
            n = n[1:]
            desc = epics.caget(pv + ".NM" + n)
            if desc == "I0_USAXS":
                I0_SIGNAL = ch
            elif desc == "I00_USAXS":
                I00_SIGNAL = ch
            elif desc == "PD_USAXS":
                UPD_SIGNAL = ch
            elif desc == "TR diode":
                TRD_SIGNAL = ch


# ignore scaler 1 for now
scaler2_I000_counts = EpicsSignalRO("9idcLAX:vsc:c2.S2", name="scaler2_I000_counts")
scaler2_I000_cps = EpicsSignalRO("9idcLAX:vsc:c2_cts1.B", name="scaler2_I000_counts")


"""
REFERENCE

usaxs@usaxscontrol ~/.../startup/spec $ caget 9idcLAX:vsc:c{0,1,2}.NM{1,2,3,4,5,6,7,8}
9idcLAX:vsc:c0.NM1             seconds
9idcLAX:vsc:c0.NM2             I0_USAXS
9idcLAX:vsc:c0.NM3             I00_USAXS
9idcLAX:vsc:c0.NM4             PD_USAXS
9idcLAX:vsc:c0.NM5             TR diode
9idcLAX:vsc:c0.NM6             I000
9idcLAX:vsc:c0.NM7             
9idcLAX:vsc:c0.NM8             
9idcLAX:vsc:c1.NM1             10MHz_ref
9idcLAX:vsc:c1.NM2             I0
9idcLAX:vsc:c1.NM3             TR diode
9idcLAX:vsc:c1.NM4             
9idcLAX:vsc:c1.NM5             
9idcLAX:vsc:c1.NM6             
9idcLAX:vsc:c1.NM7             
9idcLAX:vsc:c1.NM8             
9idcLAX:vsc:c2.NM1             time
9idcLAX:vsc:c2.NM2             I000
9idcLAX:vsc:c2.NM3             
9idcLAX:vsc:c2.NM4             
9idcLAX:vsc:c2.NM5             
9idcLAX:vsc:c2.NM6             
9idcLAX:vsc:c2.NM7             
9idcLAX:vsc:c2.NM8             
"""
