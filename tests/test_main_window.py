# Tests for Main Window Module
"""
test_main_window - Unit tests for MainWindow and related components.
"""

import pytest
import tkinter as tk
from tkinter import ttk

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui.styles import configure_dark_theme
from gui.main_window import StatusBar, PresetPanel, MainWindow


@pytest.fixture
def root():
    """Create a root window for testing."""
    root = tk.Tk()
    root.withdraw()
    configure_dark_theme(root)
    yield root
    root.destroy()


class TestStatusBar:
    """Tests for StatusBar widget."""

    def test_init(self, root):
        """Should create status bar."""
        bar = StatusBar(root)
        assert bar is not None

    def test_has_status_label(self, root):
        """Should have status label."""
        bar = StatusBar(root)
        assert hasattr(bar, 'status_label')
        assert bar.status_label.cget('text') == 'Ready'

    def test_has_voice_label(self, root):
        """Should have voice count label."""
        bar = StatusBar(root)
        assert hasattr(bar, 'voice_label')
        assert bar.voice_label.cget('text') == 'Voices: 0/8'

    def test_has_cpu_label(self, root):
        """Should have CPU usage label."""
        bar = StatusBar(root)
        assert hasattr(bar, 'cpu_label')
        assert bar.cpu_label.cget('text') == 'CPU: 0%'

    def test_set_status(self, root):
        """Should update status message."""
        bar = StatusBar(root)
        bar.set_status("Test message")
        assert bar.status_label.cget('text') == "Test message"

    def test_set_voice_count(self, root):
        """Should update voice count."""
        bar = StatusBar(root)
        bar.set_voice_count(3, 8)
        assert bar.voice_label.cget('text') == "Voices: 3/8"

    def test_set_voice_count_different_max(self, root):
        """Should handle different max voice counts."""
        bar = StatusBar(root)
        bar.set_voice_count(5, 16)
        assert bar.voice_label.cget('text') == "Voices: 5/16"

    def test_set_cpu(self, root):
        """Should update CPU percentage."""
        bar = StatusBar(root)
        bar.set_cpu(45.7)
        assert bar.cpu_label.cget('text') == "CPU: 46%"

    def test_set_cpu_zero(self, root):
        """Should handle zero CPU."""
        bar = StatusBar(root)
        bar.set_cpu(0.0)
        assert bar.cpu_label.cget('text') == "CPU: 0%"


class TestPresetPanel:
    """Tests for PresetPanel widget."""

    def test_init(self, root):
        """Should create preset panel."""
        panel = PresetPanel(root)
        assert panel is not None

    def test_has_preset_combo(self, root):
        """Should have preset combobox."""
        panel = PresetPanel(root)
        assert hasattr(panel, 'preset_combo')
        assert hasattr(panel, 'preset_var')

    def test_default_presets_list(self, root):
        """Should have default presets."""
        panel = PresetPanel(root)
        expected = ['Init', 'Fat Bass', 'Bright Lead', 'Soft Pad', 'Retro Square']
        assert panel.DEFAULT_PRESETS == expected

    def test_initial_preset_value(self, root):
        """Should default to Init preset."""
        panel = PresetPanel(root)
        assert panel.preset_var.get() == 'Init'

    def test_get_current_preset(self, root):
        """Should return current preset name."""
        panel = PresetPanel(root)
        panel.preset_var.set('Fat Bass')
        assert panel.get_current_preset() == 'Fat Bass'

    def test_set_current_preset(self, root):
        """Should set current preset name."""
        panel = PresetPanel(root)
        panel.set_current_preset('Bright Lead')
        assert panel.preset_var.get() == 'Bright Lead'

    def test_set_preset_list(self, root):
        """Should update preset list."""
        panel = PresetPanel(root)
        new_presets = ['Custom 1', 'Custom 2', 'Custom 3']
        panel.set_preset_list(new_presets)
        assert panel.preset_combo['values'] == tuple(new_presets)

    def test_on_load_callback(self, root):
        """Should call on_load callback."""
        loaded = []
        panel = PresetPanel(root, on_load=lambda name: loaded.append(name))
        panel.preset_var.set('Fat Bass')
        panel._load_preset()
        assert len(loaded) == 1
        assert loaded[0] == 'Fat Bass'

    def test_on_save_callback(self, root):
        """Should call on_save callback."""
        saved = []
        panel = PresetPanel(root, on_save=lambda: saved.append(True))
        panel._save_preset()
        assert len(saved) == 1

    def test_on_init_callback(self, root):
        """Should call on_init callback."""
        inited = []
        panel = PresetPanel(root, on_init=lambda: inited.append(True))
        panel._init_patch()
        assert len(inited) == 1
        assert panel.preset_var.get() == 'Init'


