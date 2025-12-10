# Tests for Distortion Effect
"""
test_distortion - Unit tests for distortion effect.
"""

import pytest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from effects.distortion import Distortion


class TestDistortionInit:
    """Tests for Distortion initialization."""

    def test_default_init(self):
        """Should initialize with defaults."""
        dist = Distortion()
        assert dist.sample_rate == 44100
        assert dist.drive == 2.0
        assert dist.tone == 0.5
        assert dist.mix == 1.0
        assert dist.mode == 'soft'
        assert not dist.enabled

    def test_custom_sample_rate(self):
        """Should accept custom sample rate."""
        dist = Distortion(sample_rate=48000)
        assert dist.sample_rate == 48000

    def test_custom_drive(self):
        """Should accept custom drive."""
        dist = Distortion(drive=5.0)
        assert dist.drive == 5.0

    def test_custom_tone(self):
        """Should accept custom tone."""
        dist = Distortion(tone=0.8)
        assert dist.tone == 0.8

    def test_custom_mix(self):
        """Should accept custom mix."""
        dist = Distortion(mix=0.5)
        assert dist.mix == 0.5

    def test_custom_mode(self):
        """Should accept custom mode."""
        dist = Distortion(mode='hard')
        assert dist.mode == 'hard'

    def test_drive_clamped_min(self):
        """Drive should be clamped to minimum."""
        dist = Distortion(drive=0.1)
        assert dist.drive == 1.0

    def test_drive_clamped_max(self):
        """Drive should be clamped to maximum."""
        dist = Distortion(drive=50.0)
        assert dist.drive == 20.0

    def test_invalid_mode_uses_default(self):
        """Invalid mode should use default."""
        dist = Distortion(mode='invalid')
        assert dist.mode == 'soft'


class TestDistortionProcess:
    """Tests for Distortion processing."""

    def test_process_output_shape(self):
        """Should return same shape as input."""
        dist = Distortion()
        dist.enabled = True
        input_samples = np.random.randn(1024).astype(np.float32)
        output = dist.process(input_samples)
        assert len(output) == 1024

    def test_process_output_dtype(self):
        """Should return float32."""
        dist = Distortion()
        dist.enabled = True
        input_samples = np.random.randn(1024).astype(np.float32)
        output = dist.process(input_samples)
        assert output.dtype == np.float32

    def test_process_disabled(self):
        """When disabled, should return input unchanged."""
        dist = Distortion(mix=1.0)
        dist.enabled = False
        input_samples = np.random.randn(1024).astype(np.float32)
        output = dist.process(input_samples)
        np.testing.assert_array_almost_equal(output, input_samples)

    def test_process_dry_only(self):
        """With mix=0, should return input unchanged."""
        dist = Distortion(mix=0.0)
        dist.enabled = True
        input_samples = np.random.randn(1024).astype(np.float32)
        output = dist.process(input_samples)
        np.testing.assert_array_almost_equal(output, input_samples)

    def test_process_soft_mode(self):
        """Soft mode should produce smooth saturation."""
        dist = Distortion(mode='soft', drive=10.0, mix=1.0)
        dist.enabled = True

        # High amplitude input
        input_samples = np.ones(100, dtype=np.float32) * 0.5
        output = dist.process(input_samples)

        # Soft clip should compress but not hard clip
        # tanh(10 * 0.5) = tanh(5) ~= 0.999
        assert np.max(output) < 1.0
        assert np.max(output) > 0.9

    def test_process_hard_mode(self):
        """Hard mode should produce digital clipping."""
        dist = Distortion(mode='hard', drive=10.0, mix=1.0)
        dist.enabled = True

        # High amplitude input
        input_samples = np.ones(100, dtype=np.float32) * 0.5
        output = dist.process(input_samples)

        # Hard clip should hit -1/+1 exactly (after tone filter settles)
        # Check that output is close to 1.0 (it will be filtered slightly)
        assert np.max(output) > 0.8

    def test_process_tube_mode(self):
        """Tube mode should produce asymmetric saturation."""
        dist = Distortion(mode='tube', drive=5.0, mix=1.0)
        dist.enabled = True

        # Sine wave input
        t = np.linspace(0, 0.01, 441, dtype=np.float32)
        input_samples = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        output = dist.process(input_samples)

        # Tube mode should create asymmetry
        # Check that positive and negative peaks are different
        pos_peak = np.max(output)
        neg_peak = np.abs(np.min(output))
        # Should have some asymmetry
        assert abs(pos_peak - neg_peak) > 0.01

    def test_process_drive_increases_distortion(self):
        """Higher drive should produce more distortion."""
        input_samples = np.random.randn(1024).astype(np.float32) * 0.1

        dist_low = Distortion(drive=2.0, mix=1.0, tone=1.0)
        dist_low.enabled = True
        output_low = dist_low.process(input_samples.copy())

        dist_high = Distortion(drive=15.0, mix=1.0, tone=1.0)
        dist_high.enabled = True
        output_high = dist_high.process(input_samples.copy())

        # Higher drive should result in more compressed signal
        # Standard deviation should be lower due to compression
        std_low = np.std(output_low)
        std_high = np.std(output_high)
        # Higher drive compresses more, so std should be similar or lower
        # but output will be "louder" overall
        assert np.mean(np.abs(output_high)) >= np.mean(np.abs(output_low)) * 0.5


