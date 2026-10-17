import unittest
from unittest.mock import MagicMock, patch

from app import config
from app.session import MicrophoneSession


class ModelProfileTests(unittest.TestCase):
    def test_slow_decode_never_emits_an_actionable_final(self):
        session = MicrophoneSession()
        recognizer = MagicMock()
        recognizer.feed.return_value = {"kind": "final", "changed": True,
                                       "text": "hey slides next slide"}
        stream = MagicMock()

        def make_stream(**kwargs):
            stream.__enter__.side_effect = lambda: kwargs["callback"](b"\0\0" * 400, 400, None, False)
            return stream

        with patch("app.session.load_model", return_value=object()), \
             patch("app.session.StreamingRecognizer", return_value=recognizer), \
             patch("sounddevice.check_input_settings"), \
             patch("sounddevice.RawInputStream", side_effect=make_stream), \
             patch("app.session.time.perf_counter", side_effect=[0.0, 0.0, 1.0]):
            session._run(None, "light", config.model_path("light"))
        events = []
        while not session.events.empty():
            events.append(session.events.get_nowait())
        self.assertTrue(any(event["kind"] == "error" and "stale-audio" in event["text"] for event in events))
        self.assertFalse(any(event["kind"] == "final" for event in events))

    def test_profile_paths_are_fixed_project_models(self):
        self.assertEqual(config.model_path("light").name, "vosk-model-small-en-us-0.15")
        self.assertEqual(config.model_path("balanced").name, "vosk-model-en-us-0.22-lgraph")
        with self.assertRaises(ValueError):
            config.model_path("../../outside")

    def test_worker_reuses_same_profile_and_reloads_on_change(self):
        session = MicrophoneSession()
        stream = MagicMock()
        stream.__enter__.side_effect = lambda: session.stop()
        recognizer = MagicMock()
        recognizer.finish.return_value = {"text": ""}
        with patch("app.session.load_model", side_effect=[object(), object()]) as load, \
             patch("app.session.StreamingRecognizer", return_value=recognizer), \
             patch("sounddevice.check_input_settings"), \
             patch("sounddevice.RawInputStream", return_value=stream):
            for profile in ("light", "light", "balanced"):
                session._stop.clear()
                session._run(None, profile, config.model_path(profile))
            self.assertEqual(load.call_count, 2)
            self.assertEqual(load.call_args_list[0].args[0], config.model_path("light"))
            self.assertEqual(load.call_args_list[1].args[0], config.model_path("balanced"))
            self.assertEqual(session._model_profile, "balanced")
        events = []
        while not session.events.empty():
            events.append(session.events.get_nowait())
        self.assertFalse(any(event["kind"] == "error" for event in events), events)
