# Demo Songs
"""
demo_songs - Built-in demonstration songs for the Mini Synthesizer.

Provides three demo songs:
1. Twinkle Twinkle Little Star - Simple melody, Soft Pad preset
2. Fur Elise (Intro) - Classical arpeggios, Bright Lead preset
3. Synth Demo - Electronic sequence, Fat Bass preset
"""

from typing import List, Optional
from .song import Song, SongEvent


def _create_twinkle_twinkle() -> Song:
    """Create Twinkle Twinkle Little Star demo song.

    Simple C major melody at 90 BPM.
    Uses "Soft Pad" preset for a gentle sound.

    Returns:
        Song object with Twinkle Twinkle melody
    """
    # MIDI note numbers: C4=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71, C5=72
    # Tempo: 90 BPM = 0.667 seconds per beat

    bpm = 90
    beat = 60.0 / bpm  # Duration of one beat
    half = beat / 2
    velocity = 80

    # Note sequence: Twinkle Twinkle Little Star
    # C C G G A A G - F F E E D D C
    # G G F F E E D - G G F F E E D
    # C C G G A A G - F F E E D D C

    melody = [
        # Line 1: "Twinkle twinkle little star"
        (0, 60, beat), (1*beat, 60, beat),      # C C
        (2*beat, 67, beat), (3*beat, 67, beat),  # G G
        (4*beat, 69, beat), (5*beat, 69, beat),  # A A
        (6*beat, 67, 2*beat),                    # G (held)

        # Line 2: "How I wonder what you are"
        (8*beat, 65, beat), (9*beat, 65, beat),  # F F
        (10*beat, 64, beat), (11*beat, 64, beat), # E E
        (12*beat, 62, beat), (13*beat, 62, beat), # D D
        (14*beat, 60, 2*beat),                    # C (held)

        # Line 3: "Up above the world so high"
        (16*beat, 67, beat), (17*beat, 67, beat), # G G
        (18*beat, 65, beat), (19*beat, 65, beat), # F F
        (20*beat, 64, beat), (21*beat, 64, beat), # E E
        (22*beat, 62, 2*beat),                    # D (held)

        # Line 4: "Like a diamond in the sky"
        (24*beat, 67, beat), (25*beat, 67, beat), # G G
        (26*beat, 65, beat), (27*beat, 65, beat), # F F
        (28*beat, 64, beat), (29*beat, 64, beat), # E E
        (30*beat, 62, 2*beat),                    # D (held)

        # Line 5: "Twinkle twinkle little star" (repeat)
        (32*beat, 60, beat), (33*beat, 60, beat),
        (34*beat, 67, beat), (35*beat, 67, beat),
        (36*beat, 69, beat), (37*beat, 69, beat),
        (38*beat, 67, 2*beat),

        # Line 6: "How I wonder what you are"
        (40*beat, 65, beat), (41*beat, 65, beat),
        (42*beat, 64, beat), (43*beat, 64, beat),
        (44*beat, 62, beat), (45*beat, 62, beat),
        (46*beat, 60, 2*beat),
    ]

    events = [
        SongEvent(time=t, note=n, velocity=velocity, duration=d)
        for t, n, d in melody
    ]

    return Song(
        name="Twinkle Twinkle",
        bpm=bpm,
        preset="Soft Pad",
        events=events
    )


