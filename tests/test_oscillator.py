# Tests for Oscillator module
"""
test_oscillator.py - Unit tests for the Oscillator class

Tests cover:
- Waveform generation for all 5 types
- Frequency setting and conversion
- Phase accumulation
- Level control
- Pitch modulation
- MIDI note conversion
"""

import pytest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from synth.oscillator import Oscillator, Waveform, midi_to_frequency


class TestMidiToFrequency:
    """Tests for MIDI note to frequency conversion."""

    def test_a4_is_440hz(self):
        """A4 (MIDI 69) should be 440 Hz."""
        freq = midi_to_frequency(69)
        assert abs(freq - 440.0) < 0.001

    def test_middle_c(self):
        """Middle C (MIDI 60) should be ~261.63 Hz."""
        freq = midi_to_frequency(60)
        assert abs(freq - 261.6256) < 0.01

    def test_octave_doubling(self):
        """Frequency should double every 12 semitones."""
        freq_a3 = midi_to_frequency(57)
        freq_a4 = midi_to_frequency(69)
        freq_a5 = midi_to_frequency(81)

        assert abs(freq_a4 / freq_a3 - 2.0) < 0.001
        assert abs(freq_a5 / freq_a4 - 2.0) < 0.001

    def test_low_note(self):
        """Test very low MIDI note."""
        freq = midi_to_frequency(21)  # A0
        assert abs(freq - 27.5) < 0.1

    def test_high_note(self):
        """Test very high MIDI note."""
        freq = midi_to_frequency(108)  # C8
        assert abs(freq - 4186.01) < 1.0


class TestOscillatorInit:
    """Tests for Oscillator initialization."""

    def test_default_init(self):
        """Test default initialization values."""
        osc = Oscillator()
        assert osc.sample_rate == 44100
        assert osc.frequency == 440.0
        assert osc.waveform == Waveform.SINE
        assert osc.level == 1.0
        assert osc.pulse_width == 0.5

    def test_custom_sample_rate(self):
        """Test initialization with custom sample rate."""
        osc = Oscillator(sample_rate=48000)
        assert osc.sample_rate == 48000


class TestOscillatorProperties:
    """Tests for Oscillator property getters and setters."""

    def test_frequency_clamping_low(self):
        """Frequency should be clamped to minimum 20 Hz."""
        osc = Oscillator()
        osc.frequency = 5.0
        assert osc.frequency == 20.0

    def test_frequency_clamping_high(self):
        """Frequency should be clamped to maximum 20000 Hz."""
        osc = Oscillator()
        osc.frequency = 25000.0
        assert osc.frequency == 20000.0

    def test_level_clamping(self):
        """Level should be clamped to 0.0-1.0."""
        osc = Oscillator()
        osc.level = -0.5
        assert osc.level == 0.0
        osc.level = 1.5
        assert osc.level == 1.0

    def test_pulse_width_clamping(self):
        """Pulse width should be clamped to 0.05-0.95."""
        osc = Oscillator()
        osc.pulse_width = 0.01
        assert osc.pulse_width == 0.05
        osc.pulse_width = 0.99
        assert osc.pulse_width == 0.95

    def test_set_note(self):
        """Test setting frequency via MIDI note."""
        osc = Oscillator()
        osc.set_note(69)  # A4
        assert abs(osc.frequency - 440.0) < 0.001


class TestOscillatorWaveforms:
    """Tests for waveform generation."""

    @pytest.fixture
    def osc(self):
        """Create oscillator for testing."""
        osc = Oscillator(sample_rate=44100)
        osc.frequency = 440.0
        return osc

    def test_sine_output_range(self, osc):
        """Sine wave should be in range [-1, 1]."""
        osc.waveform = Waveform.SINE
        samples = osc.generate(1024)
        assert np.all(samples >= -1.0)
        assert np.all(samples <= 1.0)

    def test_sine_is_not_silent(self, osc):
        """Sine wave should not be silent."""
        osc.waveform = Waveform.SINE
        samples = osc.generate(1024)
        rms = np.sqrt(np.mean(samples**2))
        assert rms > 0.1

    def test_sawtooth_output_range(self, osc):
        """Sawtooth wave should be in range [-1, 1]."""
        osc.waveform = Waveform.SAWTOOTH
        samples = osc.generate(1024)
        assert np.all(samples >= -1.0)
        assert np.all(samples <= 1.0)

    def test_sawtooth_reaches_extremes(self, osc):
        """Sawtooth should reach near -1 and +1."""
        osc.waveform = Waveform.SAWTOOTH
        samples = osc.generate(4096)  # More samples for full cycle
        assert np.max(samples) > 0.9
        assert np.min(samples) < -0.9

    def test_square_binary_output(self, osc):
        """Square wave should only have values near -1 or 1."""
        osc.waveform = Waveform.SQUARE
        samples = osc.generate(1024)
        # All samples should be close to -1 or +1
        assert np.all(np.abs(np.abs(samples) - 1.0) < 0.01)

    def test_triangle_output_range(self, osc):
        """Triangle wave should be in range [-1, 1]."""
        osc.waveform = Waveform.TRIANGLE
        samples = osc.generate(1024)
        assert np.all(samples >= -1.0)
        assert np.all(samples <= 1.0)

    def test_pulse_output_range(self, osc):
        """Pulse wave should be in range [-1, 1]."""
        osc.waveform = Waveform.PULSE
        samples = osc.generate(1024)
        assert np.all(samples >= -1.0)
        assert np.all(samples <= 1.0)

    def test_pulse_width_affects_duty_cycle(self, osc):
        """Changing pulse width should change duty cycle."""
        osc.waveform = Waveform.PULSE

        osc.pulse_width = 0.25
        samples_25 = osc.generate(4096)
        high_count_25 = np.sum(samples_25 > 0)

        osc.reset_phase()
        osc.pulse_width = 0.75
        samples_75 = osc.generate(4096)
        high_count_75 = np.sum(samples_75 > 0)

        # 75% pulse width should have more high samples than 25%
        assert high_count_75 > high_count_25


