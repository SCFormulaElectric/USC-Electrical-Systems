#!/usr/bin/env python3
"""R2 non-latching BSPD analytical evidence; not SPICE or a hardware test.

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
    "TS_max_voltage_user_declared_V": 404.0,
    "target_raw_GLV_range_V_tentative": [11.5, 16.0],
    "power_criterion_W": 5000.0,
    "AiM_brake_output_nominal_V": [1.0, 5.0],
    "logic_supply_assumed_V": [4.75, 5.25],
    "comparator_output_LOW_for_nominal_model_V": 0.0,
    "comparator_output_LOW_upper_bound_V": 0.55,
    "timer_reset_FET_on_resistance_assumed_ohm": 10.0,
    "conceptual_trace_step_s": 0.00025,
}

SOURCES = {
    "LM2901B": "https://www.ti.com/lit/ds/symlink/lm339.pdf",
    "LM4040": "https://www.ti.com/lit/ds/symlink/lm4040-n.pdf",
    "HC132": "https://assets.nexperia.com/documents/data-sheet/74HC_HCT132.pdf",
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


def conceptual_trace(name, segments, expected_permits, timer_r, timer_c):
    """Combinational permit and first-order charge/reset model; not transistor simulation.

    Segments contain duration, POR_N, VALID, C_HIGH, B_HARD. VALID combines
    sensor-window and undervoltage health. The supervisor's POR_N is an input,
    so its analogue voltage detection/recovery delay is not simulated here.
    """
    step = ASSUMPTIONS["conceptual_trace_step_s"]
    timer_v = 0.0
    permit = False
    elapsed = 0.0
    events = []
    segment_results = []
    for index, (duration, por_n, valid, current_high, brake_high) in enumerate(segments):
        count = int(round(duration / step))
        for _ in range(count):
            before = permit
            elapsed += step
            if current_high and brake_high:
                timer_v = 5.0 + (timer_v - 5.0) * math.exp(-step / (timer_r * timer_c))
            else:
                ron = ASSUMPTIONS["timer_reset_FET_on_resistance_assumed_ohm"]
                final = 5.0 * ron / (timer_r + ron)
                tau = parallel(timer_r, ron) * timer_c
                timer_v = final + (timer_v - final) * math.exp(-step / tau)
            timer_ok = timer_v < 2.5
            fault_ok = bool(valid and timer_ok)
            permit_n = not (fault_ok and por_n)
            permit = not permit_n
            if before != permit:
                events.append({"t_s": round(elapsed, 6), "POR_N": por_n,
                    "VALID": valid, "C_HIGH": current_high, "B_HARD": brake_high,
                    "TIMER_OK": timer_ok, "FAULT_OK": fault_ok,
                    "PERMIT_N": permit_n, "PERMIT": permit,
                    "timer_V": timer_v})
        events.append({"t_s": round(elapsed, 6), "segment_end": True,
            "POR_N": por_n, "VALID": valid, "C_HIGH": current_high, "B_HARD": brake_high,
            "TIMER_OK": timer_ok, "FAULT_OK": fault_ok, "PERMIT": permit,"timer_V": timer_v})
        segment_results.append({"segment": index + 1, "PERMIT": permit,
            "expected_PERMIT": expected_permits[index], "passed": permit == expected_permits[index]})
    return {"name": name, "events": events, "final_permit": permit,
        "segment_expectations": segment_results,
        "conceptual_expectation_passed": all(v["passed"] for v in segment_results),
        "model_limitations": ["Ideal comparator/Schmitt logic and output stage",
        "No comparator propagation, input-clamp behavior, sensor dynamics or mechanical relay model",
        "Reset FET uses an assumed constant 10-ohm on-resistance; recovery is not a measured bound",
        "POR_N is supplied by the test scenario; supervisor analogue behavior is not simulated",
        "External relay-board fault retention is user confirmed and is not simulated"]}


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
        "permit_NAND_fault_input": roles["coincidence_logic"]["pins"].get("4") == "FAULT_OK",
        "permit_NAND_supervisor_input": roles["coincidence_logic"]["pins"].get("5") == "POR_N",
        "permit_NAND_output": roles["coincidence_logic"]["pins"].get("6") == "PERMIT_N",
        "permit_inverter_inputs": all(roles["coincidence_logic"]["pins"].get(p) == "PERMIT_N" for p in ["9", "10"]),
        "permit_inverter_output": roles["coincidence_logic"]["pins"].get("8") == "PERMIT",
        "output_base_driven_by_permit": roles["permit_base"]["pins"].get("1") == "PERMIT",
        "onboard_trip_memory_absent": "hardware_trip_latch" not in roles,
        "startup_memory_network_absent": all(role not in roles for role in ["latch_bypass", "arm_clock_delay", "arm_clock_delay_cap", "power_fault_or"]),
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

    power_supervision = {
        "permit_equation": "PERMIT = FAULT_OK AND POR_N",
        "MCP809_post_recovery_reset_time_s": {"min": 0.150, "typical": 0.350, "max": 0.700},
        "MCP809T_450_trip_V": {"min": 4.25, "typical": 4.375, "max": 4.50},
        "source": SOURCES["Microchip_MCP809"],
        "behavior": "LOW POR_N inhibits permit. HIGH POR_N permits immediately when all comparator conditions are healthy; no onboard reset or stored trip is used.",
        "external_relay_retention": "User-confirmed relay-board latch retains a shutdown after its relay has opened.",
    }
    healthy = (True, True, False, False)
    trace = lambda name, segments, expected: conceptual_trace(name, segments, expected, r("timer_charge"), cnom)
    traces = [
        trace("healthy_startup_after_POR", [(0.2, False, True, False, False), (0.1, *healthy)], [False, True]),
        trace("current_only_no_trip", [(0.2, False, True, False, False), (0.1, *healthy), (0.6, True, True, True, False)], [False, True, True]),
        trace("brake_only_no_trip", [(0.2, False, True, False, False), (0.1, *healthy), (0.6, True, True, False, True)], [False, True, True]),
        trace("coincidence_trip_stays_LOW_while_held", [(0.2, False, True, False, False), (0.1, *healthy), (0.4, True, True, True, True), (0.1, True, True, True, True)], [False, True, False, False]),
        trace("timer_trip_recovers_when_current_clears_without_reset", [(0.2, False, True, False, False), (0.1, *healthy), (0.4, True, True, True, True), (0.1, True, True, False, True)], [False, True, False, True]),
        trace("timer_trip_recovers_when_brake_clears_without_reset", [(0.2, False, True, False, False), (0.1, *healthy), (0.4, True, True, True, True), (0.1, True, True, True, False)], [False, True, False, True]),
        trace("brief_coincidence_resets_timer", [(0.2, False, True, False, False), (0.1, *healthy), (0.1, True, True, True, True), (0.2, *healthy)], [False, True, True, True]),
        trace("sensor_fault_clears_and_permit_recovers_without_reset", [(0.2, False, True, False, False), (0.1, *healthy), (0.02, True, False, False, False), (0.2, *healthy)], [False, True, False, True]),
        trace("UV_fault_clears_and_permit_recovers_without_reset", [(0.2, False, True, False, False), (0.1, *healthy), (0.02, True, False, False, False), (0.2, *healthy)], [False, True, False, True]),
        trace("initial_sensor_late_ready_automatically_permits", [(0.2, False, False, False, False), (0.1, True, False, False, False), (0.2, *healthy)], [False, False, True]),
        trace("POR_inhibit_and_recovery", [(0.1, *healthy), (0.2, False, True, False, False), (0.2, *healthy)], [True, False, True]),
    ]
    if not all(case["conceptual_expectation_passed"] for case in traces):
        raise AssertionError("R2 non-latching functional expectation failed")
    truth_table = [
        {"POR_N": por, "VALID": valid, "TIMER_OK": tok,
         "FAULT_OK": valid and tok, "PERMIT": por and valid and tok}
        for por, valid, tok in itertools.product([False, True], repeat=3)
    ]
    ron = ASSUMPTIONS["timer_reset_FET_on_resistance_assumed_ohm"]
    reset_final = 5 * ron / (r("timer_charge") + ron)
    reset_tau = parallel(r("timer_charge"), ron) * cnom
    from_v = 5.0
    timer["reset_recovery_example"] = {
        "condition": "Either C_HIGH or B_HARD clears, turning the timer reset FET on",
        "reset_FET_Ron_assumed_ohm": ron,
        "reset_final_V": reset_final,
        "reset_time_constant_s": reset_tau,
        "initial_timer_V": from_v,
        "time_to_fall_below_nominal_half_reference_s": reset_tau * math.log((from_v - reset_final) / (2.5 - reset_final)),
        "status": "Illustrative first-order model with assumed FET on-resistance, not a guaranteed or measured recovery time",
    }

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
    gate_buffer = {
        "implementation": "U8 gate2 NAND(FAULT_OK, POR_N), followed by gate3 inverter",
        "permit_equation": "PERMIT = FAULT_OK AND POR_N",
        "onboard_trip_memory": False,
        "fault_clearance_requires_GLV_reset": False,
        "external_relay_retention_user_confirmed": True,
        "healthy_FAULT_OK_V_if_directly_loaded_by_base_resistor":
            (5 * r("permit_base") + 0.7 * r("fault_bus_pullup")) /
            (r("permit_base") + r("fault_bus_pullup")),
        "nominal_gate_output_base_resistor_current_A": (5 - 0.7) / r("permit_base"),
        "NPN_VBE_assumption_V": 0.7,
        "truth_table": truth_table,
        "qualification": "Combinational model excludes propagation delays, analogue gate levels and the mechanical relay; the retained output/relay budget requires physical verification.",
    }
    results={"analysis_type":"R2 non-latching analytical nodal/corner and conceptual model; NOT SPICE or hardware evidence",
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
        "timer":timer,"logic":gate_buffer,"power_supervision":power_supervision,
        "conceptual_functional_traces":traces,"current_sensor_constraints":sensor,
        "clamp_selected":roles["current_input_clamp"]["value"],
        "hard_release_blockers":["Unknown Orion sensor5V rail; unusedJ1pin1sensewire decision is not approved in thissnapshot",
            "FixedCH2 threshold cannot guaranteehealthy0A and5kW over full4.75-5.25V supplyrange",
            "Actual brake hard-braking hydraulic calibration pending",
            "Clamp leakage and sustainednegative/unpoweredfault behavior pendingphysicalqualification",
            "Physical timer/output/relay timing, including suppression release time, remains unmeasured"],
        "not_measured":["Actual board", "SPICE transistor model", "Relay contacts", "Sensor voltages/currents", "Thermal chamber behavior", "Negative input fault behavior"]}
    args.output.write_text(json.dumps(results,indent=2,allow_nan=False)+"\n")
    summary=args.output.with_name("circuit_analysis_summary.md")
    current_range_statement = (
        "The ideal +200 A point lies inside this nominal window. Sensor errors, window tolerances and overload clamping still require qualification."
        if sensor["full_channel2_plus200A_valid_with_current_fault_window"] else
        "The ideal +200 A point lies above this nominal window, so the full positive sensor range is not covered at that supply."
    )
    summary.write_text(f"""# R2 non-latching circuit analysis

