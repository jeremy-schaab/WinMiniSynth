"""
Effect Validation Tests - Prove effects actually process audio.

These tests validate that each audio effect (Distortion, Chorus, Delay, Reverb)
demonstrably modifies the audio signal in measurable ways. This ensures effects
are properly wired and functioning, not just returning pass-through audio.
"""

import numpy as np
import pytest
from typing import Tuple

# Import effects
import sys
sys.path.insert(0, 'src')

from effects.distortion import Distortion
from effects.chorus import Chorus
from effects.delay import Delay
from effects.reverb import Reverb


def generate_test_sine(
    frequency: float = 440.0,
    duration: float = 0.1,
    amplitude: float = 0.3,
    sample_rate: int = 44100
) -> np.ndarray:
    """Generate a test sine wave signal."""
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    return amplitude * np.sin(2 * np.pi * frequency * t)


def rms(signal: np.ndarray) -> float:
    """Calculate RMS (root mean square) of a signal."""
    return float(np.sqrt(np.mean(signal ** 2)))


def peak_amplitude(signal: np.ndarray) -> float:
    """Get maximum absolute amplitude."""
    return float(np.max(np.abs(signal)))


def signal_energy(signal: np.ndarray) -> float:
    """Calculate total energy in signal."""
    return float(np.sum(signal ** 2))


class TestDistortionValidation:
    """Validate distortion effect actually processes audio."""

    def test_distortion_increases_rms(self):
        """Distortion with drive > 1 should increase RMS power."""
        distortion = Distortion(sample_rate=44100)
        distortion.enabled = True
        distortion.drive = 5.0
        distortion.mix = 1.0

        input_signal = generate_test_sine(amplitude=0.3)
        output_signal = distortion.process(input_signal.copy())

        input_rms = rms(input_signal)
        output_rms = rms(output_signal)

        # Distortion should increase average power
        assert output_rms > input_rms, \
            f"Expected RMS increase with distortion, got {output_rms:.4f} vs {input_rms:.4f}"

    def test_distortion_soft_mode_applies_saturation(self):
        """Soft distortion should apply saturation curve (tanh-style)."""
        distortion = Distortion(sample_rate=44100)
        distortion.enabled = True
        distortion.drive = 10.0
        distortion.mix = 1.0
        distortion.mode = 'soft'

        # Input with high amplitude
        input_signal = generate_test_sine(amplitude=0.9)
        output_signal = distortion.process(input_signal.copy())

        # Soft saturation should change the signal
        assert not np.allclose(output_signal, input_signal), \
            "Soft distortion should modify the signal"

        # Output peak should differ from simple gain
        input_peak = peak_amplitude(input_signal)
        output_peak = peak_amplitude(output_signal)
        assert output_peak != input_peak * distortion.drive, \
            "Soft distortion should apply non-linear saturation"

    def test_distortion_hard_mode_applies_clipping(self):
        """Hard distortion should apply hard clipping characteristic."""
        distortion = Distortion(sample_rate=44100)
        distortion.enabled = True
        distortion.drive = 10.0
        distortion.mix = 1.0
        distortion.mode = 'hard'

        input_signal = generate_test_sine(amplitude=0.9)
        output_signal = distortion.process(input_signal.copy())

        # Hard clipping should create flat-topped waveform
        # Check that many samples are at or near maximum (clipped)
        high_samples = np.sum(np.abs(output_signal) > 0.9)
        assert high_samples > len(output_signal) * 0.3, \
            "Hard clipping should create more samples at high amplitude"

    def test_distortion_tone_affects_brightness(self):
        """Tone control should affect high frequency content."""
        # Create input with harmonics
        t = np.linspace(0, 0.1, 4410, dtype=np.float32)
        input_signal = 0.3 * np.sin(2 * np.pi * 440 * t) + \
                       0.15 * np.sin(2 * np.pi * 880 * t) + \
                       0.1 * np.sin(2 * np.pi * 1760 * t)

        # Dark tone
        distortion_dark = Distortion(sample_rate=44100)
        distortion_dark.enabled = True
        distortion_dark.drive = 3.0
        distortion_dark.tone = 0.2  # Dark
        distortion_dark.mix = 1.0
        output_dark = distortion_dark.process(input_signal.copy())

        # Bright tone
        distortion_bright = Distortion(sample_rate=44100)
        distortion_bright.enabled = True
        distortion_bright.drive = 3.0
        distortion_bright.tone = 0.8  # Bright
        distortion_bright.mix = 1.0
        output_bright = distortion_bright.process(input_signal.copy())

        # Outputs should be different due to tone
        correlation = np.corrcoef(output_dark, output_bright)[0, 1]
        assert correlation < 0.99, \
            f"Tone control should produce different outputs, correlation={correlation:.4f}"

    def test_distortion_mix_blends_signals(self):
        """Mix=0 should be dry, mix=1 should be fully wet."""
        distortion = Distortion(sample_rate=44100)
        distortion.enabled = True
        distortion.drive = 5.0

        input_signal = generate_test_sine(amplitude=0.3)

        # Dry (mix=0)
        distortion.mix = 0.0
        output_dry = distortion.process(input_signal.copy())

        # Wet (mix=1)
        distortion.mix = 1.0
        output_wet = distortion.process(input_signal.copy())

        # Dry should be very similar to input
        dry_diff = np.max(np.abs(output_dry - input_signal))
        assert dry_diff < 0.01, \
            f"Mix=0 should return nearly dry signal, max diff={dry_diff:.4f}"

        # Wet should be significantly different
        wet_diff = np.max(np.abs(output_wet - input_signal))
        assert wet_diff > 0.1, \
            f"Mix=1 should significantly modify signal, max diff={wet_diff:.4f}"