class TestOscillatorFrequency:
    """Tests for frequency accuracy."""

    def test_fundamental_frequency_sine(self):
        """Verify sine wave has correct fundamental frequency."""
        osc = Oscillator(sample_rate=44100)
        osc.waveform = Waveform.SINE
        osc.frequency = 440.0

        # Generate one second of audio
        samples = osc.generate(44100)

        # FFT to find fundamental
        fft = np.abs(np.fft.rfft(samples))
        freqs = np.fft.rfftfreq(len(samples), 1/44100)
        peak_freq = freqs[np.argmax(fft)]

        # Should be within 1 Hz of target
        assert abs(peak_freq - 440.0) < 1.0

    def test_pitch_modulation(self):
        """Pitch modulation should shift frequency."""
        osc = Oscillator(sample_rate=44100)
        osc.frequency = 440.0
        osc.pitch_mod = 12.0  # One octave up

        # Effective frequency should be doubled
        assert abs(osc.effective_frequency - 880.0) < 0.01


class TestOscillatorLevel:
    """Tests for level control."""

    def test_level_scaling(self):
        """Output amplitude should scale with level."""
        osc = Oscillator()
        osc.waveform = Waveform.SINE
        osc.frequency = 440.0

        osc.level = 1.0
        samples_full = osc.generate(1024)
        rms_full = np.sqrt(np.mean(samples_full**2))

        osc.reset_phase()
        osc.level = 0.5
        samples_half = osc.generate(1024)
        rms_half = np.sqrt(np.mean(samples_half**2))

        # Half level should give approximately half RMS
        assert abs(rms_half / rms_full - 0.5) < 0.05

    def test_zero_level(self):
        """Zero level should produce silence."""
        osc = Oscillator()
        osc.waveform = Waveform.SINE
        osc.level = 0.0
        samples = osc.generate(1024)
        assert np.all(samples == 0.0)


class TestOscillatorPhase:
    """Tests for phase handling."""

    def test_phase_continuity(self):
        """Phase should be continuous across generate calls."""
        osc = Oscillator()
        osc.waveform = Waveform.SINE
        osc.frequency = 100.0  # Lower frequency for smoother transitions

        # Generate two buffers in sequence
        samples1 = osc.generate(512)
        samples2 = osc.generate(512)

        # Check that the boundary is smooth (no clicks/pops)
        # At 100 Hz with 44100 sample rate, phase changes ~0.00227 per sample
        # So consecutive samples should differ by at most ~sin(2*pi*0.00227) ~ 0.014
        boundary_diff = abs(samples2[0] - samples1[-1])

        # Also check typical internal differences
        internal_diffs = np.abs(np.diff(samples1))
        avg_internal_diff = np.mean(internal_diffs)

        # Boundary diff should be within reasonable range of internal differences
        # Allow 3x margin for floating point accumulation
        assert boundary_diff < avg_internal_diff * 3.0

    def test_reset_phase(self):
        """Reset phase should start oscillator from beginning."""
        osc = Oscillator()
        osc.waveform = Waveform.SINE
        osc.frequency = 440.0

        samples1 = osc.generate(512)
        first_sample_1 = samples1[0]

        osc.reset_phase()
        samples2 = osc.generate(512)
        first_sample_2 = samples2[0]

        # After reset, first sample should be same (near zero for sine)
        assert abs(first_sample_1 - first_sample_2) < 0.01


class TestOscillatorOutput:
    """Tests for output format."""

    def test_output_dtype(self):
        """Output should be float32."""
        osc = Oscillator()
        samples = osc.generate(512)
        assert samples.dtype == np.float32

    def test_output_length(self):
        """Output should have requested number of samples."""
        osc = Oscillator()
        for length in [64, 128, 256, 512, 1024, 2048]:
            samples = osc.generate(length)
            assert len(samples) == length


class TestOscillatorRepr:
    """Tests for string representation."""

    def test_repr(self):
        """String representation should include key info."""
        osc = Oscillator()
        osc.frequency = 440.0
        osc.waveform = Waveform.SAWTOOTH
        osc.level = 0.8

        repr_str = repr(osc)
        assert '440' in repr_str
        assert 'SAWTOOTH' in repr_str
        assert '0.8' in repr_str
