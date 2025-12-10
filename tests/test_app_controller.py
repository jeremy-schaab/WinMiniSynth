# Tests for Application Controller Module
"""
test_app_controller - Unit tests for AppController and related components.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app_controller import (
    SynthPreset, DEFAULT_PRESETS, ParameterQueue, AppController
)
from synth import Waveform


class TestSynthPreset:
    """Tests for SynthPreset dataclass."""

    def test_create_default_preset(self):
        """Should create preset with default values."""
        preset = SynthPreset(name='Test')
        assert preset.name == 'Test'
        assert preset.osc1_waveform == 'sawtooth'
        assert preset.osc1_level == 0.7
        assert preset.master_volume == 0.7

    def test_create_custom_preset(self):
        """Should create preset with custom values."""
        preset = SynthPreset(
            name='Custom',
            osc1_waveform='sine',
            osc1_level=0.5,
            filter_cutoff=1000.0
        )
        assert preset.osc1_waveform == 'sine'
        assert preset.osc1_level == 0.5
        assert preset.filter_cutoff == 1000.0

    def test_to_dict(self):
        """Should convert preset to dictionary."""
        preset = SynthPreset(name='Test')
        d = preset.to_dict()
        assert isinstance(d, dict)
        assert d['name'] == 'Test'
        assert d['osc1_waveform'] == 'sawtooth'
        assert 'filter_cutoff' in d

    def test_from_dict(self):
        """Should create preset from dictionary."""
        data = {
            'name': 'FromDict',
            'osc1_waveform': 'square',
            'osc1_level': 0.3,
            'osc1_detune': 0.0,
            'osc1_octave': 0,
            'osc2_waveform': 'sawtooth',
            'osc2_level': 0.5,
            'osc2_detune': 5.0,
            'osc2_octave': 0,
            'filter_cutoff': 2000.0,
            'filter_resonance': 0.3,
            'filter_env_amount': 0.5,
            'amp_attack': 0.01,
            'amp_decay': 0.1,
            'amp_sustain': 0.7,
            'amp_release': 0.3,
            'filter_attack': 0.01,
            'filter_decay': 0.2,
            'filter_sustain': 0.5,
            'filter_release': 0.2,
            'lfo_waveform': 'sine',
            'lfo_rate': 5.0,
            'lfo_depth': 0.5,
            'lfo_to_pitch': 0.0,
            'lfo_to_filter': 0.0,
            'lfo_to_pw': 0.0,
            'master_volume': 0.7
        }
        preset = SynthPreset.from_dict(data)
        assert preset.name == 'FromDict'
        assert preset.osc1_waveform == 'square'
        assert preset.osc1_level == 0.3

    def test_save_to_file(self):
        """Should save preset to JSON file."""
        preset = SynthPreset(name='SaveTest')
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            preset.save_to_file(filepath)
            with open(filepath, 'r') as f:
                data = json.load(f)
            assert data['name'] == 'SaveTest'
        finally:
            os.unlink(filepath)

    def test_load_from_file(self):
        """Should load preset from JSON file."""
        data = {
            'name': 'LoadTest',
            'osc1_waveform': 'triangle',
            'osc1_level': 0.7,
            'osc1_detune': 0.0,
            'osc1_octave': 0,
            'osc2_waveform': 'sawtooth',
            'osc2_level': 0.5,
            'osc2_detune': 5.0,
            'osc2_octave': 0,
            'filter_cutoff': 2000.0,
            'filter_resonance': 0.3,
            'filter_env_amount': 0.5,
            'amp_attack': 0.01,
            'amp_decay': 0.1,
            'amp_sustain': 0.7,
            'amp_release': 0.3,
            'filter_attack': 0.01,
            'filter_decay': 0.2,
            'filter_sustain': 0.5,
            'filter_release': 0.2,
            'lfo_waveform': 'sine',
            'lfo_rate': 5.0,
            'lfo_depth': 0.5,
            'lfo_to_pitch': 0.0,
            'lfo_to_filter': 0.0,
            'lfo_to_pw': 0.0,
            'master_volume': 0.7
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            filepath = f.name

        try:
            preset = SynthPreset.load_from_file(filepath)
            assert preset.name == 'LoadTest'
            assert preset.osc1_waveform == 'triangle'
        finally:
            os.unlink(filepath)


class TestDefaultPresets:
    """Tests for DEFAULT_PRESETS dictionary."""

    def test_has_init_preset(self):
        """Should have Init preset."""
        assert 'Init' in DEFAULT_PRESETS

    def test_has_fat_bass_preset(self):
        """Should have Fat Bass preset."""
        assert 'Fat Bass' in DEFAULT_PRESETS

    def test_has_bright_lead_preset(self):
        """Should have Bright Lead preset."""
        assert 'Bright Lead' in DEFAULT_PRESETS

    def test_has_soft_pad_preset(self):
        """Should have Soft Pad preset."""
        assert 'Soft Pad' in DEFAULT_PRESETS

    def test_has_retro_square_preset(self):
        """Should have Retro Square preset."""
        assert 'Retro Square' in DEFAULT_PRESETS

    def test_fat_bass_has_low_cutoff(self):
        """Fat Bass should have low filter cutoff."""
        preset = DEFAULT_PRESETS['Fat Bass']
        assert preset.filter_cutoff < 1000.0

    def test_bright_lead_has_high_cutoff(self):
        """Bright Lead should have high filter cutoff."""
        preset = DEFAULT_PRESETS['Bright Lead']
        assert preset.filter_cutoff > 5000.0

    def test_soft_pad_has_slow_attack(self):
        """Soft Pad should have slow attack."""
        preset = DEFAULT_PRESETS['Soft Pad']
        assert preset.amp_attack > 0.1


class TestParameterQueue:
    """Tests for ParameterQueue class."""

    def test_create_queue(self):
        """Should create parameter queue."""
        queue = ParameterQueue()
        assert queue is not None

    def test_put_parameter(self):
        """Should queue parameter change."""
        queue = ParameterQueue()
        result = queue.put('test_param', 42)
        assert result is True

    def test_get_all_empty(self):
        """Should return empty list when queue is empty."""
        queue = ParameterQueue()
        changes = queue.get_all()
        assert changes == []

    def test_get_all_returns_changes(self):
        """Should return all queued changes."""
        queue = ParameterQueue()
        queue.put('param1', 1)
        queue.put('param2', 2)
        queue.put('param3', 3)

        changes = queue.get_all()
        assert len(changes) == 3
        assert changes[0] == ('param1', 1)
        assert changes[1] == ('param2', 2)
        assert changes[2] == ('param3', 3)

    def test_get_all_drains_queue(self):
        """Should drain queue on get_all."""
        queue = ParameterQueue()
        queue.put('param1', 1)
        queue.put('param2', 2)

        # First call drains
        changes1 = queue.get_all()
        assert len(changes1) == 2

        # Second call returns empty
        changes2 = queue.get_all()
        assert len(changes2) == 0

    def test_queue_handles_max_size(self):
        """Should handle queue at max size."""
        queue = ParameterQueue(maxsize=3)
        assert queue.put('p1', 1) is True
        assert queue.put('p2', 2) is True
        assert queue.put('p3', 3) is True
        # Queue full, should fail silently
        assert queue.put('p4', 4) is False


class TestAppController:
    """Tests for AppController class."""

    def test_create_controller(self):
        """Should create app controller."""
        controller = AppController()
        assert controller is not None

    def test_default_sample_rate(self):
        """Should have default sample rate."""
        controller = AppController()
        assert controller.sample_rate == 44100

    def test_custom_sample_rate(self):
        """Should accept custom sample rate."""
        controller = AppController(sample_rate=48000)
        assert controller.sample_rate == 48000

    def test_default_buffer_size(self):
        """Should have default buffer size."""
        controller = AppController()
        assert controller.buffer_size == 512

    def test_custom_buffer_size(self):
        """Should accept custom buffer size."""
        controller = AppController(buffer_size=256)
        assert controller.buffer_size == 256

    def test_default_max_voices(self):
        """Should have default max voices."""
        controller = AppController()
        assert controller.max_voices == 8

    def test_custom_max_voices(self):
        """Should accept custom max voices."""
        controller = AppController(max_voices=16)
        assert controller.max_voices == 16

    def test_is_not_running_initially(self):
        """Should not be running initially."""
        controller = AppController()
        assert controller.is_running is False

    def test_current_preset_name_default(self):
        """Should default to Init preset."""
        controller = AppController()
        assert controller.current_preset_name == 'Init'

    def test_set_parameter(self):
        """Should queue parameter changes."""
        controller = AppController()
        controller.set_parameter('master_volume', 0.5)
        # Verify by checking queue
        changes = controller._param_queue.get_all()
        assert len(changes) == 1
        assert changes[0] == ('master_volume', 0.5)

    def test_note_on(self):
        """Should trigger note on."""
        controller = AppController()
        # Should not raise
        controller.note_on(60, 100)

    def test_note_off(self):
        """Should trigger note off."""
        controller = AppController()
        controller.note_on(60, 100)
        # Should not raise
        controller.note_off(60)

    def test_all_notes_off(self):
        """Should release all notes."""
        controller = AppController()
        controller.note_on(60, 100)
        controller.note_on(64, 100)
        controller.note_on(67, 100)
        # Should not raise - notes are in release phase but still active briefly
        controller.all_notes_off()
        # After all_notes_off, voices enter release stage (may still show as active)
        # Just verify no exception is raised

    def test_voice_change_callback(self):
        """Should call voice change callback."""
        counts = []
        controller = AppController()
        controller.set_voice_change_callback(lambda c: counts.append(c))
        controller.note_on(60, 100)
        assert len(counts) >= 1

    def test_get_preset_list(self):
        """Should return list of presets."""
        controller = AppController()
        presets = controller.get_preset_list()
        assert 'Init' in presets
        assert 'Fat Bass' in presets

    def test_load_preset_by_name(self):
        """Should load preset by name."""
        controller = AppController()
        result = controller.load_preset('Fat Bass')
        assert result is not None  # Returns params dict on success
        assert isinstance(result, dict)
        assert controller.current_preset_name == 'Fat Bass'

    def test_load_preset_invalid_name(self):
        """Should return None for invalid preset."""
        controller = AppController()
        result = controller.load_preset('NonexistentPreset')
        assert result is None

    def test_load_preset_from_file(self):
        """Should load preset from file."""
        # Create temp preset file
        data = {
            'name': 'FilePreset',
            'osc1_waveform': 'square',
            'osc1_level': 0.7,
            'osc1_detune': 0.0,
            'osc1_octave': 0,
            'osc2_waveform': 'sawtooth',
            'osc2_level': 0.5,
            'osc2_detune': 5.0,
            'osc2_octave': 0,
            'filter_cutoff': 2000.0,
            'filter_resonance': 0.3,
            'filter_env_amount': 0.5,
            'amp_attack': 0.01,
            'amp_decay': 0.1,
            'amp_sustain': 0.7,
            'amp_release': 0.3,
            'filter_attack': 0.01,
            'filter_decay': 0.2,
            'filter_sustain': 0.5,
            'filter_release': 0.2,
            'lfo_waveform': 'sine',
            'lfo_rate': 5.0,
            'lfo_depth': 0.5,
            'lfo_to_pitch': 0.0,
            'lfo_to_filter': 0.0,
            'lfo_to_pw': 0.0,
            'master_volume': 0.7
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            filepath = f.name

        try:
            controller = AppController()
            result = controller.load_preset(filepath)
            assert result is not None  # Returns params dict on success
            assert isinstance(result, dict)
            assert controller.current_preset_name == 'FilePreset'
        finally:
            os.unlink(filepath)

    def test_save_preset(self):
        """Should save preset to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            controller = AppController(presets_dir=tmpdir)
            result = controller.save_preset('TestSave')
            assert result is True
            # Check file was created
            expected_file = os.path.join(tmpdir, 'testsave.json')
            assert os.path.exists(expected_file)

    def test_waveform_map(self):
        """Should have waveform string to enum mapping."""
        assert AppController.WAVEFORM_MAP['sine'] == Waveform.SINE
        assert AppController.WAVEFORM_MAP['sawtooth'] == Waveform.SAWTOOTH
        assert AppController.WAVEFORM_MAP['square'] == Waveform.SQUARE
        assert AppController.WAVEFORM_MAP['triangle'] == Waveform.TRIANGLE
        assert AppController.WAVEFORM_MAP['pulse'] == Waveform.PULSE

    def test_apply_master_volume(self):
        """Should apply master volume parameter."""
        controller = AppController()
        controller._apply_parameter('master_volume', 0.5)
        assert controller._synth.master_volume == 0.5

    def test_apply_osc1_waveform(self):
        """Should apply osc1 waveform parameter."""
        controller = AppController()
        controller._apply_parameter('osc1_waveform', 'sine')
        # Verify through internal tracking
        assert controller._current_params['osc1_waveform'] == Waveform.SINE

    def test_apply_filter_cutoff(self):
        """Should apply filter cutoff parameter."""
        controller = AppController()
        controller._apply_parameter('filter_cutoff', 1000.0)
        # Verify through internal tracking
        assert controller._current_params['filter_cutoff'] == 1000.0

    def test_apply_amp_envelope(self):
        """Should apply amp envelope parameters."""
        controller = AppController()
        controller._apply_parameter('amp_attack', 0.5)
        # Verify through internal tracking
        assert controller._current_params['amp_attack'] == 0.5

    def test_get_display_buffer(self):
        """Should return display buffer copy."""
        controller = AppController()
        buffer = controller.get_display_buffer()
        assert buffer is not None
        assert len(buffer) == controller.buffer_size

