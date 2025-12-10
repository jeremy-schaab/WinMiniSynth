# Visualization Panel Module
"""
panel - Container widget for audio visualizations.

Provides a combined panel containing:
- Oscilloscope (waveform display)
- Filter curve (frequency response)
- Controls for display settings

Usage:
    panel = VisualizationPanel(parent)
    panel.pack(fill='both', expand=True)

    # Update from audio callback:
    panel.update_waveform(audio_samples)

    # Update when filter changes:
    panel.update_filter(cutoff=1000, resonance=0.5)
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import numpy as np

from .oscilloscope import Oscilloscope, TriggerMode, DisplayMode
from .filter_curve import FilterCurve, ScaleMode

# Import styles - handle import for both module and standalone use
try:
    from gui.styles import COLORS, FONTS, DIMENSIONS, ColorScheme
except ImportError:
    COLORS = {
        'bg_dark': '#1a1a1a',
        'bg_panel': '#252525',
        'fg_primary': '#e0e0e0',
        'fg_secondary': '#a0a0a0',
        'border': '#404040',
        'accent_primary': '#00b4d8',
    }
    FONTS = {
        'label': ('Segoe UI', 9),
        'small': ('Segoe UI', 8),
    }
    DIMENSIONS = {
        'padding_small': 4,
        'padding_medium': 8,
    }
    ColorScheme = None


class VisualizationPanel(ttk.Frame):
    """Combined visualization panel with oscilloscope and filter display.

    Contains both visualization widgets with optional controls for
    adjusting display parameters.

    Attributes:
        oscilloscope: The Oscilloscope widget
        filter_curve: The FilterCurve widget
    """

    # Default sizes
    SCOPE_HEIGHT = 150
    FILTER_HEIGHT = 120
    MIN_WIDTH = 300

    def __init__(
        self,
        parent: tk.Widget,
        show_controls: bool = True,
        show_filter: bool = True,
        sample_rate: int = 44100,
        **kwargs
    ):
        """Initialize visualization panel.

        Args:
            parent: Parent widget
            show_controls: Whether to show control buttons
            show_filter: Whether to show filter response section
            sample_rate: Audio sample rate
        """
        super().__init__(parent, style='Dark.TFrame', **kwargs)

        self._sample_rate = sample_rate
        self._show_controls = show_controls
        self._show_filter = show_filter

        # Create widgets
        self._create_widgets()

        # Update timer (for scheduled redraws)
        self._update_pending = False

    def _create_widgets(self):
        """Create panel widgets."""
        # Main container with two sections
        main_frame = ttk.Frame(self, style='Dark.TFrame')
        main_frame.pack(fill='both', expand=True)

        # Oscilloscope section
        scope_frame = ttk.LabelFrame(
            main_frame,
            text="WAVEFORM",
            style='Dark.TLabelframe',
            padding=DIMENSIONS.get('padding_small', 4)
        )
        scope_frame.pack(fill='x', padx=2, pady=(0, 4))

        # Oscilloscope canvas
        self.oscilloscope = Oscilloscope(
            scope_frame,
            height=self.SCOPE_HEIGHT,
            sample_rate=self._sample_rate
        )
        self.oscilloscope.pack(fill='x', expand=True)

        # Oscilloscope controls
        if self._show_controls:
            scope_controls = ttk.Frame(scope_frame, style='Dark.TFrame')
            scope_controls.pack(fill='x', pady=(4, 0))

            # Trigger mode selector
            ttk.Label(
                scope_controls,
                text="Trigger:",
                style='Dark.TLabel'
            ).pack(side='left', padx=(0, 4))

            self._trigger_var = tk.StringVar(value="AUTO")
            trigger_combo = ttk.Combobox(
                scope_controls,
                textvariable=self._trigger_var,
                values=["FREE", "RISING", "FALLING", "AUTO"],
                state='readonly',
                width=8,
                style='Dark.TCombobox'
            )
            trigger_combo.pack(side='left', padx=(0, 8))
            trigger_combo.bind('<<ComboboxSelected>>', self._on_trigger_change)

            # Time scale
            ttk.Label(
                scope_controls,
                text="Scale:",
                style='Dark.TLabel'
            ).pack(side='left', padx=(0, 4))

            self._scale_var = tk.IntVar(value=4)
            scale_spin = ttk.Spinbox(
                scope_controls,
                from_=1,
                to=32,
                width=4,
                textvariable=self._scale_var,
                command=self._on_scale_change,
                style='Dark.TSpinbox'
            )
            scale_spin.pack(side='left', padx=(0, 8))

            # Freeze button
            self._freeze_btn = ttk.Button(
                scope_controls,
                text="Freeze",
                style='Dark.TButton',
                width=6,
                command=self._toggle_freeze
            )
            self._freeze_btn.pack(side='left', padx=(0, 4))

            # Clear button
            ttk.Button(
                scope_controls,
                text="Clear",
                style='Dark.TButton',
                width=6,
                command=self._clear_scope
            ).pack(side='left')

            # Time per division label
            self._time_label = ttk.Label(
                scope_controls,
                text="",
                style='Value.TLabel'
            )
            self._time_label.pack(side='right')
            self._update_time_label()

        # Filter curve section (optional)
        if self._show_filter:
            filter_frame = ttk.LabelFrame(
                main_frame,
                text="FILTER RESPONSE",
                style='Dark.TLabelframe',
                padding=DIMENSIONS.get('padding_small', 4)
            )
            filter_frame.pack(fill='x', padx=2, pady=(0, 2))

            # Filter curve canvas
            self.filter_curve = FilterCurve(
                filter_frame,
                height=self.FILTER_HEIGHT,
                sample_rate=self._sample_rate
            )
            self.filter_curve.pack(fill='x', expand=True)

            # Filter controls
            if self._show_controls:
                filter_controls = ttk.Frame(filter_frame, style='Dark.TFrame')
                filter_controls.pack(fill='x', pady=(4, 0))

                # Scale mode selector
                ttk.Label(
                    filter_controls,
                    text="Scale:",
                    style='Dark.TLabel'
                ).pack(side='left', padx=(0, 4))

                self._filter_scale_var = tk.StringVar(value="dB")
                scale_combo = ttk.Combobox(
                    filter_controls,
                    textvariable=self._filter_scale_var,
                    values=["dB", "Linear"],
                    state='readonly',
                    width=6,
                    style='Dark.TCombobox'
                )
                scale_combo.pack(side='left', padx=(0, 8))
                scale_combo.bind('<<ComboboxSelected>>', self._on_filter_scale_change)

                # Show/hide labels
                self._labels_var = tk.BooleanVar(value=True)
                ttk.Checkbutton(
                    filter_controls,
                    text="Labels",
                    variable=self._labels_var,
                    style='Dark.TCheckbutton',
                    command=self._on_labels_toggle
                ).pack(side='left', padx=(0, 8))

                # Filter info label
                self._filter_info = ttk.Label(
                    filter_controls,
                    text="",
                    style='Value.TLabel'
                )
                self._filter_info.pack(side='right')

    def _on_trigger_change(self, event=None):
        """Handle trigger mode change."""
        mode_map = {
            "FREE": TriggerMode.FREE_RUN,
            "RISING": TriggerMode.RISING,
            "FALLING": TriggerMode.FALLING,
            "AUTO": TriggerMode.AUTO
        }
        mode = mode_map.get(self._trigger_var.get(), TriggerMode.AUTO)
        self.oscilloscope.trigger_mode = mode

    def _on_scale_change(self):
        """Handle time scale change."""
        try:
            scale = self._scale_var.get()
            self.oscilloscope.time_scale = scale
            self._update_time_label()
        except (ValueError, tk.TclError):
            pass

    def _toggle_freeze(self):
        """Toggle oscilloscope freeze."""
        if self.oscilloscope.frozen:
            self.oscilloscope.unfreeze()
            self._freeze_btn.configure(text="Freeze")
        else:
            self.oscilloscope.freeze()
            self._freeze_btn.configure(text="Unfreeze")

    def _clear_scope(self):
        """Clear oscilloscope display."""
        self.oscilloscope.clear()

    def _on_filter_scale_change(self, event=None):
        """Handle filter scale mode change."""
        if self._filter_scale_var.get() == "dB":
            self.filter_curve.scale_mode = ScaleMode.DECIBEL
        else:
            self.filter_curve.scale_mode = ScaleMode.LINEAR

    def _on_labels_toggle(self):
        """Handle label visibility toggle."""
        self.filter_curve.show_labels = self._labels_var.get()

    def _update_time_label(self):
        """Update time per division label."""
        if hasattr(self, '_time_label'):
            time_ms = self.oscilloscope.get_time_per_division()
            if time_ms >= 1.0:
                self._time_label.configure(text=f"{time_ms:.1f}ms/div")
            else:
                self._time_label.configure(text=f"{time_ms*1000:.0f}us/div")

    # Public methods for updating displays

    def update_waveform(self, samples: np.ndarray):
        """Update oscilloscope with new audio samples.

        Call this from audio callback or update loop.

        Args:
            samples: Audio samples (mono, float32)
        """
        self.oscilloscope.update_waveform(samples)

    def update_filter(self, cutoff: float, resonance: float):
        """Update filter curve display.

        Args:
            cutoff: Filter cutoff frequency in Hz
            resonance: Filter resonance (0.0 to 1.0)
        """
        self.filter_curve.update_response(cutoff, resonance)

        # Update info label
        if hasattr(self, '_filter_info'):
            if cutoff >= 1000:
                freq_str = f"{cutoff/1000:.1f}kHz"
            else:
                freq_str = f"{cutoff:.0f}Hz"
            self._filter_info.configure(text=f"Fc: {freq_str}, Q: {resonance:.2f}")

    def update_filter_from_object(self, filter_obj):
        """Update filter curve from a filter object.

        Args:
            filter_obj: Object with cutoff and resonance properties
        """
        if hasattr(filter_obj, 'cutoff') and hasattr(filter_obj, 'resonance'):
            self.update_filter(filter_obj.cutoff, filter_obj.resonance)

    def set_trigger_mode(self, mode: TriggerMode):
        """Set oscilloscope trigger mode.

        Args:
            mode: TriggerMode enum value
        """
        self.oscilloscope.trigger_mode = mode
        if hasattr(self, '_trigger_var'):
            mode_names = {
                TriggerMode.FREE_RUN: "FREE",
                TriggerMode.RISING: "RISING",
                TriggerMode.FALLING: "FALLING",
                TriggerMode.AUTO: "AUTO"
            }
            self._trigger_var.set(mode_names.get(mode, "AUTO"))

    def set_time_scale(self, scale: int):
        """Set oscilloscope time scale.

        Args:
            scale: Samples per pixel (1-32)
        """
        self.oscilloscope.time_scale = scale
        if hasattr(self, '_scale_var'):
            self._scale_var.set(scale)
        self._update_time_label()

    def freeze_scope(self):
        """Freeze oscilloscope display."""
        self.oscilloscope.freeze()
        if hasattr(self, '_freeze_btn'):
            self._freeze_btn.configure(text="Unfreeze")

    def unfreeze_scope(self):
        """Unfreeze oscilloscope display."""
        self.oscilloscope.unfreeze()
        if hasattr(self, '_freeze_btn'):
            self._freeze_btn.configure(text="Freeze")

    def clear(self):
        """Clear all displays."""
        self.oscilloscope.clear()
        self.filter_curve.clear()

    # Properties

    @property
    def scope_frozen(self) -> bool:
        """Whether oscilloscope is frozen."""
        return self.oscilloscope.frozen

    @property
    def peak_level(self) -> float:
        """Current peak level from oscilloscope."""
        return self.oscilloscope.peak_level

    def get_settings(self) -> dict:
        """Get current visualization settings.

        Returns:
            Dict of current settings
        """
        return {
            'trigger_mode': self.oscilloscope.trigger_mode.name,
            'time_scale': self.oscilloscope.time_scale,
            'filter_scale': self.filter_curve.scale_mode.name,
            'show_labels': self.filter_curve.show_labels,
            'frozen': self.oscilloscope.frozen,
        }

    def set_settings(self, settings: dict):
        """Apply visualization settings.

        Args:
            settings: Dict of settings from get_settings()
        """
        if 'trigger_mode' in settings:
            mode = getattr(TriggerMode, settings['trigger_mode'], TriggerMode.AUTO)
            self.set_trigger_mode(mode)

        if 'time_scale' in settings:
            self.set_time_scale(settings['time_scale'])

        if 'filter_scale' in settings:
            mode = getattr(ScaleMode, settings['filter_scale'], ScaleMode.DECIBEL)
            self.filter_curve.scale_mode = mode
            if hasattr(self, '_filter_scale_var'):
                self._filter_scale_var.set("dB" if mode == ScaleMode.DECIBEL else "Linear")

        if 'show_labels' in settings:
            self.filter_curve.show_labels = settings['show_labels']
            if hasattr(self, '_labels_var'):
                self._labels_var.set(settings['show_labels'])

        if 'frozen' in settings:
            if settings['frozen']:
                self.freeze_scope()
            else:
                self.unfreeze_scope()

    def __repr__(self) -> str:
        return f"VisualizationPanel(scope={self.oscilloscope}, filter={self.filter_curve})"
