# Voice Slide Control Berbasis MFCC dan Linear SVM

Laporan Proyek COMP6822001 Speech Recognition

BINUS University

Voice Slide Control dirancang untuk membantu presenter mengendalikan slide melalui perintah suara dengan pemrosesan lokal. Dokumen ini menjelaskan pendahuluan, dasar pengenalan suara, dan desain sistem yang akan digunakan dalam pengembangan aplikasi. Pendekatan yang dipilih adalah pengenalan perintah dengan kosakata terbatas, ekstraksi fitur Mel Frequency Cepstral Coefficients (MFCC) secara eksplisit, serta klasifikasi menggunakan Linear Support Vector Machine (Linear SVM).

# BAB 1 PENDAHULUAN

## 1.1 Latar Belakang

Presentasi merupakan kegiatan yang sering dilakukan dalam perkuliahan, demonstrasi praktikum, dan penyampaian hasil proyek. Dalam kegiatan tersebut, presenter perlu menyampaikan penjelasan sekaligus mengatur perpindahan slide. Pengaturan slide umumnya dilakukan melalui keyboard, mouse, atau perangkat kendali presentasi. Cara tersebut membutuhkan interaksi fisik dengan perangkat, sehingga dapat menyulitkan presenter ketika kedua tangannya digunakan untuk memegang alat peraga atau melakukan demonstrasi.

Teknologi pengenalan suara memungkinkan ucapan digunakan sebagai masukan untuk mengoperasikan aplikasi. Pada kebutuhan yang memiliki perintah terbatas, pengenalan tidak harus mencakup seluruh bahasa percakapan. Sistem dapat difokuskan pada kata tertentu yang memiliki hubungan langsung dengan fungsi aplikasi, misalnya navigasi dan pemilihan nomor slide. Pendekatan ini dikenal sebagai pengenalan dengan kosakata terbatas dan berkaitan dengan tugas keyword spotting [1].

Proyek Voice Slide Control mengusulkan aplikasi yang menerima audio secara berkelanjutan, mengekstraksi fitur MFCC, mengenali kata perintah, menampilkan transkrip perintah, dan menjalankan aksi presentasi. Pengenalan dilakukan di komputer pengguna tanpa layanan Speech Recognition eksternal. Ekstraksi fitur dirancang sebagai tahap yang terpisah dan dapat dijelaskan, sehingga hubungan antara karakteristik audio, representasi fitur, dan keputusan model dapat dianalisis.

## 1.2 Permasalahan Dunia Nyata

Permasalahan yang menjadi dasar proyek adalah kebutuhan mengendalikan slide ketika presenter tidak dapat menggunakan perangkat kendali secara leluasa. Contoh situasinya adalah asisten laboratorium yang menjelaskan prosedur sambil memegang peralatan, dosen yang memperagakan objek sambil merujuk slide, serta mahasiswa yang melakukan demonstrasi prototipe. Pada situasi tersebut, mengoperasikan perangkat dapat mengharuskan pengguna meletakkan objek atau kembali ke posisi laptop.

Perangkat kendali presentasi merupakan solusi yang sudah tersedia, tetapi tetap membutuhkan tangan untuk dioperasikan. Voice Slide Control ditujukan pada situasi tertentu ketika penggunaan suara berpotensi mengurangi kebutuhan interaksi fisik tersebut. Relevansi masalah akan diperiksa melalui pengamatan dan pengujian bersama pengguna yang benar-benar melakukan presentasi atau demonstrasi.

Penggunaan suara juga menimbulkan tantangan baru. Presenter tetap berbicara untuk menjelaskan materi, sehingga sebagian besar audio yang diterima sistem bukan merupakan perintah. Sistem perlu membedakan ucapan biasa dari instruksi yang disengaja agar tidak mengubah slide pada waktu yang tidak diinginkan. Oleh karena itu, kegunaan aplikasi tidak hanya ditentukan oleh ketepatan klasifikasi kata, tetapi juga oleh kemampuannya menghindari aktivasi palsu.

## 1.3 Target Pengguna

Target pengguna utama adalah asisten laboratorium dan mahasiswa yang melakukan demonstrasi alat atau prototipe sambil menyampaikan materi melalui slide. Karakteristik pengguna yang relevan adalah melakukan presentasi secara nyata, mengalami situasi ketika tangan digunakan untuk kegiatan lain, dan membutuhkan navigasi slide selama demonstrasi. Dosen dengan kegiatan presentasi yang serupa dapat menjadi pengguna tambahan.

Pemilihan pengguna tidak didasarkan hanya pada status sebagai mahasiswa atau dosen. Peserta pengujian akan dipilih berdasarkan kesesuaian aktivitasnya dengan masalah yang diteliti. Dengan demikian, penilaian kegunaan aplikasi berasal dari pengalaman pengguna yang relevan. Pengujian direncanakan melibatkan sedikitnya lima pengguna, dengan target tujuh peserta untuk memberikan ruang terhadap kemungkinan pembatalan keikutsertaan [10].

