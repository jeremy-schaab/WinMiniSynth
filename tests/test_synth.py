# Tests for MiniSynth module
"""
test_synth.py - Unit tests for the MiniSynth class

Tests cover:
- Synth initialization
- Note on/off handling
- Polyphony and voice allocation
- Voice stealing
- Audio generation
- Parameter convenience methods
"""

import pytest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from synth.synth import MiniSynth, VoiceStealingStrategy, SynthState
from synth.voice import VoiceParameters
from synth.oscillator import Waveform


class TestMiniSynthInit:
    """Tests for MiniSynth initialization."""

    def test_default_init(self):
        """Test default initialization values."""
        synth = MiniSynth()
        assert synth.sample_rate == 44100
        assert synth.max_voices == 8
        assert synth.master_volume == 0.8

    def test_custom_init(self):
        """Test initialization with custom values."""
        synth = MiniSynth(sample_rate=48000, max_voices=4)
        assert synth.sample_rate == 48000
        assert synth.max_voices == 4

    def test_invalid_max_voices(self):
        """Should raise error for invalid max_voices."""
        with pytest.raises(ValueError):
            MiniSynth(max_voices=0)
        with pytest.raises(ValueError):
            MiniSynth(max_voices=33)

    def test_initial_state(self):
        """Initial state should have no active voices."""
        synth = MiniSynth()
        assert synth.get_active_voice_count() == 0
        assert synth.get_playing_notes() == []


class TestMiniSynthNoteOn:
    """Tests for note_on behavior."""

    def test_note_on_activates_voice(self):
        """Note on should activate a voice."""
        synth = MiniSynth()
        synth.note_on(60, 100)
        assert synth.get_active_voice_count() == 1
        assert 60 in synth.get_playing_notes()

    def test_multiple_notes(self):
        """Should be able to play multiple notes."""
        synth = MiniSynth()
        synth.note_on(60, 100)
        synth.note_on(64, 100)
        synth.note_on(67, 100)
        assert synth.get_active_voice_count() == 3
        assert set(synth.get_playing_notes()) == {60, 64, 67}

    def test_retrigger_same_note(self):
        """Same note should retrigger, not use new voice."""
        synth = MiniSynth()
        synth.note_on(60, 100)
        assert synth.get_active_voice_count() == 1
        synth.note_on(60, 80)  # Retrigger
        assert synth.get_active_voice_count() == 1

    def test_velocity_zero_is_note_off(self):
        """Velocity 0 should be treated as note off."""
        synth = MiniSynth()
        synth.note_on(60, 100)
        assert synth.get_active_voice_count() == 1
        synth.note_on(60, 0)  # Should release
        # Voice may still be in release, but note should be released
        assert 60 not in synth.get_playing_notes()

    def test_invalid_note_ignored(self):
        """Invalid MIDI notes should be ignored."""
        synth = MiniSynth()
        synth.note_on(-1, 100)
        synth.note_on(128, 100)
        assert synth.get_active_voice_count() == 0


class TestMiniSynthNoteOff:
    """Tests for note_off behavior."""

    def test_note_off_releases_voice(self):
        """Note off should release the voice."""
        synth = MiniSynth()
        synth.note_on(60, 100)
        synth.note_off(60)
        # Voice is still active (releasing) but note is removed from map
        assert 60 not in synth.get_playing_notes()

    def test_note_off_nonexistent(self):
        """Note off for non-playing note should do nothing."""
        synth = MiniSynth()
        synth.note_off(60)  # Should not crash
        assert synth.get_active_voice_count() == 0


class TestMiniSynthAllNotesOff:
    """Tests for all_notes_off behavior."""

    def test_all_notes_off_releases_all(self):
        """All notes off should release all notes."""
        synth = MiniSynth()
        synth.note_on(60, 100)
        synth.note_on(64, 100)
        synth.note_on(67, 100)
        assert len(synth.get_playing_notes()) == 3
        synth.all_notes_off()
        assert len(synth.get_playing_notes()) == 0


class TestMiniSynthPanic:
    """Tests for panic behavior."""

    def test_panic_silences_all(self):
        """Panic should immediately silence all voices."""
        synth = MiniSynth()
        synth.note_on(60, 100)
        synth.note_on(64, 100)
        synth.panic()
        assert synth.get_active_voice_count() == 0
        assert synth.get_playing_notes() == []


class TestMiniSynthPolyphony:
    """Tests for polyphonic voice management."""

    def test_max_polyphony(self):
        """Should respect max_voices limit."""
        synth = MiniSynth(max_voices=4)
        for note in range(60, 70):  # 10 notes
            synth.note_on(note, 100)
        # Should have max 4 active
        assert synth.get_active_voice_count() <= 4


