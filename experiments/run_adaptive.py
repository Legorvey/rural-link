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
    cmp_d = [2.0, 5.0, 8.0, 12.0]
    comparison = curves[curves.distance_km.isin(cmp_d)][
        [
            "freq_mhz",
            "environment",
            "scenario",
            "distance_km",
            "shadow_outage_prob",
            "shadow_mean_rate_bps",
            "fading_outage_prob",
            "fading_effective_rate_bps",
            "fading_cond_ber_mean",
            "fading_cond_ber_max",
        ]
    ]
    comparison.to_csv(RES / "adaptive_strategy_comparison.csv", index=False)
    write_summary(curves, summary, mc, comparison, n_bits, n_draws)

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


def _mbps(x: float) -> str:
    return f"{x / 1e6:.2f}"


def write_summary(curves, summary, mc, comparison, n_bits: int, n_draws: int) -> None:
    """Write outputs/summary.md from the exported CSV data only."""
    L = [
        "# RuralLink Phase 04-06 numerical summary",
        "",
        f"Generated by `experiments/run_adaptive.py` (seed {DEFAULT_CONFIG.default_seed}, "
        f"{n_draws} shared shadowing and Rayleigh realizations per distance, {n_bits:,} MC bits).",
        "Grid 1-12 km, step 0.25 km. UE power 23 dBm, BER target 1e-2, outage target 5%.",
        "Rates are nominal and uncoded (B x log2 M), averaged over realizations with outage counted as 0.",
        "",
        "## Reading the labels",
        "- `<1 km`: no coverage at the first tested distance. `>=12 km`: right-censored, true radius unknown.",
        "- **Median PL** (THEORETICAL): deterministic, not a reliability figure.",
        "- **Shadowing** (SIMULATED): log-normal shadowing only, outage <= 5%.",
        "- **Shadowing + Rayleigh, instantaneous CSI** (SIMULATED): per realization the link picks the max-rate option "
        "whose Eb/N0 meets the AWGN threshold, then BER is the AWGN BER at that instantaneous Eb/N0 "
        "(conditional BER, at most 1e-2 by construction). Outage means no feasible option.",
        "- S0 fixed QPSK 25 RB, S1 adaptive modulation, S2 adaptive bandwidth (QPSK), S3 joint, "
        "R0 fixed BPSK 1 RB. All scenarios share the same realizations.",
        "",
    ]
    for (f, env), g in summary.groupby(["freq_mhz", "environment"], sort=False):
        L += [
            f"## {f:.0f} MHz {env}: coverage radius",
            "",
            "| Scenario | Median PL | Shadowing | Shadowing + Rayleigh (CSI) |",
            "|---|---|---|---|",
        ]
        for _, r in g.iterrows():
            L.append(
                f"| {r.scenario} {r.label} | {r.radius_median_label} | "
                f"{r.radius_stochastic_label} | {r.radius_fading_label} |"
            )
        L.append("")
    L += [
        "## Outage and effective rate (shadowing + Rayleigh, instantaneous CSI)",
        "",
        "| MHz | Env | Scenario | km | Outage | Effective rate (Mbit/s) | Mean cond. BER |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, r in comparison.sort_values(
        ["freq_mhz", "environment", "distance_km", "scenario"]
    ).iterrows():
        ber = "n/a" if np.isnan(r.fading_cond_ber_mean) else f"{r.fading_cond_ber_mean:.2e}"
        L.append(
            f"| {r.freq_mhz:.0f} | {r.environment} | {r.scenario} | {r.distance_km:g} | "
            f"{r.fading_outage_prob:.1%} | {_mbps(r.fading_effective_rate_bps)} | {ber} |"
        )
    mx = curves.fading_cond_ber_max.max()
    L += [
        "",
        f"Largest conditional BER over all served realizations: {mx:.3e} (target 1e-2).",
        "",
        "## Average Rayleigh BER without CSI versus conditional adaptive BER",
        "",
        "The 4-7% figures reported earlier are bit-level Monte Carlo BERs for a modulation chosen from the "
        "slow SNR and then sent through independent Rayleigh fading with no instantaneous adaptation. "
        "They are average BERs over the whole fading distribution, so they sit far above the AWGN target. "
        "With instantaneous CSI the adaptive link transmits only when the instantaneous Eb/N0 meets the "
        "threshold, so served bits have conditional BER <= 1e-2. The price is outage and lower effective rate.",
        "",
        "| MHz | Env | km | Mod | N_RB | Eb/N0 dB | AWGN theory | AWGN MC | Rayleigh no-CSI MC |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in mc.iterrows():
        L.append(
            f"| {r.freq_mhz:.0f} | {r.environment} | {r.distance_km:g} | {r.modulation} | {r.n_rb} | "
            f"{r.ebn0_db:.2f} | {r.theory_ber_awgn:.2e} | {r.mc_ber_awgn:.2e} | {r.mc_ber_rayleigh:.2e} |"
        )
    (ROOT / "outputs" / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")


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
