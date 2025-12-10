# Application Controller - Wiring GUI to Synth Engine
"""
app_controller - Central coordinator for the Mini Synthesizer application.

Provides the glue between GUI, synthesizer engine, and audio output.
Handles parameter routing, preset management, and state coordination.
"""

import json
import os
from pathlib import Path
from queue import Queue
from threading import Lock
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, asdict
import time

import numpy as np

# Import synth engine components
from synth import (
    MiniSynth,
    AudioEngine,
    AudioConfig,
    Waveform,
    VoiceParameters
)

# BOLT-007: Import recording components
from recording import (
    Metronome,
    TimeSignature,
    AudioRecorder,
    RecordingState,
    FileExporter,
    ExportConfig
)

# BOLT-008: Import effects and songs
from effects import Reverb
# BOLT-009: Import additional effects
from effects import Delay, Chorus, Flanger, Distortion
from songs import Song, SongPlayer, get_all_songs, get_song_by_name


@dataclass
class SynthPreset:
    """Represents a synthesizer preset configuration."""

    name: str
    # Oscillator 1
    osc1_waveform: str = 'sawtooth'
    osc1_level: float = 0.7
    osc1_detune: float = 0.0
    osc1_octave: int = 0
    # Oscillator 2
    osc2_waveform: str = 'sawtooth'
    osc2_level: float = 0.5
    osc2_detune: float = 5.0
    osc2_octave: int = 0
    # Filter
    filter_cutoff: float = 2000.0
    filter_resonance: float = 0.3
    filter_env_amount: float = 0.0
    # Amp envelope
    amp_attack: float = 0.01
    amp_decay: float = 0.1
    amp_sustain: float = 0.7
    amp_release: float = 0.3
    # Filter envelope
    filter_attack: float = 0.01
    filter_decay: float = 0.2
    filter_sustain: float = 0.5
    filter_release: float = 0.2
    # LFO
    lfo_waveform: str = 'sine'
    lfo_rate: float = 5.0
    lfo_depth: float = 0.5
    lfo_to_pitch: float = 0.0
    lfo_to_filter: float = 0.0
    lfo_to_pw: float = 0.0
    # Master
    master_volume: float = 0.7

    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SynthPreset':
        """Create preset from dictionary."""
        return cls(**data)

    def save_to_file(self, filepath: str):
        """Save preset to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'SynthPreset':
        """Load preset from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


