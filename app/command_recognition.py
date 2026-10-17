"""Experimental constrained decoder alongside, never instead of, full transcription.

Confidence scores are model outputs, not calibrated probabilities or guarantees
of intent. Unknown/filler tokens and low-score hypotheses cannot authorize actions.
"""

import math
from statistics import mean

from app.config import COMMAND_PREFIXES
from app.recognition import StreamingRecognizer


def command_grammar():
    units = "zero one two three four five six seven eight nine".split()
    small = "ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
    tens = "twenty thirty forty fifty sixty seventy eighty ninety".split()
    numbers = units[1:] + small + tens + [f"{ten} {one}" for ten in tens for one in units[1:]]
    # These digit sequences expose zero and repeated-digit transitions too.
    numbers += ["one zero", "one one", "one zero zero"]
    commands = ["next slide", "next slides", "previous slide", "previous slides"]
    commands += [f"go to slide {number}" for number in numbers]
    phrases = ["[unk]", *COMMAND_PREFIXES, *commands]
    phrases += [f"{prefix} {command}" for prefix in COMMAND_PREFIXES for command in commands]
    return list(dict.fromkeys(phrases))


def assess_candidate(event, minimum_word_score=0.55, minimum_mean_score=0.80):
    text = event.get("text", "").strip()
    if not text:
        return {"eligible": False, "reason": "empty", "mean_score": None}
    if "[unk]" in text or any(word.get("word") == "[unk]" for word in event.get("words", [])):
        return {"eligible": False, "reason": "unknown audio", "mean_score": None}
    words = event.get("words", [])
    scores = [float(word.get("conf", 0)) for word in words]
    if not scores or len(words) != len(text.split()) or not all(math.isfinite(score) and 0 <= score <= 1 for score in scores):
        return {"eligible": False, "reason": "missing word scores", "mean_score": None}
    average = mean(scores)
    eligible = min(scores) >= minimum_word_score and average >= minimum_mean_score
    return {"eligible": eligible, "reason": "candidate" if eligible else "low model score",
            "mean_score": average, "minimum_score": min(scores)}


class CommandRecognizer:
    def __init__(self, model, sample_rate=16000):
        self.model = model
        self.sample_rate = sample_rate
        self.reset()

    def reset(self):
        self.decoder = StreamingRecognizer(self.model, self.sample_rate, grammar=command_grammar())

    def feed(self, pcm):
        event = self.decoder.feed(pcm)
        if event["kind"] == "final":
            event.update(assess_candidate(event))
        return event

    def finish(self):
        event = self.decoder.finish()
        event.update(assess_candidate(event))
        return event


def align_command_endpoint(general_event, command_event, recognizer):
    """Do not carry rejected ordinary speech into the next spoken command.

    The free recognizer's completed-utterance boundary also closes the focused
    segment. An already completed focused result is retained, not emitted twice.
    """
    if general_event["kind"] == "final":
        if command_event["kind"] != "final" or not command_event["text"]:
            command_event = recognizer.finish()
        recognizer.reset()
    return command_event
