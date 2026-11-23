"""Replay a WAV through the live command pipeline with different Vosk endpoint
silence settings, and report how long each command waits before it is emitted.

No microphone and no presentation are used. Each variant runs the same code path
as the app (general recognizer + focused command recognizer + endpoint alignment
+ command parser), fed in 25 ms blocks.

endpoint_wait_ms = (stream position when the command result was emitted
                    - end of its last word) in audio time.
This is the part of L1/L2 that Vosk's trailing-silence endpoint adds; live L1/L2
also include decode time per block, the UI poll interval and slide redraw.
partial_wait_ms = when the complete command text first appeared as a partial
(negative = before the word-end timestamp). The app currently acts only on finals.

Vosk 0.3.45 reads the endpoint rules from conf/model.conf when the model loads,
so each variant is a hard-linked copy of the model with only model.conf rewritten
(under logs/endpoint-models/). The source model is never modified by this script.

Example:
  python -m scripts.endpoint_sweep logs/commands.wav --silence 0.5 0.3 0.2 \
      --expect next,previous,goto:3 --out logs/endpoint-sweep.json
"""

import argparse
import difflib
import json
import os
from pathlib import Path
import shutil
import statistics
import wave

from app import config
from app.command_recognition import CommandRecognizer, align_command_endpoint
from app.commands import CommandParser
from app.recognition import StreamingRecognizer, endpoint_conf, load_model

def variant_model(source: Path, silence: float, workdir: Path) -> Path:
    """Model dir whose conf/model.conf uses `silence` (the app may have rewritten the
    source conf already, so the source is only reused when it matches exactly)."""
    text = (source / "conf" / "model.conf").read_text(encoding="utf-8")
    updated = endpoint_conf(text, silence)
    if updated is None:
        raise ValueError(f"endpoint rules 2-4 not found in {source / 'conf' / 'model.conf'}")
    if updated == text:
        return source
    target = workdir / f"{source.name}-endpoint-{silence:.2f}"
    if not target.exists():
        def link_or_copy(src, dst):
            try:
                os.link(src, dst)
            except OSError:
                shutil.copy2(src, dst)
        shutil.copytree(source, target, copy_function=link_or_copy)
    conf = target / "conf" / "model.conf"
    conf.unlink()  # break the hard link first so the source model.conf stays untouched
    conf.write_text(updated, encoding="utf-8")
    return target


def read_pcm(path: Path, tail_silence_s=1.5) -> bytes:
    with wave.open(str(path), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, config.SAMPLE_RATE):
            raise ValueError(f"{path} must be mono 16-bit PCM at {config.SAMPLE_RATE} Hz")
        pcm = audio.readframes(audio.getnframes())
    # Trailing silence so the last command can reach its endpoint, as it would live.
    return pcm + bytes(int(tail_silence_s * config.SAMPLE_RATE) * 2)


def replay(model, pcm: bytes, require_prefix=False):
    general = StreamingRecognizer(model, config.SAMPLE_RATE)
    command = CommandRecognizer(model, config.SAMPLE_RATE, require_prefix=require_prefix)
    parser = CommandParser(require_prefix=require_prefix)
    rate, block = config.SAMPLE_RATE, config.AUDIO_BLOCK_SAMPLES * 2
    # Same as the live session. Only command-decoder word times are used below, so the
    # warm-up offset in the general recognizer's times does not matter here.
    general.warm_up(rate)
    base = fed = 0
    results = []
    partial_seen = {}  # partial text -> stream position when the command decoder first showed it
    for start in range(0, len(pcm), block):
        chunk = pcm[start:start + block]
        fed += len(chunk) // 2
        event = general.feed(chunk)
        command_event = command.feed(chunk)
        if command_event["kind"] == "partial" and command_event["text"]:
            partial_seen.setdefault(command_event["text"], fed)
        event_base = base
        command_event = align_command_endpoint(event, command_event, command)
        if event["kind"] == "final":
            base = fed
        if command_event["kind"] != "final" or not command_event["text"]:
            continue
        partial_at = partial_seen.get(command_event["text"])
        partial_seen = {}
        ends = [float(word["end"]) for word in command_event.get("words", []) if "end" in word]
        word_end = event_base + round(max(ends) * rate) if ends else None
        decision = (parser.accept(command_event["text"], f"replay:{len(results)}")
                    if command_event.get("eligible") else None)
        action = decision.action if decision else None
        if action == "goto":
            action = f"goto:{decision.target_slide}"
        results.append({"text": command_event["text"], "eligible": command_event.get("eligible"),
                        "reason": command_event.get("reason"), "action": action,
                        "word_end_s": None if word_end is None else round(word_end / rate, 3),
                        "emitted_s": round(fed / rate, 3),
                        "endpoint_wait_ms": None if word_end is None else round((fed - word_end) / rate * 1000, 1),
                        # When the full command text first appeared as a partial (could act here, before the endpoint).
                        "partial_wait_ms": (None if word_end is None or partial_at is None
                                            else round((partial_at - word_end) / rate * 1000, 1))})
    return results


