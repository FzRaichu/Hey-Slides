"""Offline Vosk adapter. Timings here measure calls, not word-to-screen latency."""

import json
from pathlib import Path
from time import perf_counter


def load_model(path):
    from vosk import Model, SetLogLevel
    path = Path(path)
    if not (path / "am" / "final.mdl").is_file():
        raise FileNotFoundError("ASR model not installed. Run: python -m scripts.download_model")
    SetLogLevel(-1)
    return Model(str(path))


class StreamingRecognizer:
    def __init__(self, model, sample_rate=16000):
        from vosk import KaldiRecognizer
        # No restricted grammar: normal speech remains transcribable.
        self.recognizer = KaldiRecognizer(model, sample_rate)
        self.recognizer.SetWords(True)
        self._last_partial = ""

    def feed(self, pcm: bytes):
        started = perf_counter()
        final = self.recognizer.AcceptWaveform(pcm)
        payload = json.loads(self.recognizer.Result() if final else self.recognizer.PartialResult())
        elapsed = (perf_counter() - started) * 1000
        text = payload.get("text" if final else "partial", "")
        changed = final or text != self._last_partial
        self._last_partial = "" if final else text
        return {"kind": "final" if final else "partial", "text": text,
                "decode_ms": elapsed, "changed": changed, "words": payload.get("result", [])}

    def finish(self):
        payload = json.loads(self.recognizer.FinalResult())
        return {"kind": "final", "text": payload.get("text", ""),
                "words": payload.get("result", []), "decode_ms": None, "changed": True}