## 1.4 Permasalahan Pengguna

Pengguna membutuhkan cara untuk berpindah slide tanpa harus menghentikan demonstrasi atau melepaskan objek yang sedang dipegang. Pengguna juga memerlukan respons yang cukup cepat agar perintah tidak mengganggu alur penjelasan. Selain navigasi maju dan mundur, pemilihan slide tertentu dapat membantu ketika pengguna perlu kembali menjelaskan bagian sebelumnya.

Dalam penggunaan berbasis suara, pengguna perlu mengetahui apakah ucapannya sudah dikenali dan apakah perintahnya telah dijalankan. Tanpa umpan balik yang jelas, pengguna dapat mengulang instruksi secara berlebihan atau salah memahami kondisi aplikasi. Oleh sebab itu, sistem akan menyediakan transkrip perintah, status penerimaan perintah, dan informasi aksi terakhir pada panel yang dapat dilihat presenter.

Pengguna juga membutuhkan perlindungan terhadap perubahan slide yang tidak disengaja. Sebagai contoh, penyebutan kata "right" dalam penjelasan berbahasa Inggris tidak selalu berarti meminta slide berikutnya. Rancangan menggunakan kata pemicu "marvin" dan aturan urutan perintah untuk membedakan instruksi dari pembicaraan biasa.

## 1.5 Rumusan Masalah

Rumusan masalah penelitian ini adalah bagaimana merancang sistem pengenalan perintah suara lokal berbasis MFCC dan Linear SVM yang dapat membantu navigasi presentasi, menghasilkan transkrip perintah selama audio diterima, serta mengurangi aktivasi palsu ketika presenter berbicara secara normal.

Rumusan tersebut dijabarkan ke dalam pertanyaan berikut:

1. Bagaimana audio mikrofon yang diterima secara berkelanjutan diubah menjadi fitur berdimensi tetap untuk klasifikasi kata perintah?
2. Seberapa baik Linear SVM mengenali kata perintah pada pembicara yang berbeda, dan bagaimana hasilnya dibandingkan dengan Random Forest pada fitur yang sama?
3. Bagaimana aturan kata pemicu, ambang keputusan, dan penggabungan prediksi memengaruhi aktivasi palsu serta perintah yang tidak terdeteksi?
4. Apakah latensi pengenalan kata dapat memenuhi target maksimum 200 ms berdasarkan definisi dan prosedur pengukuran yang ditetapkan?
5. Apakah aplikasi membantu pengguna dalam skenario presentasi yang relevan, dan keterbatasan apa yang ditemukan melalui pengujian teknis serta umpan balik pengguna?

## 1.6 Tujuan Proyek

Tujuan umum proyek adalah merancang dan mengevaluasi aplikasi pengendalian presentasi menggunakan perintah suara dengan pengenalan yang dijalankan secara lokal. Tujuan khusus proyek adalah:

1. Mengembangkan penerimaan audio mikrofon secara berkelanjutan tanpa menunggu selesainya rekaman penuh.
2. Menyusun ekstraksi MFCC dan fitur turunannya secara eksplisit sebagai masukan model klasifikasi.
3. Melatih Linear SVM sebagai model utama dan Random Forest sebagai model pembanding menggunakan protokol pembagian data yang memisahkan pembicara.
4. Menghasilkan transkrip perintah sementara dan terkonfirmasi, kemudian menerjemahkan urutan kata yang sah menjadi aksi presentasi.
5. Mengukur ketepatan pengenalan, Word Error Rate (WER), aktivasi palsu, perintah yang tidak terdeteksi, serta latensi pengenalan dan eksekusi aksi secara terpisah.
6. Melaksanakan pengujian bersama pengguna yang relevan dan menghubungkan umpan baliknya dengan hasil evaluasi teknis.

## 1.7 Ruang Lingkup Proyek

Sistem difokuskan pada pengenalan kata perintah dalam bahasa Inggris dengan kosakata tertutup. Dataset utama yang direncanakan adalah Google Speech Commands v2. Rekaman tambahan dari pengguna akan digunakan untuk pengujian urutan perintah dan kondisi pemakaian, bukan sebagai pengganti pengujian pada pembicara yang belum digunakan dalam pelatihan. Data validasi digunakan untuk pemilihan parameter, sedangkan data uji digunakan untuk penilaian akhir.

Kosakata rancangan terdiri atas 20 kata perintah, satu kata pemicu, dan dua kelas penolakan, sehingga menghasilkan 23 kelas. Dua puluh kata perintah tersebut adalah "right", "left", "up", "down", "go", "stop", "on", "off", "yes", "no", serta "zero" sampai "nine". Kata "marvin" berfungsi sebagai pemicu, sedangkan "unknown" dan "silence" digunakan untuk merepresentasikan audio di luar perintah serta keheningan atau latar tanpa ucapan target. Penggunaan semua kata sebagai aksi aktif dapat dilakukan secara bertahap mengikuti kemampuan integrasi platform.

