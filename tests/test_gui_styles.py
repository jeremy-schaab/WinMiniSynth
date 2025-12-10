# Tests for GUI Styles Module
"""
test_gui_styles - Unit tests for the GUI styles and theme configuration.
"""

import pytest
import tkinter as tk
from tkinter import ttk

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui.styles import (
    COLORS, FONTS, DIMENSIONS, ColorScheme,
    configure_dark_theme, create_panel_frame, create_slider_with_label
)


class TestColors:
    """Tests for COLORS dictionary."""

    def test_colors_is_dict(self):
        """COLORS should be a dictionary."""
        assert isinstance(COLORS, dict)

    def test_colors_has_required_keys(self):
        """COLORS should have all required keys."""
        required = [
            'bg_dark', 'bg_panel', 'bg_widget', 'bg_input',
            'fg_primary', 'fg_secondary', 'fg_muted',
            'accent_primary', 'accent_secondary', 'accent_hover',
            'success', 'warning', 'error', 'record',
            'border'
        ]
        for key in required:
            assert key in COLORS, f"Missing color key: {key}"

    def test_colors_are_hex_strings(self):
        """All color values should be valid hex color strings."""
        for key, value in COLORS.items():
            assert isinstance(value, str), f"{key} is not a string"
            assert value.startswith('#'), f"{key} doesn't start with #"
            assert len(value) == 7, f"{key} is not a valid hex color (expected #RRGGBB)"

    def test_colors_are_valid_hex(self):
        """Color hex values should be valid."""
        for key, value in COLORS.items():
            try:
                int(value[1:], 16)
            except ValueError:
                pytest.fail(f"{key}={value} is not a valid hex color")


class TestFonts:
    """Tests for FONTS dictionary."""

    def test_fonts_is_dict(self):
        """FONTS should be a dictionary."""
        assert isinstance(FONTS, dict)

    def test_fonts_has_required_keys(self):
        """FONTS should have required font definitions."""
        required = ['title', 'label', 'value', 'small']
        for key in required:
            assert key in FONTS, f"Missing font key: {key}"

    def test_fonts_are_tuples(self):
        """Font definitions should be tuples."""
        for key, value in FONTS.items():
            assert isinstance(value, tuple), f"{key} is not a tuple"
            assert len(value) >= 2, f"{key} should have at least 2 elements"
            assert isinstance(value[0], str), f"{key} family should be string"
            assert isinstance(value[1], int), f"{key} size should be int"


class TestDimensions:
    """Tests for DIMENSIONS dictionary."""

    def test_dimensions_is_dict(self):
        """DIMENSIONS should be a dictionary."""
        assert isinstance(DIMENSIONS, dict)

    def test_dimensions_are_ints(self):
        """All dimension values should be integers."""
        for key, value in DIMENSIONS.items():
            assert isinstance(value, int), f"{key} is not an int"

    def test_window_dimensions(self):
        """Window dimensions should be reasonable."""
        assert DIMENSIONS['window_width'] >= 800
        assert DIMENSIONS['window_height'] >= 600
        assert DIMENSIONS['min_window_width'] >= 640
        assert DIMENSIONS['min_window_height'] >= 480

    def test_padding_values(self):
        """Padding values should be positive."""
        assert DIMENSIONS['padding_small'] > 0
        assert DIMENSIONS['padding_medium'] > DIMENSIONS['padding_small']
        assert DIMENSIONS['padding_large'] > DIMENSIONS['padding_medium']


class TestColorScheme:
    """Tests for ColorScheme convenience class."""

    def test_colorscheme_has_bg_colors(self):
        """ColorScheme should have background colors."""
        assert hasattr(ColorScheme, 'bg_dark')
        assert hasattr(ColorScheme, 'bg_panel')
        assert hasattr(ColorScheme, 'bg_widget')

    def test_colorscheme_has_fg_colors(self):
        """ColorScheme should have foreground colors."""
        assert hasattr(ColorScheme, 'fg_primary')
        assert hasattr(ColorScheme, 'fg_secondary')
        assert hasattr(ColorScheme, 'fg_muted')

    def test_colorscheme_has_accent(self):
        """ColorScheme should have accent color."""
        assert hasattr(ColorScheme, 'accent')

    def test_colorscheme_values_match_colors(self):
        """ColorScheme values should match COLORS dict."""
        assert ColorScheme.bg_dark == COLORS['bg_dark']
        assert ColorScheme.accent == COLORS['accent_primary']
        assert ColorScheme.border == COLORS['border']


