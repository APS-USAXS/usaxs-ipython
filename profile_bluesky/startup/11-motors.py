print(__file__)

"""motors, stages, positioners, ..."""


def move_motors(*args):
    """
    move one or more motors at the same time, returns when all moves are done
    
    move_motors(m1, 0)
    move_motors(m2, 0, m3, 0, m4, 0)
    """
    status = []
    for m, v in pairwise(args):
        status.append(m.move(v))
    
    for st in status:
        ophyd.status.wait(st)


class UsaxsSampleStageDevice(MotorBundle):
    """USAXS sample stage"""
    x = Component(EpicsMotor, '9idcLAX:m58:c2:m1', labels=("sample",))
    y = Component(EpicsMotor, '9idcLAX:m58:c2:m2', labels=("sample",))

s_stage = UsaxsSampleStageDevice('', name='s_stage')



class UsaxsDetectorStageDevice(MotorBundle):
    """USAXS detector stage"""
    x = Component(EpicsMotor, '9idcLAX:m58:c2:m3', labels=("detector",))
    y = Component(EpicsMotor, '9idcLAX:aero:c2:m1', labels=("detector",))

d_stage = UsaxsDetectorStageDevice('', name='d_stage')



class UsaxsSlitDevice(MotorBundle):
    """USAXS slit just before the sample"""
    hap  = Component(EpicsMotor, '9idcLAX:m58:c2:m8', labels=("uslit",))
    hcen = Component(EpicsMotor, '9idcLAX:m58:c2:m6', labels=("uslit",))
    vap  = Component(EpicsMotor, '9idcLAX:m58:c2:m7', labels=("uslit",))
    vcen = Component(EpicsMotor, '9idcLAX:m58:c2:m5', labels=("uslit",))

usaxs_slit = UsaxsSlitDevice('', name='usaxs_slit')



class MonoSlitDevice(MotorBundle):
    """mono beam slit"""
    bot = Component(EpicsMotor, '9ida:m46', labels=("mslit",))
    inb = Component(EpicsMotor, '9ida:m43', labels=("mslit",))
    out = Component(EpicsMotor, '9ida:m44', labels=("mslit",))
    top = Component(EpicsMotor, '9ida:m45', labels=("mslit",))

mono_slit = MonoSlitDevice('', name='mono_slit')



class GSlitDevice(MotorBundle):
    """guard slit"""
    bot = Component(EpicsMotor, '9idcLAX:mxv:c0:m6', labels=("gslit",))
    inb = Component(EpicsMotor, '9idcLAX:mxv:c0:m4', labels=("gslit",))
    out = Component(EpicsMotor, '9idcLAX:mxv:c0:m3', labels=("gslit",))
    top = Component(EpicsMotor, '9idcLAX:mxv:c0:m5', labels=("gslit",))
    x = Component(EpicsMotor, '9idcLAX:m58:c1:m5', labels=("gslit",))
    y = Component(EpicsMotor, '9idcLAX:m58:c0:m6', labels=("gslit",))

guard_slit = GSlitDevice('', name='guard_slit')



class UsaxsCollimatorStageDevice(MotorBundle):
    """USAXS Collimator (Monochromator) stage"""
    r = Component(TunableEpicsMotor, '9idcLAX:aero:c3:m1', labels=("collimator", "tunable",))
    x = Component(EpicsMotor, '9idcLAX:m58:c0:m2', labels=("collimator",))
    y = Component(EpicsMotor, '9idcLAX:m58:c0:m3', labels=("collimator",))
    r2p = Component(TunableEpicsMotor, '9idcLAX:pi:c0:m2', labels=("collimator", "tunable",))

m_stage = UsaxsCollimatorStageDevice('', name='m_stage')



class UsaxsCollimatorSideReflectionStageDevice(MotorBundle):
    """USAXS Collimator (Monochromator) side-reflection stage"""
    #r = Component(EpicsMotor, '9idcLAX:xps:c0:m5', labels=("side_collimator",))
    #t = Component(EpicsMotor, '9idcLAX:xps:c0:m3', labels=("side_collimator",))
    x = Component(EpicsMotor, '9idcLAX:m58:c1:m1', labels=("side_collimator",))
    y = Component(EpicsMotor, '9idcLAX:m58:c1:m2')
    rp = Component(TunableEpicsMotor, '9idcLAX:pi:c0:m3', labels=("side_collimator", "tunable",))

ms_stage = UsaxsCollimatorSideReflectionStageDevice('', name='ms_stage')


class UsaxsAnalyzerStageDevice(MotorBundle):
    """USAXS Analyzer stage"""
    r = Component(TunableEpicsMotor, '9idcLAX:aero:c0:m1', labels=("analyzer", "tunable"))
    x = Component(EpicsMotor, '9idcLAX:m58:c0:m5', labels=("analyzer",))
    y = Component(EpicsMotor, '9idcLAX:aero:c1:m1', labels=("analyzer",))
    z = Component(EpicsMotor, '9idcLAX:m58:c0:m7', labels=("analyzer",))
    r2p = Component(TunableEpicsMotor, '9idcLAX:pi:c0:m1', labels=("analyzer", "tunable"))
    rt = Component(EpicsMotor, '9idcLAX:m58:c1:m3', labels=("analyzer",))

a_stage = UsaxsAnalyzerStageDevice('', name='a_stage')



class UsaxsAnalyzerSideReflectionStageDevice(MotorBundle):
    """USAXS Analyzer side-reflection stage"""
    #r = Component(EpicsMotor, '9idcLAX:xps:c0:m6', labels=("analyzer",))
    #t = Component(EpicsMotor, '9idcLAX:xps:c0:m4', labels=("analyzer",))
    y = Component(EpicsMotor, '9idcLAX:m58:c1:m4', labels=("analyzer",))
    rp = Component(TunableEpicsMotor, '9idcLAX:pi:c0:m4', labels=("analyzer", "tunable"))

as_stage = UsaxsAnalyzerSideReflectionStageDevice('', name='aw_stage')



class SaxsDetectorStageDevice(MotorBundle):
    """SAXS detector stage"""
    x = Component(EpicsMotor, '9idcLAX:mxv:c0:m1', labels=("saxs",))
    y = Component(EpicsMotor, '9idcLAX:mxv:c0:m8', labels=("saxs",))
    z = Component(EpicsMotor, '9idcLAX:mxv:c0:m2', labels=("saxs",))
    
saxs_stage = SaxsDetectorStageDevice('', name='saxs_stage')



camy = EpicsMotor('9idcLAX:m58:c1:m7', name='camy')  # cam_y
tcam = EpicsMotor('9idcLAX:m58:c1:m6', name='tcam')  # tcam
tens = EpicsMotor('9idcLAX:m58:c1:m8', name='tens')  # Tension
waxsx = EpicsMotor('9idcLAX:m58:c0:m4', name='waxsx', labels=("waxs",))  # WAXS X
