# Flanger Effect
"""
flanger - Flanger effect for the Mini Synthesizer.

Implements a flanger effect with:
- Short LFO-modulated delay line (1-10ms)
- Feedback for resonant sweeps
- Adjustable rate, depth, feedback, and wet/dry mix

Flanger differs from chorus by using shorter delays and feedback,
creating the characteristic "jet plane" sweep sound.
"""

import numpy as np
from typing import Optional
import math


class Flanger:
    """Flanger effect using LFO-modulated delay with feedback.

    Creates the characteristic sweeping/jet sound by mixing a short,
    modulated delay with feedback back into the input.

    Attributes:
        rate: LFO rate in Hz (0.1-5.0)
        depth: Modulation depth (0.0-1.0)
        feedback: Feedback amount (0.0-0.95)
        wet_dry: Wet/dry mix (0.0 = dry, 1.0 = wet)
        enabled: Whether flanger is active
    """

    # Parameter limits
    MIN_RATE = 0.1
    MAX_RATE = 5.0
    MIN_FEEDBACK = 0.0
    MAX_FEEDBACK = 0.95  # Keep below 1.0 to prevent runaway

    # Delay parameters (in ms)
    MIN_DELAY_MS = 1.0   # Minimum delay time
    MAX_DELAY_MS = 10.0  # Maximum delay time (at full depth)

    # Defaults
    DEFAULT_RATE = 0.3
    DEFAULT_DEPTH = 0.7
    DEFAULT_FEEDBACK = 0.5
    DEFAULT_WET_DRY = 0.5

    def __init__(
        self,
        sample_rate: int = 44100,
        rate: float = DEFAULT_RATE,
        depth: float = DEFAULT_DEPTH,
        feedback: float = DEFAULT_FEEDBACK,
        wet_dry: float = DEFAULT_WET_DRY
    ):
        """Initialize flanger effect.

        Args:
            sample_rate: Audio sample rate in Hz
            rate: LFO rate in Hz (0.1-5.0)
            depth: Modulation depth (0.0-1.0)
            feedback: Feedback amount (0.0-0.95)
            wet_dry: Wet/dry mix (0.0-1.0)
        """
        self._sample_rate = sample_rate
        self._enabled = False

        # Clamp and set parameters
        self._rate = max(self.MIN_RATE, min(self.MAX_RATE, rate))
        self._depth = max(0.0, min(1.0, depth))
        self._feedback = max(self.MIN_FEEDBACK, min(self.MAX_FEEDBACK, feedback))
        self._wet_dry = max(0.0, min(1.0, wet_dry))

        # Calculate buffer size for maximum delay
        max_delay_samples = int((self.MAX_DELAY_MS / 1000.0) * sample_rate) + 10
        self._buffer = np.zeros(max_delay_samples, dtype=np.float32)
        self._buffer_size = max_delay_samples
        self._write_pos = 0

        # LFO state
        self._lfo_phase = 0.0

        # Feedback sample (previous output)
        self._feedback_sample = 0.0

    def _get_delay_range(self) -> tuple:
        """Get min and max delay in samples based on depth."""
        min_samples = (self.MIN_DELAY_MS / 1000.0) * self._sample_rate
        max_samples = (self.MAX_DELAY_MS / 1000.0) * self._sample_rate * self._depth
        return min_samples, max_samples

    def _interpolate(self, delay: float) -> float:
        """Linear interpolation for fractional delay.

        Args:
            delay: Fractional delay in samples

        Returns:
            Interpolated sample value
        """
        delay = max(0.0, min(delay, self._buffer_size - 2))

        read_pos = self._write_pos - delay
        if read_pos < 0:
            read_pos += self._buffer_size

        idx0 = int(read_pos) % self._buffer_size
        idx1 = (idx0 + 1) % self._buffer_size
        frac = read_pos - int(read_pos)

        return self._buffer[idx0] * (1.0 - frac) + self._buffer[idx1] * frac

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Process audio through flanger.

        Args:
            samples: Input audio samples (mono, float32)

        Returns:
            Processed audio samples
        """
        if not self._enabled:
            return samples

        output = np.zeros_like(samples)
        min_delay, max_delay = self._get_delay_range()
        lfo_inc = (2.0 * math.pi * self._rate) / self._sample_rate

        for i in range(len(samples)):
            # Calculate current delay from LFO (triangle wave for smoother sweep)
            lfo_value = math.sin(self._lfo_phase)
            current_delay = min_delay + (max_delay * (lfo_value + 1.0) * 0.5)

            # Get delayed sample
            delayed = self._interpolate(current_delay)

            # Input with feedback
            input_sample = samples[i] + (self._feedback_sample * self._feedback)

            # Write to buffer
            self._buffer[self._write_pos] = input_sample
            self._write_pos = (self._write_pos + 1) % self._buffer_size

            # Store for feedback
            self._feedback_sample = delayed

            # Mix wet/dry
            output[i] = samples[i] * (1.0 - self._wet_dry) + delayed * self._wet_dry

            # Advance LFO
            self._lfo_phase += lfo_inc
            if self._lfo_phase >= 2.0 * math.pi:
                self._lfo_phase -= 2.0 * math.pi

        return output.astype(np.float32)

    def reset(self):
        """Reset effect state."""
        self._buffer.fill(0.0)
        self._write_pos = 0
        self._lfo_phase = 0.0
        self._feedback_sample = 0.0

    # Properties
    @property
    def enabled(self) -> bool:
        """Whether effect is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable effect."""
        if value and not self._enabled:
            self.reset()
        self._enabled = value

    @property
    def rate(self) -> float:
        """LFO rate in Hz."""
        return self._rate

    @rate.setter
    def rate(self, value: float):
        """Set LFO rate."""
        self._rate = max(self.MIN_RATE, min(self.MAX_RATE, value))

    @property
    def depth(self) -> float:
        """Modulation depth (0.0-1.0)."""
        return self._depth

    @depth.setter
    def depth(self, value: float):
        """Set modulation depth."""
        self._depth = max(0.0, min(1.0, value))

    @property
    def feedback(self) -> float:
        """Feedback amount (0.0-0.95)."""
        return self._feedback

    @feedback.setter
    def feedback(self, value: float):
        """Set feedback amount."""
        self._feedback = max(self.MIN_FEEDBACK, min(self.MAX_FEEDBACK, value))

    @property
    def wet_dry(self) -> float:
        """Wet/dry mix (0.0-1.0)."""
        return self._wet_dry

    @wet_dry.setter
    def wet_dry(self, value: float):
        """Set wet/dry mix."""
        self._wet_dry = max(0.0, min(1.0, value))
