logger.info(__file__)
# logger.debug(resource_usage(os.path.split(__file__)[-1]))


CT_RANGE = [0, 0, 0, 0, 0]  # how is this used?


"""
USAXS step scan: uascan

    (base) user@host:~/.../startup/ref$ grep "^def " macros/local/usaxs_uascan.mac
    def USAXSscan '{
    def USAXSscanStep '{
    def measure_USAXS_PinT'
    def set_Filters_For_Transm '
    def resetUSAXS '{
    def uascan '
    def uascanStepFunc(x, factor, center, exponent, minStep) '{
    def uascanTestSeries(start, center, finish, numPts, factor, exponent, minStep) '{
    def uascanFindFactor(start center finish numPts exponent minStep) '{
    def _usaxs_triangulate (rot,center,dist) '{
"""


def USAXSscan(*args, **kwargs):
    """
    """
    # TODO: work-in-progress


def USAXSscanStep(*args, **kwargs):
    """
    """
    # TODO: work-in-progress


def uascan(
        motor, start, center, finish, minStep,
        dy0, SDD_mm, ay0, SAD_mm,
        exponent, intervals, count_time,
        useDynamicTime=True,
        useIntelligentTime=True,
    ):
    """
    general USAXS step scan plan

    Why do we need to pass `motor` as a parameter?
    Will it ever be anything different?
    """
    if intervals <= 0:
        raise ValueError(f"intervals must be >0, given: {intervals}")

    u = Ustep(start, center, finish, intervals, exponent, minStep)
    # print(u.factor)
    # print(u.series)

    count_time_base = count_time
    if useDynamicTime:
        count_time = count_time_base / 3
    if useIntelligentTime:
        count_time = CT_RANGE[0]

    # original values before scan
    prescan_positions = {
        'sy' : s_stage.y.position,
        'dy' : d_stage.y.position,
        'ay' : a_stage.y.position,
        'ar' : a_stage.r.position,
        'asrp' : as_stage.rp.position,
        }

    if terms.USAXS.useSBUSAXS:
        pass        # FIXME:

    def _after_scan_():
        yield from bps.mv(
            # indicate USAXS scan is not running
            terms.USAXS.scanning, 0,

            monochromator.feedback.on, MONO_FEEDBACK_ON,

            scaler0.count_mode, SCALER_AUTOCOUNT_MODE,
            upd_controls.auto.mode, "auto+background",
            I0_controls.auto.mode, "manual",
            I00_controls.auto.mode, "manual",

            # close the shutter after each scan to preserve the detector
            ti_filter_shutter, "close",
            )
        yield from user_data.set_state_plan("returning AR, AY, SY, and DY")
        motor_resets = [
            # reset motors to pre-scan positions: AY, SY, DY, and "the first motor" (AR)
            s_stage.y, prescan_positions["sy"],
            d_stage.y, prescan_positions["dy"],
            a_stage.y, prescan_positions["ay"],
            a_stage.r, prescan_positions["ar"],
        ]
        if terms.USAXS.useSBUSAXS:
            motor_resets += [as_stage.rp, prescan_positions["asrp"]]
        # reset motors to pre-scan positions: AY, SY, DY, and "the first motor" (AR)
        yield from bps.mv(*motor_resets)  # all at once

    def _scan_():
        scan_over = False
        # TODO: work-in-progress

	yield from _scan_()
    yield from _after_scan_()
