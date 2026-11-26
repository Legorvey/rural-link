<div align="center">

<img src="docs/assets/rurallink-mark.svg" alt="RuralLink logo: minimal radio tower with signal waves over rural terrain" width="96"/>

# RuralLink

**Adaptive Uplink Coverage Simulator for Rural & 3T Indonesia (700 / 900 / 1800 MHz)**

[![Static Dashboard](https://img.shields.io/badge/Interface-Static_HTML_Dashboard-0f766e?style=flat-square)](https://rural-uplink.vercel.app/)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)](public/index.html)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)](public/index.html)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)](public/index.html)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](src/)
[![Pytest](https://img.shields.io/badge/Tested_with-Pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)](tests/)
[![Ruff](https://img.shields.io/badge/Linted_with-Ruff-D7FF64?style=flat-square&logo=ruff&logoColor=black)](pyproject.toml)
[![Vercel](https://img.shields.io/badge/Deployed_on-Vercel-000000?style=flat-square&logo=vercel&logoColor=white)](https://rural-uplink.vercel.app/)

[Live Demo](#-live-demo) · [What It Does](#-what-this-project-does) · [Dashboard Overview](#-main-interface-overview) · [Key Concepts](#-key-concepts-covered) · [Run Locally](#-how-to-run-locally) · [Reproducibility](#-reproducibility--research-notes) · [Team](#-team--credits)

</div>

---

## Live Demo

- **Primary Web App:** [https://rural-uplink.vercel.app/](https://rural-uplink.vercel.app/)
- **Format:** Pure static HTML dashboard (`public/index.html`, identical to `dashboard_rurallink.html`). It runs entirely in the browser with no backend, no database, and no external API calls.

---

## What This Project Does

**RuralLink** models uplink communication limits—from a user device (User Equipment / UE) to a cellular base station (BTS)—in rural and 3T (*Tertinggal, Terdepan, Terluar*) regions of Indonesia.

In large rural cells (1–12 km), the uplink is power-limited: a handheld UE is capped at **23 dBm (200 mW)**, far below a base station's transmit power. As distance increases or obstacles block the signal (Non-Line-of-Sight / NLOS), the uplink drops out long before the downlink does. According to Indonesia's Komdigi 2025 Performance Report, 4G reached 98.95% of the population in Q2 2025, but covered only 53.82% of land area.

The simulator compares:
- **Carrier frequencies:** **900 MHz** and **1800 MHz** (primary research), plus **700 MHz** (exploratory toggle in the dashboard).
- **Propagation environments:** Line-of-Sight (**LOS**) vs. Non-Line-of-Sight (**NLOS**), and **AWGN** vs. **Rayleigh** fading.
- **Five adaptation strategies (`S0–S3` and `R0`):**

| Code | Strategy | Modulation | Resource Blocks (`N_RB`) | Evaluation Role |
|---|---|---|---|---|
| **S0** | Fixed baseline | `QPSK` fixed | `25 RB` (`4.50 MHz`) fixed | Standard unadapted reference |
| **S1** | Adaptive modulation | `BPSK`–`64-QAM` | `25 RB` fixed | Isolates the gain from modulation switching alone |
| **S2** | Adaptive bandwidth | `QPSK` fixed | `1, 2, 5, 10, 25 RB` | Isolates the gain from narrowing bandwidth alone |
| **S3** | Joint adaptive | `BPSK`–`64-QAM` | `1, 2, 5, 10, 25 RB` | Selects the highest nominal rate that still meets the BER target |
| **R0** | Robust reference | `BPSK` fixed | `1 RB` (`180 kHz`) fixed | Maximum coverage reference at 23 dBm UE power |

*(The interactive dashboard also includes a `MANUAL` mode to lock a custom `N_RB` value.)*

---

## Main Interface Overview

The canonical web interface is Zahran's standalone static HTML dashboard ([`public/index.html`](public/index.html) / [`dashboard_rurallink.html`](dashboard_rurallink.html)). It is organized into four tabs:

1. **Interactive Simulator:** Left-hand parameter controls (`700 / 900 / 1800 MHz`, strategy `S0–S3 / R0 / MANUAL`, `N_RB`, `LOS / NLOS`, `Median / 95% Margin`, `AWGN / Rayleigh`, distance `1.0–12.0 km`, and UE power `20–26 dBm` for sensitivity exploration), a cross-frequency comparison table, a 6-metric telemetry strip, **Uplink SNR vs. Distance** plot, **I/Q Constellation** view, **2D Radial Coverage Zone Map**, and PNG/CSV export.
2. **Research Results:** Summary findings and verified tables from the Python experiments (`adaptive_coverage_summary.csv`, `adaptive_strategy_comparison.csv`, `adaptive_mc_validation.csv`) with CSV downloads.
3. **Methodology & Limitations:** Core equations (Close-In path loss, link budget, thermal noise, $E_b/N_0$, nominal rate), model parameters, study limitations, references, and team credits.
4. **Glossary & Equations (127):** Searchable reference of 127 digital communications terms across 10 categories, with category filters and CSV export.

---

## Key Concepts Covered

- **Path Loss:** Signal attenuation over distance. Moving from 1800 MHz to 900 MHz reduces free-space/Close-In path loss by **6.02 dB** ($20\log_{10}(2)$), extending usable cell radius.
- **Signal-to-Noise Ratio (SNR):** The ratio of received signal power to thermal noise power. Higher SNR allows higher data rates and fewer bit errors.
- **BER Target:** The maximum acceptable Bit Error Rate—set to **$\text{BER} \le 10^{-2}$** in this study—used to decide whether a modulation and bandwidth pair is viable.
- **Outage:** The probability that a link fails to meet the BER target under random shadowing and fading (evaluated against a **5% outage** reliability threshold).
- **Adaptive Modulation:** Switching between `BPSK`, `QPSK`, `16-QAM`, and `64-QAM` based on channel quality—using higher-order modulation near the BTS and falling back to `BPSK`/`QPSK` near the cell edge.
- **Adaptive Bandwidth (`N_RB`):** Narrowing the UE's allocated LTE Resource Blocks from `25 RB` (`4.50 MHz`) down to `1 RB` (`180 kHz`). Because total UE power is fixed, concentrating it into fewer RBs lowers receiver thermal noise and increases SNR by up to **13.98 dB**, trading nominal data rate for range.

---

## Repository Structure

```text
rural-link/
├── dashboard_rurallink.html   # Canonical standalone static HTML dashboard (immutable)
├── public/                    # Static Vercel deployment root
│   ├── index.html             # Byte-for-byte copy of dashboard_rurallink.html
│   └── favicon.ico            # RuralLink icon
├── vercel.json                # Pure static hosting config (outputDirectory: public)
├── config.py                  # Python simulation parameters and validation
├── src/                       # Python scientific engine (propagation, link_budget, modulation, channels, metrics, adaptive)
├── experiments/               # Deterministic experiment scripts (run_experiments.py, run_adaptive.py)
├── outputs/                   # Verified results: summary.md, results/*.csv, figures/*.png
├── tests/                     # Automated scientific and environment tests (pytest)
├── glossary_data.py           # Dataset of 127 glossary terms
└── docs/                      # Methodology, references, results guide, and team documentation
```

---

## How to Run Locally

### Option 1: Open Directly in a Browser (No Setup)
Double-click [`public/index.html`](public/index.html) or [`dashboard_rurallink.html`](dashboard_rurallink.html) to open the dashboard offline in any modern browser.

### Option 2: Serve with a Local Static Server
```powershell
python -m http.server --directory public 8000
```
Then open `http://127.0.0.1:8000/`.

---

## Reproducibility & Research Notes

The repository preserves the full offline **Python 3.12** research engine (`src/`, `experiments/`, `outputs/`) used to generate and validate the published numbers. Note that the HTML dashboard uses real-time analytical JavaScript for instant interactivity, whereas the Python engine runs exact Cho–Yoon BER math and bit-level Monte Carlo simulations (`seed = 42`, `5,000` shared shadowing + Rayleigh CSI realizations, `1,000,000` MC bits, Wilson 95% CI, UE power hard-capped at `23 dBm`).

### Running the Python Experiments & Checks
```powershell
# Setup environment (Python 3.12 via uv)
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt

# Reproduce Phase 02-03 validation (CSVs & PNG figures)
.venv\Scripts\python.exe -m experiments.run_experiments

# Reproduce Phase 04-06 adaptive strategy experiments (S0-S3 & R0)
.venv\Scripts\python.exe -m experiments.run_adaptive

# Run tests and linter
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
```

### Verified Numerical Highlights ([`outputs/summary.md`](outputs/summary.md))
- **RB Narrowing SNR Gain (THEORETICAL):** `25 -> 1 RB` = **`+13.9794 dB`**; `25 -> 5 RB` = **`+6.9897 dB`**; `1 RB` noise floor = **`-117.447 dBm`**.
- **900 MHz NLOS at 2 km (Shadowing + Rayleigh CSI, SIMULATED):** `S0` outage **`38.9%`** (`5.50 Mbit/s` effective) vs. `S3` outage **`5.7%`** (`11.97 Mbit/s` effective), compared to `R0` (`5.7%` outage, `0.17 Mbit/s` effective).
- **1800 MHz NLOS at 2 km (Shadowing + Rayleigh CSI, SIMULATED):** `S0` outage **`57.8%`** (`3.79 Mbit/s` effective) vs. `S3` outage **`12.0%`** (`7.79 Mbit/s` effective), compared to `R0` (`12.0%` outage, `0.16 Mbit/s` effective).

### Scope & Limitations
- Link-level uncoded model (no FEC/HARQ, no inter-cell interference, no multi-user scheduling); nominal rates (`B_active * log2(M)`) are not full LTE network throughput.
- Close-In path loss parameters (`n`, `sigma`) are extrapolated from 1400 MHz rural measurements in South Korea (Park et al., 2023) without Indonesian 3T field calibration.
- 2D coverage maps are radial and do not include terrain elevation; radii reaching `12 km` are right-censored (`>=12 km`).
- `700 MHz` and `>23 dBm` controls in the HTML dashboard are exploratory only; canonical Python experiments evaluate `900/1800 MHz` at `<= 23 dBm`.

---

## Deployment

Configured for pure static hosting on **Vercel** via [`vercel.json`](vercel.json) (`outputDirectory: "public"`). No build step, Python runtime, or environment variables are required.

---

## Team & Credits

**Group 1 — Digital Communication Systems (2026)**  
Lecturer: **Bu Dessy** · S1 Electrical Engineering, FMIPA, Universitas Padjadjaran

| Member | Role |
|---|---|
| **Yusril** | Presentation / PPT |
| **Rizqul** | Presentation / PPT |
| **Baihaqy** | Analysis and discussion |
| **Jeyd** | Analysis and discussion |
| **Aditya** | Programming and simulation |
| **Zahran** | Programming and simulation (including canonical static HTML app `dashboard_rurallink.html`) |

**Key References:** Reddy et al. (2022) · Khan et al. (2025) · Park et al. (2023) · Cho & Yoon (2002) · Yogapratama et al. (2015) · Kementerian Komdigi RI (2025). Full citations and methodology notes are in [`docs/REFERENCES.md`](docs/REFERENCES.md) and [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).
