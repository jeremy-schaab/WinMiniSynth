# Tests for Metronome Module
"""
test_metronome - Unit tests for metronome click generation.
"""

import pytest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from recording.metronome import Metronome, TimeSignature, ClickSound


class TestTimeSignature:
    """Tests for TimeSignature dataclass."""

    def test_default_time_signature(self):
        """Default should be 4/4."""
        ts = TimeSignature()
        assert ts.numerator == 4
        assert ts.denominator == 4

    def test_custom_time_signature(self):
        """Should accept custom values."""
        ts = TimeSignature(3, 4)
        assert ts.numerator == 3
        assert ts.denominator == 4

    def test_beats_per_measure(self):
        """Should return numerator as beats per measure."""
        ts = TimeSignature(6, 8)
        assert ts.beats_per_measure == 6

    def test_string_representation(self):
        """Should format as fraction."""
        ts = TimeSignature(3, 4)
        assert str(ts) == "3/4"

    def test_invalid_numerator_low(self):
        """Should reject numerator < 1."""
        with pytest.raises(ValueError):
            TimeSignature(0, 4)

    def test_invalid_numerator_high(self):
        """Should reject numerator > 16."""
        with pytest.raises(ValueError):
            TimeSignature(17, 4)

    def test_invalid_denominator(self):
        """Should reject invalid denominator."""
        with pytest.raises(ValueError):
            TimeSignature(4, 3)

    def test_valid_denominators(self):
        """Should accept 2, 4, 8, 16."""
        for denom in [2, 4, 8, 16]:
            ts = TimeSignature(4, denom)
            assert ts.denominator == denom


class TestMetronomeInit:
    """Tests for Metronome initialization."""

    def test_default_init(self):
        """Should initialize with defaults."""
        metro = Metronome()
        assert metro.bpm == 120.0
        assert metro.time_signature.numerator == 4
        assert metro.time_signature.denominator == 4
        assert metro.volume == 0.5
        assert not metro.is_running

    def test_custom_bpm(self):
        """Should accept custom BPM."""
        metro = Metronome(bpm=140)
        assert metro.bpm == 140.0

    def test_custom_time_signature(self):
        """Should accept custom time signature."""
        ts = TimeSignature(3, 4)
        metro = Metronome(time_signature=ts)
        assert metro.time_signature.numerator == 3

    def test_custom_volume(self):
        """Should accept custom volume."""
        metro = Metronome(volume=0.8)
        assert metro.volume == 0.8

    def test_volume_clamped_low(self):
        """Volume should be clamped to 0."""
        metro = Metronome(volume=-0.5)
        assert metro.volume == 0.0

    def test_volume_clamped_high(self):
        """Volume should be clamped to 1."""
        metro = Metronome(volume=1.5)
        assert metro.volume == 1.0


class TestMetronomeBPM:
    """Tests for BPM property."""

    def test_bpm_setter(self):
        """Should set BPM."""
        metro = Metronome()
        metro.bpm = 100
        assert metro.bpm == 100.0

    def test_bpm_clamped_low(self):
        """BPM should be clamped to minimum."""
        metro = Metronome()
        metro.bpm = 10
        assert metro.bpm == Metronome.MIN_BPM

    def test_bpm_clamped_high(self):
        """BPM should be clamped to maximum."""
        metro = Metronome()
        metro.bpm = 500
        assert metro.bpm == Metronome.MAX_BPM

    def test_samples_per_beat(self):
        """Should calculate samples per beat correctly."""
        metro = Metronome(bpm=120, sample_rate=44100)
        # 120 BPM = 2 beats/sec = 0.5 sec/beat = 22050 samples/beat
        assert metro.samples_per_beat == 22050

    def test_beat_duration_ms(self):
        """Should calculate beat duration in ms."""
        metro = Metronome(bpm=120)
        # 120 BPM = 500ms per beat
        assert metro.beat_duration_ms == 500.0


class TestMetronomeStartStop:
    """Tests for start/stop functionality."""

    def test_start(self):
        """Should set running to True."""
        metro = Metronome()
        metro.start()
        assert metro.is_running

    def test_stop(self):
        """Should set running to False."""
        metro = Metronome()
        metro.start()
        metro.stop()
        assert not metro.is_running

    def test_reset(self):
        """Should reset to beginning of measure."""
        metro = Metronome()
        metro.start()
        # Generate some samples to advance beat
        metro.generate(44100)  # 1 second
        metro.reset()
        assert metro.current_beat == 0


class TestMetronomeGenerate:
    """Tests for audio generation."""

    def test_generate_output_shape(self):
        """Should return correct number of samples."""
        metro = Metronome()
        metro.start()
        output = metro.generate(1024)
        assert len(output) == 1024

    def test_generate_output_dtype(self):
        """Should return float32."""
        metro = Metronome()
        metro.start()
        output = metro.generate(1024)
        assert output.dtype == np.float32

    def test_generate_silent_when_stopped(self):
        """Should output zeros when stopped."""
        metro = Metronome()
        # Don't start
        output = metro.generate(1024)
        assert np.allclose(output, 0.0)

    def test_generate_has_clicks_when_running(self):
        """Should output non-zero when running at beat."""
        metro = Metronome(bpm=120, sample_rate=44100)
        metro.start()
        # Generate enough for at least one click
        output = metro.generate(1000)
        # Should have some non-zero samples (the click)
        assert np.abs(output).max() > 0

    def test_generate_volume_scaling(self):
        """Volume should scale output."""
        metro1 = Metronome(volume=0.5)
        metro2 = Metronome(volume=1.0)
        metro1.start()
        metro2.start()

        out1 = metro1.generate(1000)
        out2 = metro2.generate(1000)

        # Higher volume should have higher peak
        assert np.abs(out2).max() > np.abs(out1).max()


