# Metronome Module
"""
metronome - Click track generation for the Mini Synthesizer.

Provides a metronome with:
- Configurable BPM (20-300)
- Time signature support (4/4, 3/4, 6/8, etc.)
- Accent on first beat
- High/low click sounds
- Sample-accurate timing

Usage:
    metro = Metronome(bpm=120, time_signature=(4, 4))
    metro.start()

    # In audio callback:
    click_samples = metro.generate(num_samples)
    output = synth_samples + click_samples * metro.volume
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple, Optional
import numpy as np
import math


class ClickSound(Enum):
    """Click sound type."""
    HIGH = auto()  # Accent beat (downbeat)
    LOW = auto()   # Normal beat
    SILENT = auto()  # No click


@dataclass
class TimeSignature:
    """Musical time signature.

    Attributes:
        numerator: Beats per measure (e.g., 4 in 4/4)
        denominator: Note value for one beat (e.g., 4 = quarter note)
    """
    numerator: int = 4
    denominator: int = 4

    def __post_init__(self):
        """Validate time signature."""
        if self.numerator < 1 or self.numerator > 16:
            raise ValueError(f"Numerator must be 1-16: {self.numerator}")
        if self.denominator not in [2, 4, 8, 16]:
            raise ValueError(f"Denominator must be 2, 4, 8, or 16: {self.denominator}")

    @property
    def beats_per_measure(self) -> int:
        """Number of beats in one measure."""
        return self.numerator

    def __str__(self) -> str:
        return f"{self.numerator}/{self.denominator}"


class Metronome:
    """Click track generator with configurable tempo and time signature.

    Generates metronome clicks synchronized to musical time.
    Uses synthesized click sounds (short sine bursts).

    Attributes:
        bpm: Tempo in beats per minute
        time_signature: Musical time signature
        volume: Click volume (0.0-1.0)
        is_running: Whether metronome is active
        current_beat: Current beat in measure (0-indexed)
    """

    # BPM limits
    MIN_BPM = 20
    MAX_BPM = 300
    DEFAULT_BPM = 120

    # Click sound parameters
    CLICK_FREQUENCY_HIGH = 1500.0  # Hz for accent
    CLICK_FREQUENCY_LOW = 1000.0   # Hz for normal beat
    CLICK_DURATION = 0.015         # 15ms click duration
    CLICK_ATTACK = 0.001           # 1ms attack
    CLICK_DECAY = 0.014            # 14ms decay

    def __init__(
        self,
        bpm: float = DEFAULT_BPM,
        time_signature: Optional[TimeSignature] = None,
        sample_rate: int = 44100,
        volume: float = 0.5,
        accent_enabled: bool = True
    ):
        """Initialize metronome.

        Args:
            bpm: Tempo in beats per minute (20-300)
            time_signature: Time signature (default: 4/4)
            sample_rate: Audio sample rate
            volume: Click volume (0.0-1.0)
            accent_enabled: Whether to accent first beat
        """
        self._sample_rate = sample_rate
        self._volume = max(0.0, min(1.0, volume))
        self._accent_enabled = accent_enabled

        # Time signature
        self._time_signature = time_signature or TimeSignature(4, 4)

        # Set BPM (this also calculates samples per beat)
        self._bpm = 0.0
        self.bpm = bpm

        # State
        self._running = False
        self._current_beat = 0
        self._sample_position = 0  # Position within current beat

        # Pre-generate click sounds
        self._click_high = self._generate_click(self.CLICK_FREQUENCY_HIGH)
        self._click_low = self._generate_click(self.CLICK_FREQUENCY_LOW)

        # Callbacks
        self._on_beat_callback = None

    def _generate_click(self, frequency: float) -> np.ndarray:
        """Generate a click sound (short sine burst with envelope).

        Args:
            frequency: Click frequency in Hz

        Returns:
            Click audio samples
        """
        num_samples = int(self.CLICK_DURATION * self._sample_rate)
        t = np.arange(num_samples) / self._sample_rate

        # Generate sine wave
        sine = np.sin(2 * np.pi * frequency * t)

        # Generate envelope (attack-decay)
        attack_samples = int(self.CLICK_ATTACK * self._sample_rate)
        decay_samples = num_samples - attack_samples

        envelope = np.zeros(num_samples)

        # Attack (linear ramp up)
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

        # Decay (exponential decay)
        if decay_samples > 0:
            decay_curve = np.exp(-5 * np.linspace(0, 1, decay_samples))
            envelope[attack_samples:] = decay_curve

        return (sine * envelope).astype(np.float32)

    @property
    def bpm(self) -> float:
        """Get current tempo in BPM."""
        return self._bpm

    @bpm.setter
    def bpm(self, value: float):
        """Set tempo in BPM.

        Args:
            value: Tempo (will be clamped to MIN_BPM-MAX_BPM)
        """
        self._bpm = max(self.MIN_BPM, min(self.MAX_BPM, value))
        self._samples_per_beat = int(60.0 / self._bpm * self._sample_rate)

    @property
    def time_signature(self) -> TimeSignature:
        """Get current time signature."""
        return self._time_signature

    @time_signature.setter
    def time_signature(self, value: TimeSignature):
        """Set time signature."""
        self._time_signature = value
        # Reset to beginning of measure
        self._current_beat = 0
        self._sample_position = 0

    @property
    def volume(self) -> float:
        """Get click volume."""
        return self._volume

    @volume.setter
    def volume(self, value: float):
        """Set click volume (0.0-1.0)."""
        self._volume = max(0.0, min(1.0, value))

    @property
    def accent_enabled(self) -> bool:
        """Whether first beat accent is enabled."""
        return self._accent_enabled

    @accent_enabled.setter
    def accent_enabled(self, value: bool):
        """Enable/disable first beat accent."""
        self._accent_enabled = value

    @property
    def is_running(self) -> bool:
        """Whether metronome is active."""
        return self._running

    @property
    def current_beat(self) -> int:
        """Current beat in measure (0-indexed)."""
        return self._current_beat

    @property
    def current_measure_beat(self) -> int:
        """Current beat in measure (1-indexed for display)."""
        return self._current_beat + 1

    @property
    def samples_per_beat(self) -> int:
        """Number of samples per beat at current BPM."""
        return self._samples_per_beat

    @property
    def beat_duration_ms(self) -> float:
        """Duration of one beat in milliseconds."""
        return 60000.0 / self._bpm

    def set_on_beat_callback(self, callback):
        """Set callback for beat events.

        Args:
            callback: Function(beat_num, is_downbeat) called on each beat
        """
        self._on_beat_callback = callback

    def start(self):
        """Start the metronome."""
        self._running = True

    def stop(self):
        """Stop the metronome."""
        self._running = False

    def reset(self):
        """Reset to beginning of measure."""
        self._current_beat = 0
        self._sample_position = 0

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate metronome audio samples.

        Should be called from audio callback to generate click track.

        Args:
            num_samples: Number of samples to generate

        Returns:
            Audio samples (mono float32)
        """
        output = np.zeros(num_samples, dtype=np.float32)

        if not self._running:
            return output

        write_pos = 0

        while write_pos < num_samples:
            # Check if we're at the start of a beat
            if self._sample_position == 0:
                # Determine click type
                is_downbeat = (self._current_beat == 0)

                if is_downbeat and self._accent_enabled:
                    click = self._click_high
                else:
                    click = self._click_low

                # Copy click samples to output
                click_len = len(click)
                samples_remaining = num_samples - write_pos
                copy_len = min(click_len, samples_remaining)

                output[write_pos:write_pos + copy_len] = click[:copy_len] * self._volume

                # Fire callback
                if self._on_beat_callback:
                    try:
                        self._on_beat_callback(self._current_beat, is_downbeat)
                    except Exception:
                        pass  # Don't crash audio thread

            # Advance position
            samples_to_end_of_beat = self._samples_per_beat - self._sample_position
            samples_remaining = num_samples - write_pos
            advance = min(samples_to_end_of_beat, samples_remaining)

            write_pos += advance
            self._sample_position += advance

            # Check if we've reached end of beat
            if self._sample_position >= self._samples_per_beat:
                self._sample_position = 0
                self._current_beat = (self._current_beat + 1) % self._time_signature.beats_per_measure

        return output

    def tap_tempo(self, tap_time: float) -> Optional[float]:
        """Calculate tempo from tap events.

        Call this method each time user taps. After 2+ taps,
        returns calculated BPM.

        Args:
            tap_time: Time of tap (e.g., time.time())

        Returns:
            Calculated BPM after 2+ taps, or None
        """
        if not hasattr(self, '_tap_times'):
            self._tap_times = []

        # Keep last 8 taps
        self._tap_times.append(tap_time)
        if len(self._tap_times) > 8:
            self._tap_times = self._tap_times[-8:]

        # Need at least 2 taps
        if len(self._tap_times) < 2:
            return None

        # Reset if too long between taps (> 2 seconds)
        if tap_time - self._tap_times[-2] > 2.0:
            self._tap_times = [tap_time]
            return None

        # Calculate average interval
        intervals = []
        for i in range(1, len(self._tap_times)):
            intervals.append(self._tap_times[i] - self._tap_times[i-1])

        avg_interval = sum(intervals) / len(intervals)
        calculated_bpm = 60.0 / avg_interval

        # Clamp to valid range
        return max(self.MIN_BPM, min(self.MAX_BPM, calculated_bpm))

    def __repr__(self) -> str:
        status = "running" if self._running else "stopped"
        return f"Metronome({self._bpm:.1f} BPM, {self._time_signature}, {status})"
