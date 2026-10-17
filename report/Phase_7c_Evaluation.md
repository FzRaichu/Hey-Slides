# Fase 7c — Evaluasi Rekaman Pengguna dan Kandidat ASR

Tanggal: 17 Oktober 2026.

## Kesimpulan

Prototipe telah berhasil menjalankan tiga jenis perintah pada rekaman terakhir:
**next, previous, dan go to slide seven**. Keberhasilan tersebut belum konsisten
pada rekaman sebelumnya. Decoder perintah terfokus tetap dipertahankan.

Whisper base.en memperbaiki hasil transkripsi pada satu rekaman yang memiliki
referensi lengkap, tetapi masih salah mengenali kata pemicu dan menunjukkan
penghilangan keluaran pada rekaman panjang. Oleh karena itu, kandidat ini belum
dipasang sebagai pengganti recognizer aplikasi. Pelatihan ulang model belum
dilakukan. Fase evaluasi keseluruhan belum selesai.

## Data dan metode

Enam rekaman WAV pengguna tersedia, dengan total durasi **192,35 detik**.
Format seluruh rekaman adalah mono, PCM16, 16 kHz. Semua berasal dari pengguna
yang sama dan sudah pernah dipakai untuk mencoba aplikasi; data ini bukan
pengujian independen terhadap pengguna baru.

Audit mencocokkan setiap rekaman dengan session ID pada log aplikasi. Hanya
aksi bersumber dari pengenalan suara yang dihitung; tombol dan pengujian teks
dikecualikan. Jumlah aksi yang tercatat bukan jumlah percobaan yang benar dan
tidak langsung menjadi persentase akurasi.

| ID rekaman (awalan) | Durasi (detik) | Aksi suara berhasil pada log langsung |
|---|---:|---|
| e0ec9a69 | 10,10 | Tidak ada |
| ca049351 | 11,00 | next, next, next |
| 975637b2 | 92,90 | Enam next dan dua previous |
| 2f40f393 | 19,45 | next, previous |
| c6267adb | 21,85 | previous |
| 2bd97f26 | 37,05 | next, previous, goto 7 |

Rekaman terakhir dikonfirmasi pengguna berhasil untuk ketiga jenis perintah.
Tidak terdapat aksi tambahan setelah goto 7 sampai rekaman berakhir. Hal ini
belum menetapkan tingkat false activation karena referensi lengkap ucapan biasa
dan jumlah percobaan negatif belum tersedia. Sampel indikator kualitas audio
di keenam sesi tidak menunjukkan clipping; indikator tersebut tidak membuktikan
seluruh aspek kualitas mikrofon telah baik.

Perbandingan offline memakai audio yang sama tanpa mengirimkan rekaman keluar
komputer dan tanpa menggerakkan PowerPoint:

1. Vosk Light, transkripsi tanpa pembatasan kosakata.
2. Vosk Light, decoder perintah terfokus dengan gerbang skor yang sudah digunakan aplikasi.
3. Whisper base.en melalui faster-whisper, CPU int8, empat thread, beam size 5,
   bahasa Inggris, VAD aktif, condition_on_previous_text=False, tanpa initial
   prompt maupun hotword berisi jawaban yang diharapkan.

WAV divalidasi dan diubah langsung menjadi array float32 dari PCM16 untuk
Whisper. Jalur ini juga menghindari ketidakcocokan pemanggilan pembaca berkas
faster-whisper 1.2.1 dengan PyAV 19.0.1 yang ditemukan pada lingkungan evaluasi.
Seluruh generator segmen dikonsumsi sebelum timer decoding dihentikan.

Model: Systran/faster-whisper-base.en, revision
`3d3d5dee26484f91867d81cb899cfcf72b96be6c`.
SHA-256 model.bin:
`2a166925539a16005f14ff328359f9b9adb9dc4fb631bb3b227526862e93e2ef`.
Transfer model sempat macet pada tahap penyelesaian; bobot yang sudah lengkap
dipulihkan dari berkas sementara setelah hash cocok dengan hash LFS Hub.

Lingkungan: Windows 11, Python 3.12.4, faster-whisper 1.2.1,
CTranslate2 4.8.3, Vosk 0.3.45, NumPy 2.2.6, 20 logical CPU.
Versi dependency dan hash tiap rekaman disimpan pada hasil lokal.

## Hasil yang dapat dinilai

Hanya **ca049351** memiliki referensi lengkap yang secara eksplisit dikonfirmasi
pengguna: tiga pengulangan “hey slide next slide”, sejumlah **12 kata**.
Rekaman lain tetap tidak diberi WER karena ucapan lengkapnya belum diverifikasi.
Referensi tiga perintah saja tidak digunakan untuk menilai seluruh rekaman
terakhir yang juga memuat ucapan biasa.

Normalisasi WER hanya menyamakan huruf besar/kecil dan tanda baca. Kata pemicu,
plural, dan bentuk angka tidak dikoreksi menggunakan jawaban yang diharapkan.

