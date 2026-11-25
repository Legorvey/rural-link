# AGENTS.md — RuralLink

**Purpose:** Reproducible Python simulator of uplink coverage limits and joint adaptive modulation–bandwidth allocation at 900/1800 MHz in Indonesian 3T regions (Group 1, Digital Communication Systems, 2026).

## Reading Paths (Token Conservation)
- **Before any work:** Read `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`.
- **Canonical documentation:**
  - Scientific math & assumptions: `docs/METHODOLOGY.md` and `config.py`
  - Literature & provenance: `docs/REFERENCES.md`
  - Architecture & contracts: `docs/ARCHITECTURE.md`
  - Team onboarding & handoff: `docs/START_HERE.md`, `docs/TEAM_HANDOFF.md`, `docs/RESULTS_GUIDE.md`
- **Token conservation:** Do NOT load the entire repository or re-read full reference PDFs when `docs/REFERENCES.md` and `docs/METHODOLOGY.md` already contain the verified facts.

## Conventions
- Python 3.12 in project-local `.venv` (Windows: `.venv\Scripts\python.exe`).
- Layout: engine in `src/`, runs in `experiments/`, UI in `app.py`, outputs in `outputs/`.
- Runtime deps in `requirements.txt`, dev deps in `requirements-dev.txt`. Keep Streamlit Cloud compatible; no databases, Docker, paid or external APIs.
- Checks: `.venv\Scripts\python.exe -m pytest`, `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m ruff format --check .` must pass.
- Never commit secrets, `.env`, or reference PDFs (`*.pdf` is gitignored).

## Scientific Integrity
- Do not invent research results or citation details; mark unverified items as pending.
- Do not silently change scientific assumptions; record changes in `docs/DECISIONS.md`.
- Do not overwrite validated modules in `src/` unnecessarily.
- Label all data as **THEORETICAL**, **SIMULATED** (Monte Carlo, bit-level), or **ILLUSTRATIVE**.
- Verify actual outputs (`outputs/results/*.csv`, `outputs/figures/*.png`) before claiming results.
- Scientific code needs tests (known closed-form checks, seeds for reproducibility).
- Update `docs/PROGRESS.md` after every implementation or documentation phase.
- Do not start a new scientific phase without authorization.
