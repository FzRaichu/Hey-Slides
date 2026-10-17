"""Microphone worker. Tkinter stays on the main thread; audio callbacks only queue."""

import queue
import threading
import time
import uuid

import numpy as np

from app import config
from app.features import ManualMFCC
from app.recognition import StreamingRecognizer, load_model


class MicrophoneSession:
    def __init__(self):
        self.events = queue.Queue()
        self._stop = threading.Event()
        self._thread = None
        self._model = None
        self.session_id = ""

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self, device=None):
        if self.running:
            raise RuntimeError("Previous audio session is still stopping. Try again shortly.")
        self._stop.clear()
        self.session_id = uuid.uuid4().hex
        self._thread = threading.Thread(target=self._run, args=(device,), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _emit(self, kind, **payload):
        self.events.put({"kind": kind, "session_id": self.session_id, **payload})

    def _run(self, device):
        audio = queue.Queue(maxsize=12)
        discontinuity = threading.Event()

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
            self._emit("status", text="Loading local English model...")
            if self._model is None:
                self._model = load_model(config.MODEL_DIR)
            if self._stop.is_set():
                return
            recognizer = StreamingRecognizer(self._model, config.SAMPLE_RATE)
            extractor = ManualMFCC()
            rolling = np.empty(0, dtype=np.float32)
            last_features = 0.0
            utterance = 0
            sd.check_input_settings(device=device, samplerate=config.SAMPLE_RATE,
                                    channels=1, dtype="int16")
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
                    if age_ms > 500:
                        raise RuntimeError("Audio queue fell behind by over 500 ms. Listening stopped to avoid delayed actions.")
                    event = recognizer.feed(pcm)
                    if discontinuity.is_set():
                        raise RuntimeError("Audio discontinuity detected. Listening stopped; no action was sent for this block.")
                    if self._stop.is_set():
                        break
                    if event["changed"]:
                        if event["kind"] == "final":
                            utterance += 1
                        kind = event.pop("kind")
                        self._emit(kind, **event, utterance_id=f"{self.session_id}:{utterance}",
                                   queue_ms=age_ms, allow_action=True)
                    samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
                    rolling = np.concatenate((rolling, samples))[-config.SAMPLE_RATE:]
                    now = time.perf_counter()
                    if now - last_features >= 0.25:
                        began = time.perf_counter()
                        features = extractor.extract(rolling)
                        self._emit("features", mfcc=features.mfcc, vector=features.vector,
                                   rms=features.rms, mfcc_ms=(time.perf_counter() - began) * 1000)
                        last_features = now
            # Preserve the final text on Stop, but never execute its unfinished command.
            tail = recognizer.finish()
            if tail["text"] and not discontinuity.is_set():
                kind = tail.pop("kind")
                self._emit(kind, **tail, utterance_id=f"{self.session_id}:tail", allow_action=False)
        except Exception as exc:
            self._emit("error", text=str(exc))
        finally:
            self._emit("stopped")
