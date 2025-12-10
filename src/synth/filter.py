# Moog Filter module for Mini Synthesizer
"""
filter.py - 4-pole ladder lowpass filter

Implements the MoogFilter value object from the domain model.
Emulates the classic Moog transistor ladder filter with resonance feedback.

Filter characteristics:
- 4-pole (24dB/octave) lowpass response
- Resonance feedback for self-oscillation capability
- Cutoff frequency modulation support
- Real-time safe (no allocations in process loop)

The filter uses a simplified digital model based on the Huovilainen
variation of the Moog ladder filter.

Usage:
    filt = MoogFilter(sample_rate=44100)
    filt.cutoff = 1000.0      # 1kHz cutoff
    filt.resonance = 0.5      # 50% resonance
    output = filt.process(input_samples)
"""

from typing import Optional
import numpy as np

try:
    from numba import jit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    # Fallback: no-op decorator if numba not installed
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


@jit(nopython=True, cache=True)
def _moog_filter_process(samples: np.ndarray, g: float, k: float,
                          s0: float, s1: float, s2: float, s3: float):
    """JIT-compiled Moog filter processing loop.

    This is the performance-critical inner loop, compiled to native code.

    Args:
        samples: Input audio samples
        g: Stage gain coefficient
        k: Feedback coefficient
        s0-s3: Filter stage states

    Returns:
        Tuple of (output array, updated s0, s1, s2, s3)
    """
    num_samples = len(samples)
    output = np.empty(num_samples, dtype=np.float32)

    for i in range(num_samples):
        x = samples[i]

        # Apply feedback from output (with soft clipping)
        # np.tanh not available in numba nopython, use approximation
        tanh_s3 = s3
        if s3 > 3.0:
            tanh_s3 = 1.0
        elif s3 < -3.0:
            tanh_s3 = -1.0
        else:
            s3_sq = s3 * s3
            tanh_s3 = s3 * (27.0 + s3_sq) / (27.0 + 9.0 * s3_sq)

        feedback = k * tanh_s3
        u = x - feedback

        # Apply soft clipping to input
        if u > 3.0:
            u = 1.0
        elif u < -3.0:
            u = -1.0
        else:
            u_sq = u * u
            u = u * (27.0 + u_sq) / (27.0 + 9.0 * u_sq)

        # Stage 0: First lowpass
        v0 = g * (u - s0)
        lp0 = v0 + s0
        s0 = lp0 + v0

        # Stage 1: Second lowpass
        v1 = g * (lp0 - s1)
        lp1 = v1 + s1
        s1 = lp1 + v1

        # Stage 2: Third lowpass
        v2 = g * (lp1 - s2)
        lp2 = v2 + s2
        s2 = lp2 + v2

        # Stage 3: Fourth lowpass (output)
        v3 = g * (lp2 - s3)
        lp3 = v3 + s3
        s3 = lp3 + v3

        output[i] = lp3

    return output, s0, s1, s2, s3


