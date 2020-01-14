logger.info(__file__)
# logger.debug(resource_usage(os.path.split(__file__)[-1]))


CT_RANGE = [0, 0, 0, 0, 0]  # Where are these values changed?


def uascan(
        motor, start, reference, finish, minStep,
        exponent, intervals, count_time,
        dy0, SDD_mm, ay0, SAD_mm,
        useDynamicTime=True,
        useIntelligentTime=True,
        md={}
    ):
    """
    USAXS ascan (step size varies with distance from a reference point)

    Why do we need to pass `motor` as a parameter?
    Will it ever be anything different?
    """
    if intervals <= 0:
        raise ValueError(f"intervals must be >0, given: {intervals}")

    # set heading for scans to show if we are running USAXS or SBUSAXS
    scan_cmd = (
        "uascan"
        f" ar {start} {reference} {finish} {minStep}"
        f" {dy0} {SDD_mm}"
        f" {ay0} {SAD_mm}"
        f" {exponent} {intervals} {count_time}"
    )

    count_time_base = count_time
    if useDynamicTime:
        count_time = count_time_base / 3
    if useIntelligentTime:
        count_time = CT_RANGE[0]
    
    # stop scaler, if it is counting
    yield from bps.mv(
        scaler.count, 0,
        scaler.preset_time, count_time,
        )

    # original values before scan
    asrp0 = as_stage.rp.position
    prescan_positions = {
        'sy' : s_stage.y.position,
        'dy' : d_stage.y.position,
        'ay' : a_stage.y.position,
        'ar' : a_stage.r.position,
        'asrp' : asrp0,
        }
    
    # devices which are recorded in the "primary" stream
    read_devices = [
        m_stage.r,
        a_stage.r,
        a_stage.y,
        s_stage.y,
        d_stage.y,
        scaler0,
        # TODO: what else?
    ]

    if terms.USAXS.useSBUSAXS.value:
        read_devices.append(as_stage.rp)
        scan_cmd = "sb" + scan_cmd
        # TODO: anything else?

    ar_series = Ustep(start, reference, finish, intervals, exponent, minStep)
    # print(f"factor={ar_series.factor} for {len(ar_series.series())} points")

    _md = OrderedDict()
    _md.update(md or {})
    _p = scan_cmd.find(" ")
    _md['plan_name'] = scan_cmd[:_p]
    _md['plan_args'] = scan_cmd[_p+1:]
    _md['uascan_factor'] = ar_series.factor
    _md['useSBUSAXS'] = str(terms.USAXS.useSBUSAXS.value)
    _md['start'] = start
    _md['center'] = reference
    _md['finish'] = finish
    _md['intervals'] = intervals
    _md['exponent'] = exponent
    _md['minStep'] = minStep
    _md['dy0'] = dy0
    _md['SDD_mm'] = SDD_mm
    _md['ay0'] = ay0
    _md['SAD_mm'] = SAD_mm
    _md['useDynamicTime'] = str(useDynamicTime)
    _md['useIntelligentTime'] = str(useIntelligentTime)

    def _triangulate_(angle, dist):
        """triangulate offset, given angle of rotation"""
        return dist * math.tan(angle*math.pi/180)
    
    @bpp.run_decorator(md=_md)
    def _scan_():
        scan_over = False

        ar0 = terms.USAXS.center.AR.value
        sy0 = s_stage.y.position
        for i, target_ar in enumerate(ar_series.stepper()):
            # track ay & dy on scattered beam position
            target_ay = ay0 + _triangulate_(target_ar-ar0, SAD_mm)
            target_dy = dy0 + _triangulate_(target_ar-ar0, SDD_mm)

            # re-position the sample before each step
            target_sy = sy0 + i*terms.USAXS.sample_y_step.value

            moves = [
                a_stage.r, target_ar,
                a_stage.y, target_ay,
                d_stage.y, target_dy,
                s_stage.y, target_sy,
            ]

            if terms.USAXS.useSBUSAXS.value:
                # adjust the ASRP piezo on the AS side-bounce stage
                tanBragg = math.tan(reference*math.pi/180)
                cosScatAngle = math.cos((reference-target_ar)*math.pi/180)
                diff = math.atan(tanBragg/cosScatAngle)*180/math.pi - reference

                # Note on asrp adjustment:  NOTE: seems wrong, but may need to be revisited???
                #   use "-" when reflecting  inboard towards storage ring (single bounce setup)
                #   use "+" when reflecting outboard towards experimenters (channel-cut setup)
                ### on 2/06/2002 Andrew realized, that we are moving in wrong direction
                    ## the sign change to - moves ASRP towards larger Bragg angles...
                    ## verified experimentally - higher voltage on piezo = lower Bragg angle...
                ## and we need to INCREASE the Bragg Angle with increasing Q, to correct for tilt down...

                asrp_vdc = asrp0 - diff/terms.usaxs.asrp_degrees_per_VDC.value
                moves += [as_stage.rp, asrp_vdc]

            # added for fuel spray users as indication that we are counting...
            moves += [fuel_spray_bit, 1]

            yield from user_data.set_state_plan(f"moving motors {i+1}/{intervals}")
            yield from bps.mv(*moves)

            # count
            yield from user_data.set_state_plan(f"counting {i+1}/{intervals}")
            yield from bps.trigger(scaler0, group="uascan_count")   # start the scaler
            yield from bps.wait(group="uascan_count")               # wait for the scaler

            # collect data for the primary stream
            yield from APS_plans.addDeviceDataAsStream(read_devices, "primary")

            if useDynamicTime:
                if i < intervals/3:
                    count_time = count_time_base / 2
                elif intervals/3 <= i < intervals * 2/3:
                    count_time = count_time_base
                else:
                    count_time = 2*count_time_base

            if useIntelligentTime:
                updRange = upd_controls.auto.lurange.value
                count_time = CT_RANGE[updRange]

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
        if terms.USAXS.useSBUSAXS.value:
            motor_resets += [as_stage.rp, prescan_positions["asrp"]]
        yield from bps.mv(*motor_resets)  # all at once

	# run the scan
    yield from _scan_()
    yield from _after_scan_()
