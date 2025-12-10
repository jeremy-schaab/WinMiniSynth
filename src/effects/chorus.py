# Chorus Effect
"""
chorus - Chorus effect for the Mini Synthesizer.

Implements a chorus effect with:
- LFO-modulated delay lines
- Multiple voices (2-4) with phase-offset LFOs
- Adjustable rate, depth, and wet/dry mix
"""

import numpy as np
from typing import Optional
import math


class Chorus:
    """Chorus effect using LFO-modulated delay lines.

    Creates a thickening effect by mixing delayed copies of the signal
    with the original. Each delay line has an LFO modulating its delay
    time, creating subtle pitch variations.

    Attributes:
        rate: LFO rate in Hz (0.1-5.0)
        depth: Modulation depth (0.0-1.0)
        voices: Number of delay voices (2-4)
        wet_dry: Wet/dry mix (0.0 = dry, 1.0 = wet)
        enabled: Whether chorus is active
    """

    # Parameter limits
    MIN_RATE = 0.1
    MAX_RATE = 5.0
    MIN_VOICES = 2
    MAX_VOICES = 4

    # Delay parameters (in samples at 44100 Hz)
    BASE_DELAY_MS = 25.0  # Base delay time
    MAX_DEPTH_MS = 5.0    # Maximum LFO modulation depth

    # Defaults
    DEFAULT_RATE = 0.5
    DEFAULT_DEPTH = 0.5
    DEFAULT_VOICES = 3
    DEFAULT_WET_DRY = 0.3

    def __init__(
        self,
        sample_rate: int = 44100,
        rate: float = DEFAULT_RATE,
        depth: float = DEFAULT_DEPTH,
        voices: int = DEFAULT_VOICES,
        wet_dry: float = DEFAULT_WET_DRY
    ):
        """Initialize chorus effect.

        Args:
            sample_rate: Audio sample rate in Hz
            rate: LFO rate in Hz (0.1-5.0)
            depth: Modulation depth (0.0-1.0)
            voices: Number of delay voices (2-4)
            wet_dry: Wet/dry mix (0.0-1.0)
        """
        self._sample_rate = sample_rate
        self._enabled = False

        # Clamp and set parameters
        self._rate = max(self.MIN_RATE, min(self.MAX_RATE, rate))
        self._depth = max(0.0, min(1.0, depth))
        self._voices = max(self.MIN_VOICES, min(self.MAX_VOICES, voices))
        self._wet_dry = max(0.0, min(1.0, wet_dry))

        # Calculate buffer size for maximum delay + modulation
        max_delay_samples = int(((self.BASE_DELAY_MS + self.MAX_DEPTH_MS) / 1000.0) * sample_rate) + 10
        self._buffer = np.zeros(max_delay_samples, dtype=np.float32)
        self._write_pos = 0

        # LFO phase for each voice (distributed evenly)
        self._lfo_phases = np.zeros(self.MAX_VOICES, dtype=np.float64)
        self._reset_lfo_phases()

    def _reset_lfo_phases(self):
        """Initialize LFO phases with even distribution."""
        for i in range(self._voices):
            self._lfo_phases[i] = (2.0 * math.pi * i) / self._voices

    def _get_base_delay_samples(self) -> float:
        """Get base delay in samples."""
        return (self.BASE_DELAY_MS / 1000.0) * self._sample_rate

    def _get_depth_samples(self) -> float:
        """Get modulation depth in samples."""
        return (self.MAX_DEPTH_MS / 1000.0) * self._sample_rate * self._depth

    def _interpolate(self, delay: float) -> float:
        """Linear interpolation for fractional delay.

        Args:
            delay: Fractional delay in samples

        Returns:
            Interpolated sample value
        """
        buffer_size = len(self._buffer)

        # Calculate integer and fractional parts
        int_delay = int(delay)
        frac = delay - int_delay

        # Read positions
        pos1 = (self._write_pos - int_delay) % buffer_size
        pos2 = (self._write_pos - int_delay - 1) % buffer_size

        # Linear interpolation
        return self._buffer[pos1] * (1.0 - frac) + self._buffer[pos2] * frac

    def process(self, input_samples: np.ndarray) -> np.ndarray:
        """Process audio through chorus.

        Args:
            input_samples: Input audio samples (mono)

        Returns:
            Processed audio with chorus applied
        """
        if not self._enabled or self._wet_dry == 0.0:
            return input_samples.copy()

        # Ensure float32
        if input_samples.dtype != np.float32:
            input_samples = input_samples.astype(np.float32)

        num_samples = len(input_samples)
        output = np.zeros(num_samples, dtype=np.float32)
        buffer_size = len(self._buffer)

        base_delay = self._get_base_delay_samples()
        depth_samples = self._get_depth_samples()

        # LFO phase increment per sample
        phase_inc = 2.0 * math.pi * self._rate / self._sample_rate

        for i in range(num_samples):
            # Write input to buffer
            self._buffer[self._write_pos] = input_samples[i]

            # Sum contributions from each voice
            wet_sample = 0.0
            for v in range(self._voices):
                # Calculate modulated delay for this voice
                lfo_value = math.sin(self._lfo_phases[v])
                delay = base_delay + lfo_value * depth_samples

                # Ensure delay is positive
                delay = max(1.0, delay)

                # Get interpolated sample
                wet_sample += self._interpolate(delay)

                # Advance LFO phase
                self._lfo_phases[v] += phase_inc
                if self._lfo_phases[v] >= 2.0 * math.pi:
                    self._lfo_phases[v] -= 2.0 * math.pi

            # Normalize by voice count
            wet_sample /= self._voices

            output[i] = wet_sample

            # Advance write position
            self._write_pos = (self._write_pos + 1) % buffer_size

        # Mix wet and dry
        dry_gain = 1.0 - self._wet_dry
        wet_gain = self._wet_dry

        return input_samples * dry_gain + output * wet_gain

    def reset(self):
        """Reset chorus buffer and LFO phases."""
        self._buffer.fill(0.0)
        self._write_pos = 0
        self._reset_lfo_phases()

    # Properties

    @property
    def rate(self) -> float:
        """Get LFO rate in Hz."""
        return self._rate

    @rate.setter
    def rate(self, value: float):
        """Set LFO rate in Hz."""
        self._rate = max(self.MIN_RATE, min(self.MAX_RATE, value))

    @property
    def depth(self) -> float:
        """Get modulation depth (0.0-1.0)."""
        return self._depth

    @depth.setter
    def depth(self, value: float):
        """Set modulation depth."""
        self._depth = max(0.0, min(1.0, value))

    @property
    def voices(self) -> int:
        """Get number of voices."""
        return self._voices

    @voices.setter
    def voices(self, value: int):
        """Set number of voices."""
        new_voices = max(self.MIN_VOICES, min(self.MAX_VOICES, int(value)))
        if new_voices != self._voices:
            self._voices = new_voices
            self._reset_lfo_phases()

    @property
    def wet_dry(self) -> float:
        """Get wet/dry mix (0.0 = dry, 1.0 = wet)."""
        return self._wet_dry

    @wet_dry.setter
    def wet_dry(self, value: float):
        """Set wet/dry mix."""
        self._wet_dry = max(0.0, min(1.0, value))

    @property
    def enabled(self) -> bool:
        """Check if chorus is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable chorus."""
        self._enabled = value
        if not value:
            self.reset()

    @property
    def sample_rate(self) -> int:
        """Get sample rate."""
        return self._sample_rate

    def __repr__(self) -> str:
        """String representation."""
        status = "enabled" if self._enabled else "disabled"
        return (f"Chorus({status}, rate={self._rate:.2f}Hz, "
                f"depth={self._depth:.2f}, voices={self._voices}, "
                f"wet_dry={self._wet_dry:.2f})")
