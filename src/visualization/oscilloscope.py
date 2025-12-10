# Oscilloscope Module
"""
oscilloscope - Real-time waveform display for the Mini Synthesizer.

Provides a tkinter canvas-based oscilloscope with:
- Real-time waveform rendering
- Trigger modes (free-run, rising edge, falling edge)
- Adjustable time scale
- Grid overlay
- Peak level indicator
- Freeze/pause capability

Usage:
    scope = Oscilloscope(parent, width=400, height=200)
    scope.pack()

    # In audio callback or update loop:
    scope.update_waveform(audio_samples)
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
    # Fallback colors if styles not available
    COLORS = {
        'bg_dark': '#1a1a1a',
        'bg_panel': '#252525',
        'grid': '#333333',
        'waveform': '#00ff88',
        'fg_primary': '#e0e0e0',
        'fg_muted': '#606060',
        'border': '#404040',
        'accent_primary': '#00b4d8',
    }
    ColorScheme = None


class TriggerMode(Enum):
    """Oscilloscope trigger mode."""
    FREE_RUN = auto()    # No triggering, continuous display
    RISING = auto()      # Trigger on rising edge
    FALLING = auto()     # Trigger on falling edge
    AUTO = auto()        # Auto-trigger if no edge found


class DisplayMode(Enum):
    """Oscilloscope display mode."""
    WAVEFORM = auto()    # Time-domain waveform
    LISSAJOUS = auto()   # X-Y display (for stereo)
    SPECTRUM = auto()    # Simple frequency display


class Oscilloscope(tk.Canvas):
    """Real-time waveform oscilloscope display.

    Renders audio waveform data on a tkinter canvas with grid,
    triggering, and various display options.

    Attributes:
        trigger_mode: Current trigger mode
        trigger_level: Trigger threshold (-1.0 to 1.0)
        time_scale: Samples per pixel
        frozen: Whether display is frozen
    """

    # Default dimensions
    DEFAULT_WIDTH = 400
    DEFAULT_HEIGHT = 200

    # Display settings
    GRID_DIVISIONS_X = 10
    GRID_DIVISIONS_Y = 8
    WAVEFORM_LINE_WIDTH = 1

    def __init__(
        self,
        parent: tk.Widget,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        sample_rate: int = 44100,
        **kwargs
    ):
        """Initialize oscilloscope.

        Args:
            parent: Parent widget
            width: Canvas width in pixels
            height: Canvas height in pixels
            sample_rate: Audio sample rate
        """
        # Set canvas colors
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

        # Display settings
        self._trigger_mode = TriggerMode.AUTO
        self._trigger_level = 0.0
        self._time_scale = 4  # samples per pixel
        self._frozen = False
        self._display_mode = DisplayMode.WAVEFORM

        # Waveform data buffer
        self._buffer_size = width * self._time_scale * 2
        self._buffer = np.zeros(self._buffer_size, dtype=np.float32)
        self._write_pos = 0

        # Display buffer (points to draw)
        self._display_points: List[Tuple[int, int]] = []

        # Peak level tracking
        self._peak_level = 0.0
        self._peak_hold = 0.0
        self._peak_decay = 0.95

        # Colors
        self._grid_color = COLORS.get('grid', '#333333')
        self._waveform_color = COLORS.get('waveform', '#00ff88')
        self._text_color = COLORS.get('fg_muted', '#606060')
        self._trigger_color = COLORS.get('accent_primary', '#00b4d8')

        # Create initial display
        self._draw_grid()
        self._waveform_id = None

        # Bind resize event
        self.bind('<Configure>', self._on_resize)

    def _on_resize(self, event):
        """Handle canvas resize."""
        self._width = event.width
        self._height = event.height
        self._buffer_size = self._width * self._time_scale * 2
        self._buffer = np.zeros(self._buffer_size, dtype=np.float32)
        self._write_pos = 0
        self._draw_grid()

    def _draw_grid(self):
        """Draw the background grid."""
        self.delete('grid')

        w = self._width
        h = self._height

        # Vertical grid lines
        for i in range(1, self.GRID_DIVISIONS_X):
            x = i * w // self.GRID_DIVISIONS_X
            self.create_line(
                x, 0, x, h,
                fill=self._grid_color,
                tags='grid'
            )

        # Horizontal grid lines
        for i in range(1, self.GRID_DIVISIONS_Y):
            y = i * h // self.GRID_DIVISIONS_Y
            self.create_line(
                0, y, w, y,
                fill=self._grid_color,
                tags='grid'
            )

        # Center line (zero crossing) - slightly brighter
        center_y = h // 2
        self.create_line(
            0, center_y, w, center_y,
            fill=self._grid_color,
            width=1,
            tags='grid'
        )

        # Trigger level line (if not free-run)
        if self._trigger_mode != TriggerMode.FREE_RUN:
            trigger_y = self._level_to_y(self._trigger_level)
            self.create_line(
                0, trigger_y, 10, trigger_y,
                fill=self._trigger_color,
                width=2,
                tags='grid'
            )

    def _level_to_y(self, level: float) -> int:
        """Convert audio level (-1 to 1) to Y coordinate."""
        # Clamp level
        level = max(-1.0, min(1.0, level))
        # Map to canvas (inverted: positive up)
        return int(self._height / 2 * (1.0 - level))

    def _find_trigger_point(self, samples: np.ndarray) -> int:
        """Find trigger point in samples.

        Args:
            samples: Audio samples to search

        Returns:
            Index of trigger point, or 0 if not found
        """
        if len(samples) < 2:
            return 0

        level = self._trigger_level

        if self._trigger_mode == TriggerMode.FREE_RUN:
            return 0

        # Calculate search range: only search first half so display has room
        # Need display_samples * time_scale after trigger point
        required_after = self._width * self._time_scale
        max_search = max(1, len(samples) - required_after)

        if self._trigger_mode == TriggerMode.RISING:
            # Find rising edge crossing trigger level
            for i in range(1, max_search):
                if samples[i-1] < level <= samples[i]:
                    return i

        elif self._trigger_mode == TriggerMode.FALLING:
            # Find falling edge crossing trigger level
            for i in range(1, max_search):
                if samples[i-1] > level >= samples[i]:
                    return i

        elif self._trigger_mode == TriggerMode.AUTO:
            # Try rising edge first
            for i in range(1, max_search):
                if samples[i-1] < level <= samples[i]:
                    return i
            # Fall back to free-run if no trigger found
            return 0

        return 0

    def update_waveform(self, samples: np.ndarray):
        """Update the oscilloscope display with new samples.

        Call this method with audio data to update the display.
        Typically called from the audio callback or a timer.

        Args:
            samples: Audio samples (mono, float32)
        """
        if self._frozen:
            return

        # Update peak level
        peak = np.abs(samples).max() if len(samples) > 0 else 0.0
        if peak > self._peak_level:
            self._peak_level = peak
        if peak > self._peak_hold:
            self._peak_hold = peak
        else:
            self._peak_hold *= self._peak_decay

        # Add samples to buffer
        num_samples = len(samples)
        if num_samples > 0:
            # Circular buffer write
            space = self._buffer_size - self._write_pos
            if num_samples <= space:
                self._buffer[self._write_pos:self._write_pos + num_samples] = samples
                self._write_pos += num_samples
            else:
                # Wrap around
                self._buffer[self._write_pos:] = samples[:space]
                remaining = num_samples - space
                self._buffer[:remaining] = samples[space:]
                self._write_pos = remaining

        # Extract display samples
        self._render_waveform()

    def _render_waveform(self):
        """Render the waveform on the canvas."""
        # Delete old waveform
        self.delete('waveform')

        # Get samples for display
        display_samples = self._width
        total_samples = display_samples * self._time_scale

        # Get samples from buffer
        if self._write_pos >= total_samples:
            start = self._write_pos - total_samples
            samples = self._buffer[start:self._write_pos].copy()
        else:
            # Wrap around case
            samples = np.concatenate([
                self._buffer[-(total_samples - self._write_pos):],
                self._buffer[:self._write_pos]
            ])

        if len(samples) < 10:
            # Need at least some data
            return

        # Find trigger point
        trigger_idx = self._find_trigger_point(samples)
        required_samples = display_samples * self._time_scale
        
        # Extract samples from trigger point, padding if needed
        end_idx = min(trigger_idx + required_samples, len(samples))
        samples = samples[trigger_idx:end_idx]
        
        # Pad with zeros if not enough samples (ensures we always draw)
        if len(samples) < required_samples:
            samples = np.pad(samples, (0, required_samples - len(samples)), mode='constant')

        # Downsample to screen resolution
        if self._time_scale > 1:
            # Take max absolute value in each chunk for better peak visibility
            # Truncate to exact multiple of time_scale to avoid reshape error
            samples = samples[:required_samples]
            samples = samples.reshape(display_samples, self._time_scale)
            # Use sample with maximum absolute value in each chunk
            max_idx = np.argmax(np.abs(samples), axis=1)
            display_samples_arr = samples[np.arange(len(samples)), max_idx]
        else:
            display_samples_arr = samples[:display_samples]

        # Build point list
        points = []
        for x, sample in enumerate(display_samples_arr):
            y = self._level_to_y(sample)
            points.extend([x, y])

        # Draw waveform line
        if len(points) >= 4:
            self.create_line(
                *points,
                fill=self._waveform_color,
                width=self.WAVEFORM_LINE_WIDTH,
                smooth=False,
                tags='waveform'
            )

        # Draw peak indicator
        self._draw_peak_indicator()

    def _draw_peak_indicator(self):
        """Draw peak level indicator."""
        self.delete('peak')

        # Peak bar on right edge
        bar_width = 4
        bar_x = self._width - bar_width - 2

        # Current peak
        peak_height = int(self._peak_hold * (self._height / 2))
        if peak_height > 0:
            center_y = self._height // 2
            self.create_rectangle(
                bar_x, center_y - peak_height,
                bar_x + bar_width, center_y + peak_height,
                fill=self._waveform_color,
                outline='',
                tags='peak'
            )

    def clear(self):
        """Clear the waveform display."""
        self._buffer.fill(0.0)
        self._write_pos = 0
        self._peak_level = 0.0
        self._peak_hold = 0.0
        self.delete('waveform')
        self.delete('peak')

    def freeze(self):
        """Freeze the display (stop updating)."""
        self._frozen = True

    def unfreeze(self):
        """Unfreeze the display (resume updating)."""
        self._frozen = False

    # Properties

    @property
    def trigger_mode(self) -> TriggerMode:
        """Get trigger mode."""
        return self._trigger_mode

    @trigger_mode.setter
    def trigger_mode(self, mode: TriggerMode):
        """Set trigger mode."""
        self._trigger_mode = mode
        self._draw_grid()

    @property
    def trigger_level(self) -> float:
        """Get trigger level."""
        return self._trigger_level

    @trigger_level.setter
    def trigger_level(self, level: float):
        """Set trigger level (-1.0 to 1.0)."""
        self._trigger_level = max(-1.0, min(1.0, level))
        self._draw_grid()

    @property
    def time_scale(self) -> int:
        """Get time scale (samples per pixel)."""
        return self._time_scale

    @time_scale.setter
    def time_scale(self, scale: int):
        """Set time scale."""
        self._time_scale = max(1, min(32, scale))
        self._buffer_size = self._width * self._time_scale * 2
        self._buffer = np.zeros(self._buffer_size, dtype=np.float32)
        self._write_pos = 0

    @property
    def frozen(self) -> bool:
        """Whether display is frozen."""
        return self._frozen

    @property
    def peak_level(self) -> float:
        """Current peak level."""
        return self._peak_level

    @property
    def display_mode(self) -> DisplayMode:
        """Get display mode."""
        return self._display_mode

    @display_mode.setter
    def display_mode(self, mode: DisplayMode):
        """Set display mode."""
        self._display_mode = mode
        self.clear()

    def get_time_per_division(self) -> float:
        """Get time per horizontal division in milliseconds."""
        samples_per_div = (self._width / self.GRID_DIVISIONS_X) * self._time_scale
        return (samples_per_div / self._sample_rate) * 1000.0

    def __repr__(self) -> str:
        return f"Oscilloscope({self._width}x{self._height}, trigger={self._trigger_mode.name})"