PowerPoint pada Windows dipilih sebagai integrasi awal. Canva dalam mode presentasi direncanakan sebagai pengembangan lanjutan, terutama untuk navigasi maju, mundur, dan pemilihan halaman. Pemetaan aksi disesuaikan dengan masing-masing platform. Pengenalan suara tetap lokal meskipun aplikasi presentasi yang digunakan memiliki layanan daring.

Transkrip yang dihasilkan dibatasi pada kata perintah yang dikenali. Sistem tidak ditujukan untuk mentranskripsi seluruh penjelasan presenter, merangkum materi, memisahkan pembicara, atau melakukan transkripsi bebas dalam bahasa Indonesia. Kesesuaian ruang lingkup transkripsi perintah terhadap ketentuan mata kuliah perlu ditetapkan sebelum ruang lingkup ini dijadikan dasar implementasi akhir.

Target latensi pengenalan adalah paling lama 200 ms, dengan definisi operasional yang diusulkan berupa waktu dari akhir kata yang diucapkan sampai kata terkonfirmasi tampil pada panel pengguna. Waktu penggabungan beberapa kata menjadi perintah dan waktu perubahan slide diukur terpisah. Target tersebut merupakan kriteria yang akan diuji, bukan pernyataan performa yang telah dicapai.

# BAB 2 DASAR PENGENALAN SUARA

## 2.1 Konsep Pengenalan Suara

Pengenalan suara merupakan proses mengubah sinyal ucapan menjadi representasi linguistik, seperti kata atau rangkaian kata. Sinyal audio merepresentasikan perubahan amplitudo terhadap waktu, sedangkan model memerlukan pola yang dapat digunakan untuk membedakan ucapan. Oleh karena itu, proses pengenalan mencakup pembentukan representasi audio, pengambilan keputusan model, dan penentuan keluaran yang akan ditampilkan.

Voice Slide Control menggunakan pengenalan kata dengan kosakata terbatas. Pada tingkat model, tugasnya adalah memilih kelas kata dari fitur suatu jendela audio. Pada tingkat aplikasi, prediksi tersebut diproses dari waktu ke waktu untuk menghasilkan rangkaian kata perintah. Perbedaan ini penting karena ketepatan klasifikasi satu klip audio belum menjamin ketepatan rangkaian perintah dalam audio yang diterima secara berkelanjutan.

Istilah real-time pada proyek ini merujuk pada pemrosesan audio ketika audio terus masuk, disertai pembaruan keluaran tanpa menunggu pengguna menyelesaikan seluruh rekaman. Kemampuan tersebut akan dinilai melalui pengujian aliran audio dan pengukuran latensi. Frekuensi pemanggilan model yang tinggi saja tidak membuktikan bahwa hasil pengenalan sudah akurat dan responsif.

## 2.2 Pemrosesan Ucapan

Pemrosesan dimulai dengan representasi audio mono pada laju sampel 16.000 Hz. Sebagai konfigurasi awal, analisis spektral menggunakan bingkai sepanjang 25 ms dan pergeseran antarbingkai 10 ms. Pada laju sampel tersebut, panjang bingkai adalah 400 sampel dan pergeserannya 160 sampel. Parameter yang sama digunakan dalam pelatihan dan inferensi agar representasi masukan konsisten.

MFCC dibentuk melalui pembagian sinyal menjadi bingkai, penerapan fungsi jendela, perhitungan spektrum daya, pemetaan energi menggunakan bank filter Mel, transformasi logaritmik, dan Discrete Cosine Transform (DCT). Rancangan mengambil 13 koefisien untuk setiap bingkai. Skala Mel menyediakan representasi frekuensi yang relevan bagi persepsi pendengaran, sedangkan DCT membentuk representasi cepstral yang lebih ringkas [2].

Fitur delta orde pertama dan kedua ditambahkan untuk mewakili perubahan MFCC terhadap waktu. Gabungan 13 MFCC, 13 delta, dan 13 delta orde kedua menghasilkan 39 komponen per bingkai [3]. Ekstraksi ini ditempatkan sebagai modul terpisah sebelum klasifikasi. Dengan demikian, fitur yang digunakan model dapat diperiksa, disimpan, dan dibandingkan tanpa bergantung pada ekstraktor fitur neural.

## 2.3 Pipeline Pengenalan Suara

Pipeline rancangan terdiri atas penerimaan audio, penyiapan format audio, ekstraksi MFCC, penggabungan fitur, penskalaan, klasifikasi, pemrosesan temporal, penyusunan perintah, dan penyajian keluaran. Pada tahap pelatihan, pipeline menghasilkan pasangan vektor fitur dan label kata. Pada tahap inferensi, pipeline yang sama mengubah audio baru menjadi prediksi kelas.

