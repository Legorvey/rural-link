# Serah Terima Tim (Team Handoff) — RuralLink

Dokumen ini menjadi rujukan tunggal bagi **Tim PPT** (2 anggota, *pending konfirmasi*) dan **Tim Analisis & Laporan** (2 anggota, *pending konfirmasi*).

## 1. Identitas & Konteks Resmi
- **Tema:** *Keandalan dan Perluasan Jangkauan Sistem Komunikasi Digital pada Wilayah Terdepan, Terluar, dan Tertinggal (3T) Indonesia dengan Keterbatasan Daya Uplink.*
- **Judul:** *Analisis Peningkatan Jangkauan Uplink melalui Modulasi Adaptif dan Alokasi Bandwidth pada Frekuensi 900 MHz dan 1800 MHz di Wilayah 3T Indonesia.*
- **Jadwal Presentasi:** 26 November 2026, 15.00 WIB | **Dosen:** Bu Dessy.

## 2. Ringkasan Bahan Baku (Dari Sumber Terverifikasi)
- **Masalah:** Cakupan 4G Indonesia Q2 2025 mencapai `98,95%` populasi tetapi hanya `53,82%` luas daratan (Komdigi 2025, hal. 104–105). Pada sel 3T yang luas, daya UE (`23 dBm`) jauh lebih kecil dari BTS (`43 dBm`), menyebabkan *uplink* lebih cepat gagal.
- **Literatur Utama:** Reddy et al. (2022) (konsentrasi daya PRB), Khan et al. (2025) (target $\text{BER} = 10^{-2}$), Park et al. (2023) (model CI LOS $n=2{,}16, \sigma=3{,}07$; NLOS $n=2{,}56, \sigma=11{,}40$), Yogapratama et al. (2015) (parameter RF Tabel IV). Detail lengkap: [docs/REFERENCES.md](REFERENCES.md).
- **Persamaan & Parameter Kanonik:** Lihat [docs/METHODOLOGY.md](METHODOLOGY.md) dan `config.py`.
- **Inventaris Hasil Terverifikasi (Fase 02–03):**
  - Grafik: `outputs/figures/path_loss_vs_distance.png`, `uplink_snr_vs_distance.png`, `ber_awgn_validation.png`, `ber_rayleigh_validation.png`.
  - CSV: `outputs/results/link_budget_validation.csv`, `ber_validation.csv`, `modulation_thresholds.csv`.
- **Dependensi Belum Selesai:** Eksperimen komparatif S0–S3 (Fase 04) dan dashboard interaktif penuh (Fase 05) masih *pending*.

## 3. Tabel *Claim-to-Evidence* (Wajib Dipatuhi di PPT & Laporan)

| Klaim | Sumber / Output | Status | Rekomendasi Kalimat | Larangan Over-interpretasi |
|---|---|---|---|---|
| Cakupan 4G daratan `53,82%` vs populasi `98,95%` | Komdigi (2025), hal. 104–105 | **VERIFIED SOURCE** | "Data Komdigi Q2 2025 mencatat cakupan 4G 98,95% populasi dan 53,82% luas daratan." | Jangan sebut 46,18% penduduk tidak punya sinyal. |
| 1800 MHz punya *path loss* `6,0206 dB` lebih tinggi dari 900 MHz | `link_budget_validation.csv` | **THEORETICAL** | "Secara teoretis pada model CI, penggandaan frekuensi menambah *path loss* 6,02 dB." | Jangan klaim sebagai hasil ukur lapangan Indonesia. |
| Pengurangan `25 → 1 RB` menaikkan SNR `13,9794 dB` | `link_budget_validation.csv` | **THEORETICAL** | "Pada model daya UE tetap, pengurangan 25 ke 1 RB meningkatkan SNR sebesar 13,98 dB." | Jangan klaim terjadi di semua skenario *power control* nyata. |
| Ambang batas AWGN $\text{BER}=10^{-2}$: BPSK `4,32`, QPSK `7,33`, 16-QAM `13,90`, 64-QAM `19,74` dB ($E_s/N_0$) | `modulation_thresholds.csv` | **THEORETICAL** | "Berdasarkan kurva BER eksak AWGN, ambang SNR ($E_s/N_0$) untuk BER 1% berkisar 4,32–19,74 dB." | Jangan tertukar antara $E_b/N_0$ dan $E_s/N_0$. |
| Simulasi MC BPSK AWGN cocok dengan teori (~0,3% error di BER ≈ 1,25e-2) | `ber_validation.csv` | **SIMULATED** | "Simulasi Monte Carlo *bit-level* tervalidasi cocok dengan kurva teoretis eksak." | Jangan klaim throughput LTE nyata. |

## 4. Urutan Slide PPT yang Disarankan
1. **Judul & Tema Resmi** (Identitas Kelompok 1)
2. **Masalah & Motivasi** (Data Komdigi 2025 & ketimpangan *uplink–downlink*)
3. **Referensi Utama & Pendukung** (Reddy 2022, Khan 2025, Park 2023, Yogapratama 2015)
4. **Tujuan Penelitian** (5 tujuan terukur)
5. **Metodologi & Formulasi Matematis** (CI path loss, Link budget, BER Cho–Yoon)
6. **Arsitektur Simulasi** (Diagram alir `src/`)
7. **Skenario Eksperimen** (Rencana S0–S3)
8. **Hasil Tervalidasi Saat Ini** (4 grafik Fase 02–03)
9. **Analisis & Diskusi** (*Trade-off* SNR vs laju nominal, AWGN vs Rayleigh)
10. **Keterbatasan Penelitian** (Tanpa kalibrasi lapangan, tanpa FEC/interferensi)
11. **Kesimpulan Sementara & Status**
12. **Demo Singkat / Rencana Demo**
13. **Kontribusi Tim & Daftar Pustaka**
