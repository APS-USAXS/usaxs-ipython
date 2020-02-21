
"""
PSS, FE-EPS, BL-EPS, : diagnostics
"""

__all__ = [
    'diagnostics',
    ]

from ..session_logs import logger
logger.info(__file__)

import apstools.synApps
from ..framework import sd
from ophyd import Component, Device
from ophyd import EpicsSignalRO


class PSS_Parameters(Device):
    a_beam_active = Component(EpicsSignalRO, "PA:09ID:A_BEAM_ACTIVE.VAL", string=True)
    b_beam_active = Component(EpicsSignalRO, "PA:09ID:B_BEAM_ACTIVE.VAL", string=True)
    # does not connect: a_beam_ready = Component(EpicsSignalRO, "PA:09ID:A_BEAM_READY.VAL", string=True)
    b_beam_ready = Component(EpicsSignalRO, "PA:09ID:B_BEAM_READY.VAL", string=True)
    a_shutter_open_chain_A = Component(EpicsSignalRO, "PA:09ID:STA_A_FES_OPEN_PL", string=True)
    b_shutter_open_chain_A = Component(EpicsSignalRO, "PA:09ID:STA_B_FES_OPEN_PL", string=True)
    # does not connect: a_shutter_closed_chain_B = Component(EpicsSignalRO, "PB:09ID:STA_A_SBS_CLSD_PL", string=True)
    b_shutter_closed_chain_B = Component(EpicsSignalRO, "PB:09ID:STA_B_SBS_CLSD_PL", string=True)
    c_shutter_closed_chain_A = Component(EpicsSignalRO, "PA:09ID:SCS_PS_CLSD_LS", string=True)
    c_shutter_closed_chain_B = Component(EpicsSignalRO, "PB:09ID:SCS_PS_CLSD_LS", string=True)
    c_station_no_access_chain_A = Component(EpicsSignalRO, "PA:09ID:STA_C_NO_ACCESS.VAL", string=True)
    # other signals?

    @property
    def c_station_enabled(self):
        """
        look at the switches: are we allowed to operate?
    
        The PSS has a beam plug just before the C station
        
        :Plug in place:
          Cannot use beam in 9-ID-C.
          Should not use FE or mono shutters, monochromator, ti_filter_shutter...
    
        :Plug removed:
          Operations in 9-ID-C are allowed
        """
        enabled = self.c_shutter_closed_chain_A.get() == "OFF" or \
           self.c_shutter_closed_chain_A.get() == "OFF"
        return enabled


class BLEPS_Parameters(Device):
    """Beam Line Equipment Protection System"""
    red_light = Component(EpicsSignalRO, "9idBLEPS:RED_LIGHT")
    station_shutter_b = Component(EpicsSignalRO, "9idBLEPS:SBS_CLOSED", string=True)
    flow_1 = Component(EpicsSignalRO, "9idBLEPS:FLOW1_CURRENT")
    flow_2 = Component(EpicsSignalRO, "9idBLEPS:FLOW2_CURRENT")
    flow_1_setpoint = Component(EpicsSignalRO, "9idBLEPS:FLOW1_SET_POINT")
    flow_2_setpoint = Component(EpicsSignalRO, "9idBLEPS:FLOW2_SET_POINT")
    
    temperature_1_chopper = Component(EpicsSignalRO, "9idBLEPS:TEMP1_CURRENT")
    temperature_2 = Component(EpicsSignalRO, "9idBLEPS:TEMP2_CURRENT")
    temperature_3 = Component(EpicsSignalRO, "9idBLEPS:TEMP3_CURRENT")
    temperature_4 = Component(EpicsSignalRO, "9idBLEPS:TEMP4_CURRENT")
    temperature_5 = Component(EpicsSignalRO, "9idBLEPS:TEMP5_CURRENT")
    temperature_6 = Component(EpicsSignalRO, "9idBLEPS:TEMP6_CURRENT")
    temperature_7 = Component(EpicsSignalRO, "9idBLEPS:TEMP7_CURRENT")
    temperature_8 = Component(EpicsSignalRO, "9idBLEPS:TEMP8_CURRENT")
    temperature_1_chopper_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP1_SET_POINT")
    temperature_2_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP2_SET_POINT")
    temperature_3_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP3_SET_POINT")
    temperature_4_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP4_SET_POINT")
    temperature_5_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP5_SET_POINT")
    temperature_6_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP6_SET_POINT")
    temperature_7_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP7_SET_POINT")
    temperature_8_setpoint = Component(EpicsSignalRO, "9idBLEPS:TEMP8_SET_POINT")
    # other signals?
    
    # technically, these come from the FE-EPS IOC, reading signals from the BL-EPS
    shutter_permit = Component(EpicsSignalRO, "EPS:09:ID:BLEPS:SPER", string=True)
    vacuum_permit = Component(EpicsSignalRO, "EPS:09:ID:BLEPS:VACPER", string=True)
    vacuum_ok = Component(EpicsSignalRO, "EPS:09:ID:BLEPS:VAC", string=True)


class FEEPS_Parameters(Device):
    """Front End Equipment Protection System"""
    fe_permit = Component(EpicsSignalRO, "EPS:09:ID:FE:PERM", string=True)
    major_fault = Component(EpicsSignalRO, "EPS:09:ID:Major", string=True)
    minor_fault = Component(EpicsSignalRO, "EPS:09:ID:Minor", string=True)
    mps_permit = Component(EpicsSignalRO, "EPS:09:ID:MPS:RF:PERM", string=True)
    photon_shutter_1 = Component(EpicsSignalRO, "EPS:09:ID:PS1:POSITION", string=True)
    photon_shutter_2 = Component(EpicsSignalRO, "EPS:09:ID:PS2:POSITION", string=True)
    safety_shutter_1 = Component(EpicsSignalRO, "EPS:09:ID:SS1:POSITION", string=True)
    safety_shutter_2 = Component(EpicsSignalRO, "EPS:09:ID:SS2:POSITION", string=True)
    # other signals?


class DiagnosticsParameters(Device):
    """for beam line diagnostics and post-mortem analyses"""
    beam_in_hutch_swait = Component(
        apstools.synApps.SwaitRecord,
        "9idcLAX:blCalc:userCalc1")

    PSS = Component(PSS_Parameters)
    BL_EPS = Component(BLEPS_Parameters)
    FE_EPS = Component(FEEPS_Parameters)
    
    @property
    def beam_in_hutch(self):
        return self.beam_in_hutch_swait.val.get() != 0

diagnostics = DiagnosticsParameters(name="diagnostics")
sd.baseline.append(diagnostics)
