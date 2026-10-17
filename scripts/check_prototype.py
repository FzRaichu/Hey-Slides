"""Check the pretrained-ASR prototype, not the older Speech Commands experiment."""

import importlib.metadata
import sys

from app.config import MODEL_DIR


def main():
    errors = []
    print("Python:", sys.version.split()[0])
    for package in ("numpy", "vosk", "sounddevice"):
        try:
            print(package + ":", importlib.metadata.version(package))
        except importlib.metadata.PackageNotFoundError:
            errors.append(f"Install {package}")
    try:
        import tkinter
        print("Tk:", tkinter.Tcl().eval("info patchlevel"))
    except Exception as exc:
        errors.append(f"Tk unavailable: {exc}")
    if (MODEL_DIR / "am" / "final.mdl").is_file():
        print("Local English model:", MODEL_DIR)
    else:
        errors.append("Run python -m scripts.download_model")
    try:
        import sounddevice as sd
        sd.check_input_settings(samplerate=16000, channels=1, dtype="int16")
        print("Default microphone: supports 16 kHz mono PCM16")
    except Exception as exc:
        errors.append(f"Microphone settings: {exc}")
    if errors:
        for message in errors:
            print("CHECK:", message)
        return 1
    print("Ready. Run python -m app.main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
