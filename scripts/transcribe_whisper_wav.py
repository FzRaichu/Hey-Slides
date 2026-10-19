"""Review a captured WAV with local multilingual Whisper; never controls slides."""

import argparse
import json
from pathlib import Path
import time
import wave

import numpy as np

from app import config
from app.whisper_recognition import load_whisper_model, transcribe_audio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path)
    parser.add_argument("--model", choices=("small", "small.en", "base.en"), default="small")
    parser.add_argument("--language", choices=("auto", "en", "id"), default="auto")
    parser.add_argument("--segmentation", choices=("whole", "vad", "context"), default="whole")
    parser.add_argument("--output", type=Path, default=Path("logs/whisper-review.json"))
    args = parser.parse_args()
    if args.model.endswith(".en") and args.language != "en":
        parser.error("English-only models require --language en")
    with wave.open(str(args.wav), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, 16000, "NONE"):
            parser.error("Expected uncompressed mono PCM16 16 kHz WAV")
        audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(np.float32) / 32768
    print(f"Loading local {args.model}; transcription only, no slide actions", flush=True)
    began = time.perf_counter()
    model = load_whisper_model(config.PROJECT_ROOT / "models" / f"faster-whisper-{args.model}")
    load_seconds = time.perf_counter() - began
    result = transcribe_audio(model, audio, segmentation=args.segmentation,
                              language=None if args.language == "auto" else args.language)
    text = " ".join(segment["text"] for segment in result["segments"])
    result.update(source=str(args.wav.resolve()), model=args.model, requested_language=args.language,
                  task="transcribe", segmentation=args.segmentation, text=text,
                  load_seconds=load_seconds, audio_seconds=len(audio) / 16000,
                  note="Offline review; no actions, no audio upload, no latency claim.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(text or "[No transcript returned]")
    print(f"Saved {args.output}; decode {result['elapsed_seconds']:.2f}s (offline)")


if __name__ == "__main__":
    main()
