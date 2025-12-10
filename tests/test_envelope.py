# Tests for ADSR Envelope module
"""
test_envelope.py - Unit tests for the ADSREnvelope class

Tests cover:
- Stage transitions (IDLE -> ATTACK -> DECAY -> SUSTAIN -> RELEASE -> IDLE)
- ADSR parameter setting and clamping
- Gate on/off behavior
- Output value ranges
- Timing accuracy
"""

import pytest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from synth.envelope import ADSREnvelope, EnvelopeStage


class TestEnvelopeInit:
    """Tests for ADSREnvelope initialization."""

    def test_default_init(self):
        """Test default initialization values."""
        env = ADSREnvelope()
        assert env.sample_rate == 44100
        assert env.stage == EnvelopeStage.IDLE
        assert env.value == 0.0
        assert env.attack == 0.01
        assert env.decay == 0.1
        assert env.sustain == 0.7
        assert env.release == 0.3

    def test_custom_sample_rate(self):
        """Test initialization with custom sample rate."""
        env = ADSREnvelope(sample_rate=48000)
        assert env.sample_rate == 48000


class TestEnvelopeProperties:
    """Tests for ADSR property getters and setters."""

    def test_attack_clamping(self):
        """Attack should be clamped to valid range."""
        env = ADSREnvelope()
        env.attack = 0.0001
        assert env.attack == ADSREnvelope.MIN_TIME
        env.attack = 20.0
        assert env.attack == 10.0

    def test_decay_clamping(self):
        """Decay should be clamped to valid range."""
        env = ADSREnvelope()
        env.decay = 0.0001
        assert env.decay == ADSREnvelope.MIN_TIME
        env.decay = 20.0
        assert env.decay == 10.0

    def test_sustain_clamping(self):
        """Sustain should be clamped to 0.0-1.0."""
        env = ADSREnvelope()
        env.sustain = -0.5
        assert env.sustain == 0.0
        env.sustain = 1.5
        assert env.sustain == 1.0

    def test_release_clamping(self):
        """Release should be clamped to valid range."""
        env = ADSREnvelope()
        env.release = 0.0001
        assert env.release == ADSREnvelope.MIN_TIME
        env.release = 20.0
        assert env.release == 10.0


class TestEnvelopeStages:
    """Tests for envelope stage transitions."""

    def test_initial_state_is_idle(self):
        """Envelope should start in IDLE stage."""
        env = ADSREnvelope()
        assert env.stage == EnvelopeStage.IDLE
        assert env.value == 0.0
        assert not env.is_active()

    def test_gate_on_triggers_attack(self):
        """gate_on() should transition to ATTACK stage."""
        env = ADSREnvelope()
        env.gate_on()
        assert env.stage == EnvelopeStage.ATTACK
        assert env.is_active()

    def test_attack_rises_to_one(self):
        """Attack stage should rise toward 1.0."""
        env = ADSREnvelope(sample_rate=44100)
        env.attack = 0.01  # 10ms attack
        env.gate_on()

        # Generate samples for attack duration
        attack_samples = int(0.015 * 44100)  # 15ms to ensure completion
        samples = env.generate(attack_samples)

        # Should have reached 1.0 and moved to decay
        assert env.value <= 1.0
        assert np.max(samples) >= 0.99

    def test_attack_to_decay_transition(self):
        """After reaching 1.0, should transition to DECAY."""
        env = ADSREnvelope(sample_rate=44100)
        env.attack = 0.001  # Very fast attack
        env.decay = 0.1
        env.sustain = 0.5
        env.gate_on()

        # Generate enough samples to pass attack
        env.generate(int(0.01 * 44100))

        # Should be in decay or sustain
        assert env.stage in [EnvelopeStage.DECAY, EnvelopeStage.SUSTAIN]

    def test_decay_approaches_sustain(self):
        """Decay should approach sustain level."""
        env = ADSREnvelope(sample_rate=44100)
        env.attack = 0.001
        env.decay = 0.1
        env.sustain = 0.5
        env.gate_on()

        # Generate enough samples for attack + decay
        samples = env.generate(int(0.5 * 44100))

        # Should be near sustain level
        assert abs(env.value - 0.5) < 0.1

    def test_sustain_holds_level(self):
        """Sustain should hold steady at sustain level."""
        env = ADSREnvelope(sample_rate=44100)
        env.attack = 0.001
        env.decay = 0.01
        env.sustain = 0.6
        env.gate_on()

        # Get to sustain stage
        env.generate(int(0.1 * 44100))

        # Generate sustain samples
        sustain_samples = env.generate(1024)

        # All sustain samples should be near sustain level
        assert np.all(np.abs(sustain_samples - 0.6) < 0.1)

    def test_gate_off_triggers_release(self):
        """gate_off() should transition to RELEASE stage."""
        env = ADSREnvelope(sample_rate=44100)
        env.attack = 0.001
        env.sustain = 0.5
        env.gate_on()
        env.generate(int(0.1 * 44100))  # Get to sustain

        env.gate_off()
        assert env.stage == EnvelopeStage.RELEASE
        assert env.is_releasing()

    def test_release_approaches_zero(self):
        """Release should approach zero."""
        env = ADSREnvelope(sample_rate=44100)
        env.attack = 0.001
        env.decay = 0.001
        env.sustain = 0.5
        env.release = 0.1
        env.gate_on()
        env.generate(int(0.05 * 44100))

        env.gate_off()
        samples = env.generate(int(0.5 * 44100))

        # Should reach near zero
        assert env.value < 0.01

    def test_release_to_idle_transition(self):
        """After release completes, should return to IDLE."""
        env = ADSREnvelope(sample_rate=44100)
        env.attack = 0.001
        env.decay = 0.001
        env.sustain = 0.5
        env.release = 0.01  # Fast release
        env.gate_on()
        env.generate(int(0.05 * 44100))

        env.gate_off()
        env.generate(int(0.1 * 44100))

        assert env.stage == EnvelopeStage.IDLE
        assert env.value == 0.0
        assert not env.is_active()