Karena jumlah bingkai dalam suatu potongan audio dapat berbeda, keluaran MFCC perlu diubah menjadi vektor berdimensi tetap. Rancangan menggunakan statistics pooling, yaitu perhitungan nilai rata-rata, simpangan baku, minimum, dan maksimum untuk masing-masing dari 39 komponen. Hasilnya adalah vektor dengan 39 × 4 = 156 dimensi. Vektor tersebut menjadi masukan model klasifikasi.

Parameter ekstraksi, pengisian audio pendek, pembentukan fitur, dan penskalaan harus konsisten antara pelatihan dan inferensi. Ketidaksesuaian pada tahap tersebut dapat mengubah distribusi fitur dan menurunkan ketepatan model. Pada evaluasi, rekaman akan diputar melalui jalur pemrosesan yang sama dengan mikrofon agar pengukuran tidak hanya mencerminkan klasifikasi berkas secara terpisah.

## 2.4 Model yang Dipilih

Model utama yang dipilih adalah Linear SVM dengan implementasi LinearSVC pada scikit-learn. Model ini dipilih sebagai pendekatan awal karena dapat menerima vektor fitur berdimensi tetap, dilatih sebagai model classical machine learning, dan memberikan fungsi keputusan yang dapat dijelaskan. Implementasi LinearSVC juga sesuai sebagai kandidat awal untuk jumlah sampel yang lebih besar dibandingkan pendekatan SVM berbasis kernel yang membutuhkan pelatihan lebih mahal [4, 6].

Random Forest digunakan sebagai pembanding untuk memeriksa apakah keluarga model yang berbeda memberikan ketepatan dan karakteristik waktu pemrosesan yang lebih sesuai pada fitur yang sama. Model tersebut menggabungkan keputusan sejumlah pohon klasifikasi [7]. Perbandingan menggunakan pembagian data dan prosedur evaluasi yang konsisten.

Pemilihan Linear SVM sebagai model utama merupakan keputusan rancangan. Keputusan model yang digunakan pada aplikasi akhir akan mempertimbangkan WER, ketepatan per kelas, aktivasi palsu, dan latensi yang benar-benar terukur. Rancangan ini tidak mengasumsikan bahwa salah satu model pasti lebih akurat sebelum eksperimen dilakukan.

## 2.5 Arsitektur Model

Arsitektur model terdiri atas vektor fitur 156 dimensi, StandardScaler, dan LinearSVC. StandardScaler mengubah fitur berdasarkan rata-rata dan simpangan baku yang dipelajari dari data latih. Transformasi dapat dinyatakan sebagai z_j = (x_j - μ_j) / σ_j, dengan x_j sebagai fitur masukan, μ_j sebagai rata-rata data latih, dan σ_j sebagai simpangan baku data latih [5]. Data validasi dan data uji hanya ditransformasikan menggunakan parameter yang sudah dipelajari tersebut.

Klasifikasi multikelas LinearSVC dirancang menggunakan pendekatan one-vs-rest. Setiap kelas memiliki fungsi keputusan linear s_k(z) = w_kᵀz + b_k. Kelas dengan skor tertinggi menjadi kandidat prediksi. Pelatihan mempelajari parameter w_k dan b_k dengan menyeimbangkan pemisahan kelas dan regularisasi [4].

Skor fungsi keputusan bukan probabilitas. Oleh sebab itu, antarmuka akan menyebutnya sebagai skor model, kecuali kalibrasi probabilitas ditambahkan dan diverifikasi. Ambang penerimaan, selisih antara skor kandidat tertinggi dan kandidat kedua, serta kestabilan prediksi dapat digunakan sebagai bahan pengujian untuk menentukan apakah suatu kandidat layak dikonfirmasi.

## 2.6 Inferensi Lokal

Inferensi lokal berarti perhitungan fitur dan prediksi kata dilakukan pada komputer pengguna. Model dan parameter scaler disimpan sebagai berkas lokal, kemudian dimuat ketika aplikasi dijalankan. Proses pengenalan tidak mengirim audio ke layanan Speech Recognition eksternal dan tidak bergantung pada koneksi jaringan untuk melakukan klasifikasi.

Jalur pengenalan direncanakan berjalan menggunakan CPU. Kemampuan memenuhi target latensi tetap perlu diukur pada perangkat yang benar-benar digunakan. Proses pemuatan model, pemrosesan audio pertama, dan kondisi pemrosesan yang sudah stabil dapat menghasilkan waktu berbeda, sehingga pengukuran akan membedakan kondisi awal dan kondisi operasi berkelanjutan.

Unduhan dataset atau dependensi pada tahap pengembangan berbeda dari pengiriman audio untuk inferensi. Jika Canva digunakan sebagai platform presentasi, kebutuhan jaringan Canva juga dipisahkan dari sifat lokal sistem pengenalan suara. Dengan pemisahan tersebut, klaim inferensi lokal merujuk secara khusus pada jalur pemrosesan audio dan pengenalan kata.

