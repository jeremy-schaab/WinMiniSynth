# Filter Curve Module
"""
filter_curve - Frequency response visualization for the Mini Synthesizer.

Provides a tkinter canvas-based filter response display with:
- Logarithmic frequency scale
- dB magnitude scale
- Cutoff frequency marker
- Resonance peak visualization
- Real-time parameter updates

Usage:
    curve = FilterCurve(parent, width=400, height=200)
    curve.pack()

    # Update with filter parameters:
    curve.update_response(cutoff=1000, resonance=0.5)

    # Or with a MoogFilter instance:
    curve.update_from_filter(moog_filter)
"""

import tkinter as tk
from tkinter import ttk
from enum import Enum, auto
from typing import Optional, List, Tuple
import numpy as np
import math

# Import styles - handle import for both module and standalone use
try:
    from gui.styles import COLORS, ColorScheme
except ImportError:
    COLORS = {
        'bg_dark': '#1a1a1a',
        'bg_panel': '#252525',
        'grid': '#333333',
        'filter_curve': '#ff6b6b',
        'fg_primary': '#e0e0e0',
        'fg_muted': '#606060',
        'border': '#404040',
        'accent_primary': '#00b4d8',
    }
    ColorScheme = None


class ScaleMode(Enum):
    """Y-axis scale mode."""
    LINEAR = auto()    # Linear magnitude (0-1)
    DECIBEL = auto()   # Decibels (-60 to +12 dB)