This is an analytical model, **not SPICE or hardware validation**. It reads component roles and values from the current {results['part_count']}-part specification. Input SHA-256: `{results['spec_sha256']}`.

Regenerate from the project directory with `python3 reports/analyze_circuit.py --spec circuit_spec.json`. The JSON contains assumptions, corner witnesses, independent nodal checks and conceptual traces.

## Permit behavior

`PERMIT = FAULT_OK AND POR_N`. Existing HC132 gates buffer the fault bus and directly apply the supervisor inhibit. There is no onboard trip storage or startup-memory network. Permit returns HIGH when faults clear, the timer has recovered and POR_N is HIGH; **no GLV reset is needed for BSPD permit recovery**. The user-confirmed external relay board retains the shutdown after its relay opens.

All {len(traces)} conceptual scenarios pass their segment-by-segment expectations: healthy and late-sensor startup, current alone, brake alone, sustained coincidence, recovery when either coincidence input clears, brief pulses, sensor/UV fault clearance and POR inhibit/recovery. These are model checks; relay retention is not simulated.

| Quantity | Calculated result |
|---|---:|
| Current raw rising / falling point | {thresholds['current']['raw_rising_V']:.6f} / {thresholds['current']['raw_falling_V']:.6f} V |
| Current nominal rising at exactly 5 V sensor supply | {thresholds['current']['nominal_rising_current_A_at_Uc5']:.3f} A |
| Current raw hysteresis / channel-2 equivalent | {thresholds['current']['raw_hysteresis_V']*1000:.3f} mV / {thresholds['current']['nominal_hysteresis_A_at_Uc5']:.3f} A |
| Current nominal fault window | {thresholds['current']['fault_window']['low']['nominal_raw_V']:.4f}…{highraw:.4f} V |
| Brake raw rising / falling point | {thresholds['brake']['raw_rising_V']:.6f} / {thresholds['brake']['raw_falling_V']:.6f} V |
| Brake nominal fault window | {thresholds['brake']['fault_window']['low']['nominal_raw_V']:.4f}…{thresholds['brake']['fault_window']['high']['nominal_raw_V']:.4f} V |
| UV nominal cutoff / conservative VP range including bias | {uv_nom:.4f} V / {uv_min_with_bias:.4f}…{uv_max_with_bias:.4f} V |
| Output combined load / source ratio | {rload:.1f} Ω / {ratio:.5f} |
| Timer nominal / conservative model maximum | {timer['nominal_s']*1000:.2f} / {timer_max*1000:.2f} ms |
| Timer + assumed 2 ms sensor/filter + 20 ms relay/output | {total_budget*1000:.2f} ms |
| Margin below 500 ms with those assumptions | {timer['500ms_margin_s']*1000:.2f} ms |
| Illustrative timer recovery from 5 V below the half-reference | {timer['reset_recovery_example']['time_to_fall_below_nominal_half_reference_s']*1e6:.2f} µs |

