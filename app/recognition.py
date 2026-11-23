"""Offline Vosk adapter. Timings here measure calls, not word-to-screen latency."""

import json
from pathlib import Path
import re
from time import perf_counter

# Vosk endpoint rules 2-4 (minimum trailing silence before an utterance is final),
# as multiples of rule2. vosk-model-small-en-us-0.15 ships 0.5 / 0.75 / 1.0 s.
ENDPOINT_RULE_RATIOS = {"rule2": 1.0, "rule3": 1.5, "rule4": 2.0}


def endpoint_conf(text, silence):
    """Return model.conf text with rules 2-4 scaled to `silence` seconds, or None if
    the file does not define all three rules."""
    for rule, ratio in ENDPOINT_RULE_RATIOS.items():
        text, count = re.subn(rf"(--endpoint\.{rule}\.min-trailing-silence=)[0-9.]+",
                              lambda m, value=silence * ratio: f"{m.group(1)}{value:.3f}", text)
        if count != 1:
            return None
    return text


def apply_endpoint_silence(model_dir, silence):
    """Set how long Vosk waits in silence before finalizing an utterance.

    Vosk 0.3.45 has no runtime API for this; it reads conf/model.conf when the model
    loads, so the rules are rewritten there (the first original is kept as
    model.conf.original). Returns True when the setting is in effect.
    """
    conf = Path(model_dir) / "conf" / "model.conf"
    if not conf.is_file():
        return False
    text = conf.read_text(encoding="utf-8")
    updated = endpoint_conf(text, silence)
    if updated is None:
        return False
    if updated != text:
        backup = conf.with_name("model.conf.original")
        if not backup.exists():
            backup.write_text(text, encoding="utf-8")
        conf.write_text(updated, encoding="utf-8")
    return True


def load_model(path, endpoint_silence=None):
    from vosk import Model, SetLogLevel
    path = Path(path)
    if not (path / "am" / "final.mdl").is_file():
        from app.config import MODEL_PROFILES
        profile = next((key for key, item in MODEL_PROFILES.items() if item["name"] == path.name), None)
        suffix = f" --profile {profile}" if profile else ""
        raise FileNotFoundError(f"ASR model not installed at {path}. Run: python -m scripts.download_model{suffix}")
    if endpoint_silence is not None and not apply_endpoint_silence(path, endpoint_silence):
        raise RuntimeError(f"Could not set the endpoint silence in {path / 'conf' / 'model.conf'}. "
                           "Choose the Vosk default in Pengaturan.")
    SetLogLevel(-1)
    return Model(str(path))


class StreamingRecognizer:
    def __init__(self, model, sample_rate=16000, grammar=None):
        from vosk import KaldiRecognizer
        # No restricted grammar: normal speech remains transcribable.
        self.recognizer = (KaldiRecognizer(model, sample_rate) if grammar is None
                           else KaldiRecognizer(model, sample_rate, json.dumps(grammar)))
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

    def warm_up(self, sample_rate=16000, seconds=2.0):
        """Decode synthetic audio once, then reset; returns the number of samples fed.

        The first speech-like audio a new Vosk recognizer decodes costs ~0.5 s of
        one-time setup. Live, that stall can exceed the stale-audio limit and stop the
        session at the first spoken word. A tone sweep triggers the setup up front
        (measured: worst live block ~560 ms -> ~150 ms).

        Vosk keeps counting time across Reset(), so later word timestamps are offset
        by the returned number of samples.
        """
        import numpy as np
        count = int(sample_rate * seconds)
        sweep = np.sin(2 * np.pi * np.cumsum(np.linspace(150, 900, count)) / sample_rate)
        pcm = (6000 * sweep).astype("<i2").tobytes()
        for start in range(0, len(pcm), 800):
            self.recognizer.AcceptWaveform(pcm[start:start + 800])
        self.recognizer.Reset()
        self._last_partial = ""
        return count

    def finish(self):
        payload = json.loads(self.recognizer.FinalResult())
        return {"kind": "final", "text": payload.get("text", ""),
                "words": payload.get("result", []), "decode_ms": None, "changed": True}