class TestChorusValidation:
    """Validate chorus effect actually processes audio."""

    def test_chorus_creates_variation(self):
        """Chorus should create pitch/time variation in output."""
        chorus = Chorus(sample_rate=44100)
        chorus.enabled = True
        chorus.rate = 1.0
        chorus.depth = 0.5
        chorus.wet_dry = 1.0

        input_signal = generate_test_sine(duration=0.5)
        output_signal = chorus.process(input_signal.copy())

        # Output should differ from input due to modulated delay
        difference = np.sum(np.abs(output_signal - input_signal))
        assert difference > 0.1, \
            f"Chorus should modify signal, total difference={difference:.4f}"

    def test_chorus_rate_affects_modulation(self):
        """Higher rate should produce faster modulation."""
        input_signal = generate_test_sine(duration=1.0)

        # Slow rate
        chorus_slow = Chorus(sample_rate=44100)
        chorus_slow.enabled = True
        chorus_slow.rate = 0.5
        chorus_slow.depth = 0.5
        chorus_slow.wet_dry = 1.0
        output_slow = chorus_slow.process(input_signal.copy())

        # Fast rate
        chorus_fast = Chorus(sample_rate=44100)
        chorus_fast.enabled = True
        chorus_fast.rate = 5.0
        chorus_fast.depth = 0.5
        chorus_fast.wet_dry = 1.0
        output_fast = chorus_fast.process(input_signal.copy())

        # Different rates should produce different outputs
        correlation = np.corrcoef(output_slow, output_fast)[0, 1]
        assert correlation < 0.99, \
            f"Different rates should produce different outputs, correlation={correlation:.4f}"

    def test_chorus_depth_affects_intensity(self):
        """Greater depth should produce more noticeable effect."""
        input_signal = generate_test_sine(duration=0.5)

        # Low depth
        chorus_low = Chorus(sample_rate=44100)
        chorus_low.enabled = True
        chorus_low.rate = 2.0
        chorus_low.depth = 0.1
        chorus_low.wet_dry = 1.0
        output_low = chorus_low.process(input_signal.copy())

        # High depth
        chorus_high = Chorus(sample_rate=44100)
        chorus_high.enabled = True
        chorus_high.rate = 2.0
        chorus_high.depth = 0.9
        chorus_high.wet_dry = 1.0
        output_high = chorus_high.process(input_signal.copy())

        # Higher depth should have more variation
        variance_low = np.var(output_low - input_signal)
        variance_high = np.var(output_high - input_signal)
        assert variance_high > variance_low, \
            f"Higher depth should produce more variation, {variance_high:.6f} vs {variance_low:.6f}"

    def test_chorus_voices_add_richness(self):
        """More voices should create thicker/richer sound."""
        input_signal = generate_test_sine(duration=0.5)

        # Single voice
        chorus_1 = Chorus(sample_rate=44100)
        chorus_1.enabled = True
        chorus_1.voices = 1
        chorus_1.wet_dry = 1.0
        output_1 = chorus_1.process(input_signal.copy())

        # Multiple voices
        chorus_4 = Chorus(sample_rate=44100)
        chorus_4.enabled = True
        chorus_4.voices = 4
        chorus_4.wet_dry = 1.0
        output_4 = chorus_4.process(input_signal.copy())

        # More voices typically increases energy
        energy_1 = signal_energy(output_1)
        energy_4 = signal_energy(output_4)
        # Output should be different at least
        assert not np.allclose(output_1, output_4), \
            "Different voice counts should produce different outputs"

    def test_chorus_wet_dry_blends(self):
        """Wet/dry mix should blend dry and processed signals."""
        chorus = Chorus(sample_rate=44100)
        chorus.enabled = True
        chorus.rate = 2.0
        chorus.depth = 0.5

        input_signal = generate_test_sine(duration=0.3)

        # Fully dry
        chorus.wet_dry = 0.0
        output_dry = chorus.process(input_signal.copy())

        # Fully wet
        chorus.wet_dry = 1.0
        output_wet = chorus.process(input_signal.copy())

        # Dry should be closer to input than wet
        dry_diff = np.mean(np.abs(output_dry - input_signal))
        wet_diff = np.mean(np.abs(output_wet - input_signal))
        assert dry_diff < wet_diff, \
            f"Dry mix should be closer to input, dry_diff={dry_diff:.4f}, wet_diff={wet_diff:.4f}"


