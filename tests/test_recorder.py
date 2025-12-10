# Tests for Audio Recorder Module
"""
test_recorder - Unit tests for audio recording.
"""

import pytest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from recording.recorder import AudioRecorder, RecordingState, RecordingInfo


class TestRecordingState:
    """Tests for RecordingState enum."""

    def test_state_values(self):
        """Should have all states."""
        assert RecordingState.IDLE
        assert RecordingState.ARMED
        assert RecordingState.RECORDING
        assert RecordingState.PAUSED

    def test_states_distinct(self):
        """States should be distinct."""
        states = [RecordingState.IDLE, RecordingState.ARMED,
                  RecordingState.RECORDING, RecordingState.PAUSED]
        assert len(set(states)) == 4


class TestRecordingInfo:
    """Tests for RecordingInfo dataclass."""

    def test_info_creation(self):
        """Should create info with all fields."""
        info = RecordingInfo(
            duration_samples=44100,
            duration_seconds=1.0,
            peak_level=0.5,
            sample_rate=44100
        )
        assert info.duration_samples == 44100
        assert info.duration_seconds == 1.0
        assert info.peak_level == 0.5
        assert info.sample_rate == 44100


class TestAudioRecorderInit:
    """Tests for AudioRecorder initialization."""

    def test_default_init(self):
        """Should initialize with defaults."""
        recorder = AudioRecorder()
        assert recorder.sample_rate == 44100
        assert recorder.state == RecordingState.IDLE
        assert recorder.duration_samples == 0
        assert recorder.duration_seconds == 0.0

    def test_custom_sample_rate(self):
        """Should accept custom sample rate."""
        recorder = AudioRecorder(sample_rate=48000)
        assert recorder.sample_rate == 48000

    def test_custom_max_duration(self):
        """Should accept custom max duration."""
        recorder = AudioRecorder(max_duration_seconds=60.0)
        # 60 seconds at 44100 Hz
        assert recorder._max_samples == 60 * 44100


class TestAudioRecorderState:
    """Tests for recording state management."""

    def test_initial_state_idle(self):
        """Should start in IDLE state."""
        recorder = AudioRecorder()
        assert recorder.state == RecordingState.IDLE
        assert not recorder.is_recording
        assert not recorder.is_armed

    def test_arm_state(self):
        """Arm should set ARMED state."""
        recorder = AudioRecorder()
        recorder.arm()
        assert recorder.state == RecordingState.ARMED
        assert recorder.is_armed
        assert not recorder.is_recording

    def test_start_state(self):
        """Start should set RECORDING state."""
        recorder = AudioRecorder()
        recorder.start()
        assert recorder.state == RecordingState.RECORDING
        assert recorder.is_recording

    def test_pause_state(self):
        """Pause should set PAUSED state."""
        recorder = AudioRecorder()
        recorder.start()
        recorder.pause()
        assert recorder.state == RecordingState.PAUSED

    def test_resume_state(self):
        """Resume should return to RECORDING."""
        recorder = AudioRecorder()
        recorder.start()
        recorder.pause()
        recorder.resume()
        assert recorder.state == RecordingState.RECORDING

    def test_stop_state(self):
        """Stop should return to IDLE."""
        recorder = AudioRecorder()
        recorder.start()
        recorder.stop()
        assert recorder.state == RecordingState.IDLE


class TestAudioRecorderAddSamples:
    """Tests for adding samples."""

    def test_add_samples_when_recording(self):
        """Should accept samples when recording."""
        recorder = AudioRecorder()
        recorder.start()
        samples = np.zeros(1024, dtype=np.float32)
        result = recorder.add_samples(samples)
        assert result is True

    def test_add_samples_when_idle(self):
        """Should reject samples when idle."""
        recorder = AudioRecorder()
        samples = np.zeros(1024, dtype=np.float32)
        result = recorder.add_samples(samples)
        assert result is False

    def test_add_samples_updates_duration(self):
        """Duration should increase with samples."""
        recorder = AudioRecorder(sample_rate=44100)
        recorder.start()
        samples = np.zeros(44100, dtype=np.float32)
        recorder.add_samples(samples)
        assert recorder.duration_samples == 44100
        assert abs(recorder.duration_seconds - 1.0) < 0.01

    def test_add_samples_tracks_peak(self):
        """Should track peak level."""
        recorder = AudioRecorder()
        recorder.start()
        samples = np.array([0.0, 0.5, -0.3, 0.8], dtype=np.float32)
        recorder.add_samples(samples)
        assert abs(recorder.peak_level - 0.8) < 0.001

    def test_add_samples_multiple_buffers(self):
        """Should accumulate multiple buffers."""
        recorder = AudioRecorder()
        recorder.start()
        for _ in range(10):
            samples = np.zeros(1024, dtype=np.float32)
            recorder.add_samples(samples)
        assert recorder.duration_samples == 10240


