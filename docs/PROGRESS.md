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


---

## Documentation & Team Knowledge Hub: COMPLETE (2026-11-25)
- **Done:** Transformed repository into a structured research hub for the 6-person team:
  - Rewrote `README.md` as the main Indonesian/English research hub.
  - Created `docs/START_HERE.md`, `docs/RESEARCH_OVERVIEW.md`, `docs/ARCHITECTURE.md`, `docs/DEVELOPER_GUIDE.md`, `docs/RESULTS_GUIDE.md`, `docs/TEAM_HANDOFF.md`, `docs/PRESENTATION_GUIDE.md`, `docs/AI_HANDOFF.md`, `docs/GLOSSARY.md`.
  - Created `CONTRIBUTING.md`, `CITATION.cff`, and `docs/assets/rurallink-mark.svg`; updated `AGENTS.md`.
- **Current Scientific Status:** Phase 01–03 complete and independently audited (77/77 tests passing, 0 ruff errors). Phase 04 (`src/adaptive.py` and S0–S3 comparative experiments), Phase 05 (full Streamlit dashboard), Phase 06 (final audit), and Phase 07 (deployment) remain **pending** authorization.
- **Documentation Limitations:** Phase 04–07 sections are explicitly marked pending; PPT and analysis team member pairings remain pending confirmation.

---

## Phase 04-05: COMPLETE (2026-11-26, branch feature/scientific-app)
- **Phase 04:** `src/adaptive.py` (joint optimizer, S0-S3, shadowing reliability, bit-level validation), `experiments/run_adaptive.py`, `tests/test_adaptive.py`. Outputs: `outputs/results/adaptive_coverage_curves.csv`, `adaptive_coverage_summary.csv`, `adaptive_mc_validation.csv`; `outputs/figures/adaptive_coverage_radius.png`, `adaptive_rate_vs_distance.png`.
- **Phase 05:** `app.py` Streamlit workbench (left rail, telemetry strip, coverage zones, operating points, bit-level MC with engine constellation samples, method tab); `tests/test_app.py` AppTest smoke tests; light theme in `.streamlit/config.toml`.
- **Checks:** pytest 91 passed, ruff check and format clean.
- **Pending:** Phase 06 final audit and Phase 07 deployment (not started, no merge).

---

## Phase 06 targeted audit: COMPLETE (2026-11-26)
- **Defect fixed:** Phase 05 evaluated only slow (shadowing) adaptation. Added instantaneous-CSI evaluation: per shared Rayleigh+shadowing realization the max-rate option meeting the AWGN Eb/N0 threshold is chosen; BER is the conditional AWGN BER (max 1e-2 by construction). The earlier 4-7 % BER is the no-CSI average Rayleigh BER at slow-selected points (clarified in `outputs/summary.md`).
- **Fixed:** radii now reported as `<1 km` (no coverage at first tested point) and `>=12 km` (right-censored); added R0 fixed BPSK/1 RB reference; outage-adjusted effective rate (outage = 0) exported.
- **Verified unchanged:** shared realizations across scenarios, Es/N0 to Eb/N0 conversion (k = log2 M), 23 dBm cap, UI values from `src/` only.
- **Exports:** `adaptive_coverage_curves.csv`, `adaptive_coverage_summary.csv`, `adaptive_strategy_comparison.csv`, `adaptive_mc_validation.csv`, `outputs/summary.md`.
- **Checks:** pytest 93 passed (incl. AppTest), ruff clean, experiments rerun.
- **Pending:** Phase 07 deployment (not started, no merge).

---

## Phase 07 release preparation: COMPLETE (2026-11-26, branch feature/scientific-app)
- **Runtime & Cloud compatibility:** Pinned Linux-compatible runtime dependencies in `requirements.txt` (`numpy==2.5.5`, `scipy==1.18.1`, `pandas==3.1.1`, `matplotlib==3.11.2`, `plotly==7.2.0`, `streamlit==1.67.0`) for Python 3.12 (`.python-version`). Verified no Windows-specific packages, local PDF dependencies, absolute Windows paths, external APIs, or secrets in runtime code.
- **Offline launcher & docs:** Added `run_local.ps1` for offline `.venv` launch; updated `README.md` with Streamlit Community Cloud deployment settings (`feature/scientific-app`, `app.py`, Python 3.12) and live demo sequence.
- **Artifacts:** All `outputs/` CSVs, PNGs, and `outputs/summary.md` verified tracked in Git.
- **Checks:** `pytest` 93 passed (including AppTest), `ruff check` and `ruff format --check` clean.

