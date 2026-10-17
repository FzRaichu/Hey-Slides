import unittest
import numpy as np

from app.features import ManualMFCC


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.extractor = ManualMFCC()

    def test_shape_and_finiteness_for_one_second(self):
        t = np.arange(16000) / 16000
        result = self.extractor.extract(0.25 * np.sin(2 * np.pi * 440 * t))
        self.assertEqual(result.mfcc.shape, (13, 98))
        self.assertEqual(result.vector.shape, (156,))
        self.assertTrue(np.isfinite(result.vector).all())
        self.assertAlmostEqual(result.rms, 0.25 / np.sqrt(2), places=6)

    def test_silence_and_short_inputs(self):
        for samples in (np.zeros(16000), np.zeros(15), np.array([])):
            result = self.extractor.extract(samples)
            self.assertTrue(np.isfinite(result.vector).all())
            self.assertEqual(result.rms, 0)
            self.assertLess(np.abs(self.extractor.delta(result.mfcc)).max(), 1e-10)

    def test_orthonormal_dct(self):
        np.testing.assert_allclose(self.extractor.dct @ self.extractor.dct.T,
                                   np.eye(13), atol=1e-12)

    def test_delta_of_linear_sequence_and_constant(self):
        linear = np.arange(15, dtype=float)[None, :]
        np.testing.assert_allclose(self.extractor.delta(linear)[:, 2:-2], 1)
        np.testing.assert_allclose(self.extractor.delta(np.ones((13, 15))), 0)

    def test_filter_bank_has_frequency_selectivity(self):
        bank = self.extractor.mel_bank
        self.assertTrue((bank >= 0).all())
        self.assertTrue((bank.sum(axis=1) > 0).all())
        self.assertTrue((np.diff(bank.argmax(axis=1)) > 0).all())

    def test_invalid_audio_rejected(self):
        for samples in (np.zeros((2, 20)), np.array([float("nan")]), np.array([float("inf")])):
            with self.assertRaises(ValueError):
                self.extractor.extract(samples)


if __name__ == "__main__":
    unittest.main()
