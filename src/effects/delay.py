# Delay Effect
"""
delay - Digital delay/echo effect for the Mini Synthesizer.

Implements a delay effect with:
- Circular buffer delay line
- Adjustable delay time (10-2000ms)
- Feedback control with DC blocking
- Wet/dry mix control
- Optional tempo sync calculation
"""

import numpy as np
from typing import Optional


class Delay:
    """Digital delay/echo effect with circular buffer.

    Provides adjustable delay time, feedback, and wet/dry mix.
    Includes DC blocking to prevent runaway oscillation with high feedback.

    Attributes:
        delay_time_ms: Delay time in milliseconds (10-2000)
        feedback: Feedback amount (0.0-0.95)
        wet_dry: Wet/dry mix (0.0 = dry, 1.0 = wet)
        enabled: Whether delay is active
    """

    # Parameter limits
    MIN_DELAY_MS = 10
    MAX_DELAY_MS = 2000
    MAX_FEEDBACK = 0.95
    DEFAULT_DELAY_MS = 300
    DEFAULT_FEEDBACK = 0.4
    DEFAULT_WET_DRY = 0.3

    def __init__(
        self,
        sample_rate: int = 44100,
        delay_time_ms: float = DEFAULT_DELAY_MS,
        feedback: float = DEFAULT_FEEDBACK,
        wet_dry: float = DEFAULT_WET_DRY
    ):
        """Initialize delay effect.

        Args:
            sample_rate: Audio sample rate in Hz
            delay_time_ms: Initial delay time in milliseconds (10-2000)
            feedback: Initial feedback amount (0.0-0.95)
            wet_dry: Initial wet/dry mix (0.0-1.0)
        """
        self._sample_rate = sample_rate
        self._enabled = False

        # Clamp and set parameters
        self._delay_time_ms = max(self.MIN_DELAY_MS, min(self.MAX_DELAY_MS, delay_time_ms))
        self._feedback = max(0.0, min(self.MAX_FEEDBACK, feedback))
        self._wet_dry = max(0.0, min(1.0, wet_dry))

        # Calculate maximum buffer size for MAX_DELAY_MS
        max_delay_samples = int((self.MAX_DELAY_MS / 1000.0) * sample_rate) + 1
        self._buffer = np.zeros(max_delay_samples, dtype=np.float32)
        self._write_pos = 0

        # DC blocking filter state (simple high-pass)
        self._dc_block_prev_input = 0.0
        self._dc_block_prev_output = 0.0
        self._dc_block_coeff = 0.995  # High-pass coefficient

    def _get_delay_samples(self) -> int:
        """Calculate delay in samples from delay_time_ms."""
        return int((self._delay_time_ms / 1000.0) * self._sample_rate)

    def _dc_block(self, sample: float) -> float:
        """Apply DC blocking filter to prevent runaway oscillation.

        Args:
            sample: Input sample

        Returns:
            DC-blocked sample
        """
        # Simple first-order high-pass: y[n] = x[n] - x[n-1] + coeff * y[n-1]
        output = sample - self._dc_block_prev_input + self._dc_block_coeff * self._dc_block_prev_output
        self._dc_block_prev_input = sample
        self._dc_block_prev_output = output
        return output

    def process(self, input_samples: np.ndarray) -> np.ndarray:
        """Process audio through delay.

        Args:
            input_samples: Input audio samples (mono)

        Returns:
            Processed audio with delay applied
        """
        if not self._enabled or self._wet_dry == 0.0:
            return input_samples.copy()

        # Ensure float32
        if input_samples.dtype != np.float32:
            input_samples = input_samples.astype(np.float32)

        num_samples = len(input_samples)
        output = np.zeros(num_samples, dtype=np.float32)
        delay_samples = self._get_delay_samples()
        buffer_size = len(self._buffer)

        for i in range(num_samples):
            # Calculate read position
            read_pos = (self._write_pos - delay_samples) % buffer_size

            # Read delayed sample
            delayed = self._buffer[read_pos]

            # Apply DC blocking to feedback path
            delayed_blocked = self._dc_block(delayed)

            # Write input + feedback to buffer
            self._buffer[self._write_pos] = input_samples[i] + delayed_blocked * self._feedback

            # Output is the delayed sample
            output[i] = delayed

            # Advance write position
            self._write_pos = (self._write_pos + 1) % buffer_size

        # Mix wet and dry
        dry_gain = 1.0 - self._wet_dry
        wet_gain = self._wet_dry

        return input_samples * dry_gain + output * wet_gain

    def reset(self):
        """Reset delay buffer and DC blocking state."""
        self._buffer.fill(0.0)
        self._write_pos = 0
        self._dc_block_prev_input = 0.0
        self._dc_block_prev_output = 0.0

    def sync_to_tempo(self, bpm: float, note_value: str = "1/4") -> float:
        """Calculate and set delay time based on tempo and note value.

        Args:
            bpm: Tempo in beats per minute
            note_value: Note value string ("1/4", "1/8", "1/16", "1/8T", "1/4.")

        Returns:
            Calculated delay time in milliseconds
        """
        # Base quarter note duration in ms
        quarter_note_ms = 60000.0 / bpm

        # Note value multipliers
        multipliers = {
            "1/1": 4.0,      # Whole note
            "1/2": 2.0,      # Half note
            "1/4": 1.0,      # Quarter note
            "1/8": 0.5,      # Eighth note
            "1/16": 0.25,    # Sixteenth note
            "1/32": 0.125,   # Thirty-second note
            "1/4.": 1.5,     # Dotted quarter
            "1/8.": 0.75,    # Dotted eighth
            "1/8T": 1.0/3,   # Eighth triplet
            "1/4T": 2.0/3,   # Quarter triplet
        }

        multiplier = multipliers.get(note_value, 1.0)
        delay_ms = quarter_note_ms * multiplier

        # Clamp to valid range
        delay_ms = max(self.MIN_DELAY_MS, min(self.MAX_DELAY_MS, delay_ms))
        self._delay_time_ms = delay_ms

        return delay_ms

    # Properties

    @property
    def delay_time_ms(self) -> float:
        """Get delay time in milliseconds."""
        return self._delay_time_ms

    @delay_time_ms.setter
    def delay_time_ms(self, value: float):
        """Set delay time in milliseconds."""
        self._delay_time_ms = max(self.MIN_DELAY_MS, min(self.MAX_DELAY_MS, value))

    @property
    def feedback(self) -> float:
        """Get feedback amount (0.0-0.95)."""
        return self._feedback

    @feedback.setter
    def feedback(self, value: float):
        """Set feedback amount (clamped to 0.0-0.95)."""
        self._feedback = max(0.0, min(self.MAX_FEEDBACK, value))

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
        """Check if delay is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable delay."""
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
        return (f"Delay({status}, time={self._delay_time_ms:.0f}ms, "
                f"feedback={self._feedback:.2f}, wet_dry={self._wet_dry:.2f})")
