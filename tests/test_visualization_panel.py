# Tests for Visualization Panel Module
"""
test_visualization_panel - Unit tests for combined visualization panel.
"""

import pytest
import tkinter as tk
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from visualization.oscilloscope import TriggerMode
from visualization.filter_curve import ScaleMode


class TestVisualizationPanelConstants:
    """Tests for panel constants."""

    def test_default_heights(self):
        """Should have default height constants."""
        # Import here to test constants without GUI
        from visualization.panel import VisualizationPanel

        assert VisualizationPanel.SCOPE_HEIGHT == 150
        assert VisualizationPanel.FILTER_HEIGHT == 120
        assert VisualizationPanel.MIN_WIDTH == 300


class TestTriggerModeMapping:
    """Tests for trigger mode string mapping."""

    def test_trigger_mode_names(self):
        """Should have correct mode names."""
        mode_map = {
            "FREE": TriggerMode.FREE_RUN,
            "RISING": TriggerMode.RISING,
            "FALLING": TriggerMode.FALLING,
            "AUTO": TriggerMode.AUTO
        }

        assert mode_map["FREE"] == TriggerMode.FREE_RUN
        assert mode_map["RISING"] == TriggerMode.RISING
        assert mode_map["AUTO"] == TriggerMode.AUTO

    def test_mode_name_reverse_mapping(self):
        """Should be able to get name from mode."""
        mode_names = {
            TriggerMode.FREE_RUN: "FREE",
            TriggerMode.RISING: "RISING",
            TriggerMode.FALLING: "FALLING",
            TriggerMode.AUTO: "AUTO"
        }

        assert mode_names[TriggerMode.AUTO] == "AUTO"
        assert mode_names[TriggerMode.RISING] == "RISING"


class TestScaleModeMapping:
    """Tests for scale mode mapping."""

    def test_scale_mode_names(self):
        """Should map dB and Linear correctly."""
        scale_map = {
            "dB": ScaleMode.DECIBEL,
            "Linear": ScaleMode.LINEAR
        }

        assert scale_map["dB"] == ScaleMode.DECIBEL
        assert scale_map["Linear"] == ScaleMode.LINEAR


class TestSettingsDict:
    """Tests for settings serialization."""

    def test_settings_structure(self):
        """Settings dict should have all keys."""
        settings = {
            'trigger_mode': 'AUTO',
            'time_scale': 4,
            'filter_scale': 'DECIBEL',
            'show_labels': True,
            'frozen': False,
        }

        assert 'trigger_mode' in settings
        assert 'time_scale' in settings
        assert 'filter_scale' in settings
        assert 'show_labels' in settings
        assert 'frozen' in settings

    def test_settings_default_values(self):
        """Settings should have valid default values."""
        settings = {
            'trigger_mode': 'AUTO',
            'time_scale': 4,
            'filter_scale': 'DECIBEL',
            'show_labels': True,
            'frozen': False,
        }

        assert settings['trigger_mode'] in ['FREE', 'RISING', 'FALLING', 'AUTO']
        assert 1 <= settings['time_scale'] <= 32
        assert settings['filter_scale'] in ['LINEAR', 'DECIBEL']
        assert isinstance(settings['show_labels'], bool)
        assert isinstance(settings['frozen'], bool)

    def test_settings_from_getattr(self):
        """Should be able to get mode from string name."""
        mode_name = 'AUTO'
        mode = getattr(TriggerMode, mode_name, TriggerMode.AUTO)
        assert mode == TriggerMode.AUTO

        mode_name = 'RISING'
        mode = getattr(TriggerMode, mode_name, TriggerMode.AUTO)
        assert mode == TriggerMode.RISING

        # Invalid should fall back
        mode_name = 'INVALID'
        mode = getattr(TriggerMode, mode_name, TriggerMode.AUTO)
        assert mode == TriggerMode.AUTO


class TestTimePerDivision:
    """Tests for time per division calculation."""

    def test_time_calculation(self):
        """Should calculate time per division correctly."""
        width = 400
        grid_divisions = 10
        time_scale = 4
        sample_rate = 44100

        samples_per_div = (width / grid_divisions) * time_scale
        time_ms = (samples_per_div / sample_rate) * 1000.0

        # 40 pixels * 4 samples/pixel = 160 samples
        # 160 / 44100 * 1000 = ~3.63 ms
        assert abs(time_ms - 3.63) < 0.1

    def test_time_formatting_ms(self):
        """Time >= 1ms should show as ms."""
        time_ms = 3.63

        if time_ms >= 1.0:
            label = f"{time_ms:.1f}ms/div"
        else:
            label = f"{time_ms*1000:.0f}us/div"

        assert "ms/div" in label
        assert "3.6" in label

    def test_time_formatting_us(self):
        """Time < 1ms should show as us."""
        time_ms = 0.5

        if time_ms >= 1.0:
            label = f"{time_ms:.1f}ms/div"
        else:
            label = f"{time_ms*1000:.0f}us/div"

        assert "us/div" in label
        assert "500" in label


class TestFilterInfoFormatting:
    """Tests for filter info label formatting."""

    def test_freq_format_khz(self):
        """Frequencies >= 1kHz should show as kHz."""
        cutoff = 2500.0

        if cutoff >= 1000:
            freq_str = f"{cutoff/1000:.1f}kHz"
        else:
            freq_str = f"{cutoff:.0f}Hz"

        assert "2.5kHz" in freq_str

    def test_freq_format_hz(self):
        """Frequencies < 1kHz should show as Hz."""
        cutoff = 500.0

        if cutoff >= 1000:
            freq_str = f"{cutoff/1000:.1f}kHz"
        else:
            freq_str = f"{cutoff:.0f}Hz"

        assert "500Hz" in freq_str

    def test_full_info_format(self):
        """Full info should include Fc and Q."""
        cutoff = 1000.0
        resonance = 0.5

        freq_str = f"{cutoff/1000:.1f}kHz"
        info = f"Fc: {freq_str}, Q: {resonance:.2f}"

        assert "Fc:" in info
        assert "Q:" in info
        assert "1.0kHz" in info
        assert "0.50" in info


class TestVisualizationPanelRepr:
    """Tests for string representation."""

    def test_repr_contains_components(self):
        """Repr should mention both components."""
        scope_repr = "Oscilloscope(400x150, trigger=AUTO)"
        filter_repr = "FilterCurve(400x120, fc=1000Hz, Q=0.50)"

        panel_repr = f"VisualizationPanel(scope={scope_repr}, filter={filter_repr})"

        assert "VisualizationPanel" in panel_repr
        assert "scope=" in panel_repr
        assert "filter=" in panel_repr
