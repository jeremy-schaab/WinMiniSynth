# File Export Module
"""
file_export - Audio file export for the Mini Synthesizer.

Provides WAV file export with:
- Multiple bit depths (16-bit, 24-bit, 32-bit float)
- Normalization options
- Metadata support
- Progress callback

Usage:
    exporter = FileExporter()

    # Simple export
    exporter.export_wav(audio_data, 'output.wav')

    # Export with options
    config = ExportConfig(bit_depth=24, normalize=True)
    exporter.export_wav(audio_data, 'output.wav', config)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable, Dict, Any
from pathlib import Path
import numpy as np
import wave
import struct
import datetime


class ExportFormat(Enum):
    """Supported export formats."""
    WAV = auto()
    # Future: MP3, FLAC, OGG


class BitDepth(Enum):
    """Audio bit depth options."""
    INT16 = 16    # CD quality
    INT24 = 24    # Professional
    FLOAT32 = 32  # Maximum precision


@dataclass
class ExportConfig:
    """Export configuration.

    Attributes:
        bit_depth: Output bit depth (16, 24, or 32)
        sample_rate: Output sample rate
        channels: Number of channels (1=mono, 2=stereo)
        normalize: Whether to normalize audio to 0dB
        normalize_headroom_db: Headroom below 0dB if normalizing
        dither: Apply dither when reducing bit depth
        metadata: Optional metadata dict
    """
    bit_depth: int = 16
    sample_rate: int = 44100
    channels: int = 1
    normalize: bool = False
    normalize_headroom_db: float = 0.5
    dither: bool = True
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration."""
        if self.bit_depth not in [16, 24, 32]:
            raise ValueError(f"Bit depth must be 16, 24, or 32: {self.bit_depth}")
        if self.channels not in [1, 2]:
            raise ValueError(f"Channels must be 1 or 2: {self.channels}")
        if self.sample_rate < 8000 or self.sample_rate > 192000:
            raise ValueError(f"Sample rate out of range: {self.sample_rate}")