def _create_fur_elise() -> Song:
    """Create Fur Elise intro demo song.

    First section of Beethoven's Fur Elise at 72 BPM.
    Uses "Bright Lead" preset for clear articulation.

    Returns:
        Song object with Fur Elise intro
    """
    # MIDI notes for Fur Elise intro pattern
    # E5=76, D#5=75, E5=76, D#5=75, E5=76, B4=71, D5=74, C5=72, A4=69
    # E4=64, A4=69, B4=71, E4=64, G#4=68, B4=71, C5=72

    bpm = 72
    beat = 60.0 / bpm
    eighth = beat / 2
    velocity = 85

    # Fur Elise opening pattern (simplified)
    melody = [
        # Main motif (E-D#-E-D#-E-B-D-C)
        (0, 76, eighth),           # E5
        (eighth, 75, eighth),      # D#5
        (2*eighth, 76, eighth),    # E5
        (3*eighth, 75, eighth),    # D#5
        (4*eighth, 76, eighth),    # E5
        (5*eighth, 71, eighth),    # B4
        (6*eighth, 74, eighth),    # D5
        (7*eighth, 72, eighth),    # C5

        # A minor chord arpeggio
        (8*eighth, 69, beat),      # A4
        (8*eighth + beat, 64, eighth),  # E4
        (9*eighth + beat, 69, eighth),  # A4
        (10*eighth + beat, 71, beat),   # B4

        # E-G#-B
        (10*eighth + 2*beat, 64, eighth),  # E4
        (11*eighth + 2*beat, 68, eighth),  # G#4
        (12*eighth + 2*beat, 71, beat),    # B4

        # C5
        (12*eighth + 3*beat, 72, beat),    # C5

        # Repeat main motif
        (12*eighth + 4*beat, 76, eighth),
        (13*eighth + 4*beat, 75, eighth),
        (14*eighth + 4*beat, 76, eighth),
        (15*eighth + 4*beat, 75, eighth),
        (16*eighth + 4*beat, 76, eighth),
        (17*eighth + 4*beat, 71, eighth),
        (18*eighth + 4*beat, 74, eighth),
        (19*eighth + 4*beat, 72, eighth),

        # A minor resolution
        (20*eighth + 4*beat, 69, beat),
        (20*eighth + 5*beat, 64, eighth),
        (21*eighth + 5*beat, 69, eighth),
        (22*eighth + 5*beat, 71, beat),

        # Final resolution to C
        (22*eighth + 6*beat, 64, eighth),
        (23*eighth + 6*beat, 72, eighth),
        (24*eighth + 6*beat, 71, beat),

        # Final A
        (24*eighth + 7*beat, 69, 2*beat),
    ]

    events = [
        SongEvent(time=t, note=n, velocity=velocity, duration=d)
        for t, n, d in melody
    ]

    return Song(
        name="Fur Elise (Intro)",
        bpm=bpm,
        preset="Bright Lead",
        events=events
    )


def _create_ambient_pad() -> Song:
    """Create Ambient Pad showcase song.

    Slow, evolving pad chords showcasing reverb and chorus.
    Uses "Soft Pad" preset with long notes for ambient texture.
    Duration: ~20 seconds

    Returns:
        Song object with ambient pad sequence
    """
    bpm = 60
    beat = 60.0 / bpm
    velocity = 70

    # Slow chord progression: Am - F - C - G
    # Each chord held for 4 beats with overlapping voices
    melody = []

    # Chord 1: Am (A3, C4, E4) - 0-4 beats
    melody.extend([
        (0, 57, 4*beat),      # A3
        (0.1, 60, 4*beat),    # C4
        (0.2, 64, 4*beat),    # E4
    ])

    # Chord 2: F (F3, A3, C4) - 4-8 beats
    melody.extend([
        (4*beat, 53, 4*beat),      # F3
        (4*beat + 0.1, 57, 4*beat), # A3
        (4*beat + 0.2, 60, 4*beat), # C4
    ])

    # Chord 3: C (C3, E3, G3) - 8-12 beats
    melody.extend([
        (8*beat, 48, 4*beat),      # C3
        (8*beat + 0.1, 52, 4*beat), # E3
        (8*beat + 0.2, 55, 4*beat), # G3
    ])

    # Chord 4: G (G3, B3, D4) - 12-16 beats
    melody.extend([
        (12*beat, 55, 4*beat),      # G3
        (12*beat + 0.1, 59, 4*beat), # B3
        (12*beat + 0.2, 62, 4*beat), # D4
    ])

    # Resolve back to Am - 16-20 beats
    melody.extend([
        (16*beat, 57, 4*beat),      # A3
        (16*beat + 0.1, 60, 4*beat), # C4
        (16*beat + 0.2, 64, 4*beat), # E4
    ])

    events = [
        SongEvent(time=t, note=n, velocity=velocity, duration=d)
        for t, n, d in melody
    ]

    return Song(
        name="Ambient Pad",
        bpm=bpm,
        preset="Soft Pad",
        events=events
    )


