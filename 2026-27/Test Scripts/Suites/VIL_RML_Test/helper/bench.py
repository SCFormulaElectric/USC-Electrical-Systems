"""Small SCPI bench driver. No resource is opened at import time."""
import csv
import math
import json
import time
from pathlib import Path

from backend.measurements import ascii_waveform, reading as number, pulse_timing as timing
from backend.operator import monitored_input
from backend.visa import validate_settings


def validate(c, required=None):
    required = set(required) if required is not None else {'hv', 'glv'} | {
        name for name in ('dmm', 'scope', 'generator') if c.get(name, {}).get('address')}
    if c.get('visa_backend') != '@py':
        raise ValueError('This suite requires visa_backend = "@py" (pyvisa-py)')
    for key in ('hv_max', 'glv_min', 'glv_max', 'glv_nominal',
                'hv_current_limit', 'glv_current_limit', 'temperature_limit_c',
                'settle_timeout_s', 'voltage_tolerance_v', 'soak_seconds',
                'temperature_interval_s', 'hv_ovp', 'glv_ovp', 'hv_uncertainty_v', 'operator_timeout_s'):
        if 'hv' not in required and key in ('hv_max', 'hv_current_limit', 'hv_ovp'):
            continue
        if number(c[key]) <= 0:
            raise ValueError(f"Set a reviewed positive {key}")
    if not c['reviewed'] or not c['manual']:
        raise ValueError("Reviewed configuration and attended manual observations required")
    if not (c['glv_min'] <= c['glv_nominal'] <= c['glv_max'] <= 15) or ('hv' in required and c['hv_max'] > 404):
        raise ValueError("Invalid voltage bounds (GLV ceiling 15 V; component review still required)")
    if c['soak_seconds'] < 3600 or c['temperature_interval_s'] > 900:
        raise ValueError("Soak requires >=3600 seconds, temperature interval <=900 seconds")
    if ('hv' in required and not c['hv_max'] < c['hv_ovp'] <= 450) or not c['glv_max'] < c['glv_ovp'] <= 15:
        raise ValueError('OVP must exceed test range, within reviewed HV <=450 V / GLV <=15 V ceilings')
    if not 0 <= number(c['duty_tolerance_fraction']) < .5:
        raise ValueError('Duty engineering tolerance must be a fraction from zero to less than 0.5')
    addresses = []
    for name in ('hv', 'glv'):
        if name in required and not c[name]['commands_verified']:
            raise ValueError(f"Set {name} address and verify model-specific SCPI commands")
    for name in sorted(required):
        try:
            validate_settings(c.get(name, {}))
        except ValueError as error:
            raise ValueError(f'{name}: {error}') from error
        addresses.append(c[name]['address'].strip())
    if 'glv' in required and not c['glv'].get('output_delay_off', '').strip():
        raise ValueError('Set glv.output_delay_off to the verified channel-qualified shutdown-delay command')
    if len(set(addresses)) != len(addresses):
        raise ValueError("Instrument addresses must be distinct")
    if c['dmm']['mode'] not in ('hv_voltage', 'hv_shunt', 'glv_shunt'):
        raise ValueError("Unsupported DMM wiring mode")
    if c['dmm']['mode'] != 'hv_voltage' and number(c['dmm']['shunt_ohms']) <= 0:
        raise ValueError("Set shunt resistance")


