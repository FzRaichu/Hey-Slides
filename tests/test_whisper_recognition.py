from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from app.whisper_recognition import transcribe_audio, context_spans


def segment(text, start=0.1, end=0.9):
    return SimpleNamespace(text=text, start=start, end=end, avg_logprob=-0.2,
                           no_speech_prob=0.01, compression_ratio=1.1)


class WhisperRecognitionTests(unittest.TestCase):
    def test_context_groups_keep_gaps_without_overlap_or_mutating_vad_spans(self):
        original = [{"start": 100, "end": 200}, {"start": 300, "end": 400},
                    {"start": 500, "end": 900}]
        self.assertEqual(context_spans(original, max_samples=400),
                         [{"start": 100, "end": 400}, {"start": 500, "end": 900}])
        self.assertEqual(original[0]["end"], 200)
        self.assertEqual(context_spans([]), [])
        with self.assertRaises(ValueError):
            context_spans([{"start": 10, "end": 20}, {"start": 19, "end": 30}])

    def test_independent_spans_preserve_original_offsets_and_consume_generator(self):
        model = MagicMock()
        consumed = []

        def decode(audio, **kwargs):
            def generate():
                consumed.append(len(audio))
                yield segment(" next slide ")
            return generate(), None

        model.transcribe.side_effect = decode
        with patch("app.whisper_recognition.speech_spans", return_value=[
            {"start": 16000, "end": 32000}, {"start": 64000, "end": 80000}]):
            result = transcribe_audio(model, np.zeros(96000), "vad")
        self.assertEqual(consumed, [16000, 16000])
        self.assertEqual([s["start"] for s in result["segments"]], [1.1, 4.1])
        self.assertEqual([s["text"] for s in result["segments"]], ["next slide", "next slide"])
        for call in model.transcribe.call_args_list:
            self.assertFalse(call.kwargs["vad_filter"])
            self.assertIsNone(call.kwargs["initial_prompt"])
            self.assertIsNone(call.kwargs["hotwords"])

    def test_whole_mode_preserves_original_internal_vad_path(self):
        model = MagicMock()
        model.transcribe.return_value = (iter([segment("hello")]), None)
        result = transcribe_audio(model, np.zeros(16000), "whole")
        self.assertTrue(model.transcribe.call_args.kwargs["vad_filter"])
        self.assertEqual(result["segments"][0]["start"], 0.1)

    def test_silence_with_no_speech_spans_does_not_decode(self):
        model = MagicMock()
        with patch("app.whisper_recognition.speech_spans", return_value=[]):
            self.assertEqual(transcribe_audio(model, np.zeros(16000), "vad")["segments"], [])
        model.transcribe.assert_not_called()

    def test_invalid_audio_and_overlapping_spans_rejected(self):
        for audio in (np.zeros((2, 2)), [float("nan")]):
            with self.assertRaises(ValueError):
                transcribe_audio(MagicMock(), audio)
        with patch("app.whisper_recognition.speech_spans", return_value=[
            {"start": 0, "end": 100}, {"start": 90, "end": 200}]):
            with self.assertRaises(ValueError):
                model = MagicMock()
                model.transcribe.return_value = ([], None)
                transcribe_audio(model, np.zeros(300), "vad")


if __name__ == "__main__":
    unittest.main()
