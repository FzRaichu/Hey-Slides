"""Download the official Apache-2.0 English model; no audio leaves this computer."""

from pathlib import Path
import shutil
import urllib.request
import zipfile

from app.config import MODEL_DIR, MODEL_NAME, MODEL_URL


def main():
    if (MODEL_DIR / "am" / "final.mdl").is_file():
        print(f"Model already installed: {MODEL_DIR}")
        return
    MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
    archive = MODEL_DIR.parent / f"{MODEL_NAME}.zip"
    temporary = archive.with_suffix(".zip.part")
    print(f"Downloading official English model (~40 MB): {MODEL_URL}", flush=True)
    request = urllib.request.Request(MODEL_URL, headers={"User-Agent": "VoiceSlideUniversityPrototype/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output)
    temporary.replace(archive)
    root = MODEL_DIR.parent.resolve()
    with zipfile.ZipFile(archive) as model_zip:
        # Check all archive members before writing any file.
        for member in model_zip.infolist():
            target = (root / member.filename).resolve()
            if not target.is_relative_to(root) or not member.filename.startswith(MODEL_NAME + "/"):
                raise ValueError("Unexpected path in model archive")
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Symbolic links are not allowed in model archive")
        model_zip.extractall(root)
    if not (MODEL_DIR / "am" / "final.mdl").is_file():
        raise RuntimeError("Downloaded archive does not contain the acoustic model")
    print(f"Model installed: {MODEL_DIR}")
    print("Source/license: https://alphacephei.com/vosk/models (Apache 2.0)")


if __name__ == "__main__":
    main()
