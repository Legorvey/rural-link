"""FastAPI scientific API and local static server for RuralLink native web frontend."""

from __future__ import annotations

import math
import sys
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DEFAULT_CONFIG, PROJECT_NAME, RESEARCH_TITLE, SimulationConfig  # noqa: E402
from glossary_data import CATEGORIES as GLOSSARY_CATEGORIES  # noqa: E402
from glossary_data import ENTRIES as GLOSSARY_ENTRIES  # noqa: E402
from glossary_data import glossary_csv_bytes  # noqa: E402
from src.adaptive import (  # noqa: E402
    SCENARIOS,
    check_tx_power,
    evaluate_scenario_curves,
    select_operating_point,
    summarize_coverage,
    validate_operating_point,
)
from src.link_budget import (  # noqa: E402
    active_bandwidth_hz,
    compute_link_budget,
    nominal_data_rate_bps,
    shannon_capacity_bps,
)
from src.modulation import (  # noqa: E402
    bits_per_symbol,
    derive_switching_thresholds,
    get_constellation,
    theoretical_ber_awgn,
    theoretical_ber_rayleigh,
)
from src.propagation import (  # noqa: E402
    analytical_shadow_margin_db,
    get_ci_parameters,
    median_path_loss_db,
)

CFG = DEFAULT_CONFIG
RES_DIR = ROOT / "outputs" / "results"
FIG_DIR = ROOT / "outputs" / "figures"
PUBLIC_DIR = ROOT / "public"
TEAM_MEMBERS = ("Aditya", "Zahran", "Baihaqy", "Jeyd", "Rizqul", "Yusril")
FREQ_OPTIONS: tuple[float, ...] = (700.0, 900.0, 1800.0)
ALLOWED_BER_TARGETS: tuple[float, ...] = (1e-2, 1e-3)
ALLOWED_N_BITS: tuple[int, ...] = (100, 1_000, 10_000, 100_000, 1_000_000)
DISTANCES_KM = np.round(np.arange(CFG.distance_min_km, CFG.distance_max_km + 1e-9, 0.25), 4)
N_DRAWS = 5000
CONSTELLATION_SAMPLE_LIMIT = 320

ALLOWED_RESULT_CSVS = {
    "adaptive_coverage_curves.csv",
    "adaptive_coverage_summary.csv",
    "adaptive_mc_validation.csv",
    "adaptive_strategy_comparison.csv",
    "ber_validation.csv",
    "link_budget_validation.csv",
    "modulation_thresholds.csv",
}
ALLOWED_RESULT_PNGS = {
    "adaptive_coverage_radius.png",
    "adaptive_rate_vs_distance.png",
    "path_loss_vs_distance.png",
    "uplink_snr_vs_distance.png",
    "ber_awgn_validation.png",
    "ber_rayleigh_validation.png",
}

STRATEGY_LABELS = {k: f"{k}: {v['label']}" for k, v in SCENARIOS.items()} | {
    "MANUAL": "Manual: RB dan modulasi dikunci pengguna"
}


class WorkbenchRequest(BaseModel):
    """Validated simulation parameters for operating-point and curve queries."""

    freq_mhz: Literal[700, 900, 1800] = 900
    env: Literal["LOS", "NLOS"] = "NLOS"
    channel: Literal["AWGN", "Rayleigh"] = "AWGN"
    shadow: Literal["median", "margin95"] = "median"
    dist_km: float = Field(default=5.0, ge=CFG.distance_min_km, le=CFG.distance_max_km)
    tx_power_dbm: float = Field(default=23.0, ge=10.0, le=CFG.ue_tx_power_dbm)
    ber_target: float = Field(default=1e-2)
    strategy: Literal["S0", "S1", "S2", "S3", "R0", "MANUAL"] = "S3"
    rb_manual: Literal[1, 2, 5, 10, 25] = 25
    mod_manual: Literal["BPSK", "QPSK", "16-QAM", "64-QAM"] = "QPSK"

    @field_validator("ber_target")
    @classmethod
    def _check_ber_target(cls, v: float) -> float:
        for allowed in ALLOWED_BER_TARGETS:
            if math.isclose(v, allowed, rel_tol=1e-9):
                return allowed
        raise ValueError("ber_target must be 1e-2 or 1e-3.")


