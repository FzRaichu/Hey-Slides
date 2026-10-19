import unittest
from unittest.mock import MagicMock, patch

from app.command_recognition import assess_candidate, command_grammar, align_command_endpoint, CommandRecognizer
from app.commands import CommandParser


def candidate(text, score=0.95):
    return {"text": text, "words": [{"word": word, "conf": score} for word in text.split()]}


class FocusedRecognitionTests(unittest.TestCase):
    def test_direct_grammar_has_commands_and_unknown_without_wake_phrases(self):
        grammar = command_grammar(require_prefix=False)
        for phrase in ("[unk]", "next slide", "next slides", "previous slides", "go to slides seven"):
            self.assertIn(phrase, grammar)
        self.assertFalse(any("hey" in phrase for phrase in grammar))

    def test_direct_decoder_reset_retains_grammar_and_score_checks(self):
        with patch("app.command_recognition.StreamingRecognizer") as decoder:
            focused = CommandRecognizer(object(), require_prefix=False)
            focused.reset()
            for call in decoder.call_args_list:
                self.assertEqual(call.kwargs["grammar"], command_grammar(False))
            decoder.return_value.feed.return_value = {"kind": "final", **candidate("next slide", 0.4)}
            self.assertFalse(focused.feed(b"pcm")["eligible"])

    def test_shared_endpoint_flushes_partial_and_clears_old_unknown_context(self):
        decoder = MagicMock()
        flushed = {"kind": "final", "text": "hey slides next slide"}
        decoder.finish.return_value = flushed
        self.assertIs(align_command_endpoint({"kind": "final"}, {"kind": "partial"}, decoder), flushed)
        decoder.reset.assert_called_once()

    def test_shared_endpoint_keeps_completed_candidate_without_duplicate_flush(self):
        decoder = MagicMock()
        event = {"kind": "final", "text": "hey slides next slide"}
        self.assertIs(align_command_endpoint({"kind": "final"}, event, decoder), event)
        decoder.finish.assert_not_called()
        decoder.reset.assert_called_once()

    def test_grammar_has_unknown_and_both_prefixes(self):
        grammar = command_grammar()
        for phrase in ("[unk]", "hey slides", "hey slide", "hey slides next slide",
                       "hey slide previous slides", "hey slides go to slide twenty five"):
            self.assertIn(phrase, grammar)
        self.assertEqual(len(grammar), len(set(grammar)))

    def test_unknown_cannot_authorize_even_with_high_scores(self):
        self.assertFalse(assess_candidate(candidate("[unk] hey slides next slide"))["eligible"])

    def test_low_and_invalid_scores_rejected(self):
        for score in (0.4, float("nan"), float("inf"), 1.1, -1):
            self.assertFalse(assess_candidate(candidate("hey slides next slide", score))["eligible"])
        self.assertFalse(assess_candidate({"text": "hey slides", "words": []})["eligible"])

    def test_one_weak_word_is_not_hidden_by_high_mean(self):
        event = candidate("hey slides next slide", 1)
        event["words"][0]["conf"] = 0.4
        self.assertFalse(assess_candidate(event)["eligible"])

    def test_focused_candidate_still_needs_valid_grammar_and_prefix(self):
        parser = CommandParser()
        event = candidate("next slide")
        self.assertTrue(assess_candidate(event)["eligible"])
        self.assertIsNone(parser.accept(event["text"], "a", 1).action)
        self.assertEqual(parser.accept("hey slide next slides", "b", 2).action, "next")
        self.assertIsNone(parser.accept("hey slides next slide do not", "c", 3).action)

    def test_disarm_preserves_deduplication(self):
        parser = CommandParser()
        self.assertEqual(parser.accept("hey slides next slide", "a", 1).action, "next")
        parser.disarm()
        self.assertIsNone(parser.accept("hey slides next slide", "a", 2).action)