class TestEnvelopeReset:
    """Tests for envelope reset functionality."""

    def test_reset_returns_to_idle(self):
        """reset() should return envelope to idle state."""
        env = ADSREnvelope()
        env.gate_on()
        env.generate(1024)

        env.reset()
        assert env.stage == EnvelopeStage.IDLE
        assert env.value == 0.0

    def test_reset_during_release(self):
        """reset() should work during release stage."""
        env = ADSREnvelope()
        env.gate_on()
        env.generate(1024)
        env.gate_off()
        env.generate(512)

        env.reset()
        assert env.stage == EnvelopeStage.IDLE


class TestEnvelopeOutput:
    """Tests for envelope output characteristics."""

    def test_output_range(self):
        """Envelope output should be in range [0.0, 1.0]."""
        env = ADSREnvelope(sample_rate=44100)
        env.attack = 0.01
        env.decay = 0.1
        env.sustain = 0.5
        env.release = 0.1
        env.gate_on()

        # Generate full envelope cycle
        samples = []
        for _ in range(10):
            samples.extend(env.generate(1024))

        env.gate_off()
        for _ in range(10):
            samples.extend(env.generate(1024))

        samples = np.array(samples)
        assert np.all(samples >= 0.0)
        assert np.all(samples <= 1.0)

    def test_output_dtype(self):
        """Output should be float32."""
        env = ADSREnvelope()
        env.gate_on()
        samples = env.generate(512)
        assert samples.dtype == np.float32

    def test_output_length(self):
        """Output should have requested number of samples."""
        env = ADSREnvelope()
        env.gate_on()
        for length in [64, 128, 256, 512, 1024]:
            samples = env.generate(length)
            assert len(samples) == length

    def test_idle_produces_zeros(self):
        """IDLE stage should produce zeros."""
        env = ADSREnvelope()
        samples = env.generate(1024)
        assert np.all(samples == 0.0)


class TestEnvelopeTiming:
    """Tests for envelope timing accuracy."""

    def test_attack_timing(self):
        """Attack time should be approximately correct."""
        env = ADSREnvelope(sample_rate=44100)
        env.attack = 0.1  # 100ms

        env.gate_on()

        # Generate samples until we reach peak
        total_samples = 0
        while env.value < 0.99 and total_samples < 44100:
            env.generate(64)
            total_samples += 64

        # Should reach peak within reasonable time
        # (allowing for some variation due to discrete samples)
        attack_time = total_samples / 44100
        assert 0.08 < attack_time < 0.15  # 80-150ms tolerance

    def test_zero_sustain(self):
        """Zero sustain should skip sustain stage."""
        env = ADSREnvelope(sample_rate=44100)
        env.attack = 0.001
        env.decay = 0.1
        env.sustain = 0.0  # No sustain

        env.gate_on()
        env.generate(int(0.5 * 44100))

        # Value should be at or near zero (sustain level)
        assert env.value < 0.1


class TestEnvelopeRepr:
    """Tests for string representation."""

    def test_repr(self):
        """String representation should include key info."""
        env = ADSREnvelope()
        env.attack = 0.05
        env.decay = 0.2
        env.sustain = 0.6
        env.release = 0.3
        env.gate_on()
        env.generate(100)

        repr_str = repr(env)
        assert 'ADSR' in repr_str or 'Envelope' in repr_str
        assert '0.05' in repr_str or 'attack' in repr_str.lower()


class TestEnvelopeRetrigger:
    """Tests for envelope retriggering behavior."""

    def test_retrigger_during_sustain(self):
        """Retriggering during sustain should restart attack."""
        env = ADSREnvelope(sample_rate=44100)
        env.attack = 0.001
        env.decay = 0.01
        env.sustain = 0.5

        env.gate_on()
        env.generate(int(0.1 * 44100))  # Get to sustain

        value_before = env.value
        env.gate_on()  # Retrigger

        assert env.stage == EnvelopeStage.ATTACK

    def test_retrigger_during_release(self):
        """Retriggering during release should restart attack."""
        env = ADSREnvelope(sample_rate=44100)
        env.attack = 0.001
        env.sustain = 0.5
        env.release = 0.5

        env.gate_on()
        env.generate(int(0.05 * 44100))
        env.gate_off()
        env.generate(int(0.1 * 44100))  # Partially release

        env.gate_on()  # Retrigger
        assert env.stage == EnvelopeStage.ATTACK
