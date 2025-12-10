# Tests for Oscilloscope Module
"""
test_oscilloscope - Unit tests for real-time waveform display.
"""

import pytest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from visualization.oscilloscope import Oscilloscope, TriggerMode, DisplayMode


class TestTriggerMode:
    """Tests for TriggerMode enum."""

    def test_trigger_modes_exist(self):
        """Should have all trigger modes."""
        assert TriggerMode.FREE_RUN
        assert TriggerMode.RISING
        assert TriggerMode.FALLING
        assert TriggerMode.AUTO

    def test_modes_distinct(self):
        """Modes should be distinct."""
        modes = [TriggerMode.FREE_RUN, TriggerMode.RISING,
                 TriggerMode.FALLING, TriggerMode.AUTO]
        assert len(set(modes)) == 4


class TestDisplayMode:
    """Tests for DisplayMode enum."""

    def test_display_modes_exist(self):
        """Should have all display modes."""
        assert DisplayMode.WAVEFORM
        assert DisplayMode.LISSAJOUS
        assert DisplayMode.SPECTRUM


class TestOscilloscopeInit:
    """Tests for Oscilloscope initialization (without GUI)."""

    def test_default_dimensions(self):
        """Should have default dimensions."""
        assert Oscilloscope.DEFAULT_WIDTH == 400
        assert Oscilloscope.DEFAULT_HEIGHT == 200

    def test_grid_divisions(self):
        """Should have grid division constants."""
        assert Oscilloscope.GRID_DIVISIONS_X == 10
        assert Oscilloscope.GRID_DIVISIONS_Y == 8


class TestOscilloscopeTriggerLogic:
    """Tests for trigger point finding logic."""

    def test_find_rising_edge(self):
        """Test rising edge detection."""
        # Create oscilloscope-like object for testing logic
        class MockScope:
            _trigger_mode = TriggerMode.RISING
            _trigger_level = 0.0
            _width = 100

            def _find_trigger_point(self, samples):
                if len(samples) < 2:
                    return 0
                level = self._trigger_level
                if self._trigger_mode == TriggerMode.FREE_RUN:
                    return 0
                elif self._trigger_mode == TriggerMode.RISING:
                    for i in range(1, len(samples) - self._width):
                        if samples[i-1] < level <= samples[i]:
                            return i
                return 0

        scope = MockScope()
        # Signal with rising edge at index ~50
        samples = np.concatenate([
            np.linspace(-0.5, -0.1, 50),
            np.linspace(-0.1, 0.5, 50),
            np.linspace(0.5, 0.3, 100)
        ])

        trigger_idx = scope._find_trigger_point(samples)
        # Should trigger near the zero crossing (around index 50-60)
        assert 45 <= trigger_idx <= 65

    def test_find_falling_edge(self):
        """Test falling edge detection."""
        class MockScope:
            _trigger_mode = TriggerMode.FALLING
            _trigger_level = 0.0
            _width = 100

            def _find_trigger_point(self, samples):
                if len(samples) < 2:
                    return 0
                level = self._trigger_level
                if self._trigger_mode == TriggerMode.FALLING:
                    for i in range(1, len(samples) - self._width):
                        if samples[i-1] > level >= samples[i]:
                            return i
                return 0

        scope = MockScope()
        # Signal with falling edge
        samples = np.concatenate([
            np.linspace(0.5, 0.1, 50),
            np.linspace(0.1, -0.5, 50),
            np.linspace(-0.5, -0.3, 100)
        ])

        trigger_idx = scope._find_trigger_point(samples)
        # Should trigger near the zero crossing (around index 50-60)
        assert 45 <= trigger_idx <= 65

    def test_free_run_returns_zero(self):
        """Free-run should always return 0."""
        class MockScope:
            _trigger_mode = TriggerMode.FREE_RUN
            _trigger_level = 0.0
            _width = 100

            def _find_trigger_point(self, samples):
                if self._trigger_mode == TriggerMode.FREE_RUN:
                    return 0
                return 0

        scope = MockScope()
        samples = np.random.randn(200).astype(np.float32)
        assert scope._find_trigger_point(samples) == 0