# Default presets
DEFAULT_PRESETS: Dict[str, SynthPreset] = {
    'Init': SynthPreset(name='Init'),
    'Fat Bass': SynthPreset(
        name='Fat Bass',
        osc1_waveform='sawtooth',
        osc1_level=0.8,
        osc2_waveform='square',
        osc2_level=0.6,
        osc2_detune=7.0,
        filter_cutoff=500.0,
        filter_resonance=0.5,
        filter_env_amount=0.7,
        amp_attack=0.005,
        amp_decay=0.15,
        amp_sustain=0.6,
        amp_release=0.2
    ),
    'Bright Lead': SynthPreset(
        name='Bright Lead',
        osc1_waveform='sawtooth',
        osc1_level=0.9,
        osc2_waveform='sawtooth',
        osc2_level=0.7,
        osc2_detune=10.0,
        filter_cutoff=8000.0,
        filter_resonance=0.4,
        filter_env_amount=0.3,
        amp_attack=0.01,
        amp_decay=0.1,
        amp_sustain=0.8,
        amp_release=0.3,
        lfo_rate=6.0,
        lfo_depth=0.3,
        lfo_to_pitch=0.1
    ),
    'Soft Pad': SynthPreset(
        name='Soft Pad',
        osc1_waveform='triangle',
        osc1_level=0.6,
        osc2_waveform='sine',
        osc2_level=0.5,
        osc2_detune=3.0,
        filter_cutoff=3000.0,
        filter_resonance=0.2,
        filter_env_amount=0.2,
        amp_attack=0.5,
        amp_decay=0.3,
        amp_sustain=0.7,
        amp_release=1.0,
        lfo_rate=2.0,
        lfo_depth=0.2,
        lfo_to_filter=0.3
    ),
    'Retro Square': SynthPreset(
        name='Retro Square',
        osc1_waveform='square',
        osc1_level=0.7,
        osc2_waveform='square',
        osc2_level=0.5,
        osc2_detune=12.0,
        osc2_octave=-1,
        filter_cutoff=1500.0,
        filter_resonance=0.6,
        filter_env_amount=0.6,
        amp_attack=0.01,
        amp_decay=0.2,
        amp_sustain=0.5,
        amp_release=0.4
    ),
    'Ethereal Strings': SynthPreset(
        name='Ethereal Strings',
        osc1_waveform='sawtooth',
        osc1_level=0.5,
        osc1_detune=-7.0,
        osc2_waveform='sawtooth',
        osc2_level=0.5,
        osc2_detune=7.0,
        filter_cutoff=2500.0,
        filter_resonance=0.15,
        filter_env_amount=0.25,
        amp_attack=0.8,
        amp_decay=0.4,
        amp_sustain=0.85,
        amp_release=1.5,
        lfo_rate=0.3,
        lfo_depth=0.35,
        lfo_to_pitch=0.05,
        lfo_to_filter=0.2
    ),
    'Plucky Keys': SynthPreset(
        name='Plucky Keys',
        osc1_waveform='triangle',
        osc1_level=0.8,
        osc2_waveform='sine',
        osc2_level=0.4,
        osc2_octave=1,
        filter_cutoff=4000.0,
        filter_resonance=0.25,
        filter_env_amount=0.6,
        amp_attack=0.002,
        amp_decay=0.35,
        amp_sustain=0.3,
        amp_release=0.4
    ),
    'Warm Organ': SynthPreset(
        name='Warm Organ',
        osc1_waveform='sine',
        osc1_level=0.7,
        osc2_waveform='sine',
        osc2_level=0.5,
        osc2_octave=1,
        filter_cutoff=2000.0,
        filter_resonance=0.1,
        filter_env_amount=0.1,
        amp_attack=0.02,
        amp_decay=0.05,
        amp_sustain=0.9,
        amp_release=0.15,
        lfo_rate=6.5,
        lfo_depth=0.2,
        lfo_to_pitch=0.08
    ),
    'Acid Squelch': SynthPreset(
        name='Acid Squelch',
        osc1_waveform='sawtooth',
        osc1_level=0.9,
        osc1_octave=-1,
        osc2_waveform='square',
        osc2_level=0.3,
        osc2_octave=-1,
        filter_cutoff=500.0,
        filter_resonance=0.85,
        filter_env_amount=0.9,
        amp_attack=0.001,
        amp_decay=0.25,
        amp_sustain=0.0,
        amp_release=0.1
    ),
    'Cosmic Bell': SynthPreset(
        name='Cosmic Bell',
        osc1_waveform='triangle',
        osc1_level=0.6,
        osc1_octave=1,
        osc2_waveform='sine',
        osc2_level=0.7,
        osc2_detune=12.0,
        osc2_octave=2,
        filter_cutoff=6000.0,
        filter_resonance=0.35,
        filter_env_amount=0.4,
        amp_attack=0.001,
        amp_decay=1.5,
        amp_sustain=0.0,
        amp_release=2.0,
        lfo_rate=0.2,
        lfo_depth=0.25,
        lfo_to_pitch=0.02,
        lfo_to_filter=0.15
    ),
}


class ParameterQueue:
    """Thread-safe queue for GUI->Audio parameter changes."""

    def __init__(self, maxsize: int = 256):
        """Initialize parameter queue."""
        self._queue: Queue = Queue(maxsize=maxsize)

    def put(self, name: str, value: Any) -> bool:
        """
        Queue a parameter change (non-blocking).

        Args:
            name: Parameter name
            value: Parameter value

        Returns:
            True if queued successfully, False if queue full
        """
        try:
            self._queue.put_nowait((name, value))
            return True
        except Exception:
            return False  # Queue full, drop update

    def get_all(self) -> List[tuple]:
        """
        Drain all pending changes.

        Returns:
            List of (name, value) tuples
        """
        changes = []
        while not self._queue.empty():
            try:
                changes.append(self._queue.get_nowait())
            except Exception:
                break
        return changes