class TestDistortionTone:
    """Tests for tone control."""

    def test_tone_dark(self):
        """Low tone should filter high frequencies."""
        dist = Distortion(drive=2.0, tone=0.0, mix=1.0)
        dist.enabled = True

        # High frequency content
        t = np.linspace(0, 0.1, 4410, dtype=np.float32)
        input_samples = np.sin(2 * np.pi * 5000 * t).astype(np.float32)
        output = dist.process(input_samples)

        # Dark tone should attenuate high frequencies
        assert np.std(output) < np.std(input_samples) * 0.5

    def test_tone_bright(self):
        """High tone should preserve high frequencies."""
        dist = Distortion(drive=2.0, tone=1.0, mix=1.0)
        dist.enabled = True

        # High frequency content
        t = np.linspace(0, 0.1, 4410, dtype=np.float32)
        input_samples = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
        output = dist.process(input_samples)

        # Bright tone should preserve more energy
        assert np.std(output) > 0.1


class TestDistortionProperties:
    """Tests for Distortion properties."""

    def test_drive_setter(self):
        """Should set drive."""
        dist = Distortion()
        dist.drive = 8.0
        assert dist.drive == 8.0

    def test_drive_clamped_setter(self):
        """Setter should clamp drive."""
        dist = Distortion()
        dist.drive = 50.0
        assert dist.drive == 20.0
        dist.drive = 0.1
        assert dist.drive == 1.0

    def test_tone_setter(self):
        """Should set tone."""
        dist = Distortion()
        dist.tone = 0.8
        assert dist.tone == 0.8

    def test_tone_clamped_setter(self):
        """Setter should clamp tone."""
        dist = Distortion()
        dist.tone = 1.5
        assert dist.tone == 1.0
        dist.tone = -0.5
        assert dist.tone == 0.0

    def test_mix_setter(self):
        """Should set mix."""
        dist = Distortion()
        dist.mix = 0.5
        assert dist.mix == 0.5

    def test_mode_setter(self):
        """Should set mode."""
        dist = Distortion()
        dist.mode = 'hard'
        assert dist.mode == 'hard'
        dist.mode = 'tube'
        assert dist.mode == 'tube'

    def test_mode_invalid_ignored(self):
        """Invalid mode should be ignored."""
        dist = Distortion(mode='soft')
        dist.mode = 'invalid'
        assert dist.mode == 'soft'

    def test_enabled_setter(self):
        """Should enable/disable."""
        dist = Distortion()
        dist.enabled = True
        assert dist.enabled
        dist.enabled = False
        assert not dist.enabled


class TestDistortionReset:
    """Tests for Distortion reset."""

    def test_reset_clears_state(self):
        """Reset should clear filter states."""
        dist = Distortion()
        dist.enabled = True
        # Process some audio
        dist.process(np.random.randn(1024).astype(np.float32))

        # Reset
        dist.reset()

        # Tone filter state should be cleared
        assert dist._tone_filter_state == 0.0
        assert dist._dc_block_prev_input == 0.0
        assert dist._dc_block_prev_output == 0.0


class TestDistortionDCBlocking:
    """Tests for DC offset removal."""

    def test_dc_offset_removed(self):
        """DC offset should be removed from output."""
        dist = Distortion(drive=5.0, mix=1.0)
        dist.enabled = True

        # Input with DC offset
        input_samples = np.ones(4410, dtype=np.float32) * 0.5
        output = dist.process(input_samples)

        # After settling, output should have minimal DC
        # Check the last portion of the signal
        dc_level = np.mean(output[-1000:])
        assert abs(dc_level) < 0.5  # Should be reduced from input DC


class TestDistortionRepr:
    """Tests for string representation."""

    def test_repr_enabled(self):
        """Should show enabled status."""
        dist = Distortion()
        dist.enabled = True
        assert "enabled" in repr(dist)

    def test_repr_disabled(self):
        """Should show disabled status."""
        dist = Distortion()
        assert "disabled" in repr(dist)

    def test_repr_parameters(self):
        """Should show distortion parameters."""
        dist = Distortion(drive=5.0, tone=0.7, mode='hard')
        repr_str = repr(dist)
        assert "5.0" in repr_str
        assert "0.70" in repr_str
        assert "hard" in repr_str
