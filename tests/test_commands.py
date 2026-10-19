import unittest

from app.commands import CommandParser, SlideDeck


class CommandTests(unittest.TestCase):
    def test_direct_commands_accept_exact_singular_plural_and_numbers(self):
        parser = CommandParser(require_prefix=False)
        for index, (text, action, target) in enumerate([
            ("Next slide!", "next", None), ("Next Slides", "next", None),
            ("Previous slides", "previous", None), ("previous slide", "previous", None),
            ("Go to slide seven", "goto", 7), ("go to slides 12", "goto", 12)]):
            decision = parser.accept(text, str(index), index + 1)
            self.assertEqual((decision.action, decision.target_slide), (action, target))

    def test_direct_mode_rejects_embedded_negated_prefixed_and_incomplete_phrases(self):
        parser = CommandParser(require_prefix=False)
        for index, text in enumerate(["on the next slide", "next slide shows results",
                                      "do not go to slide seven", "go to slide", "next",
                                      "hey slides next slide", "hey slides", "next slide next slide",
                                      "go to slides zero", "next slideshow", "next slide 2"]):
            self.assertIsNone(parser.accept(text, str(index), index + 1).action, text)
        self.assertEqual(parser.armed_until, 0)

    def test_direct_mode_deduplicates_events_but_allows_intentional_repetition(self):
        parser = CommandParser(require_prefix=False)
        self.assertEqual(parser.accept("next slide", "a", 1).action, "next")
        self.assertIsNone(parser.accept("next slide", "a", 2).action)
        self.assertEqual(parser.accept("next slide", "b", 3).action, "next")

    def setUp(self):
        self.parser = CommandParser()

    def test_explicit_phrases_and_case(self):
        self.assertEqual(self.parser.accept("HEY SLIDES, next slide!", "a", 1).action, "next")
        self.assertEqual(self.parser.accept("Hey Slides, previous slide.", "b", 2).action, "previous")

    def test_plural_slide_phrases_keep_prefix_requirement(self):
        self.assertEqual(self.parser.accept("hey slides next slides", "a", 1).action, "next")
        self.assertEqual(self.parser.accept("hey slides previous slides", "b", 2).action, "previous")
        self.assertIsNone(self.parser.accept("next slides", "c", 3).action)
        self.assertIsNone(self.parser.accept("a slight max lights", "d", 4).action)

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

    def test_numbered_slide_commands(self):
        for n, (words, target) in enumerate([("five", 5), ("12", 12), ("one two", 12),
                                             ("twenty five", 25), ("nineteen", 19),
                                             ("ninety-nine", 99), ("one zero zero", 100)]):
            decision = self.parser.accept(f"Hey Slides, go to slide {words}", str(n), n + 1)
            self.assertEqual((decision.action, decision.target_slide), ("goto", target))

    def test_invalid_numbered_commands_do_not_act(self):
        for n, text in enumerate(["zero", "0", "1000", "five please", "one hundred",
                                  "minus five", "five point five", "twenty zero"]):
            self.assertIsNone(self.parser.accept(f"hey slides go to slide {text}", str(n), n + 1).action)

    def test_goto_requires_prefix_and_valid_deck_number(self):
        self.assertIsNone(self.parser.accept("go to slide five", "a", 1).action)
        deck = SlideDeck()
        self.assertTrue(deck.apply("goto", 5))
        self.assertEqual(deck.index, 4)
        for target in (0, 6, None, True):
            with self.assertRaises(ValueError):
                deck.apply("goto", target)
            self.assertEqual(deck.index, 4)


if __name__ == "__main__":
    unittest.main()