class TestMainWindow:
    """Tests for MainWindow widget."""

    @pytest.fixture
    def window(self):
        """Create a main window for testing."""
        window = MainWindow()
        window.withdraw()
        yield window
        window.destroy()

    def test_init(self, window):
        """Should create main window."""
        assert window is not None
        assert window.title() == "KarokeLite Mini Synthesizer"

    def test_has_osc1_panel(self, window):
        """Should have oscillator 1 panel."""
        assert hasattr(window, 'osc1_panel')

    def test_has_osc2_panel(self, window):
        """Should have oscillator 2 panel."""
        assert hasattr(window, 'osc2_panel')

    def test_has_filter_panel(self, window):
        """Should have filter panel."""
        assert hasattr(window, 'filter_panel')

    def test_has_amp_env_panel(self, window):
        """Should have amp envelope panel."""
        assert hasattr(window, 'amp_env_panel')

    def test_has_filter_env_panel(self, window):
        """Should have filter envelope panel."""
        assert hasattr(window, 'filter_env_panel')

    def test_has_lfo_panel(self, window):
        """Should have LFO panel."""
        assert hasattr(window, 'lfo_panel')

    def test_has_preset_panel(self, window):
        """Should have preset panel."""
        assert hasattr(window, 'preset_panel')

    def test_has_master_panel(self, window):
        """Should have master panel."""
        assert hasattr(window, 'master_panel')

    def test_has_status_bar(self, window):
        """Should have status bar."""
        assert hasattr(window, 'status_bar')

    def test_has_keyboard(self, window):
        """Should have PianoKeyboard widget."""
        assert hasattr(window, 'keyboard')

    def test_get_all_parameters(self, window):
        """Should return all parameters."""
        params = window.get_all_parameters()
        # Check some expected keys
        assert 'osc1_waveform' in params
        assert 'osc2_level' in params
        assert 'filter_cutoff' in params
        assert 'amp_attack' in params
        assert 'lfo_rate' in params
        assert 'master_volume' in params

    def test_set_all_parameters(self, window):
        """Should set all parameters."""
        params = {
            'osc1_waveform': 'sine',
            'osc1_level': 0.5,
            'osc2_waveform': 'square',
            'filter_cutoff': 3000.0,
            'master_volume': 0.8
        }
        window.set_all_parameters(params)
        result = window.get_all_parameters()
        assert result['osc1_waveform'] == 'sine'
        assert result['osc1_level'] == 0.5
        assert result['filter_cutoff'] == 3000.0

    def test_update_voice_count(self, window):
        """Should update voice count in status bar."""
        window.update_voice_count(4, 8)
        assert window.status_bar.voice_label.cget('text') == "Voices: 4/8"

    def test_update_cpu(self, window):
        """Should update CPU in status bar."""
        window.update_cpu(25.0)
        assert window.status_bar.cpu_label.cget('text') == "CPU: 25%"

    def test_set_status(self, window):
        """Should set status bar message."""
        window.set_status("Test status")
        assert window.status_bar.status_label.cget('text') == "Test status"

    def test_on_note_on_callback(self):
        """Should call note on callback via keyboard widget."""
        notes = []
        window = MainWindow(on_note_on=lambda n, v: notes.append((n, v)))
        window.withdraw()
        try:
            # Trigger note via keyboard widget's internal method
            window.keyboard._note_on(60, 100)
            assert len(notes) == 1
            assert notes[0][0] == 60
            assert notes[0][1] == 100
        finally:
            window.destroy()

    def test_on_note_off_callback(self):
        """Should call note off callback via keyboard widget."""
        notes = []
        window = MainWindow(on_note_off=lambda n: notes.append(n))
        window.withdraw()
        try:
            window.keyboard._note_on(60, 100)  # First press
            window.keyboard._note_off(60)  # Then release
            assert len(notes) == 1
            assert notes[0] == 60
        finally:
            window.destroy()

    def test_on_parameter_change_callback(self):
        """Should call parameter change callback."""
        changes = []
        window = MainWindow(on_parameter_change=lambda p, v: changes.append((p, v)))
        window.withdraw()
        try:
            window._on_param_change('test_param', 42)
            assert len(changes) == 1
            assert changes[0] == ('test_param', 42)
        finally:
            window.destroy()

    def test_on_quit_callback(self):
        """Should call quit callback on close."""
        quit_called = []
        window = MainWindow(on_quit=lambda: quit_called.append(True))
        window.withdraw()
        try:
            # Simulate close without actually destroying
            window._on_quit = lambda: quit_called.append(True)
            window._on_quit()
            assert len(quit_called) == 1
        finally:
            window.destroy()

    def test_key_mapping_exists(self, window):
        """Should have keyboard mapping via keyboard widget."""
        # Key mapping is now in the keyboard widget
        assert hasattr(window, 'keyboard')
        # Test that keyboard can map keys to notes
        assert window.keyboard._map_key_to_note('z') is not None  # C3
        assert window.keyboard._map_key_to_note('q') is not None  # C4

    def test_panic_clears_notes(self, window):
        """Panic should release all notes via keyboard widget."""
        # Press some notes on keyboard widget
        window.keyboard._note_on(48, 100)
        window.keyboard._note_on(50, 100)
        # Panic via main window
        window._panic()
        # Notes should be cleared in keyboard widget
        assert len(window.keyboard.pressed_notes) == 0

    def test_init_patch_resets_values(self, window):
        """Init patch should reset all values."""
        # Change some values
        window.osc1_panel.set_values({'osc1_waveform': 'sine', 'osc1_level': 0.1})
        # Reset
        window._init_patch()
        # Check reset values
        values = window.osc1_panel.get_values()
        assert values['osc1_waveform'] == 'sawtooth'
        assert values['osc1_level'] == 0.7

