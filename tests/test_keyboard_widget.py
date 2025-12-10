# Tests for Virtual Piano Keyboard Widget
"""
test_keyboard_widget - Unit tests for PianoKeyboard and related components.
"""

import pytest
import tkinter as tk
from tkinter import ttk

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui.styles import configure_dark_theme
from gui.keyboard_widget import PianoKeyboard, KeyInfo, KeyType


@pytest.fixture
def root():
    """Create a root window for testing."""
    root = tk.Tk()
    root.withdraw()
    configure_dark_theme(root)
    yield root
    root.destroy()


class TestKeyType:
    """Tests for KeyType enumeration."""

    def test_white_value(self):
        """WHITE should have value 0."""
        assert KeyType.WHITE == 0

    def test_black_value(self):
        """BLACK should have value 1."""
        assert KeyType.BLACK == 1


class TestKeyInfo:
    """Tests for KeyInfo dataclass."""

    def test_create_white_key(self):
        """Should create a white key info."""
        key = KeyInfo(
            midi_note=60,
            key_type=KeyType.WHITE,
            x1=0, y1=0, x2=50, y2=100
        )
        assert key.midi_note == 60
        assert key.key_type == KeyType.WHITE
        assert key.is_white is True
        assert key.is_black is False

    def test_create_black_key(self):
        """Should create a black key info."""
        key = KeyInfo(
            midi_note=61,
            key_type=KeyType.BLACK,
            x1=40, y1=0, x2=60, y2=65
        )
        assert key.midi_note == 61
        assert key.key_type == KeyType.BLACK
        assert key.is_white is False
        assert key.is_black is True

    def test_canvas_id_default_none(self):
        """Canvas ID should default to None."""
        key = KeyInfo(midi_note=60, key_type=KeyType.WHITE, x1=0, y1=0, x2=50, y2=100)
        assert key.canvas_id is None

    def test_label_id_default_none(self):
        """Label ID should default to None."""
        key = KeyInfo(midi_note=60, key_type=KeyType.WHITE, x1=0, y1=0, x2=50, y2=100)
        assert key.label_id is None


class TestPianoKeyboardInit:
    """Tests for PianoKeyboard initialization."""

    def test_create_keyboard(self, root):
        """Should create a piano keyboard widget."""
        keyboard = PianoKeyboard(root)
        assert keyboard is not None

    def test_default_num_octaves(self, root):
        """Should default to 2 octaves."""
        keyboard = PianoKeyboard(root)
        assert keyboard.num_octaves == 2

    def test_custom_num_octaves(self, root):
        """Should accept custom octave count."""
        keyboard = PianoKeyboard(root, num_octaves=3)
        assert keyboard.num_octaves == 3

    def test_num_octaves_clamped_min(self, root):
        """Should clamp num_octaves to minimum 1."""
        keyboard = PianoKeyboard(root, num_octaves=0)
        assert keyboard.num_octaves == 1

    def test_num_octaves_clamped_max(self, root):
        """Should clamp num_octaves to maximum 4."""
        keyboard = PianoKeyboard(root, num_octaves=10)
        assert keyboard.num_octaves == 4

    def test_default_start_octave(self, root):
        """Should default to starting octave 3."""
        keyboard = PianoKeyboard(root)
        assert keyboard.start_octave == 3

    def test_custom_start_octave(self, root):
        """Should accept custom start octave."""
        keyboard = PianoKeyboard(root, start_octave=4)
        assert keyboard.start_octave == 4

    def test_default_octave_shift(self, root):
        """Should default to octave shift 0."""
        keyboard = PianoKeyboard(root)
        assert keyboard.octave_shift == 0

    def test_current_octave(self, root):
        """Should calculate current octave correctly."""
        keyboard = PianoKeyboard(root, start_octave=3)
        assert keyboard.current_octave == 3

    def test_pressed_notes_initially_empty(self, root):
        """Should have no pressed notes initially."""
        keyboard = PianoKeyboard(root)
        assert len(keyboard.pressed_notes) == 0


