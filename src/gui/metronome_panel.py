# Metronome Panel
"""
metronome_panel - GUI controls for the metronome.

Provides:
- BPM control with slider and spinbox
- Time signature selector
- Tap tempo button
- Volume control
- Visual beat indicator

Usage:
    panel = MetronomePanel(
        parent,
        on_start=lambda: metro.start(),
        on_stop=lambda: metro.stop(),
        on_bpm_change=lambda bpm: metro.bpm = bpm
    )
    panel.pack()
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
import time

from .styles import COLORS, FONTS, DIMENSIONS, ColorScheme


class MetronomePanel(ttk.LabelFrame):
    """Metronome control panel.

    Provides GUI controls for metronome settings.

    Attributes:
        bpm: Current tempo
        time_signature: Current time signature (num, denom)
        volume: Metronome volume (0.0-1.0)
        is_running: Whether metronome is active
    """

    # BPM range
    MIN_BPM = 20
    MAX_BPM = 300
    DEFAULT_BPM = 120

    # Time signature options
    TIME_SIGNATURES = [
        (4, 4), (3, 4), (2, 4), (6, 8), (5, 4), (7, 8)
    ]

    def __init__(
        self,
        parent: tk.Widget,
        on_start: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        on_bpm_change: Optional[Callable[[float], None]] = None,
        on_time_sig_change: Optional[Callable[[int, int], None]] = None,
        on_volume_change: Optional[Callable[[float], None]] = None,
        **kwargs
    ):
        """Initialize metronome panel.

        Args:
            parent: Parent widget
            on_start: Callback when metronome starts
            on_stop: Callback when metronome stops
            on_bpm_change: Callback when BPM changes
            on_time_sig_change: Callback when time signature changes
            on_volume_change: Callback when volume changes
        """
        super().__init__(
            parent,
            text="METRONOME",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_small'],
            **kwargs
        )

        # Callbacks
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_bpm_change = on_bpm_change
        self._on_time_sig_change_callback = on_time_sig_change
        self._on_volume_change = on_volume_change

        # State
        self._running = False
        self._current_beat = 0
        self._beats_per_measure = 4

        # Tap tempo tracking
        self._tap_times = []

        # Variables
        self._bpm_var = tk.DoubleVar(value=self.DEFAULT_BPM)
        self._time_sig_var = tk.StringVar(value="4/4")
        self._volume_var = tk.DoubleVar(value=0.5)

        # Create widgets
        self._create_widgets()

    def _create_widgets(self):
        """Create panel widgets."""
        # Main container
        main_frame = ttk.Frame(self, style='Dark.TFrame')
        main_frame.pack(fill='both', expand=True)

        # Top row: BPM control
        bpm_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        bpm_frame.pack(fill='x', pady=(0, 8))

        ttk.Label(
            bpm_frame,
            text="BPM",
            style='Dark.TLabel'
        ).pack(side='left', padx=(0, 8))

        # BPM spinbox
        self._bpm_spinbox = ttk.Spinbox(
            bpm_frame,
            from_=self.MIN_BPM,
            to=self.MAX_BPM,
            width=5,
            textvariable=self._bpm_var,
            command=self._on_bpm_spinbox_change,
            style='Dark.TSpinbox'
        )
        self._bpm_spinbox.pack(side='left', padx=(0, 8))
        self._bpm_spinbox.bind('<Return>', lambda e: self._on_bpm_spinbox_change())

        # BPM slider
        self._bpm_slider = ttk.Scale(
            bpm_frame,
            from_=self.MIN_BPM,
            to=self.MAX_BPM,
            variable=self._bpm_var,
            orient='horizontal',
            length=150,
            style='Dark.Horizontal.TScale',
            command=self._on_bpm_slider_change
        )
        self._bpm_slider.pack(side='left', fill='x', expand=True, padx=(0, 8))

        # Tap tempo button
        self._tap_btn = ttk.Button(
            bpm_frame,
            text="TAP",
            style='Dark.TButton',
            width=5,
            command=self._on_tap
        )
        self._tap_btn.pack(side='right')

        # Middle row: Time signature and volume
        controls_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        controls_frame.pack(fill='x', pady=(0, 8))

        # Time signature
        ttk.Label(
            controls_frame,
            text="Time",
            style='Dark.TLabel'
        ).pack(side='left', padx=(0, 4))

        self._time_sig_combo = ttk.Combobox(
            controls_frame,
            textvariable=self._time_sig_var,
            values=[f"{n}/{d}" for n, d in self.TIME_SIGNATURES],
            state='readonly',
            width=5,
            style='Dark.TCombobox'
        )
        self._time_sig_combo.pack(side='left', padx=(0, 16))
        self._time_sig_combo.bind('<<ComboboxSelected>>', self._on_time_sig_change)

        # Volume
        ttk.Label(
            controls_frame,
            text="Vol",
            style='Dark.TLabel'
        ).pack(side='left', padx=(0, 4))

        self._volume_slider = ttk.Scale(
            controls_frame,
            from_=0.0,
            to=1.0,
            variable=self._volume_var,
            orient='horizontal',
            length=80,
            style='Dark.Horizontal.TScale',
            command=self._on_volume_slider_change
        )
        self._volume_slider.pack(side='left', padx=(0, 8))

        self._volume_label = ttk.Label(
            controls_frame,
            text="50%",
            style='Value.TLabel',
            width=4
        )
        self._volume_label.pack(side='left')

        # Bottom row: Start/Stop and beat indicator
        bottom_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        bottom_frame.pack(fill='x')

        # Start/Stop button
        self._start_btn = ttk.Button(
            bottom_frame,
            text="START",
            style='Accent.TButton',
            width=8,
            command=self._toggle_metronome
        )
        self._start_btn.pack(side='left', padx=(0, 16))

        # Beat indicator (visual dots)
        self._beat_frame = ttk.Frame(bottom_frame, style='Dark.TFrame')
        self._beat_frame.pack(side='left', fill='x', expand=True)

        self._beat_indicators = []
        self._create_beat_indicators()

    def _create_beat_indicators(self):
        """Create beat indicator dots."""
        # Clear existing
        for widget in self._beat_indicators:
            widget.destroy()
        self._beat_indicators.clear()

        # Create new indicators
        num_beats = self._beats_per_measure
        for i in range(num_beats):
            canvas = tk.Canvas(
                self._beat_frame,
                width=16,
                height=16,
                bg=ColorScheme.bg_panel,
                highlightthickness=0
            )
            canvas.pack(side='left', padx=2)

            # Draw circle
            is_downbeat = (i == 0)
            fill_color = ColorScheme.fg_muted
            canvas.create_oval(
                2, 2, 14, 14,
                fill=fill_color,
                outline=ColorScheme.border,
                tags='dot'
            )
            self._beat_indicators.append(canvas)

    def _toggle_metronome(self):
        """Toggle metronome on/off."""
        if self._running:
            self._stop_metronome()
        else:
            self._start_metronome()

    def _start_metronome(self):
        """Start the metronome."""
        self._running = True
        self._start_btn.configure(text="STOP", style='Record.TButton')

        if self._on_start:
            self._on_start()

    def _stop_metronome(self):
        """Stop the metronome."""
        self._running = False
        self._start_btn.configure(text="START", style='Accent.TButton')

        # Reset beat indicators
        for canvas in self._beat_indicators:
            canvas.itemconfig('dot', fill=ColorScheme.fg_muted)

        if self._on_stop:
            self._on_stop()

    def _on_bpm_spinbox_change(self):
        """Handle BPM spinbox change."""
        try:
            bpm = float(self._bpm_var.get())
            bpm = max(self.MIN_BPM, min(self.MAX_BPM, bpm))
            self._bpm_var.set(bpm)
            if self._on_bpm_change:
                self._on_bpm_change(bpm)
        except ValueError:
            pass

    def _on_bpm_slider_change(self, value):
        """Handle BPM slider change."""
        bpm = float(value)
        if self._on_bpm_change:
            self._on_bpm_change(bpm)

    def _on_time_sig_change(self, event=None):
        """Handle time signature change."""
        sig_str = self._time_sig_var.get()
        try:
            num, denom = map(int, sig_str.split('/'))
            self._beats_per_measure = num
            self._create_beat_indicators()

            if self._on_time_sig_change_callback:
                self._on_time_sig_change_callback(num, denom)
        except ValueError:
            pass

    def _on_volume_slider_change(self, value):
        """Handle volume slider change."""
        vol = float(value)
        self._volume_label.configure(text=f"{int(vol * 100)}%")

        if self._on_volume_change:
            self._on_volume_change(vol)

    def _on_tap(self):
        """Handle tap tempo button."""
        now = time.time()

        # Keep last 8 taps
        self._tap_times.append(now)
        if len(self._tap_times) > 8:
            self._tap_times = self._tap_times[-8:]

        # Need at least 2 taps
        if len(self._tap_times) < 2:
            return

        # Reset if too long between taps
        if now - self._tap_times[-2] > 2.0:
            self._tap_times = [now]
            return

        # Calculate average interval
        intervals = []
        for i in range(1, len(self._tap_times)):
            intervals.append(self._tap_times[i] - self._tap_times[i-1])

        avg_interval = sum(intervals) / len(intervals)
        calculated_bpm = 60.0 / avg_interval
        calculated_bpm = max(self.MIN_BPM, min(self.MAX_BPM, calculated_bpm))

        # Update BPM
        self._bpm_var.set(round(calculated_bpm, 1))
        if self._on_bpm_change:
            self._on_bpm_change(calculated_bpm)

    def update_beat(self, beat: int, is_downbeat: bool):
        """Update beat indicator display.

        Call this from metronome beat callback.

        Args:
            beat: Current beat (0-indexed)
            is_downbeat: Whether this is the first beat
        """
        self._current_beat = beat

        # Update indicators
        for i, canvas in enumerate(self._beat_indicators):
            if i == beat:
                # Active beat
                if is_downbeat:
                    fill = ColorScheme.accent
                else:
                    fill = ColorScheme.success
            else:
                # Inactive beat
                fill = ColorScheme.fg_muted

            canvas.itemconfig('dot', fill=fill)

    # Public properties

    @property
    def bpm(self) -> float:
        """Get current BPM."""
        return self._bpm_var.get()

    @bpm.setter
    def bpm(self, value: float):
        """Set BPM."""
        value = max(self.MIN_BPM, min(self.MAX_BPM, value))
        self._bpm_var.set(value)

    @property
    def time_signature(self) -> tuple:
        """Get current time signature as (numerator, denominator)."""
        sig_str = self._time_sig_var.get()
        try:
            num, denom = map(int, sig_str.split('/'))
            return (num, denom)
        except ValueError:
            return (4, 4)

    @time_signature.setter
    def time_signature(self, value: tuple):
        """Set time signature."""
        num, denom = value
        self._time_sig_var.set(f"{num}/{denom}")
        self._beats_per_measure = num
        self._create_beat_indicators()

    @property
    def volume(self) -> float:
        """Get metronome volume."""
        return self._volume_var.get()

    @volume.setter
    def volume(self, value: float):
        """Set metronome volume."""
        value = max(0.0, min(1.0, value))
        self._volume_var.set(value)
        self._volume_label.configure(text=f"{int(value * 100)}%")

    @property
    def is_running(self) -> bool:
        """Whether metronome is running."""
        return self._running

    def get_values(self) -> dict:
        """Get all metronome values as dict."""
        num, denom = self.time_signature
        return {
            'metro_bpm': self.bpm,
            'metro_time_sig_num': num,
            'metro_time_sig_denom': denom,
            'metro_volume': self.volume,
        }

    def set_values(self, values: dict):
        """Set metronome values from dict."""
        if 'metro_bpm' in values:
            self.bpm = values['metro_bpm']
        if 'metro_time_sig_num' in values and 'metro_time_sig_denom' in values:
            self.time_signature = (
                values['metro_time_sig_num'],
                values['metro_time_sig_denom']
            )
        if 'metro_volume' in values:
            self.volume = values['metro_volume']
