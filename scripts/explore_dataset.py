"""
LANGKAH 1b — Kenali dataset sebelum melatih apa pun.

Jalankan dari dalam folder voice-slide:
    python -m scripts.explore_dataset

Yang dicari tahu:
  1. berapa sampel per kata, dan berapa yang masuk train / validation / test
  2. apakah split resmi benar-benar memisahkan PEMBICARA (tidak ada orang yang sama
     di train dan test) -> alasan kita wajib memakai split resmi
  3. format audio: sample rate & berapa klip yang lebih pendek dari 1 detik
  4. ketidakseimbangan kelas: kelas _unknown_ akan jauh lebih besar

Hasilnya dicetak ke layar DAN disimpan ke report/dataset_summary.csv
(bukti untuk Bab 5 laporan: "Dataset/audio samples").
"""

import csv
from collections import Counter

import soundfile as sf

from app import config


def speaker_of(rel_path: str) -> str:
    """'right/0a7c2a8d_nohash_0.wav' -> '0a7c2a8d' (ID pembicara ada di nama file)."""
    filename = rel_path.split("/")[-1]
    return filename.split("_nohash_")[0]


def load_list(name: str) -> set:
    """Baca validation_list.txt / testing_list.txt jadi himpunan path relatif."""
    path = config.DATA_DIR / name
    with open(path, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def which_split(rel: str, val: set, test: set) -> str:
    # Aturan resmi dataset: yang tidak tercantum di kedua daftar = data latih
    if rel in test:
        return "test"
    if rel in val:
        return "val"
    return "train"


def main():
    d = config.DATA_DIR
    val, test = load_list("validation_list.txt"), load_list("testing_list.txt")

    words = sorted(p.name for p in d.iterdir()
                   if p.is_dir() and p.name != config.BACKGROUND_NOISE_DIR)

    rows = []                                          # satu baris per kata
    speakers = {"train": set(), "val": set(), "test": set()}
    sample_rates = Counter()
    short_clips = 0
    total = 0

    print(f"Membaca {len(words)} folder kata (bisa 1-3 menit)...\n")
    for word in words:
        counts = Counter()
        for wav in sorted((d / word).glob("*.wav")):
            rel = wav.relative_to(d).as_posix()        # pakai '/' walau di Windows
            split = which_split(rel, val, test)
            counts[split] += 1
            speakers[split].add(speaker_of(rel))

            info = sf.info(wav)                        # hanya baca header, cepat
            sample_rates[info.samplerate] += 1
            if info.frames < config.CLIP_SAMPLES:
                short_clips += 1
            total += 1

        rows.append({
            "word": word,
            "role": config.class_role(word),
            "train": counts["train"],
            "val": counts["val"],
            "test": counts["test"],
            "total": sum(counts.values()),
        })

    # ------------------------------------------------------------------ tabel
    print(f"{'kata':<10}{'peran':<9}{'train':>7}{'val':>7}{'test':>7}{'total':>8}")
    print("-" * 48)
    for role in ("command", "wake", "unknown"):
        for r in rows:
            if r["role"] == role:
                print(f"{r['word']:<10}{r['role']:<9}{r['train']:>7}{r['val']:>7}"
                      f"{r['test']:>7}{r['total']:>8}")

    # ------------------------------------------------- ringkasan per kelompok
    def total_of(role):
        return sum(r["total"] for r in rows if r["role"] == role)

    n_cmd = total_of("command")
    n_cmd_words = sum(1 for r in rows if r["role"] == "command")
    n_unknown = total_of("unknown")
    n_unknown_words = sum(1 for r in rows if r["role"] == "unknown")

    print("\n=== Ringkasan ===")
    print(f"Total klip                 : {total}")
    print(f"Sample rate                : {dict(sample_rates)}")
    print(f"Klip < 1 detik             : {short_clips} "
          f"({short_clips / max(total, 1):.1%}) -> perlu padding di Langkah 2")
    print(f"Kata perintah              : {n_cmd_words} kata, {n_cmd} klip "
          f"(rata-rata {n_cmd // max(n_cmd_words, 1)} per kata)")
    print(f"Kata lain -> {config.UNKNOWN:<14}: {n_unknown_words} kata digabung, {n_unknown} klip")
    if n_cmd_words:
        ratio = n_unknown / (n_cmd / n_cmd_words)
        print(f"  -> kelas {config.UNKNOWN} {ratio:.1f}x lebih besar dari satu kelas perintah."
              " Harus di-downsample saat training.")

    # ----------------------------------------------- bukti pemisahan pembicara
    print("\n=== Apakah split resmi memisahkan pembicara? ===")
    for s in ("train", "val", "test"):
        print(f"Pembicara di {s:<5}: {len(speakers[s])}")
    overlap_tt = speakers["train"] & speakers["test"]
    overlap_tv = speakers["train"] & speakers["val"]
    print(f"Pembicara yang muncul di train DAN test : {len(overlap_tt)}")
    print(f"Pembicara yang muncul di train DAN val  : {len(overlap_tv)}")
    if not overlap_tt and not overlap_tv:
        print("-> Tidak ada kebocoran pembicara. Model diuji pada suara orang yang BELUM pernah didengar.")

    # ------------------------------------------------------ noise latar
    noise_dir = d / config.BACKGROUND_NOISE_DIR
    print(f"\n=== {config.BACKGROUND_NOISE_DIR} (sumber kelas {config.SILENCE}) ===")
    for wav in sorted(noise_dir.glob("*.wav")):
        info = sf.info(wav)
        print(f"{wav.name:<28}{info.frames / info.samplerate:>7.1f} detik")

    # ------------------------------------------------------ simpan CSV
    config.REPORT_DIR.mkdir(exist_ok=True)
    out = config.REPORT_DIR / "dataset_summary.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["word", "role", "train", "val", "test", "total"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nTersimpan: {out}")


if __name__ == "__main__":
    main()
