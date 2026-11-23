# Evaluasi latensi suara: sesi 23 November 2026

## Ringkasan

- **Akurasi perintah (live):** 18 dari 20 perintah dijalankan dengan benar (90%). Tidak ada aksi salah, 2 perintah terlewat, dan tidak ada aksi palsu selama sesi.
- **L2 (akhir kata → slide berpindah):** median **1032 ms**, p90 1103 ms. Target 200 ms **tidak tercapai** dengan desain saat ini.
- Sekitar **93%** dari L2 (median 957 ms) adalah **waktu tunggu endpoint Vosk**, yaitu jeda hening sebelum hasil final keluar. Pemrosesan, tampilan, dan pergantian slide hanya menambah sekitar 50–75 ms.
- Teks perintah lengkap sudah muncul sebagai **hasil partial ±190–215 ms** setelah akhir kata. Target 200 ms secara teknis bisa didekati kalau aksi dijalankan dari partial yang stabil, dengan risiko aksi palsu yang lebih tinggi. Opsi ini belum diimplementasikan.
- **Jeda endpoint 0,3 s** (default 0,5 s) memberi kompromi terbaik pada rekaman ini: 19/20 benar dan waktu tunggu turun ±280 ms (median 659 ms). Jeda 0,2 s dan 0,1 s lebih cepat, tetapi lebih banyak perintah yang terlewat.

## Kondisi pengujian

| Item | Nilai |
|---|---|
| Pembicara | 1 anggota kelompok (bukan target user eksternal) |
| Perangkat | Laptop Windows 11, Microphone Array (Realtek), mikrofon bawaan |
| Lingkungan | Ruangan dalam ruang, tanpa pengukuran noise formal |
| Level input | median −42 dBFS, maksimum −29 dBFS, tanpa clipping |
| Aplikasi | HeySlides.exe (build 23 Nov), Light English `vosk-model-small-en-us-0.15`, Direct commands + Command assist, target Demo slides |
| Skrip | 20 perintah: next/previous/go to slide N, diucapkan dengan jeda ±2 s |
| Data mentah | `session-20261123-081737-ea14a3.jsonl` dan `input-2e866eb3….wav` **terhapus** saat exe di-build ulang (PyInstaller mengosongkan `dist\HeySlides`; skrip build sudah diperbaiki). Yang tersisa secara lokal: `logs/latency.csv` (semua sampel latensi sesi live), `logs/latency-summary.md`, `logs/endpoint-sweep.json` (hasil per perintah tiap jeda). Hasil replay 0,3 s di bawah diukur sebelum file terhapus. |

## Definisi pengukuran

Semua latensi diukur dari **akhir kata terakhir** perintah. Waktu itu diambil dari timestamp kata Vosk, lalu dipetakan ke saat blok audio 25 ms tiba di aplikasi. Latensi driver/perangkat keras sebelum callback audio tidak termasuk.

- **endpoint**: akhir kata → Vosk mengeluarkan hasil final
- **L1**: akhir kata → teks tampil di transkrip
- **L2**: akhir kata → slide berpindah dan panel slide digambar ulang

## Hasil live (latency_report)

| Metrik | n | median | p90 | min | max | ≤ 200 ms |
|---|---|---|---|---|---|---|
| L2 perintah dijalankan | 18 | 1032 | 1103 | 749 | 1247 | 0% |
| L1 perintah (teks PERINTAH tampil) | 19 | 1008 | 1070 | 724 | 1217 | 0% |
| bagian tunggu endpoint (perintah) | 19 | 957 | 1019 | 676 | 1071 | 0% |
| L1 ucapan umum (teks UCAPAN tampil) | 21 | 1087 | 1170 | 333 | 1216 | 0% |
| bagian tunggu endpoint (ucapan) | 21 | 1029 | 1108 | 309 | 1183 | 0% |

Semua angka dalam ms.

## Analisis error perintah

