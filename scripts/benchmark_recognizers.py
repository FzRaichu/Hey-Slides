"""Offline local comparison on saved WAVs; never controls slides or opens a mic.

Optional references JSON maps WAV basenames to {"text": ..., "confirmed": true,
"complete": true}. Only complete confirmed references receive WER. Other
recordings remain unscored. Results contain private speech: keep them in logs/.
"""

import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import time
import wave

import numpy as np

from app import config
from app.recognition import load_model
from app.whisper_recognition import load_whisper_model, transcribe_audio, VAD_SETTINGS
from scripts.compare_command_decoders import compare
from scripts.evaluation_metrics import word_errors


def score_reference(reference, hypotheses):
    if reference.get("confirmed") is not True or reference.get("complete") is not True:
        return None
    return {name: word_errors(reference["text"], text) for name, text in hypotheses.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wavs", nargs="+", type=Path)
    parser.add_argument("--whisper-model", type=Path, default=Path("models/faster-whisper-base.en"))
    parser.add_argument("--references", type=Path)
    parser.add_argument("--output", type=Path, default=Path("logs/recognizer-benchmark.json"))
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--segmentation", choices=("whole", "vad", "context"), default="whole")
    parser.add_argument("--command-mode", choices=config.COMMAND_MODES, default="wake")
    parser.add_argument("--language", choices=("en", "id", "auto"), default="en")
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("--threads must be positive")
    if not (args.whisper_model / "model.bin").is_file():
        parser.error("Download the evaluation model first: python -m scripts.download_whisper_evaluation")
    if args.whisper_model.name.endswith(".en") and args.language != "en":
        parser.error("Use a multilingual model for Indonesian or automatic language detection")
    print("Loading optional Whisper runtime", flush=True)

    references = json.loads(args.references.read_text(encoding="utf-8")) if args.references else {}
    print("Loading local Vosk and Whisper models", flush=True)
    started = time.perf_counter()
    vosk = load_model(config.model_path("light"))
    vosk_load = time.perf_counter() - started
    started = time.perf_counter()
    whisper = load_whisper_model(args.whisper_model, args.threads)
    whisper_load = time.perf_counter() - started
    provenance_path = args.whisper_model / "evaluation-provenance.json"
    result = {
        "mode": "offline; no microphone, presentation actions, or audio upload",
        "vosk": {"profile": "light", "command_mode": args.command_mode},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor(), "logical_cpus": os.cpu_count(),
                        "versions": {p: version(p) for p in ("faster-whisper", "ctranslate2", "vosk", "numpy",
                                                               "av", "onnxruntime", "tokenizers", "huggingface-hub")}},
        "whisper": {"model": str(args.whisper_model.resolve()), "device": "cpu", "compute_type": "int8",
                    "threads": args.threads, "beam_size": 5, "language": args.language,
                    "task": "transcribe", "segmentation": args.segmentation,
                    "vad_filter": True, "external_vad_settings": VAD_SETTINGS if args.segmentation != "whole" else None,
                    "condition_on_previous_text": False, "initial_prompt": None, "hotwords": None,
                    "provenance": json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.exists() else None},
        "load_seconds": {"vosk": vosk_load, "whisper": whisper_load},
        "latency_note": "Offline decode time / audio duration is throughput, not microphone-to-text or slide latency.",
        "clips": [],
    }
    # Write each completed clip so a failed later decode does not lose evidence.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for path in args.wavs:
        with wave.open(str(path), "rb") as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, 16000, "NONE"):
                raise ValueError(f"Expected mono PCM16 16 kHz WAV: {path}")
            if not wav.getnframes():
                raise ValueError(f"Empty WAV: {path}")
            pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(np.float32) / 32768
        print(f"Decoding {path.name}", flush=True)
        started = time.perf_counter()
        baseline = compare(path, model=vosk, command_mode=args.command_mode)
        vosk_seconds = time.perf_counter() - started
        started = time.perf_counter()
        transcription = transcribe_audio(whisper, pcm, segmentation=args.segmentation,
                                        language=None if args.language == "auto" else args.language)
        segments = transcription["segments"]
        whisper_seconds = time.perf_counter() - started
        hypotheses = {
            "vosk_general": " ".join(e["text"] for e in baseline["results"]["unrestricted"]),
            "vosk_focused": " ".join(e["text"] for e in baseline["results"]["command_focused"]),
            "whisper_general": " ".join(s["text"] for s in segments),
        }
        reference = references.get(path.name, {})
        clip = {"source": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "audio_seconds": baseline["audio_seconds"], "vosk": baseline["results"],
                "whisper_segments": segments, "whisper_spans": transcription["spans"], "hypotheses": hypotheses,
                "decode_seconds": {"vosk_both_decoders": vosk_seconds, "whisper_general": whisper_seconds},
                "offline_real_time_factor": {"vosk_both_decoders": vosk_seconds / baseline["audio_seconds"],
                                             "whisper_general": whisper_seconds / baseline["audio_seconds"]},
                "reference": reference or None,
                "wer": score_reference(reference, hypotheses),
                "scoring_note": "Focused output is command-constrained, not a general STT competitor; EOF candidates are not live actions."}
        result["clips"].append(clip)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Saved {len(result['clips'])} clip(s); Whisper decode {whisper_seconds:.2f}s", flush=True)


if __name__ == "__main__":
    main()