---

## Final Integration & Presentation Release: COMPLETE (2026-11-26, branch feature/final-integration)
- **Git integration:** Created `feature/final-integration` from `origin/feature/ui-prototype` (`5c3a7d9`), merged `origin/feature/scientific-app` (`8d5c541`) preserving both histories without modifying original branches. Moved `dashboard_rurallink.html` to `prototypes/dashboard_rurallink.html` with `prototypes/README.md` (explicitly labeled prototype; defects not inherited).
- **Integrated Streamlit workbench (`app.py`):** Light engineering workbench inspired by Zahran's prototype (left parameter rail, segmented controls, 8-cell telemetry strip, SNR curves, bit-level MC constellation, side-by-side 900/1800 MHz radial coverage zones, S0-S3 & R0 comparison, research results tab with CSV/PNG downloads, Indonesian methodology & team attribution). All values originate from `src/`.
- **Docs & demo:** Added `docs/DEMO_GUIDE.md`; updated `README.md` and `docs/PROGRESS.md`.
- **Checks:** `pytest` 96 passed (incl. 8 AppTest cases), `ruff check` and `ruff format --check` clean.

---

## Interactive Workbench Upgrade: COMPLETE (2026-11-26, branch feature/interactive-workbench)
- **Single-page primary workbench (`app.py`):** Consolidated telemetry strip, interactive SNR vs distance (with active distance/operating-point marker), explicit bit-level Monte Carlo with side-by-side received constellations (`Dioptimalkan vs S0` and `Antar Frekuensi` using identical seed), side-by-side radial modulation coverage maps, fixed vs adaptive strategy comparison, and frequency comparison table into Tab A; kept published CSV/PNG results (Tab B) and methodology/limitations (Tab C) in secondary tabs.
- **Optional exploratory sensitivity (UI-only, `src/` & `outputs/` untouched):** Added dynamic BER target (`1e-2` primary / `1e-3` exploratory via `derive_switching_thresholds`) and supplementary `700 MHz` toggle (labeled exploratory inspired by Reddy 2022, not replication). Per-frequency caching avoids recomputation on unrelated widget changes.
- **Docs & tests:** Updated `tests/test_app.py`, `README.md`, `docs/DEMO_GUIDE.md`, `docs/DECISIONS.md` (D17), and `docs/PROGRESS.md`.
- **Sidebar UX refinement (2026-11-26):** Removed exploratory expander; exposed 700/900/1800 MHz (default 900) and BER 1e-2/1e-3 (default 1e-2) directly in sidebar with supplementary/exploratory labels and 3-frequency comparisons; replaced linear MC slider with discrete logarithmic choices (10²–10⁶, default 10⁵), modulation bit alignment, actual bit/symbol/constellation sample reporting, small-sample uncertainty warning, rule-of-three zero-error CI display, and stale MC result suppression on parameter change.
- **Research Encyclopedia & Label Cleanup (2026-11-26):** Simplified frequency control/chart labels (`700 | 900 | 1800`, concise supplementary caption); created `glossary_data.py` (10 categories A–J, synced to `docs/GLOSSARY.md`) and Tab D **Ensiklopedia RuralLink** in `app.py` with search, category filter, 4-column wrapped tables, and CSV export.

---

