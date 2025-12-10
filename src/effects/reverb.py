# Reverb Effect
"""
reverb - Schroeder reverb effect for the Mini Synthesizer.

Implements a classic Schroeder reverb algorithm with:
- 4 parallel comb filters for density
- 2 series allpass filters for diffusion
- Wet/dry mix control
- Room size parameter to scale decay

Reference: M.R. Schroeder, "Natural Sounding Artificial Reverberation" (1962)
"""

import numpy as np
from typing import Optional


class CombFilter:
    """Comb filter with feedback for reverb density.

    A comb filter adds delayed copies of the signal with feedback,
    creating the characteristic 'ringing' of reverb.

    Attributes:
        delay_samples: Delay time in samples
        feedback: Feedback coefficient (0.0-1.0)
    """

    def __init__(self, delay_samples: int, feedback: float = 0.84):
        """Initialize comb filter.

        Args:
            delay_samples: Delay time in samples
            feedback: Feedback coefficient (0.0-1.0)
        """
        self._delay_samples = delay_samples
        self._feedback = feedback
        self._buffer = np.zeros(delay_samples, dtype=np.float32)
        self._write_pos = 0

    def process(self, input_sample: float) -> float:
        """Process a single sample through the comb filter.

        Args:
            input_sample: Input sample value

        Returns:
            Filtered output sample
        """
        # Read from delay buffer
        output = self._buffer[self._write_pos]

        # Write input + feedback to buffer
        self._buffer[self._write_pos] = input_sample + output * self._feedback

        # Advance write position
        self._write_pos = (self._write_pos + 1) % self._delay_samples

        return output

    def process_block(self, input_samples: np.ndarray) -> np.ndarray:
        """Process a block of samples through the comb filter.

        Args:
            input_samples: Input sample array

        Returns:
            Filtered output array
        """
        output = np.zeros(len(input_samples), dtype=np.float32)

        for i, sample in enumerate(input_samples):
            output[i] = self.process(sample)

        return output

    def reset(self):
        """Reset filter state."""
        self._buffer.fill(0.0)
        self._write_pos = 0

    @property
    def feedback(self) -> float:
        """Get feedback coefficient."""
        return self._feedback

    @feedback.setter
    def feedback(self, value: float):
        """Set feedback coefficient."""
        self._feedback = max(0.0, min(0.99, value))


class AllpassFilter:
    """Allpass filter for reverb diffusion.

    An allpass filter adds phase dispersion without changing
    frequency response, creating a more diffuse reverb sound.

    Attributes:
        delay_samples: Delay time in samples
        gain: Allpass gain coefficient (typically 0.5)
    """

    def __init__(self, delay_samples: int, gain: float = 0.5):
        """Initialize allpass filter.

        Args:
            delay_samples: Delay time in samples
            gain: Allpass gain coefficient
        """
        self._delay_samples = delay_samples
        self._gain = gain
        self._buffer = np.zeros(delay_samples, dtype=np.float32)
        self._write_pos = 0

    def process(self, input_sample: float) -> float:
        """Process a single sample through the allpass filter.

        Args:
            input_sample: Input sample value

        Returns:
            Filtered output sample
        """
        # Read delayed sample
        delayed = self._buffer[self._write_pos]

        # Allpass formula: y[n] = -g*x[n] + x[n-D] + g*y[n-D]
        output = -self._gain * input_sample + delayed

        # Write to buffer: x[n] + g*y[n-D]
        self._buffer[self._write_pos] = input_sample + self._gain * delayed

        # Advance write position
        self._write_pos = (self._write_pos + 1) % self._delay_samples

        return output

    def process_block(self, input_samples: np.ndarray) -> np.ndarray:
        """Process a block of samples through the allpass filter.

        Args:
            input_samples: Input sample array

        Returns:
            Filtered output array
        """
        output = np.zeros(len(input_samples), dtype=np.float32)

        for i, sample in enumerate(input_samples):
            output[i] = self.process(sample)

        return output

    def reset(self):
        """Reset filter state."""
        self._buffer.fill(0.0)
        self._write_pos = 0