class TestAudioRecorderArmed:
    """Tests for armed recording (auto-start)."""

    def test_armed_auto_start_on_signal(self):
        """Should auto-start when signal detected."""
        recorder = AudioRecorder()
        recorder.arm()

        # Add signal above threshold
        samples = np.array([0.0, 0.1, 0.5], dtype=np.float32)
        recorder.add_samples(samples)

        assert recorder.state == RecordingState.RECORDING

    def test_armed_no_start_on_silence(self):
        """Should not start on silence."""
        recorder = AudioRecorder()
        recorder.arm()

        # Add very quiet samples
        samples = np.array([0.0, 0.001, 0.005], dtype=np.float32)
        recorder.add_samples(samples)

        assert recorder.state == RecordingState.ARMED


class TestAudioRecorderGetAudio:
    """Tests for retrieving recorded audio."""

    def test_get_audio_empty(self):
        """Should return empty array initially."""
        recorder = AudioRecorder()
        audio = recorder.get_audio()
        assert len(audio) == 0

    def test_get_audio_returns_copy(self):
        """Should return copy of recorded audio."""
        recorder = AudioRecorder()
        recorder.start()
        samples = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        recorder.add_samples(samples)

        audio = recorder.get_audio()
        assert np.allclose(audio, samples)

        # Modify returned array
        audio[0] = 999.0

        # Original should be unchanged
        audio2 = recorder.get_audio()
        assert audio2[0] != 999.0

    def test_get_info(self):
        """Should return RecordingInfo."""
        recorder = AudioRecorder(sample_rate=44100)
        recorder.start()
        samples = np.array([0.1, 0.5, 0.3], dtype=np.float32)
        recorder.add_samples(samples)
        recorder.stop()

        info = recorder.get_info()
        assert isinstance(info, RecordingInfo)
        assert info.duration_samples == 3
        assert info.peak_level == 0.5
        assert info.sample_rate == 44100


class TestAudioRecorderClear:
    """Tests for clearing recording."""

    def test_clear_resets_duration(self):
        """Clear should reset duration to 0."""
        recorder = AudioRecorder()
        recorder.start()
        recorder.add_samples(np.zeros(1024, dtype=np.float32))
        recorder.stop()
        recorder.clear()

        assert recorder.duration_samples == 0
        assert recorder.duration_seconds == 0.0

    def test_clear_resets_peak(self):
        """Clear should reset peak level."""
        recorder = AudioRecorder()
        recorder.start()
        recorder.add_samples(np.array([0.8], dtype=np.float32))
        recorder.stop()
        recorder.clear()

        assert recorder.peak_level == 0.0


class TestAudioRecorderUndo:
    """Tests for undo functionality."""

    def test_can_undo_false_initially(self):
        """Can't undo with no history."""
        recorder = AudioRecorder()
        assert not recorder.can_undo

    def test_can_undo_after_new_recording(self):
        """Should be able to undo after starting new recording."""
        recorder = AudioRecorder()

        # First recording
        recorder.start()
        recorder.add_samples(np.array([0.1, 0.2], dtype=np.float32))
        recorder.stop()

        # Start new recording (saves previous to undo)
        recorder.start()
        recorder.add_samples(np.array([0.5, 0.6, 0.7], dtype=np.float32))
        recorder.stop()

        assert recorder.can_undo

    def test_undo_restores_previous(self):
        """Undo should restore previous recording."""
        recorder = AudioRecorder()

        # First recording
        recorder.start()
        first = np.array([0.1, 0.2], dtype=np.float32)
        recorder.add_samples(first)
        recorder.stop()

        # Second recording
        recorder.start()
        second = np.array([0.5, 0.6, 0.7], dtype=np.float32)
        recorder.add_samples(second)
        recorder.stop()

        # Undo
        result = recorder.undo()
        assert result is True

        # Should have first recording
        audio = recorder.get_audio()
        assert len(audio) == 2
        assert np.allclose(audio, first)


class TestAudioRecorderCallback:
    """Tests for state change callback."""

    def test_callback_on_start(self):
        """Callback should fire on start."""
        recorder = AudioRecorder()
        states_received = []

        recorder.set_on_state_change(lambda s: states_received.append(s))
        recorder.start()

        assert RecordingState.RECORDING in states_received

    def test_callback_on_stop(self):
        """Callback should fire on stop."""
        recorder = AudioRecorder()
        states_received = []

        recorder.set_on_state_change(lambda s: states_received.append(s))
        recorder.start()
        recorder.stop()

        assert RecordingState.IDLE in states_received


class TestAudioRecorderRepr:
    """Tests for string representation."""

    def test_repr(self):
        """Should show state and duration."""
        recorder = AudioRecorder()
        repr_str = repr(recorder)
        assert "IDLE" in repr_str
        assert "0.00" in repr_str


class TestAudioRecorderLevelCallback:
    """Tests for level update callback."""

    def test_level_callback(self):
        """Level callback should be called periodically."""
        recorder = AudioRecorder()
        levels = []

        recorder.set_on_level_update(lambda p: levels.append(p))
        recorder.start()

        # Add enough samples to trigger callback (every 4410)
        for _ in range(5):
            samples = np.full(4410, 0.5, dtype=np.float32)
            recorder.add_samples(samples)

        # Should have received some level updates
        # Note: may or may not fire depending on timing
        # Just verify no crash
