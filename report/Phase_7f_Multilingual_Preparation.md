# Fase 7f — Persiapan transkripsi Indonesia–Inggris

Tanggal: 19 Oktober 2026.

## Perubahan kebutuhan

Pengguna mengonfirmasi bahwa presentasinya menggunakan campuran bahasa Inggris
dan Indonesia. Model Vosk yang aktif sekarang adalah model Inggris, sedangkan
Whisper base.en dan small.en pada percobaan sebelumnya juga ditujukan untuk
bahasa Inggris. Karena itu, kandidat berikutnya adalah **Whisper small
multibahasa**, bukan small.en.

Ini perubahan kandidat evaluasi, bukan pergantian recognizer live. Aplikasi
desktop masih memakai Vosk dan perintah navigasi bahasa Inggris. Mengunduh model
baru tidak mengubah isi tampilan MIC secara otomatis.

## Yang sudah dikerjakan

- Mengunduh `Systran/faster-whisper-small` dengan revision
  `536b0662742c02347bc0e980a01041f333bce120`.
- Memverifikasi SHA-256 model.bin:
  `3e305921506d8872816023e4c273e75d2419fb89b24da97b4fe7bce14170d671`.
- Memperluas downloader agar menerima small multibahasa.
- Menambahkan language=en, id, atau auto pada inferensi/benchmark. task selalu
  transcribe; initial prompt dan hotwords tetap tidak digunakan.
- Menyimpan bahasa yang dipilih model dan skor deteksinya pada diagnostik tiap
  input decode. Skor tersebut bukan jaminan bahasa atau akurasi transkripsi.
- Menolak pemakaian opsi auto/id dengan nama model English-only pada CLI.
- Menambahkan alat review WAV lokal yang mencetak transkrip dan menyimpan JSON.
  Alat ini tidak membuka mikrofon, mengunggah audio, atau mengirim aksi slide.
- Menyiapkan `Mixed_Language_Test_Script.md` dengan paragraf campuran, tiga
  perintah langsung, dan dua kalimat negatif.
- Pengujian otomatis mencapai **61 tes lulus**, termasuk permintaan task
  transcribe dan language=None untuk deteksi otomatis.

## Batas bukti saat ini

Perbandingan awal menggunakan enam WAV lama, total 192,35 detik. Data ini
berisi percobaan perintah Inggris dan belum memiliki referensi lengkap ucapan
Indonesia–Inggris. Hasilnya hanya pemeriksaan regresi awal, **bukan evaluasi
code-switching pengguna**.

Pada mode whole/auto, klip dengan referensi lengkap 12 kata menghasilkan tiga
substitusi, WER 25%. Total decode enam klip sekitar 49,75 detik (RTF 0,259),
di luar pemuatan model. Lima input dipilih sebagai en dan satu input pendek
sebagai id dengan skor sekitar 0,425. Pilihan id itu tidak membuktikan bahwa
bahasa sumber benar-benar Indonesia; referensi manusia masih diperlukan.

Mode whole juga menghasilkan pengulangan next slide yang berlebihan pada klip
panjang. Keluaran tersebut tidak boleh dianggap transkripsi yang andal atau
dipakai untuk menjalankan aksi. Kemampuan model multibahasa tidak otomatis
menyelesaikan masalah segmentasi, salah kata, dan pengulangan.

Mode grouped context juga menyelesaikan keenam klip. Hasil mentah tetap lokal
pada `logs/benchmark-multilingual-small-context.json`; mode whole disimpan pada
`logs/benchmark-multilingual-small-whole.json`.

| small multibahasa / auto | WER pada 12 kata terkonfirmasi | Total waktu decode | RTF |
|---|---:|---:|---:|
| Whole | 25,0% (3 substitusi) | 49,75 s | 0,259 |
| Grouped context | 25,0% (3 substitusi) | 57,62 s | 0,300 |

Grouped context mengurangi rangkaian pengulangan yang terlihat pada klip panjang
dan kembali memuat previous slide, tetapi masih banyak salah kata. Deteksi
bahasa dapat berubah antar-rentang. Hal ini bukan bukti perpindahan bahasa
yang benar tanpa referensi manusia. Uji CLI review pada klip terkonfirmasi juga
berhasil mencetak teks dan menyimpan hasil; tidak ada aksi slide yang dikirim.

Konfigurasi sama dengan fase sebelumnya: CPU int8 empat thread, beam size 5,
condition_on_previous_text=False, tanpa prompt/hotwords. Seluruh generator
dikonsumsi sebelum timer berakhir. Waktu merupakan satu pengukuran offline,
bukan latensi live, dan tidak membuktikan efisiensi gabungan dengan Vosk.
Model belum dipilih sebagai konfigurasi live atau terbukti akurat untuk campuran
bahasa pengguna.

## Penggunaan untuk pengujian berikutnya

Rekam sekali mengikuti script campuran melalui opsi Record input for diagnosis
pada aplikasi desktop, kemudian Stop. Nilai WAV dengan:

```powershell
.\.venv\Scripts\python.exe -m scripts.transcribe_whisper_wav logs/input-YOUR-SESSION.wav --model small --language auto --output logs/mixed-review.json
```

Untuk membandingkan context, tambahkan `--segmentation context` dan simpan ke
nama output berbeda. Untuk ucapan dominan Indonesia, --language id juga dapat
dicoba sebagai konfigurasi terpisah. Jangan menyamakan hasil model dengan teks
referensi; konfirmasikan ucapan sebenarnya terlebih dahulu.

Auto memilih bahasa per input decode, bukan jaminan deteksi per kata. Walaupun
task=transcribe meminta transkripsi alih-alih terjemahan, pergantian bahasa di
dalam satu kalimat masih dapat salah dikenali atau dirender ke bahasa dominan.
Belum ada bukti akurasi campuran bahasa, beban gabungan live, atau latensi 200 ms.

## Sumber

- [Model card Systran small multibahasa](https://huggingface.co/Systran/faster-whisper-small).
- [Dokumentasi faster-whisper](https://github.com/SYSTRAN/faster-whisper).