class TestPianoKeyboardOctaveShift:
    """Tests for octave shift functionality."""

    def test_octave_shift_property(self, root):
        """Should get and set octave shift."""
        keyboard = PianoKeyboard(root, start_octave=3)
        keyboard.octave_shift = 1
        assert keyboard.octave_shift == 1
        assert keyboard.current_octave == 4

    def test_octave_shift_clamped_min(self, root):
        """Should clamp octave shift to minimum."""
        keyboard = PianoKeyboard(root)
        keyboard.octave_shift = -10
        assert keyboard.octave_shift >= -2

    def test_octave_shift_clamped_max(self, root):
        """Should clamp octave shift to maximum."""
        keyboard = PianoKeyboard(root)
        keyboard.octave_shift = 10
        assert keyboard.octave_shift <= 4


class TestPianoKeyboardKeys:
    """Tests for keyboard key management."""

    def test_keys_created(self, root):
        """Should create key info for all keys."""
        keyboard = PianoKeyboard(root, num_octaves=1)
        # 1 octave = 7 white keys + 5 black keys = 12 keys
        assert len(keyboard._keys) == 12

    def test_two_octaves_keys(self, root):
        """Should create correct number of keys for 2 octaves."""
        keyboard = PianoKeyboard(root, num_octaves=2)
        # 2 octaves = 14 white keys + 10 black keys = 24 keys
        assert len(keyboard._keys) == 24

    def test_white_keys_count(self, root):
        """Should have correct number of white keys."""
        keyboard = PianoKeyboard(root, num_octaves=1)
        white_count = sum(1 for k in keyboard._keys.values() if k.is_white)
        assert white_count == 7

    def test_black_keys_count(self, root):
        """Should have correct number of black keys."""
        keyboard = PianoKeyboard(root, num_octaves=1)
        black_count = sum(1 for k in keyboard._keys.values() if k.is_black)
        assert black_count == 5


class TestPianoKeyboardNotes:
    """Tests for note on/off functionality."""

    def test_note_on_callback(self, root):
        """Should call note on callback."""
        notes = []
        keyboard = PianoKeyboard(
            root,
            on_note_on=lambda n, v: notes.append((n, v))
        )
        keyboard._note_on(60, 100)
        assert len(notes) == 1
        assert notes[0] == (60, 100)

    def test_note_on_adds_to_pressed(self, root):
        """Should add note to pressed notes."""
        keyboard = PianoKeyboard(root)
        keyboard._note_on(60, 100)
        assert 60 in keyboard.pressed_notes

    def test_note_on_duplicate_ignored(self, root):
        """Should ignore duplicate note on."""
        notes = []
        keyboard = PianoKeyboard(
            root,
            on_note_on=lambda n, v: notes.append((n, v))
        )
        keyboard._note_on(60, 100)
        keyboard._note_on(60, 100)  # Duplicate
        assert len(notes) == 1

    def test_note_off_callback(self, root):
        """Should call note off callback."""
        notes = []
        keyboard = PianoKeyboard(
            root,
            on_note_off=lambda n: notes.append(n)
        )
        keyboard._note_on(60, 100)
        keyboard._note_off(60)
        assert len(notes) == 1
        assert notes[0] == 60

    def test_note_off_removes_from_pressed(self, root):
        """Should remove note from pressed notes."""
        keyboard = PianoKeyboard(root)
        keyboard._note_on(60, 100)
        keyboard._note_off(60)
        assert 60 not in keyboard.pressed_notes

    def test_note_off_not_pressed_ignored(self, root):
        """Should ignore note off for unpressed note."""
        notes = []
        keyboard = PianoKeyboard(
            root,
            on_note_off=lambda n: notes.append(n)
        )
        keyboard._note_off(60)  # Not pressed
        assert len(notes) == 0


