"""Microphone worker. Tkinter stays on the main thread; audio callbacks only queue."""

import queue
import threading
import time
import uuid
import wave

import numpy as np

from app import config
from app.features import ManualMFCC
from app.recognition import StreamingRecognizer, load_model
from app.command_recognition import CommandRecognizer, align_command_endpoint


class MicrophoneSession:
    def __init__(self):
        self.events = queue.Queue()
        self._stop = threading.Event()
        self._thread = None
        self._model = None
        self._model_profile = None
        self.session_id = ""

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self, device=None, model_profile=config.DEFAULT_MODEL_PROFILE,
              command_assist=True, record_audio=False):
        if self.running:
            raise RuntimeError("Previous audio session is still stopping. Try again shortly.")
        self._stop.clear()
        self.session_id = uuid.uuid4().hex
        model_dir = config.model_path(model_profile)
        self._thread = threading.Thread(target=self._run,
                                        args=(device, model_profile, model_dir, command_assist, record_audio), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _emit(self, kind, **payload):
        self.events.put({"kind": kind, "session_id": self.session_id, **payload})

    def _run(self, device, model_profile, model_dir, command_assist=True, record_audio=False):
        profile_settings = config.MODEL_PROFILES[model_profile]
        audio = queue.Queue(maxsize=profile_settings["queue_blocks"])
        max_age_ms = profile_settings["max_queue_ms"]
        discontinuity = threading.Event()
        recording = None
        recording_path = None
        recorded_samples = 0
        failed = False

        def callback(indata, frames, timing, status):
            if status:
                discontinuity.set()
            if self._stop.is_set():
                return
            try:
                audio.put_nowait((bytes(indata), time.perf_counter()))
            except queue.Full:
                discontinuity.set()

        try:
            import sounddevice as sd
            self._emit("status", text=f"Loading {config.MODEL_PROFILES[model_profile]['label']}...")
            if self._model is None or self._model_profile != model_profile:
                # Release the previous model before loading another profile.
                self._model = None
                self._model = load_model(model_dir)
                self._model_profile = model_profile
            if self._stop.is_set():
                return
            recognizer = StreamingRecognizer(self._model, config.SAMPLE_RATE)
            command_recognizer = CommandRecognizer(self._model, config.SAMPLE_RATE) if command_assist else None
            extractor = ManualMFCC()
            rolling = np.empty(0, dtype=np.float32)
            last_features = 0.0
            utterance = 0
            command_utterance = 0
            sd.check_input_settings(device=device, samplerate=config.SAMPLE_RATE,
                                    channels=1, dtype="int16")
            if record_audio:
                config.LOG_DIR.mkdir(parents=True, exist_ok=True)
                recording_path = config.LOG_DIR / f"input-{self.session_id}.wav"
                recording = wave.open(str(recording_path), "wb")
                recording.setparams((1, 2, config.SAMPLE_RATE, 0, "NONE", "not compressed"))
            with sd.RawInputStream(samplerate=config.SAMPLE_RATE,
                                   blocksize=config.AUDIO_BLOCK_SAMPLES,
                                   device=device, channels=1, dtype="int16", callback=callback):
                self._emit("status", text="Listening | say: Hey Slides, next slide")
                while not self._stop.is_set():
                    if discontinuity.is_set():
                        raise RuntimeError("Audio was lost or overflowed. Listening stopped; restart after checking the microphone/load.")
                    try:
                        pcm, received_at = audio.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    age_ms = (time.perf_counter() - received_at) * 1000
                    if age_ms > max_age_ms:
                        raise RuntimeError(f"Audio queue fell behind by over {max_age_ms} ms. Try the Light English model or reduce CPU load.")
                    if recording is not None:
                        recording.writeframesraw(pcm)
                        recorded_samples += len(pcm) // 2
                    event = recognizer.feed(pcm)
                    command_event = command_recognizer.feed(pcm) if command_recognizer else None
                    if command_recognizer:
                        command_event = align_command_endpoint(event, command_event, command_recognizer)
                    if (time.perf_counter() - received_at) * 1000 > max_age_ms:
                        raise RuntimeError(f"Recognition exceeded the {max_age_ms} ms stale-audio limit. Try Light English or reduce CPU load.")
                    if discontinuity.is_set():
                        raise RuntimeError("Audio discontinuity detected. Listening stopped; no action was sent for this block.")
                    if self._stop.is_set():
                        break
                    if event["changed"]:
                        if event["kind"] == "final":
                            utterance += 1
                        kind = event.pop("kind")
                        self._emit(kind, **event, utterance_id=f"{self.session_id}:{utterance}",
                                   queue_ms=age_ms, allow_action=not command_assist,
                                   transcript_only=command_assist)
                    if command_event and command_event["kind"] == "final" and command_event["text"]:
                        command_utterance += 1
                        command_event.pop("kind")
                        self._emit("command_final", **command_event,
                                   utterance_id=f"{self.session_id}:command:{command_utterance}",
                                   allow_action=True)
                    samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
                    rolling = np.concatenate((rolling, samples))[-config.SAMPLE_RATE:]
                    now = time.perf_counter()
                    if now - last_features >= 0.25:
                        began = time.perf_counter()
                        features = extractor.extract(rolling)
                        self._emit("features", mfcc=features.mfcc, vector=features.vector,
                                   rms=features.rms, peak=float(np.max(np.abs(rolling))),
                                   clipped_fraction=float(np.mean(np.abs(rolling) >= 0.999)),
                                   mfcc_ms=(time.perf_counter() - began) * 1000)
                        last_features = now
            # Preserve the final text on Stop, but never execute its unfinished command.
            tail = recognizer.finish()
            if tail["text"] and not discontinuity.is_set():
                kind = tail.pop("kind")
                self._emit(kind, **tail, utterance_id=f"{self.session_id}:tail", allow_action=False)
        except Exception as exc:
            failed = True
            self._emit("error", text=str(exc))
        finally:
            if recording is not None:
                try:
                    recording.close()
                    self._emit("recording_saved", path=str(recording_path), seconds=recorded_samples / config.SAMPLE_RATE,
                               interrupted=failed or discontinuity.is_set())
                except OSError as exc:
                    self._emit("error", text=f"Could not finalize the diagnostic recording: {exc}")
            self._emit("stopped")
