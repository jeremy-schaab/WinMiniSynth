# Tests for Song Player
"""
test_song_player - Unit tests for song data model and player.
"""

import pytest
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from songs.song import Song, SongEvent
from songs.player import SongPlayer, PlayerState
from songs.demo_songs import get_all_songs, get_song_by_name


class TestSongEvent:
    """Tests for SongEvent dataclass."""

    def test_create_event(self):
        """Should create event with valid params."""
        event = SongEvent(time=1.0, note=60, velocity=100, duration=0.5)
        assert event.time == 1.0
        assert event.note == 60
        assert event.velocity == 100
        assert event.duration == 0.5

    def test_invalid_time(self):
        """Should reject negative time."""
        with pytest.raises(ValueError):
            SongEvent(time=-1.0, note=60, velocity=100, duration=0.5)

    def test_invalid_note_low(self):
        """Should reject note < 0."""
        with pytest.raises(ValueError):
            SongEvent(time=0.0, note=-1, velocity=100, duration=0.5)

    def test_invalid_note_high(self):
        """Should reject note > 127."""
        with pytest.raises(ValueError):
            SongEvent(time=0.0, note=128, velocity=100, duration=0.5)

    def test_invalid_velocity_low(self):
        """Should reject velocity < 0."""
        with pytest.raises(ValueError):
            SongEvent(time=0.0, note=60, velocity=-1, duration=0.5)

    def test_invalid_velocity_high(self):
        """Should reject velocity > 127."""
        with pytest.raises(ValueError):
            SongEvent(time=0.0, note=60, velocity=128, duration=0.5)

    def test_invalid_duration(self):
        """Should reject duration <= 0."""
        with pytest.raises(ValueError):
            SongEvent(time=0.0, note=60, velocity=100, duration=0)
        with pytest.raises(ValueError):
            SongEvent(time=0.0, note=60, velocity=100, duration=-0.5)


class TestSong:
    """Tests for Song dataclass."""

    def test_create_song(self):
        """Should create song with valid params."""
        song = Song(name="Test", bpm=120, preset="Init")
        assert song.name == "Test"
        assert song.bpm == 120
        assert song.preset == "Init"
        assert song.events == []

    def test_song_with_events(self):
        """Should accept events list."""
        events = [
            SongEvent(time=0.0, note=60, velocity=100, duration=0.5),
            SongEvent(time=0.5, note=62, velocity=100, duration=0.5),
        ]
        song = Song(name="Test", bpm=120, preset="Init", events=events)
        assert len(song.events) == 2

    def test_duration_empty(self):
        """Empty song should have 0 duration."""
        song = Song(name="Test", bpm=120, preset="Init")
        assert song.duration == 0.0

    def test_duration_with_events(self):
        """Duration should be end of last note."""
        events = [
            SongEvent(time=0.0, note=60, velocity=100, duration=0.5),
            SongEvent(time=1.0, note=62, velocity=100, duration=0.5),
        ]
        song = Song(name="Test", bpm=120, preset="Init", events=events)
        assert song.duration == 1.5  # 1.0 + 0.5

    def test_event_count(self):
        """Should return correct event count."""
        events = [
            SongEvent(time=0.0, note=60, velocity=100, duration=0.5),
            SongEvent(time=0.5, note=62, velocity=100, duration=0.5),
            SongEvent(time=1.0, note=64, velocity=100, duration=0.5),
        ]
        song = Song(name="Test", bpm=120, preset="Init", events=events)
        assert song.event_count == 3

    def test_beat_duration(self):
        """Should calculate beat duration correctly."""
        song = Song(name="Test", bpm=120, preset="Init")
        assert song.beat_duration == 0.5  # 60/120

    def test_get_events_in_range(self):
        """Should return events within time range."""
        events = [
            SongEvent(time=0.0, note=60, velocity=100, duration=0.5),
            SongEvent(time=0.5, note=62, velocity=100, duration=0.5),
            SongEvent(time=1.0, note=64, velocity=100, duration=0.5),
        ]
        song = Song(name="Test", bpm=120, preset="Init", events=events)

        in_range = song.get_events_in_range(0.4, 1.0)
        assert len(in_range) == 1
        assert in_range[0].note == 62


class TestSongPlayerInit:
    """Tests for SongPlayer initialization."""

    def test_default_init(self):
        """Should initialize with default state."""
        player = SongPlayer()
        assert player.is_stopped
        assert not player.is_playing
        assert not player.is_paused
        assert player.current_song is None

    def test_with_callbacks(self):
        """Should accept callbacks."""
        notes_on = []
        notes_off = []

        player = SongPlayer(
            on_note_on=lambda n, v: notes_on.append((n, v)),
            on_note_off=lambda n: notes_off.append(n)
        )
        assert player is not None


class TestSongPlayerLoad:
    """Tests for SongPlayer load."""

    def test_load_song(self):
        """Should load song."""
        player = SongPlayer()
        song = Song(name="Test", bpm=120, preset="Init")
        player.load(song)
        assert player.current_song == song

    def test_load_replaces_song(self):
        """Loading new song should replace old."""
        player = SongPlayer()
        song1 = Song(name="Test1", bpm=120, preset="Init")
        song2 = Song(name="Test2", bpm=100, preset="Fat Bass")

        player.load(song1)
        player.load(song2)
        assert player.current_song == song2