class FilterCurve(tk.Canvas):
    """Filter frequency response display.

    Renders filter frequency response curve with logarithmic
    frequency scale and optional dB magnitude scale.

    Attributes:
        cutoff: Filter cutoff frequency
        resonance: Filter resonance (0-1)
        scale_mode: Y-axis scale (linear or dB)
        sample_rate: Audio sample rate
    """

    # Default dimensions
    DEFAULT_WIDTH = 400
    DEFAULT_HEIGHT = 200

    # Frequency range
    MIN_FREQ = 20.0
    MAX_FREQ = 20000.0

    # dB range for display
    MIN_DB = -60.0
    MAX_DB = 12.0

    # Grid settings
    FREQ_GRID_LINES = [100, 1000, 10000]  # Hz
    DB_GRID_LINES = [-48, -36, -24, -12, 0]  # dB

    def __init__(
        self,
        parent: tk.Widget,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        sample_rate: int = 44100,
        **kwargs
    ):
        """Initialize filter curve display.

        Args:
            parent: Parent widget
            width: Canvas width in pixels
            height: Canvas height in pixels
            sample_rate: Audio sample rate
        """
        bg_color = COLORS.get('bg_dark', '#1a1a1a')

        super().__init__(
            parent,
            width=width,
            height=height,
            bg=bg_color,
            highlightthickness=1,
            highlightbackground=COLORS.get('border', '#404040'),
            **kwargs
        )

        self._width = width
        self._height = height
        self._sample_rate = sample_rate

        # Filter parameters
        self._cutoff = 1000.0
        self._resonance = 0.0
        self._filter_type = '4-pole'  # For label

        # Display settings
        self._scale_mode = ScaleMode.DECIBEL
        self._show_cutoff_marker = True
        self._show_labels = True

        # Pre-compute frequency array for response calculation
        self._frequencies = self._generate_log_frequencies()

        # Colors
        self._grid_color = COLORS.get('grid', '#333333')
        self._curve_color = COLORS.get('filter_curve', '#ff6b6b')
        self._text_color = COLORS.get('fg_muted', '#606060')
        self._marker_color = COLORS.get('accent_primary', '#00b4d8')
        self._fill_color = self._hex_to_rgba(self._curve_color, 0.2)

        # Draw initial display
        self._draw_grid()
        self._draw_response()

        # Bind resize event
        self.bind('<Configure>', self._on_resize)

    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        """Convert hex color with alpha to darker version (simulated transparency)."""
        # Parse hex
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Blend with background (dark)
        bg_r, bg_g, bg_b = 26, 26, 26  # #1a1a1a
        r = int(r * alpha + bg_r * (1 - alpha))
        g = int(g * alpha + bg_g * (1 - alpha))
        b = int(b * alpha + bg_b * (1 - alpha))

        return f'#{r:02x}{g:02x}{b:02x}'

    def _on_resize(self, event):
        """Handle canvas resize."""
        self._width = event.width
        self._height = event.height
        self._frequencies = self._generate_log_frequencies()
        self._draw_grid()
        self._draw_response()

    def _generate_log_frequencies(self) -> np.ndarray:
        """Generate logarithmically spaced frequencies for response."""
        return np.logspace(
            np.log10(self.MIN_FREQ),
            np.log10(self.MAX_FREQ),
            self._width
        )

    def _freq_to_x(self, freq: float) -> int:
        """Convert frequency to X coordinate (log scale)."""
        if freq <= 0:
            return 0
        log_min = np.log10(self.MIN_FREQ)
        log_max = np.log10(self.MAX_FREQ)
        log_freq = np.log10(max(self.MIN_FREQ, min(self.MAX_FREQ, freq)))
        return int((log_freq - log_min) / (log_max - log_min) * self._width)

    def _x_to_freq(self, x: int) -> float:
        """Convert X coordinate to frequency."""
        log_min = np.log10(self.MIN_FREQ)
        log_max = np.log10(self.MAX_FREQ)
        log_freq = log_min + (x / self._width) * (log_max - log_min)
        return 10 ** log_freq

    def _mag_to_y(self, magnitude: float) -> int:
        """Convert magnitude to Y coordinate."""
        if self._scale_mode == ScaleMode.DECIBEL:
            # Convert to dB
            if magnitude > 0:
                db = 20 * np.log10(magnitude)
            else:
                db = self.MIN_DB
            db = max(self.MIN_DB, min(self.MAX_DB, db))
            # Map dB to Y (inverted)
            normalized = (db - self.MIN_DB) / (self.MAX_DB - self.MIN_DB)
            return int(self._height * (1.0 - normalized))
        else:
            # Linear scale
            magnitude = max(0.0, min(2.0, magnitude))  # Allow some headroom
            return int(self._height * (1.0 - magnitude / 2.0))

    def _draw_grid(self):
        """Draw the frequency/magnitude grid."""
        self.delete('grid')
        self.delete('label')

        w = self._width
        h = self._height
        margin_left = 35 if self._show_labels else 0
        margin_bottom = 20 if self._show_labels else 0

        # Frequency grid lines (vertical)
        for freq in self.FREQ_GRID_LINES:
            x = self._freq_to_x(freq)
            if margin_left < x < w:
                self.create_line(
                    x, 0, x, h - margin_bottom,
                    fill=self._grid_color,
                    tags='grid'
                )
                if self._show_labels:
                    label = f"{freq//1000}k" if freq >= 1000 else str(freq)
                    self.create_text(
                        x, h - margin_bottom + 10,
                        text=label,
                        fill=self._text_color,
                        font=('Segoe UI', 7),
                        tags='label'
                    )

        # Additional frequency markers
        for freq in [50, 200, 500, 2000, 5000]:
            x = self._freq_to_x(freq)
            if margin_left < x < w:
                self.create_line(
                    x, 0, x, h - margin_bottom,
                    fill=self._grid_color,
                    dash=(2, 4),
                    tags='grid'
                )

        # Magnitude grid lines (horizontal)
        if self._scale_mode == ScaleMode.DECIBEL:
            for db in self.DB_GRID_LINES:
                y = self._mag_to_y(10 ** (db / 20))
                self.create_line(
                    margin_left, y, w, y,
                    fill=self._grid_color,
                    tags='grid'
                )
                if self._show_labels:
                    self.create_text(
                        margin_left - 5, y,
                        text=f"{db}",
                        fill=self._text_color,
                        font=('Segoe UI', 7),
                        anchor='e',
                        tags='label'
                    )

        # 0 dB line (unity gain) - slightly brighter
        unity_y = self._mag_to_y(1.0)
        self.create_line(
            margin_left, unity_y, w, unity_y,
            fill=self._grid_color,
            width=1,
            tags='grid'
        )

    def _calculate_response(self) -> np.ndarray:
        """Calculate filter frequency response.

        Returns:
            Array of magnitude values (linear)
        """
        # Simplified 4-pole Moog ladder response calculation
        fc = self._cutoff
        res = self._resonance

        # Normalized frequencies
        w = self._frequencies / self._sample_rate

        # Calculate one-pole lowpass coefficient (approximation)
        wc = fc / self._sample_rate
        g = np.tan(np.pi * np.minimum(wc, 0.49))

        # One-pole magnitude at each frequency
        omega = 2.0 * np.pi * w
        H_one_pole = g / np.sqrt(g**2 + omega**2 + 1e-10)

        # Four-pole magnitude
        magnitude = H_one_pole ** 4

        # Resonance peak
        if res > 0:
            # Add resonance peak near cutoff
            peak_width = fc * 0.3
            peak = np.exp(-0.5 * ((self._frequencies - fc) / peak_width) ** 2)
            magnitude = magnitude * (1.0 + res * 4.0 * peak)

        # Normalize so passband is near unity
        if len(magnitude) > 0 and magnitude[0] > 0:
            magnitude = magnitude / magnitude[0]

        return magnitude.astype(np.float32)

    def _draw_response(self):
        """Draw the filter response curve."""
        self.delete('curve')
        self.delete('marker')
        self.delete('fill')

        # Calculate response
        magnitudes = self._calculate_response()

        if len(magnitudes) == 0:
            return

        margin_left = 35 if self._show_labels else 0
        margin_bottom = 20 if self._show_labels else 0

        # Build point list for curve
        points = []
        for x, mag in enumerate(magnitudes):
            if x >= margin_left:
                y = self._mag_to_y(mag)
                y = max(0, min(self._height - margin_bottom, y))
                points.extend([x, y])

        if len(points) < 4:
            return

        # Draw filled area under curve
        fill_points = list(points)
        # Close the polygon at bottom
        fill_points.extend([points[-2], self._height - margin_bottom])  # Bottom right
        fill_points.extend([margin_left, self._height - margin_bottom])  # Bottom left
        fill_points.extend([margin_left, points[1]])  # Back to start

        self.create_polygon(
            *fill_points,
            fill=self._fill_color,
            outline='',
            tags='fill'
        )

        # Draw curve line
        self.create_line(
            *points,
            fill=self._curve_color,
            width=2,
            smooth=True,
            tags='curve'
        )

        # Draw cutoff marker
        if self._show_cutoff_marker:
            cutoff_x = self._freq_to_x(self._cutoff)
            if margin_left < cutoff_x < self._width:
                # Vertical line at cutoff
                self.create_line(
                    cutoff_x, 0, cutoff_x, self._height - margin_bottom,
                    fill=self._marker_color,
                    width=1,
                    dash=(4, 2),
                    tags='marker'
                )

                # Cutoff frequency label
                if self._cutoff >= 1000:
                    label = f"{self._cutoff/1000:.1f}kHz"
                else:
                    label = f"{self._cutoff:.0f}Hz"

                self.create_text(
                    cutoff_x, 10,
                    text=label,
                    fill=self._marker_color,
                    font=('Segoe UI', 8),
                    anchor='n',
                    tags='marker'
                )

        # Draw resonance indicator
        if self._resonance > 0:
            res_label = f"Q: {self._resonance:.2f}"
            self.create_text(
                self._width - 5, 10,
                text=res_label,
                fill=self._text_color,
                font=('Segoe UI', 8),
                anchor='ne',
                tags='marker'
            )

    def update_response(self, cutoff: float, resonance: float):
        """Update filter response with new parameters.

        Args:
            cutoff: Filter cutoff frequency in Hz
            resonance: Filter resonance (0.0 to 1.0)
        """
        self._cutoff = max(self.MIN_FREQ, min(self.MAX_FREQ, cutoff))
        self._resonance = max(0.0, min(1.0, resonance))
        self._draw_response()

    def update_from_filter(self, filter_obj):
        """Update response from a MoogFilter object.

        Args:
            filter_obj: MoogFilter instance with cutoff and resonance properties
        """
        if hasattr(filter_obj, 'cutoff') and hasattr(filter_obj, 'resonance'):
            self.update_response(
                filter_obj.cutoff,
                filter_obj.resonance
            )

    def set_response_data(self, frequencies: np.ndarray, magnitudes: np.ndarray):
        """Set response curve from external data.

        Useful when response is calculated by the filter itself.

        Args:
            frequencies: Array of frequencies in Hz
            magnitudes: Array of magnitude values (linear)
        """
        # Interpolate to display resolution
        display_mags = np.interp(
            self._frequencies,
            frequencies,
            magnitudes
        )

        # Store and redraw
        self._external_response = display_mags
        self._draw_response()

    def clear(self):
        """Clear the display."""
        self.delete('curve')
        self.delete('fill')
        self.delete('marker')

    # Properties

    @property
    def cutoff(self) -> float:
        """Get cutoff frequency."""
        return self._cutoff

    @cutoff.setter
    def cutoff(self, value: float):
        """Set cutoff frequency."""
        self._cutoff = max(self.MIN_FREQ, min(self.MAX_FREQ, value))
        self._draw_response()

    @property
    def resonance(self) -> float:
        """Get resonance."""
        return self._resonance

    @resonance.setter
    def resonance(self, value: float):
        """Set resonance."""
        self._resonance = max(0.0, min(1.0, value))
        self._draw_response()

    @property
    def scale_mode(self) -> ScaleMode:
        """Get Y-axis scale mode."""
        return self._scale_mode

    @scale_mode.setter
    def scale_mode(self, mode: ScaleMode):
        """Set Y-axis scale mode."""
        self._scale_mode = mode
        self._draw_grid()
        self._draw_response()

    @property
    def show_cutoff_marker(self) -> bool:
        """Whether cutoff marker is shown."""
        return self._show_cutoff_marker

    @show_cutoff_marker.setter
    def show_cutoff_marker(self, value: bool):
        """Set cutoff marker visibility."""
        self._show_cutoff_marker = value
        self._draw_response()

    @property
    def show_labels(self) -> bool:
        """Whether axis labels are shown."""
        return self._show_labels

    @show_labels.setter
    def show_labels(self, value: bool):
        """Set axis label visibility."""
        self._show_labels = value
        self._draw_grid()
        self._draw_response()

    def __repr__(self) -> str:
        return f"FilterCurve({self._width}x{self._height}, fc={self._cutoff:.0f}Hz, Q={self._resonance:.2f})"
