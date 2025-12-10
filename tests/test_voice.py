# Tests for SynthVoice module
"""
test_voice.py - Unit tests for the SynthVoice class

Tests cover:
- Voice initialization
- Note on/off handling
- Voice state management
- Audio generation
- Parameter application
- Voice stealing preparation
"""

import pytest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from synth.voice import SynthVoice, VoiceParameters
from synth.oscillator import Waveform


class TestVoiceInit:
    """Tests for SynthVoice initialization."""

    def test_default_init(self):
        """Test default initialization values."""
        voice = SynthVoice()
        assert voice.sample_rate == 44100
        assert voice.voice_id == 0
        assert voice.note == -1
        assert voice.velocity == 0

    def test_custom_init(self):
        """Test initialization with custom values."""
        voice = SynthVoice(sample_rate=48000, voice_id=5)
        assert voice.sample_rate == 48000
        assert voice.voice_id == 5

    def test_initial_state_inactive(self):
        """Voice should start inactive."""
        voice = SynthVoice()
        assert not voice.is_active()
        assert not voice.is_releasing()


class TestVoiceNoteOn:
    """Tests for note_on behavior."""

    def test_note_on_activates_voice(self):
        """Note on should activate the voice."""
        voice = SynthVoice()
        voice.note_on(60, 100)
        assert voice.is_active()
        assert voice.note == 60
        assert voice.velocity == 100

    def test_note_on_multiple_notes(self):
        """Subsequent note_on should change the note."""
        voice = SynthVoice()
        voice.note_on(60, 100)
        assert voice.note == 60
        voice.note_on(64, 80)
        assert voice.note == 64
        assert voice.velocity == 80

    def test_note_on_velocity_range(self):
        """Test various velocity values."""
        voice = SynthVoice()
        voice.note_on(60, 0)
        assert voice.velocity == 0
        voice.note_on(60, 127)
        assert voice.velocity == 127


class TestVoiceNoteOff:
    """Tests for note_off behavior."""

    def test_note_off_triggers_release(self):
        """Note off should put voice in release state."""
        voice = SynthVoice()
        voice.note_on(60, 100)
        voice.note_off()
        assert voice.is_active()  # Still active during release
        assert voice.is_releasing()

    def test_note_off_when_idle(self):
        """Note off on idle voice should do nothing."""
        voice = SynthVoice()
        voice.note_off()  # Should not crash
        assert not voice.is_active()


class TestVoiceReset:
    """Tests for voice reset."""

    def test_reset_returns_to_idle(self):
        """Reset should return voice to idle state."""
        voice = SynthVoice()
        voice.note_on(60, 100)
        assert voice.is_active()
        voice.reset()
        assert not voice.is_active()
        assert voice.note == -1
        assert voice.velocity == 0

    def test_reset_during_release(self):
        """Reset during release should force idle."""
        voice = SynthVoice()
        voice.note_on(60, 100)
        voice.note_off()
        assert voice.is_releasing()
        voice.reset()
        assert not voice.is_active()


class TestVoiceGenerate:
    """Tests for audio generation."""

    def test_generate_output_shape(self):
        """Output should have correct length."""
        voice = SynthVoice()
        voice.note_on(60, 100)
        output = voice.generate(512)
        assert len(output) == 512

    def test_generate_output_dtype(self):
        """Output should be float32."""
        voice = SynthVoice()
        voice.note_on(60, 100)
        output = voice.generate(512)
        assert output.dtype == np.float32

    def test_generate_idle_produces_zeros(self):
        """Idle voice should output zeros."""
        voice = SynthVoice()
        output = voice.generate(512)
        assert np.all(output == 0.0)

    def test_generate_active_produces_sound(self):
        """Active voice should produce non-zero output."""
        voice = SynthVoice()
        voice.note_on(60, 100)
        output = voice.generate(512)
        assert np.max(np.abs(output)) > 0.0

    def test_generate_output_range(self):
        """Output should be in reasonable range."""
        voice = SynthVoice()
        voice.note_on(60, 100)
        output = voice.generate(4096)
        assert np.all(output >= -2.0)
        assert np.all(output <= 2.0)

    def test_generate_multiple_buffers(self):
        """Should be able to generate multiple buffers."""
        voice = SynthVoice()
        voice.note_on(60, 100)
        buf1 = voice.generate(512)
        buf2 = voice.generate(512)
        # Both should be non-zero
        assert np.max(np.abs(buf1)) > 0.0
        assert np.max(np.abs(buf2)) > 0.0


