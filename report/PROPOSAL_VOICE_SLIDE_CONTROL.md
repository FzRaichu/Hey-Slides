# Proposal Proyek: Voice Slide Control

**Sistem Navigasi Slide Presentasi Menggunakan Perintah Suara**

COMP6822001 - Speech Recognition | BINUS University

Draf untuk ditinjau - 20 Oktober 2026

## 1. Ringkasan

Voice Slide Control adalah aplikasi speech recognition real-time yang memungkinkan presenter mengendalikan slide presentasi menggunakan perintah suara, tanpa menyentuh perangkat apa pun. Seluruh pengenalan suara berjalan **lokal di laptop presenter**, tanpa koneksi internet dan tanpa layanan speech recognition eksternal.

## 2. Latar Belakang dan Masalah

Dalam kegiatan presentasi, presenter perlu menyampaikan materi sekaligus mengatur perpindahan slide. Hal ini dapat mengganggu alur penjelasan ketika presenter sedang memegang alat peraga, menulis di papan tulis, atau berdiri jauh dari laptop.

Pada sebagian presentasi, presenter meminta bantuan orang lain untuk memindahkan slide sesuai arahannya. Ketergantungan pada operator tambahan menimbulkan kebutuhan koordinasi dan dapat menyebabkan slide berpindah terlalu cepat, terlambat, atau tidak sesuai keinginan presenter. Voice Slide Control diusulkan untuk mengurangi kebutuhan orang tambahan yang hanya bertugas mengoperasikan slide, sehingga presenter dapat mengendalikan presentasinya sendiri.

Masalah yang ingin dijawab adalah: **bagaimana perintah suara dapat digunakan untuk memindahkan slide secara tepat sambil tetap menampilkan hasil pengenalan ucapan kepada presenter?**

### Batasan masalah

- Perintah dan materi uji menggunakan bahasa Inggris, dengan satu pembicara utama pada satu waktu.
- Fungsi utama dibatasi pada slide berikutnya, slide sebelumnya, dan perpindahan ke nomor slide 1-10.
- Prototipe awal digunakan pada laptop Windows dengan PowerPoint. Fitur penyuntingan slide, laser pointer, dan kendali animasi tidak termasuk ruang lingkup.
- Pengenalan suara dilakukan secara lokal menggunakan model pretrained. Perintah diberikan langsung tanpa wake word atau tombol yang harus ditahan.

## 3. Target Pengguna

| Kelompok pengguna | Konteks penggunaan |
|---|---|
| Asisten laboratorium | Menjelaskan langkah praktikum sambil memperagakan alat atau prosedur. |
| Mahasiswa presenter | Menyampaikan tugas atau demonstrasi proyek di depan kelas. |
| Dosen | Mengajar menggunakan slide sambil menulis atau bergerak di ruang kelas. |

**Rencana rekrutmen:** lima penguji yang sesuai dengan kelompok pengguna, terdiri atas **3 asisten laboratorium, 1 mahasiswa, dan 1 dosen**. Jumlah ini memenuhi minimum lima target pengguna pada brief. Rekrutmen dan pengujian tersebut masih merupakan rencana, bukan kegiatan yang dinyatakan sudah selesai.

## 4. Solusi yang Diusulkan

Voice Slide Control akan menerima suara dari mikrofon, menampilkan transkripsi selama pengguna berbicara, dan menjalankan navigasi ketika mengenali perintah yang valid. Ucapan biasa tetap dapat ditampilkan sebagai teks, tetapi tidak dimaksudkan untuk menggerakkan slide.

Antarmuka dasar menyediakan tombol mulai dan berhenti mendengarkan, pilihan mikrofon, tampilan transkrip, posisi slide, serta riwayat aksi. Presenter dapat memeriksa apakah ucapan dikenali dan apakah slide yang dituju sudah sesuai.

**Skenario penggunaan:** seorang asisten laboratorium sedang memperagakan alat. Untuk melanjutkan materi, ia mengatakan “Next slide.” Ketika perlu mengulang penjelasan, ia mengatakan “Previous slide.” Ia juga dapat mengatakan “Go to slide seven” untuk menuju slide tertentu tanpa meminta bantuan operator.

Alur pengerjaan proyek direncanakan sebagai **ide → proposal → prototipe → pengujian → pengembangan berdasarkan hasil pengujian**. Proposal ini berfokus pada fungsi dasar dan rencana evaluasinya.

## 5. Dataset dan Data Pengujian

### 5.1 Dataset publik untuk transkripsi

