"""Download the official Apache-2.0 English model; no audio leaves this computer."""

import argparse
import shutil
import urllib.request
import zipfile

from app.config import DEFAULT_MODEL_PROFILE, MODEL_PROFILES, model_path


def download(profile=DEFAULT_MODEL_PROFILE):
    model_dir = model_path(profile)
    model_name = MODEL_PROFILES[profile]["name"]
    model_url = f"https://alphacephei.com/vosk/models/{model_name}.zip"
    if (model_dir / "am" / "final.mdl").is_file():
        print(f"Model already installed: {model_dir}")
        return
    model_dir.parent.mkdir(parents=True, exist_ok=True)
    archive = model_dir.parent / f"{model_name}.zip"
    temporary = archive.with_suffix(".zip.part")
    print(f"Downloading {profile} English model (~{MODEL_PROFILES[profile]['size_mb']} MB): {model_url}", flush=True)
    request = urllib.request.Request(model_url, headers={"User-Agent": "VoiceSlideUniversityPrototype/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output)
    temporary.replace(archive)
    root = model_dir.parent.resolve()
    with zipfile.ZipFile(archive) as model_zip:
        # Check all archive members before writing any file.
        for member in model_zip.infolist():
            target = (root / member.filename).resolve()
            if not target.is_relative_to(root) or not member.filename.startswith(model_name + "/"):
                raise ValueError("Unexpected path in model archive")
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Symbolic links are not allowed in model archive")
        model_zip.extractall(root)
    if not (model_dir / "am" / "final.mdl").is_file():
        raise RuntimeError("Downloaded archive does not contain the acoustic model")
    print(f"Model installed: {model_dir}")
    print("Source/license: https://alphacephei.com/vosk/models (Apache 2.0)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=MODEL_PROFILES, default=DEFAULT_MODEL_PROFILE)
    args = parser.parse_args()
    download(args.profile)


if __name__ == "__main__":
    main()
