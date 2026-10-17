import unittest

from app.commands import CommandParser, SlideDeck


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.parser = CommandParser()

    def test_explicit_phrases_and_case(self):
        self.assertEqual(self.parser.accept("HEY SLIDES, next slide!", "a", 1).action, "next")
        self.assertEqual(self.parser.accept("Hey Slides, previous slide.", "b", 2).action, "previous")

    def test_ordinary_speech_and_embedded_prefix_do_not_act(self):
        for n, text in enumerate(["next slide", "The next slide shows our results",
                                  "I said hey slides next slide", "hey slides next slideshow",
                                  "hey slides do not go to the next slide", "hey slides next slide is interesting",
                                  "hey slides next slide 2"]):
            self.assertIsNone(self.parser.accept(text, str(n), n + 1).action, text)

    def test_separate_wake_and_command(self):
        self.assertEqual(self.parser.accept("hey slides", "a", 10).status, "armed")
        self.assertEqual(self.parser.accept("next slide", "b", 12).action, "next")
        self.assertIsNone(self.parser.accept("next slide", "c", 13).action)

    def test_expired_wake_is_rejected(self):
        self.parser.accept("hey slides", "a", 10)
        self.assertIsNone(self.parser.accept("next slide", "b", 14).action)

    def test_unrelated_utterance_consumes_wake(self):
        self.parser.accept("hey slides", "a", 1)
        self.parser.accept("here is my explanation", "b", 2)
        self.assertIsNone(self.parser.accept("next slide", "c", 3).action)

    def test_replayed_event_deduplicates_but_new_identical_command_works(self):
        phrase = "hey slides next slide"
        self.assertEqual(self.parser.accept(phrase, "a", 1).action, "next")
        self.assertIsNone(self.parser.accept(phrase, "a", 2).action)
        self.assertEqual(self.parser.accept(phrase, "b", 3).action, "next")

    def test_reset_clears_authorization(self):
        self.parser.accept("hey slides", "a", 1)
        self.parser.reset()
        self.assertIsNone(self.parser.accept("previous slide", "b", 2).action)

    def test_slide_boundaries(self):
        deck = SlideDeck(count=2)
        self.assertFalse(deck.apply("previous"))
        self.assertTrue(deck.apply("next"))
        self.assertFalse(deck.apply("next"))
        self.assertEqual(deck.index, 1)
        self.assertTrue(deck.apply("previous"))
        with self.assertRaises(ValueError):
            deck.apply("delete")


if __name__ == "__main__":
    unittest.main()