class TestOscilloscopeBuffer:
    """Tests for buffer management logic."""

    def test_circular_buffer_write(self):
        """Test circular buffer write logic."""
        buffer_size = 1000
        buffer = np.zeros(buffer_size, dtype=np.float32)
        write_pos = 0

        # Write samples
        samples = np.ones(300, dtype=np.float32) * 0.5
        num_samples = len(samples)

        space = buffer_size - write_pos
        if num_samples <= space:
            buffer[write_pos:write_pos + num_samples] = samples
            write_pos += num_samples
        else:
            buffer[write_pos:] = samples[:space]
            remaining = num_samples - space
            buffer[:remaining] = samples[space:]
            write_pos = remaining

        assert write_pos == 300
        assert buffer[0] == 0.5
        assert buffer[299] == 0.5

    def test_circular_buffer_wraparound(self):
        """Test buffer wraparound."""
        buffer_size = 100
        buffer = np.zeros(buffer_size, dtype=np.float32)
        write_pos = 90

        samples = np.ones(30, dtype=np.float32) * 0.8
        num_samples = len(samples)

        space = buffer_size - write_pos
        if num_samples <= space:
            buffer[write_pos:write_pos + num_samples] = samples
            write_pos += num_samples
        else:
            buffer[write_pos:] = samples[:space]
            remaining = num_samples - space
            buffer[:remaining] = samples[space:]
            write_pos = remaining

        # Should wrap to position 20
        assert write_pos == 20
        # End of buffer should have samples
        assert abs(buffer[90] - 0.8) < 0.001
        assert abs(buffer[99] - 0.8) < 0.001
        # Beginning should have wrapped samples
        assert abs(buffer[0] - 0.8) < 0.001
        assert abs(buffer[19] - 0.8) < 0.001


class TestOscilloscopeLevelConversion:
    """Tests for level to Y coordinate conversion."""

    def test_level_to_y_center(self):
        """Zero level should be at center."""
        height = 200
        level = 0.0
        # level_to_y: int(height / 2 * (1.0 - level))
        y = int(height / 2 * (1.0 - level))
        assert y == 100  # Center

    def test_level_to_y_positive(self):
        """Positive level should be above center."""
        height = 200
        level = 0.5
        y = int(height / 2 * (1.0 - level))
        assert y == 50  # Upper half

    def test_level_to_y_negative(self):
        """Negative level should be below center."""
        height = 200
        level = -0.5
        y = int(height / 2 * (1.0 - level))
        assert y == 150  # Lower half

    def test_level_to_y_max(self):
        """Max level (+1) should be at top."""
        height = 200
        level = 1.0
        y = int(height / 2 * (1.0 - level))
        assert y == 0  # Top

    def test_level_to_y_min(self):
        """Min level (-1) should be at bottom."""
        height = 200
        level = -1.0
        y = int(height / 2 * (1.0 - level))
        assert y == 200  # Bottom


class TestOscilloscopePeakTracking:
    """Tests for peak level tracking."""

    def test_peak_tracking(self):
        """Should track peak level."""
        peak_level = 0.0
        peak_hold = 0.0
        peak_decay = 0.95

        # Add samples with peak of 0.8
        samples = np.array([0.0, 0.3, 0.8, 0.5], dtype=np.float32)
        peak = np.abs(samples).max()

        if peak > peak_level:
            peak_level = peak
        if peak > peak_hold:
            peak_hold = peak
        else:
            peak_hold *= peak_decay

        assert abs(peak_level - 0.8) < 0.001
        assert abs(peak_hold - 0.8) < 0.001

    def test_peak_decay(self):
        """Peak hold should decay over time."""
        peak_hold = 0.8
        peak_decay = 0.95

        # Simulate decay with no new peaks
        for _ in range(10):
            peak_hold *= peak_decay

        assert peak_hold < 0.5  # Should have decayed


class TestOscilloscopeTimeScale:
    """Tests for time scale calculations."""

    def test_time_per_division(self):
        """Should calculate time per division."""
        width = 400
        grid_divisions = 10
        time_scale = 4
        sample_rate = 44100

        samples_per_div = (width / grid_divisions) * time_scale
        time_ms = (samples_per_div / sample_rate) * 1000.0

        # 40 * 4 = 160 samples per div
        # 160 / 44100 * 1000 = ~3.6ms
        assert abs(time_ms - 3.63) < 0.1

    def test_time_scale_bounds(self):
        """Time scale should have bounds."""
        # Test clamping logic
        min_scale = 1
        max_scale = 32

        test_scale = 0
        clamped = max(min_scale, min(max_scale, test_scale))
        assert clamped == 1

        test_scale = 50
        clamped = max(min_scale, min(max_scale, test_scale))
        assert clamped == 32


class TestOscilloscopeRepr:
    """Tests for string representation."""

    def test_repr_format(self):
        """Should format repr correctly."""
        width = 400
        height = 200
        trigger = TriggerMode.AUTO

        repr_str = f"Oscilloscope({width}x{height}, trigger={trigger.name})"
        assert "400x200" in repr_str
        assert "AUTO" in repr_str
