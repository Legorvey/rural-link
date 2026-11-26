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


def test_default_render_single_page_workbench_and_tabs():
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
        "Peta zona modulasi radial sisi-ke-sisi",
        "Fixed vs adaptif",
        "Perbandingan frekuensi",
    ):
        assert label in text
    assert len(at.tabs) == 3
    assert len(at.get("plotly_chart")) == 4
    assert len(at.dataframe) >= 4
    assert not at.error
    assert list(at.sidebar.segmented_control(key="freq").options) == ["700* (supl.)", "900", "1800"]
    assert list(at.sidebar.segmented_control(key="ber_target").options) == [
        "10⁻² (Primer)",
        "10⁻³ (Eksploratori)",
    ]
    assert list(at.sidebar.select_slider(key="nbits").options) == [
        "10²",
        "10³",
        "10⁴",
        "10⁵",
        "10⁶",
    ]
    assert at.session_state["freq"] == 900.0
    assert at.session_state["ber_target"] == 1e-2
    assert at.session_state["nbits"] == 100_000


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
    assert at.session_state["ber_target"] == 1e-2
    assert at.session_state["nbits"] == 100_000


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


def test_run_simulation_uses_engine_monte_carlo_and_both_views():
    at = _app()
    at.button(key="run_mc").click()
    _run(at)
    text = " ".join(c.value for c in at.caption)
    assert "BER MC AWGN" in text and "Baseline S0" in text
    mc = at.session_state["mc"]
    assert mc["opt"]["samples_awgn"].size > 0 and mc["opt"]["mc_errors_awgn"] >= 0
    assert mc["base"] is None  # preset 900 MHz NLOS 5 km: S0 baseline in outage
    assert 700.0 in mc["by_freq"] and 900.0 in mc["by_freq"] and 1800.0 in mc["by_freq"]
    n_charts_with_mc = len(at.get("plotly_chart"))
    assert n_charts_with_mc == 5

    at.segmented_control(key="mc_view").set_value("Antar Frekuensi")
    _run(at)
    assert len(at.get("plotly_chart")) == n_charts_with_mc

    at.sidebar.slider(key="dist").set_value(2.0)
    _run(at)
    assert any("Parameter berubah" in w.value for w in at.warning)
    assert len(at.get("plotly_chart")) == 4
    assert "BER MC AWGN" not in " ".join(c.value for c in at.caption)


def test_direct_sidebar_700mhz_and_ber_1e3():
    at = _app()
    at.sidebar.segmented_control(key="freq").set_value(700.0)
    at.sidebar.segmented_control(key="ber_target").set_value(1e-3)
    _run(at)
    text = _md(at)
    assert "Mode sensitivitas eksploratori aktif" in text
    assert "bukan replikasi Reddy" in text
    assert at.session_state["freq"] == 700.0
    assert not at.error


def test_mc_logarithmic_bits_alignment_small_sample_warning_and_zero_error_ci():
    at = _app()
    at.sidebar.select_slider(key="nbits").set_value(100)
    at.sidebar.selectbox(key="strat").set_value("MANUAL")
    at.sidebar.slider(key="dist").set_value(1.0)
    _run(at)
    at.sidebar.segmented_control(key="mod").set_value("64-QAM")
    at.sidebar.segmented_control(key="rb").set_value(1)
    _run(at)
    assert any("Sampel kecil" in w.value for w in at.warning)
    at.button(key="run_mc").click()
    _run(at)
    mc = at.session_state["mc"]
    assert mc["opt"]["n_bits"] == 102
    assert mc["opt"]["samples_awgn"].size == 17
    captions = " ".join(c.value for c in at.caption)
    assert "102 bit / 17 simbol, sampel konstelasi 17" in captions
    if mc["opt"]["mc_errors_awgn"] == 0:
        assert "rule-of-three" in captions


def test_zone_strategy_sync_and_independent_override():
    at = _app()
    assert at.session_state["zone_sc"] == "S3"
    at.selectbox(key="zone_sc").set_value("S0")
    _run(at)
    assert at.session_state["zone_sc"] == "S0"


def test_live_results_match_published_csv():
    grid = np.round(np.arange(1.0, 12.0 + 1e-9, 0.25), 4)
    live = summarize_coverage(
        evaluate_scenario_curves(900.0, "NLOS", grid, n_draws=5000, seed=42)
    ).set_index("scenario")
    pub = pd.read_csv(RES / "adaptive_coverage_summary.csv")
    pub = pub[(pub.freq_mhz == 900.0) & (pub.environment == "NLOS")].set_index("scenario")
    for col in ("radius_median_km", "radius_stochastic_km", "radius_fading_km"):
        assert (live[col] == pub.loc[live.index, col]).all()
