# GUI Module
"""
gui - Graphical user interface components for the Mini Synthesizer.

This module provides the tkinter-based GUI:
- MainWindow: Top-level application window
- OscillatorPanel: Oscillator controls
- FilterPanel: Filter controls
- EnvelopePanel: ADSR envelope controls
- LFOPanel: LFO controls
- MasterPanel: Master volume control
- StatusBar: Application status display
- PresetPanel: Preset management
- PianoKeyboard: Virtual piano keyboard widget

Usage:
    from gui import MainWindow, PianoKeyboard

    def on_note_on(note, velocity):
        synth.note_on(note, velocity)

    window = MainWindow(
        on_note_on=on_note_on,
        on_note_off=lambda n: synth.note_off(n),
        on_parameter_change=lambda p, v: synth.set_parameter(p, v)
    )
    window.mainloop()
"""

# BOLT-003: Main Window & Controls
from .styles import (
    COLORS,
    FONTS,
    DIMENSIONS,
    ColorScheme,
    configure_dark_theme,
    create_panel_frame,
    create_slider_with_label
)

from .controls_panel import (
    OscillatorPanel,
    FilterPanel,
    EnvelopePanel,
    LFOPanel,
    MasterPanel
)

from .main_window import (
    MainWindow,
    StatusBar,
    PresetPanel
)

# BOLT-004: Virtual Keyboard
from .keyboard_widget import (
    PianoKeyboard,
    KeyInfo,
    KeyType
)

# BOLT-005: Metronome & Recording Panels
from .metronome_panel import MetronomePanel
from .recording_panel import RecordingPanel

# BOLT-008: Reverb & Song Player Panels
from .reverb_panel import ReverbPanel
from .song_player_panel import SongPlayerPanel

# BOLT-009: Additional Effect Panels
from .delay_panel import DelayPanel
from .chorus_panel import ChorusPanel
from .distortion_panel import DistortionPanel

# BOLT-006: Visualization Panel (re-export from visualization module)
from visualization.panel import VisualizationPanel
from visualization.oscilloscope import Oscilloscope, TriggerMode, DisplayMode
from visualization.filter_curve import FilterCurve, ScaleMode

__all__ = [
    # Styles
    'COLORS',
    'FONTS',
    'DIMENSIONS',
    'ColorScheme',
    'configure_dark_theme',
    'create_panel_frame',
    'create_slider_with_label',
    # Control panels
    'OscillatorPanel',
    'FilterPanel',
    'EnvelopePanel',
    'LFOPanel',
    'MasterPanel',
    # Main window
    'MainWindow',
    'StatusBar',
    'PresetPanel',
    # Keyboard widget
    'PianoKeyboard',
    'KeyInfo',
    'KeyType',
    # Metronome & Recording panels
    'MetronomePanel',
    'RecordingPanel',
    # Reverb & Song Player panels
    'ReverbPanel',
    'SongPlayerPanel',
    # BOLT-009: Additional Effect Panels
    'DelayPanel',
    'ChorusPanel',
    'DistortionPanel',
    # Visualization components
    'VisualizationPanel',
    'Oscilloscope',
    'TriggerMode',
    'DisplayMode',
    'FilterCurve',
    'ScaleMode',
]
