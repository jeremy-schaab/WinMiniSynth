# Controls Panel - Oscillator, Filter, Envelope, LFO Controls
"""
controls_panel - GUI control panels for synthesizer parameters.

Provides control panels for:
- OscillatorPanel: Waveform, level, detune controls
- FilterPanel: Cutoff, resonance controls
- EnvelopePanel: ADSR envelope controls
- LFOPanel: LFO rate, depth, routing controls
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional, Any
import math

from .styles import (
    COLORS, FONTS, DIMENSIONS, ColorScheme,
    create_panel_frame, create_slider_with_label
)


class OscillatorPanel(ttk.LabelFrame):
    """Control panel for a single oscillator."""

    WAVEFORMS = ['sine', 'sawtooth', 'square', 'triangle', 'pulse']

    def __init__(
        self,
        parent: tk.Widget,
        osc_num: int,
        on_change: Optional[Callable[[str, Any], None]] = None
    ):
        """
        Initialize oscillator panel.

        Args:
            parent: Parent widget
            osc_num: Oscillator number (1 or 2)
            on_change: Callback for parameter changes (param_name, value)
        """
        super().__init__(
            parent,
            text=f"OSCILLATOR {osc_num}",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_medium']
        )

        self.osc_num = osc_num
        self._on_change = on_change
        self._prefix = f'osc{osc_num}_'

        # Variables
        self.variables: Dict[str, tk.Variable] = {}

        self._create_widgets()

    def _create_widgets(self):
        """Create all oscillator control widgets."""
        # Waveform selector
        wave_frame = ttk.Frame(self, style='Dark.TFrame')
        wave_frame.pack(fill='x', pady=4)

        ttk.Label(
            wave_frame,
            text="Waveform:",
            style='Dark.TLabel'
        ).pack(side='left')

        self.variables['waveform'] = tk.StringVar(value='sawtooth')
        self.waveform_combo = ttk.Combobox(
            wave_frame,
            textvariable=self.variables['waveform'],
            values=self.WAVEFORMS,
            state='readonly',
            width=10,
            style='Dark.TCombobox'
        )
        self.waveform_combo.pack(side='left', padx=(8, 0))
        self.waveform_combo.bind('<<ComboboxSelected>>', self._on_waveform_change)

        # Level slider
        level_frame = ttk.Frame(self, style='Dark.TFrame')
        level_frame.pack(fill='x', pady=4)

        ttk.Label(level_frame, text="Level:", style='Dark.TLabel').pack(side='left')

        default_level = 0.7 if self.osc_num == 1 else 0.5
        self.variables['level'] = tk.DoubleVar(value=default_level)

        self.level_scale = ttk.Scale(
            level_frame,
            from_=0.0,
            to=1.0,
            variable=self.variables['level'],
            orient='horizontal',
            length=120,
            style='Dark.Horizontal.TScale',
            command=self._on_level_change
        )
        self.level_scale.pack(side='left', padx=8, expand=True, fill='x')

        self.level_label = ttk.Label(
            level_frame,
            text=f"{default_level:.2f}",
            style='Value.TLabel',
            width=6
        )
        self.level_label.pack(side='right')

        # Detune slider (for OSC2 primarily, but available for both)
        detune_frame = ttk.Frame(self, style='Dark.TFrame')
        detune_frame.pack(fill='x', pady=4)

        ttk.Label(detune_frame, text="Detune:", style='Dark.TLabel').pack(side='left')

        default_detune = 5.0 if self.osc_num == 2 else 0.0
        self.variables['detune'] = tk.DoubleVar(value=default_detune)

        self.detune_scale = ttk.Scale(
            detune_frame,
            from_=-50.0,
            to=50.0,
            variable=self.variables['detune'],
            orient='horizontal',
            length=120,
            style='Dark.Horizontal.TScale',
            command=self._on_detune_change
        )
        self.detune_scale.pack(side='left', padx=8, expand=True, fill='x')

        self.detune_label = ttk.Label(
            detune_frame,
            text=f"{default_detune:+.0f} ct",
            style='Value.TLabel',
            width=8
        )
        self.detune_label.pack(side='right')

        # Octave selector
        octave_frame = ttk.Frame(self, style='Dark.TFrame')
        octave_frame.pack(fill='x', pady=4)

        ttk.Label(octave_frame, text="Octave:", style='Dark.TLabel').pack(side='left')

        self.variables['octave'] = tk.IntVar(value=0)
        octave_btns = ttk.Frame(octave_frame, style='Dark.TFrame')
        octave_btns.pack(side='left', padx=8)

        for oct in range(-2, 3):
            text = f"{oct:+d}" if oct != 0 else "0"
            rb = ttk.Radiobutton(
                octave_btns,
                text=text,
                variable=self.variables['octave'],
                value=oct,
                style='Dark.TRadiobutton',
                command=lambda o=oct: self._on_octave_change(o)
            )
            rb.pack(side='left', padx=2)

        # Pulse width (shown conditionally)
        self.pw_frame = ttk.Frame(self, style='Dark.TFrame')

        ttk.Label(self.pw_frame, text="Pulse Width:", style='Dark.TLabel').pack(side='left')

        self.variables['pulse_width'] = tk.DoubleVar(value=0.5)

        self.pw_scale = ttk.Scale(
            self.pw_frame,
            from_=0.1,
            to=0.9,
            variable=self.variables['pulse_width'],
            orient='horizontal',
            length=100,
            style='Dark.Horizontal.TScale',
            command=self._on_pw_change
        )
        self.pw_scale.pack(side='left', padx=8, expand=True, fill='x')

        self.pw_label = ttk.Label(
            self.pw_frame,
            text="50%",
            style='Value.TLabel',
            width=6
        )
        self.pw_label.pack(side='right')

        # Show pulse width when pulse waveform selected
        self._update_pw_visibility()

    def _on_waveform_change(self, event=None):
        """Handle waveform selection change."""
        waveform = self.variables['waveform'].get()
        self._update_pw_visibility()
        self._notify_change('waveform', waveform)

    def _on_level_change(self, value):
        """Handle level slider change."""
        level = float(value)
        self.level_label.config(text=f"{level:.2f}")
        self._notify_change('level', level)

    def _on_detune_change(self, value):
        """Handle detune slider change."""
        detune = float(value)
        self.detune_label.config(text=f"{detune:+.0f} ct")
        self._notify_change('detune', detune)

    def _on_octave_change(self, octave):
        """Handle octave change."""
        self._notify_change('octave', octave)

    def _on_pw_change(self, value):
        """Handle pulse width change."""
        pw = float(value)
        self.pw_label.config(text=f"{int(pw * 100)}%")
        self._notify_change('pulse_width', pw)

    def _update_pw_visibility(self):
        """Show/hide pulse width based on waveform."""
        if self.variables['waveform'].get() == 'pulse':
            self.pw_frame.pack(fill='x', pady=4)
        else:
            self.pw_frame.pack_forget()

    def _notify_change(self, param: str, value: Any):
        """Notify callback of parameter change."""
        if self._on_change:
            full_param = f"{self._prefix}{param}"
            self._on_change(full_param, value)

    def get_values(self) -> Dict[str, Any]:
        """Get all current parameter values."""
        return {
            f"{self._prefix}waveform": self.variables['waveform'].get(),
            f"{self._prefix}level": self.variables['level'].get(),
            f"{self._prefix}detune": self.variables['detune'].get(),
            f"{self._prefix}octave": self.variables['octave'].get(),
            f"{self._prefix}pulse_width": self.variables['pulse_width'].get(),
        }

    def set_values(self, values: Dict[str, Any]):
        """Set parameter values from dictionary."""
        for key, value in values.items():
            param = key.replace(self._prefix, '')
            if param in self.variables:
                self.variables[param].set(value)
        self._update_pw_visibility()


class FilterPanel(ttk.LabelFrame):
    """Control panel for the Moog filter."""

    def __init__(
        self,
        parent: tk.Widget,
        on_change: Optional[Callable[[str, Any], None]] = None
    ):
        """
        Initialize filter panel.

        Args:
            parent: Parent widget
            on_change: Callback for parameter changes (param_name, value)
        """
        super().__init__(
            parent,
            text="FILTER",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_medium']
        )

        self._on_change = on_change
        self.variables: Dict[str, tk.Variable] = {}

        self._create_widgets()

    def _create_widgets(self):
        """Create filter control widgets."""
        # Cutoff frequency
        cutoff_frame = ttk.Frame(self, style='Dark.TFrame')
        cutoff_frame.pack(fill='x', pady=4)

        ttk.Label(cutoff_frame, text="Cutoff:", style='Dark.TLabel').pack(side='left')

        self.variables['cutoff'] = tk.DoubleVar(value=2000.0)

        self.cutoff_scale = ttk.Scale(
            cutoff_frame,
            from_=20.0,
            to=20000.0,
            variable=self.variables['cutoff'],
            orient='horizontal',
            length=180,
            style='Dark.Horizontal.TScale',
            command=self._on_cutoff_change
        )
        self.cutoff_scale.pack(side='left', padx=8, expand=True, fill='x')

        self.cutoff_label = ttk.Label(
            cutoff_frame,
            text="2.0 kHz",
            style='Value.TLabel',
            width=10
        )
        self.cutoff_label.pack(side='right')

        # Resonance
        res_frame = ttk.Frame(self, style='Dark.TFrame')
        res_frame.pack(fill='x', pady=4)

        ttk.Label(res_frame, text="Resonance:", style='Dark.TLabel').pack(side='left')

        self.variables['resonance'] = tk.DoubleVar(value=0.3)

        self.res_scale = ttk.Scale(
            res_frame,
            from_=0.0,
            to=1.0,
            variable=self.variables['resonance'],
            orient='horizontal',
            length=180,
            style='Dark.Horizontal.TScale',
            command=self._on_resonance_change
        )
        self.res_scale.pack(side='left', padx=8, expand=True, fill='x')

        self.res_label = ttk.Label(
            res_frame,
            text="0.30",
            style='Value.TLabel',
            width=10
        )
        self.res_label.pack(side='right')

        # Envelope amount
        env_frame = ttk.Frame(self, style='Dark.TFrame')
        env_frame.pack(fill='x', pady=4)

        ttk.Label(env_frame, text="Env Amt:", style='Dark.TLabel').pack(side='left')

        self.variables['env_amount'] = tk.DoubleVar(value=0.5)

        self.env_scale = ttk.Scale(
            env_frame,
            from_=-1.0,
            to=1.0,
            variable=self.variables['env_amount'],
            orient='horizontal',
            length=180,
            style='Dark.Horizontal.TScale',
            command=self._on_env_amount_change
        )
        self.env_scale.pack(side='left', padx=8, expand=True, fill='x')

        self.env_label = ttk.Label(
            env_frame,
            text="0.50",
            style='Value.TLabel',
            width=10
        )
        self.env_label.pack(side='right')

    def _on_cutoff_change(self, value):
        """Handle cutoff slider change."""
        cutoff = float(value)
        if cutoff >= 1000:
            text = f"{cutoff/1000:.1f} kHz"
        else:
            text = f"{int(cutoff)} Hz"
        self.cutoff_label.config(text=text)
        self._notify_change('filter_cutoff', cutoff)

    def _on_resonance_change(self, value):
        """Handle resonance slider change."""
        res = float(value)
        self.res_label.config(text=f"{res:.2f}")
        self._notify_change('filter_resonance', res)

    def _on_env_amount_change(self, value):
        """Handle envelope amount change."""
        amount = float(value)
        self.env_label.config(text=f"{amount:+.2f}")
        self._notify_change('filter_env_amount', amount)

    def _notify_change(self, param: str, value: Any):
        """Notify callback of parameter change."""
        if self._on_change:
            self._on_change(param, value)

    def get_values(self) -> Dict[str, Any]:
        """Get current filter parameter values."""
        return {
            'filter_cutoff': self.variables['cutoff'].get(),
            'filter_resonance': self.variables['resonance'].get(),
            'filter_env_amount': self.variables['env_amount'].get(),
        }

    def set_values(self, values: Dict[str, Any]):
        """Set filter parameter values."""
        if 'filter_cutoff' in values:
            self.variables['cutoff'].set(values['filter_cutoff'])
            self._on_cutoff_change(values['filter_cutoff'])
        if 'filter_resonance' in values:
            self.variables['resonance'].set(values['filter_resonance'])
            self._on_resonance_change(values['filter_resonance'])
        if 'filter_env_amount' in values:
            self.variables['env_amount'].set(values['filter_env_amount'])
            self._on_env_amount_change(values['filter_env_amount'])


class EnvelopePanel(ttk.LabelFrame):
    """Control panel for a single ADSR envelope."""

    def __init__(
        self,
        parent: tk.Widget,
        name: str,
        prefix: str,
        defaults: Optional[Dict[str, float]] = None,
        on_change: Optional[Callable[[str, Any], None]] = None
    ):
        """
        Initialize envelope panel.

        Args:
            parent: Parent widget
            name: Display name (e.g., "AMP", "FILTER")
            prefix: Parameter prefix (e.g., "amp_", "filter_")
            defaults: Default ADSR values
            on_change: Callback for parameter changes
        """
        super().__init__(
            parent,
            text=f"{name} ENVELOPE",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_small']
        )

        self.name = name
        self._prefix = prefix
        self._on_change = on_change

        self.defaults = defaults or {
            'attack': 0.01,
            'decay': 0.1,
            'sustain': 0.7,
            'release': 0.3
        }

        self.variables: Dict[str, tk.Variable] = {}

        self._create_widgets()

    def _create_widgets(self):
        """Create envelope control widgets."""
        # Visualization canvas
        self.canvas = tk.Canvas(
            self,
            width=160,
            height=50,
            bg=ColorScheme.bg_input,
            highlightthickness=1,
            highlightbackground=ColorScheme.border
        )
        self.canvas.pack(pady=(0, 8))

        # ADSR sliders in a row
        sliders_frame = ttk.Frame(self, style='Dark.TFrame')
        sliders_frame.pack(fill='x')

        for param in ['attack', 'decay', 'sustain', 'release']:
            col = ttk.Frame(sliders_frame, style='Dark.TFrame')
            col.pack(side='left', padx=4, expand=True)

            # Parameter label
            label_text = param[0].upper()
            ttk.Label(
                col,
                text=label_text,
                style='Dark.TLabel'
            ).pack()

            # Variable and slider
            default = self.defaults[param]
            self.variables[param] = tk.DoubleVar(value=default)

            # Sustain is 0-1, others are time in seconds
            if param == 'sustain':
                from_val, to_val = 0.0, 1.0
            else:
                from_val, to_val = 0.001, 2.0

            slider = ttk.Scale(
                col,
                from_=to_val,  # Reversed for vertical
                to=from_val,
                variable=self.variables[param],
                orient='vertical',
                length=60,
                style='Dark.Vertical.TScale',
                command=lambda v, p=param: self._on_change_param(p, float(v))
            )
            slider.pack(pady=2)

            # Value label
            if param == 'sustain':
                text = f"{default:.1f}"
            else:
                text = f"{default:.2f}s"

            value_label = ttk.Label(
                col,
                text=text,
                style='Value.TLabel'
            )
            value_label.pack()
            setattr(self, f'{param}_label', value_label)

        self._draw_envelope()

    def _on_change_param(self, param: str, value: float):
        """Handle parameter slider change."""
        # Update label
        label = getattr(self, f'{param}_label')
        if param == 'sustain':
            label.config(text=f"{value:.1f}")
        else:
            label.config(text=f"{value:.2f}s")

        # Redraw envelope visualization
        self._draw_envelope()

        # Notify callback
        self._notify_change(param, value)

    def _draw_envelope(self):
        """Draw envelope shape visualization."""
        self.canvas.delete('curve')

        w, h = 160, 50
        pad = 5

        # Get ADSR values
        a = self.variables['attack'].get()
        d = self.variables['decay'].get()
        s = self.variables['sustain'].get()
        r = self.variables['release'].get()

        # Normalize times for display
        sustain_display = 0.3  # Fixed sustain time for display
        total = a + d + sustain_display + r
        if total == 0:
            total = 1

        x_scale = (w - 2 * pad) / total
        y_scale = h - 2 * pad

        # Calculate points
        points = [
            pad, h - pad,  # Start
            pad + a * x_scale, pad,  # Attack peak
            pad + (a + d) * x_scale, pad + (1 - s) * y_scale,  # Decay to sustain
            pad + (a + d + sustain_display) * x_scale, pad + (1 - s) * y_scale,  # Sustain
            w - pad, h - pad  # Release to zero
        ]

        self.canvas.create_line(
            points,
            fill=ColorScheme.warning,
            width=2,
            tags='curve'
        )

    def _notify_change(self, param: str, value: float):
        """Notify callback of parameter change."""
        if self._on_change:
            full_param = f"{self._prefix}{param}"
            self._on_change(full_param, value)

    def get_values(self) -> Dict[str, Any]:
        """Get current envelope parameter values."""
        return {
            f"{self._prefix}attack": self.variables['attack'].get(),
            f"{self._prefix}decay": self.variables['decay'].get(),
            f"{self._prefix}sustain": self.variables['sustain'].get(),
            f"{self._prefix}release": self.variables['release'].get(),
        }

    def set_values(self, values: Dict[str, Any]):
        """Set envelope parameter values."""
        for param in ['attack', 'decay', 'sustain', 'release']:
            key = f"{self._prefix}{param}"
            if key in values:
                self.variables[param].set(values[key])
                self._on_change_param(param, values[key])


class LFOPanel(ttk.LabelFrame):
    """Control panel for the LFO (Low Frequency Oscillator)."""

    WAVEFORMS = ['sine', 'triangle', 'square', 'sawtooth']

    def __init__(
        self,
        parent: tk.Widget,
        on_change: Optional[Callable[[str, Any], None]] = None
    ):
        """
        Initialize LFO panel.

        Args:
            parent: Parent widget
            on_change: Callback for parameter changes
        """
        super().__init__(
            parent,
            text="LFO",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_medium']
        )

        self._on_change = on_change
        self.variables: Dict[str, tk.Variable] = {}

        self._create_widgets()

    def _create_widgets(self):
        """Create LFO control widgets."""
        # Top row: Waveform, Rate, Depth
        top_frame = ttk.Frame(self, style='Dark.TFrame')
        top_frame.pack(fill='x', pady=4)

        # Waveform selector
        wave_frame = ttk.Frame(top_frame, style='Dark.TFrame')
        wave_frame.pack(side='left', padx=(0, 16))

        ttk.Label(wave_frame, text="Wave:", style='Dark.TLabel').pack(anchor='w')

        self.variables['waveform'] = tk.StringVar(value='sine')
        wave_combo = ttk.Combobox(
            wave_frame,
            textvariable=self.variables['waveform'],
            values=self.WAVEFORMS,
            state='readonly',
            width=8,
            style='Dark.TCombobox'
        )
        wave_combo.pack()
        wave_combo.bind('<<ComboboxSelected>>', self._on_waveform_change)

        # Rate slider
        rate_frame = ttk.Frame(top_frame, style='Dark.TFrame')
        rate_frame.pack(side='left', padx=8, fill='x', expand=True)

        ttk.Label(rate_frame, text="Rate:", style='Dark.TLabel').pack(anchor='w')

        rate_row = ttk.Frame(rate_frame, style='Dark.TFrame')
        rate_row.pack(fill='x')

        self.variables['rate'] = tk.DoubleVar(value=5.0)

        self.rate_scale = ttk.Scale(
            rate_row,
            from_=0.1,
            to=20.0,
            variable=self.variables['rate'],
            orient='horizontal',
            length=100,
            style='Dark.Horizontal.TScale',
            command=self._on_rate_change
        )
        self.rate_scale.pack(side='left', fill='x', expand=True)

        self.rate_label = ttk.Label(
            rate_row,
            text="5.0 Hz",
            style='Value.TLabel',
            width=8
        )
        self.rate_label.pack(side='right')

        # Depth slider
        depth_frame = ttk.Frame(top_frame, style='Dark.TFrame')
        depth_frame.pack(side='left', padx=8, fill='x', expand=True)

        ttk.Label(depth_frame, text="Depth:", style='Dark.TLabel').pack(anchor='w')

        depth_row = ttk.Frame(depth_frame, style='Dark.TFrame')
        depth_row.pack(fill='x')

        self.variables['depth'] = tk.DoubleVar(value=0.5)

        self.depth_scale = ttk.Scale(
            depth_row,
            from_=0.0,
            to=1.0,
            variable=self.variables['depth'],
            orient='horizontal',
            length=100,
            style='Dark.Horizontal.TScale',
            command=self._on_depth_change
        )
        self.depth_scale.pack(side='left', fill='x', expand=True)

        self.depth_label = ttk.Label(
            depth_row,
            text="0.50",
            style='Value.TLabel',
            width=6
        )
        self.depth_label.pack(side='right')

        # Routing checkboxes
        route_frame = ttk.LabelFrame(
            self,
            text="Route To",
            style='Dark.TLabelframe',
            padding=8
        )
        route_frame.pack(fill='x', pady=(8, 0))

        self.variables['to_pitch'] = tk.BooleanVar(value=False)
        self.variables['to_filter'] = tk.BooleanVar(value=False)
        self.variables['to_pw'] = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            route_frame,
            text="Pitch",
            variable=self.variables['to_pitch'],
            style='Dark.TCheckbutton',
            command=lambda: self._on_route_change('to_pitch')
        ).pack(side='left', padx=8)

        ttk.Checkbutton(
            route_frame,
            text="Filter",
            variable=self.variables['to_filter'],
            style='Dark.TCheckbutton',
            command=lambda: self._on_route_change('to_filter')
        ).pack(side='left', padx=8)

        ttk.Checkbutton(
            route_frame,
            text="Pulse Width",
            variable=self.variables['to_pw'],
            style='Dark.TCheckbutton',
            command=lambda: self._on_route_change('to_pw')
        ).pack(side='left', padx=8)

    def _on_waveform_change(self, event=None):
        """Handle waveform selection change."""
        waveform = self.variables['waveform'].get()
        self._notify_change('lfo_waveform', waveform)

    def _on_rate_change(self, value):
        """Handle rate slider change."""
        rate = float(value)
        self.rate_label.config(text=f"{rate:.1f} Hz")
        self._notify_change('lfo_rate', rate)

    def _on_depth_change(self, value):
        """Handle depth slider change."""
        depth = float(value)
        self.depth_label.config(text=f"{depth:.2f}")
        self._notify_change('lfo_depth', depth)

    def _on_route_change(self, route: str):
        """Handle routing checkbox change."""
        value = self.variables[route].get()
        param_map = {
            'to_pitch': 'lfo_to_pitch',
            'to_filter': 'lfo_to_filter',
            'to_pw': 'lfo_to_pw'
        }
        self._notify_change(param_map[route], 1.0 if value else 0.0)

    def _notify_change(self, param: str, value: Any):
        """Notify callback of parameter change."""
        if self._on_change:
            self._on_change(param, value)

    def get_values(self) -> Dict[str, Any]:
        """Get current LFO parameter values."""
        return {
            'lfo_waveform': self.variables['waveform'].get(),
            'lfo_rate': self.variables['rate'].get(),
            'lfo_depth': self.variables['depth'].get(),
            'lfo_to_pitch': 1.0 if self.variables['to_pitch'].get() else 0.0,
            'lfo_to_filter': 1.0 if self.variables['to_filter'].get() else 0.0,
            'lfo_to_pw': 1.0 if self.variables['to_pw'].get() else 0.0,
        }

    def set_values(self, values: Dict[str, Any]):
        """Set LFO parameter values."""
        if 'lfo_waveform' in values:
            self.variables['waveform'].set(values['lfo_waveform'])
        if 'lfo_rate' in values:
            self.variables['rate'].set(values['lfo_rate'])
            self._on_rate_change(values['lfo_rate'])
        if 'lfo_depth' in values:
            self.variables['depth'].set(values['lfo_depth'])
            self._on_depth_change(values['lfo_depth'])
        if 'lfo_to_pitch' in values:
            self.variables['to_pitch'].set(values['lfo_to_pitch'] > 0.5)
        if 'lfo_to_filter' in values:
            self.variables['to_filter'].set(values['lfo_to_filter'] > 0.5)
        if 'lfo_to_pw' in values:
            self.variables['to_pw'].set(values['lfo_to_pw'] > 0.5)


class MasterPanel(ttk.LabelFrame):
    """Master volume control panel."""

    def __init__(
        self,
        parent: tk.Widget,
        on_change: Optional[Callable[[str, Any], None]] = None
    ):
        """
        Initialize master panel.

        Args:
            parent: Parent widget
            on_change: Callback for parameter changes
        """
        super().__init__(
            parent,
            text="MASTER",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_medium']
        )

        self._on_change = on_change
        self.variables: Dict[str, tk.Variable] = {}

        self._create_widgets()

    def _create_widgets(self):
        """Create master volume control widgets."""
        ttk.Label(
            self,
            text="VOLUME",
            style='Dark.TLabel'
        ).pack(side='left')

        self.variables['volume'] = tk.DoubleVar(value=0.7)

        self.volume_scale = ttk.Scale(
            self,
            from_=0.0,
            to=1.0,
            variable=self.variables['volume'],
            orient='horizontal',
            length=150,
            style='Dark.Horizontal.TScale',
            command=self._on_volume_change
        )
        self.volume_scale.pack(side='left', padx=8, expand=True, fill='x')

        self.volume_label = ttk.Label(
            self,
            text="0.70",
            style='Value.TLabel',
            width=6
        )
        self.volume_label.pack(side='right')

    def _on_volume_change(self, value):
        """Handle volume slider change."""
        volume = float(value)
        self.volume_label.config(text=f"{volume:.2f}")
        if self._on_change:
            self._on_change('master_volume', volume)

    def get_values(self) -> Dict[str, Any]:
        """Get current master volume."""
        return {'master_volume': self.variables['volume'].get()}

    def set_values(self, values: Dict[str, Any]):
        """Set master volume."""
        if 'master_volume' in values:
            self.variables['volume'].set(values['master_volume'])
            self._on_volume_change(values['master_volume'])
