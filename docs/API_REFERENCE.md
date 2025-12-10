# WinMiniSynth API Reference

## Overview

This document provides detailed API documentation for WinMiniSynth modules. It covers the synthesis engine, effects processing, GUI components, recording system, and utilities.

## Table of Contents

1. [Synth Module](#synth-module)
2. [Effects Module](#effects-module)
3. [GUI Module](#gui-module)
4. [Recording Module](#recording-module)
5. [Songs Module](#songs-module)
6. [Visualization Module](#visualization-module)
7. [Application Controller](#application-controller)

---

## Synth Module

The `synth` module contains core audio synthesis components.

### synth.Synthesizer

The main synthesizer class managing voices, filter, and audio generation.

```python
from synth import Synthesizer

class Synthesizer:
    """8-voice polyphonic synthesizer with dual oscillators and filter."""

    def __init__(self, sample_rate: int = 44100, num_voices: int = 8):
        """Initialize synthesizer.

        Args:
            sample_rate: Audio sample rate in Hz
            num_voices: Maximum polyphony (default: 8)
        """

    def note_on(self, note: int, velocity: int = 127) -> None:
        """Trigger a note.

        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (0-127)
        """

    def note_off(self, note: int) -> None:
        """Release a note.

        Args:
            note: MIDI note number to release
        """

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate audio samples.

        Args:
            num_samples: Number of samples to generate

        Returns:
            np.ndarray: Audio samples (float32, -1.0 to 1.0)
        """

    def set_parameter(self, name: str, value: Any) -> None:
        """Set a synthesis parameter.

        Args:
            name: Parameter name (see Parameters section)
            value: New parameter value
        """

    def get_parameter(self, name: str) -> Any:
        """Get current parameter value.

        Args:
            name: Parameter name

        Returns:
            Current parameter value
        """

    def get_parameters(self) -> Dict[str, Any]:
        """Get all parameters as dictionary."""

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Set multiple parameters from dictionary."""

    def all_notes_off(self) -> None:
        """Release all playing notes (PANIC)."""

    @property
    def active_voice_count(self) -> int:
        """Number of currently active voices."""
```

#### Synthesizer Parameters

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `osc1_waveform` | str | sine, sawtooth, square, triangle, pulse | OSC1 waveform |
| `osc1_level` | float | 0.0-1.0 | OSC1 volume |
| `osc1_detune` | float | -50.0 to 50.0 | OSC1 detune (cents) |
| `osc1_octave` | int | -2 to 2 | OSC1 octave shift |
| `osc2_waveform` | str | Same as OSC1 | OSC2 waveform |
| `osc2_level` | float | 0.0-1.0 | OSC2 volume |
| `osc2_detune` | float | -50.0 to 50.0 | OSC2 detune (cents) |
| `osc2_octave` | int | -2 to 2 | OSC2 octave shift |
| `filter_cutoff` | float | 20.0-20000.0 | Filter cutoff (Hz) |
| `filter_resonance` | float | 0.0-0.95 | Filter resonance |
| `filter_env_amount` | float | 0.0-1.0 | Filter envelope depth |
| `amp_attack` | float | 0.001-10.0 | Amp envelope attack (sec) |
| `amp_decay` | float | 0.001-10.0 | Amp envelope decay (sec) |
| `amp_sustain` | float | 0.0-1.0 | Amp envelope sustain level |
| `amp_release` | float | 0.001-10.0 | Amp envelope release (sec) |
| `filter_attack` | float | 0.001-10.0 | Filter envelope attack |
| `filter_decay` | float | 0.001-10.0 | Filter envelope decay |
| `filter_sustain` | float | 0.0-1.0 | Filter envelope sustain |
| `filter_release` | float | 0.001-10.0 | Filter envelope release |
| `lfo_waveform` | str | sine, sawtooth, square, triangle, pulse | LFO waveform |
| `lfo_rate` | float | 0.1-50.0 | LFO frequency (Hz) |
| `lfo_depth` | float | 0.0-1.0 | LFO depth |
| `lfo_to_pitch` | float | 0.0-1.0 | LFO to pitch amount |
| `lfo_to_filter` | float | 0.0-1.0 | LFO to filter amount |
| `lfo_to_pw` | float | 0.0-1.0 | LFO to pulse width |
| `master_volume` | float | 0.0-1.0 | Master output volume |

---

### synth.Voice

Individual synthesizer voice managing oscillators and envelopes.

```python
from synth import Voice

class Voice:
    """Single voice with dual oscillators, filter, and envelopes."""

    def __init__(self, sample_rate: int = 44100):
        """Initialize voice."""

    def note_on(self, note: int, velocity: int) -> None:
        """Trigger voice with note and velocity."""

    def note_off(self) -> None:
        """Release voice (enter release stage)."""

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate voice output samples."""

    @property
    def is_active(self) -> bool:
        """Whether voice is currently producing sound."""

    @property
    def note(self) -> int:
        """Currently playing MIDI note."""

    @property
    def velocity(self) -> int:
        """Note velocity (0-127)."""
```

---

### synth.Oscillator

Waveform generator with multiple wave shapes.

```python
from synth import Oscillator, Waveform

class Waveform(Enum):
    """Available oscillator waveforms."""
    SINE = "sine"
    SAWTOOTH = "sawtooth"
    SQUARE = "square"
    TRIANGLE = "triangle"
    PULSE = "pulse"

class Oscillator:
    """Audio oscillator with multiple waveforms.

    Attributes:
        sample_rate: Audio sample rate
        waveform: Current waveform type
        frequency: Oscillator frequency (Hz)
        phase: Current phase (0.0-1.0)
        pulse_width: Pulse wave duty cycle (0.0-1.0)
    """

    def __init__(self, sample_rate: int = 44100):
        """Initialize oscillator."""

    def generate(self, num_samples: int,
                 freq_mod: Optional[np.ndarray] = None,
                 pw_mod: Optional[np.ndarray] = None) -> np.ndarray:
        """Generate waveform samples.

        Args:
            num_samples: Number of samples to generate
            freq_mod: Optional frequency modulation array
            pw_mod: Optional pulse width modulation array

        Returns:
            np.ndarray: Generated samples (float32)
        """

    def reset_phase(self) -> None:
        """Reset oscillator phase to zero."""

    @property
    def waveform(self) -> Waveform:
        """Current waveform type."""

    @waveform.setter
    def waveform(self, value: Waveform) -> None:
        """Set waveform type."""

    @property
    def frequency(self) -> float:
        """Oscillator frequency in Hz."""

    @frequency.setter
    def frequency(self, value: float) -> None:
        """Set frequency (clamped to valid range)."""
```

---

### synth.MoogFilter

4-pole Moog-style ladder filter implementation.

```python
from synth import MoogFilter

class MoogFilter:
    """Moog ladder filter (4-pole lowpass).

    Implements the classic Moog transistor ladder filter
    with resonance (self-oscillation) capability.

    Attributes:
        sample_rate: Audio sample rate
        cutoff: Cutoff frequency (Hz)
        resonance: Resonance (0.0-0.95)
    """

    def __init__(self, sample_rate: int = 44100):
        """Initialize filter."""

    def process(self, input_samples: np.ndarray,
                cutoff_mod: Optional[np.ndarray] = None) -> np.ndarray:
        """Process samples through filter.

        Args:
            input_samples: Input audio samples
            cutoff_mod: Optional cutoff modulation array

        Returns:
            np.ndarray: Filtered samples
        """

    def reset(self) -> None:
        """Reset filter state."""

    @property
    def cutoff(self) -> float:
        """Cutoff frequency in Hz."""

    @cutoff.setter
    def cutoff(self, value: float) -> None:
        """Set cutoff (clamped 20-20000 Hz)."""

    @property
    def resonance(self) -> float:
        """Filter resonance (0.0-0.95)."""

    @resonance.setter
    def resonance(self, value: float) -> None:
        """Set resonance (clamped 0.0-0.95)."""
```

---

### synth.ADSREnvelope

Attack-Decay-Sustain-Release envelope generator.

```python
from synth import ADSREnvelope, EnvelopeStage

class EnvelopeStage(Enum):
    """Envelope stage enumeration."""
    IDLE = 0
    ATTACK = 1
    DECAY = 2
    SUSTAIN = 3
    RELEASE = 4

class ADSREnvelope:
    """ADSR envelope generator.

    Attributes:
        attack: Attack time in seconds
        decay: Decay time in seconds
        sustain: Sustain level (0.0-1.0)
        release: Release time in seconds
        stage: Current envelope stage
    """

    def __init__(self, sample_rate: int = 44100):
        """Initialize envelope."""

    def gate_on(self) -> None:
        """Trigger envelope (note on)."""

    def gate_off(self) -> None:
        """Release envelope (note off)."""

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate envelope samples.

        Args:
            num_samples: Number of samples to generate

        Returns:
            np.ndarray: Envelope values (0.0-1.0)
        """

    @property
    def stage(self) -> EnvelopeStage:
        """Current envelope stage."""

    @property
    def is_active(self) -> bool:
        """Whether envelope is active (not IDLE)."""

    @property
    def current_level(self) -> float:
        """Current envelope level."""
```

---

### synth.LFO

Low-frequency oscillator for modulation.

```python
from synth import LFO

class LFO:
    """Low-frequency oscillator for modulation.

    Attributes:
        frequency: LFO rate (0.1-50 Hz)
        waveform: LFO waveform type
        depth: Modulation depth (0.0-1.0)
    """

    MIN_FREQ = 0.1
    MAX_FREQ = 50.0

    def __init__(self, sample_rate: int = 44100):
        """Initialize LFO."""

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate bipolar modulation signal (-depth to +depth).

        Args:
            num_samples: Number of samples

        Returns:
            np.ndarray: Modulation values
        """

    def generate_unipolar(self, num_samples: int) -> np.ndarray:
        """Generate unipolar modulation signal (0 to depth).

        Args:
            num_samples: Number of samples

        Returns:
            np.ndarray: Modulation values (0.0 to depth)
        """

    def generate_sample(self) -> float:
        """Generate single modulation sample."""

    def reset_phase(self) -> None:
        """Reset LFO phase to zero."""
```

---

### synth.AudioEngine

Audio I/O management using sounddevice.

```python
from synth import AudioEngine, AudioConfig

@dataclass
class AudioConfig:
    """Audio configuration settings.

    Attributes:
        sample_rate: Sample rate in Hz (default: 44100)
        buffer_size: Buffer size in samples (default: 512)
        channels: Output channels (default: 1)
    """
    sample_rate: int = 44100
    buffer_size: int = 512
    channels: int = 1

    @property
    def latency_ms(self) -> float:
        """Audio latency in milliseconds."""

class AudioEngine:
    """Audio output engine using sounddevice.

    Attributes:
        config: Audio configuration
        is_running: Whether audio stream is active
    """

    def __init__(self, config: Optional[AudioConfig] = None):
        """Initialize audio engine."""

    def set_callback(self, callback: Callable[[int], np.ndarray]) -> None:
        """Set audio generation callback.

        The callback receives the number of samples to generate
        and must return a numpy array of float32 samples.

        Args:
            callback: Audio generation function
        """

    def start(self) -> None:
        """Start audio stream."""

    def stop(self) -> None:
        """Stop audio stream."""

    @property
    def is_running(self) -> bool:
        """Whether audio is currently running."""

    @property
    def underrun_count(self) -> int:
        """Number of buffer underruns detected."""

    def get_last_error(self) -> Optional[Exception]:
        """Get last error from audio callback."""
```

---

## Effects Module

The `effects` module contains audio effects processors.

### effects.Reverb

Schroeder reverb algorithm implementation.

```python
from effects import Reverb

class Reverb:
    """Reverb effect using Schroeder algorithm.

    Attributes:
        room_size: Room size (0.0-1.0)
        wet_dry: Wet/dry mix (0.0-1.0)
        enabled: Whether reverb is active
    """

    def __init__(self, sample_rate: int = 44100,
                 room_size: float = 0.5,
                 wet_dry: float = 0.3):
        """Initialize reverb."""

    def process(self, input_samples: np.ndarray) -> np.ndarray:
        """Process audio through reverb.

        Args:
            input_samples: Input audio

        Returns:
            np.ndarray: Processed audio
        """

    def reset(self) -> None:
        """Reset reverb state."""

    @property
    def room_size(self) -> float:
        """Room size (0.0-1.0)."""

    @property
    def wet_dry(self) -> float:
        """Wet/dry mix (0.0-1.0)."""

    @property
    def enabled(self) -> bool:
        """Whether reverb is enabled."""
```

---

### effects.Delay

Digital delay/echo effect.

```python
from effects import Delay

class Delay:
    """Digital delay effect with feedback.

    Attributes:
        delay_time_ms: Delay time in milliseconds (10-2000)
        feedback: Feedback amount (0.0-0.95)
        wet_dry: Wet/dry mix (0.0-1.0)
        enabled: Whether delay is active
    """

    MIN_DELAY_MS = 10
    MAX_DELAY_MS = 2000
    MAX_FEEDBACK = 0.95

    def __init__(self, sample_rate: int = 44100,
                 delay_time_ms: float = 300,
                 feedback: float = 0.4,
                 wet_dry: float = 0.3):
        """Initialize delay."""

    def process(self, input_samples: np.ndarray) -> np.ndarray:
        """Process audio through delay."""

    def reset(self) -> None:
        """Reset delay buffer."""

    def sync_to_tempo(self, bpm: float,
                      note_value: str = "1/4") -> float:
        """Calculate and set delay time from tempo.

        Args:
            bpm: Tempo in beats per minute
            note_value: Note value ("1/4", "1/8", "1/16", etc.)

        Returns:
            Calculated delay time in milliseconds
        """
```

---

### effects.Chorus

Multi-voice chorus effect.

```python
from effects import Chorus

class Chorus:
    """Chorus effect with LFO-modulated delays.

    Attributes:
        rate: LFO rate in Hz (0.1-5.0)
        depth: Modulation depth (0.0-1.0)
        voices: Number of chorus voices (2-4)
        wet_dry: Wet/dry mix (0.0-1.0)
        enabled: Whether chorus is active
    """

    def __init__(self, sample_rate: int = 44100,
                 rate: float = 0.5,
                 depth: float = 0.5,
                 voices: int = 3,
                 wet_dry: float = 0.3):
        """Initialize chorus."""

    def process(self, input_samples: np.ndarray) -> np.ndarray:
        """Process audio through chorus."""

    def reset(self) -> None:
        """Reset chorus state."""
```

---

### effects.Distortion

Waveshaping distortion effect.

```python
from effects import Distortion

class Distortion:
    """Distortion effect with multiple modes.

    Attributes:
        drive: Drive amount (1.0-20.0)
        tone: Tone control (0.0-1.0)
        mix: Wet/dry mix (0.0-1.0)
        mode: Distortion mode ('soft', 'hard', 'tube')
        enabled: Whether distortion is active
    """

    MODES = ('soft', 'hard', 'tube')

    def __init__(self, sample_rate: int = 44100,
                 drive: float = 2.0,
                 tone: float = 0.5,
                 mix: float = 1.0,
                 mode: str = 'soft'):
        """Initialize distortion."""

    def process(self, input_samples: np.ndarray) -> np.ndarray:
        """Process audio through distortion."""

    def reset(self) -> None:
        """Reset filter states."""
```

---

### effects.Flanger

Flanger effect with modulated delay.

```python
from effects import Flanger

class Flanger:
    """Flanger effect with LFO-modulated delay.

    Attributes:
        rate: LFO rate in Hz (0.1-5.0)
        depth: Modulation depth (0.0-1.0)
        feedback: Feedback amount (0.0-0.95)
        wet_dry: Wet/dry mix (0.0-1.0)
        enabled: Whether flanger is active
    """

    def __init__(self, sample_rate: int = 44100,
                 rate: float = 0.5,
                 depth: float = 0.5,
                 feedback: float = 0.5,
                 wet_dry: float = 0.5):
        """Initialize flanger."""

    def process(self, input_samples: np.ndarray) -> np.ndarray:
        """Process audio through flanger."""

    def reset(self) -> None:
        """Reset flanger state."""
```

---

## Recording Module

The `recording` module handles audio capture and preset management.

### recording.AudioRecorder

Real-time audio capture system.

```python
from recording import AudioRecorder, RecordingState, RecordingInfo

class RecordingState(Enum):
    """Recording state enumeration."""
    IDLE = auto()
    ARMED = auto()
    RECORDING = auto()
    PAUSED = auto()

@dataclass
class RecordingInfo:
    """Recording metadata.

    Attributes:
        duration_samples: Number of samples recorded
        duration_seconds: Duration in seconds
        peak_level: Peak audio level (0.0-1.0)
        sample_rate: Sample rate of recording
    """

class AudioRecorder:
    """Real-time audio recorder.

    Records audio samples with:
    - Ring buffer for efficient capture
    - Start/stop/pause controls
    - Undo last take support
    - Peak level tracking
    """

    MAX_DURATION_SAMPLES = 44100 * 60 * 30  # 30 minutes

    def __init__(self, sample_rate: int = 44100,
                 max_duration_seconds: Optional[float] = None):
        """Initialize recorder."""

    def arm(self) -> None:
        """Arm for recording (auto-start on input)."""

    def start(self) -> None:
        """Start recording immediately."""

    def stop(self) -> None:
        """Stop recording."""

    def pause(self) -> None:
        """Pause recording."""

    def resume(self) -> None:
        """Resume from pause."""

    def add_samples(self, samples: np.ndarray) -> bool:
        """Add samples to recording (call from audio callback).

        Args:
            samples: Audio samples to record

        Returns:
            True if samples were recorded
        """

    def get_audio(self) -> np.ndarray:
        """Get recorded audio (copy)."""

    def get_info(self) -> RecordingInfo:
        """Get recording information."""

    def clear(self) -> None:
        """Clear current recording."""

    def undo(self) -> bool:
        """Restore previous recording."""

    @property
    def state(self) -> RecordingState:
        """Current recording state."""

    @property
    def is_recording(self) -> bool:
        """Whether actively recording."""

    @property
    def can_undo(self) -> bool:
        """Whether undo is available."""

    @property
    def duration_seconds(self) -> float:
        """Recording duration in seconds."""

    @property
    def peak_level(self) -> float:
        """Peak audio level (0.0-1.0)."""
```

---

### recording.PresetStorage

JSON-based preset management.

```python
from recording import PresetStorage, Preset

@dataclass
class Preset:
    """Synthesizer preset data.

    Attributes:
        name: Preset name
        parameters: Synth parameters dict
        author: Creator name
        description: Preset description
        category: Preset category
        tags: List of tags
        created_at: Creation timestamp
        modified_at: Last modified timestamp
        version: Preset format version
    """

class PresetStorage:
    """Preset storage manager.

    Manages loading and saving presets as JSON files.
    Includes factory presets built into the application.
    """

    CATEGORIES = ['bass', 'lead', 'pad', 'keys', 'pluck',
                  'fx', 'drums', 'ambient', 'uncategorized']

    FACTORY_PRESETS = {...}  # Built-in presets

    def __init__(self, preset_dir: Optional[str] = None):
        """Initialize preset storage.

        Args:
            preset_dir: Directory for user presets
        """

    def save_preset(self, name: str, parameters: Dict[str, Any],
                    author: str = "", description: str = "",
                    category: str = "uncategorized",
                    tags: Optional[List[str]] = None) -> bool:
        """Save preset to file."""

    def load_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Load preset parameters.

        Args:
            name: Preset name

        Returns:
            Parameters dict or None if not found
        """

    def load_preset_full(self, name: str) -> Optional[Preset]:
        """Load full preset with metadata."""

    def delete_preset(self, name: str) -> bool:
        """Delete a user preset (factory presets cannot be deleted)."""

    def list_presets(self, include_factory: bool = True) -> List[str]:
        """List all available preset names."""

    def list_presets_by_category(self,
                                  include_factory: bool = True) -> Dict[str, List[str]]:
        """List presets organized by category."""

    def preset_exists(self, name: str) -> bool:
        """Check if preset exists."""

    def is_factory_preset(self, name: str) -> bool:
        """Check if preset is a factory preset."""

    def get_factory_preset_names(self) -> List[str]:
        """Get list of factory preset names."""

    def import_preset(self, filepath: str) -> Optional[str]:
        """Import preset from external JSON file."""

    def export_preset(self, name: str, filepath: str) -> bool:
        """Export preset to external file."""
```

---

## Songs Module

The `songs` module handles demo song playback.

### songs.Song

Song data structure.

```python
from songs import Song, SongEvent

@dataclass
class SongEvent:
    """Single note event in a song.

    Attributes:
        time: Event time in seconds from song start
        note: MIDI note number (0-127)
        velocity: Note velocity (0-127)
        duration: Note duration in seconds
    """
    time: float
    note: int
    velocity: int = 100
    duration: float = 0.5

@dataclass
class Song:
    """Song container with note events.

    Attributes:
        name: Song name
        bpm: Tempo in beats per minute
        preset: Recommended preset name
        events: List of note events
    """
    name: str
    bpm: int
    preset: str
    events: List[SongEvent]

    @property
    def duration(self) -> float:
        """Total song duration in seconds."""
```

---

### songs.SongPlayer

Song playback engine.

```python
from songs import SongPlayer, PlayerState

class PlayerState(Enum):
    """Player state enumeration."""
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2

class SongPlayer:
    """Song playback engine with callbacks.

    Uses threading.Timer for note scheduling.
    """

    def __init__(self,
                 on_note_on: Optional[Callable[[int, int], None]] = None,
                 on_note_off: Optional[Callable[[int], None]] = None,
                 on_progress: Optional[Callable[[float, float], None]] = None,
                 on_complete: Optional[Callable[[], None]] = None,
                 on_preset_change: Optional[Callable[[str], None]] = None):
        """Initialize player with callbacks.

        Args:
            on_note_on: Callback(note, velocity) for note on
            on_note_off: Callback(note) for note off
            on_progress: Callback(current, total) for progress
            on_complete: Callback() when song ends
            on_preset_change: Callback(preset_name) for preset change
        """

    def load(self, song: Song) -> None:
        """Load a song for playback."""

    def play(self) -> None:
        """Start or resume playback."""

    def stop(self) -> None:
        """Stop playback immediately."""

    def pause(self) -> None:
        """Pause playback."""

    def resume(self) -> None:
        """Resume from pause."""

    @property
    def state(self) -> PlayerState:
        """Current player state."""

    @property
    def is_playing(self) -> bool:
        """Whether currently playing."""

    @property
    def current_position(self) -> float:
        """Current playback position in seconds."""

    @property
    def total_duration(self) -> float:
        """Total song duration in seconds."""

    @property
    def progress(self) -> float:
        """Playback progress (0.0-1.0)."""

    @property
    def current_song(self) -> Optional[Song]:
        """Currently loaded song."""
```

---

### songs.demo_songs

Built-in demonstration songs.

```python
from songs.demo_songs import get_all_songs, get_song_by_name, DEMO_SONGS

DEMO_SONGS: List[Song]
"""List of all built-in demo songs."""

def get_all_songs() -> List[Song]:
    """Get list of all demo songs."""

def get_song_by_name(name: str) -> Optional[Song]:
    """Get a demo song by name (case-insensitive)."""
```

**Available Demo Songs:**
- Twinkle Twinkle (90 BPM, Soft Pad)
- Fur Elise Intro (72 BPM, Bright Lead)
- Synth Demo (120 BPM, Fat Bass)
- Ambient Pad (60 BPM, Soft Pad)
- Retro Arp (140 BPM, Retro Square)
- Bass Groove (100 BPM, Fat Bass)
- Dreamy Lead (80 BPM, Bright Lead)
- Techno Pulse (130 BPM, Fat Bass)

---

## Visualization Module

The `visualization` module provides real-time audio visualization.

### visualization.Oscilloscope

Real-time waveform display.

```python
from visualization import Oscilloscope, TriggerMode, DisplayMode

class TriggerMode(Enum):
    """Oscilloscope trigger mode."""
    FREE_RUN = auto()
    RISING = auto()
    FALLING = auto()
    AUTO = auto()

class DisplayMode(Enum):
    """Oscilloscope display mode."""
    WAVEFORM = auto()
    LISSAJOUS = auto()
    SPECTRUM = auto()

class Oscilloscope(tk.Canvas):
    """Real-time waveform oscilloscope display.

    Renders audio on a tkinter canvas with:
    - Trigger modes
    - Adjustable time scale
    - Grid overlay
    - Peak indicator
    - Freeze capability
    """

    def __init__(self, parent: tk.Widget,
                 width: int = 400,
                 height: int = 200,
                 sample_rate: int = 44100):
        """Initialize oscilloscope."""

    def update_waveform(self, samples: np.ndarray) -> None:
        """Update display with new audio samples.

        Args:
            samples: Audio samples (mono, float32)
        """

    def clear(self) -> None:
        """Clear the waveform display."""

    def freeze(self) -> None:
        """Freeze display (stop updating)."""

    def unfreeze(self) -> None:
        """Unfreeze display (resume updating)."""

    @property
    def trigger_mode(self) -> TriggerMode:
        """Get/set trigger mode."""

    @property
    def trigger_level(self) -> float:
        """Get/set trigger level (-1.0 to 1.0)."""

    @property
    def time_scale(self) -> int:
        """Get/set time scale (samples per pixel)."""

    @property
    def frozen(self) -> bool:
        """Whether display is frozen."""

    @property
    def peak_level(self) -> float:
        """Current peak level."""

    def get_time_per_division(self) -> float:
        """Get time per horizontal division in milliseconds."""
```

---

## Application Controller

The `app_controller` module orchestrates the entire application.

### AppController

Main application controller coordinating all components.

```python
from app_controller import AppController

class AppController:
    """Main application orchestration controller.

    Coordinates:
    - Synthesizer and effects
    - Audio engine
    - Recording system
    - Song playback
    - GUI updates
    """

    def __init__(self):
        """Initialize controller and all subsystems."""

    def start(self) -> None:
        """Start audio engine and systems."""

    def stop(self) -> None:
        """Stop all systems."""

    # Note handling
    def handle_note_on(self, note: int, velocity: int = 127) -> None:
        """Handle note on event."""

    def handle_note_off(self, note: int) -> None:
        """Handle note off event."""

    def all_notes_off(self) -> None:
        """Panic - release all notes."""

    # Parameter handling
    def handle_parameter_change(self, name: str, value: Any) -> None:
        """Handle parameter change from GUI."""

    def get_parameter(self, name: str) -> Any:
        """Get current parameter value."""

    # Preset handling
    def load_preset(self, name: str) -> bool:
        """Load a preset by name."""

    def save_preset(self, name: str) -> bool:
        """Save current settings as preset."""

    def get_preset_names(self) -> List[str]:
        """Get list of available presets."""

    # Recording
    def start_recording(self) -> None:
        """Start audio recording."""

    def stop_recording(self) -> None:
        """Stop audio recording."""

    def export_recording(self, filepath: str) -> bool:
        """Export recording to WAV file."""

    # Song playback
    def play_song(self, song_name: str) -> None:
        """Start playing a demo song."""

    def stop_song(self) -> None:
        """Stop song playback."""

    # Status
    @property
    def active_voice_count(self) -> int:
        """Number of active synth voices."""

    @property
    def is_recording(self) -> bool:
        """Whether currently recording."""

    @property
    def is_playing_song(self) -> bool:
        """Whether a song is playing."""
```

---

## Usage Examples

### Basic Synthesis

```python
from synth import Synthesizer

# Create synthesizer
synth = Synthesizer(sample_rate=44100, num_voices=8)

# Set parameters
synth.set_parameter('osc1_waveform', 'sawtooth')
synth.set_parameter('filter_cutoff', 1000)
synth.set_parameter('filter_resonance', 0.5)

# Play a note
synth.note_on(60, velocity=100)  # Middle C

# Generate audio
samples = synth.generate(512)

# Release note
synth.note_off(60)
```

### Effects Processing

```python
from effects import Reverb, Delay, Chorus

# Create effects
reverb = Reverb(sample_rate=44100, room_size=0.7, wet_dry=0.3)
delay = Delay(sample_rate=44100, delay_time_ms=300, feedback=0.4)
chorus = Chorus(sample_rate=44100, rate=0.5, depth=0.5)

# Enable effects
reverb.enabled = True
delay.enabled = True
chorus.enabled = True

# Process audio
processed = reverb.process(
    delay.process(
        chorus.process(samples)
    )
)
```

### Recording Audio

```python
from recording import AudioRecorder

# Create recorder
recorder = AudioRecorder(sample_rate=44100)

# Start recording
recorder.start()

# Add samples in audio callback
recorder.add_samples(audio_buffer)

# Stop and get audio
recorder.stop()
audio = recorder.get_audio()
```

### Preset Management

```python
from recording import PresetStorage

# Create storage
storage = PresetStorage()

# List presets
presets = storage.list_presets()
print(f"Available presets: {presets}")

# Load a preset
params = storage.load_preset('Fat Bass')
if params:
    synth.set_parameters(params)

# Save custom preset
storage.save_preset(
    name='My Bass',
    parameters=synth.get_parameters(),
    category='bass',
    author='User'
)
```

### Song Playback

```python
from songs import SongPlayer, get_song_by_name

# Create player with callbacks
player = SongPlayer(
    on_note_on=lambda n, v: synth.note_on(n, v),
    on_note_off=lambda n: synth.note_off(n),
    on_complete=lambda: print("Song finished!")
)

# Load and play song
song = get_song_by_name("Twinkle Twinkle")
player.load(song)
player.play()

# Later: stop playback
player.stop()
```

---

## Error Handling

Most components use these patterns:

1. **Parameter clamping**: Invalid values are clamped to valid range
2. **None returns**: Failed lookups return None
3. **Boolean returns**: Operations return True/False for success
4. **Exception storage**: Audio callback errors stored for retrieval

```python
# Check for audio errors
error = engine.get_last_error()
if error:
    print(f"Audio error: {error}")
    engine.clear_error()

# Safe preset loading
params = storage.load_preset('NonexistentPreset')
if params is None:
    print("Preset not found")
```

---

## Thread Safety Notes

| Component | Thread Safety |
|-----------|--------------|
| Synthesizer | Parameter updates atomic |
| Effects | No shared state |
| AudioRecorder | Lock-protected buffer |
| PresetStorage | File I/O on main thread |
| SongPlayer | Lock + Timer threads |
| Oscilloscope | GUI thread only |

**Best Practice**: Update parameters from main thread, audio callback only reads.
