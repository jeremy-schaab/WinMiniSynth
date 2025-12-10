# Virtual Piano Keyboard Widget
"""
keyboard_widget - Canvas-based piano keyboard for the Mini Synthesizer.

Provides a fully-featured virtual piano keyboard with:
- Mouse click to play notes
- Computer keyboard mapping (two rows for two octaves)
- Octave shift controls
- Visual feedback for pressed keys
- Panic button to release all notes
- Velocity sensitivity based on vertical click position
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import IntEnum

from .styles import COLORS, FONTS, ColorScheme


class KeyType(IntEnum):
    """Piano key type enumeration."""
    WHITE = 0
    BLACK = 1


@dataclass
class KeyInfo:
    """Information about a piano key."""
    midi_note: int
    key_type: KeyType
    x1: float
    y1: float
    x2: float
    y2: float
    canvas_id: Optional[int] = None
    label_id: Optional[int] = None

    @property
    def is_black(self) -> bool:
        """Check if this is a black key."""
        return self.key_type == KeyType.BLACK

    @property
    def is_white(self) -> bool:
        """Check if this is a white key."""
        return self.key_type == KeyType.WHITE


class PianoKeyboard(ttk.Frame):
    """
    Canvas-based piano keyboard widget.

    Features:
    - Configurable number of octaves (1-4)
    - Octave shift controls (+/- buttons)
    - Mouse interaction (click, drag, release)
    - Computer keyboard mapping
    - Visual feedback for pressed keys
    - Velocity sensitivity
    - Panic button (all notes off)

    Usage:
        keyboard = PianoKeyboard(
            parent,
            on_note_on=lambda note, vel: print(f"Note ON: {note} @ {vel}"),
            on_note_off=lambda note: print(f"Note OFF: {note}")
        )
        keyboard.pack(fill='x')
    """

    # Note names for labels
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    # Pattern of white/black keys in an octave (0=white, 1=black)
    # Index is note within octave: C=0, C#=1, D=2, ...
    KEY_PATTERN = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0]  # W B W B W W B W B W B W

    # White key indices within octave
    WHITE_INDICES = [0, 2, 4, 5, 7, 9, 11]  # C D E F G A B

    # Black key positions (relative to which white key they follow)
    # Index 0 = after C, 1 = after D, skip E, 3 = after F, 4 = after G, 5 = after A
    BLACK_AFTER_WHITE = {0: 0, 1: 1, 3: 3, 4: 4, 5: 5}  # white_index: black_offset

    # Computer keyboard mapping (lower row = lower octave)
    LOWER_ROW_KEYS = 'zsxdcvgbhnjm,l.;/'
    UPPER_ROW_KEYS = 'q2w3er5t6y7ui9o0p'

    # Default dimensions
    DEFAULT_WIDTH = 800
    DEFAULT_HEIGHT = 120
    WHITE_KEY_WIDTH_RATIO = 1.0
    BLACK_KEY_WIDTH_RATIO = 0.6
    BLACK_KEY_HEIGHT_RATIO = 0.65

    def __init__(
        self,
        parent: tk.Widget,
        num_octaves: int = 2,
        start_octave: int = 3,
        on_note_on: Optional[Callable[[int, int], None]] = None,
        on_note_off: Optional[Callable[[int], None]] = None,
        show_labels: bool = True,
        show_controls: bool = True,
        velocity_sensitive: bool = True,
        **kwargs
    ):
        """
        Initialize the piano keyboard widget.

        Args:
            parent: Parent widget
            num_octaves: Number of octaves to display (1-4)
            start_octave: Starting MIDI octave (0-7)
            on_note_on: Callback for note on (note, velocity)
            on_note_off: Callback for note off (note)
            show_labels: Show note labels on keys
            show_controls: Show octave shift and panic controls
            velocity_sensitive: Enable velocity based on click position
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, style='Dark.TFrame', **kwargs)

        # Validate and store parameters
        self._num_octaves = max(1, min(4, num_octaves))
        self._start_octave = max(0, min(7, start_octave))
        self._on_note_on = on_note_on
        self._on_note_off = on_note_off
        self._show_labels = show_labels
        self._show_controls = show_controls
        self._velocity_sensitive = velocity_sensitive

        # Key tracking
        self._keys: Dict[int, KeyInfo] = {}  # MIDI note -> KeyInfo
        self._pressed_notes: Set[int] = set()  # Currently pressed MIDI notes (user)
        self._external_pressed: Set[int] = set()  # Externally pressed notes (playback)
        self._mouse_pressed_note: Optional[int] = None
        self._keyboard_pressed: Dict[str, int] = {}  # keyboard key -> MIDI note

        # Octave shift (can be negative or positive)
        self._octave_shift = 0
        self._min_octave_shift = -2
        self._max_octave_shift = 4

        # Build the widget
        self._create_controls()
        self._create_keyboard()
        self._bind_events()

    def _create_controls(self):
        """Create the control panel with octave shift and panic button."""
        if not self._show_controls:
            return

        control_frame = ttk.Frame(self, style='Dark.TFrame')
        control_frame.pack(fill='x', pady=(0, 4))

        # Left side: Octave controls
        octave_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        octave_frame.pack(side='left')

        ttk.Label(
            octave_frame,
            text="OCTAVE",
            style='Dark.TLabel'
        ).pack(side='left', padx=(0, 8))

        self._octave_down_btn = ttk.Button(
            octave_frame,
            text="-",
            width=3,
            style='Dark.TButton',
            command=self._octave_down
        )
        self._octave_down_btn.pack(side='left', padx=2)

        self._octave_label = ttk.Label(
            octave_frame,
            text=f"C{self._start_octave}",
            style='Value.TLabel',
            width=4
        )
        self._octave_label.pack(side='left', padx=4)

        self._octave_up_btn = ttk.Button(
            octave_frame,
            text="+",
            width=3,
            style='Dark.TButton',
            command=self._octave_up
        )
        self._octave_up_btn.pack(side='left', padx=2)

        # Center: Keyboard hints
        hints_label = ttk.Label(
            control_frame,
            text="Keys: Z-/ (lower) | Q-P (upper) | Esc=Panic",
            style='Dark.TLabel'
        )
        hints_label.pack(side='left', expand=True)

        # Right side: Panic button
        self._panic_btn = ttk.Button(
            control_frame,
            text="PANIC",
            style='Record.TButton',
            command=self.panic
        )
        self._panic_btn.pack(side='right', padx=4)

    def _create_keyboard(self):
        """Create the piano keyboard canvas."""
        # Calculate canvas dimensions
        num_white_keys = self._num_octaves * 7
        canvas_width = self.DEFAULT_WIDTH
        canvas_height = self.DEFAULT_HEIGHT

        # Create canvas with dark background
        self._canvas = tk.Canvas(
            self,
            width=canvas_width,
            height=canvas_height,
            bg=ColorScheme.bg_input,
            highlightthickness=1,
            highlightbackground=ColorScheme.border
        )
        self._canvas.pack(fill='x', expand=True)

        # Draw the keyboard
        self._draw_keyboard()

    def _draw_keyboard(self):
        """Draw all piano keys on the canvas."""
        self._canvas.delete('all')
        self._keys.clear()

        # Get current canvas dimensions
        self._canvas.update_idletasks()
        width = self._canvas.winfo_width() or self.DEFAULT_WIDTH
        height = self._canvas.winfo_height() or self.DEFAULT_HEIGHT

        # Calculate key dimensions
        num_white_keys = self._num_octaves * 7
        white_key_width = width / num_white_keys
        white_key_height = height
        black_key_width = white_key_width * self.BLACK_KEY_WIDTH_RATIO
        black_key_height = white_key_height * self.BLACK_KEY_HEIGHT_RATIO

        # First pass: Draw white keys
        white_index = 0
        for octave in range(self._num_octaves):
            for note_in_octave in self.WHITE_INDICES:
                midi_note = self._get_midi_note(octave, note_in_octave)
                x = white_index * white_key_width

                # Create key info
                key_info = KeyInfo(
                    midi_note=midi_note,
                    key_type=KeyType.WHITE,
                    x1=x,
                    y1=0,
                    x2=x + white_key_width - 1,
                    y2=white_key_height
                )

                # Draw the key
                key_id = self._canvas.create_rectangle(
                    key_info.x1, key_info.y1, key_info.x2, key_info.y2,
                    fill=ColorScheme.key_white,
                    outline=ColorScheme.border,
                    tags=('key', 'white', f'note_{midi_note}')
                )
                key_info.canvas_id = key_id

                # Add label if enabled
                if self._show_labels and note_in_octave == 0:  # Only label C notes
                    actual_octave = self._start_octave + self._octave_shift + octave
                    label_id = self._canvas.create_text(
                        x + white_key_width / 2,
                        white_key_height - 12,
                        text=f"C{actual_octave}",
                        fill=ColorScheme.fg_muted,
                        font=FONTS['small']
                    )
                    key_info.label_id = label_id

                self._keys[midi_note] = key_info
                white_index += 1

        # Second pass: Draw black keys (on top)
        white_index = 0
        for octave in range(self._num_octaves):
            for i, note_in_octave in enumerate(self.WHITE_INDICES):
                # Check if there's a black key after this white key
                if i in self.BLACK_AFTER_WHITE and i < len(self.WHITE_INDICES) - 1:
                    black_note_in_octave = note_in_octave + 1
                    midi_note = self._get_midi_note(octave, black_note_in_octave)

                    # Position black key centered between this white and next
                    x = (white_index + 1) * white_key_width - black_key_width / 2

                    key_info = KeyInfo(
                        midi_note=midi_note,
                        key_type=KeyType.BLACK,
                        x1=x,
                        y1=0,
                        x2=x + black_key_width,
                        y2=black_key_height
                    )

                    key_id = self._canvas.create_rectangle(
                        key_info.x1, key_info.y1, key_info.x2, key_info.y2,
                        fill=ColorScheme.key_black,
                        outline=ColorScheme.border,
                        tags=('key', 'black', f'note_{midi_note}')
                    )
                    key_info.canvas_id = key_id
                    self._keys[midi_note] = key_info

                white_index += 1

    def _get_midi_note(self, octave_offset: int, note_in_octave: int) -> int:
        """
        Calculate MIDI note number.

        Args:
            octave_offset: Octave offset from start (0 = first octave displayed)
            note_in_octave: Note within octave (0=C, 1=C#, ..., 11=B)

        Returns:
            MIDI note number (0-127)
        """
        actual_octave = self._start_octave + self._octave_shift + octave_offset
        # MIDI note: C0=12, C1=24, C2=36, C3=48, C4=60, etc.
        return (actual_octave + 1) * 12 + note_in_octave

    def _bind_events(self):
        """Bind mouse and keyboard events."""
        # Mouse events on canvas
        self._canvas.bind('<Button-1>', self._on_mouse_press)
        self._canvas.bind('<ButtonRelease-1>', self._on_mouse_release)
        self._canvas.bind('<B1-Motion>', self._on_mouse_drag)
        self._canvas.bind('<Leave>', self._on_mouse_leave)

        # Resize event
        self._canvas.bind('<Configure>', self._on_resize)

        # Request focus for keyboard events
        self._canvas.bind('<Enter>', lambda e: self._canvas.focus_set())

        # Keyboard events (bind to canvas for when it has focus)
        self._canvas.bind('<KeyPress>', self._on_key_press)
        self._canvas.bind('<KeyRelease>', self._on_key_release)

    def _on_resize(self, event):
        """Handle canvas resize."""
        # Redraw keyboard on resize
        self.after(10, self._draw_keyboard)
        # Re-highlight pressed keys
        self.after(20, self._restore_pressed_state)

    def _restore_pressed_state(self):
        """Restore visual state of pressed keys after redraw."""
        for note in self._pressed_notes:
            self._highlight_key(note, True)

    def _get_key_at_position(self, x: int, y: int) -> Optional[int]:
        """
        Get the MIDI note at canvas position.

        Black keys are checked first since they're on top.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            MIDI note number or None if no key at position
        """
        # Check black keys first (they're on top)
        for midi_note, key_info in self._keys.items():
            if key_info.is_black:
                if (key_info.x1 <= x <= key_info.x2 and
                    key_info.y1 <= y <= key_info.y2):
                    return midi_note

        # Then check white keys
        for midi_note, key_info in self._keys.items():
            if key_info.is_white:
                if (key_info.x1 <= x <= key_info.x2 and
                    key_info.y1 <= y <= key_info.y2):
                    return midi_note

        return None

    def _calculate_velocity(self, y: int, key_info: KeyInfo) -> int:
        """
        Calculate velocity based on vertical click position.

        Higher on the key = lower velocity
        Lower on the key = higher velocity

        Args:
            y: Y coordinate of click
            key_info: Key information

        Returns:
            Velocity (1-127)
        """
        if not self._velocity_sensitive:
            return 100

        # Calculate relative position (0=top, 1=bottom)
        key_height = key_info.y2 - key_info.y1
        relative_y = (y - key_info.y1) / key_height
        relative_y = max(0.0, min(1.0, relative_y))

        # Map to velocity: top=40, bottom=127
        velocity = int(40 + relative_y * 87)
        return max(1, min(127, velocity))

    def _on_mouse_press(self, event):
        """Handle mouse button press."""
        note = self._get_key_at_position(event.x, event.y)
        if note is not None:
            key_info = self._keys.get(note)
            velocity = self._calculate_velocity(event.y, key_info) if key_info else 100
            self._note_on(note, velocity)
            self._mouse_pressed_note = note

    def _on_mouse_release(self, event):
        """Handle mouse button release."""
        if self._mouse_pressed_note is not None:
            self._note_off(self._mouse_pressed_note)
            self._mouse_pressed_note = None

    def _on_mouse_drag(self, event):
        """Handle mouse drag (for glissando effect)."""
        note = self._get_key_at_position(event.x, event.y)

        if note != self._mouse_pressed_note:
            # Release previous note
            if self._mouse_pressed_note is not None:
                self._note_off(self._mouse_pressed_note)

            # Press new note
            if note is not None:
                key_info = self._keys.get(note)
                velocity = self._calculate_velocity(event.y, key_info) if key_info else 100
                self._note_on(note, velocity)

            self._mouse_pressed_note = note

    def _on_mouse_leave(self, event):
        """Handle mouse leaving the canvas."""
        if self._mouse_pressed_note is not None:
            self._note_off(self._mouse_pressed_note)
            self._mouse_pressed_note = None

    def _on_key_press(self, event):
        """Handle computer keyboard key press."""
        key = event.char.lower()
        keysym = event.keysym.lower()

        # Handle escape for panic
        if keysym == 'escape':
            self.panic()
            return

        # Handle octave shift
        if keysym == 'z' and event.state & 0x4:  # Ctrl+Z - octave down
            self._octave_down()
            return
        if keysym == 'x' and event.state & 0x4:  # Ctrl+X - octave up
            self._octave_up()
            return

        # Prevent key repeat
        if key in self._keyboard_pressed:
            return

        # Map key to note
        note = self._map_key_to_note(key)
        if note is not None and 0 <= note <= 127:
            self._keyboard_pressed[key] = note
            self._note_on(note, 100)

    def _on_key_release(self, event):
        """Handle computer keyboard key release."""
        key = event.char.lower()

        if key in self._keyboard_pressed:
            note = self._keyboard_pressed.pop(key)
            self._note_off(note)

    def _map_key_to_note(self, key: str) -> Optional[int]:
        """
        Map computer keyboard key to MIDI note.

        Lower row (Z-/) maps to lower octave (C3-E4 by default)
        Upper row (Q-P) maps to upper octave (C4-E5 by default)

        Args:
            key: Keyboard character

        Returns:
            MIDI note number or None
        """
        base_octave = self._start_octave + self._octave_shift

        # Lower row: starting at C of base_octave
        # Pattern: white, black, white, black, white, white, black, ...
        lower_mapping = {
            'z': 0,   # C
            's': 1,   # C#
            'x': 2,   # D
            'd': 3,   # D#
            'c': 4,   # E
            'v': 5,   # F
            'g': 6,   # F#
            'b': 7,   # G
            'h': 8,   # G#
            'n': 9,   # A
            'j': 10,  # A#
            'm': 11,  # B
            ',': 12,  # C (next octave)
            'l': 13,  # C#
            '.': 14,  # D
            ';': 15,  # D#
            '/': 16,  # E
        }

        # Upper row: starting at C of base_octave + 1
        upper_mapping = {
            'q': 0,   # C
            '2': 1,   # C#
            'w': 2,   # D
            '3': 3,   # D#
            'e': 4,   # E
            'r': 5,   # F
            '5': 6,   # F#
            't': 7,   # G
            '6': 8,   # G#
            'y': 9,   # A
            '7': 10,  # A#
            'u': 11,  # B
            'i': 12,  # C (next octave)
            '9': 13,  # C#
            'o': 14,  # D
            '0': 15,  # D#
            'p': 16,  # E
        }

        if key in lower_mapping:
            note_offset = lower_mapping[key]
            return (base_octave + 1) * 12 + note_offset  # C3 = 48

        if key in upper_mapping:
            note_offset = upper_mapping[key]
            return (base_octave + 2) * 12 + note_offset  # C4 = 60

        return None

    def _note_on(self, note: int, velocity: int):
        """
        Trigger note on event.

        Args:
            note: MIDI note number
            velocity: Note velocity (1-127)
        """
        if note in self._pressed_notes:
            return  # Already pressed

        self._pressed_notes.add(note)
        self._highlight_key(note, True)

        if self._on_note_on:
            self._on_note_on(note, velocity)

    def _note_off(self, note: int):
        """
        Trigger note off event.

        Args:
            note: MIDI note number
        """
        if note not in self._pressed_notes:
            return  # Not pressed

        self._pressed_notes.discard(note)
        self._highlight_key(note, False)

        if self._on_note_off:
            self._on_note_off(note)

    def _highlight_key(self, note: int, pressed: bool):
        """
        Highlight or unhighlight a key.

        Args:
            note: MIDI note number
            pressed: True to highlight, False to restore
        """
        key_info = self._keys.get(note)
        if key_info is None or key_info.canvas_id is None:
            return

        if pressed:
            fill_color = ColorScheme.key_pressed
        else:
            fill_color = (ColorScheme.key_black if key_info.is_black
                          else ColorScheme.key_white)

        self._canvas.itemconfig(key_info.canvas_id, fill=fill_color)

    def _octave_up(self):
        """Shift keyboard up one octave."""
        if self._octave_shift < self._max_octave_shift:
            self._release_all_keyboard_notes()
            self._octave_shift += 1
            self._update_octave_display()
            self._draw_keyboard()
            self._restore_pressed_state()

    def _octave_down(self):
        """Shift keyboard down one octave."""
        if self._octave_shift > self._min_octave_shift:
            self._release_all_keyboard_notes()
            self._octave_shift -= 1
            self._update_octave_display()
            self._draw_keyboard()
            self._restore_pressed_state()

    def _update_octave_display(self):
        """Update the octave label in controls."""
        if hasattr(self, '_octave_label'):
            actual_octave = self._start_octave + self._octave_shift
            self._octave_label.config(text=f"C{actual_octave}")

    def _release_all_keyboard_notes(self):
        """Release all notes triggered by computer keyboard."""
        for key, note in list(self._keyboard_pressed.items()):
            self._note_off(note)
        self._keyboard_pressed.clear()

    def panic(self):
        """
        Release all notes immediately (panic button).

        Releases all pressed notes and clears pressed state.
        """
        # Release all pressed notes
        for note in list(self._pressed_notes):
            self._highlight_key(note, False)
            if self._on_note_off:
                self._on_note_off(note)

        self._pressed_notes.clear()
        self._keyboard_pressed.clear()
        self._mouse_pressed_note = None

    # Public API

    @property
    def octave_shift(self) -> int:
        """Get current octave shift."""
        return self._octave_shift

    @octave_shift.setter
    def octave_shift(self, value: int):
        """Set octave shift."""
        value = max(self._min_octave_shift, min(self._max_octave_shift, value))
        if value != self._octave_shift:
            self._octave_shift = value
            self._update_octave_display()
            self._draw_keyboard()

    @property
    def start_octave(self) -> int:
        """Get the base starting octave."""
        return self._start_octave

    @property
    def current_octave(self) -> int:
        """Get the current effective octave (start + shift)."""
        return self._start_octave + self._octave_shift

    @property
    def num_octaves(self) -> int:
        """Get number of displayed octaves."""
        return self._num_octaves

    @property
    def pressed_notes(self) -> Set[int]:
        """Get set of currently pressed MIDI notes."""
        return self._pressed_notes.copy()

    def get_note_name(self, midi_note: int) -> str:
        """
        Get the name of a MIDI note.

        Args:
            midi_note: MIDI note number (0-127)

        Returns:
            Note name (e.g., "C4", "F#5")
        """
        octave = (midi_note // 12) - 1
        note_in_octave = midi_note % 12
        return f"{self.NOTE_NAMES[note_in_octave]}{octave}"

    def set_callbacks(
        self,
        on_note_on: Optional[Callable[[int, int], None]] = None,
        on_note_off: Optional[Callable[[int], None]] = None
    ):
        """
        Set or update callbacks.

        Args:
            on_note_on: Note on callback (note, velocity)
            on_note_off: Note off callback (note)
        """
        if on_note_on is not None:
            self._on_note_on = on_note_on
        if on_note_off is not None:
            self._on_note_off = on_note_off

    def refresh(self):
        """Refresh the keyboard display."""
        self._draw_keyboard()
        self._restore_pressed_state()

    # External note control (for song playback visualization)

    def external_note_on(self, note: int):
        """Highlight a key externally for playback visualization.

        This method highlights the key visually without triggering
        note callbacks. Used by SongPlayer to show which keys are
        being played during song playback.

        Args:
            note: MIDI note number (0-127)
        """
        if note in self._external_pressed:
            return  # Already highlighted

        self._external_pressed.add(note)
        self._highlight_key(note, True)

    def external_note_off(self, note: int):
        """Unhighlight a key that was externally pressed.

        Args:
            note: MIDI note number (0-127)
        """
        if note not in self._external_pressed:
            return

        self._external_pressed.discard(note)

        # Only unhighlight if not also pressed by user
        if note not in self._pressed_notes:
            self._highlight_key(note, False)

    def clear_external_notes(self):
        """Clear all externally pressed notes.

        Unhighlights all keys that were highlighted by external_note_on,
        unless they are also pressed by the user.
        """
        for note in list(self._external_pressed):
            if note not in self._pressed_notes:
                self._highlight_key(note, False)
        self._external_pressed.clear()

    @property
    def external_pressed_notes(self) -> Set[int]:
        """Get set of externally pressed MIDI notes."""
        return self._external_pressed.copy()