The recovery example uses an assumed 10 Ω reset-FET on-resistance; it is not a guaranteed physical recovery bound. Either C_HIGH or B_HARD clearing turns the existing FET on. The model retains charge and finite discharge, so TIMER_OK and permit recover when the capacitor crosses below threshold, rather than requiring a reset or clock.

## Tolerance limits

Analogue calculations are retained: reference drift stays correlated between timer charge source and threshold; resistor TCR may differ; comparator offset and outward bias, FET off leakage and positive X7R capacitance bounds remain included. Threshold corners exclude clamp leakage and reference load regulation. BAT54S has no guaranteed 85°C leakage figure in the referenced datasheet, so threshold corners are **not complete vehicle-release bounds**. The reset-FET, sensor/filter and suppressed-relay timing assumptions require measurement.

Raw inlet voltage is `VIN = VP + SS14 forward drop`. The minimum modeled UV cutoff, {uv_min_with_bias:.4f} V at VP, exceeds the AiM nominal 10 V supply requirement without assuming a minimum diode drop. Operation at the tentative 11.5 V raw-GLV lower target requires actual diode drop below approximately {ASSUMPTIONS['target_raw_GLV_range_V_tentative'][0]-uv_max_with_bias:.4f} V at the worst UV corner. Verify cold operation. The tentative board range −20…85°C does not qualify the AiM sensor's unspecified environmental performance.

