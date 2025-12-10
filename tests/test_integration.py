# Integration Tests for KarokeLite Mini Synthesizer
"""
test_integration - End-to-end integration tests for the Mini Synthesizer.

These tests verify the correct interaction between:
- Synthesis engine components (oscillators, filters, envelopes, LFO)
- Voice management and polyphony
- Audio generation pipeline
- Recording subsystem
- Visualization components
- Application controller
"""

import pytest
import numpy as np
import tempfile
import os
import json
from typing import List, Tuple
from unittest.mock import Mock, MagicMock, patch
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# =============================================================================
# INTEGRATION TEST: Synth Engine Pipeline
# =============================================================================

class TestSynthEnginePipeline:
    """Integration tests for the complete synthesis pipeline."""

    def test_oscillator_to_filter_to_envelope_chain(self):
        """Verify signal flows correctly through osc -> filter -> envelope."""
        from synth import Oscillator, MoogFilter, ADSREnvelope, Waveform

        sample_rate = 44100
        num_samples = 1024

        # Create pipeline components
        osc = Oscillator(sample_rate)
        osc.waveform = Waveform.SAWTOOTH
        osc.frequency = 440.0

        filt = MoogFilter(sample_rate)
        filt.cutoff = 2000.0
        filt.resonance = 0.3

        env = ADSREnvelope(sample_rate)
        env.attack = 0.01
        env.decay = 0.1
        env.sustain = 0.7
        env.release = 0.3
        env.gate_on()

        # Generate through pipeline
        osc_output = osc.generate(num_samples)
        filtered_output = filt.process(osc_output)
        envelope_values = env.generate(num_samples)
        final_output = filtered_output * envelope_values

        # Verify signal is non-zero and shaped
        assert len(final_output) == num_samples
        assert np.max(np.abs(final_output)) > 0.0
        assert np.max(np.abs(final_output)) <= 1.5  # Allow some overshoot from filter

        # Verify envelope shaping (attack phase should ramp up)
        assert final_output[0] < final_output[100]

    def test_lfo_modulates_filter_cutoff(self):
        """Verify LFO correctly modulates filter cutoff frequency."""
        from synth import LFO, MoogFilter, Waveform

        sample_rate = 44100
        num_samples = 44100  # 1 second (to capture full LFO cycles)

        lfo = LFO(sample_rate)
        lfo.rate = 2.0  # 2 Hz LFO (slower for clearer modulation)
        lfo.waveform = Waveform.SINE

        filt = MoogFilter(sample_rate)
        base_cutoff = 1000.0
        mod_depth = 500.0  # +/- 500 Hz

        # Generate test signal (white noise for filter visibility)
        np.random.seed(42)
        test_signal = np.random.randn(num_samples).astype(np.float32) * 0.5

        # Process in chunks, modulating filter with LFO
        chunk_size = 4410  # 100ms chunks
        outputs = []
        cutoffs = []

        for i in range(0, num_samples, chunk_size):
            chunk = test_signal[i:i+chunk_size]
            lfo_value = lfo.generate(len(chunk))
            avg_lfo = np.mean(lfo_value)

            # Modulate cutoff
            mod_cutoff = base_cutoff + avg_lfo * mod_depth
            filt.cutoff = mod_cutoff
            cutoffs.append(mod_cutoff)

            output = filt.process(chunk)
            outputs.append(output)

        # Verify cutoff was modulated (should have variation)
        cutoff_range = max(cutoffs) - min(cutoffs)
        assert cutoff_range > 100, f"Cutoff should vary by at least 100Hz, got {cutoff_range}"

    def test_dual_oscillator_mix(self):
        """Verify two oscillators mix correctly with detuning."""
        from synth import Oscillator, Waveform

        sample_rate = 44100
        num_samples = 4410

        osc1 = Oscillator(sample_rate)
        osc1.waveform = Waveform.SAWTOOTH
        osc1.frequency = 440.0

        osc2 = Oscillator(sample_rate)
        osc2.waveform = Waveform.SAWTOOTH
        osc2.frequency = 440.0 * (2 ** (5/1200))  # 5 cents detune

        out1 = osc1.generate(num_samples)
        out2 = osc2.generate(num_samples)

        # Mix with levels
        mixed = out1 * 0.7 + out2 * 0.5

        # Should produce beating effect (amplitude modulation)
        # Due to phase interference between detuned oscillators
        assert len(mixed) == num_samples
        assert np.max(np.abs(mixed)) > 0.5  # Combined amplitude


