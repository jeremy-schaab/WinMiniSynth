# Tests for Delay Effect
"""
test_delay - Unit tests for digital delay effect.
"""

import pytest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from effects.delay import Delay


class TestDelayInit:
    """Tests for Delay initialization."""

    def test_default_init(self):
        """Should initialize with defaults."""
        delay = Delay()
        assert delay.sample_rate == 44100
        assert delay.delay_time_ms == 300
        assert delay.feedback == 0.4
        assert delay.wet_dry == 0.3
        assert not delay.enabled

    def test_custom_sample_rate(self):
        """Should accept custom sample rate."""
        delay = Delay(sample_rate=48000)
        assert delay.sample_rate == 48000

    def test_custom_delay_time(self):
        """Should accept custom delay time."""
        delay = Delay(delay_time_ms=500)
        assert delay.delay_time_ms == 500

    def test_custom_feedback(self):
        """Should accept custom feedback."""
        delay = Delay(feedback=0.6)
        assert delay.feedback == 0.6

    def test_custom_wet_dry(self):
        """Should accept custom wet/dry."""
        delay = Delay(wet_dry=0.5)
        assert delay.wet_dry == 0.5

    def test_delay_time_clamped_min(self):
        """Delay time should be clamped to minimum."""
        delay = Delay(delay_time_ms=1)
        assert delay.delay_time_ms == 10

    def test_delay_time_clamped_max(self):
        """Delay time should be clamped to maximum."""
        delay = Delay(delay_time_ms=5000)
        assert delay.delay_time_ms == 2000

    def test_feedback_clamped_max(self):
        """Feedback should be clamped to 0.95."""
        delay = Delay(feedback=1.0)
        assert delay.feedback == 0.95

    def test_feedback_clamped_min(self):
        """Feedback should be clamped to 0."""
        delay = Delay(feedback=-0.5)
        assert delay.feedback == 0.0


class TestDelayProcess:
    """Tests for Delay processing."""

    def test_process_output_shape(self):
        """Should return same shape as input."""
        delay = Delay()
        delay.enabled = True
        input_samples = np.random.randn(1024).astype(np.float32)
        output = delay.process(input_samples)
        assert len(output) == 1024

    def test_process_output_dtype(self):
        """Should return float32."""
        delay = Delay()
        delay.enabled = True
        input_samples = np.random.randn(1024).astype(np.float32)
        output = delay.process(input_samples)
        assert output.dtype == np.float32

    def test_process_disabled(self):
        """When disabled, should return input unchanged."""
        delay = Delay(wet_dry=0.5)
        delay.enabled = False
        input_samples = np.random.randn(1024).astype(np.float32)
        output = delay.process(input_samples)
        np.testing.assert_array_almost_equal(output, input_samples)

    def test_process_dry_only(self):
        """With wet_dry=0, should return input unchanged."""
        delay = Delay(wet_dry=0.0)
        delay.enabled = True
        input_samples = np.random.randn(1024).astype(np.float32)
        output = delay.process(input_samples)
        np.testing.assert_array_almost_equal(output, input_samples)

    def test_process_creates_echo(self):
        """Should create delayed echo."""
        delay = Delay(delay_time_ms=100, feedback=0.0, wet_dry=0.5)
        delay.enabled = True

        # Create impulse
        input_samples = np.zeros(8820, dtype=np.float32)  # 200ms at 44100
        input_samples[0] = 1.0

        output = delay.process(input_samples)

        # Find the echo around sample 4410 (100ms delay)
        delay_samples = int(0.1 * 44100)
        echo_region = output[delay_samples - 10:delay_samples + 10]
        assert np.max(np.abs(echo_region)) > 0.1

    def test_process_feedback_creates_repeats(self):
        """With feedback, should create multiple echoes."""
        delay = Delay(delay_time_ms=50, feedback=0.5, wet_dry=0.8)
        delay.enabled = True

        # Create impulse
        input_samples = np.zeros(22050, dtype=np.float32)  # 500ms at 44100
        input_samples[0] = 1.0

        output = delay.process(input_samples)

        # Check for multiple echoes
        delay_samples = int(0.05 * 44100)
        first_echo = np.max(np.abs(output[delay_samples - 5:delay_samples + 5]))
        second_echo = np.max(np.abs(output[delay_samples * 2 - 5:delay_samples * 2 + 5]))

        assert first_echo > 0.1
        assert second_echo > 0.01  # Should be quieter due to feedback


