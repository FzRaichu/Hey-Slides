"""Summarize live voice latency from the app's session logs.

The app writes one "latency" record per final recognition result to
logs/session-*.jsonl (see Prototype.record_latency). All values are measured from
the end of the last recognized word (Vosk word timestamps mapped to the time the
audio block reached the app):

  endpoint_ms  word end -> recognizer emitted the final result
  l1_ms        word end -> text shown in the transcript
  l2_ms        word end -> slide changed and redrawn (executed commands only)

Hardware/driver input latency before the audio callback is not included.

Examples:
  python -m scripts.latency_report                      # all logs/session-*.jsonl
  python -m scripts.latency_report logs/session-X.jsonl --out logs/latency-summary.md
"""

import argparse
import csv
import json
from pathlib import Path
import statistics

from app import config

TARGET_MS = 200


def load(paths):
    records, endpoints = [], set()
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("kind") == "start" and item.get("endpoint_silence") is not None:
                endpoints.add(f"{item['endpoint_silence']} s")
            if item.get("kind") == "latency":
                item["file"] = path.name
                records.append(item)
    return records, sorted(endpoints)


def stats(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    p90 = values[min(len(values) - 1, round(0.9 * (len(values) - 1)))]
    return {"n": len(values), "median": statistics.median(values), "p90": p90, "min": values[0],
            "max": values[-1], "under_target": sum(v <= TARGET_MS for v in values) / len(values)}


def row(name, s):
    if s is None:
        return f"| {name} | 0 | - | - | - | - | - |"
    return (f"| {name} | {s['n']} | {s['median']:.0f} | {s['p90']:.0f} | {s['min']:.0f} | {s['max']:.0f} | "
            f"{s['under_target'] * 100:.0f}% |")


def build_report(records, endpoints=()):
    commands = [r for r in records if r.get("source") == "command recognizer"]
    executed = [r for r in commands if r.get("l2_ms") is not None]
    speech = [r for r in records if r.get("source") == "microphone"]
    lines = [
        "# Latensi suara Hey Slides",
        "",
        f"Sumber: {len({r['file'] for r in records})} file log, {len(records)} sampel. "
        "Semua angka dalam ms, diukur dari akhir kata terakhir (timestamp kata Vosk). "
        f"Kolom terakhir = persentase sampel <= {TARGET_MS} ms.",
        "",
        f"| Metrik | n | median | p90 | min | max | <= {TARGET_MS} ms |",
        "|---|---|---|---|---|---|---|",
        row("L2 perintah dijalankan (kata -> slide pindah)", stats(r["l2_ms"] for r in executed)),
        row("L1 perintah (kata -> teks PERINTAH tampil)", stats(r.get("l1_ms") for r in commands)),
        row("  bagian tunggu endpoint Vosk (perintah)", stats(r.get("endpoint_ms") for r in commands)),
        row("L1 ucapan umum (kata -> teks UCAPAN tampil)", stats(r.get("l1_ms") for r in speech)),
        row("  bagian tunggu endpoint Vosk (ucapan)", stats(r.get("endpoint_ms") for r in speech)),
        "",
        "Catatan: Vosk baru mengeluarkan hasil final setelah jeda hening (endpoint.rule2.min-trailing-silence; "
        f"dipakai di sesi ini: {', '.join(endpoints) or 'tidak tercatat, 0,5 s untuk log sebelum 23 Nov'}). "
        "Bagian 'tunggu endpoint' menunjukkan porsi itu. Latensi input perangkat keras sebelum callback "
        "audio tidak termasuk.",
    ]
    outcomes = {}
    for r in commands:
        outcomes[r.get("outcome")] = outcomes.get(r.get("outcome"), 0) + 1
    if outcomes:
        lines += ["", "Hasil perintah: " + ", ".join(f"{k} = {v}" for k, v in sorted(outcomes.items()))]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("logs", type=Path, nargs="*", help="session JSONL files (default: logs/session-*.jsonl)")
    parser.add_argument("--out", type=Path, help="write the Markdown summary here")
    parser.add_argument("--csv", type=Path, help="write every latency sample as CSV")
    args = parser.parse_args()

    paths = args.logs or sorted(config.LOG_DIR.glob("session-*.jsonl"))
    records, endpoints = load(paths)
    if not records:
        raise SystemExit("No latency records found. Run the app, click Mulai mendengarkan, speak "
                         "some commands, then Stop. Logs are written to " + str(config.LOG_DIR))
    report = build_report(records, endpoints)
    print(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"Saved {args.out}")
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        fields = ["file", "at", "source", "text", "action", "outcome", "endpoint_ms", "l1_ms", "l2_ms"]
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)
        print(f"Saved {args.csv}")


if __name__ == "__main__":
    main()