class StochasticRequest(BaseModel):
    """Validated parameters for 5,000-draw stochastic analysis and radial zones."""

    freq_mhz: Literal[700, 900, 1800] = 900
    env: Literal["LOS", "NLOS"] = "NLOS"
    dist_km: float = Field(default=5.0, ge=CFG.distance_min_km, le=CFG.distance_max_km)
    tx_power_dbm: float = Field(default=23.0, ge=10.0, le=CFG.ue_tx_power_dbm)
    ber_target: float = Field(default=1e-2)
    active_strategy: Literal["S0", "S1", "S2", "S3", "R0", "MANUAL"] = "S3"
    zone_strategy: Literal["S0", "S1", "S2", "S3", "R0"] = "S3"
    include_zones: bool = True

    @field_validator("ber_target")
    @classmethod
    def _check_ber_target(cls, v: float) -> float:
        for allowed in ALLOWED_BER_TARGETS:
            if math.isclose(v, allowed, rel_tol=1e-9):
                return allowed
        raise ValueError("ber_target must be 1e-2 or 1e-3.")


class MonteCarloRequest(WorkbenchRequest):
    """Validated parameters for explicit or live bit-level Monte Carlo execution."""

    n_bits: int = Field(default=100_000, ge=100, le=1_000_000)
    mode: Literal["all", "opt_vs_s0", "by_freq"] = "all"
    is_preview: bool = False

    @field_validator("n_bits")
    @classmethod
    def _check_n_bits(cls, v: int) -> int:
        if v not in ALLOWED_N_BITS:
            raise ValueError(f"n_bits must be one of {ALLOWED_N_BITS}.")
        return v


@lru_cache(maxsize=8)
def _make_config(ber_target: float) -> SimulationConfig:
    if math.isclose(ber_target, CFG.ber_target):
        return CFG
    return replace(CFG, ber_target=float(ber_target))


@lru_cache(maxsize=8)
def _thresholds(ber_target: float) -> dict[str, dict[str, float]]:
    return derive_switching_thresholds(float(ber_target), CFG.modulations)