At Uc = 5.25 V, ideal +200 A produces {sensor['channel2_plus200A_at_Uc5p25_raw_V']:.4f} V; the nominal high-fault boundary is {highraw:.4f} V. {current_range_statement} The minimum stated upper overload-clamp value at that rail is {sensor['overload_clamp_min_at_Uc5p25_V']:.4f} V. Ground/supply-disconnection behavior must be tested on actual sensors.

## Calibration still pending

Ideal zero-current output at maximum Uc is {sensor['ideal_zero_output_at_Uc_max_V']:.4f} V, while ideal 5 kW output at minimum Uc is {sensor['ideal_5kW_output_at_Uc_min_V']:.4f} V at nominal 360 V TS. Their overlap prevents a fixed absolute threshold from guaranteeing both behaviors over that whole rail range. The declared TS maximum is 404 V; the power criterion uses 360 V nominal. Orion rail bounds/reference strategy and current calibration remain unresolved; J1 pin 1 is still unused. The brake hard-braking pressure also remains uncalibrated. The confirmed AiM document does not state accuracy, temperature or output-load limits.

The retained Microchip supervisor has 150…700 ms reset-release delay (350 ms typical), and a 4.25…4.50 V trip interval (4.375 V typical). This ordinary power supervision remains independent of fault retention.

Bench verification should check direct POR inhibition, fault clearance without GLV cycling, timer recovery after either input clears, thresholds with the actual sensors, total time to contact opening, loaded output and external relay retention. Very short LOW pulses may recover before a mechanical relay opens; measure the actual minimum release pulse. The BSPD itself deliberately retains no fault state.
""")
    print(json.dumps({"JSON":str(args.output.resolve()),"summary":str(summary.resolve()),"spec_sha256":results["spec_sha256"],
        "current_rising_raw_V":thresholds["current"]["raw_rising_V"],"timer_nominal_ms":timer["nominal_s"]*1000,
        "timer_max_ms":timer_max*1000,"total_budget_ms":total_budget*1000,
        "conceptual_cases_passed":sum(t["conceptual_expectation_passed"] for t in traces),"release_status":results["release_status"]},indent=2))


if __name__ == "__main__":
    main()
