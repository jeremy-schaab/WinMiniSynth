# Tests for Controls Panel Module
"""
test_controls_panel - Unit tests for GUI control panels.
"""

import pytest
import tkinter as tk
from tkinter import ttk

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui.styles import configure_dark_theme
from gui.controls_panel import (
    OscillatorPanel, FilterPanel, EnvelopePanel,
    LFOPanel, MasterPanel
)


@pytest.fixture
def root():
    """Create a root window for testing."""
    root = tk.Tk()
    root.withdraw()
    configure_dark_theme(root)
    yield root
    root.destroy()


class TestOscillatorPanel:
    """Tests for OscillatorPanel widget."""

    def test_init_osc1(self, root):
        """Should create oscillator 1 panel."""
        panel = OscillatorPanel(root, osc_num=1)
        assert panel is not None
        assert panel.osc_num == 1

    def test_init_osc2(self, root):
        """Should create oscillator 2 panel."""
        panel = OscillatorPanel(root, osc_num=2)
        assert panel is not None
        assert panel.osc_num == 2

    def test_has_waveform_variable(self, root):
        """Should have waveform variable."""
        panel = OscillatorPanel(root, osc_num=1)
        assert 'waveform' in panel.variables
        assert panel.variables['waveform'].get() == 'sawtooth'

    def test_has_level_variable(self, root):
        """Should have level variable."""
        panel = OscillatorPanel(root, osc_num=1)
        assert 'level' in panel.variables
        # OSC1 default level is 0.7
        assert panel.variables['level'].get() == 0.7

    def test_osc2_default_level(self, root):
        """OSC2 should have different default level."""
        panel = OscillatorPanel(root, osc_num=2)
        # OSC2 default level is 0.5
        assert panel.variables['level'].get() == 0.5

    def test_has_detune_variable(self, root):
        """Should have detune variable."""
        panel = OscillatorPanel(root, osc_num=1)
        assert 'detune' in panel.variables

    def test_osc2_default_detune(self, root):
        """OSC2 should have non-zero default detune."""
        panel = OscillatorPanel(root, osc_num=2)
        assert panel.variables['detune'].get() == 5.0

    def test_has_octave_variable(self, root):
        """Should have octave variable."""
        panel = OscillatorPanel(root, osc_num=1)
        assert 'octave' in panel.variables
        assert panel.variables['octave'].get() == 0

    def test_has_pulse_width_variable(self, root):
        """Should have pulse width variable."""
        panel = OscillatorPanel(root, osc_num=1)
        assert 'pulse_width' in panel.variables
        assert panel.variables['pulse_width'].get() == 0.5

    def test_waveform_options(self, root):
        """Should have all waveform options."""
        panel = OscillatorPanel(root, osc_num=1)
        expected_waveforms = ['sine', 'sawtooth', 'square', 'triangle', 'pulse']
        assert panel.WAVEFORMS == expected_waveforms

    def test_callback_on_change(self, root):
        """Should call callback on parameter change."""
        changes = []
        panel = OscillatorPanel(
            root, osc_num=1,
            on_change=lambda p, v: changes.append((p, v))
        )
        panel.variables['level'].set(0.5)
        panel._on_level_change(0.5)
        assert len(changes) == 1
        assert changes[0][0] == 'osc1_level'
        assert changes[0][1] == 0.5

    def test_get_values(self, root):
        """Should return all values as dict."""
        panel = OscillatorPanel(root, osc_num=1)
        values = panel.get_values()
        assert 'osc1_waveform' in values
        assert 'osc1_level' in values
        assert 'osc1_detune' in values
        assert 'osc1_octave' in values
        assert 'osc1_pulse_width' in values

    def test_set_values(self, root):
        """Should set values from dict."""
        panel = OscillatorPanel(root, osc_num=1)
        panel.set_values({
            'osc1_waveform': 'sine',
            'osc1_level': 0.3,
            'osc1_detune': 10.0
        })
        assert panel.variables['waveform'].get() == 'sine'
        assert panel.variables['level'].get() == 0.3
        assert panel.variables['detune'].get() == 10.0


