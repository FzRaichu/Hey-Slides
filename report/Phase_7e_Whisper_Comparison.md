# Fase 7e — Whisper small.en dan segmentasi ucapan

Tanggal: 19 Oktober 2026.

## Hasil dan keputusan

Model **small.en berhasil dipasang dan dibandingkan secara lokal**. Model yang
lebih besar belum memberikan peningkatan yang konsisten pada rekaman pengguna.
Karena itu, recognizer aplikasi desktop tidak diganti pada fase ini. Mode Direct
commands dari Fase 7d tetap tersedia; tidak ada klaim bahwa masalah transkripsi
umum atau batas latensi 200 ms sudah diselesaikan.

Pada satu rekaman dengan referensi lengkap, konfigurasi small.en terbaik yang
diuji hanya menyamai WER base.en sebelumnya. Sebagian frasa pada rekaman lain
membaik, tetapi muncul penghilangan, salah kata, dan keluaran berulang yang
menunjukkan risiko halusinasi. Bukti ini tidak cukup untuk menjadikan small.en
sebagai recognizer live utama.

## Data dan konfigurasi

Enam WAV yang sama dengan Fase 7c, total **192,35 detik**, satu pengguna,
mono PCM16 16 kHz. Tidak ada rekaman baru dari mode Direct pada saat evaluasi.
Seluruh klip lama masih mengandung percobaan wake phrase. Pemeriksaan command
Vosk dalam benchmark tetap menggunakan mode wake, bukan bukti akurasi mode Direct.

Hanya klip `ca049351` memiliki referensi lengkap terkonfirmasi: tiga kali
“hey slide next slide”, sejumlah 12 kata. Lima klip lain tidak diberi WER.
Keluaran ucapan biasa belum memiliki referensi manusia lengkap; peningkatan
akurasi transkripsi umum **belum dapat dihitung**. Tidak ada transkrip yang
dibuat oleh model lalu digunakan sebagai ground truth.

Konfigurasi bersama: faster-whisper 1.2.1, CTranslate2 4.8.3, CPU int8, empat
thread, beam size 5, language=en, condition_on_previous_text=False, tanpa
initial prompt dan hotwords. Model dibaca dari berkas lokal; tidak ada unggahan
audio, pembukaan mikrofon, atau aksi presentasi selama benchmark.

Varian segmentasi:

- **Whole**: perilaku benchmark lama; seluruh klip diberikan ke faster-whisper
  dengan VAD internal. Ini bukan satu decoding window sepanjang seluruh klip.
- **VAD terpisah**: Silero VAD, threshold 0,5, minimum speech 200 ms, silence
  300 ms, padding 200 ms, maksimum speech 8 detik. Setiap rentang didekode sendiri
  tanpa VAD internal tambahan. Banyak rentang sebenarnya hanya sekitar satu detik.
- **Grouped context**: rentang VAD berdekatan dikelompokkan dalam jendela konteks
  bertarget delapan detik, termasuk jeda di antaranya. Tidak ada overlap atau
  deduplikasi teks yang dapat menghapus pengulangan yang disengaja. Varian ini
  diuji setelah fragmen pendek menunjukkan masalah; hasilnya bersifat eksploratif.

Model small.en: `Systran/faster-whisper-small.en`, revision
`d1d751a5f8271d482d14ca55d9e2deeebbae577f`.
SHA-256 model.bin:
`62b2a45b05ee59acb4a5341b33ee35e041395d378d418a18acfe4c9e768ee37a`.
Bobot berukuran sekitar 484 MB. Unduhan HTTPS dan pemeriksaan hash LFS berhasil.

## Hasil terukur

| Model dan segmentasi | Kesalahan pada 12 kata | WER | Total waktu decode enam klip | RTF agregat |
|---|---:|---:|---:|---:|
| base.en, whole — hasil historis 17 Oktober | 3 substitusi | 25,0% | 20,51 s | 0,107 |
| base.en, VAD terpisah | 4 substitusi | 33,3% | 55,80 s | 0,290 |
| small.en, whole | 3 substitusi + 2 insersi | 41,7% | 37,59 s | 0,195 |
| small.en, VAD terpisah | 4 substitusi + 1 insersi | 41,7% | 148,77 s | 0,773 |
| small.en, grouped context | 3 substitusi | 25,0% | 39,40 s | 0,205 |

Sebagai pembanding historis pada klip yang sama, Vosk umum memiliki WER 91,7%
dan Vosk terfokus memiliki WER 0%. Decoder terfokus dibatasi pada kosakata
perintah, sehingga tidak dapat dinyatakan unggul pada transkripsi umum.

WER hanya menormalisasi huruf besar/kecil dan tanda baca. Tidak ada penggantian
otomatis kata pemicu atau penyamaan angka yang menyembunyikan kesalahan.
Tabel mencakup seluruh konfigurasi yang dicoba, bukan hanya konfigurasi sukses.

