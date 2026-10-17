"""Explicit model download only. Never reads or uploads recordings."""

import hashlib
import json
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download


def main():
    root = Path(__file__).resolve().parents[1]
    repo = "Systran/faster-whisper-base.en"
    info = HfApi().model_info(repo, files_metadata=True)
    revision = info.sha
    expected_hash = next(file.lfs.sha256 for file in info.siblings if file.rfilename == "model.bin")
    destination = root / "models" / "faster-whisper-base.en"
    snapshot_download(repo, revision=revision, local_dir=destination,
                      allow_patterns=["config.json", "model.bin", "tokenizer.json", "vocabulary.*", "preprocessor_config.json"],
                      max_workers=2)
    actual_hash = hashlib.sha256((destination / "model.bin").read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError("Downloaded model failed the published LFS SHA256 check")
    provenance = {"repository": repo, "revision": revision, "model_sha256": actual_hash}
    (destination / "evaluation-provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(provenance))
    print(destination)


if __name__ == "__main__":
    main()