class TestFilterPanel:
    """Tests for FilterPanel widget."""

    def test_init(self, root):
        """Should create filter panel."""
        panel = FilterPanel(root)
        assert panel is not None

    def test_has_cutoff_variable(self, root):
        """Should have cutoff variable."""
        panel = FilterPanel(root)
        assert 'cutoff' in panel.variables
        assert panel.variables['cutoff'].get() == 2000.0

    def test_has_resonance_variable(self, root):
        """Should have resonance variable."""
        panel = FilterPanel(root)
        assert 'resonance' in panel.variables
        assert panel.variables['resonance'].get() == 0.3

    def test_has_env_amount_variable(self, root):
        """Should have envelope amount variable."""
        panel = FilterPanel(root)
        assert 'env_amount' in panel.variables
        assert panel.variables['env_amount'].get() == 0.5

    def test_callback_on_cutoff_change(self, root):
        """Should call callback on cutoff change."""
        changes = []
        panel = FilterPanel(
            root,
            on_change=lambda p, v: changes.append((p, v))
        )
        panel._on_cutoff_change(1000)
        assert len(changes) == 1
        assert changes[0][0] == 'filter_cutoff'
        assert changes[0][1] == 1000

    def test_cutoff_label_formatting_hz(self, root):
        """Should format cutoff as Hz for values < 1000."""
        panel = FilterPanel(root)
        panel._on_cutoff_change(500)
        assert panel.cutoff_label.cget('text') == '500 Hz'

    def test_cutoff_label_formatting_khz(self, root):
        """Should format cutoff as kHz for values >= 1000."""
        panel = FilterPanel(root)
        panel._on_cutoff_change(5000)
        assert panel.cutoff_label.cget('text') == '5.0 kHz'

    def test_get_values(self, root):
        """Should return all values as dict."""
        panel = FilterPanel(root)
        values = panel.get_values()
        assert 'filter_cutoff' in values
        assert 'filter_resonance' in values
        assert 'filter_env_amount' in values

    def test_set_values(self, root):
        """Should set values from dict."""
        panel = FilterPanel(root)
        panel.set_values({
            'filter_cutoff': 3000.0,
            'filter_resonance': 0.5,
            'filter_env_amount': 0.8
        })
        assert panel.variables['cutoff'].get() == 3000.0
        assert panel.variables['resonance'].get() == 0.5
        assert panel.variables['env_amount'].get() == 0.8


class TestEnvelopePanel:
    """Tests for EnvelopePanel widget."""

    def test_init_amp_envelope(self, root):
        """Should create amp envelope panel."""
        panel = EnvelopePanel(root, name="AMP", prefix="amp_")
        assert panel is not None
        assert panel.name == "AMP"

    def test_init_filter_envelope(self, root):
        """Should create filter envelope panel."""
        panel = EnvelopePanel(root, name="FILTER", prefix="filter_")
        assert panel is not None
        assert panel.name == "FILTER"

    def test_has_adsr_variables(self, root):
        """Should have all ADSR variables."""
        panel = EnvelopePanel(root, name="AMP", prefix="amp_")
        assert 'attack' in panel.variables
        assert 'decay' in panel.variables
        assert 'sustain' in panel.variables
        assert 'release' in panel.variables

    def test_default_values(self, root):
        """Should have default ADSR values."""
        panel = EnvelopePanel(
            root, name="AMP", prefix="amp_",
            defaults={'attack': 0.01, 'decay': 0.1, 'sustain': 0.7, 'release': 0.3}
        )
        assert panel.variables['attack'].get() == 0.01
        assert panel.variables['decay'].get() == 0.1
        assert panel.variables['sustain'].get() == 0.7
        assert panel.variables['release'].get() == 0.3

    def test_custom_defaults(self, root):
        """Should use custom default values."""
        panel = EnvelopePanel(
            root, name="TEST", prefix="test_",
            defaults={'attack': 0.5, 'decay': 0.5, 'sustain': 0.5, 'release': 0.5}
        )
        assert panel.variables['attack'].get() == 0.5
        assert panel.variables['sustain'].get() == 0.5

    def test_callback_on_change(self, root):
        """Should call callback on parameter change."""
        changes = []
        panel = EnvelopePanel(
            root, name="AMP", prefix="amp_",
            on_change=lambda p, v: changes.append((p, v))
        )
        panel._on_change_param('attack', 0.5)
        assert len(changes) == 1
        assert changes[0][0] == 'amp_attack'
        assert changes[0][1] == 0.5

    def test_get_values(self, root):
        """Should return all values with prefix."""
        panel = EnvelopePanel(root, name="AMP", prefix="amp_")
        values = panel.get_values()
        assert 'amp_attack' in values
        assert 'amp_decay' in values
        assert 'amp_sustain' in values
        assert 'amp_release' in values

    def test_set_values(self, root):
        """Should set values from dict."""
        panel = EnvelopePanel(root, name="AMP", prefix="amp_")
        panel.set_values({
            'amp_attack': 0.2,
            'amp_decay': 0.3,
            'amp_sustain': 0.5,
            'amp_release': 0.4
        })
        assert panel.variables['attack'].get() == 0.2
        assert panel.variables['sustain'].get() == 0.5

    def test_has_canvas(self, root):
        """Should have envelope visualization canvas."""
        panel = EnvelopePanel(root, name="AMP", prefix="amp_")
        assert hasattr(panel, 'canvas')
        assert isinstance(panel.canvas, tk.Canvas)