| # | Diucapkan | Decoder perintah | Decoder umum (UCAPAN) | Hasil |
|---|---|---|---|---|
| 10 | go to slide three | "to slide three" | "no to slide dream" | terlewat: kata "go" tidak terdengar, parser menolak |
| 15 | previous slide | "previous slides" (skor model rendah) | "previous slide" | terlewat: ditolak oleh ambang skor Command assist |

Decoder umum sering salah pada perintah "go to slide N", misalnya "no to slide for" dan "no to slide was". Decoder perintah yang kosakatanya dibatasi tetap memilih perintah yang benar pada 18 dari 20 kasus. Ini mendukung desain dua decoder.

## Sweep jeda endpoint (offline, rekaman yang sama)

`python -m scripts.endpoint_sweep` memutar ulang WAV sesi di atas lewat pipeline yang sama dengan aplikasi live, termasuk warm-up. Pada 0,5 s hasilnya identik dengan sesi live (18/20, dua perintah terlewat yang sama).

| Jeda (s) | Benar | Salah | Terlewat | Ekstra | Tunggu endpoint median | p90 | Partial lengkap median |
|---|---|---|---|---|---|---|---|
| 0,50 (default) | 18/20 | 0 | 2 | 0 | 940 ms | 1000 ms | 215 ms |
| **0,30** | **19/20** | 0 | 1 | 0 | **659 ms** | 740 ms | 190 ms |
| 0,20 | 17/20 | 0 | 3 | 0 | 513 ms | 610 ms | 190 ms |
| 0,10 | 16/20 | 0 | 4 | 0 | 424 ms | 500 ms | 225 ms |

Jeda 0,3 s memperbaiki "go to slide three" pada rekaman ini. Jeda yang lebih pendek membuat perintah pertama terpotong atau tergabung, sehingga lebih banyak yang terlewat. Satu rekaman dari satu pembicara belum cukup untuk memilih nilai final. Sweep ini perlu diulang pada rekaman penguji lain.

## Setelah jeda 0,3 s dipasang sebagai default

Aplikasi sekarang memakai jeda endpoint 0,3 s secara default (Pengaturan → "Jeda akhir perintah"; 0,5 s tetap tersedia). Rekaman yang sama diputar ulang secara real time lewat aplikasi lengkap (mikrofon simulasi, UI, parser, Demo slides). Ini **replay rekaman yang sama, bukan sesi live baru**:

| Metrik | 0,5 s (sesi live) | 0,3 s (replay lewat aplikasi) |
|---|---|---|
| Perintah benar | 18/20 | 20/20 |
| L2 median / p90 | 1032 / 1103 ms | **737 / 858 ms** |
| L1 perintah median | 1008 ms | 698 ms |
| Tunggu endpoint median | 957 ms | 664 ms |
| Aksi palsu | 0 | 0 |

Replay offline `endpoint_sweep` pada 0,3 s memberi 19/20 (perintah "previous slides" berskor rendah ditolak), sedangkan replay lewat aplikasi menerimanya. Jadi akurasinya dilaporkan sebagai 19–20/20. Target 200 ms tetap tidak tercapai.

## Keterbatasan

- Hanya 1 pembicara dan 20 perintah. Belum mewakili 5 target user, aksen lain, jarak, atau kondisi noise.
- False activation belum diukur dengan rekaman bicara biasa yang panjang (sesi ini hanya berisi perintah).
- Latensi input perangkat keras tidak termasuk, sehingga angka sebenarnya sedikit lebih besar.

## Langkah berikutnya yang disarankan

1. Ulangi pengukuran yang sama pada 5 penguji (zip exe, centang "Rekam input"), lalu jalankan `latency_report` dan `endpoint_sweep` untuk tiap rekaman.
2. Rekam ±5 menit bicara presentasi biasa tanpa perintah untuk mengukur false activation per menit pada jeda 0,5 dan 0,3 s.
3. Putuskan apakah perlu mencoba aksi dari partial yang stabil untuk mendekati 200 ms, dan ukur dampaknya ke false activation.
