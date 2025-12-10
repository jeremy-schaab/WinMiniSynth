# ADSR Envelope module for Mini Synthesizer
"""
envelope.py - ADSR envelope generator

Implements the ADSREnvelope value object from the domain model.
Shapes amplitude or filter cutoff over time in response to note events.

Envelope stages:
- IDLE: Output = 0, waiting for gate
- ATTACK: Rising from 0 to 1 (linear)
- DECAY: Falling from 1 to sustain level (exponential)
- SUSTAIN: Holding at sustain level
- RELEASE: Falling from current value to 0 (exponential)

Usage:
    env = ADSREnvelope(sample_rate=44100)
    env.attack = 0.01   # 10ms attack
    env.decay = 0.1     # 100ms decay
    env.sustain = 0.7   # 70% sustain level
    env.release = 0.3   # 300ms release

    env.gate_on()       # Trigger envelope
    samples = env.generate(512)

    env.gate_off()      # Release envelope
    samples = env.generate(512)
"""

from enum import IntEnum
from typing import Optional
import numpy as np

try:
    from numba import jit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    # Fallback: no-op decorator if numba not installed
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


# Stage constants for numba (IntEnum not supported in nopython mode)
_STAGE_IDLE = 0
_STAGE_ATTACK = 1
_STAGE_DECAY = 2
_STAGE_SUSTAIN = 3
_STAGE_RELEASE = 4


@jit(nopython=True, cache=True)
def _envelope_generate(num_samples: int, stage: int, value: float,
                        attack_coef: float, decay_coef: float, release_coef: float,
                        sustain: float):
    """JIT-compiled envelope generation loop.

    Args:
        num_samples: Number of samples to generate
        stage: Current envelope stage (integer)
        value: Current envelope value
        attack_coef: Attack increment per sample
        decay_coef: Decay coefficient
        release_coef: Release coefficient
        sustain: Sustain level

    Returns:
        Tuple of (output array, final stage, final value)
    """
    output = np.empty(num_samples, dtype=np.float32)

    for i in range(num_samples):
        if stage == _STAGE_IDLE:
            value = 0.0

        elif stage == _STAGE_ATTACK:
            # Linear attack
            value += attack_coef
            if value >= 1.0:
                value = 1.0
                stage = _STAGE_DECAY

        elif stage == _STAGE_DECAY:
            # Exponential decay toward sustain level
            value = sustain + (value - sustain) * decay_coef
            # Check if we've reached sustain (within small threshold)
            if abs(value - sustain) < 0.001:
                value = sustain
                stage = _STAGE_SUSTAIN

        elif stage == _STAGE_SUSTAIN:
            # Hold at sustain level
            value = sustain

        elif stage == _STAGE_RELEASE:
            # Exponential release toward zero
            value *= release_coef
            # Check if we've reached zero (within small threshold)
            if value < 0.001:
                value = 0.0
                stage = _STAGE_IDLE

        output[i] = value

    return output, stage, value


class EnvelopeStage(IntEnum):
    """Envelope stage enumeration."""
    IDLE = 0
    ATTACK = 1
    DECAY = 2
    SUSTAIN = 3
    RELEASE = 4