class FileExporter:
    """Audio file exporter.

    Exports audio data to various file formats.
    Currently supports WAV files with multiple bit depths.
    """

    def __init__(self, default_config: Optional[ExportConfig] = None):
        """Initialize exporter.

        Args:
            default_config: Default export configuration
        """
        self._default_config = default_config or ExportConfig()

    def export_wav(
        self,
        audio: np.ndarray,
        filepath: str,
        config: Optional[ExportConfig] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> bool:
        """Export audio to WAV file.

        Args:
            audio: Audio data (mono float32, -1.0 to 1.0)
            filepath: Output file path
            config: Export configuration (uses default if None)
            progress_callback: Optional callback(progress: 0.0-1.0)

        Returns:
            True if export successful

        Raises:
            ValueError: If audio data is invalid
            IOError: If file cannot be written
        """
        config = config or self._default_config

        # Validate audio
        if len(audio) == 0:
            raise ValueError("Audio data is empty")

        # Ensure audio is float32
        audio = np.asarray(audio, dtype=np.float32)

        # Apply normalization if requested
        if config.normalize:
            audio = self._normalize(audio, config.normalize_headroom_db)

        if progress_callback:
            progress_callback(0.1)

        # Convert to target bit depth
        if config.bit_depth == 32:
            # 32-bit float WAV
            audio_bytes = self._convert_to_float32(audio)
            sample_width = 4
            fmt_tag = 3  # IEEE float
        elif config.bit_depth == 24:
            # 24-bit integer WAV
            audio_bytes = self._convert_to_int24(audio, config.dither)
            sample_width = 3
            fmt_tag = 1  # PCM
        else:
            # 16-bit integer WAV
            audio_bytes = self._convert_to_int16(audio, config.dither)
            sample_width = 2
            fmt_tag = 1  # PCM

        if progress_callback:
            progress_callback(0.5)

        # Handle stereo conversion
        if config.channels == 2:
            # Duplicate mono to stereo
            audio_bytes = self._mono_to_stereo(audio_bytes, sample_width)

        if progress_callback:
            progress_callback(0.7)

        # Write WAV file
        self._write_wav_file(
            filepath,
            audio_bytes,
            config.sample_rate,
            config.channels,
            sample_width,
            fmt_tag
        )

        if progress_callback:
            progress_callback(1.0)

        return True

    def _normalize(self, audio: np.ndarray, headroom_db: float) -> np.ndarray:
        """Normalize audio to 0dB minus headroom.

        Args:
            audio: Audio data
            headroom_db: Headroom below 0dB

        Returns:
            Normalized audio
        """
        peak = np.abs(audio).max()
        if peak > 0:
            # Calculate target level
            target = 10 ** (-headroom_db / 20)
            return audio * (target / peak)
        return audio

    def _convert_to_int16(self, audio: np.ndarray, dither: bool) -> bytes:
        """Convert float audio to 16-bit integer bytes.

        Args:
            audio: Float audio (-1.0 to 1.0)
            dither: Apply dither

        Returns:
            Byte array of 16-bit samples
        """
        # Clip to valid range
        audio = np.clip(audio, -1.0, 1.0)

        # Apply triangular dither
        if dither:
            dither_noise = (np.random.random(len(audio)) +
                           np.random.random(len(audio)) - 1.0)
            audio = audio + dither_noise / 32768.0

        # Scale to 16-bit range
        scaled = audio * 32767.0
        scaled = np.clip(scaled, -32768, 32767)
        int_data = scaled.astype(np.int16)

        return int_data.tobytes()

    def _convert_to_int24(self, audio: np.ndarray, dither: bool) -> bytes:
        """Convert float audio to 24-bit integer bytes.

        Args:
            audio: Float audio (-1.0 to 1.0)
            dither: Apply dither

        Returns:
            Byte array of 24-bit samples (3 bytes per sample)
        """
        # Clip to valid range
        audio = np.clip(audio, -1.0, 1.0)

        # Apply triangular dither
        if dither:
            dither_noise = (np.random.random(len(audio)) +
                           np.random.random(len(audio)) - 1.0)
            audio = audio + dither_noise / 8388608.0

        # Scale to 24-bit range
        scaled = audio * 8388607.0
        scaled = np.clip(scaled, -8388608, 8388607)
        int_data = scaled.astype(np.int32)

        # Pack as 24-bit (3 bytes per sample, little-endian)
        result = bytearray()
        for sample in int_data:
            # Extract 3 bytes from 32-bit integer
            result.extend(struct.pack('<i', sample)[:3])

        return bytes(result)

    def _convert_to_float32(self, audio: np.ndarray) -> bytes:
        """Convert float audio to 32-bit float bytes.

        Args:
            audio: Float audio

        Returns:
            Byte array of 32-bit float samples
        """
        # Clip to valid range
        audio = np.clip(audio, -1.0, 1.0)
        return audio.astype(np.float32).tobytes()

    def _mono_to_stereo(self, audio_bytes: bytes, sample_width: int) -> bytes:
        """Convert mono audio bytes to stereo.

        Args:
            audio_bytes: Mono audio bytes
            sample_width: Bytes per sample

        Returns:
            Stereo audio bytes
        """
        result = bytearray()
        for i in range(0, len(audio_bytes), sample_width):
            sample = audio_bytes[i:i + sample_width]
            result.extend(sample)  # Left
            result.extend(sample)  # Right
        return bytes(result)

    def _write_wav_file(
        self,
        filepath: str,
        audio_bytes: bytes,
        sample_rate: int,
        channels: int,
        sample_width: int,
        fmt_tag: int
    ):
        """Write WAV file with audio data.

        Args:
            filepath: Output file path
            audio_bytes: Audio data as bytes
            sample_rate: Sample rate in Hz
            channels: Number of channels
            sample_width: Bytes per sample
            fmt_tag: Format tag (1=PCM, 3=IEEE float)
        """
        # Ensure directory exists
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate header values
        byte_rate = sample_rate * channels * sample_width
        block_align = channels * sample_width
        data_size = len(audio_bytes)
        file_size = 36 + data_size

        with open(filepath, 'wb') as f:
            # RIFF header
            f.write(b'RIFF')
            f.write(struct.pack('<I', file_size))
            f.write(b'WAVE')

            # fmt chunk
            f.write(b'fmt ')
            if fmt_tag == 3:  # IEEE float needs extended format
                f.write(struct.pack('<I', 18))  # chunk size
            else:
                f.write(struct.pack('<I', 16))  # chunk size

            f.write(struct.pack('<H', fmt_tag))          # format tag
            f.write(struct.pack('<H', channels))         # channels
            f.write(struct.pack('<I', sample_rate))      # sample rate
            f.write(struct.pack('<I', byte_rate))        # byte rate
            f.write(struct.pack('<H', block_align))      # block align
            f.write(struct.pack('<H', sample_width * 8)) # bits per sample

            if fmt_tag == 3:
                f.write(struct.pack('<H', 0))  # extension size

            # data chunk
            f.write(b'data')
            f.write(struct.pack('<I', data_size))
            f.write(audio_bytes)

    def get_export_info(
        self,
        audio: np.ndarray,
        config: Optional[ExportConfig] = None
    ) -> Dict[str, Any]:
        """Get information about a potential export.

        Args:
            audio: Audio data
            config: Export configuration

        Returns:
            Dict with duration, file size estimate, etc.
        """
        config = config or self._default_config

        duration_seconds = len(audio) / config.sample_rate
        bytes_per_sample = config.bit_depth // 8
        estimated_size = len(audio) * bytes_per_sample * config.channels + 44  # header

        return {
            'duration_seconds': duration_seconds,
            'duration_formatted': self._format_duration(duration_seconds),
            'sample_count': len(audio),
            'sample_rate': config.sample_rate,
            'bit_depth': config.bit_depth,
            'channels': config.channels,
            'estimated_size_bytes': estimated_size,
            'estimated_size_formatted': self._format_size(estimated_size),
        }

    def _format_duration(self, seconds: float) -> str:
        """Format duration as MM:SS.ms."""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:05.2f}"

    def _format_size(self, bytes_: int) -> str:
        """Format file size."""
        if bytes_ < 1024:
            return f"{bytes_} B"
        elif bytes_ < 1024 * 1024:
            return f"{bytes_ / 1024:.1f} KB"
        else:
            return f"{bytes_ / (1024 * 1024):.1f} MB"

    def __repr__(self) -> str:
        return f"FileExporter(bit_depth={self._default_config.bit_depth})"
