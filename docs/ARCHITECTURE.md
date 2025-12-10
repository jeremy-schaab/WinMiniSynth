# WinMiniSynth Architecture Documentation

## Overview

WinMiniSynth is a Python-based virtual analog synthesizer following a layered architecture with clear separation between audio synthesis, effects processing, GUI, and application control.

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Module Structure](#module-structure)
4. [Audio Pipeline](#audio-pipeline)
5. [Component Diagrams](#component-diagrams)
6. [Data Flow](#data-flow)
7. [Threading Model](#threading-model)
8. [Technology Stack](#technology-stack)

---

## System Overview

### High-Level Architecture

```
+------------------------------------------+
|             User Interface               |
|  (tkinter: MainWindow, Panels, Keyboard) |
+------------------------------------------+
                    |
                    v
+------------------------------------------+
|          Application Controller          |
|       (AppController: orchestration)     |
+------------------------------------------+
          |         |         |
          v         v         v
+----------+ +----------+ +----------+
|   Synth  | | Effects  | |Recording |
|  Engine  | |  Chain   | |  System  |
+----------+ +----------+ +----------+
          |         |         |
          v         v         v
+------------------------------------------+
|            Audio Engine                  |
|    (sounddevice: real-time output)       |
+------------------------------------------+
```

### Key Characteristics

- **8-voice polyphony** with voice stealing
- **44.1kHz sample rate** with 512-sample buffer (~11.6ms latency)
- **Real-time audio processing** in separate thread
- **Event-driven GUI** using tkinter
- **Optional JIT compilation** via numba for performance

---

## Architecture Principles

### 1. Separation of Concerns

- **Synthesis**: Pure audio generation (oscillators, filters, envelopes)
- **Effects**: Audio processing (reverb, delay, chorus, distortion)
- **GUI**: User interface and visualization
- **Control**: Application orchestration and event handling

### 2. Real-Time Safety

Audio callback must be:
- **Non-blocking**: No I/O, file access, or memory allocation
- **Deterministic**: Consistent execution time
- **Lock-free**: Minimal synchronization with GUI thread

### 3. Callback Architecture

```python
# Audio callback contract
def audio_callback(num_samples: int) -> np.ndarray:
    """
    Must return exactly num_samples float32 values.
    Must complete within buffer duration (~11.6ms).
    Must not allocate memory or block.
    Should normalize output to [-1.0, 1.0].
    """
    pass
```

### 4. Domain-Driven Design

Core synthesis components are modeled as domain objects:
- **Voice**: Aggregate managing a single polyphonic voice
- **Oscillator**: Value object generating waveforms
- **Filter**: Value object implementing Moog ladder filter
- **Envelope**: Value object (ADSR) shaping parameters over time

---

## Module Structure

```
src/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point
├── main.py              # Application startup
├── app_controller.py    # Main orchestration controller
│
├── synth/               # Synthesis engine
│   ├── __init__.py
│   ├── synth.py         # Synthesizer aggregate
│   ├── voice.py         # Voice management
│   ├── oscillator.py    # Waveform generation
│   ├── filter.py        # Moog ladder filter
│   ├── envelope.py      # ADSR envelope
│   ├── lfo.py           # Low-frequency oscillator
│   └── engine.py        # Audio I/O engine
│
├── effects/             # Effects processing
│   ├── __init__.py
│   ├── reverb.py        # Schroeder reverb
│   ├── delay.py         # Digital delay
│   ├── chorus.py        # Multi-voice chorus
│   ├── distortion.py    # Waveshaping distortion
│   └── flanger.py       # Flanger effect
│
├── gui/                 # User interface
│   ├── __init__.py
│   ├── main_window.py   # Top-level window
│   ├── keyboard_widget.py # Virtual piano
│   ├── controls_panel.py  # Parameter panels
│   ├── styles.py        # Visual themes
│   └── [effect]_panel.py  # Effect control panels
│
├── visualization/       # Audio visualization
│   ├── __init__.py
│   ├── panel.py         # Visualization container
│   ├── oscilloscope.py  # Waveform display
│   └── filter_curve.py  # Filter response
│
├── recording/           # Audio recording
│   ├── __init__.py
│   ├── recorder.py      # Audio capture
│   ├── exporter.py      # WAV export
│   └── preset_storage.py # Preset management
│
└── songs/               # Demo songs
    ├── __init__.py
    ├── song.py          # Song data structure
    ├── player.py        # Playback engine
    └── demo_songs.py    # Built-in songs
```

---

## Audio Pipeline

### Signal Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        VOICE (x8)                               │
│  ┌─────────┐   ┌─────────┐                                      │
│  │  OSC 1  │ + │  OSC 2  │  -> Mix                              │
│  └─────────┘   └─────────┘                                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │  FILTER (Moog Ladder)                               │       │
│  │  Cutoff modulated by: Filter Env + LFO              │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │  AMP ENVELOPE (ADSR)                                │       │
│  │  Gates voice amplitude                              │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────────┐
│                      VOICE MIXER                                │
│                Sum all active voices                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────────┐
│                      EFFECTS CHAIN                              │
│  ┌────────────┐ ┌─────────┐ ┌───────┐ ┌─────────┐ ┌──────────┐ │
│  │ Distortion │→│ Chorus  │→│ Delay │→│ Flanger │→│  Reverb  │ │
│  └────────────┘ └─────────┘ └───────┘ └─────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────────┐
│                      MASTER OUTPUT                              │
│  Volume control + Soft clipping                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Per-Voice Processing

1. **Oscillator Generation**
   - OSC1: Generate waveform at note frequency
   - OSC2: Generate waveform at detuned frequency
   - Mix oscillators by level

2. **Filter Processing**
   - Calculate filter envelope value
   - Apply LFO modulation to cutoff
   - Process through 4-pole Moog ladder filter

3. **Amplitude Shaping**
   - Generate amplitude envelope
   - Apply voice amplitude

4. **Voice State Management**
   - Track voice stage (IDLE, ATTACK, DECAY, SUSTAIN, RELEASE)
   - Handle voice stealing when polyphony exceeded

---

## Component Diagrams

### Synthesizer Class Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                      Synthesizer                            │
│  - voices: List[Voice]                                      │
│  - filter: MoogFilter                                       │
│  - effects: EffectsChain                                    │
│  + note_on(note, velocity)                                  │
│  + note_off(note)                                           │
│  + generate(num_samples) -> np.ndarray                      │
│  + set_parameter(name, value)                               │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              v               v               v
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │    Voice     │ │  MoogFilter  │ │ EffectsChain │
     │  - osc1      │ │  - cutoff    │ │  - reverb    │
     │  - osc2      │ │  - resonance │ │  - delay     │
     │  - amp_env   │ │  - stages[4] │ │  - chorus    │
     │  - filter_env│ │  + process() │ │  - distortion│
     │  + generate()│ └──────────────┘ │  + process() │
     └──────────────┘                  └──────────────┘
              │
    ┌─────────┼─────────┐
    v         v         v
┌────────┐ ┌────────┐ ┌────────┐
│Oscillator│ │ADSREnv│ │  LFO   │
│- waveform│ │- ADSR │ │- rate  │
│- phase  │ │- stage│ │- depth │
│+ generate│ │+ gen()│ │+ gen() │
└────────┘ └────────┘ └────────┘
```

### GUI Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                     MainWindow (tk.Tk)                      │
│  Title: "KarokeLite Mini Synthesizer"                       │
└─────────────────────────────────────────────────────────────┘
         │
         ├── Row 1: Synthesis
         │   ├── OscillatorPanel (OSC 1)
         │   ├── OscillatorPanel (OSC 2)
         │   ├── EnvelopePanel (AMP)
         │   └── EnvelopePanel (FILTER)
         │
         ├── Row 2: Effects
         │   ├── DistortionPanel
         │   ├── ChorusPanel
         │   ├── DelayPanel
         │   ├── FlangerPanel
         │   └── ReverbPanel
         │
         ├── Row 3: Filter & Visualization
         │   ├── FilterPanel
         │   ├── LFOPanel
         │   ├── FilterCurve
         │   └── VisualizationPanel (Oscilloscope)
         │
         ├── Row 4: Controls
         │   ├── PresetPanel
         │   ├── SongPlayerPanel
         │   ├── MetronomePanel
         │   └── RecordingPanel
         │
         ├── Row 5: Keyboard
         │   └── PianoKeyboard
         │
         └── Row 6: Status
             └── StatusBar
```

---

## Data Flow

### Note Event Flow

```
┌─────────────────┐
│  User Input     │
│ (Key Press/GUI) │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  MainWindow     │
│  (note_on CB)   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ AppController   │
│ handle_note_on()│
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Synthesizer    │
│  note_on()      │
│  - Find voice   │
│  - Trigger envs │
└────────┬────────┘
         │
         v
┌─────────────────┐
│     Voice       │
│  - OSC freq set │
│  - Env gate_on  │
└─────────────────┘
```

### Parameter Change Flow

```
┌─────────────────┐
│   GUI Panel     │
│ (slider change) │
└────────┬────────┘
         │ on_change callback
         v
┌─────────────────┐
│  MainWindow     │
│ _on_param_change│
└────────┬────────┘
         │ on_parameter_change
         v
┌─────────────────┐
│ AppController   │
│ handle_param()  │
└────────┬────────┘
         │ set_parameter
         v
┌─────────────────┐
│  Synthesizer    │
│  or Effects     │
│  update param   │
└─────────────────┘
```

### Audio Callback Flow

```
┌─────────────────┐
│  sounddevice    │
│  OutputStream   │
│  (audio thread) │
└────────┬────────┘
         │ callback
         v
┌─────────────────┐
│  AudioEngine    │
│ _audio_callback │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ AppController   │
│ _audio_callback │
└────────┬────────┘
         │
    ┌────┴────┐
    v         v
┌────────┐ ┌────────┐
│ Synth  │ │Recorder│
│generate│ │add_samp│
└───┬────┘ └────────┘
    │
    v
┌─────────────────┐
│  Effects Chain  │
│  process()      │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Master Output  │
│  (clamped)      │
└─────────────────┘
```

---

## Threading Model

### Thread Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MAIN THREAD                            │
│  - tkinter event loop                                       │
│  - GUI updates and callbacks                                │
│  - Parameter changes                                        │
│  - Visualization updates                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                    (callbacks, shared state)
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                     AUDIO THREAD                            │
│  - sounddevice callback                                     │
│  - Real-time synthesis                                      │
│  - Effects processing                                       │
│  - Recording capture                                        │
│                                                             │
│  MUST BE:                                                   │
│  - Non-blocking                                             │
│  - No memory allocation                                     │
│  - Deterministic execution time                             │
└─────────────────────────────────────────────────────────────┘
                              │
                    (scheduled events)
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                    TIMER THREADS                            │
│  - Song playback scheduling                                 │
│  - Metronome ticks                                          │
│  - Progress updates                                         │
└─────────────────────────────────────────────────────────────┘
```

### Thread Safety

| Component | Thread Safety Mechanism |
|-----------|------------------------|
| Synthesizer | Parameter atomic updates |
| Effects | No shared mutable state |
| Recorder | Lock for buffer access |
| GUI | tkinter event loop only |
| SongPlayer | threading.Lock + Timer |

---

## Technology Stack

### Core Technologies

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.10+ |
| Audio I/O | sounddevice | Latest |
| Numerical | NumPy | Latest |
| JIT (optional) | Numba | Latest |
| GUI | tkinter | Built-in |

### Audio Specifications

| Parameter | Value |
|-----------|-------|
| Sample Rate | 44100 Hz |
| Bit Depth | 32-bit float |
| Buffer Size | 512 samples |
| Latency | ~11.6 ms |
| Channels | 1 (mono) |
| Polyphony | 8 voices |

### Performance Characteristics

| Metric | Without Numba | With Numba |
|--------|---------------|------------|
| Voice generation | ~1.5ms/buffer | ~0.3ms/buffer |
| Filter processing | ~0.5ms/buffer | ~0.1ms/buffer |
| Effects chain | ~2.0ms/buffer | ~0.5ms/buffer |
| Total callback | ~4.0ms/buffer | ~1.0ms/buffer |
| CPU headroom | ~65% | ~91% |

---

## Design Decisions

### ADR-001: Use sounddevice for Audio

**Context**: Need cross-platform audio I/O with low latency.

**Decision**: Use sounddevice library wrapping PortAudio.

**Consequences**:
- Works on Windows, macOS, Linux
- Low latency possible (512 samples)
- Requires PortAudio installation on some systems

### ADR-002: Optional Numba JIT

**Context**: Real-time audio requires fast DSP code.

**Decision**: Make numba optional with graceful fallback.

**Consequences**:
- Performance benefit when available
- No hard dependency
- Fallback works but uses more CPU

### ADR-003: tkinter for GUI

**Context**: Need simple, cross-platform GUI.

**Decision**: Use tkinter (Python's built-in GUI toolkit).

**Consequences**:
- No additional dependencies
- Limited styling options
- Good enough for synthesizer controls
- Built-in event loop integration

### ADR-004: Mono Audio Output

**Context**: Stereo vs mono for synthesizer.

**Decision**: Use mono output, effects can be stereo internally.

**Consequences**:
- Simpler signal flow
- Less CPU usage
- Suitable for most use cases
- Easy to extend to stereo later

---

## Extension Points

### Adding New Waveforms

1. Add entry to `Waveform` enum in `oscillator.py`
2. Implement generation in `Oscillator._generate_wave()`
3. Add GUI option in `OscillatorPanel`

### Adding New Effects

1. Create new effect class in `effects/` with `process()` method
2. Add to effects chain in `Synthesizer`
3. Create control panel in `gui/`
4. Wire callbacks in `MainWindow`

### Adding MIDI Support

1. Install `mido` and `python-rtmidi`
2. Create `MidiController` class
3. Wire MIDI events to `AppController.handle_note_on/off`

---

## Performance Optimization

### Critical Path Optimization

1. **Pre-allocate buffers**: All NumPy arrays allocated at init
2. **Avoid allocations in callback**: Reuse work buffers
3. **Numba JIT**: Compile hot loops to native code
4. **Vectorized operations**: Use NumPy broadcasting

### Voice Management

1. **Voice stealing**: Oldest voice released when exceeding polyphony
2. **Idle detection**: Voices return to pool when envelope completes
3. **Parameter caching**: Avoid recalculating coefficients every sample

---

## Security Considerations

- No network access
- Preset files validated before loading
- Audio buffer bounds checking
- No execution of external code

---

## Future Considerations

1. **MIDI Input**: Support external MIDI controllers
2. **Stereo Output**: Full stereo effects chain
3. **Additional Filters**: High-pass, band-pass, notch
4. **Modulation Matrix**: Flexible routing of modulators
5. **Sample Playback**: Wavetable and sample-based oscillators
6. **Plugin Format**: VST/AU export for DAW integration
