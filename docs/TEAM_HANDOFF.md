# Serah Terima Tim (Team Handoff) — RuralLink

Dokumen ini menjadi rujukan tunggal bagi **Tim PPT (Yusril & Rizqul)** dan **Tim Analisis & Laporan (Baihaqy & Jeyd)**, dengan dukungan implementasi oleh **Tim Program (Aditya & Zahran)**.

## 1. Identitas & Konteks Resmi
- **Tema:** *Keandalan dan Perluasan Jangkauan Sistem Komunikasi Digital pada Wilayah Terdepan, Terluar, dan Tertinggal (3T) Indonesia dengan Keterbatasan Daya Uplink.*
- **Judul:** *Analisis Peningkatan Jangkauan Uplink melalui Modulasi Adaptif dan Alokasi Bandwidth pada Frekuensi 900 MHz dan 1800 MHz di Wilayah 3T Indonesia.*
- **Jadwal Presentasi:** 26 November 2026, 15.00 WIB | **Dosen Pengampu:** Bu Dessy.

## 2. Ringkasan Bahan Baku (Dari Sumber Terverifikasi)
- **Masalah:** Cakupan 4G Indonesia Q2 2025 mencapai `98,95%` populasi tetapi hanya `53,82%` luas daratan (Komdigi 2025, hal. 104–105; `6.747` lokasi BTS 3T di hal. 108). Pada sel 3T yang luas, daya UE (`23 dBm`) jauh lebih kecil dari BTS, menyebabkan *uplink* lebih cepat gagal.
- **Literatur Utama:** Reddy et al. (2022) (konsentrasi daya PRB), Khan et al. (2025) (target $\text{BER} = 10^{-2}$), Park et al. (2023) (model CI LOS $n=2{,}16, \sigma=3{,}07$; NLOS $n=2{,}56, \sigma=11{,}40$), Yogapratama et al. (2015) (parameter RF Tabel IV), Cho & Yoon (2002) (BER QAM Gray-coded eksak). Detail lengkap: [docs/REFERENCES.md](REFERENCES.md).
- **Persamaan & Parameter Kanonik:** Lihat [docs/METHODOLOGY.md](METHODOLOGY.md) dan `config.py`.
- **Inventaris Hasil Terverifikasi (Fase 02–06):**
  - Ringkasan terpadu: [outputs/summary.md](../outputs/summary.md)
  - Grafik (6 PNG): `path_loss_vs_distance.png`, `uplink_snr_vs_distance.png`, `ber_awgn_validation.png`, `ber_rayleigh_validation.png`, `adaptive_coverage_radius.png`, `adaptive_rate_vs_distance.png`
  - Dataset CSV (7 CSV): `link_budget_validation.csv`, `ber_validation.csv`, `modulation_thresholds.csv`, `adaptive_coverage_curves.csv`, `adaptive_coverage_summary.csv`, `adaptive_strategy_comparison.csv`, `adaptive_mc_validation.csv`
- **Website Presentasi:** Website statis kanonik karya Zahran di `public/index.html` / `dashboard_rurallink.html` (4 tab, berjalan langsung offline).

## 3. Tabel *Claim-to-Evidence* (Wajib Dipatuhi di PPT & Laporan)

