# Tests for File Export Module
"""
test_file_export - Unit tests for WAV file export.
"""

import pytest
import numpy as np
import sys
import os
import tempfile
import wave
import struct
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from recording.file_export import FileExporter, ExportFormat, ExportConfig, BitDepth


class TestExportFormat:
    """Tests for ExportFormat enum."""

    def test_wav_format(self):
        """Should have WAV format."""
        assert ExportFormat.WAV


class TestBitDepth:
    """Tests for BitDepth enum."""

    def test_bit_depths(self):
        """Should have 16, 24, 32 bit depths."""
        assert BitDepth.INT16.value == 16
        assert BitDepth.INT24.value == 24
        assert BitDepth.FLOAT32.value == 32


class TestExportConfig:
    """Tests for ExportConfig dataclass."""

    def test_default_config(self):
        """Should have sensible defaults."""
        config = ExportConfig()
        assert config.bit_depth == 16
        assert config.sample_rate == 44100
        assert config.channels == 1
        assert config.normalize is False
        assert config.dither is True

    def test_custom_config(self):
        """Should accept custom values."""
        config = ExportConfig(
            bit_depth=24,
            sample_rate=48000,
            channels=2,
            normalize=True
        )
        assert config.bit_depth == 24
        assert config.sample_rate == 48000
        assert config.channels == 2
        assert config.normalize is True

    def test_invalid_bit_depth(self):
        """Should reject invalid bit depth."""
        with pytest.raises(ValueError):
            ExportConfig(bit_depth=8)

    def test_invalid_channels(self):
        """Should reject invalid channel count."""
        with pytest.raises(ValueError):
            ExportConfig(channels=3)

    def test_invalid_sample_rate_low(self):
        """Should reject too low sample rate."""
        with pytest.raises(ValueError):
            ExportConfig(sample_rate=1000)

    def test_invalid_sample_rate_high(self):
        """Should reject too high sample rate."""
        with pytest.raises(ValueError):
            ExportConfig(sample_rate=500000)


class TestFileExporterInit:
    """Tests for FileExporter initialization."""

    def test_default_init(self):
        """Should initialize with default config."""
        exporter = FileExporter()
        assert exporter._default_config is not None

    def test_custom_config(self):
        """Should accept custom default config."""
        config = ExportConfig(bit_depth=24)
        exporter = FileExporter(default_config=config)
        assert exporter._default_config.bit_depth == 24


class TestFileExporterWAV16:
    """Tests for 16-bit WAV export."""

    def test_export_16bit_mono(self):
        """Should export 16-bit mono WAV."""
        exporter = FileExporter()
        audio = np.array([0.0, 0.5, -0.5, 0.25], dtype=np.float32)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            filepath = f.name

        try:
            config = ExportConfig(bit_depth=16, channels=1)
            result = exporter.export_wav(audio, filepath, config)

            assert result is True
            assert Path(filepath).exists()

            # Verify WAV file
            with wave.open(filepath, 'rb') as wav:
                assert wav.getnchannels() == 1
                assert wav.getsampwidth() == 2  # 16-bit = 2 bytes
                assert wav.getframerate() == 44100
                assert wav.getnframes() == 4
        finally:
            if Path(filepath).exists():
                Path(filepath).unlink()

    def test_export_16bit_stereo(self):
        """Should export 16-bit stereo WAV."""
        exporter = FileExporter()
        audio = np.array([0.0, 0.5, -0.5, 0.25], dtype=np.float32)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            filepath = f.name

        try:
            config = ExportConfig(bit_depth=16, channels=2)
            result = exporter.export_wav(audio, filepath, config)

            assert result is True

            with wave.open(filepath, 'rb') as wav:
                assert wav.getnchannels() == 2
                assert wav.getsampwidth() == 2
        finally:
            if Path(filepath).exists():
                Path(filepath).unlink()


class TestFileExporterWAV24:
    """Tests for 24-bit WAV export."""

    def test_export_24bit(self):
        """Should export 24-bit WAV."""
        exporter = FileExporter()
        audio = np.array([0.0, 0.5, -0.5], dtype=np.float32)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            filepath = f.name

        try:
            config = ExportConfig(bit_depth=24, channels=1)
            result = exporter.export_wav(audio, filepath, config)

            assert result is True
            assert Path(filepath).exists()

            # Verify file size (header + 3 bytes per sample)
            file_size = Path(filepath).stat().st_size
            assert file_size > 44  # Header is 44 bytes minimum
        finally:
            if Path(filepath).exists():
                Path(filepath).unlink()


class TestFileExporterWAV32:
    """Tests for 32-bit float WAV export."""

    def test_export_32bit_float(self):
        """Should export 32-bit float WAV."""
        exporter = FileExporter()
        audio = np.array([0.0, 0.5, -0.5], dtype=np.float32)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            filepath = f.name

        try:
            config = ExportConfig(bit_depth=32, channels=1)
            result = exporter.export_wav(audio, filepath, config)

            assert result is True
            assert Path(filepath).exists()
        finally:
            if Path(filepath).exists():
                Path(filepath).unlink()


