"""Check actual demo layout at laptop sizes. No microphone or Office is opened.

--capture writes a Windows render of this test window only (simulated UI events).
It never captures other windows or uses a real user's speech.
"""

import argparse
from pathlib import Path
import tkinter as tk

import numpy as np

from app.features import ManualMFCC
from app.main import Prototype


def within(widget, root):
    x = widget.winfo_rootx() - root.winfo_rootx()
    y = widget.winfo_rooty() - root.winfo_rooty()
    assert widget.winfo_ismapped(), str(widget)
    assert 0 <= x and 0 <= y, (str(widget), x, y)
    assert x + widget.winfo_width() <= root.winfo_width() + 1, str(widget)
    assert y + widget.winfo_height() <= root.winfo_height() + 1, str(widget)


def capture_window(root, path):
    import ctypes
    import struct
    import zlib
    import win32gui
    import win32ui

    hwnd = win32gui.GetParent(root.winfo_id())
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width, height = right - left, bottom - top
    dc = win32gui.GetWindowDC(hwnd)
    source = win32ui.CreateDCFromHandle(dc)
    memory = source.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(source, width, height)
    previous = memory.SelectObject(bitmap)
    try:
        if not ctypes.windll.user32.PrintWindow(hwnd, memory.GetSafeHdc(), 2):
            raise RuntimeError("Could not render test window")
        pixels = np.frombuffer(bitmap.GetBitmapBits(True), dtype=np.uint8).reshape(height, width, 4)
        rgb = pixels[:, :, [2, 1, 0]]
        scanlines = b"".join(b"\0" + row.tobytes() for row in rgb)

        def chunk(kind, content):
            return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", zlib.crc32(kind + content) & 0xFFFFFFFF)

        png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(scanlines)) + chunk(b"IEND", b"")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(png)
    finally:
        memory.SelectObject(previous)
        win32gui.DeleteObject(bitmap.GetHandle())
        memory.DeleteDC()
        source.DeleteDC()
        win32gui.ReleaseDC(hwnd, dc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path)
    args = parser.parse_args()
    root = tk.Tk()
    root.withdraw()
    ui = Prototype(root)
    try:
        assert str(ui.settings_dialog.state()) == "withdrawn"
        assert not ui.parser.require_prefix and ui.command_assist.get()
        assert not ui.record_audio.get()
        assert "Belum ada model pengenal" in ui.mfcc_explanation.cget("text")
        root.deiconify()
        root.title("Voice Slide Control | UI QA - data simulasi, bukan uji suara")
        ui.active_session = "layout-test"
        ui.handle_final("Contoh tampilan (simulasi).",
                        "layout-text", "text test", allow_action=False, transcript_only=True)
        result = ManualMFCC().extract(0.2 * np.sin(2 * np.pi * 440 * np.arange(16000) / 16000))
        before = ui.deck.index
        ui.session.events.put({"kind": "features", "session_id": "layout-test", "mfcc": result.mfcc,
                               "vector": result.vector, "rms": result.rms, "peak": 0.2,
                               "clipped_fraction": 0.0, "mfcc_ms": 1.0})
        ui.poll()
        assert ui.deck.index == before, "Feature output must not navigate"
        assert "156" in ui.feature_values.get() and len(ui.heatmap.find_all()) > 0
        assert str(ui.save_features_button.cget("state")) == "normal"
        assert np.array_equal(ui.last_vector, result.vector)
        for width, height in ((960, 660), (1120, 740)):
            root.geometry(f"{width}x{height}+30+30")
            root.update()
            for widget in (ui.start_button, ui.stop_button, ui.target_box, ui.settings_button,
                           ui.pretrained_panel, ui.mfcc_panel, ui.transcript, ui.heatmap,
                           ui.feature_values_label, ui.mfcc_explanation,
                           ui.previous_button, ui.next_button, ui.actions):
                within(widget, root)
            for label in (ui.mfcc_explanation, ui.feature_values_label):
                assert label.winfo_height() >= label.winfo_reqheight(), "Clipped explanatory text"
                within(label, ui.mfcc_panel)
            within(ui.heatmap, ui.mfcc_panel)
            within(ui.transcript, ui.pretrained_panel)
            within(ui.command_label, ui.pretrained_panel)
            assert not ui.connect_button.winfo_ismapped()
            assert not ui.model_box.winfo_ismapped(), "Advanced selectors must stay off the demo screen"
            print(f"Demo layout OK at {width}x{height}")
            if args.capture:
                capture_window(root, args.capture.with_stem(f"{args.capture.stem}-{width}x{height}"))
        if args.capture:
            capture_window(root, args.capture)
            print(f"Saved test-window render: {args.capture}")
        ui.show_settings()
        root.update()
        for widget in (ui.device_box, ui.model_box, ui.mode_box, ui.assist_check, ui.record_check, ui.play_button):
            within(widget, ui.settings_dialog)
        if args.capture:
            capture_window(ui.settings_dialog, args.capture.with_stem(f"{args.capture.stem}-settings"))
        ui.settings_tabs.select(1)
        root.update()
        within(ui.test_input, ui.settings_dialog)
        within(ui.save_features_button, ui.settings_dialog)
        if args.capture:
            capture_window(ui.settings_dialog, args.capture.with_stem(f"{args.capture.stem}-diagnostics"))
        ui.hide_settings()
        root.update()
        assert str(ui.settings_dialog.state()) == "withdrawn"
        print("Settings/diagnostics OK; no audio capture or presentation actions executed")
    finally:
        ui.close()


if __name__ == "__main__":
    main()
