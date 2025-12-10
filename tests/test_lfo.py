# Tests for LFO module
"""
test_lfo.py - Unit tests for the LFO class

Tests cover:
- LFO initialization
- Frequency and depth parameter handling
- Waveform generation for all types
- Bipolar and unipolar output modes
- Phase reset
- Single sample generation
"""

import pytest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from synth.lfo import LFO
from synth.oscillator import Waveform


class TestLFOInit:
    """Tests for LFO initialization."""

    def test_default_init(self):
        """Test default initialization values."""
        lfo = LFO()
        assert lfo.sample_rate == 44100
        assert lfo.frequency == 5.0
        assert lfo.waveform == Waveform.SINE
        assert lfo.depth == 0.5

    def test_custom_sample_rate(self):
        """Test initialization with custom sample rate."""
        lfo = LFO(sample_rate=48000)
        assert lfo.sample_rate == 48000


class TestLFOProperties:
    """Tests for LFO property getters and setters."""

    def test_frequency_clamping_low(self):
        """Frequency should be clamped to minimum 0.1 Hz."""
        lfo = LFO()
        lfo.frequency = 0.01
        assert lfo.frequency == LFO.MIN_FREQ

    def test_frequency_clamping_high(self):
        """Frequency should be clamped to maximum 50 Hz."""
        lfo = LFO()
        lfo.frequency = 100.0
        assert lfo.frequency == LFO.MAX_FREQ

    def test_depth_clamping(self):
        """Depth should be clamped to 0.0-1.0."""
        lfo = LFO()
        lfo.depth = -0.5
        assert lfo.depth == 0.0
        lfo.depth = 1.5
        assert lfo.depth == 1.0

    def test_waveform_setting(self):
        """Should be able to set any valid waveform."""
        lfo = LFO()
        for waveform in Waveform:
            lfo.waveform = waveform
            assert lfo.waveform == waveform


class TestLFOWaveforms:
    """Tests for LFO waveform generation."""

    @pytest.fixture
    def lfo(self):
        """Create LFO for testing."""
        lfo = LFO(sample_rate=44100)
        lfo.frequency = 5.0
        lfo.depth = 1.0  # Full depth for easier testing
        return lfo

    def test_sine_output_range(self, lfo):
        """Sine wave should be in range [-depth, depth]."""
        lfo.waveform = Waveform.SINE
        samples = lfo.generate(4096)
        assert np.all(samples >= -lfo.depth)
        assert np.all(samples <= lfo.depth)

    def test_sine_reaches_extremes(self, lfo):
        """Sine should reach near -depth and +depth."""
        lfo.waveform = Waveform.SINE
        # Generate enough samples for multiple cycles
        samples = lfo.generate(44100)  # 5 Hz * 1 sec = 5 cycles
        assert np.max(samples) > 0.95 * lfo.depth
        assert np.min(samples) < -0.95 * lfo.depth

    def test_sawtooth_output_range(self, lfo):
        """Sawtooth wave should be in range [-depth, depth]."""
        lfo.waveform = Waveform.SAWTOOTH
        samples = lfo.generate(4096)
        assert np.all(samples >= -lfo.depth)
        assert np.all(samples <= lfo.depth)

    def test_square_binary_output(self, lfo):
        """Square wave should only have values near -depth or +depth."""
        lfo.waveform = Waveform.SQUARE
        samples = lfo.generate(4096)
        # All samples should be close to -depth or +depth
        assert np.all(np.abs(np.abs(samples) - lfo.depth) < 0.01)

    def test_triangle_output_range(self, lfo):
        """Triangle wave should be in range [-depth, depth]."""
        lfo.waveform = Waveform.TRIANGLE
        samples = lfo.generate(4096)
        assert np.all(samples >= -lfo.depth)
        assert np.all(samples <= lfo.depth)

    def test_pulse_output_range(self, lfo):
        """Pulse wave should be in range [-depth, depth]."""
        lfo.waveform = Waveform.PULSE
        samples = lfo.generate(4096)
        assert np.all(samples >= -lfo.depth)
        assert np.all(samples <= lfo.depth)


class TestLFODepth:
    """Tests for depth parameter behavior."""

    def test_zero_depth_produces_zeros(self):
        """Zero depth should produce silent output."""
        lfo = LFO()
        lfo.depth = 0.0
        samples = lfo.generate(1024)
        assert np.all(samples == 0.0)

    def test_depth_scaling(self):
        """Output amplitude should scale with depth."""
        lfo = LFO()
        lfo.waveform = Waveform.SINE
        lfo.frequency = 5.0

        lfo.depth = 1.0
        lfo.reset_phase()
        samples_full = lfo.generate(4096)
        max_full = np.max(np.abs(samples_full))

        lfo.depth = 0.5
        lfo.reset_phase()
        samples_half = lfo.generate(4096)
        max_half = np.max(np.abs(samples_half))

        # Half depth should give approximately half amplitude
        assert abs(max_half / max_full - 0.5) < 0.05