class Bench:
    def __init__(self, config, directory, resource_manager, required=None):
        validate(config, required)
        self.c, self.rm = config, resource_manager
        self.resources = {}
        self.identified = set()
        self.review_reasons = []
        self.sources = ('hv', 'glv')
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.logfile = (self.directory/'measurements.csv').open('w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.logfile)
        self.writer.writerow(['utc_epoch_s', 'name', 'value', 'source'])

    def log(self, name, value, source='instrument'):
        self.writer.writerow([time.time(), name, value, source])
        self.logfile.flush()
        return value

    def connect(self, required=None):
        validate(self.c, required)
        required = set(required or ('hv', 'glv', 'dmm', 'scope'))
        self.sources = tuple(n for n in ('hv', 'glv') if n in required)
        # Register each resource immediately so partial setup can be cleaned up.
        for name in ('hv', 'glv', 'dmm', 'scope', 'generator'):
            if name not in required:
                continue
            p = self.c[name]
            if not p['address']:
                continue
            r = self.rm.open_resource(p['address'])
            self.resources[name] = r
            r.timeout = 120000 if name == 'scope' else 10000
            r.write_termination = '\n'
            r.read_termination = '\n'
            identity = r.query('*IDN?').strip()
            self.log(name+'.identity', identity)
            if p['identity'].strip().upper() not in identity.upper():
                raise ValueError(f"Unexpected {name}: {identity}")
            self.identified.add(name)
            if name in self.sources:
                self.output_off(name)
        for name in self.sources:
            self.output_off(name)
            self.command(name, 'set_current', self.c[name+'_current_limit'])
            self.command(name, 'set_voltage', 0)
            actual_current_limit = self.read(name, 'current_setting')
            if not math.isclose(actual_current_limit, self.c[name+'_current_limit'], rel_tol=.01, abs_tol=1e-6):
                raise RuntimeError(f'{name} current limit was not applied exactly enough; inspect supply minimum/resolution')
            if self.read(name, 'output_state') != 0:
                raise RuntimeError(f'{name} did not switch output OFF')
            if 'ovp' in self.c[name]:
                self.command(name, 'ovp', self.c[name+'_ovp'])
                actual = self.read(name, 'ovp_read')
                if abs(actual-self.c[name+'_ovp']) > .05:
                    raise RuntimeError(f'{name} OVP readback mismatch')
        if 'dmm' in self.resources:
            r = self.resources['dmm']
            r.write('CONF:VOLT:DC '+('1000' if self.c['dmm']['mode'] == 'hv_voltage' else '1'))
            if 'VOLT' not in r.query('FUNC?').upper():
                raise RuntimeError('DMM is not in DC voltage mode')
            if int(r.query('SYST:ERR?').split(',')[0]) != 0:
                raise RuntimeError('DMM configuration error')
        if 'generator' in self.resources:
            self.generator(0, False)
        if 'scope' in self.resources:
            s = self.c['scope']
            # Reject unsupported setup commands while all sources are still OFF.
            self.scope_setup(50, [s['lamp_channel'], s['startup_channel'], s['current_channel']])

    def review(self, reason):
        if reason not in self.review_reasons:
            self.review_reasons.append(reason)
        self.log('review_required', reason, 'assessment')

    def summary(self, procedure_status):
        status = 'NEEDS_REVIEW' if self.review_reasons and procedure_status == 'PASS' else procedure_status
        (self.directory/'summary.json').write_text(json.dumps({
            'procedure_status': procedure_status, 'acceptance_status': status,
            'review_required': self.review_reasons,
            'scope': 'Selected bench procedure only; not full vehicle compliance',
        }, indent=2), encoding='utf-8')

    def command(self, name, key, value):
        self.resources[name].write(self.c[name][key].format(value=value))
        self.error(name)

    def error(self, name):
        reply = self.resources[name].query(self.c[name]['error']).strip()
        if int(reply.split(',')[0]) != 0:
            raise RuntimeError(f"{name}: {reply}")

    def read(self, name, key):
        return self.log(name+'.'+key, number(self.resources[name].query(self.c[name][key])))

    def dmm(self):
        return self.log('dmm.voltage', number(self.resources['dmm'].query('READ?')))

    def voltage(self, name):
        if name == 'hv' and self.c['dmm']['mode'] == 'hv_voltage' and 'dmm' in self.resources:
            return self.dmm()
        return self.read(name, 'voltage')

    def check(self):
        for name in self.sources:
            self.error(name)
            current = self.read(name, 'current')
            if current >= self.c[name+'_current_limit'] * 0.98:
                raise RuntimeError(f"{name} at current limit; stop and inspect")
            measured = self.read(name, 'voltage')
            if measured > self.c[name+'_ovp']:
                raise RuntimeError(f'{name} voltage above reviewed OVP limit')

    def set(self, name, value):
        value = number(value)
        if not 0 <= value <= self.c[name+'_max']:
            raise ValueError(f"{name} voltage outside configured limits")
        self.command(name, 'set_voltage', value)
        if value > 0:
            self.command(name, 'output', 1)
        else:
            self.output_off(name)
        deadline = time.monotonic()+self.c['settle_timeout_s']
        while True:
            self.check()
            if abs(self.voltage(name)-value) <= self.c['voltage_tolerance_v']:
                return
            if time.monotonic() > deadline:
                raise TimeoutError(f"{name} did not settle/discharge to {value} V")
            time.sleep(0.2)

    def wait(self, seconds):
        deadline = time.monotonic()+seconds
        while time.monotonic() < deadline:
            self.check()
            time.sleep(min(0.5, max(0, deadline-time.monotonic())))

    def prompt(self, question):
        return monitored_input(question, check=self.check, timeout_s=self.c.get('operator_timeout_s', 300))

    def observe(self, question, allowed):
        while True:
            answer = self.prompt(question+' ['+'/'.join(allowed)+']: ').strip().lower()
            if answer in allowed:
                return self.log(question, answer, 'manual')

    def scope_setup(self, seconds, channels, trigger=False):
        r = self.resources['scope']
        s = self.c['scope']
        r.write(':STOP')
        r.write(':ACQ:TYPE NORM')
        r.write(':TIM:MODE MAIN')
        r.write(f':TIM:RANG {seconds}')
        r.write(f':TIM:POS {seconds*.4 if trigger else 0}')
        for ch in channels:
            r.write(f':CHAN{ch}:DISP ON')
            r.write(f':CHAN{ch}:PROB {s["probe_factor"]}')
            r.write(f':CHAN{ch}:COUP DC')
            scale = s['current_scale_v_div'] if ch == s['current_channel'] else 5
            r.write(f':CHAN{ch}:SCAL {scale}')
            r.write(f':CHAN{ch}:OFFS {scale*3}')
        r.write(':TRIG:MODE EDGE')
        r.write(f':TRIG:EDGE:SOUR CHAN{s["startup_channel"] if trigger else s["lamp_channel"]}')
        r.write(':TRIG:EDGE:SLOP POS')
        r.write(f':TRIG:LEV {s["startup_threshold"] if trigger else s["lamp_on_below"]}')
        r.write(':TRIG:SWE NORM' if trigger else ':TRIG:SWE AUTO')
        self.scope_error()

    def scope_error(self):
        reply = self.resources['scope'].query(':SYST:ERR?')
        if int(reply.split(',')[0]):
            raise RuntimeError('Scope: '+reply)

    def scope_start(self):
        r = self.resources['scope']
        r.query(':ADER?')
        r.write(':SING')

    def scope_wait(self, timeout=90):
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            self.check()
            if int(self.resources['scope'].query(':ADER?')):
                self.scope_error()
                return
            time.sleep(.2)
        raise TimeoutError('Scope capture did not complete')

    def waveform(self, channel, label, acquire=True):
        r = self.resources['scope']
        if acquire:
            self.scope_setup(50, [channel])
            self.scope_start()
            self.scope_wait()
        r.write(f':WAV:SOUR CHAN{channel}')
        r.write(':WAV:FORM ASC')
        r.write(':WAV:POIN:MODE RAW')
        r.write(':WAV:POIN MAX')
        self.scope_error()
        dt = number(r.query(':WAV:XINC?'))
        if dt <= 0:
            raise ValueError('Invalid scope sample interval')
        values = ascii_waveform(r.query(':WAV:DATA?'))
        if not values:
            raise ValueError('Empty scope capture')
        with (self.directory/(label+'.csv')).open('w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['relative_seconds', 'volts'])
            w.writerows((i*dt, number(v)) for i,v in enumerate(values))
        return values, dt

    def paired_capture(self, channel, reference, label):
        values, dt = self.waveform(channel, label, acquire=False)
        ref, ref_dt = self.waveform(reference, label+'_reference', acquire=False)
        if len(values) != len(ref) or not math.isclose(dt, ref_dt, rel_tol=1e-6):
            raise ValueError('Scope channels not aligned')
        return values, ref, dt

    def generator(self, voltage, enabled=True):
        if not 0 <= voltage <= 5:
            raise ValueError('Injection limited to 0 through 5 V at isolated RESET pin')
        r = self.resources['generator']
        r.write('OUTP1 OFF')
        r.write('OUTP1:LOAD INF')
        r.write('SOUR1:FUNC DC')
        r.write(f'SOUR1:VOLT:OFFS {voltage}')
        r.write(f'OUTP1 {"ON" if enabled else "OFF"}')
        if int(r.query('SYST:ERR?').split(',')[0]):
            raise RuntimeError('Generator rejected DC injection configuration')

    def flash(self, label):
        values, dt = self.waveform(self.c['scope']['lamp_channel'], label)
        periods, duties = timing(values, dt, self.c['scope']['lamp_on_below'])
        for p, d in zip(periods, duties):
            self.log('frequency_hz', 1/p)
            self.log('duty_error_percentage_points', (d-.5)*100)
        assert all(.66 <= 1/p <= 1.33 for p in periods), 'Flash frequency outside rule limits'
        # No invented duty-cycle acceptance tolerance.
        tolerance = self.c.get('duty_tolerance_fraction', 0)
        if tolerance:
            if not all(abs(d-.5) <= tolerance for d in duties):
                raise AssertionError('Duty cycle outside reviewed engineering tolerance')
            self.review('Duty assessed against engineering tolerance; rule target remains 50%')
        else:
            self.review('Duty-cycle acceptance tolerance/uncertainty has not been established')

    def output_off(self, name):
        errors = []
        if name == 'glv':
            try:
                self.command(name, 'output_delay_off', 0)
            except Exception as error:
                errors.append(str(error))
        try:
            self.command(name, 'output', 0)
        except Exception as error:
            errors.append(str(error))
        try:
            if self.read(name, 'output_state') != 0:
                errors.append('Output OFF readback failed')
        except Exception as error:
            errors.append(str(error))
        if errors:
            raise RuntimeError(f'{name} shutdown failed: ' + '; '.join(errors))

    def close(self):
        errors = []
        if 'generator' in self.identified:
            try:
                self.resources['generator'].write('OUTP1 OFF')
            except Exception as e:
                errors.append(f'Generator shutdown failed: {e}')
        for name in ('hv', 'glv'):
            if name in self.identified:
                try:
                    self.output_off(name)
                except Exception as e:
                    errors.append(f'{name} shutdown failed: {e}')
        for r in self.resources.values():
            try:
                r.close()
            except Exception as e:
                errors.append(str(e))
        self.logfile.close()
        if errors:
            raise RuntimeError('; '.join(errors)+'; use hardware emergency disconnect')
