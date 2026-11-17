"""Validate the selected procedure before opening any instrument."""
from .bench import validate, number


def requirements(test):
    required = {'hv', 'glv'}
    if any(word in test for word in ('threshold', 'shutdown', 'current_draw')) or test == 'test_vil_thermal_soak':
        required.add('dmm')
    if test in ('test_rml_flash_timing', 'test_rml_lamp_check', 'test_rml_glv_variation',
                'test_rml_current_draw', 'test_rml_thermal_soak'):
        required.add('scope')
    if test == 'test_rml_timer_driver':
        required = {'glv', 'dmm', 'scope', 'generator'}
    return required


def preflight(c, test):
    required = requirements(test)
    validate(c, required)
    for source in required & {'hv', 'glv'}:
        for key in ('set_voltage', 'set_current', 'output', 'voltage', 'current', 'error', 'ovp', 'ovp_read', 'current_setting', 'output_state'):
            if not isinstance(c[source].get(key), str) or not c[source][key]:
                raise ValueError(f'Missing {source} SCPI command: {key}')
    for name in required:
        if not c.get(name, {}).get('address'):
            raise ValueError(f'{test}: missing {name} address; run discovery first')
    mode = c['dmm']['mode']
    expected = ('hv_shunt' if test == 'test_vil_current_draw' else
                'glv_shunt' if test == 'test_rml_current_draw' else 'hv_voltage')
    if 'dmm' in required and mode != expected:
        raise ValueError(f'{test}: prewire DMM for {expected}, not {mode}')
    if expected in ('hv_shunt', 'glv_shunt'):
        source = 'hv' if expected == 'hv_shunt' else 'glv'
        if c[source+'_current_limit'] * c['dmm']['shunt_ohms'] > 1:
            raise ValueError('Shunt drop exceeds configured 1 V DMM range at current limit')
    if test == 'test_rml_timer_driver' and not c['generator'].get('injection_fixture_verified'):
        raise ValueError('Timer injection requires HV physically disconnected and Q4 isolated from U2 pin 4')
    if test == 'test_rml_timer_driver' and not c['generator'].get('commands_verified'):
        raise ValueError('Verify EDU33212A command profile before generator use')
    if 'scope' in required:
        s = c['scope']
        if not 0 < number(s['probe_factor']) <= 1000:
            raise ValueError('Invalid scope probe factor')
        if number(s['current_scale_v_div']) <= 0 or not 0 < number(s['startup_threshold']) < c['glv_nominal']:
            raise ValueError('Invalid scope scale or GLV trigger threshold')
        if not 0 < number(s['lamp_on_below']) < c['glv_nominal']:
            raise ValueError('Lamp threshold must be between zero and nominal GLV')
        channels = [s['lamp_channel'], s['startup_channel']]
        if test == 'test_rml_current_draw':
            channels.append(s['current_channel'])
            if number(c['dmm']['shunt_ohms']) <= 0:
                raise ValueError('Positive current shunt resistance required')
        if len(channels) != len(set(channels)) or any(ch not in (1,2,3,4) for ch in channels):
            raise ValueError('Scope channel assignments must be distinct channels 1 through 4')
    if 'thermal' in test and not c.get('temperature_method'):
        raise ValueError('Identify the isolated/IR temperature measurement method')
    needed_hv = 65 if 'threshold' in test else 80
    if test in ('test_vil_operating_range', 'test_vil_glv_independence', 'test_vil_shutdown',
                'test_vil_current_draw', 'test_vil_thermal_soak', 'test_rml_flash_timing',
                'test_rml_lamp_check', 'test_rml_shutdown', 'test_rml_thermal_soak'):
        needed_hv = 404
    if 'hv' in required and c['hv_max'] < needed_hv:
        raise ValueError(f'{test} needs HV ceiling {needed_hv} V; configured {c["hv_max"]} V')
    return required
