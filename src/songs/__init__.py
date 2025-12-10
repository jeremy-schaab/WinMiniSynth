# Songs Module
"""
songs - Song playback and demo songs for the Mini Synthesizer.

This module provides:
- SongEvent: Dataclass for individual note events
- Song: Dataclass for complete song definition
- SongPlayer: Plays back songs with timing and callbacks
- Demo songs: Built-in demonstration songs

Usage:
    from songs import Song, SongEvent, SongPlayer, get_all_songs

    player = SongPlayer(
        on_note_on=lambda note, vel: synth.note_on(note, vel),
        on_note_off=lambda note: synth.note_off(note)
    )

    songs = get_all_songs()
    player.load(songs[0])
    player.play()
"""

from .song import Song, SongEvent
from .player import SongPlayer
from .demo_songs import get_all_songs, get_song_by_name, DEMO_SONGS

__all__ = [
    'Song',
    'SongEvent',
    'SongPlayer',
    'get_all_songs',
    'get_song_by_name',
    'DEMO_SONGS',
]
