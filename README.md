# RuralLink

Uplink coverage enhancement via adaptive modulation and bandwidth allocation at 900/1800 MHz in Indonesia's 3T regions (Group 1, Digital Communication Systems).

**Status:** Phase 02–03 complete. Scientific simulation engine implemented and validated.

## Research Context
> Analisis Peningkatan Jangkauan Uplink melalui Modulasi Adaptif dan Alokasi Bandwidth pada Frekuensi 900 MHz dan 1800 MHz di Wilayah 3T Indonesia.

**Research question:** Under a power-limited uplink, how does joint adaptive modulation and bandwidth allocation affect reliable communication range, outage probability, and achievable nominal data rate compared with fixed configurations?

## Setup (Windows, Python 3.12)
```
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe experiments/run_experiments.py
.venv\Scripts\python.exe -m streamlit run app.py
```
Exact versions: `requirements.lock.txt`. Docs: `docs/`. Agents: read `AGENTS.md` first.

## Engine Architecture (Phase 03)

| Module | Purpose |
|---|---|
| `config.py` | Typed `SimulationConfig` with units, defaults, validation |
| `src/propagation.py` | Close-In rural path loss (Park 2023 LOS/NLOS params) |
| `src/link_budget.py` | Received power, noise, SNR, Eb/N0, nominal rate |
| `src/modulation.py` | Gray-coded constellations, exact QAM BER (Cho-Yoon), thresholds |
| `src/channels.py` | AWGN, independent/block Rayleigh, coherent ZF equalization |
| `src/metrics.py` | Batched Monte Carlo, Wilson CI, zero-error 3/N bound |
| `experiments/run_experiments.py` | Smoke experiments → 4 figures, 3 CSVs |
| `src/adaptive.py` | Reserved for Phase 04 |

## Key Scientific Parameters (900/1800 MHz, NLOS Median)
- UE Tx power: 23 dBm (fixed, power-limited)
- BTS Rx gain: 11 dBi; Feeder 5 dB; NF 4 dB
- CI path loss: n=2.56, σ=11.40 dB (Park 2023 1400 MHz — extrapolated)
- Switching thresholds (BER=1e-2 AWGN): BPSK 4.32 dB → QPSK 4.32 dB → 16-QAM 7.88 dB → 64-QAM 11.95 dB Eb/N0

## Data Labels
All outputs are explicitly labeled: **THEORETICAL** (closed-form) or **SIMULATED** (Monte Carlo, bit-level).
No actual LTE throughput or geographic coverage claims are made.

## Phases
| Phase | Status |
|---|---|
| 01 Environment setup | ✅ COMPLETE |
| 02 Mathematical specification | ✅ COMPLETE |
| 03 Scientific simulation engine | ✅ COMPLETE |
| 04 Adaptive optimization | ⏳ Awaiting authorization |
| 05 Web interface | ⏳ Pending |
| 06 Scientific audit | ⏳ Pending |
| 07 Deployment | ⏳ Pending |
