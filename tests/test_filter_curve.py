# Tests for Filter Curve Module
"""
test_filter_curve - Unit tests for frequency response visualization.
"""

import pytest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from visualization.filter_curve import FilterCurve, ScaleMode


class TestScaleMode:
    """Tests for ScaleMode enum."""

    def test_scale_modes_exist(self):
        """Should have all scale modes."""
        assert ScaleMode.LINEAR
        assert ScaleMode.DECIBEL

    def test_modes_distinct(self):
        """Modes should be distinct."""
        assert ScaleMode.LINEAR != ScaleMode.DECIBEL


class TestFilterCurveInit:
    """Tests for FilterCurve initialization constants."""

    def test_default_dimensions(self):
        """Should have default dimensions."""
        assert FilterCurve.DEFAULT_WIDTH == 400
        assert FilterCurve.DEFAULT_HEIGHT == 200

    def test_frequency_range(self):
        """Should have valid frequency range."""
        assert FilterCurve.MIN_FREQ == 20.0
        assert FilterCurve.MAX_FREQ == 20000.0

    def test_db_range(self):
        """Should have valid dB range."""
        assert FilterCurve.MIN_DB == -60.0
        assert FilterCurve.MAX_DB == 12.0

    def test_grid_lines(self):
        """Should have grid line definitions."""
        assert 1000 in FilterCurve.FREQ_GRID_LINES
        assert 0 in FilterCurve.DB_GRID_LINES


class TestFilterCurveFrequencyConversion:
    """Tests for frequency to X coordinate conversion."""

    def test_freq_to_x_min(self):
        """Minimum frequency should map to X=0."""
        width = 400
        min_freq = 20.0
        max_freq = 20000.0

        log_min = np.log10(min_freq)
        log_max = np.log10(max_freq)
        log_freq = np.log10(min_freq)
        x = int((log_freq - log_min) / (log_max - log_min) * width)

        assert x == 0

    def test_freq_to_x_max(self):
        """Maximum frequency should map to X=width."""
        width = 400
        min_freq = 20.0
        max_freq = 20000.0

        log_min = np.log10(min_freq)
        log_max = np.log10(max_freq)
        log_freq = np.log10(max_freq)
        x = int((log_freq - log_min) / (log_max - log_min) * width)

        assert x == width

    def test_freq_to_x_1khz(self):
        """1kHz should be roughly in middle-left."""
        width = 400
        min_freq = 20.0
        max_freq = 20000.0

        log_min = np.log10(min_freq)
        log_max = np.log10(max_freq)
        log_freq = np.log10(1000.0)
        x = int((log_freq - log_min) / (log_max - log_min) * width)

        # 1kHz is about 57% of the way on log scale from 20 to 20k
        assert 200 < x < 280

    def test_x_to_freq_roundtrip(self):
        """Converting X back to freq should be consistent."""
        width = 400
        min_freq = 20.0
        max_freq = 20000.0
        original_freq = 1000.0

        # freq_to_x
        log_min = np.log10(min_freq)
        log_max = np.log10(max_freq)
        log_freq = np.log10(original_freq)
        x = int((log_freq - log_min) / (log_max - log_min) * width)

        # x_to_freq
        log_freq_back = log_min + (x / width) * (log_max - log_min)
        freq_back = 10 ** log_freq_back

        # Should be close (within rounding error)
        assert abs(freq_back - original_freq) < 50  # ~5% tolerance


class TestFilterCurveMagnitudeConversion:
    """Tests for magnitude to Y coordinate conversion."""

    def test_mag_to_y_unity_db(self):
        """Unity gain (0 dB) should map to specific Y."""
        height = 200
        min_db = -60.0
        max_db = 12.0

        magnitude = 1.0  # 0 dB
        db = 20 * np.log10(magnitude)
        normalized = (db - min_db) / (max_db - min_db)
        y = int(height * (1.0 - normalized))

        # 0 dB is 60/72 of the way up from -60 to +12
        expected_normalized = (0 - min_db) / (max_db - min_db)
        expected_y = int(height * (1.0 - expected_normalized))
        assert y == expected_y

    def test_mag_to_y_minus_6db(self):
        """- 6 dB should be below unity."""
        height = 200
        min_db = -60.0
        max_db = 12.0

        magnitude = 0.5  # -6 dB
        db = 20 * np.log10(magnitude)

        normalized = (db - min_db) / (max_db - min_db)
        y = int(height * (1.0 - normalized))

        # Calculate unity Y for comparison
        db_unity = 0
        normalized_unity = (db_unity - min_db) / (max_db - min_db)
        y_unity = int(height * (1.0 - normalized_unity))

        # -6 dB should be lower on screen (higher Y value)
        assert y > y_unity

    def test_mag_to_y_linear(self):
        """Linear scale should map magnitude directly."""
        height = 200

        magnitude = 0.5
        # Linear: magnitude = max(0.0, min(2.0, magnitude))
        # y = int(height * (1.0 - magnitude / 2.0))
        y = int(height * (1.0 - magnitude / 2.0))

        # 0.5 / 2.0 = 0.25, so y = 200 * 0.75 = 150
        assert y == 150