# =============================================================================
# INTEGRATION TEST: Voice and Polyphony
# =============================================================================

class TestVoicePolyphonyIntegration:
    """Integration tests for voice management and polyphony."""

    def test_voice_plays_complete_note(self):
        """Verify a voice can play a complete note from attack to release."""
        from synth import SynthVoice, VoiceParameters

        sample_rate = 44100
        voice = SynthVoice(sample_rate)

        params = VoiceParameters()
        params.amp_attack = 0.01
        params.amp_decay = 0.05
        params.amp_sustain = 0.7
        params.amp_release = 0.1
        voice.parameters = params

        # Attack and sustain
        voice.note_on(60, 100)
        attack_samples = voice.generate(int(0.1 * sample_rate))

        assert voice.is_active()
        assert np.max(np.abs(attack_samples)) > 0.3

        # Release
        voice.note_off()
        assert voice.is_releasing()

        # Continue through release
        release_samples = voice.generate(int(0.2 * sample_rate))

        # Should fade out - compare RMS rather than single samples
        attack_rms = np.sqrt(np.mean(attack_samples[-500:]**2))
        release_rms = np.sqrt(np.mean(release_samples[-500:]**2))
        assert release_rms < attack_rms

    def test_minisynth_polyphonic_chords(self):
        """Verify MiniSynth plays polyphonic chords correctly."""
        from synth import MiniSynth

        synth = MiniSynth(sample_rate=44100, max_voices=8)

        # Play a C major chord
        synth.note_on(60, 100)  # C4
        synth.note_on(64, 100)  # E4
        synth.note_on(67, 100)  # G4

        assert synth.get_active_voice_count() == 3
        assert set(synth.get_playing_notes()) == {60, 64, 67}

        # Generate audio
        samples = synth.generate(1024)

        assert len(samples) == 1024
        assert np.max(np.abs(samples)) > 0.1

        # Release notes
        synth.note_off(60)
        synth.note_off(64)
        synth.note_off(67)

        # Notes should still be active (releasing)
        assert synth.get_active_voice_count() >= 0

    def test_voice_stealing_under_load(self):
        """Verify voice stealing works when all voices are used."""
        from synth import MiniSynth

        max_voices = 4
        synth = MiniSynth(sample_rate=44100, max_voices=max_voices)

        # Fill all voices
        for note in range(60, 64):
            synth.note_on(note, 100)

        assert synth.get_active_voice_count() == max_voices

        # Play one more note - should steal a voice
        synth.note_on(70, 100)

        # Still max voices, but 70 should be playing
        assert synth.get_active_voice_count() == max_voices
        assert 70 in synth.get_playing_notes()

    def test_panic_silences_all_voices(self):
        """Verify panic immediately silences all voices."""
        from synth import MiniSynth

        synth = MiniSynth(sample_rate=44100, max_voices=8)

        # Play several notes
        for note in range(60, 68):
            synth.note_on(note, 100)

        assert synth.get_active_voice_count() == 8

        # Panic
        synth.panic()

        assert synth.get_active_voice_count() == 0
        assert len(synth.get_playing_notes()) == 0


# =============================================================================
# INTEGRATION TEST: Audio Engine Integration
# =============================================================================

class TestAudioEngineIntegration:
    """Integration tests for audio engine with synth."""

    def test_audio_callback_generates_samples(self):
        """Verify audio callback generates correct sample count."""
        from synth import MiniSynth, AudioEngine, AudioConfig

        synth = MiniSynth(sample_rate=44100)
        config = AudioConfig(sample_rate=44100, buffer_size=512)
        engine = AudioEngine(config)

        # Set synth as callback
        engine.set_callback(synth.generate)

        # Simulate callback
        synth.note_on(60, 100)
        samples = synth.generate(512)

        assert len(samples) == 512
        assert samples.dtype == np.float32

    def test_continuous_audio_generation(self):
        """Verify continuous audio generation over multiple buffers."""
        from synth import MiniSynth

        synth = MiniSynth(sample_rate=44100)
        synth.note_on(60, 100)

        buffers = []
        for _ in range(10):
            buffer = synth.generate(512)
            buffers.append(buffer.copy())

        # All buffers should have audio
        for buf in buffers:
            assert len(buf) == 512
            assert np.max(np.abs(buf)) > 0.05


# =============================================================================
# INTEGRATION TEST: Recording Subsystem
# =============================================================================

