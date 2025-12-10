# Song Player
"""
player - Song playback engine with timer-based scheduling.

Provides SongPlayer class for playing back Song objects with precise
timing using threading.Timer for note scheduling.
"""

import time
import threading
from threading import Timer, Lock
from typing import Callable, Optional, List
from enum import Enum

from .song import Song, SongEvent


class PlayerState(Enum):
    """Song player state enumeration."""
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2


class SongPlayer:
    """Plays back song sequences with callbacks.

    Uses threading.Timer for precise note scheduling. Provides
    callbacks for note on/off events, progress updates, and
    completion notification.

    Attributes:
        is_playing: Whether currently playing
        is_paused: Whether currently paused
        current_position: Current playback position in seconds
        total_duration: Total song duration in seconds
    """

    # Progress callback interval in seconds
    PROGRESS_INTERVAL = 0.1

    def __init__(
        self,
        on_note_on: Optional[Callable[[int, int], None]] = None,
        on_note_off: Optional[Callable[[int], None]] = None,
        on_progress: Optional[Callable[[float, float], None]] = None,
        on_complete: Optional[Callable[[], None]] = None,
        on_preset_change: Optional[Callable[[str], None]] = None
    ):
        """Initialize song player.

        Args:
            on_note_on: Callback for note on (note, velocity)
            on_note_off: Callback for note off (note)
            on_progress: Callback for progress (current, total)
            on_complete: Callback when song completes
            on_preset_change: Callback when preset should change (preset_name)
        """
        self._on_note_on = on_note_on
        self._on_note_off = on_note_off
        self._on_progress = on_progress
        self._on_complete = on_complete
        self._on_preset_change = on_preset_change

        # Current song
        self._song: Optional[Song] = None

        # State
        self._state = PlayerState.STOPPED
        self._start_time: Optional[float] = None
        self._pause_time: Optional[float] = None
        self._pause_offset: float = 0.0

        # Timers
        self._timers: List[Timer] = []
        self._progress_timer: Optional[Timer] = None
        self._lock = Lock()

        # Track active notes for cleanup
        self._active_notes: set = set()

    def load(self, song: Song):
        """Load a song for playback.

        Stops any current playback and loads the new song.

        Args:
            song: Song to load
        """
        self.stop()
        self._song = song

    def play(self):
        """Start or resume playback.

        If paused, resumes from pause position.
        If stopped, starts from beginning.
        """
        if self._song is None:
            return

        with self._lock:
            if self._state == PlayerState.PAUSED:
                # Resume from pause
                self._resume_from_pause()
            elif self._state == PlayerState.STOPPED:
                # Start from beginning
                self._start_playback()

    # Delay before first note to allow preset parameters to be applied by audio thread
    PRESET_SETTLE_DELAY = 0.05  # 50ms for preset parameters to settle

    def _start_playback(self):
        """Start playback from the beginning."""
        self._state = PlayerState.PLAYING
        self._start_time = time.time()
        self._pause_offset = 0.0
        self._active_notes.clear()

        # Notify preset change first
        if self._on_preset_change and self._song:
            self._on_preset_change(self._song.preset)

        # Schedule note events with a small delay to allow preset to settle
        # This prevents first notes from playing before preset is fully applied
        self._schedule_events(offset_delay=self.PRESET_SETTLE_DELAY)

        # Start progress timer
        self._start_progress_timer()

    def _resume_from_pause(self):
        """Resume playback from paused position."""
        if self._pause_time is None:
            return

        # Calculate how long we were paused
        pause_duration = time.time() - self._pause_time
        self._pause_offset += pause_duration
        self._pause_time = None

        self._state = PlayerState.PLAYING

        # Resume progress timer
        self._start_progress_timer()

    def _schedule_events(self, offset_delay: float = 0.0):
        """Schedule all note on/off timers.

        Args:
            offset_delay: Extra delay to add before all events (for preset settle time)
        """
        if self._song is None:
            return

        for event in self._song.events:
            # Calculate delay from now (with optional offset for preset settle time)
            note_on_delay = event.time + offset_delay
            note_off_delay = event.time + event.duration + offset_delay

            # Schedule note on
            timer = Timer(note_on_delay, self._fire_note_on, args=[event])
            timer.daemon = True
            timer.start()
            self._timers.append(timer)

            # Schedule note off
            timer = Timer(note_off_delay, self._fire_note_off, args=[event])
            timer.daemon = True
            timer.start()
            self._timers.append(timer)

        # Schedule completion callback
        if self._song.duration > 0:
            timer = Timer(self._song.duration + offset_delay + 0.1, self._on_playback_complete)
            timer.daemon = True
            timer.start()
            self._timers.append(timer)

    def _fire_note_on(self, event: SongEvent):
        """Fire note on callback."""
        if self._state != PlayerState.PLAYING:
            return

        self._active_notes.add(event.note)

        if self._on_note_on:
            self._on_note_on(event.note, event.velocity)

    def _fire_note_off(self, event: SongEvent):
        """Fire note off callback."""
        if self._state != PlayerState.PLAYING:
            return

        self._active_notes.discard(event.note)

        if self._on_note_off:
            self._on_note_off(event.note)

    def _start_progress_timer(self):
        """Start the progress update timer."""
        def progress_update():
            if self._state == PlayerState.PLAYING:
                if self._on_progress and self._song:
                    pos = self.current_position
                    total = self._song.duration
                    self._on_progress(pos, total)

                # Reschedule
                self._progress_timer = Timer(
                    self.PROGRESS_INTERVAL,
                    progress_update
                )
                self._progress_timer.daemon = True
                self._progress_timer.start()

        self._progress_timer = Timer(self.PROGRESS_INTERVAL, progress_update)
        self._progress_timer.daemon = True
        self._progress_timer.start()

    def _on_playback_complete(self):
        """Handle playback completion."""
        if self._state != PlayerState.PLAYING:
            return

        self._state = PlayerState.STOPPED
        self._cleanup_timers()

        if self._on_complete:
            self._on_complete()

    def stop(self):
        """Stop playback immediately.

        Releases all active notes and cancels all timers.
        """
        with self._lock:
            was_playing = self._state != PlayerState.STOPPED
            self._state = PlayerState.STOPPED
            self._start_time = None
            self._pause_time = None
            self._pause_offset = 0.0

            # Cancel all timers
            self._cleanup_timers()

            # Release all active notes
            if was_playing:
                for note in list(self._active_notes):
                    if self._on_note_off:
                        self._on_note_off(note)
                self._active_notes.clear()

    def pause(self):
        """Pause playback.

        Notes currently playing will be released.
        """
        with self._lock:
            if self._state != PlayerState.PLAYING:
                return

            self._state = PlayerState.PAUSED
            self._pause_time = time.time()

            # Cancel timers (will reschedule on resume)
            self._cleanup_timers()

            # Release active notes
            for note in list(self._active_notes):
                if self._on_note_off:
                    self._on_note_off(note)
            self._active_notes.clear()

    def resume(self):
        """Resume paused playback."""
        if self._state == PlayerState.PAUSED:
            self.play()

    def _cleanup_timers(self):
        """Cancel all pending timers."""
        for timer in self._timers:
            timer.cancel()
        self._timers.clear()

        if self._progress_timer:
            self._progress_timer.cancel()
            self._progress_timer = None

    @property
    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._state == PlayerState.PLAYING

    @property
    def is_paused(self) -> bool:
        """Check if currently paused."""
        return self._state == PlayerState.PAUSED

    @property
    def is_stopped(self) -> bool:
        """Check if stopped."""
        return self._state == PlayerState.STOPPED

    @property
    def state(self) -> PlayerState:
        """Get current player state."""
        return self._state

    @property
    def current_position(self) -> float:
        """Get current playback position in seconds."""
        if self._state == PlayerState.STOPPED:
            return 0.0

        if self._start_time is None:
            return 0.0

        if self._state == PlayerState.PAUSED and self._pause_time:
            # Return position when paused
            return self._pause_time - self._start_time - self._pause_offset

        # Return current position
        return time.time() - self._start_time - self._pause_offset

    @property
    def total_duration(self) -> float:
        """Get total song duration in seconds."""
        if self._song is None:
            return 0.0
        return self._song.duration

    @property
    def progress(self) -> float:
        """Get playback progress as fraction (0.0-1.0)."""
        if self.total_duration == 0:
            return 0.0
        return min(1.0, self.current_position / self.total_duration)

    @property
    def current_song(self) -> Optional[Song]:
        """Get currently loaded song."""
        return self._song

    def __repr__(self) -> str:
        """String representation."""
        song_name = self._song.name if self._song else "None"
        return f"SongPlayer(song='{song_name}', state={self._state.name})"
