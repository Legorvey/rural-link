"""Phase 04 experiments: S0-S3 comparison, shadowing reliability, bit-level MC validation."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from config import DEFAULT_CONFIG  # noqa: E402
from src.adaptive import (  # noqa: E402
    SCENARIOS,
    evaluate_scenario_curves,
    select_operating_point,
    summarize_coverage,
    validate_operating_point,
)
from src.modulation import derive_switching_thresholds  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "outputs" / "results"
FIG = ROOT / "outputs" / "figures"
ENVIRONMENTS = ("LOS", "NLOS")
DISTANCES_KM = np.round(np.arange(1.0, 12.0 + 1e-9, 0.25), 4)


def run(n_bits: int, n_draws: int) -> dict[str, pd.DataFrame]:
    RES.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    cfg = DEFAULT_CONFIG
    curves = pd.concat(
        [
            evaluate_scenario_curves(f, env, DISTANCES_KM, n_draws=n_draws, seed=cfg.default_seed)
            for f in cfg.carrier_frequencies_mhz
            for env in ENVIRONMENTS
        ],
        ignore_index=True,
    )
    summary = summarize_coverage(curves, cfg)
    curves.to_csv(RES / "adaptive_coverage_curves.csv", index=False)
    summary.to_csv(RES / "adaptive_coverage_summary.csv", index=False)

    # Bit-level MC at the S3 operating point at the median-coverage edge of each case.
    thr = derive_switching_thresholds(cfg.ber_target, cfg.modulations)
    mc_rows = []
    for f in cfg.carrier_frequencies_mhz:
        for env in ENVIRONMENTS:
            g = curves[
                (curves.freq_mhz == f)
                & (curves.environment == env)
                & (curves.scenario == "S3")
                & curves.median_feasible
            ]
            for dist in (g.distance_km.min(), g.distance_km.max()):
                r = g[g.distance_km == dist].iloc[0]
                sel = select_operating_point(r.path_loss_median_db, "S3", cfg=cfg)
                ebn0_db = float(sel.ebn0_margin_db[0]) + thr[r.median_modulation]["ebn0_db"]
                v = validate_operating_point(
                    r.median_modulation, ebn0_db, n_bits, seed=cfg.default_seed
                )
                v.pop("samples_awgn")
                v.pop("samples_rayleigh")
                mc_rows.append(
                    {
                        "freq_mhz": f,
                        "environment": env,
                        "distance_km": dist,
                        "n_rb": r.median_n_rb,
                        **v,
                    }
                )
    mc = pd.DataFrame(mc_rows)
    mc.to_csv(RES / "adaptive_mc_validation.csv", index=False)

    # Figure 1: coverage radii (median vs 95 % margin vs stochastic).
    fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharey=True)
    for ax, ((f, env), g) in zip(
        axes.ravel(), summary.groupby(["freq_mhz", "environment"]), strict=False
    ):
        x = np.arange(len(g))
        w = 0.27
        ax.bar(x - w, g.radius_median_km, w, label="Median PL (THEORETICAL)", color="#8aa4b0")
        ax.bar(x, g.radius_margin95_km, w, label="95% margin (THEORETICAL)", color="#2f6f7e")
        ax.bar(x + w, g.radius_stochastic_km, w, label="Outage<=5% (SIMULATED)", color="#c4572a")
        ax.set_xticks(x, g.scenario)
        ax.set_title(f"{f:.0f} MHz {env}")
        ax.set_ylabel("Coverage radius (km)")
    axes[0, 0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "adaptive_coverage_radius.png", dpi=150)
    plt.close(fig)

    # Figure 2: rate vs distance, S0-S3, NLOS.
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, f in zip(axes, cfg.carrier_frequencies_mhz, strict=False):
        for sc in SCENARIOS:
            g = curves[
                (curves.freq_mhz == f) & (curves.environment == "NLOS") & (curves.scenario == sc)
            ]
            ax.step(g.distance_km, g.shadow_mean_rate_bps / 1e6, where="post", label=sc)
        ax.set_title(f"{f:.0f} MHz NLOS, mean rate under shadowing (SIMULATED)")
        ax.set_xlabel("Distance (km)")
    axes[0].set_ylabel("Mean nominal rate (Mbit/s)")
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(FIG / "adaptive_rate_vs_distance.png", dpi=150)
    plt.close(fig)
    return {"curves": curves, "summary": summary, "mc": mc}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--n-bits", type=int, default=DEFAULT_CONFIG.research_n_bits)
    p.add_argument("--n-draws", type=int, default=5000)
    a = p.parse_args()
    out = run(a.n_bits, a.n_draws)
    pd.set_option("display.width", 200)
    print(out["summary"].drop(columns="label").to_string(index=False))
    print(
        out["mc"][
            [
                "freq_mhz",
                "environment",
                "distance_km",
                "modulation",
                "n_rb",
                "ebn0_db",
                "theory_ber_awgn",
                "mc_ber_awgn",
                "mc_ber_rayleigh",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
