# Visualization Module
"""
visualization - Real-time audio visualization components.

This module provides:
- Oscilloscope: Real-time waveform display
- FilterCurve: Frequency response visualization
- VisualizationPanel: Container widget for all visualizations

Usage:
    from visualization import Oscilloscope, FilterCurve, VisualizationPanel

    # Standalone oscilloscope
    scope = Oscilloscope(parent, width=400, height=200)
    scope.update_waveform(audio_samples)

    # Standalone filter curve
    curve = FilterCurve(parent, width=400, height=200)
    curve.update_response(cutoff=1000, resonance=0.5)

    # Combined panel
    panel = VisualizationPanel(parent)
    panel.update_waveform(audio_samples)
    panel.update_filter(cutoff=1000, resonance=0.5)
"""

# BOLT-006: Waveform & Filter Display
from .oscilloscope import Oscilloscope, TriggerMode, DisplayMode
from .filter_curve import FilterCurve, ScaleMode
from .panel import VisualizationPanel

__all__ = [
    # Oscilloscope
    'Oscilloscope',
    'TriggerMode',
    'DisplayMode',
    # Filter curve
    'FilterCurve',
    'ScaleMode',
    # Combined panel
    'VisualizationPanel',
]
