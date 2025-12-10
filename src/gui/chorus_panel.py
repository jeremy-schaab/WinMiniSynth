# Chorus Panel
"""
chorus_panel - GUI controls for the chorus effect.

Provides:
- Enable/disable toggle
- Rate slider (0.1-5.0 Hz)
- Depth slider (0-100%)
- Voices selector (2-4)
- Wet/dry mix slider
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from .styles import COLORS, FONTS, DIMENSIONS, ColorScheme


class ChorusPanel(ttk.LabelFrame):
    """Chorus effect control panel.

    Provides GUI controls for chorus settings including enable/disable,
    rate, depth, voices, and wet/dry mix.

    Attributes:
        enabled: Whether chorus is enabled
        rate: LFO rate in Hz (0.1-5.0)
        depth: Modulation depth (0.0-1.0)
        voices: Number of voices (2-4)
        wet_dry: Wet/dry mix (0.0-1.0)
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_enable_change: Optional[Callable[[bool], None]] = None,
        on_rate_change: Optional[Callable[[float], None]] = None,
        on_depth_change: Optional[Callable[[float], None]] = None,
        on_voices_change: Optional[Callable[[int], None]] = None,
        on_wet_dry_change: Optional[Callable[[float], None]] = None,
        **kwargs
    ):
        """Initialize chorus panel.

        Args:
            parent: Parent widget
            on_enable_change: Callback when chorus enabled/disabled
            on_rate_change: Callback when LFO rate changes
            on_depth_change: Callback when depth changes
            on_voices_change: Callback when voice count changes
            on_wet_dry_change: Callback when wet/dry mix changes
        """
        super().__init__(
            parent,
            text="CHORUS",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_small'],
            **kwargs
        )

        # Callbacks
        self._on_enable_change = on_enable_change
        self._on_rate_change = on_rate_change
        self._on_depth_change = on_depth_change
        self._on_voices_change = on_voices_change
        self._on_wet_dry_change = on_wet_dry_change

        # Variables
        self._enabled_var = tk.BooleanVar(value=False)
        self._rate_var = tk.DoubleVar(value=0.5)
        self._depth_var = tk.DoubleVar(value=0.5)
        self._voices_var = tk.IntVar(value=3)
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

        # Rate slider
        rate_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        rate_frame.pack(fill='x', pady=(0, 4))

        ttk.Label(
            rate_frame,
            text="Rate",
            style='Dark.TLabel',
            width=5
        ).pack(side='left')

        self._rate_slider = ttk.Scale(
            rate_frame,
            from_=0.1,
            to=5.0,
            variable=self._rate_var,
            orient='horizontal',
            length=100,
            style='Dark.Horizontal.TScale',
            command=self._on_rate_slider_change
        )
        self._rate_slider.pack(side='left', fill='x', expand=True, padx=(0, 4))

        self._rate_label = ttk.Label(
            rate_frame,
            text="0.5Hz",
            style='Value.TLabel',
            width=5
        )
        self._rate_label.pack(side='right')

        # Depth slider
        depth_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        depth_frame.pack(fill='x', pady=(0, 4))

        ttk.Label(
            depth_frame,
            text="Depth",
            style='Dark.TLabel',
            width=5
        ).pack(side='left')

        self._depth_slider = ttk.Scale(
            depth_frame,
            from_=0.0,
            to=1.0,
            variable=self._depth_var,
            orient='horizontal',
            length=100,
            style='Dark.Horizontal.TScale',
            command=self._on_depth_slider_change
        )
        self._depth_slider.pack(side='left', fill='x', expand=True, padx=(0, 4))

        self._depth_label = ttk.Label(
            depth_frame,
            text="50%",
            style='Value.TLabel',
            width=4
        )
        self._depth_label.pack(side='right')

        # Voices selector (compact)
        voices_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        voices_frame.pack(fill='x', pady=(0, 4))

        ttk.Label(
            voices_frame,
            text="Voices",
            style='Dark.TLabel',
            width=5
        ).pack(side='left')

        for v in [2, 3, 4]:
            rb = ttk.Radiobutton(
                voices_frame,
                text=str(v),
                value=v,
                variable=self._voices_var,
                style='Dark.TRadiobutton',
                command=self._on_voices_change_internal
            )
            rb.pack(side='left', padx=2)

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

    def _on_rate_slider_change(self, value):
        """Handle rate slider change."""
        rate = float(value)
        self._rate_label.configure(text=f"{rate:.1f}Hz")

        if self._on_rate_change:
            self._on_rate_change(rate)

    def _on_depth_slider_change(self, value):
        """Handle depth slider change."""
        depth = float(value)
        self._depth_label.configure(text=f"{int(depth * 100)}%")

        if self._on_depth_change:
            self._on_depth_change(depth)

    def _on_voices_change_internal(self):
        """Handle voices radio button change."""
        voices = self._voices_var.get()

        if self._on_voices_change:
            self._on_voices_change(voices)

    def _on_wet_dry_slider_change(self, value):
        """Handle wet/dry slider change."""
        mix = float(value)
        self._wet_dry_label.configure(text=f"{int(mix * 100)}%")

        if self._on_wet_dry_change:
            self._on_wet_dry_change(mix)

    # Public properties

    @property
    def enabled(self) -> bool:
        """Get whether chorus is enabled."""
        return self._enabled_var.get()

    @enabled.setter
    def enabled(self, value: bool):
        """Set whether chorus is enabled."""
        self._enabled_var.set(value)
        self._on_enable_toggle()

    @property
    def rate(self) -> float:
        """Get LFO rate in Hz."""
        return self._rate_var.get()

    @rate.setter
    def rate(self, value: float):
        """Set LFO rate in Hz."""
        value = max(0.1, min(5.0, value))
        self._rate_var.set(value)
        self._rate_label.configure(text=f"{value:.1f}Hz")

    @property
    def depth(self) -> float:
        """Get modulation depth."""
        return self._depth_var.get()

    @depth.setter
    def depth(self, value: float):
        """Set modulation depth."""
        value = max(0.0, min(1.0, value))
        self._depth_var.set(value)
        self._depth_label.configure(text=f"{int(value * 100)}%")

    @property
    def voices(self) -> int:
        """Get number of voices."""
        return self._voices_var.get()

    @voices.setter
    def voices(self, value: int):
        """Set number of voices."""
        value = max(2, min(4, value))
        self._voices_var.set(value)

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
        """Get all chorus values as dict."""
        return {
            'chorus_enabled': self.enabled,
            'chorus_rate': self.rate,
            'chorus_depth': self.depth,
            'chorus_voices': self.voices,
            'chorus_wet_dry': self.wet_dry,
        }

    def set_values(self, values: dict):
        """Set chorus values from dict."""
        if 'chorus_enabled' in values:
            self.enabled = values['chorus_enabled']
        if 'chorus_rate' in values:
            self.rate = values['chorus_rate']
        if 'chorus_depth' in values:
            self.depth = values['chorus_depth']
        if 'chorus_voices' in values:
            self.voices = values['chorus_voices']
        if 'chorus_wet_dry' in values:
            self.wet_dry = values['chorus_wet_dry']
