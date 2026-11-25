# References

All local reference PDFs in `references/` (gitignored per Decision D5) were inspected in Phase 02. Bibliographic details, extracted equations/tables, intended applications, and verified limitations are recorded below.

## Summary Inventory

| Ref Key | Citation / Source | Local PDF | Verification Status |
|---|---|---|---|
| Reddy2022 | M. P. Reddy, G. K. Rao, D. H. Kumar, K. Subhash, S. Amuru, & K. Kuchi, "Uplink coverage enhancements for extremely large-cell sites," *EURASIP Journal on Wireless Communications and Networking*, 2022:57, pp. 1–29, 2022. DOI: `10.1186/s13638-022-02133-3` | `Jurnal2_Reddy2022_EURASIP_JWCN_Rural_LargeCell_Coverage.pdf` | Verified |
| Khan2025 | R. Khan, Z. U. Khan, S. Taj, S. U. Khan, J. Khan, N. Alturki, & S. Alanazi, "Optimizing adaptive modulation technique using standard propagation model for enhanced wireless communication channels," *Scientific Reports*, 15:30796, pp. 1–22, 2025. DOI: `10.1038/s41598-025-16743-6` | `Jurnal1_Khan2025_ScientificReports_AdaptiveModulation_PathLoss.pdf` | Verified (with equation caveats) |
| Park2023 | J. Park, H.-B. Jeon, J. Cho, & C.-B. Chae, "Measurement-based Close-in Path Loss Modeling with Diffraction for Rural Long-distance Communications," *IEEE Wireless Communications Letters* (arXiv preprint `arXiv:2305.01152v1`, 2 May 2023) | `Jurnal3_Park2023_IEEE_WCL_Rural_CloseIn_PathLoss.pdf` | Verified (preprint; DOI not in PDF) |
| Yogapratama2015 | *Analysis on 900 MHz and 1800 MHz LTE network planning in rural area* (attributed in brief to Yogapratama et al., 2015) | `Analysis on 900 MHz and 1800 MHz LTE network planning in rural area (Figures Only).pdf` | Partial (Figures & Tables only; author/year unverified from PDF) |
| Komdigi2025 | Kementerian Komunikasi dan Digital Republik Indonesia (KOMDIGI), *Laporan Kinerja 2025*, Jakarta (issued 2026) | `Laporan Kinerja KOMIDIG 2025.pdf` | Verified |

---

## Detailed Extraction & Application

### 1. Reddy et al. (2022) — Primary Reference
- **Source & Location:** `Jurnal2_Reddy2022_EURASIP_JWCN_Rural_LargeCell_Coverage.pdf`, pp. 1–29.
- **Extracted Equations & Parameters:**
  - **Table 1 (p. 5):** Rural macro large-cell parameters ($P_{\text{tUE}} = 23\text{ dBm}$, $N_0 = -174\text{ dBm/Hz}$, 1 RB = 180 kHz, 15 kHz SCS).
  - **Eq. (1) (p. 6):** Uplink SNR link budget in dB scale and 95% CDF shadow fading margin ($1.645 \times \sigma$).
  - **Eq. (7) (p. 16):** Power per RB under fixed total UE transmit power: $P_{\text{RB}} = P_{\text{tx}} - 10\log_{10}(N_{\text{RB}})$.
  - **Sec. 5.3 / Table 11 (pp. 23, 27):** PRB reduction (8 RBs $\to$ 1 RB) concentrates power per RB (+9 dB) to extend uplink cell radius.
- **Intended Application in RuralLink:** Inspires the power-limited uplink model ($P_{\text{tx}} = 23\text{ dBm}$ fixed across active RBs $N_{\text{RB}} \in \{1, 2, 5, 10, 25\}$ of 180 kHz each) and the analytical 95% shadow margin ($1.645\sigma$).
- **Limitations:** Reddy et al. evaluate 700 MHz RMa-LMLC with multi-antenna BS ($N_{\text{BS}} = 16$), TDD $\pi/2$-BPSK power boosting, and 3GPP HARQ/BLER-0.1 CQI tables. RuralLink simplifies this to an uncoded single-antenna link-level model at 900/1800 MHz without TDD power boosting or HARQ.

### 2. Khan et al. (2025) — Supporting Reference (Adaptive Modulation)
- **Source & Location:** `Jurnal1_Khan2025_ScientificReports_AdaptiveModulation_PathLoss.pdf`, pp. 1–22.
- **Extracted Equations & Parameters:**
  - **Eq. (10) (p. 7):** BPSK/QPSK BER in AWGN: $P_b = Q(\sqrt{2 E_b / N_0})$.
  - **Algorithm 1 (p. 9) & Table 9 (p. 18):** Threshold-based adaptive modulation switching among BPSK, QPSK, 16-QAM, and 64-QAM at target $\text{BER} = 10^{-2}$.