class TestLFOPanel:
    """Tests for LFOPanel widget."""

    def test_init(self, root):
        """Should create LFO panel."""
        panel = LFOPanel(root)
        assert panel is not None

    def test_has_waveform_variable(self, root):
        """Should have waveform variable."""
        panel = LFOPanel(root)
        assert 'waveform' in panel.variables
        assert panel.variables['waveform'].get() == 'sine'

    def test_has_rate_variable(self, root):
        """Should have rate variable."""
        panel = LFOPanel(root)
        assert 'rate' in panel.variables
        assert panel.variables['rate'].get() == 5.0

    def test_has_depth_variable(self, root):
        """Should have depth variable."""
        panel = LFOPanel(root)
        assert 'depth' in panel.variables
        assert panel.variables['depth'].get() == 0.5

    def test_has_routing_variables(self, root):
        """Should have routing checkbox variables."""
        panel = LFOPanel(root)
        assert 'to_pitch' in panel.variables
        assert 'to_filter' in panel.variables
        assert 'to_pw' in panel.variables
        assert panel.variables['to_pitch'].get() == False
        assert panel.variables['to_filter'].get() == False
        assert panel.variables['to_pw'].get() == False

    def test_waveform_options(self, root):
        """Should have all LFO waveform options."""
        panel = LFOPanel(root)
        expected = ['sine', 'triangle', 'square', 'sawtooth']
        assert panel.WAVEFORMS == expected

    def test_callback_on_rate_change(self, root):
        """Should call callback on rate change."""
        changes = []
        panel = LFOPanel(root, on_change=lambda p, v: changes.append((p, v)))
        panel._on_rate_change(10.0)
        assert len(changes) == 1
        assert changes[0][0] == 'lfo_rate'
        assert changes[0][1] == 10.0

    def test_get_values(self, root):
        """Should return all values as dict."""
        panel = LFOPanel(root)
        values = panel.get_values()
        assert 'lfo_waveform' in values
        assert 'lfo_rate' in values
        assert 'lfo_depth' in values
        assert 'lfo_to_pitch' in values
        assert 'lfo_to_filter' in values
        assert 'lfo_to_pw' in values

    def test_routing_values_as_float(self, root):
        """Routing values should be returned as float."""
        panel = LFOPanel(root)
        panel.variables['to_pitch'].set(True)
        values = panel.get_values()
        assert values['lfo_to_pitch'] == 1.0
        assert values['lfo_to_filter'] == 0.0


class TestMasterPanel:
    """Tests for MasterPanel widget."""

    def test_init(self, root):
        """Should create master panel."""
        panel = MasterPanel(root)
        assert panel is not None

    def test_has_volume_variable(self, root):
        """Should have volume variable."""
        panel = MasterPanel(root)
        assert 'volume' in panel.variables
        assert panel.variables['volume'].get() == 0.7

    def test_callback_on_volume_change(self, root):
        """Should call callback on volume change."""
        changes = []
        panel = MasterPanel(root, on_change=lambda p, v: changes.append((p, v)))
        panel._on_volume_change(0.5)
        assert len(changes) == 1
        assert changes[0][0] == 'master_volume'
        assert changes[0][1] == 0.5

    def test_volume_label_update(self, root):
        """Should update volume label on change."""
        panel = MasterPanel(root)
        panel._on_volume_change(0.5)
        assert panel.volume_label.cget('text') == '0.50'

    def test_get_values(self, root):
        """Should return volume as dict."""
        panel = MasterPanel(root)
        values = panel.get_values()
        assert 'master_volume' in values
        assert values['master_volume'] == 0.7

    def test_set_values(self, root):
        """Should set volume from dict."""
        panel = MasterPanel(root)
        panel.set_values({'master_volume': 0.3})
        assert panel.variables['volume'].get() == 0.3
