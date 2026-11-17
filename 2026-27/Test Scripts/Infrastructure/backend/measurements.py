"""Board-independent numeric/waveform calculations; no instrument connections."""
import math
from statistics import mean
from typing import Any, Sequence


def reading(value: Any) -> float:
    """Convert to a finite number; reject overload sentinels and booleans."""
    if isinstance(value, bool):
        raise ValueError('Expected a numeric instrument reading')
    result = float(value)
    if not math.isfinite(result) or abs(result) >= 1e30:
        raise ValueError(f'Invalid or overloaded reading: {value!r}')
    return result


def ascii_waveform(reply: str) -> list[float]:
    """Parse comma-separated ASCII values, optionally inside an IEEE 488.2 block."""
    payload = reply.strip()
    if reply.startswith('#'):
        if len(reply) < 2 or reply[1] not in '123456789':
            raise ValueError('Unsupported waveform block header')
        digits = int(reply[1])
        size = reply[2:2+digits]
        if len(size) != digits or not size.isascii() or not size.isdigit():
            raise ValueError('Invalid waveform block length')
        length = int(size)
        payload = reply[2+digits:2+digits+length]
        if len(payload) != length:
            raise ValueError('Truncated waveform block')
        if reply[2+digits+length:].strip():
            raise ValueError('Unexpected data after waveform block')
    if not payload.strip():
        raise ValueError('Empty waveform data')
    return [reading(value) for value in payload.split(',')]


def pulse_timing(samples: Sequence[float], dt: float, threshold: float,
                 min_cycles: int = 30, active_below: bool = True) -> tuple[list[float], list[float]]:
    """Return complete-cycle periods (seconds) and active-duty fractions; ignore edge fragments."""
    dt, threshold = reading(dt), reading(threshold)
    if dt <= 0 or isinstance(min_cycles, bool) or not isinstance(min_cycles, int) or min_cycles < 1:
        raise ValueError('Sample interval and minimum cycle count must be positive')
    values = [reading(value) for value in samples]
    on = [v < threshold if active_below else v >= threshold for v in values]
    starts = [i for i in range(1, len(on)) if on[i] and not on[i-1]]
    if len(starts) < min_cycles+1:
        raise ValueError(f'Capture must contain at least {min_cycles} complete cycles')
    periods = [(b-a)*dt for a, b in zip(starts, starts[1:])]
    duties = [sum(on[a:b])/(b-a) for a, b in zip(starts, starts[1:])]
    return periods, duties


def pulse_window(values: Sequence[float], times: Sequence[float], threshold: float,
                 below: bool = True) -> tuple[float, float]:
    """Return first complete pulse start/end timestamps; skip an initially active fragment."""
    if len(values) != len(times):
        raise ValueError('Waveform values and timestamps must align')
    timestamps = [reading(t) for t in times]
    if any(b <= a for a, b in zip(timestamps, timestamps[1:])):
        raise ValueError('Waveform timestamps must increase strictly')
    threshold = reading(threshold)
    samples = [reading(v) for v in values]
    active = [v < threshold if below else v >= threshold for v in samples]
    starts = [i for i in range(1, len(active)) if active[i] and not active[i-1]]
    if not starts:
        raise ValueError('No complete pulse start in capture')
    start = starts[0]
    end = next((i for i in range(start+1, len(active)) if not active[i]), None)
    if end is None:
        raise ValueError('Pulse end outside capture')
    return timestamps[start], timestamps[end]


def current_statistics(current: Sequence[float], lamp: Sequence[float], threshold: float,
                       active_below: bool = True) -> dict[str, float]:
    """ON/OFF/mean/sampled-peak amps. 'lamp' may be any aligned gating waveform."""
    if len(current) != len(lamp) or len(current) == 0:
        raise ValueError('Current/return captures must have aligned samples')
    amps = [reading(v) for v in current]
    gate = [reading(v) for v in lamp]
    threshold = reading(threshold)
    active = [v < threshold if active_below else v >= threshold for v in gate]
    on = [v for v, state in zip(amps, active) if state]
    off = [v for v, state in zip(amps, active) if not state]
    if not on or not off:
        raise ValueError('Capture must include ON and OFF intervals')
    return {'on_a': mean(on), 'off_a': mean(off), 'average_a': mean(amps), 'peak_a': max(amps)}