class TestVoiceVelocity:
    """Tests for velocity handling."""

    def test_velocity_affects_amplitude(self):
        """Higher velocity should produce louder output."""
        voice1 = SynthVoice()
        voice1.note_on(60, 64)
        out1 = voice1.generate(4096)

        voice2 = SynthVoice()
        voice2.note_on(60, 127)
        out2 = voice2.generate(4096)

        # Higher velocity should be louder
        assert np.max(np.abs(out2)) > np.max(np.abs(out1))

    def test_zero_velocity(self):
        """Zero velocity should produce minimal output."""
        voice = SynthVoice()
        voice.note_on(60, 0)
        output = voice.generate(512)
        # Zero velocity means no sound
        assert np.max(np.abs(output)) < 0.01


class TestVoiceParameters:
    """Tests for voice parameter handling."""

    def test_default_parameters(self):
        """Voice should have default parameters."""
        voice = SynthVoice()
        params = voice.parameters
        assert isinstance(params, VoiceParameters)
        assert params.osc1_waveform == Waveform.SAWTOOTH

    def test_set_parameters(self):
        """Should be able to set parameters."""
        voice = SynthVoice()
        params = VoiceParameters()
        params.osc1_waveform = Waveform.SQUARE
        params.filter_cutoff = 500.0
        voice.parameters = params
        assert voice.parameters.osc1_waveform == Waveform.SQUARE
        assert voice.parameters.filter_cutoff == 500.0

    def test_parameter_changes_affect_sound(self):
        """Parameter changes should affect output."""
        voice1 = SynthVoice()
        params1 = VoiceParameters()
        params1.osc1_waveform = Waveform.SINE
        voice1.parameters = params1
        voice1.note_on(60, 100)
        out_sine = voice1.generate(4096)

        voice2 = SynthVoice()
        params2 = VoiceParameters()
        params2.osc1_waveform = Waveform.SAWTOOTH
        voice2.parameters = params2
        voice2.note_on(60, 100)
        out_saw = voice2.generate(4096)

        # Different waveforms should produce different output
        correlation = np.corrcoef(out_sine, out_saw)[0, 1]
        assert correlation < 0.99  # Should be different


class TestVoiceSteal:
    """Tests for voice stealing."""

    def test_steal_resets_voice(self):
        """Steal should prepare voice for reuse after fade-out."""
        voice = SynthVoice()
        voice.note_on(60, 100)
        assert voice.is_active()
        voice.steal()
        # Steal starts fade-out; note is reset after generate() completes fade
        # Generate enough samples to complete the fade-out
        for _ in range(10):  # Multiple generate calls to complete fade
            voice.generate(512)
        assert voice.note == -1
        assert voice.velocity == 0

    def test_get_age_active(self):
        """Active voice should have positive age."""
        voice = SynthVoice()
        voice.note_on(60, 100)
        voice.generate(512)  # Advance envelope
        age = voice.get_age()
        assert age >= 0.0

    def test_get_age_idle(self):
        """Idle voice should have zero age."""
        voice = SynthVoice()
        age = voice.get_age()
        assert age == 0.0


class TestVoiceRepr:
    """Tests for string representation."""

    def test_repr_idle(self):
        """Repr should show idle state."""
        voice = SynthVoice(voice_id=3)
        repr_str = repr(voice)
        assert '3' in repr_str
        assert 'idle' in repr_str

    def test_repr_active(self):
        """Repr should show active state and note."""
        voice = SynthVoice(voice_id=2)
        voice.note_on(60, 100)
        repr_str = repr(voice)
        assert '2' in repr_str
        assert 'active' in repr_str
        assert '60' in repr_str


class TestVoiceParametersDataclass:
    """Tests for VoiceParameters dataclass."""

    def test_default_values(self):
        """Test default parameter values."""
        params = VoiceParameters()
        assert params.osc1_waveform == Waveform.SAWTOOTH
        assert params.osc1_level == 0.7
        assert params.osc2_detune == 5.0
        assert params.filter_cutoff == 2000.0
        assert params.filter_resonance == 0.3

    def test_custom_values(self):
        """Test setting custom parameter values."""
        params = VoiceParameters(
            osc1_waveform=Waveform.SQUARE,
            filter_cutoff=1000.0,
            amp_attack=0.1
        )
        assert params.osc1_waveform == Waveform.SQUARE
        assert params.filter_cutoff == 1000.0
        assert params.amp_attack == 0.1
