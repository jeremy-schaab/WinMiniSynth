# Preset Storage Module
"""
preset_storage - JSON preset management for the Mini Synthesizer.

Provides preset save/load functionality with:
- JSON file format
- Built-in factory presets
- User preset directory
- Preset validation
- Metadata support

Usage:
    storage = PresetStorage()

    # Save preset
    storage.save_preset('my_bass', synth.get_parameters())

    # Load preset
    params = storage.load_preset('my_bass')
    synth.set_parameters(params)

    # List presets
    presets = storage.list_presets()
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import datetime


@dataclass
class Preset:
    """Synthesizer preset data.

    Attributes:
        name: Preset name
        parameters: Synth parameters dict
        author: Creator name
        description: Preset description
        category: Preset category (bass, lead, pad, etc.)
        tags: List of tags
        created_at: Creation timestamp
        modified_at: Last modification timestamp
        version: Preset format version
    """
    name: str
    parameters: Dict[str, Any]
    author: str = ""
    description: str = ""
    category: str = "uncategorized"
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    modified_at: str = ""
    version: str = "1.0"

    def __post_init__(self):
        """Set timestamps if not provided."""
        now = datetime.datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.modified_at:
            self.modified_at = now

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Preset':
        """Create preset from dictionary."""
        return cls(
            name=data.get('name', 'Unnamed'),
            parameters=data.get('parameters', {}),
            author=data.get('author', ''),
            description=data.get('description', ''),
            category=data.get('category', 'uncategorized'),
            tags=data.get('tags', []),
            created_at=data.get('created_at', ''),
            modified_at=data.get('modified_at', ''),
            version=data.get('version', '1.0')
        )


class PresetStorage:
    """JSON preset storage manager.

    Manages loading and saving of synthesizer presets.
    Presets are stored as JSON files in the preset directory.

    Attributes:
        preset_dir: Directory for user presets
        factory_presets: Built-in factory presets
    """

    # Default preset directory
    DEFAULT_PRESET_DIR = "presets"

    # Preset categories
    CATEGORIES = [
        'bass', 'lead', 'pad', 'keys', 'pluck',
        'fx', 'drums', 'ambient', 'uncategorized'
    ]

    # Factory presets (built-in)
    FACTORY_PRESETS = {
        'Init': {
            'osc1_waveform': 'sawtooth',
            'osc1_level': 0.7,
            'osc1_detune': 0.0,
            'osc1_octave': 0,
            'osc2_waveform': 'sawtooth',
            'osc2_level': 0.5,
            'osc2_detune': 5.0,
            'osc2_octave': 0,
            'filter_cutoff': 2000.0,
            'filter_resonance': 0.3,
            'filter_env_amount': 0.0,
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
            'master_volume': 0.7,
        },
        'Fat Bass': {
            'osc1_waveform': 'sawtooth',
            'osc1_level': 0.8,
            'osc1_detune': 0.0,
            'osc1_octave': -1,
            'osc2_waveform': 'square',
            'osc2_level': 0.6,
            'osc2_detune': 10.0,
            'osc2_octave': -1,
            'filter_cutoff': 800.0,
            'filter_resonance': 0.5,
            'filter_env_amount': 0.7,
            'amp_attack': 0.005,
            'amp_decay': 0.2,
            'amp_sustain': 0.6,
            'amp_release': 0.2,
            'filter_attack': 0.01,
            'filter_decay': 0.3,
            'filter_sustain': 0.3,
            'filter_release': 0.2,
            'lfo_waveform': 'sine',
            'lfo_rate': 0.5,
            'lfo_depth': 0.0,
            'lfo_to_pitch': 0.0,
            'lfo_to_filter': 0.0,
            'lfo_to_pw': 0.0,
            'master_volume': 0.75,
        },
        'Bright Lead': {
            'osc1_waveform': 'sawtooth',
            'osc1_level': 0.7,
            'osc1_detune': -5.0,
            'osc1_octave': 0,
            'osc2_waveform': 'sawtooth',
            'osc2_level': 0.7,
            'osc2_detune': 5.0,
            'osc2_octave': 0,
            'filter_cutoff': 5000.0,
            'filter_resonance': 0.4,
            'filter_env_amount': 0.3,
            'amp_attack': 0.01,
            'amp_decay': 0.1,
            'amp_sustain': 0.8,
            'amp_release': 0.3,
            'filter_attack': 0.01,
            'filter_decay': 0.15,
            'filter_sustain': 0.6,
            'filter_release': 0.25,
            'lfo_waveform': 'triangle',
            'lfo_rate': 6.0,
            'lfo_depth': 0.3,
            'lfo_to_pitch': 0.1,
            'lfo_to_filter': 0.0,
            'lfo_to_pw': 0.0,
            'master_volume': 0.7,
        },
        'Soft Pad': {
            'osc1_waveform': 'triangle',
            'osc1_level': 0.6,
            'osc1_detune': -3.0,
            'osc1_octave': 0,
            'osc2_waveform': 'sine',
            'osc2_level': 0.5,
            'osc2_detune': 3.0,
            'osc2_octave': 1,
            'filter_cutoff': 1500.0,
            'filter_resonance': 0.2,
            'filter_env_amount': 0.2,
            'amp_attack': 0.5,
            'amp_decay': 0.3,
            'amp_sustain': 0.8,
            'amp_release': 1.0,
            'filter_attack': 0.4,
            'filter_decay': 0.5,
            'filter_sustain': 0.5,
            'filter_release': 0.8,
            'lfo_waveform': 'sine',
            'lfo_rate': 0.5,
            'lfo_depth': 0.4,
            'lfo_to_pitch': 0.0,
            'lfo_to_filter': 0.3,
            'lfo_to_pw': 0.0,
            'master_volume': 0.65,
        },
        'Retro Square': {
            'osc1_waveform': 'square',
            'osc1_level': 0.7,
            'osc1_detune': 0.0,
            'osc1_octave': 0,
            'osc2_waveform': 'square',
            'osc2_level': 0.4,
            'osc2_detune': 0.0,
            'osc2_octave': 1,
            'filter_cutoff': 3000.0,
            'filter_resonance': 0.3,
            'filter_env_amount': 0.4,
            'amp_attack': 0.01,
            'amp_decay': 0.15,
            'amp_sustain': 0.7,
            'amp_release': 0.2,
            'filter_attack': 0.01,
            'filter_decay': 0.2,
            'filter_sustain': 0.4,
            'filter_release': 0.15,
            'lfo_waveform': 'square',
            'lfo_rate': 4.0,
            'lfo_depth': 0.0,
            'lfo_to_pitch': 0.0,
            'lfo_to_filter': 0.0,
            'lfo_to_pw': 0.0,
            'master_volume': 0.7,
        },
        # New presets (BOLT-009)
        'Ethereal Strings': {
            'osc1_waveform': 'sawtooth',
            'osc1_level': 0.5,
            'osc1_detune': -7.0,
            'osc1_octave': 0,
            'osc2_waveform': 'sawtooth',
            'osc2_level': 0.5,
            'osc2_detune': 7.0,
            'osc2_octave': 0,
            'filter_cutoff': 2500.0,
            'filter_resonance': 0.15,
            'filter_env_amount': 0.25,
            'amp_attack': 0.8,
            'amp_decay': 0.4,
            'amp_sustain': 0.85,
            'amp_release': 1.5,
            'filter_attack': 0.6,
            'filter_decay': 0.5,
            'filter_sustain': 0.6,
            'filter_release': 1.2,
            'lfo_waveform': 'sine',
            'lfo_rate': 0.3,
            'lfo_depth': 0.35,
            'lfo_to_pitch': 0.05,
            'lfo_to_filter': 0.2,
            'lfo_to_pw': 0.0,
            'master_volume': 0.65,
        },
        'Plucky Keys': {
            'osc1_waveform': 'triangle',
            'osc1_level': 0.8,
            'osc1_detune': 0.0,
            'osc1_octave': 0,
            'osc2_waveform': 'sine',
            'osc2_level': 0.4,
            'osc2_detune': 0.0,
            'osc2_octave': 1,
            'filter_cutoff': 4000.0,
            'filter_resonance': 0.25,
            'filter_env_amount': 0.6,
            'amp_attack': 0.002,
            'amp_decay': 0.35,
            'amp_sustain': 0.3,
            'amp_release': 0.4,
            'filter_attack': 0.001,
            'filter_decay': 0.25,
            'filter_sustain': 0.2,
            'filter_release': 0.3,
            'lfo_waveform': 'sine',
            'lfo_rate': 3.0,
            'lfo_depth': 0.0,
            'lfo_to_pitch': 0.0,
            'lfo_to_filter': 0.0,
            'lfo_to_pw': 0.0,
            'master_volume': 0.7,
        },
        'Warm Organ': {
            'osc1_waveform': 'sine',
            'osc1_level': 0.7,
            'osc1_detune': 0.0,
            'osc1_octave': 0,
            'osc2_waveform': 'sine',
            'osc2_level': 0.5,
            'osc2_detune': 0.0,
            'osc2_octave': 1,
            'filter_cutoff': 2000.0,
            'filter_resonance': 0.1,
            'filter_env_amount': 0.1,
            'amp_attack': 0.02,
            'amp_decay': 0.05,
            'amp_sustain': 0.9,
            'amp_release': 0.15,
            'filter_attack': 0.01,
            'filter_decay': 0.1,
            'filter_sustain': 0.8,
            'filter_release': 0.1,
            'lfo_waveform': 'sine',
            'lfo_rate': 6.5,
            'lfo_depth': 0.2,
            'lfo_to_pitch': 0.08,
            'lfo_to_filter': 0.0,
            'lfo_to_pw': 0.0,
            'master_volume': 0.7,
        },
        'Acid Squelch': {
            'osc1_waveform': 'sawtooth',
            'osc1_level': 0.9,
            'osc1_detune': 0.0,
            'osc1_octave': -1,
            'osc2_waveform': 'square',
            'osc2_level': 0.3,
            'osc2_detune': 0.0,
            'osc2_octave': -1,
            'filter_cutoff': 500.0,
            'filter_resonance': 0.85,
            'filter_env_amount': 0.9,
            'amp_attack': 0.001,
            'amp_decay': 0.25,
            'amp_sustain': 0.0,
            'amp_release': 0.1,
            'filter_attack': 0.001,
            'filter_decay': 0.2,
            'filter_sustain': 0.1,
            'filter_release': 0.1,
            'lfo_waveform': 'sine',
            'lfo_rate': 0.0,
            'lfo_depth': 0.0,
            'lfo_to_pitch': 0.0,
            'lfo_to_filter': 0.0,
            'lfo_to_pw': 0.0,
            'master_volume': 0.75,
        },
        'Cosmic Bell': {
            'osc1_waveform': 'triangle',
            'osc1_level': 0.6,
            'osc1_detune': 0.0,
            'osc1_octave': 1,
            'osc2_waveform': 'sine',
            'osc2_level': 0.7,
            'osc2_detune': 12.0,
            'osc2_octave': 2,
            'filter_cutoff': 6000.0,
            'filter_resonance': 0.35,
            'filter_env_amount': 0.4,
            'amp_attack': 0.001,
            'amp_decay': 1.5,
            'amp_sustain': 0.0,
            'amp_release': 2.0,
            'filter_attack': 0.001,
            'filter_decay': 1.2,
            'filter_sustain': 0.2,
            'filter_release': 1.5,
            'lfo_waveform': 'sine',
            'lfo_rate': 0.2,
            'lfo_depth': 0.25,
            'lfo_to_pitch': 0.02,
            'lfo_to_filter': 0.15,
            'lfo_to_pw': 0.0,
            'master_volume': 0.6,
        },
    }

    def __init__(self, preset_dir: Optional[str] = None):
        """Initialize preset storage.

        Args:
            preset_dir: Directory for user presets (default: 'presets')
        """
        self._preset_dir = Path(preset_dir or self.DEFAULT_PRESET_DIR)
        self._ensure_preset_dir()

    def _ensure_preset_dir(self):
        """Create preset directory if it doesn't exist."""
        self._preset_dir.mkdir(parents=True, exist_ok=True)

    @property
    def preset_dir(self) -> Path:
        """Get preset directory path."""
        return self._preset_dir

    def save_preset(
        self,
        name: str,
        parameters: Dict[str, Any],
        author: str = "",
        description: str = "",
        category: str = "uncategorized",
        tags: Optional[List[str]] = None
    ) -> bool:
        """Save preset to file.

        Args:
            name: Preset name
            parameters: Synth parameters dict
            author: Creator name
            description: Preset description
            category: Preset category
            tags: List of tags

        Returns:
            True if saved successfully
        """
        # Create preset object
        preset = Preset(
            name=name,
            parameters=parameters,
            author=author,
            description=description,
            category=category,
            tags=tags or []
        )

        # Generate filename
        filename = self._sanitize_filename(name) + '.json'
        filepath = self._preset_dir / filename

        # Write JSON file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(preset.to_dict(), f, indent=2)
            return True
        except Exception:
            return False

    def load_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Load preset parameters.

        Args:
            name: Preset name

        Returns:
            Parameters dict or None if not found
        """
        # Check factory presets first
        if name in self.FACTORY_PRESETS:
            return self.FACTORY_PRESETS[name].copy()

        # Try to load from file
        filename = self._sanitize_filename(name) + '.json'
        filepath = self._preset_dir / filename

        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('parameters', {})
            except Exception:
                pass

        return None

    def load_preset_full(self, name: str) -> Optional[Preset]:
        """Load full preset with metadata.

        Args:
            name: Preset name

        Returns:
            Preset object or None if not found
        """
        # Check factory presets
        if name in self.FACTORY_PRESETS:
            return Preset(
                name=name,
                parameters=self.FACTORY_PRESETS[name].copy(),
                author="Factory",
                category="factory"
            )

        # Try to load from file
        filename = self._sanitize_filename(name) + '.json'
        filepath = self._preset_dir / filename

        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return Preset.from_dict(data)
            except Exception:
                pass

        return None

    def delete_preset(self, name: str) -> bool:
        """Delete a user preset.

        Args:
            name: Preset name

        Returns:
            True if deleted, False if not found or factory preset
        """
        # Cannot delete factory presets
        if name in self.FACTORY_PRESETS:
            return False

        filename = self._sanitize_filename(name) + '.json'
        filepath = self._preset_dir / filename

        if filepath.exists():
            try:
                filepath.unlink()
                return True
            except Exception:
                pass

        return False

    def list_presets(self, include_factory: bool = True) -> List[str]:
        """List all available preset names.

        Args:
            include_factory: Include factory presets

        Returns:
            List of preset names
        """
        presets = []

        # Add factory presets
        if include_factory:
            presets.extend(sorted(self.FACTORY_PRESETS.keys()))

        # Add user presets
        for filepath in self._preset_dir.glob('*.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    name = data.get('name', filepath.stem)
                    if name not in presets:
                        presets.append(name)
            except Exception:
                continue

        return presets

    def list_presets_by_category(
        self,
        include_factory: bool = True
    ) -> Dict[str, List[str]]:
        """List presets organized by category.

        Args:
            include_factory: Include factory presets

        Returns:
            Dict mapping category to list of preset names
        """
        result = {cat: [] for cat in self.CATEGORIES}

        # Add factory presets
        if include_factory:
            for name in self.FACTORY_PRESETS:
                result['uncategorized'].append(name)

        # Add user presets
        for filepath in self._preset_dir.glob('*.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    name = data.get('name', filepath.stem)
                    category = data.get('category', 'uncategorized')
                    if category not in result:
                        category = 'uncategorized'
                    result[category].append(name)
            except Exception:
                continue

        # Remove empty categories
        return {k: v for k, v in result.items() if v}

    def preset_exists(self, name: str) -> bool:
        """Check if preset exists.

        Args:
            name: Preset name

        Returns:
            True if preset exists
        """
        if name in self.FACTORY_PRESETS:
            return True

        filename = self._sanitize_filename(name) + '.json'
        filepath = self._preset_dir / filename
        return filepath.exists()

    def is_factory_preset(self, name: str) -> bool:
        """Check if preset is a factory preset.

        Args:
            name: Preset name

        Returns:
            True if factory preset
        """
        return name in self.FACTORY_PRESETS

    def get_factory_preset_names(self) -> List[str]:
        """Get list of factory preset names.

        Returns:
            List of factory preset names
        """
        return list(self.FACTORY_PRESETS.keys())

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize preset name for use as filename.

        Args:
            name: Preset name

        Returns:
            Safe filename (without extension)
        """
        # Replace unsafe characters
        safe = name.lower()
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ']:
            safe = safe.replace(char, '_')

        # Remove consecutive underscores
        while '__' in safe:
            safe = safe.replace('__', '_')

        # Remove leading/trailing underscores
        safe = safe.strip('_')

        # Ensure not empty
        if not safe:
            safe = 'preset'

        return safe

    def import_preset(self, filepath: str) -> Optional[str]:
        """Import preset from external file.

        Args:
            filepath: Path to preset JSON file

        Returns:
            Imported preset name or None if failed
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            preset = Preset.from_dict(data)

            # Save to preset directory
            self.save_preset(
                name=preset.name,
                parameters=preset.parameters,
                author=preset.author,
                description=preset.description,
                category=preset.category,
                tags=preset.tags
            )

            return preset.name
        except Exception:
            return None

    def export_preset(self, name: str, filepath: str) -> bool:
        """Export preset to external file.

        Args:
            name: Preset name
            filepath: Output file path

        Returns:
            True if exported successfully
        """
        preset = self.load_preset_full(name)
        if preset is None:
            return False

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(preset.to_dict(), f, indent=2)
            return True
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"PresetStorage(dir='{self._preset_dir}')"
