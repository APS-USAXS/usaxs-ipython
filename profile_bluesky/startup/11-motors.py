print(__file__)

"""motors, stages, positioners, ..."""



# sx = EpicsMotor('9idcLAX:m58:c2:m1', name='sx')  # sx
# sy = EpicsMotor('9idcLAX:m58:c2:m2', name='sy')  # sy

class UsaxsSampleStageDevice(Device):
    """USAXS sample stage"""
    x = Component(EpicsMotor, '9idcLAX:m58:c2:m1')
    y = Component(EpicsMotor, '9idcLAX:m58:c2:m2')

sample_stage = UsaxsSampleStageDevice('', name='sample_stage')
append_wa_motor_list(sample_stage.x, sample_stage.y)


# . . . . . . . . . . . . . . . . . . . . . . . . . . . .


# dx = EpicsMotor('9idcLAX:m58:c2:m3', name='dx')  # dx
# dy = EpicsMotor('9idcLAX:aero:c2:m1', name='dy')  # dy

class UsaxsDetectorStageDevice(Device):
    """USAXS detector stage"""
    x = Component(EpicsMotor, '9idcLAX:m58:c2:m3')
    y = Component(EpicsMotor, '9idcLAX:aero:c2:m1')

detector_stage = UsaxsDetectorStageDevice('', name='detector_stage')
append_wa_motor_list(detector_stage.x, detector_stage.y)


# . . . . . . . . . . . . . . . . . . . . . . . . . . . .


# uslhap = EpicsMotor('9idcLAX:m58:c2:m8', name='uslhap')  # uslithorap
# uslhcen = EpicsMotor('9idcLAX:m58:c2:m6', name='uslhcen')  # uslithorcen
# uslvap = EpicsMotor('9idcLAX:m58:c2:m7', name='uslvap')  # uslitverap
# uslvcen = EpicsMotor('9idcLAX:m58:c2:m5', name='uslvcen')  # uslitvercen

class UsaxsSlitDevice(Device):
    """USAXS slit just before the sample"""
    hap  = Component(EpicsMotor, '9idcLAX:m58:c2:m8')
    hcen = Component(EpicsMotor, '9idcLAX:m58:c2:m6')
    vap  = Component(EpicsMotor, '9idcLAX:m58:c2:m7')
    vcen = Component(EpicsMotor, '9idcLAX:m58:c2:m5')

usaxs_slit = UsaxsSlitDevice('', name='usaxs_slit')
append_wa_motor_list(
    usaxs_slit.hcen, usaxs_slit.vcen,
    usaxs_slit.hap,  usaxs_slit.vap
)


# . . . . . . . . . . . . . . . . . . . . . . . . . . . .


# BotMS = EpicsMotor('9ida:m46', name='BotMS')  # MonoSl_bot
# InbMS = EpicsMotor('9ida:m43', name='InbMS')  # MonoSl_inb
# OutMS = EpicsMotor('9ida:m44', name='OutMS')  # MonoSl_out
# TopMS = EpicsMotor('9ida:m45', name='TopMS')  # MonoSl_top

class MonoSlitDevice(Device):
    """mono beam slit"""
    bot = Component(EpicsMotor, '9ida:m46')
    inb = Component(EpicsMotor, '9ida:m43')
    out = Component(EpicsMotor, '9ida:m44')
    top = Component(EpicsMotor, '9ida:m45')

mono_slit = MonoSlitDevice('', name='mono_slit')
append_wa_motor_list(
    mono_slit.top, mono_slit.bot,
    mono_slit.inb, mono_slit.out
)


# . . . . . . . . . . . . . . . . . . . . . . . . . . . .


# gslbot = EpicsMotor('9idcLAX:mxv:c0:m6', name='gslbot')  # GSlit_bot
# gslinb = EpicsMotor('9idcLAX:mxv:c0:m4', name='gslinb')  # GSlit_inb
# gslitx = EpicsMotor('9idcLAX:m58:c1:m5', name='gslitx')  # Gslit_X
# gslity = EpicsMotor('9idcLAX:m58:c0:m6', name='gslity')  # Gslit_Y
# gslout = EpicsMotor('9idcLAX:mxv:c0:m3', name='gslout')  # GSlit_outb
# gsltop = EpicsMotor('9idcLAX:mxv:c0:m5', name='gsltop')  # GSlit_top

class GSlitDevice(Device):
    """guard slit"""
    bot = Component(EpicsMotor, '9idcLAX:mxv:c0:m6')
    inb = Component(EpicsMotor, '9idcLAX:mxv:c0:m4')
    out = Component(EpicsMotor, '9idcLAX:mxv:c0:m3')
    top = Component(EpicsMotor, '9idcLAX:mxv:c0:m5')
    x = Component(EpicsMotor, '9idcLAX:m58:c1:m5')
    y = Component(EpicsMotor, '9idcLAX:m58:c0:m6')

guard_slit = GSlitDevice('', name='guard_slit')
append_wa_motor_list(
    guard_slit.top, guard_slit.bot,
    guard_slit.inb, guard_slit.out,
    guard_slit.x,   guard_slit.y
)


# . . . . . . . . . . . . . . . . . . . . . . . . . . . .

# mr = EpicsMotor('9idcLAX:aero:c3:m1', name='mr')  # mr
# mx = EpicsMotor('9idcLAX:m58:c0:m2', name='mx')  # mx
# my = EpicsMotor('9idcLAX:m58:c0:m3', name='my')  # my
# m2rp = EpicsMotor('9idcLAX:pi:c0:m2', name='m2rp')  # USAXS.m2rp

