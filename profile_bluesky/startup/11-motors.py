logger.info(__file__)
# logger.debug(resource_usage(os.path.split(__file__)[-1]))

"""motors, stages, positioners, ..."""


def move_motors(*args):
    """
    move one or more motors at the same time, returns when all moves are done
    
    move_motors(m1, 0)
    move_motors(m2, 0, m3, 0, m4, 0)
    """
    status = []
    for m, v in APS_utils.pairwise(args):
        status.append(m.move(v, wait=False))
    
    for st in status:
        ophyd.status.wait(st)


class UsaxsSampleStageDevice(MotorBundle):
    """USAXS sample stage"""
    x = Component(UsaxsMotor, '9idcLAX:m58:c2:m1', labels=("sample",))
    y = Component(UsaxsMotor, '9idcLAX:m58:c2:m2', labels=("sample",))


class UsaxsDetectorStageDevice(MotorBundle):
    """USAXS detector stage"""
    x = Component(UsaxsMotorTunable, '9idcLAX:m58:c2:m3', labels=("detector", "tunable",))
    y = Component(UsaxsMotorTunable, '9idcLAX:aero:c2:m1', labels=("detector", "tunable",))


class UsaxsSlitDevice(MotorBundle):
    """
    USAXS slit just before the sample
    
    * center of slit: (x, y)
    * aperture: (h_size, v_size)
    """
    h_size = Component(UsaxsMotor, '9idcLAX:m58:c2:m8', labels=("uslit",))
    x      = Component(UsaxsMotor, '9idcLAX:m58:c2:m6', labels=("uslit",))
    v_size = Component(UsaxsMotor, '9idcLAX:m58:c2:m7', labels=("uslit",))
    y      = Component(UsaxsMotor, '9idcLAX:m58:c2:m5', labels=("uslit",))
    
    def set_size(self, *args, h=None, v=None):
        """move the slits to the specified size"""
        if h is None:
            raise ValueError("must define horizontal size")
        if v is None:
            raise ValueError("must define vertical size")
        move_motors(self.h_size, h, self.v_size, v)


class GuardSlitMotor(UsaxsMotor):
    status_update = Component(EpicsSignal, ".STUP")


class GSlitDevice(MotorBundle):
    """
    guard slit

    * aperture: (h_size, v_size)
    """
    bot  = Component(GuardSlitMotor, '9idcLAX:mxv:c0:m6', labels=("gslit",))
    inb  = Component(GuardSlitMotor, '9idcLAX:mxv:c0:m4', labels=("gslit",))
    outb = Component(GuardSlitMotor, '9idcLAX:mxv:c0:m3', labels=("gslit",))
    top  = Component(GuardSlitMotor, '9idcLAX:mxv:c0:m5', labels=("gslit",))
    x    = Component(UsaxsMotor, '9idcLAX:m58:c1:m5', labels=("gslit",))
    y    = Component(UsaxsMotor, '9idcLAX:m58:c0:m6', labels=("gslit",))

    h_size = Component(EpicsSignal, '9idcLAX:GSlit1H:size')
    v_size = Component(EpicsSignal, '9idcLAX:GSlit1V:size')

    h_sync_proc = Component(EpicsSignal, '9idcLAX:GSlit1H:sync.PROC')
    v_sync_proc = Component(EpicsSignal, '9idcLAX:GSlit1V:sync.PROC')
    
    gap_tolerance = 0.02        # actual must be this close to desired
    scale_factor = 1.2    # 1.2x the size of the beam should be good guess for guard slits.
    h_step_away = 0.2     # 0.2mm step away from beam
    v_step_away = 0.1     # 0.1mm step away from beam
    h_step_into = 1.1     # 1.1mm step into the beam (blocks the beam)
    v_step_into = 0.4     # 0.4mm step into the beam (blocks the beam)
    tuning_intensity_threshold = 500
    
    def set_size(self, *args, h=None, v=None):
        """move the slits to the specified size"""
        if h is None:
            raise ValueError("must define horizontal size")
        if v is None:
            raise ValueError("must define vertical size")
        move_motors(self.h_size, h, self.v_size, v)
    
    @property
    def h_gap_ok(self):
        gap = self.outb.position - self.inb.position
        return abs(gap - terms.SAXS.guard_h_size.value) <= self.gap_tolerance
    
    @property
    def v_h_gap_ok(self):
        gap = self.top.position - self.bot.position
        return abs(gap - terms.SAXS.guard_v_size.value) <= self.gap_tolerance
    
    @property
    def gap_ok(self):
        return self.h_gap_ok and self.v_h_gap_ok
    
    def status_update(self):
        # TODO: Did this code cause the following exception?
        #  RuntimeError: Another set() call is still in progress
        yield from bps.abs_set(self.top.status_update, 1)
        yield from bps.sleep(0.05)
        yield from bps.abs_set(self.bot.status_update, 1)
        yield from bps.sleep(0.05)
        yield from bps.abs_set(self.outb.status_update, 1)
        yield from bps.sleep(0.05)
        yield from bps.abs_set(self.inb.status_update, 1)
        yield from bps.sleep(0.05)
    

