# Tests for Reverb Effect
"""
test_reverb - Unit tests for Schroeder reverb effect.
"""

import pytest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from effects.reverb import Reverb, CombFilter, AllpassFilter


class TestCombFilter:
    """Tests for CombFilter class."""

    def test_init_default(self):
        """Should initialize with default feedback."""
        comb = CombFilter(100)
        assert comb.feedback == 0.84

    def test_init_custom_feedback(self):
        """Should accept custom feedback."""
        comb = CombFilter(100, feedback=0.7)
        assert comb.feedback == 0.7

    def test_process_initial_output_zero(self):
        """First output should be zero (no delay yet)."""
        comb = CombFilter(100)
        output = comb.process(1.0)
        assert output == 0.0

    def test_process_delayed_output(self):
        """Output should be delayed input."""
        comb = CombFilter(10, feedback=0.0)
        # Feed impulse
        comb.process(1.0)
        # Process 9 zeros
        for _ in range(9):
            comb.process(0.0)
        # 10th output should be the impulse
        output = comb.process(0.0)
        assert output == 1.0

    def test_process_block(self):
        """Should process block correctly."""
        comb = CombFilter(10)
        input_samples = np.ones(20, dtype=np.float32)
        output = comb.process_block(input_samples)
        assert len(output) == 20
        assert output.dtype == np.float32

    def test_reset(self):
        """Should reset internal state."""
        comb = CombFilter(10)
        comb.process_block(np.ones(10, dtype=np.float32))
        comb.reset()
        # After reset, first output should be zero again
        output = comb.process(1.0)
        assert output == 0.0

    def test_feedback_clamped(self):
        """Feedback should be clamped to valid range."""
        comb = CombFilter(100)
        comb.feedback = 1.5
        assert comb.feedback <= 0.99
        comb.feedback = -0.5
        assert comb.feedback >= 0.0


class TestAllpassFilter:
    """Tests for AllpassFilter class."""

    def test_init_default(self):
        """Should initialize with default gain."""
        allpass = AllpassFilter(100)
        assert allpass._gain == 0.5

    def test_init_custom_gain(self):
        """Should accept custom gain."""
        allpass = AllpassFilter(100, gain=0.7)
        assert allpass._gain == 0.7

    def test_process_block(self):
        """Should process block correctly."""
        allpass = AllpassFilter(10)
        input_samples = np.ones(20, dtype=np.float32)
        output = allpass.process_block(input_samples)
        assert len(output) == 20
        assert output.dtype == np.float32

    def test_reset(self):
        """Should reset internal state."""
        allpass = AllpassFilter(10)
        allpass.process_block(np.ones(10, dtype=np.float32))
        allpass.reset()
        # State should be cleared
        assert allpass._write_pos == 0
        assert np.allclose(allpass._buffer, 0.0)


class TestReverbInit:
    """Tests for Reverb initialization."""

    def test_default_init(self):
        """Should initialize with defaults."""
        reverb = Reverb()
        assert reverb.sample_rate == 44100
        assert reverb.wet_dry == 0.3
        assert reverb.room_size == 0.5
        assert reverb.enabled

    def test_custom_sample_rate(self):
        """Should accept custom sample rate."""
        reverb = Reverb(sample_rate=48000)
        assert reverb.sample_rate == 48000

    def test_custom_wet_dry(self):
        """Should accept custom wet/dry."""
        reverb = Reverb(wet_dry=0.5)
        assert reverb.wet_dry == 0.5

    def test_custom_room_size(self):
        """Should accept custom room size."""
        reverb = Reverb(room_size=0.8)
        assert reverb.room_size == 0.8

    def test_wet_dry_clamped(self):
        """Wet/dry should be clamped to 0-1."""
        reverb = Reverb(wet_dry=1.5)
        assert reverb.wet_dry == 1.0
        reverb = Reverb(wet_dry=-0.5)
        assert reverb.wet_dry == 0.0

    def test_room_size_clamped(self):
        """Room size should be clamped to 0-1."""
        reverb = Reverb(room_size=1.5)
        assert reverb.room_size == 1.0
        reverb = Reverb(room_size=-0.5)
        assert reverb.room_size == 0.0