class ADSREnvelope:
    """ADSR envelope generator.

    Generates time-varying amplitude envelope for modulating synthesis parameters.
    Uses linear attack and exponential decay/release for natural-sounding envelopes.

    Attributes:
        sample_rate: Audio sample rate in Hz
        stage: Current envelope stage
        attack: Attack time in seconds
        decay: Decay time in seconds
        sustain: Sustain level (0.0 to 1.0)
        release: Release time in seconds
    """

    # Minimum time constant to prevent instant transitions
    MIN_TIME = 0.001  # 1ms

    # Time constant multiplier for exponential curves
    # Higher values = slower exponential approach
    EXP_COEFFICIENT = 5.0

    def __init__(self, sample_rate: int = 44100):
        """Initialize envelope with sample rate.

        Args:
            sample_rate: Audio sample rate in Hz (default: 44100)
        """
        self.sample_rate = sample_rate

        # Envelope state
        self._stage: EnvelopeStage = EnvelopeStage.IDLE
        self._value: float = 0.0
        self._release_value: float = 0.0  # Value captured at gate_off

        # ADSR parameters
        self._attack: float = 0.01    # 10ms default
        self._decay: float = 0.1      # 100ms default
        self._sustain: float = 0.7    # 70% default
        self._release: float = 0.3    # 300ms default

        # Pre-computed coefficients (updated when parameters change)
        self._attack_coef: float = 0.0
        self._decay_coef: float = 0.0
        self._release_coef: float = 0.0
        self._update_coefficients()

        # Pre-allocate work buffer
        self._work_buffer: Optional[np.ndarray] = None

    @property
    def stage(self) -> EnvelopeStage:
        """Current envelope stage."""
        return self._stage

    @property
    def value(self) -> float:
        """Current envelope value (0.0 to 1.0)."""
        return self._value

    @property
    def attack(self) -> float:
        """Attack time in seconds."""
        return self._attack

    @attack.setter
    def attack(self, value: float) -> None:
        """Set attack time, clamped to valid range."""
        self._attack = max(self.MIN_TIME, min(10.0, value))
        self._update_coefficients()

    @property
    def decay(self) -> float:
        """Decay time in seconds."""
        return self._decay

    @decay.setter
    def decay(self, value: float) -> None:
        """Set decay time, clamped to valid range."""
        self._decay = max(self.MIN_TIME, min(10.0, value))
        self._update_coefficients()

    @property
    def sustain(self) -> float:
        """Sustain level (0.0 to 1.0)."""
        return self._sustain

    @sustain.setter
    def sustain(self, value: float) -> None:
        """Set sustain level, clamped to 0.0-1.0."""
        self._sustain = max(0.0, min(1.0, value))

    @property
    def release(self) -> float:
        """Release time in seconds."""
        return self._release

    @release.setter
    def release(self, value: float) -> None:
        """Set release time, clamped to valid range."""
        self._release = max(self.MIN_TIME, min(10.0, value))
        self._update_coefficients()

    def _update_coefficients(self) -> None:
        """Recalculate envelope coefficients when parameters change."""
        # Linear attack: increment per sample
        self._attack_coef = 1.0 / (self._attack * self.sample_rate)

        # Exponential decay/release coefficients
        # Using time constant: coef = exp(-1 / (time * sample_rate / EXP))
        decay_samples = self._decay * self.sample_rate
        release_samples = self._release * self.sample_rate

        self._decay_coef = np.exp(-self.EXP_COEFFICIENT / max(1.0, decay_samples))
        self._release_coef = np.exp(-self.EXP_COEFFICIENT / max(1.0, release_samples))

    def gate_on(self) -> None:
        """Trigger envelope attack stage.

        Call this when a note starts (key pressed).
        Transitions to ATTACK stage regardless of current stage.
        """
        self._stage = EnvelopeStage.ATTACK
        # Don't reset value for legato-style retriggering
        # self._value = 0.0  # Uncomment for hard restart

    def gate_off(self) -> None:
        """Trigger envelope release stage.

        Call this when a note ends (key released).
        Captures current value and transitions to RELEASE stage.
        """
        if self._stage != EnvelopeStage.IDLE:
            self._release_value = self._value
            self._stage = EnvelopeStage.RELEASE

    def reset(self) -> None:
        """Reset envelope to idle state.

        Use for panic/all-notes-off situations.
        """
        self._stage = EnvelopeStage.IDLE
        self._value = 0.0
        self._release_value = 0.0

    def is_active(self) -> bool:
        """Check if envelope is producing non-zero output.

        Returns:
            True if envelope is in any stage except IDLE
        """
        return self._stage != EnvelopeStage.IDLE

    def is_releasing(self) -> bool:
        """Check if envelope is in release stage.

        Returns:
            True if envelope is in RELEASE stage
        """
        return self._stage == EnvelopeStage.RELEASE

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate envelope samples.

        Generates envelope values based on current stage and parameters.
        Automatically transitions between stages as thresholds are reached.
        Uses JIT-compiled code for performance when numba is available.

        Args:
            num_samples: Number of samples to generate

        Returns:
            NumPy array of float32 envelope values (0.0 to 1.0)
        """
        # Use JIT-compiled function for processing
        output, new_stage, new_value = _envelope_generate(
            num_samples, int(self._stage), self._value,
            self._attack_coef, self._decay_coef, self._release_coef,
            self._sustain
        )

        # Update state
        self._stage = EnvelopeStage(new_stage)
        self._value = new_value

        return output

    def _process_sample(self) -> float:
        """Process a single envelope sample.

        Handles stage transitions and value updates.

        Returns:
            Current envelope value
        """
        if self._stage == EnvelopeStage.IDLE:
            self._value = 0.0

        elif self._stage == EnvelopeStage.ATTACK:
            # Linear attack
            self._value += self._attack_coef
            if self._value >= 1.0:
                self._value = 1.0
                self._stage = EnvelopeStage.DECAY

        elif self._stage == EnvelopeStage.DECAY:
            # Exponential decay toward sustain level
            self._value = self._sustain + (self._value - self._sustain) * self._decay_coef
            # Check if we've reached sustain (within small threshold)
            if abs(self._value - self._sustain) < 0.001:
                self._value = self._sustain
                self._stage = EnvelopeStage.SUSTAIN

        elif self._stage == EnvelopeStage.SUSTAIN:
            # Hold at sustain level
            self._value = self._sustain

        elif self._stage == EnvelopeStage.RELEASE:
            # Exponential release toward zero
            self._value *= self._release_coef
            # Check if we've reached zero (within small threshold)
            if self._value < 0.001:
                self._value = 0.0
                self._stage = EnvelopeStage.IDLE

        return self._value

    def generate_vectorized(self, num_samples: int) -> np.ndarray:
        """Generate envelope samples (vectorized version).

        This is a faster implementation that works well when staying
        in a single stage. Falls back to sample-by-sample for transitions.

        Args:
            num_samples: Number of samples to generate

        Returns:
            NumPy array of float32 envelope values
        """
        # For simplicity, use sample-by-sample processing
        # A fully vectorized version would need to predict stage transitions
        return self.generate(num_samples)

    def __repr__(self) -> str:
        """String representation of envelope state."""
        return (f"ADSREnvelope(A={self._attack:.3f}s, D={self._decay:.3f}s, "
                f"S={self._sustain:.2f}, R={self._release:.3f}s, "
                f"stage={self._stage.name}, value={self._value:.3f})")
