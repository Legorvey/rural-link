import numpy as np
import pytest

from config import DEFAULT_CONFIG
from src.adaptive import (
    SCENARIOS,
    check_tx_power,
    coverage_radius_km,
    evaluate_scenario_curves,
    rayleigh_outage_probability,
    scenario_options,
    select_operating_point,
    summarize_coverage,
    validate_operating_point,
)
from src.link_budget import compute_link_budget
from src.modulation import derive_switching_thresholds

D = np.arange(1.0, 12.01, 0.5)


def test_tx_power_cap():
    assert check_tx_power(23.0) == 23.0
    with pytest.raises(ValueError):
        check_tx_power(26.0)
    with pytest.raises(ValueError):
        select_operating_point(120.0, tx_power_dbm=30.0)


def test_option_sets():
    assert scenario_options("S0") == [("QPSK", 25)]
    assert len(scenario_options("S3")) == 4 * len(DEFAULT_CONFIG.active_rb_choices)
    with pytest.raises(ValueError):
        scenario_options("S9")


def test_selection_is_feasible_and_max_rate():
    thr = derive_switching_thresholds()
    for pl in (95.0, 110.0, 125.0, 135.0):
        sel = select_operating_point(pl, "S3", thresholds=thr)
        i = int(sel.index[0])
        if i < 0:
            continue
        mod, rb = sel.options[i]
        snr = compute_link_budget(pl, n_rb=rb).snr_db
        k = {"BPSK": 1, "QPSK": 2, "16-QAM": 4, "64-QAM": 6}[mod]
        assert snr - 10 * np.log10(k) >= thr[mod]["ebn0_db"] - 1e-9
        assert sel.ebn0_margin_db[0] >= 0.0
    assert select_operating_point(300.0, "S3").index[0] == -1


def test_thresholds_not_mislabeled():
    thr = derive_switching_thresholds()
    assert thr["BPSK"]["ebn0_db"] == pytest.approx(thr["QPSK"]["ebn0_db"], abs=1e-6)
    assert thr["QPSK"]["ebn0_db"] == pytest.approx(4.323, abs=2e-3)
    assert thr["QPSK"]["esn0_db"] == pytest.approx(thr["QPSK"]["ebn0_db"] + 3.0103, abs=1e-3)


def test_scenario_ordering_and_reliability_gap():
    c = evaluate_scenario_curves(900.0, "NLOS", D, n_draws=400)
    s = summarize_coverage(c).set_index("scenario")
    assert s.loc["S3", "radius_median_km"] >= s.loc["S1", "radius_median_km"]
    assert s.loc["S3", "radius_median_km"] >= s.loc["S2", "radius_median_km"]
    assert s.loc["S1", "radius_median_km"] >= s.loc["S0", "radius_median_km"]
    # deterministic median coverage overstates 95 % reliable coverage under shadowing
    assert (s["radius_stochastic_km"] <= s["radius_median_km"]).all()
    assert s.loc["S3", "radius_stochastic_km"] < s.loc["S3", "radius_median_km"]


def test_frequency_ordering_and_seed_reproducible():
    a = summarize_coverage(evaluate_scenario_curves(900.0, "LOS", D, ("S3",), n_draws=300))
    b = summarize_coverage(evaluate_scenario_curves(1800.0, "LOS", D, ("S3",), n_draws=300))
    assert a.radius_median_km[0] >= b.radius_median_km[0]
    c1 = evaluate_scenario_curves(900.0, "NLOS", D, ("S3",), n_draws=200, seed=7)
    c2 = evaluate_scenario_curves(900.0, "NLOS", D, ("S3",), n_draws=200, seed=7)
    assert c1.equals(c2)


def test_coverage_radius_helper():
    d = np.array([1.0, 2.0, 3.0, 4.0])
    assert coverage_radius_km(d, np.array([1, 1, 0, 1], bool)) == (2.0, False)
    assert coverage_radius_km(d, np.ones(4, bool)) == (4.0, True)
    assert coverage_radius_km(d, np.zeros(4, bool)) == (0.0, False)


def test_rayleigh_outage_closed_form():
    assert rayleigh_outage_probability(10.0, 10.0) == pytest.approx(1 - np.exp(-1))
    assert rayleigh_outage_probability(0.0, 1.0) == 1.0


def test_mc_validation_matches_theory_and_returns_engine_samples():
    v = validate_operating_point("QPSK", 4.323, 200_000, seed=3, constellation_sample_size=100)
    assert v["mc_ber_awgn"] == pytest.approx(1e-2, rel=0.2)
    assert v["mc_ber_rayleigh"] > 5 * v["mc_ber_awgn"]
    assert v["samples_awgn"].shape == (100,) and v["samples_rayleigh"].shape == (100,)
    assert SCENARIOS["S3"]["adapt_mod"] and SCENARIOS["S3"]["adapt_rb"]


def test_fixed_bpsk_1rb_reference_and_labels():
    from src.adaptive import radius_label

    assert scenario_options("R0") == [("BPSK", 1)]
    assert radius_label(0.0, False, 1.0, 12.0) == "<1 km"
    assert radius_label(12.0, True, 1.0, 12.0) == ">=12 km"
    assert radius_label(3.25, False, 1.0, 12.0) == "3.25 km"


def test_instantaneous_csi_conditional_ber_and_shared_realizations():
    c = evaluate_scenario_curves(1800.0, "NLOS", D, n_draws=500, seed=11)
    served = c.dropna(subset=["fading_cond_ber_max"])
    assert len(served) > 0
    assert served.fading_cond_ber_max.max() <= DEFAULT_CONFIG.ber_target + 1e-12
    p = c.pivot(index="distance_km", columns="scenario")
    for other in ("S0", "S1", "S2", "R0"):
        assert (p["fading_outage_prob"]["S3"] <= p["fading_outage_prob"][other] + 1e-12).all()
        assert (
            p["fading_effective_rate_bps"]["S3"] >= p["fading_effective_rate_bps"][other] - 1e-6
        ).all()
    # R0 is the most robust fixed option: it cannot have more outage than S0
    assert (p["fading_outage_prob"]["R0"] <= p["fading_outage_prob"]["S0"] + 1e-12).all()
    # fading adds outage relative to shadowing alone
    s3 = c[c.scenario == "S3"]
    assert (s3.fading_outage_prob >= s3.shadow_outage_prob - 0.05).all()
