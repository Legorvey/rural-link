# Panduan Membaca Hasil Simulasi — RuralLink

Dokumen ini menjelaskan cara membaca seluruh grafik dan file CSV yang tersedia di `outputs/` (hasil eksperimen Python Fase 02–06; lihat juga ringkasan lengkap di [outputs/summary.md](../outputs/summary.md)).

## 1. Katalog Output Tersedia

| File | Jenis & Label | Pertanyaan yang Dijawab |
|---|---|---|
| `outputs/summary.md` | Ringkasan Markdown (**THEORETICAL + SIMULATED**) | Tabel terpadu radius cakupan (`S0–S3`, `R0`), outage, laju efektif, dan validasi MC. |
| `outputs/figures/path_loss_vs_distance.png` | Grafik PNG (**THEORETICAL**) | Bagaimana *path loss* CI meningkat terhadap jarak (1–12 km) pada 900 vs 1800 MHz (LOS & NLOS)? |
| `outputs/figures/uplink_snr_vs_distance.png` | Grafik PNG (**THEORETICAL**) | Bagaimana SNR *uplink* berubah terhadap jarak dan jumlah RB ($N_{\text{RB}} \in \{1, 5, 25\}$)? |
| `outputs/figures/ber_awgn_validation.png` | Grafik PNG (**THEORETICAL + SIMULATED**) | Apakah simulasi Monte Carlo *bit-level* cocok dengan kurva BER eksak AWGN? |
| `outputs/figures/ber_rayleigh_validation.png` | Grafik PNG (**THEORETICAL + SIMULATED**) | Seberapa jauh penurunan performa BER pada kanal Rayleigh fading dibanding AWGN? |
| `outputs/figures/adaptive_coverage_radius.png` | Grafik PNG (**THEORETICAL + SIMULATED**) | Perbandingan radius cakupan (`Median PL`, `Shadowing`, `Shadowing + Rayleigh CSI`) antar strategi `S0–S3` & `R0`. |
| `outputs/figures/adaptive_rate_vs_distance.png` | Grafik PNG (**SIMULATED**) | Laju nominal efektif (dengan outage = 0) terhadap jarak `1–12 km` untuk `S0–S3` & `R0`. |
| `outputs/results/link_budget_validation.csv` | CSV (**THEORETICAL**) | Nilai numerik `freq_mhz, n_rb, distance_km, path_loss_db, noise_dbm, snr_db, nominal_rate_mbps, data_label`. |
| `outputs/results/ber_validation.csv` | CSV (**SIMULATED**) | Nilai numerik `channel, modulation, ebn0_db, ebn0_linear, n_bits, n_errors, ber_simulated, ci_lower, ci_upper, zero_errors_upper_bound, ber_theoretical, data_label`. |
| `outputs/results/modulation_thresholds.csv` | CSV (**THEORETICAL**) | Ambang batas `ebn0_db_threshold` dan `esn0_db_threshold` pada `ber_target = 0.01`. |
| `outputs/results/adaptive_coverage_curves.csv` | CSV (**THEORETICAL + SIMULATED**) | Kurva jarak `1–12 km` (step `0,25 km`) untuk seluruh skenario `S0–S3` & `R0`. |
| `outputs/results/adaptive_coverage_summary.csv` | CSV (**THEORETICAL + SIMULATED**) | Ringkasan radius median, margin 95%, shadowing MC, dan shadowing + Rayleigh CSI. |
| `outputs/results/adaptive_strategy_comparison.csv` | CSV (**SIMULATED**) | Perbandingan outage, laju efektif, dan mean conditional BER pada jarak perwakilan `2, 5, 8, 12 km`. |
| `outputs/results/adaptive_mc_validation.csv` | CSV (**THEORETICAL + SIMULATED**) | Validasi Monte Carlo `1.000.000` bit pada titik operasi terpilih `S3` (AWGN vs Rayleigh no-CSI). |

## 2. Cara Membaca & Jebakan Interpretasi

- **Sumbu Logaritmik BER:** Sumbu-Y pada grafik BER menggunakan skala logaritmik ($10^{-5}$ hingga $10^{0}$). Garis putus-putus/kontinu adalah **kurva teoretis**, sedangkan titik penanda (*marker*) adalah **hasil simulasi Monte Carlo**.
- **Interval Kepercayaan & Nol Kesalahan (`zero_errors_upper_bound`):**
  - Setiap titik simulasi dilengkapi interval kepercayaan Wilson 95% (`ci_lower`, `ci_upper`).
  - Jika `n_errors = 0`, itu **tidak** membuktikan BER sebenarnya adalah nol. Simulator menggunakan batas atas *rule-of-three* ($3/N_{\text{bits}}$) sebagai estimasi konservatif.
  - Pada kanal Rayleigh (*block fading*), kesalahan bit dapat berkorelasi sehingga asumsi independensi pada CI standar perlu dicermati.
- **Perbedaan $E_b/N_0$ dan $E_s/N_0$ (SNR):**
  - Pada grafik BER terhadap $E_b/N_0$, kurva `BPSK` dan `QPSK` **berimpit** karena keduanya memiliki efisiensi energi per bit yang sama.
  - Namun, ambang batas $E_s/N_0$ (yang menentukan kebutuhan SNR kanal) **berbeda**: QPSK butuh `7,33 dB` sedangkan BPSK butuh `4,32 dB` (selisih `3,01 dB` karena 2 bit/simbol).
- **Laju Data Nominal (`nominal_rate_mbps` / efektif):** Dihitung sebagai $B_{\text{active}} \cdot k$ (dengan realisasi *outage* dihitung `0` pada laju efektif). Ini bukan *throughput* aktual LTE yang menyertakan *overhead* dan FEC.
- **Sensor Radius (`<1 km` dan `>=12 km`):** `<1 km` menandakan outage sudah melewati 5% pada jarak uji pertama `1 km`; `>=12 km` berarti tersensor kanan oleh batas akhir grid uji `12 km`.
- **BER Bersyarat CSI vs BER Rata-rata Rayleigh tanpa CSI:** Adaptasi CSI sesaat hanya mentransmisikan data saat SNR sesaat memenuhi ambang AWGN (`conditional BER <= 1e-2`), sedangkan angka 4–7% di `adaptive_mc_validation.csv` adalah BER rata-rata Rayleigh **tanpa** CSI sesaat.
