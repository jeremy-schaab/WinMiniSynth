# Audio Engine module for Mini Synthesizer
"""
engine.py - Audio output management with sounddevice

Implements the AudioEngine domain service from the domain model.
Manages the audio stream and callback mechanism for real-time synthesis.

The AudioEngine:
- Wraps sounddevice OutputStream for audio output
- Manages the audio callback thread
- Provides configuration for sample rate, buffer size, channels
- Handles start/stop lifecycle

Audio callback contract:
- MUST return exactly num_samples float values
- MUST complete within buffer duration (< 11.6ms for 512 samples at 44.1kHz)
- MUST NOT allocate memory or block
- SHOULD normalize output to [-1.0, 1.0]

Usage:
    from synth.engine import AudioEngine, AudioConfig

    def my_callback(num_samples: int) -> np.ndarray:
        return np.zeros(num_samples, dtype=np.float32)

    config = AudioConfig(sample_rate=44100, buffer_size=512)
    engine = AudioEngine(config)
    engine.set_callback(my_callback)
    engine.start()

    # ... play audio ...

    engine.stop()
"""

from dataclasses import dataclass
from typing import Callable, Optional
import threading
import numpy as np

# Import sounddevice - may not be available in all environments
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False


# Type alias for audio callback function
AudioCallback = Callable[[int], np.ndarray]


@dataclass
class AudioConfig:
    """Audio configuration settings.

    Attributes:
        sample_rate: Sample rate in Hz (default: 44100)
        buffer_size: Buffer size in samples (default: 512, ~11.6ms latency)
        channels: Number of output channels (default: 1 for mono)
    """
    sample_rate: int = 44100
    buffer_size: int = 512
    channels: int = 1

    @property
    def latency_ms(self) -> float:
        """Calculate audio latency in milliseconds."""
        return self.buffer_size / self.sample_rate * 1000.0

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.sample_rate not in [22050, 44100, 48000, 96000]:
            raise ValueError(f"Unsupported sample rate: {self.sample_rate}")
        if self.buffer_size < 64 or self.buffer_size > 4096:
            raise ValueError(f"Buffer size must be 64-4096: {self.buffer_size}")
        if self.channels not in [1, 2]:
            raise ValueError(f"Channels must be 1 or 2: {self.channels}")


