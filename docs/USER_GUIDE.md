# WinMiniSynth User Guide

## Overview

WinMiniSynth (KarokeLite Mini Synthesizer) is a virtual analog synthesizer built with Python and tkinter. It provides 8-voice polyphony, dual oscillators, a Moog-style filter, multiple effects, and real-time visualization.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [User Interface](#user-interface)
5. [Keyboard Controls](#keyboard-controls)
6. [Synthesis Parameters](#synthesis-parameters)
7. [Effects](#effects)
8. [Presets](#presets)
9. [Recording](#recording)
10. [Demo Songs](#demo-songs)
11. [Troubleshooting](#troubleshooting)

---

## Getting Started

### System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.10 or higher
- **Audio**: Working audio output device
- **RAM**: 4GB minimum (8GB recommended)
- **Display**: 1280x720 minimum resolution

### Installation

#### Option 1: Install from Source

```bash
# Clone the repository
git clone https://github.com/your-repo/WinMiniSynth.git
cd WinMiniSynth

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

#### Option 2: Install with pip

```bash
pip install karokelite-minisynth
```

### Dependencies

The synthesizer requires the following Python packages:
- `numpy` - Numerical computing for audio processing
- `sounddevice` - Cross-platform audio I/O
- `numba` (optional) - JIT compilation for performance optimization

---

## Quick Start

### Starting the Synthesizer

```bash
# Run from command line
python -m src

# Or if installed via pip
karokelite-synth
```

### Your First Sound

1. **Launch the application** - The main window opens with the synthesizer interface
2. **Play notes** - Press keys on your computer keyboard (see [Keyboard Controls](#keyboard-controls))
3. **Select a preset** - Choose from the preset dropdown (e.g., "Fat Bass" or "Bright Lead")
4. **Adjust parameters** - Move sliders to shape the sound
5. **Add effects** - Enable reverb, delay, chorus, or distortion

---

## User Interface

The interface is organized in rows from top to bottom:

### Row 1: Synthesis Engine
- **OSC 1** - First oscillator with waveform, level, detune, and octave controls
- **OSC 2** - Second oscillator with independent controls
- **AMP ENV** - Amplitude envelope (ADSR) shaping note volume over time
- **FILTER ENV** - Filter envelope (ADSR) modulating the filter cutoff

### Row 2: Effects Chain
- **DISTORTION** - Waveshaping distortion with drive and tone controls
- **CHORUS** - Multi-voice modulated delay for thickness
- **DELAY** - Echo effect with feedback and time controls
- **FLANGER** - Short modulated delay for jet/sweep effects
- **REVERB** - Room simulation for space and depth

### Row 3: Filter and Visualization
- **FILTER** - Moog-style 4-pole lowpass filter with cutoff and resonance
- **LFO** - Low-frequency oscillator for modulation
- **FILTER RESPONSE** - Real-time filter curve display
- **OSCILLOSCOPE** - Waveform visualization

### Row 4: Control Panel
- **PRESET / MASTER** - Preset selection and master volume
- **SONG PLAYER** - Demo song playback controls
- **METRONOME** - Click track for timing
- **RECORDING** - Audio recording controls

### Row 5: Virtual Keyboard
- Interactive piano keyboard with 2 octaves
- Click or use computer keyboard to play

### Row 6: Status Bar
- Voice count, sample rate, buffer size, CPU usage

---

## Keyboard Controls

### Playing Notes

The computer keyboard is mapped to a piano layout across two octaves:

#### Lower Octave (C3-E4)
| Key | Note |
|-----|------|
| Z | C |
| S | C# |
| X | D |
| D | D# |
| C | E |
| V | F |
| G | F# |
| B | G |
| H | G# |
| N | A |
| J | A# |
| M | B |
| , | C (next octave) |
| L | C# |
| . | D |
| ; | D# |
| / | E |

#### Upper Octave (C4-E5)
| Key | Note |
|-----|------|
| Q | C |
| 2 | C# |
| W | D |
| 3 | D# |
| E | E |
| R | F |
| 5 | F# |
| T | G |
| 6 | G# |
| Y | A |
| 7 | A# |
| U | B |
| I | C (next octave) |
| 9 | C# |
| O | D |
| 0 | D# |
| P | E |

### Special Keys

| Key | Function |
|-----|----------|
| Escape | **PANIC** - All notes off |
| Ctrl+S | Save preset |
| Ctrl+O | Open preset |

### Octave Controls

Use the +/- buttons in the keyboard panel to shift octaves up or down.

---

## Synthesis Parameters

### Oscillators (OSC 1 & OSC 2)

Each oscillator generates a basic waveform that forms the foundation of the sound.

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Waveform** | Sine, Saw, Square, Triangle, Pulse | Basic wave shape |
| **Level** | 0.0 - 1.0 | Volume of this oscillator |
| **Detune** | -50 to +50 cents | Fine pitch adjustment |
| **Octave** | -2 to +2 | Coarse pitch shift in octaves |

**Tips:**
- Use two detuned sawtooth waves for a classic "supersaw" sound
- Mix a square and sine wave for a hollow, flute-like tone
- Detune OSC2 slightly (5-10 cents) for a richer sound

### Filter

The filter shapes the harmonic content of the sound by attenuating frequencies.

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Cutoff** | 20 - 20000 Hz | Frequency at which filtering begins |
| **Resonance** | 0.0 - 0.95 | Emphasis at the cutoff frequency |
| **Env Amount** | 0.0 - 1.0 | How much the filter envelope affects cutoff |

**Tips:**
- Low cutoff + high resonance = "squelchy" acid bass
- High cutoff + low resonance = bright, open sound
- Modulate cutoff with the filter envelope for dynamic sweeps

### ADSR Envelopes

Both AMP and FILTER envelopes use Attack-Decay-Sustain-Release stages.

| Stage | Range | Description |
|-------|-------|-------------|
| **Attack** | 0.001 - 10 sec | Time to reach full level |
| **Decay** | 0.001 - 10 sec | Time to fall to sustain level |
| **Sustain** | 0.0 - 1.0 | Level held while key is pressed |
| **Release** | 0.001 - 10 sec | Time to fade after key release |

**Tips:**
- Fast attack (0.01s) for plucky/percussive sounds
- Slow attack (0.5s+) for pads and strings
- Zero sustain creates percussive envelopes
- Long release creates ambient tails

### LFO (Low-Frequency Oscillator)

The LFO generates a slow, periodic signal for modulation.

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Waveform** | Sine, Saw, Square, Triangle, Pulse | Modulation wave shape |
| **Rate** | 0.1 - 50 Hz | Speed of modulation |
| **Depth** | 0.0 - 1.0 | Amount of modulation |
| **To Pitch** | 0.0 - 1.0 | Vibrato (pitch modulation) |
| **To Filter** | 0.0 - 1.0 | Wah/sweep (filter modulation) |
| **To PW** | 0.0 - 1.0 | Pulse width modulation |

---

## Effects

All effects can be enabled/disabled independently and are processed in this order:
**Distortion -> Chorus -> Delay -> Flanger -> Reverb**

### Distortion

Adds harmonic content through waveshaping.

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Enable** | On/Off | Toggle effect |
| **Drive** | 1.0 - 20.0 | Amount of distortion |
| **Tone** | 0.0 - 1.0 | Brightness (0=dark, 1=bright) |
| **Mode** | Soft, Hard, Tube | Distortion character |
| **Mix** | 0.0 - 1.0 | Wet/dry blend |

**Modes:**
- **Soft**: Warm, tube-like saturation (tanh)
- **Hard**: Aggressive digital clipping
- **Tube**: Asymmetric clipping for even harmonics

### Chorus

Creates a thicker sound by layering modulated copies.

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Enable** | On/Off | Toggle effect |
| **Rate** | 0.1 - 5.0 Hz | LFO modulation speed |
| **Depth** | 0.0 - 1.0 | Amount of pitch variation |
| **Voices** | 2 - 4 | Number of chorus voices |
| **Mix** | 0.0 - 1.0 | Wet/dry blend |

### Delay

Adds echo/repeat effects.

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Enable** | On/Off | Toggle effect |
| **Time** | 10 - 2000 ms | Delay time |
| **Feedback** | 0.0 - 0.95 | Amount of repeats |
| **Mix** | 0.0 - 1.0 | Wet/dry blend |

### Flanger

Creates a sweeping, jet-like effect.

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Enable** | On/Off | Toggle effect |
| **Rate** | 0.1 - 5.0 Hz | Sweep speed |
| **Depth** | 0.0 - 1.0 | Sweep depth |
| **Feedback** | 0.0 - 0.95 | Intensity of effect |
| **Mix** | 0.0 - 1.0 | Wet/dry blend |

### Reverb

Simulates acoustic space.

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Enable** | On/Off | Toggle effect |
| **Room Size** | 0.0 - 1.0 | Size of simulated space |
| **Mix** | 0.0 - 1.0 | Wet/dry blend |

---

## Presets

### Factory Presets

The synthesizer includes 10 built-in presets:

| Preset | Character | Best For |
|--------|-----------|----------|
| **Init** | Neutral starting point | Building new sounds |
| **Fat Bass** | Deep, punchy bass | Bass lines, sub drops |
| **Bright Lead** | Cutting, detuned saw | Lead melodies |
| **Soft Pad** | Gentle, evolving texture | Ambient backgrounds |
| **Retro Square** | Classic 8-bit sound | Chiptune, retro games |
| **Ethereal Strings** | Lush, detuned ensemble | Orchestral pads |
| **Plucky Keys** | Quick attack, fast decay | Marimba, pluck sounds |
| **Warm Organ** | Rich sine harmonics | Hammond-style organ |
| **Acid Squelch** | High resonance bass | 303-style acid |
| **Cosmic Bell** | Metallic, bell-like | Atmospheric hits |

### Using Presets

1. **Load Preset**: Select from dropdown and click "Load"
2. **Save Preset**: Modify a sound, click "Save" to store as JSON
3. **Init Patch**: Click "Init" to reset to default settings

### Preset Files

User presets are stored as JSON files in the `presets/` directory.

---

## Recording

### Recording Controls

| Button | Function |
|--------|----------|
| **ARM** | Arm recording (auto-start on input) |
| **REC** | Start recording immediately |
| **PAUSE** | Pause recording |
| **STOP** | Stop recording |
| **EXPORT** | Save recording as WAV file |
| **CLEAR** | Delete current recording |
| **UNDO** | Restore previous take |

### Recording Workflow

1. **Arm or Start**: Click ARM to wait for input, or REC to start immediately
2. **Play**: Perform on the keyboard
3. **Stop**: Click STOP when finished
4. **Export**: Click EXPORT and choose a filename to save as WAV

### Recording Settings

- **Sample Rate**: 44100 Hz
- **Bit Depth**: 32-bit float
- **Channels**: Mono
- **Max Duration**: 30 minutes
- **Undo Levels**: 3 previous takes

---

## Demo Songs

The synthesizer includes 8 demo songs to showcase its capabilities:

| Song | BPM | Preset | Style |
|------|-----|--------|-------|
| **Twinkle Twinkle** | 90 | Soft Pad | Children's melody |
| **Fur Elise (Intro)** | 72 | Bright Lead | Classical |
| **Synth Demo** | 120 | Fat Bass | Electronic |
| **Ambient Pad** | 60 | Soft Pad | Ambient chords |
| **Retro Arp** | 140 | Retro Square | Arpeggiated sequence |
| **Bass Groove** | 100 | Fat Bass | Funky bass line |
| **Dreamy Lead** | 80 | Bright Lead | Melodic lead |
| **Techno Pulse** | 130 | Fat Bass | Driving electronic |

### Playing Demo Songs

1. Select a song from the dropdown
2. Click **Play** to start
3. The keyboard shows which notes are being played
4. Click **Stop** to end playback

---

## Troubleshooting

### No Sound

1. **Check volume**: Ensure master volume is not at zero
2. **Check audio device**: Verify your speakers/headphones are working
3. **Check voice count**: Status bar shows active voices (should be > 0 when playing)
4. **Restart application**: Close and reopen the synthesizer

### Audio Glitches/Crackling

1. **Increase buffer size**: Modify `buffer_size` in AudioConfig (default: 512)
2. **Close other applications**: Free up CPU resources
3. **Install numba**: `pip install numba` for JIT optimization
4. **Check CPU usage**: Status bar shows CPU usage

### Keyboard Not Responding

1. **Click on keyboard area**: Ensure keyboard widget has focus
2. **Check for key conflicts**: Other applications may capture keystrokes
3. **Use PANIC (Escape)**: Release any stuck notes

### High CPU Usage

1. **Reduce polyphony**: Play fewer simultaneous notes
2. **Disable effects**: Turn off reverb/delay/chorus
3. **Install numba**: Provides 2-10x performance improvement

### Application Won't Start

1. **Check Python version**: Requires Python 3.10+
2. **Install dependencies**: `pip install -e .`
3. **Check sounddevice**: `pip install sounddevice`
4. **Check for errors**: Run from command line to see error messages

### Common Error Messages

| Error | Solution |
|-------|----------|
| `sounddevice not available` | `pip install sounddevice` |
| `No module named 'numba'` | `pip install numba` (optional) |
| `No audio devices found` | Check audio hardware/drivers |

---

## Tips and Tricks

### Sound Design

1. **Layer oscillators**: Mix different waveforms for complex timbres
2. **Use filter envelope**: Modulate cutoff for evolving sounds
3. **Add subtle chorus**: Makes sounds wider and more professional
4. **Detune slightly**: 5-10 cents of detune adds warmth

### Performance

1. **Install numba**: Significant performance improvement
2. **Use lower buffer sizes**: For lower latency (may cause glitches)
3. **Reduce polyphony**: Play single notes for less CPU load

### Creative Ideas

1. **Acid bass**: Low cutoff, high resonance, fast filter decay
2. **Pad sounds**: Slow attack, high sustain, long release, chorus
3. **Pluck sounds**: Fast attack, fast decay, zero sustain
4. **Lead sounds**: Medium attack, full sustain, vibrato via LFO

---

## Keyboard Shortcuts Reference

| Shortcut | Action |
|----------|--------|
| Z-/ | Play lower octave |
| Q-P | Play upper octave |
| 2-0 (number row) | Black keys |
| Escape | Panic (all notes off) |
| Ctrl+S | Save preset |
| Ctrl+O | Open preset |

---

## Support

For issues, feature requests, or contributions, please visit the project repository or contact the development team.

**Version**: 1.0.0
**Sample Rate**: 44100 Hz
**Buffer Size**: 512 samples
**Polyphony**: 8 voices
**Effects**: Reverb, Delay, Chorus, Flanger, Distortion
