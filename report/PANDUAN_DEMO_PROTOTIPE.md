# Panduan demo Voice Slide Control

## Tujuan demo

Menunjukkan pengenalan pretrained yang sudah mengendalikan slide dan ekstraksi
MFCC manual yang berjalan pada audio yang sama. Kedua keluaran ditampilkan
berdampingan agar dosen dapat menilai arah implementasinya.

**Ini belum merupakan perbandingan dua model pengenal.** Panel kiri memakai
model Vosk pretrained. Panel kanan menghitung fitur MFCC; belum ada classifier
yang mengubah fitur manual tersebut menjadi kata. Jangan menyebut nilai MFCC
sebagai hasil pengenalan kata atau membandingkan akurasinya dengan Vosk.

## Persiapan

1. Tutup versi aplikasi yang lama, lalu jalankan `Start Prototype.cmd`.
2. Untuk demo pertama, gunakan **Demo slides**. Slide demo berjumlah lima.
3. Default aplikasi sudah **Light English + Direct commands + Command assist**.
   Tidak perlu memilih model atau menahan tombol.
4. Jika perlu mengganti mikrofon, buka **Pengaturan → Pengaturan**. Pilih
   mikrofon, kemudian tutup jendela pengaturan. Rekaman WAV tetap mati secara
   default; aktifkan hanya jika ingin menyimpan audio untuk evaluasi.

## Urutan demonstrasi

1. Klik **Mulai mendengarkan**. Tunggu status Listening/model siap.
2. Ucapkan satu kalimat bahasa Inggris. Tunjukkan teks sementara dan hasil MIC
   di panel **Pengenalan pretrained**. Hasil dapat salah; jangan dikoreksi secara
   diam-diam atau dianggap bukti akurasi yang sudah tinggi.
3. Ucapkan satu kali setiap perintah berikut, dengan jeda sekitar dua detik:
   - **Next slide**: dari slide satu ke dua.
   - **Previous slide**: kembali ke slide satu.
   - **Go to slide three**: menuju slide tiga.
4. Tunjukkan riwayat aksi. Entri bertanda **suara** berasal dari pengenalan;
   **tombol** dari navigasi manual; **tes teks** dari pemeriksaan parser.
5. Tunjukkan panel **MFCC manual**: heatmap, jumlah frame, 156 nilai fitur, dan
   contoh enam nilai. Fitur dihitung dari audio, bukan transkrip pretrained.
6. Baca kalimat biasa seperti **The next slide contains our results**. Kalimat
   tersebut seharusnya tidak memindahkan slide. Jika berpindah, catat sebagai
   kesalahan, bukan keberhasilan.
7. Klik **Stop**. Setelah sesi berhenti, hasil fitur terakhir tetap terlihat.

Jika perintah gagal, jelaskan hasilnya lalu ulangi secara terbuka. Tombol
Previous/Next dapat dipakai sebagai cadangan, tetapi aksi tombol tidak dihitung
sebagai keberhasilan pengenalan suara.

## Jika menggunakan PowerPoint

1. Buka satu presentasi dan mulai slideshow dengan pengaturan All slides.
2. Ubah Target menjadi **PowerPoint**. Tombol **Hubungkan PowerPoint** muncul.
3. Klik tombol tersebut dan periksa nama/nomor slide yang terhubung.
4. Klik Mulai mendengarkan dan gunakan perintah yang sama.

Panel aplikasi menunjukkan status nomor slide, bukan gambar isi PowerPoint.
Perubahan target atau penyambungan ulang menghentikan sesi suara. Pastikan
nomor tujuan tersedia dalam presentasi; Go to slide seven hanya cocok bila
presentasi memiliki sedikitnya tujuh slide.

## Pengaturan dan bukti teknis

Pilihan teknis dipindahkan dari layar utama, bukan dihapus:

| Lokasi | Isi |
|---|---|
| Pengaturan → Pengaturan | Mikrofon, model Vosk, mode direct/wake, command assist, rekaman dan playback WAV. |
| Pengaturan → Diagnostik / tes teks | Waktu pemrosesan, tes parser, dan Simpan fitur terakhir (JSON). |

Tes parser melewati pengenalan suara dan dapat menggerakkan slide. Gunakan
hanya untuk menjelaskan logika aplikasi, bukan untuk membuktikan ASR berhasil.
Waktu decode/MFCC/antrean bukan latensi suara-ke-slide dan tidak membuktikan
target 200 ms. Model Whisper tetap hanya tersedia melalui alat evaluasi offline.

## Penjelasan singkat kepada dosen

> Jalur pertama menggunakan model Vosk pretrained untuk mengubah audio menjadi
> teks. Kandidat perintah diperiksa sebelum digunakan untuk mengendalikan slide.
> Jalur kedua menghitung MFCC secara manual menggunakan NumPy dan menampilkan
> hasil fitur angkanya. Saat ini fitur manual belum menjadi input model pengenal.
> Kami ingin memastikan apakah tugas mengharuskan hasil MFCC manual tersebut
> digunakan oleh classifier, atau cukup diimplementasikan dan dianalisis.

Apabila fitur manual harus menjadi input pengenal, penambahan model/classifier
berbasis fitur tersebut merupakan pekerjaan berikutnya. UI demo tidak membuat
kesan bahwa komponen itu sudah selesai.