class TestMiniSynthVoiceStealing:
    """Tests for voice stealing behavior."""

    def test_voice_stealing_occurs(self):
        """Voice stealing should occur when all voices are active."""
        synth = MiniSynth(max_voices=2)
        synth.note_on(60, 100)
        synth.note_on(64, 100)
        assert synth.get_active_voice_count() == 2
        synth.note_on(67, 100)  # Should steal
        assert synth.get_active_voice_count() == 2
        assert 67 in synth.get_playing_notes()

    def test_quietest_strategy(self):
        """Quietest strategy should work."""
        synth = MiniSynth(max_voices=2)
        synth.steal_strategy = VoiceStealingStrategy.QUIETEST
        synth.note_on(60, 100)
        synth.note_on(64, 100)
        synth.note_on(67, 100)  # Should steal quietest
        assert synth.get_active_voice_count() == 2

    def test_oldest_strategy(self):
        """Oldest strategy should work."""
        synth = MiniSynth(max_voices=2)
        synth.steal_strategy = VoiceStealingStrategy.OLDEST
        synth.note_on(60, 100)
        synth.note_on(64, 100)
        synth.note_on(67, 100)  # Should steal oldest
        assert synth.get_active_voice_count() == 2

    def test_lowest_strategy(self):
        """Lowest pitch strategy should steal lowest note."""
        synth = MiniSynth(max_voices=2)
        synth.steal_strategy = VoiceStealingStrategy.LOWEST
        synth.note_on(60, 100)
        synth.note_on(64, 100)
        synth.note_on(67, 100)  # Should steal note 60
        assert synth.get_active_voice_count() == 2
        assert 60 not in synth.get_playing_notes()

    def test_highest_strategy(self):
        """Highest pitch strategy should steal highest note."""
        synth = MiniSynth(max_voices=2)
        synth.steal_strategy = VoiceStealingStrategy.HIGHEST
        synth.note_on(60, 100)
        synth.note_on(64, 100)
        synth.note_on(55, 100)  # Should steal note 64
        assert synth.get_active_voice_count() == 2
        assert 64 not in synth.get_playing_notes()


class TestMiniSynthGenerate:
    """Tests for audio generation."""

    def test_generate_output_shape(self):
        """Output should have correct length."""
        synth = MiniSynth()
        output = synth.generate(512)
        assert len(output) == 512

    def test_generate_output_dtype(self):
        """Output should be float32."""
        synth = MiniSynth()
        output = synth.generate(512)
        assert output.dtype == np.float32

    def test_generate_silent_when_no_notes(self):
        """Should output silence when no notes playing."""
        synth = MiniSynth()
        output = synth.generate(512)
        assert np.all(output == 0.0)

    def test_generate_sound_when_playing(self):
        """Should output sound when notes are playing."""
        synth = MiniSynth()
        synth.note_on(60, 100)
        output = synth.generate(512)
        assert np.max(np.abs(output)) > 0.0

    def test_generate_output_range(self):
        """Output should not clip (or be soft-clipped)."""
        synth = MiniSynth()
        # Play multiple notes to potentially cause clipping
        for note in range(60, 68):
            synth.note_on(note, 100)
        output = synth.generate(4096)
        # Soft clipping via tanh keeps output in [-1, 1]
        assert np.all(output >= -1.5)
        assert np.all(output <= 1.5)

    def test_generate_multiple_buffers(self):
        """Should be able to generate multiple buffers."""
        synth = MiniSynth()
        synth.note_on(60, 100)
        buf1 = synth.generate(512)
        buf2 = synth.generate(512)
        assert np.max(np.abs(buf1)) > 0.0
        assert np.max(np.abs(buf2)) > 0.0


class TestMiniSynthMasterVolume:
    """Tests for master volume control."""

    def test_master_volume_clamping(self):
        """Master volume should be clamped to 0.0-1.0."""
        synth = MiniSynth()
        synth.master_volume = -0.5
        assert synth.master_volume == 0.0
        synth.master_volume = 1.5
        assert synth.master_volume == 1.0

    def test_master_volume_affects_output(self):
        """Master volume should scale output."""
        synth1 = MiniSynth()
        synth1.master_volume = 1.0
        synth1.note_on(60, 100)
        out1 = synth1.generate(4096)

        synth2 = MiniSynth()
        synth2.master_volume = 0.5
        synth2.note_on(60, 100)
        out2 = synth2.generate(4096)

        # Half volume should be roughly half amplitude
        ratio = np.max(np.abs(out2)) / np.max(np.abs(out1))
        assert 0.4 < ratio < 0.6