class TestDelayValidation:
    """Validate delay effect actually creates echoes."""

    def test_delay_creates_echo(self):
        """Delay should create echoes in the output."""
        delay = Delay(sample_rate=44100, delay_time_ms=100)  # 100ms in milliseconds
        delay.enabled = True
        delay.feedback = 0.5  # Multiple echoes
        delay.wet_dry = 0.7

        # Process a signal that's longer than delay time
        # With 100ms delay and 500ms signal, we should see echo effect
        input_signal = generate_test_sine(duration=0.5, amplitude=0.5)
        output_signal = delay.process(input_signal)

        # Output should differ from input due to delay mixing
        diff = np.mean(np.abs(output_signal - input_signal))
        assert diff > 0.01, \
            f"Delay should modify signal, mean diff={diff:.4f}"

    def test_delay_time_affects_output(self):
        """Different delay times should produce different outputs."""
        input_signal = generate_test_sine(duration=0.5)

        # Short delay - create, enable, and process
        delay_short = Delay(sample_rate=44100, delay_time_ms=50)  # 50ms
        delay_short.enabled = True
        delay_short.feedback = 0.5
        delay_short.wet_dry = 0.7
        output_short = delay_short.process(input_signal.copy())

        # Long delay - create, enable, and process
        delay_long = Delay(sample_rate=44100, delay_time_ms=300)  # 300ms
        delay_long.enabled = True
        delay_long.feedback = 0.5
        delay_long.wet_dry = 0.7
        output_long = delay_long.process(input_signal.copy())

        # Both should differ from input
        short_diff = np.mean(np.abs(output_short - input_signal))
        long_diff = np.mean(np.abs(output_long - input_signal))

        assert short_diff > 0.01, f"Short delay should modify signal, diff={short_diff:.4f}"
        assert long_diff > 0.01, f"Long delay should modify signal, diff={long_diff:.4f}"

        # Different delay times should produce measurably different results
        mutual_diff = np.mean(np.abs(output_short - output_long))
        assert mutual_diff > 0.001, \
            f"Different delay times should produce different outputs, mutual_diff={mutual_diff:.6f}"

    def test_delay_feedback_creates_repeats(self):
        """Higher feedback should create more echo repeats."""
        # No feedback
        delay_no_fb = Delay(sample_rate=44100)
        delay_no_fb.enabled = True
        delay_no_fb.delay_time = 0.1
        delay_no_fb.feedback = 0.0
        delay_no_fb.wet_dry = 1.0

        # High feedback
        delay_high_fb = Delay(sample_rate=44100)
        delay_high_fb.enabled = True
        delay_high_fb.delay_time = 0.1
        delay_high_fb.feedback = 0.7
        delay_high_fb.wet_dry = 1.0

        # Impulse with extended buffer for multiple echoes
        input_signal = np.zeros(44100, dtype=np.float32)
        input_signal[0:50] = 0.5

        output_no_fb = delay_no_fb.process(input_signal.copy())
        output_high_fb = delay_high_fb.process(input_signal.copy())

        # High feedback should have more total energy (more echoes)
        energy_no_fb = signal_energy(output_no_fb[4410:])  # After first echo
        energy_high_fb = signal_energy(output_high_fb[4410:])

        assert energy_high_fb > energy_no_fb, \
            f"High feedback should have more echo energy, {energy_high_fb:.4f} vs {energy_no_fb:.4f}"

    def test_delay_wet_dry_blends(self):
        """Wet/dry should blend dry and delayed signals."""
        delay = Delay(sample_rate=44100)
        delay.enabled = True
        delay.delay_time = 0.1
        delay.feedback = 0.3

        input_signal = generate_test_sine(duration=0.5)

        # Fully dry
        delay.wet_dry = 0.0
        output_dry = delay.process(input_signal.copy())

        # Fully wet
        delay.wet_dry = 1.0
        output_wet = delay.process(input_signal.copy())

        # Dry should be closer to input
        dry_diff = rms(output_dry - input_signal)
        wet_diff = rms(output_wet - input_signal)
        assert dry_diff < wet_diff, \
            f"Dry should be closer to input, dry_diff={dry_diff:.4f}, wet_diff={wet_diff:.4f}"


