"""Run with python -m app.main. Desktop prototype; no network service required."""

from datetime import datetime
import json
import queue
import tkinter as tk
from tkinter import ttk
import uuid

import numpy as np

from app import config
from app.commands import CommandParser, SlideDeck
from app.powerpoint import PowerPointAdapter, PowerPointError, PowerPointCommandError
from app.session import MicrophoneSession


SLIDES = [
    ("A voice for your slides.", "Voice Slide Control", "Speak naturally. Use Hey Slides when you want to navigate."),
    ("From speech to text.", "01 / Local recognition", "The English ASR model runs on your computer. Ordinary speech stays in the transcript."),
    ("A phrase with a purpose.", "02 / Intentional commands", "Say Hey Slides, next slide or Hey Slides, previous slide. Completed phrases trigger one action."),
    ("See the signal.", "03 / Manual MFCC analysis", "Our NumPy pipeline extracts MFCC features separately. Vosk uses its own internal feature pipeline."),
    ("Measure, then improve.", "04 / Evaluation ahead", "Recognition accuracy, false activations, user testing, and the 200 ms target still need evaluation."),
]

BG, CARD, INK, MUTED, ACCENT = "#edf1f5", "#ffffff", "#14273c", "#53697e", "#087f78"


class Prototype:
    def __init__(self, root, powerpoint=None):
        self.root = root
        root.title("Hey Slides | University Speech Recognition Prototype")
        root.geometry("1180x850")
        root.minsize(980, 760)
        root.configure(bg=BG)
        self.parser = CommandParser()
        self.deck = SlideDeck(count=len(SLIDES))
        self.powerpoint = powerpoint or PowerPointAdapter()
        self.powerpoint_state = None
        self.target = tk.StringVar(value="Demo slides")
        self.session = MicrophoneSession()
        self.listening = False
        self.active_session = ""
        self.last_vector = None
        self.status = tk.StringVar(value="Ready | microphone is off")
        self.partial = tk.StringVar(value="Partial recognition will appear here...")
        self.command_status = tk.StringVar(value="Command prefix: Hey Slides")
        self.timing = tk.StringVar(value="Decode: -- | MFCC: -- | queue: --")
        self.feature_status = tk.StringVar(value="Manual MFCC analysis | waiting for audio")
        self.slide_number = tk.StringVar()
        self.devices = {"Default microphone": None}
        self.device = tk.StringVar(value="Default microphone")
        self.model_profile = tk.StringVar(value=config.MODEL_PROFILES[config.DEFAULT_MODEL_PROFILE]["label"])
        self.audio_quality = tk.StringVar(value="Input level: -- | microphone is off")
        self._log_file = None
        self._build()
        self.show_slide()
        self.refresh_devices()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(50, self.poll)

    def _build(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
        style.configure("Accent.TButton", background=ACCENT, foreground="white")
        style.configure("TCombobox", padding=6)
        outer = tk.Frame(self.root, bg=BG, padx=26, pady=18)
        outer.pack(fill="both", expand=True)
        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x")
        tk.Label(header, text="Hey Slides", bg=BG, fg=INK, font=("Segoe UI", 25, "bold")).pack(side="left")
        tk.Label(header, text="LOCAL SPEECH RECOGNITION / PROTOTYPE", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(side="right")
        tk.Label(outer, textvariable=self.status, anchor="w", bg=BG, fg=ACCENT,
                 font=("Segoe UI", 11)).pack(fill="x", pady=(4, 12))
        controls = tk.Frame(outer, bg=BG)
        controls.pack(fill="x", pady=(0, 14))
        self.start_button = ttk.Button(controls, text="Start listening", command=self.start, style="Accent.TButton")
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(controls, text="Stop", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=8)
        self.device_box = ttk.Combobox(controls, textvariable=self.device, state="readonly", width=41)
        self.device_box.pack(side="left", padx=(8, 5))
        self.refresh_button = ttk.Button(controls, text="Refresh inputs", command=self.refresh_devices)
        self.refresh_button.pack(side="left")
        tk.Label(controls, text="English / offline", bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(side="right")
        target_controls = tk.Frame(outer, bg=BG)
        target_controls.pack(fill="x", pady=(0, 10))
        tk.Label(target_controls, text="Control target", bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        self.target_box = ttk.Combobox(target_controls, textvariable=self.target, state="readonly",
                                      values=("Demo slides", "PowerPoint"), width=17)
        self.target_box.pack(side="left")
        self.target_box.bind("<<ComboboxSelected>>", lambda event: self.change_target())
        self.connect_button = ttk.Button(target_controls, text="Connect / refresh PowerPoint", command=self.connect_powerpoint)
        self.connect_button.pack(side="left", padx=8)
        tk.Label(target_controls, text="Open a slideshow first. Target changes stop listening.", bg=BG,
                 fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
        model_controls = tk.Frame(outer, bg=BG)
        model_controls.pack(fill="x", pady=(0, 10))
        tk.Label(model_controls, text="ASR model", bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        self.model_box = ttk.Combobox(model_controls, textvariable=self.model_profile, state="readonly", width=27,
                                     values=[item["label"] for item in config.MODEL_PROFILES.values()])
        self.model_box.pack(side="left")
        tk.Label(model_controls, textvariable=self.audio_quality, bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=12)
        body = tk.Frame(outer, bg=BG)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=6, uniform="body")
        body.columnconfigure(1, weight=5, uniform="body")
        body.rowconfigure(0, weight=1)
        left = tk.Frame(body, bg=INK, padx=24, pady=22)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.preview_caption = tk.Label(left, text="PRESENTATION PREVIEW", bg=INK, fg="#6dd8ca", font=("Segoe UI", 9, "bold"))
        self.preview_caption.pack(anchor="w")
        self.slide_kicker = tk.Label(left, bg=INK, fg="#a7bbcf", font=("Segoe UI", 11), anchor="w")
        self.slide_kicker.pack(fill="x", pady=(30, 14))
        self.slide_title = tk.Label(left, bg=INK, fg="white", font=("Segoe UI", 29, "bold"), anchor="w", justify="left")
        self.slide_title.pack(fill="x")
        self.slide_body = tk.Label(left, bg=INK, fg="#d4e1ec", font=("Segoe UI", 13), justify="left", anchor="nw")
        self.slide_body.pack(fill="both", expand=True, pady=(18, 20))
        left.bind("<Configure>", lambda e: (self.slide_title.configure(wraplength=max(280, e.width - 48)),
                                           self.slide_body.configure(wraplength=max(280, e.width - 48))))
        nav = tk.Frame(left, bg=INK)
        nav.pack(fill="x")
        ttk.Button(nav, text="Previous", command=lambda: self.manual_action("previous")).pack(side="left")
        tk.Label(nav, textvariable=self.slide_number, bg=INK, fg="white", font=("Segoe UI", 11)).pack(side="left", expand=True)
        ttk.Button(nav, text="Next", command=lambda: self.manual_action("next")).pack(side="right")
        right = tk.Frame(body, bg=CARD, padx=18, pady=16)
        right.grid(row=0, column=1, sticky="nsew")
        tk.Label(right, text="LIVE TRANSCRIPT", bg=CARD, fg=INK, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(right, textvariable=self.partial, bg=CARD, fg=ACCENT, font=("Segoe UI", 11, "italic"),
                 justify="left", anchor="w", wraplength=390).pack(fill="x", pady=(8, 10))
        transcript_frame = tk.Frame(right, bg=CARD)
        transcript_frame.pack(fill="both", expand=True)
        self.transcript = tk.Text(transcript_frame, height=9, width=35, wrap="word", state="disabled",
                                  bg="#f6f8fa", fg=INK, relief="flat", font=("Segoe UI", 11), padx=10, pady=10)
        scrollbar = ttk.Scrollbar(transcript_frame, command=self.transcript.yview)
        self.transcript.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.transcript.pack(side="left", fill="both", expand=True)
        tk.Label(right, textvariable=self.command_status, bg=CARD, fg=ACCENT, font=("Segoe UI", 10),
                 wraplength=390, justify="left", anchor="w").pack(fill="x", pady=(10, 6))
        tk.Label(right, text="ACTION HISTORY", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.actions = tk.Listbox(right, height=3, bg=CARD, fg=INK, relief="flat", font=("Segoe UI", 10), selectborderwidth=0)
        self.actions.pack(fill="x", pady=(4, 0))
        signal = tk.Frame(outer, bg=CARD, padx=16, pady=10)
        signal.pack(fill="x", pady=(14, 0))
        signal_head = tk.Frame(signal, bg=CARD)
        signal_head.pack(fill="x")
        tk.Label(signal_head, textvariable=self.feature_status, bg=CARD, fg=INK, font=("Segoe UI", 10)).pack(side="left")
        ttk.Button(signal_head, text="Save feature vector", command=self.save_features).pack(side="right")
        self.heatmap = tk.Canvas(signal, height=75, bg=INK, highlightthickness=0)
        self.heatmap.pack(fill="x", pady=(6, 5))
        tk.Label(signal, text="Separate analysis branch; these extracted features are not fed into Vosk.",
                 bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
        test = tk.Frame(outer, bg=BG)
        test.pack(fill="x", pady=(12, 4))
        tk.Label(test, text="Text-only parser check (bypasses ASR):", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
        self.test_input = ttk.Entry(test, width=31, font=("Segoe UI", 10))
        self.test_input.insert(0, "Hey Slides, next slide")
        self.test_input.pack(side="left", fill="x", expand=True, padx=9)
        self.test_input.bind("<Return>", lambda event: self.test_phrase())
        ttk.Button(test, text="Test phrase", command=self.test_phrase).pack(side="right")
        tk.Label(outer, textvariable=self.timing, bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w").pack(fill="x")
        tk.Label(outer, text="Call timings are processing measurements, not word-to-screen latency. The 200 ms target is not yet validated.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w").pack(fill="x", pady=(3, 0))

    def log(self, kind, **data):
        try:
            if self._log_file is None:
                config.LOG_DIR.mkdir(parents=True, exist_ok=True)
                path = config.LOG_DIR / f"session-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}.jsonl"
                self._log_file = path.open("a", encoding="utf-8")
            self._log_file.write(json.dumps({"at": datetime.now().isoformat(), "kind": kind, **data}) + "\n")
            self._log_file.flush()
        except OSError as exc:
            self.status.set(f"Log could not be written: {exc}")

    def refresh_devices(self):
        try:
            import sounddevice as sd
            self.devices = {"Default microphone": None}
            for index, device in enumerate(sd.query_devices()):
                if device["max_input_channels"] > 0:
                    self.devices[f"{index}: {device['name']}"] = index
            self.device_box["values"] = list(self.devices)
            if self.device.get() not in self.devices:
                self.device.set("Default microphone")
        except Exception as exc:
            self.status.set(f"Microphone unavailable: {exc}. Text-only checks still work.")

    def start(self):
        try:
            if self.target.get() == "PowerPoint":
                self.powerpoint_state = self.powerpoint.snapshot()
                self.show_slide()
            self.parser.reset()
            profile = next(key for key, item in config.MODEL_PROFILES.items() if item["label"] == self.model_profile.get())
            self.session.start(self.devices.get(self.device.get()), model_profile=profile)
            self.active_session = self.session.session_id
            self.listening = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.device_box.configure(state="disabled")
            self.refresh_button.configure(state="disabled")
            self.model_box.configure(state="disabled")
            self.status.set("Starting microphone...")
            self.command_status.set("Command prefix: Hey Slides")
            self.log("start", device=self.device.get(), model_profile=profile, session_id=self.active_session)
        except Exception as exc:
            if isinstance(exc, PowerPointError):
                self.powerpoint_state = None
                self.show_slide()
            self.status.set(str(exc))

    def change_target(self):
        if self.listening:
            self.stop()
        self.parser.reset()
        self.powerpoint.disconnect()
        self.powerpoint_state = None
        self.show_slide()
        self.command_status.set(f"Target: {self.target.get()} | command authorization reset")
        self.log("target_changed", target=self.target.get())

    def connect_powerpoint(self):
        if self.target.get() != "PowerPoint":
            self.target.set("PowerPoint")
            self.change_target()
        # Rebinding also invalidates microphone input captured for the previous show.
        if self.listening:
            self.stop()
        self.parser.reset()
        try:
            self.powerpoint_state = self.powerpoint.connect()
            self.status.set(f"Connected: {self.powerpoint_state.name} | microphone is off")
            self.command_status.set("PowerPoint ready | click Start listening")
            self.log("powerpoint_connected", presentation=self.powerpoint_state.name,
                     slide=self.powerpoint_state.slide, count=self.powerpoint_state.count)
        except PowerPointError as exc:
            self.powerpoint_state = None
            self.status.set(str(exc))
            self.command_status.set("PowerPoint not connected | no action will be sent")
            self.log("powerpoint_error", text=str(exc))
        self.show_slide()

    def stop(self):
        self.listening = False
        self.parser.reset()
        self.session.stop()
        self.stop_button.configure(state="disabled")
        self.command_status.set("Commands disabled | microphone stopping")
        self.status.set("Stopping microphone...")
        self.log("stop_requested")

    def poll(self):
        try:
            for _ in range(200):
                event = self.session.events.get_nowait()
                if event["session_id"] != self.active_session:
                    continue
                kind = event["kind"]
                if kind == "status":
                    if self.listening:
                        self.status.set(event["text"])
                elif kind == "partial":
                    self.partial.set(event["text"] or "Listening...")
                    self._update_timing(event)
                elif kind == "final":
                    self.partial.set("Listening..." if self.listening else "Microphone off")
                    if event["text"]:
                        self.handle_final(event["text"], event["utterance_id"], "microphone",
                                          allow_action=self.listening and event["allow_action"])
                        self.log("recognition", text=event["text"], words=event["words"],
                                 decode_ms=event["decode_ms"], session_id=self.active_session)
                    self._update_timing(event)
                elif kind == "features":
                    self.last_vector = event["vector"]
                    self.draw_features(event["mfcc"])
                    self.feature_status.set(f"Manual MFCC | 13 x {event['mfcc'].shape[1]} frames | 156 features | RMS {event['rms']:.4f}")
                    self._mfcc_ms = event["mfcc_ms"]
                    dbfs = 20 * np.log10(max(event["rms"], 1e-6))
                    note = "quiet / no speech" if dbfs < -40 else "level detected"
                    if event.get("clipped_fraction", 0) > 0.001:
                        note = "clipping: lower microphone gain"
                    self.audio_quality.set(f"Input: {dbfs:.0f} dBFS | {note}")
                    if getattr(self, "_last_audio_log", None) != int(datetime.now().timestamp()):
                        self._last_audio_log = int(datetime.now().timestamp())
                        self.log("audio_quality", rms=event["rms"], dbfs=float(dbfs),
                                 peak=event.get("peak"), clipped_fraction=event.get("clipped_fraction"))
                elif kind == "error":
                    self.listening = False
                    self.parser.reset()
                    self.status.set("Error: " + event["text"])
                    self.log("error", text=event["text"])
                elif kind == "stopped":
                    self.listening = False
                    self.parser.reset()
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self.device_box.configure(state="readonly")
                    self.refresh_button.configure(state="normal")
                    self.model_box.configure(state="readonly")
                    self.partial.set("Microphone off")
                    self.audio_quality.set("Input level: -- | microphone is off")
                    if not self.status.get().startswith("Error:"):
                        self.status.set("Ready | microphone is off")
        except queue.Empty:
            pass
        self.root.after(50, self.poll)

    def _update_timing(self, event):
        decode = event.get("decode_ms")
        mfcc = getattr(self, "_mfcc_ms", None)
        age = event.get("queue_ms")
        fmt = lambda x: "--" if x is None else f"{x:.1f} ms"
        self.timing.set(f"Decode call: {fmt(decode)} | MFCC analysis: {fmt(mfcc)} | audio queue: {fmt(age)}")

    def handle_final(self, text, utterance_id, source, allow_action=True):
        self.transcript.configure(state="normal")
        label = "MIC" if source == "microphone" else "TEXT TEST / not ASR"
        self.transcript.insert("end", f"[{label}] {text}\n\n")
        # Keep the visible transcript bounded; the full local log remains available.
        if int(self.transcript.index("end-1c").split(".")[0]) > 500:
            self.transcript.delete("1.0", "101.0")
        self.transcript.see("end")
        self.transcript.configure(state="disabled")
        if not allow_action:
            self.command_status.set("Transcript saved on Stop; actions disabled")
            return
        decision = self.parser.accept(text, utterance_id)
        messages = {"armed": "Hey Slides detected | say a command within 4 seconds",
                    "ordinary speech": "Ordinary speech | no slide action",
                    "unrecognized command": "Use next slide, previous slide, or go to slide five"}
        self.command_status.set(messages.get(decision.status, decision.status))
        if decision.action:
            self.apply_action(decision.action, source, decision.target_slide)
        self.log("command_decision", text=text, source=source, status=decision.status,
                 action=decision.action, target_slide=decision.target_slide, utterance_id=utterance_id)

    def apply_action(self, action, source, target_slide=None):
        target = self.target.get()
        elapsed_ms = None
        try:
            if target == "PowerPoint":
                result = self.powerpoint.apply(action, target_slide)
                self.powerpoint_state = result.state
                moved, slide, elapsed_ms = result.moved, result.state.slide, result.elapsed_ms
            else:
                moved = self.deck.apply(action, target_slide)
                slide = self.deck.index + 1
        except (PowerPointError, ValueError) as exc:
            if target == "PowerPoint" and not isinstance(exc, PowerPointCommandError):
                self.powerpoint_state = None
            self.show_slide()
            self.command_status.set(f"Action failed: {exc}")
            self.actions.insert(0, f"{datetime.now():%H:%M:%S} [{target}] FAILED: {action}")
            if self.actions.size() > 50:
                self.actions.delete(50, "end")
            self.log("slide_action_failed", target=target, action=action, source=source,
                     target_slide=target_slide, error=str(exc))
            return
        self.show_slide()
        text = f"{action.upper()} -> slide {slide}" + ("" if moved else " (unchanged)")
        self.command_status.set(text)
        self.actions.insert(0, f"{datetime.now():%H:%M:%S}  [{target}/{source}]  {text}")
        if self.actions.size() > 50:
            self.actions.delete(50, "end")
        self.log("slide_action", target=target, action=action, source=source, slide=slide, moved=moved,
                 target_slide=target_slide, adapter_ms=elapsed_ms,
                 verification="PowerPoint slide-index read-back" if target == "PowerPoint" else "internal state")

    def manual_action(self, action):
        self.apply_action(action, "button")

    def test_phrase(self):
        # Prevent a typed prefix from authorizing a subsequent microphone command.
        text = self.test_input.get().strip()
        if text:
            self.parser.reset()
            self.handle_final(text, uuid.uuid4().hex, "text test")
            self.parser.reset()

    def show_slide(self):
        if self.target.get() == "PowerPoint":
            self.preview_caption.configure(text="POWERPOINT STATUS / not a slide thumbnail")
            state = self.powerpoint_state
            self.slide_title.configure(text=f"Slide {state.slide}" if state else "Connect a slideshow.")
            self.slide_kicker.configure(text=state.name if state else "Windows desktop PowerPoint")
            self.slide_body.configure(text=("Displayed slide index confirmed by PowerPoint. Say Hey Slides, next slide, previous slide, or go to slide five."
                                             if state else "Open your presentation and start its slideshow. Then click Connect / refresh PowerPoint. Commands never fall back to the demo viewer."))
            self.slide_number.set(f"{state.slide:02d} / {state.count:02d}" if state else "-- / --")
            return
        self.preview_caption.configure(text="PRESENTATION PREVIEW")
        title, kicker, body = SLIDES[self.deck.index]
        self.slide_title.configure(text=title)
        self.slide_kicker.configure(text=kicker)
        self.slide_body.configure(text=body)
        self.slide_number.set(f"{self.deck.index + 1:02d} / {self.deck.count:02d}")

    def draw_features(self, mfcc):
        self.heatmap.delete("all")
        # Per-coefficient normalization is display-only, not a feature transform.
        values = mfcc[:, ::max(1, mfcc.shape[1] // 70)]
        spread = np.maximum(np.ptp(values, axis=1, keepdims=True), 1e-9)
        values = (values - values.min(axis=1, keepdims=True)) / spread
        width, height = max(1, self.heatmap.winfo_width()), 75
        for row in range(values.shape[0]):
            for col in range(values.shape[1]):
                value = float(values[row, col])
                color = f"#{int(20 + 50 * value):02x}{int(39 + 165 * value):02x}{int(60 + 112 * value):02x}"
                self.heatmap.create_rectangle(col * width / values.shape[1], row * height / 13,
                                             (col + 1) * width / values.shape[1] + 1, (row + 1) * height / 13 + 1,
                                             fill=color, outline="")

    def save_features(self):
        if self.last_vector is None:
            self.status.set("No features yet. Start listening first.")
            return
        try:
            config.LOG_DIR.mkdir(parents=True, exist_ok=True)
            path = config.LOG_DIR / f"mfcc-{datetime.now():%Y%m%d-%H%M%S}.json"
            path.write_text(json.dumps({"sample_rate": 16000, "n_mfcc": 13, "n_mels": 40,
                                        "frame_ms": 25, "hop_ms": 10, "n_fft": 512,
                                        "pooling": ["mean", "std", "min", "max"],
                                        "components": "MFCC, delta, delta-delta",
                                        "used_as_vosk_input": False, "vector": self.last_vector.tolist()}, indent=2), encoding="utf-8")
            self.status.set(f"Saved manual features: {path.name}")
        except OSError as exc:
            self.status.set(f"Could not save features: {exc}")

    def close(self):
        self.listening = False
        self.session.stop()
        self.powerpoint.disconnect()
        if self._log_file is not None:
            self._log_file.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    Prototype(root)
    root.mainloop()


if __name__ == "__main__":
    main()
