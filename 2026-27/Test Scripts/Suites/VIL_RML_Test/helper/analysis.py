"""VIL/RML startup behavior; general waveform calculations live in Infrastructure."""
# Retain existing imports while keeping one shared implementation.
from backend.measurements import current_statistics, pulse_window


def lamp_check(lamp, reference, dt, lamp_threshold, glv_threshold):
    if len(lamp) != len(reference) or dt <= 0:
        raise ValueError('Startup channels must have aligned samples')
    times = [i*dt for i in range(len(lamp))]
    edges = [i for i in range(1, len(reference))
             if reference[i] >= glv_threshold > reference[i-1]]
    if not edges:
        raise ValueError('GLV rising edge missing from startup capture')
    i = edges[0]
    # An unpowered return can also be low; only evaluate after GLV rises.
    on = next((j for j in range(i, len(lamp)) if lamp[j] < lamp_threshold), None)
    if on is None:
        raise ValueError('Lamp check never illuminated')
    off = next((j for j in range(on+1, len(lamp)) if lamp[j] >= lamp_threshold), None)
    if off is None:
        raise ValueError('Lamp check did not end within capture')
    return times[on]-times[i], times[off]-times[on]