class TestMiniSynthState:
    """Tests for state reporting."""

    def test_get_state(self):
        """get_state should return valid SynthState."""
        synth = MiniSynth()
        synth.note_on(60, 100)
        synth.note_on(64, 100)
        state = synth.get_state()
        assert isinstance(state, SynthState)
        assert state.active_voices == 2
        assert set(state.notes_playing) == {60, 64}
        assert state.master_volume == synth.master_volume
        assert state.cpu_load_estimate >= 0.0


class TestMiniSynthParameters:
    """Tests for parameter convenience methods."""

    def test_set_oscillator1(self):
        """Should set oscillator 1 parameters."""
        synth = MiniSynth()
        synth.set_oscillator1(Waveform.SQUARE, 0.8)
        assert synth.voice_parameters.osc1_waveform == Waveform.SQUARE
        assert synth.voice_parameters.osc1_level == 0.8

    def test_set_oscillator2(self):
        """Should set oscillator 2 parameters."""
        synth = MiniSynth()
        synth.set_oscillator2(Waveform.TRIANGLE, 0.6, -10.0)
        assert synth.voice_parameters.osc2_waveform == Waveform.TRIANGLE
        assert synth.voice_parameters.osc2_level == 0.6
        assert synth.voice_parameters.osc2_detune == -10.0

    def test_set_filter(self):
        """Should set filter parameters."""
        synth = MiniSynth()
        synth.set_filter(1000.0, 0.7, 0.8)
        assert synth.voice_parameters.filter_cutoff == 1000.0
        assert synth.voice_parameters.filter_resonance == 0.7
        assert synth.voice_parameters.filter_env_amount == 0.8

    def test_set_amp_envelope(self):
        """Should set amplitude envelope parameters."""
        synth = MiniSynth()
        synth.set_amp_envelope(0.1, 0.2, 0.5, 0.5)
        assert synth.voice_parameters.amp_attack == 0.1
        assert synth.voice_parameters.amp_decay == 0.2
        assert synth.voice_parameters.amp_sustain == 0.5
        assert synth.voice_parameters.amp_release == 0.5

    def test_set_filter_envelope(self):
        """Should set filter envelope parameters."""
        synth = MiniSynth()
        synth.set_filter_envelope(0.05, 0.3, 0.2, 0.4)
        assert synth.voice_parameters.filter_attack == 0.05
        assert synth.voice_parameters.filter_decay == 0.3
        assert synth.voice_parameters.filter_sustain == 0.2
        assert synth.voice_parameters.filter_release == 0.4

    def test_set_lfo(self):
        """Should set LFO parameters."""
        synth = MiniSynth()
        synth.set_lfo(3.0, 0.5, Waveform.TRIANGLE, 0.2, 0.3, 0.1)
        assert synth.voice_parameters.lfo_rate == 3.0
        assert synth.voice_parameters.lfo_depth == 0.5
        assert synth.voice_parameters.lfo_waveform == Waveform.TRIANGLE
        assert synth.voice_parameters.lfo_to_pitch == 0.2
        assert synth.voice_parameters.lfo_to_filter == 0.3
        assert synth.voice_parameters.lfo_to_pw == 0.1


class TestMiniSynthCallback:
    """Tests for audio callback integration."""

    def test_get_audio_callback(self):
        """Should return a callable."""
        synth = MiniSynth()
        callback = synth.get_audio_callback()
        assert callable(callback)

    def test_callback_generates_audio(self):
        """Callback should generate audio."""
        synth = MiniSynth()
        synth.note_on(60, 100)
        callback = synth.get_audio_callback()
        output = callback(512)
        assert len(output) == 512
        assert np.max(np.abs(output)) > 0.0


class TestMiniSynthVoiceChangeCallback:
    """Tests for voice change notification."""

    def test_voice_change_callback(self):
        """Should notify on voice count change."""
        synth = MiniSynth()
        callback_counts = []

        def on_change(count):
            callback_counts.append(count)

        synth.set_on_voice_change(on_change)
        synth.note_on(60, 100)
        synth.note_on(64, 100)
        synth.note_off(60)

        assert len(callback_counts) >= 3


class TestMiniSynthRepr:
    """Tests for string representation."""

    def test_repr(self):
        """Repr should show synth state."""
        synth = MiniSynth(max_voices=4)
        synth.master_volume = 0.7
        repr_str = repr(synth)
        assert '0' in repr_str  # Active voices
        assert '4' in repr_str  # Max voices
        assert '0.7' in repr_str or '0.70' in repr_str  # Volume
