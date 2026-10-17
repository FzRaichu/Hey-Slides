import unittest

from scripts.audit_recorded_sessions import audit


class SessionAuditTests(unittest.TestCase):
    def test_only_saved_matching_session_and_voice_actions_count(self):
        rows = [{"kind": "slide_action", "source": "command recognizer"},
                {"kind": "start", "at": "a", "session_id": "one"},
                {"kind": "slide_action", "source": "text test"},
                {"kind": "slide_action", "source": "button"},
                {"kind": "slide_action", "source": "command recognizer", "action": "next"},
                {"kind": "command_decision", "utterance_id": "old:command:1"},
                {"kind": "recording_saved", "path": "input-one.wav", "seconds": 3, "at": "b"},
                {"kind": "slide_action", "source": "command recognizer"}]
        sessions = audit(rows)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(len(sessions[0]["actions"]), 1)
        self.assertEqual(sessions[0]["decisions"], [])

    def test_mismatched_or_unsaved_session_not_reported(self):
        rows = [{"kind": "start", "at": "a", "session_id": "one"},
                {"kind": "recording_saved", "path": "input-other.wav", "seconds": 3, "at": "b"}]
        self.assertEqual(audit(rows), [])


if __name__ == "__main__":
    unittest.main()
