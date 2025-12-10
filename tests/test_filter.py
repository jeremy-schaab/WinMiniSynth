# Tests for Moog Filter module
"""
test_filter.py - Unit tests for the MoogFilter class

Tests cover:
- Filter initialization
- Cutoff and resonance parameter handling
- Lowpass filter response
- Resonance behavior
- Filter state reset
- Frequency response calculation
"""

import pytest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from synth.filter import MoogFilter


class TestFilterInit:
    """Tests for MoogFilter initialization."""

    def test_default_init(self):
        """Test default initialization values."""
        filt = MoogFilter()
        assert filt.sample_rate == 44100
        assert filt.cutoff == 1000.0
        assert filt.resonance == 0.0

    def test_custom_sample_rate(self):
        """Test initialization with custom sample rate."""
        filt = MoogFilter(sample_rate=48000)
        assert filt.sample_rate == 48000
        assert filt.nyquist == 24000.0


class TestFilterProperties:
    """Tests for filter property getters and setters."""

    def test_cutoff_clamping_low(self):
        """Cutoff should be clamped to minimum 20 Hz."""
        filt = MoogFilter()
        filt.cutoff = 5.0
        assert filt.cutoff == 20.0

    def test_cutoff_clamping_high(self):
        """Cutoff should be clamped to below Nyquist."""
        filt = MoogFilter(sample_rate=44100)
        filt.cutoff = 25000.0
        assert filt.cutoff < filt.nyquist

    def test_resonance_clamping(self):
        """Resonance should be clamped to 0.0-1.0."""
        filt = MoogFilter()
        filt.resonance = -0.5
        assert filt.resonance == 0.0
        filt.resonance = 1.5
        assert filt.resonance == 1.0

    def test_cutoff_modulation(self):
        """Cutoff modulation should affect effective cutoff."""
        filt = MoogFilter()
        filt.cutoff = 1000.0
        filt.cutoff_mod = 1.0  # +1 octave (4x with 4.0 multiplier)

        # Effective cutoff should be higher
        assert filt.effective_cutoff > filt.cutoff


class TestFilterProcessing:
    """Tests for filter audio processing."""

    @pytest.fixture
    def filt(self):
        """Create filter for testing."""
        return MoogFilter(sample_rate=44100)

    @pytest.fixture
    def noise(self):
        """Create white noise test signal."""
        np.random.seed(42)
        return np.random.uniform(-1.0, 1.0, 4096).astype(np.float32)

    @pytest.fixture
    def sine_1khz(self):
        """Create 1kHz sine wave test signal."""
        t = np.arange(4096) / 44100
        return np.sin(2 * np.pi * 1000 * t).astype(np.float32)

    def test_output_shape(self, filt, noise):
        """Output should have same length as input."""
        output = filt.process(noise)
        assert len(output) == len(noise)

    def test_output_dtype(self, filt, noise):
        """Output should be float32."""
        output = filt.process(noise)
        assert output.dtype == np.float32

    def test_lowpass_attenuates_high_frequencies(self, filt, noise):
        """Filter should attenuate frequencies above cutoff."""
        filt.cutoff = 1000.0
        filt.resonance = 0.0

        # Get spectrum of input and output
        input_spectrum = np.abs(np.fft.rfft(noise))
        output = filt.process(noise)
        output_spectrum = np.abs(np.fft.rfft(output))

        freqs = np.fft.rfftfreq(len(noise), 1/44100)

        # Find index of 5000 Hz (well above cutoff)
        high_freq_idx = np.argmin(np.abs(freqs - 5000))

        # Compare energy at high frequencies
        input_high_energy = np.mean(input_spectrum[high_freq_idx:])
        output_high_energy = np.mean(output_spectrum[high_freq_idx:])

        # High frequencies should be attenuated
        assert output_high_energy < input_high_energy * 0.5

    def test_lowpass_passes_low_frequencies(self, filt):
        """Filter should pass frequencies well below cutoff."""
        filt.cutoff = 5000.0
        filt.resonance = 0.0

        # Create 200 Hz sine (well below cutoff)
        t = np.arange(4096) / 44100
        low_sine = np.sin(2 * np.pi * 200 * t).astype(np.float32)

        output = filt.process(low_sine)

        # Calculate RMS of input and output
        input_rms = np.sqrt(np.mean(low_sine**2))
        output_rms = np.sqrt(np.mean(output**2))

        # Low frequency should pass with minimal attenuation
        # Allow some attenuation due to filter warm-up
        assert output_rms > input_rms * 0.5

    def test_cutoff_affects_brightness(self, filt, noise):
        """Lower cutoff should produce darker (less bright) sound."""
        filt.resonance = 0.0

        # High cutoff
        filt.cutoff = 10000.0
        filt.reset()
        output_bright = filt.process(noise.copy())

        # Low cutoff
        filt.cutoff = 500.0
        filt.reset()
        output_dark = filt.process(noise.copy())

        # Compare high-frequency content
        freqs = np.fft.rfftfreq(len(noise), 1/44100)
        high_freq_mask = freqs > 2000

        bright_high_energy = np.sum(np.abs(np.fft.rfft(output_bright))[high_freq_mask])
        dark_high_energy = np.sum(np.abs(np.fft.rfft(output_dark))[high_freq_mask])

        # Lower cutoff should have less high frequency energy
        assert dark_high_energy < bright_high_energy