class Reverb:
    """Schroeder reverb effect.

    Implements a classic Schroeder reverb with 4 parallel comb filters
    feeding into 2 series allpass filters. This creates a dense,
    diffuse reverb suitable for smoothing synthesizer output.

    Classic delay times at 44.1kHz:
    - Comb filters: 1557, 1617, 1491, 1422 samples
    - Allpass filters: 225, 556 samples

    Attributes:
        wet_dry: Wet/dry mix (0.0 = dry, 1.0 = wet)
        room_size: Room size scaling factor (0.0-1.0)
        enabled: Whether reverb is active
    """

    # Classic Schroeder delay times at 44.1kHz (in samples)
    COMB_DELAYS = [1557, 1617, 1491, 1422]
    ALLPASS_DELAYS = [225, 556]

    # Default parameters
    DEFAULT_FEEDBACK = 0.84
    DEFAULT_ALLPASS_GAIN = 0.5
    DEFAULT_WET_DRY = 0.3
    DEFAULT_ROOM_SIZE = 0.5

    def __init__(
        self,
        sample_rate: int = 44100,
        wet_dry: float = DEFAULT_WET_DRY,
        room_size: float = DEFAULT_ROOM_SIZE
    ):
        """Initialize reverb effect.

        Args:
            sample_rate: Audio sample rate in Hz
            wet_dry: Initial wet/dry mix (0.0-1.0)
            room_size: Initial room size (0.0-1.0)
        """
        self._sample_rate = sample_rate
        self._wet_dry = max(0.0, min(1.0, wet_dry))
        self._room_size = max(0.0, min(1.0, room_size))
        self._enabled = True

        # Scale delay times for sample rate
        scale = sample_rate / 44100.0

        # Create comb filters
        self._comb_filters = []
        for delay in self.COMB_DELAYS:
            scaled_delay = int(delay * scale * self._get_room_scale())
            scaled_delay = max(1, scaled_delay)
            feedback = self._get_feedback_for_room()
            self._comb_filters.append(CombFilter(scaled_delay, feedback))

        # Create allpass filters
        self._allpass_filters = []
        for delay in self.ALLPASS_DELAYS:
            scaled_delay = int(delay * scale)
            scaled_delay = max(1, scaled_delay)
            self._allpass_filters.append(
                AllpassFilter(scaled_delay, self.DEFAULT_ALLPASS_GAIN)
            )

        # Output gain to prevent clipping (4 comb filters mixed)
        self._output_gain = 0.25

    def _get_room_scale(self) -> float:
        """Get delay time scaling based on room size.

        Returns:
            Scale factor for delay times (0.5-2.0)
        """
        # Map room_size 0-1 to scale 0.5-2.0
        return 0.5 + self._room_size * 1.5

    def _get_feedback_for_room(self) -> float:
        """Get comb filter feedback based on room size.

        Returns:
            Feedback coefficient (0.7-0.9)
        """
        # Larger rooms have longer decay (higher feedback)
        return 0.7 + self._room_size * 0.2

    def _rebuild_filters(self):
        """Rebuild filters with updated room size."""
        scale = self._sample_rate / 44100.0
        room_scale = self._get_room_scale()
        feedback = self._get_feedback_for_room()

        for i, delay in enumerate(self.COMB_DELAYS):
            scaled_delay = int(delay * scale * room_scale)
            scaled_delay = max(1, scaled_delay)
            self._comb_filters[i] = CombFilter(scaled_delay, feedback)

    def process(self, input_samples: np.ndarray) -> np.ndarray:
        """Process audio through reverb.

        Args:
            input_samples: Input audio samples (mono)

        Returns:
            Processed audio with reverb applied
        """
        if not self._enabled or self._wet_dry == 0.0:
            return input_samples.copy()

        # Ensure float32
        if input_samples.dtype != np.float32:
            input_samples = input_samples.astype(np.float32)

        num_samples = len(input_samples)
        wet_output = np.zeros(num_samples, dtype=np.float32)

        # Process through parallel comb filters
        for comb in self._comb_filters:
            wet_output += comb.process_block(input_samples)

        # Apply output gain
        wet_output *= self._output_gain

        # Process through series allpass filters
        for allpass in self._allpass_filters:
            wet_output = allpass.process_block(wet_output)

        # Mix wet and dry
        dry_gain = 1.0 - self._wet_dry
        wet_gain = self._wet_dry

        output = input_samples * dry_gain + wet_output * wet_gain

        return output

    def reset(self):
        """Reset all filter states."""
        for comb in self._comb_filters:
            comb.reset()
        for allpass in self._allpass_filters:
            allpass.reset()

    @property
    def wet_dry(self) -> float:
        """Get wet/dry mix (0.0 = dry, 1.0 = wet)."""
        return self._wet_dry

    @wet_dry.setter
    def wet_dry(self, value: float):
        """Set wet/dry mix."""
        self._wet_dry = max(0.0, min(1.0, value))

    @property
    def room_size(self) -> float:
        """Get room size (0.0 = small, 1.0 = large)."""
        return self._room_size

    @room_size.setter
    def room_size(self, value: float):
        """Set room size (rebuilds filters)."""
        new_size = max(0.0, min(1.0, value))
        if abs(new_size - self._room_size) > 0.01:
            self._room_size = new_size
            self._rebuild_filters()

    @property
    def enabled(self) -> bool:
        """Check if reverb is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable reverb."""
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
        return (f"Reverb({status}, wet_dry={self._wet_dry:.2f}, "
                f"room_size={self._room_size:.2f})")
