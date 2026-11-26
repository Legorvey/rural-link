"""Targeted API tests verifying FastAPI parity with src/, validation, and endpoints."""

from __future__ import annotations

import math

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.index import app
from config import DEFAULT_CONFIG
from glossary_data import CATEGORIES, ENTRIES
from src.adaptive import evaluate_scenario_curves, select_operating_point, summarize_coverage
from src.link_budget import compute_link_budget, nominal_data_rate_bps
from src.modulation import bits_per_symbol, derive_switching_thresholds, get_constellation
from src.propagation import analytical_shadow_margin_db, get_ci_parameters, median_path_loss_db

client = TestClient(app)


def test_health_and_static_index():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["project"] == "RuralLink"
    assert set(body["team"]) == {"Aditya", "Zahran", "Baihaqy", "Jeyd", "Rizqul", "Yusril"}

    idx = client.get("/")
    assert idx.status_code == 200
    assert "RuralLink" in idx.text


def test_operating_point_numerical_parity_with_src():
    payload = {
        "freq_mhz": 900,
        "env": "NLOS",
        "channel": "AWGN",
        "shadow": "margin95",
        "dist_km": 2.0,
        "tx_power_dbm": 23.0,
        "ber_target": 1e-2,
        "strategy": "S3",
        "rb_manual": 25,
        "mod_manual": "QPSK",
    }
    resp = client.post("/api/operating-point", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    _, sigma = get_ci_parameters("NLOS")
    margin = analytical_shadow_margin_db(sigma, 1.0 - DEFAULT_CONFIG.outage_target)
    pl = float(median_path_loss_db(2000.0, 900.0, "NLOS")) + margin
    thr = derive_switching_thresholds(1e-2, DEFAULT_CONFIG.modulations)
    sel = select_operating_point(pl, "S3", 23.0, DEFAULT_CONFIG, thr)
    idx = int(sel.index[0])
    assert idx >= 0
    expected_mod, expected_rb = sel.options[idx]
    lb = compute_link_budget(pl, n_rb=expected_rb, tx_power_dbm=23.0)
    expected_rate = nominal_data_rate_bps(lb.b_active_hz, expected_mod)

    act = data["active"]
    assert act["ok"] is True
    assert act["mod"] == expected_mod
    assert act["rb"] == expected_rb
    assert math.isclose(act["pl_db"], pl, rel_tol=1e-9)
    assert math.isclose(act["snr_db"], float(lb.snr_db), rel_tol=1e-9)
    assert math.isclose(act["rate_bps"], expected_rate, rel_tol=1e-9)

    for mod in DEFAULT_CONFIG.modulations:
        assert math.isclose(data["thresholds"][mod]["ebn0_db"], thr[mod]["ebn0_db"], rel_tol=1e-9)


@pytest.mark.parametrize("strategy", ["S0", "S1", "S2", "S3", "R0"])
def test_representative_scenarios_at_5km_900mhz_nlos(strategy: str):
    resp = client.post(
        "/api/operating-point",
        json={"freq_mhz": 900, "env": "NLOS", "dist_km": 5.0, "strategy": strategy},
    )
    assert resp.status_code == 200
    act = resp.json()["active"]
    if strategy in ("S0", "S1"):
        assert act["ok"] is False
        assert act["mod"] == "Outage"
    else:
        assert act["ok"] is True
        assert act["rate_mbps"] > 0.0


def test_ber_target_1e3_raises_switching_thresholds():
    r2 = client.post("/api/operating-point", json={"ber_target": 1e-2}).json()
    r3 = client.post("/api/operating-point", json={"ber_target": 1e-3}).json()
    for mod in DEFAULT_CONFIG.modulations:
        assert r3["thresholds"][mod]["ebn0_db"] > r2["thresholds"][mod]["ebn0_db"]
    assert r3["is_exploratory"] is True
    assert r2["is_exploratory"] is False


def test_stochastic_analysis_parity_with_engine():
    resp = client.post(
        "/api/stochastic-analysis",
        json={
            "freq_mhz": 900,
            "env": "NLOS",
            "dist_km": 5.0,
            "tx_power_dbm": 23.0,
            "ber_target": 1e-2,
            "active_strategy": "S3",
            "zone_strategy": "S3",
        },
    )
    assert resp.status_code == 200
    body = resp.json()

    grid = np.round(np.arange(1.0, 12.25, 0.25), 4)
    curves = evaluate_scenario_curves(900.0, "NLOS", grid, n_draws=5000, seed=42)
    summary = summarize_coverage(curves)
    s3_sum = summary[summary.scenario == "S3"].iloc[0]

    zone_900 = [z for z in body["zones"] if z["freq_mhz"] == 900][0]
    assert zone_900["radius_median_label"] == s3_sum["radius_median_label"]
    assert zone_900["radius_stochastic_label"] == s3_sum["radius_stochastic_label"]
    assert zone_900["radius_fading_label"] == s3_sum["radius_fading_label"]

    by_sc = {r["scenario"]: r for r in body["strategy_comparison"]}
    assert set(by_sc) == {"S0", "S1", "S2", "S3", "R0"}
    assert by_sc["S3"]["fading_outage_pct"] < by_sc["S0"]["fading_outage_pct"]


@pytest.mark.parametrize(
    "bad_payload",
    [
        {"tx_power_dbm": 24.0},
        {"tx_power_dbm": 43.0},
        {"dist_km": 0.5},
        {"dist_km": 13.0},
        {"freq_mhz": 850},
        {"env": "Rician"},
        {"channel": "Rician"},
        {"ber_target": 1e-4},
        {"strategy": "INVALID"},
        {"rb_manual": 15},
        {"mod_manual": "256-QAM"},
    ],
)
def test_invalid_parameters_rejected(bad_payload: dict):
    resp = client.post("/api/operating-point", json=bad_payload)
    assert resp.status_code == 422


def test_monte_carlo_integrity_and_outage_blocking():
    # Outage on S0 at 900 MHz NLOS 5 km must return 400
    out_resp = client.post(
        "/api/monte-carlo",
        json={"freq_mhz": 900, "env": "NLOS", "dist_km": 5.0, "strategy": "S0", "n_bits": 1000},
    )
    assert out_resp.status_code == 400

    # Valid manual 64-QAM with 100 bits aligns up to 102 (17 symbols) and bounds I/Q samples
    mc_resp = client.post(
        "/api/monte-carlo",
        json={
            "freq_mhz": 900,
            "env": "NLOS",
            "dist_km": 1.0,
            "strategy": "MANUAL",
            "rb_manual": 1,
            "mod_manual": "64-QAM",
            "n_bits": 100,
        },
    )
    assert mc_resp.status_code == 200
    mc = mc_resp.json()
    opt = mc["opt"]
    assert opt["modulation"] == "64-QAM"
    assert opt["n_bits"] == 102
    assert opt["n_symbols"] == 17
    assert opt["n_samples_awgn"] == 17
    assert len(opt["samples_awgn"]["i"]) == 17
    assert len(opt["samples_awgn"]["q"]) == 17

    ref, _ = get_constellation("64-QAM")
    assert len(opt["ideal_constellation"]["i"]) == len(ref) == 64

    # Large bit count keeps displayed sample array bounded <= 320
    big_resp = client.post(
        "/api/monte-carlo",
        json={"freq_mhz": 900, "env": "NLOS", "dist_km": 5.0, "strategy": "S3", "n_bits": 100_000},
    )
    assert big_resp.status_code == 200
    big_opt = big_resp.json()["opt"]
    k = bits_per_symbol(big_opt["modulation"])
    assert big_opt["n_bits"] % k == 0
    assert big_opt["n_samples_awgn"] <= 320
    assert big_opt["n_samples_rayleigh"] <= 320


def test_results_methodology_and_glossary_endpoints():
    res = client.get("/api/results")
    assert res.status_code == 200
    rbody = res.json()
    assert len(rbody["figures"]) == 6
    assert len(rbody["csv_files"]) == 7

    assert client.get("/api/outputs/figures/adaptive_coverage_radius.png").status_code == 200
    assert client.get("/api/outputs/figures/not_allowed.png").status_code == 404
    assert client.get("/api/outputs/results/adaptive_coverage_summary.csv").status_code == 200
    assert client.get("/api/outputs/results/../secret.csv").status_code == 404

    meth = client.get("/api/methodology")
    assert meth.status_code == 200
    assert meth.json()["config"]["ue_tx_power_dbm"] == 23.0

    gl = client.get("/api/glossary")
    assert gl.status_code == 200
    gbody = gl.json()
    assert gbody["total_count"] == len(ENTRIES) == 127
    assert len(gbody["categories"]) == len(CATEGORIES) == 10

    gl_q = client.get(
        "/api/glossary", params={"q": "Wilson", "category": "H. Simulasi & Statistik"}
    )
    assert gl_q.status_code == 200
    assert gl_q.json()["filtered_count"] == 1

    gl_csv = client.get("/api/glossary/csv")
    assert gl_csv.status_code == 200
    assert "Kategori,Istilah / Singkatan" in gl_csv.content.decode("utf-8-sig")


def test_compact_distance_stochastic_and_mc_preview_modes():
    st_resp = client.post(
        "/api/stochastic-analysis",
        json={
            "freq_mhz": 900,
            "env": "NLOS",
            "dist_km": 5.0,
            "tx_power_dbm": 23.0,
            "ber_target": 1e-2,
            "active_strategy": "S3",
            "zone_strategy": "S3",
            "include_zones": False,
        },
    )
    assert st_resp.status_code == 200
    st_body = st_resp.json()
    assert st_body["zones"] is None
    assert st_body["active_outage"]["fading_cond_ber_mean"] <= 1e-2
    assert len(st_body["strategy_comparison"]) == 5

    mc_resp = client.post(
        "/api/monte-carlo",
        json={
            "freq_mhz": 900,
            "env": "NLOS",
            "dist_km": 5.0,
            "strategy": "S3",
            "n_bits": 10_000,
            "mode": "opt_vs_s0",
            "is_preview": True,
        },
    )
    assert mc_resp.status_code == 200
    mc_body = mc_resp.json()
    assert mc_body["is_preview"] is True
    assert mc_body["mode"] == "opt_vs_s0"
    assert mc_body["by_freq"] == {}
    assert mc_body["opt"]["n_bits"] == 10_000
    assert mc_body["opt"]["n_samples_awgn"] <= 320


def test_native_web_ui_cleanup_contract():
    html = client.get("/").text
    assert 'class="topbar-meta"' not in html
    assert 'id="workbenchStatusBar"' not in html
    assert 'id="snrUpdateStatus"' not in html
    assert 'id="mcStatusPill"' not in html
    assert 'id="mcPairSummary"' not in html
    assert 'id="chkShowReliability"' in html
    assert 'id="chkLiveMc" checked' in html
    assert "perubahan jumlah Resource Block" in html
    for tab_id in ("panelWorkbench", "panelResults", "panelMethodology", "panelEncyclopedia"):
        assert f'id="{tab_id}"' in html


@pytest.mark.parametrize("zone_strategy", ["S0", "S1", "S2", "S3", "R0"])
def test_radial_zone_invariants_and_src_parity(zone_strategy: str):
    resp = client.post(
        "/api/stochastic-analysis",
        json={
            "freq_mhz": 900,
            "env": "NLOS",
            "dist_km": 5.0,
            "tx_power_dbm": 23.0,
            "ber_target": 1e-2,
            "active_strategy": "S3",
            "zone_strategy": zone_strategy,
            "include_zones": True,
        },
    )
    assert resp.status_code == 200
    zones = resp.json()["zones"]
    assert len(zones) == 3

    mod_rank = {"64-QAM": 6, "16-QAM": 4, "QPSK": 2, "BPSK": 1, "Outage": 0}
    grid = np.round(np.arange(1.0, 12.25, 0.25), 4)
    curves = evaluate_scenario_curves(900.0, "NLOS", grid, n_draws=5000, seed=42)
    summary = summarize_coverage(curves)
    s_row = summary[summary.scenario == zone_strategy].iloc[0]

    z900 = [z for z in zones if z["freq_mhz"] == 900][0]
    assert z900["scenario"] == zone_strategy
    assert z900["radius_median_label"] == s_row["radius_median_label"]
    assert z900["radius_stochastic_label"] == s_row["radius_stochastic_label"]
    assert z900["radius_fading_label"] == s_row["radius_fading_label"]

    for z in zones:
        mods = [r["modulation"] for r in z["rings"]]
        if zone_strategy == "S0":
            assert set(mods) <= {"QPSK", "Outage"}
        elif zone_strategy == "S1":
            ranks = [mod_rank[m] for m in mods]
            assert ranks == sorted(ranks, reverse=True)
        elif zone_strategy == "S2":
            assert set(mods) <= {"QPSK", "Outage"}
        elif zone_strategy == "R0":
            assert set(mods) <= {"BPSK", "Outage"}
