# RuralLink

Uplink coverage enhancement via adaptive modulation and bandwidth allocation at 900/1800 MHz in Indonesia's 3T regions (Group 1, Digital Communication Systems).

**Status:** Phase 01 (environment setup) only. The scientific engine is NOT implemented; the app shows a landing page without results.

## Setup (Windows, Python 3.12)
```
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m streamlit run app.py
```
Exact versions: `requirements.lock.txt`. Docs: `docs/`. Agents: read `AGENTS.md` first.