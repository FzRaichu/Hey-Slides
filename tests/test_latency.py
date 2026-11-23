import unittest

from app.session import AudioTimeline, speech_end_at


class AudioTimelineTests(unittest.TestCase):
    def setUp(self):
        self.timeline = AudioTimeline(16000)
        # Three 25 ms blocks arriving at t = 10.025, 10.050, 10.075 s.
        for index in range(3):
            self.timeline.add(400, 10.0 + 0.025 * (index + 1))

    def test_sample_maps_to_capture_time_inside_its_block(self):
        self.assertAlmostEqual(self.timeline.time_of(400), 10.025)
        self.assertAlmostEqual(self.timeline.time_of(600), 10.050 - 200 / 16000)
        self.assertAlmostEqual(self.timeline.time_of(0), 10.0)

    def test_unknown_future_sample_is_none(self):
        self.assertIsNone(self.timeline.time_of(5000))

    def test_speech_end_uses_last_word_and_base_offset(self):
        words = [{"word": "next", "start": 0.0, "end": 0.01}, {"word": "slide", "start": 0.01, "end": 0.0375}]
        self.assertAlmostEqual(speech_end_at(words, 0, self.timeline), 10.0375)
        # A recognizer created after 400 samples reports times from its own start.
        self.assertAlmostEqual(speech_end_at([{"end": 0.0125}], 400, self.timeline), 10.0375)
        # Warm-up audio before the stream makes Vosk times start late: negative base.
        self.assertAlmostEqual(speech_end_at([{"end": 2.0375}], -32000, self.timeline), 10.0375)

    def test_missing_words_give_none(self):
        self.assertIsNone(speech_end_at([], 0, self.timeline))
        self.assertIsNone(speech_end_at([{"word": "x"}], 0, self.timeline))


if __name__ == "__main__":
    unittest.main()
