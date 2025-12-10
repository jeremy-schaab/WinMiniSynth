# Recording Panel
"""
recording_panel - GUI controls for audio recording.

Provides:
- Record/Stop/Pause buttons
- Recording time display
- Level meter
- Export controls
- Undo last take

Usage:
    panel = RecordingPanel(
        parent,
        on_record=lambda: recorder.start(),
        on_stop=lambda: recorder.stop(),
        on_export=lambda path: exporter.export_wav(audio, path)
    )
    panel.pack()
"""

import tkinter as tk
from tkinter import ttk, filedialog
from typing import Callable, Optional

from .styles import COLORS, FONTS, DIMENSIONS, ColorScheme


class RecordingPanel(ttk.LabelFrame):
    """Recording control panel.

    Provides GUI controls for audio recording.

    Attributes:
        is_recording: Whether recording is active
        is_paused: Whether recording is paused
        duration: Current recording duration in seconds
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_record: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        on_pause: Optional[Callable[[], None]] = None,
        on_resume: Optional[Callable[[], None]] = None,
        on_arm: Optional[Callable[[], None]] = None,
        on_export: Optional[Callable[[str], None]] = None,
        on_clear: Optional[Callable[[], None]] = None,
        on_undo: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """Initialize recording panel.

        Args:
            parent: Parent widget
            on_record: Callback when record starts
            on_stop: Callback when record stops
            on_pause: Callback when record pauses
            on_resume: Callback when record resumes
            on_arm: Callback when record arms
            on_export: Callback for export (filepath)
            on_clear: Callback to clear recording
            on_undo: Callback to undo last take
        """
        super().__init__(
            parent,
            text="RECORDING",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_small'],
            **kwargs
        )

        # Callbacks
        self._on_record = on_record
        self._on_stop = on_stop
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_arm = on_arm
        self._on_export = on_export
        self._on_clear = on_clear
        self._on_undo = on_undo

        # State
        self._recording = False
        self._paused = False
        self._armed = False
        self._duration = 0.0
        self._peak_level = 0.0
        self._has_recording = False
        self._can_undo = False

        # Create widgets
        self._create_widgets()

    def _create_widgets(self):
        """Create panel widgets."""
        # Main container
        main_frame = ttk.Frame(self, style='Dark.TFrame')
        main_frame.pack(fill='both', expand=True)

        # Top row: Transport controls
        transport_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        transport_frame.pack(fill='x', pady=(0, 8))

        # Record button
        self._record_btn = ttk.Button(
            transport_frame,
            text="REC",
            style='Record.TButton',
            width=5,
            command=self._on_record_click
        )
        self._record_btn.pack(side='left', padx=(0, 4))

        # Arm button
        self._arm_btn = ttk.Button(
            transport_frame,
            text="ARM",
            style='Dark.TButton',
            width=5,
            command=self._on_arm_click
        )
        self._arm_btn.pack(side='left', padx=(0, 4))

        # Pause button
        self._pause_btn = ttk.Button(
            transport_frame,
            text="PAUSE",
            style='Dark.TButton',
            width=6,
            command=self._on_pause_click,
            state='disabled'
        )
        self._pause_btn.pack(side='left', padx=(0, 4))

        # Stop button
        self._stop_btn = ttk.Button(
            transport_frame,
            text="STOP",
            style='Dark.TButton',
            width=5,
            command=self._on_stop_click,
            state='disabled'
        )
        self._stop_btn.pack(side='left', padx=(0, 8))

        # Time display
        self._time_label = ttk.Label(
            transport_frame,
            text="00:00.00",
            style='Value.TLabel',
            font=FONTS['large_value'],
            width=10
        )
        self._time_label.pack(side='left', padx=(8, 0))

        # Status indicator
        self._status_label = ttk.Label(
            transport_frame,
            text="IDLE",
            style='Dark.TLabel',
            width=10
        )
        self._status_label.pack(side='right')

        # Middle row: Level meter
        meter_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        meter_frame.pack(fill='x', pady=(0, 8))

        ttk.Label(
            meter_frame,
            text="Level",
            style='Dark.TLabel'
        ).pack(side='left', padx=(0, 8))

        # Level meter canvas
        self._meter_canvas = tk.Canvas(
            meter_frame,
            width=200,
            height=16,
            bg=ColorScheme.bg_input,
            highlightthickness=1,
            highlightbackground=ColorScheme.border
        )
        self._meter_canvas.pack(side='left', fill='x', expand=True, padx=(0, 8))

        # Draw initial meter
        self._meter_bar = self._meter_canvas.create_rectangle(
            2, 2, 2, 14,
            fill=ColorScheme.success,
            outline=''
        )

        # Peak level label
        self._level_label = ttk.Label(
            meter_frame,
            text="0.0 dB",
            style='Value.TLabel',
            width=8
        )
        self._level_label.pack(side='left')

        # Bottom row: File controls
        file_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        file_frame.pack(fill='x')

        # Export button
        self._export_btn = ttk.Button(
            file_frame,
            text="Export WAV...",
            style='Accent.TButton',
            command=self._on_export_click,
            state='disabled'
        )
        self._export_btn.pack(side='left', padx=(0, 8))

        # Clear button
        self._clear_btn = ttk.Button(
            file_frame,
            text="Clear",
            style='Dark.TButton',
            command=self._on_clear_click,
            state='disabled'
        )
        self._clear_btn.pack(side='left', padx=(0, 8))

        # Undo button
        self._undo_btn = ttk.Button(
            file_frame,
            text="Undo",
            style='Dark.TButton',
            command=self._on_undo_click,
            state='disabled'
        )
        self._undo_btn.pack(side='left')

        # Recording info label
        self._info_label = ttk.Label(
            file_frame,
            text="",
            style='Dark.TLabel'
        )
        self._info_label.pack(side='right')

    def _on_record_click(self):
        """Handle record button click."""
        if not self._recording:
            self._start_recording()
        else:
            self._stop_recording()

    def _on_arm_click(self):
        """Handle arm button click."""
        if not self._armed and not self._recording:
            self._arm_recording()
        elif self._armed:
            self._disarm_recording()

    def _on_pause_click(self):
        """Handle pause button click."""
        if self._recording and not self._paused:
            self._pause_recording()
        elif self._paused:
            self._resume_recording()

    def _on_stop_click(self):
        """Handle stop button click."""
        self._stop_recording()

    def _on_export_click(self):
        """Handle export button click."""
        filepath = filedialog.asksaveasfilename(
            title="Export WAV",
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        if filepath and self._on_export:
            self._on_export(filepath)

    def _on_clear_click(self):
        """Handle clear button click."""
        if self._on_clear:
            self._on_clear()
        self._has_recording = False
        self._duration = 0.0
        self._update_time_display()
        self._update_button_states()

    def _on_undo_click(self):
        """Handle undo button click."""
        if self._on_undo:
            self._on_undo()

    def _start_recording(self):
        """Start recording."""
        self._recording = True
        self._paused = False
        self._armed = False
        self._has_recording = True

        self._record_btn.configure(text="REC", style='Record.TButton')
        self._status_label.configure(text="RECORDING")
        self._update_button_states()

        if self._on_record:
            self._on_record()

    def _stop_recording(self):
        """Stop recording."""
        self._recording = False
        self._paused = False
        self._armed = False

        self._record_btn.configure(text="REC", style='Record.TButton')
        self._status_label.configure(text="STOPPED")
        self._update_button_states()

        if self._on_stop:
            self._on_stop()

    def _pause_recording(self):
        """Pause recording."""
        self._paused = True

        self._pause_btn.configure(text="RESUME")
        self._status_label.configure(text="PAUSED")

        if self._on_pause:
            self._on_pause()

    def _resume_recording(self):
        """Resume recording."""
        self._paused = False

        self._pause_btn.configure(text="PAUSE")
        self._status_label.configure(text="RECORDING")

        if self._on_resume:
            self._on_resume()

    def _arm_recording(self):
        """Arm for recording (auto-start on input)."""
        self._armed = True

        self._arm_btn.configure(style='Record.TButton')
        self._status_label.configure(text="ARMED")

        if self._on_arm:
            self._on_arm()

    def _disarm_recording(self):
        """Disarm recording."""
        self._armed = False

        self._arm_btn.configure(style='Dark.TButton')
        self._status_label.configure(text="IDLE")

    def _update_button_states(self):
        """Update button enabled/disabled states."""
        if self._recording:
            self._record_btn.configure(state='normal')
            self._arm_btn.configure(state='disabled')
            self._pause_btn.configure(state='normal')
            self._stop_btn.configure(state='normal')
            self._export_btn.configure(state='disabled')
            self._clear_btn.configure(state='disabled')
            self._undo_btn.configure(state='disabled')
        else:
            self._record_btn.configure(state='normal')
            self._arm_btn.configure(state='normal')
            self._pause_btn.configure(state='disabled')
            self._stop_btn.configure(state='disabled')

            if self._has_recording:
                self._export_btn.configure(state='normal')
                self._clear_btn.configure(state='normal')
            else:
                self._export_btn.configure(state='disabled')
                self._clear_btn.configure(state='disabled')

            if self._can_undo:
                self._undo_btn.configure(state='normal')
            else:
                self._undo_btn.configure(state='disabled')

    def _update_time_display(self):
        """Update the time display label."""
        minutes = int(self._duration // 60)
        seconds = self._duration % 60
        self._time_label.configure(text=f"{minutes:02d}:{seconds:05.2f}")

    def _update_level_meter(self):
        """Update the level meter display."""
        # Calculate meter width (0-196 pixels)
        meter_width = self._meter_canvas.winfo_width() - 4
        bar_width = int(self._peak_level * meter_width)
        bar_width = max(0, min(meter_width, bar_width))

        # Determine color based on level
        if self._peak_level > 0.9:
            color = ColorScheme.error  # Red for clipping
        elif self._peak_level > 0.7:
            color = ColorScheme.warning  # Yellow for hot
        else:
            color = ColorScheme.success  # Green for normal

        # Update bar
        self._meter_canvas.coords(self._meter_bar, 2, 2, 2 + bar_width, 14)
        self._meter_canvas.itemconfig(self._meter_bar, fill=color)

        # Update dB label
        if self._peak_level > 0:
            import math
            db = 20 * math.log10(max(self._peak_level, 0.0001))
            self._level_label.configure(text=f"{db:.1f} dB")
        else:
            self._level_label.configure(text="-inf dB")

    # Public methods for external updates

    def update_duration(self, seconds: float):
        """Update recording duration.

        Args:
            seconds: Duration in seconds
        """
        self._duration = seconds
        self._update_time_display()

    def update_level(self, peak: float):
        """Update audio level meter.

        Args:
            peak: Peak level (0.0-1.0)
        """
        self._peak_level = peak
        self._update_level_meter()

    def update_state(self, state_name: str):
        """Update recording state from external source.

        Args:
            state_name: State name (IDLE, ARMED, RECORDING, PAUSED)
        """
        state_name = state_name.upper()
        self._status_label.configure(text=state_name)

        if state_name == 'RECORDING':
            self._recording = True
            self._paused = False
            self._armed = False
            self._has_recording = True
            self._record_btn.configure(style='Record.TButton')
        elif state_name == 'PAUSED':
            self._recording = True
            self._paused = True
            self._pause_btn.configure(text="RESUME")
        elif state_name == 'ARMED':
            self._recording = False
            self._armed = True
            self._arm_btn.configure(style='Record.TButton')
        else:  # IDLE
            self._recording = False
            self._paused = False
            self._armed = False
            self._arm_btn.configure(style='Dark.TButton')
            self._pause_btn.configure(text="PAUSE")

        self._update_button_states()

    def set_can_undo(self, can_undo: bool):
        """Set whether undo is available.

        Args:
            can_undo: True if undo is available
        """
        self._can_undo = can_undo
        self._update_button_states()

    def set_has_recording(self, has_recording: bool):
        """Set whether a recording exists.

        Args:
            has_recording: True if recording exists
        """
        self._has_recording = has_recording
        self._update_button_states()

    def set_info(self, info_text: str):
        """Set recording info text.

        Args:
            info_text: Info to display (e.g., "2.5 MB, 44100 Hz")
        """
        self._info_label.configure(text=info_text)

    # Properties

    @property
    def is_recording(self) -> bool:
        """Whether recording is active."""
        return self._recording

    @property
    def is_paused(self) -> bool:
        """Whether recording is paused."""
        return self._paused

    @property
    def is_armed(self) -> bool:
        """Whether recording is armed."""
        return self._armed

    @property
    def duration(self) -> float:
        """Current recording duration in seconds."""
        return self._duration

    def get_values(self) -> dict:
        """Get recording panel state as dict."""
        return {
            'rec_duration': self._duration,
            'rec_peak_level': self._peak_level,
        }
