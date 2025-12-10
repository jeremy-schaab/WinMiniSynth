# Reverb Panel
"""
reverb_panel - GUI controls for the reverb effect.

Provides:
- Enable/disable toggle
- Wet/dry mix slider
- Room size slider

Usage:
    panel = ReverbPanel(
        parent,
        on_enable_change=lambda enabled: reverb.enabled = enabled,
        on_wet_dry_change=lambda mix: reverb.wet_dry = mix,
        on_room_size_change=lambda size: reverb.room_size = size
    )
    panel.pack()
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from .styles import COLORS, FONTS, DIMENSIONS, ColorScheme


class ReverbPanel(ttk.LabelFrame):
    """Reverb effect control panel.

    Provides GUI controls for reverb settings including enable/disable,
    wet/dry mix, and room size.

    Attributes:
        enabled: Whether reverb is enabled
        wet_dry: Wet/dry mix (0.0-1.0)
        room_size: Room size (0.0-1.0)
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_enable_change: Optional[Callable[[bool], None]] = None,
        on_wet_dry_change: Optional[Callable[[float], None]] = None,
        on_room_size_change: Optional[Callable[[float], None]] = None,
        **kwargs
    ):
        """Initialize reverb panel.

        Args:
            parent: Parent widget
            on_enable_change: Callback when reverb enabled/disabled
            on_wet_dry_change: Callback when wet/dry mix changes
            on_room_size_change: Callback when room size changes
        """
        super().__init__(
            parent,
            text="REVERB",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_small'],
            **kwargs
        )

        # Callbacks
        self._on_enable_change = on_enable_change
        self._on_wet_dry_change = on_wet_dry_change
        self._on_room_size_change = on_room_size_change

        # Variables
        self._enabled_var = tk.BooleanVar(value=False)
        self._wet_dry_var = tk.DoubleVar(value=0.3)
        self._room_size_var = tk.DoubleVar(value=0.5)

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

        # Wet/Dry slider
        wetdry_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        wetdry_frame.pack(fill='x', pady=(0, 4))

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

        # Room Size slider
        room_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        room_frame.pack(fill='x')

        ttk.Label(
            room_frame,
            text="Room",
            style='Dark.TLabel',
            width=5
        ).pack(side='left')

        self._room_size_slider = ttk.Scale(
            room_frame,
            from_=0.0,
            to=1.0,
            variable=self._room_size_var,
            orient='horizontal',
            length=100,
            style='Dark.Horizontal.TScale',
            command=self._on_room_size_slider_change
        )
        self._room_size_slider.pack(side='left', fill='x', expand=True, padx=(0, 4))

        self._room_size_label = ttk.Label(
            room_frame,
            text="50%",
            style='Value.TLabel',
            width=4
        )
        self._room_size_label.pack(side='right')

    def _on_enable_toggle(self):
        """Handle enable toggle."""
        enabled = self._enabled_var.get()

        if enabled:
            self._status_label.configure(text="ON", foreground=ColorScheme.success)
        else:
            self._status_label.configure(text="OFF", foreground=ColorScheme.fg_muted)

        if self._on_enable_change:
            self._on_enable_change(enabled)

    def _on_wet_dry_slider_change(self, value):
        """Handle wet/dry slider change."""
        mix = float(value)
        self._wet_dry_label.configure(text=f"{int(mix * 100)}%")

        if self._on_wet_dry_change:
            self._on_wet_dry_change(mix)

    def _on_room_size_slider_change(self, value):
        """Handle room size slider change."""
        size = float(value)
        self._room_size_label.configure(text=f"{int(size * 100)}%")

        if self._on_room_size_change:
            self._on_room_size_change(size)

    # Public properties

    @property
    def enabled(self) -> bool:
        """Get whether reverb is enabled."""
        return self._enabled_var.get()

    @enabled.setter
    def enabled(self, value: bool):
        """Set whether reverb is enabled."""
        self._enabled_var.set(value)
        self._on_enable_toggle()

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

    @property
    def room_size(self) -> float:
        """Get room size."""
        return self._room_size_var.get()

    @room_size.setter
    def room_size(self, value: float):
        """Set room size."""
        value = max(0.0, min(1.0, value))
        self._room_size_var.set(value)
        self._room_size_label.configure(text=f"{int(value * 100)}%")

    def get_values(self) -> dict:
        """Get all reverb values as dict."""
        return {
            'reverb_enabled': self.enabled,
            'reverb_wet_dry': self.wet_dry,
            'reverb_room_size': self.room_size,
        }

    def set_values(self, values: dict):
        """Set reverb values from dict."""
        if 'reverb_enabled' in values:
            self.enabled = values['reverb_enabled']
        if 'reverb_wet_dry' in values:
            self.wet_dry = values['reverb_wet_dry']
        if 'reverb_room_size' in values:
            self.room_size = values['reverb_room_size']
