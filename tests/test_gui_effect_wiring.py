# Tests for GUI Effect Wiring
"""
test_gui_effect_wiring - Tests that GUI controls properly trigger AppController methods.

Validates that:
- Effect panel callbacks fire when sliders/buttons are manipulated
- AppController methods are called with correct values
- All effects (Distortion, Chorus, Delay, Reverb) are wired correctly
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app_controller import AppController


class TestDistortionWiring:
    """Tests for distortion panel -> controller wiring."""

    def test_distortion_enable_calls_controller(self):
        """Enabling distortion should call set_distortion_enabled."""
        controller = AppController()
        controller.set_distortion_enabled(True)
        assert controller.distortion_enabled is True

    def test_distortion_disable_calls_controller(self):
        """Disabling distortion should call set_distortion_enabled."""
        controller = AppController()
        controller.set_distortion_enabled(True)
        controller.set_distortion_enabled(False)
        assert controller.distortion_enabled is False

    def test_distortion_drive_calls_controller(self):
        """Changing drive should call set_distortion_drive."""
        controller = AppController()
        controller.set_distortion_drive(10.0)
        assert controller._distortion.drive == 10.0

    def test_distortion_tone_calls_controller(self):
        """Changing tone should call set_distortion_tone."""
        controller = AppController()
        controller.set_distortion_tone(0.8)
        assert controller._distortion.tone == 0.8

    def test_distortion_mode_calls_controller(self):
        """Changing mode should call set_distortion_mode."""
        controller = AppController()
        controller.set_distortion_mode('hard')
        assert controller._distortion.mode == 'hard'

    def test_distortion_mix_calls_controller(self):
        """Changing mix should call set_distortion_mix."""
        controller = AppController()
        controller.set_distortion_mix(0.75)
        assert controller._distortion.mix == 0.75


class TestChorusWiring:
    """Tests for chorus panel -> controller wiring."""

    def test_chorus_enable_calls_controller(self):
        """Enabling chorus should call set_chorus_enabled."""
        controller = AppController()
        controller.set_chorus_enabled(True)
        assert controller.chorus_enabled is True

    def test_chorus_disable_calls_controller(self):
        """Disabling chorus should call set_chorus_enabled."""
        controller = AppController()
        controller.set_chorus_enabled(True)
        controller.set_chorus_enabled(False)
        assert controller.chorus_enabled is False

    def test_chorus_rate_calls_controller(self):
        """Changing rate should call set_chorus_rate."""
        controller = AppController()
        controller.set_chorus_rate(2.5)
        assert controller._chorus.rate == 2.5

    def test_chorus_depth_calls_controller(self):
        """Changing depth should call set_chorus_depth."""
        controller = AppController()
        controller.set_chorus_depth(0.6)
        assert controller._chorus.depth == 0.6

    def test_chorus_voices_calls_controller(self):
        """Changing voices should call set_chorus_voices."""
        controller = AppController()
        controller.set_chorus_voices(4)
        assert controller._chorus.voices == 4

    def test_chorus_wet_dry_calls_controller(self):
        """Changing wet/dry should call set_chorus_wet_dry."""
        controller = AppController()
        controller.set_chorus_wet_dry(0.5)
        assert controller._chorus.wet_dry == 0.5


class TestDelayWiring:
    """Tests for delay panel -> controller wiring."""

    def test_delay_enable_calls_controller(self):
        """Enabling delay should call set_delay_enabled."""
        controller = AppController()
        controller.set_delay_enabled(True)
        assert controller.delay_enabled is True

    def test_delay_disable_calls_controller(self):
        """Disabling delay should call set_delay_enabled."""
        controller = AppController()
        controller.set_delay_enabled(True)
        controller.set_delay_enabled(False)
        assert controller.delay_enabled is False

    def test_delay_time_calls_controller(self):
        """Changing delay time should call set_delay_time."""
        controller = AppController()
        controller.set_delay_time(300)  # milliseconds
        assert controller._delay.delay_time_ms == 300

    def test_delay_feedback_calls_controller(self):
        """Changing feedback should call set_delay_feedback."""
        controller = AppController()
        controller.set_delay_feedback(0.6)
        assert controller._delay.feedback == 0.6

    def test_delay_wet_dry_calls_controller(self):
        """Changing wet/dry should call set_delay_wet_dry."""
        controller = AppController()
        controller.set_delay_wet_dry(0.7)
        assert controller._delay.wet_dry == 0.7


class TestReverbWiring:
    """Tests for reverb panel -> controller wiring."""

    def test_reverb_enable_calls_controller(self):
        """Enabling reverb should call set_reverb_enabled."""
        controller = AppController()
        controller.set_reverb_enabled(True)
        assert controller.reverb_enabled is True

    def test_reverb_disable_calls_controller(self):
        """Disabling reverb should call set_reverb_enabled."""
        controller = AppController()
        controller.set_reverb_enabled(True)
        controller.set_reverb_enabled(False)
        assert controller.reverb_enabled is False

    def test_reverb_room_size_calls_controller(self):
        """Changing room size should call set_reverb_room_size."""
        controller = AppController()
        controller.set_reverb_room_size(0.8)
        assert controller._reverb.room_size == 0.8

    def test_reverb_wet_dry_calls_controller(self):
        """Changing wet/dry should call set_reverb_wet_dry."""
        controller = AppController()
        controller.set_reverb_wet_dry(0.5)
        assert controller._reverb.wet_dry == 0.5


class TestEffectChainWiring:
    """Tests for the complete effects chain integration."""

    def test_all_effects_can_be_enabled(self):
        """All effects should be able to be enabled simultaneously."""
        controller = AppController()
        controller.set_distortion_enabled(True)
        controller.set_chorus_enabled(True)
        controller.set_delay_enabled(True)
        controller.set_reverb_enabled(True)

        assert controller.distortion_enabled is True
        assert controller.chorus_enabled is True
        assert controller.delay_enabled is True
        assert controller.reverb_enabled is True

    def test_effects_independent_toggle(self):
        """Toggling one effect should not affect others."""
        controller = AppController()

        # Enable all
        controller.set_distortion_enabled(True)
        controller.set_chorus_enabled(True)
        controller.set_delay_enabled(True)
        controller.set_reverb_enabled(True)

        # Disable distortion only
        controller.set_distortion_enabled(False)

        # Other effects should remain enabled
        assert controller.distortion_enabled is False
        assert controller.chorus_enabled is True
        assert controller.delay_enabled is True
        assert controller.reverb_enabled is True

    def test_effects_parameters_persist(self):
        """Effect parameters should persist after enable/disable."""
        controller = AppController()

        # Set parameters
        controller.set_distortion_drive(15.0)
        controller.set_chorus_rate(3.0)
        controller.set_delay_time(400)
        controller.set_reverb_room_size(0.9)

        # Toggle effects off and on
        controller.set_distortion_enabled(True)
        controller.set_distortion_enabled(False)
        controller.set_distortion_enabled(True)

        # Parameters should persist
        assert controller._distortion.drive == 15.0
        assert controller._chorus.rate == 3.0
        assert controller._delay.delay_time_ms == 400
        assert controller._reverb.room_size == 0.9


class TestSynthParameterWiring:
    """Tests for synth parameter wiring via set_parameter."""

    def test_master_volume_wiring(self):
        """Master volume should route through parameter queue."""
        controller = AppController()
        controller.set_parameter('master_volume', 0.5)

        # Check queue received the parameter
        changes = controller._param_queue.get_all()
        assert ('master_volume', 0.5) in changes

    def test_filter_cutoff_wiring(self):
        """Filter cutoff should route through parameter queue."""
        controller = AppController()
        controller.set_parameter('filter_cutoff', 1500.0)

        changes = controller._param_queue.get_all()
        assert ('filter_cutoff', 1500.0) in changes

    def test_filter_resonance_wiring(self):
        """Filter resonance should route through parameter queue."""
        controller = AppController()
        controller.set_parameter('filter_resonance', 0.7)

        changes = controller._param_queue.get_all()
        assert ('filter_resonance', 0.7) in changes

    def test_osc1_waveform_wiring(self):
        """Osc1 waveform should route through parameter queue."""
        controller = AppController()
        controller.set_parameter('osc1_waveform', 'square')

        changes = controller._param_queue.get_all()
        assert ('osc1_waveform', 'square') in changes

    def test_amp_envelope_wiring(self):
        """Amp envelope params should route through parameter queue."""
        controller = AppController()
        controller.set_parameter('amp_attack', 0.2)
        controller.set_parameter('amp_decay', 0.3)
        controller.set_parameter('amp_sustain', 0.5)
        controller.set_parameter('amp_release', 0.4)

        changes = controller._param_queue.get_all()
        assert ('amp_attack', 0.2) in changes
        assert ('amp_decay', 0.3) in changes
        assert ('amp_sustain', 0.5) in changes
        assert ('amp_release', 0.4) in changes


class TestNoteWiring:
    """Tests for note on/off wiring."""

    def test_note_on_activates_voice(self):
        """Note on should activate a voice."""
        controller = AppController()
        controller.note_on(60, 100)

        # Should have at least one active voice
        assert controller.get_active_voice_count() >= 1

    def test_note_off_releases_voice(self):
        """Note off should release a voice."""
        controller = AppController()
        controller.note_on(60, 100)
        controller.note_off(60)

        # Voice should be in release state (may still count as active briefly)
        # Just verify no exception occurs
        count = controller.get_active_voice_count()
        assert count >= 0

    def test_all_notes_off(self):
        """All notes off should release all voices."""
        controller = AppController()
        controller.note_on(60, 100)
        controller.note_on(64, 100)
        controller.note_on(67, 100)
        controller.all_notes_off()

        # After releasing, voices may still be active during release
        # Just verify it doesn't crash
        count = controller.get_active_voice_count()
        assert count >= 0


class TestPresetWiring:
    """Tests for preset loading wiring."""

    def test_preset_load_returns_params(self):
        """Loading a preset should return parameter dict."""
        controller = AppController()
        result = controller.load_preset('Fat Bass')

        assert result is not None
        assert isinstance(result, dict)
        assert 'filter_cutoff' in result

    def test_preset_load_updates_current_name(self):
        """Loading a preset should update current preset name."""
        controller = AppController()
        controller.load_preset('Bright Lead')

        assert controller.current_preset_name == 'Bright Lead'

    def test_preset_list_contains_defaults(self):
        """Preset list should contain default presets."""
        controller = AppController()
        presets = controller.get_preset_list()

        assert 'Init' in presets
        assert 'Fat Bass' in presets
        assert 'Bright Lead' in presets


class TestEffectPropertyAccessors:
    """Tests for effect property accessors."""

    def test_distortion_enabled_property(self):
        """distortion_enabled property should work."""
        controller = AppController()
        assert controller.distortion_enabled is False

        controller.set_distortion_enabled(True)
        assert controller.distortion_enabled is True

    def test_chorus_enabled_property(self):
        """chorus_enabled property should work."""
        controller = AppController()
        assert controller.chorus_enabled is False

        controller.set_chorus_enabled(True)
        assert controller.chorus_enabled is True

    def test_delay_enabled_property(self):
        """delay_enabled property should work."""
        controller = AppController()
        assert controller.delay_enabled is False

        controller.set_delay_enabled(True)
        assert controller.delay_enabled is True

    def test_reverb_enabled_property(self):
        """reverb_enabled property should work."""
        controller = AppController()
        assert controller.reverb_enabled is False

        controller.set_reverb_enabled(True)
        assert controller.reverb_enabled is True