## 2.7 Algoritma yang Relevan

Algoritma yang digunakan meliputi transformasi Fourier untuk pembentukan spektrum, bank filter Mel dan DCT untuk MFCC, perhitungan turunan temporal untuk fitur delta, statistics pooling, standardisasi fitur, serta klasifikasi Linear SVM. Random Forest digunakan pada eksperimen pembanding. Keluaran classifier selanjutnya diproses menggunakan penggabungan prediksi temporal dan finite state machine.

Penggabungan prediksi temporal memeriksa kandidat pada beberapa jendela yang bertumpang tindih agar satu kata tidak menghasilkan banyak keluaran yang sama. Pengendalian pengulangan perlu mempertimbangkan berakhirnya kejadian ucapan, perubahan kandidat, atau kembalinya sistem ke kondisi tanpa kata target. Penolakan berdasarkan jeda waktu tetap saja dapat menghilangkan pengulangan yang disengaja, misalnya "right right" atau dua digit yang sama.

Finite state machine digunakan untuk mengatur kondisi menunggu kata pemicu, menerima perintah, mengumpulkan digit, dan mengeksekusi aksi. Struktur ini membatasi urutan perintah yang dapat dijalankan, tetapi tidak menjamin bahwa kata yang dikenali benar. Pengenalan akustik dan keabsahan grammar tetap menjadi dua aspek yang dievaluasi terpisah.

WER digunakan untuk menilai rangkaian keluaran kata dengan persamaan WER = (S + D + I) / N. S menyatakan jumlah substitusi, D jumlah penghapusan, I jumlah penyisipan, dan N jumlah kata pada referensi. Referensi dan hipotesis akan memakai aturan normalisasi yang sama. Akurasi klip tunggal dilaporkan terpisah agar tidak dianggap setara dengan ketepatan transkrip perintah.

## 2.8 Keterbatasan Model

Linear SVM pada rancangan ini hanya dapat memilih kelas yang ditetapkan saat pelatihan. Model tidak dapat menghasilkan kata baru di luar kosakata. Kelas unknown membantu menyediakan pilihan penolakan, tetapi sampel unknown dari kata-kata dataset tidak merepresentasikan seluruh kemungkinan percakapan, musik, batuk, atau suara lingkungan. Ketahanan terhadap masukan tersebut memerlukan pengujian pada rekaman yang lebih menyerupai penggunaan sebenarnya.

Statistics pooling mengurangi kebutuhan terhadap panjang masukan yang seragam, tetapi menghilangkan sebagian informasi urutan antarbingkai. Jendela yang mengandung dua kata, kata yang belum selesai, atau suara penjelasan yang menyambung dengan perintah dapat menghasilkan fitur berbeda dari klip kata terisolasi. Oleh sebab itu, ketepatan pada dataset tidak dapat langsung dianggap sebagai ketepatan pada presentasi yang berlangsung terus-menerus.

Variasi pembicara, aksen, jarak mikrofon, dan derau dapat mengubah fitur. Dampak setiap faktor perlu dibedakan melalui rancangan pengujian yang sesuai. Selisih hasil antara dataset dan pengguna Indonesia tidak dapat langsung diatribusikan hanya kepada aksen karena kondisi mikrofon dan lingkungan juga dapat berbeda.

Model juga menghasilkan kompromi antara penerimaan dan penolakan. Ambang yang ketat dapat mengurangi aktivasi palsu, tetapi berpotensi meningkatkan jumlah perintah sah yang tidak diterima. Penetapan ambang akan menggunakan data validasi dan mempertimbangkan kebutuhan pengguna, bukan ditentukan hanya berdasarkan angka akurasi keseluruhan.

# BAB 3 DESAIN SISTEM

## 3.1 Arsitektur Sistem

Arsitektur sistem dirancang secara modular untuk memisahkan penerimaan audio, pengenalan kata, penyusunan perintah, integrasi presentasi, dan antarmuka pengguna. Pemisahan tersebut memungkinkan model pembanding menggunakan jalur audio dan fitur yang sama. Sumber mikrofon dan sumber berkas juga menggunakan format keluaran yang sama agar pengujian dapat dilakukan tanpa mengubah komponen pengenalan.

Jalur utama terdiri atas sumber audio, buffer melingkar, modul prapemrosesan dan MFCC, modul scaler dan classifier, penggabung prediksi temporal, serta decoder perintah. Setelah kata diproses secara temporal, keluaran bercabang menjadi transkrip pada panel pengguna dan masukan decoder. Transkrip kata tidak menunggu selesainya penggabungan beberapa kata menjadi aksi.

