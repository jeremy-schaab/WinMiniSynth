# Delay Panel
"""
delay_panel - GUI controls for the delay effect.

Provides:
- Enable/disable toggle
- Delay time slider (10-2000ms)
- Feedback slider (0-95%)
- Wet/dry mix slider
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from .styles import COLORS, FONTS, DIMENSIONS, ColorScheme


class DelayPanel(ttk.LabelFrame):
    """Delay effect control panel.

    Provides GUI controls for delay settings including enable/disable,
    delay time, feedback, and wet/dry mix.

    Attributes:
        enabled: Whether delay is enabled
        delay_time: Delay time in ms (10-2000)
        feedback: Feedback amount (0.0-0.95)
        wet_dry: Wet/dry mix (0.0-1.0)
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_enable_change: Optional[Callable[[bool], None]] = None,
        on_time_change: Optional[Callable[[float], None]] = None,
        on_feedback_change: Optional[Callable[[float], None]] = None,
        on_wet_dry_change: Optional[Callable[[float], None]] = None,
        **kwargs
    ):
        """Initialize delay panel.

        Args:
            parent: Parent widget
            on_enable_change: Callback when delay enabled/disabled
            on_time_change: Callback when delay time changes
            on_feedback_change: Callback when feedback changes
            on_wet_dry_change: Callback when wet/dry mix changes
        """
        super().__init__(
            parent,
            text="DELAY",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_small'],
            **kwargs
        )

        # Callbacks
        self._on_enable_change = on_enable_change
        self._on_time_change = on_time_change
        self._on_feedback_change = on_feedback_change
        self._on_wet_dry_change = on_wet_dry_change

        # Variables
        self._enabled_var = tk.BooleanVar(value=False)
        self._time_var = tk.DoubleVar(value=300.0)
        self._feedback_var = tk.DoubleVar(value=0.4)
        self._wet_dry_var = tk.DoubleVar(value=0.3)

        # Create widgets
        self._create_widgets()

    def _create_widgets(self):
        """Create panel widgets."""
        # Main container
        main_frame = ttk.Frame(self, style='Dark.TFrame')
        main_frame.pack(fill='both', expand=True)

        # Top row: Enable toggle
        top_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        top_frame.pack(fill='x', pady=(0, 8))

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
            foreground=ColorScheme.fg_muted
        )
        self._status_label.pack(side='right')

        # Time slider
        time_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        time_frame.pack(fill='x', pady=(0, 4))

        ttk.Label(
            time_frame,
            text="Time",
            style='Dark.TLabel',
            width=5
        ).pack(side='left')

        self._time_slider = ttk.Scale(
            time_frame,
            from_=10,
            to=2000,
            variable=self._time_var,
            orient='horizontal',
            length=100,
            style='Dark.Horizontal.TScale',
            command=self._on_time_slider_change
        )
        self._time_slider.pack(side='left', fill='x', expand=True, padx=(0, 4))

        self._time_label = ttk.Label(
            time_frame,
            text="300ms",
            style='Value.TLabel',
            width=6
        )
        self._time_label.pack(side='right')

        # Feedback slider
        feedback_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        feedback_frame.pack(fill='x', pady=(0, 4))

        ttk.Label(
            feedback_frame,
            text="Fdbk",
            style='Dark.TLabel',
            width=5
        ).pack(side='left')

        self._feedback_slider = ttk.Scale(
            feedback_frame,
            from_=0.0,
            to=0.95,
            variable=self._feedback_var,
            orient='horizontal',
            length=100,
            style='Dark.Horizontal.TScale',
            command=self._on_feedback_slider_change
        )
        self._feedback_slider.pack(side='left', fill='x', expand=True, padx=(0, 4))

        self._feedback_label = ttk.Label(
            feedback_frame,
            text="40%",
            style='Value.TLabel',
            width=4
        )
        self._feedback_label.pack(side='right')

        # Wet/Dry slider
        wetdry_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        wetdry_frame.pack(fill='x')

        ttk.Label(
            wetdry_frame,
            text="Mix",
            style='Dark.TLabel',
            width=5
        ).pack(side='left')

        self._wet_dry_slider = ttk.Scale(
            wetdry_frame,
            from_=0.0,
            to=1.0,
            variable=self._wet_dry_var,
            orient='horizontal',
            length=100,
            style='Dark.Horizontal.TScale',
            command=self._on_wet_dry_slider_change
        )
        self._wet_dry_slider.pack(side='left', fill='x', expand=True, padx=(0, 4))

        self._wet_dry_label = ttk.Label(
            wetdry_frame,
            text="30%",
            style='Value.TLabel',
            width=4
        )
        self._wet_dry_label.pack(side='right')

    def _on_enable_toggle(self):
        """Handle enable toggle."""
        enabled = self._enabled_var.get()

        if enabled:
            self._status_label.configure(text="ON", foreground=ColorScheme.success)
        else:
            self._status_label.configure(text="OFF", foreground=ColorScheme.fg_muted)

        if self._on_enable_change:
            self._on_enable_change(enabled)

    def _on_time_slider_change(self, value):
        """Handle time slider change."""
        time_ms = float(value)
        self._time_label.configure(text=f"{int(time_ms)}ms")

        if self._on_time_change:
            self._on_time_change(time_ms)

    def _on_feedback_slider_change(self, value):
        """Handle feedback slider change."""
        feedback = float(value)
        self._feedback_label.configure(text=f"{int(feedback * 100)}%")

        if self._on_feedback_change:
            self._on_feedback_change(feedback)

    def _on_wet_dry_slider_change(self, value):
        """Handle wet/dry slider change."""
        mix = float(value)
        self._wet_dry_label.configure(text=f"{int(mix * 100)}%")

        if self._on_wet_dry_change:
            self._on_wet_dry_change(mix)

    # Public properties

    @property
    def enabled(self) -> bool:
        """Get whether delay is enabled."""
        return self._enabled_var.get()

    @enabled.setter
    def enabled(self, value: bool):
        """Set whether delay is enabled."""
        self._enabled_var.set(value)
        self._on_enable_toggle()

    @property
    def delay_time(self) -> float:
        """Get delay time in ms."""
        return self._time_var.get()

    @delay_time.setter
    def delay_time(self, value: float):
        """Set delay time in ms."""
        value = max(10, min(2000, value))
        self._time_var.set(value)
        self._time_label.configure(text=f"{int(value)}ms")

    @property
    def feedback(self) -> float:
        """Get feedback amount."""
        return self._feedback_var.get()

    @feedback.setter
    def feedback(self, value: float):
        """Set feedback amount."""
        value = max(0.0, min(0.95, value))
        self._feedback_var.set(value)
        self._feedback_label.configure(text=f"{int(value * 100)}%")

    @property
    def wet_dry(self) -> float:
        """Get wet/dry mix."""
        return self._wet_dry_var.get()

    @wet_dry.setter
    def wet_dry(self, value: float):
        """Set wet/dry mix."""
        value = max(0.0, min(1.0, value))
        self._wet_dry_var.set(value)
        self._wet_dry_label.configure(text=f"{int(value * 100)}%")

    def get_values(self) -> dict:
        """Get all delay values as dict."""
        return {
            'delay_enabled': self.enabled,
            'delay_time': self.delay_time,
            'delay_feedback': self.feedback,
            'delay_wet_dry': self.wet_dry,
        }

    def set_values(self, values: dict):
        """Set delay values from dict."""
        if 'delay_enabled' in values:
            self.enabled = values['delay_enabled']
        if 'delay_time' in values:
            self.delay_time = values['delay_time']
        if 'delay_feedback' in values:
            self.feedback = values['delay_feedback']
        if 'delay_wet_dry' in values:
            self.wet_dry = values['delay_wet_dry']
