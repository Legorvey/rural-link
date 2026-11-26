# Panduan Demo Presentasi RuralLink (Kelompok 1, 2026)

Dokumen ini memandu alur demo langsung `app.py` untuk presentasi kelas (proyeksi layar).
Seluruh metrik, kurva, zona, dan konstelasi berasal dari mesin Python (`src/`).

## 1. Preset Awal (Pemulihan Tepi Sel)
- Jalankan `.\run_local.ps1` (atau buka URL Streamlit Cloud).
- Klik **Preset: pemulihan tepi sel** di panel kiri.
- Parameter aktif: `900 MHz`, `NLOS`, `Shadowing: Median (0 dB)`, jarak `5.0 km`, daya UE `23 dBm`, strategi `S3: Joint adaptive`, target BER `1e-2`.
- Seluruh elemen utama tampil dalam satu halaman **A. Workbench interaktif**: *telemetry strip* 8 sel, kurva **SNR vs jarak** dengan penanda jarak aktif, kontrol & konstelasi **Monte Carlo**, **peta zona modulasi radial sisi-ke-sisi**, serta tabel **Fixed vs adaptif** dan **Perbandingan frekuensi**.

## 2. Perbandingan Frekuensi (900 MHz vs 1800 MHz)
- Pada panel kiri, klik segmented control **1800** MHz, lalu kembali ke **900** MHz.
- Tunjukkan tabel **Perbandingan frekuensi** di bagian bawah workbench: `900 MHz` memiliki path loss lebih rendah (~6,02 dB lebih kecil dari `1800 MHz`) sehingga SNR dan radius cakupan lebih besar pada kondisi propagasi CI dan seed yang identik (`seed = 42`).

## 3. Perbandingan Fixed vs Adaptif (S0–S3 & R0) & Peta Zona Radial
- Tunjukkan tabel **Fixed vs adaptif** serta **Peta zona modulasi radial sisi-ke-sisi** langsung pada workbench utama:
  - `S0` (fixed QPSK 25 RB) vs `S1` (adaptive modulation) vs `S2` (adaptive bandwidth) vs `S3` (joint adaptive) vs `R0` (fixed BPSK 1 RB).
  - Gunakan pemilih **Strategi peta zona** di kanan atas peta untuk membandingkan cincin zona `S0` vs `S3` secara langsung (model radial hipotetis, bukan peta geografis), termasuk garis batas **radius andal 95% (SIMULATED)** vs **zona median PL (THEORETICAL)**.
  - Beralih ke strategi `MANUAL` di panel kiri untuk mengunci `N_RB` dan modulasi sendiri (lalu kembali ke `S3`).

## 4. Simulasi Monte Carlo Bit-Level Aktual
- Pilih kanal `AWGN` atau `Rayleigh (CSI sesaat)`, lalu klik **Jalankan Monte Carlo**.
- Tunjukkan bahwa nilai BER MC dan titik konstelasi I/Q berasal dari transmisi bit acak aktual di mesin Python (`src/metrics.py` dan `src/channels.py`), bukan titik sintetis statis.
- Gunakan tombol tampilan konstelasi **Dioptimalkan vs S0** dan **Antar Frekuensi** untuk membandingkan konstelasi yang diterima secara sisi-ke-sisi dengan seed identik.

## 5. Kontrol Suplemen Eksploratori di Panel Kiri (700 MHz & BER 1e-3)
- Gunakan langsung di panel kiri bila ingin meninjau sensitivitas:
  - Ubah **Target BER** dari `10⁻² (Primer)` ke `10⁻³ (Eksploratori)` untuk melihat ambang `Es/N0` dan kurva/tabel diperbarui dinamis oleh `src/modulation.py`.
  - Pilih **700* (supl.)** pada **Frekuensi pembawa (MHz)** sebagai frekuensi suplemen eksploratori yang terinspirasi Reddy (2022) di atas model CI Park (2023) (bukan replikasi Reddy); ketiga frekuensi tampil langsung di grafik/peta perbandingan.
- Kembalikan ke preset awal sebelum membahas hasil publikasi agar konfigurasi riset utama (`900/1800 MHz`, `BER 1e-2`) tetap jelas.

## 6. Temuan Penelitian Utama (Tab B. Hasil penelitian)
- Buka tab **B. Hasil penelitian (CSV & PNG)** untuk menampilkan kurva outage, laju efektif (outage = 0), serta tabel ringkasan dari `outputs/` (tidak berubah oleh opsi eksploratori):
  - **900 MHz NLOS, 2 km (shadowing + Rayleigh CSI):** `S0` outage `38.9%` (laju efektif `5.50 Mbit/s`), sedangkan `S3` menekan outage ke `5.7%` dengan laju efektif `11.97 Mbit/s` (`R0` juga `5.7%` tetapi hanya `0.17 Mbit/s`).
  - **1800 MHz NLOS, 2 km:** `S0` outage `57.8%` (`3.79 Mbit/s`), `S3` turun ke `12.0%` (`7.79 Mbit/s`).
  - **Batas radius:** `<1 km` menandakan outage pada titik uji pertama (1 km); `>=12 km` menandakan tersensor kanan oleh batas rentang evaluasi.

## 7. Rencana Cadangan Offline (Offline Fallback)
Jika koneksi internet atau Streamlit Cloud bermasalah saat presentasi:
1. Jalankan `.\run_local.ps1` di PowerShell (menggunakan `.venv` lokal, 100% offline).
2. Jika aplikasi web tidak dapat dibuka, gunakan grafik PNG di `outputs/figures/` dan ringkasan angka di `outputs/summary.md` serta `outputs/results/*.csv`.