class TestFilterResonance:
    """Tests for filter resonance behavior."""

    @pytest.fixture
    def noise(self):
        """Create white noise test signal."""
        np.random.seed(42)
        return np.random.uniform(-1.0, 1.0, 8192).astype(np.float32)

    def test_resonance_creates_peak(self, noise):
        """High resonance should create peak at cutoff frequency."""
        filt = MoogFilter(sample_rate=44100)
        filt.cutoff = 2000.0
        filt.resonance = 0.9

        output = filt.process(noise)
        spectrum = np.abs(np.fft.rfft(output))
        freqs = np.fft.rfftfreq(len(noise), 1/44100)

        # Find peak frequency
        peak_idx = np.argmax(spectrum[:len(spectrum)//4])  # Look in lower half
        peak_freq = freqs[peak_idx]

        # Peak should be somewhat near cutoff (within factor of 2)
        # Note: Filter response can shift peak frequency
        assert 500 < peak_freq < 4000

    def test_zero_resonance_no_emphasis(self, noise):
        """Zero resonance should not create resonant peak."""
        filt = MoogFilter(sample_rate=44100)
        filt.cutoff = 2000.0
        filt.resonance = 0.0

        output = filt.process(noise)
        spectrum = np.abs(np.fft.rfft(output))

        # Spectrum should be monotonically decreasing (roughly)
        # Check that early spectrum is higher than late spectrum
        early_energy = np.mean(spectrum[:len(spectrum)//8])
        late_energy = np.mean(spectrum[len(spectrum)//2:])

        assert early_energy > late_energy


class TestFilterReset:
    """Tests for filter state reset."""

    def test_reset_clears_state(self):
        """reset() should clear filter state."""
        filt = MoogFilter()
        noise = np.random.uniform(-1.0, 1.0, 1024).astype(np.float32)

        # Process some audio
        filt.process(noise)

        # Reset and check state
        filt.reset()
        assert np.all(filt._stage == 0.0)

    def test_reset_produces_same_output(self):
        """Same input after reset should produce same output."""
        filt = MoogFilter()
        filt.cutoff = 1000.0
        filt.resonance = 0.5

        noise = np.random.uniform(-1.0, 1.0, 1024).astype(np.float32)

        # First process
        filt.reset()
        output1 = filt.process(noise.copy())

        # Reset and process again
        filt.reset()
        output2 = filt.process(noise.copy())

        # Should be identical
        np.testing.assert_array_almost_equal(output1, output2)


class TestFilterFrequencyResponse:
    """Tests for frequency response calculation."""

    def test_response_shape(self):
        """Frequency response should have same length as input."""
        filt = MoogFilter()
        freqs = np.linspace(20, 20000, 512)
        response = filt.get_frequency_response(freqs)
        assert len(response) == len(freqs)

    def test_response_lowpass_shape(self):
        """Response should decrease with increasing frequency."""
        filt = MoogFilter()
        filt.cutoff = 1000.0
        filt.resonance = 0.0

        freqs = np.array([100, 500, 1000, 5000, 10000])
        response = filt.get_frequency_response(freqs)

        # Response should generally decrease
        # (may not be monotonic with resonance)
        assert response[0] > response[-1]

    def test_response_dtype(self):
        """Response should be float32."""
        filt = MoogFilter()
        freqs = np.linspace(20, 20000, 100)
        response = filt.get_frequency_response(freqs)
        assert response.dtype == np.float32


class TestFilterStability:
    """Tests for filter numerical stability."""

    def test_no_nan_output(self):
        """Filter should not produce NaN values."""
        filt = MoogFilter()
        filt.cutoff = 1000.0
        filt.resonance = 0.95  # High resonance

        # Process noise
        noise = np.random.uniform(-1.0, 1.0, 4096).astype(np.float32)
        output = filt.process(noise)

        assert not np.any(np.isnan(output))

    def test_no_inf_output(self):
        """Filter should not produce infinite values."""
        filt = MoogFilter()
        filt.cutoff = 1000.0
        filt.resonance = 0.99  # Very high resonance

        # Process noise
        noise = np.random.uniform(-1.0, 1.0, 4096).astype(np.float32)
        output = filt.process(noise)

        assert not np.any(np.isinf(output))

    def test_bounded_output(self):
        """Output should remain bounded with high resonance."""
        filt = MoogFilter()
        filt.cutoff = 1000.0
        filt.resonance = 0.95

        # Process noise
        noise = np.random.uniform(-1.0, 1.0, 8192).astype(np.float32)
        output = filt.process(noise)

        # Output should be within reasonable bounds
        # Resonance can amplify but tanh saturation should limit
        assert np.max(np.abs(output)) < 10.0


class TestFilterRepr:
    """Tests for string representation."""

    def test_repr(self):
        """String representation should include key info."""
        filt = MoogFilter()
        filt.cutoff = 2500.0
        filt.resonance = 0.6

        repr_str = repr(filt)
        assert '2500' in repr_str
        assert '0.6' in repr_str or 'resonance' in repr_str.lower()
