"""Explicit educational MFCC extraction using NumPy, not librosa's MFCC helper.

This analysis branch does NOT replace Vosk's internal feature extraction.
Steps: framing -> Hamming -> FFT power -> Mel bank -> log -> orthonormal
DCT-II -> deltas -> mean/std/min/max pooling. No future audio is requested.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class FeatureResult:
    mfcc: np.ndarray
    vector: np.ndarray
    rms: float


class ManualMFCC:
    def __init__(self, sample_rate=16000, frame_ms=25, hop_ms=10,
                 n_fft=512, n_mels=40, n_mfcc=13):
        self.sample_rate = sample_rate
        self.frame_length = round(sample_rate * frame_ms / 1000)
        self.hop_length = round(sample_rate * hop_ms / 1000)
        self.n_fft = n_fft
        if not 0 < self.hop_length <= self.frame_length <= n_fft:
            raise ValueError("Require 0 < hop <= frame <= FFT length")
        if not 0 < n_mfcc <= n_mels:
            raise ValueError("Require 0 < MFCC count <= Mel filter count")
        self.window = np.hamming(self.frame_length)
        # HTK Mel scale, with triangular filters evaluated at FFT frequencies.
        mel_max = 2595 * np.log10(1 + (sample_rate / 2) / 700)
        edges = 700 * (10 ** (np.linspace(0, mel_max, n_mels + 2) / 2595) - 1)
        frequencies = np.fft.rfftfreq(n_fft, 1 / sample_rate)
        rising = (frequencies[None, :] - edges[:-2, None]) / (edges[1:-1] - edges[:-2])[:, None]
        falling = (edges[2:, None] - frequencies[None, :]) / (edges[2:] - edges[1:-1])[:, None]
        self.mel_bank = np.maximum(0, np.minimum(rising, falling))
        k, n = np.arange(n_mfcc)[:, None], np.arange(n_mels)[None, :]
        self.dct = np.sqrt(2 / n_mels) * np.cos(np.pi / n_mels * (n + 0.5) * k)
        self.dct[0] /= np.sqrt(2)

    @staticmethod
    def delta(features, radius=2):
        padded = np.pad(features, ((0, 0), (radius, radius)), mode="edge")
        result = np.zeros_like(features)
        length = features.shape[1]
        for offset in range(1, radius + 1):
            result += offset * (padded[:, radius + offset:radius + offset + length]
                                - padded[:, radius - offset:radius - offset + length])
        return result / (2 * sum(i * i for i in range(1, radius + 1)))

    def extract(self, samples) -> FeatureResult:
        samples = np.asarray(samples, dtype=np.float64)
        if samples.ndim != 1 or not np.isfinite(samples).all():
            raise ValueError("Expected a finite mono float waveform")
        rms = float(np.sqrt(np.mean(samples ** 2))) if samples.size else 0.0
        if samples.size < self.frame_length:
            samples = np.pad(samples, (0, self.frame_length - samples.size))
        frames = np.lib.stride_tricks.sliding_window_view(samples, self.frame_length)[::self.hop_length]
        power = np.abs(np.fft.rfft(frames * self.window, n=self.n_fft, axis=1)) ** 2 / self.n_fft
        log_mel = np.log(np.maximum(power @ self.mel_bank.T, 1e-12))
        mfcc = self.dct @ log_mel.T
        delta = self.delta(mfcc)
        combined = np.vstack((mfcc, delta, self.delta(delta)))
        vector = np.concatenate((combined.mean(axis=1), combined.std(axis=1),
                                 combined.min(axis=1), combined.max(axis=1)))
        return FeatureResult(mfcc, vector, rms)
