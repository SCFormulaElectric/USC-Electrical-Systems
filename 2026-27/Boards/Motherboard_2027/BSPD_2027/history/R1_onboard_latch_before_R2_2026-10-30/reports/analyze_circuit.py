#!/usr/bin/env python3
"""Deterministic analytical BSPD evidence; not SPICE or a hardware test.

Run: python3 analyze_circuit.py --spec ../circuit_spec.json
Writes circuit_analysis.json and circuit_analysis_summary.md beside this script.
All populated-part values are read by their stable role from the current spec.
"""
import argparse
import hashlib
import itertools
import json
import math
import re
from pathlib import Path

ASSUMPTIONS = {
    "board_temperature_C": [-20.0, 85.0],
    "reference_temperature_C": 25.0,
    "resistor_TCR_bound_ppm_per_C": 100.0,
    "reference_initial_tolerance": 0.001,
    "reference_TCR_bound_ppm_per_C": 100.0,
    "comparator_offset_bound_V": 0.0055,
    "comparator_input_outward_bias_bound_A": 50e-9,
    "timer_FET_sink_leakage_bound_A": 10e-6,
    "timer_C_positive_temperature_change": 0.15,
    "timer_C_negative_temperature_change": -0.15,
    "timer_half_initial_ratio_relative_bound": 0.001,
    "external_relay_and_output_budget_s": 0.020,
    "input_filter_and_sensor_budget_s": 0.002,
    "motherboard_input_load_ohm": 24000.0,
    "PNP_source_drop_assumed_V": [0.05, 0.30],
    "current_sensor_supply_V": [4.75, 5.25],
    "current_sensor_offset_nominal_V": 2.5,
    "current_sensor_channel2_gain_V_per_A": 0.010,
    "current_sensor_channel2_range_A": [-200.0, 200.0],
    "current_sensor_channel2_offset_bound_A": 1.5,
    "current_sensor_channel2_gain_relative_bound": 0.012,
    "current_sensor_linearity_assumed_bound_A": 1.0,
    "current_sensor_ratiometric_relative_bound": 0.006,
    "current_sensor_noise_conservative_bound_V": 0.010,
    "current_sensor_output_resistance_bound_ohm": 10.0,
    "TS_nominal_voltage_assumed_V": 360.0,
    "target_raw_GLV_range_V_tentative": [11.5, 16.0],
    "power_criterion_W": 5000.0,
    "AiM_brake_output_nominal_V": [1.0, 5.0],
    "logic_supply_assumed_V": [4.75, 5.25],
    "comparator_output_LOW_for_nominal_model_V": 0.0,
    "comparator_output_LOW_upper_bound_V": 0.55,
    "startup_cap_initial_tolerance_assumed": 0.10,
    "startup_cap_temperature_bound_assumed": 0.15,
    "startup_cap_DC_bias_min_multiplier_assumed": 0.80,
    "HC132_positive_threshold_fraction_envelope": [0.35, 0.75],
    "HC132_negative_threshold_fraction_envelope": [0.15, 0.50],
    "HC74_recovery_conservative_bound_s": 45e-9,
    "HC74_CLR_guaranteed_HIGH_fraction": 0.70,
    "fault_bus_release_budget_assumed_s": 10e-6,
    "conceptual_trace_step_s": 0.00025,
}

SOURCES = {
    "LM2901B": "https://www.ti.com/lit/ds/symlink/lm339.pdf",
    "LM4040": "https://www.ti.com/lit/ds/symlink/lm4040-n.pdf",
    "HC132": "https://assets.nexperia.com/documents/data-sheet/74HC_HCT132.pdf",
    "HC74": "https://assets.nexperia.com/documents/data-sheet/74HC_HCT74.pdf",
    "DHAB_S134": "https://www.lem.com/sites/default/files/products_datasheets/dhab_s_134.pdf",
    "BAT54S": "https://assets.nexperia.com/documents/data-sheet/BAT54S.pdf",
    "BAV199_candidate": "https://assets.nexperia.com/documents/data-sheet/BAV199.pdf",
    "Microchip_MCP809": "https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/11194c.pdf",
    "AiM_0_135bar": "https://www.aim-sportline.com/download/doc/eng/sensors/oldies/Datasheet_BrakePressure0-2000PSI_101_eng.pdf",
}


def si_value(text):
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*([pnumkKM]?)", text)
    if not m:
        raise ValueError("Cannot parse value: " + text)
    return float(m.group(1)) * {"": 1, "p": 1e-12, "n": 1e-9,
        "u": 1e-6, "m": 1e-3, "k": 1e3, "K": 1e3, "M": 1e6}[m.group(2)]


