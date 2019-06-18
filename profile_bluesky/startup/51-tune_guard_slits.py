print(__file__)

"""
tune the guard slits


public

    tune_Gslits()
    tune_GslitsCenter()
    tune_GslitsSize()
    GuardSlitTuneError()
    numerical_derivative()
    peak_center()

internal

    _USAXS_tune_guardSlits()
"""


class GuardSlitTuneError(RuntimeError): ...    # custom error


def numerical_derivative(x, y):
    """
    computes first derivative yp(xp) of y(x), returns tuple (xp, yp) 
    
    here, xp is at midpoints of x
    """
    if len(x) < 10:
        raise ValueError(f"Need more points to analyze, received {len(x)}")
    if len(x) != len(y):
        raise ValueError(f"X & Y arrays must be same length to analyze, x:{len(x)} y:{len(y)}")
    x1 = np.array(x[:-1])       # all but the last
    x2 = np.array(x[1:])        # all but the first
    y1 = np.array(y[:-1])       # ditto
    y2 = np.array(y[1:])
    # let numpy do this work with arrays
    xp = (x2+x1)/2              # midpoint
    yp = (y2-y1) * (x2-x1)      # slope
    return xp, yp


def peak_center(x, y, use_area=False):
    """
    calculate center-of-mass and sqrt(variance) of y vs. x
    """
    if len(x) < 10:
        raise ValueError(f"Need more points to analyze, received {len(x)}")
    if len(x) != len(y):
        raise ValueError(f"X & Y arrays must be same length to analyze, x:{len(x)} y:{len(y)}")
    
    if use_area:
        x1 = np.array(x[:-1])       # all but the last
        x2 = np.array(x[1:])        # all but the first
        y1 = np.array(y[:-1])       # ditto
        y2 = np.array(y[1:])
        
        x = (x1+x2)/2               # midpoints
        y = 0.5*(y1+y2) * (x2-x1)   # areas
    else:
        x = np.array(x)
        y = np.array(y)

    # let numpy do this work with arrays
    sum_y = y.sum()
    sum_yx = (y*x).sum()
    sum_yxx = (y*x*x).sum()
    
    x_bar = sum_yx / sum_y
    variance = sum_yxx / sum_y - x_bar*x_bar
    width = 2 * np.sqrt(abs(variance))
    return x_bar, width


def tune_GslitsCenter():
    """
    plan: optimize the guard slits' position
    """
    yield from IfRequestedStopBeforeNextScan()
    title = "tuning USAXS Gslit center"
    ts = str(datetime.datetime.now())
    yield from bps.mv(
        user_data.sample_title, title,
        user_data.state, "tune Guard slits center",
        user_data.user_name, USERNAME,
        # user_data.user_dir, ZZZZZZZZZZZ,
        user_data.spec_scan, str(RE.md["scan_id"]+1+1),     # TODO: Why SCAN_N+1?
        user_data.time_stamp, ts,
        user_data.scan_macro, "tune_GslitCenter",
        )
 
    yield from mode_USAXS()
    yield from bps.mv(
        usaxs_slit.v_size, terms.SAXS.usaxs_v_size.value,
        usaxs_slit.h_size, terms.SAXS.usaxs_h_size.value,
        )
    yield from bps.mv(ti_filter_shutter, "open")
    yield from insertTransmissionFilters()
    yield from bps.sleep(0.1)
    yield from bps.mv(
        user_data.state, "autoranging the PD",
        )
    yield from autoscale_amplifiers([upd_controls, I0_controls, I00_controls])
    yield from bps.mv(user_data.state, title)
    
    old_preset_time = scaler0.preset_time.value
    yield from bps.mv(scaler0.preset_time, 0.2)

    def tune_guard_slit_motor(motor, width, steps):
        if steps < 10:
            raise GuardSlitTuneError(f"Not enough points ({n}) to tune guard slits.")

        x_c = motor.position
        x_0 = x_c - abs(width)/2
        x_n = x_c + abs(width)/2

        tuner = APS_plans.TuneAxis([scaler0], motor)
        yield from tuner.tune(width=-width, num=steps+1)

        bluesky_runengine_running = RE.state != "idle"
        
        if bluesky_runengine_running:
            found = tuner.peak_detected()
            center = tuner.peaks.com    # center of mass

            table = pyRestTable.Table()
            table.addLabel("tune parameter")
            table.addLabel("fitted value")
            table.addRow(("peak detected?", found))
            table.addRow(("center of mass", center))
            table.addRow(("center from half max", tuner.peaks.cen))
            table.addRow(("peak max (x,y)", tuner.peaks.max))
            table.addRow(("FWHM", tuner.peaks.fwhm))
            print(table)

            def cleanup_then_GuardSlitTuneError(msg):
                print(f"{motor.name}: move to {x_c} (initial position)")
                yield from bps.mv(
                    motor, x_c,
                    scaler0.preset_time, old_preset_time,
                    ti_filter_shutter, "close"
                    )
                raise GuardSlitTuneError(msg)

            if not found:
                yield from cleanup_then_GuardSlitTuneError(f"{motor.name} Peak not found.")
            if center < x_0:      # sanity check that start <= COM
                msg = f"{motor.name}: Computed center too low: {center} < {x_0}"
                yield from cleanup_then_GuardSlitTuneError(msg)
            if center > x_n:      # sanity check that COM  <= end
                msg = f"{motor.name}: Computed center too high: {center} > {x_n}"
                yield from cleanup_then_GuardSlitTuneError(msg)
            if max(tuner.peaks.y_data) <= guard_slit.tuning_intensity_threshold:
                msg = f"{motor.name}: Peak intensity not strong enough to tune."
                msg += f" {max(tuner.peaks.y_data)} < {guard_slit.tuning_intensity_threshold}"
                yield from cleanup_then_GuardSlitTuneError(msg)

            print(f"{motor.name}: move to {center} (center of mass)")
            yield from bps.mv(motor, center)

    # Here is the MAIN EVENT
    yield from tune_guard_slit_motor(guard_slit.y, 2, 50)
    yield from tune_guard_slit_motor(guard_slit.x, 4, 20)
    
    yield from bps.mv(scaler0.preset_time, old_preset_time)
    
    yield from bps.mv(ti_filter_shutter, "close")


