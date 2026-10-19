"""Explicit model download only. Never reads or uploads recordings."""

import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.request import urlopen

from huggingface_hub import HfApi, snapshot_download


def sha256_file(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("base.en", "small.en", "small"), default="base.en")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    repo = f"Systran/faster-whisper-{args.model}"
    info = HfApi().model_info(repo, files_metadata=True)
    revision = info.sha
    expected_hash = next(file.lfs.sha256 for file in info.siblings if file.rfilename == "model.bin")
    destination = root / "models" / f"faster-whisper-{args.model}"
    snapshot_download(repo, revision=revision, local_dir=destination,
                      allow_patterns=["config.json", "tokenizer.json", "vocabulary.*", "preprocessor_config.json"],
                      max_workers=2)
    weights = destination / "model.bin"
    if not weights.exists() or sha256_file(weights) != expected_hash:
        # Standard HTTPS avoids transfer-helper stalls seen on the demo laptop.
        # A fresh query also avoids reusing an expired cached signed redirect.
        url = f"https://huggingface.co/{repo}/resolve/{revision}/model.bin?download=true&request={time.time_ns()}"
        temporary = destination / "model.bin.partial"
        digest = hashlib.sha256()
        total, last_report = 0, time.monotonic()
        with urlopen(url, timeout=60) as response, temporary.open("wb") as output:
            while block := response.read(1024 * 1024):
                output.write(block)
                digest.update(block)
                total += len(block)
                if time.monotonic() - last_report >= 5:
                    print(f"Downloaded {total / 1_000_000:.1f} MB", flush=True)
                    last_report = time.monotonic()
        if digest.hexdigest() != expected_hash:
            raise ValueError("Downloaded model failed the published LFS SHA256 check")
        temporary.replace(weights)
    actual_hash = sha256_file(weights)
    if actual_hash != expected_hash:
        raise ValueError("Downloaded model failed the published LFS SHA256 check")
    provenance = {"repository": repo, "revision": revision, "model_sha256": actual_hash}
    (destination / "evaluation-provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(provenance))
    print(destination)


if __name__ == "__main__":
    main()