Decoder mengirim aksi yang sah ke adapter presentasi. Adapter PowerPoint dan adapter Canva memiliki antarmuka perintah yang sama, tetapi menggunakan pemetaan kendali berbeda. Modul pencatatan waktu memantau tahap pengenalan, pengiriman transkrip, dan eksekusi aksi. Diagram berikut menunjukkan rancangan alur utama.

```text
Mikrofon atau pemutaran berkas
             |
             v
Buffer audio dan prapemrosesan
             |
             v
MFCC dan fitur delta -> pooling 156 dimensi
             |
             v
StandardScaler -> Linear SVM atau Random Forest
             |
             v
Kandidat kata -> penggabungan prediksi temporal
             |
             +------> Transkrip sementara dan terkonfirmasi
             |
             v
Decoder kata pemicu dan grammar
             |
             v
Adapter PowerPoint atau Canva -> aksi presentasi

Pencatatan waktu dan kejadian dilakukan sepanjang pipeline.
```

## 3.2 Aliran Data

Audio masuk sebagai blok sampel yang dilengkapi nomor urut dan informasi waktu berdasarkan posisi sampel. Blok tersebut dimasukkan ke buffer melingkar yang menyimpan audio terbaru. Worker pengenalan mengambil snapshot buffer dan mengubahnya menjadi vektor fitur. Model kemudian menghasilkan kandidat kelas, skor keputusan, dan waktu selesainya prediksi.

Modul temporal menerima kandidat tersebut dan menghasilkan kejadian keluaran sementara atau terkonfirmasi. Kejadian terkonfirmasi dikirim kepada modul transkrip dan decoder perintah. Kelas silence dan unknown digunakan sebagai informasi penolakan serta status internal; keduanya tidak diterjemahkan menjadi kata yang seolah-olah benar-benar diucapkan pengguna.

Keputusan decoder diteruskan ke adapter presentasi dalam bentuk aksi terstruktur, misalnya NEXT, PREVIOUS, atau GOTO dengan nomor slide. Hasil pengiriman dicatat pada log aksi. Adapter yang hanya mengirim keystroke harus membedakan status "aksi dikirim" dari status "perubahan slide terverifikasi", karena keberhasilan pengiriman tombol belum membuktikan keadaan akhir aplikasi presentasi.

## 3.3 Audio Streaming

Audio diterima secara berkelanjutan selama pengguna mengaktifkan mode mendengarkan. Konfigurasi awal menggunakan audio mono 16 kHz dan blok penerimaan sekitar 25 ms. Buffer melingkar menyimpan paling banyak satu detik audio terakhir. Jendela satu detik merupakan konteks audio sebelumnya, bukan instruksi untuk selalu menunggu satu detik setelah kata selesai sebelum melakukan prediksi.

Snapshot untuk pengenalan direncanakan diambil setiap 25 ms sebagai titik awal pengujian. Interval tersebut berbeda dari pergeseran 10 ms pada analisis MFCC. Interval snapshot mengatur frekuensi pengenalan, sedangkan pergeseran bingkai MFCC mengatur analisis di dalam satu snapshot. Parameter dapat disesuaikan berdasarkan ketepatan, beban pemrosesan, dan latensi yang diukur.

Callback audio hanya menerima dan menyalin sampel agar tidak tertahan oleh ekstraksi fitur, inferensi, atau kendali presentasi. Pemrosesan tersebut ditempatkan pada worker terpisah dengan antrean terbatas. Jika sistem tidak dapat memproses setiap snapshot, strategi pengambilan snapshot terbaru perlu dicatat dan diuji agar tidak menimbulkan backlog yang terus bertambah atau kehilangan kata perintah.

Sumber berkas akan mengirim audio mengikuti waktu sampel, sehingga dapat digunakan untuk mengulang skenario yang sama melalui pipeline streaming. Dengan jendela bertumpang tindih, beban pemrosesan perlu dinilai terhadap waktu audio baru yang masuk. Pemrosesan satu snapshot dalam waktu lebih singkat dari durasi satu detik belum membuktikan sistem mampu mengikuti snapshot yang dijadwalkan setiap 25 ms.

## 3.4 Prapemrosesan

Prapemrosesan mencakup pemeriksaan format, pengubahan audio multikanal menjadi mono jika diperlukan, penyesuaian laju sampel, konversi representasi amplitudo, dan penanganan audio pendek. Sampel yang belum memenuhi panjang jendela diberi padding sesuai kebijakan yang sama pada pelatihan dan inferensi. Normalisasi yang menguatkan audio sangat pelan secara berlebihan dihindari karena dapat memperbesar derau dan memicu prediksi yang keliru.

Sebagai konfigurasi awal, MFCC menggunakan 13 koefisien, 40 filter Mel, jendela Hamming 25 ms, pergeseran 10 ms, dan FFT 512 titik. Nilai-nilai tersebut merupakan parameter rancangan yang akan diverifikasi. Analisis dilakukan tanpa pemusatan bingkai yang memerlukan sampel masa depan. Fitur delta dihitung dari bingkai yang sudah tersedia, dengan penanganan batas yang terdokumentasi agar tidak ada penundaan tambahan yang tersembunyi.

