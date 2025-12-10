# Song Data Model
"""
song - Data classes for song representation.

Provides SongEvent and Song dataclasses for representing
musical sequences that can be played back by SongPlayer.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class SongEvent:
    """Single note event in a song.

    Represents a single note with timing information for playback.

    Attributes:
        time: Time in seconds from song start
        note: MIDI note number (0-127)
        velocity: Note velocity (0-127)
        duration: Note duration in seconds
    """
    time: float
    note: int
    velocity: int
    duration: float

    def __post_init__(self):
        """Validate event parameters."""
        if self.time < 0:
            raise ValueError("time must be >= 0")
        if not 0 <= self.note <= 127:
            raise ValueError("note must be 0-127")
        if not 0 <= self.velocity <= 127:
            raise ValueError("velocity must be 0-127")
        if self.duration <= 0:
            raise ValueError("duration must be > 0")


@dataclass
class Song:
    """Complete song definition.

    Represents a complete song with metadata and note events.

    Attributes:
        name: Display name of the song
        bpm: Tempo in beats per minute
        preset: Synth preset name to use
        events: List of SongEvent objects
    """
    name: str
    bpm: float
    preset: str
    events: List[SongEvent] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """Get total song duration in seconds.

        Returns:
            Duration from start to end of last note
        """
        if not self.events:
            return 0.0

        last_event = max(self.events, key=lambda e: e.time + e.duration)
        return last_event.time + last_event.duration

    @property
    def event_count(self) -> int:
        """Get number of note events."""
        return len(self.events)

    @property
    def beat_duration(self) -> float:
        """Get duration of one beat in seconds."""
        return 60.0 / self.bpm

    def get_events_in_range(self, start: float, end: float) -> List[SongEvent]:
        """Get events that start within a time range.

        Args:
            start: Start time in seconds
            end: End time in seconds

        Returns:
            List of events within the range
        """
        return [e for e in self.events if start <= e.time < end]

    def __repr__(self) -> str:
        """String representation."""
        return (f"Song(name='{self.name}', bpm={self.bpm}, "
                f"preset='{self.preset}', events={len(self.events)}, "
                f"duration={self.duration:.1f}s)")
