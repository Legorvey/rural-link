# Panduan Presentasi & Tanya-Jawab (Q&A) — RuralLink

Dokumen ini mempersiapkan seluruh tim untuk presentasi pada **26 November 2026, 15.00 WIB** di hadapan **Bu Dessy**.

## 1. Alur Narasi & Demo Singkat
- **Pembukaan (30 detik):** "RuralLink adalah proyek riset *link-level* untuk menganalisis batas jangkauan *uplink* di wilayah 3T Indonesia. Karena daya pancar HP jauh lebih kecil dari BTS, koneksi sering gagal di arah *uplink*. Kami memodelkan kombinasi modulasi adaptif dan penyempitan bandwidth (RB) pada 900 dan 1800 MHz."
- **Urutan Demo (Lihat detail di [docs/DEMO_GUIDE.md](DEMO_GUIDE.md)):**
  1. Buka website statis `public/index.html` atau `dashboard_rurallink.html` langsung di browser (100% offline, tanpa backend).
  2. Tunjukkan Tab **Simulator Interaktif** (perbandingan 900 vs 1800 MHz, skenario S0 vs S3, peta zona radial), lalu pindah ke Tab **Hasil Penelitian** untuk angka resmi dari `outputs/summary.md`.
- **Rencana Pemulihan (Fallback):**
  - Website HTML berjalan 100% lokal tanpa internet dan tanpa Python.
  - Grafik PNG di `outputs/figures/` dan tabel CSV di `outputs/results/` tersedia langsung untuk disisipkan di slide.

## 2. Tanya-Jawab (Q&A) Teknis (20 Pertanyaan)

1. **Mengapa memilih *uplink*?** Karena daya pancar UE (`23 dBm`) jauh lebih kecil dari BTS (`43 dBm`), sehingga *uplink* menjadi *bottleneck* jangkauan di sel pedesaan luas.
2. **Mengapa 900 MHz dan 1800 MHz?** Keduanya adalah pita frekuensi utama LTE pedesaan di Indonesia (sesuai Yogapratama et al., 2015), di mana 900 MHz memberi jangkauan lebih jauh (`6,02 dB` lebih rendah *path loss*-nya).
3. **Mengapa tidak langsung menyalin implementasi penuh Reddy et al. (2022)?** Reddy menggunakan 700 MHz, 16 antena BS, dan HARQ/BLER penuh. RuralLink menyederhanakannya menjadi model *link-level* tak-berkode (*uncoded*) agar jernih untuk analisis fundamental.
4. **Apa itu *Close-In* (CI) *path loss*?** Model propagasi berbasis jarak referensi $d_0 = 1\text{ m}$ dengan satu parameter eksponen $n$ dan *shadow fading* $\sigma$.
5. **Mengapa memakai parameter pengukuran Korea Selatan (Park 2023)?** Karena belum ada data pengukuran CI pedesaan 3T Indonesia yang tersedia; keterbatasan ini kami catat secara eksplisit.
6. **Apa itu LOS dan NLOS?** *Line-of-Sight* (pandangan langsung tanpa halangan, $n=2{,}16$) dan *Non-Line-of-Sight* (terhalang bangunan/vegetasi, $n=2{,}56$, variasi $\sigma=11{,}40\text{ dB}$).
7. **Mengapa Rayleigh lebih buruk daripada AWGN?** Karena kanal Rayleigh mengalami fluktuasi amplitudo acak (*multipath fading*) yang menyebabkan *deep fade* sesaat, sehingga rata-rata BER turun jauh lebih lambat.
8. **Mengapa kurva BPSK dan QPSK berimpit terhadap $E_b/N_0$?** Karena QPSK dapat dipandang sebagai dua kanal BPSK ortogonal (I dan Q) yang masing-masing membawa 1 bit dengan energi per bit yang sama.
9. **Mengapa ambang batas SNR ($E_s/N_0$) pergantian modulasi berbeda?** Karena $E_s/N_0 = E_b/N_0 + 10\log_{10}(k)$. QPSK ($k=2$) butuh `3,01 dB` lebih tinggi daripada BPSK ($k=1$).
10. **Mengapa mempersempit bandwidth meningkatkan SNR?** Pada daya pancar total UE yang tetap, memperkecil jumlah RB menurunkan daya derau termal penerima ($N = -174 + 10\log_{10}(B) + \mathrm{NF}$), sehingga SNR naik (`+13,98 dB` dari 25 ke 1 RB).
11. **Apakah modulasi adaptif memperbesar daya terima?** Tidak. Modulasi adaptif hanya memilih skema deteksi yang lebih tahan derau, tidak mengubah daya terima maupun *path loss*.
12. **Apa arti $\text{BER} = 0{,}01$?** Rata-rata 1 bit salah dari setiap 100 bit yang dikirim; digunakan sebagai target batas keandalan sebelum *channel coding* (mengikuti Khan 2025).
13. **Bagaimana *outage* didefinisikan?** Kondisi ketika SNR atau BER gagal memenuhi target keandalan ($\text{BER} > 10^{-2}$), dengan batas probabilitas *outage* target $P_{\text{out}} \le 5\%$ (95% keandalan).
14. **Apa itu simulasi Monte Carlo?** Metode mengirim jutaan bit acak melalui model kanal di mesin Python dan menghitung rasio kesalahan bit secara empiris untuk memvalidasi rumus teoretis.
15. **Bagaimana cara memvalidasi simulasi?** Membandingkan kurva Monte Carlo Python dengan rumus eksak (Cho–Yoon AWGN & Rayleigh), memeriksa konservasi energi $E_s = 1$, dan menjalankan pengujian otomatis `pytest`.
16. **Apakah laju data yang dihitung adalah *throughput* LTE nyata?** Bukan. Ini adalah *nominal data rate* ($B_{\text{active}} \cdot k$) tanpa *overhead* protokol, *cyclic prefix*, maupun FEC.
17. **Apakah estimasi jangkauan ini berlaku untuk seluruh Indonesia?** Tidak. Ini adalah simulasi *link-level* dengan parameter ekstrapolasi, bukan pemetaan geografis nasional.
18. **Apa perbedaan website HTML dan simulasi Python di repo ini?** Website statis (`public/index.html`) memakai perhitungan analitis JavaScript untuk respons instan di browser, sedangkan eksperimen Python (`src/`, `experiments/`) menjalankan simulasi stokastik (`5.000` realisasi) dan validasi Monte Carlo *bit-level* (`1.000.000` bit) untuk menghasilkan `outputs/`.
19. **Apa kontribusi kelompok?** Membangun mesin simulasi *bit-level* tervalidasi (Python), mengevaluasi optimasi adaptif S0–S3 dan R0, serta menyajikan dashboard web statis interaktif karya Zahran.
20. **Apa keterbatasan yang masih tersisa?** Belum ada kalibrasi lapangan Indonesia, asumsi CSI sempurna, tanpa FEC/interferensi antar-sel, dan estimasi radius `>=12 km` tersensor oleh batas grid uji.
