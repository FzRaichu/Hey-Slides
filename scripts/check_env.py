"""
LANGKAH 1a — Cek lingkungan kerja.

Jalankan dari dalam folder voice-slide:
    python -m scripts.check_env

Script ini TIDAK mengubah apa pun. Ia hanya memeriksa:
  1. versi Python
  2. library yang dibutuhkan sudah terpasang
  3. mikrofon terdeteksi
  4. GPU NVIDIA (belum wajib di langkah ini)
  5. dataset sudah diekstrak di tempat yang benar
"""

import importlib
import shutil
import subprocess
import sys

from app import config

OK, FAIL, WARN = "[OK]  ", "[GAGAL]", "[CATATAN]"
problems = []   # kumpulan hal yang wajib diperbaiki


def check_python():
    v = sys.version_info
    label = f"Python {v.major}.{v.minor}.{v.micro}"
    if (v.major, v.minor) < (3, 10):
        print(FAIL, label, "- butuh minimal Python 3.10")
        problems.append("Pasang Python 3.11")
    elif (v.major, v.minor) >= (3, 13):
        print(WARN, label, "- bisa jalan, tapi 3.11 paling aman untuk librosa")
    else:
        print(OK, label)


def check_libraries():
    # nama import -> nama paket untuk pip
    required = {
        "numpy": "numpy",
        "soundfile": "soundfile",
        "librosa": "librosa",
        "sklearn": "scikit-learn",
        "sounddevice": "sounddevice",
    }
    for module, pip_name in required.items():
        try:
            mod = importlib.import_module(module)
            print(OK, f"{pip_name} {getattr(mod, '__version__', '')}")
        except ImportError:
            print(FAIL, f"{pip_name} belum terpasang")
            problems.append(f"pip install {pip_name}")
        except OSError as e:
            # contoh: sounddevice terpasang tapi library PortAudio-nya tidak ditemukan
            print(FAIL, f"{pip_name} terpasang tapi gagal dimuat: {e}")
            problems.append(f"pip install --force-reinstall {pip_name}")


def check_microphone():
    try:
        import sounddevice as sd
    except (ImportError, OSError):
        return  # sudah dilaporkan di check_libraries
    try:
        devices = sd.query_devices()
        inputs = [d for d in devices if d["max_input_channels"] > 0]
    except Exception as e:  # driver audio bermasalah
        print(FAIL, f"tidak bisa membaca perangkat audio: {e}")
        problems.append("Periksa driver audio / izin mikrofon di Windows")
        return
    if not inputs:
        print(FAIL, "tidak ada mikrofon terdeteksi")
        problems.append("Sambungkan / izinkan mikrofon")
        return
    default_in = sd.default.device[0]
    name = devices[default_in]["name"] if default_in is not None and default_in >= 0 else "?"
    print(OK, f"{len(inputs)} perangkat input; default: {name}")


def check_gpu():
    if shutil.which("nvidia-smi") is None:
        print(WARN, "nvidia-smi tidak ditemukan (GPU baru dibutuhkan di Tingkat T2/T3)")
        return
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
        capture_output=True, text=True,
    )
    print(OK, "GPU:", out.stdout.strip() or "(tidak terbaca)")


def check_dataset():
    d = config.DATA_DIR
    if not d.exists():
        print(FAIL, f"folder dataset tidak ada: {d}")
        problems.append("Unduh & ekstrak Speech Commands ke data/speech_commands")
        return

    must_exist = ["validation_list.txt", "testing_list.txt", config.BACKGROUND_NOISE_DIR]
    must_exist += config.COMMANDS + [config.WAKE_WORD]
    missing = [name for name in must_exist if not (d / name).exists()]

    if missing:
        print(FAIL, f"dataset tidak lengkap, hilang: {', '.join(missing[:5])}"
                    + (" ..." if len(missing) > 5 else ""))
        problems.append("Ekstrak ulang dataset; pastikan isinya langsung di data/speech_commands, "
                        "bukan di subfolder lain")
    else:
        n_words = sum(1 for p in d.iterdir() if p.is_dir() and p.name != config.BACKGROUND_NOISE_DIR)
        print(OK, f"dataset ditemukan: {n_words} folder kata di {d}")


def main():
    print("=== Cek lingkungan Voice Slide Control ===\n")
    print("-- Python");      check_python()
    print("\n-- Library");   check_libraries()
    print("\n-- Mikrofon");  check_microphone()
    print("\n-- GPU");       check_gpu()
    print("\n-- Dataset");   check_dataset()

    print("\n=== Ringkasan ===")
    if problems:
        print("Perbaiki dulu:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("Semua siap. Lanjut: python -m scripts.explore_dataset")


if __name__ == "__main__":
    main()
