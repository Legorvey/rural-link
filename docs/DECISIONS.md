# Decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | Python 3.12.14 (installed via `uv`) in `.venv` | System has only 3.13/3.14; spec requires 3.11/3.12; 3.12 is supported by Streamlit Cloud |
| D2 | Repository root is the workspace folder (no nested `RuralLink/`) | Avoid nested repositories |
| D3 | Runtime/dev deps split; version floors in requirements, exact pins in `requirements.lock.txt` | Reproducibility with Cloud compatibility |
| D4 | Ruff rules E,F,I,B; line length 100 | Simple, fast |
| D5 | `*.pdf` gitignored globally | Copyrighted references must not be redistributed |
| D6 | Scientific modules are docstring-only placeholders | No fabricated functionality before Phase 02 |
| D7 | `requests` in dev deps only, used for HTTP smoke test | Not needed at runtime |
| D8 | Standard CI path loss with Park et al. (2023) 1400 MHz LOS/NLOS parameters extrapolated to 900/1800 MHz | No measured Indonesian rural data available; Park (2023) is the closest published rural close-in campaign. Extrapolation labeled as comparative simulation only. |
| D9 | Yogapratama (2015) RF parameters from Table IV (figures-only PDF) | Authors, venue, and year unverified from local PDF; parameters match typical rural LTE planning and Reddy (2022) Table 1. Used with explicit limitation note. |
| D10 | Khan (2025) BER equations NOT copied directly | Khan (2025) Eqs. (11)/(14) omit the 1/log2(M) Gray-coding BER factor (giving SER not BER). RuralLink uses standard exact Gray-coded BER (Cho & Yoon, 2002) instead. |
| D11 | No diffraction-adjusted CI exponent | Diffraction-adjusted NLOS models from Park (2023) require terrain elevation profiles (ITU-R P.526/P.1812) not available for this simulation. Standard NLOS (n=2.56, σ=11.40 dB) is used. |
| D12 | numpy.uint8 dtype rejected for Gray PAM level arithmetic; replaced with int64 | 2*indices - (n_levels-1) overflows uint8 for n_levels>=2, producing large positive values instead of negative integers. Bug found in Phase 03 test cycle; fixed before commit. |
| D13 | Exact Cho & Yoon (2002) QAM BER used for thresholds and primary curves | Standard nearest-neighbour approximation available as `method='approx'` for reference but overestimates at low SNR. |