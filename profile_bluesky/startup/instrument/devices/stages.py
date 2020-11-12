
"""
stages
"""

__all__ = [
    's_stage',      # sample
    'd_stage',      # detector
    'm_stage',      # collimating (monochromator)
    'ms_stage',     # side-reflecting M
    'a_stage',      # analyzer
    'as_stage',     # side-reflecting A
    'saxs_stage',   # SAXS detector
    'waxsx',        # WAXS detector X translation
]

from ..session_logs import logger
logger.info(__file__)

from ophyd import Component, MotorBundle

from .usaxs_motor_devices import UsaxsMotor
from .usaxs_motor_devices import UsaxsMotorTunable


class UsaxsDetectorStageDevice(MotorBundle):
    """USAXS detector stage"""
    x = Component(
        UsaxsMotorTunable,
        '9idcLAX:m58:c2:m3',
        labels=("detector", "tunable",))
    y = Component(
        UsaxsMotorTunable,
        '9idcLAX:aero:c2:m1',
        labels=("detector", "tunable",))


class UsaxsSampleStageDevice(MotorBundle):
    """USAXS sample stage"""
    x = Component(
        UsaxsMotor,
        '9idcLAX:m58:c2:m1',
        labels=("sample",))
    y = Component(
        UsaxsMotor,
        '9idcLAX:m58:c2:m2',
        labels=("sample",))


class UsaxsCollimatorStageDevice(MotorBundle):
    """USAXS Collimator (Monochromator) stage"""
    r = Component(UsaxsMotorTunable, '9idcLAX:aero:c3:m1', labels=("collimator", "tunable",))
    x = Component(UsaxsMotor, '9idcLAX:m58:c0:m2', labels=("collimator",))
    y = Component(UsaxsMotor, '9idcLAX:m58:c0:m3', labels=("collimator",))
    r2p = Component(UsaxsMotorTunable, '9idcLAX:pi:c0:m2', labels=("collimator", "tunable",))
    isChannelCut = True


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


s_stage    = UsaxsSampleStageDevice('', name='s_stage')
d_stage    = UsaxsDetectorStageDevice('', name='d_stage')

m_stage    = UsaxsCollimatorStageDevice('', name='m_stage')
ms_stage   = UsaxsCollimatorSideReflectionStageDevice('', name='ms_stage')

a_stage    = UsaxsAnalyzerStageDevice('', name='a_stage')
as_stage   = UsaxsAnalyzerSideReflectionStageDevice('', name='as_stage')

saxs_stage = SaxsDetectorStageDevice('', name='saxs_stage')

waxsx = UsaxsMotor(
    '9idcLAX:m58:c0:m4',
    name='waxsx',
    labels=("waxs", "motor"))  # WAXS X
