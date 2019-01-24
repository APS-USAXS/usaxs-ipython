print(__file__)

"""
signals

from: https://subversion.xray.aps.anl.gov/spec/beamlines/USAXS/trunk/macros/local/usaxs_commands.mac
"""

aps = APS_devices.ApsMachineParametersDevice(name="aps")
sd.baseline.append(aps)

undulator = ApsUndulatorDual("ID09", name="undulator")
sd.baseline.append(undulator)

if aps.inUserOperations:
    sd.monitors.append(aps.current)
    # suspend when current < 2 mA
    # resume 100s after current > 10 mA
    suspend_APS_current = bluesky.suspenders.SuspendFloor(aps.current, 2, resume_thresh=10, sleep=100)
    RE.install_suspender(suspend_APS_current)

    suspend_FE_shutter = bluesky.suspenders.SuspendFloor(FE_shutter.pss_state, 1)
    RE.install_suspender(suspend_FE_shutter)

    suspend_mono_shutter = bluesky.suspenders.SuspendFloor(mono_shutter.pss_state, 1)
    RE.install_suspender(suspend_mono_shutter)


class MyMonochromator(Device):
    dcm = Component(KohzuSeqCtl_Monochromator, "9ida:")
    feedback = Component(DCM_Feedback, "9idcLAX:fbe:omega")
    temperature = Component(EpicsSignal, "9ida:DP41:s1:temp")
    cryo_level = Component(EpicsSignal, "9idCRYO:MainLevel:val")


monochromator = MyMonochromator(name="monochromator")
sd.baseline.append(monochromator)


userCalcs_lax = APS_devices.userCalcsDevice("9idcLAX:", name="userCalcs_lax")

usaxs_q_calc = APS_synApps_ophyd.swaitRecord("9idcLAX:USAXS:Q", name="usaxs_q_calc")
usaxs_q = usaxs_q_calc.val

user_data = UserDataDevice(name="user_data")
sd.baseline.append(user_data)

# TODO: use APS_devices.ApsBssUserInfoDevice once we have PVs for ESAF info
bss_user_info = ApsBssUserInfoDevice("9id_bss:", name="bss_user_info")
sd.baseline.append(bss_user_info)


if False:       # TODO: needs some thought and refactoring
    # https://github.com/APS-USAXS/ipython-usaxs/issues/83
    # from: /home/beams/USAXS/spec/macros/local/usaxs_CheckBeam.mac
    # used: def chk_beam_setup   in /home/beams/USAXS/spec/macros/std/checkbeam.mac
      # this is used to set the check beam PV to use I000 PD on Mirror window, limit is set
      # in user calc. This would fail for tune_dcmth and other macros, which may take
      # the intensity there down. For that use the other macro... 
    usaxs_CheckBeamStandard = EpicsSignal(
        "9idcLAX:blCalc:userCalc1", 
        name="usaxs_CheckBeamStandard"
    )

      # this is used to set the check beam PV to use many PVs and conditions to decide, 
      # if there is chance to have beam. Uses also userCalc on lax
    usaxs_CheckBeamSpecial = EpicsSignal(
        "9idcLAX:blCalc:userCalc2", 
        name="usaxs_CheckBeamSpecial"
    )


email_notices = EmailNotifications("usaxs@aps.anl.gov")
email_notices.add_addresses(
    "ilavsky@aps.anl.gov",
    "kuzmenko@aps.anl.gov",
    "mfrith@anl.gov",
)


# NOTE: ALL referenced PVs **MUST** exist or get() operations will fail!
terms = GeneralParameters(name="terms")
sd.baseline.append(terms)

# terms.summary() to see all the fields
# terms.read() to read all the fields from EPICS
