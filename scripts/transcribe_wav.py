"""Repeatable offline smoke test, using the same decoder and command parser as UI.

python -m scripts.transcribe_wav path/to/mono-16k-pcm16.wav
No microphone, speaker playback, or PowerPoint interaction occurs.
"""

import argparse
import json
from pathlib import Path
import time
import wave

import numpy as np

from app import config
from app.commands import CommandParser, SlideDeck
from app.features import ManualMFCC
from app.recognition import StreamingRecognizer, load_model


def transcribe(path, realtime=False):
    model = load_model(config.MODEL_DIR)
    recognizer = StreamingRecognizer(model)
    parser, deck = CommandParser(), SlideDeck()
    results, timings, audio = [], [], bytearray()
    processed_samples = 0
    began = time.perf_counter()
    with wave.open(str(path), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, 16000, "NONE"):
            raise ValueError("Expected uncompressed mono 16000 Hz, signed 16-bit PCM WAV")
        total_samples = wav.getnframes()
        while pcm := wav.readframes(config.AUDIO_BLOCK_SAMPLES):
            processed_samples += len(pcm) // 2
            audio.extend(pcm)
            if len(audio) > 32000:
                del audio[:-32000]
            if realtime:
                remaining = began + processed_samples / config.SAMPLE_RATE - time.perf_counter()
                if remaining > 0:
                    time.sleep(remaining)
            event = recognizer.feed(pcm)
            timings.append(event["decode_ms"])
            if event["kind"] == "final" and event["text"]:
                decision = parser.accept(event["text"], str(len(results)), now=processed_samples / 16000)
                if decision.action:
                    deck.apply(decision.action)
                results.append({"text": event["text"], "action": decision.action,
                                "status": decision.status, "words": event["words"]})
        tail = recognizer.finish()
        if tail["text"]:
            # EOF can finalize a real phrase. This is a file test, unlike microphone Stop.
            decision = parser.accept(tail["text"], str(len(results)), now=processed_samples / 16000)
            if decision.action:
                deck.apply(decision.action)
            results.append({"text": tail["text"], "action": decision.action,
                            "status": decision.status, "words": tail["words"], "finalized_at_eof": True})
    elapsed = time.perf_counter() - began
    samples = np.frombuffer(audio, dtype="<i2").astype(np.float32) / 32768
    features = ManualMFCC().extract(samples)
    return {"source": str(Path(path).resolve()), "mode": "realtime file replay" if realtime else "offline file decode",
            "audio_seconds": total_samples / 16000, "elapsed_seconds_excluding_model_load": elapsed,
            "decode_call_ms_median": float(np.median(timings)) if timings else None,
            "decode_call_ms_p95": float(np.percentile(timings, 95)) if timings else None,
            "word_to_screen_latency_ms": None,
            "latency_note": "Decode timings exclude endpoint waiting and UI. They do not verify the 200 ms target.",
            "utterances": results, "preview_slide": deck.index + 1,
            "manual_mfcc_shape": list(features.mfcc.shape), "manual_feature_dimensions": features.vector.size,
            "manual_features_used_as_vosk_input": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path)
    parser.add_argument("--realtime", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = transcribe(args.wav, args.realtime)
    output = json.dumps(result, indent=2)
    print(output)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