## Native Web Migration (Vercel + FastAPI): COMPLETE (2026-11-26, branch feature/native-web)
- **Native Frontend (`public/`):** Built `public/index.html`, `public/styles.css`, `public/app.js`, and `public/favicon.svg` directly on Zahran's latest HTML workbench (`prototypes/dashboard_interaktif_siskom.html` archived), preserving its light engineering workbench aesthetic, compact parameter rail, segmented controls, horizontal telemetry strip, side-by-side Canvas SNR & constellation plots, 3 radial coverage maps, and comparison tables, with 4-tab navigation (A. Workbench, B. Hasil Penelitian, C. Metodologi & Batasan, D. Ensiklopedia) and all 6 team members credited.
- **FastAPI Scientific Layer (`api/index.py`):** Exposed validated `src/`, `config.py`, `outputs/`, and `glossary_data.py` over `/api/health`, `/api/operating-point`, `/api/stochastic-analysis`, `/api/monte-carlo`, `/api/results`, `/api/methodology`, `/api/glossary`, `/api/glossary/csv`, and `/api/outputs/*`, with server-side range checks (`<= 23 dBm`, `1-12 km`, `10^2-10^6` bits), LRU caching, bounded constellation samples (`<= 320`), and zero JS scientific formulas.
- **Deployment & Safety Net:** Separated Vercel runtime dependencies (`requirements.txt`: FastAPI, Uvicorn, Pydantic, NumPy, SciPy, Pandas) from `requirements-streamlit.txt` and `requirements-dev.txt`; added `vercel.json` and `run_web.ps1` while preserving `app.py` and `run_local.ps1` intact.
- **Verification:** Added `tests/test_api.py` (22 tests) alongside existing 101 tests; verified live FastAPI + headless Chrome DOM, Canvas rendering, sliders, Monte Carlo, tabs A-D, mobile 390px layout, and zero console/HTTP errors.
- **Real-Time Interactive Simulation Upgrade (2026-11-26):**
  - Made SNR chart active marker directly draggable/clickable (`Pointer Events`, pointer capture, `touch-action` drag guard, `requestAnimationFrame`) with bidirectional slider/readout/UE map marker sync over `1–12 km`.
  - Enabled automatic live Monte Carlo by default with a `Simulasi Langsung (Live)` toggle, bounded preview samples (`<=10,000` bits during continuous drag), settled full-budget runs (`10^2–10^6`), `AbortController` + sequence-ID stale-response rejection, distance-independent radial zone caching (`include_zones=false` for distance-only updates), and strict stale-MC UI clearing.
  - Added regression tests (`tests/test_api.py`, 23 tests) and verified pointer dragging, touch pointer handling, `10^6`-bit burst debouncing, and CSI conditional BER display in headless Chrome.
- **Presentation UI Cleanup & Visual Refinement (2026-11-26):**
  - Cleaned up topbar (removed `.topbar-meta` chip/metadata clutter while preserving title, subtitle, team attribution, and Tabs A–D), removed `#workbenchStatusBar` banner above KPIs (replaced with hidden `#apiErrorBanner`), removed `#snrUpdateStatus`/`#mcStatusPill` status chips, and tightened KPI card labels.
  - Simplified SNR chart caption to one line with crisp white-haloed threshold/marker labels; replaced Monte Carlo prose with a fixed-height 4-row structured summary (`Aktif`, `BER AWGN`, `BER Rayleigh`, `Baseline S0`) preserving previous valid results during async updates.
  - Redesigned the 3-frequency radial modulation map (`700` / `900` / `1800 MHz`) with seamless filled modulation zones, BTS center, yellow UE marker, and optional `Batas 95% andal` overlay toggle (OFF by default); stacked comparison tables full-width with compact headers so all columns display without clipping.
  - Added UI structure regression test in `tests/test_api.py` (125 total tests) and verified live drag, MC updates, radial map overlay, and Tabs A–D in headless Chrome.

---

## Final Website Replacement & Repository Cleanup: COMPLETE (2026-11-26, branch feature/native-web)
- **HTML Freeze & Parity:** Adopted Zahran's standalone static HTML (`dashboard_rurallink.html`) byte-for-byte into `public/index.html` without altering any HTML, CSS, JS, formulas, or layout (`SHA256: 6a9a0ab73d9e622ccc622638e981a019f14ab00a0873ee3d371ed5afe3d89290`; `.gitattributes` preserves exact bytes across OS line endings).
- **Archive & Cleanup:** Tagged `archive/native-web` at `cfc1a70` before removing obsolete FastAPI (`api/`), custom JS/CSS (`public/app.js`, `public/styles.css`, `public/favicon.svg`), Streamlit workbench (`app.py`, `.streamlit/`, `requirements-streamlit.txt`, `run_local.ps1`, `run_web.ps1`), obsolete web tests (`tests/test_api.py`, `tests/test_app.py`), and old prototype duplicates (`prototypes/`).
- **Static Vercel Config & Branding:** Updated `vercel.json` for pure static hosting (`outputDirectory: "public"`, no functions/rewrites/build); generated `public/favicon.ico` from `docs/assets/rurallink-mark.svg` without modifying `public/index.html`.
- **Research Preservation & Docs:** Kept `src/`, `config.py`, `experiments/`, `outputs/`, `glossary_data.py`, and all scientific tests (`tests/test_scientific_engine.py`, `tests/test_adaptive.py`, `tests/test_environment.py`) intact; updated `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, and `docs/` to separate the analytical static JS website from the Python bit-level Monte Carlo research engine.