- **Intended Application in RuralLink:** Supports threshold-based adaptive modulation among `{BPSK, QPSK, 16-QAM, 64-QAM}` targeting $\text{BER} \le 10^{-2}$.
- **Limitations & Equation Caveats (Not Copied Blindly):**
  - Khan et al. model a **downlink** ($P_t = 43\text{ dBm}$ at 2 GHz) with co-channel interference and a calibrated Standard Propagation Model (SPM), without bandwidth/PRB allocation.
  - **Eqs. (11) and (14) (p. 7)** in Khan et al. omit the $1/\log_2 M$ Gray-coding BER factor (giving SER rather than BER), and **Eq. (12)** uses the real-channel $1/2$ capacity prefactor. RuralLink does **not** copy those expressions; instead, RuralLink uses standard Gray-coded BER expressions (exact Cho–Yoon 2002 and standard approximation) and complex baseband capacity $B\log_2(1+\text{SNR})$.

### 3. Park et al. (2023) — Supporting Reference (Propagation)
- **Source & Location:** `Jurnal3_Park2023_IEEE_WCL_Rural_CloseIn_PathLoss.pdf`, pp. 1–5.
- **Extracted Equations & Parameters:**
  - **Eq. (3) (p. 2):** Close-In (CI) path loss with $d_0 = 1\text{ m}$ and $f_c$ in GHz:
    $$\mathrm{PL}^{\mathrm{CI}}(f_c, d)\text{ [dB]} = 32.4 + 20\log_{10}(f_c) + 10 n_{\mathrm{CI}} \log_{10}(d) + \chi_\sigma, \quad \chi_\sigma \sim \mathcal{N}(0, \sigma^2)$$
  - **Eqs. (7)–(8) (p. 3) & Table II (p. 4), 1400 MHz measurements:**
    - Standard CI LOS: $n = 2.16$, $\sigma = 3.07\text{ dB}$.
    - Standard CI NLOS: $n = 2.56$, $\sigma = 11.40\text{ dB}$.
- **Intended Application in RuralLink:** Provides the CI path loss equation and LOS/NLOS parameters $(n, \sigma)$ from the 1400 MHz dataset, extrapolated to 900 MHz and 1800 MHz for comparative simulation.
- **Limitations:** Measured in rural South Korea (agricultural land and low hills, spring, Tx 15 m / Rx 2 m AGL) at 1400 MHz and 2250 MHz—not calibrated for Indonesian 3T terrain or tropical foliage. RuralLink does **not** use the diffraction-adjusted exponent (Eq. 4, Table II) because terrain elevation profiles for diffraction loss $\phi$ are unavailable.

### 4. Yogapratama et al. (2015) — Supporting Reference (Rural LTE Parameters)
- **Source & Location:** `Analysis on 900 MHz and 1800 MHz LTE network planning in rural area (Figures Only).pdf`, p. 9 (`TABLE IV. COVERAGE PLANNING PARAMETERS`).
- **Extracted Parameters (Uplink Budget, Table IV, p. 9):**
  - Bandwidth: `5 MHz`
  - UE Tx Power: `23 dBm`
  - UE Body Loss: `3 dB`
  - UE Antenna Gain: `0 dBi`
  - eNB (BTS) Rx Antenna Gain: `11 dBi`
  - eNB (BTS) Feeder Loss: `5 dB`
  - eNB (BTS) Noise Figure: `4 dB`
- **Intended Application in RuralLink:** Supplies the default RF link-budget hardware/loss parameters and 5 MHz nominal channel bandwidth.
- **Limitations:** The local PDF contains **figures and tables only** (no full text, author list, venue, or publication year). Attribution to "Yogapratama et al. (2015)" is carried from the project brief and remains unverified against the full paper.

### 5. Kementerian Komdigi Performance Report (2025) — National Context
- **Source & Location:** `Laporan Kinerja KOMIDIG 2025.pdf`, pp. 104–105 (Sec. 3.1.1, Gambar 3.2 & 3.3) and p. 108 (Sec. 7, Gambar 3.6).
- **Extracted Statistics:**
  - **pp. 104–105 (Q2 2025 4G Coverage):** `53.82%` of Indonesian land area (`1,022,161.15 km²`), `98.95%` of population (`267,211,024` of `270,051,626` residents), and `99.23%` of settlement area (`50,651.17 km²`).
  - **p. 108 (3T BTS Deployment through 2025):** `6,747` BTS locations operating in 3T regions (`3,262` in Papua); status breakdown: `5,514` BTS 4G On Air, `1,233` BTS USO On Air, `449` BTS USO Terminasi. (Note: 3T-specific BTS counts appear on p. 108, whereas pp. 104–105 report national 4G/5G coverage.)
- **Intended Application in RuralLink:** Motivates the gap between population coverage (98.95%) and geographic area coverage (53.82%) in Indonesia's 3T regions.
- **Limitations:** Macro-level deployment statistics only; does not provide RF propagation measurements or link-level parameters.
