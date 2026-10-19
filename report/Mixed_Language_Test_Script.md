# Uji transkripsi campuran Indonesia–Inggris

Pengguna mengonfirmasi pada 19 Oktober 2026 bahwa bahasa presentasinya campuran.
Gunakan **Whisper small multibahasa**, bukan small.en, untuk perbandingan ini.
Script ini baru rencana bacaan, belum merupakan rekaman atau hasil pengujian.

## Rekam melalui aplikasi desktop

Pilih Demo slides, Light English, Direct commands, Command assist, dan Record
input for diagnosis. Klik Start listening. Model MIC desktop masih Vosk Inggris;
transkrip campuran dinilai kemudian dari WAV dengan alat Whisper lokal. Jangan
menganggap tampilan MIC sudah memakai model multibahasa.

Baca paragraf berikut dengan suara alami. Jangan membaca instruksi:

> Hari ini saya akan menjelaskan speech recognition project kami. This application
> listens to the microphone and converts speech into text. Audio dari mikrofon
> diproses secara lokal menggunakan pretrained model. We also calculate MFCC
> features manually for analysis. Pada bagian ini saya hanya menjelaskan sistem,
> jadi posisi slide seharusnya tetap sama.

Kemudian ucapkan setiap perintah sekali dengan jeda sekitar dua detik:

> Next slides.

> Previous slides.

> Go to slide three.

Terakhir, baca dua kalimat penjelasan yang tidak boleh menyebabkan navigasi:

> Pada next slide, kita akan membahas hasil evaluasi.

> Do not go to slide four.

Klik Stop. Jika ada kata yang berubah, terlewat, atau diulang, catat ucapan
sebenarnya. Script tidak otomatis menjadi referensi terkonfirmasi. Mulai dari
slide satu: aksi yang diharapkan adalah 2 -> 1 -> 3; bagian penjelasan tidak
boleh menambah aksi.

## Periksa WAV dengan Whisper multibahasa

Ganti nama berkas contoh dengan WAV yang baru disimpan:

```powershell
.\.venv\Scripts\python.exe -m scripts.transcribe_whisper_wav logs/input-YOUR-SESSION.wav --model small --language auto --output logs/mixed-review.json
```

Alat mencetak teks dan menyimpan hasil lokal, tanpa mengendalikan presentasi.
Mode auto mendeteksi bahasa untuk setiap input decode. task=transcribe meminta
transkripsi, bukan terjemahan. Pergantian bahasa dalam satu kalimat masih dapat
salah dikenali atau dinormalisasi ke bahasa dominan; kemampuan code-switching
belum terbukti pada suara pengguna. Bandingkan teks dengan ucapan asli.

Jika sebagian besar penjelasan berbahasa Indonesia, `--language id` dapat
dibandingkan secara terpisah. Simpan ke output lain dan laporkan kedua hasil;
jangan mengganti referensi agar sesuai keluaran model. Perintah navigasi tetap
dalam bahasa Inggris pada prototipe saat ini.
