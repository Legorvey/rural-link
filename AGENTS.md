# AGENTS.md — RuralLink

**Purpose:** reproducible Python simulator of uplink coverage limits and joint adaptive modulation–bandwidth allocation at 900/1800 MHz in Indonesian 3T regions (undergraduate research, Group 1 Digital Communication Systems).

## Before any work
Read `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`. After every implementation phase, update `docs/PROGRESS.md`.

## Conventions
- Python 3.12 in project-local `.venv` (Windows: `.venv\Scripts\python.exe`). Layout: engine in `src/`, runs in `experiments/`, UI in `app.py`, outputs in `outputs/`.
- Runtime deps in `requirements.txt`, dev deps in `requirements-dev.txt`. Keep Streamlit Cloud compatible; no databases, Docker, paid or external APIs.
- Checks: `pytest`, `ruff check .`, `ruff format --check .` must pass.
- Never commit secrets, `.env`, or reference PDFs.

## Scientific integrity
- Do not invent research results or citation details; mark unverified items as pending.
- Do not silently change scientific assumptions; record changes in `docs/DECISIONS.md`.
- Label all data as **theoretical**, **simulated** (Monte Carlo, bit-level), or **illustrative**.
- Scientific code needs tests (known closed-form checks, seeds for reproducibility).
- Do not start a phase without authorization.