Dataset yang diusulkan adalah **LibriSpeech ASR Corpus, subset test-clean**, yang menyediakan rekaman pembacaan bahasa Inggris beserta transkrip referensi. Dataset tersedia melalui OpenSLR dan berlisensi CC BY 4.0. [Sumber dataset](https://www.openslr.org/12).

Untuk menjaga ukuran eksperimen tetap sederhana, direncanakan penggunaan **100 klip dari sedikitnya lima pembicara**. Daftar klip akan ditetapkan sebelum evaluasi dan tidak digunakan untuk menyetel konfigurasi sistem.

Alasan pemilihannya:

1. Memiliki transkrip referensi untuk menghitung kesalahan pengenalan kata.
2. Berisi ucapan bahasa Inggris berbentuk kalimat, sehingga sesuai untuk memeriksa transkripsi di luar perintah.
3. Memiliki identitas pembicara yang membantu pencatatan dan pengelompokan hasil.

Dataset ini digunakan sebagai **data evaluasi**, bukan untuk melatih ulang model. Hasil pada bacaan audiobook tidak langsung mewakili kualitas aplikasi saat presentasi; karena itu, pengujian pengguna tetap diperlukan.

**Penyesuaian dari rencana awal:** Google Speech Commands v2 lebih sesuai untuk keyword spotting kata tunggal. Dataset tersebut tidak menyediakan contoh frasa navigasi lengkap yang digunakan dalam proposal ini. Oleh sebab itu, dataset tersebut tidak dijadikan data utama untuk menilai “Next slide,” “Previous slide,” dan “Go to slide seven.” [Deskripsi Speech Commands](https://www.tensorflow.org/datasets/catalog/speech_commands).

### 5.2 Data pengguna untuk navigasi slide

Kelima penguji akan membaca skrip yang sama, meliputi:

- Satu paragraf penjelasan presentasi dalam bahasa Inggris untuk menguji transkripsi ucapan biasa.
- Lima belas perintah: masing-masing lima percobaan untuk next, previous, dan go to slide.
- Beberapa kalimat bukan perintah, misalnya “The next slide contains our results,” untuk memeriksa perpindahan slide yang tidak diinginkan.

Skrip dibaca pada kecepatan normal dan lebih cepat sesuai eksperimen pada Bagian 8. Rekaman serta transkrip aktual disimpan dengan persetujuan penguji dan identitas disamarkan sebagai U1-U5. Kata yang berubah, terlewat, atau diulang saat membaca akan dicatat agar referensi sesuai dengan ucapan sebenarnya.

## 6. Kosakata dan Grammar Perintah

Sistem hanya menjalankan tiga jenis aksi berikut:

| Aksi | Perintah utama | Variasi yang diterima | Hasil yang diharapkan |
|---|---|---|---|
| Slide berikutnya | `Next slide` | `Next slides` | Berpindah satu slide ke depan. |
| Slide sebelumnya | `Previous slide` | `Previous slides` | Berpindah satu slide ke belakang. |
| Menuju nomor slide | `Go to slide <number>` | `Go to slides <number>` | Berpindah ke nomor yang disebutkan. |

`<number>` adalah bilangan **one sampai ten** atau representasi angkanya **1-10**, selama nomor tersebut tersedia pada presentasi. Contoh: `Go to slide three` dan `Go to slide 3` memiliki tujuan yang sama.

Aturan penerimaan perintah:

1. Pengguna mengucapkan satu perintah lengkap, kemudian memberi jeda agar ujaran dapat diselesaikan.
2. Hanya hasil pengenalan final yang dapat memicu aksi; teks sementara tidak menggerakkan slide.
3. Hasil harus sesuai dengan salah satu pola pada tabel dan melewati pemeriksaan skor pengenalan.
4. Kalimat yang memuat kata perintah sebagai bagian penjelasan, seperti “The next slide contains our results,” tidak diterima sebagai perintah lengkap.
5. Satu kejadian pengenalan hanya boleh diproses sekali, dan nomor slide harus diperiksa sebelum navigasi.

Aturan ini mengurangi peluang kesalahan, tetapi tidak menjamin bahwa recognizer selalu menghasilkan teks yang benar. Kemungkinan salah pemicu tetap diuji.

## 7. Arsitektur dan Model

### 7.1 Alur sistem

```text
Mikrofon
   ↓
Audio streaming dan pemeriksaan format
   ↓
Model pengenalan suara lokal
   ├── Transkripsi sementara dan final → Tampilan teks
   └── Kandidat perintah final → Pemeriksaan grammar → Navigasi PowerPoint

Audio yang sama → Ekstraksi MFCC manual → Tampilan dan analisis fitur
```

| Langkah | Proses | Tujuan |
|---|---|---|
| 1 | Menangkap audio mikrofon secara berkelanjutan. | Menerima ucapan ketika presenter berbicara. |
| 2 | Menggunakan audio mono 16 kHz dan antrean audio. | Menyiapkan masukan yang sesuai dan mengatur pemrosesan. |
| 3 | Menjalankan model ASR lokal. | Menghasilkan teks sementara dan final tanpa menunggu seluruh rekaman selesai. |
| 4 | Memeriksa kandidat perintah, skor, dan pola kalimat. | Memisahkan navigasi yang valid dari ucapan biasa. |
| 5 | Mengirim aksi ke PowerPoint dan membaca kembali nomor slide. | Memeriksa kesesuaian hasil navigasi. |
| 6 | Menampilkan transkrip, status, dan riwayat aksi. | Membantu pengguna memahami hasil dan memeriksa kegagalan. |

### 7.2 Model yang dipilih

Model awal yang diusulkan adalah **Vosk English `vosk-model-small-en-us-0.15`**. Model ini merupakan model pretrained berukuran sekitar 40 MB dan mendukung penggunaan lokal. [Daftar model resmi Vosk](https://alphacephei.com/vosk/models).

Satu model digunakan dengan dua konfigurasi decoder: pengenalan umum untuk transkripsi dan pengenalan dengan kosakata terbatas untuk kandidat perintah. Keduanya tidak berarti dua model baru dilatih.

**Pelatihan model baru dan perbandingan banyak model tidak dimasukkan dalam ruang lingkup proposal dasar.** Brief memperbolehkan model pretrained dan meminta evaluasi kondisi sistem; tidak menetapkan jumlah model pembanding. Perbandingan pada proposal ini berfokus pada pembicara dan kecepatan bicara.

### 7.3 Ekstraksi fitur manual

MFCC akan dihitung secara manual melalui framing, Hamming window, FFT, Mel filter bank, log energi, dan DCT. Hasilnya digunakan untuk menampilkan serta menjelaskan karakteristik fitur audio.

Pada pendekatan pretrained ini, **MFCC manual merupakan cabang analisis terpisah dan tidak menjadi input Vosk**, karena Vosk menjalankan pemrosesan fitur internalnya sendiri. Kesesuaian cabang analisis ini dengan arahan dosen mengenai ekstraksi fitur manual perlu dipastikan dalam peninjauan proposal; keduanya tidak akan diklaim sebagai proses yang sama.

## 8. Rencana Eksperimen dan Pengujian Pengguna

Rencana eksperimen mengikuti Bagian 12 *Experimental Evaluation* pada brief: baseline dan kondisi yang memengaruhi pengenalan suara. Dipilih dua kondisi yang relevan, yaitu **E2: different speakers** dan **E3: different speaking speed**. Penamaan ini mengikuti brief, bukan penomoran eksperimen pada rencana proyek lama.

| Pengujian | Kondisi | Tujuan |
|---|---|---|
| **Baseline** | Salah satu penguji sebagai pembicara acuan, ruang relatif tenang, mikrofon tetap, dan kecepatan bicara normal. | Menetapkan hasil awal untuk skrip presentasi dan perintah. |
| **E2 - Pembicara berbeda** | Kelima penguji membaca skrip yang sama pada kecepatan normal. | Menilai variasi hasil antar-pembicara. |
| **E3 - Kecepatan bicara berbeda** | Kelima penguji mengulangi skrip pada kecepatan lebih cepat. | Membandingkan hasil normal dan lebih cepat pada orang yang sama. |

Mikrofon, jarak ke mikrofon, lingkungan, konfigurasi model, dan skrip dijaga sama sejauh memungkinkan. Setiap sesi dimulai kembali dari slide satu. Kecepatan diubah melalui pembacaan langsung, bukan mempercepat berkas audio. Durasi bacaan dicatat untuk memeriksa perbedaan kondisi. Hasil E2 dilaporkan per penguji; perbandingan E3 dilakukan dalam masing-masing penguji agar perbedaan pembicara tidak dianggap sebagai pengaruh kecepatan.

Subset LibriSpeech diuji secara terpisah sebagai benchmark transkripsi publik. Hasilnya tidak langsung dibandingkan dengan rekaman pengguna untuk menyimpulkan pengaruh pembicara karena isi dan kondisi rekamannya berbeda.

Dalam pengujian aplikasi, setiap penguji diminta membuka presentasi uji, memberi perintah navigasi, dan melanjutkan penjelasan biasa. Peneliti mencatat kegagalan pengenalan, perpindahan slide yang salah, dan kebutuhan mengulang perintah. Setelah itu, penguji memberikan penilaian skala 1-5 dan komentar singkat mengenai kemudahan penggunaan, kejelasan keluaran, responsivitas, dan kepuasan.

Feedback akan dihubungkan dengan hasil teknis. Misalnya, keluhan bahwa perintah sering perlu diulang akan diperiksa bersama jumlah perintah yang tidak menghasilkan aksi. Seluruh kegiatan pada bagian ini merupakan rencana; hasil dan feedback hanya dilaporkan setelah pengujian benar-benar dilakukan.

## 9. Metrik Evaluasi

| Metrik | Apa yang dinilai |
|---|---|
| **Word Error Rate (WER)** | Kesalahan kata berupa substitusi, penghapusan, dan penambahan dibandingkan transkrip referensi. |
| **Keberhasilan aksi** | Persentase perintah yang menghasilkan jenis aksi dan nomor slide akhir sesuai tujuan. |
| **False reject rate** | Persentase perintah valid yang tidak menghasilkan aksi. |
| **Aksi tidak diinginkan** | Jumlah aksi saat pengguna tidak memberikan perintah, disertai durasi pengamatan. |
| **Real-Time Factor (RTF)** | Perbandingan waktu pemrosesan dengan durasi audio sebagai indikator kemampuan pemrosesan. |
| **Penilaian pengguna** | Skor dan komentar mengenai kemudahan, kejelasan, responsivitas, serta kepuasan. |

WER dihitung dengan rumus **WER = (S + D + I) / N × 100%**, dengan S sebagai substitusi, D penghapusan, I penambahan, dan N jumlah kata referensi. WER transkripsi umum dan WER kandidat perintah dilaporkan terpisah agar keluaran yang kosakatanya dibatasi tidak dianggap sebagai hasil transkripsi umum.

Normalisasi huruf, tanda baca, dan penulisan angka ditetapkan sebelum penilaian serta diterapkan sama pada referensi dan keluaran. Contoh kesalahan akan dianalisis untuk melihat kata atau perintah yang sering tertukar. RTF dihitung sebagai waktu pemrosesan dibagi durasi audio; hasil pemrosesan berkas tidak dianggap sebagai bukti langsung responsivitas antarmuka saat digunakan.

## 10. Risiko dan Mitigasi

Risiko berikut dirumuskan dari kegagalan pengenalan dan pemrosesan audio pada eksplorasi awal, serta kasus navigasi yang telah ditangani dalam pengembangan. Tidak semua risiko sudah terjadi pada pengguna; salah arah, salah nomor, dan aksi ganda tetap merupakan kasus yang perlu dicegah dan diuji.

| Risiko | Dampak | Mitigasi yang direncanakan |
|---|---|---|
| Ucapan tidak dikenali atau berubah menjadi kata lain. | Perintah perlu diulang dan transkrip sulit dipahami. | Memeriksa pilihan mikrofon dan kualitas rekaman, menyediakan contoh pengucapan, memakai decoder perintah terfokus, serta menganalisis kesalahan antar-pengguna. |
| Kalimat penjelasan dianggap sebagai perintah. | Slide berpindah tanpa diminta. | Memeriksa pola perintah lengkap dan skor, menolak teks sementara, menguji kalimat bukan perintah, dan menyediakan Stop untuk menonaktifkan aksi. |
| Perintah dikenali tetapi arah atau nomor slide tidak sesuai. | Presenter kehilangan alur penjelasan. | Memvalidasi aksi dan nomor tujuan, membaca kembali posisi slide dari PowerPoint, dan menampilkan riwayat aksi. |
| Satu perintah diproses lebih dari sekali. | Slide berpindah beberapa langkah. | Menggunakan identitas kejadian pengenalan untuk mencegah pemrosesan ulang kejadian yang sama. |
| Pemrosesan audio tertinggal atau hasil muncul setelah pengguna berhenti. | Perintah berpotensi dijalankan pada waktu yang tidak diinginkan. | Membatasi antrean, menghentikan sesi ketika audio bermasalah, dan menolak aksi dari sesi yang sudah dihentikan. |

---

**Acuan brief:** `FINAL_PROJECT_Speech_Recognition_CASE`, terutama Bagian 3 dan 10 mengenai streaming/transkripsi, Bagian 6 mengenai minimum lima penguji, Bagian 11 mengenai model lokal dan pretrained, serta Bagian 12-14 mengenai eksperimen, metrik, dan analisis kesalahan. Dokumen ini adalah proposal ruang lingkup dasar, bukan laporan hasil eksperimen akhir.