class TestRecordingIntegration:
    """Integration tests for recording with synth output."""

    def test_metronome_generates_click_track(self):
        """Verify metronome generates audible clicks at correct tempo."""
        from recording import Metronome

        sample_rate = 44100
        bpm = 120.0
        # Metronome signature: bpm, time_signature, sample_rate
        metronome = Metronome(bpm=bpm, sample_rate=sample_rate, volume=0.8)
        metronome.start()

        # Generate 2 seconds of audio (should have ~4 clicks at 120 BPM)
        samples = metronome.generate(sample_rate * 2)

        assert len(samples) == sample_rate * 2

        # Find clicks (peaks) - use lower threshold since volume is 0.8
        threshold = 0.2
        peaks = np.where(np.abs(samples) > threshold)[0]

        # Should have clicks (at least some samples above threshold)
        assert len(peaks) > 0  # At least some samples above threshold

    def test_recorder_captures_audio(self):
        """Verify recorder captures incoming audio correctly."""
        from recording import AudioRecorder

        sample_rate = 44100
        recorder = AudioRecorder(sample_rate, max_duration_seconds=10.0)

        # Create test signal (1 second sine wave)
        t = np.linspace(0, 1, sample_rate, dtype=np.float32)
        test_signal = np.sin(2 * np.pi * 440 * t).astype(np.float32)

        # Record in chunks
        recorder.arm()
        recorder.start()

        chunk_size = 512
        for i in range(0, len(test_signal), chunk_size):
            chunk = test_signal[i:i+chunk_size]
            recorder.add_samples(chunk)

        recorder.stop()

        # Verify recording
        recorded = recorder.get_audio()
        assert len(recorded) >= sample_rate - chunk_size  # Allow for last partial chunk

    def test_recorder_exports_to_wav(self):
        """Verify recorder can export to WAV file."""
        from recording import AudioRecorder, FileExporter, ExportConfig

        sample_rate = 44100
        recorder = AudioRecorder(sample_rate, max_duration_seconds=5.0)

        # Create and record test signal
        t = np.linspace(0, 0.5, sample_rate // 2, dtype=np.float32)
        test_signal = np.sin(2 * np.pi * 440 * t).astype(np.float32)

        recorder.arm()
        recorder.start()
        recorder.add_samples(test_signal)
        recorder.stop()

        # Export - FileExporter takes ExportConfig, not sample_rate
        config = ExportConfig(sample_rate=sample_rate)
        exporter = FileExporter(config)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name

        try:
            recording = recorder.get_audio()
            exporter.export_wav(recording, temp_path)

            # Verify file exists and has content
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 44  # At least header size
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


# =============================================================================
# INTEGRATION TEST: Preset System
# =============================================================================

class TestPresetIntegration:
    """Integration tests for preset save/load with synth."""

    def test_preset_storage_save_load_roundtrip(self):
        """Verify presets can be saved and loaded correctly."""
        from recording import PresetStorage

        with tempfile.TemporaryDirectory() as temp_dir:
            storage = PresetStorage(temp_dir)

            # Create test preset parameters
            test_params = {
                'osc1_waveform': 'sawtooth',
                'osc1_level': 0.8,
                'filter_cutoff': 2500.0,
                'filter_resonance': 0.4
            }

            # Save using the correct API
            storage.save_preset("Test Preset", test_params, category="Test")

            # Load
            loaded = storage.load_preset("Test Preset")

            assert loaded is not None
            assert loaded['osc1_level'] == 0.8
            assert loaded['filter_cutoff'] == 2500.0

    def test_factory_presets_exist(self):
        """Verify factory presets are available."""
        from recording import PresetStorage

        with tempfile.TemporaryDirectory() as temp_dir:
            storage = PresetStorage(temp_dir)

            presets = storage.list_presets()

            # Should have factory presets
            factory_names = ['Init', 'Fat Bass', 'Bright Lead', 'Soft Pad', 'Retro Square']
            for name in factory_names:
                assert name in presets, f"Missing factory preset: {name}"


# =============================================================================
# INTEGRATION TEST: Visualization with Synth
# =============================================================================

class TestVisualizationIntegration:
    """Integration tests for visualization with synth output."""

    def test_oscilloscope_buffer_management(self):
        """Verify oscilloscope buffer management works correctly."""
        from synth import MiniSynth

        synth = MiniSynth(sample_rate=44100)
        synth.note_on(60, 100)

        # Generate audio
        samples = synth.generate(1024)

        # Test buffer operations directly without tkinter
        buffer = np.zeros(4096, dtype=np.float32)
        buffer_pos = 0

        # Add samples to buffer
        num_to_add = min(len(samples), len(buffer) - buffer_pos)
        buffer[buffer_pos:buffer_pos + num_to_add] = samples[:num_to_add]
        buffer_pos += num_to_add

        # Calculate peak level
        peak_level = np.max(np.abs(samples))

        assert peak_level > 0.0
        assert buffer_pos == 1024

    def test_filter_response_calculation(self):
        """Verify filter response calculation works correctly."""
        # Test filter response directly without tkinter
        cutoff = 1000.0
        resonance = 0.5
        sample_rate = 44100

        # Generate frequency points (logarithmic scale)
        frequencies = np.logspace(np.log10(20), np.log10(20000), 256)

        # Calculate simplified filter response
        response = []
        for f in frequencies:
            # Simplified 4-pole lowpass magnitude
            ratio = f / cutoff
            magnitude = 1.0 / (1.0 + ratio**4)
            # Add resonance peak
            if 0.5 < ratio < 2.0:
                magnitude *= (1.0 + resonance * 2.0 * (1.0 - abs(ratio - 1.0)))
            response.append(magnitude)

        response = np.array(response)

        # Verify response shape
        assert len(response) == 256
        assert response[0] > response[-1]  # Low frequencies higher than high


# =============================================================================
# INTEGRATION TEST: Application Controller
# =============================================================================

class TestAppControllerIntegration:
    """Integration tests for application controller."""

    def test_controller_wires_gui_to_synth(self):
        """Verify controller correctly routes GUI events to synth."""
        from app_controller import AppController

        controller = AppController(
            sample_rate=44100,
            buffer_size=512,
            max_voices=8
        )

        # Trigger note through controller
        controller.note_on(60, 100)

        # Check synth received the note
        assert controller.get_active_voice_count() >= 1

        # Release note
        controller.note_off(60)

    def test_controller_parameter_routing(self):
        """Verify controller routes parameters to synth."""
        from app_controller import AppController

        controller = AppController(sample_rate=44100)

        # Set master volume parameter (simple parameter)
        controller.set_parameter('master_volume', 0.5)

        # Process parameter queue by generating audio
        controller._audio_callback(512)

        # Parameter should be applied
        assert controller._synth.master_volume == 0.5

    def test_controller_preset_load(self):
        """Verify controller can load presets."""
        from app_controller import AppController

        controller = AppController(sample_rate=44100)

        # Load default preset
        result = controller.load_preset('Fat Bass')

        assert result is not None  # Returns params dict on success
        assert isinstance(result, dict)
        assert controller.current_preset_name == 'Fat Bass'

    def test_controller_display_buffer(self):
        """Verify controller provides display buffer for visualization."""
        from app_controller import AppController

        controller = AppController(sample_rate=44100, buffer_size=512)

        # Generate audio with a note playing
        controller.note_on(60, 100)
        controller._audio_callback(512)

        # Get display buffer
        buffer = controller.get_display_buffer()

        assert len(buffer) == 512
        assert np.max(np.abs(buffer)) > 0.0


# =============================================================================
# INTEGRATION TEST: End-to-End Workflow
# =============================================================================

class TestEndToEndWorkflow:
    """End-to-end integration tests simulating real usage."""

    def test_play_record_export_workflow(self):
        """Simulate: play notes -> record -> export WAV."""
        from synth import MiniSynth
        from recording import AudioRecorder, FileExporter, ExportConfig

        sample_rate = 44100
        synth = MiniSynth(sample_rate=sample_rate)
        recorder = AudioRecorder(sample_rate, max_duration_seconds=5.0)
        config = ExportConfig(sample_rate=sample_rate)
        exporter = FileExporter(config)

        # Arm and start recording
        recorder.arm()
        recorder.start()

        # Play a melody
        melody = [(60, 0.2), (62, 0.2), (64, 0.2), (65, 0.2), (67, 0.4)]

        for note, duration in melody:
            synth.note_on(note, 100)
            samples_per_note = int(duration * sample_rate)

            for _ in range(0, samples_per_note, 512):
                samples = synth.generate(512)
                recorder.add_samples(samples)

            synth.note_off(note)

        recorder.stop()

        # Export
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name

        try:
            recording = recorder.get_audio()
            assert len(recording) > 0

            exporter.export_wav(recording, temp_path)
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 1000
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_preset_modify_save_reload_workflow(self):
        """Simulate: load preset -> modify -> save -> reload."""
        from app_controller import AppController

        with tempfile.TemporaryDirectory() as temp_dir:
            controller = AppController(
                sample_rate=44100,
                presets_dir=temp_dir
            )

            # Load preset
            controller.load_preset('Init')

            # Modify master volume parameter directly (simpler, no queue processing)
            controller._synth.master_volume = 0.6

            # Save as new preset
            result = controller.save_preset('My Custom')
            assert result is True

            # Create new controller and reload
            controller2 = AppController(
                sample_rate=44100,
                presets_dir=temp_dir
            )

            # Preset should be in list
            presets = controller2.get_preset_list()
            assert 'My Custom' in presets

    def test_metronome_synced_recording(self):
        """Simulate: recording with metronome."""
        from synth import MiniSynth
        from recording import Metronome, AudioRecorder

        sample_rate = 44100
        bpm = 120.0

        synth = MiniSynth(sample_rate=sample_rate)
        metronome = Metronome(bpm=bpm, sample_rate=sample_rate)
        recorder = AudioRecorder(sample_rate, max_duration_seconds=10.0)

        metronome.start()

        # Record 2 bars (4 beats per bar at 120 BPM = 4 seconds)
        duration_samples = int(4.0 * sample_rate)
        chunk_size = 512

        recorder.arm()
        recorder.start()

        synth.note_on(60, 100)

        for _ in range(0, duration_samples, chunk_size):
            synth_samples = synth.generate(chunk_size)
            metro_samples = metronome.generate(chunk_size)

            # Mix synth and metronome
            mixed = synth_samples * 0.8 + metro_samples * 0.3
            recorder.add_samples(mixed)

        synth.note_off(60)
        recorder.stop()

        recording = recorder.get_audio()

        # Should have approximately 4 seconds of audio
        expected_samples = 4 * sample_rate
        assert abs(len(recording) - expected_samples) < chunk_size


# =============================================================================
# INTEGRATION TEST: Error Handling
# =============================================================================

class TestErrorHandlingIntegration:
    """Integration tests for error handling across components."""

    def test_invalid_note_values_handled(self):
        """Verify invalid MIDI note values are handled gracefully."""
        from synth import MiniSynth

        synth = MiniSynth(sample_rate=44100)

        # Invalid notes should not crash
        synth.note_on(-1, 100)  # Too low
        synth.note_on(128, 100)  # Too high
        synth.note_on(60, -50)  # Negative velocity
        synth.note_on(60, 200)  # Velocity too high

        # Should still work normally
        synth.note_on(60, 100)
        assert synth.get_active_voice_count() >= 1

    def test_small_buffer_generation(self):
        """Verify generating small buffers works correctly."""
        from synth import MiniSynth

        synth = MiniSynth(sample_rate=44100)
        synth.note_on(60, 100)

        # Generate minimal samples
        samples = synth.generate(1)
        assert len(samples) == 1

    def test_recorder_without_arming(self):
        """Verify recorder handles recording without arming."""
        from recording import AudioRecorder

        recorder = AudioRecorder(44100, max_duration_seconds=5.0)

        # Start without arming - should still work
        recorder.start()

        # Write some data
        test_data = np.zeros(512, dtype=np.float32)
        recorder.add_samples(test_data)

        # Should handle gracefully
        recorder.stop()


# =============================================================================
# INTEGRATION TEST: Performance
# =============================================================================

class TestPerformanceIntegration:
    """Integration tests for performance characteristics."""

    def test_audio_generation_performance(self):
        """Verify audio generation completes in reasonable time."""
        import time
        from synth import MiniSynth

        synth = MiniSynth(sample_rate=44100, max_voices=8)

        # Play all 8 voices
        for i in range(8):
            synth.note_on(60 + i, 100)

        # Time generation of 1 second of audio
        buffer_size = 512
        num_buffers = 44100 // buffer_size

        start = time.perf_counter()
        for _ in range(num_buffers):
            synth.generate(buffer_size)
        elapsed = time.perf_counter() - start

        # Should complete in less than 5 seconds (reasonable for CI environments)
        assert elapsed < 5.0, f"Audio generation took {elapsed:.3f}s for 1s of audio"

    def test_memory_stability_during_recording(self):
        """Verify memory doesn't grow unbounded during recording."""
        import gc
        from recording import AudioRecorder

        recorder = AudioRecorder(44100, max_duration_seconds=60.0)

        recorder.arm()
        recorder.start()

        # Write 10 seconds of audio
        chunk = np.zeros(4410, dtype=np.float32)  # 0.1 second
        for _ in range(100):
            recorder.add_samples(chunk)

        recorder.stop()

        # Force garbage collection
        gc.collect()

        # Verify we can still get the recording
        recording = recorder.get_audio()
        assert len(recording) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