def tolerance(text, default=None):
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if m:
        return float(m.group(1)) / 100
    if default is None:
        raise ValueError("Missing explicit tolerance: " + text)
    return default


def divider(v, top, bottom):
    return v * bottom / (top + bottom)


def parallel(a, b):
    return a * b / (a + b)


def corner_extrema(func, ranges, names):
    points = [(func(*p), dict(zip(names, p))) for p in itertools.product(*ranges)]
    lo, hi = min(points, key=lambda p: p[0]), max(points, key=lambda p: p[0])
    return {"min": lo[0], "max": hi[0], "min_corner": lo[1], "max_corner": hi[1],
            "corners_evaluated": len(points)}


def trip_raw(vtrip, vo, rs, rg, ri, rf, rout=0, direct_inject=0, cmp_inject=0):
    """Exact DC nodal threshold including feedback loading on the input divider."""
    gain = rg / (rs + rout + rg)
    rth = parallel(rs + rout, rg)
    return (vtrip + (ri + rth) * (vtrip - vo) / rf
            - (ri + rth) * cmp_inject - rth * direct_inject) / gain


def solve_linear(matrix, rhs):
    """Small Gaussian elimination used for an independent DC nodal check."""
    rows = [list(a)+[b] for a,b in zip(matrix,rhs)]
    n=len(rows)
    for j in range(n):
        k=max(range(j,n),key=lambda i:abs(rows[i][j]))
        rows[j],rows[k]=rows[k],rows[j]
        pivot=rows[j][j]
        rows[j]=[x/pivot for x in rows[j]]
        for i in range(n):
            if i!=j:
                scale=rows[i][j]
                rows[i]=[a-scale*b for a,b in zip(rows[i],rows[j])]
    return [row[-1] for row in rows]


def nodal_check(vraw,rs,rg,ri,rf,rp,high=False):
    if not high:
        sense,cmp=solve_linear([[1/rs+1/rg+1/ri,-1/ri],[-1/ri,1/ri+1/rf]],[vraw/rs,0])
        return {"SENSE_V":sense,"CMP_V":cmp,"OUT_V":0}
    sense,cmp,out=solve_linear([[1/rs+1/rg+1/ri,-1/ri,0],[-1/ri,1/ri+1/rf,-1/rf],[0,-1/rf,1/rf+1/rp]],
        [vraw/rs,0,5/rp])
    return {"SENSE_V":sense,"CMP_V":cmp,"OUT_V":out}


def timer_delay(r, c, vref, half_fraction, offset=0, sink=0, half_bias=0):
    final = vref - r * sink
    threshold = vref * half_fraction + offset + half_bias
    if final <= threshold:
        return math.inf
    return r * c * math.log(final / (final - threshold))