def _create_retro_arp() -> Song:
    """Create Retro Arpeggio showcase song.

    Fast arpeggiated pattern showcasing delay effect.
    Uses "Retro Square" preset for classic synth sound.
    Duration: ~18 seconds

    Returns:
        Song object with retro arpeggio sequence
    """
    bpm = 140
    beat = 60.0 / bpm
    sixteenth = beat / 4
    velocity = 85

    melody = []

    # C minor arpeggio pattern: C, Eb, G, C (up), then back down
    arp_up = [48, 51, 55, 60]      # C3, Eb3, G3, C4
    arp_down = [60, 55, 51, 48]    # C4, G3, Eb3, C3

    # 4 bars of ascending arpeggios
    for bar in range(4):
        bar_start = bar * beat
        for i, note in enumerate(arp_up):
            melody.append((bar_start + i * sixteenth, note, sixteenth * 0.8))

    # 4 bars of descending arpeggios
    for bar in range(4):
        bar_start = (4 + bar) * beat
        for i, note in enumerate(arp_down):
            melody.append((bar_start + i * sixteenth, note, sixteenth * 0.8))

    # Modulate to G minor (G, Bb, D, G)
    arp_gm_up = [55, 58, 62, 67]
    for bar in range(4):
        bar_start = (8 + bar) * beat
        for i, note in enumerate(arp_gm_up):
            melody.append((bar_start + i * sixteenth, note, sixteenth * 0.8))

    # Back to C minor with variation
    arp_cm_var = [48, 55, 51, 60]  # C3, G3, Eb3, C4
    for bar in range(4):
        bar_start = (12 + bar) * beat
        for i, note in enumerate(arp_cm_var):
            melody.append((bar_start + i * sixteenth, note, sixteenth * 0.8))

    # Final sustained chord
    melody.extend([
        (16*beat, 48, 2*beat),
        (16*beat, 51, 2*beat),
        (16*beat, 55, 2*beat),
        (16*beat, 60, 2*beat),
    ])

    events = [
        SongEvent(time=t, note=n, velocity=velocity, duration=d)
        for t, n, d in melody
    ]

    return Song(
        name="Retro Arp",
        bpm=bpm,
        preset="Retro Square",
        events=events
    )


def _create_bass_groove() -> Song:
    """Create Bass Groove showcase song.

    Punchy bass line showcasing distortion effect.
    Uses "Fat Bass" preset with rhythmic pattern.
    Duration: ~16 seconds

    Returns:
        Song object with bass groove sequence
    """
    bpm = 100
    beat = 60.0 / bpm
    eighth = beat / 2
    sixteenth = beat / 4
    velocity = 100

    melody = []

    # Funky bass pattern in E minor
    # Pattern: E--E-G-A-E--E-B-A
    pattern1 = [
        (0, 40, eighth + sixteenth),           # E2 (long)
        (eighth + sixteenth, 40, sixteenth),   # E2 (short)
        (2*eighth, 43, eighth),                # G2
        (3*eighth, 45, eighth),                # A2
    ]

    pattern2 = [
        (0, 40, eighth + sixteenth),           # E2 (long)
        (eighth + sixteenth, 40, sixteenth),   # E2 (short)
        (2*eighth, 47, eighth),                # B2
        (3*eighth, 45, eighth),                # A2
    ]

    # 4 bars alternating patterns
    for bar in range(4):
        bar_start = bar * beat
        pattern = pattern1 if bar % 2 == 0 else pattern2
        for offset, note, dur in pattern:
            melody.append((bar_start + offset, note, dur))

    # Drop to D for 2 bars
    pattern_d = [
        (0, 38, eighth + sixteenth),           # D2
        (eighth + sixteenth, 38, sixteenth),
        (2*eighth, 41, eighth),                # F2
        (3*eighth, 43, eighth),                # G2
    ]

    for bar in range(2):
        bar_start = (4 + bar) * beat
        for offset, note, dur in pattern_d:
            melody.append((bar_start + offset, note, dur))

    # Return to E with power ending
    for bar in range(2):
        bar_start = (6 + bar) * beat
        for offset, note, dur in pattern1:
            melody.append((bar_start + offset, note, dur))

    # Final note
    melody.append((8*beat, 40, 2*beat))  # Long E2

    events = [
        SongEvent(time=t, note=n, velocity=velocity, duration=d)
        for t, n, d in melody
    ]

    return Song(
        name="Bass Groove",
        bpm=bpm,
        preset="Fat Bass",
        events=events
    )