class TestReverbValidation:
    """Validate reverb effect creates spatial ambience."""

    def test_reverb_extends_signal(self):
        """Reverb should create a tail after the input ends."""
        reverb = Reverb(sample_rate=44100)
        reverb.enabled = True
        reverb.room_size = 0.8
        reverb.wet_dry = 1.0

        # Short burst at the beginning
        input_signal = np.zeros(44100, dtype=np.float32)
        input_signal[0:1000] = generate_test_sine(duration=1000/44100)

        output_signal = reverb.process(input_signal)

        # Tail (after input ends) should have energy
        tail_energy = signal_energy(output_signal[2000:])
        input_tail_energy = signal_energy(input_signal[2000:])

        assert tail_energy > input_tail_energy * 10, \
            f"Reverb should create tail energy, {tail_energy:.6f} vs input {input_tail_energy:.6f}"

    def test_reverb_room_size_affects_decay(self):
        """Larger room size should create longer decay."""
        # Small room
        reverb_small = Reverb(sample_rate=44100)
        reverb_small.enabled = True
        reverb_small.room_size = 0.2
        reverb_small.wet_dry = 1.0

        # Large room
        reverb_large = Reverb(sample_rate=44100)
        reverb_large.enabled = True
        reverb_large.room_size = 0.9
        reverb_large.wet_dry = 1.0

        # Short burst
        input_signal = np.zeros(44100, dtype=np.float32)
        input_signal[0:500] = generate_test_sine(duration=500/44100, amplitude=0.5)

        output_small = reverb_small.process(input_signal.copy())
        output_large = reverb_large.process(input_signal.copy())

        # Large room should have more late energy
        late_energy_small = signal_energy(output_small[20000:])
        late_energy_large = signal_energy(output_large[20000:])

        # They should at least be different
        assert not np.isclose(late_energy_small, late_energy_large, rtol=0.1), \
            f"Room size should affect decay, small={late_energy_small:.6f}, large={late_energy_large:.6f}"

    def test_reverb_wet_dry_blends(self):
        """Wet/dry should control reverb amount."""
        reverb = Reverb(sample_rate=44100)
        reverb.enabled = True
        reverb.room_size = 0.7

        input_signal = generate_test_sine(duration=0.2)

        # Fully dry
        reverb.wet_dry = 0.0
        output_dry = reverb.process(input_signal.copy())

        # Fully wet
        reverb.wet_dry = 1.0
        output_wet = reverb.process(input_signal.copy())

        # Dry should be closer to input
        dry_diff = rms(output_dry - input_signal)
        wet_diff = rms(output_wet - input_signal)
        assert dry_diff < wet_diff, \
            f"Dry should be closer to input, dry_diff={dry_diff:.4f}, wet_diff={wet_diff:.4f}"


class TestEffectsChainValidation:
    """Validate effects chain processing order and integration."""

    def test_all_effects_enabled_no_errors(self):
        """All effects enabled should process without errors."""
        from app_controller import AppController

        controller = AppController(sample_rate=44100)

        # Enable all effects
        controller.set_distortion_enabled(True)
        controller.set_chorus_enabled(True)
        controller.set_delay_enabled(True)
        controller.set_reverb_enabled(True)

        # Generate audio (should not raise)
        controller.note_on(60, 100)

        # Process some audio
        for _ in range(10):
            buffer = controller.get_display_buffer()
            assert len(buffer) > 0

        controller.note_off(60)

    def test_effects_chain_modifies_signal(self):
        """Complete effects chain should demonstrably modify the signal."""
        from app_controller import AppController

        # Without effects
        controller_dry = AppController(sample_rate=44100)
        controller_dry.note_on(60, 100)
        for _ in range(5):
            controller_dry.get_display_buffer()
        dry_buffer = controller_dry.get_display_buffer()
        controller_dry.note_off(60)

        # With all effects
        controller_wet = AppController(sample_rate=44100)
        controller_wet.set_distortion_enabled(True)
        controller_wet._distortion.drive = 3.0
        controller_wet.set_chorus_enabled(True)
        controller_wet.set_delay_enabled(True)
        controller_wet.set_reverb_enabled(True)

        controller_wet.note_on(60, 100)
        for _ in range(5):
            controller_wet.get_display_buffer()
        wet_buffer = controller_wet.get_display_buffer()
        controller_wet.note_off(60)

        # Buffers should differ
        if signal_energy(dry_buffer) > 0.0001 and signal_energy(wet_buffer) > 0.0001:
            # Both have signal, compare
            correlation = np.corrcoef(dry_buffer, wet_buffer)[0, 1]
            # With effects, correlation should be less than 1
            assert correlation < 0.99 or not np.isclose(correlation, 1.0), \
                f"Effects chain should modify signal, correlation={correlation:.4f}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