Setelah pooling, vektor 156 dimensi ditransformasikan menggunakan scaler yang telah dilatih. Jika augmentasi pergeseran posisi kata atau campuran derau digunakan, augmentasi hanya dibentuk dari data latih. Pembagian data dilakukan sebelum augmentasi untuk menghindari versi berbeda dari rekaman yang sama muncul pada data latih dan data uji. Untuk pembentukan silence, pemisahan sumber atau segmen noise juga perlu dicatat.

## 3.5 Model Pengenalan Lokal

Model lokal menyimpan daftar kelas, parameter scaler, parameter classifier, dan konfigurasi fitur yang digunakan. Metadata tersebut diperlukan untuk memastikan bahwa model dimuat dengan urutan label dan representasi masukan yang benar. Antarmuka classifier menerima vektor fitur dan mengembalikan kandidat label beserta skor, sedangkan informasi waktu dicatat oleh pipeline.

Untuk membentuk kelas unknown, kata-kata yang tidak dipilih sebagai perintah atau pemicu digabungkan ke dalam kelas penolakan. Pada rancangan 35 kata dengan 20 kata perintah dan satu pemicu, terdapat 14 kata sumber untuk kelas tersebut. Sampel silence dibentuk dari keheningan dan potongan latar yang sesuai. Keseimbangan kelas serta jumlah sampel setiap kelas akan dicatat karena dapat memengaruhi keputusan model.

Linear SVM dan Random Forest menggunakan definisi kelas dan fitur yang sama. Parameter model dan ambang temporal dipilih menggunakan data validasi, kemudian dibekukan untuk pengujian akhir. Rekaman pengguna yang dipakai sebagai pengujian akhir tidak digunakan kembali untuk menyesuaikan model tanpa pemisahan data pengembangan yang jelas.

## 3.6 Pipeline Inferensi

Inferensi dimulai dengan pengambilan snapshot audio, pembentukan fitur, penskalaan, dan klasifikasi. Kandidat kata ditampilkan sebagai prediksi sementara jika memenuhi aturan tampilan, lalu dikonfirmasi setelah memenuhi aturan kestabilan dan penerimaan. Prediksi pada jendela yang berdekatan tidak diperlakukan sebagai kejadian kata yang berbeda secara otomatis.

Decoder perintah menggunakan kondisi IDLE, ARMED, COLLECTING_DIGITS, dan EXECUTING. Pada kondisi IDLE, aksi dinonaktifkan sampai kata "marvin" dikonfirmasi. Kondisi ARMED menerima urutan perintah dalam batas waktu yang ditentukan. Setelah satu aksi dijalankan, sistem kembali ke IDLE. Batas waktu, pembatalan, dan status kesiapan ditampilkan agar pengguna dapat memahami kondisi sistem.

Pemetaan awal meliputi "right" untuk navigasi berikutnya, "left" untuk navigasi sebelumnya, "up" untuk awal presentasi, "down" untuk akhir presentasi, dan "go" diikuti digit untuk memilih nomor slide. Urutan "go one two" membentuk nomor 12. Decoder perlu memvalidasi nomor dan kemampuan platform sebelum menjalankan aksi. Angka yang berulang harus tetap dapat diterima sebagai kejadian yang berbeda.

Kata "go" tanpa digit direncanakan sebagai perintah memulai presentasi. Karena memiliki awalan yang sama dengan perintah pemilihan nomor slide, decoder perlu menunggu batas waktu tanpa digit sebelum menentukan aksi. Batas awal 1,5 detik akan diuji dan dapat direvisi. Waktu tunggu grammar tersebut dicatat sebagai bagian latensi aksi, sementara kata "go" dapat ditampilkan lebih dahulu pada transkrip. Fungsi "on", "off", "yes", dan "no" hanya diaktifkan pada konteks yang mendukungnya.

Adapter PowerPoint dapat menggunakan kendali slideshow langsung atau shortcut yang sesuai. Shortcut navigasi standar dapat menjalankan animasi terlebih dahulu, sehingga kebutuhan "langkah berikutnya" dan "slide berikutnya" harus dibedakan dalam pengujian [8]. Adapter Canva akan memakai kendali yang sesuai dengan mode presentasi dan diuji secara terpisah [9]. Sistem tidak mengasumsikan bahwa satu shortcut memiliki arti yang sama pada kedua platform.

## 3.7 Transkripsi Real Time

Transkripsi pada aplikasi berupa urutan kata perintah. Prediksi sementara ditampilkan pada area yang dapat diperbarui, sedangkan kata terkonfirmasi ditambahkan pada riwayat transkrip. Pemisahan ini menunjukkan bahwa prediksi awal masih dapat berubah. Riwayat pengenalan dan log aksi dipisahkan agar kata yang dikenali tidak otomatis dianggap sebagai perintah yang sudah dijalankan.

