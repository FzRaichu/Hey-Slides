"""Entry point for the packaged Windows build (PyInstaller).

During development keep using: python -m app.main

    HeySlides.exe              -> open the app
    HeySlides.exe --self-test  -> load model, check microphone and
                                  PowerPoint COM, write logs/self-test.txt,
                                  exit code 0 (ok) or 1 (problem)
"""

import sys


def self_test() -> int:
    from app import config

    lines, ok = [], True

    def check(name, fn):
        nonlocal ok
        try:
            lines.append(f"[OK]   {name}: {fn()}")
        except Exception as exc:  # report every failure, keep going
            ok = False
            lines.append(f"[FAIL] {name}: {type(exc).__name__}: {exc}")

    def model():
        from app.recognition import StreamingRecognizer, load_model
        recognizer = StreamingRecognizer(load_model(config.model_path()), config.SAMPLE_RATE)
        recognizer.feed(bytes(config.SAMPLE_RATE * 2))  # 1 s of silence, PCM16
        return config.model_path()

    def microphone():
        import sounddevice as sd
        sd.check_input_settings(samplerate=config.SAMPLE_RATE, channels=1, dtype="int16")
        return sd.query_devices(kind="input")["name"]

    def powerpoint_com():
        import win32com.client  # noqa: F401
        return "pywin32 COM available (PowerPoint itself not required for this check)"

    check("Project root", lambda: config.PROJECT_ROOT)
    check("Vosk model", model)
    check("Microphone 16 kHz mono", microphone)
    check("PowerPoint COM", powerpoint_com)
    lines.append("RESULT: " + ("PASS" if ok else "FAIL"))

    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    (config.LOG_DIR / "self-test.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    from app.main import main
    main()