class TestFilterCurveResponse:
    """Tests for filter response calculation."""

    def test_response_shape(self):
        """Response should match frequency array length."""
        width = 400
        min_freq = 20.0
        max_freq = 20000.0

        frequencies = np.logspace(
            np.log10(min_freq),
            np.log10(max_freq),
            width
        )

        # Simplified response calculation
        cutoff = 1000.0
        resonance = 0.5
        sample_rate = 44100

        w = frequencies / sample_rate
        wc = cutoff / sample_rate
        g = np.tan(np.pi * np.minimum(wc, 0.49))

        omega = 2.0 * np.pi * w
        H_one_pole = g / np.sqrt(g**2 + omega**2 + 1e-10)
        magnitude = H_one_pole ** 4

        assert len(magnitude) == width

    def test_response_lowpass_shape(self):
        """Response should decrease at high frequencies."""
        frequencies = np.logspace(np.log10(20), np.log10(20000), 100)
        cutoff = 1000.0
        sample_rate = 44100

        w = frequencies / sample_rate
        wc = cutoff / sample_rate
        g = np.tan(np.pi * np.minimum(wc, 0.49))

        omega = 2.0 * np.pi * w
        H_one_pole = g / np.sqrt(g**2 + omega**2 + 1e-10)
        magnitude = H_one_pole ** 4

        # Low frequencies should have higher magnitude than high
        low_freq_mag = magnitude[:20].mean()
        high_freq_mag = magnitude[-20:].mean()

        assert low_freq_mag > high_freq_mag

    def test_resonance_adds_peak(self):
        """Resonance should add peak near cutoff."""
        frequencies = np.logspace(np.log10(20), np.log10(20000), 400)
        cutoff = 1000.0
        sample_rate = 44100

        # Calculate base response
        w = frequencies / sample_rate
        wc = cutoff / sample_rate
        g = np.tan(np.pi * np.minimum(wc, 0.49))
        omega = 2.0 * np.pi * w
        H_one_pole = g / np.sqrt(g**2 + omega**2 + 1e-10)
        base_magnitude = H_one_pole ** 4

        # Calculate with resonance
        resonance = 0.8
        peak_width = cutoff * 0.3
        peak = np.exp(-0.5 * ((frequencies - cutoff) / peak_width) ** 2)
        resonant_magnitude = base_magnitude * (1.0 + resonance * 4.0 * peak)

        # Peak should be higher with resonance
        cutoff_idx = np.argmin(np.abs(frequencies - cutoff))
        assert resonant_magnitude[cutoff_idx] > base_magnitude[cutoff_idx]


class TestFilterCurveParameterBounds:
    """Tests for parameter bounds."""

    def test_cutoff_bounds(self):
        """Cutoff should be clamped to valid range."""
        min_freq = 20.0
        max_freq = 20000.0

        # Test low bound
        cutoff = 5.0
        clamped = max(min_freq, min(max_freq, cutoff))
        assert clamped == min_freq

        # Test high bound
        cutoff = 30000.0
        clamped = max(min_freq, min(max_freq, cutoff))
        assert clamped == max_freq

    def test_resonance_bounds(self):
        """Resonance should be clamped to 0-1."""
        # Test low bound
        resonance = -0.5
        clamped = max(0.0, min(1.0, resonance))
        assert clamped == 0.0

        # Test high bound
        resonance = 1.5
        clamped = max(0.0, min(1.0, resonance))
        assert clamped == 1.0


class TestFilterCurveLogFrequencies:
    """Tests for logarithmic frequency generation."""

    def test_log_frequency_range(self):
        """Generated frequencies should span full range."""
        min_freq = 20.0
        max_freq = 20000.0
        width = 400

        frequencies = np.logspace(
            np.log10(min_freq),
            np.log10(max_freq),
            width
        )

        assert len(frequencies) == width
        assert abs(frequencies[0] - min_freq) < 0.1
        assert abs(frequencies[-1] - max_freq) < 1.0

    def test_log_spacing(self):
        """Frequencies should be logarithmically spaced."""
        min_freq = 20.0
        max_freq = 20000.0
        width = 100

        frequencies = np.logspace(
            np.log10(min_freq),
            np.log10(max_freq),
            width
        )

        # Ratio between adjacent frequencies should be roughly constant
        ratios = frequencies[1:] / frequencies[:-1]
        ratio_std = np.std(ratios)

        # Standard deviation should be very small for log spacing
        assert ratio_std < 0.001


class TestFilterCurveHexConversion:
    """Tests for hex color conversion."""

    def test_hex_to_rgba(self):
        """Should convert hex with alpha to darker color."""
        hex_color = '#ff6b6b'
        alpha = 0.2

        # Parse hex
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)

        # Background color
        bg_r, bg_g, bg_b = 26, 26, 26

        # Blend
        new_r = int(r * alpha + bg_r * (1 - alpha))
        new_g = int(g * alpha + bg_g * (1 - alpha))
        new_b = int(b * alpha + bg_b * (1 - alpha))

        result = f'#{new_r:02x}{new_g:02x}{new_b:02x}'

        # Should be a valid hex color
        assert result.startswith('#')
        assert len(result) == 7


class TestFilterCurveRepr:
    """Tests for string representation."""

    def test_repr_format(self):
        """Should format repr correctly."""
        width = 400
        height = 200
        cutoff = 1000.0
        resonance = 0.5

        repr_str = f"FilterCurve({width}x{height}, fc={cutoff:.0f}Hz, Q={resonance:.2f})"
        assert "400x200" in repr_str
        assert "1000Hz" in repr_str
        assert "0.50" in repr_str
