# Panduan Demo Presentasi RuralLink (Kelompok 1, 2026)

Dokumen ini memandu alur demo langsung menggunakan website statis resmi RuralLink karya Zahran ([public/index.html](../public/index.html) / [dashboard_rurallink.html](../dashboard_rurallink.html)).

> **Catatan penting untuk presenter:** Tab 1 (*Simulator Interaktif*) melakukan kalkulasi JavaScript analitis secara langsung di browser untuk visualisasi cepat, sedangkan seluruh angka publikasi resmi dan validasi Monte Carlo *bit-level* berasal dari mesin Python (`src/` + `experiments/`) yang dirangkum di Tab 2 (*Hasil Penelitian*) dan [outputs/summary.md](../outputs/summary.md).

## 1. Membuka Website untuk Presentasi
- **Secara lokal / offline (paling aman saat presentasi):** Buka langsung file `dashboard_rurallink.html` atau `public/index.html` di browser (double-click, tanpa Python maupun internet).
- **Via server statis lokal:** Jalankan `python -m http.server --directory public 8000` lalu buka `http://127.0.0.1:8000/`.
- **Legacy backup (opsional):** Rilis Streamlit lama tersedia di `https://rural-link.streamlit.app/` sebagai cadangan arsip.

## 2. Alur Demo 4 Tab (Saran Urutan Presentasi)
1. **Tab `Simulator Interaktif` — Perbandingan Frekuensi & Strategi:**
   - Pada kondisi default (`900 MHz`, `NLOS`, `S3: Joint Adaptive`, jarak `4,0 km`, daya `23 dBm`), tunjukkan 6 sel *telemetry strip* dan tabel perbandingan `700 / 900 / 1800 MHz` di panel kiri.
   - Beralih antara **900 MHz** dan **1800 MHz** pada kontrol *segmented* untuk menunjukkan keunggulan path loss 900 MHz (`6,02 dB` lebih rendah pada model CI).
   - Ubah skenario dari **S3 (Joint Adaptive)** ke **S0 (Baseline Fixed)** lalu kembali ke **S3** untuk menunjukkan bagaimana penyempitan `N_RB` dan adaptasi modulasi memperluas zona cakupan pada **Peta Zona Cakupan Radial 2D** dan **Uplink SNR vs Jarak**.
   - Aktifkan mode **Margin 95%** dan kanal **Rayleigh**, lalu geser jarak (`1,0–12,0 km`) untuk memperlihatkan batas ketahanan tautan di tepi sel. (Catat bahwa opsi `700 MHz` dan rentang daya `20–26 dBm` adalah fitur eksploratori HTML; riset utama fokus pada `900/1800 MHz` dengan batas UE `23 dBm`.)
   - Tunjukkan tombol **Unduh PNG** dan **Unduh CSV** bila diperlukan.
2. **Tab `Hasil Penelitian` — Bukti Eksperimen Python (`outputs/`):**
   - Tunjukkan tabel ringkasan radius cakupan (`S0–S3`, `R0`), perbandingan outage & laju efektif (`900 MHz NLOS 2 km`: `S0` outage `38,9%` vs `S3` `5,7%` dengan laju `11,97 Mbit/s`; `1800 MHz NLOS 2 km`: `S0` `57,8%` vs `S3` `12,0%`), serta validasi Monte Carlo *bit-level* (`1.000.000` bit).
   - Jelaskan arti `<1 km` (gagal di titik uji awal 1 km) dan `>=12 km` (tersensor kanan oleh batas evaluasi).
3. **Tab `Metodologi & Batasan`:**
   - Rujuk 5 persamaan inti (Close-In path loss, link budget uplink, thermal noise, $E_b/N_0$, laju nominal) serta 5 batasan penelitian (uncoded, tanpa kalibrasi lapangan Indonesia, peta radial hipotetis).
4. **Tab `Kamus & Persamaan (127)`:**
   - Perlihatkan fitur pencarian cepat istilah (mis. `Wilson`, `CSI`, `Close-In`, `PRB`) saat sesi tanya jawab.

## 3. Rencana Cadangan Materi Slide
Jika proyektor hanya memakai file statis/gambar, gunakan grafik resolusi publikasi di `outputs/figures/*.png` dan ringkasan angka di [outputs/summary.md](../outputs/summary.md).
