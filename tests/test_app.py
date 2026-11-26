from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"

TIMEOUT = 120


def _run(at: AppTest) -> AppTest:
    at.run(timeout=TIMEOUT)
    assert not at.exception, [e.value for e in at.exception]
    return at


def _app() -> AppTest:
    return _run(AppTest.from_file(str(APP), default_timeout=TIMEOUT))


def test_default_render_shows_engine_metrics():
    at = _app()
    labels = [m.label for m in at.metric]
    assert any("Path loss" in x for x in labels)
    assert any("Joint choice" in x for x in labels)
    assert len(at.tabs) == 4
    assert not at.error


def test_frequency_and_environment_interaction():
    at = _app()
    before = at.metric[0].value
    at.sidebar.radio[0].set_value(1800.0)
    _run(at)
    assert at.metric[0].value != before
    at.sidebar.radio[1].set_value("LOS")
    _run(at)
    assert not at.error


def test_power_slider_is_capped_at_23_dbm():
    at = _app()
    power = next(s for s in at.sidebar.slider if "transmit power" in s.label)
    assert power.max == 23.0
    power.set_value(10.0)
    _run(at)
    assert not at.error


def test_empty_scenario_selection_shows_info():
    at = _app()
    at.sidebar.multiselect[0].set_value([])
    _run(at)
    assert any("at least one scenario" in i.value for i in at.info)


def test_monte_carlo_button_runs_engine_transmission():
    at = _app()
    at.sidebar.slider[1].set_value(3.0)
    _run(at)
    btn = next(b for b in at.button if "Monte Carlo" in b.label)
    btn.click()
    _run(at)
    labels = [m.label for m in at.metric]
    assert any("MC AWGN" in x for x in labels) and any("MC Rayleigh" in x for x in labels)
