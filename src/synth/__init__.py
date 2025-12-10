# Audio Synthesis Engine
"""
synth - Core audio synthesis components for the Mini Synthesizer.

This module provides the audio generation pipeline:
- Oscillator: Waveform generation (sine, saw, square, triangle, pulse)
- ADSREnvelope: Amplitude/filter envelope shaping
- MoogFilter: 4-pole ladder lowpass filter
- LFO: Low-frequency oscillator for modulation
- SynthVoice: Complete voice with all components (BOLT-002)
- MiniSynth: Polyphonic synthesizer aggregate (BOLT-002)
- AudioEngine: sounddevice output management

Usage:
    from synth import MiniSynth, AudioEngine

    synth = MiniSynth()
    engine = AudioEngine()
    engine.set_callback(synth.generate)
    engine.start()
"""

# BOLT-001: Core Synthesis Engine Components
from .oscillator import Oscillator, Waveform, midi_to_frequency
from .envelope import ADSREnvelope, EnvelopeStage
from .filter import MoogFilter
from .lfo import LFO
from .engine import AudioEngine, AudioConfig, MockAudioEngine

# BOLT-002: Polyphony & Voice Management
from .voice import SynthVoice, VoiceParameters
from .synth import MiniSynth, VoiceStealingStrategy, SynthState

__all__ = [
    # Oscillator
    'Oscillator',
    'Waveform',
    'midi_to_frequency',
    # Envelope
    'ADSREnvelope',
    'EnvelopeStage',
    # Filter
    'MoogFilter',
    # LFO
    'LFO',
    # Engine
    'AudioEngine',
    'AudioConfig',
    'MockAudioEngine',
    # Voice (BOLT-002)
    'SynthVoice',
    'VoiceParameters',
    # Synth (BOLT-002)
    'MiniSynth',
    'VoiceStealingStrategy',
    'SynthState',
]