class MoogFilter:
    """4-pole ladder lowpass filter.

    Digital emulation of the classic Moog transistor ladder filter.
    Features cutoff frequency control, resonance/feedback, and
    modulation input for envelope or LFO control.

    Attributes:
        sample_rate: Audio sample rate in Hz
        cutoff: Cutoff frequency in Hz (20 to Nyquist)
        resonance: Resonance/feedback amount (0.0 to 1.0)
        cutoff_mod: Cutoff frequency modulation amount
    """

    def __init__(self, sample_rate: int = 44100):
        """Initialize filter with sample rate.

        Args:
            sample_rate: Audio sample rate in Hz (default: 44100)
        """
        self.sample_rate = sample_rate
        self.nyquist = sample_rate / 2.0

        # Filter state (4 stages)
        self._stage = np.zeros(4, dtype=np.float64)

        # Filter parameters
        self._cutoff: float = 1000.0
        self._resonance: float = 0.0
        self._cutoff_mod: float = 0.0

        # Pre-computed coefficients
        self._g: float = 0.0  # Stage gain
        self._k: float = 0.0  # Feedback coefficient
        self._update_coefficients()

        # Work buffer
        self._work_buffer: Optional[np.ndarray] = None

    @property
    def cutoff(self) -> float:
        """Cutoff frequency in Hz."""
        return self._cutoff

    @cutoff.setter
    def cutoff(self, value: float) -> None:
        """Set cutoff frequency, clamped to valid range."""
        max_cutoff = self.nyquist * 0.9  # Prevent aliasing issues
        self._cutoff = max(20.0, min(max_cutoff, value))
        self._update_coefficients()

    @property
    def resonance(self) -> float:
        """Resonance amount (0.0 to 1.0)."""
        return self._resonance

    @resonance.setter
    def resonance(self, value: float) -> None:
        """Set resonance, clamped to 0.0-1.0."""
        self._resonance = max(0.0, min(1.0, value))
        self._update_coefficients()

    @property
    def cutoff_mod(self) -> float:
        """Cutoff modulation amount (in octaves)."""
        return self._cutoff_mod

    @cutoff_mod.setter
    def cutoff_mod(self, value: float) -> None:
        """Set cutoff modulation amount."""
        self._cutoff_mod = value
        self._update_coefficients()

    @property
    def effective_cutoff(self) -> float:
        """Actual cutoff frequency including modulation."""
        modulated = self._cutoff * (2.0 ** (self._cutoff_mod * 4.0))
        max_cutoff = self.nyquist * 0.9
        return max(20.0, min(max_cutoff, modulated))

    def _update_coefficients(self) -> None:
        """Recalculate filter coefficients when parameters change.

        Uses the Huovilainen/Zavalishin TPT (topology-preserving transform)
        style digital filter design for stability.
        """
        fc = self.effective_cutoff

        # Normalized frequency (0 to 0.5)
        f = fc / self.sample_rate

        # Pre-warp for bilinear transform (Tustin)
        # This compensates for frequency warping in digital filters
        wd = 2.0 * self.sample_rate * np.tan(np.pi * f)

        # One-pole lowpass coefficient
        # g = wd / (2 * fs + wd) simplified
        self._g = wd / (2.0 * self.sample_rate + wd)

        # Feedback coefficient (4 * resonance for 4-pole filter)
        self._k = 4.0 * self._resonance

    def reset(self) -> None:
        """Reset filter state to zero.

        Call this when starting a new note to prevent clicks.
        """
        self._stage.fill(0.0)

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Process audio samples through the filter.

        Implements a 4-stage ladder filter with feedback.
        Each stage is a one-pole lowpass filter.
        Uses JIT-compiled code for performance when numba is available.

        Args:
            samples: Input audio samples (NumPy array)

        Returns:
            Filtered audio samples (same length as input)
        """
        # Ensure samples are float32 for consistent processing
        if samples.dtype != np.float32:
            samples = samples.astype(np.float32)

        # Use JIT-compiled function for processing
        output, s0, s1, s2, s3 = _moog_filter_process(
            samples, self._g, self._k,
            self._stage[0], self._stage[1], self._stage[2], self._stage[3]
        )

        # Save state
        self._stage[0] = s0
        self._stage[1] = s1
        self._stage[2] = s2
        self._stage[3] = s3

        return output

    def get_frequency_response(self, frequencies: np.ndarray) -> np.ndarray:
        """Calculate filter frequency response at given frequencies.

        Useful for visualization of the filter curve.

        Args:
            frequencies: Array of frequencies in Hz

        Returns:
            Array of magnitude responses (linear scale)
        """
        # Normalized frequencies
        w = frequencies / self.sample_rate

        # Calculate one-pole magnitude response at each frequency
        # H(w) = g / sqrt(g^2 + (1-g)^2 + 2*g*(1-g)*cos(2*pi*w))
        g = self._g
        cos_w = np.cos(2.0 * np.pi * w)

        # Simplified magnitude for one pole
        mag_one_pole = g / np.sqrt(g**2 + (1-g)**2 - 2*g*(1-g)*cos_w + 1e-10)

        # Four-pole magnitude is one-pole to the 4th power
        magnitude = mag_one_pole ** 4

        # Apply resonance boost near cutoff
        if self._resonance > 0:
            fc = self.effective_cutoff
            # Resonance peak around cutoff frequency
            peak_width = fc * 0.5
            peak = np.exp(-0.5 * ((frequencies - fc) / peak_width) ** 2)
            magnitude = magnitude * (1.0 + self._resonance * 3.0 * peak)

        return magnitude.astype(np.float32)

    def __repr__(self) -> str:
        """String representation of filter state."""
        return (f"MoogFilter(cutoff={self._cutoff:.1f}Hz, "
                f"resonance={self._resonance:.2f}, "
                f"effective_cutoff={self.effective_cutoff:.1f}Hz)")