| Klaim | Sumber / Output | Status | Rekomendasi Kalimat | Larangan Over-interpretasi |
|---|---|---|---|---|
| Cakupan 4G daratan `53,82%` vs populasi `98,95%` | Komdigi (2025), hal. 104–105 | **VERIFIED SOURCE** | "Data Komdigi Q2 2025 mencatat cakupan 4G 98,95% populasi dan 53,82% luas daratan." | Jangan sebut 46,18% penduduk tidak punya sinyal. |
| 1800 MHz punya *path loss* `6,0206 dB` lebih tinggi dari 900 MHz | `link_budget_validation.csv` | **THEORETICAL** | "Secara teoretis pada model CI, penggandaan frekuensi menambah *path loss* 6,02 dB." | Jangan klaim sebagai hasil ukur lapangan Indonesia. |
| Pengurangan `25 → 1 RB` menaikkan SNR `13,9794 dB` | `link_budget_validation.csv` | **THEORETICAL** | "Pada model daya UE tetap, pengurangan 25 ke 1 RB meningkatkan SNR sebesar 13,98 dB." | Jangan klaim terjadi di semua skenario *power control* nyata. |
| Ambang batas AWGN $\text{BER}=10^{-2}$: BPSK `4,32`, QPSK `7,33`, 16-QAM `13,90`, 64-QAM `19,74` dB ($E_s/N_0$) | `modulation_thresholds.csv` | **THEORETICAL** | "Berdasarkan kurva BER eksak AWGN, ambang SNR ($E_s/N_0$) untuk BER 1% berkisar 4,32–19,74 dB." | Jangan tertukar antara $E_b/N_0$ dan $E_s/N_0$. |
| Simulasi MC BPSK AWGN cocok dengan teori (~0,3% error di BER ≈ 1,25e-2) | `ber_validation.csv` | **SIMULATED** | "Simulasi Monte Carlo *bit-level* tervalidasi cocok dengan kurva teoretis eksak." | Jangan klaim throughput LTE nyata. |
| Radius andal 95% (+Rayleigh CSI) 1800 MHz LOS: `S0` `1,75 km` vs `S3` `11,25 km` | `adaptive_coverage_summary.csv` | **SIMULATED** | "Pada 1800 MHz LOS dengan shadowing + Rayleigh CSI, optimasi gabungan S3 memperluas radius andal dari 1,75 km (S0) menjadi 11,25 km." | Jangan samakan radius median PL dengan radius andal 95%. |
| Tepi sel 900 MHz NLOS `2 km`: `S0` outage `38,9%` (`5,50 Mbit/s`) vs `S3` `5,7%` (`11,97 Mbit/s`) vs `R0` `5,7%` (`0,17 Mbit/s`) | `adaptive_strategy_comparison.csv` | **SIMULATED** | "Di 900 MHz NLOS 2 km, S3 menyamai keandalan R0 (5,7% outage) sambil menjaga laju efektif nominal 11,97 Mbit/s." | Jangan sebut laju nominal sebagai *throughput* jaringan LTE aktual. |

## 4. Urutan Slide PPT yang Disarankan
1. **Judul & Tema Resmi** (Identitas Kelompok 1)
2. **Masalah & Motivasi** (Data Komdigi 2025 & ketimpangan *uplink–downlink*)
3. **Referensi Utama & Pendukung** (Reddy 2022, Khan 2025, Park 2023, Yogapratama 2015, Cho & Yoon 2002)
4. **Tujuan Penelitian** (Perbandingan S0–S3 & R0 pada 900/1800 MHz)
5. **Metodologi & Formulasi Matematis** (CI path loss, Link budget, BER Cho–Yoon, optimasi adaptif)
6. **Arsitektur Sistem** (Website statis Zahran vs mesin riset offline Python)
7. **Skenario Eksperimen** (S0, S1, S2, S3, R0; seed 42, 5.000 realisasi)
8. **Hasil Tervalidasi** (Kurva SNR, validasi MC AWGN/Rayleigh, radius cakupan & laju efektif)
9. **Analisis & Diskusi** (*Trade-off* SNR vs laju nominal, AWGN vs Rayleigh CSI, 900 vs 1800 MHz)
10. **Keterbatasan Penelitian** (Tanpa kalibrasi lapangan, tanpa FEC/interferensi, batas 23 dBm & sensor `>=12 km`)
11. **Kesimpulan** (Keunggulan gabungan `S3`)
12. **Demo Singkat Website Statis** (`dashboard_rurallink.html` / `public/index.html`)
13. **Kontribusi Tim & Daftar Pustaka**