class UsaxsCollimatorStageDevice(Device):
    """USAXS Collimator (Monochromator) stage"""
    r = Component(EpicsMotor, '9idcLAX:aero:c3:m1')
    x = Component(EpicsMotor, '9idcLAX:m58:c0:m2')
    y = Component(EpicsMotor, '9idcLAX:m58:c0:m3')
    r2p = Component(EpicsMotor, '9idcLAX:pi:c0:m2')

m_stage = UsaxsCollimatorStageDevice('', name='m_stage')
append_wa_motor_list(
    m_stage.r, m_stage.x, m_stage.y,
    m_stage.r2p, 
)


# #msr = EpicsMotor('9idcLAX:xps:c0:m5', name='msr')  # msr
# #mst = EpicsMotor('9idcLAX:xps:c0:m3', name='mst')  # mst
# msrp = EpicsMotor('9idcLAX:pi:c0:m3', name='msrp')  # USAXS.msrp
# msx = EpicsMotor('9idcLAX:m58:c1:m1', name='msx')  # msx
# msy = EpicsMotor('9idcLAX:m58:c1:m2', name='msy')  # msy

class UsaxsCollimatorSideReflectionStageDevice(Device):
    """USAXS Collimator (Monochromator) side-reflection stage"""
    #r = Component(EpicsMotor, '9idcLAX:xps:c0:m5')
    #t = Component(EpicsMotor, '9idcLAX:xps:c0:m3')
    x = Component(EpicsMotor, '9idcLAX:m58:c1:m1')
    y = Component(EpicsMotor, '9idcLAX:m58:c1:m2')
    rp = Component(EpicsMotor, '9idcLAX:pi:c0:m3')

ms_stage = UsaxsCollimatorSideReflectionStageDevice('', name='ms_stage')
append_wa_motor_list(m_stage.x, m_stage.y, m_stage.rp)


# . . . . . . . . . . . . . . . . . . . . . . . . . . . .


# ar = EpicsMotor('9idcLAX:aero:c0:m1', name='ar')  # ar
# ax = EpicsMotor('9idcLAX:m58:c0:m5', name='ax')  # ax
# ay = EpicsMotor('9idcLAX:aero:c1:m1', name='ay')  # ay
# az = EpicsMotor('9idcLAX:m58:c0:m7', name='az')  # az
# a2rp = EpicsMotor('9idcLAX:pi:c0:m1', name='a2rp')  # USAXS.a2rp
# art = EpicsMotor('9idcLAX:m58:c1:m3', name='art')  # ART50-100

class UsaxsAnalyzerStageDevice(Device):
    """USAXS Analyzer stage"""
    r = Component(EpicsMotor, '9idcLAX:aero:c0:m1')
    x = Component(EpicsMotor, '9idcLAX:m58:c0:m5')
    y = Component(EpicsMotor, '9idcLAX:aero:c1:m1')
    z = Component(EpicsMotor, '9idcLAX:m58:c0:m7')
    r2p = Component(EpicsMotor, '9idcLAX:pi:c0:m1')
    rt = Component(EpicsMotor, '9idcLAX:m58:c1:m3')

a_stage = UsaxsAnalyzerStageDevice('', name='a_stage')
append_wa_motor_list(
    a_stage.r, 
    a_stage.x, a_stage.y, a_stage.z,
    a_stage.r2p, a_stage.rt,
)


# #asr = EpicsMotor('9idcLAX:xps:c0:m6', name='asr')  # asr
# #ast = EpicsMotor('9idcLAX:xps:c0:m4', name='ast')  # ast
# asrp = EpicsMotor('9idcLAX:pi:c0:m4', name='asrp')  # USAXS.asrp
# asy = EpicsMotor('9idcLAX:m58:c1:m4', name='asy')  # asy

class UsaxsAnalyzerSideReflectionStageDevice(Device):
    """USAXS Analyzer side-reflection stage"""
    #r = Component(EpicsMotor, '9idcLAX:xps:c0:m6')
    #t = Component(EpicsMotor, '9idcLAX:xps:c0:m4')
    y = Component(EpicsMotor, '9idcLAX:m58:c1:m4')
    rp = Component(EpicsMotor, '9idcLAX:pi:c0:m4')

as_stage = UsaxsAnalyzerStageDevice('', name='aw_stage')
append_wa_motor_list(as_stage.sy, as_stage.srp)


# . . . . . . . . . . . . . . . . . . . . . . . . . . . .

# pin_x = EpicsMotor('9idcLAX:mxv:c0:m1', name='pin_x')  # pin_x
# pin_y = EpicsMotor('9idcLAX:mxv:c0:m8', name='pin_y')  # pin_y
# pin_z = EpicsMotor('9idcLAX:mxv:c0:m2', name='pin_z')  # pin_z

class PinStageDevice(Device):
    """USAXS Pin stage"""
    x = Component(EpicsMotor, '9idcLAX:mxv:c0:m1')
    y = Component(EpicsMotor, '9idcLAX:mxv:c0:m8')
    z = Component(EpicsMotor, '9idcLAX:mxv:c0:m2')
    
pin_stage = PinStageDevice('', name='pin_stage')
append_wa_motor_list(
    pin_stage.x, pin_stage.y, pin_stage.z,
)


# . . . . . . . . . . . . . . . . . . . . . . . . . . . .

camy = EpicsMotor('9idcLAX:m58:c1:m7', name='camy')  # cam_y
tcam = EpicsMotor('9idcLAX:m58:c1:m6', name='tcam')  # tcam
tens = EpicsMotor('9idcLAX:m58:c1:m8', name='tens')  # Tension
waxsx = EpicsMotor('9idcLAX:m58:c0:m4', name='waxsx')  # WAXS X
append_wa_motor_list(camy, tcam, tens, waxsx)
