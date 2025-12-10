# Distortion Panel
"""
distortion_panel - GUI controls for the distortion effect.

Provides:
- Enable/disable toggle
- Drive slider (1-20)
- Tone slider (0-100%)
- Mode selector (soft/hard/tube)
- Mix slider (0-100%)
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from .styles import COLORS, FONTS, DIMENSIONS, ColorScheme


class DistortionPanel(ttk.LabelFrame):
    """Distortion effect control panel.

    Provides GUI controls for distortion settings including enable/disable,
    drive, tone, mode, and mix.

    Attributes:
        enabled: Whether distortion is enabled
        drive: Drive amount (1.0-20.0)
        tone: Tone (0.0-1.0, dark to bright)
        mode: Waveshaping mode ('soft', 'hard', 'tube')
        mix: Wet/dry mix (0.0-1.0)
    """

    MODES = ['soft', 'hard', 'tube']

    def __init__(
        self,
        parent: tk.Widget,
        on_enable_change: Optional[Callable[[bool], None]] = None,
        on_drive_change: Optional[Callable[[float], None]] = None,
        on_tone_change: Optional[Callable[[float], None]] = None,
        on_mode_change: Optional[Callable[[str], None]] = None,
        on_mix_change: Optional[Callable[[float], None]] = None,
        **kwargs
    ):
        """Initialize distortion panel.

        Args:
            parent: Parent widget
            on_enable_change: Callback when distortion enabled/disabled
            on_drive_change: Callback when drive changes
            on_tone_change: Callback when tone changes
            on_mode_change: Callback when mode changes
            on_mix_change: Callback when mix changes
        """
        super().__init__(
            parent,
            text="DISTORTION",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_small'],
            **kwargs
        )

        # Callbacks
        self._on_enable_change = on_enable_change
        self._on_drive_change = on_drive_change
        self._on_tone_change = on_tone_change
        self._on_mode_change = on_mode_change
        self._on_mix_change = on_mix_change

        # Variables
        self._enabled_var = tk.BooleanVar(value=False)
        self._drive_var = tk.DoubleVar(value=2.0)
        self._tone_var = tk.DoubleVar(value=0.5)
        self._mode_var = tk.StringVar(value='soft')
        self._mix_var = tk.DoubleVar(value=1.0)

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

        # Drive slider
        drive_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        drive_frame.pack(fill='x', pady=(0, 4))

        ttk.Label(
            drive_frame,
            text="Drive",
            style='Dark.TLabel',
            width=5
        ).pack(side='left')

        self._drive_slider = ttk.Scale(
            drive_frame,
            from_=1.0,
            to=20.0,
            variable=self._drive_var,
            orient='horizontal',
            length=100,
            style='Dark.Horizontal.TScale',
            command=self._on_drive_slider_change
        )
        self._drive_slider.pack(side='left', fill='x', expand=True, padx=(0, 4))

        self._drive_label = ttk.Label(
            drive_frame,
            text="2.0x",
            style='Value.TLabel',
            width=5
        )
        self._drive_label.pack(side='right')

        # Tone slider
        tone_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        tone_frame.pack(fill='x', pady=(0, 4))

        ttk.Label(
            tone_frame,
            text="Tone",
            style='Dark.TLabel',
            width=5
        ).pack(side='left')

        self._tone_slider = ttk.Scale(
            tone_frame,
            from_=0.0,
            to=1.0,
            variable=self._tone_var,
            orient='horizontal',
            length=100,
            style='Dark.Horizontal.TScale',
            command=self._on_tone_slider_change
        )
        self._tone_slider.pack(side='left', fill='x', expand=True, padx=(0, 4))

        self._tone_label = ttk.Label(
            tone_frame,
            text="50%",
            style='Value.TLabel',
            width=4
        )
        self._tone_label.pack(side='right')

        # Mode selector
        mode_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        mode_frame.pack(fill='x', pady=(0, 4))

        ttk.Label(
            mode_frame,
            text="Mode",
            style='Dark.TLabel',
            width=5
        ).pack(side='left')

        for mode in self.MODES:
            rb = ttk.Radiobutton(
                mode_frame,
                text=mode.capitalize(),
                value=mode,
                variable=self._mode_var,
                style='Dark.TRadiobutton',
                command=self._on_mode_change_internal
            )
            rb.pack(side='left', padx=2)

        # Mix slider
        mix_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        mix_frame.pack(fill='x')

        ttk.Label(
            mix_frame,
            text="Mix",
            style='Dark.TLabel',
            width=5
        ).pack(side='left')

        self._mix_slider = ttk.Scale(
            mix_frame,
            from_=0.0,
            to=1.0,
            variable=self._mix_var,
            orient='horizontal',
            length=100,
            style='Dark.Horizontal.TScale',
            command=self._on_mix_slider_change
        )
        self._mix_slider.pack(side='left', fill='x', expand=True, padx=(0, 4))

        self._mix_label = ttk.Label(
            mix_frame,
            text="100%",
            style='Value.TLabel',
            width=4
        )
        self._mix_label.pack(side='right')

    def _on_enable_toggle(self):
        """Handle enable toggle."""
        enabled = self._enabled_var.get()

        if enabled:
            self._status_label.configure(text="ON", foreground=ColorScheme.success)
        else:
            self._status_label.configure(text="OFF", foreground=ColorScheme.fg_muted)

        if self._on_enable_change:
            self._on_enable_change(enabled)

    def _on_drive_slider_change(self, value):
        """Handle drive slider change."""
        drive = float(value)
        self._drive_label.configure(text=f"{drive:.1f}x")

        if self._on_drive_change:
            self._on_drive_change(drive)

    def _on_tone_slider_change(self, value):
        """Handle tone slider change."""
        tone = float(value)
        self._tone_label.configure(text=f"{int(tone * 100)}%")

        if self._on_tone_change:
            self._on_tone_change(tone)

    def _on_mode_change_internal(self):
        """Handle mode radio button change."""
        mode = self._mode_var.get()

        if self._on_mode_change:
            self._on_mode_change(mode)

    def _on_mix_slider_change(self, value):
        """Handle mix slider change."""
        mix = float(value)
        self._mix_label.configure(text=f"{int(mix * 100)}%")

        if self._on_mix_change:
            self._on_mix_change(mix)

    # Public properties

    @property
    def enabled(self) -> bool:
        """Get whether distortion is enabled."""
        return self._enabled_var.get()

    @enabled.setter
    def enabled(self, value: bool):
        """Set whether distortion is enabled."""
        self._enabled_var.set(value)
        self._on_enable_toggle()

    @property
    def drive(self) -> float:
        """Get drive amount."""
        return self._drive_var.get()

    @drive.setter
    def drive(self, value: float):
        """Set drive amount."""
        value = max(1.0, min(20.0, value))
        self._drive_var.set(value)
        self._drive_label.configure(text=f"{value:.1f}x")

    @property
    def tone(self) -> float:
        """Get tone."""
        return self._tone_var.get()

    @tone.setter
    def tone(self, value: float):
        """Set tone."""
        value = max(0.0, min(1.0, value))
        self._tone_var.set(value)
        self._tone_label.configure(text=f"{int(value * 100)}%")

    @property
    def mode(self) -> str:
        """Get waveshaping mode."""
        return self._mode_var.get()

    @mode.setter
    def mode(self, value: str):
        """Set waveshaping mode."""
        if value in self.MODES:
            self._mode_var.set(value)

    @property
    def mix(self) -> float:
        """Get mix."""
        return self._mix_var.get()

    @mix.setter
    def mix(self, value: float):
        """Set mix."""
        value = max(0.0, min(1.0, value))
        self._mix_var.set(value)
        self._mix_label.configure(text=f"{int(value * 100)}%")

    def get_values(self) -> dict:
        """Get all distortion values as dict."""
        return {
            'distortion_enabled': self.enabled,
            'distortion_drive': self.drive,
            'distortion_tone': self.tone,
            'distortion_mode': self.mode,
            'distortion_mix': self.mix,
        }

    def set_values(self, values: dict):
        """Set distortion values from dict."""
        if 'distortion_enabled' in values:
            self.enabled = values['distortion_enabled']
        if 'distortion_drive' in values:
            self.drive = values['distortion_drive']
        if 'distortion_tone' in values:
            self.tone = values['distortion_tone']
        if 'distortion_mode' in values:
            self.mode = values['distortion_mode']
        if 'distortion_mix' in values:
            self.mix = values['distortion_mix']
