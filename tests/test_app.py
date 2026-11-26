from pathlib import Path

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from src.adaptive import evaluate_scenario_curves, summarize_coverage

APP = Path(__file__).resolve().parents[1] / "app.py"
RES = Path(__file__).resolve().parents[1] / "outputs" / "results"
TIMEOUT = 180
TEAM = ["Aditya", "Zahran", "Baihaqy", "Jeyd", "Rizqul", "Yusril"]


def _run(at: AppTest) -> AppTest:
    at.run(timeout=TIMEOUT)
    assert not at.exception, [e.value for e in at.exception]
    return at


def _app() -> AppTest:
    return _run(AppTest.from_file(str(APP), default_timeout=TIMEOUT))


def _md(at: AppTest) -> str:
    return " ".join(m.value for m in at.markdown)


def test_default_render_header_tabs_and_strip():
    at = _app()
    text = _md(at)
    assert "Kelompok 1" in text and "2026" in text
    assert all(n in text for n in TEAM)
    for label in (
        "Path loss CI",
        "Daya terima Pr",
        "Noise floor",
        "SNR (Es/N0)",
        "Konfigurasi aktif",
        "Laju nominal",
        "Probabilitas outage",
    ):
        assert label in text
    assert len(at.tabs) == 4
    assert not at.error


def test_power_slider_capped_and_dist_range():
    at = _app()
    assert at.sidebar.slider(key="ptx").max == 23.0
    assert at.sidebar.slider(key="dist").max == 12.0


def test_frequency_change_updates_telemetry_and_preset_resets():
    at = _app()
    before = _md(at)
    at.sidebar.segmented_control(key="freq").set_value(1800.0)
    _run(at)
    assert _md(at) != before
    at.sidebar.button(key="preset_btn").click()
    _run(at)
    assert at.session_state["freq"] == 900.0 and at.session_state["dist"] == 5.0
    assert at.session_state["strat"] == "S3"


def test_adaptive_disables_manual_controls_manual_enables_them():
    at = _app()
    assert at.sidebar.segmented_control(key="rb").disabled
    at.sidebar.selectbox(key="strat").set_value("MANUAL")
    _run(at)
    assert not at.sidebar.segmented_control(key="rb").disabled
    assert not at.sidebar.segmented_control(key="mod").disabled


def test_infeasible_manual_config_warns():
    at = _app()
    at.sidebar.selectbox(key="strat").set_value("MANUAL")
    at.sidebar.slider(key="dist").set_value(12.0)
    _run(at)
    at.sidebar.segmented_control(key="mod").set_value("64-QAM")
    at.sidebar.segmented_control(key="rb").set_value(25)
    _run(at)
    assert any("tidak layak" in w.value for w in at.warning)


def test_baseline_outage_state_blocks_monte_carlo():
    at = _app()
    at.sidebar.selectbox(key="strat").set_value("S0")
    _run(at)
    assert any("Tidak ada kombinasi" in e.value for e in at.error)
    assert at.button(key="run_mc").disabled


def test_run_simulation_uses_engine_monte_carlo_and_both_strategies():
    at = _app()
    at.button(key="run_mc").click()
    _run(at)
    text = _md(at)
    assert "BER MC AWGN" in text and "Baseline S0" in text
    mc = at.session_state["mc"]
    assert mc["opt"]["samples_awgn"].size > 0 and mc["opt"]["mc_errors_awgn"] >= 0
    assert mc["base"] is None  # preset 900 MHz NLOS 5 km: S0 baseline in outage
    at.sidebar.slider(key="dist").set_value(2.0)
    _run(at)
    assert any("Parameter berubah" in w.value for w in at.warning)


def test_live_results_match_published_csv():
    grid = np.round(np.arange(1.0, 12.0 + 1e-9, 0.25), 4)
    live = summarize_coverage(
        evaluate_scenario_curves(900.0, "NLOS", grid, n_draws=5000, seed=42)
    ).set_index("scenario")
    pub = pd.read_csv(RES / "adaptive_coverage_summary.csv")
    pub = pub[(pub.freq_mhz == 900.0) & (pub.environment == "NLOS")].set_index("scenario")
    for col in ("radius_median_km", "radius_stochastic_km", "radius_fading_km"):
        assert (live[col] == pub.loc[live.index, col]).all()
