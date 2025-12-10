# Effects Module
"""
effects - Audio effects processing for the Mini Synthesizer.

This module provides audio effects:
- Reverb: Schroeder reverb with wet/dry mix and room size control
- Delay: Digital delay with feedback and tempo sync
- Chorus: LFO-modulated delay for thickening
- Distortion: Waveshaping with multiple modes

Effects Chain Order (recommended):
    Synth --> Distortion --> Chorus --> Delay --> Reverb --> Output

Usage:
    from effects import Reverb, Delay, Chorus, Distortion

    # Create effects
    distortion = Distortion(sample_rate=44100)
    chorus = Chorus(sample_rate=44100)
    delay = Delay(sample_rate=44100)
    reverb = Reverb(sample_rate=44100)

    # Process audio through chain
    output = synth.generate(num_samples)
    if distortion.enabled:
        output = distortion.process(output)
    if chorus.enabled:
        output = chorus.process(output)
    if delay.enabled:
        output = delay.process(output)
    if reverb.enabled:
        output = reverb.process(output)
"""

from .reverb import Reverb
from .delay import Delay
from .chorus import Chorus
from .flanger import Flanger
from .distortion import Distortion

__all__ = ['Reverb', 'Delay', 'Chorus', 'Flanger', 'Distortion']
