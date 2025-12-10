# Distortion Effect
"""
distortion - Distortion/saturation effect for the Mini Synthesizer.

Implements distortion with:
- Multiple waveshaping modes (soft, hard, tube)
- Drive control for intensity
- Tone control (post-filter)
- Wet/dry mix
- DC offset removal
"""

import numpy as np
from typing import Literal
import math


class Distortion:
    """Distortion/saturation effect with multiple waveshaping modes.

    Provides drive, tone shaping, and wet/dry mix controls.
    Includes DC offset removal to prevent signal drift.

    Attributes:
        drive: Drive amount (1.0-20.0)
        tone: Post-filter tone (0.0 = dark, 1.0 = bright)
        mix: Wet/dry mix (0.0 = dry, 1.0 = wet)
        mode: Waveshaping mode ('soft', 'hard', 'tube')
        enabled: Whether distortion is active
    """

    # Parameter limits
    MIN_DRIVE = 1.0
    MAX_DRIVE = 20.0

    # Defaults
    DEFAULT_DRIVE = 2.0
    DEFAULT_TONE = 0.5
    DEFAULT_MIX = 1.0
    DEFAULT_MODE = 'soft'

    # Valid modes
    MODES = ('soft', 'hard', 'tube')

    def __init__(
        self,
        sample_rate: int = 44100,
        drive: float = DEFAULT_DRIVE,
        tone: float = DEFAULT_TONE,
        mix: float = DEFAULT_MIX,
        mode: str = DEFAULT_MODE
    ):
        """Initialize distortion effect.

        Args:
            sample_rate: Audio sample rate in Hz
            drive: Drive amount (1.0-20.0)
            tone: Post-filter tone (0.0-1.0)
            mix: Wet/dry mix (0.0-1.0)
            mode: Waveshaping mode ('soft', 'hard', 'tube')
        """
        self._sample_rate = sample_rate
        self._enabled = False

        # Clamp and set parameters
        self._drive = max(self.MIN_DRIVE, min(self.MAX_DRIVE, drive))
        self._tone = max(0.0, min(1.0, tone))
        self._mix = max(0.0, min(1.0, mix))
        self._mode = mode if mode in self.MODES else self.DEFAULT_MODE

        # DC blocking filter state (simple high-pass)
        self._dc_block_prev_input = 0.0
        self._dc_block_prev_output = 0.0
        self._dc_block_coeff = 0.995

        # Tone filter state (simple one-pole low-pass)
        self._tone_filter_state = 0.0

    def _soft_clip(self, x: np.ndarray) -> np.ndarray:
        """Soft clipping using tanh.

        Produces warm, tube-like saturation.

        Args:
            x: Input samples

        Returns:
            Soft-clipped samples
        """
        return np.tanh(x)

    def _hard_clip(self, x: np.ndarray) -> np.ndarray:
        """Hard clipping.

        Produces aggressive digital distortion.

        Args:
            x: Input samples

        Returns:
            Hard-clipped samples
        """
        return np.clip(x, -1.0, 1.0)

    def _tube_clip(self, x: np.ndarray) -> np.ndarray:
        """Asymmetric soft clipping to simulate tube warmth.

        Positive and negative halves are clipped differently
        to create even harmonics like real tubes.

        Args:
            x: Input samples

        Returns:
            Tube-style clipped samples
        """
        output = np.zeros_like(x)

        # Asymmetric clipping
        pos_mask = x >= 0
        neg_mask = ~pos_mask

        # Positive half: softer clipping
        output[pos_mask] = np.tanh(x[pos_mask] * 0.9)

        # Negative half: slightly harder clipping with asymmetry
        output[neg_mask] = np.tanh(x[neg_mask] * 1.1) * 0.9

        return output

    def _apply_waveshaping(self, x: np.ndarray) -> np.ndarray:
        """Apply selected waveshaping mode.

        Args:
            x: Input samples (pre-amplified by drive)

        Returns:
            Waveshaped samples
        """
        if self._mode == 'soft':
            return self._soft_clip(x)
        elif self._mode == 'hard':
            return self._hard_clip(x)
        else:  # tube
            return self._tube_clip(x)

    def _apply_tone_filter(self, samples: np.ndarray) -> np.ndarray:
        """Apply tone control filter.

        Simple one-pole low-pass filter where tone controls cutoff.
        tone=0 is dark (more filtering), tone=1 is bright (less filtering).

        Args:
            samples: Input samples

        Returns:
            Tone-filtered samples
        """
        # Calculate filter coefficient from tone
        # tone=1 -> coeff near 1 (pass everything)
        # tone=0 -> coeff near 0.1 (heavy filtering)
        coeff = 0.1 + 0.9 * self._tone

        output = np.zeros_like(samples)

        for i in range(len(samples)):
            # One-pole low-pass: y[n] = coeff * x[n] + (1-coeff) * y[n-1]
            self._tone_filter_state = coeff * samples[i] + (1.0 - coeff) * self._tone_filter_state
            output[i] = self._tone_filter_state

        return output

    def _dc_block(self, samples: np.ndarray) -> np.ndarray:
        """Apply DC blocking filter to remove offset.

        Args:
            samples: Input samples

        Returns:
            DC-blocked samples
        """
        output = np.zeros_like(samples)

        for i in range(len(samples)):
            # High-pass: y[n] = x[n] - x[n-1] + coeff * y[n-1]
            out = samples[i] - self._dc_block_prev_input + self._dc_block_coeff * self._dc_block_prev_output
            self._dc_block_prev_input = samples[i]
            self._dc_block_prev_output = out
            output[i] = out

        return output

    def process(self, input_samples: np.ndarray) -> np.ndarray:
        """Process audio through distortion.

        Args:
            input_samples: Input audio samples (mono)

        Returns:
            Processed audio with distortion applied
        """
        if not self._enabled or self._mix == 0.0:
            return input_samples.copy()

        # Ensure float32
        if input_samples.dtype != np.float32:
            input_samples = input_samples.astype(np.float32)

        # Apply drive (pre-amplification)
        driven = input_samples * self._drive

        # Apply waveshaping
        distorted = self._apply_waveshaping(driven)

        # Apply tone control
        toned = self._apply_tone_filter(distorted)

        # Remove DC offset
        dc_blocked = self._dc_block(toned)

        # Mix wet and dry
        dry_gain = 1.0 - self._mix
        wet_gain = self._mix

        return input_samples * dry_gain + dc_blocked * wet_gain

    def reset(self):
        """Reset filter states."""
        self._dc_block_prev_input = 0.0
        self._dc_block_prev_output = 0.0
        self._tone_filter_state = 0.0

    # Properties

    @property
    def drive(self) -> float:
        """Get drive amount (1.0-20.0)."""
        return self._drive

    @drive.setter
    def drive(self, value: float):
        """Set drive amount."""
        self._drive = max(self.MIN_DRIVE, min(self.MAX_DRIVE, value))

    @property
    def tone(self) -> float:
        """Get tone (0.0 = dark, 1.0 = bright)."""
        return self._tone

    @tone.setter
    def tone(self, value: float):
        """Set tone."""
        self._tone = max(0.0, min(1.0, value))

    @property
    def mix(self) -> float:
        """Get wet/dry mix (0.0 = dry, 1.0 = wet)."""
        return self._mix

    @mix.setter
    def mix(self, value: float):
        """Set wet/dry mix."""
        self._mix = max(0.0, min(1.0, value))

    @property
    def mode(self) -> str:
        """Get waveshaping mode."""
        return self._mode

    @mode.setter
    def mode(self, value: str):
        """Set waveshaping mode."""
        if value in self.MODES:
            self._mode = value

    @property
    def enabled(self) -> bool:
        """Check if distortion is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable distortion."""
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
        return (f"Distortion({status}, drive={self._drive:.1f}, "
                f"tone={self._tone:.2f}, mix={self._mix:.2f}, mode='{self._mode}')")