def score(actions, expected):
    """Align executed actions with the expected sequence (one missed command must not
    shift every later one). Returns correct, substituted, missed, extra."""
    matcher = difflib.SequenceMatcher(a=expected, b=actions, autojunk=False)
    counts = {"correct": 0, "substituted": 0, "missed": 0, "extra": 0}
    for op, a0, a1, b0, b1 in matcher.get_opcodes():
        if op == "equal":
            counts["correct"] += a1 - a0
        elif op == "replace":
            paired = min(a1 - a0, b1 - b0)
            counts["substituted"] += paired
            counts["missed"] += (a1 - a0) - paired
            counts["extra"] += (b1 - b0) - paired
        elif op == "delete":
            counts["missed"] += a1 - a0
        elif op == "insert":
            counts["extra"] += b1 - b0
    return counts


def summary(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return {"n": 0}
    p90 = values[min(len(values) - 1, round(0.9 * (len(values) - 1)))]
    return {"n": len(values), "median": round(statistics.median(values), 1), "p90": round(p90, 1),
            "max": round(values[-1], 1)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("wav", type=Path, help="mono 16 kHz 16-bit WAV, e.g. a recording saved by the app")
    parser.add_argument("--silence", type=float, nargs="+", default=[0.5, 0.3, 0.2],
                        help="rule2 trailing silence in seconds (rule3/rule4 scale with it)")
    parser.add_argument("--expect", help="comma list of expected actions in order, e.g. next,previous,goto:3")
    parser.add_argument("--wake", action="store_true", help="require the Hey Slides prefix")
    parser.add_argument("--out", type=Path, help="write all results as JSON")
    args = parser.parse_args()

    pcm = read_pcm(args.wav)
    expected = [item.strip() for item in args.expect.split(",")] if args.expect else None
    source = config.model_path()
    workdir = config.LOG_DIR / "endpoint-models"
    workdir.mkdir(parents=True, exist_ok=True)
    report = {"wav": str(args.wav), "expected": expected, "variants": []}

    print(f"WAV: {args.wav}  ({(len(pcm) // 2) / config.SAMPLE_RATE - 1.5:.1f} s audio)")
    print("| silence (s) | actions | correct | wrong | missed | extra | endpoint wait median | p90 | max | full partial median |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for silence in args.silence:
        results = replay(load_model(variant_model(source, silence, workdir)), pcm, require_prefix=args.wake)
        actions = [item["action"] for item in results if item["action"]]
        counts = score(actions, expected) if expected is not None else None
        waits = summary(item["endpoint_wait_ms"] for item in results if item["action"])
        partial = summary(item["partial_wait_ms"] for item in results if item["action"])
        report["variants"].append({"silence_s": silence, "actions": actions, "score": counts,
                                   "endpoint_wait_ms": waits, "partial_wait_ms": partial, "results": results})
        c = counts or {}
        correct_text = "-" if counts is None else f"{c['correct']}/{len(expected)}"
        print(f"| {silence:.2f} | {len(actions)} | {correct_text} | {c.get('substituted', '-')} | "
              f"{c.get('missed', '-')} | {c.get('extra', '-')} | {waits.get('median', '-')} ms | "
              f"{waits.get('p90', '-')} ms | {waits.get('max', '-')} ms | {partial.get('median', '-')} ms |")
        print(f"|   actions: {', '.join(actions) or '(none)'} | | | | | | | | | |")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
