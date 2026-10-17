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
        actions = {"next slide": "next", "previous slide": "previous"}
        action = actions.get(command)
        return Decision("command" if action else "unrecognized command", action)


@dataclass
class SlideDeck:
    count: int = 5
    index: int = 0

    def apply(self, action: str) -> bool:
        before = self.index
        if action == "next":
            self.index = min(self.count - 1, self.index + 1)
        elif action == "previous":
            self.index = max(0, self.index - 1)
        else:
            raise ValueError(f"Unsupported action: {action}")
        return self.index != before