class TestFileExporterNormalize:
    """Tests for audio normalization."""

    def test_normalize_increases_level(self):
        """Normalized audio should reach target level."""
        exporter = FileExporter()
        # Quiet audio
        audio = np.array([0.0, 0.1, -0.1, 0.05], dtype=np.float32)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            filepath = f.name

        try:
            config = ExportConfig(bit_depth=16, normalize=True, normalize_headroom_db=0.0)
            exporter.export_wav(audio, filepath, config)

            # Read back and verify level increased
            with wave.open(filepath, 'rb') as wav:
                frames = wav.readframes(wav.getnframes())
                samples = np.frombuffer(frames, dtype=np.int16) / 32767.0
                peak = np.abs(samples).max()
                # Normalized to near 1.0
                assert peak > 0.9
        finally:
            if Path(filepath).exists():
                Path(filepath).unlink()

    def test_normalize_with_headroom(self):
        """Headroom should reduce peak level."""
        exporter = FileExporter()
        audio = np.array([0.0, 0.5, -0.5], dtype=np.float32)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            filepath = f.name

        try:
            # 3 dB headroom = target ~0.707
            config = ExportConfig(bit_depth=16, normalize=True, normalize_headroom_db=3.0)
            exporter.export_wav(audio, filepath, config)

            with wave.open(filepath, 'rb') as wav:
                frames = wav.readframes(wav.getnframes())
                samples = np.frombuffer(frames, dtype=np.int16) / 32767.0
                peak = np.abs(samples).max()
                # Should be less than 1.0 due to headroom
                assert peak < 0.85
        finally:
            if Path(filepath).exists():
                Path(filepath).unlink()


class TestFileExporterValidation:
    """Tests for input validation."""

    def test_empty_audio_raises(self):
        """Should raise on empty audio."""
        exporter = FileExporter()
        audio = np.array([], dtype=np.float32)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            filepath = f.name

        try:
            with pytest.raises(ValueError):
                exporter.export_wav(audio, filepath)
        finally:
            if Path(filepath).exists():
                Path(filepath).unlink()


class TestFileExporterProgress:
    """Tests for progress callback."""

    def test_progress_callback_called(self):
        """Progress callback should be called."""
        exporter = FileExporter()
        audio = np.zeros(1000, dtype=np.float32)
        progress_values = []

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            filepath = f.name

        try:
            def on_progress(p):
                progress_values.append(p)

            exporter.export_wav(audio, filepath, progress_callback=on_progress)

            # Should have received progress updates
            assert len(progress_values) > 0
            # Should end at 1.0
            assert progress_values[-1] == 1.0
        finally:
            if Path(filepath).exists():
                Path(filepath).unlink()


class TestFileExporterInfo:
    """Tests for export info."""

    def test_get_export_info(self):
        """Should return export info dict."""
        exporter = FileExporter()
        audio = np.zeros(44100, dtype=np.float32)  # 1 second

        info = exporter.get_export_info(audio)

        assert info['duration_seconds'] == 1.0
        assert info['sample_count'] == 44100
        assert info['sample_rate'] == 44100
        assert info['bit_depth'] == 16  # default
        assert info['channels'] == 1  # default
        assert 'estimated_size_bytes' in info
        assert 'duration_formatted' in info

    def test_duration_formatted(self):
        """Duration should be formatted as MM:SS.ms."""
        exporter = FileExporter()
        audio = np.zeros(44100 * 65, dtype=np.float32)  # 65 seconds

        info = exporter.get_export_info(audio)

        assert info['duration_formatted'] == "1:05.00"

    def test_size_formatted(self):
        """Size should be formatted with units."""
        exporter = FileExporter()
        audio = np.zeros(44100 * 60, dtype=np.float32)  # 1 minute

        info = exporter.get_export_info(audio)

        # 60 seconds * 44100 samples * 2 bytes = ~5.3 MB
        assert "MB" in info['estimated_size_formatted']


class TestFileExporterRepr:
    """Tests for string representation."""

    def test_repr(self):
        """Should show default bit depth."""
        exporter = FileExporter()
        repr_str = repr(exporter)
        assert "16" in repr_str  # default bit depth


class TestFileExporterClipping:
    """Tests for clipping handling."""

    def test_clips_values_above_one(self):
        """Values > 1.0 should be clipped."""
        exporter = FileExporter()
        audio = np.array([0.0, 1.5, -1.5], dtype=np.float32)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            filepath = f.name

        try:
            config = ExportConfig(bit_depth=16)
            exporter.export_wav(audio, filepath, config)

            with wave.open(filepath, 'rb') as wav:
                frames = wav.readframes(wav.getnframes())
                samples = np.frombuffer(frames, dtype=np.int16)
                # Clipped values should not exceed 16-bit range
                assert samples.max() <= 32767
                assert samples.min() >= -32768
        finally:
            if Path(filepath).exists():
                Path(filepath).unlink()
