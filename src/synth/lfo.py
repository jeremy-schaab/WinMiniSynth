# LFO module for Mini Synthesizer
"""
lfo.py - Low-Frequency Oscillator for modulation

Implements the LFO value object from the domain model.
Generates low-frequency periodic signals for modulating synthesis parameters
like pitch (vibrato), filter cutoff, and pulse width.

LFO characteristics:
- Frequency range: 0.1 Hz to 50 Hz
- Multiple waveform types (same as audio oscillator)
- Depth control for modulation amount
- Unipolar or bipolar output options

Usage:
    lfo = LFO(sample_rate=44100)
    lfo.frequency = 5.0      # 5 Hz vibrato
    lfo.depth = 0.3          # 30% modulation depth
    lfo.waveform = Waveform.SINE

    mod_signal = lfo.generate(512)  # Generate modulation signal
    # Apply to oscillator: osc.pitch_mod = mod_signal * semitones
"""

from typing import Optional
import numpy as np

from .oscillator import Waveform


class LFO:
    """Low-Frequency Oscillator for modulation.

    Generates low-frequency periodic signals for modulating various
    synthesis parameters. Similar to audio Oscillator but optimized
    for sub-audio frequency range.

    Attributes:
        sample_rate: Audio sample rate in Hz
        frequency: LFO frequency in Hz (0.1 to 50)
        waveform: Waveform type for modulation shape
        depth: Modulation depth (0.0 to 1.0)
    """

    # Frequency limits for LFO range
    MIN_FREQ = 0.1   # 0.1 Hz (10 second period)
    MAX_FREQ = 50.0  # 50 Hz

    def __init__(self, sample_rate: int = 44100):
        """Initialize LFO with sample rate.

        Args:
            sample_rate: Audio sample rate in Hz (default: 44100)
        """
        self.sample_rate = sample_rate

        # LFO state
        self._phase: float = 0.0
        self._frequency: float = 5.0
        self._waveform: Waveform = Waveform.SINE
        self._depth: float = 0.5

        # Work buffer
        self._work_buffer: Optional[np.ndarray] = None

    @property
    def frequency(self) -> float:
        """LFO frequency in Hz."""
        return self._frequency

    @frequency.setter
    def frequency(self, value: float) -> None:
        """Set LFO frequency, clamped to valid range."""
        self._frequency = max(self.MIN_FREQ, min(self.MAX_FREQ, value))

    @property
    def waveform(self) -> Waveform:
        """LFO waveform type."""
        return self._waveform

    @waveform.setter
    def waveform(self, value: Waveform) -> None:
        """Set LFO waveform type."""
        self._waveform = value

    @property
    def depth(self) -> float:
        """Modulation depth (0.0 to 1.0)."""
        return self._depth

    @depth.setter
    def depth(self, value: float) -> None:
        """Set modulation depth, clamped to 0.0-1.0."""
        self._depth = max(0.0, min(1.0, value))

    @property
    def phase(self) -> float:
        """Current LFO phase (0.0 to 1.0)."""
        return self._phase

    def reset_phase(self) -> None:
        """Reset LFO phase to zero.

        Use to synchronize LFO with note events if desired.
        """
        self._phase = 0.0

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate modulation signal.

        Generates LFO output scaled by depth parameter.
        Output range is -depth to +depth (bipolar).

        Args:
            num_samples: Number of samples to generate

        Returns:
            NumPy array of float32 modulation values
        """
        # Ensure work buffer is allocated
        if self._work_buffer is None or len(self._work_buffer) < num_samples:
            self._work_buffer = np.zeros(num_samples, dtype=np.float32)

        output = self._work_buffer[:num_samples]

        # Calculate phase increment per sample
        phase_inc = self._frequency / self.sample_rate

        # Generate phase array
        phases = (self._phase + np.arange(num_samples) * phase_inc) % 1.0

        # Generate waveform
        if self._waveform == Waveform.SINE:
            output[:] = np.sin(2.0 * np.pi * phases)
        elif self._waveform == Waveform.SAWTOOTH:
            output[:] = 2.0 * phases - 1.0
        elif self._waveform == Waveform.SQUARE:
            output[:] = np.where(phases < 0.5, 1.0, -1.0)
        elif self._waveform == Waveform.TRIANGLE:
            output[:] = 4.0 * np.abs(phases - 0.5) - 1.0
        elif self._waveform == Waveform.PULSE:
            # For LFO, pulse with 25% duty cycle (more interesting modulation)
            output[:] = np.where(phases < 0.25, 1.0, -1.0)

        # Update phase for next buffer
        self._phase = (self._phase + num_samples * phase_inc) % 1.0

        # Apply depth scaling
        output *= self._depth

        return output.astype(np.float32)

    def generate_unipolar(self, num_samples: int) -> np.ndarray:
        """Generate unipolar modulation signal.

        Output range is 0.0 to depth (always positive).
        Useful for filter cutoff modulation.

        Args:
            num_samples: Number of samples to generate

        Returns:
            NumPy array of float32 modulation values (0.0 to depth)
        """
        bipolar = self.generate(num_samples)
        return (bipolar + self._depth) * 0.5

    def generate_sample(self) -> float:
        """Generate a single modulation sample.

        Useful for per-sample modulation in tight loops.

        Returns:
            Single modulation value
        """
        # Calculate current value
        if self._waveform == Waveform.SINE:
            value = np.sin(2.0 * np.pi * self._phase)
        elif self._waveform == Waveform.SAWTOOTH:
            value = 2.0 * self._phase - 1.0
        elif self._waveform == Waveform.SQUARE:
            value = 1.0 if self._phase < 0.5 else -1.0
        elif self._waveform == Waveform.TRIANGLE:
            value = 4.0 * abs(self._phase - 0.5) - 1.0
        else:  # PULSE
            value = 1.0 if self._phase < 0.25 else -1.0

        # Advance phase
        self._phase = (self._phase + self._frequency / self.sample_rate) % 1.0

        return value * self._depth

    def __repr__(self) -> str:
        """String representation of LFO state."""
        return (f"LFO(freq={self._frequency:.2f}Hz, "
                f"waveform={self._waveform.name}, "
                f"depth={self._depth:.2f})")
