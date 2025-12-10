# Tests for Recording Panel
"""
test_recording_panel - Unit tests for recording GUI panel.
"""

import pytest
import tkinter as tk
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui.recording_panel import RecordingPanel


@pytest.fixture
def root():
    """Create tkinter root window for testing."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def panel(root):
    """Create RecordingPanel for testing."""
    panel = RecordingPanel(root)
    panel.pack()
    root.update()
    return panel


class TestRecordingPanelInit:
    """Tests for RecordingPanel initialization."""

    def test_creates_panel(self, panel):
        """Should create panel widget."""
        assert panel is not None
        assert isinstance(panel, RecordingPanel)

    def test_not_recording_initially(self, panel):
        """Should not be recording initially."""
        assert not panel.is_recording

    def test_not_paused_initially(self, panel):
        """Should not be paused initially."""
        assert not panel.is_paused

    def test_not_armed_initially(self, panel):
        """Should not be armed initially."""
        assert not panel.is_armed

    def test_zero_duration_initially(self, panel):
        """Should have zero duration initially."""
        assert panel.duration == 0.0


class TestRecordingPanelState:
    """Tests for recording state."""

    def test_start_recording(self, panel):
        """Starting should set recording state."""
        panel._start_recording()
        assert panel.is_recording
        assert not panel.is_paused

    def test_stop_recording(self, panel):
        """Stopping should clear recording state."""
        panel._start_recording()
        panel._stop_recording()
        assert not panel.is_recording

    def test_pause_recording(self, panel):
        """Pausing should set paused state."""
        panel._start_recording()
        panel._pause_recording()
        assert panel.is_paused

    def test_resume_recording(self, panel):
        """Resuming should clear paused state."""
        panel._start_recording()
        panel._pause_recording()
        panel._resume_recording()
        assert not panel.is_paused
        assert panel.is_recording

    def test_arm_recording(self, panel):
        """Arming should set armed state."""
        panel._arm_recording()
        assert panel.is_armed

    def test_disarm_recording(self, panel):
        """Disarming should clear armed state."""
        panel._arm_recording()
        panel._disarm_recording()
        assert not panel.is_armed


class TestRecordingPanelCallbacks:
    """Tests for callback functionality."""

    def test_on_record_callback(self, root):
        """Should call on_record when recording starts."""
        recorded = []
        panel = RecordingPanel(root, on_record=lambda: recorded.append(True))
        panel.pack()

        panel._start_recording()

        assert len(recorded) == 1

    def test_on_stop_callback(self, root):
        """Should call on_stop when recording stops."""
        stopped = []
        panel = RecordingPanel(root, on_stop=lambda: stopped.append(True))
        panel.pack()

        panel._start_recording()
        panel._stop_recording()

        assert len(stopped) == 1

    def test_on_pause_callback(self, root):
        """Should call on_pause when recording pauses."""
        paused = []
        panel = RecordingPanel(root, on_pause=lambda: paused.append(True))
        panel.pack()

        panel._start_recording()
        panel._pause_recording()

        assert len(paused) == 1

    def test_on_resume_callback(self, root):
        """Should call on_resume when recording resumes."""
        resumed = []
        panel = RecordingPanel(root, on_resume=lambda: resumed.append(True))
        panel.pack()

        panel._start_recording()
        panel._pause_recording()
        panel._resume_recording()

        assert len(resumed) == 1

    def test_on_arm_callback(self, root):
        """Should call on_arm when recording arms."""
        armed = []
        panel = RecordingPanel(root, on_arm=lambda: armed.append(True))
        panel.pack()

        panel._arm_recording()

        assert len(armed) == 1


class TestRecordingPanelUpdateDuration:
    """Tests for duration updates."""

    def test_update_duration(self, panel, root):
        """Should update duration display."""
        panel.update_duration(65.5)  # 1:05.50
        root.update()

        assert panel.duration == 65.5
        # Time label should show formatted time
        assert "01:05" in panel._time_label.cget('text') or "1:05" in panel._time_label.cget('text')

    def test_update_duration_zero(self, panel, root):
        """Should handle zero duration."""
        panel.update_duration(0.0)
        root.update()

        assert "00:00" in panel._time_label.cget('text')


class TestRecordingPanelUpdateLevel:
    """Tests for level meter updates."""

    def test_update_level(self, panel, root):
        """Should update level meter."""
        panel.update_level(0.5)
        root.update()
        # Just verify no crash

    def test_update_level_zero(self, panel, root):
        """Should handle zero level."""
        panel.update_level(0.0)
        root.update()
        # dB label should show -inf
        assert "inf" in panel._level_label.cget('text').lower()

    def test_update_level_max(self, panel, root):
        """Should handle max level."""
        panel.update_level(1.0)
        root.update()
        # Should show ~0 dB
        assert "0" in panel._level_label.cget('text')


class TestRecordingPanelUpdateState:
    """Tests for state updates from external source."""

    def test_update_state_recording(self, panel, root):
        """Should update to RECORDING state."""
        panel.update_state('RECORDING')
        root.update()

        assert panel.is_recording
        assert panel._status_label.cget('text') == 'RECORDING'

    def test_update_state_paused(self, panel, root):
        """Should update to PAUSED state."""
        panel.update_state('RECORDING')
        panel.update_state('PAUSED')
        root.update()

        assert panel.is_paused
        assert panel._status_label.cget('text') == 'PAUSED'

    def test_update_state_armed(self, panel, root):
        """Should update to ARMED state."""
        panel.update_state('ARMED')
        root.update()

        assert panel.is_armed
        assert panel._status_label.cget('text') == 'ARMED'

    def test_update_state_idle(self, panel, root):
        """Should update to IDLE state."""
        panel.update_state('RECORDING')
        panel.update_state('IDLE')
        root.update()

        assert not panel.is_recording
        assert panel._status_label.cget('text') == 'IDLE'


class TestRecordingPanelCanUndo:
    """Tests for undo availability."""

    def test_set_can_undo_true(self, panel, root):
        """Should enable undo button."""
        panel.set_has_recording(True)
        panel._recording = False
        panel.set_can_undo(True)
        root.update()

        assert str(panel._undo_btn.cget('state')) == 'normal'

    def test_set_can_undo_false(self, panel, root):
        """Should disable undo button."""
        panel.set_can_undo(False)
        root.update()

        assert str(panel._undo_btn.cget('state')) == 'disabled'


class TestRecordingPanelHasRecording:
    """Tests for recording availability."""

    def test_set_has_recording_true(self, panel, root):
        """Should enable export/clear when recording exists."""
        panel.set_has_recording(True)
        panel._recording = False  # Not currently recording
        panel._update_button_states()
        root.update()

        assert str(panel._export_btn.cget('state')) == 'normal'
        assert str(panel._clear_btn.cget('state')) == 'normal'

    def test_set_has_recording_false(self, panel, root):
        """Should disable export/clear when no recording."""
        panel.set_has_recording(False)
        root.update()

        assert str(panel._export_btn.cget('state')) == 'disabled'
        assert str(panel._clear_btn.cget('state')) == 'disabled'


class TestRecordingPanelSetInfo:
    """Tests for info text display."""

    def test_set_info(self, panel, root):
        """Should display info text."""
        panel.set_info("2.5 MB, 44100 Hz")
        root.update()

        assert panel._info_label.cget('text') == "2.5 MB, 44100 Hz"


class TestRecordingPanelGetValues:
    """Tests for get_values."""

    def test_get_values(self, panel):
        """Should return dict of values."""
        panel._duration = 10.5
        panel._peak_level = 0.8

        values = panel.get_values()

        assert values['rec_duration'] == 10.5
        assert values['rec_peak_level'] == 0.8


class TestRecordingPanelClear:
    """Tests for clear functionality."""

    def test_clear_click(self, root):
        """Clear should call callback and reset state."""
        cleared = []
        panel = RecordingPanel(root, on_clear=lambda: cleared.append(True))
        panel.pack()

        panel._has_recording = True
        panel._duration = 10.0
        panel._on_clear_click()

        assert len(cleared) == 1
        assert panel._duration == 0.0
        assert not panel._has_recording