class TestDelayProperties:
    """Tests for Delay properties."""

    def test_delay_time_setter(self):
        """Should set delay time."""
        delay = Delay()
        delay.delay_time_ms = 500
        assert delay.delay_time_ms == 500

    def test_delay_time_clamped_setter(self):
        """Setter should clamp delay time."""
        delay = Delay()
        delay.delay_time_ms = 5000
        assert delay.delay_time_ms == 2000
        delay.delay_time_ms = 1
        assert delay.delay_time_ms == 10

    def test_feedback_setter(self):
        """Should set feedback."""
        delay = Delay()
        delay.feedback = 0.7
        assert delay.feedback == 0.7

    def test_feedback_clamped_setter(self):
        """Setter should clamp feedback."""
        delay = Delay()
        delay.feedback = 1.0
        assert delay.feedback == 0.95

    def test_wet_dry_setter(self):
        """Should set wet/dry."""
        delay = Delay()
        delay.wet_dry = 0.8
        assert delay.wet_dry == 0.8

    def test_enabled_setter(self):
        """Should enable/disable."""
        delay = Delay()
        delay.enabled = True
        assert delay.enabled
        delay.enabled = False
        assert not delay.enabled


class TestDelayTempoSync:
    """Tests for tempo sync functionality."""

    def test_sync_quarter_note(self):
        """Should calculate quarter note delay."""
        delay = Delay()
        # At 120 BPM, quarter note = 500ms
        delay_ms = delay.sync_to_tempo(120, "1/4")
        assert abs(delay_ms - 500) < 1

    def test_sync_eighth_note(self):
        """Should calculate eighth note delay."""
        delay = Delay()
        # At 120 BPM, eighth note = 250ms
        delay_ms = delay.sync_to_tempo(120, "1/8")
        assert abs(delay_ms - 250) < 1

    def test_sync_dotted_eighth(self):
        """Should calculate dotted eighth note delay."""
        delay = Delay()
        # At 120 BPM, dotted eighth = 375ms
        delay_ms = delay.sync_to_tempo(120, "1/8.")
        assert abs(delay_ms - 375) < 1

    def test_sync_updates_delay_time(self):
        """Sync should update delay_time_ms property."""
        delay = Delay()
        delay.sync_to_tempo(120, "1/4")
        assert abs(delay.delay_time_ms - 500) < 1


class TestDelayReset:
    """Tests for Delay reset."""

    def test_reset_clears_buffer(self):
        """Reset should clear delay buffer."""
        delay = Delay()
        delay.enabled = True
        # Process some audio
        delay.process(np.random.randn(1024).astype(np.float32))

        # Reset
        delay.reset()

        # Process impulse - should have clean response (no previous audio)
        impulse = np.zeros(1000, dtype=np.float32)
        impulse[0] = 1.0
        output = delay.process(impulse)

        # Early samples should be mostly the dry signal
        assert abs(output[0] - (1.0 * (1 - delay.wet_dry))) < 0.1


class TestDelayRepr:
    """Tests for string representation."""

    def test_repr_enabled(self):
        """Should show enabled status."""
        delay = Delay()
        delay.enabled = True
        assert "enabled" in repr(delay)

    def test_repr_disabled(self):
        """Should show disabled status."""
        delay = Delay()
        assert "disabled" in repr(delay)

    def test_repr_parameters(self):
        """Should show delay parameters."""
        delay = Delay(delay_time_ms=400, feedback=0.5)
        repr_str = repr(delay)
        assert "400" in repr_str
        assert "0.50" in repr_str
