print(__file__)

"""
signals

from: https://subversion.xray.aps.anl.gov/spec/beamlines/USAXS/trunk/macros/local/usaxs_commands.mac
"""

MAX_EPICS_STRINGOUT_LENGTH = 40

APS = APS_devices.ApsMachineParametersDevice(name="APS")
aps_current = APS.current

mono_energy = EpicsSignal('9ida:BraggERdbkAO', name='mono_energy', write_pv="9ida:BraggEAO")
und_us_energy = EpicsSignal('ID09us:Energy', name='und_us_energy', write_pv="ID09us:EnergySet")
und_ds_energy = EpicsSignal('ID09ds:Energy', name='und_ds_energy', write_pv="ID09ds:EnergySet")

mono_feedback = DCM_Feedback("9idcLAX:fbe:omega", name="mono_feedback")
mono_temperature = EpicsSignal("9ida:DP41:s1:temp", name="mono_temperature")
cryo_level = EpicsSignal("9idCRYO:MainLevel:val", name="cryo_level")


userCalcs_lax = APS_devices.userCalcsDevice("9idcLAX:", name="userCalcs_lax")

usaxs_q_calc = APS_synApps_ophyd.swaitRecord("9idcLAX:USAXS:Q", name="usaxs_q_calc")
usaxs_q = usaxs_q_calc.val

# TODO: should these signals go into "terms" somewhere?
mr_val_center = EpicsSignal("9idcLAX:USAXS:MRcenter", name="mr_val_center")
msr_val_center = EpicsSignal("9idcLAX:USAXS:MSRcenter", name="msr_val_center")
ar_val_center = EpicsSignal("9idcLAX:USAXS:ARcenter", name="ar_val_center")
asr_val_center = EpicsSignal("9idcLAX:USAXS:ASRcenter", name="asr_val_center")


user_data = UserDataDevice(name="user_data")

email_notices = EmailNotifications()
email_notices.add_addresses(
    "ilavsky@aps.anl.gov",
    "kuzmenko@aps.anl.gov",
    "mfrith@anl.gov",
)

# TODO: should these two signals go into "terms" somewhere?
PauseBeforeNextScan = EpicsSignal("9idcLAX:USAXS:PauseBeforeNextScan", name="PauseBeforeNextScan")
StopBeforeNextScan = EpicsSignal("9idcLAX:USAXS:StopBeforeNextScan", name="StopBeforeNextScan")

# NOTE: ALL referenced PVs **MUST** exist or get() operations will fail!
terms = GeneralParameters(name="terms")

# terms.summary() to see all the fields
# terms.read() to read all the fields from EPICS
