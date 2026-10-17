"""
config.py — SATU tempat untuk semua pengaturan proyek.

Semua file lain meng-import nilai dari sini, bukan menulis angkanya sendiri.
Kalau suatu saat kamu mau mengganti sample rate atau daftar perintah,
cukup ubah di file ini saja.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Lokasi folder
# ---------------------------------------------------------------------------
# __file__ = .../voice-slide/app/config.py
# .parent  = .../voice-slide/app
# .parent  = .../voice-slide          <- ini akar proyek
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data" / "speech_commands"   # hasil ekstrak dataset
REPORT_DIR = PROJECT_ROOT / "report"                   # bahan untuk laporan

# ---------------------------------------------------------------------------
# Format audio
# ---------------------------------------------------------------------------
SAMPLE_RATE = 16_000      # Speech Commands direkam 16 kHz
CLIP_SECONDS = 1.0        # setiap klip dataset panjangnya maksimal 1 detik
CLIP_SAMPLES = int(SAMPLE_RATE * CLIP_SECONDS)   # = 16000 sampel

# ---------------------------------------------------------------------------
# Kosakata
# ---------------------------------------------------------------------------
# 20 kata perintah yang dipakai aplikasi
COMMANDS = [
    "right", "left",            # navigasi: slide berikut / sebelumnya
    "up", "down",               # lompat ke slide pertama / terakhir
    "go", "stop",               # mulai presentasi / layar hitam
    "on", "off",                # laser pointer nyala / mati
    "yes", "no",                # konfirmasi
    "zero", "one", "two", "three", "four",
    "five", "six", "seven", "eight", "nine",   # angka untuk "go <angka>"
]

WAKE_WORD = "marvin"            # hanya untuk eksperimen dataset lama, bukan prefix aplikasi

# Kelas khusus (bukan kata di dataset, tapi label buatan kita)
UNKNOWN = "_unknown_"           # semua kata lain di dataset digabung jadi satu kelas
SILENCE = "_silence_"           # potongan dari rekaman noise latar

BACKGROUND_NOISE_DIR = "_background_noise_"   # nama folder noise di dataset

# Semua label yang akan dikenali model: 20 + 1 + 2 = 23 kelas
ALL_LABELS = COMMANDS + [WAKE_WORD, UNKNOWN, SILENCE]


def class_role(word: str) -> str:
    """Kembalikan peran sebuah folder kata di dataset: command / wake / unknown."""
    if word in COMMANDS:
        return "command"
    if word == WAKE_WORD:
        return "wake"
    return "unknown"


# Prototipe ASR pretrained: kosakata bebas, bukan classifier 23 kelas di atas.
COMMAND_PREFIX = "hey slides"
MODEL_PROFILES = {
    "light": {"name": "vosk-model-small-en-us-0.15", "size_mb": 40,
              "label": "Light English (40 MB)", "queue_blocks": 12, "max_queue_ms": 500},
    "balanced": {"name": "vosk-model-en-us-0.22-lgraph", "size_mb": 128,
                 "label": "Balanced English (experimental)", "queue_blocks": 48, "max_queue_ms": 1000},
}
DEFAULT_MODEL_PROFILE = "light"


def model_path(profile=DEFAULT_MODEL_PROFILE):
    if profile not in MODEL_PROFILES:
        raise ValueError(f"Unknown ASR profile: {profile}")
    return PROJECT_ROOT / "models" / MODEL_PROFILES[profile]["name"]


MODEL_NAME = MODEL_PROFILES[DEFAULT_MODEL_PROFILE]["name"]
MODEL_DIR = PROJECT_ROOT / "models" / MODEL_NAME
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
LOG_DIR = PROJECT_ROOT / "logs"
AUDIO_BLOCK_SAMPLES = 400  # 25 ms pada 16 kHz
