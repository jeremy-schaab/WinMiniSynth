# Main Window - Top-level tkinter window
"""
main_window - Main application window for the Mini Synthesizer.

Provides the top-level window that contains all control panels,
visualization, and keyboard widgets.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Dict, Optional, Any

from .styles import (
    COLORS, FONTS, DIMENSIONS, ColorScheme,
    configure_dark_theme
)
from .controls_panel import (
    OscillatorPanel, FilterPanel, EnvelopePanel,
    LFOPanel, MasterPanel
)
from .keyboard_widget import PianoKeyboard
from .metronome_panel import MetronomePanel
from .recording_panel import RecordingPanel
from .reverb_panel import ReverbPanel
from .song_player_panel import SongPlayerPanel
# BOLT-009: Additional effect panels
from .delay_panel import DelayPanel
from .chorus_panel import ChorusPanel
from .distortion_panel import DistortionPanel
from .flanger_panel import FlangerPanel
from visualization.panel import VisualizationPanel
from visualization.filter_curve import FilterCurve


class StatusBar(ttk.Frame):
    """Application status bar showing system information."""

    def __init__(self, parent: tk.Widget):
        """Initialize status bar."""
        super().__init__(parent, style='Dark.TFrame')

        self._create_widgets()

    def _create_widgets(self):
        """Create status bar widgets."""
        # Status message (left)
        self.status_label = ttk.Label(
            self,
            text="Ready",
            style='Dark.TLabel'
        )
        self.status_label.pack(side='left', padx=8)

        # Separator
        ttk.Separator(self, orient='vertical').pack(side='left', fill='y', padx=4)

        # Voice count
        self.voice_label = ttk.Label(
            self,
            text="Voices: 0/8",
            style='Dark.TLabel'
        )
        self.voice_label.pack(side='left', padx=8)

        # Separator
        ttk.Separator(self, orient='vertical').pack(side='left', fill='y', padx=4)

        # Sample rate
        ttk.Label(
            self,
            text="44100 Hz",
            style='Dark.TLabel'
        ).pack(side='left', padx=8)

        # Buffer size
        ttk.Label(
            self,
            text="Buffer: 512",
            style='Dark.TLabel'
        ).pack(side='left', padx=8)

        # CPU usage (right)
        self.cpu_label = ttk.Label(
            self,
            text="CPU: 0%",
            style='Dark.TLabel'
        )
        self.cpu_label.pack(side='right', padx=8)

    def set_status(self, message: str):
        """Set status message."""
        self.status_label.config(text=message)

    def set_voice_count(self, active: int, max_voices: int = 8):
        """Update voice count display."""
        self.voice_label.config(text=f"Voices: {active}/{max_voices}")

    def set_cpu(self, percent: float):
        """Update CPU usage display."""
        self.cpu_label.config(text=f"CPU: {percent:.0f}%")


class PresetPanel(ttk.LabelFrame):
    """Preset selection and master volume panel (combined)."""

    DEFAULT_PRESETS = [
        'Init', 'Fat Bass', 'Bright Lead', 'Soft Pad', 'Retro Square',
        'Ethereal Strings', 'Plucky Keys', 'Warm Organ', 'Acid Squelch', 'Cosmic Bell'
    ]

    def __init__(
        self,
        parent: tk.Widget,
        on_load: Optional[Callable[[str], None]] = None,
        on_save: Optional[Callable[[], None]] = None,
        on_init: Optional[Callable[[], None]] = None,
        on_volume_change: Optional[Callable[[str, Any], None]] = None
    ):
        """
        Initialize preset panel with master volume.

        Args:
            parent: Parent widget
            on_load: Callback when preset is loaded
            on_save: Callback when save is clicked
            on_init: Callback when init patch is clicked
            on_volume_change: Callback for master volume changes
        """
        super().__init__(
            parent,
            text="PRESET / MASTER",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_small']
        )

        self._on_load = on_load
        self._on_save = on_save
        self._on_init = on_init
        self._on_volume_change = on_volume_change
        self.variables: Dict[str, tk.Variable] = {}

        self._create_widgets()

    def _create_widgets(self):
        """Create preset and master volume widgets in stacked layout."""
        # Row 1: Preset controls
        preset_row = ttk.Frame(self, style='Dark.TFrame')
        preset_row.pack(fill='x', pady=(0, 4))

        self.preset_var = tk.StringVar(value='Init')
        self.preset_combo = ttk.Combobox(
            preset_row,
            textvariable=self.preset_var,
            values=self.DEFAULT_PRESETS,
            state='readonly',
            width=12,
            style='Dark.TCombobox'
        )
        self.preset_combo.pack(side='left', padx=(0, 4))
        self.preset_combo.bind('<<ComboboxSelected>>', self._on_preset_selected)

        ttk.Button(
            preset_row,
            text="Load",
            style='Dark.TButton',
            command=self._load_preset,
            width=5
        ).pack(side='left', padx=2)

        ttk.Button(
            preset_row,
            text="Save",
            style='Accent.TButton',
            command=self._save_preset,
            width=5
        ).pack(side='left', padx=2)

        ttk.Button(
            preset_row,
            text="Init",
            style='Dark.TButton',
            command=self._init_patch,
            width=4
        ).pack(side='left', padx=2)

        # Row 2: Master volume
        volume_row = ttk.Frame(self, style='Dark.TFrame')
        volume_row.pack(fill='x')

        ttk.Label(
            volume_row,
            text="VOL",
            style='Dark.TLabel'
        ).pack(side='left')

        self.variables['volume'] = tk.DoubleVar(value=0.7)
        self.volume_scale = ttk.Scale(
            volume_row,
            from_=0.0,
            to=1.0,
            variable=self.variables['volume'],
            orient='horizontal',
            length=120,
            style='Dark.Horizontal.TScale',
            command=self._on_volume_slider_change
        )
        self.volume_scale.pack(side='left', padx=4, expand=True, fill='x')

        self.volume_label = ttk.Label(
            volume_row,
            text="0.70",
            style='Value.TLabel',
            width=5
        )
        self.volume_label.pack(side='right')

    def _on_preset_selected(self, event=None):
        """Handle preset selection change."""
        self._load_preset()

    def _load_preset(self):
        """Load selected preset."""
        preset_name = self.preset_var.get()
        if self._on_load:
            self._on_load(preset_name)

    def _save_preset(self):
        """Save current preset."""
        if self._on_save:
            self._on_save()

    def _init_patch(self):
        """Initialize patch to defaults."""
        self.preset_var.set('Init')
        if self._on_init:
            self._on_init()

    def _on_volume_slider_change(self, value):
        """Handle volume slider change."""
        volume = float(value)
        self.volume_label.config(text=f"{volume:.2f}")
        if self._on_volume_change:
            self._on_volume_change('master_volume', volume)

    def get_current_preset(self) -> str:
        """Get currently selected preset name."""
        return self.preset_var.get()

    def get_volume(self) -> float:
        """Get current master volume."""
        return self.variables['volume'].get()

    def set_volume(self, value: float):
        """Set master volume."""
        self.variables['volume'].set(value)
        self._on_volume_slider_change(value)

    def set_preset_list(self, presets: list):
        """Update available presets list."""
        self.preset_combo['values'] = presets

    def set_current_preset(self, name: str):
        """Set the current preset name."""
        self.preset_var.set(name)


class MainWindow(tk.Tk):
    """Main application window for the Mini Synthesizer."""

    def __init__(
        self,
        on_note_on: Optional[Callable[[int, int], None]] = None,
        on_note_off: Optional[Callable[[int], None]] = None,
        on_parameter_change: Optional[Callable[[str, Any], None]] = None,
        on_preset_load: Optional[Callable[[str], None]] = None,
        on_preset_save: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None,
        # BOLT-007: Metronome callbacks
        on_metronome_start: Optional[Callable[[], None]] = None,
        on_metronome_stop: Optional[Callable[[], None]] = None,
        on_metronome_bpm_change: Optional[Callable[[float], None]] = None,
        on_metronome_time_sig_change: Optional[Callable[[int, int], None]] = None,
        on_metronome_volume_change: Optional[Callable[[float], None]] = None,
        # BOLT-007: Recording callbacks
        on_record_start: Optional[Callable[[], None]] = None,
        on_record_stop: Optional[Callable[[], None]] = None,
        on_record_pause: Optional[Callable[[], None]] = None,
        on_record_resume: Optional[Callable[[], None]] = None,
        on_record_arm: Optional[Callable[[], None]] = None,
        on_record_export: Optional[Callable[[str], None]] = None,
        on_record_clear: Optional[Callable[[], None]] = None,
        on_record_undo: Optional[Callable[[], None]] = None,
        # BOLT-008: Reverb callbacks
        on_reverb_enable: Optional[Callable[[bool], None]] = None,
        on_reverb_wet_dry: Optional[Callable[[float], None]] = None,
        on_reverb_room_size: Optional[Callable[[float], None]] = None,
        # BOLT-008: Song player callbacks
        on_song_play: Optional[Callable[[], None]] = None,
        on_song_stop: Optional[Callable[[], None]] = None,
        on_song_pause: Optional[Callable[[], None]] = None,
        on_song_select: Optional[Callable[[str], None]] = None,
        # BOLT-009: Delay callbacks
        on_delay_enable: Optional[Callable[[bool], None]] = None,
        on_delay_time: Optional[Callable[[float], None]] = None,
        on_delay_feedback: Optional[Callable[[float], None]] = None,
        on_delay_wet_dry: Optional[Callable[[float], None]] = None,
        # BOLT-009: Chorus callbacks
        on_chorus_enable: Optional[Callable[[bool], None]] = None,
        on_chorus_rate: Optional[Callable[[float], None]] = None,
        on_chorus_depth: Optional[Callable[[float], None]] = None,
        on_chorus_voices: Optional[Callable[[int], None]] = None,
        on_chorus_wet_dry: Optional[Callable[[float], None]] = None,
        # BOLT-009: Distortion callbacks
        on_distortion_enable: Optional[Callable[[bool], None]] = None,
        on_distortion_drive: Optional[Callable[[float], None]] = None,
        on_distortion_tone: Optional[Callable[[float], None]] = None,
        on_distortion_mode: Optional[Callable[[str], None]] = None,
        on_distortion_mix: Optional[Callable[[float], None]] = None,
        # BOLT-010: Flanger callbacks
        on_flanger_enable: Optional[Callable[[bool], None]] = None,
        on_flanger_rate: Optional[Callable[[float], None]] = None,
        on_flanger_depth: Optional[Callable[[float], None]] = None,
        on_flanger_feedback: Optional[Callable[[float], None]] = None,
        on_flanger_wet_dry: Optional[Callable[[float], None]] = None,
        sample_rate: int = 44100
    ):
        """
        Initialize main window.

        Args:
            on_note_on: Callback for note on events (note, velocity)
            on_note_off: Callback for note off events (note)
            on_parameter_change: Callback for parameter changes (name, value)
            on_preset_load: Callback for preset loading (preset_name)
            on_preset_save: Callback for preset saving
            on_quit: Callback when window is closed
            on_metronome_start: Callback when metronome starts
            on_metronome_stop: Callback when metronome stops
            on_metronome_bpm_change: Callback when BPM changes
            on_metronome_time_sig_change: Callback when time signature changes
            on_metronome_volume_change: Callback when metronome volume changes
            on_record_start: Callback when recording starts
            on_record_stop: Callback when recording stops
            on_record_pause: Callback when recording pauses
            on_record_resume: Callback when recording resumes
            on_record_arm: Callback when recording arms
            on_record_export: Callback for export (filepath)
            on_record_clear: Callback to clear recording
            on_record_undo: Callback to undo last take
            sample_rate: Audio sample rate for visualization
        """
        super().__init__()

        # Store callbacks
        self._on_note_on = on_note_on
        self._on_note_off = on_note_off
        self._on_parameter_change = on_parameter_change
        self._on_preset_load = on_preset_load
        self._on_preset_save = on_preset_save
        self._on_quit = on_quit

        # BOLT-007: Metronome callbacks
        self._on_metronome_start = on_metronome_start
        self._on_metronome_stop = on_metronome_stop
        self._on_metronome_bpm_change = on_metronome_bpm_change
        self._on_metronome_time_sig_change = on_metronome_time_sig_change
        self._on_metronome_volume_change = on_metronome_volume_change

        # BOLT-007: Recording callbacks
        self._on_record_start = on_record_start
        self._on_record_stop = on_record_stop
        self._on_record_pause = on_record_pause
        self._on_record_resume = on_record_resume
        self._on_record_arm = on_record_arm
        self._on_record_export = on_record_export
        self._on_record_clear = on_record_clear
        self._on_record_undo = on_record_undo

        # BOLT-008: Reverb callbacks
        self._on_reverb_enable = on_reverb_enable
        self._on_reverb_wet_dry = on_reverb_wet_dry
        self._on_reverb_room_size = on_reverb_room_size

        # BOLT-008: Song player callbacks
        self._on_song_play = on_song_play
        self._on_song_stop = on_song_stop
        self._on_song_pause = on_song_pause
        self._on_song_select = on_song_select

        # BOLT-009: Delay callbacks
        self._on_delay_enable = on_delay_enable
        self._on_delay_time = on_delay_time
        self._on_delay_feedback = on_delay_feedback
        self._on_delay_wet_dry = on_delay_wet_dry

        # BOLT-009: Chorus callbacks
        self._on_chorus_enable = on_chorus_enable
        self._on_chorus_rate = on_chorus_rate
        self._on_chorus_depth = on_chorus_depth
        self._on_chorus_voices = on_chorus_voices
        self._on_chorus_wet_dry = on_chorus_wet_dry

        # BOLT-009: Distortion callbacks
        self._on_distortion_enable = on_distortion_enable
        self._on_distortion_drive = on_distortion_drive
        self._on_distortion_tone = on_distortion_tone
        self._on_distortion_mode = on_distortion_mode
        self._on_distortion_mix = on_distortion_mix
        self._on_flanger_enable = on_flanger_enable
        self._on_flanger_rate = on_flanger_rate
        self._on_flanger_depth = on_flanger_depth
        self._on_flanger_feedback = on_flanger_feedback
        self._on_flanger_wet_dry = on_flanger_wet_dry

        # Sample rate for visualization
        self._sample_rate = sample_rate

        # Configure window
        self.title("KarokeLite Mini Synthesizer")
        self.geometry(f"{DIMENSIONS['window_width']}x{DIMENSIONS['window_height']}")
        self.minsize(DIMENSIONS['min_window_width'], DIMENSIONS['min_window_height'])
        self.configure(bg=ColorScheme.bg_dark)

        # Apply dark theme
        self.style = configure_dark_theme(self)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Create all widgets
        self._create_menu()
        self._create_layout()

        # Bind window-level escape key for panic
        self.bind('<Escape>', lambda e: self._panic())

    def _create_menu(self):
        """Create application menu bar."""
        menubar = tk.Menu(self, bg=ColorScheme.bg_panel, fg=ColorScheme.fg_primary)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=ColorScheme.bg_panel, fg=ColorScheme.fg_primary)
        file_menu.add_command(label="New Project", command=self._new_project)
        file_menu.add_command(label="Open Project...", command=self._open_project)
        file_menu.add_command(label="Save Project", command=self._save_project)
        file_menu.add_separator()
        file_menu.add_command(label="Export WAV...", command=self._export_wav)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        # Preset menu
        preset_menu = tk.Menu(menubar, tearoff=0, bg=ColorScheme.bg_panel, fg=ColorScheme.fg_primary)
        preset_menu.add_command(label="Load Preset...", command=self._load_preset_dialog)
        preset_menu.add_command(label="Save Preset...", command=self._save_preset_dialog)
        preset_menu.add_separator()
        preset_menu.add_command(label="Init Patch", command=self._init_patch)
        menubar.add_cascade(label="Preset", menu=preset_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=ColorScheme.bg_panel, fg=ColorScheme.fg_primary)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _create_layout(self):
        """Create the main layout with all panels.

        BOLT-009 Reorganized Layout:
            Row 1: [OSC1][OSC2][FILTER][AMP ENV][FILTER ENV]
            Row 2: [DISTORTION][CHORUS][DELAY][REVERB]  <- Effects row
            Row 3: [LFO][VISUALIZATION]
            Row 4: [PRESET][MASTER][SONG][METRO][RECORDING]
            Row 5: [KEYBOARD]
            Row 6: [STATUS]
        """
        # Main container
        main_frame = ttk.Frame(self, style='Dark.TFrame')
        main_frame.pack(fill='both', expand=True, padx=8, pady=8)

        # Row 1: Oscillators + Filter + Envelopes
        row1_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        row1_frame.pack(fill='x', pady=(0, 8))

        # Oscillator 1
        self.osc1_panel = OscillatorPanel(
            row1_frame,
            osc_num=1,
            on_change=self._on_param_change
        )
        self.osc1_panel.pack(side='left', fill='y', padx=(0, 8))

        # Oscillator 2
        self.osc2_panel = OscillatorPanel(
            row1_frame,
            osc_num=2,
            on_change=self._on_param_change
        )
        self.osc2_panel.pack(side='left', fill='y', padx=(0, 8))

        # Amp Envelope
        self.amp_env_panel = EnvelopePanel(
            row1_frame,
            name="AMP",
            prefix="amp_",
            defaults={'attack': 0.01, 'decay': 0.1, 'sustain': 0.7, 'release': 0.3},
            on_change=self._on_param_change
        )
        self.amp_env_panel.pack(side='left', fill='y', padx=(0, 8))

        # Filter Envelope
        self.filter_env_panel = EnvelopePanel(
            row1_frame,
            name="FILTER",
            prefix="filter_",
            defaults={'attack': 0.01, 'decay': 0.2, 'sustain': 0.5, 'release': 0.2},
            on_change=self._on_param_change
        )
        self.filter_env_panel.pack(side='left', fill='y', padx=(0, 8))

        # Row 2: Effects chain (Distortion -> Chorus -> Delay -> Reverb)
        row2_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        row2_frame.pack(fill='x', pady=(0, 8))

        # BOLT-009: Distortion Panel
        self.distortion_panel = DistortionPanel(
            row2_frame,
            on_enable_change=self._on_distortion_enable,
            on_drive_change=self._on_distortion_drive,
            on_tone_change=self._on_distortion_tone,
            on_mode_change=self._on_distortion_mode,
            on_mix_change=self._on_distortion_mix
        )
        self.distortion_panel.pack(side='left', fill='y', padx=(0, 8))

        # BOLT-009: Chorus Panel
        self.chorus_panel = ChorusPanel(
            row2_frame,
            on_enable_change=self._on_chorus_enable,
            on_rate_change=self._on_chorus_rate,
            on_depth_change=self._on_chorus_depth,
            on_voices_change=self._on_chorus_voices,
            on_wet_dry_change=self._on_chorus_wet_dry
        )
        self.chorus_panel.pack(side='left', fill='y', padx=(0, 8))

        # BOLT-009: Delay Panel
        self.delay_panel = DelayPanel(
            row2_frame,
            on_enable_change=self._on_delay_enable,
            on_time_change=self._on_delay_time,
            on_feedback_change=self._on_delay_feedback,
            on_wet_dry_change=self._on_delay_wet_dry
        )
        self.delay_panel.pack(side='left', fill='y', padx=(0, 8))

        # BOLT-010: Flanger Panel
        self.flanger_panel = FlangerPanel(
            row2_frame,
            on_enable_change=self._on_flanger_enable,
            on_rate_change=self._on_flanger_rate,
            on_depth_change=self._on_flanger_depth,
            on_feedback_change=self._on_flanger_feedback,
            on_wet_dry_change=self._on_flanger_wet_dry
        )
        self.flanger_panel.pack(side='left', fill='y', padx=(0, 8))

        # BOLT-008: Reverb Panel
        self.reverb_panel = ReverbPanel(
            row2_frame,
            on_enable_change=self._on_reverb_enable,
            on_wet_dry_change=self._on_reverb_wet_dry,
            on_room_size_change=self._on_reverb_room_size
        )
        self.reverb_panel.pack(side='left', fill='y', padx=(0, 8))

        # Row 3: Filter | LFO+FilterResponse | Oscilloscope
        row3_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        row3_frame.pack(fill='x', pady=(0, 8))

        # Filter Panel (moved from Row 1)
        self.filter_panel = FilterPanel(
            row3_frame,
            on_change=self._on_param_change
        )
        self.filter_panel.pack(side='left', fill='y', padx=(0, 8))

        # LFO + Filter Response stacked in a column
        lfo_filter_frame = ttk.Frame(row3_frame, style='Dark.TFrame')
        lfo_filter_frame.pack(side='left', fill='y', padx=(0, 8))

        # LFO (compact)
        self.lfo_panel = LFOPanel(
            lfo_filter_frame,
            on_change=self._on_param_change
        )
        self.lfo_panel.pack(fill='x', pady=(0, 4))

        # Filter Response (stacked below LFO)
        filter_response_frame = ttk.LabelFrame(
            lfo_filter_frame,
            text="FILTER RESPONSE",
            style='Dark.TLabelframe',
            padding=4
        )
        filter_response_frame.pack(fill='both', expand=True)

        self.filter_curve = FilterCurve(
            filter_response_frame,
            height=100,
            sample_rate=self._sample_rate
        )
        self.filter_curve.pack(fill='both', expand=True)

        # BOLT-007: Visualization Panel (waveform only)
        self.visualization_panel = VisualizationPanel(
            row3_frame,
            show_controls=True,
            show_filter=False,
            sample_rate=self._sample_rate
        )
        self.visualization_panel.pack(side='left', fill='both', expand=True)

        # Row 4: Preset + Master + Song + Metronome + Recording
        row4_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        row4_frame.pack(fill='x', pady=(0, 8))

        # Preset panel (combined with Master volume)
        self.preset_panel = PresetPanel(
            row4_frame,
            on_load=self._on_preset_load,
            on_save=self._on_preset_save,
            on_init=self._init_patch,
            on_volume_change=self._on_param_change
        )
        self.preset_panel.pack(side='left', fill='y', padx=(0, 8))

        # BOLT-008: Song Player Panel
        self.song_player_panel = SongPlayerPanel(
            row4_frame,
            on_play=self._on_song_play,
            on_stop=self._on_song_stop,
            on_pause=self._on_song_pause,
            on_song_select=self._on_song_select
        )
        self.song_player_panel.pack(side='left', fill='y', padx=(0, 8))

        # BOLT-007: Metronome Panel
        self.metronome_panel = MetronomePanel(
            row4_frame,
            on_start=self._on_metronome_start,
            on_stop=self._on_metronome_stop,
            on_bpm_change=self._on_metronome_bpm_change,
            on_time_sig_change=self._on_metronome_time_sig_change,
            on_volume_change=self._on_metronome_volume_change
        )
        self.metronome_panel.pack(side='left', fill='y', padx=(0, 8))

        # BOLT-007: Recording Panel
        self.recording_panel = RecordingPanel(
            row4_frame,
            on_record=self._on_record_start,
            on_stop=self._on_record_stop,
            on_pause=self._on_record_pause,
            on_resume=self._on_record_resume,
            on_arm=self._on_record_arm,
            on_export=self._on_record_export,
            on_clear=self._on_record_clear,
            on_undo=self._on_record_undo
        )
        self.recording_panel.pack(side='left', fill='both', expand=True)

        # Row 5: BOLT-004: Virtual Piano Keyboard
        self.keyboard = PianoKeyboard(
            main_frame,
            num_octaves=2,
            start_octave=3,
            on_note_on=self._on_keyboard_note_on,
            on_note_off=self._on_keyboard_note_off,
            show_labels=True,
            show_controls=True,
            velocity_sensitive=True
        )
        self.keyboard.pack(fill='x', pady=(0, 8))

        # Row 6: Status bar
        self.status_bar = StatusBar(main_frame)
        self.status_bar.pack(fill='x', side='bottom')

    # BOLT-004: Keyboard callback methods (delegating to PianoKeyboard widget)

    def _on_keyboard_note_on(self, note: int, velocity: int):
        """Handle note on from PianoKeyboard widget."""
        if self._on_note_on:
            self._on_note_on(note, velocity)

    def _on_keyboard_note_off(self, note: int):
        """Handle note off from PianoKeyboard widget."""
        if self._on_note_off:
            self._on_note_off(note)

    def _panic(self):
        """Release all notes (panic button)."""
        self.status_bar.set_status("All notes off")
        self.keyboard.panic()

    def _on_param_change(self, param: str, value: Any):
        """Handle parameter change from any panel."""
        if self._on_parameter_change:
            self._on_parameter_change(param, value)

    def _on_close(self):
        """Handle window close."""
        if self._on_quit:
            self._on_quit()
        self.destroy()

    # Menu handlers
    def _new_project(self):
        """Create new project."""
        self._init_patch()
        self.status_bar.set_status("New project created")

    def _open_project(self):
        """Open project file."""
        filepath = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            self.status_bar.set_status(f"Opened: {filepath}")

    def _save_project(self):
        """Save project file."""
        filepath = filedialog.asksaveasfilename(
            title="Save Project",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            self.status_bar.set_status(f"Saved: {filepath}")

    def _export_wav(self):
        """Export audio to WAV file."""
        filepath = filedialog.asksaveasfilename(
            title="Export WAV",
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        if filepath:
            self.status_bar.set_status(f"Exported: {filepath}")

    def _load_preset_dialog(self):
        """Show preset load dialog."""
        filepath = filedialog.askopenfilename(
            title="Load Preset",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath and self._on_preset_load:
            self._on_preset_load(filepath)

    def _save_preset_dialog(self):
        """Show preset save dialog."""
        if self._on_preset_save:
            self._on_preset_save()

    def _init_patch(self):
        """Reset to initial patch."""
        # Reset all panels to defaults
        self.osc1_panel.set_values({
            'osc1_waveform': 'sawtooth',
            'osc1_level': 0.7,
            'osc1_detune': 0.0,
            'osc1_octave': 0
        })
        self.osc2_panel.set_values({
            'osc2_waveform': 'sawtooth',
            'osc2_level': 0.5,
            'osc2_detune': 5.0,
            'osc2_octave': 0
        })
        self.filter_panel.set_values({
            'filter_cutoff': 2000.0,
            'filter_resonance': 0.3,
            'filter_env_amount': 0.5
        })
        self.amp_env_panel.set_values({
            'amp_attack': 0.01,
            'amp_decay': 0.1,
            'amp_sustain': 0.7,
            'amp_release': 0.3
        })
        self.filter_env_panel.set_values({
            'filter_attack': 0.01,
            'filter_decay': 0.2,
            'filter_sustain': 0.5,
            'filter_release': 0.2
        })
        self.lfo_panel.set_values({
            'lfo_waveform': 'sine',
            'lfo_rate': 5.0,
            'lfo_depth': 0.5,
            'lfo_to_pitch': 0.0,
            'lfo_to_filter': 0.0,
            'lfo_to_pw': 0.0
        })
        self.preset_panel.set_volume(0.7)

        self.status_bar.set_status("Patch initialized")

    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts = """
