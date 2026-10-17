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
        ui.handle_final("hey slides next slide", "transcript-only", "microphone", allow_action=False, transcript_only=True)
        assert ui.deck.index == 0
        ui.session.events.put({"session_id": "test", "kind": "command_final", "text": "hey slide next slide",
                               "utterance_id": "focused", "allow_action": True, "eligible": True,
                               "reason": "candidate", "mean_score": 0.95, "words": [], "decode_ms": 1})
        ui.poll()
        assert ui.deck.index == 1
        ui.session.events.put({"session_id": "test", "kind": "command_final", "text": "hey slides next slide",
                               "utterance_id": "rejected-focused", "allow_action": True, "eligible": False,
                               "reason": "low model score", "mean_score": 0.4, "words": [], "decode_ms": 1})
        ui.poll()
        assert ui.deck.index == 1
        ui.deck.index = 0
        ui.show_slide()
        ui.handle_final("hey slides go to slide five", "goto", "text test")
        assert ui.deck.index == 4
        ui.handle_final("hey slides go to slide 99", "invalid-goto", "text test")
        assert ui.deck.index == 4
        ui.manual_action("previous")
        ui.deck.index = 0
        ui.show_slide()
        ui.stop()
        ui.session.events.put({"session_id": "test", "kind": "final",
                               "text": "hey slides next slide", "utterance_id": "d",
                               "allow_action": True, "words": [], "decode_ms": 1})
        ui.poll()
        assert ui.deck.index == 0, "Queued final after Stop must not execute"
        ui.session.events.put({"session_id": "test", "kind": "command_final", "text": "hey slides next slide",
                               "utterance_id": "focused-after-stop", "allow_action": True, "eligible": True,
                               "reason": "candidate", "mean_score": 0.95, "words": [], "decode_ms": 1})
        ui.poll()
        assert ui.deck.index == 0, "Queued focused command after Stop must not execute"
        # Events from an old session must never authorize the current session.
        ui.session.events.put({"session_id": "old", "kind": "final",
                               "text": "hey slides next slide", "utterance_id": "e",
                               "allow_action": True, "words": [], "decode_ms": 1})
        ui.poll()
        assert ui.deck.index == 0
        ui.draw_features(ManualMFCC().extract(np.zeros(16000)).mfcc)
        result = ManualMFCC().extract(np.zeros(16000))
        ui.session.events.put({"session_id": "test", "kind": "features", "mfcc": result.mfcc,
                               "vector": result.vector, "rms": 0.2, "peak": 1.0,
                               "clipped_fraction": 0.02, "mfcc_ms": 1.0})
        ui.poll()
        assert "clipping" in ui.audio_quality.get()
        root.update()
        assert ui.slide_number.get() == "01 / 05"
        # Explicit PowerPoint target with a deterministic injected COM-like fixture.
        from app.powerpoint import PowerPointAdapter
        from tests.test_powerpoint import fake_application
        fake_app, window = fake_application()
        ui.powerpoint = PowerPointAdapter(lambda: fake_app)
        ui.connect_powerpoint()
        assert ui.target.get() == "PowerPoint"
        ui.handle_final("hey slides next slide", "ppt-next", "text test")
        assert window.View.index == 2 and ui.deck.index == 0
        ui.handle_final("hey slides go to slide four", "ppt-goto", "text test")
        assert window.View.index == 4 and ui.slide_number.get() == "04 / 05"
        fake_app.SlideShowWindows.items = []  # show closed
        ui.handle_final("hey slides next slide", "ppt-closed", "text test")
        assert window.View.index == 4 and ui.deck.index == 0
        assert ui.powerpoint_state is None
        ui.listening = True
        ui.target.set("Demo slides")
        ui.change_target()
        assert not ui.listening and ui.parser.armed_until == 0
        print("UI integration OK: transcription, parser, Stop, stale events, heatmap, goto, PowerPoint routing/failure, target changes")
    finally:
        ui.close()


if __name__ == "__main__":
    main()
