"""Joint adaptive modulation-bandwidth allocation (Phase 04).

Selection rule (THEORETICAL): for each (modulation, N_RB) option the link is feasible when the
uplink Eb/N0 at that N_RB reaches the exact AWGN threshold for BER = ber_target. The optimizer
picks the feasible option with the highest nominal rate B_active * log2(M). Switching uses the
slowly varying (path loss + shadowing) SNR only; the Rayleigh average BER is never used as a
switching criterion. Fast fading is validated separately with bit-level Monte Carlo.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import DEFAULT_CONFIG, SimulationConfig
from src.link_budget import active_bandwidth_hz, compute_link_budget, nominal_data_rate_bps
from src.metrics import simulate_ber_point
from src.modulation import (
    bits_per_symbol,
    derive_switching_thresholds,
    theoretical_ber_awgn,
    theoretical_ber_rayleigh,
)
from src.propagation import analytical_shadow_margin_db, get_ci_parameters, median_path_loss_db

SCENARIOS: dict[str, dict] = {
    "S0": {"label": "Fixed QPSK, fixed 25 RB", "adapt_mod": False, "adapt_rb": False},
    "S1": {"label": "Adaptive modulation, 25 RB", "adapt_mod": True, "adapt_rb": False},
    "S2": {"label": "Adaptive bandwidth, QPSK", "adapt_mod": False, "adapt_rb": True},
    "S3": {"label": "Joint adaptive", "adapt_mod": True, "adapt_rb": True},
}
BASELINE_MOD = "QPSK"


def check_tx_power(tx_power_dbm: float, cfg: SimulationConfig = DEFAULT_CONFIG) -> float:
    """Reject UE power above the approved maximum (cfg.ue_tx_power_dbm = 23 dBm)."""
    if tx_power_dbm > cfg.ue_tx_power_dbm + 1e-9:
        raise ValueError(
            f"UE power {tx_power_dbm} dBm exceeds the {cfg.ue_tx_power_dbm} dBm maximum."
        )
    return float(tx_power_dbm)


def scenario_options(
    scenario: str, cfg: SimulationConfig = DEFAULT_CONFIG
) -> list[tuple[str, int]]:
    """List of (modulation, N_RB) options available to a scenario."""
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario {scenario!r}.")
    spec = SCENARIOS[scenario]
    mods = cfg.modulations if spec["adapt_mod"] else (BASELINE_MOD,)
    rbs = (
        tuple(sorted(cfg.active_rb_choices)) if spec["adapt_rb"] else (max(cfg.active_rb_choices),)
    )
    return [(m, rb) for rb in rbs for m in mods]


@dataclass(frozen=True)
class Selection:
    """Vectorized selection result; index -1 means outage (no feasible option)."""

    options: list[tuple[str, int]]
    index: np.ndarray
    rate_bps: np.ndarray
    ebn0_margin_db: np.ndarray


def select_operating_point(
    path_loss_db: float | np.ndarray,
    scenario: str = "S3",
    tx_power_dbm: float = DEFAULT_CONFIG.ue_tx_power_dbm,
    cfg: SimulationConfig = DEFAULT_CONFIG,
    thresholds: dict[str, dict[str, float]] | None = None,
) -> Selection:
    """Pick the max-rate feasible (modulation, N_RB) for each path-loss value."""
    check_tx_power(tx_power_dbm, cfg)
    thr = thresholds or derive_switching_thresholds(cfg.ber_target, cfg.modulations)
    pl = np.atleast_1d(np.asarray(path_loss_db, dtype=float))
    options = scenario_options(scenario, cfg)
    rates = np.zeros((len(options), pl.size))
    margins = np.full((len(options), pl.size), -np.inf)
    snr_cache: dict[int, np.ndarray] = {}
    for i, (mod, rb) in enumerate(options):
        if rb not in snr_cache:
            snr_cache[rb] = np.atleast_1d(
                compute_link_budget(pl, n_rb=rb, tx_power_dbm=tx_power_dbm).snr_db
            )
        ebn0_db = snr_cache[rb] - 10.0 * np.log10(bits_per_symbol(mod))
        margins[i] = ebn0_db - thr[mod]["ebn0_db"]
        rate = nominal_data_rate_bps(active_bandwidth_hz(rb, cfg.rb_bandwidth_hz), mod)
        rates[i] = np.where(margins[i] >= 0.0, rate, 0.0)
    best = np.argmax(rates, axis=0)
    cols = np.arange(pl.size)
    best_rate = rates[best, cols]
    index = np.where(best_rate > 0.0, best, -1)
    return Selection(
        options=options,
        index=index,
        rate_bps=best_rate,
        ebn0_margin_db=np.where(index >= 0, margins[best, cols], np.nan),
    )


def coverage_radius_km(distance_km: np.ndarray, ok: np.ndarray) -> tuple[float, bool]:
    """Largest distance reached with unbroken coverage from the first grid point.

    Returns (radius_km, censored). censored=True means the grid end was reached, so the real
    radius is at least this value. A radius of 0.0 means the first grid point is not covered.
    """
    ok = np.asarray(ok, dtype=bool)
    if not ok[0]:
        return 0.0, False
    bad = np.flatnonzero(~ok)
    if bad.size == 0:
        return float(distance_km[-1]), True
    return float(distance_km[bad[0] - 1]), False


def evaluate_scenario_curves(
    freq_mhz: float,
    environment: str,
    distance_km: np.ndarray,
    scenarios: tuple[str, ...] = tuple(SCENARIOS),
    tx_power_dbm: float = DEFAULT_CONFIG.ue_tx_power_dbm,
    n_draws: int = 2000,
    seed: int = DEFAULT_CONFIG.default_seed,
    cfg: SimulationConfig = DEFAULT_CONFIG,
) -> pd.DataFrame:
    """Deterministic (median) and stochastic (shadowing Monte Carlo) curves per scenario.

    SIMULATED columns: shadow_* (zero-mean Gaussian shadowing draws in dB, seeded).
    THEORETICAL columns: median_* (X_sigma = 0) and margin95_* (analytic 95 % shadow margin).
    """
    check_tx_power(tx_power_dbm, cfg)
    thr = derive_switching_thresholds(cfg.ber_target, cfg.modulations)
    _, sigma = get_ci_parameters(environment)
    margin = analytical_shadow_margin_db(sigma, 1.0 - cfg.outage_target)
    d = np.asarray(distance_km, dtype=float)
    pl_med = np.asarray(median_path_loss_db(d * 1000.0, freq_mhz, environment), dtype=float)
    rng = np.random.default_rng(seed)
    shadow = rng.normal(0.0, sigma, size=(d.size, n_draws))
    rows = []
    for sc in scenarios:
        sel_med = select_operating_point(pl_med, sc, tx_power_dbm, cfg, thr)
        sel_mar = select_operating_point(pl_med + margin, sc, tx_power_dbm, cfg, thr)
        sel_shd = select_operating_point(
            (pl_med[:, None] + shadow).ravel(), sc, tx_power_dbm, cfg, thr
        )
        shd_rate = sel_shd.rate_bps.reshape(d.size, n_draws)
        for j, dist in enumerate(d):
            idx = sel_med.index[j]
            mod, rb = sel_med.options[idx] if idx >= 0 else ("none", 0)
            rows.append(
                {
                    "freq_mhz": freq_mhz,
                    "environment": environment,
                    "scenario": sc,
                    "distance_km": float(dist),
                    "path_loss_median_db": float(pl_med[j]),
                    "median_feasible": bool(idx >= 0),
                    "median_rate_bps": float(sel_med.rate_bps[j]),
                    "median_modulation": mod,
                    "median_n_rb": int(rb),
                    "margin95_feasible": bool(sel_mar.index[j] >= 0),
                    "margin95_rate_bps": float(sel_mar.rate_bps[j]),
                    "shadow_outage_prob": float(np.mean(shd_rate[j] == 0.0)),
                    "shadow_mean_rate_bps": float(np.mean(shd_rate[j])),
                }
            )
    return pd.DataFrame(rows)


def summarize_coverage(
    curves: pd.DataFrame, cfg: SimulationConfig = DEFAULT_CONFIG
) -> pd.DataFrame:
    """Coverage radii per (freq, environment, scenario): median, 95 % margin, stochastic."""
    out = []
    for (f, env, sc), g in curves.groupby(["freq_mhz", "environment", "scenario"], sort=False):
        g = g.sort_values("distance_km")
        d = g["distance_km"].to_numpy()
        r_med, c_med = coverage_radius_km(d, g["median_feasible"].to_numpy())
        r_mar, c_mar = coverage_radius_km(d, g["margin95_feasible"].to_numpy())
        r_sto, c_sto = coverage_radius_km(
            d, (g["shadow_outage_prob"] <= cfg.outage_target).to_numpy()
        )
        out.append(
            {
                "freq_mhz": f,
                "environment": env,
                "scenario": sc,
                "label": SCENARIOS[sc]["label"],
                "radius_median_km": r_med,
                "radius_margin95_km": r_mar,
                "radius_stochastic_km": r_sto,
                "censored_at_grid_end": bool(c_med or c_mar or c_sto),
            }
        )
    return pd.DataFrame(out)


def rayleigh_outage_probability(avg_ebn0_linear: float, threshold_ebn0_linear: float) -> float:
    """THEORETICAL P(instantaneous Eb/N0 < threshold) for unit-mean exponential Rayleigh power."""
    if avg_ebn0_linear <= 0.0:
        return 1.0
    return float(1.0 - np.exp(-threshold_ebn0_linear / avg_ebn0_linear))


def validate_operating_point(
    modulation: str,
    ebn0_db: float,
    n_bits: int,
    seed: int = DEFAULT_CONFIG.default_seed,
    constellation_sample_size: int = 400,
) -> dict:
    """Bit-level Monte Carlo at an operating point, AWGN and independent Rayleigh (SIMULATED).

    Constellation samples are the equalized received symbols produced by the engine.
    """
    ebn0_lin = 10.0 ** (ebn0_db / 10.0)
    out: dict = {
        "modulation": modulation,
        "ebn0_db": float(ebn0_db),
        "n_bits": int(n_bits),
        "theory_ber_awgn": float(theoretical_ber_awgn(ebn0_lin, modulation)),
        "theory_ber_rayleigh": float(theoretical_ber_rayleigh(ebn0_lin, modulation)),
    }
    for ch in ("AWGN", "RAYLEIGH"):
        m, samples = simulate_ber_point(
            modulation,
            ebn0_db,
            n_bits,
            channel_type=ch,
            seed=seed,
            constellation_sample_size=constellation_sample_size,
        )
        key = ch.lower()
        out[f"mc_ber_{key}"] = m.ber
        out[f"mc_errors_{key}"] = m.n_bit_errors
        out[f"ci_low_{key}"] = m.ci_lower
        out[f"ci_high_{key}"] = m.ci_upper
        out[f"samples_{key}"] = samples
    return out
