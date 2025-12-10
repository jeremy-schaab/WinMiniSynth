# Song Player Panel
"""
song_player_panel - GUI controls for song playback.

Provides:
- Song selector dropdown
- Play/Stop/Pause buttons
- Progress bar
- Current time display

Usage:
    panel = SongPlayerPanel(
        parent,
        on_play=lambda: player.play(),
        on_stop=lambda: player.stop(),
        on_song_select=lambda name: player.load(get_song(name))
    )
    panel.pack()
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional

from .styles import COLORS, FONTS, DIMENSIONS, ColorScheme


class SongPlayerPanel(ttk.LabelFrame):
    """Song player control panel.

    Provides GUI controls for song playback including song selection,
    play/stop/pause controls, and progress display.

    Attributes:
        selected_song: Currently selected song name
        is_playing: Whether currently playing
        progress: Current progress (0.0-1.0)
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_play: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        on_pause: Optional[Callable[[], None]] = None,
        on_song_select: Optional[Callable[[str], None]] = None,
        song_list: Optional[List[str]] = None,
        **kwargs
    ):
        """Initialize song player panel.

        Args:
            parent: Parent widget
            on_play: Callback when play is clicked
            on_stop: Callback when stop is clicked
            on_pause: Callback when pause is clicked
            on_song_select: Callback when song is selected (song_name)
            song_list: Initial list of available song names
        """
        super().__init__(
            parent,
            text="SONG PLAYER",
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_small'],
            **kwargs
        )

        # Callbacks
        self._on_play = on_play
        self._on_stop = on_stop
        self._on_pause = on_pause
        self._on_song_select = on_song_select

        # State
        self._is_playing = False
        self._is_paused = False

        # Variables
        self._song_var = tk.StringVar()
        self._progress_var = tk.DoubleVar(value=0.0)

        # Song list
        self._song_list = song_list or []

        # Create widgets
        self._create_widgets()

    def _create_widgets(self):
        """Create panel widgets."""
        # Main container
        main_frame = ttk.Frame(self, style='Dark.TFrame')
        main_frame.pack(fill='both', expand=True)

        # Top row: Song selector
        selector_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        selector_frame.pack(fill='x', pady=(0, 8))

        ttk.Label(
            selector_frame,
            text="Song",
            style='Dark.TLabel'
        ).pack(side='left', padx=(0, 8))

        self._song_combo = ttk.Combobox(
            selector_frame,
            textvariable=self._song_var,
            values=self._song_list,
            state='readonly',
            width=20,
            style='Dark.TCombobox'
        )
        self._song_combo.pack(side='left', fill='x', expand=True)
        self._song_combo.bind('<<ComboboxSelected>>', self._on_song_selected)

        # Middle row: Control buttons
        controls_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        controls_frame.pack(fill='x', pady=(0, 8))

        # Play button
        self._play_btn = ttk.Button(
            controls_frame,
            text="PLAY",
            style='Accent.TButton',
            width=8,
            command=self._on_play_click
        )
        self._play_btn.pack(side='left', padx=(0, 4))

        # Pause button
        self._pause_btn = ttk.Button(
            controls_frame,
            text="PAUSE",
            style='Dark.TButton',
            width=8,
            command=self._on_pause_click,
            state='disabled'
        )
        self._pause_btn.pack(side='left', padx=(0, 4))

        # Stop button
        self._stop_btn = ttk.Button(
            controls_frame,
            text="STOP",
            style='Dark.TButton',
            width=8,
            command=self._on_stop_click,
            state='disabled'
        )
        self._stop_btn.pack(side='left', padx=(0, 8))

        # Status label
        self._status_label = ttk.Label(
            controls_frame,
            text="Stopped",
            style='Dark.TLabel',
            foreground=ColorScheme.fg_muted
        )
        self._status_label.pack(side='left', padx=(8, 0))

        # Bottom row: Progress bar and time display
        progress_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        progress_frame.pack(fill='x')

        # Time display (current / total)
        self._time_label = ttk.Label(
            progress_frame,
            text="0:00 / 0:00",
            style='Value.TLabel',
            width=12
        )
        self._time_label.pack(side='left', padx=(0, 8))

        # Progress bar
        self._progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self._progress_var,
            maximum=1.0,
            mode='determinate',
            style='Dark.Horizontal.TProgressbar',
            length=200
        )
        self._progress_bar.pack(side='left', fill='x', expand=True)

    def _on_song_selected(self, event=None):
        """Handle song selection change."""
        song_name = self._song_var.get()
        if song_name and self._on_song_select:
            self._on_song_select(song_name)

    def _on_play_click(self):
        """Handle play button click."""
        if self._is_paused:
            # Resume from pause
            self._is_paused = False
            self._is_playing = True
            self._update_button_states()

            if self._on_play:
                self._on_play()
        elif not self._is_playing:
            # Start playback
            self._is_playing = True
            self._update_button_states()

            if self._on_play:
                self._on_play()

    def _on_pause_click(self):
        """Handle pause button click."""
        if self._is_playing and not self._is_paused:
            self._is_paused = True
            self._is_playing = False
            self._update_button_states()

            if self._on_pause:
                self._on_pause()

    def _on_stop_click(self):
        """Handle stop button click."""
        self._is_playing = False
        self._is_paused = False
        self._progress_var.set(0.0)
        self._time_label.configure(text="0:00 / 0:00")
        self._update_button_states()

        if self._on_stop:
            self._on_stop()

    def _update_button_states(self):
        """Update button enabled states based on playback state."""
        if self._is_playing:
            self._play_btn.configure(state='disabled')
            self._pause_btn.configure(state='normal')
            self._stop_btn.configure(state='normal')
            self._status_label.configure(
                text="Playing",
                foreground=ColorScheme.success
            )
        elif self._is_paused:
            self._play_btn.configure(state='normal', text="RESUME")
            self._pause_btn.configure(state='disabled')
            self._stop_btn.configure(state='normal')
            self._status_label.configure(
                text="Paused",
                foreground=ColorScheme.warning
            )
        else:
            self._play_btn.configure(state='normal', text="PLAY")
            self._pause_btn.configure(state='disabled')
            self._stop_btn.configure(state='disabled')
            self._status_label.configure(
                text="Stopped",
                foreground=ColorScheme.fg_muted
            )

    def _format_time(self, seconds: float) -> str:
        """Format seconds as M:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    # Public methods

    def set_song_list(self, songs: List[str]):
        """Update available song list.

        Args:
            songs: List of song names
        """
        self._song_list = songs
        self._song_combo['values'] = songs

        if songs and not self._song_var.get():
            self._song_var.set(songs[0])
            self._on_song_selected()

    def update_progress(self, current: float, total: float):
        """Update progress display.

        Args:
            current: Current position in seconds
            total: Total duration in seconds
        """
        if total > 0:
            progress = min(1.0, current / total)
            self._progress_var.set(progress)

        time_str = f"{self._format_time(current)} / {self._format_time(total)}"
        self._time_label.configure(text=time_str)

    def set_playing(self, is_playing: bool):
        """Set playing state.

        Args:
            is_playing: Whether currently playing
        """
        self._is_playing = is_playing
        if is_playing:
            self._is_paused = False
        self._update_button_states()

    def set_paused(self, is_paused: bool):
        """Set paused state.

        Args:
            is_paused: Whether currently paused
        """
        self._is_paused = is_paused
        if is_paused:
            self._is_playing = False
        self._update_button_states()

    def set_stopped(self):
        """Set stopped state."""
        self._is_playing = False
        self._is_paused = False
        self._progress_var.set(0.0)
        self._time_label.configure(text="0:00 / 0:00")
        self._update_button_states()

    @property
    def selected_song(self) -> str:
        """Get currently selected song name."""
        return self._song_var.get()

    @selected_song.setter
    def selected_song(self, name: str):
        """Set selected song."""
        if name in self._song_list:
            self._song_var.set(name)

    @property
    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._is_playing

    @property
    def is_paused(self) -> bool:
        """Check if currently paused."""
        return self._is_paused

    def get_values(self) -> dict:
        """Get song player values as dict."""
        return {
            'song_selected': self.selected_song,
            'song_is_playing': self.is_playing,
        }

    def set_values(self, values: dict):
        """Set song player values from dict."""
        if 'song_selected' in values:
            self.selected_song = values['song_selected']
