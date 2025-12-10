# Oscillator module for Mini Synthesizer
"""
oscillator.py - Audio waveform generation with PolyBLEP anti-aliasing

Implements the Oscillator value object from the domain model.
Generates periodic waveforms at audio frequencies using NumPy vectorization
with PolyBLEP (Polynomial Bandlimited Step) anti-aliasing to prevent
high-frequency aliasing artifacts.

Waveform types:
- SINE: Pure tone, no harmonics (fundamental only)
- SAWTOOTH: Rich harmonics, all partials (f, 2f, 3f, ...) - PolyBLEP applied
- SQUARE: Hollow sound, odd harmonics only (f, 3f, 5f, ...) - PolyBLEP applied
- TRIANGLE: Soft sound, weak odd harmonics (naturally bandlimited)
- PULSE: Variable duty cycle square wave - PolyBLEP applied

PolyBLEP reduces aliasing by smoothing discontinuities in the waveform
using a polynomial approximation of the ideal bandlimited step function.

Usage:
    osc = Oscillator(sample_rate=44100)
    osc.set_frequency(440.0)  # A4
    osc.waveform = Waveform.SAWTOOTH
    samples = osc.generate(512)
"""

from enum import IntEnum
from typing import Optional
import numpy as np


class Waveform(IntEnum):
    """Waveform type enumeration."""
    SINE = 0
    SAWTOOTH = 1
    SQUARE = 2
    TRIANGLE = 3
    PULSE = 4


def midi_to_frequency(midi_note: int) -> float:
    """Convert MIDI note number to frequency in Hz.

    Uses A4 = 440 Hz as reference (MIDI note 69).

    Args:
        midi_note: MIDI note number (0-127)

    Returns:
        Frequency in Hz

    Examples:
        >>> midi_to_frequency(69)  # A4
        440.0
        >>> midi_to_frequency(60)  # C4 (middle C)
        261.6255653005986
    """
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def _polyblep(t: float, dt: float) -> float:
    """Compute PolyBLEP correction for a single sample.

    PolyBLEP (Polynomial Bandlimited Step) smooths discontinuities
    by applying a polynomial correction near transition points.

    Args:
        t: Phase value (0.0 to 1.0)
        dt: Phase increment per sample (frequency / sample_rate)

    Returns:
        Correction value to subtract from naive waveform
    """
    # Sample is in the first segment after discontinuity
    if t < dt:
        t_norm = t / dt
        return t_norm + t_norm - t_norm * t_norm - 1.0
    # Sample is in the last segment before discontinuity
    elif t > 1.0 - dt:
        t_norm = (t - 1.0) / dt
        return t_norm * t_norm + t_norm + t_norm + 1.0
    else:
        return 0.0


def _polyblep_vectorized(phases: np.ndarray, dt: float) -> np.ndarray:
    """Compute PolyBLEP correction for array of phases.

    Args:
        phases: Phase values (0.0 to 1.0)
        dt: Phase increment per sample (frequency / sample_rate)

    Returns:
        Correction values to subtract from naive waveform
    """
    correction = np.zeros_like(phases, dtype=np.float64)

    # Handle samples just after discontinuity (0 <= t < dt)
    mask1 = phases < dt
    if np.any(mask1):
        t_norm = phases[mask1] / dt
        correction[mask1] = t_norm + t_norm - t_norm * t_norm - 1.0

    # Handle samples just before discontinuity (1-dt <= t < 1)
    mask2 = phases > 1.0 - dt
    if np.any(mask2):
        t_norm = (phases[mask2] - 1.0) / dt
        correction[mask2] = t_norm * t_norm + t_norm + t_norm + 1.0

    return correction


def _polyblep_at(phases: np.ndarray, dt: float, transition: float) -> np.ndarray:
    """Compute PolyBLEP correction at arbitrary transition point.

    Args:
        phases: Phase values (0.0 to 1.0)
        dt: Phase increment per sample
        transition: Phase position of the discontinuity (0.0 to 1.0)

    Returns:
        Correction values to subtract from naive waveform
    """
    # Shift phase so transition is at 0, handle wrapping correctly
    t_shifted = phases - transition
    # Wrap negative values
    t_shifted = np.where(t_shifted < 0, t_shifted + 1.0, t_shifted)
    # Wrap values >= 1
    t_shifted = np.where(t_shifted >= 1.0, t_shifted - 1.0, t_shifted)
    return _polyblep_vectorized(t_shifted, dt)


