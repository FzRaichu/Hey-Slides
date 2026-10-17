import unittest
from unittest.mock import MagicMock, patch

from scripts.transcribe_wav import transcribe


class FileReplayTests(unittest.TestCase):
    def test_invalid_slide_is_logged_and_later_valid_commands_continue(self):
        wav = MagicMock()
        wav.getnchannels.return_value = 1
        wav.getsampwidth.return_value = 2
        wav.getframerate.return_value = 16000
        wav.getcomptype.return_value = "NONE"
        wav.getnframes.return_value = 800
        wav.readframes.side_effect = [b"\0\0" * 400, b"\0\0" * 400, b""]
        recognizer = MagicMock()
        recognizer.feed.side_effect = [
            {"kind": "final", "text": "hey slides go to slide 99", "words": [], "decode_ms": 1},
            {"kind": "final", "text": "hey slides next slide", "words": [], "decode_ms": 1},
        ]
        recognizer.finish.return_value = {"text": "", "words": []}
        with patch("scripts.transcribe_wav.load_model"), \
             patch("scripts.transcribe_wav.StreamingRecognizer", return_value=recognizer), \
             patch("scripts.transcribe_wav.wave.open") as opened:
            opened.return_value.__enter__.return_value = wav
            result = transcribe("fixture.wav")
        self.assertEqual(result["utterances"][0]["status"], "command rejected")
        self.assertIsNone(result["utterances"][0]["action"])
        self.assertEqual(result["utterances"][1]["action"], "next")
        self.assertEqual(result["preview_slide"], 2)


if __name__ == "__main__":
    unittest.main()
