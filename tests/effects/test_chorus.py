# Tests for Chorus Effect
"""
test_chorus - Unit tests for chorus effect.
"""

import pytest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from effects.chorus import Chorus


class TestChorusInit:
    """Tests for Chorus initialization."""

    def test_default_init(self):
        """Should initialize with defaults."""
        chorus = Chorus()
        assert chorus.sample_rate == 44100
        assert chorus.rate == 0.5
        assert chorus.depth == 0.5
        assert chorus.voices == 3
        assert chorus.wet_dry == 0.3
        assert not chorus.enabled

    def test_custom_sample_rate(self):
        """Should accept custom sample rate."""
        chorus = Chorus(sample_rate=48000)
        assert chorus.sample_rate == 48000

    def test_custom_rate(self):
        """Should accept custom rate."""
        chorus = Chorus(rate=2.0)
        assert chorus.rate == 2.0

    def test_custom_depth(self):
        """Should accept custom depth."""
        chorus = Chorus(depth=0.8)
        assert chorus.depth == 0.8

    def test_custom_voices(self):
        """Should accept custom voices."""
        chorus = Chorus(voices=4)
        assert chorus.voices == 4

    def test_custom_wet_dry(self):
        """Should accept custom wet/dry."""
        chorus = Chorus(wet_dry=0.5)
        assert chorus.wet_dry == 0.5

    def test_rate_clamped_min(self):
        """Rate should be clamped to minimum."""
        chorus = Chorus(rate=0.01)
        assert chorus.rate == 0.1

    def test_rate_clamped_max(self):
        """Rate should be clamped to maximum."""
        chorus = Chorus(rate=10.0)
        assert chorus.rate == 5.0

    def test_voices_clamped_min(self):
        """Voices should be clamped to minimum."""
        chorus = Chorus(voices=1)
        assert chorus.voices == 2

    def test_voices_clamped_max(self):
        """Voices should be clamped to maximum."""
        chorus = Chorus(voices=8)
        assert chorus.voices == 4


class TestChorusProcess:
    """Tests for Chorus processing."""

    def test_process_output_shape(self):
        """Should return same shape as input."""
        chorus = Chorus()
        chorus.enabled = True
        input_samples = np.random.randn(1024).astype(np.float32)
        output = chorus.process(input_samples)
        assert len(output) == 1024

    def test_process_output_dtype(self):
        """Should return float32."""
        chorus = Chorus()
        chorus.enabled = True
        input_samples = np.random.randn(1024).astype(np.float32)
        output = chorus.process(input_samples)
        assert output.dtype == np.float32

    def test_process_disabled(self):
        """When disabled, should return input unchanged."""
        chorus = Chorus(wet_dry=0.5)
        chorus.enabled = False
        input_samples = np.random.randn(1024).astype(np.float32)
        output = chorus.process(input_samples)
        np.testing.assert_array_almost_equal(output, input_samples)

    def test_process_dry_only(self):
        """With wet_dry=0, should return input unchanged."""
        chorus = Chorus(wet_dry=0.0)
        chorus.enabled = True
        input_samples = np.random.randn(1024).astype(np.float32)
        output = chorus.process(input_samples)
        np.testing.assert_array_almost_equal(output, input_samples)

    def test_process_modifies_signal(self):
        """With chorus enabled, output should differ from input."""
        chorus = Chorus(wet_dry=0.5, depth=0.5)
        chorus.enabled = True

        # Use a simple sine wave
        t = np.linspace(0, 0.1, 4410, dtype=np.float32)
        input_samples = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        output = chorus.process(input_samples)

        # Output should be different from input
        diff = np.abs(output - input_samples)
        assert np.mean(diff) > 0.01

    def test_process_no_clipping(self):
        """Output should not exceed reasonable bounds."""
        chorus = Chorus(wet_dry=1.0, depth=1.0)
        chorus.enabled = True

        input_samples = np.ones(4410, dtype=np.float32) * 0.5
        output = chorus.process(input_samples)

        # Should not clip/overflow
        assert np.max(np.abs(output)) < 2.0


class TestChorusProperties:
    """Tests for Chorus properties."""

    def test_rate_setter(self):
        """Should set rate."""
        chorus = Chorus()
        chorus.rate = 2.5
        assert chorus.rate == 2.5

    def test_rate_clamped_setter(self):
        """Setter should clamp rate."""
        chorus = Chorus()
        chorus.rate = 10.0
        assert chorus.rate == 5.0
        chorus.rate = 0.01
        assert chorus.rate == 0.1

    def test_depth_setter(self):
        """Should set depth."""
        chorus = Chorus()
        chorus.depth = 0.8
        assert chorus.depth == 0.8

    def test_depth_clamped_setter(self):
        """Setter should clamp depth."""
        chorus = Chorus()
        chorus.depth = 1.5
        assert chorus.depth == 1.0
        chorus.depth = -0.5
        assert chorus.depth == 0.0

    def test_voices_setter(self):
        """Should set voices."""
        chorus = Chorus()
        chorus.voices = 4
        assert chorus.voices == 4

    def test_voices_clamped_setter(self):
        """Setter should clamp voices."""
        chorus = Chorus()
        chorus.voices = 8
        assert chorus.voices == 4
        chorus.voices = 1
        assert chorus.voices == 2

    def test_wet_dry_setter(self):
        """Should set wet/dry."""
        chorus = Chorus()
        chorus.wet_dry = 0.8
        assert chorus.wet_dry == 0.8

    def test_enabled_setter(self):
        """Should enable/disable."""
        chorus = Chorus()
        chorus.enabled = True
        assert chorus.enabled
        chorus.enabled = False
        assert not chorus.enabled


class TestChorusReset:
    """Tests for Chorus reset."""

    def test_reset_clears_buffer(self):
        """Reset should clear delay buffer."""
        chorus = Chorus()
        chorus.enabled = True
        # Process some audio
        chorus.process(np.random.randn(4410).astype(np.float32))

        # Reset
        chorus.reset()

        # Process silence - should be silent
        silence = np.zeros(100, dtype=np.float32)
        output = chorus.process(silence)

        # Should be very quiet after reset
        assert np.max(np.abs(output)) < 0.01


class TestChorusVoices:
    """Tests for multi-voice functionality."""

    def test_different_voice_counts(self):
        """Different voice counts should produce different sounds."""
        input_samples = np.random.randn(4410).astype(np.float32)

        chorus2 = Chorus(voices=2, wet_dry=1.0)
        chorus2.enabled = True
        output2 = chorus2.process(input_samples.copy())

        chorus4 = Chorus(voices=4, wet_dry=1.0)
        chorus4.enabled = True
        output4 = chorus4.process(input_samples.copy())

        # Outputs should be different
        diff = np.abs(output2 - output4)
        assert np.mean(diff) > 0.001


class TestChorusRepr:
    """Tests for string representation."""

    def test_repr_enabled(self):
        """Should show enabled status."""
        chorus = Chorus()
        chorus.enabled = True
        assert "enabled" in repr(chorus)

    def test_repr_disabled(self):
        """Should show disabled status."""
        chorus = Chorus()
        assert "disabled" in repr(chorus)

    def test_repr_parameters(self):
        """Should show chorus parameters."""
        chorus = Chorus(rate=1.5, depth=0.7, voices=4)
        repr_str = repr(chorus)
        assert "1.50" in repr_str
        assert "0.70" in repr_str
        assert "4" in repr_str
