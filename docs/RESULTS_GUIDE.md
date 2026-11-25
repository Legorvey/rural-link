# Panduan Membaca Hasil Simulasi — RuralLink

Dokumen ini menjelaskan cara membaca seluruh grafik dan file CSV yang saat ini tersedia di `outputs/` (hasil Fase 02–03).

## 1. Katalog Output Tersedia

| File | Jenis & Label | Pertanyaan yang Dijawab |
|---|---|---|
| `outputs/figures/path_loss_vs_distance.png` | Grafik PNG (**THEORETICAL**) | Bagaimana *path loss* CI meningkat terhadap jarak (1–12 km) pada 900 vs 1800 MHz (LOS & NLOS)? |
| `outputs/figures/uplink_snr_vs_distance.png` | Grafik PNG (**THEORETICAL**) | Bagaimana SNR *uplink* berubah terhadap jarak dan jumlah RB ($N_{\text{RB}} \in \{1, 5, 25\}$)? |
| `outputs/figures/ber_awgn_validation.png` | Grafik PNG (**THEORETICAL + SIMULATED**) | Apakah simulasi Monte Carlo *bit-level* cocok dengan kurva BER eksak AWGN? |
| `outputs/figures/ber_rayleigh_validation.png` | Grafik PNG (**THEORETICAL + SIMULATED**) | Seberapa jauh penurunan performa BER pada kanal Rayleigh fading dibanding AWGN? |
| `outputs/results/link_budget_validation.csv` | CSV (**THEORETICAL**) | Nilai numerik `freq_mhz, n_rb, distance_km, path_loss_db, noise_dbm, snr_db, nominal_rate_mbps, data_label`. |
| `outputs/results/ber_validation.csv` | CSV (**SIMULATED**) | Nilai numerik `channel, modulation, ebn0_db, ebn0_linear, n_bits, n_errors, ber_simulated, ci_lower, ci_upper, zero_errors_upper_bound, ber_theoretical, data_label`. |
| `outputs/results/modulation_thresholds.csv` | CSV (**THEORETICAL**) | Ambang batas `ebn0_db_threshold` dan `esn0_db_threshold` pada `ber_target = 0.01`. |

## 2. Cara Membaca & Jebakan Interpretasi

- **Sumbu Logaritmik BER:** Sumbu-Y pada grafik BER menggunakan skala logaritmik ($10^{-5}$ hingga $10^{0}$). Garis putus-putus/kontinu adalah **kurva teoretis**, sedangkan titik penanda (*marker*) adalah **hasil simulasi Monte Carlo**.
- **Interval Kepercayaan & Nol Kesalahan (`zero_errors_upper_bound`):**
  - Setiap titik simulasi dilengkapi interval kepercayaan Wilson 95% (`ci_lower`, `ci_upper`).
  - Jika `n_errors = 0`, itu **tidak** membuktikan BER sebenarnya adalah nol. Simulator menggunakan batas atas *rule-of-three* ($3/N_{\text{bits}}$) sebagai estimasi konservatif.
  - Pada kanal Rayleigh (*block fading*), kesalahan bit dapat berkorelasi sehingga asumsi independensi pada CI standar perlu dicermati.
- **Perbedaan $E_b/N_0$ dan $E_s/N_0$ (SNR):**
  - Pada grafik BER terhadap $E_b/N_0$, kurva `BPSK` dan `QPSK` **berimpit** karena keduanya memiliki efisiensi energi per bit yang sama.
  - Namun, ambang batas $E_s/N_0$ (yang menentukan kebutuhan SNR kanal) **berbeda**: QPSK butuh `7,33 dB` sedangkan BPSK butuh `4,32 dB` (selisih `3,01 dB` karena 2 bit/simbol).
- **Laju Data Nominal (`nominal_rate_mbps`):** Dihitung sebagai $B_{\text{active}} \cdot k$. Ini adalah batas laju simbol ideal tanpa *overhead* protokol LTE, *cyclic prefix*, maupun *channel coding*.
- **Status Fase 04:** Output untuk *outage probability*, *reliable coverage radius*, dan perbandingan skenario S0–S3 belum tersedia karena Fase 04 masih *pending*.
