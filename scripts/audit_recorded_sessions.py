"""Audit voice actions for saved real sessions; exclude buttons and text tests."""

import argparse
import json
from pathlib import Path


def audit(rows):
    sessions = []
    current = None
    for row in rows:
        if row["kind"] == "start":
            current = {"session_id": row["session_id"], "start": row["at"],
                       "model_profile": row.get("model_profile"), "actions": [],
                       "decisions": [], "max_clipped_fraction": 0.0}
        elif current is not None:
            kind = row["kind"]
            if kind in ("slide_action", "slide_action_failed") and row.get("source") in ("command recognizer", "microphone"):
                current["actions"].append(row)
            elif kind == "command_decision" and row.get("utterance_id", "").startswith(current["session_id"] + ":"):
                current["decisions"].append(row)
            elif kind == "audio_quality":
                current["max_clipped_fraction"] = max(current["max_clipped_fraction"], row.get("clipped_fraction", 0))
            elif kind == "recording_saved":
                if Path(row["path"]).stem == "input-" + current["session_id"]:
                    current.update(recording=row["path"], audio_seconds=row["seconds"],
                                   interrupted=row.get("interrupted"), end=row["at"])
                    sessions.append(current)
                current = None
            elif kind == "stopped":
                current = None
    return sessions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("logs/recorded-session-audit.json"))
    args = parser.parse_args()
    sessions = []
    for path in args.jsonl:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        for session in audit(rows):
            session["log_source"] = str(path.resolve())
            sessions.append(session)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(sessions, indent=2) + "\n", encoding="utf-8")
    for session in sessions:
        actions = [(row["action"], row.get("target_slide")) for row in session["actions"] if row["kind"] == "slide_action"]
        print(session["session_id"][:8], session["audio_seconds"], actions)


if __name__ == "__main__":
    main()