def _create_dreamy_lead() -> Song:
    """Create Dreamy Lead showcase song.

    Melodic lead line showcasing chorus and reverb together.
    Uses "Bright Lead" preset with expressive melody.
    Duration: ~24 seconds

    Returns:
        Song object with dreamy lead melody
    """
    bpm = 80
    beat = 60.0 / bpm
    eighth = beat / 2
    quarter = beat
    half = 2 * beat
    velocity = 75

    melody = []

    # Pentatonic melody in G major (G A B D E)
    # Phrase 1
    melody.extend([
        (0, 67, quarter),           # G4
        (quarter, 69, eighth),      # A4
        (quarter + eighth, 71, quarter),  # B4
        (2*quarter + eighth, 74, half),   # D5 (held)
    ])

    # Phrase 2
    melody.extend([
        (4*quarter, 76, quarter),           # E5
        (5*quarter, 74, eighth),            # D5
        (5*quarter + eighth, 71, quarter),  # B4
        (6*quarter + eighth, 69, half),     # A4 (held)
    ])

    # Phrase 3 - ascending
    melody.extend([
        (8*quarter, 67, eighth),            # G4
        (8*quarter + eighth, 69, eighth),   # A4
        (9*quarter, 71, eighth),            # B4
        (9*quarter + eighth, 74, eighth),   # D5
        (10*quarter, 76, half + quarter),   # E5 (long hold)
    ])

    # Phrase 4 - descending resolution
    melody.extend([
        (13*quarter, 74, quarter),          # D5
        (14*quarter, 71, quarter),          # B4
        (15*quarter, 69, quarter),          # A4
        (16*quarter, 67, 2*half),           # G4 (final long note)
    ])

    events = [
        SongEvent(time=t, note=n, velocity=velocity, duration=d)
        for t, n, d in melody
    ]

    return Song(
        name="Dreamy Lead",
        bpm=bpm,
        preset="Bright Lead",
        events=events
    )


def _create_techno_pulse() -> Song:
    """Create Techno Pulse showcase song.

    Driving electronic pattern showcasing all effects.
    Uses "Fat Bass" preset with pulsing rhythm.
    Duration: ~20 seconds

    Returns:
        Song object with techno pulse sequence
    """
    bpm = 130
    beat = 60.0 / bpm
    sixteenth = beat / 4
    eighth = beat / 2
    velocity_kick = 110
    velocity_synth = 85

    melody = []

    # Kick pattern (low C) - every beat
    for bar in range(8):
        bar_start = bar * 4 * beat
        for i in range(4):
            melody.append((bar_start + i * beat, 36, eighth, velocity_kick))  # C2

    # Offbeat stabs (higher) - syncopated
    stab_notes = [60, 63, 67]  # C4, Eb4, G4 (C minor)
    for bar in range(8):
        bar_start = bar * 4 * beat
        # Offbeat hits
        melody.append((bar_start + eighth, stab_notes[bar % 3], sixteenth, velocity_synth))
        melody.append((bar_start + beat + eighth, stab_notes[(bar + 1) % 3], sixteenth, velocity_synth))
        melody.append((bar_start + 2*beat + eighth, stab_notes[(bar + 2) % 3], sixteenth, velocity_synth))
        melody.append((bar_start + 3*beat + eighth, stab_notes[bar % 3], sixteenth, velocity_synth))

    # Build-up section - rising notes
    build_start = 8 * 4 * beat
    build_notes = [48, 51, 55, 60, 63, 67, 72, 75]  # Rising C minor
    for i, note in enumerate(build_notes):
        melody.append((build_start + i * eighth, note, eighth * 0.9, velocity_synth))

    # Drop - sustained chord
    drop_start = build_start + 8 * eighth
    melody.extend([
        (drop_start, 48, 2*beat, velocity_kick),      # C3
        (drop_start, 55, 2*beat, velocity_synth),     # G3
        (drop_start, 60, 2*beat, velocity_synth),     # C4
        (drop_start, 63, 2*beat, velocity_synth),     # Eb4
    ])

    events = [
        SongEvent(time=t, note=n, velocity=v, duration=d)
        for t, n, d, v in melody
    ]

    return Song(
        name="Techno Pulse",
        bpm=bpm,
        preset="Fat Bass",
        events=events
    )


