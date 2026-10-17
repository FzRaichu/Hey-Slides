from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import uuid
import wave

from app import config
from app.session import MicrophoneSession


class AudioSessionTests(unittest.TestCase):
    def test_dual_decoder_keeps_transcript_separate_and_records_exact_pcm(self):
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=config.LOG_DIR) as folder:
            session = MicrophoneSession()
            session.session_id = uuid.uuid4().hex
            original_emit = session._emit

            def emit(kind, **event):
                original_emit(kind, **event)
                if kind == "command_final":
                    session.stop()

            session._emit = emit
            pcm = b"\x01\x00" * 400
            stream = MagicMock()

            def make_stream(**kwargs):
                stream.__enter__.side_effect = lambda: kwargs["callback"](pcm, 400, None, False)
                return stream

            general = MagicMock()
            general.feed.return_value = {"kind": "final", "changed": True, "text": "a slight next line",
                                         "decode_ms": 1, "words": []}
            general.finish.return_value = {"kind": "final", "changed": True, "text": "", "decode_ms": None, "words": []}
            focused = MagicMock()
            focused.feed.return_value = {"kind": "final", "changed": True, "text": "hey slides next slide",
                                         "decode_ms": 1, "words": [], "eligible": True, "reason": "candidate"}
            with patch("app.session.load_model", return_value=object()), \
                 patch("app.session.StreamingRecognizer", return_value=general), \
                 patch("app.session.CommandRecognizer", return_value=focused), \
                 patch("sounddevice.RawInputStream", side_effect=make_stream), \
                 patch("sounddevice.check_input_settings"), \
                 patch("app.session.config.LOG_DIR", Path(folder)):
                session._run(None, "light", config.model_path("light"), command_assist=True, record_audio=True)
            events = []
            while not session.events.empty():
                events.append(session.events.get_nowait())
            self.assertFalse(any(event["kind"] == "error" for event in events), events)
            normal = next(event for event in events if event["kind"] == "final")
            self.assertEqual(normal["text"], "a slight next line")
            self.assertFalse(normal["allow_action"])
            self.assertTrue(normal["transcript_only"])
            command = next(event for event in events if event["kind"] == "command_final")
            self.assertEqual(command["text"], "hey slides next slide")
            self.assertTrue(command["allow_action"])
            saved = next(event for event in events if event["kind"] == "recording_saved")
            with wave.open(saved["path"], "rb") as recording:
                self.assertEqual(recording.getframerate(), 16000)
                self.assertEqual(recording.getnchannels(), 1)
                self.assertEqual(recording.readframes(400), pcm)
            focused.finish.assert_not_called()  # Stop must not flush a command into an action.
