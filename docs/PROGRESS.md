# Progress

## Phase 01 — Environment setup: COMPLETE (2026-11-25)
**Done:** Python 3.12.14 (via uv) `.venv`; deps installed (numpy 2.5.5, scipy 1.18.1, pandas 3.1.1, matplotlib 3.11.2, plotly 7.2.0, streamlit 1.67.0, pytest 9.2.0, ruff 0.17.6; full list in `requirements.lock.txt`); repo structure; placeholder modules; docs; landing page.

**Verification:** imports OK; `uv pip check` compatible; pytest 9 passed; ruff check/format clean; Streamlit `/_stcore/health` and `/` returned HTTP 200, process stopped, port freed.

**Blockers resolved:**
- `.venv` has no pip (uv-managed); use `uv pip`.
- Pins in `requirements.lock.txt` are Windows-resolved; requirements.txt uses floors for Cloud.
- Streamlit Cloud will need Python 3.12 selected in app settings.

---

## Phase 02–03 — Mathematical Specification & Scientific Engine: COMPLETE (2026-11-25)

### Reference Verification
All reference PDFs in `references/` inspected and recorded in `docs/REFERENCES.md`.
- **Reddy (2022):** Verified — link budget (Eq. 1), PRB power per RB (Eq. 7), 95% shadow margin (1.645σ).
- **Khan (2025):** Verified with caveats — Eqs. (11)/(14) are SER not BER; not used directly (see D10).
- **Park (2023):** Verified — CI Eq. (3), LOS n=2.16/σ=3.07, NLOS n=2.56/σ=11.40 from Table II (1400 MHz).
- **Yogapratama (2015):** Partial — Table IV parameters extracted from figures-only PDF; authorship unverified.
- **Komdigi (2025):** Verified — 4G: 53.82% land area, 98.95% population (Q2 2025); 3T BTS: 6,747 on p. 108.

### Methodology
`docs/METHODOLOGY.md` locked with complete mathematical specification: propagation, link budget, energy normalization, Gray-coded modulations (exact Cho-Yoon BER), channel models, and statistical validation.

### Modules Implemented
| Module | Description |
|---|---|
| `config.py` | Typed `SimulationConfig` dataclass with units, defaults, and full validation |
| `src/propagation.py` | CI path loss (median, stochastic, 95% margin); Park (2023) LOS/NLOS params |
| `src/link_budget.py` | Received power, noise floor, SNR, RB gain, Eb/N0, nominal rate, Shannon capacity |
| `src/modulation.py` | Gray-coded BPSK/QPSK/16-QAM/64-QAM; exact Cho-Yoon BER; Rayleigh BER; thresholds |
| `src/channels.py` | AWGN; independent/block Rayleigh; coherent ZF equalization |
| `src/metrics.py` | Batched MC simulation; Wilson 95% CI; rule-of-three zero-error bound |
| `experiments/run_experiments.py` | Scientific smoke experiment entrypoint |

### Scientific Bug Fixed (Phase 03)
- **D12:** `numpy.uint8` dtype overflow in `_gray_pam_table` caused BPSK symbol levels of {255, 1} instead of {-1, +1}. Fixed by changing to `int64` dtype. All modulations failed roundtrip and BER validation until this fix.

### Test Results
- **pytest:** 77/77 PASSED (2.19 s), `tests/test_scientific_engine.py` + `tests/test_environment.py`
- **ruff check:** Clean (0 errors)
- **ruff format:** Clean (all files formatted)

### Experiment Outputs
| Artifact | Description |
|---|---|
| `outputs/figures/path_loss_vs_distance.png` | LOS/NLOS median and 95% margin for 900/1800 MHz — THEORETICAL |
| `outputs/figures/uplink_snr_vs_distance.png` | SNR vs distance for N_RB={1,5,25} at 900/1800 MHz — THEORETICAL |
| `outputs/figures/ber_awgn_validation.png` | Theory vs MC BER for all 4 modulations in AWGN — THEORETICAL + SIMULATED |
| `outputs/figures/ber_rayleigh_validation.png` | Theory vs MC BER for all 4 modulations in Rayleigh — THEORETICAL + SIMULATED |
| `outputs/results/link_budget_validation.csv` | SNR, noise floor, path loss vs distance and N_RB — THEORETICAL |
| `outputs/results/ber_validation.csv` | BER, CI bounds, error counts, theory vs MC — SIMULATED (Monte Carlo, bit-level) |
| `outputs/results/modulation_thresholds.csv` | Eb/N0 and Es/N0 switching thresholds at BER=1e-2 — THEORETICAL |

### Scientific Verification (Numerical)
| Check | Result |
|---|---|
| 900 vs 1800 MHz PL difference | **6.0206 dB** (20·log10(2)) ✓ |
| 25→1 RB SNR gain | **13.9794 dB** (10·log10(25)) ✓ |
| 25→5 RB SNR gain | **6.9897 dB** (10·log10(5)) ✓ |
| Noise floor N_RB=1 | **−117.447 dBm** ✓ |
| BPSK Eb/N0 threshold | **4.323 dB** (at BER=1e-2) ✓ |
| QPSK Eb/N0 threshold | **4.323 dB** (same as BPSK) ✓ |
| 16-QAM Eb/N0 threshold | **7.882 dB** ✓ |
| 64-QAM Eb/N0 threshold | **11.954 dB** ✓ |
| BPSK AWGN MC vs theory | **~0.3% relative error** at BER≈1.25e-2 ✓ |
| Rayleigh channel E[|h|^2] | **≈1.0** (empirical 200k samples) ✓ |
| Es=1 for all constellations | **1.000000** (all 4) ✓ |

**Next:** Phase 04 (adaptive modulation-bandwidth optimizer) — awaiting authorization.

### Recovery & Independent Audit (2026-11-25)
- Independent scientific audit (`code-reviewer`) verified all 12 core areas (Gray mapping, `E_s=1`, AWGN `N_0/2` normalization, `E_s/N_0` vs `E_b/N_0` distinction, Rayleigh `E[|h|^2]=1` & ZF equalization, exact Cho–Yoon QAM BER, `BER=1e-2` thresholds, no double-counted shadowing/RB gain, Wilson/rule-of-three CIs, seeded RNG) with 0 confirmed defects.
- Final verification: `pytest` 77/77 passed, `ruff check` & `ruff format --check` clean, `experiments.run_experiments` completed (5.3 s), Streamlit `/_stcore/health` HTTP 200.
