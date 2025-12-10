# WinMiniSynth

A polyphonic Windows software synthesizer with virtual keyboard, recording, and real-time visualization.

## Features

- **8-Voice Polyphonic Synthesis** - Play chords and melodies with up to 8 simultaneous voices
- **Dual Oscillators** - Each with sine, square, saw, triangle, pulse waveforms and pulse width control
- **Moog-Style Filter** - 24dB/oct resonant lowpass filter with cutoff and resonance
- **ADSR Envelopes** - Separate amplitude and filter envelopes
- **LFO Modulation** - Modulate pitch, filter, or pulse width
- **Effects Chain** - Reverb, Delay, Chorus, Flanger, Distortion
- **Real-Time Visualization** - Oscilloscope waveform display and filter response curve
- **Preset System** - Save and load synth patches
- **Recording** - Record your performances to WAV files
- **Metronome** - Built-in click track for practice
- **Demo Songs** - Built-in songs to showcase the synth

## Screenshot

The synthesizer features a clean tkinter GUI with:
- Virtual piano keyboard (click or use computer keys)
- Oscillator controls (waveform, detune, mix)
- Filter controls (cutoff, resonance, envelope amount)
- Effects panels (reverb, delay, chorus, flanger, distortion)
- Real-time oscilloscope and filter response display

## Installation

### Requirements
- Python 3.10 or higher
- Windows (tested), macOS, Linux

### Install from source

```bash
git clone https://github.com/jeremy-schaab/WinMiniSynth.git
cd WinMiniSynth
pip install -e .
```

### Optional: Performance boost

```bash
pip install -e ".[performance]"  # Adds numba JIT compilation
```

## Usage

After installation, run the synthesizer:

```bash
# Using the installed command
minisynth

# Or using Python module
python -m karokelite

# Or directly
python src/main.py
```

### Keyboard Controls

- **Z-M keys**: Lower octave (C3-B3)
- **Q-U keys**: Upper octave (C4-B4)
- **Number keys 2,3,5,6,7**: Black keys (sharps/flats)

## Project Structure

```
WinMiniSynth/
├── src/
│   ├── main.py              # Application entry point
│   ├── app_controller.py    # Central coordinator
│   ├── synth/               # Audio synthesis engine
│   │   ├── oscillator.py    # Waveform generators
│   │   ├── filter.py        # Moog filter
│   │   ├── envelope.py      # ADSR envelopes
│   │   ├── lfo.py           # Low frequency oscillator
│   │   ├── voice.py         # Polyphonic voice
│   │   └── synth.py         # Voice manager
│   ├── effects/             # Audio effects
│   │   ├── reverb.py
│   │   ├── delay.py
│   │   ├── chorus.py
│   │   ├── flanger.py
│   │   └── distortion.py
│   ├── gui/                 # tkinter UI
│   ├── visualization/       # Oscilloscope & filter display
│   ├── recording/           # Audio recording & presets
│   └── songs/               # Demo song playback
├── tests/                   # Unit and integration tests
├── pyproject.toml           # Package configuration
└── requirements.txt         # Dependencies
```

## Dependencies

- **numpy** - Audio signal processing
- **sounddevice** - Cross-platform audio I/O
- **numba** (optional) - JIT compilation for performance
- **tkinter** - GUI (included with Python)

## License

MIT License

## Author

Created with AI-DLC (AI-Driven Development Lifecycle) methodology.
