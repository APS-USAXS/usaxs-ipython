print(__file__)

"""motors, stages, positioners, ..."""


dx = EpicsMotor('9idcLAX:m58:c2:m3', name='dx')
#unused_olddy = EpicsMotor('9idcLAX:m58:c2:m4', name='unused_olddy')
append_wa_motor_list(dx)

sample_stage = UsaxsSampleStageDevice('', name='sample_stage')
append_wa_motor_list(sample_stage.x, sample_stage.y)

usaxs_slit = UsaxsSlitDevice('', name='usaxs_slit')
append_wa_motor_list(
    usaxs_slit.h0, usaxs_slit.v0,
    usaxs_slit.h_size, usaxs_slit.v_size
)