Ucapan biasa tidak ditranskripsikan menjadi kalimat bebas. Sistem dapat mendeteksi kandidat kata target dalam percakapan, tetapi decoder tetap membutuhkan pemicu dan urutan yang sah untuk menjalankan aksi. Dengan demikian, perlindungan terhadap aksi palsu tidak bergantung hanya pada keberadaan kelas unknown.

Pengukuran latensi pengenalan diusulkan sebagai L_rec = t_tampil_terkonfirmasi - t_akhir_kata. Latensi prediksi sementara dicatat terpisah. Pada pengujian berkas, akhir kata perlu diberi anotasi berdasarkan audio; akhir berkas WAV tidak selalu sama dengan akhir ucapan karena dapat mengandung keheningan. Pada pengujian mikrofon, estimasi batas kata harus diberi keterangan sebagai estimasi, bukan dianggap sebagai ground truth yang pasti.

Waktu sampai label diprediksi pada backend dan waktu sampai label tampil pada antarmuka merupakan ukuran berbeda. Pengukuran yang mengklaim keluaran telah tampil harus menyertakan pengiriman dan pembaruan antarmuka. Latensi aksi L_action dihitung sampai perubahan presentasi terverifikasi, sedangkan waktu pengiriman instruksi dilaporkan terpisah jika verifikasi belum tersedia. Hasil akan mencakup distribusi latensi, termasuk median dan persentil ke-95; klaim batas maksimum membutuhkan pemeriksaan seluruh kejadian yang dinilai.

## 3.8 Antarmuka Aplikasi

Antarmuka dirancang sebagai panel lokal untuk presenter, dengan PowerPoint atau Canva tetap digunakan untuk menampilkan materi kepada audiens. Panel dapat diakses melalui browser lokal yang terhubung ke backend Python. Pembaruan prediksi dan status dikirim melalui koneksi lokal, misalnya WebSocket, agar pengguna tidak perlu memuat ulang halaman.

Elemen utama panel meliputi tombol mulai dan berhenti mendengarkan, pemilihan perangkat mikrofon, indikator aktivitas audio, pilihan platform, prediksi sementara, riwayat kata terkonfirmasi, status kata pemicu, dan aksi terakhir. Pengaturan ambang atau model dapat disediakan pada bagian konfigurasi pengujian, sehingga alur penggunaan utama tetap sederhana.

Panel juga menyediakan informasi waktu pemrosesan dan hasil pengukuran latensi yang memiliki dasar waktu valid. Jika akhir kata pada sesi langsung belum dapat diketahui dengan andal, tampilan menyebut ukuran yang tersedia sebagai waktu pemrosesan, bukan menampilkannya sebagai latensi pengenalan penuh. Nomor slide aktual hanya ditampilkan jika adapter dapat membaca atau memverifikasinya; jika tidak, panel menampilkan tujuan perintah terakhir.

Status kegagalan dibuat jelas, misalnya mikrofon tidak tersedia, platform presentasi belum aktif, perintah kedaluwarsa, atau nomor slide tidak valid. Pada integrasi berbasis keystroke, perpindahan fokus jendela dapat mengubah tujuan tombol yang dikirim. Oleh sebab itu, kesiapan platform perlu diperiksa sebelum aksi. Pengguna tetap dapat menghentikan penerimaan perintah ketika aplikasi tidak diperlukan.

# REFERENSI

[1] Warden, P. (2018). Speech Commands A Dataset for Limited Vocabulary Speech Recognition. arXiv:1804.03209. https://arxiv.org/abs/1804.03209

[2] librosa. Dokumentasi librosa.feature.mfcc versi 0.11.0. https://librosa.org/doc/0.11.0/generated/librosa.feature.mfcc.html

[3] librosa. Dokumentasi librosa.feature.delta versi 0.11.0. https://librosa.org/doc/0.11.0/generated/librosa.feature.delta.html

[4] scikit-learn. Dokumentasi LinearSVC. https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html

[5] scikit-learn. Dokumentasi StandardScaler. https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html

[6] scikit-learn. Dokumentasi SVC. https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html

[7] scikit-learn. Dokumentasi RandomForestClassifier. https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html

[8] Microsoft. Use keyboard shortcuts to deliver PowerPoint presentations. https://support.microsoft.com/en-us/accessibility/powerpoint/use-keyboard-shortcuts-to-deliver-powerpoint-presentations

[9] Canva. Present your design dan Presentation modes. https://www.canva.com/help/presenting-designs/ ; https://www.canva.com/help/presentation-modes/

[10] BINUS University. FINAL_PROJECT_Speech_Recognition_CASE. COMP6822001 Speech Recognition. Tahun akademik 2026/2027. Dokumen ketentuan proyek yang disediakan untuk mata kuliah.

Dokumentasi daring diakses pada 6 Oktober 2026.
