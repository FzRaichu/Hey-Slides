"""Desktop integration smoke check; no microphone is opened.

Exercises actual Tk widgets and queued events, not speech recognition accuracy.
"""

import tkinter as tk
import numpy as np

from app.main import Prototype
from app.features import ManualMFCC


def main():
    root = tk.Tk()
    root.withdraw()
    ui = Prototype(root)
    try:
        root.update()
        ui.active_session = "test"
        ui.listening = True
        ui.session.events.put({"session_id": "test", "kind": "partial",
                               "text": "hey slides next slide", "decode_ms": 1})
        ui.poll()
        assert ui.deck.index == 0, "Partial text must never execute"
        ui.handle_final("today we explain our system", "a", "text test")
        assert ui.deck.index == 0
        ui.handle_final("hey slides next slide", "b", "text test")
        assert ui.deck.index == 1
        ui.handle_final("hey slides next slide", "b", "text test")
        assert ui.deck.index == 1, "Replayed event must not execute twice"
        ui.handle_final("hey slides previous slide", "c", "text test")
        assert ui.deck.index == 0
        ui.stop()
        ui.session.events.put({"session_id": "test", "kind": "final",
                               "text": "hey slides next slide", "utterance_id": "d",
                               "allow_action": True, "words": [], "decode_ms": 1})
        ui.poll()
        assert ui.deck.index == 0, "Queued final after Stop must not execute"
        # Events from an old session must never authorize the current session.
        ui.session.events.put({"session_id": "old", "kind": "final",
                               "text": "hey slides next slide", "utterance_id": "e",
                               "allow_action": True, "words": [], "decode_ms": 1})
        ui.poll()
        assert ui.deck.index == 0
        ui.draw_features(ManualMFCC().extract(np.zeros(16000)).mfcc)
        root.update()
        assert ui.slide_number.get() == "01 / 05"
        print("UI integration OK: partial, ordinary speech, next/previous, duplicate, Stop, stale session, heatmap")
    finally:
        ui.close()


if __name__ == "__main__":
    main()