def _USAXS_tune_guardSlits():
    """
    plan: (internal) this performs the guard slit scan
    
    Called from tune_GslitsSize()
    """
    # # define proper counters and set the geometry... 
    # plotselect upd2
    # counters cnt_num(I0) cnt_num(upd2)
    
    # remember original motor positons
    original_position = dict(
        top = guard_slit.top.position,
        bot = guard_slit.bot.position,
        out = guard_slit.out.position,
        inb = guard_slit.inb.position,
        )
    table = pyRestTable.Table()
    table.addLabel("guard slit blade")
    table.addLabel("starting position")
    table.addRow(("top", original_position["top"]))
    table.addRow(("bottom", original_position["bot"]))
    table.addRow(("Outboard", original_position["out"]))
    table.addRow(("Inboard", original_position["inb"]))
    print(table)

    # Now move all guard slit motors back a bit
    yield from bps.mv(
        guard_slit.top, original_position["top"] + guard_slit.v_step_out,
        guard_slit.bot, original_position["bot"] - guard_slit.v_step_out,
        guard_slit.out, original_position["out"] + guard_slit.h_step_out,
        guard_slit.inb, original_position["inb"] - guard_slit.h_step_out,
        )
    
    yield from bps.mv(user_data.state, "autoranging the PD")
    yield from autoscale_amplifiers([upd_controls, I0_controls, I00_controls])

    def cleanup(msg):
        """if scan is aborted, return motors to original positions"""
        print("Returning the guard slit motors to original (pre-tune) positions")
        yield from bps.mv(
            guard_slit.top, original_position["top"],
            guard_slit.bot, original_position["bot"],
            guard_slit.out, original_position["out"],
            guard_slit.inb, original_position["inb"],
            )
        raise GuardSlitTuneError(msg)

    print("And now we can tune all of the guard slits, blade-by-blade")

    def tune_blade_edge(axis, start, end, steps, ct_time, results):
        print(f"{axis.name}: scan from {start} to {end}")
        old_ct_time = scaler0.preset_time.value
        old_position = axis.position

        yield from bps.mv(  # move to center of scan range for tune
            scaler0.preset_time, ct_time,
            axis, (start + end)/2,
            )
        scan_width = end - start
        tuner = APS_plans.TuneAxis([scaler0], axis)
        yield from tuner.tune(width=scan_width, num=steps+1)
        
        diff = abs(tuner.peaks.y_data[0] - tuner.peaks.y_data[-1])
        if diff < guard_slit.tuning_intensity_threshold:
            msg = f"{axis.name}: Not enough intensity change from first to last point."
            msg += f" {diff} < {guard_slit.tuning_intensity_threshold}."
            msg += "  Did the guard slit move far enough to move into/out of the beam?"
            msg += "  Not tuning this axis."
            yield from cleanup(msg)
        
        x, y = numerical_derivative(tuner.peaks.x_data, tuner.peaks.y_data)
        position, width = peak_center(x, y)
        width *= guard_slit.scale_factor   # expand a bit

        # Check if movement was from unblocked to blocked
        if tuner.peaks.y_data[0] > tuner.peaks.y_data[-1]:
            width *= -1     # flip the sign
        
        if position < min(start, end):
            msg = f"{axis.name}: Computed tune position {position} < {min(start, end)}."
            msg += "  Not tuning this axis."
            yield from cleanup(msg)
        if position > max(start, end):
            msg = f"{axis.name}: Computed tune position {position} > {max(start, end)}."
            msg += "  Not tuning this axis."
            yield from cleanup(msg)

        print(f"{axis.name}: will be tuned to {position}")
        print(f"{axis.name}: width = {width}")
        # TODO: SPEC comments, too
        yield from bps.mv(
            scaler0.preset_time, old_ct_time,
            axis, old_position,             # reset position for other scans
            )
        
        results["width"] = width
        results["position"] = position
  
    tunes = defaultdict(dict)
    print("*** 1. tune top guard slits")
    yield from tune_blade_edge(
        guard_slit.top, 
        original_position["top"] + guard_slit.v_step_in, 
        original_position["top"] - guard_slit.v_step_out, 
        60, 
        0.25, 
        tunes["top"])

    print("*** 2. tune bottom guard slits")
    yield from tune_blade_edge(
        guard_slit.bot, 
        original_position["bot"] - guard_slit.v_step_in, 
        original_position["bot"] + guard_slit.v_step_out, 
        60, 
        0.25, 
        tunes["bot"])

    print("*** 3. tune outboard guard slits")
    yield from tune_blade_edge(
        guard_slit.out, 
        original_position["out"] + guard_slit.h_step_in, 
        original_position["out"] - guard_slit.h_step_out, 
        60, 
        0.25, 
        tunes["out"])

    print("*** 4. tune inboard guard slits")
    yield from tune_blade_edge(
        guard_slit.inb, 
        original_position["inb"] - guard_slit.h_step_in, 
        original_position["inb"] + guard_slit.h_step_out, 
        60, 
        0.25, 
        tunes["inb"])

    # Tuning is done, now move the motors to the center of the beam found
    yield from bps.mv(
        guard_slit.top, tunes["top"]["position"],
        guard_slit.bot, tunes["bot"]["position"],
        guard_slit.out, tunes["out"]["position"],
        guard_slit.inb, tunes["inb"]["position"],
        )
    
    # redefine the motor positions so the centers are 0
    def redefine(axis, pos):
        """set motor record's user coordinate to `pos`"""
        yield from bps.mv(axis.set_use_switch, 1)
        yield from bps.mv(axis.user_setpoint, pos)
        yield from bps.mv(axis.set_use_switch, 0)

    yield from redefine(guard_slit.top, 0)
    yield from redefine(guard_slit.bot, 0)
    yield from redefine(guard_slit.out, 0)
    yield from redefine(guard_slit.inb, 0)

    # center of the slits is set to 0
    # now move the motors to the width found above
    # use average of the individual blade values.
    v = (tunes["top"]["width"] + tunes["bot"]["width"])/2
    h = (tunes["out"]["width"] + tunes["inb"]["width"])/2
    yield from bps.mv(
        guard_slit.top, v,
        guard_slit.bot, -v,
        guard_slit.out, h,
        guard_slit.inb, -h,
        )

    # sync the slits software
    yield from bps.mv(
        guard_slit.h_sync_proc, 1,
        guard_slit.v_sync_proc, 1,
        )


