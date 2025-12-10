# Tests for Metronome Panel
"""
test_metronome_panel - Unit tests for metronome GUI panel.
"""

import pytest
import tkinter as tk
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui.metronome_panel import MetronomePanel


@pytest.fixture
def root():
    """Create tkinter root window for testing."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def panel(root):
    """Create MetronomePanel for testing."""
    panel = MetronomePanel(root)
    panel.pack()
    root.update()
    return panel


class TestMetronomePanelInit:
    """Tests for MetronomePanel initialization."""

    def test_creates_panel(self, panel):
        """Should create panel widget."""
        assert panel is not None
        assert isinstance(panel, MetronomePanel)

    def test_default_bpm(self, panel):
        """Should have default BPM of 120."""
        assert panel.bpm == 120.0

    def test_default_time_signature(self, panel):
        """Should have default time signature 4/4."""
        assert panel.time_signature == (4, 4)

    def test_default_volume(self, panel):
        """Should have default volume of 0.5."""
        assert panel.volume == 0.5

    def test_not_running_initially(self, panel):
        """Should not be running initially."""
        assert not panel.is_running


class TestMetronomePanelBPM:
    """Tests for BPM control."""

    def test_set_bpm(self, panel):
        """Should set BPM."""
        panel.bpm = 140
        assert panel.bpm == 140.0

    def test_bpm_clamped_low(self, panel):
        """BPM should clamp to minimum."""
        panel.bpm = 10
        assert panel.bpm == panel.MIN_BPM

    def test_bpm_clamped_high(self, panel):
        """BPM should clamp to maximum."""
        panel.bpm = 500
        assert panel.bpm == panel.MAX_BPM


class TestMetronomePanelTimeSignature:
    """Tests for time signature control."""

    def test_set_time_signature(self, panel):
        """Should set time signature."""
        panel.time_signature = (3, 4)
        assert panel.time_signature == (3, 4)

    def test_time_signature_changes_indicators(self, panel, root):
        """Time signature should update beat indicators."""
        panel.time_signature = (6, 8)
        root.update()
        # Should have 6 beat indicators
        assert len(panel._beat_indicators) == 6


class TestMetronomePanelVolume:
    """Tests for volume control."""

    def test_set_volume(self, panel):
        """Should set volume."""
        panel.volume = 0.8
        assert panel.volume == 0.8

    def test_volume_clamped_low(self, panel):
        """Volume should clamp to 0."""
        panel.volume = -0.5
        assert panel.volume == 0.0

    def test_volume_clamped_high(self, panel):
        """Volume should clamp to 1."""
        panel.volume = 1.5
        assert panel.volume == 1.0


class TestMetronomePanelCallbacks:
    """Tests for callback functionality."""

    def test_on_start_callback(self, root):
        """Should call on_start when started."""
        started = []
        panel = MetronomePanel(root, on_start=lambda: started.append(True))
        panel.pack()

        panel._start_metronome()

        assert len(started) == 1

    def test_on_stop_callback(self, root):
        """Should call on_stop when stopped."""
        stopped = []
        panel = MetronomePanel(root, on_stop=lambda: stopped.append(True))
        panel.pack()

        panel._start_metronome()
        panel._stop_metronome()

        assert len(stopped) == 1

    def test_on_bpm_change_callback(self, root):
        """Should call on_bpm_change when BPM changes."""
        bpm_values = []
        panel = MetronomePanel(root, on_bpm_change=lambda b: bpm_values.append(b))
        panel.pack()

        panel._bpm_var.set(150)
        panel._on_bpm_spinbox_change()

        assert 150 in bpm_values

    def test_on_time_sig_change_callback(self, root):
        """Should call on_time_sig_change."""
        sigs = []
        panel = MetronomePanel(
            root,
            on_time_sig_change=lambda n, d: sigs.append((n, d))
        )
        panel.pack()

        panel._time_sig_var.set("3/4")
        panel._on_time_sig_change()

        assert (3, 4) in sigs


class TestMetronomePanelTapTempo:
    """Tests for tap tempo functionality."""

    def test_tap_tempo_first_tap(self, panel):
        """First tap should not change BPM."""
        original_bpm = panel.bpm
        panel._tap_times = []
        panel._on_tap()
        # BPM should remain unchanged after first tap
        assert panel.bpm == original_bpm


class TestMetronomePanelUpdateBeat:
    """Tests for beat indicator update."""

    def test_update_beat(self, panel, root):
        """Should update beat indicators."""
        panel.update_beat(1, False)
        root.update()
        # Second indicator (index 1) should be highlighted
        # Just verify no crash

    def test_update_beat_downbeat(self, panel, root):
        """Should highlight downbeat differently."""
        panel.update_beat(0, True)
        root.update()
        # First indicator should show downbeat color


class TestMetronomePanelGetSetValues:
    """Tests for get/set values."""

    def test_get_values(self, panel):
        """Should return dict of values."""
        panel.bpm = 140
        panel.volume = 0.7

        values = panel.get_values()

        assert values['metro_bpm'] == 140
        assert values['metro_volume'] == 0.7
        assert 'metro_time_sig_num' in values
        assert 'metro_time_sig_denom' in values

    def test_set_values(self, panel):
        """Should set values from dict."""
        values = {
            'metro_bpm': 160,
            'metro_volume': 0.9,
            'metro_time_sig_num': 3,
            'metro_time_sig_denom': 4
        }

        panel.set_values(values)

        assert panel.bpm == 160
        assert panel.volume == 0.9
        assert panel.time_signature == (3, 4)
