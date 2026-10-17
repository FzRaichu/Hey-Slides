"""Parse completed ASR utterances; partial hypotheses must never call this module."""

from collections import deque
from dataclasses import dataclass
import re
import time

from app.config import COMMAND_PREFIX


@dataclass(frozen=True)
class Decision:
    status: str
    action: str | None = None
    target_slide: int | None = None


def slide_number(text: str) -> int | None:
    """Digits up to 999, digit-by-digit speech, or English cardinal 1..99."""
    units = dict(zip("zero one two three four five six seven eight nine".split(), range(10)))
    small = dict(zip("ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split(), range(10, 20)))
    tens = dict(zip("twenty thirty forty fifty sixty seventy eighty ninety".split(), range(20, 100, 10)))
    words = text.split()
    number = None
    if re.fullmatch(r"[0-9]{1,3}", text):
        number = int(text)
    elif 1 <= len(words) <= 3 and all(word in units for word in words):
        number = int("".join(str(units[word]) for word in words))
    elif text in small:
        number = small[text]
    elif words and words[0] in tens:
        if len(words) == 1:
            number = tens[words[0]]
        elif len(words) == 2 and words[1] in units and units[words[1]] > 0:
            number = tens[words[0]] + units[words[1]]
    return number if number is not None and 1 <= number <= 999 else None


class CommandParser:
    """Strict phrase grammar with a short window for a separately spoken prefix.

    Utterance IDs deduplicate delivery, not text: two intentionally repeated
    commands with different IDs both work. All times are monotonic seconds.
    """

    def __init__(self, wake_timeout: float = 4.0):
        self.wake_timeout = wake_timeout
        self.armed_until = 0.0
        self._seen = deque(maxlen=256)

    def reset(self):
        self.armed_until = 0.0
        self._seen.clear()

    def accept(self, text: str, utterance_id: str, now: float | None = None) -> Decision:
        now = time.monotonic() if now is None else now
        if utterance_id in self._seen:
            return Decision("duplicate")
        self._seen.append(utterance_id)
        # Preserve word boundaries, including hyphens and punctuation.
        text = " ".join(re.findall(r"[a-z0-9]+", text.lower()))
        if not text:
            return Decision("empty")
        if text == COMMAND_PREFIX:
            self.armed_until = now + self.wake_timeout
            return Decision("armed")
        prefixed = text.startswith(COMMAND_PREFIX + " ")
        if prefixed:
            command = text[len(COMMAND_PREFIX):].strip()
        elif now < self.armed_until:
            command = text
        else:
            self.armed_until = 0.0
            return Decision("ordinary speech")
        # A prefix authorizes only the following complete utterance.
        self.armed_until = 0.0
        actions = {"next slide": "next", "next slides": "next",
                   "previous slide": "previous", "previous slides": "previous"}
        action = actions.get(command)
        if command.startswith("go to slide "):
            target = slide_number(command[len("go to slide "):])
            if target is not None:
                return Decision("command", "goto", target)
        return Decision("command" if action else "unrecognized command", action)


@dataclass
class SlideDeck:
    count: int = 5
    index: int = 0

    def apply(self, action: str, target_slide: int | None = None) -> bool:
        before = self.index
        if action == "next":
            self.index = min(self.count - 1, self.index + 1)
        elif action == "previous":
            self.index = max(0, self.index - 1)
        elif action == "goto":
            if type(target_slide) is not int or not 1 <= target_slide <= self.count:
                raise ValueError(f"Slide number must be between 1 and {self.count}.")
            self.index = target_slide - 1
        else:
            raise ValueError(f"Unsupported action: {action}")
        return self.index != before