class TestReverbProcess:
    """Tests for Reverb processing."""

    def test_process_output_shape(self):
        """Should return same shape as input."""
        reverb = Reverb()
        input_samples = np.random.randn(1024).astype(np.float32)
        output = reverb.process(input_samples)
        assert len(output) == 1024

    def test_process_output_dtype(self):
        """Should return float32."""
        reverb = Reverb()
        input_samples = np.random.randn(1024).astype(np.float32)
        output = reverb.process(input_samples)
        assert output.dtype == np.float32

    def test_process_dry_only(self):
        """With wet_dry=0, should return input unchanged."""
        reverb = Reverb(wet_dry=0.0)
        input_samples = np.random.randn(1024).astype(np.float32)
        output = reverb.process(input_samples)
        np.testing.assert_array_almost_equal(output, input_samples)

    def test_process_disabled(self):
        """When disabled, should return input unchanged."""
        reverb = Reverb(wet_dry=0.5)
        reverb.enabled = False
        input_samples = np.random.randn(1024).astype(np.float32)
        output = reverb.process(input_samples)
        np.testing.assert_array_almost_equal(output, input_samples)

    def test_process_adds_reverb(self):
        """With wet_dry > 0, output should differ from input."""
        reverb = Reverb(wet_dry=0.5)
        input_samples = np.zeros(2048, dtype=np.float32)
        input_samples[0] = 1.0  # Impulse
        output = reverb.process(input_samples)

        # After processing impulse, reverb tail should have non-zero values
        # Check samples after the initial impulse
        assert np.abs(output[100:]).max() > 0.0

    def test_process_wet_scaling(self):
        """Higher wet should have more reverb."""
        input_samples = np.zeros(2048, dtype=np.float32)
        input_samples[0] = 1.0

        reverb_low = Reverb(wet_dry=0.2)
        reverb_high = Reverb(wet_dry=0.8)

        output_low = reverb_low.process(input_samples.copy())
        output_high = reverb_high.process(input_samples.copy())

        # Higher wet should have larger tail amplitude
        tail_low = np.abs(output_low[500:]).mean()
        tail_high = np.abs(output_high[500:]).mean()
        assert tail_high > tail_low


class TestReverbProperties:
    """Tests for Reverb properties."""

    def test_wet_dry_setter(self):
        """Should set wet/dry."""
        reverb = Reverb()
        reverb.wet_dry = 0.7
        assert reverb.wet_dry == 0.7

    def test_wet_dry_clamped_setter(self):
        """Setter should clamp wet/dry."""
        reverb = Reverb()
        reverb.wet_dry = 1.5
        assert reverb.wet_dry == 1.0
        reverb.wet_dry = -0.5
        assert reverb.wet_dry == 0.0

    def test_room_size_setter(self):
        """Should set room size."""
        reverb = Reverb()
        reverb.room_size = 0.8
        assert reverb.room_size == 0.8

    def test_room_size_rebuilds_filters(self):
        """Setting room size should rebuild filters."""
        reverb = Reverb(room_size=0.3)
        old_delay = reverb._comb_filters[0]._delay_samples
        reverb.room_size = 0.9
        new_delay = reverb._comb_filters[0]._delay_samples
        # Larger room = longer delay
        assert new_delay > old_delay

    def test_enabled_setter(self):
        """Should enable/disable."""
        reverb = Reverb()
        reverb.enabled = False
        assert not reverb.enabled
        reverb.enabled = True
        assert reverb.enabled


class TestReverbReset:
    """Tests for Reverb reset."""

    def test_reset_clears_state(self):
        """Reset should clear all filter states."""
        reverb = Reverb()
        # Process some audio
        reverb.process(np.random.randn(1024).astype(np.float32))

        # Reset
        reverb.reset()

        # Process impulse - should have clean response
        impulse = np.zeros(100, dtype=np.float32)
        impulse[0] = 1.0
        output = reverb.process(impulse)

        # First output should be close to the dry signal
        assert abs(output[0] - (1.0 * (1 - reverb.wet_dry))) < 0.1


class TestReverbRepr:
    """Tests for string representation."""

    def test_repr_enabled(self):
        """Should show enabled status."""
        reverb = Reverb()
        assert "enabled" in repr(reverb)

    def test_repr_disabled(self):
        """Should show disabled status."""
        reverb = Reverb()
        reverb.enabled = False
        assert "disabled" in repr(reverb)

    def test_repr_parameters(self):
        """Should show wet_dry and room_size."""
        reverb = Reverb(wet_dry=0.4, room_size=0.6)
        repr_str = repr(reverb)
        assert "0.40" in repr_str
        assert "0.60" in repr_str