class TestPianoKeyboardPanic:
    """Tests for panic functionality."""

    def test_panic_releases_all_notes(self, root):
        """Panic should release all pressed notes."""
        off_notes = []
        keyboard = PianoKeyboard(
            root,
            on_note_off=lambda n: off_notes.append(n)
        )
        keyboard._note_on(60, 100)
        keyboard._note_on(64, 100)
        keyboard._note_on(67, 100)

        keyboard.panic()

        assert len(keyboard.pressed_notes) == 0
        assert len(off_notes) == 3

    def test_panic_clears_keyboard_pressed(self, root):
        """Panic should clear keyboard pressed state."""
        keyboard = PianoKeyboard(root)
        keyboard._keyboard_pressed['z'] = 48
        keyboard.panic()
        assert len(keyboard._keyboard_pressed) == 0

    def test_panic_clears_mouse_pressed(self, root):
        """Panic should clear mouse pressed state."""
        keyboard = PianoKeyboard(root)
        keyboard._mouse_pressed_note = 60
        keyboard.panic()
        assert keyboard._mouse_pressed_note is None


class TestPianoKeyboardKeyMapping:
    """Tests for computer keyboard to note mapping."""

    def test_map_lower_row_c(self, root):
        """Z should map to C of base octave."""
        keyboard = PianoKeyboard(root, start_octave=3)
        note = keyboard._map_key_to_note('z')
        assert note == 48  # C3

    def test_map_lower_row_d(self, root):
        """X should map to D of base octave."""
        keyboard = PianoKeyboard(root, start_octave=3)
        note = keyboard._map_key_to_note('x')
        assert note == 50  # D3

    def test_map_lower_row_csharp(self, root):
        """S should map to C# of base octave."""
        keyboard = PianoKeyboard(root, start_octave=3)
        note = keyboard._map_key_to_note('s')
        assert note == 49  # C#3

    def test_map_upper_row_c(self, root):
        """Q should map to C of upper octave."""
        keyboard = PianoKeyboard(root, start_octave=3)
        note = keyboard._map_key_to_note('q')
        assert note == 60  # C4

    def test_map_upper_row_d(self, root):
        """W should map to D of upper octave."""
        keyboard = PianoKeyboard(root, start_octave=3)
        note = keyboard._map_key_to_note('w')
        assert note == 62  # D4

    def test_map_upper_row_csharp(self, root):
        """2 should map to C# of upper octave."""
        keyboard = PianoKeyboard(root, start_octave=3)
        note = keyboard._map_key_to_note('2')
        assert note == 61  # C#4

    def test_map_unknown_key_returns_none(self, root):
        """Unknown key should return None."""
        keyboard = PianoKeyboard(root)
        note = keyboard._map_key_to_note('!')
        assert note is None

    def test_map_respects_octave_shift(self, root):
        """Key mapping should respect octave shift."""
        keyboard = PianoKeyboard(root, start_octave=3)
        keyboard._octave_shift = 1
        note = keyboard._map_key_to_note('z')
        assert note == 60  # C4 (shifted up)


class TestPianoKeyboardNoteName:
    """Tests for note name conversion."""

    def test_middle_c(self, root):
        """Should return C4 for MIDI note 60."""
        keyboard = PianoKeyboard(root)
        name = keyboard.get_note_name(60)
        assert name == "C4"

    def test_a_440(self, root):
        """Should return A4 for MIDI note 69."""
        keyboard = PianoKeyboard(root)
        name = keyboard.get_note_name(69)
        assert name == "A4"

    def test_c_sharp(self, root):
        """Should return C#4 for MIDI note 61."""
        keyboard = PianoKeyboard(root)
        name = keyboard.get_note_name(61)
        assert name == "C#4"

    def test_low_c(self, root):
        """Should return C0 for MIDI note 12."""
        keyboard = PianoKeyboard(root)
        name = keyboard.get_note_name(12)
        assert name == "C0"


