# Project Context

**Title:** Analisis Peningkatan Jangkauan Uplink melalui Modulasi Adaptif dan Alokasi Bandwidth pada Frekuensi 900 MHz dan 1800 MHz di Wilayah 3T Indonesia.

**Team:** Group 1 — Digital Communication Systems (undergraduate engineering research).

## Problem statement
Uplink coverage in large rural cells is power-limited (UE transmit power far below base-station power). Limited coverage in Indonesia's 3T (tertinggal, terdepan, terluar) regions motivates studying how modulation order and bandwidth can be adapted jointly to extend usable uplink range.

## Objectives
Build a scientifically valid, reproducible, interactive simulator for uplink coverage and joint adaptive modulation-bandwidth allocation under power constraints, using bit-level Monte Carlo simulation.

## References and intended roles
| Reference | Role |
|---|---|
| Reddy et al. (2022), DOI 10.1186/s13638-022-02133-3 | Primary: uplink coverage enhancement for extremely large cells |
| Khan et al. (2025), DOI 10.1038/s41598-025-16743-6 | Supporting (role to be verified) |
| Park et al. (2023), DOI 10.1109/LWC.2023.3273280 | Supporting (role to be verified) |
| Yogapratama et al. (2015) | Rural LTE planning at 900/1800 MHz |
| Kementerian Komdigi, Performance Report 2025 | Indonesian context |

## Final deliverables
1. Scientific simulation engine (`src/`). 2. Bit-level Monte Carlo validation. 3. Adaptive modulation + bandwidth optimization (`S0–S3`, `R0`). 4. Static interactive HTML website (`dashboard_rurallink.html` / `public/index.html`, with legacy Streamlit release archived in Git). 5. Reproducible experiments (`experiments/`). 6. Publication-quality figures and CSVs (`outputs/`). 7. Automated scientific tests (`tests/`). 8. Static Vercel deployment + direct offline HTML usage.

## Known limitations
- Propagation parameters are extrapolated from Park et al. (2023) 1400 MHz South Korea measurements without Indonesian 3T field calibration.
- Uncoded link-level model without FEC, HARQ, inter-cell interference, or multi-user scheduling; radii reaching 12 km are right-censored (`>=12 km`).
- Reference PDFs in `references/` are gitignored; verified facts are recorded in `docs/REFERENCES.md`.

## Current scope
Scientific engine (Phases 01–06), reproducible outputs, and Zahran's frozen static HTML website are complete and integrated.