@lru_cache(maxsize=64)
def _cached_freq_curves(
    freq_mhz: float, env: str, tx_power_dbm: float, ber_target: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = _make_config(ber_target)
    curves = evaluate_scenario_curves(
        float(freq_mhz),
        env,
        DISTANCES_KM,
        tuple(SCENARIOS),
        float(tx_power_dbm),
        N_DRAWS,
        cfg.default_seed,
        cfg,
    )
    return curves, summarize_coverage(curves, cfg)


def align_mc_bits(n_bits: int, modulation: str) -> int:
    """Align requested bit count upward to an exact multiple of bits_per_symbol."""
    k = bits_per_symbol(modulation)
    return max(k, ((int(n_bits) + k - 1) // k) * k)


def evaluate_link(
    freq_mhz: float,
    env: str,
    dist_km: float,
    tx_power_dbm: float,
    shadow: str,
    strategy: str,
    rb_manual: int,
    mod_manual: str,
    ber_target: float,
) -> dict:
    """Evaluate single uplink operating point directly via validated src/ functions."""
    check_tx_power(tx_power_dbm, CFG)
    cfg = _make_config(ber_target)
    thr = _thresholds(ber_target)
    _, sigma = get_ci_parameters(env)
    margin = (
        analytical_shadow_margin_db(sigma, 1.0 - cfg.outage_target) if shadow == "margin95" else 0.0
    )
    pl_db = float(median_path_loss_db(dist_km * 1000.0, freq_mhz, env)) + margin

    if strategy == "MANUAL":
        mod, rb = mod_manual, int(rb_manual)
    else:
        sel = select_operating_point(pl_db, strategy, tx_power_dbm, cfg, thr)
        idx = int(sel.index[0])
        if idx >= 0:
            mod, rb = sel.options[idx]
        else:
            mod, rb = "Outage", min(r for _, r in sel.options)

    lb = compute_link_budget(pl_db, n_rb=rb, tx_power_dbm=tx_power_dbm)
    b_hz = active_bandwidth_hz(rb, cfg.rb_bandwidth_hz)
    shannon_mbps = float(shannon_capacity_bps(b_hz, float(lb.snr_linear)) / 1e6)

    out: dict = {
        "pl_db": float(pl_db),
        "margin_db": float(margin),
        "pr_dbm": float(lb.pr_dbm),
        "noise_dbm": float(lb.noise_dbm),
        "snr_db": float(lb.snr_db),
        "rb": int(rb),
        "mod": mod,
        "b_hz": float(b_hz),
        "p_rb_dbm": float(lb.power_per_rb_dbm),
        "shannon_mbps": shannon_mbps,
    }
    if mod == "Outage":
        out |= {
            "ok": False,
            "ebn0_db": None,
            "ebn0_margin_db": None,
            "ebn0_threshold_db": None,
            "esn0_threshold_db": None,
            "spectral_eff_active": 0,
            "rate_bps": 0.0,
            "rate_mbps": 0.0,
            "ber_awgn": None,
            "ber_rayleigh": None,
        }
        return out

    k = bits_per_symbol(mod)
    ebn0 = float(lb.snr_db) - 10.0 * math.log10(k)
    margin_eb = ebn0 - thr[mod]["ebn0_db"]
    ok = margin_eb >= 0.0
    rate_bps = float(nominal_data_rate_bps(b_hz, mod)) if ok else 0.0
    out |= {
        "ok": bool(ok),
        "ebn0_db": float(ebn0),
        "ebn0_margin_db": float(margin_eb),
        "ebn0_threshold_db": float(thr[mod]["ebn0_db"]),
        "esn0_threshold_db": float(thr[mod]["esn0_db"]),
        "spectral_eff_active": int(k) if ok else 0,
        "rate_bps": rate_bps,
        "rate_mbps": rate_bps / 1e6,
        "ber_awgn": float(theoretical_ber_awgn(10.0 ** (ebn0 / 10.0), mod)),
        "ber_rayleigh": float(theoretical_ber_rayleigh(10.0 ** (ebn0 / 10.0), mod)),
    }
    return out


@lru_cache(maxsize=64)
def _cached_mc(modulation: str, ebn0_db_rounded: float, aligned_bits: int) -> dict:
    res = validate_operating_point(
        modulation,
        ebn0_db_rounded,
        aligned_bits,
        seed=CFG.default_seed,
        constellation_sample_size=CONSTELLATION_SAMPLE_LIMIT,
    )
    ref, labels = get_constellation(modulation)
    payload: dict = {
        "modulation": res["modulation"],
        "ebn0_db": round(float(res["ebn0_db"]), 4),
        "n_bits": int(res["n_bits"]),
        "bits_per_symbol": bits_per_symbol(modulation),
        "n_symbols": int(res["n_bits"] // bits_per_symbol(modulation)),
        "theory_ber_awgn": float(res["theory_ber_awgn"]),
        "theory_ber_rayleigh": float(res["theory_ber_rayleigh"]),
        "ideal_constellation": {
            "i": [round(float(z.real), 5) for z in ref],
            "q": [round(float(z.imag), 5) for z in ref],
            "labels": labels,
        },
    }
    for ch in ("awgn", "rayleigh"):
        smp = res[f"samples_{ch}"]
        payload[f"mc_ber_{ch}"] = float(res[f"mc_ber_{ch}"])
        payload[f"mc_errors_{ch}"] = int(res[f"mc_errors_{ch}"])
        payload[f"ci_low_{ch}"] = (
            None if res[f"ci_low_{ch}"] is None else float(res[f"ci_low_{ch}"])
        )
        payload[f"ci_high_{ch}"] = (
            None if res[f"ci_high_{ch}"] is None else float(res[f"ci_high_{ch}"])
        )
        payload[f"n_samples_{ch}"] = int(smp.size)
        payload[f"samples_{ch}"] = {
            "i": [round(float(v), 5) for v in smp.real],
            "q": [round(float(v), 5) for v in smp.imag],
        }
    return payload


def _build_radial_rings(curves_df: pd.DataFrame, freq_mhz: float, scenario: str) -> list[dict]:
    g = curves_df[(curves_df.freq_mhz == freq_mhz) & (curves_df.scenario == scenario)].sort_values(
        "distance_km"
    )
    labels = np.where(g.median_feasible, g.median_modulation, "Outage").tolist()
    d = g.distance_km.to_numpy()
    rmax = float(CFG.distance_max_km)
    rings: list[dict] = []
    start = 0
    for i in range(1, len(labels) + 1):
        if i == len(labels) or labels[i] != labels[start]:
            inner = 0.0 if start == 0 else float(d[start]) - 0.125
            outer = min(rmax, float(d[i - 1]) + 0.125)
            rings.append(
                {
                    "inner_km": round(inner, 4),
                    "outer_km": round(outer, 4),
                    "modulation": labels[start],
                }
            )
            start = i
    return rings


def _serialize_strategy_rows(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        cond_ber = r["fading_cond_ber_mean"]
        rows.append(
            {
                "scenario": str(r["scenario"]),
                "label": SCENARIOS[str(r["scenario"])]["label"],
                "median_config": (
                    f"{r['median_modulation']} x {int(r['median_n_rb'])} RB"
                    if bool(r["median_feasible"])
                    else "Outage"
                ),
                "median_rate_mbps": round(float(r["median_rate_bps"]) / 1e6, 2),
                "shadow_outage_prob": float(r["shadow_outage_prob"]),
                "shadow_outage_pct": round(float(r["shadow_outage_prob"]) * 100.0, 1),
                "fading_outage_prob": float(r["fading_outage_prob"]),
                "fading_outage_pct": round(float(r["fading_outage_prob"]) * 100.0, 1),
                "fading_effective_rate_mbps": round(float(r["fading_effective_rate_bps"]) / 1e6, 2),
                "fading_cond_ber_mean": None if pd.isna(cond_ber) else float(cond_ber),
            }
        )
    return rows


app = FastAPI(
    title="RuralLink Scientific API",
    description="FastAPI layer over validated RuralLink Python simulation engine (src/).",
    version="1.0.0",
)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "project": PROJECT_NAME,
        "title": RESEARCH_TITLE,
        "team": list(TEAM_MEMBERS),
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.post("/api/operating-point")
def api_operating_point(req: WorkbenchRequest) -> dict:
    try:
        thr = _thresholds(req.ber_target)
        active = evaluate_link(
            float(req.freq_mhz),
            req.env,
            req.dist_km,
            req.tx_power_dbm,
            req.shadow,
            req.strategy,
            req.rb_manual,
            req.mod_manual,
            req.ber_target,
        )
        baseline_s0 = evaluate_link(
            float(req.freq_mhz),
            req.env,
            req.dist_km,
            req.tx_power_dbm,
            req.shadow,
            "S0",
            req.rb_manual,
            req.mod_manual,
            req.ber_target,
        )
        by_freq = []
        for f in FREQ_OPTIONS:
            lk_strat = evaluate_link(
                f,
                req.env,
                req.dist_km,
                req.tx_power_dbm,
                req.shadow,
                req.strategy,
                req.rb_manual,
                req.mod_manual,
                req.ber_target,
            )
            lk_s3 = evaluate_link(
                f,
                req.env,
                req.dist_km,
                req.tx_power_dbm,
                req.shadow,
                "S3",
                req.rb_manual,
                req.mod_manual,
                req.ber_target,
            )
            snr_25 = float(
                compute_link_budget(lk_s3["pl_db"], n_rb=25, tx_power_dbm=req.tx_power_dbm).snr_db
            )
            snr_1 = float(
                compute_link_budget(lk_s3["pl_db"], n_rb=1, tx_power_dbm=req.tx_power_dbm).snr_db
            )
            by_freq.append(
                {
                    "freq_mhz": int(f),
                    "pl_db": round(lk_s3["pl_db"], 2),
                    "snr_25rb_db": round(snr_25, 2),
                    "snr_1rb_db": round(snr_1, 2),
                    "active": lk_strat,
                    "s3": lk_s3,
                }
            )

        offset = active["margin_db"]
        snr_curves: dict[str, dict[str, list[float]]] = {}
        for f in FREQ_OPTIONS:
            pl_d = np.asarray(median_path_loss_db(DISTANCES_KM * 1000.0, f, req.env)) + offset
            snr_1 = np.atleast_1d(
                compute_link_budget(pl_d, n_rb=1, tx_power_dbm=req.tx_power_dbm).snr_db
            )
            snr_25 = np.atleast_1d(
                compute_link_budget(pl_d, n_rb=25, tx_power_dbm=req.tx_power_dbm).snr_db
            )
            entry = {
                "rb_1": [round(float(x), 3) for x in snr_1],
                "rb_25": [round(float(x), 3) for x in snr_25],
            }
            if int(f) == req.freq_mhz and active["rb"] not in (1, 25):
                snr_act = np.atleast_1d(
                    compute_link_budget(
                        pl_d, n_rb=active["rb"], tx_power_dbm=req.tx_power_dbm
                    ).snr_db
                )
                entry["rb_active"] = [round(float(x), 3) for x in snr_act]
            snr_curves[str(int(f))] = entry

        return {
            "active": active,
            "baseline_s0": baseline_s0,
            "by_freq": by_freq,
            "thresholds": thr,
            "distances_km": [float(d) for d in DISTANCES_KM],
            "snr_curves": snr_curves,
            "is_exploratory": bool(
                req.freq_mhz == 700 or not math.isclose(req.ber_target, CFG.ber_target)
            ),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/stochastic-analysis")
def api_stochastic_analysis(req: StochasticRequest) -> dict:
    try:
        check_tx_power(req.tx_power_dbm, CFG)
        cfg = _make_config(req.ber_target)
        zones = []
        freq_summary_s3 = []
        active_curves_df: pd.DataFrame | None = None

        for f in FREQ_OPTIONS:
            curves_df, summary_df = _cached_freq_curves(
                f, req.env, float(req.tx_power_dbm), float(req.ber_target)
            )
            if int(f) == req.freq_mhz:
                active_curves_df = curves_df

            if req.include_zones:
                srow_z = summary_df[
                    (summary_df.freq_mhz == f) & (summary_df.scenario == req.zone_strategy)
                ].iloc[0]
                zones.append(
                    {
                        "freq_mhz": int(f),
                        "scenario": req.zone_strategy,
                        "rings": _build_radial_rings(curves_df, f, req.zone_strategy),
                        "radius_median_km": float(srow_z["radius_median_km"]),
                        "radius_median_label": str(srow_z["radius_median_label"]),
                        "radius_stochastic_km": float(srow_z["radius_stochastic_km"]),
                        "radius_stochastic_label": str(srow_z["radius_stochastic_label"]),
                        "radius_fading_km": float(srow_z["radius_fading_km"]),
                        "radius_fading_label": str(srow_z["radius_fading_label"]),
                    }
                )
            srow_s3 = summary_df[(summary_df.freq_mhz == f) & (summary_df.scenario == "S3")].iloc[0]
            freq_summary_s3.append(
                {
                    "freq_mhz": int(f),
                    "radius_median_label": str(srow_s3["radius_median_label"]),
                    "radius_stochastic_label": str(srow_s3["radius_stochastic_label"]),
                    "radius_fading_label": str(srow_s3["radius_fading_label"]),
                }
            )

        assert active_curves_df is not None
        matched = active_curves_df[np.isclose(active_curves_df.distance_km, req.dist_km)]
        if matched.empty:
            matched = evaluate_scenario_curves(
                float(req.freq_mhz),
                req.env,
                np.array([req.dist_km], dtype=float),
                tuple(SCENARIOS),
                float(req.tx_power_dbm),
                N_DRAWS,
                cfg.default_seed,
                cfg,
            )

        strategy_rows = _serialize_strategy_rows(matched)
        active_outage = None
        if req.active_strategy != "MANUAL":
            for row in strategy_rows:
                if row["scenario"] == req.active_strategy:
                    active_outage = {
                        "shadow_outage_prob": row["shadow_outage_prob"],
                        "fading_outage_prob": row["fading_outage_prob"],
                        "fading_effective_rate_mbps": row["fading_effective_rate_mbps"],
                        "fading_cond_ber_mean": row["fading_cond_ber_mean"],
                    }
                    break

        return {
            "n_draws": N_DRAWS,
            "seed": cfg.default_seed,
            "outage_target": cfg.outage_target,
            "active_outage": active_outage,
            "zones": zones if req.include_zones else None,
            "strategy_comparison": strategy_rows,
            "freq_summary_s3": freq_summary_s3,
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/monte-carlo")
def api_monte_carlo(req: MonteCarloRequest) -> dict:
    try:
        active = evaluate_link(
            float(req.freq_mhz),
            req.env,
            req.dist_km,
            req.tx_power_dbm,
            req.shadow,
            req.strategy,
            req.rb_manual,
            req.mod_manual,
            req.ber_target,
        )
        if not active["ok"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Konfigurasi aktif sedang outage; tidak ada transmisi yang dapat disimulasikan."
                ),
            )

        base_s0 = evaluate_link(
            float(req.freq_mhz),
            req.env,
            req.dist_km,
            req.tx_power_dbm,
            req.shadow,
            "S0",
            req.rb_manual,
            req.mod_manual,
            req.ber_target,
        )

        opt_bits = align_mc_bits(req.n_bits, active["mod"])
        opt_mc = _cached_mc(active["mod"], round(float(active["ebn0_db"]), 6), opt_bits)

        base_mc = None
        if base_s0["ok"]:
            base_bits = align_mc_bits(req.n_bits, base_s0["mod"])
            base_mc = _cached_mc(base_s0["mod"], round(float(base_s0["ebn0_db"]), 6), base_bits)

        by_freq: dict[str, dict | None] = {}
        if req.mode in ("all", "by_freq"):
            freq_strat = "S3" if req.strategy == "MANUAL" else req.strategy
            for f in FREQ_OPTIONS:
                lk_f = evaluate_link(
                    f,
                    req.env,
                    req.dist_km,
                    req.tx_power_dbm,
                    req.shadow,
                    freq_strat,
                    req.rb_manual,
                    req.mod_manual,
                    req.ber_target,
                )
                if lk_f["ok"]:
                    f_bits = align_mc_bits(req.n_bits, lk_f["mod"])
                    by_freq[str(int(f))] = _cached_mc(
                        lk_f["mod"], round(float(lk_f["ebn0_db"]), 6), f_bits
                    )
                else:
                    by_freq[str(int(f))] = None

        return {
            "requested_bits": req.n_bits,
            "is_preview": req.is_preview,
            "mode": req.mode,
            "seed": CFG.default_seed,
            "opt": opt_mc,
            "base": base_mc,
            "by_freq": by_freq,
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/results")
def api_results() -> dict:
    curves_path = RES_DIR / "adaptive_coverage_curves.csv"
    summary_path = RES_DIR / "adaptive_coverage_summary.csv"
    cmp_path = RES_DIR / "adaptive_strategy_comparison.csv"
    mc_path = RES_DIR / "adaptive_mc_validation.csv"
    summary_md_path = ROOT / "outputs" / "summary.md"

    if not curves_path.exists() or not summary_path.exists():
        raise HTTPException(status_code=404, detail="Published CSV results not found.")

    curves_df = pd.read_csv(curves_path)
    summary_df = pd.read_csv(summary_path)
    cmp_df = pd.read_csv(cmp_path) if cmp_path.exists() else pd.DataFrame()
    mc_df = pd.read_csv(mc_path) if mc_path.exists() else pd.DataFrame()

    csv_files = sorted(p.name for p in RES_DIR.glob("*.csv") if p.name in ALLOWED_RESULT_CSVS)
    png_files = [
        {
            "filename": name,
            "title": name.replace(".png", "").replace("_", " ").title(),
            "url": f"/api/outputs/figures/{name}",
        }
        for name in (
            "adaptive_coverage_radius.png",
            "adaptive_rate_vs_distance.png",
            "path_loss_vs_distance.png",
            "uplink_snr_vs_distance.png",
            "ber_awgn_validation.png",
            "ber_rayleigh_validation.png",
        )
        if (FIG_DIR / name).exists()
    ]

    findings = []
    if not cmp_df.empty:
        for f in CFG.carrier_frequencies_mhz:
            q = cmp_df[
                (cmp_df.freq_mhz == f)
                & (cmp_df.environment == "NLOS")
                & (cmp_df.distance_km == 2.0)
            ].set_index("scenario")
            if {"S0", "S3"} <= set(q.index):
                findings.append(
                    {
                        "freq_mhz": int(f),
                        "s0_outage_pct": round(float(q.loc["S0", "fading_outage_prob"]) * 100, 1),
                        "s0_rate_mbps": round(
                            float(q.loc["S0", "fading_effective_rate_bps"]) / 1e6, 2
                        ),
                        "s3_outage_pct": round(float(q.loc["S3", "fading_outage_prob"]) * 100, 1),
                        "s3_rate_mbps": round(
                            float(q.loc["S3", "fading_effective_rate_bps"]) / 1e6, 2
                        ),
                    }
                )

    return {
        "outage_target": CFG.outage_target,
        "curves": curves_df[
            [
                "freq_mhz",
                "environment",
                "scenario",
                "distance_km",
                "fading_outage_prob",
                "fading_effective_rate_bps",
            ]
        ].to_dict(orient="records"),
        "summary": summary_df[
            [
                "freq_mhz",
                "environment",
                "scenario",
                "label",
                "radius_median_label",
                "radius_stochastic_label",
                "radius_fading_label",
            ]
        ].to_dict(orient="records"),
        "mc_validation": mc_df.round(6).to_dict(orient="records") if not mc_df.empty else [],
        "findings_nlos_2km": findings,
        "figures": png_files,
        "csv_files": [{"filename": f, "url": f"/api/outputs/results/{f}"} for f in csv_files],
        "summary_md": summary_md_path.read_text(encoding="utf-8")
        if summary_md_path.exists()
        else "",
    }


@app.get("/api/outputs/figures/{filename}")
def api_get_figure(filename: str) -> FileResponse:
    if filename not in ALLOWED_RESULT_PNGS:
        raise HTTPException(status_code=404, detail="Figure not found.")
    target = FIG_DIR / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="Figure file missing.")
    return FileResponse(target, media_type="image/png", filename=filename)


@app.get("/api/outputs/results/{filename}")
def api_get_csv(filename: str) -> FileResponse:
    if filename not in ALLOWED_RESULT_CSVS:
        raise HTTPException(status_code=404, detail="CSV file not found.")
    target = RES_DIR / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="CSV file missing.")
    return FileResponse(target, media_type="text/csv; charset=utf-8", filename=filename)


@app.get("/api/methodology")
def api_methodology() -> dict:
    los_n, los_s = get_ci_parameters("LOS")
    nlos_n, nlos_s = get_ci_parameters("NLOS")
    return {
        "config": {
            "carrier_frequencies_mhz": list(CFG.carrier_frequencies_mhz),
            "nominal_channel_bandwidth_mhz": CFG.nominal_channel_bandwidth_hz / 1e6,
            "active_rb_choices": list(CFG.active_rb_choices),
            "rb_bandwidth_khz": CFG.rb_bandwidth_hz / 1e3,
            "ue_tx_power_dbm": CFG.ue_tx_power_dbm,
            "ue_antenna_gain_dbi": CFG.ue_antenna_gain_dbi,
            "bts_rx_antenna_gain_dbi": CFG.bts_rx_antenna_gain_dbi,
            "feeder_loss_db": CFG.feeder_loss_db,
            "body_loss_db": CFG.body_loss_db,
            "rx_noise_figure_db": CFG.rx_noise_figure_db,
            "thermal_noise_density_dbm_hz": CFG.thermal_noise_density_dbm_hz,
            "distance_min_km": CFG.distance_min_km,
            "distance_max_km": CFG.distance_max_km,
            "outage_target": CFG.outage_target,
            "default_seed": CFG.default_seed,
        },
        "ci_parameters": {
            "LOS": {"n": los_n, "sigma_db": los_s},
            "NLOS": {"n": nlos_n, "sigma_db": nlos_s},
        },
        "thresholds": {
            "1e-2": _thresholds(1e-2),
            "1e-3": _thresholds(1e-3),
        },
        "strategies": [{"code": k, "label": v["label"]} for k, v in SCENARIOS.items()],
        "team": list(TEAM_MEMBERS),
    }


@app.get("/api/glossary")
def api_glossary(
    q: str = Query(default="", max_length=120),
    category: str = Query(default="Semua kategori", max_length=120),
) -> dict:
    entries = GLOSSARY_ENTRIES
    if category and category != "Semua kategori":
        entries = tuple(e for e in entries if e.kategori == category)
    query = q.strip().lower()
    if query:
        entries = tuple(
            e
            for e in entries
            if query in e.istilah.lower()
            or query in e.kepanjangan.lower()
            or query in e.penjelasan.lower()
            or query in e.persamaan.lower()
            or query in e.kategori.lower()
        )
    return {
        "total_count": len(GLOSSARY_ENTRIES),
        "filtered_count": len(entries),
        "categories": list(GLOSSARY_CATEGORIES),
        "entries": [
            {
                "kategori": e.kategori,
                "istilah": e.istilah,
                "kepanjangan": e.kepanjangan,
                "penjelasan": e.penjelasan,
                "persamaan": e.persamaan,
            }
            for e in entries
        ],
    }


@app.get("/api/glossary/csv")
def api_glossary_csv() -> Response:
    return Response(
        content=glossary_csv_bytes(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="rurallink_ensiklopedia.csv"'},
    )


if PUBLIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="static")