class UsaxsCollimatorStageDevice(MotorBundle):
    """USAXS Collimator (Monochromator) stage"""
    r = Component(UsaxsMotorTunable, '9idcLAX:aero:c3:m1', labels=("collimator", "tunable",))
    x = Component(UsaxsMotor, '9idcLAX:m58:c0:m2', labels=("collimator",))
    y = Component(UsaxsMotor, '9idcLAX:m58:c0:m3', labels=("collimator",))
    r2p = Component(UsaxsMotorTunable, '9idcLAX:pi:c0:m2', labels=("collimator", "tunable",))


class UsaxsCollimatorSideReflectionStageDevice(MotorBundle):
    """USAXS Collimator (Monochromator) side-reflection stage"""
    #r = Component(UsaxsMotor, '9idcLAX:xps:c0:m5', labels=("side_collimator",))
    #t = Component(UsaxsMotor, '9idcLAX:xps:c0:m3', labels=("side_collimator",))
    x = Component(UsaxsMotor, '9idcLAX:m58:c1:m1', labels=("side_collimator",))
    y = Component(UsaxsMotor, '9idcLAX:m58:c1:m2')
    rp = Component(UsaxsMotorTunable, '9idcLAX:pi:c0:m3', labels=("side_collimator", "tunable",))


class UsaxsAnalyzerStageDevice(MotorBundle):
    """USAXS Analyzer stage"""
    r = Component(UsaxsMotorTunable, '9idcLAX:aero:c0:m1', labels=("analyzer", "tunable"))
    x = Component(UsaxsMotor, '9idcLAX:m58:c0:m5', labels=("analyzer",))
    y = Component(UsaxsMotor, '9idcLAX:aero:c1:m1', labels=("analyzer",))
    z = Component(UsaxsMotor, '9idcLAX:m58:c0:m7', labels=("analyzer",))
    r2p = Component(UsaxsMotorTunable, '9idcLAX:pi:c0:m1', labels=("analyzer", "tunable"))
    rt = Component(UsaxsMotor, '9idcLAX:m58:c1:m3', labels=("analyzer",))


class UsaxsAnalyzerSideReflectionStageDevice(MotorBundle):
    """USAXS Analyzer side-reflection stage"""
    #r = Component(UsaxsMotor, '9idcLAX:xps:c0:m6', labels=("analyzer",))
    #t = Component(UsaxsMotor, '9idcLAX:xps:c0:m4', labels=("analyzer",))
    y = Component(UsaxsMotor, '9idcLAX:m58:c1:m4', labels=("analyzer",))
    rp = Component(UsaxsMotorTunable, '9idcLAX:pi:c0:m4', labels=("analyzer", "tunable"))


class SaxsDetectorStageDevice(MotorBundle):
    """SAXS detector stage (aka: pin SAXS stage)"""
    x = Component(UsaxsMotor, '9idcLAX:mxv:c0:m1', labels=("saxs",))
    y = Component(UsaxsMotor, '9idcLAX:mxv:c0:m8', labels=("saxs",))
    z = Component(UsaxsMotor, '9idcLAX:mxv:c0:m2', labels=("saxs",))


guard_slit = GSlitDevice('', name='guard_slit')
usaxs_slit = UsaxsSlitDevice('', name='usaxs_slit')
sd.baseline.append(guard_slit)
sd.baseline.append(usaxs_slit)

s_stage    = UsaxsSampleStageDevice('', name='s_stage')
d_stage    = UsaxsDetectorStageDevice('', name='d_stage')

m_stage    = UsaxsCollimatorStageDevice('', name='m_stage')
ms_stage   = UsaxsCollimatorSideReflectionStageDevice('', name='ms_stage')

a_stage    = UsaxsAnalyzerStageDevice('', name='a_stage')
as_stage   = UsaxsAnalyzerSideReflectionStageDevice('', name='aw_stage')

saxs_stage = SaxsDetectorStageDevice('', name='saxs_stage')

camy       = UsaxsMotor('9idcLAX:m58:c1:m7', name='camy')  # cam_y
tcam       = UsaxsMotor('9idcLAX:m58:c1:m6', name='tcam')  # tcam
tens       = UsaxsMotor('9idcLAX:m58:c1:m8', name='tens')  # Tension
waxsx      = UsaxsMotor('9idcLAX:m58:c0:m4', name='waxsx', labels=("waxs",))  # WAXS X
