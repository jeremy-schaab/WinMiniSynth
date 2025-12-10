# Tests for Preset Storage Module
"""
test_preset_storage - Unit tests for JSON preset management.
"""

import pytest
import sys
import os
import tempfile
import shutil
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from recording.preset_storage import PresetStorage, Preset


class TestPreset:
    """Tests for Preset dataclass."""

    def test_preset_creation(self):
        """Should create preset with parameters."""
        preset = Preset(
            name="Test",
            parameters={'filter_cutoff': 1000}
        )
        assert preset.name == "Test"
        assert preset.parameters['filter_cutoff'] == 1000

    def test_preset_defaults(self):
        """Should have sensible defaults."""
        preset = Preset(name="Test", parameters={})
        assert preset.author == ""
        assert preset.category == "uncategorized"
        assert preset.tags == []
        assert preset.version == "1.0"

    def test_preset_timestamps(self):
        """Should auto-set timestamps."""
        preset = Preset(name="Test", parameters={})
        assert preset.created_at != ""
        assert preset.modified_at != ""

    def test_preset_to_dict(self):
        """Should convert to dict."""
        preset = Preset(
            name="Test",
            parameters={'key': 'value'},
            author="Me"
        )
        d = preset.to_dict()
        assert d['name'] == "Test"
        assert d['parameters']['key'] == 'value'
        assert d['author'] == "Me"

    def test_preset_from_dict(self):
        """Should create from dict."""
        data = {
            'name': 'Test',
            'parameters': {'key': 'value'},
            'author': 'Me'
        }
        preset = Preset.from_dict(data)
        assert preset.name == "Test"
        assert preset.parameters['key'] == 'value'
        assert preset.author == "Me"


class TestPresetStorageInit:
    """Tests for PresetStorage initialization."""

    def test_default_init(self):
        """Should initialize with default directory."""
        storage = PresetStorage()
        assert storage.preset_dir == Path("presets")

    def test_custom_dir(self):
        """Should accept custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            assert storage.preset_dir == Path(tmpdir)

    def test_creates_directory(self):
        """Should create preset directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            preset_dir = Path(tmpdir) / "new_presets"
            storage = PresetStorage(preset_dir=str(preset_dir))
            assert preset_dir.exists()


class TestPresetStorageFactoryPresets:
    """Tests for factory presets."""

    def test_has_factory_presets(self):
        """Should have built-in factory presets."""
        storage = PresetStorage()
        factory = storage.get_factory_preset_names()
        assert len(factory) > 0
        assert 'Init' in factory

    def test_factory_preset_content(self):
        """Factory presets should have parameters."""
        storage = PresetStorage()
        params = storage.load_preset('Init')
        assert params is not None
        assert 'osc1_waveform' in params
        assert 'filter_cutoff' in params

    def test_is_factory_preset(self):
        """Should identify factory presets."""
        storage = PresetStorage()
        assert storage.is_factory_preset('Init')
        assert storage.is_factory_preset('Fat Bass')
        assert not storage.is_factory_preset('NonExistent')


class TestPresetStorageSaveLoad:
    """Tests for save/load functionality."""

    def test_save_preset(self):
        """Should save preset to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            params = {'filter_cutoff': 1500, 'osc1_waveform': 'sine'}

            result = storage.save_preset('MyPreset', params)

            assert result is True
            # File should exist
            files = list(Path(tmpdir).glob('*.json'))
            assert len(files) == 1

    def test_load_preset(self):
        """Should load saved preset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            params = {'filter_cutoff': 1500}

            storage.save_preset('MyPreset', params)
            loaded = storage.load_preset('MyPreset')

            assert loaded is not None
            assert loaded['filter_cutoff'] == 1500

    def test_load_full_preset(self):
        """Should load full preset with metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)

            storage.save_preset(
                'MyPreset',
                {'cutoff': 1000},
                author='Me',
                description='Test preset'
            )
            preset = storage.load_preset_full('MyPreset')

            assert preset is not None
            assert preset.name == 'MyPreset'
            assert preset.author == 'Me'
            assert preset.description == 'Test preset'

    def test_load_nonexistent(self):
        """Should return None for nonexistent preset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            result = storage.load_preset('NonExistent')
            assert result is None


