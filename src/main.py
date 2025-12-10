#!/usr/bin/env python
# Application Entry Point
"""
main - Entry point for the KarokeLite Mini Synthesizer application.

Initializes and runs the synthesizer with GUI.

Usage:
    python -m main
    or
    python main.py
"""

import sys
import os
import argparse
from typing import Optional

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_controller import AppController
from gui import MainWindow


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='KarokeLite Mini Synthesizer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                    # Run with defaults
    python main.py --buffer 256       # Lower latency
    python main.py --voices 4         # Limit polyphony
        """
    )

    parser.add_argument(
        '--sample-rate', '-s',
        type=int,
        default=44100,
        help='Audio sample rate in Hz (default: 44100)'
    )

    parser.add_argument(
        '--buffer', '-b',
        type=int,
        default=512,
        help='Audio buffer size in samples (default: 512)'
    )

    parser.add_argument(
        '--voices', '-v',
        type=int,
        default=8,
        help='Maximum polyphony (default: 8)'
    )

    # Calculate default presets path relative to project root (parent of src/)
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(src_dir)
    default_presets_dir = os.path.join(project_root, 'presets')

    parser.add_argument(
        '--presets-dir', '-p',
        type=str,
        default=default_presets_dir,
        help=f'Directory for preset files (default: {default_presets_dir})'
    )

    parser.add_argument(
        '--no-audio',
        action='store_true',
        help='Run without audio (for testing GUI)'
    )

    return parser.parse_args()


class Application:
    """Main application class coordinating all components."""

    # Update intervals (milliseconds)
    VOICE_UPDATE_INTERVAL = 100      # Voice count update
    VISUALIZATION_UPDATE_INTERVAL = 33  # ~30 FPS for visualization
    RECORDING_UPDATE_INTERVAL = 100   # Recording time/level update
    SONG_PLAYER_UPDATE_INTERVAL = 100  # Song progress update

    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 512,
        max_voices: int = 8,
        presets_dir: str = './presets',
        no_audio: bool = False
    ):
        """
        Initialize application.

        Args:
            sample_rate: Audio sample rate in Hz
            buffer_size: Audio buffer size in samples
            max_voices: Maximum polyphony
            presets_dir: Directory for preset files
            no_audio: If True, don't start audio engine
        """
        self._no_audio = no_audio
        self._sample_rate = sample_rate

        # Track filter values for visualization
        self._current_filter_cutoff = 2000.0
        self._current_filter_resonance = 0.3

        # Create controller
        self._controller = AppController(
            sample_rate=sample_rate,
            buffer_size=buffer_size,
            max_voices=max_voices,
            presets_dir=presets_dir
        )

        # Create main window with callbacks
        self._window = MainWindow(
            on_note_on=self._on_note_on,
            on_note_off=self._on_note_off,
            on_parameter_change=self._on_parameter_change,
            on_preset_load=self._on_preset_load,
            on_preset_save=self._on_preset_save,
            on_quit=self._on_quit,
            # BOLT-007: Metronome callbacks
            on_metronome_start=self._on_metronome_start,
            on_metronome_stop=self._on_metronome_stop,
            on_metronome_bpm_change=self._on_metronome_bpm_change,
            on_metronome_time_sig_change=self._on_metronome_time_sig_change,
            on_metronome_volume_change=self._on_metronome_volume_change,
            # BOLT-007: Recording callbacks
            on_record_start=self._on_record_start,
            on_record_stop=self._on_record_stop,
            on_record_pause=self._on_record_pause,
            on_record_resume=self._on_record_resume,
            on_record_arm=self._on_record_arm,
            on_record_export=self._on_record_export,
            on_record_clear=self._on_record_clear,
            on_record_undo=self._on_record_undo,
            # BOLT-008: Reverb callbacks
            on_reverb_enable=self._on_reverb_enable,
            on_reverb_wet_dry=self._on_reverb_wet_dry,
            on_reverb_room_size=self._on_reverb_room_size,
            # BOLT-008: Song player callbacks
            on_song_play=self._on_song_play,
            on_song_stop=self._on_song_stop,
            on_song_pause=self._on_song_pause,
            on_song_select=self._on_song_select,
            # BOLT-009: Delay callbacks
            on_delay_enable=self._on_delay_enable,
            on_delay_time=self._on_delay_time,
            on_delay_feedback=self._on_delay_feedback,
            on_delay_wet_dry=self._on_delay_wet_dry,
            # BOLT-009: Chorus callbacks
            on_chorus_enable=self._on_chorus_enable,
            on_chorus_rate=self._on_chorus_rate,
            on_chorus_depth=self._on_chorus_depth,
            on_chorus_voices=self._on_chorus_voices,
            on_chorus_wet_dry=self._on_chorus_wet_dry,
            # BOLT-009: Distortion callbacks
            on_distortion_enable=self._on_distortion_enable,
            on_distortion_drive=self._on_distortion_drive,
            on_distortion_tone=self._on_distortion_tone,
            on_distortion_mode=self._on_distortion_mode,
            on_distortion_mix=self._on_distortion_mix,
            # BOLT-010: Flanger callbacks
            on_flanger_enable=self._on_flanger_enable,
            on_flanger_rate=self._on_flanger_rate,
            on_flanger_depth=self._on_flanger_depth,
            on_flanger_feedback=self._on_flanger_feedback,
            on_flanger_wet_dry=self._on_flanger_wet_dry,
            sample_rate=sample_rate
        )

        # Set up voice count callback
        self._controller.set_voice_change_callback(self._on_voice_change)

        # BOLT-007: Set up metronome beat callback
        self._controller.set_metronome_beat_callback(self._on_metronome_beat)

        # BOLT-008: Set up song player callbacks
        self._controller.set_song_callbacks(
            on_note_on=self._on_song_note_on,
            on_note_off=self._on_song_note_off,
            on_progress=self._on_song_progress,
            on_complete=self._on_song_complete
        )

        # BOLT-008: Initialize song list
        self._window.set_song_list(self._controller.get_song_list())

        # Schedule periodic updates
        self._schedule_updates()

    def _on_note_on(self, note: int, velocity: int):
        """Handle note on event from GUI."""
        self._controller.note_on(note, velocity)
        self._window.set_status(f"Note on: {note} vel={velocity}")

    def _on_note_off(self, note: int):
        """Handle note off event from GUI."""
        self._controller.note_off(note)

    def _on_parameter_change(self, name: str, value):
        """Handle parameter change from GUI."""
        self._controller.set_parameter(name, value)

        # BOLT-007: Track filter values for visualization
        if name == 'filter_cutoff':
            self._current_filter_cutoff = float(value)
            self._window.update_filter_display(
                self._current_filter_cutoff,
                self._current_filter_resonance
            )
        elif name == 'filter_resonance':
            self._current_filter_resonance = float(value)
            self._window.update_filter_display(
                self._current_filter_cutoff,
                self._current_filter_resonance
            )

    def _on_preset_load(self, name: str):
        """Handle preset load request."""
        params = self._controller.load_preset(name)
        if params:
            # Update GUI controls to reflect preset values
            self._window.set_all_parameters(params)
            self._window.set_status(f"Loaded preset: {name}")
        else:
            self._window.set_status(f"Failed to load preset: {name}")

    def _on_preset_save(self):
        """Handle preset save request."""
        # For now, just save with current name
        name = self._controller.current_preset_name
        if self._controller.save_preset(name):
            self._window.set_status(f"Saved preset: {name}")
        else:
            self._window.set_status(f"Failed to save preset")

    def _on_voice_change(self, active_voices: int):
        """Handle voice count change."""
        self._window.update_voice_count(active_voices, self._controller.max_voices)

    def _on_quit(self):
        """Handle application quit."""
        self._controller.stop()

    def _schedule_updates(self):
        """Schedule periodic GUI updates."""
        # Voice count update loop
        def update_voices():
            count = self._controller.get_active_voice_count()
            self._window.update_voice_count(count, self._controller.max_voices)
            self._window.after(self.VOICE_UPDATE_INTERVAL, update_voices)

        # BOLT-007: Visualization update loop (~30 FPS)
        def update_visualization():
            if not self._no_audio:
                # Get display buffer and update waveform
                buffer = self._controller.get_display_buffer()
                self._window.update_waveform(buffer)
            self._window.after(self.VISUALIZATION_UPDATE_INTERVAL, update_visualization)

        # BOLT-007: Recording status update loop
        def update_recording():
            if self._controller.is_recording:
                # Update duration
                duration = self._controller.get_recording_duration()
                self._window.update_recording_duration(duration)
                # Update level
                peak = self._controller.get_recording_peak_level()
                self._window.update_recording_level(peak)
            # Update state
            self._window.update_recording_state(self._controller.recording_state)
            self._window.set_recording_has_data(self._controller.recording_has_data)
            self._window.set_recording_can_undo(self._controller.recording_can_undo)
            self._window.after(self.RECORDING_UPDATE_INTERVAL, update_recording)

        # Start all update loops
        self._window.after(self.VOICE_UPDATE_INTERVAL, update_voices)
        self._window.after(self.VISUALIZATION_UPDATE_INTERVAL, update_visualization)
        self._window.after(self.RECORDING_UPDATE_INTERVAL, update_recording)

        # Initialize filter display
        self._window.update_filter_display(
            self._current_filter_cutoff,
            self._current_filter_resonance
        )

    # BOLT-007: Metronome callback handlers

    def _on_metronome_start(self):
        """Handle metronome start."""
        self._controller.start_metronome()
        self._window.set_status("Metronome started")

    def _on_metronome_stop(self):
        """Handle metronome stop."""
        self._controller.stop_metronome()
        self._window.set_status("Metronome stopped")

    def _on_metronome_bpm_change(self, bpm: float):
        """Handle BPM change."""
        self._controller.set_metronome_bpm(bpm)

    def _on_metronome_time_sig_change(self, numerator: int, denominator: int):
        """Handle time signature change."""
        self._controller.set_metronome_time_signature(numerator, denominator)

    def _on_metronome_volume_change(self, volume: float):
        """Handle metronome volume change."""
        self._controller.set_metronome_volume(volume)

    def _on_metronome_beat(self, beat: int, is_downbeat: bool):
        """Handle metronome beat event (called from audio thread)."""
        # Schedule GUI update on main thread
        self._window.after(0, lambda: self._window.update_metronome_beat(beat, is_downbeat))

    # BOLT-007: Recording callback handlers

    def _on_record_start(self):
        """Handle record start."""
        self._controller.start_recording()
        self._window.set_status("Recording started")

    def _on_record_stop(self):
        """Handle record stop."""
        self._controller.stop_recording()
        duration = self._controller.get_recording_duration()
        self._window.set_status(f"Recording stopped ({duration:.1f}s)")

    def _on_record_pause(self):
        """Handle record pause."""
        self._controller.pause_recording()
        self._window.set_status("Recording paused")

    def _on_record_resume(self):
        """Handle record resume."""
        self._controller.resume_recording()
        self._window.set_status("Recording resumed")

    def _on_record_arm(self):
        """Handle record arm."""
        self._controller.arm_recording()
        self._window.set_status("Recording armed - waiting for input")

    def _on_record_export(self, filepath: str):
        """Handle export request."""
        self._window.set_status(f"Exporting to {filepath}...")
        if self._controller.export_wav(filepath):
            info = self._controller.get_export_info()
            self._window.set_status(
                f"Exported: {info.get('duration_formatted', '')} ({info.get('estimated_size_formatted', '')})"
            )
            self._window.set_recording_info(
                f"{info.get('duration_formatted', '')} - {info.get('estimated_size_formatted', '')}"
            )
        else:
            self._window.set_status("Export failed - no recording data")

    def _on_record_clear(self):
        """Handle clear recording."""
        self._controller.clear_recording()
        self._window.set_status("Recording cleared")

    def _on_record_undo(self):
        """Handle undo recording."""
        if self._controller.undo_recording():
            self._window.set_status("Recording restored")
        else:
            self._window.set_status("Nothing to undo")

    # BOLT-008: Reverb callback handlers

    def _on_reverb_enable(self, enabled: bool):
        """Handle reverb enable/disable."""
        self._controller.set_reverb_enabled(enabled)
        status = "enabled" if enabled else "disabled"
        self._window.set_status(f"Reverb {status}")

    def _on_reverb_wet_dry(self, mix: float):
        """Handle reverb wet/dry change."""
        self._controller.set_reverb_wet_dry(mix)

    def _on_reverb_room_size(self, size: float):
        """Handle reverb room size change."""
        self._controller.set_reverb_room_size(size)

    # BOLT-009: Delay callback handlers

    def _on_delay_enable(self, enabled: bool):
        """Handle delay enable/disable."""
        self._controller.set_delay_enabled(enabled)
        status = "enabled" if enabled else "disabled"
        self._window.set_status(f"Delay {status}")

    def _on_delay_time(self, time_ms: float):
        """Handle delay time change."""
        self._controller.set_delay_time(time_ms)

    def _on_delay_feedback(self, feedback: float):
        """Handle delay feedback change."""
        self._controller.set_delay_feedback(feedback)

    def _on_delay_wet_dry(self, mix: float):
        """Handle delay wet/dry change."""
        self._controller.set_delay_wet_dry(mix)

    # BOLT-009: Chorus callback handlers

    def _on_chorus_enable(self, enabled: bool):
        """Handle chorus enable/disable."""
        self._controller.set_chorus_enabled(enabled)
        status = "enabled" if enabled else "disabled"
        self._window.set_status(f"Chorus {status}")

    def _on_chorus_rate(self, rate: float):
        """Handle chorus rate change."""
        self._controller.set_chorus_rate(rate)

    def _on_chorus_depth(self, depth: float):
        """Handle chorus depth change."""
        self._controller.set_chorus_depth(depth)

    def _on_chorus_voices(self, voices: int):
        """Handle chorus voices change."""
        self._controller.set_chorus_voices(voices)

    def _on_chorus_wet_dry(self, mix: float):
        """Handle chorus wet/dry change."""
        self._controller.set_chorus_wet_dry(mix)

    # BOLT-009: Distortion callback handlers

    def _on_distortion_enable(self, enabled: bool):
        """Handle distortion enable/disable."""
        self._controller.set_distortion_enabled(enabled)
        status = "enabled" if enabled else "disabled"
        self._window.set_status(f"Distortion {status}")

    def _on_distortion_drive(self, drive: float):
        """Handle distortion drive change."""
        self._controller.set_distortion_drive(drive)

    def _on_distortion_tone(self, tone: float):
        """Handle distortion tone change."""
        self._controller.set_distortion_tone(tone)

    def _on_distortion_mode(self, mode: str):
        """Handle distortion mode change."""
        self._controller.set_distortion_mode(mode)
        self._window.set_status(f"Distortion mode: {mode}")

    def _on_distortion_mix(self, mix: float):
        """Handle distortion mix change."""
        self._controller.set_distortion_mix(mix)


    # BOLT-010: Flanger callback handlers

    def _on_flanger_enable(self, enabled: bool):
        """Handle flanger enable/disable."""
        self._controller.set_flanger_enabled(enabled)
        status = "enabled" if enabled else "disabled"
        self._window.set_status(f"Flanger {status}")

    def _on_flanger_rate(self, rate: float):
        """Handle flanger rate change."""
        self._controller.set_flanger_rate(rate)

    def _on_flanger_depth(self, depth: float):
        """Handle flanger depth change."""
        self._controller.set_flanger_depth(depth)

    def _on_flanger_feedback(self, feedback: float):
        """Handle flanger feedback change."""
        self._controller.set_flanger_feedback(feedback)

    def _on_flanger_wet_dry(self, mix: float):
        """Handle flanger mix change."""
        self._controller.set_flanger_wet_dry(mix)

    # BOLT-008: Song player callback handlers

    def _on_song_play(self):
        """Handle song play."""
        self._controller.play_song()
        self._window.set_status(f"Playing: {self._controller.current_song_name or 'Song'}")

    def _on_song_stop(self):
        """Handle song stop."""
        self._controller.stop_song()
        self._window.clear_external_notes()
        self._window.set_song_stopped()
        self._window.set_status("Song stopped")

    def _on_song_pause(self):
        """Handle song pause."""
        self._controller.pause_song()
        self._window.clear_external_notes()
        self._window.set_status("Song paused")

    def _on_song_select(self, song_name: str):
        """Handle song selection."""
        if self._controller.load_song(song_name):
            self._window.set_status(f"Loaded: {song_name}")
        else:
            self._window.set_status(f"Failed to load: {song_name}")

    def _on_song_note_on(self, note: int, velocity: int):
        """Handle song note on (for keyboard visualization)."""
        # Schedule GUI update on main thread
        self._window.after(0, lambda: self._window.external_note_on(note))

    def _on_song_note_off(self, note: int):
        """Handle song note off (for keyboard visualization)."""
        # Schedule GUI update on main thread
        self._window.after(0, lambda: self._window.external_note_off(note))

    def _on_song_progress(self, current: float, total: float):
        """Handle song progress update."""
        # Schedule GUI update on main thread
        self._window.after(0, lambda: self._window.update_song_progress(current, total))

    def _on_song_complete(self):
        """Handle song completion."""
        def on_complete():
            self._window.clear_external_notes()
            self._window.set_song_stopped()
            self._window.set_status("Song finished")
        self._window.after(0, on_complete)

    def run(self):
        """Run the application."""
        # Start audio engine
        if not self._no_audio:
            try:
                self._controller.start()
                self._window.set_status("Audio engine started")
            except Exception as e:
                self._window.set_status(f"Audio error: {e}")
                print(f"Warning: Could not start audio engine: {e}")
        else:
            self._window.set_status("Running without audio (--no-audio)")

        # Start GUI main loop
        try:
            self._window.mainloop()
        finally:
            # Ensure cleanup on exit
            self._controller.stop()


def main():
    """Application entry point."""
    args = parse_args()

    print("KarokeLite Mini Synthesizer")
    print(f"  Sample Rate: {args.sample_rate} Hz")
    print(f"  Buffer Size: {args.buffer} samples")
    print(f"  Max Voices: {args.voices}")
    print()

    app = Application(
        sample_rate=args.sample_rate,
        buffer_size=args.buffer,
        max_voices=args.voices,
        presets_dir=args.presets_dir,
        no_audio=args.no_audio
    )

    app.run()


if __name__ == '__main__':
    main()
