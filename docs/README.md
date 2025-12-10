# WinMiniSynth Documentation

## Overview

WinMiniSynth (KarokeLite Mini Synthesizer) is a virtual analog synthesizer built with Python. This documentation covers installation, usage, architecture, and API reference.

## Documentation Index

| Document | Description | Audience |
|----------|-------------|----------|
| [User Guide](USER_GUIDE.md) | Installation, usage, keyboard controls, features | End Users |
| [Architecture](ARCHITECTURE.md) | System design, module structure, audio pipeline | Developers |
| [API Reference](API_REFERENCE.md) | Module documentation, classes, methods | Developers |

---

## Quick Links

### Getting Started
- [Installation](USER_GUIDE.md#installation)
- [Quick Start](USER_GUIDE.md#quick-start)
- [Keyboard Controls](USER_GUIDE.md#keyboard-controls)

### Using the Synthesizer
- [User Interface](USER_GUIDE.md#user-interface)
- [Synthesis Parameters](USER_GUIDE.md#synthesis-parameters)
- [Effects](USER_GUIDE.md#effects)
- [Presets](USER_GUIDE.md#presets)
- [Recording](USER_GUIDE.md#recording)
- [Demo Songs](USER_GUIDE.md#demo-songs)

### Technical Reference
- [System Overview](ARCHITECTURE.md#system-overview)
- [Audio Pipeline](ARCHITECTURE.md#audio-pipeline)
- [Module Structure](ARCHITECTURE.md#module-structure)
- [Threading Model](ARCHITECTURE.md#threading-model)

### API Documentation
- [Synth Module](API_REFERENCE.md#synth-module)
- [Effects Module](API_REFERENCE.md#effects-module)
- [Recording Module](API_REFERENCE.md#recording-module)
- [GUI Module](API_REFERENCE.md#gui-module)

---

## Features at a Glance

### Synthesis Engine
- 8-voice polyphony with voice stealing
- Dual oscillators (Sine, Saw, Square, Triangle, Pulse)
- 4-pole Moog-style ladder filter
- ADSR envelopes for amplitude and filter
- LFO with multiple waveform shapes
- Pitch, filter, and pulse width modulation

### Effects
- **Reverb**: Schroeder algorithm room simulation
- **Delay**: Digital delay with feedback (10-2000ms)
- **Chorus**: Multi-voice modulated delay (2-4 voices)
- **Flanger**: Short modulated delay with feedback
- **Distortion**: Soft, hard, and tube waveshaping modes

### User Interface
- Virtual piano keyboard with 2-octave range
- Real-time oscilloscope waveform display
- Filter frequency response curve
- Comprehensive parameter controls
- Preset management system

### Recording & Playback
- Real-time audio recording (up to 30 minutes)
- WAV export functionality
- 8 built-in demo songs
- Song player with progress tracking

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11, macOS, Linux |
| Python | 3.10 or higher |
| RAM | 4GB minimum (8GB recommended) |
| Audio | Working audio output device |
| Display | 1280x720 minimum resolution |

---

## Installation

### From Source
```bash
git clone https://github.com/your-repo/WinMiniSynth.git
cd WinMiniSynth
pip install -e .
```

### Running
```bash
python -m src
```

---

## Quick Reference

### Keyboard Layout
```
Lower Octave:     Z S X D C V G B H N J M , L . ; /
Upper Octave:     Q 2 W 3 E R 5 T 6 Y 7 U I 9 O 0 P
```

### Factory Presets
| Preset | Sound Type |
|--------|------------|
| Init | Neutral starting point |
| Fat Bass | Deep, punchy bass |
| Bright Lead | Cutting lead melody |
| Soft Pad | Gentle ambient texture |
| Retro Square | Classic 8-bit chiptune |
| Ethereal Strings | Lush ensemble |
| Plucky Keys | Quick attack plucks |
| Warm Organ | Hammond-style organ |
| Acid Squelch | 303-style acid |
| Cosmic Bell | Metallic bells |

### Effects Chain Order
```
Input -> Distortion -> Chorus -> Delay -> Flanger -> Reverb -> Output
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No sound | Check volume, audio device, voice count |
| Audio glitches | Increase buffer size, install numba |
| High CPU | Disable effects, install numba |
| Keys not working | Click on keyboard to focus |

For detailed troubleshooting, see [User Guide - Troubleshooting](USER_GUIDE.md#troubleshooting).

---

## Contributing

Contributions are welcome! Please read the architecture documentation before making changes to understand the system design.

### Key Extension Points
- Adding new waveforms
- Adding new effects
- Adding MIDI support
- Performance optimization

See [Architecture - Extension Points](ARCHITECTURE.md#extension-points) for details.

---

## Technical Specifications

| Specification | Value |
|---------------|-------|
| Sample Rate | 44100 Hz |
| Bit Depth | 32-bit float |
| Buffer Size | 512 samples |
| Latency | ~11.6 ms |
| Polyphony | 8 voices |
| Channels | Mono |

---

## License

See LICENSE file in the project root.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024 | Initial release with full feature set |

---

## Contact

For issues, feature requests, or contributions, please visit the project repository.
