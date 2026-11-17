"""Small, model-specific APIs. Commands/sources are listed in Infrastructure/DRIVERS.md."""
from __future__ import annotations

import math
import time
from typing import Any

from .measurements import reading


def check_error(session: Any) -> None:
    """Raise on the first queued instrument error without clearing it silently."""
    reply = session.query('SYST:ERR?').strip()
    if int(reply.split(',')[0]) != 0:
        raise RuntimeError(f'Instrument error: {reply}')


class EDU34450A:
    """Keysight DMM. Creating the driver only queries identity."""

    def __init__(self, session: Any):
        self._session = session
        if 'EDU34450A' not in self.identify().upper():
            raise ValueError('EDU34450A driver requires an EDU34450A instrument')

    def identify(self) -> str:
        """Return the instrument identity string."""
        return self._session.query('*IDN?').strip()

    def query(self, command: str) -> str:
        """Raw query escape hatch, retained for existing tests using dmm.query()."""
        return self._session.query(command)

    def read_voltage_v(self) -> float:
        """Measure DC volts using autorange. Probe placement/rating is a fixture responsibility."""
        result = reading(self._session.query('MEAS:VOLT:DC?'))
        check_error(self._session)
        return result


class EDU36311A:
    """One reviewed supply channel. Construction never changes an output."""

    @staticmethod
    def validate_settings(settings: dict) -> None:
        """Validate board limits before requesting VISA access."""
        if settings.get('reviewed') is not True:
            raise ValueError('Supply settings require reviewed = true after board/fixture limit review')
        ch = settings.get('channel')
        if isinstance(ch, bool) or not isinstance(ch, int) or ch not in (1, 2, 3):
            raise ValueError('Supply channel must be 1, 2 or 3')
        vmax, imax = (6.0, 5.0) if ch == 1 else (30.0, 1.0)
        low = reading(settings['voltage_min_v'])
        high = reading(settings['voltage_max_v'])
        current = reading(settings['current_limit_a'])
        ovp = reading(settings['ovp_v'])
        if not 0 <= low <= high <= vmax:
            raise ValueError(f'Invalid voltage limits for channel {ch} (maximum {vmax} V)')
        if not 0 < current <= imax:
            raise ValueError(f'Current limit must be positive and <= {imax} A')
        if not high < ovp <= vmax * 1.1:
            raise ValueError('OVP must exceed test voltage and stay within instrument limits')

    def __init__(self, session: Any, settings: dict):
        self.validate_settings(settings)
        self._session = session
        self._settings = dict(settings)
        self._channel = settings['channel']
        self._configured = False
        if 'EDU36311A' not in session.query('*IDN?').upper():
            raise ValueError('EDU36311A driver requires an EDU36311A instrument')

    def _write(self, command: str) -> None:
        self._session.write(f'{command}, (@{self._channel})')
        check_error(self._session)

    def _read(self, command: str) -> float:
        result = reading(self._session.query(f'{command} (@{self._channel})'))
        check_error(self._session)
        return result

    def output_off(self) -> None:
        """Attempt immediate OFF even if removing an old output delay fails. Verify OFF state."""
        errors = []
        for command in ('OUTP:DEL:FALL 0', 'OUTP 0'):
            try:
                self._write(command)
            except Exception as error:
                errors.append(str(error))
        try:
            if self._read('OUTP?') != 0:
                errors.append('Output-off state readback is not zero')
        except Exception as error:
            errors.append(str(error))
        if errors:
            raise RuntimeError('Supply shutdown failed: '+'; '.join(errors))

    def configure(self) -> None:
        """Set OFF/zero volts, reviewed current limit, OVP and OCP. Never enables output."""
        self._configured = False
        self.output_off()
        self._write('OUTP:DEL:RISE 0')
        self._write('VOLT 0')
        self._write(f'CURR {self._settings["current_limit_a"]}')
        self._write(f'VOLT:PROT {self._settings["ovp_v"]}')
        self._write('CURR:PROT:DEL 0')
        self._write('CURR:PROT:STAT 1')
        self._check_protection()
        if abs(self._read('VOLT?')) > .005:
            raise RuntimeError('Supply zero-voltage setting was not applied')
        self._configured = True

    def _check_protection(self) -> None:
        for query, key, tolerance in (('CURR?', 'current_limit_a', .000001), ('VOLT:PROT?', 'ovp_v', .005)):
            if not math.isclose(self._read(query), self._settings[key], rel_tol=1e-4, abs_tol=tolerance):
                raise RuntimeError(f'Supply {key} readback does not match reviewed settings')
        if self._read('CURR:PROT:STAT?') != 1:
            raise RuntimeError('Supply OCP is not enabled')
        if self._read('CURR:PROT:DEL?') != 0:
            raise RuntimeError('Supply OCP delay must be zero')

    def _check_voltage(self, value: float) -> float:
        value = reading(value)
        if value != 0 and not self._settings['voltage_min_v'] <= value <= self._settings['voltage_max_v']:
            raise ValueError('Requested voltage is outside reviewed board limits')
        return value

    def set_voltage_v(self, voltage_v: float) -> None:
        """Program volts within reviewed limits; does not enable the output."""
        if not self._configured:
            raise RuntimeError('Configure supply before setting test voltage')
        value = self._check_voltage(voltage_v)
        self._write(f'VOLT {value}')
        if not math.isclose(self._read('VOLT?'), value, abs_tol=.005, rel_tol=1e-4):
            raise RuntimeError('Voltage setting readback mismatch')

    def output_on(self) -> None:
        """Enable the selected channel only after configuration and protection checks."""
        if not self._configured:
            raise RuntimeError('Configure supply before enabling output')
        self._check_voltage(self._read('VOLT?'))
        self._check_protection()
        self._write('OUTP 1')
        if self._read('OUTP?') != 1:
            raise RuntimeError('Supply did not enable output; check protection state')

    def read_voltage_v(self) -> float:
        """Read measured output volts, not the programmed setpoint."""
        return self._read('MEAS:VOLT?')

    def read_current_a(self) -> float:
        """Read average output amperes; not a peak/inrush measurement."""
        return self._read('MEAS:CURR?')

    def wait_for_voltage_v(self, target_v: float, tolerance_v: float, timeout_s: float) -> float:
        """Wait for measured output to settle; raises on timeout, never retries enabling."""
        target = self._check_voltage(target_v)
        tolerance, timeout = reading(tolerance_v), reading(timeout_s)
        if tolerance <= 0 or timeout <= 0:
            raise ValueError('Settling tolerance and timeout must be positive')
        deadline = time.monotonic()+timeout
        while True:
            actual = self.read_voltage_v()
            if abs(actual-target) <= tolerance:
                return actual
            if time.monotonic() >= deadline:
                raise TimeoutError(f'Supply did not settle to {target} V; last reading {actual} V')
            time.sleep(.1)