Waktu adalah satu pengukuran offline per konfigurasi pada laptop pengembangan,
di luar pemuatan model; RTF = waktu decode / durasi audio. Angka historis tidak
diulang pada fase ini dan kondisi beban mesin dapat berbeda. Benchmark tidak
mengukur utilisasi CPU, penggunaan memori puncak, atau latensi streaming.
Belum ada uji beban gabungan Whisper, Vosk, MFCC, dan antarmuka secara live.

## Temuan penting

1. **Besar model bukan jaminan peningkatan.** Small.en whole mengenali ketiga
   frasa wake/command pada rekaman terakhir secara lebih masuk akal, tetapi
   lebih buruk pada satu klip terkonfirmasi. Ini pengamatan keluaran, bukan
   tiga aksi live dari Whisper atau ukuran akurasi keseluruhan.
2. **Segmentasi dapat memperbaiki cakupan sekaligus merusak isi.** Base.en whole
   sebelumnya baru mengeluarkan teks sekitar detik 58 pada klip 92,90 detik.
   VAD terpisah dan grouped context menghasilkan keluaran sejak sekitar detik
   0,70. Namun tambahan keluaran tidak otomatis benar.
3. **Fragmen sangat pendek bermasalah.** VAD memisahkan sebagian prefix dari
   perintah berikutnya. Base.en mengeluarkan pengulangan kata yang tidak dapat
   dianggap pemulihan ucapan. Small.en VAD terpisah juga lambat: klip 92,90 detik
   memerlukan sekitar 88,39 detik decoding. Konfigurasi ini tidak dipromosikan.
4. **Grouped context lebih menjanjikan untuk pemeriksaan lanjutan.** Pada klip
   panjang, keluarannya kembali memuat dua frasa previous slide yang hilang
   dari keluaran small.en whole. Salah kata dan penghilangan tetap ada; tanpa
   referensi manusia, peningkatan lengkapnya belum dapat dinyatakan.

## Yang ditambahkan ke kode

- Downloader menerima `--model base.en|small.en`, mengunduh bobot melalui HTTPS
  dengan laporan progres, dan memeriksa SHA-256 terhadap metadata Hub.
- `app/whisper_recognition.py`: loader lokal CPU int8, segmentasi, penjagaan
  rentang audio, konsumsi generator lengkap, dan pengembalian offset waktu asli.
  Modul ini untuk evaluasi saat ini, **belum dipanggil oleh aplikasi desktop**.
- Benchmark menerima `--segmentation whole|vad|context` dan `--command-mode`.
  Hasil menyimpan konfigurasi, provenance, hash audio, diagnostik rentang,
  teks keluaran, waktu, dan WER hanya bila referensi lengkap terkonfirmasi.
- Lima pengujian baru memeriksa offset, generator, grouping, silence, input
  tidak valid, dan rentang tumpang tindih. Total **60 tes regresi lulus**.
- Script bacaan terkontrol disiapkan pada `Recognition_Test_Script.md`.

Semua audio, model, dan keluaran transkrip mentah tetap dalam direktori yang
diabaikan Git. Hasil lokal: `logs/benchmark-base-vad.json`,
`logs/benchmark-small-whole.json`, `logs/benchmark-small-vad.json`, dan
`logs/benchmark-small-context.json`. Hasil historis:
`logs/recognizer-benchmark.json`.

## Langkah berikutnya

Gunakan satu bacaan biasa dengan teks yang diketahui serta tiga perintah
langsung, mengikuti script yang disiapkan. Konfirmasikan kata-kata yang benar-benar
dibaca, lalu nilai WER ucapan biasa dan aksi langsung secara terpisah. Dengan
demikian, pemilihan model tidak hanya didasarkan pada pengulangan tiga perintah
yang sudah dipakai berkali-kali untuk pengembangan.

Perlu juga memastikan bahasa presentasi: model `.en` hanya dipilih untuk
pengujian bahasa Inggris. Bahasa Indonesia atau campuran memerlukan kandidat
multibahasa. Sesudah kandidat terbukti lebih akurat, baru integrasikan sebagai
transkrip non-actionable, pertahankan jalur command terpisah, dan uji beban live.

MFCC manual tetap merupakan cabang analisis terpisah, tidak menjadi input
pretrained Vosk atau Whisper. Tidak ada fine-tuning pada fase ini.

## Sumber

- [Model card Systran small.en](https://huggingface.co/Systran/faster-whisper-small.en):
  konversi model Whisper small.en ke CTranslate2 dan lisensi MIT.
- [Dokumentasi faster-whisper](https://github.com/SYSTRAN/faster-whisper):
  inferensi CPU int8, model lokal, generator transkripsi, dan VAD.
