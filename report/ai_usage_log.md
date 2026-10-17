# AI Usage Log

Wajib ada di Technical Report (Section 21.2 brief). Isi setiap kali AI dipakai secara
berarti. Catat juga saran yang DITOLAK atau DIUBAH — itu yang dinilai sebagai
"critical use of AI".

| No. | Tanggal | AI Tool | Tujuan | Ringkasan Prompt | Output Dipakai | Verifikasi oleh Mahasiswa |
|---|---|---|---|---|---|---|
| 1 | | Claude | Brainstorming ide & kritik | Minta kritik ide transkripsi kuliah + alternatif ide | Sebagian — ide transkripsi kuliah dibatalkan | (isi: misalnya dicek ulang terhadap brief & batasan latency dosen) |
| 2 | | Claude | Analisis batasan 200 ms | Minta penjelasan pengaruh batas latency ke pilihan arsitektur | Dipakai sebagai dasar memilih keyword spotting | (isi: misalnya latency diukur sendiri di Langkah 3) |
| 3 | | Claude | Kode Langkah 1 (check_env, explore_dataset) | Minta script cek lingkungan & eksplorasi dataset | Dipakai | (isi: dijalankan, angka dicocokkan dengan dokumentasi dataset) |
| 4 | 2026-10-17 | Codex | Implementasi prototipe lokal | Setelah pretrained diizinkan, buat transkripsi penuh, prefix Hey Slides, MFCC manual, dan navigasi slide sederhana | Vosk pretrained, parser ketat, ekstraksi NumPy MFCC terpisah, UI desktop dan pengujian | Pemeriksaan otomatis oleh AI dicatat pada README/log; verifikasi mahasiswa terhadap suara sendiri, kebutuhan MFCC dosen, dan latensi masih diperlukan. MFCC manual tidak diklaim sebagai input Vosk. |
| 5 | 2026-10-17 | Codex | Fase 6 integrasi PowerPoint | Lanjutkan fase berikutnya dan buat commit per fase | Adapter COM attach-only, pemilihan target, navigasi nomor slide, pengecekan balik posisi slide, pengujian regresi dan dokumentasi | Tes otomatis dan uji PowerPoint nyata memakai presentasi kosong sementara berhasil. Pengujian suara mahasiswa dan latensi akustik masih diperlukan; waktu adapter tidak diklaim sebagai latensi 200 ms. |