class AppController:
    """Central coordinator for the Mini Synthesizer application."""

    # Waveform string to enum mapping
    WAVEFORM_MAP = {
        'sine': Waveform.SINE,
        'sawtooth': Waveform.SAWTOOTH,
        'square': Waveform.SQUARE,
        'triangle': Waveform.TRIANGLE,
        'pulse': Waveform.PULSE
    }

    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 512,
        max_voices: int = 8,
        presets_dir: Optional[str] = None
    ):
        """
        Initialize application controller.

        Args:
            sample_rate: Audio sample rate in Hz
            buffer_size: Audio buffer size in samples
            max_voices: Maximum polyphony
            presets_dir: Directory for preset files
        """
        self._sample_rate = sample_rate
        self._buffer_size = buffer_size
        self._max_voices = max_voices
        self._presets_dir = presets_dir or './presets'

        # Create synthesizer
        self._synth = MiniSynth(
            sample_rate=sample_rate,
            max_voices=max_voices
        )

        # Track current parameter values for batched synth updates
        self._current_params = {
            'osc1_waveform': Waveform.SAWTOOTH,
            'osc1_level': 0.7,
            'osc2_waveform': Waveform.SAWTOOTH,
            'osc2_level': 0.5,
            'osc2_detune': 5.0,
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
            'lfo_waveform': Waveform.SINE,
            'lfo_rate': 5.0,
            'lfo_depth': 0.5,
            'lfo_to_pitch': 0.0,
            'lfo_to_filter': 0.0,
            'lfo_to_pw': 0.0,
        }

        # Create audio engine
        self._audio_config = AudioConfig(
            sample_rate=sample_rate,
            buffer_size=buffer_size,
            channels=1
        )
        self._engine = AudioEngine(self._audio_config)

        # Parameter queue for thread-safe GUI->Audio communication
        self._param_queue = ParameterQueue()

        # Display buffer for visualization (double-buffered with atomic swap)
        # Audio thread always writes, GUI reads from ready buffer
        self._display_buffer = np.zeros(buffer_size, dtype=np.float32)
        self._display_buffer_ready = np.zeros(buffer_size, dtype=np.float32)
        self._display_lock = Lock()
        self._display_samples_count = 0

        # State tracking
        self._running = False
        self._current_preset_name = 'Init'

        # Voice change callback
        self._voice_change_callback: Optional[Callable[[int], None]] = None

        # BOLT-007: Metronome
        self._metronome = Metronome(
            bpm=120,
            sample_rate=sample_rate,
            volume=0.5
        )
        self._metronome_beat_callback: Optional[Callable[[int, bool], None]] = None

        # BOLT-007: Recorder
        self._recorder = AudioRecorder(
            sample_rate=sample_rate
        )

        # BOLT-007: File exporter
        self._exporter = FileExporter(
            default_config=ExportConfig(
                sample_rate=sample_rate,
                bit_depth=16,
                normalize=True
            )
        )

        # BOLT-008: Reverb effect
        self._reverb = Reverb(sample_rate=sample_rate)
        self._reverb.enabled = False  # Off by default

        # BOLT-009: Additional effects (chain order: Distortion -> Chorus -> Delay -> Reverb)
        self._distortion = Distortion(sample_rate=sample_rate)
        self._distortion.enabled = False  # Off by default

        self._chorus = Chorus(sample_rate=sample_rate)
        self._chorus.enabled = False  # Off by default

        self._delay = Delay(sample_rate=sample_rate)
        self._delay.enabled = False  # Off by default

        self._flanger = Flanger(sample_rate=sample_rate)
        self._flanger.enabled = False  # Off by default

        # BOLT-008: Song player
        self._song_player = SongPlayer(
            on_note_on=self._on_song_note_on,
            on_note_off=self._on_song_note_off,
            on_progress=self._on_song_progress,
            on_complete=self._on_song_complete,
            on_preset_change=self._on_song_preset_change
        )
        self._song_note_on_callback: Optional[Callable[[int, int], None]] = None
        self._song_note_off_callback: Optional[Callable[[int], None]] = None
        self._song_progress_callback: Optional[Callable[[float, float], None]] = None
        self._song_complete_callback: Optional[Callable[[], None]] = None

        # Set up audio callback
        self._engine.set_callback(self._audio_callback)

    def _audio_callback(self, num_samples: int) -> np.ndarray:
        """
        Audio callback function - called from audio thread.

        Args:
            num_samples: Number of samples to generate

        Returns:
            Audio buffer
        """
        # Process pending parameter changes
        changes = self._param_queue.get_all()
        for name, value in changes:
            self._apply_parameter(name, value)

        # Generate synth audio
        output = self._synth.generate(num_samples)

        # BOLT-007: Mix in metronome if running
        if self._metronome.is_running:
            metronome_audio = self._metronome.generate(num_samples)
            output = output + metronome_audio

        # BOLT-009: Apply effects chain (Distortion -> Chorus -> Delay -> Reverb)
        if self._distortion.enabled:
            output = self._distortion.process(output)
        if self._chorus.enabled:
            output = self._chorus.process(output)
        if self._delay.enabled:
            output = self._delay.process(output)
        if self._flanger.enabled:
            output = self._flanger.process(output)
        # BOLT-008: Apply reverb effect (last in chain)
        if self._reverb.enabled:
            output = self._reverb.process(output)

        # BOLT-007: Capture audio for recording
        if self._recorder.is_recording or self._recorder.is_armed:
            self._recorder.add_samples(output)

        # Always copy to display buffer for visualization
        # Use double-buffer: write to main buffer, swap to ready when GUI reads
        self._display_buffer[:len(output)] = output
        self._display_samples_count = len(output)

        return output

    def _apply_parameter(self, name: str, value: Any):
        """
        Apply a parameter change to the synthesizer.

        Args:
            name: Parameter name
            value: Parameter value
        """
        # Handle waveform parameters specially
        if name.endswith('_waveform'):
            if isinstance(value, str):
                value = self.WAVEFORM_MAP.get(value, Waveform.SAWTOOTH)

        # Route to appropriate synth method
        if name == 'master_volume':
            self._synth.master_volume = float(value)

        elif name.startswith('osc1_'):
            param = name.replace('osc1_', '')
            self._apply_oscillator_param(1, param, value)

        elif name.startswith('osc2_'):
            param = name.replace('osc2_', '')
            self._apply_oscillator_param(2, param, value)

        elif name.startswith('filter_') and not name.startswith('filter_attack'):
            param = name.replace('filter_', '')
            if param in ['cutoff', 'resonance', 'env_amount']:
                self._current_params[name] = float(value)
                self._synth.set_filter(
                    cutoff=self._current_params['filter_cutoff'],
                    resonance=self._current_params['filter_resonance'],
                    env_amount=self._current_params['filter_env_amount']
                )
            elif param in ['attack', 'decay', 'sustain', 'release']:
                # This is filter envelope, handled below
                pass

        elif name.startswith('amp_'):
            param = name.replace('amp_', '')
            self._apply_envelope_param('amp', param, value)

        elif name.startswith('filter_'):
            # Filter envelope parameters
            param = name.replace('filter_', '')
            if param in ['attack', 'decay', 'sustain', 'release']:
                self._apply_envelope_param('filter', param, value)

        elif name.startswith('lfo_'):
            param = name.replace('lfo_', '')
            self._apply_lfo_param(param, value)

    def _apply_oscillator_param(self, osc_num: int, param: str, value: Any):
        """Apply oscillator parameter change."""
        # Track the param
        key = f'osc{osc_num}_{param}'
        if param == 'waveform':
            if isinstance(value, str):
                value = self.WAVEFORM_MAP.get(value, Waveform.SAWTOOTH)
        self._current_params[key] = value

        if osc_num == 1:
            if param == 'waveform':
                self._synth.set_oscillator1(
                    waveform=self._current_params['osc1_waveform'],
                    level=self._current_params['osc1_level']
                )
            elif param == 'level':
                self._synth.set_oscillator1(
                    waveform=self._current_params['osc1_waveform'],
                    level=float(value)
                )
            elif param == 'detune':
                pass  # OSC1 detune not typically used
            elif param == 'octave':
                pass  # Octave shift handled differently
        else:
            if param == 'waveform':
                self._synth.set_oscillator2(
                    waveform=self._current_params['osc2_waveform'],
                    level=self._current_params['osc2_level'],
                    detune=self._current_params['osc2_detune']
                )
            elif param == 'level':
                self._synth.set_oscillator2(
                    waveform=self._current_params['osc2_waveform'],
                    level=float(value),
                    detune=self._current_params['osc2_detune']
                )
            elif param == 'detune':
                self._synth.set_oscillator2(
                    waveform=self._current_params['osc2_waveform'],
                    level=self._current_params['osc2_level'],
                    detune=float(value)
                )
            elif param == 'octave':
                pass  # Octave shift handled differently

    def _apply_envelope_param(self, env_type: str, param: str, value: Any):
        """Apply envelope parameter change."""
        # Update tracked param
        key = f'{env_type}_{param}'
        self._current_params[key] = float(value)

        # Call synth with all envelope params
        if env_type == 'amp':
            self._synth.set_amp_envelope(
                attack=self._current_params['amp_attack'],
                decay=self._current_params['amp_decay'],
                sustain=self._current_params['amp_sustain'],
                release=self._current_params['amp_release']
            )
        else:
            self._synth.set_filter_envelope(
                attack=self._current_params['filter_attack'],
                decay=self._current_params['filter_decay'],
                sustain=self._current_params['filter_sustain'],
                release=self._current_params['filter_release']
            )

    def _apply_lfo_param(self, param: str, value: Any):
        """Apply LFO parameter change."""
        key = f'lfo_{param}'

        if param == 'waveform':
            if isinstance(value, str):
                value = self.WAVEFORM_MAP.get(value, Waveform.SINE)
            self._current_params[key] = value
        elif param in ['rate', 'depth']:
            self._current_params[key] = float(value)
        elif param in ['to_pitch', 'to_filter', 'to_pw']:
            # LFO routing amounts - track but not all are supported by synth
            self._current_params[key] = float(value)

        # Apply all LFO params at once
        self._synth.set_lfo(
            rate=self._current_params['lfo_rate'],
            depth=self._current_params['lfo_depth'],
            waveform=self._current_params['lfo_waveform']
        )

    # Public API

    def start(self):
        """Start audio engine and begin processing."""
        if not self._running:
            self._engine.start()
            self._running = True

    def stop(self):
        """Stop audio engine and cleanup."""
        if self._running:
            self._engine.stop()
            self._running = False

    @property
    def is_running(self) -> bool:
        """Check if audio engine is running."""
        return self._running

    def note_on(self, note: int, velocity: int = 100):
        """
        Trigger a note.

        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (0-127)
        """
        self._synth.note_on(note, velocity)

        # Notify voice change
        if self._voice_change_callback:
            state = self._synth.get_state()
            self._voice_change_callback(state.active_voices)

    def note_off(self, note: int):
        """
        Release a note.

        Args:
            note: MIDI note number (0-127)
        """
        self._synth.note_off(note)

        # Notify voice change (after a short delay for release)
        if self._voice_change_callback:
            state = self._synth.get_state()
            self._voice_change_callback(state.active_voices)

    def all_notes_off(self):
        """Release all notes immediately (panic)."""
        self._synth.all_notes_off()

        if self._voice_change_callback:
            self._voice_change_callback(0)

    def set_parameter(self, name: str, value: Any):
        """
        Set a synth parameter (thread-safe).

        Args:
            name: Parameter name
            value: Parameter value
        """
        self._param_queue.put(name, value)

    def get_display_buffer(self) -> np.ndarray:
        """
        Get current audio buffer for visualization.

        Returns:
            Copy of the display buffer
        """
        # Copy from display buffer (audio thread writes directly, no lock needed
        # for single writer/single reader on numpy array with atomic assignment)
        return self._display_buffer[:self._display_samples_count].copy()

    def get_active_voice_count(self) -> int:
        """Get number of currently active voices."""
        state = self._synth.get_state()
        return state.active_voices

    def set_voice_change_callback(self, callback: Callable[[int], None]):
        """Set callback for voice count changes."""
        self._voice_change_callback = callback

    # Preset management

    def load_preset(self, name_or_path: str) -> Optional[Dict[str, Any]]:
        """
        Load a preset by name or file path.

        Args:
            name_or_path: Preset name or file path

        Returns:
            Dictionary of preset parameters if loaded successfully, None otherwise
        """
        try:
            if name_or_path in DEFAULT_PRESETS:
                preset = DEFAULT_PRESETS[name_or_path]
            elif os.path.exists(name_or_path):
                preset = SynthPreset.load_from_file(name_or_path)
            else:
                return None

            self._apply_preset(preset)
            self._current_preset_name = preset.name
            # Return the preset values so GUI can be updated
            params = preset.to_dict()
            del params['name']
            return params
        except Exception as e:
            print(f"Error loading preset: {e}")
            return None

    def save_preset(self, name: str, filepath: Optional[str] = None) -> bool:
        """
        Save current settings as preset.

        Args:
            name: Preset name
            filepath: Optional file path (uses presets_dir if not specified)

        Returns:
            True if saved successfully
        """
        try:
            preset = self._create_preset_from_current(name)

            if filepath is None:
                os.makedirs(self._presets_dir, exist_ok=True)
                filepath = os.path.join(self._presets_dir, f"{name.lower().replace(' ', '_')}.json")

            preset.save_to_file(filepath)
            self._current_preset_name = name
            return True
        except Exception as e:
            print(f"Error saving preset: {e}")
            return False

    def _apply_preset(self, preset: SynthPreset):
        """Apply preset settings to synthesizer."""
        params = preset.to_dict()
        del params['name']  # Don't apply name as parameter

        for name, value in params.items():
            self.set_parameter(name, value)

    def _create_preset_from_current(self, name: str) -> SynthPreset:
        """Create preset from current synth settings."""
        # This would ideally read back from synth state
        # For now, return a default preset with the given name
        return SynthPreset(name=name)

    def get_preset_list(self) -> List[str]:
        """Get list of available preset names."""
        presets = list(DEFAULT_PRESETS.keys())

        # Add presets from directory
        if os.path.exists(self._presets_dir):
            for f in os.listdir(self._presets_dir):
                if f.endswith('.json'):
                    presets.append(f.replace('.json', '').replace('_', ' ').title())

        return presets

    @property
    def current_preset_name(self) -> str:
        """Get current preset name."""
        return self._current_preset_name

    @property
    def sample_rate(self) -> int:
        """Get audio sample rate."""
        return self._sample_rate

    @property
    def buffer_size(self) -> int:
        """Get audio buffer size."""
        return self._buffer_size

    @property
    def max_voices(self) -> int:
        """Get maximum voice count."""
        return self._max_voices

    # BOLT-007: Metronome API

    def start_metronome(self):
        """Start the metronome."""
        self._metronome.start()

    def stop_metronome(self):
        """Stop the metronome."""
        self._metronome.stop()

    def set_metronome_bpm(self, bpm: float):
        """Set metronome tempo.

        Args:
            bpm: Beats per minute (20-300)
        """
        self._metronome.bpm = bpm

    def set_metronome_time_signature(self, numerator: int, denominator: int):
        """Set metronome time signature.

        Args:
            numerator: Beats per measure
            denominator: Note value for one beat
        """
        self._metronome.time_signature = TimeSignature(numerator, denominator)

    def set_metronome_volume(self, volume: float):
        """Set metronome volume.

        Args:
            volume: Volume level (0.0-1.0)
        """
        self._metronome.volume = volume

    def set_metronome_beat_callback(self, callback: Callable[[int, bool], None]):
        """Set callback for metronome beat events.

        Args:
            callback: Function(beat_num, is_downbeat) called on each beat
        """
        self._metronome_beat_callback = callback
        self._metronome.set_on_beat_callback(callback)

    @property
    def metronome_bpm(self) -> float:
        """Get current metronome BPM."""
        return self._metronome.bpm

    @property
    def metronome_is_running(self) -> bool:
        """Check if metronome is running."""
        return self._metronome.is_running

    # BOLT-007: Recording API

    def start_recording(self):
        """Start audio recording."""
        self._recorder.start()

    def stop_recording(self):
        """Stop audio recording."""
        self._recorder.stop()

    def pause_recording(self):
        """Pause audio recording."""
        self._recorder.pause()

    def resume_recording(self):
        """Resume audio recording."""
        self._recorder.resume()

    def arm_recording(self):
        """Arm for recording (auto-start on input)."""
        self._recorder.arm()

    def clear_recording(self):
        """Clear current recording."""
        self._recorder.clear()

    def undo_recording(self) -> bool:
        """Undo last recording.

        Returns:
            True if undo was performed
        """
        return self._recorder.undo()

    def get_recording_audio(self) -> np.ndarray:
        """Get recorded audio data.

        Returns:
            Numpy array of recorded audio
        """
        return self._recorder.get_audio()

    def get_recording_duration(self) -> float:
        """Get recording duration in seconds."""
        return self._recorder.duration_seconds

    def get_recording_peak_level(self) -> float:
        """Get recording peak level (0.0-1.0)."""
        return self._recorder.peak_level

    @property
    def recording_state(self) -> str:
        """Get current recording state as string."""
        return self._recorder.state.name

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recorder.is_recording

    @property
    def recording_has_data(self) -> bool:
        """Check if recording has data."""
        return self._recorder.duration_samples > 0

    @property
    def recording_can_undo(self) -> bool:
        """Check if undo is available."""
        return self._recorder.can_undo

    def set_recording_state_callback(self, callback: Callable[[RecordingState], None]):
        """Set callback for recording state changes.

        Args:
            callback: Function(new_state) called on state change
        """
        self._recorder.set_on_state_change(callback)

    # BOLT-007: Export API

    def export_wav(
        self,
        filepath: str,
        bit_depth: int = 16,
        normalize: bool = True,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> bool:
        """Export recorded audio to WAV file.

        Args:
            filepath: Output file path
            bit_depth: Output bit depth (16, 24, or 32)
            normalize: Whether to normalize audio
            progress_callback: Optional progress callback (0.0-1.0)

        Returns:
            True if export successful
        """
        audio = self._recorder.get_audio()
        if len(audio) == 0:
            return False

        try:
            config = ExportConfig(
                sample_rate=self._sample_rate,
                bit_depth=bit_depth,
                normalize=normalize
            )
            self._exporter.export_wav(audio, filepath, config, progress_callback)
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False

    def get_export_info(self) -> dict:
        """Get information about potential export.

        Returns:
            Dict with duration, estimated file size, etc.
        """
        audio = self._recorder.get_audio()
        return self._exporter.get_export_info(audio)

    # BOLT-008: Reverb API

    def set_reverb_enabled(self, enabled: bool):
        """Enable or disable reverb effect.

        Args:
            enabled: Whether reverb should be enabled
        """
        self._reverb.enabled = enabled

    def set_reverb_wet_dry(self, mix: float):
        """Set reverb wet/dry mix.

        Args:
            mix: Wet/dry mix (0.0 = dry, 1.0 = wet)
        """
        self._reverb.wet_dry = mix

    def set_reverb_room_size(self, size: float):
        """Set reverb room size.

        Args:
            size: Room size (0.0 = small, 1.0 = large)
        """
        self._reverb.room_size = size

    @property
    def reverb_enabled(self) -> bool:
        """Check if reverb is enabled."""
        return self._reverb.enabled

    @property
    def reverb_wet_dry(self) -> float:
        """Get reverb wet/dry mix."""
        return self._reverb.wet_dry

    @property
    def reverb_room_size(self) -> float:
        """Get reverb room size."""
        return self._reverb.room_size

    # BOLT-008: Song Player API

    def _on_song_note_on(self, note: int, velocity: int):
        """Handle song note on event."""
        # Play through synth
        self._synth.note_on(note, velocity)

        # Notify GUI for keyboard visualization
        if self._song_note_on_callback:
            self._song_note_on_callback(note, velocity)

    def _on_song_note_off(self, note: int):
        """Handle song note off event."""
        # Release from synth
        self._synth.note_off(note)

        # Notify GUI for keyboard visualization
        if self._song_note_off_callback:
            self._song_note_off_callback(note)

    def _on_song_progress(self, current: float, total: float):
        """Handle song progress update."""
        if self._song_progress_callback:
            self._song_progress_callback(current, total)

    def _on_song_complete(self):
        """Handle song completion."""
        if self._song_complete_callback:
            self._song_complete_callback()

    def _on_song_preset_change(self, preset_name: str):
        """Handle song preset change.

        Uses immediate application to avoid race condition with first note.
        """
        self._load_preset_immediate(preset_name)

    def _load_preset_immediate(self, name: str) -> bool:
        """Load preset via parameter queue for thread-safe application.

        Parameters are queued and will be applied by the audio thread
        in the next audio callback, ensuring no race conditions with
        the synth state.

        Args:
            name: Preset name

        Returns:
            True if preset was loaded successfully
        """
        if name not in DEFAULT_PRESETS:
            return False

        preset = DEFAULT_PRESETS[name]
        params = preset.to_dict()
        del params['name']

        # Queue parameters for thread-safe application by audio thread
        # The PRESET_SETTLE_DELAY in SongPlayer ensures notes don't play
        # until the audio callback has processed these queued parameters
        for param_name, value in params.items():
            self._param_queue.put(param_name, value)

        self._current_preset_name = preset.name
        return True

    def set_song_callbacks(
        self,
        on_note_on: Optional[Callable[[int, int], None]] = None,
        on_note_off: Optional[Callable[[int], None]] = None,
        on_progress: Optional[Callable[[float, float], None]] = None,
        on_complete: Optional[Callable[[], None]] = None
    ):
        """Set callbacks for song player events.

        Args:
            on_note_on: Called when song plays a note (note, velocity)
            on_note_off: Called when song releases a note (note)
            on_progress: Called periodically with progress (current, total)
            on_complete: Called when song finishes
        """
        self._song_note_on_callback = on_note_on
        self._song_note_off_callback = on_note_off
        self._song_progress_callback = on_progress
        self._song_complete_callback = on_complete

    def get_song_list(self) -> List[str]:
        """Get list of available song names.

        Returns:
            List of song names
        """
        songs = get_all_songs()
        return [song.name for song in songs]

    def load_song(self, song_name: str) -> bool:
        """Load a song by name.

        Args:
            song_name: Name of song to load

        Returns:
            True if song was loaded successfully
        """
        song = get_song_by_name(song_name)
        if song:
            self._song_player.load(song)
            return True
        return False

    def play_song(self):
        """Start or resume song playback."""
        self._song_player.play()

    def stop_song(self):
        """Stop song playback."""
        self._song_player.stop()

    def pause_song(self):
        """Pause song playback."""
        self._song_player.pause()

    def resume_song(self):
        """Resume paused song playback."""
        self._song_player.resume()

    @property
    def song_is_playing(self) -> bool:
        """Check if song is currently playing."""
        return self._song_player.is_playing

    @property
    def song_is_paused(self) -> bool:
        """Check if song is currently paused."""
        return self._song_player.is_paused

    def get_song_progress(self) -> tuple:
        """Get current song progress.

        Returns:
            Tuple of (current_position, total_duration) in seconds
        """
        return (
            self._song_player.current_position,
            self._song_player.total_duration
        )

    @property
    def current_song_name(self) -> Optional[str]:
        """Get name of currently loaded song."""
        song = self._song_player.current_song
        return song.name if song else None

    # BOLT-009: Delay API

    def set_delay_enabled(self, enabled: bool):
        """Enable or disable delay effect.

        Args:
            enabled: Whether delay should be enabled
        """
        self._delay.enabled = enabled

    def set_delay_time(self, time_ms: float):
        """Set delay time in milliseconds.

        Args:
            time_ms: Delay time (10-2000ms)
        """
        self._delay.delay_time_ms = time_ms

    def set_delay_feedback(self, feedback: float):
        """Set delay feedback.

        Args:
            feedback: Feedback amount (0.0-0.95)
        """
        self._delay.feedback = feedback

    def set_delay_wet_dry(self, mix: float):
        """Set delay wet/dry mix.

        Args:
            mix: Wet/dry mix (0.0-1.0)
        """
        self._delay.wet_dry = mix

    @property
    def delay_enabled(self) -> bool:
        """Check if delay is enabled."""
        return self._delay.enabled

    @property
    def delay_time_ms(self) -> float:
        """Get delay time in milliseconds."""
        return self._delay.delay_time_ms

    @property
    def delay_feedback(self) -> float:
        """Get delay feedback."""
        return self._delay.feedback

    @property
    def delay_wet_dry(self) -> float:
        """Get delay wet/dry mix."""
        return self._delay.wet_dry


    # BOLT-010: Flanger API

    def set_flanger_enabled(self, enabled: bool):
        """Enable or disable flanger effect.

        Args:
            enabled: Whether flanger should be enabled
        """
        self._flanger.enabled = enabled

    def set_flanger_rate(self, rate: float):
        """Set flanger LFO rate in Hz.

        Args:
            rate: LFO rate (0.1-5.0 Hz)
        """
        self._flanger.rate = rate

    def set_flanger_depth(self, depth: float):
        """Set flanger modulation depth.

        Args:
            depth: Modulation depth (0.0-1.0)
        """
        self._flanger.depth = depth

    def set_flanger_feedback(self, feedback: float):
        """Set flanger feedback.

        Args:
            feedback: Feedback amount (0.0-0.95)
        """
        self._flanger.feedback = feedback

    def set_flanger_wet_dry(self, mix: float):
        """Set flanger wet/dry mix.

        Args:
            mix: Wet/dry mix (0.0-1.0)
        """
        self._flanger.wet_dry = mix

    @property
    def flanger_enabled(self) -> bool:
        """Check if flanger is enabled."""
        return self._flanger.enabled

    @property
    def flanger_rate(self) -> float:
        """Get flanger LFO rate."""
        return self._flanger.rate

    @property
    def flanger_depth(self) -> float:
        """Get flanger modulation depth."""
        return self._flanger.depth

    @property
    def flanger_feedback(self) -> float:
        """Get flanger feedback."""
        return self._flanger.feedback

    @property
    def flanger_wet_dry(self) -> float:
        """Get flanger wet/dry mix."""
        return self._flanger.wet_dry

    # BOLT-009: Chorus API

    def set_chorus_enabled(self, enabled: bool):
        """Enable or disable chorus effect.

        Args:
            enabled: Whether chorus should be enabled
        """
        self._chorus.enabled = enabled

    def set_chorus_rate(self, rate: float):
        """Set chorus LFO rate.

        Args:
            rate: LFO rate in Hz (0.1-5.0)
        """
        self._chorus.rate = rate

    def set_chorus_depth(self, depth: float):
        """Set chorus modulation depth.

        Args:
            depth: Modulation depth (0.0-1.0)
        """
        self._chorus.depth = depth

    def set_chorus_voices(self, voices: int):
        """Set number of chorus voices.

        Args:
            voices: Number of voices (2-4)
        """
        self._chorus.voices = voices

    def set_chorus_wet_dry(self, mix: float):
        """Set chorus wet/dry mix.

        Args:
            mix: Wet/dry mix (0.0-1.0)
        """
        self._chorus.wet_dry = mix

    @property
    def chorus_enabled(self) -> bool:
        """Check if chorus is enabled."""
        return self._chorus.enabled

    @property
    def chorus_rate(self) -> float:
        """Get chorus LFO rate."""
        return self._chorus.rate

    @property
    def chorus_depth(self) -> float:
        """Get chorus modulation depth."""
        return self._chorus.depth

    @property
    def chorus_voices(self) -> int:
        """Get number of chorus voices."""
        return self._chorus.voices

    @property
    def chorus_wet_dry(self) -> float:
        """Get chorus wet/dry mix."""
        return self._chorus.wet_dry

    # BOLT-009: Distortion API

    def set_distortion_enabled(self, enabled: bool):
        """Enable or disable distortion effect.

        Args:
            enabled: Whether distortion should be enabled
        """
        self._distortion.enabled = enabled

    def set_distortion_drive(self, drive: float):
        """Set distortion drive.

        Args:
            drive: Drive amount (1.0-20.0)
        """
        self._distortion.drive = drive

    def set_distortion_tone(self, tone: float):
        """Set distortion tone.

        Args:
            tone: Tone (0.0 = dark, 1.0 = bright)
        """
        self._distortion.tone = tone

    def set_distortion_mode(self, mode: str):
        """Set distortion waveshaping mode.

        Args:
            mode: Mode ('soft', 'hard', 'tube')
        """
        self._distortion.mode = mode

    def set_distortion_mix(self, mix: float):
        """Set distortion wet/dry mix.

        Args:
            mix: Wet/dry mix (0.0-1.0)
        """
        self._distortion.mix = mix

    @property
    def distortion_enabled(self) -> bool:
        """Check if distortion is enabled."""
        return self._distortion.enabled

    @property
    def distortion_drive(self) -> float:
        """Get distortion drive."""
        return self._distortion.drive

    @property
    def distortion_tone(self) -> float:
        """Get distortion tone."""
        return self._distortion.tone

    @property
    def distortion_mode(self) -> str:
        """Get distortion mode."""
        return self._distortion.mode

    @property
    def distortion_mix(self) -> float:
        """Get distortion mix."""
        return self._distortion.mix