| Decoder | Kesalahan kata / 12 kata | WER |
|---|---:|---:|
| Vosk tanpa pembatasan | 11 substitusi | 91,7% |
| Whisper tanpa pembatasan | 3 substitusi | 25,0% |
| Vosk terfokus pada perintah | 0 | 0,0% |

Whisper menulis “a slide” pada ketiga kata pemicu; bagian “next slide” benar.
Decoder terfokus memiliki kosakata yang sengaja dibatasi, sehingga hasil 0%
tersebut **bukan bukti akurasi transkripsi umum**. Ukuran sampel ini juga terlalu
kecil untuk menyatakan WER keseluruhan sistem.

## Temuan lintas rekaman

- Replay Vosk terfokus menghasilkan urutan aksi yang sama dengan log langsung
  pada keenam rekaman. Tidak ada aksi presentasi yang benar-benar dijalankan saat replay.
- Kegagalan meliputi prefix berubah atau hilang, kata perintah salah/hilang,
  serta kandidat yang ditolak karena skor rendah. Mengganti parser menjadi
  pencocokan longgar dapat menambah aksi yang tidak diinginkan; belum ada data
  negatif yang cukup untuk membenarkan perubahan tersebut.
- Whisper masih menulis variasi “a slide” atau “a slight” dan pada rekaman pertama
  mengeluarkan empat “next slide”. Jumlah itu tidak dianggap benar karena jumlah
  ujaran pada rekaman tersebut belum dikonfirmasi.
- Pada rekaman 92,90 detik, keluaran Whisper baru dimulai sekitar detik 58,11,
  sementara decoder Vosk menghasilkan ujaran lebih awal. Ada penghilangan
  keluaran yang perlu diperiksa pada kandidat/konfigurasi ini. Penyebabnya belum
  dipastikan; hasil tidak boleh dipromosikan sebagai transkripsi penuh yang andal.
- Total waktu decode Whisper sekitar **20,51 detik** untuk audio 192,35 detik
  (RTF agregat sekitar **0,107**), di luar pemuatan model. Ini pengukuran
  throughput offline, bukan latensi streaming. Pemrosesan seluruh klip setelah
  EOF, VAD, dan segmentasi tidak membuktikan target 200 ms.

## Keputusan dan tahap berikutnya

1. Pertahankan decoder perintah saat ini dan pisahkan evaluasinya dari kualitas
   transkripsi umum. Kandidat Whisper ini tetap menjadi alat eksperimen offline.
2. Siapkan referensi manusia untuk rekaman yang belum dinilai, lalu bandingkan
   kandidat transkripsi yang lebih kuat serta segmentasi ujaran pendek. Periksa
   penghilangan ujaran dan kata pemicu secara khusus sebelum integrasi live.
3. Gunakan rekaman baru dengan perintah, ucapan biasa, dan frasa mirip sebagai
   data uji terpisah. Jangan melonggarkan ambang skor atau prefix berdasarkan
   sampel sukses saja. Evaluasi pengguna lain tetap diperlukan.
4. Sesudah kandidat dipilih, uji jalur mikrofon secara streaming, antrean audio,
   pemisahan aksi/transkrip, dan latensi dari akhir ujaran yang didefinisikan
   secara jelas. Persyaratan 200 ms belum tercapai atau dibuktikan.

MFCC manual tetap merupakan cabang analisis terpisah dan tidak menjadi input
pretrained Vosk/Whisper. Kesesuaiannya dengan persyaratan dosen masih perlu
dikonfirmasi. Pelatihan model khusus belum menjadi langkah berikutnya karena
data berlabel dan evaluasi independen belum memadai.

## Reproduksi dan berkas bukti

Dependency evaluasi bersifat opsional dan terpisah dari runtime aplikasi.
Instruksi menjalankan alat ada pada README. Hasil berisi transkrip pribadi dan
disimpan dalam direktori logs yang diabaikan Git:

- `recorded-session-audit.json`: audit aksi langsung per sesi.
- `recognizer-benchmark.json`: hash audio, konfigurasi, teks keluaran, segmen,
  waktu decode, serta WER jika referensi lengkap dan terkonfirmasi.
- `evaluation-references.json`: referensi lengkap yang telah dikonfirmasi.

Tidak ada audio, transkrip mentah pengguna, dependency biner, atau model yang
dimasukkan ke commit. Pemeriksaan otomatis: 50 tes unit/regresi lulus.

## Sumber teknis

- [Dokumentasi resmi faster-whisper](https://github.com/SYSTRAN/faster-whisper):
  pemuatan model lokal, CPU int8, generator transkripsi, dan VAD.
- [Model card resmi Systran base.en](https://huggingface.co/Systran/faster-whisper-base.en):
  model konversi Whisper bahasa Inggris dan lisensinya.