class TestLFOFrequency:
    """Tests for LFO frequency behavior."""

    def test_frequency_affects_period(self):
        """Higher frequency should have shorter period."""
        lfo = LFO(sample_rate=44100)
        lfo.waveform = Waveform.SINE
        lfo.depth = 1.0

        # Count zero crossings for different frequencies
        lfo.frequency = 2.0
        lfo.reset_phase()
        samples_2hz = lfo.generate(44100)

        lfo.frequency = 4.0
        lfo.reset_phase()
        samples_4hz = lfo.generate(44100)

        # Count positive zero crossings
        crossings_2hz = np.sum((samples_2hz[:-1] <= 0) & (samples_2hz[1:] > 0))
        crossings_4hz = np.sum((samples_4hz[:-1] <= 0) & (samples_4hz[1:] > 0))

        # 4 Hz should have approximately double the crossings of 2 Hz
        assert abs(crossings_4hz / crossings_2hz - 2.0) < 0.2


class TestLFOUnipolar:
    """Tests for unipolar output mode."""

    def test_unipolar_always_positive(self):
        """Unipolar output should always be non-negative."""
        lfo = LFO()
        lfo.waveform = Waveform.SINE
        lfo.depth = 1.0
        samples = lfo.generate_unipolar(4096)
        assert np.all(samples >= 0.0)

    def test_unipolar_range(self):
        """Unipolar output should be in range [0, depth]."""
        lfo = LFO()
        lfo.depth = 0.8
        lfo.waveform = Waveform.SINE
        # Generate enough samples for full range
        samples = lfo.generate_unipolar(44100)
        assert np.min(samples) >= 0.0
        assert np.max(samples) <= lfo.depth + 0.01  # Small tolerance


class TestLFOPhase:
    """Tests for phase handling."""

    def test_phase_property(self):
        """Should be able to read current phase."""
        lfo = LFO()
        assert lfo.phase == 0.0

    def test_reset_phase(self):
        """Reset phase should return to zero."""
        lfo = LFO()
        lfo.generate(1000)  # Advance phase
        assert lfo.phase != 0.0  # Phase should have advanced
        lfo.reset_phase()
        assert lfo.phase == 0.0

    def test_phase_continuity(self):
        """Phase should be continuous across generate calls."""
        lfo = LFO()
        lfo.waveform = Waveform.SINE
        lfo.frequency = 5.0

        samples1 = lfo.generate(512)
        samples2 = lfo.generate(512)

        # Check for discontinuity at boundary
        diff = abs(samples2[0] - samples1[-1])
        assert diff < 0.1  # Should be smooth transition


class TestLFOSingleSample:
    """Tests for single sample generation."""

    def test_generate_sample_returns_float(self):
        """generate_sample should return a single float."""
        lfo = LFO()
        value = lfo.generate_sample()
        assert isinstance(value, (float, np.floating))

    def test_generate_sample_in_range(self):
        """Single sample should be in [-depth, depth]."""
        lfo = LFO()
        lfo.depth = 0.7
        for _ in range(1000):
            value = lfo.generate_sample()
            assert -lfo.depth <= value <= lfo.depth

    def test_generate_sample_matches_generate(self):
        """Single sample generation should match bulk generation."""
        lfo = LFO()
        lfo.waveform = Waveform.SINE
        lfo.frequency = 5.0
        lfo.depth = 1.0

        # Reset and generate single samples
        lfo.reset_phase()
        single_samples = [lfo.generate_sample() for _ in range(100)]

        # Reset and generate bulk
        lfo.reset_phase()
        bulk_samples = lfo.generate(100)

        # Should be very close
        np.testing.assert_array_almost_equal(single_samples, bulk_samples, decimal=5)


class TestLFOOutput:
    """Tests for output format."""

    def test_output_dtype(self):
        """Output should be float32."""
        lfo = LFO()
        samples = lfo.generate(512)
        assert samples.dtype == np.float32

    def test_output_length(self):
        """Output should have requested number of samples."""
        lfo = LFO()
        for length in [64, 128, 256, 512, 1024]:
            samples = lfo.generate(length)
            assert len(samples) == length


class TestLFORepr:
    """Tests for string representation."""

    def test_repr(self):
        """String representation should include key info."""
        lfo = LFO()
        lfo.frequency = 3.5
        lfo.depth = 0.7
        lfo.waveform = Waveform.TRIANGLE

        repr_str = repr(lfo)
        assert '3.5' in repr_str or '3.50' in repr_str
        assert 'TRIANGLE' in repr_str
        assert '0.7' in repr_str or '0.70' in repr_str
