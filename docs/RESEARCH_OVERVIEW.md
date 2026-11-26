# Gambaran Umum Penelitian — RuralLink

Dokumen ini menjelaskan penelitian RuralLink dalam bahasa yang mudah dipahami oleh seluruh anggota tim tanpa memerlukan latar belakang pemrograman.

## 1. Konteks Nasional & Masalah *Uplink*
Data **Laporan Kinerja Komdigi 2025** (hal. 104–105) menunjukkan bahwa cakupan 4G di Indonesia sudah menjangkau **98,95% populasi**, tetapi baru mencakup **53,82% luas wilayah daratan**. Di wilayah 3T (Terdepan, Terluar, Tertinggal), jarak antar-menara BTS sangat jauh karena kepadatan penduduk yang rendah.

Pada sel pedesaan yang luas, komunikasi dua arah tidak simetris:
- **Downlink (BTS → HP):** BTS memancarkan daya besar (ilustratif ~`43 dBm`).
- **Uplink (HP → BTS):** HP memiliki baterai dan penguat kecil sehingga daya pancarnya terbatas (ilustratif ~`23 dBm`, selisih `20 dB`).

Akibatnya, pengguna di pinggir sel sering kali masih melihat ikon sinyal di layar, tetapi gagal mengirim data atau melakukan panggilan karena sinyal *uplink* tidak cukup kuat mencapai BTS.

## 2. Motivasi & Celah Penelitian
Penelitian ini menggabungkan dua ide dari literatur ilmiah:
1. **Reddy et al. (2022):** Mempersempit alokasi *Resource Block* (RB) pada daya total UE yang tetap akan memusatkan energi per RB dan menurunkan derau penerima, sehingga jangkauan *uplink* bertambah.
2. **Khan et al. (2025):** Menyesuaikan tingkat modulasi (`BPSK`, `QPSK`, `16-QAM`, `64-QAM`) berdasarkan kondisi kanal agar BER tetap terjaga di bawah target $10^{-2}$.

Sebagai proyek pendidikan sarjana, RuralLink mengadaptasi kedua konsep tersebut ke dalam simulator *link-level* sederhana pada frekuensi `900 MHz` dan `1800 MHz` menggunakan parameter propagasi *Close-In* dari **Park et al. (2023)** dan parameter RF pedesaan dari **Yogapratama et al. (2015)**.

## 3. Desain Eksperimen & Skenario yang Dievaluasi
Simulator Python (`src/adaptive.py`, `experiments/run_adaptive.py`) membandingkan lima skenario (`5.000` realisasi *shared* shadowing + Rayleigh per jarak, `seed = 42`):
- **S0:** Modulasi tetap (`QPSK`) + Bandwidth tetap (`25 RB`) (*baseline*).
- **S1:** Modulasi adaptif (`BPSK`–`64-QAM`) + Bandwidth tetap (`25 RB`).
- **S2:** Modulasi tetap (`QPSK`) + Bandwidth adaptif (`1–25 RB`).
- **S3:** Modulasi adaptif + Bandwidth adaptif secara bersamaan (*joint adaptive*).
- **R0:** Referensi ketahanan maksimum (`BPSK` + `1 RB`).

## 4. Temuan Terverifikasi (`outputs/summary.md`)
- Secara matematis (**THEORETICAL**), frekuensi `1800 MHz` memiliki *path loss* `6,0206 dB` lebih besar daripada `900 MHz` pada eksponen $n$ yang sama, dan memperkecil alokasi dari `25 RB` ke `1 RB` meningkatkan SNR sebesar `13,9794 dB`.
- Simulasi Monte Carlo *bit-level* (**SIMULATED**) untuk keempat modulasi di kanal AWGN dan Rayleigh telah cocok dengan kurva teoretis eksak.
- Pada evaluasi shadowing + Rayleigh dengan CSI sesaat (**SIMULATED**), `S3` memperluas radius andal `1800 MHz LOS` dari `1,75 km` (`S0`) menjadi `11,25 km`, dan pada `900 MHz NLOS 2 km` menekan *outage* dari `38,9%` (`S0`) menjadi `5,7%` sambil menjaga laju efektif `11,97 Mbit/s` (dibanding `0,17 Mbit/s` pada `R0`).

## 5. Batasan & Cakupan Kesimpulan
RuralLink adalah model *link-level* tanpa *channel coding* (FEC), tanpa interferensi antar-sel, dan menggunakan parameter *path loss* Korea Selatan yang diekstrapolasi. Oleh karena itu, hasil simulasi belum dapat diklaim sebagai cakupan geografis nyata di Indonesia, dan estimasi jarak `>=12 km` bersifat tersensor kanan oleh batas rentang uji.
