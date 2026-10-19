"""Local, non-actionable Whisper transcription and speech-span evaluation.

Optional dependencies are imported lazily. This module never controls slides.
"""

from pathlib import Path
import time

import numpy as np

SAMPLE_RATE = 16000
VAD_SETTINGS = {"threshold": 0.5, "min_speech_duration_ms": 200,
                "min_silence_duration_ms": 300, "speech_pad_ms": 200,
                "max_speech_duration_s": 8}


def load_whisper_model(path, threads=4):
    path = Path(path)
    if not (path / "model.bin").is_file():
        variant = path.name.removeprefix("faster-whisper-")
        variant = variant if variant in ("base.en", "small.en", "small") else "small"
        raise FileNotFoundError(f"Local Whisper model missing; run python -m scripts.download_whisper_evaluation --model {variant}")
    if threads < 1:
        raise ValueError("threads must be positive")
    from faster_whisper import WhisperModel
    return WhisperModel(str(path.resolve()), device="cpu", compute_type="int8",
                        cpu_threads=threads, local_files_only=True, num_workers=1)


def speech_spans(audio):
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    return get_speech_timestamps(audio, VadOptions(**VAD_SETTINGS), sampling_rate=SAMPLE_RATE)


def context_spans(spans, max_samples=8 * SAMPLE_RATE):
    """Group adjacent detected spans into <=8s context windows, keeping gaps.

    This avoids independently decoding every one-second fragment. No overlapping
    audio or text deduplication is used, so intentional repetitions remain.
    """
    groups = []
    previous_end = 0
    for span in spans:
        start, end = span["start"], span["end"]
        if not 0 <= previous_end <= start < end:
            raise ValueError("Invalid speech spans")
        previous_end = end
        if groups and end - groups[-1]["start"] <= max_samples:
            groups[-1]["end"] = end
        else:
            groups.append({"start": start, "end": end})
    return groups


def transcribe_audio(model, audio, segmentation="whole", language="en"):
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim != 1 or not np.isfinite(audio).all():
        raise ValueError("Expected finite mono float audio at 16 kHz")
    if segmentation not in ("whole", "vad", "context"):
        raise ValueError("Unknown segmentation mode")
    if language not in ("en", "id", None):
        raise ValueError("Expected en, id, or None for automatic language detection")
    began = time.perf_counter()
    if not audio.size:
        return {"segments": [], "spans": [], "elapsed_seconds": 0.0}
    spans = speech_spans(audio) if segmentation != "whole" else [{"start": 0, "end": len(audio)}]
    if segmentation == "context":
        spans = context_spans(spans)
    output, diagnostics = [], []
    previous_end = 0
    for span in spans:
        start, end = span["start"], span["end"]
        if not 0 <= previous_end <= start < end <= len(audio):
            raise ValueError("Speech spans must be ordered, nonoverlapping, and inside the audio")
        previous_end = end
        started = time.perf_counter()
        # Each VAD span is decoded independently, rather than concatenated back
        # into a 30-second window. Whole mode preserves the previous benchmark.
        segments, info = model.transcribe(audio[start:end], language=language, task="transcribe", beam_size=5,
                                       vad_filter=segmentation == "whole",
                                       condition_on_previous_text=False,
                                       initial_prompt=None, hotwords=None)
        decoded = [{"start": s.start + start / SAMPLE_RATE, "end": s.end + start / SAMPLE_RATE,
                    "text": s.text.strip(), "avg_logprob": s.avg_logprob,
                    "no_speech_prob": s.no_speech_prob, "compression_ratio": s.compression_ratio}
                   for s in segments]
        elapsed = time.perf_counter() - started
        output.extend(decoded)
        diagnostics.append({"start": start / SAMPLE_RATE, "end": end / SAMPLE_RATE,
                            "detected_language": getattr(info, "language", None),
                            "language_probability": getattr(info, "language_probability", None),
                            "decode_seconds": elapsed, "output_segments": len(decoded),
                            "text": " ".join(s["text"] for s in decoded)})
    return {"segments": output, "spans": diagnostics,
            "elapsed_seconds": time.perf_counter() - began}
