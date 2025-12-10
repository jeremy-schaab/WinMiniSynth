# Recording Module
"""
recording - Audio recording, metronome, and storage components.

This module provides:
- Metronome: Click track generation with configurable tempo/time signature
- AudioRecorder: Real-time audio capture with ring buffer
- FileExporter: WAV file export functionality
- PresetStorage: JSON preset save/load

Usage:
    from recording import Metronome, AudioRecorder, FileExporter, PresetStorage

    # Metronome
    metro = Metronome(bpm=120, time_signature=(4, 4))
    samples = metro.generate(num_samples)

    # Recording
    recorder = AudioRecorder()
    recorder.start()
    recorder.add_samples(audio_buffer)
    recorder.stop()

    # Export
    exporter = FileExporter()
    exporter.export_wav(recorder.get_audio(), 'output.wav')

    # Presets
    storage = PresetStorage()
    storage.save_preset('my_preset', params)
    params = storage.load_preset('my_preset')
"""

# BOLT-005: Metronome & Recording
from .metronome import Metronome, TimeSignature, ClickSound
from .recorder import AudioRecorder, RecordingState
from .file_export import FileExporter, ExportFormat, ExportConfig
from .preset_storage import PresetStorage, Preset

__all__ = [
    # Metronome
    'Metronome',
    'TimeSignature',
    'ClickSound',
    # Recorder
    'AudioRecorder',
    'RecordingState',
    # File export
    'FileExporter',
    'ExportFormat',
    'ExportConfig',
    # Preset storage
    'PresetStorage',
    'Preset',
]