def conceptual_trace(name, segments, timer_r, timer_c, start_r, start_c, fault_pullup_r):
    """Ideal digital latch plus first-order timer/POR nodes; not transistor simulation."""
    step = ASSUMPTIONS["conceptual_trace_step_s"]
    timer_v = start_rc = 0.0
    start_schmitt = boot_clock = arm_once = permit = False
    elapsed = 0.0
    events = []
    for duration, por_n, sensor_ok, current_high, brake_high in segments:
        count = int(round(duration / step))
        for _ in range(count):
            before = (permit, arm_once, boot_clock)
            elapsed += step
            if current_high and brake_high:
                timer_v = 5.0 + (timer_v - 5.0) * math.exp(-step / (timer_r * timer_c))
            else:
                timer_v = 0.0  # Ideal active reset: incomplete physical reset is not simulated.
            fault_ok_ideal = bool(por_n and sensor_ok and timer_v < 2.5)
            target = 5.0 if fault_ok_ideal else 0.0
            tau = (start_r + fault_pullup_r) * start_c if fault_ok_ideal else start_r * start_c
            start_rc = target + (start_rc - target) * math.exp(-step / tau)
            fault_voltage = ((5.0*start_r+start_rc*fault_pullup_r)/(start_r+fault_pullup_r)) if fault_ok_ideal else 0.0
            prior_boot, prior_arm = boot_clock, arm_once
            if not start_schmitt and start_rc >= 0.5 * 5:
                start_schmitt = True
            elif start_schmitt and start_rc <= 0.3 * 5:
                start_schmitt = False
            boot_clock = bool(por_n and start_schmitt)
            if not por_n:
                arm_once = False
            elif boot_clock and not prior_boot:
                arm_once = True
            clear_n = fault_ok_ideal  # Traces use ideal logic; separate corner model checks CLR margins.
            if not clear_n:
                permit = False
            elif arm_once and not prior_arm:
                permit = True
            if before != (permit, arm_once, boot_clock):
                events.append({"t_s": round(elapsed, 6), "POR_N": por_n,
                    "sensor_ok": sensor_ok, "C_HIGH": current_high, "B_HARD": brake_high,
                    "FAULT_OK": clear_n, "FAULT_OK_voltage_V":fault_voltage,
                    "START_RC_V":start_rc,"BOOT_CLK":boot_clock,"ARM_CLK": arm_once, "PERMIT": permit,
                    "timer_V": timer_v})
        events.append({"t_s": round(elapsed, 6), "segment_end": True,
            "PERMIT": permit, "ARM_CLK": arm_once,"BOOT_CLK":boot_clock,"timer_V": timer_v})
    return {"name": name, "events": events, "final_permit": permit,
        "model_limitations": ["Ideal asynchronous clear and output stage",
        "No metastability, comparator propagation, input-clamp behavior, sensor dynamics or relay model",
        "Two-stageARM_ONCE modeled; actual CLRrelease/clock margin is checked separately",
        "Timer reset forced to zero; physical residual charge needs testing",
        "Threshold fractions for traces are illustrative midrange values"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=Path(__file__).resolve().parent.parent / "circuit_spec.json")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "circuit_analysis.json")
    args = parser.parse_args()
    raw = args.spec.read_bytes()
    spec = json.loads(raw)
    roles = {p["role"]: p for p in spec["parts"]}
    r = lambda role: si_value(roles[role]["value"])
    temp_span = max(abs(t - ASSUMPTIONS["reference_temperature_C"])
                    for t in ASSUMPTIONS["board_temperature_C"])
    tcr = ASSUMPTIONS["resistor_TCR_bound_ppm_per_C"] * 1e-6 * temp_span
    ref_error = ASSUMPTIONS["reference_initial_tolerance"] + ASSUMPTIONS["reference_TCR_bound_ppm_per_C"] * 1e-6 * temp_span
    refs = [5 * (1 - ref_error), 5 * (1 + ref_error)]
    def rb(role):
        p = roles[role]
        v, tol = si_value(p["value"]), tolerance(p["value"])
        return [v * (1 - tol) * (1 - tcr), v * (1 + tol) * (1 + tcr)]
    voff = ASSUMPTIONS["comparator_offset_bound_V"]
    bias = ASSUMPTIONS["comparator_input_outward_bias_bound_A"]
    topology = {
        "latch_clear_fault_bus": roles["hardware_trip_latch"]["pins"].get("1") == "FAULT_OK",
        "latch_D_high": roles["hardware_trip_latch"]["pins"].get("2") == "V5",
        "latch_clock_startup_only": roles["hardware_trip_latch"]["pins"].get("3") == "ARM_CLK",
        "ARM_ONCE_Q_drives_main_clock":roles["hardware_trip_latch"]["pins"].get("9") == "ARM_CLK",
        "ARM_ONCE_clock_BOOT":roles["hardware_trip_latch"]["pins"].get("11") == "BOOT_CLK",
        "ARM_ONCE_D_high":roles["hardware_trip_latch"]["pins"].get("12") == "V5",
        "ARM_ONCE_CLR_POR":roles["hardware_trip_latch"]["pins"].get("13") == "POR_N",
        "START_RC_source_FAULT_OK":roles["arm_clock_delay"]["pins"].get("1") == "FAULT_OK",
        "current_reference_still_absolute_REF5":roles["current_set_top"]["pins"].get("1") == "REF5",
        "NAND_current_brake": roles["coincidence_logic"]["pins"].get("1") == "C_HIGH"
            and roles["coincidence_logic"]["pins"].get("2") == "B_HARD",
        "timer_ref_correlated": roles["timer_charge"]["pins"].get("1") == "REF5"
            and roles["timer_half_top"]["pins"].get("1") == "REF5",
    }
    if not all(topology.values()):
        raise ValueError("Topology changed; review model before regenerating evidence: " + repr(topology))

    thresholds = {}
    for prefix in ["current", "brake"]:
        vthreshold = divider(5, r(prefix + "_set_top"), r(prefix + "_set_bottom"))
        rs, rg = r(prefix + "_series"), r(prefix + "_open_bias")
        ri, rf, rp = r(prefix + "_hysteresis_input"), r(prefix + "_hysteresis_feedback"), r(prefix + "_pullup")
        high = (rf * 5 + rp * vthreshold) / (rf + rp)
        rise = trip_raw(vthreshold, 0, rs, rg, ri, rf)
        fall = trip_raw(vthreshold, high, rs, rg, ri, rf)
        input_roles = [prefix + suffix for suffix in ["_series", "_open_bias", "_hysteresis_input",
            "_hysteresis_feedback", "_set_top", "_set_bottom"]]
        def threshold_corner(a, b, c, d, top, bot, ref, offset, low, source_r, minus_bias, sense_bias, plus_bias):
            actual_reference = divider(ref, top, bot) + parallel(top, bot) * minus_bias
            return trip_raw(actual_reference + offset, low, a, b, c, d, source_r, sense_bias, plus_bias)
        ranges = [rb(role) for role in input_roles] + [refs, [-voff, voff], [0, 0.55],
            [0, ASSUMPTIONS["current_sensor_output_resistance_bound_ohm"] if prefix == "current" else 0],
            [0, bias], [0, 2*bias], [0, bias]]
        names = input_roles + ["reference_V", "comparator_offset_V", "output_LOW_V", "sensor_Rout_ohm",
            "threshold_input_outward_A", "direct_sense_outward_A", "plus_input_outward_A"]
        bounds = corner_extrema(threshold_corner, ranges, names)
        thresholds[prefix] = {"setpoint_comparator_V": vthreshold, "input_gain": rg/(rs+rg),
            "input_Thevenin_ohm": parallel(rs, rg), "loaded_HIGH_at_switch_V": high,
            "raw_rising_V": rise, "raw_falling_V": fall, "raw_hysteresis_V": rise - fall,
            "rising_corner_bound_without_clamp_leakage_V": bounds,
            "bound_exclusions": ["Input clamp leakage", "Reference load regulation and thermal self-heating",
                "PCB leakage", "Sensor transfer error", "Actual resistor TCR certificates"]}
        rising_nodes=nodal_check(rise,rs,rg,ri,rf,rp)
        falling_nodes=nodal_check(fall,rs,rg,ri,rf,rp,True)
        residual=max(abs(rising_nodes["CMP_V"]-vthreshold),abs(falling_nodes["CMP_V"]-vthreshold))
        if residual>1e-10:
            raise AssertionError("Independent nodal threshold check failed: "+prefix)
        thresholds[prefix]["independent_nodal_verification"]={"rising_nodes":rising_nodes,
            "falling_nodes":falling_nodes,"maximum_threshold_residual_V":residual,"passed":True}
        windows = {}
        for limit in ["low", "high"]:
            top_role, bottom_role = prefix + "_" + limit + "_top", prefix + "_" + limit + "_bottom"
            nominal = divider(5, r(top_role), r(bottom_role)) / (rg/(rs+rg))
            def win(a, b, top, bot, ref, offset):
                return (divider(ref, top, bot)+offset)/(b/(a+b))
            corners = corner_extrema(win, [rb(prefix+"_series"), rb(prefix+"_open_bias"), rb(top_role), rb(bottom_role), refs, [-voff,voff]],
                ["series_ohm", "ground_ohm", "threshold_top_ohm", "threshold_bottom_ohm", "reference_V", "offset_V"])
            windows[limit] = {"nominal_raw_V": nominal, "corner_bound_without_bias_or_leak_V": corners}
        thresholds[prefix]["fault_window"] = windows
    thresholds["current"]["nominal_rising_current_A_at_Uc5"] = (thresholds["current"]["raw_rising_V"]-2.5)/.010
    thresholds["current"]["nominal_hysteresis_A_at_Uc5"] = thresholds["current"]["raw_hysteresis_V"]/.010

    half = r("timer_half_bottom")/(r("timer_half_top")+r("timer_half_bottom"))
    half_rth = parallel(r("timer_half_top"), r("timer_half_bottom"))
    def uv(top, bot, vref, half_top, half_bot, offset):
        return (divider(vref, half_top, half_bot)+offset)/(bot/(top+bot))
    uv_bounds = corner_extrema(uv, [rb("undervoltage_top"), rb("undervoltage_bottom"), refs,
        rb("timer_half_top"), rb("timer_half_bottom"), [-voff,voff]],
        ["UV_top_ohm", "UV_bottom_ohm", "correlated_reference_V", "half_top_ohm", "half_bottom_ohm", "offset_V"])
    uv_nom = 5*half/(r("undervoltage_bottom")/(r("undervoltage_top")+r("undervoltage_bottom")))

    cnom = r("timer_cap")
    ctol = tolerance(roles["timer_cap"]["value"])
    cmax = cnom*(1+ctol)*(1+ASSUMPTIONS["timer_C_positive_temperature_change"])
    half_fractions = [rb("timer_half_bottom")[0]/(rb("timer_half_top")[1]+rb("timer_half_bottom")[0]),
        rb("timer_half_bottom")[1]/(rb("timer_half_top")[0]+rb("timer_half_bottom")[1])]
    timer_bounds = corner_extrema(timer_delay, [rb("timer_charge"), [cnom,cmax], refs, half_fractions,
        [-voff,voff], [0,ASSUMPTIONS["timer_FET_sink_leakage_bound_A"]+bias], [0,half_rth*(1+0.001)*(1+tcr)*bias]],
        ["R_ohm", "C_F", "correlated_reference_V", "half_fraction", "offset_V", "sink_A", "half_input_bias_V"])
    timer_max = timer_bounds["max"]
    total_budget = timer_max+ASSUMPTIONS["external_relay_and_output_budget_s"]+ASSUMPTIONS["input_filter_and_sensor_budget_s"]
    timer = {"nominal_s": timer_delay(r("timer_charge"),cnom,5,half),
        "C_max_F": cmax, "reference_V_range_correlated_in_model": refs,
        "half_fraction_with_independent_resistor_TCR": half_fractions,
        "corner_bound_s": timer_bounds, "total_including_assumed_sensor_relay_budget_s": total_budget,
        "500ms_margin_s": .5-total_budget, "passes_analytical_500ms_budget": total_budget < .5,
        "limitations": ["Evaluated minimum is not a physical lower timing guarantee: DC bias and aging can reduce C further",
            "Uses assumed 100 ppm/C resistor bounds; actual procurement data must agree",
            "10 uA FET leakage is a conservative 125C allowance; board target ends at85C",
            "Capacitor leakage/PCB contamination and extra negative current are not separately bounded",
            "Relay release budget must be measured with the installed suppression circuit"]}

    rload=parallel(ASSUMPTIONS["motherboard_input_load_ohm"],r("output_default_low"))
    ratio=rload/(rload+r("output_short_limit"))
    output_rows=[]
    for vp in [uv_nom,12.0,16.0]:
        for drop in ASSUMPTIONS["PNP_source_drop_assumed_V"]:
            vout=(vp-drop)*ratio
            output_rows.append({"VP_V":vp,"PNP_drop_assumed_V":drop,"BSPD_signal_V":vout,
                "motherboard_gate_V":vout/2,"source_current_A":vout/rload,
                "series_R_short_power_W":(vp-drop)**2/r("output_short_limit")})

    arm_r=r("arm_clock_delay");arm_c=r("arm_clock_delay_cap");fault_r=r("fault_bus_pullup")
    arm_tau=(arm_r+fault_r)*arm_c
    arm_cmin=arm_c*(1-ASSUMPTIONS["startup_cap_initial_tolerance_assumed"])*(1-ASSUMPTIONS["startup_cap_temperature_bound_assumed"])*ASSUMPTIONS["startup_cap_DC_bias_min_multiplier_assumed"]
    arm_cmax=arm_c*(1+ASSUMPTIONS["startup_cap_initial_tolerance_assumed"])*(1+ASSUMPTIONS["startup_cap_temperature_bound_assumed"])
    fmin,fmax=ASSUMPTIONS["HC132_positive_threshold_fraction_envelope"]
    def clk_delay(rs,rp,c,f):return -(rs+rp)*c*math.log(1-f)
    arm_bounds=corner_extrema(clk_delay,[rb("arm_clock_delay"),rb("fault_bus_pullup"),[arm_cmin,arm_cmax],[fmin,fmax]],
        ["START_series_ohm","FAULT_pullup_ohm","C_F","Schmitt_positive_fraction"])
    arm_min,arm_max=arm_bounds["min"],arm_bounds["max"]
    def clr_margin(rs,rp,c,f):
        tau=(rs+rp)*c
        k=rp/(rs+rp)
        clr_high=ASSUMPTIONS["HC74_CLR_guaranteed_HIGH_fraction"]
        release=0 if 1-k>=clr_high else tau*math.log(k/(1-clr_high))
        return clk_delay(rs,rp,c,f)-release-ASSUMPTIONS["fault_bus_release_budget_assumed_s"]
    clr_bounds=corner_extrema(clr_margin,[rb("arm_clock_delay"),rb("fault_bus_pullup"),[arm_cmin,arm_cmax],[fmin,fmax]],
        ["START_series_ohm","FAULT_pullup_ohm","C_F","Schmitt_positive_fraction"])
    fault_at_earliest=1-fault_r/(fault_r+arm_r)*(1-fmin)
    startup={"two_stage_ARM_ONCE":True,"nominal_coupled_RC_tau_s":arm_tau,
        "clock_after_FAULT_OK_release_min_s":arm_min,"clock_after_FAULT_OK_release_max_s":arm_max,
        "coupled_clock_corner_bound_s":arm_bounds,
        "nominal_FAULT_fraction_at_earliest_Schmitt_clock":fault_at_earliest,
        "conservative_CLR_release_to_CLOCK_margin_s":clr_bounds["min"],"CLR_to_CLOCK_corner_bound_s":clr_bounds,
        "recovery_time_budget_s":ASSUMPTIONS["HC74_recovery_conservative_bound_s"],
        "passes_assumed_CLR_recovery_budget":clr_bounds["min"]>ASSUMPTIONS["HC74_recovery_conservative_bound_s"],
        "qualification": "FAULTpullup andSTARTseriesR both determineC14charge. Schmittfraction envelope covers tabulated2/4.5/6Vbounds; interpolation,C14minimumC,faultbusrelease requireverification.",
        "MCP809_post_recovery_reset_time_s":{"min":0.150,"typical":0.350,"max":0.700},
        "MCP809T_450_trip_V":{"min":4.25,"typical":4.375,"max":4.50},
        "MCP809_reset_delay_source": SOURCES["Microchip_MCP809"]}

    healthy=(True,True,False,False)
    trace=lambda name,segments:conceptual_trace(name,segments,r("timer_charge"),cnom,arm_r,arm_c,fault_r)
    traces=[trace("startup_healthy",[(.2,False,True,False,False),(.1,*healthy)]),
        trace("current_only_no_trip",[(.2,False,True,False,False),(.1,*healthy),(.6,True,True,True,False)]),
        trace("brake_only_no_trip",[(.2,False,True,False,False),(.1,*healthy),(.6,True,True,False,True)]),
        trace("coincidence_trip_remains_latched_after_release",[(.2,False,True,False,False),(.1,*healthy),(.4,True,True,True,True),(.2,*healthy)]),
        trace("short_coincidence_resets_timer",[(.2,False,True,False,False),(.1,*healthy),(.1,True,True,True,True),(.2,*healthy)]),
        trace("sensor_fault_immediate_then_no_rearm",[(.2,False,True,False,False),(.1,*healthy),(.02,True,False,False,False),(.2,*healthy)]),
        trace("initial_sensor_late_becomes_ready_and_arms_once",[(.2,False,False,False,False),(.1,True,False,False,False),(.2,*healthy)]),
        trace("brownout_recovery_locally_rearms",[(.2,False,True,False,False),(.1,*healthy),(.2,False,True,False,False),(.2,*healthy)])]
    expected=[True,True,True,False,True,False,True,True]
    for trace,wanted in zip(traces,expected):
        trace["expected_final_permit"] = wanted
        trace["conceptual_expectation_passed"] = trace["final_permit"] == wanted

    i5=ASSUMPTIONS["power_criterion_W"]/ASSUMPTIONS["TS_nominal_voltage_assumed_V"]
    ucmin,ucmax=ASSUMPTIONS["current_sensor_supply_V"]
    highraw=thresholds["current"]["fault_window"]["high"]["nominal_raw_V"]
    sensor={"I_at_5kW_nominal_TS_A":i5,"ideal_5kW_output_at_Uc_min_V":ucmin/5*(2.5+.01*i5),
        "ideal_zero_output_at_Uc_max_V":ucmax/5*2.5,
        "fixed_threshold_zero_vs_5kW_intervals_overlap":ucmax/5*2.5 > ucmin/5*(2.5+.01*i5),
        "nominal_threshold_current_A_by_Uc":{str(uc): (thresholds["current"]["raw_rising_V"]*5/uc-2.5)/.01 for uc in [ucmin,5.0,ucmax]},
        "channel2_plus200A_at_Uc5p25_raw_V":ucmax/5*(2.5+.01*200),
        "current_high_fault_threshold_nominal_raw_V":highraw,
        "nominal_high_fault_current_A_at_Uc5p25":(highraw*5/ucmax-2.5)/.01,
        "full_channel2_plus200A_valid_with_current_fault_window":ucmax/5*(2.5+.01*200)<highraw,
        "overload_clamp_min_at_Uc5p25_V":4.7*ucmax/5,
        "limitations": ["TS maximum voltage remains unconfirmed; nominal360V is not a maximum-voltage calibration",
            "Linearity error is specified at25C; extending it tofull temperature is an explicit assumption",
            "No Orion rail tolerance is established by a nominal5V label",
            "No input-voltage window alone distinguishes all sensor-supply/ground-wire faults"]}
    sensor["ratiometric_normalized_5V_error_example"]={
        "zero_max_V":(2.5+.01*1.5)*1.006+.010*5/ucmin,
        "5kW_min_V_assuming_linearity_bound_at_all_temperatures":(2.5+.01*(i5*.988-1.5-1.0))*.994-.010*5/ucmin,
        "status":"Illustrative assumed sensor-error model; not a validated full-temperature guarantee"}

    uv_gain=r("undervoltage_bottom")/(r("undervoltage_top")+r("undervoltage_bottom"))
    uv_bias_margin=(half_rth+parallel(r("undervoltage_top"),r("undervoltage_bottom")))*bias/uv_gain
    uv_min_with_bias=uv_bounds["min"]-uv_bias_margin
    uv_max_with_bias=uv_bounds["max"]+uv_bias_margin
    results={"analysis_type":"Deterministic analytical nodal/corner and conceptual state model; NOT SPICE or hardware evidence",
        "spec_path":str(args.spec.resolve()),"spec_sha256":hashlib.sha256(raw).hexdigest(),"part_count":len(spec["parts"]),
        "release_status":"ENGINEERING_REVIEW_CALIBRATION_PENDING", "assumptions":ASSUMPTIONS,"sources":SOURCES,
        "topology_checks":topology,"thresholds":thresholds,"UV":{"nominal_VP_cutoff_V":uv_nom,"corner_bound_V":uv_bounds,
            "additional_conservative_input_bias_VP_budget_V":uv_bias_margin,
            "VP_cutoff_range_including_bias_budget_V":[uv_min_with_bias,uv_max_with_bias],
            "raw_VIN_equation":"VIN = VP + SS14 forward drop; actual drop is not established",
            "raw_VIN_cutoff_lower_bound_without_relying_on_minimum_diode_drop_V":uv_min_with_bias,
            "AiM_nominal_10V_min_supply_margin_V":uv_min_with_bias-10,
            "diode_drop_max_to_guarantee_target_raw_GLV_min_operation_V":ASSUMPTIONS["target_raw_GLV_range_V_tentative"][0]-uv_max_with_bias,
            "inlet_diode_loss_not_included_in_VP_bounds":True},
        "output":{"parallel_load_ohm":rload,"nominal_source_to_signal_ratio":ratio,"rows":output_rows},
        "timer":timer,"startup":startup,"conceptual_functional_traces":traces,"current_sensor_constraints":sensor,
        "clamp_selected":roles["current_input_clamp"]["value"],
        "hard_release_blockers":["Unknown Orion sensor5V rail; unusedJ1pin1sensewire decision is not approved in thissnapshot",
            "FixedCH2 threshold cannot guaranteehealthy0A and5kW over full4.75-5.25V supplyrange",
            "Actual brake hard-braking hydraulic calibration pending",
            "Clamp leakage and sustainednegative/unpoweredfault behavior pendingphysicalqualification",
            "Relay/suppression release time and permittedbrownout/powercycle behavior pendingqualification"]+([] if startup["passes_assumed_CLR_recovery_budget"] else ["START_RCloadsFAULTpullup; earliestclockcanprecede guaranteedmainCLRrelease. IncreaseSTARTseriesR(e.g47k) andrerun."]),
        "not_measured":["Actual board", "SPICE transistor model", "Relay contacts", "Sensor voltages/currents", "Thermal chamber behavior", "Negative input fault behavior"]}
    args.output.write_text(json.dumps(results,indent=2,allow_nan=False)+"\n")
    summary=args.output.with_name("circuit_analysis_summary.md")
    summary.write_text(f"""# Reproducible analytical circuit evidence

This is an analytical model, **not SPICE or hardware validation**. It reads the latest circuit spec by component role. Reviewed input SHA-256: `{results['spec_sha256']}`; parts: {results['part_count']}.

Regenerate with `python3 reports/analyze_circuit.py --spec circuit_spec.json` from the review directory. The JSON records all assumptions, corner witnesses, sources and conceptual traces.

| Quantity | Calculated result |
|---|---:|
| Current raw rising / falling point | {thresholds['current']['raw_rising_V']:.6f} / {thresholds['current']['raw_falling_V']:.6f} V |
| Current nominal rising at exact5V supply | {thresholds['current']['nominal_rising_current_A_at_Uc5']:.3f} A |
| Current raw hysteresis / channel2 equivalent | {thresholds['current']['raw_hysteresis_V']*1000:.3f} mV / {thresholds['current']['nominal_hysteresis_A_at_Uc5']:.3f} A |
| Brake raw rising / falling point | {thresholds['brake']['raw_rising_V']:.6f} / {thresholds['brake']['raw_falling_V']:.6f} V |
| Brake nominal fault window | {thresholds['brake']['fault_window']['low']['nominal_raw_V']:.4f}…{thresholds['brake']['fault_window']['high']['nominal_raw_V']:.4f} V |
| UV nominal cutoff / conservative VP range including bias | {uv_nom:.4f} V / {uv_min_with_bias:.4f}…{uv_max_with_bias:.4f} V |
| Output combined load / source ratio | {rload:.1f} Ω / {ratio:.5f} |
| Timer nominal / conservative model max | {timer['nominal_s']*1000:.2f} / {timer_max*1000:.2f} ms |
| Timer + assumed2ms sensor/filter +20ms relay/output | {total_budget*1000:.2f} ms |
| Margin below500ms with those assumptions | {timer['500ms_margin_s']*1000:.2f} ms |
| Delayed BOOT clock after FAULT_OK release, model envelope | {arm_min*1000:.3f}…{arm_max*1000:.3f} ms |
| Worst guaranteed CLR release to BOOT clock margin | {clr_bounds['min']*1e6:.2f} µs |
| Passes analytical startup recovery budget | {startup['passes_assumed_CLR_recovery_budget']} |

The timer keeps reference drift correlated between its charge source and half-reference threshold. Independent resistor temperature coefficients are conservatively allowed to differ; matched TCR is not silently assumed. Comparator bias is outward for this PNP-input family. Threshold corner tables exclude clamp leakage and reference load regulation, which remain explicit qualification items. The selected BAT54S has no guaranteed85°C leakage figure in the referenced datasheet, so these threshold corners are **not complete release bounds**.

Raw inlet voltage obeys `VIN = VP + SS14 forward drop`. The UV minimum including the input-bias allowance is {uv_min_with_bias:.4f}V atVP, above the AiM nominal10Vminimum without assuming any minimumdiode drop. For guaranteed operation at the tentative11.5VrawGLVminimum, the actual inletdiode drop must remain below {ASSUMPTIONS['target_raw_GLV_range_V_tentative'][0]-uv_max_with_bias:.4f}V at the worstUVcorner. Verify that cold,loaded condition;11.5…16V is a tentativeoperatingrange. The confirmedAiM datasheet doesnotstateaccuracy,temperature oroutputloadlimits, so the board'stentative−20…85°Cscope is notsensorqualification.

At Uc=5.25V, ideal +200A produces {sensor['channel2_plus200A_at_Uc5p25_raw_V']:.4f}V, above the current high-fault window {highraw:.4f}V. The circuit therefore does not cover the full +200A sensor range across the full allowed supply range; overload also faults unconditionally. Adjust the window only after fault-disconnection requirements and peak-current behavior are established.

Even ideal zero-current at maximumUc is {sensor['ideal_zero_output_at_Uc_max_V']:.4f}V, while ideal5kW at minimumUc is {sensor['ideal_5kW_output_at_Uc_min_V']:.4f}V. The overlap proves that a fixed absolute threshold cannot guarantee both behaviors. Current release remains blocked pending a defensible sensor-rail strategy; reusing pin1 has not been approved in this snapshot.

The conceptual traces verify healthy startup, individual input conditions, coincidence trip, immediate sensor fault, fault persistence, initially late sensor readiness, and brownout. BOOT_CLK sets ARM_ONCE only once per POR cycle; later FAULT_OK recovery creates BOOT edges but does not create a new ARM_CLK edge. A recovered long brownout resets ARM_ONCE and can rearm PERMIT. The external relay latch still drops; the complete reset chain must be tested and shown to meet the permitted reset method. Passing an idealized trace is not physical qualification. The coupled RC corner calculation checks the main latch CLR release separately. The selected Microchip MCP809T-450 has a 150…700ms recovery reset delay (350ms typical) and4.25…4.50V trip interval (4.375V typical); similarly named TI devices have different limits.

Required bench evidence: measure threshold rising/falling points with actual sensor supply and hydraulic pressure; test every signal/supply/ground/reference disconnection separately; test shorts, negative inputs and sensor power remaining on while GLV is off; scope FAULT_OK/ARM_CLK/PERMIT on slow startup and brownout; measure total time to SDC-contact opening with installed suppression; test the declared temperature and GLV extremes; save calibrated resistor values and results before vehicle release.
""")
    print(json.dumps({"JSON":str(args.output.resolve()),"summary":str(summary.resolve()),"spec_sha256":results["spec_sha256"],
        "current_rising_raw_V":thresholds["current"]["raw_rising_V"],"timer_nominal_ms":timer["nominal_s"]*1000,
        "timer_max_ms":timer_max*1000,"total_budget_ms":total_budget*1000,
        "conceptual_cases_passed":sum(t["conceptual_expectation_passed"] for t in traces),"release_status":results["release_status"]},indent=2))


if __name__ == "__main__":
    main()