class TestPresetStorageDelete:
    """Tests for preset deletion."""

    def test_delete_user_preset(self):
        """Should delete user preset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            storage.save_preset('ToDelete', {'key': 'value'})

            result = storage.delete_preset('ToDelete')

            assert result is True
            assert not storage.preset_exists('ToDelete')

    def test_cannot_delete_factory(self):
        """Should not delete factory presets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            result = storage.delete_preset('Init')
            assert result is False

    def test_delete_nonexistent(self):
        """Should return False for nonexistent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            result = storage.delete_preset('NonExistent')
            assert result is False


class TestPresetStorageList:
    """Tests for listing presets."""

    def test_list_includes_factory(self):
        """Should include factory presets by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            presets = storage.list_presets()
            assert 'Init' in presets

    def test_list_excludes_factory(self):
        """Should exclude factory when requested."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            storage.save_preset('UserPreset', {})
            presets = storage.list_presets(include_factory=False)
            assert 'Init' not in presets
            assert 'UserPreset' in presets

    def test_list_includes_user_presets(self):
        """Should include saved user presets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            storage.save_preset('MyBass', {})
            presets = storage.list_presets()
            assert 'MyBass' in presets


class TestPresetStorageCategory:
    """Tests for category functionality."""

    def test_save_with_category(self):
        """Should save preset with category."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            storage.save_preset('BassTest', {}, category='bass')

            preset = storage.load_preset_full('BassTest')
            assert preset.category == 'bass'

    def test_list_by_category(self):
        """Should list presets by category."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            storage.save_preset('Bass1', {}, category='bass')
            storage.save_preset('Lead1', {}, category='lead')

            by_category = storage.list_presets_by_category(include_factory=False)

            assert 'bass' in by_category
            assert 'Bass1' in by_category['bass']
            assert 'lead' in by_category
            assert 'Lead1' in by_category['lead']


class TestPresetStorageExists:
    """Tests for preset_exists."""

    def test_exists_factory(self):
        """Should find factory presets."""
        storage = PresetStorage()
        assert storage.preset_exists('Init')

    def test_exists_user(self):
        """Should find user presets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            storage.save_preset('Test', {})
            assert storage.preset_exists('Test')

    def test_not_exists(self):
        """Should return False for nonexistent."""
        storage = PresetStorage()
        assert not storage.preset_exists('NonExistent123')


class TestPresetStorageSanitize:
    """Tests for filename sanitization."""

    def test_sanitize_spaces(self):
        """Should handle spaces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            storage.save_preset('My Cool Preset', {})
            assert storage.preset_exists('My Cool Preset')

    def test_sanitize_special_chars(self):
        """Should handle special characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            storage.save_preset('Preset:Test/Ver<1>', {})
            assert storage.preset_exists('Preset:Test/Ver<1>')


class TestPresetStorageImportExport:
    """Tests for import/export functionality."""

    def test_export_preset(self):
        """Should export preset to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            storage.save_preset('ToExport', {'cutoff': 2000})

            export_path = Path(tmpdir) / 'exported.json'
            result = storage.export_preset('ToExport', str(export_path))

            assert result is True
            assert export_path.exists()

            with open(export_path) as f:
                data = json.load(f)
            assert data['name'] == 'ToExport'

    def test_import_preset(self):
        """Should import preset from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create external preset file
            external = {
                'name': 'Imported',
                'parameters': {'resonance': 0.8},
                'author': 'External'
            }
            external_path = Path(tmpdir) / 'external.json'
            with open(external_path, 'w') as f:
                json.dump(external, f)

            storage = PresetStorage(preset_dir=tmpdir)
            name = storage.import_preset(str(external_path))

            assert name == 'Imported'
            assert storage.preset_exists('Imported')

            loaded = storage.load_preset('Imported')
            assert loaded['resonance'] == 0.8

    def test_export_factory_preset(self):
        """Should be able to export factory presets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            export_path = Path(tmpdir) / 'init_export.json'

            result = storage.export_preset('Init', str(export_path))

            assert result is True
            assert export_path.exists()


class TestPresetStorageRepr:
    """Tests for string representation."""

    def test_repr(self):
        """Should show directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            repr_str = repr(storage)
            assert tmpdir in repr_str or "presets" in repr_str.lower()


class TestPresetStorageTags:
    """Tests for tag functionality."""

    def test_save_with_tags(self):
        """Should save preset with tags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PresetStorage(preset_dir=tmpdir)
            storage.save_preset(
                'Tagged',
                {'cutoff': 1000},
                tags=['acid', 'classic']
            )

            preset = storage.load_preset_full('Tagged')
            assert 'acid' in preset.tags
            assert 'classic' in preset.tags
