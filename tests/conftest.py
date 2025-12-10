# pytest configuration for Mini Synthesizer tests
"""
Shared fixtures and configuration for pytest test suite.
"""
import pytest
import numpy as np
from typing import Generator


# Standard audio configuration for tests
SAMPLE_RATE = 44100
BUFFER_SIZE = 512
TEST_DURATION_SAMPLES = SAMPLE_RATE  # 1 second of audio


@pytest.fixture
def sample_rate() -> int:
    """Standard sample rate for audio tests."""
    return SAMPLE_RATE


@pytest.fixture
def buffer_size() -> int:
    """Standard buffer size for audio tests."""
    return BUFFER_SIZE


@pytest.fixture
def test_buffer() -> np.ndarray:
    """Pre-allocated test buffer."""
    return np.zeros(BUFFER_SIZE, dtype=np.float32)


@pytest.fixture
def one_second_buffer() -> np.ndarray:
    """One second of audio samples for longer tests."""
    return np.zeros(TEST_DURATION_SAMPLES, dtype=np.float32)


@pytest.fixture
def frequency_a4() -> float:
    """A4 = 440 Hz reference pitch."""
    return 440.0


@pytest.fixture
def midi_note_a4() -> int:
    """MIDI note number for A4."""
    return 69


@pytest.fixture
def midi_note_middle_c() -> int:
    """MIDI note number for middle C (C4)."""
    return 60


def assert_audio_range(samples: np.ndarray, min_val: float = -1.0, max_val: float = 1.0):
    """Assert that audio samples are within valid range."""
    assert np.all(samples >= min_val), f"Samples below minimum: {np.min(samples)}"
    assert np.all(samples <= max_val), f"Samples above maximum: {np.max(samples)}"


def assert_not_silent(samples: np.ndarray, threshold: float = 1e-6):
    """Assert that audio samples are not completely silent."""
    rms = np.sqrt(np.mean(samples**2))
    assert rms > threshold, f"Audio appears silent (RMS: {rms})"


def assert_frequency_content(samples: np.ndarray, expected_freq: float,
                             sample_rate: int = SAMPLE_RATE, tolerance_hz: float = 5.0):
    """Assert that audio contains expected frequency content using FFT."""
    # Perform FFT
    fft_result = np.abs(np.fft.rfft(samples))
    freqs = np.fft.rfftfreq(len(samples), 1.0 / sample_rate)

    # Find peak frequency
    peak_idx = np.argmax(fft_result)
    peak_freq = freqs[peak_idx]

    # Check if peak is within tolerance of expected frequency
    freq_error = abs(peak_freq - expected_freq)
    assert freq_error <= tolerance_hz, \
        f"Expected frequency {expected_freq} Hz, got {peak_freq} Hz (error: {freq_error} Hz)"