Keyboard Shortcuts:

PLAYING NOTES:
  Z X C V B N M , . /  - Lower octave (C3-E4)
  S D F G H J K L ;    - Black keys (lower)
  Q W E R T Y U I O P  - Upper octave (C4-E5)
  2 3 4 5 6 7 8 9 0    - Black keys (upper)

CONTROLS:
  Escape - All notes off (panic)
  Ctrl+S - Save preset
  Ctrl+O - Open preset
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def _show_about(self):
        """Show about dialog."""
        about_text = """
KarokeLite Mini Synthesizer

Version 1.0.0

A virtual analog synthesizer with:
- Dual oscillators with 5 waveforms
- 4-pole Moog-style ladder filter
- Dual ADSR envelopes
- LFO with multiple destinations
- 8-voice polyphony

Built with Python and tkinter.
"""
        messagebox.showinfo("About Mini Synthesizer", about_text)

    # Public methods for external control
    def get_all_parameters(self) -> Dict[str, Any]:
        """Get all current parameter values."""
        params = {}
        params.update(self.osc1_panel.get_values())
        params.update(self.osc2_panel.get_values())
        params.update(self.filter_panel.get_values())
        params.update(self.amp_env_panel.get_values())
        params.update(self.filter_env_panel.get_values())
        params.update(self.lfo_panel.get_values())
        params['master_volume'] = self.preset_panel.get_volume()
        return params

    def set_all_parameters(self, params: Dict[str, Any]):
        """Set all parameter values from dictionary."""
        self.osc1_panel.set_values(params)
        self.osc2_panel.set_values(params)
        self.filter_panel.set_values(params)
        self.amp_env_panel.set_values(params)
        self.filter_env_panel.set_values(params)
        self.lfo_panel.set_values(params)
        if 'master_volume' in params:
            self.preset_panel.set_volume(params['master_volume'])

    def update_voice_count(self, active: int, max_voices: int = 8):
        """Update voice count in status bar."""
        self.status_bar.set_voice_count(active, max_voices)

    def update_cpu(self, percent: float):
        """Update CPU usage in status bar."""
        self.status_bar.set_cpu(percent)

    def set_status(self, message: str):
        """Set status bar message."""
        self.status_bar.set_status(message)

    # BOLT-007: Visualization public methods

    def update_waveform(self, samples):
        """Update oscilloscope with new audio samples.

        Args:
            samples: Audio samples (numpy array)
        """
        self.visualization_panel.update_waveform(samples)

    def update_filter_display(self, cutoff: float, resonance: float):
        """Update filter curve display.

        Args:
            cutoff: Filter cutoff frequency in Hz
            resonance: Filter resonance (0.0-1.0)
        """
        # Update standalone filter curve
        if hasattr(self, 'filter_curve'):
            self.filter_curve.update_response(cutoff, resonance)

    # BOLT-007: Metronome public methods

    def update_metronome_beat(self, beat: int, is_downbeat: bool):
        """Update metronome beat indicator.

        Args:
            beat: Current beat number (0-indexed)
            is_downbeat: Whether this is the first beat of measure
        """
        self.metronome_panel.update_beat(beat, is_downbeat)

    # BOLT-007: Recording public methods

    def update_recording_duration(self, seconds: float):
        """Update recording duration display.

        Args:
            seconds: Duration in seconds
        """
        self.recording_panel.update_duration(seconds)

    def update_recording_level(self, peak: float):
        """Update recording level meter.

        Args:
            peak: Peak level (0.0-1.0)
        """
        self.recording_panel.update_level(peak)

    def update_recording_state(self, state_name: str):
        """Update recording state display.

        Args:
            state_name: State name (IDLE, ARMED, RECORDING, PAUSED)
        """
        self.recording_panel.update_state(state_name)

    def set_recording_has_data(self, has_data: bool):
        """Set whether recording has data available.

        Args:
            has_data: True if recording data exists
        """
        self.recording_panel.set_has_recording(has_data)

    def set_recording_can_undo(self, can_undo: bool):
        """Set whether undo is available.

        Args:
            can_undo: True if undo is available
        """
        self.recording_panel.set_can_undo(can_undo)

    def set_recording_info(self, info_text: str):
        """Set recording info text.

        Args:
            info_text: Info to display (e.g., "2.5 MB, 44100 Hz")
        """
        self.recording_panel.set_info(info_text)

    # BOLT-008: Song player public methods

    def set_song_list(self, songs: list):
        """Set available song list.

        Args:
            songs: List of song names
        """
        self.song_player_panel.set_song_list(songs)

    def update_song_progress(self, current: float, total: float):
        """Update song playback progress.

        Args:
            current: Current position in seconds
            total: Total duration in seconds
        """
        self.song_player_panel.update_progress(current, total)

    def set_song_playing(self, is_playing: bool):
        """Set song playing state.

        Args:
            is_playing: Whether song is playing
        """
        self.song_player_panel.set_playing(is_playing)

    def set_song_paused(self, is_paused: bool):
        """Set song paused state.

        Args:
            is_paused: Whether song is paused
        """
        self.song_player_panel.set_paused(is_paused)

    def set_song_stopped(self):
        """Set song stopped state."""
        self.song_player_panel.set_stopped()

    # BOLT-008: Keyboard external note methods (for song visualization)

    def external_note_on(self, note: int):
        """Highlight keyboard key for song playback.

        Args:
            note: MIDI note number
        """
        self.keyboard.external_note_on(note)

    def external_note_off(self, note: int):
        """Unhighlight keyboard key for song playback.

        Args:
            note: MIDI note number
        """
        self.keyboard.external_note_off(note)

    def clear_external_notes(self):
        """Clear all externally highlighted keys."""
        self.keyboard.clear_external_notes()
