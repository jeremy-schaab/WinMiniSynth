# SynthVoice module for Mini Synthesizer
"""
voice.py - Single synthesizer voice combining all sound components

Implements the SynthVoice entity from the domain model.
A SynthVoice is a complete monophonic sound-producing chain that
combines oscillators, filter, envelopes, and LFO into a unified voice.

Voice signal flow:
    OSC1 + OSC2 (mixed) -> Filter -> VCA (amp envelope) -> Output

    LFO modulates: pitch (vibrato), filter cutoff, pulse width
    Filter envelope modulates: filter cutoff
    Amp envelope controls: VCA level

Usage:
    voice = SynthVoice(sample_rate=44100)
    voice.note_on(60, 100)  # Middle C, velocity 100
    samples = voice.generate(512)
    voice.note_off()
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np

from .oscillator import Oscillator, Waveform, midi_to_frequency
from .envelope import ADSREnvelope, EnvelopeStage
from .filter import MoogFilter
from .lfo import LFO


@dataclass
class VoiceParameters:
    """Aggregates all controllable parameters for a voice.

    Attributes:
        osc1_waveform: Oscillator 1 waveform type
        osc1_level: Oscillator 1 output level (0.0 to 1.0)
        osc2_waveform: Oscillator 2 waveform type
        osc2_level: Oscillator 2 output level (0.0 to 1.0)
        osc2_detune: Oscillator 2 detune in cents (-100 to 100)
        filter_cutoff: Filter cutoff frequency in Hz
        filter_resonance: Filter resonance (0.0 to 1.0)
        filter_env_amount: Filter envelope modulation amount (-1.0 to 1.0)
        amp_attack: Amplitude envelope attack time (seconds)
        amp_decay: Amplitude envelope decay time (seconds)
        amp_sustain: Amplitude envelope sustain level (0.0 to 1.0)
        amp_release: Amplitude envelope release time (seconds)
        filter_attack: Filter envelope attack time (seconds)
        filter_decay: Filter envelope decay time (seconds)
        filter_sustain: Filter envelope sustain level (0.0 to 1.0)
        filter_release: Filter envelope release time (seconds)
        lfo_rate: LFO frequency in Hz
        lfo_depth: LFO depth (0.0 to 1.0)
        lfo_waveform: LFO waveform type
        lfo_to_pitch: LFO to pitch modulation amount (0.0 to 1.0)
        lfo_to_filter: LFO to filter modulation amount (0.0 to 1.0)
        lfo_to_pw: LFO to pulse width modulation amount (0.0 to 1.0)
    """
    # Oscillator parameters
    osc1_waveform: Waveform = Waveform.SAWTOOTH
    osc1_level: float = 0.7
    osc2_waveform: Waveform = Waveform.SAWTOOTH
    osc2_level: float = 0.5
    osc2_detune: float = 5.0  # cents

    # Filter parameters
    filter_cutoff: float = 2000.0
    filter_resonance: float = 0.3
    filter_env_amount: float = 0.0

    # Amplitude envelope
    amp_attack: float = 0.01
    amp_decay: float = 0.1
    amp_sustain: float = 0.7
    amp_release: float = 0.3

    # Filter envelope
    filter_attack: float = 0.01
    filter_decay: float = 0.2
    filter_sustain: float = 0.3
    filter_release: float = 0.3

    # LFO parameters
    lfo_rate: float = 5.0
    lfo_depth: float = 0.3
    lfo_waveform: Waveform = Waveform.SINE
    lfo_to_pitch: float = 0.0
    lfo_to_filter: float = 0.0
    lfo_to_pw: float = 0.0


class SynthVoice:
    """Single synthesizer voice with complete sound chain.

    Combines two oscillators, a filter, two envelopes, and an LFO
    into a complete monophonic voice. Multiple voices enable polyphony.

    Attributes:
        sample_rate: Audio sample rate in Hz
        voice_id: Unique identifier for this voice
        note: Currently playing MIDI note (-1 if inactive)
        velocity: Note velocity (0-127)
    """

    def __init__(self, sample_rate: int = 44100, voice_id: int = 0):
        """Initialize voice with sample rate.

        Args:
            sample_rate: Audio sample rate in Hz (default: 44100)
            voice_id: Unique identifier for this voice (default: 0)
        """
        self.sample_rate = sample_rate
        self.voice_id = voice_id

        # Voice state
        self._note: int = -1  # -1 = inactive
        self._velocity: int = 0
        self._velocity_scale: float = 0.0

        # Sound components
        self._osc1 = Oscillator(sample_rate)
        self._osc2 = Oscillator(sample_rate)
        self._filter = MoogFilter(sample_rate)
        self._amp_envelope = ADSREnvelope(sample_rate)
        self._filter_envelope = ADSREnvelope(sample_rate)
        self._lfo = LFO(sample_rate)

        # Anti-click fade ramps (3ms fade = ~132 samples at 44100Hz)
        self._fade_samples = int(sample_rate * 0.003)  # 3ms
        self._fade_in_counter = 0  # Counts up during fade-in
        self._fade_out_counter = 0  # Counts down during fade-out
        self._is_stealing = False  # True when fading out for steal

        # Voice parameters
        self._params = VoiceParameters()

        # Work buffers (pre-allocated)
        self._osc1_buffer: Optional[np.ndarray] = None
        self._osc2_buffer: Optional[np.ndarray] = None
        self._mix_buffer: Optional[np.ndarray] = None
        self._amp_env_buffer: Optional[np.ndarray] = None
        self._filter_env_buffer: Optional[np.ndarray] = None
        self._lfo_buffer: Optional[np.ndarray] = None

        # Apply default parameters
        self._apply_parameters()

    @property
    def note(self) -> int:
        """Currently playing MIDI note (-1 if inactive)."""
        return self._note

    @property
    def velocity(self) -> int:
        """Note velocity (0-127)."""
        return self._velocity

    @property
    def parameters(self) -> VoiceParameters:
        """Voice parameter settings."""
        return self._params

    @parameters.setter
    def parameters(self, params: VoiceParameters) -> None:
        """Set voice parameters and apply to components."""
        self._params = params
        self._apply_parameters()

    def _apply_parameters(self) -> None:
        """Apply current parameters to all voice components."""
        p = self._params

        # Oscillator settings
        self._osc1.waveform = p.osc1_waveform
        self._osc1.level = p.osc1_level
        self._osc2.waveform = p.osc2_waveform
        self._osc2.level = p.osc2_level

        # Filter settings
        self._filter.cutoff = p.filter_cutoff
        self._filter.resonance = p.filter_resonance

        # Amplitude envelope
        self._amp_envelope.attack = p.amp_attack
        self._amp_envelope.decay = p.amp_decay
        self._amp_envelope.sustain = p.amp_sustain
        self._amp_envelope.release = p.amp_release

        # Filter envelope
        self._filter_envelope.attack = p.filter_attack
        self._filter_envelope.decay = p.filter_decay
        self._filter_envelope.sustain = p.filter_sustain
        self._filter_envelope.release = p.filter_release

        # LFO settings
        self._lfo.frequency = p.lfo_rate
        self._lfo.depth = p.lfo_depth
        self._lfo.waveform = p.lfo_waveform

    def _ensure_buffers(self, num_samples: int) -> None:
        """Ensure work buffers are allocated for given size."""
        if self._mix_buffer is None or len(self._mix_buffer) < num_samples:
            self._osc1_buffer = np.zeros(num_samples, dtype=np.float32)
            self._osc2_buffer = np.zeros(num_samples, dtype=np.float32)
            self._mix_buffer = np.zeros(num_samples, dtype=np.float32)
            self._amp_env_buffer = np.zeros(num_samples, dtype=np.float32)
            self._filter_env_buffer = np.zeros(num_samples, dtype=np.float32)
            self._lfo_buffer = np.zeros(num_samples, dtype=np.float32)

    def note_on(self, note: int, velocity: int) -> None:
        """Start playing a note.

        Triggers the envelopes and sets oscillator frequencies.

        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (0-127)
        """
        self._note = note
        self._velocity = velocity
        self._velocity_scale = velocity / 127.0

        # Set oscillator frequencies
        freq = midi_to_frequency(note)
        self._osc1.frequency = freq

        # OSC2 with detune (cents to frequency ratio)
        detune_ratio = 2.0 ** (self._params.osc2_detune / 1200.0)
        self._osc2.frequency = freq * detune_ratio

        # Reset oscillator phases for consistent attack
        self._osc1.reset_phase()
        self._osc2.reset_phase()

        # Reset filter state
        self._filter.reset()

        # Trigger envelopes
        self._amp_envelope.gate_on()
        self._filter_envelope.gate_on()

        # Optionally reset LFO phase
        self._lfo.reset_phase()

        # Start fade-in ramp (anti-click)
        self._fade_in_counter = 0
        self._is_stealing = False

    def note_off(self) -> None:
        """Release the current note.

        Triggers the release phase of envelopes.
        The voice remains active until envelopes complete.
        """
        if self._note >= 0:
            self._amp_envelope.gate_off()
            self._filter_envelope.gate_off()

    def is_active(self) -> bool:
        """Check if voice is currently producing sound.

        Returns:
            True if voice has an active note or envelope is releasing
        """
        return self._amp_envelope.is_active()

    def is_releasing(self) -> bool:
        """Check if voice is in release phase.

        Returns:
            True if envelope is in release stage
        """
        return self._amp_envelope.is_releasing()

    def reset(self) -> None:
        """Force reset voice to idle state.

        Use for panic/all-notes-off situations.
        """
        self._note = -1
        self._velocity = 0
        self._velocity_scale = 0.0
        self._amp_envelope.reset()
        self._filter_envelope.reset()
        self._filter.reset()
        self._osc1.reset_phase()
        self._osc2.reset_phase()
        self._lfo.reset_phase()
        # Reset anti-click state
        self._fade_in_counter = self._fade_samples  # Skip fade-in
        self._fade_out_counter = 0
        self._is_stealing = False

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate audio samples.

        Implements the voice signal chain:
        OSC1 + OSC2 -> Filter (with env mod) -> VCA (amp env) -> Output

        Args:
            num_samples: Number of samples to generate

        Returns:
            NumPy array of float32 audio samples
        """
        # Ensure buffers
        self._ensure_buffers(num_samples)

        # Early exit if not active
        if not self.is_active():
            return np.zeros(num_samples, dtype=np.float32)

        p = self._params

        # Generate LFO modulation
        lfo_out = self._lfo.generate(num_samples)

        # Apply LFO to pitch if enabled
        if p.lfo_to_pitch > 0:
            # Modulate pitch in semitones
            pitch_mod = lfo_out * p.lfo_to_pitch * 2.0  # Up to 2 semitones
            self._osc1.pitch_mod = pitch_mod[0]  # Use first sample for now
            self._osc2.pitch_mod = pitch_mod[0]
        else:
            self._osc1.pitch_mod = 0.0
            self._osc2.pitch_mod = 0.0

        # Apply LFO to pulse width if enabled
        if p.lfo_to_pw > 0:
            pw_mod = lfo_out * p.lfo_to_pw * 0.4  # Up to 0.4 modulation
            self._osc1.pw_mod = pw_mod[0]
            self._osc2.pw_mod = pw_mod[0]
        else:
            self._osc1.pw_mod = 0.0
            self._osc2.pw_mod = 0.0

        # Generate oscillators
        osc1_out = self._osc1.generate(num_samples)
        osc2_out = self._osc2.generate(num_samples)

        # Mix oscillators
        mix = self._mix_buffer[:num_samples]
        mix[:] = osc1_out + osc2_out

        # Normalize mix (prevent clipping from sum)
        total_level = p.osc1_level + p.osc2_level
        if total_level > 0:
            mix *= 0.5 / max(0.5, total_level * 0.5)

        # Generate filter envelope
        filter_env = self._filter_envelope.generate(num_samples)

        # Apply filter envelope to cutoff
        base_cutoff = p.filter_cutoff
        env_mod = filter_env * p.filter_env_amount * 4.0  # Up to 4 octaves

        # Apply LFO to filter if enabled
        if p.lfo_to_filter > 0:
            lfo_filter_mod = lfo_out * p.lfo_to_filter
            # Combine LFO and envelope modulation
            self._filter.cutoff_mod = env_mod[0] + lfo_filter_mod[0]
        else:
            self._filter.cutoff_mod = env_mod[0]

        # Process through filter
        filtered = self._filter.process(mix)

        # Generate amplitude envelope
        amp_env = self._amp_envelope.generate(num_samples)

        # Apply amplitude envelope (VCA)
        output = filtered * amp_env

        # Apply velocity scaling
        output *= self._velocity_scale

        # Apply anti-click fade-in ramp
        if self._fade_in_counter < self._fade_samples:
            for i in range(num_samples):
                if self._fade_in_counter < self._fade_samples:
                    fade_factor = self._fade_in_counter / self._fade_samples
                    output[i] *= fade_factor
                    self._fade_in_counter += 1

        # Apply anti-click fade-out ramp (for voice stealing)
        if self._is_stealing and self._fade_out_counter > 0:
            for i in range(num_samples):
                if self._fade_out_counter > 0:
                    fade_factor = self._fade_out_counter / self._fade_samples
                    output[i] *= fade_factor
                    self._fade_out_counter -= 1
            # Complete steal when fade-out finishes
            if self._fade_out_counter <= 0:
                self._complete_steal()

        # Check if envelope completed (voice can be recycled)
        if not self._amp_envelope.is_active():
            self._note = -1

        return output.astype(np.float32)

    def steal(self) -> None:
        """Prepare voice to be stolen for a new note.

        Called when the polyphonic manager needs to reuse this voice.
        Triggers a fast fade-out to avoid clicks.
        """
        # Start fade-out ramp (anti-click)
        self._fade_out_counter = self._fade_samples
        self._is_stealing = True
        # Note: actual reset happens after fade-out completes in generate()

    def _complete_steal(self) -> None:
        """Complete the steal after fade-out finishes."""
        self._note = -1
        self._velocity = 0
        self._velocity_scale = 0.0
        self._amp_envelope.reset()
        self._filter_envelope.reset()
        self._is_stealing = False
        # Don't reset filter state to avoid clicks

    def get_age(self) -> float:
        """Get how long the current note has been playing.

        Used by voice stealing algorithm to prioritize older notes.

        Returns:
            Age indicator (envelope value inverted - lower = older/quieter)
        """
        # Use envelope value as age proxy
        # Released notes have lower values, so they're better steal candidates
        return self._amp_envelope.value if self.is_active() else 0.0

    def __repr__(self) -> str:
        """String representation of voice state."""
        status = "active" if self.is_active() else "idle"
        note_name = f"note={self._note}" if self._note >= 0 else "no note"
        return f"SynthVoice({self.voice_id}, {status}, {note_name})"
