# MiniSynth module - Polyphonic Synthesizer Manager
"""
synth.py - Main polyphonic synthesizer aggregate

Implements the MiniSynth aggregate root from the domain model.
Manages voice allocation, note tracking, and coordinates audio generation
across multiple voices for polyphonic playback.

Features:
- 8-voice polyphony (configurable)
- Voice stealing algorithm (oldest releasing voice first)
- Global parameter control
- Master volume control
- Note-to-voice mapping

Usage:
    synth = MiniSynth(sample_rate=44100, max_voices=8)
    synth.note_on(60, 100)   # Play middle C
    synth.note_on(64, 100)   # Play E (chord)
    samples = synth.generate(512)
    synth.note_off(60)       # Release middle C
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from enum import IntEnum
import numpy as np

from .voice import SynthVoice, VoiceParameters
from .oscillator import Waveform


class VoiceStealingStrategy(IntEnum):
    """Voice stealing strategy enumeration."""
    OLDEST = 0       # Steal the oldest note
    QUIETEST = 1     # Steal the quietest voice (lowest envelope)
    LOWEST = 2       # Steal the lowest pitch note
    HIGHEST = 3      # Steal the highest pitch note


@dataclass
class SynthState:
    """Snapshot of synthesizer state for debugging/visualization.

    Attributes:
        active_voices: Number of currently active voices
        notes_playing: List of MIDI notes currently playing
        master_volume: Current master volume level
        cpu_load_estimate: Estimated CPU load percentage
    """
    active_voices: int
    notes_playing: List[int]
    master_volume: float
    cpu_load_estimate: float


class MiniSynth:
    """Polyphonic synthesizer with voice management.

    The MiniSynth is the aggregate root for the synthesis domain.
    It manages voice allocation, tracks active notes, and coordinates
    audio generation across all voices.

    Attributes:
        sample_rate: Audio sample rate in Hz
        max_voices: Maximum number of simultaneous voices
        master_volume: Master output volume (0.0 to 1.0)
    """

    def __init__(self, sample_rate: int = 44100, max_voices: int = 8):
        """Initialize synthesizer with voice pool.

        Args:
            sample_rate: Audio sample rate in Hz (default: 44100)
            max_voices: Maximum voices for polyphony (default: 8)
        """
        if max_voices < 1 or max_voices > 32:
            raise ValueError(f"max_voices must be 1-32, got {max_voices}")

        self.sample_rate = sample_rate
        self.max_voices = max_voices

        # Create voice pool
        self._voices: List[SynthVoice] = [
            SynthVoice(sample_rate, voice_id=i)
            for i in range(max_voices)
        ]

        # Note tracking: MIDI note -> voice index
        self._note_voice_map: Dict[int, int] = {}

        # Global parameters
        self._master_volume: float = 0.8
        self._voice_params = VoiceParameters()
        self._steal_strategy = VoiceStealingStrategy.QUIETEST

        # Pre-allocated mix buffer
        self._mix_buffer: Optional[np.ndarray] = None

        # Smooth normalization to prevent pops when voice count changes
        self._smooth_norm_factor: float = 1.0
        self._norm_smoothing: float = 0.99  # Smoothing coefficient

        # Optional callback for voice activity changes
        self._on_voice_change: Optional[Callable[[int], None]] = None

    @property
    def master_volume(self) -> float:
        """Master output volume (0.0 to 1.0)."""
        return self._master_volume

    @master_volume.setter
    def master_volume(self, value: float) -> None:
        """Set master volume, clamped to valid range."""
        self._master_volume = max(0.0, min(1.0, value))

    @property
    def voice_parameters(self) -> VoiceParameters:
        """Global voice parameter settings."""
        return self._voice_params

    @voice_parameters.setter
    def voice_parameters(self, params: VoiceParameters) -> None:
        """Set global voice parameters and apply to all voices."""
        self._voice_params = params
        for voice in self._voices:
            voice.parameters = params

    @property
    def steal_strategy(self) -> VoiceStealingStrategy:
        """Current voice stealing strategy."""
        return self._steal_strategy

    @steal_strategy.setter
    def steal_strategy(self, strategy: VoiceStealingStrategy) -> None:
        """Set voice stealing strategy."""
        self._steal_strategy = strategy

    def set_on_voice_change(self, callback: Optional[Callable[[int], None]]) -> None:
        """Set callback for voice count changes.

        Args:
            callback: Function taking active voice count as argument
        """
        self._on_voice_change = callback

    def _notify_voice_change(self) -> None:
        """Notify listener of voice count change."""
        if self._on_voice_change:
            self._on_voice_change(self.get_active_voice_count())

    def _find_free_voice(self) -> Optional[int]:
        """Find an inactive voice.

        Returns:
            Voice index or None if all voices are active
        """
        for i, voice in enumerate(self._voices):
            if not voice.is_active():
                return i
        return None

    def _find_steal_candidate(self) -> int:
        """Find the best voice to steal using current strategy.

        Returns:
            Index of voice to steal
        """
        if self._steal_strategy == VoiceStealingStrategy.QUIETEST:
            # Prefer releasing voices, then quietest
            best_idx = 0
            best_score = float('inf')
            for i, voice in enumerate(self._voices):
                if voice.is_releasing():
                    # Releasing voices get priority (lower score)
                    score = voice.get_age() - 10.0
                else:
                    score = voice.get_age()
                if score < best_score:
                    best_score = score
                    best_idx = i
            return best_idx

        elif self._steal_strategy == VoiceStealingStrategy.OLDEST:
            # Find voice with oldest/longest playing note
            # Lower envelope value often indicates older note
            best_idx = 0
            best_score = float('inf')
            for i, voice in enumerate(self._voices):
                score = voice.get_age()
                if voice.is_releasing():
                    score -= 10.0  # Prefer releasing
                if score < best_score:
                    best_score = score
                    best_idx = i
            return best_idx

        elif self._steal_strategy == VoiceStealingStrategy.LOWEST:
            # Steal lowest pitch
            best_idx = 0
            lowest_note = 128
            for i, voice in enumerate(self._voices):
                if voice.note >= 0 and voice.note < lowest_note:
                    lowest_note = voice.note
                    best_idx = i
            return best_idx

        elif self._steal_strategy == VoiceStealingStrategy.HIGHEST:
            # Steal highest pitch
            best_idx = 0
            highest_note = -1
            for i, voice in enumerate(self._voices):
                if voice.note > highest_note:
                    highest_note = voice.note
                    best_idx = i
            return best_idx

        return 0  # Default to first voice

    def _allocate_voice(self) -> int:
        """Allocate a voice for a new note.

        Returns:
            Index of allocated voice
        """
        # Try to find a free voice
        free_idx = self._find_free_voice()
        if free_idx is not None:
            return free_idx

        # No free voice - must steal one
        steal_idx = self._find_steal_candidate()
        stolen_voice = self._voices[steal_idx]

        # Remove stolen voice's note from mapping
        if stolen_voice.note >= 0:
            self._note_voice_map.pop(stolen_voice.note, None)

        # Prepare voice for reuse
        stolen_voice.steal()

        return steal_idx

    def note_on(self, note: int, velocity: int) -> None:
        """Start playing a note.

        Allocates a voice and triggers the note. If the note is
        already playing, retrigers it.

        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (0-127)
        """
        if note < 0 or note > 127:
            return
        if velocity < 0:
            velocity = 0
        if velocity > 127:
            velocity = 127

        # Velocity 0 is often treated as note off
        if velocity == 0:
            self.note_off(note)
            return

        # Check if note is already playing - ignore duplicate note_on
        # This prevents OS key repeat from restarting the envelope
        if note in self._note_voice_map:
            return  # Note already playing, ignore

        # Allocate a voice
        voice_idx = self._allocate_voice()
        voice = self._voices[voice_idx]

        # Apply current parameters to voice
        voice.parameters = self._voice_params

        # Start the note
        voice.note_on(note, velocity)

        # Track note -> voice mapping
        self._note_voice_map[note] = voice_idx

        self._notify_voice_change()

    def note_off(self, note: int) -> None:
        """Release a note.

        Triggers the release phase of the voice playing this note.

        Args:
            note: MIDI note number (0-127)
        """
        if note not in self._note_voice_map:
            return

        voice_idx = self._note_voice_map.pop(note)
        self._voices[voice_idx].note_off()

        self._notify_voice_change()

    def all_notes_off(self) -> None:
        """Release all currently playing notes.

        Equivalent to MIDI "All Notes Off" message.
        """
        for note in list(self._note_voice_map.keys()):
            self.note_off(note)

    def panic(self) -> None:
        """Immediately silence all voices.

        Force resets all voices without release phase.
        Use for MIDI panic or emergency stop.
        """
        self._note_voice_map.clear()
        for voice in self._voices:
            voice.reset()
        self._notify_voice_change()

    def get_active_voice_count(self) -> int:
        """Get number of currently active voices.

        Returns:
            Count of voices producing sound
        """
        return sum(1 for voice in self._voices if voice.is_active())

    def get_playing_notes(self) -> List[int]:
        """Get list of currently playing MIDI notes.

        Returns:
            List of MIDI note numbers
        """
        return list(self._note_voice_map.keys())

    def get_state(self) -> SynthState:
        """Get current synthesizer state snapshot.

        Returns:
            SynthState with current status information
        """
        active = self.get_active_voice_count()
        # Rough CPU estimate: ~5% per active voice
        cpu_estimate = active * 5.0
        return SynthState(
            active_voices=active,
            notes_playing=self.get_playing_notes(),
            master_volume=self._master_volume,
            cpu_load_estimate=min(100.0, cpu_estimate)
        )

    def _ensure_mix_buffer(self, num_samples: int) -> None:
        """Ensure mix buffer is allocated."""
        if self._mix_buffer is None or len(self._mix_buffer) < num_samples:
            self._mix_buffer = np.zeros(num_samples, dtype=np.float32)

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate mixed audio from all active voices.

        Sums output from all active voices and applies master volume.

        Args:
            num_samples: Number of samples to generate

        Returns:
            NumPy array of float32 audio samples
        """
        self._ensure_mix_buffer(num_samples)
        mix = self._mix_buffer[:num_samples]
        mix.fill(0.0)

        active_count = 0

        # Generate and sum all active voices
        for voice in self._voices:
            if voice.is_active():
                voice_output = voice.generate(num_samples)
                mix += voice_output
                active_count += 1

        # Smooth normalization to prevent pops when voice count changes
        target_norm = 1.0 / np.sqrt(max(active_count, 1))
        # Exponential smoothing toward target
        self._smooth_norm_factor = (
            self._norm_smoothing * self._smooth_norm_factor +
            (1.0 - self._norm_smoothing) * target_norm
        )
        mix *= self._smooth_norm_factor

        # Apply master volume
        mix *= self._master_volume

        # Soft clip to prevent harsh digital clipping
        # Using tanh for smooth limiting
        if np.max(np.abs(mix)) > 0.95:
            mix = np.tanh(mix)

        return mix.astype(np.float32)

    def get_audio_callback(self) -> Callable[[int], np.ndarray]:
        """Get audio callback function for AudioEngine.

        Returns:
            Callback function suitable for AudioEngine.set_callback()
        """
        return self.generate

    # Parameter convenience methods

    def set_oscillator1(self, waveform: Waveform, level: float = 0.7) -> None:
        """Set oscillator 1 parameters.

        Args:
            waveform: Waveform type
            level: Output level (0.0 to 1.0)
        """
        self._voice_params.osc1_waveform = waveform
        self._voice_params.osc1_level = max(0.0, min(1.0, level))
        self._update_voice_params()

    def set_oscillator2(self, waveform: Waveform, level: float = 0.5,
                         detune: float = 5.0) -> None:
        """Set oscillator 2 parameters.

        Args:
            waveform: Waveform type
            level: Output level (0.0 to 1.0)
            detune: Detune in cents (-100 to 100)
        """
        self._voice_params.osc2_waveform = waveform
        self._voice_params.osc2_level = max(0.0, min(1.0, level))
        self._voice_params.osc2_detune = max(-100.0, min(100.0, detune))
        self._update_voice_params()

    def set_filter(self, cutoff: float, resonance: float,
                   env_amount: float = 0.5) -> None:
        """Set filter parameters.

        Args:
            cutoff: Cutoff frequency in Hz
            resonance: Resonance (0.0 to 1.0)
            env_amount: Envelope modulation amount (-1.0 to 1.0)
        """
        self._voice_params.filter_cutoff = max(20.0, min(20000.0, cutoff))
        self._voice_params.filter_resonance = max(0.0, min(1.0, resonance))
        self._voice_params.filter_env_amount = max(-1.0, min(1.0, env_amount))
        self._update_voice_params()

    def set_amp_envelope(self, attack: float, decay: float,
                          sustain: float, release: float) -> None:
        """Set amplitude envelope parameters.

        Args:
            attack: Attack time in seconds
            decay: Decay time in seconds
            sustain: Sustain level (0.0 to 1.0)
            release: Release time in seconds
        """
        self._voice_params.amp_attack = max(0.001, min(10.0, attack))
        self._voice_params.amp_decay = max(0.001, min(10.0, decay))
        self._voice_params.amp_sustain = max(0.0, min(1.0, sustain))
        self._voice_params.amp_release = max(0.001, min(10.0, release))
        self._update_voice_params()

    def set_filter_envelope(self, attack: float, decay: float,
                             sustain: float, release: float) -> None:
        """Set filter envelope parameters.

        Args:
            attack: Attack time in seconds
            decay: Decay time in seconds
            sustain: Sustain level (0.0 to 1.0)
            release: Release time in seconds
        """
        self._voice_params.filter_attack = max(0.001, min(10.0, attack))
        self._voice_params.filter_decay = max(0.001, min(10.0, decay))
        self._voice_params.filter_sustain = max(0.0, min(1.0, sustain))
        self._voice_params.filter_release = max(0.001, min(10.0, release))
        self._update_voice_params()

    def set_lfo(self, rate: float, depth: float, waveform: Waveform = Waveform.SINE,
                to_pitch: float = 0.0, to_filter: float = 0.0,
                to_pw: float = 0.0) -> None:
        """Set LFO parameters.

        Args:
            rate: LFO frequency in Hz
            depth: LFO depth (0.0 to 1.0)
            waveform: LFO waveform type
            to_pitch: Pitch modulation amount (0.0 to 1.0)
            to_filter: Filter modulation amount (0.0 to 1.0)
            to_pw: Pulse width modulation amount (0.0 to 1.0)
        """
        self._voice_params.lfo_rate = max(0.1, min(50.0, rate))
        self._voice_params.lfo_depth = max(0.0, min(1.0, depth))
        self._voice_params.lfo_waveform = waveform
        self._voice_params.lfo_to_pitch = max(0.0, min(1.0, to_pitch))
        self._voice_params.lfo_to_filter = max(0.0, min(1.0, to_filter))
        self._voice_params.lfo_to_pw = max(0.0, min(1.0, to_pw))
        self._update_voice_params()

    def _update_voice_params(self) -> None:
        """Apply current parameters to all voices."""
        for voice in self._voices:
            voice.parameters = self._voice_params

    def __repr__(self) -> str:
        """String representation of synth state."""
        active = self.get_active_voice_count()
        return (f"MiniSynth(voices={active}/{self.max_voices}, "
                f"volume={self._master_volume:.2f})")
