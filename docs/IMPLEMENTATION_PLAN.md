# Implementation Plan

| Phase | Scope | Depends on | Acceptance criteria |
|---|---|---|---|
| 01 Environment setup | venv, deps, structure, docs, smoke test, git | — | Imports, pytest, ruff, Streamlit HTTP 200, git commit |
| 02 Mathematical specification | Written METHODOLOGY.md: propagation, link budget, modulation/BER, channels, adaptation, metrics; parameters with sources | 01, reference verification | All equations, units, assumptions, validation targets documented and approved |
| 03 Scientific simulation engine | Implement `src/` modules, bit-level Monte Carlo | 02 | Unit tests vs closed forms (e.g. BPSK/QAM AWGN BER), seeded reproducibility |
| 04 Adaptive optimization and experiments | Joint modulation-bandwidth optimizer, `run_experiments.py`, CSV + figures | 03 | Deterministic CSV/figures regenerate from one command; results labelled by data type |
| 05 Web interface | Streamlit app with interactive controls, export, offline fallback (precomputed data) | 04 | App runs locally; exports work; no hardcoded claims |
| 06 Scientific audit and testing | Cross-check vs references, coverage, edge cases, lint | 03–05 | Audit report; all tests green |
| 07 Deployment readiness | Streamlit Community Cloud, public repo review (no PDFs/secrets), offline fallback | 06 | Deployed URL works; README complete |