def tune_GslitsSize():
    """
    plan: optimize the guard slits' gap
    """
    yield from IfRequestedStopBeforeNextScan()
    yield from mode_USAXS()
    yield from bps.mv(
        usaxs_slit.v_size, terms.SAXS.usaxs_v_size.value,
        usaxs_slit.h_size, terms.SAXS.usaxs_h_size.value,
        monochromator.feedback.on, MONO_FEEDBACK_OFF,
        )
    yield from bps.mv(
        upd_controls.auto.gainU, terms.FlyScan.setpoint_up.value,
        upd_controls.auto.gainD, terms.FlyScan.setpoint_down.value,
        ti_filter_shutter, "open",
    )
    # insertCCDfilters
    yield from insertTransmissionFilters()
    yield from autoscale_amplifiers([upd_controls, I0_controls, I00_controls])
    yield from _USAXS_tune_guardSlits()
    yield from bps.mv(
        ti_filter_shutter, "close",
        terms.SAXS.guard_h_size, tune_Gslits.h_size.value,
        terms.SAXS.guard_v_size, tune_Gslits.v_size.value,
        monochromator.feedback.on, MONO_FEEDBACK_ON,
    )
    printf(f"Set V Slit={tune_Gslits.v_size.value} and H SLit={tune_Gslits.h_size.value}")


def tune_Gslits():
    """
    plan: scan and find optimal guard slit positions
    """
    yield from tune_GslitsCenter()
    yield from tune_GslitsSize()