class AudioEngine:
    """Audio output engine using sounddevice.

    Manages the audio stream lifecycle and callback invocation.
    Thread-safe for use with GUI applications.

    Attributes:
        config: Audio configuration settings
        is_running: Whether the audio stream is active
    """

    def __init__(self, config: Optional[AudioConfig] = None):
        """Initialize audio engine with configuration.

        Args:
            config: Audio configuration (default: AudioConfig())
        """
        self.config = config or AudioConfig()

        # Callback function set by user
        self._callback: Optional[AudioCallback] = None

        # Stream object (created on start)
        self._stream: Optional['sd.OutputStream'] = None

        # Running state
        self._running = False
        self._lock = threading.Lock()

        # Pre-allocate output buffer
        self._output_buffer = np.zeros(
            (self.config.buffer_size, self.config.channels),
            dtype=np.float32
        )

        # Error tracking
        self._last_error: Optional[Exception] = None
        self._underrun_count = 0

    @property
    def is_running(self) -> bool:
        """Check if audio engine is currently running."""
        return self._running

    @property
    def underrun_count(self) -> int:
        """Number of buffer underruns detected."""
        return self._underrun_count

    def set_callback(self, callback: AudioCallback) -> None:
        """Set the audio generation callback function.

        The callback will be invoked from the audio thread to generate
        audio samples. It must be real-time safe (no blocking, no allocation).

        Args:
            callback: Function that takes num_samples and returns audio array
        """
        self._callback = callback

    def _audio_callback(self, outdata: np.ndarray, frames: int,
                         time_info: dict, status) -> None:
        """Internal sounddevice callback.

        Called by sounddevice from the audio thread.
        Invokes user callback and copies output to stream buffer.

        Args:
            outdata: Output buffer to fill
            frames: Number of frames to generate
            time_info: Timing information (unused)
            status: Stream status flags
        """
        # Check for underruns
        if status:
            self._underrun_count += 1

        try:
            if self._callback is not None:
                # Generate audio from user callback
                samples = self._callback(frames)

                # Handle mono/stereo conversion
                if self.config.channels == 1:
                    outdata[:, 0] = samples[:frames]
                else:
                    # Duplicate mono to stereo
                    outdata[:, 0] = samples[:frames]
                    outdata[:, 1] = samples[:frames]
            else:
                # No callback - output silence
                outdata.fill(0.0)

        except Exception as e:
            # Log error but don't crash audio thread
            self._last_error = e
            outdata.fill(0.0)

    def start(self) -> None:
        """Start the audio engine.

        Opens the audio stream and begins callback invocation.
        Thread-safe - can be called from any thread.

        Raises:
            RuntimeError: If sounddevice is not available
            Exception: If stream fails to open
        """
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError(
                "sounddevice not available. Install with: pip install sounddevice"
            )

        with self._lock:
            if self._running:
                return  # Already running

            try:
                # Create output stream
                self._stream = sd.OutputStream(
                    samplerate=self.config.sample_rate,
                    blocksize=self.config.buffer_size,
                    channels=self.config.channels,
                    dtype=np.float32,
                    callback=self._audio_callback,
                    latency='low'
                )

                # Start the stream
                self._stream.start()
                self._running = True

            except Exception as e:
                self._last_error = e
                raise

    def stop(self) -> None:
        """Stop the audio engine.

        Stops the audio stream and releases resources.
        Thread-safe - can be called from any thread.
        """
        with self._lock:
            if not self._running:
                return  # Already stopped

            try:
                if self._stream is not None:
                    self._stream.stop()
                    self._stream.close()
                    self._stream = None

            finally:
                self._running = False

    def get_last_error(self) -> Optional[Exception]:
        """Get the last error that occurred in the audio callback.

        Returns:
            Last exception or None if no errors
        """
        return self._last_error

    def clear_error(self) -> None:
        """Clear the last error."""
        self._last_error = None

    def __enter__(self) -> 'AudioEngine':
        """Context manager entry - start engine."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - stop engine."""
        self.stop()

    def __repr__(self) -> str:
        """String representation of engine state."""
        status = "running" if self._running else "stopped"
        return (f"AudioEngine({status}, "
                f"sr={self.config.sample_rate}, "
                f"buf={self.config.buffer_size}, "
                f"ch={self.config.channels})")


class MockAudioEngine(AudioEngine):
    """Mock audio engine for testing without sounddevice.

    Simulates audio callback invocation without actual audio output.
    Useful for unit testing and environments without audio hardware.
    """

    def __init__(self, config: Optional[AudioConfig] = None):
        """Initialize mock engine."""
        # Don't call super().__init__ to avoid sounddevice dependency
        self.config = config or AudioConfig()
        self._callback: Optional[AudioCallback] = None
        self._running = False
        self._lock = threading.Lock()
        self._last_error: Optional[Exception] = None
        self._underrun_count = 0

        # Track generated samples for testing
        self.generated_samples: list = []

    def start(self) -> None:
        """Start mock engine (no-op)."""
        with self._lock:
            self._running = True

    def stop(self) -> None:
        """Stop mock engine (no-op)."""
        with self._lock:
            self._running = False

    def generate_test_buffer(self, num_samples: Optional[int] = None) -> np.ndarray:
        """Manually trigger callback for testing.

        Args:
            num_samples: Number of samples (default: config.buffer_size)

        Returns:
            Generated audio samples
        """
        if num_samples is None:
            num_samples = self.config.buffer_size

        if self._callback is not None:
            samples = self._callback(num_samples)
            self.generated_samples.append(samples.copy())
            return samples
        else:
            return np.zeros(num_samples, dtype=np.float32)
