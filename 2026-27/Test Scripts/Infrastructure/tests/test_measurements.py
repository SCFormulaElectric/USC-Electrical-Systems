import pytest

from backend import ascii_waveform, current_statistics, pulse_timing, pulse_window, reading


@pytest.mark.parametrize('reply', ['0,12,0\n', '#17'+'0,12,0\n'])
def test_ascii_waveform(reply):
    assert ascii_waveform(reply) == [0,12,0]


@pytest.mark.parametrize('reply', ['#', '#0', '#2x', '#2100,1', '#130,1junk', '', '0,nan'])
def test_invalid_waveforms_fail_clearly(reply):
    with pytest.raises(ValueError): ascii_waveform(reply)


@pytest.mark.parametrize('active_below', [True, False])
def test_timing_supports_both_polarities(active_below):
    periods, duty = pulse_timing(([12]*50+[0]*50)*4, .01, 6, min_cycles=2, active_below=active_below)
    assert periods == pytest.approx([1]*len(periods))
    assert duty == pytest.approx([.5]*len(duty))


@pytest.mark.parametrize('dt', [0, -1, float('nan')])
def test_timing_rejects_bad_sample_interval(dt):
    with pytest.raises(ValueError): pulse_timing([0,12]*10, dt, 6)


def test_pulse_window_and_timestamp_validation():
    assert pulse_window([0,0,12,12,0], [0,.1,.2,.3,.4], 6, below=False) == (.2,.4)
    with pytest.raises(ValueError, match='align'):
        pulse_window([0,12], [0], 6)
    with pytest.raises(ValueError, match='increase'):
        pulse_window([0,12,0], [0,0,1], 6)
    with pytest.raises(ValueError, match='end outside'):
        pulse_window([0,12,12], [0,1,2], 6, below=False)


def test_gated_current_supports_high_active_outputs():
    result = current_statistics([.02,.12,.12,.02], [0,12,12,0], 6, active_below=False)
    assert result == pytest.approx(dict(on_a=.12, off_a=.02, average_a=.07, peak_a=.12))
    with pytest.raises(ValueError): current_statistics([float('nan'),0], [0,12], 6)
    with pytest.raises(ValueError): current_statistics([1,1], [0,0], 6)

