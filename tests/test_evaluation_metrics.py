import unittest

from scripts.evaluation_metrics import word_errors
from scripts.benchmark_recognizers import score_reference


class EvaluationMetricTests(unittest.TestCase):
    def test_unverified_or_partial_reference_never_receives_wer(self):
        hypotheses = {"general": "hello world"}
        for reference in ({}, {"text": "hello", "confirmed": True},
                          {"text": "hello", "complete": True}):
            self.assertIsNone(score_reference(reference, hypotheses))
        result = score_reference({"text": "hello world", "confirmed": True, "complete": True}, hypotheses)
        self.assertEqual(result["general"]["wer"], 0)

    def test_separate_substitution_deletion_and_insertion(self):
        self.assertEqual(word_errors("hey slide next slide", "hey slide next line")["substitutions"], 1)
        self.assertEqual(word_errors("hey slide next slide", "slide next slide")["deletions"], 1)
        self.assertEqual(word_errors("next slide", "hey next slide")["insertions"], 1)

    def test_normalization_does_not_hide_number_or_plural_errors(self):
        self.assertEqual(word_errors("Hey Slide, next slide!", "hey slide next slide")["wer"], 0)
        self.assertEqual(word_errors("slide seven", "slides 7")["substitutions"], 2)

    def test_repetitions_and_wer_above_one_are_not_clamped(self):
        result = word_errors("next slide next slide", "next slide")
        self.assertEqual(result["deletions"], 2)
        self.assertEqual(word_errors("slide", "hey next slide now")["wer"], 3)
        with self.assertRaises(ValueError):
            word_errors("", "slide")


if __name__ == "__main__":
    unittest.main()
