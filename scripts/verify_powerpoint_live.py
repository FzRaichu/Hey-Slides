"""Opt-in integration check against real Windows PowerPoint.

python -m scripts.verify_powerpoint_live --run
Refuses to run if PowerPoint is already running. Creates only an unsaved blank
test presentation, closes that fixture afterward, and never touches user files.
"""

import argparse
from dataclasses import asdict
import json
import subprocess

from app.commands import CommandParser
from app.powerpoint import PowerPointAdapter, PowerPointError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Create and remove an unsaved PowerPoint test fixture")
    args = parser.parse_args()
    if not args.run:
        parser.error("Pass --run to explicitly enable the real Office integration check")
    tasks = subprocess.run(["tasklist", "/FI", "IMAGENAME eq POWERPNT.EXE", "/FO", "CSV", "/NH"],
                           capture_output=True, text=True, check=True)
    if "powerpnt.exe" in tasks.stdout.lower():
        raise RuntimeError("Close PowerPoint before this isolated test, or test manually with your own presentation.")
    import win32com.client
    app = win32com.client.DispatchEx("PowerPoint.Application")
    presentation = window = None
    owns_app = int(app.Presentations.Count) == 0
    if not owns_app:
        raise RuntimeError("PowerPoint has open presentations. Test aborted without closing or changing them.")
    try:
        presentation = app.Presentations.Add(0)
        for index in range(1, 5):
            presentation.Slides.Add(index, 12)  # ppLayoutBlank: a fixture, not a deliverable deck
        presentation.Slides.Item(2).SlideShowTransition.Hidden = -1
        presentation.SlideShowSettings.RangeType = 1
        presentation.SlideShowSettings.ShowType = 2  # windowed slideshow
        window = presentation.SlideShowSettings.Run()
        adapter = PowerPointAdapter()
        initial = adapter.connect()  # Uses real GetActiveObject, not injected test doubles.
        assert initial.slide == 1, initial
        commands = CommandParser()
        results = []
        for index, (phrase, expected) in enumerate([
            ("hey slides next slide", 3),  # hidden slide 2 is skipped
            ("hey slides previous slide", 1),
            ("hey slides go to slide four", 4),
            ("hey slides next slide", 4),  # last slide stays open
        ]):
            decision = commands.accept(phrase, str(index))
            result = adapter.apply(decision.action, decision.target_slide)
            assert result.state.slide == expected, result
            results.append({"phrase": phrase, "expected_slide": expected, **asdict(result)})
        window.View.Exit()
        window = None
        try:
            adapter.apply("previous")
        except PowerPointError:
            pass
        else:
            raise AssertionError("An ended show must require reconnect")
        adapter.disconnect()
        print(json.dumps({"result": "passed", "checks": results,
                          "closed_show_rejected": True,
                          "timing_note": "Adapter call/read-back only; not acoustic or screen-render latency."}, indent=2))
    finally:
        if window is not None:
            try:
                window.View.Exit()
            except Exception:
                pass
        if presentation is not None:
            try:
                # A hidden unsaved presentation may already close on View.Exit.
                presentation.Saved = -1
                presentation.Close()
            except Exception:
                pass
        if owns_app:
            try:
                app.Quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()
