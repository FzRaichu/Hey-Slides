"""Run with python -m app.main. Desktop prototype; no network service required."""

from datetime import datetime
import json
import os
from pathlib import Path
import queue
import tkinter as tk
import uuid

import numpy as np

from app import config
from app.commands import CommandParser, SlideDeck
from app.powerpoint import PowerPointAdapter, PowerPointError, PowerPointCommandError
from app.session import MicrophoneSession


SLIDES = [
    ("Kontrol lewat suara", "01 / Voice Slide Control", "Ucapkan Next slide, Previous slide, atau Go to slide three."),
    ("Ucapan menjadi teks", "02 / Pretrained Vosk", "Vosk mengenali ucapan bahasa Inggris secara lokal."),
    ("Perintah navigasi", "03 / Kendali slide", "Hasil final diperiksa sebelum navigasi dijalankan."),
    ("MFCC menjadi fitur", "04 / Analisis manual", "MFCC menghasilkan angka fitur, bukan teks atau aksi slide."),
    ("Uji dan evaluasi", "05 / Pengujian", "Akurasi dan responsivitas masih perlu diuji pada pengguna."),
]

BG, CARD, INK, MUTED, ACCENT = "#edf1f5", "#ffffff", "#14273c", "#53697e", "#087f78"


class Prototype:
    def __init__(self, root, powerpoint=None):
        self.root = root
        root.title("Voice Slide Control | Prototipe")
        width = max(960, min(1120, root.winfo_screenwidth() - 80))
        height = max(660, min(740, root.winfo_screenheight() - 100))
        root.geometry(f"{width}x{height}")
        root.minsize(960, 660)
        root.configure(bg=BG)
        self.parser = CommandParser(require_prefix=config.DEFAULT_COMMAND_MODE == "wake")
        self.deck = SlideDeck(count=len(SLIDES))
        self.powerpoint = powerpoint or PowerPointAdapter()
        self.powerpoint_state = None
        self.target = tk.StringVar(value="Demo slides")
        self.session = MicrophoneSession()
        self.listening = False
        self.active_session = ""
        self.last_vector = None
        self.last_mfcc = None
        self.status = tk.StringVar(value="Siap | mikrofon belum aktif")
        self.partial = tk.StringVar(value="Ucapan sementara akan muncul di sini...")
        self.command_status = tk.StringVar(value="Perintah: Next slide / Previous slide / Go to slide three")
        self.command_mode = tk.StringVar(value=config.COMMAND_MODES[config.DEFAULT_COMMAND_MODE])
        self.demo_hint = tk.StringVar(value="Ucapkan: Next slide  /  Previous slide  /  Go to slide three")
        self.timing = tk.StringVar(value="Decode: -- | MFCC: -- | queue: --")
        self.feature_status = tk.StringVar(value="13 koefisien MFCC | menunggu audio")
        self.feature_values = tk.StringVar(value="Vektor fitur: menunggu audio mikrofon.")
        self.slide_number = tk.StringVar()
        self.devices = {"Default microphone": None}
        self.device = tk.StringVar(value="Default microphone")
        self.model_profile = tk.StringVar(value=config.MODEL_PROFILES[config.DEFAULT_MODEL_PROFILE]["label"])
        self.audio_quality = tk.StringVar(value="Mikrofon belum aktif")
        self.command_assist = tk.BooleanVar(value=True)
        self.record_audio = tk.BooleanVar(value=False)
        self.last_recording = None
        self._log_file = None
        self._closing = False
        self._build()
        self.show_slide()
        self.refresh_devices()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(50, self.poll)

    def _build(self):
        from app.demo_view import build_demo_view
        build_demo_view(self, (BG, CARD, INK, MUTED, ACCENT))

    def show_settings(self):
        if not self._closing:
            self.settings_dialog.deiconify()
            self.settings_dialog.lift()

    def hide_settings(self):
        self.settings_dialog.withdraw()

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
        if self._closing:
            return
        try:
            if self.target.get() == "PowerPoint":
                self.powerpoint_state = self.powerpoint.snapshot()
                self.show_slide()
            self.parser.reset()
            mode = self.selected_command_mode()
            self.parser = CommandParser(require_prefix=mode == "wake")
            profile = next(key for key, item in config.MODEL_PROFILES.items() if item["label"] == self.model_profile.get())
            self.session.start(self.devices.get(self.device.get()), model_profile=profile,
                               command_assist=self.command_assist.get(), record_audio=self.record_audio.get(), command_mode=mode)
            self.active_session = self.session.session_id
            self.last_vector = None
            self.last_mfcc = None
            self.heatmap.delete("all")
            self.feature_status.set("13 koefisien MFCC | menunggu audio")
            self.feature_values.set("Vektor fitur: menunggu audio mikrofon.")
            self.save_features_button.configure(state="disabled")
            self.listening = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.device_box.configure(state="disabled")
            self.refresh_button.configure(state="disabled")
            self.model_box.configure(state="disabled")
            self.mode_box.configure(state="disabled")
            self.assist_check.configure(state="disabled")
            self.record_check.configure(state="disabled")
            self.play_button.configure(state="disabled")
            if self.record_audio.get():
                self.last_recording = None
            self.status.set("Menyiapkan mikrofon...")
            self.command_status.set(self.command_hint())
            self.log("start", device=self.device.get(), model_profile=profile,
                     command_assist=self.command_assist.get(), record_audio=self.record_audio.get(),
                     session_id=self.active_session, command_mode=mode)
        except Exception as exc:
            if isinstance(exc, PowerPointError):
                self.powerpoint_state = None
                self.show_slide()
            self.status.set(str(exc))

    def selected_command_mode(self):
        return next(key for key, label in config.COMMAND_MODES.items() if label == self.command_mode.get())

    def command_hint(self):
        return ("Perintah: Next slide / Previous slide / Go to slide three"
                if self.selected_command_mode() == "direct" else "Awali perintah dengan Hey Slides")

    def change_command_mode(self):
        if self.listening or self.session.running:
            self.stop()
        mode = self.selected_command_mode()
        self.parser = CommandParser(require_prefix=mode == "wake")
        self.command_status.set(self.command_hint())
        self.test_input.delete(0, "end")
        self.test_input.insert(0, "Next slide" if mode == "direct" else "Hey Slides, next slide")
        self.demo_hint.set("Ucapkan: Next slide  /  Previous slide  /  Go to slide three" if mode == "direct"
                           else "Ucapkan: Hey Slides, next slide  /  Hey Slides, previous slide")
        self.show_slide()
        self.log("command_mode_changed", command_mode=mode)

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
            self.status.set(f"Terhubung: {self.powerpoint_state.name} | mikrofon nonaktif")
            self.command_status.set("PowerPoint siap | klik Mulai mendengarkan")
            self.log("powerpoint_connected", presentation=self.powerpoint_state.name,
                     slide=self.powerpoint_state.slide, count=self.powerpoint_state.count)
        except PowerPointError as exc:
            self.powerpoint_state = None
            self.status.set(str(exc))
            self.command_status.set("PowerPoint belum terhubung | aksi tidak dikirim")
            self.log("powerpoint_error", text=str(exc))
        self.show_slide()

    def stop(self):
        self.listening = False
        self.parser.reset()
        self.session.stop()
        self.stop_button.configure(state="disabled")
        self.command_status.set("Aksi dinonaktifkan | mikrofon berhenti")
        self.status.set("Menghentikan mikrofon...")
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
                    self.partial.set(event["text"] or "Mendengarkan...")
                    self._update_timing(event)
                elif kind == "final":
                    self.partial.set("Mendengarkan..." if self.listening else "Mikrofon nonaktif")
                    if event["text"]:
                        self.handle_final(event["text"], event["utterance_id"], "microphone",
                                          allow_action=self.listening and event["allow_action"],
                                          transcript_only=self.listening and event.get("transcript_only", False))
                        self.log("recognition", text=event["text"], words=event["words"],
                                 decode_ms=event["decode_ms"], session_id=self.active_session)
                    self._update_timing(event)
                elif kind == "command_final":
                    if not self.listening or not event.get("allow_action"):
                        continue
                    self.log("command_recognition", text=event["text"], words=event["words"],
                             eligible=event["eligible"], reason=event["reason"],
                             mean_score=event.get("mean_score"), decode_ms=event["decode_ms"])
                    if event["eligible"]:
                        self.handle_final(event["text"], event["utterance_id"], "command recognizer")
                    else:
                        self.parser.disarm()
                        self.command_status.set(f"Command candidate rejected: {event['reason']}")
                elif kind == "recording_saved":
                    if event["seconds"] > 0:
                        self.last_recording = Path(event["path"])
                    self.log("recording_saved", path=event["path"], seconds=event["seconds"], interrupted=event["interrupted"])
                elif kind == "features":
                    self.last_vector = event["vector"]
                    self.draw_features(event["mfcc"])
                    self.feature_status.set(f"13 x {event['mfcc'].shape[1]} frame | 156 fitur | RMS {event['rms']:.3f}")
                    values = ", ".join(f"{value:.2f}" for value in self.last_vector[:6])
                    self.feature_values.set(f"Contoh 6 dari 156 nilai fitur:\n[{values}]")
                    self.save_features_button.configure(state="normal")
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
                    self.mode_box.configure(state="readonly")
                    self.assist_check.configure(state="normal")
                    self.record_check.configure(state="normal")
                    self.play_button.configure(state="normal" if self.last_recording else "disabled")
                    self.partial.set("Mikrofon nonaktif")
                    self.audio_quality.set("Mikrofon nonaktif")
                    if not self.status.get().startswith("Error:"):
                        self.status.set("Siap | mikrofon nonaktif" + (" | WAV tersimpan; buka Pengaturan untuk memutar" if self.last_recording else ""))
        except queue.Empty:
            pass
        self.root.after(50, self.poll)

    def _update_timing(self, event):
        decode = event.get("decode_ms")
        mfcc = getattr(self, "_mfcc_ms", None)
        age = event.get("queue_ms")
        fmt = lambda x: "--" if x is None else f"{x:.1f} ms"
        self.timing.set(f"Decode call: {fmt(decode)} | MFCC analysis: {fmt(mfcc)} | audio queue: {fmt(age)}")

    def handle_final(self, text, utterance_id, source, allow_action=True, transcript_only=False):
        self.transcript.configure(state="normal")
        label = ("MIC" if source == "microphone" else "COMMAND ASR" if source == "command recognizer"
                 else "TEXT TEST / not ASR")
        self.transcript.insert("end", f"[{label}] {text}\n")
        # Keep the visible transcript bounded; the full local log remains available.
        if int(self.transcript.index("end-1c").split(".")[0]) > 500:
            self.transcript.delete("1.0", "101.0")
        self.transcript.see("end-2c")
        self.transcript.configure(state="disabled")
        if transcript_only:
            return
        if not allow_action:
            self.command_status.set("Teks akhir tersimpan | aksi sudah dinonaktifkan")
            return
        decision = self.parser.accept(text, utterance_id)
        messages = {"armed": "Hey Slides dikenali | ucapkan perintah dalam 4 detik",
                    "ordinary speech": "Ucapan biasa | tidak ada aksi slide",
                    "unrecognized command": "Tidak ada aksi | ucapkan satu perintah lengkap"}
        self.command_status.set(messages.get(decision.status, decision.status))
        if decision.action:
            self.apply_action(decision.action, source, decision.target_slide)
        self.log("command_decision", text=text, source=source, status=decision.status,
                 action=decision.action, target_slide=decision.target_slide, utterance_id=utterance_id)

    def apply_action(self, action, source, target_slide=None):
        target = self.target.get()
        source_label = "suara" if source in ("microphone", "command recognizer") else "tombol" if source == "button" else "tes teks"
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
            self.actions.insert(0, f"{datetime.now():%H:%M:%S} {action.upper()}: gagal [{source_label}]")
            if self.actions.size() > 50:
                self.actions.delete(50, "end")
            self.log("slide_action_failed", target=target, action=action, source=source,
                     target_slide=target_slide, error=str(exc))
            return
        self.show_slide()
        text = f"{action.upper()} -> slide {slide}" + ("" if moved else " (unchanged)")
        self.command_status.set(text)
        self.actions.insert(0, f"{datetime.now():%H:%M:%S} {text} [{source_label}]")
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
            self.connect_button.pack(side="left", padx=(7, 0), after=self.target_box)
            self.preview_caption.configure(text="POWERPOINT / STATUS SLIDE")
            state = self.powerpoint_state
            self.slide_title.configure(text=f"Slide {state.slide}" if state else "Hubungkan slideshow.")
            self.slide_kicker.configure(text=state.name if state else "Windows desktop PowerPoint")
            self.slide_body.configure(text=("Nomor slide dikonfirmasi dari PowerPoint; panel ini bukan gambar slide."
                                             if state else "Buka presentasi dan mulai slideshow, lalu klik Hubungkan PowerPoint."))
            self.slide_number.set(f"{state.slide:02d} / {state.count:02d}" if state else "-- / --")
            return
        self.connect_button.pack_forget()
        self.preview_caption.configure(text="SLIDE DEMO")
        title, kicker, body = SLIDES[self.deck.index]
        self.slide_title.configure(text=title)
        self.slide_kicker.configure(text=kicker)
        self.slide_body.configure(text=body)
        self.slide_number.set(f"{self.deck.index + 1:02d} / {self.deck.count:02d}")

    def draw_features(self, mfcc):
        self.last_mfcc = mfcc
        self.heatmap.delete("all")
        # Per-coefficient normalization is display-only, not a feature transform.
        values = mfcc[:, ::max(1, mfcc.shape[1] // 70)]
        spread = np.maximum(np.ptp(values, axis=1, keepdims=True), 1e-9)
        values = (values - values.min(axis=1, keepdims=True)) / spread
        width, height = max(1, self.heatmap.winfo_width()), max(1, self.heatmap.winfo_height())
        for row in range(values.shape[0]):
            for col in range(values.shape[1]):
                value = float(values[row, col])
                color = f"#{int(20 + 50 * value):02x}{int(39 + 165 * value):02x}{int(60 + 112 * value):02x}"
                self.heatmap.create_rectangle(col * width / values.shape[1], row * height / 13,
                                             (col + 1) * width / values.shape[1] + 1, (row + 1) * height / 13 + 1,
                                             fill=color, outline="")

    def save_features(self):
        if self.last_vector is None:
            self.status.set("Belum ada fitur. Klik Mulai mendengarkan terlebih dahulu.")
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

    def play_recording(self):
        if self.listening or self.session.running:
            self.status.set("Klik Stop sebelum memutar rekaman agar tidak masuk kembali ke mikrofon.")
            return
        if self.last_recording is None or not self.last_recording.is_file():
            self.status.set("Belum ada WAV. Aktifkan rekaman di Pengaturan, mulai bicara, lalu Stop.")
            return
        try:
            os.startfile(str(self.last_recording))
        except (OSError, AttributeError) as exc:
            self.status.set(f"Open this recording manually: {self.last_recording} ({exc})")

    def close(self):
        if self._closing:
            return
        self._closing = True
        self.listening = False
        self.parser.reset()
        self.session.stop()
        self.powerpoint.disconnect()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        self.status.set("Closing | waiting for audio and any recording to finish...")
        self._finish_close()

    def _finish_close(self):
        if self.session.running:
            self.root.after(50, self._finish_close)
            return
        if self._log_file is not None:
            self._log_file.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    Prototype(root)
    root.mainloop()


if __name__ == "__main__":
    main()
