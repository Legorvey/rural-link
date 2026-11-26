# Panduan Demo Presentasi RuralLink (Kelompok 1, 2026)

Dokumen ini memandu alur demo langsung `app.py` untuk presentasi kelas (proyeksi layar).
Seluruh metrik, kurva, zona, dan konstelasi berasal dari mesin Python (`src/`).

## 1. Preset Awal (Pemulihan Tepi Sel)
- Jalankan `.\run_local.ps1` (atau buka URL Streamlit Cloud).
- Klik **Preset: pemulihan tepi sel** di panel kiri.
- Parameter aktif: `900 MHz`, `NLOS`, `Shadowing: Median (0 dB)`, jarak `5.0 km`, daya UE `23 dBm`, strategi `S3: Joint adaptive`.
- Tunjukkan pada *telemetry strip*: pada 5,0 km NLOS, baseline `S0` (QPSK x 25 RB) mengalami **outage**, sedangkan `S3` memulihkan koneksi dengan menurunkan RB dan/atau orde modulasi.

## 2. Perbandingan Frekuensi (900 MHz vs 1800 MHz)
- Pada panel kiri, klik segmented control **1800** MHz, lalu kembali ke **900** MHz.
- Tunjukkan tabel **Perbandingan frekuensi pada jarak yang sama** di bagian bawah tab **A. Simulator langsung**: `900 MHz` memiliki path loss lebih rendah (~6,02 dB lebih kecil dari 1800 MHz) sehingga SNR dan radius cakupan lebih besar.

## 3. Perbandingan Fixed vs Adaptif (S0–S3 & R0)
- Tunjukkan tabel **Perbandingan strategi** pada tab **A. Simulator langsung**:
  - `S0` (fixed QPSK 25 RB) vs `S1` (adaptive modulation) vs `S2` (adaptive bandwidth) vs `S3` (joint adaptive) vs `R0` (fixed BPSK 1 RB).
  - Jelaskan bahwa semua strategi dievaluasi pada realisasi *shadowing* dan *Rayleigh fading* yang sama (*shared realizations*).
  - Beralih ke strategi `MANUAL` untuk menunjukkan bagaimana kontrol RB dan modulasi terbuka untuk uji manual (dan kembali ke `S3` untuk mode adaptif).

## 4. Simulasi Monte Carlo Bit-Level Aktual
- Pilih kanal `AWGN` atau `Rayleigh (CSI sesaat)`, lalu klik **Jalankan simulasi Monte Carlo**.
- Tunjukkan bahwa nilai BER MC dan titik konstelasi I/Q berasal dari transmisi bit acak aktual di mesin Python (`src/metrics.py` dan `src/channels.py`), bukan titik sintetis statis.
- Bandingkan panel **Dioptimalkan** vs **Baseline S0** serta perbedaan BER rata-rata Rayleigh tanpa CSI (4–7%) vs BER bersyarat adaptif (<= 1e-2).

## 5. Visualisasi Cakupan Radial
- Buka tab **B. Visualisasi cakupan**.
- Tunjukkan perbandingan sisi-ke-sisi `900 MHz` dan `1800 MHz` dengan posisi **BTS** (pusat), **UE** (jarak aktif), cincin modulasi (model radial hipotetis, bukan peta lapangan geografis), serta garis batas **radius andal 95% (SIMULATED)** vs **median PL (THEORETICAL)**.

## 6. Temuan Penelitian Utama (Tab C. Hasil penelitian)
- Buka tab **C. Hasil penelitian** untuk menampilkan kurva outage, laju efektif (outage = 0), serta tabel ringkasan:
  - **900 MHz NLOS, 2 km (shadowing + Rayleigh CSI):** `S0` outage `38.9%` (laju efektif `5.50 Mbit/s`), sedangkan `S3` menekan outage ke `5.7%` dengan laju efektif `11.97 Mbit/s` (`R0` juga `5.7%` tetapi hanya `0.17 Mbit/s`).
  - **1800 MHz NLOS, 2 km:** `S0` outage `57.8%` (`3.79 Mbit/s`), `S3` turun ke `12.0%` (`7.79 Mbit/s`).
  - **Batas radius:** `<1 km` menandakan outage pada titik uji pertama (1 km); `>=12 km` menandakan tersensor kanan oleh batas rentang evaluasi.

## 7. Rencana Cadangan Offline (Offline Fallback)
Jika koneksi internet atau Streamlit Cloud bermasalah saat presentasi:
1. Jalankan `.\run_local.ps1` di PowerShell (menggunakan `.venv` lokal, 100% offline).
2. Jika aplikasi web tidak dapat dibuka, gunakan grafik PNG di `outputs/figures/` dan ringkasan angka di `outputs/summary.md` serta `outputs/results/*.csv`.