def _create_synth_demo() -> Song:
    """Create Synth Demo song.

    Electronic sequence at 120 BPM showing off synth capabilities.
    Uses "Fat Bass" preset for rich sound.

    Returns:
        Song object with synth demo sequence
    """
    # Bass-heavy electronic pattern
    # Using lower octave notes for bass emphasis

    bpm = 120
    beat = 60.0 / bpm
    sixteenth = beat / 4
    eighth = beat / 2
    velocity_bass = 100
    velocity_lead = 90

    melody = []
    t = 0.0

    # Bass pattern (4 bars, repeating)
    bass_pattern = [
        (36, beat),      # C2
        (36, eighth),    # C2
        (39, eighth),    # D#2
        (43, beat),      # G2
        (41, beat),      # F2
    ]

    # Add 4 repetitions of bass pattern
    for rep in range(4):
        offset = rep * 4 * beat
        for note, dur in bass_pattern:
            melody.append((offset + t, note, velocity_bass, dur))
            t += dur
        t = 0.0

    # Lead melody on top (octave higher)
    lead_pattern = [
        # Bar 1
        (0, 60, sixteenth),      # C4
        (sixteenth, 63, sixteenth),  # D#4
        (2*sixteenth, 67, eighth),   # G4
        (4*sixteenth, 65, eighth),   # F4

        # Bar 2
        (beat, 60, sixteenth),
        (beat + sixteenth, 67, sixteenth),
        (beat + 2*sixteenth, 72, eighth),  # C5
        (beat + 4*sixteenth, 70, eighth),  # A#4

        # Bar 3
        (2*beat, 67, sixteenth),
        (2*beat + sixteenth, 70, sixteenth),
        (2*beat + 2*sixteenth, 72, beat),

        # Bar 4
        (3*beat, 70, sixteenth),
        (3*beat + sixteenth, 67, sixteenth),
        (3*beat + 2*sixteenth, 63, sixteenth),
        (3*beat + 3*sixteenth, 60, beat + sixteenth),
    ]

    # Add lead melody for each 4-bar section
    for rep in range(4):
        offset = rep * 4 * beat
        for time_offset, note, dur in lead_pattern:
            melody.append((offset + time_offset, note, velocity_lead, dur))

    # Arpeggio section (last 4 bars)
    arp_start = 16 * beat
    arp_notes = [48, 51, 55, 60, 63, 60, 55, 51]  # C3, D#3, G3, C4, D#4, C4, G3, D#3

    for bar in range(4):
        for i, note in enumerate(arp_notes):
            t = arp_start + bar * beat + i * sixteenth
            melody.append((t, note, velocity_lead, sixteenth * 0.9))

    events = [
        SongEvent(time=t, note=n, velocity=v, duration=d)
        for t, n, v, d in melody
    ]

    return Song(
        name="Synth Demo",
        bpm=bpm,
        preset="Fat Bass",
        events=events
    )


# Pre-built demo songs
DEMO_SONGS: List[Song] = [
    _create_twinkle_twinkle(),
    _create_fur_elise(),
    _create_synth_demo(),
    # New showcase songs (BOLT-009)
    _create_ambient_pad(),
    _create_retro_arp(),
    _create_bass_groove(),
    _create_dreamy_lead(),
    _create_techno_pulse(),
]


def get_all_songs() -> List[Song]:
    """Get list of all demo songs.

    Returns:
        List of Song objects
    """
    return DEMO_SONGS.copy()


def get_song_by_name(name: str) -> Optional[Song]:
    """Get a demo song by name.

    Args:
        name: Song name to find

    Returns:
        Song object if found, None otherwise
    """
    for song in DEMO_SONGS:
        if song.name.lower() == name.lower():
            return song
    return None