class TestSongPlayerPlayback:
    """Tests for SongPlayer playback."""

    def test_play_without_load(self):
        """Should not crash if no song loaded."""
        player = SongPlayer()
        player.play()  # Should not raise

    def test_play_starts_playback(self):
        """Play should start playback."""
        player = SongPlayer()
        song = Song(name="Test", bpm=120, preset="Init", events=[
            SongEvent(time=0.0, note=60, velocity=100, duration=0.5)
        ])
        player.load(song)
        player.play()
        assert player.is_playing
        player.stop()

    def test_stop_stops_playback(self):
        """Stop should stop playback."""
        player = SongPlayer()
        song = Song(name="Test", bpm=120, preset="Init", events=[
            SongEvent(time=0.0, note=60, velocity=100, duration=0.5)
        ])
        player.load(song)
        player.play()
        player.stop()
        assert player.is_stopped

    def test_pause_pauses_playback(self):
        """Pause should pause playback."""
        player = SongPlayer()
        song = Song(name="Test", bpm=120, preset="Init", events=[
            SongEvent(time=0.0, note=60, velocity=100, duration=0.5)
        ])
        player.load(song)
        player.play()
        player.pause()
        assert player.is_paused
        player.stop()

    def test_resume_resumes_playback(self):
        """Resume should resume from pause."""
        player = SongPlayer()
        song = Song(name="Test", bpm=120, preset="Init", events=[
            SongEvent(time=0.0, note=60, velocity=100, duration=0.5)
        ])
        player.load(song)
        player.play()
        player.pause()
        player.resume()
        assert player.is_playing
        player.stop()


class TestSongPlayerCallbacks:
    """Tests for SongPlayer callbacks."""

    def test_note_on_callback(self):
        """Should call note on callback."""
        notes_on = []

        player = SongPlayer(
            on_note_on=lambda n, v: notes_on.append((n, v))
        )
        song = Song(name="Test", bpm=120, preset="Init", events=[
            SongEvent(time=0.0, note=60, velocity=100, duration=0.5)
        ])
        player.load(song)
        player.play()

        # Wait for note to trigger
        time.sleep(0.15)
        player.stop()

        assert len(notes_on) >= 1
        assert notes_on[0] == (60, 100)

    def test_preset_change_callback(self):
        """Should call preset change callback on play."""
        presets = []

        player = SongPlayer(
            on_preset_change=lambda p: presets.append(p)
        )
        song = Song(name="Test", bpm=120, preset="Fat Bass", events=[
            SongEvent(time=0.0, note=60, velocity=100, duration=0.5)
        ])
        player.load(song)
        player.play()
        player.stop()

        assert "Fat Bass" in presets


class TestSongPlayerPosition:
    """Tests for SongPlayer position tracking."""

    def test_position_starts_at_zero(self):
        """Position should start at 0."""
        player = SongPlayer()
        assert player.current_position == 0.0

    def test_total_duration(self):
        """Should return song duration."""
        player = SongPlayer()
        song = Song(name="Test", bpm=120, preset="Init", events=[
            SongEvent(time=0.0, note=60, velocity=100, duration=1.0),
            SongEvent(time=1.0, note=62, velocity=100, duration=0.5),
        ])
        player.load(song)
        assert player.total_duration == 1.5

    def test_progress_calculation(self):
        """Progress should be position/duration."""
        player = SongPlayer()
        song = Song(name="Test", bpm=120, preset="Init", events=[
            SongEvent(time=0.0, note=60, velocity=100, duration=1.0),
        ])
        player.load(song)
        player.play()
        time.sleep(0.2)
        progress = player.progress
        player.stop()

        assert 0.0 <= progress <= 1.0


class TestDemoSongs:
    """Tests for demo songs."""

    def test_get_all_songs(self):
        """Should return list of demo songs."""
        songs = get_all_songs()
        assert len(songs) >= 3

    def test_demo_songs_valid(self):
        """All demo songs should be valid."""
        songs = get_all_songs()
        for song in songs:
            assert song.name
            assert song.bpm > 0
            assert song.preset
            assert len(song.events) > 0
            assert song.duration > 0

    def test_get_song_by_name(self):
        """Should find song by name."""
        song = get_song_by_name("Twinkle Twinkle")
        assert song is not None
        assert song.name == "Twinkle Twinkle"

    def test_get_song_by_name_case_insensitive(self):
        """Should find song case-insensitively."""
        song = get_song_by_name("twinkle twinkle")
        assert song is not None

    def test_get_song_by_name_not_found(self):
        """Should return None for unknown song."""
        song = get_song_by_name("Unknown Song")
        assert song is None

    def test_twinkle_twinkle_preset(self):
        """Twinkle Twinkle should use Soft Pad."""
        song = get_song_by_name("Twinkle Twinkle")
        assert song.preset == "Soft Pad"

    def test_fur_elise_preset(self):
        """Fur Elise should use Bright Lead."""
        song = get_song_by_name("Fur Elise (Intro)")
        assert song.preset == "Bright Lead"

    def test_synth_demo_preset(self):
        """Synth Demo should use Fat Bass."""
        song = get_song_by_name("Synth Demo")
        assert song.preset == "Fat Bass"
