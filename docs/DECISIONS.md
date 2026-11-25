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