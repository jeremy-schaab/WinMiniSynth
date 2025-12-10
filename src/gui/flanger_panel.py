# Flanger Panel
"""
flanger_panel - GUI controls for the flanger effect.

Provides:
- Enable/disable toggle
- Rate slider (0.1-5.0 Hz)
- Depth slider (0-100%)
- Feedback slider (0-95%)
- Wet/dry mix slider
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from .styles import COLORS, FONTS, DIMENSIONS, ColorScheme


class FlangerPanel(ttk.LabelFrame):
    """Flanger effect control panel.

    Provides GUI controls for flanger settings including enable/disable,
    rate, depth, feedback, and wet/dry mix.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_enable_change: Optional[Callable[[bool], None]] = None,
        on_rate_change: Optional[Callable[[float], None]] = None,
        on_depth_change: Optional[Callable[[float], None]] = None,
        on_feedback_change: Optional[Callable[[float], None]] = None,
        on_wet_dry_change: Optional[Callable[[float], None]] = None,
        **kwargs
    ):
        """Initialize flanger panel.

        Args:
            parent: Parent widget
            on_enable_change: Callback when flanger enabled/disabled
            on_rate_change: Callback when LFO rate changes
            on_depth_change: Callback when depth changes
            on_feedback_change: Callback when feedback changes
            on_wet_dry_change: Callback when wet/dry mix changes
        """
        super().__init__(
            parent,
            text="FLANGER",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_small'],
            **kwargs
        )

        # Callbacks
        self._on_enable_change = on_enable_change
        self._on_rate_change = on_rate_change
        self._on_depth_change = on_depth_change
        self._on_feedback_change = on_feedback_change
        self._on_wet_dry_change = on_wet_dry_change

        # Variables
        self._enabled_var = tk.BooleanVar(value=False)
        self._rate_var = tk.DoubleVar(value=0.3)
        self._depth_var = tk.DoubleVar(value=0.7)
        self._feedback_var = tk.DoubleVar(value=0.5)
        self._wet_dry_var = tk.DoubleVar(value=0.5)

        # Create widgets
        self._create_widgets()

    def _create_widgets(self):
        """Create panel widgets."""
        # Main container
        main_frame = ttk.Frame(self, style='Dark.TFrame')
        main_frame.pack(fill='both', expand=True)

        # Top row: Enable toggle
        top_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        top_frame.pack(fill='x', pady=(0, 4))

        self._enable_btn = ttk.Checkbutton(
            top_frame,
            text="Enable",
            variable=self._enabled_var,
            style='Dark.TCheckbutton',
            command=self._on_enable_toggle
        )
        self._enable_btn.pack(side='left')

        # Status indicator
        self._status_label = ttk.Label(
            top_frame,
            text="OFF",
            style='Dark.TLabel',
            foreground=COLORS.get('fg_secondary', '#808080')
        )
        self._status_label.pack(side='right')

        # Sliders frame
        sliders_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        sliders_frame.pack(fill='both', expand=True)

        # Rate slider
        self._create_slider(
            sliders_frame, "Rate", self._rate_var,
            0.1, 5.0, self._on_rate_slider, "Hz", row=0
        )

        # Depth slider
        self._create_slider(
            sliders_frame, "Depth", self._depth_var,
            0.0, 1.0, self._on_depth_slider, "%", row=1, mult=100
        )

        # Feedback slider
        self._create_slider(
            sliders_frame, "Fdbk", self._feedback_var,
            0.0, 0.95, self._on_feedback_slider, "%", row=2, mult=100
        )

        # Wet/Dry slider
        self._create_slider(
            sliders_frame, "Mix", self._wet_dry_var,
            0.0, 1.0, self._on_wet_dry_slider, "%", row=3, mult=100
        )

    def _create_slider(self, parent, label, var, min_val, max_val, callback, unit, row, mult=1):
        """Create a labeled slider row."""
        frame = ttk.Frame(parent, style='Dark.TFrame')
        frame.pack(fill='x', pady=2)

        ttk.Label(
            frame,
            text=label,
            style='Dark.TLabel',
            width=5
        ).pack(side='left')

        slider = ttk.Scale(
            frame,
            from_=min_val,
            to=max_val,
            variable=var,
            orient='horizontal',
            length=80,
            style='Dark.Horizontal.TScale',
            command=callback
        )
        slider.pack(side='left', padx=4, expand=True, fill='x')

        value_label = ttk.Label(
            frame,
            text=f"{var.get() * mult:.0f}{unit}" if mult != 1 else f"{var.get():.1f}{unit}",
            style='Value.TLabel',
            width=5
        )
        value_label.pack(side='right')

        # Store reference for updating
        setattr(self, f"_{label.lower()}_label", value_label)
        setattr(self, f"_{label.lower()}_mult", mult)
        setattr(self, f"_{label.lower()}_unit", unit)

    def _on_enable_toggle(self):
        """Handle enable toggle."""
        enabled = self._enabled_var.get()
        self._status_label.config(
            text="ON" if enabled else "OFF",
            foreground=COLORS.get('accent_primary', '#00b4d8') if enabled else COLORS.get('fg_secondary', '#808080')
        )
        if self._on_enable_change:
            self._on_enable_change(enabled)

    def _on_rate_slider(self, value):
        """Handle rate slider change."""
        val = float(value)
        self._rate_label.config(text=f"{val:.1f}Hz")
        if self._on_rate_change:
            self._on_rate_change(val)

    def _on_depth_slider(self, value):
        """Handle depth slider change."""
        val = float(value)
        self._depth_label.config(text=f"{val * 100:.0f}%")
        if self._on_depth_change:
            self._on_depth_change(val)

    def _on_feedback_slider(self, value):
        """Handle feedback slider change."""
        val = float(value)
        self._fdbk_label.config(text=f"{val * 100:.0f}%")
        if self._on_feedback_change:
            self._on_feedback_change(val)

    def _on_wet_dry_slider(self, value):
        """Handle wet/dry slider change."""
        val = float(value)
        self._mix_label.config(text=f"{val * 100:.0f}%")
        if self._on_wet_dry_change:
            self._on_wet_dry_change(val)

    # Properties
    @property
    def enabled(self) -> bool:
        """Whether flanger is enabled."""
        return self._enabled_var.get()

    @enabled.setter
    def enabled(self, value: bool):
        """Set enabled state."""
        self._enabled_var.set(value)
        self._on_enable_toggle()

    @property
    def rate(self) -> float:
        """LFO rate in Hz."""
        return self._rate_var.get()

    @rate.setter
    def rate(self, value: float):
        """Set LFO rate."""
        self._rate_var.set(value)
        self._on_rate_slider(value)

    @property
    def depth(self) -> float:
        """Modulation depth (0.0-1.0)."""
        return self._depth_var.get()

    @depth.setter
    def depth(self, value: float):
        """Set modulation depth."""
        self._depth_var.set(value)
        self._on_depth_slider(value)

    @property
    def feedback(self) -> float:
        """Feedback amount (0.0-0.95)."""
        return self._feedback_var.get()

    @feedback.setter
    def feedback(self, value: float):
        """Set feedback amount."""
        self._feedback_var.set(value)
        self._on_feedback_slider(value)

    @property
    def wet_dry(self) -> float:
        """Wet/dry mix (0.0-1.0)."""
        return self._wet_dry_var.get()

    @wet_dry.setter
    def wet_dry(self, value: float):
        """Set wet/dry mix."""
        self._wet_dry_var.set(value)
        self._on_wet_dry_slider(value)