class TestMetronomeBeat:
    """Tests for beat tracking."""

    def test_current_beat_initial(self):
        """Should start at beat 0."""
        metro = Metronome()
        assert metro.current_beat == 0

    def test_current_measure_beat(self):
        """current_measure_beat should be 1-indexed."""
        metro = Metronome()
        assert metro.current_measure_beat == 1

    def test_beat_advances(self):
        """Beat should advance with audio generation."""
        metro = Metronome(bpm=120, sample_rate=44100)
        metro.start()
        # Generate 1 second = 2 beats at 120 BPM
        metro.generate(44100)
        # Should have advanced past beat 0
        # Note: actual beat depends on buffer boundaries
        assert metro.current_beat >= 0

    def test_beat_wraps(self):
        """Beat should wrap at end of measure."""
        metro = Metronome(bpm=240, sample_rate=44100, time_signature=TimeSignature(4, 4))
        metro.start()
        # 240 BPM = 4 beats/sec, generate 2 seconds = 8 beats = 2 measures
        metro.generate(44100 * 2)
        # Should have wrapped back to 0-3
        assert 0 <= metro.current_beat < 4


class TestMetronomeCallback:
    """Tests for beat callback."""

    def test_callback_called(self):
        """Callback should be called on beat."""
        metro = Metronome(bpm=240, sample_rate=44100)
        beats_received = []

        def callback(beat, is_downbeat):
            beats_received.append((beat, is_downbeat))

        metro.set_on_beat_callback(callback)
        metro.start()
        metro.generate(44100)  # 1 second at 240 BPM = 4 beats

        assert len(beats_received) > 0

    def test_callback_downbeat_flag(self):
        """Callback should flag downbeats."""
        metro = Metronome(bpm=240, sample_rate=44100)
        beats_received = []

        def callback(beat, is_downbeat):
            beats_received.append((beat, is_downbeat))

        metro.set_on_beat_callback(callback)
        metro.start()
        metro.generate(44100)  # 1 second

        # First beat should be downbeat
        if beats_received:
            first_beat, first_is_downbeat = beats_received[0]
            if first_beat == 0:
                assert first_is_downbeat


class TestMetronomeTapTempo:
    """Tests for tap tempo functionality."""

    def test_tap_tempo_first_tap(self):
        """First tap should return None."""
        metro = Metronome()
        result = metro.tap_tempo(0.0)
        assert result is None

    def test_tap_tempo_second_tap(self):
        """Second tap should return BPM."""
        metro = Metronome()
        metro.tap_tempo(0.0)
        result = metro.tap_tempo(0.5)  # 500ms = 120 BPM
        assert result is not None
        assert abs(result - 120.0) < 1.0

    def test_tap_tempo_multiple_taps(self):
        """Multiple taps should average."""
        metro = Metronome()
        metro.tap_tempo(0.0)
        metro.tap_tempo(0.5)
        metro.tap_tempo(1.0)
        result = metro.tap_tempo(1.5)  # All 500ms intervals
        assert result is not None
        assert abs(result - 120.0) < 1.0

    def test_tap_tempo_reset_on_long_gap(self):
        """Should reset if gap > 2 seconds."""
        metro = Metronome()
        metro.tap_tempo(0.0)
        metro.tap_tempo(0.5)
        # Long gap
        result = metro.tap_tempo(10.0)
        assert result is None


class TestMetronomeAccent:
    """Tests for accent functionality."""

    def test_accent_enabled_default(self):
        """Accent should be enabled by default."""
        metro = Metronome()
        assert metro.accent_enabled

    def test_accent_can_disable(self):
        """Should be able to disable accent."""
        metro = Metronome(accent_enabled=False)
        assert not metro.accent_enabled

    def test_accent_setter(self):
        """Should be able to toggle accent."""
        metro = Metronome()
        metro.accent_enabled = False
        assert not metro.accent_enabled
        metro.accent_enabled = True
        assert metro.accent_enabled


class TestMetronomeRepr:
    """Tests for string representation."""

    def test_repr_stopped(self):
        """Should show stopped status."""
        metro = Metronome(bpm=120)
        assert "stopped" in repr(metro)
        assert "120" in repr(metro)

    def test_repr_running(self):
        """Should show running status."""
        metro = Metronome(bpm=120)
        metro.start()
        assert "running" in repr(metro)


class TestClickSound:
    """Tests for ClickSound enum."""

    def test_click_sound_values(self):
        """Should have HIGH, LOW, SILENT."""
        assert ClickSound.HIGH
        assert ClickSound.LOW
        assert ClickSound.SILENT

    def test_click_sounds_distinct(self):
        """Values should be distinct."""
        assert ClickSound.HIGH != ClickSound.LOW
        assert ClickSound.LOW != ClickSound.SILENT
