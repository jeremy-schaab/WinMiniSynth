# Audio Recorder Module
"""
recorder - Real-time audio capture for the Mini Synthesizer.

Provides recording functionality with:
- Ring buffer for efficient capture
- Sample-accurate timing
- Start/stop/pause controls
- Memory-efficient storage
- Undo last take support

Usage:
    recorder = AudioRecorder(sample_rate=44100)
    recorder.start()

    # In audio callback:
    recorder.add_samples(audio_buffer)

    recorder.stop()
    audio = recorder.get_audio()
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List
import numpy as np
import threading
import time


class RecordingState(Enum):
    """Recording state enumeration."""
    IDLE = auto()       # Not recording
    ARMED = auto()      # Armed, waiting for input
    RECORDING = auto()  # Actively recording
    PAUSED = auto()     # Recording paused


@dataclass
class RecordingInfo:
    """Information about a recording.

    Attributes:
        duration_samples: Number of samples recorded
        duration_seconds: Duration in seconds
        peak_level: Peak audio level (0.0-1.0)
        sample_rate: Sample rate of recording
    """
    duration_samples: int
    duration_seconds: float
    peak_level: float
    sample_rate: int


class AudioRecorder:
    """Real-time audio recorder with ring buffer.

    Records audio samples in real-time from the audio callback.
    Uses a growing buffer strategy for unlimited recording duration.

    Attributes:
        state: Current recording state
        sample_rate: Audio sample rate
        duration_samples: Number of samples recorded
        duration_seconds: Recording duration in seconds
    """

    # Default settings
    DEFAULT_SAMPLE_RATE = 44100
    INITIAL_BUFFER_SIZE = 44100 * 60  # 1 minute initial
    BUFFER_GROW_SIZE = 44100 * 30     # 30 second chunks

    # Maximum recording duration (30 minutes)
    MAX_DURATION_SAMPLES = 44100 * 60 * 30

    def __init__(
        self,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        max_duration_seconds: Optional[float] = None
    ):
        """Initialize audio recorder.

        Args:
            sample_rate: Audio sample rate
            max_duration_seconds: Maximum recording duration (None=30 min)
        """
        self._sample_rate = sample_rate
        self._lock = threading.Lock()

        # Calculate max samples
        if max_duration_seconds is not None:
            self._max_samples = int(max_duration_seconds * sample_rate)
        else:
            self._max_samples = self.MAX_DURATION_SAMPLES

        # State
        self._state = RecordingState.IDLE
        self._write_position = 0
        self._peak_level = 0.0

        # Audio buffer (pre-allocated)
        self._buffer = np.zeros(self.INITIAL_BUFFER_SIZE, dtype=np.float32)

        # Undo support - store previous takes
        self._undo_stack: List[np.ndarray] = []
        self._max_undo = 3

        # Timing
        self._start_time: Optional[float] = None

        # Callbacks
        self._on_state_change = None
        self._on_level_update = None

    @property
    def state(self) -> RecordingState:
        """Get current recording state."""
        return self._state

    @property
    def sample_rate(self) -> int:
        """Get sample rate."""
        return self._sample_rate

    @property
    def duration_samples(self) -> int:
        """Get number of samples recorded."""
        return self._write_position

    @property
    def duration_seconds(self) -> float:
        """Get recording duration in seconds."""
        return self._write_position / self._sample_rate

    @property
    def peak_level(self) -> float:
        """Get peak audio level (0.0-1.0)."""
        return self._peak_level

    @property
    def is_recording(self) -> bool:
        """Whether actively recording."""
        return self._state == RecordingState.RECORDING

    @property
    def is_armed(self) -> bool:
        """Whether armed for recording."""
        return self._state == RecordingState.ARMED

    @property
    def can_undo(self) -> bool:
        """Whether undo is available."""
        return len(self._undo_stack) > 0

    def set_on_state_change(self, callback):
        """Set callback for state changes.

        Args:
            callback: Function(new_state) called on state change
        """
        self._on_state_change = callback

    def set_on_level_update(self, callback):
        """Set callback for level updates.

        Args:
            callback: Function(peak_level) called periodically
        """
        self._on_level_update = callback

    def arm(self):
        """Arm recorder for recording.

        Recording will start on first audio input.
        """
        with self._lock:
            if self._state == RecordingState.IDLE:
                self._state = RecordingState.ARMED
                self._notify_state_change()

    def start(self):
        """Start recording immediately."""
        with self._lock:
            if self._state in [RecordingState.IDLE, RecordingState.ARMED]:
                # Save current recording to undo stack if any
                if self._write_position > 0:
                    self._push_undo()

                # Reset for new recording
                self._write_position = 0
                self._peak_level = 0.0
                self._start_time = time.time()
                self._state = RecordingState.RECORDING
                self._notify_state_change()

    def stop(self):
        """Stop recording."""
        with self._lock:
            if self._state in [RecordingState.RECORDING, RecordingState.PAUSED, RecordingState.ARMED]:
                self._state = RecordingState.IDLE
                self._notify_state_change()

    def pause(self):
        """Pause recording."""
        with self._lock:
            if self._state == RecordingState.RECORDING:
                self._state = RecordingState.PAUSED
                self._notify_state_change()

    def resume(self):
        """Resume recording from pause."""
        with self._lock:
            if self._state == RecordingState.PAUSED:
                self._state = RecordingState.RECORDING
                self._notify_state_change()

    def add_samples(self, samples: np.ndarray) -> bool:
        """Add audio samples to recording.

        Call this from audio callback to record samples.

        Args:
            samples: Audio samples to record (mono float32)

        Returns:
            True if samples were recorded, False if not recording or full
        """
        if self._state not in [RecordingState.RECORDING, RecordingState.ARMED]:
            return False

        # Auto-start if armed and input detected
        if self._state == RecordingState.ARMED:
            peak = np.abs(samples).max()
            if peak > 0.01:  # Threshold for auto-start
                with self._lock:
                    self._state = RecordingState.RECORDING
                    self._start_time = time.time()
                    self._notify_state_change()
            else:
                return False

        num_samples = len(samples)

        with self._lock:
            # Check if we have space
            if self._write_position + num_samples > self._max_samples:
                # Recording full
                return False

            # Grow buffer if needed
            if self._write_position + num_samples > len(self._buffer):
                self._grow_buffer()

            # Copy samples
            self._buffer[self._write_position:self._write_position + num_samples] = samples

            # Update peak level
            peak = np.abs(samples).max()
            if peak > self._peak_level:
                self._peak_level = peak

            self._write_position += num_samples

            # Notify level update (occasionally)
            if self._on_level_update and self._write_position % 4410 == 0:
                try:
                    self._on_level_update(self._peak_level)
                except Exception:
                    pass

        return True

    def _grow_buffer(self):
        """Grow the recording buffer."""
        new_size = len(self._buffer) + self.BUFFER_GROW_SIZE
        new_size = min(new_size, self._max_samples)

        new_buffer = np.zeros(new_size, dtype=np.float32)
        new_buffer[:len(self._buffer)] = self._buffer
        self._buffer = new_buffer

    def get_audio(self) -> np.ndarray:
        """Get recorded audio.

        Returns:
            Copy of recorded audio samples
        """
        with self._lock:
            return self._buffer[:self._write_position].copy()

    def get_info(self) -> RecordingInfo:
        """Get recording information.

        Returns:
            RecordingInfo with duration, peak level, etc.
        """
        return RecordingInfo(
            duration_samples=self._write_position,
            duration_seconds=self.duration_seconds,
            peak_level=self._peak_level,
            sample_rate=self._sample_rate
        )

    def clear(self):
        """Clear current recording."""
        with self._lock:
            if self._state == RecordingState.IDLE:
                # Save to undo first
                if self._write_position > 0:
                    self._push_undo()

                self._write_position = 0
                self._peak_level = 0.0

    def undo(self) -> bool:
        """Restore previous recording from undo stack.

        Returns:
            True if undo was performed
        """
        with self._lock:
            if len(self._undo_stack) == 0:
                return False

            # Restore from undo
            previous = self._undo_stack.pop()

            # Ensure buffer is large enough
            if len(previous) > len(self._buffer):
                self._buffer = np.zeros(len(previous), dtype=np.float32)

            self._buffer[:len(previous)] = previous
            self._write_position = len(previous)
            self._peak_level = np.abs(previous).max() if len(previous) > 0 else 0.0

            return True

    def _push_undo(self):
        """Push current recording to undo stack."""
        if self._write_position > 0:
            # Save copy of current recording
            self._undo_stack.append(self._buffer[:self._write_position].copy())

            # Limit undo stack size
            while len(self._undo_stack) > self._max_undo:
                self._undo_stack.pop(0)

    def _notify_state_change(self):
        """Notify callback of state change."""
        if self._on_state_change:
            try:
                self._on_state_change(self._state)
            except Exception:
                pass

    def __repr__(self) -> str:
        return f"AudioRecorder({self._state.name}, {self.duration_seconds:.2f}s)"