class TestPianoKeyboardVelocity:
    """Tests for velocity calculation."""

    def test_velocity_sensitive_default(self, root):
        """Should default to velocity sensitive."""
        keyboard = PianoKeyboard(root)
        assert keyboard._velocity_sensitive is True

    def test_velocity_sensitive_disabled(self, root):
        """Should allow disabling velocity sensitivity."""
        keyboard = PianoKeyboard(root, velocity_sensitive=False)
        assert keyboard._velocity_sensitive is False

    def test_calculate_velocity_top(self, root):
        """Top of key should give lower velocity."""
        keyboard = PianoKeyboard(root)
        key = KeyInfo(midi_note=60, key_type=KeyType.WHITE, x1=0, y1=0, x2=50, y2=100)
        velocity = keyboard._calculate_velocity(0, key)  # Top
        assert velocity == 40  # Minimum

    def test_calculate_velocity_bottom(self, root):
        """Bottom of key should give higher velocity."""
        keyboard = PianoKeyboard(root)
        key = KeyInfo(midi_note=60, key_type=KeyType.WHITE, x1=0, y1=0, x2=50, y2=100)
        velocity = keyboard._calculate_velocity(100, key)  # Bottom
        assert velocity == 127  # Maximum

    def test_calculate_velocity_middle(self, root):
        """Middle of key should give medium velocity."""
        keyboard = PianoKeyboard(root)
        key = KeyInfo(midi_note=60, key_type=KeyType.WHITE, x1=0, y1=0, x2=50, y2=100)
        velocity = keyboard._calculate_velocity(50, key)  # Middle
        assert 70 <= velocity <= 90  # Roughly middle range

    def test_calculate_velocity_not_sensitive(self, root):
        """Should return 100 when not velocity sensitive."""
        keyboard = PianoKeyboard(root, velocity_sensitive=False)
        key = KeyInfo(midi_note=60, key_type=KeyType.WHITE, x1=0, y1=0, x2=50, y2=100)
        velocity = keyboard._calculate_velocity(0, key)
        assert velocity == 100


class TestPianoKeyboardCallbacks:
    """Tests for callback management."""

    def test_set_callbacks(self, root):
        """Should update callbacks via set_callbacks."""
        notes_on = []
        notes_off = []

        keyboard = PianoKeyboard(root)
        keyboard.set_callbacks(
            on_note_on=lambda n, v: notes_on.append((n, v)),
            on_note_off=lambda n: notes_off.append(n)
        )

        keyboard._note_on(60, 100)
        keyboard._note_off(60)

        assert len(notes_on) == 1
        assert len(notes_off) == 1

    def test_set_callbacks_partial(self, root):
        """Should allow setting only one callback."""
        notes_on = []
        keyboard = PianoKeyboard(root, on_note_off=lambda n: None)
        keyboard.set_callbacks(on_note_on=lambda n, v: notes_on.append((n, v)))

        keyboard._note_on(60, 100)
        assert len(notes_on) == 1


class TestPianoKeyboardRefresh:
    """Tests for keyboard refresh."""

    def test_refresh_maintains_pressed(self, root):
        """Refresh should maintain pressed state."""
        keyboard = PianoKeyboard(root)
        keyboard._note_on(60, 100)
        keyboard._note_on(64, 100)

        keyboard.refresh()

        assert 60 in keyboard.pressed_notes
        assert 64 in keyboard.pressed_notes


class TestPianoKeyboardControls:
    """Tests for control panel."""

    def test_show_controls_default(self, root):
        """Should show controls by default."""
        keyboard = PianoKeyboard(root)
        assert keyboard._show_controls is True

    def test_hide_controls(self, root):
        """Should allow hiding controls."""
        keyboard = PianoKeyboard(root, show_controls=False)
        assert keyboard._show_controls is False
        assert not hasattr(keyboard, '_octave_label') or keyboard._octave_label is None

    def test_show_labels_default(self, root):
        """Should show labels by default."""
        keyboard = PianoKeyboard(root)
        assert keyboard._show_labels is True

    def test_hide_labels(self, root):
        """Should allow hiding labels."""
        keyboard = PianoKeyboard(root, show_labels=False)
        assert keyboard._show_labels is False