class Oscillator:
    """Audio waveform generator.

    Generates periodic waveforms at specified frequencies using phase accumulation.
    Supports pitch modulation for vibrato and portamento effects.

    Attributes:
        sample_rate: Audio sample rate in Hz
        waveform: Current waveform type
        frequency: Base frequency in Hz
        level: Output level (0.0 to 1.0)
        pulse_width: Pulse wave duty cycle (0.05 to 0.95)
        pitch_mod: Pitch modulation in semitones
        pw_mod: Pulse width modulation amount
    """

    def __init__(self, sample_rate: int = 44100):
        """Initialize oscillator with sample rate.

        Args:
            sample_rate: Audio sample rate in Hz (default: 44100)
        """
        self.sample_rate = sample_rate
        self._phase: float = 0.0
        self._frequency: float = 440.0
        self._waveform: Waveform = Waveform.SINE
        self._level: float = 1.0
        self._pulse_width: float = 0.5
        self._pitch_mod: float = 0.0
        self._pw_mod: float = 0.0

        # Pre-allocate work buffer for efficiency
        self._work_buffer: Optional[np.ndarray] = None

    @property
    def frequency(self) -> float:
        """Base frequency in Hz."""
        return self._frequency

    @frequency.setter
    def frequency(self, value: float) -> None:
        """Set base frequency, clamped to valid audio range."""
        self._frequency = max(20.0, min(20000.0, value))

    @property
    def waveform(self) -> Waveform:
        """Current waveform type."""
        return self._waveform

    @waveform.setter
    def waveform(self, value: Waveform) -> None:
        """Set waveform type."""
        self._waveform = value

    @property
    def level(self) -> float:
        """Output level (0.0 to 1.0)."""
        return self._level

    @level.setter
    def level(self, value: float) -> None:
        """Set output level, clamped to 0.0-1.0."""
        self._level = max(0.0, min(1.0, value))

    @property
    def pulse_width(self) -> float:
        """Pulse wave duty cycle (0.05 to 0.95)."""
        return self._pulse_width

    @pulse_width.setter
    def pulse_width(self, value: float) -> None:
        """Set pulse width, clamped to valid range."""
        self._pulse_width = max(0.05, min(0.95, value))

    @property
    def pitch_mod(self) -> float:
        """Pitch modulation in semitones."""
        return self._pitch_mod

    @pitch_mod.setter
    def pitch_mod(self, value: float) -> None:
        """Set pitch modulation amount."""
        self._pitch_mod = value

    @property
    def pw_mod(self) -> float:
        """Pulse width modulation amount."""
        return self._pw_mod

    @pw_mod.setter
    def pw_mod(self, value: float) -> None:
        """Set pulse width modulation, clamped to prevent extremes."""
        self._pw_mod = max(-0.45, min(0.45, value))

    @property
    def effective_frequency(self) -> float:
        """Actual frequency including pitch modulation."""
        return self._frequency * (2.0 ** (self._pitch_mod / 12.0))

    @property
    def effective_pulse_width(self) -> float:
        """Actual pulse width including modulation."""
        pw = self._pulse_width + self._pw_mod
        return max(0.05, min(0.95, pw))

    def set_note(self, midi_note: int) -> None:
        """Set frequency from MIDI note number.

        Args:
            midi_note: MIDI note number (0-127)
        """
        self.frequency = midi_to_frequency(midi_note)

    def reset_phase(self) -> None:
        """Reset oscillator phase to zero.

        Call this when starting a new note to ensure consistent attack.
        """
        self._phase = 0.0

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate audio samples.

        Generates samples using the current waveform type and frequency.
        Uses vectorized NumPy operations for efficiency.
        Applies PolyBLEP anti-aliasing to sawtooth, square, and pulse waves.

        Args:
            num_samples: Number of samples to generate

        Returns:
            NumPy array of float32 samples
        """
        # Ensure work buffer is allocated
        if self._work_buffer is None or len(self._work_buffer) < num_samples:
            self._work_buffer = np.zeros(num_samples, dtype=np.float32)

        output = self._work_buffer[:num_samples]

        # Calculate phase increment per sample
        freq = self.effective_frequency
        phase_inc = freq / self.sample_rate

        # Generate phase array - compute raw phases first, then wrap
        raw_phases = self._phase + np.arange(num_samples) * phase_inc
        phases = raw_phases % 1.0

        # Generate waveform based on type (pass phase_inc for PolyBLEP)
        if self._waveform == Waveform.SINE:
            output[:] = self._generate_sine(phases)
        elif self._waveform == Waveform.SAWTOOTH:
            output[:] = self._generate_sawtooth(phases, phase_inc)
        elif self._waveform == Waveform.SQUARE:
            output[:] = self._generate_square(phases, phase_inc)
        elif self._waveform == Waveform.TRIANGLE:
            output[:] = self._generate_triangle(phases)
        elif self._waveform == Waveform.PULSE:
            output[:] = self._generate_pulse(phases, phase_inc)

        # Update phase for next buffer - use the last raw phase plus one increment
        self._phase = (raw_phases[-1] + phase_inc) % 1.0

        # Apply level
        output *= self._level

        # Return a copy to prevent the caller's data from being
        # overwritten when generate() is called again
        return output.copy()

    def _generate_sine(self, phases: np.ndarray) -> np.ndarray:
        """Generate sine waveform.

        Args:
            phases: Array of phase values (0.0 to 1.0)

        Returns:
            Sine wave samples (-1.0 to 1.0)
        """
        return np.sin(2.0 * np.pi * phases).astype(np.float32)

    def _generate_sawtooth(self, phases: np.ndarray, phase_inc: float) -> np.ndarray:
        """Generate bandlimited sawtooth waveform using PolyBLEP.

        Rises linearly from -1 to +1 over each cycle.
        PolyBLEP correction applied at the discontinuity (phase=0/1).

        Args:
            phases: Array of phase values (0.0 to 1.0)
            phase_inc: Phase increment per sample for PolyBLEP

        Returns:
            Sawtooth wave samples (-1.0 to 1.0)
        """
        # Naive sawtooth: rises from -1 to +1
        output = 2.0 * phases - 1.0

        # Apply PolyBLEP correction at discontinuity (phase wraps from 1 to 0)
        # Sawtooth has a downward step of 2.0 at phase=0
        output -= _polyblep_vectorized(phases, phase_inc) * 2.0

        return output.astype(np.float32)

    def _generate_square(self, phases: np.ndarray, phase_inc: float) -> np.ndarray:
        """Generate bandlimited square waveform using PolyBLEP.

        50% duty cycle square wave.
        PolyBLEP correction applied at both transitions (phase=0 and phase=0.5).

        Args:
            phases: Array of phase values (0.0 to 1.0)
            phase_inc: Phase increment per sample for PolyBLEP

        Returns:
            Square wave samples (-1.0 or 1.0)
        """
        # Naive square wave
        output = np.where(phases < 0.5, 1.0, -1.0).astype(np.float64)

        # Apply PolyBLEP at both discontinuities
        # Transition at phase=0: -1 to +1 (upward step of 2)
        output += _polyblep_vectorized(phases, phase_inc) * 2.0
        # Transition at phase=0.5: +1 to -1 (downward step of 2)
        output -= _polyblep_at(phases, phase_inc, 0.5) * 2.0

        return output.astype(np.float32)

    def _generate_triangle(self, phases: np.ndarray) -> np.ndarray:
        """Generate triangle waveform.

        Rises from -1 to +1, then falls from +1 to -1.

        Args:
            phases: Array of phase values (0.0 to 1.0)

        Returns:
            Triangle wave samples (-1.0 to 1.0)
        """
        # Triangle is absolute value of sawtooth, scaled
        return (4.0 * np.abs(phases - 0.5) - 1.0).astype(np.float32)

    def _generate_pulse(self, phases: np.ndarray, phase_inc: float) -> np.ndarray:
        """Generate bandlimited pulse waveform with variable duty cycle using PolyBLEP.

        PolyBLEP correction applied at both transitions (phase=0 and phase=pw).

        Args:
            phases: Array of phase values (0.0 to 1.0)
            phase_inc: Phase increment per sample for PolyBLEP

        Returns:
            Pulse wave samples (-1.0 or 1.0)
        """
        pw = self.effective_pulse_width

        # Naive pulse wave
        output = np.where(phases < pw, 1.0, -1.0).astype(np.float64)

        # Apply PolyBLEP at both discontinuities
        # Transition at phase=0: -1 to +1 (upward step of 2)
        output += _polyblep_vectorized(phases, phase_inc) * 2.0
        # Transition at phase=pw: +1 to -1 (downward step of 2)
        output -= _polyblep_at(phases, phase_inc, pw) * 2.0

        return output.astype(np.float32)

    def __repr__(self) -> str:
        """String representation of oscillator state."""
        return (f"Oscillator(freq={self._frequency:.1f}Hz, "
                f"waveform={self._waveform.name}, "
                f"level={self._level:.2f})")
