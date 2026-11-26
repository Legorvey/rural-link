# AGENTS.md — RuralLink

**Purpose:** Reproducible Python research engine (`src/`, `experiments/`, `outputs/`) and static interactive web simulator (`public/index.html`, byte-for-byte copy of `dashboard_rurallink.html`) for uplink coverage limits and joint adaptive modulation–bandwidth allocation at 900/1800 MHz in Indonesian 3T regions (Group 1, Digital Communication Systems, 2026).

## Reading Paths (Token Conservation)
- **Before any work:** Read `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`.
- **Canonical documentation:**
  - Scientific math & assumptions: `docs/METHODOLOGY.md` and `config.py`
  - Literature & provenance: `docs/REFERENCES.md`
  - Architecture & separation of web vs engine: `docs/ARCHITECTURE.md`
  - Team onboarding & handoff: `docs/START_HERE.md`, `docs/TEAM_HANDOFF.md`, `docs/RESULTS_GUIDE.md`
- **Token conservation:** Do NOT load the entire repository or re-read full reference PDFs when `docs/REFERENCES.md` and `docs/METHODOLOGY.md` already contain the verified facts.

## Website Freeze & Static Deployment
- `dashboard_rurallink.html` and `public/index.html` are Zahran's frozen standalone static HTML application (must remain byte-for-byte identical; never modify HTML/CSS/JS, formulas, or inject tags).
- `public/` is the isolated static Vercel root (`vercel.json` with `outputDirectory: "public"`, no backend/API/build step).
- Python (`src/`, `experiments/`) is the reproducible offline research implementation, NOT a website backend.

## Conventions
- Python 3.12 in project-local `.venv` (Windows: `.venv\Scripts\python.exe`).
- Layout: engine in `src/`, runs in `experiments/`, static website in `public/`, outputs in `outputs/`.
- Runtime research deps in `requirements.txt`, dev deps in `requirements-dev.txt`. No databases, Docker, paid APIs, or backend web servers.
- Checks: `.venv\Scripts\python.exe -m pytest`, `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m ruff format --check .` must pass.
- Never commit secrets, `.env`, or reference PDFs (`*.pdf` is gitignored).

## Scientific Integrity
- Do not invent research results or citation details; mark unverified items as pending.
- Do not silently change scientific assumptions; record changes in `docs/DECISIONS.md`.
- Do not overwrite validated modules in `src/` or published `outputs/` unnecessarily.
- Label all data as **THEORETICAL**, **SIMULATED** (Monte Carlo, bit-level), or **ILLUSTRATIVE**.
- Verify actual outputs (`outputs/results/*.csv`, `outputs/figures/*.png`) before claiming results.
- Distinguish the interactive analytical JavaScript website from Python bit-level Monte Carlo experiments.
- Scientific code needs tests (known closed-form checks, seeds for reproducibility).
- Update `docs/PROGRESS.md` after every implementation or documentation phase.
- Do not start a new scientific phase without authorization.