class TestConfigureDarkTheme:
    """Tests for configure_dark_theme function."""

    @pytest.fixture
    def root(self):
        """Create a root window for testing."""
        root = tk.Tk()
        root.withdraw()  # Hide window
        yield root
        root.destroy()

    def test_returns_style(self, root):
        """configure_dark_theme should return a ttk.Style."""
        style = configure_dark_theme(root)
        assert isinstance(style, ttk.Style)

    def test_configures_dark_frame(self, root):
        """Should configure Dark.TFrame style."""
        configure_dark_theme(root)
        # Creating a widget with the style shouldn't raise
        frame = ttk.Frame(root, style='Dark.TFrame')
        assert frame is not None

    def test_configures_dark_label(self, root):
        """Should configure Dark.TLabel style."""
        configure_dark_theme(root)
        label = ttk.Label(root, text="Test", style='Dark.TLabel')
        assert label is not None

    def test_configures_dark_button(self, root):
        """Should configure Dark.TButton style."""
        configure_dark_theme(root)
        button = ttk.Button(root, text="Test", style='Dark.TButton')
        assert button is not None

    def test_configures_accent_button(self, root):
        """Should configure Accent.TButton style."""
        configure_dark_theme(root)
        button = ttk.Button(root, text="Test", style='Accent.TButton')
        assert button is not None


class TestCreatePanelFrame:
    """Tests for create_panel_frame helper function."""

    @pytest.fixture
    def root(self):
        """Create a root window for testing."""
        root = tk.Tk()
        root.withdraw()
        configure_dark_theme(root)
        yield root
        root.destroy()

    def test_creates_frame_without_title(self, root):
        """Should create a frame without title."""
        frame = create_panel_frame(root)
        assert isinstance(frame, ttk.Frame)

    def test_creates_labelframe_with_title(self, root):
        """Should create a LabelFrame with title."""
        frame = create_panel_frame(root, title="Test Panel")
        assert isinstance(frame, ttk.LabelFrame)


class TestCreateSliderWithLabel:
    """Tests for create_slider_with_label helper function."""

    @pytest.fixture
    def root(self):
        """Create a root window for testing."""
        root = tk.Tk()
        root.withdraw()
        configure_dark_theme(root)
        yield root
        root.destroy()

    def test_creates_slider_components(self, root):
        """Should create all slider components."""
        var = tk.DoubleVar(value=0.5)
        container, label, slider, value_label = create_slider_with_label(
            root, "Test", var, 0.0, 1.0
        )
        assert isinstance(container, ttk.Frame)
        assert isinstance(label, ttk.Label)
        assert isinstance(slider, ttk.Scale)
        assert isinstance(value_label, ttk.Label)

    def test_slider_respects_range(self, root):
        """Slider should have correct range."""
        var = tk.DoubleVar(value=50)
        container, label, slider, value_label = create_slider_with_label(
            root, "Test", var, 0, 100
        )
        # Scale should be created with given range
        assert slider.cget('from') == 0
        assert slider.cget('to') == 100

    def test_vertical_orientation(self, root):
        """Should support vertical orientation."""
        var = tk.DoubleVar(value=0.5)
        container, label, slider, value_label = create_slider_with_label(
            root, "Test", var, 0.0, 1.0, orient='vertical'
        )
        # ttk.Scale.cget('orient') returns a Tcl index object, convert to string
        assert str(slider.cget('orient')) == 'vertical'

    def test_custom_value_format(self, root):
        """Should format value with custom format string."""
        var = tk.DoubleVar(value=50.0)
        container, label, slider, value_label = create_slider_with_label(
            root, "Test", var, 0, 100, value_format='{:.0f}%'
        )
        # Initial value should be formatted
        assert value_label.cget('text') == '50%'
