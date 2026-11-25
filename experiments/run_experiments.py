"""Scientific smoke experiment entrypoint for RuralLink Phase 02–03.

Generates:
  outputs/figures/path_loss_vs_distance.png
  outputs/figures/uplink_snr_vs_distance.png
  outputs/figures/ber_awgn_validation.png
  outputs/figures/ber_rayleigh_validation.png
  outputs/results/link_budget_validation.csv
  outputs/results/ber_validation.csv
  outputs/results/modulation_thresholds.csv

Data labels:  THEORETICAL (closed-form) or SIMULATED (Monte Carlo, bit-level).
Run: .venv\\Scripts\\python.exe experiments/run_experiments.py
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import DEFAULT_CONFIG, MODULATION_ORDERS, MODULATIONS
from src.link_budget import (
    compute_link_budget,
    nominal_data_rate_bps,
    rb_snr_gain_db,
)
from src.metrics import simulate_ber_point
from src.modulation import (
    derive_switching_thresholds,
    theoretical_ber_awgn,
    theoretical_ber_rayleigh,
)
from src.propagation import (
    analytical_shadow_margin_db,
    get_ci_parameters,
    median_path_loss_db,
)

# Output directories
FIG_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "figures")
RES_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "results")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)

SEED = DEFAULT_CONFIG.default_seed
N_BITS_QUICK = DEFAULT_CONFIG.quick_n_bits  # 100,000
FREQS_MHZ = list(DEFAULT_CONFIG.carrier_frequencies_mhz)
ENV = "NLOS"

MODULATION_COLORS = {
    "BPSK": "#1f77b4",
    "QPSK": "#ff7f0e",
    "16-QAM": "#2ca02c",
    "64-QAM": "#d62728",
}
MODULATION_MARKERS = {"BPSK": "o", "QPSK": "s", "16-QAM": "^", "64-QAM": "D"}

# ---------------------------------------------------------------------------
# FIGURE 1 — Path loss vs distance
# ---------------------------------------------------------------------------


def run_path_loss(distances_km: np.ndarray) -> None:
    print("  [1/4] Path loss vs distance...")
    distances_m = distances_km * 1e3
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)

    for ax, f_mhz in zip(axes, FREQS_MHZ, strict=False):
        for env, ls in [("LOS", "-"), ("NLOS", "--")]:
            n_exp, sigma = get_ci_parameters(env)
            pl_median = median_path_loss_db(distances_m, f_mhz, env)
            margin = analytical_shadow_margin_db(sigma, 0.95)
            pl_95 = pl_median + margin

            ax.plot(distances_km, pl_median, ls=ls, lw=2.0, label=f"{env} Median (n={n_exp})")
            ax.plot(
                distances_km,
                pl_95,
                ls=ls,
                lw=1.0,
                alpha=0.5,
                label=f"{env} 95% Margin (+{margin:.1f} dB)",
            )

        ax.set_title(
            f"CI Path Loss — {f_mhz:.0f} MHz\n"
            f"(Park 2023 1400 MHz params extrapolated — THEORETICAL)",
            fontsize=10,
        )
        ax.set_xlabel("Distance (km)")
        ax.set_ylabel("Path Loss (dB)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xlim([distances_km[0], distances_km[-1]])

    plt.suptitle(
        "Close-In Rural Path Loss vs Distance\n"
        "Park et al. (2023) n, σ from 1400 MHz; extrapolated to 900/1800 MHz — THEORETICAL",
        fontsize=11,
    )
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, "path_loss_vs_distance.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"    Saved: {out_path}")


# ---------------------------------------------------------------------------
# FIGURE 2 — Uplink SNR vs distance
# ---------------------------------------------------------------------------


def run_snr_vs_distance(
    distances_km: np.ndarray,
) -> pd.DataFrame:
    print("  [2/4] Uplink SNR vs distance...")
    distances_m = distances_km * 1e3
    rows: list[dict] = []

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    rb_configs = [1, 5, 25]
    rb_linestyles = {1: "-", 5: "--", 25: ":"}
    rb_colors = {1: "#1f77b4", 5: "#ff7f0e", 25: "#2ca02c"}

    for ax, f_mhz in zip(axes, FREQS_MHZ, strict=False):
        for n_rb in rb_configs:
            pl = median_path_loss_db(distances_m, f_mhz, ENV)
            lb = compute_link_budget(pl, n_rb=n_rb)
            snr = np.asarray(lb.snr_db)
            ax.plot(
                distances_km,
                snr,
                linestyle=rb_linestyles[n_rb],
                color=rb_colors[n_rb],
                lw=2.0,
                label=f"N_RB={n_rb} ({n_rb * 180:.0f} kHz)",
            )
            for d_km, pl_v, snr_v in zip(  # noqa: B905
                distances_km[::10], pl[::10], snr[::10]
            ):
                rows.append(
                    {
                        "freq_mhz": f_mhz,
                        "n_rb": n_rb,
                        "distance_km": float(d_km),
                        "path_loss_db": float(pl_v),
                        "noise_dbm": float(lb.noise_dbm),
                        "snr_db": float(snr_v),
                        "nominal_rate_mbps": nominal_data_rate_bps(lb.b_active_hz, "BPSK") / 1e6,
                        "data_label": "THEORETICAL",
                    }
                )

        ax.axhline(0, color="gray", lw=0.8, ls=":")
        ax.set_title(f"Uplink SNR — {f_mhz:.0f} MHz (NLOS Median) — THEORETICAL", fontsize=10)
        ax.set_xlabel("Distance (km)")
        ax.set_ylabel("Received SNR (dB)")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim([distances_km[0], distances_km[-1]])

    plt.suptitle(
        "Uplink SNR vs Distance for 3 RB Configurations\n"
        "(NLOS median PL, CI model Park 2023, Yogapratama IV params) — THEORETICAL",
        fontsize=11,
    )
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, "uplink_snr_vs_distance.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"    Saved: {out_path}")

    df = pd.DataFrame(rows)
    csv_path = os.path.join(RES_DIR, "link_budget_validation.csv")
    df.to_csv(csv_path, index=False)
    print(f"    Saved: {csv_path}")
    return df


# ---------------------------------------------------------------------------
# FIGURES 3 & 4 — BER validation (AWGN and Rayleigh)
# ---------------------------------------------------------------------------


def run_ber_validation() -> pd.DataFrame:
    print("  [3–4/4] BER validation (AWGN + Rayleigh)...")

    # Eb/N0 ranges per modulation order (avoid wasting compute at very low BER)
    ebn0_db_ranges: dict[str, np.ndarray] = {
        "BPSK": np.arange(-2, 12, 1.0),
        "QPSK": np.arange(-2, 12, 1.0),
        "16-QAM": np.arange(4, 18, 1.0),
        "64-QAM": np.arange(8, 24, 1.0),
    }

    all_rows: list[dict] = []

    for channel_type, fig_filename in [
        ("AWGN", "ber_awgn_validation.png"),
        ("RAYLEIGH", "ber_rayleigh_validation.png"),
    ]:
        fig, ax = plt.subplots(figsize=(10, 7))
        for mod in MODULATIONS:
            ebn0_db_arr = ebn0_db_ranges[mod]
            ebn0_lin_arr = 10.0 ** (ebn0_db_arr / 10.0)

            # --- Theoretical curves ---
            if channel_type == "AWGN":
                ber_theory = theoretical_ber_awgn(ebn0_lin_arr, mod, method="exact")
            else:
                ber_theory = theoretical_ber_rayleigh(ebn0_lin_arr, mod)

            (line_th,) = ax.semilogy(  # noqa: F841
                ebn0_db_arr,
                ber_theory,
                color=MODULATION_COLORS[mod],
                lw=2.0,
                linestyle="-",
                label=f"{mod} Theory",
            )

            # --- Monte Carlo simulated points ---
            mc_ebn0_db: list[float] = []
            mc_ber: list[float] = []
            mc_ci_lo: list[float] = []
            mc_ci_hi: list[float] = []
            mc_zero_flags: list[bool] = []

            for ebn0_db_pt in ebn0_db_arr:
                metrics, _ = simulate_ber_point(
                    mod,
                    ebn0_db=float(ebn0_db_pt),
                    n_bits=N_BITS_QUICK,
                    channel_type=channel_type,
                    seed=SEED,
                    block_size=1,
                )
                mc_ebn0_db.append(float(ebn0_db_pt))

                if metrics.n_bit_errors == 0:
                    mc_ber.append(float("nan"))  # won't plot zero
                    mc_ci_lo.append(float("nan"))
                    mc_ci_hi.append(float(metrics.ci_upper) if metrics.ci_upper else float("nan"))
                    mc_zero_flags.append(True)
                else:
                    mc_ber.append(metrics.ber)
                    mc_ci_lo.append(metrics.ci_lower or 0.0)
                    mc_ci_hi.append(metrics.ci_upper or metrics.ber)
                    mc_zero_flags.append(False)

                all_rows.append(
                    {
                        "channel": channel_type,
                        "modulation": mod,
                        "ebn0_db": float(ebn0_db_pt),
                        "ebn0_linear": float(10.0 ** (float(ebn0_db_pt) / 10.0)),
                        "n_bits": metrics.n_bits,
                        "n_errors": metrics.n_bit_errors,
                        "ber_simulated": float(metrics.ber)
                        if metrics.n_bit_errors > 0
                        else float("nan"),
                        "ci_lower": float(metrics.ci_lower)
                        if metrics.ci_lower is not None
                        else float("nan"),
                        "ci_upper": float(metrics.ci_upper)
                        if metrics.ci_upper is not None
                        else float("nan"),
                        "zero_errors_upper_bound": str(metrics.is_upper_bound_only),
                        "ber_theoretical": float(
                            theoretical_ber_awgn(
                                10.0 ** (float(ebn0_db_pt) / 10.0), mod, method="exact"
                            )
                            if channel_type == "AWGN"
                            else theoretical_ber_rayleigh(  # noqa: E501
                                10.0 ** (float(ebn0_db_pt) / 10.0), mod
                            )
                        ),
                        "data_label": "SIMULATED (Monte Carlo, bit-level)",
                    }
                )

            mc_arr = np.array(mc_ber, dtype=float)
            mc_ebn0_arr = np.array(mc_ebn0_db, dtype=float)
            ci_lo_arr = np.array(mc_ci_lo, dtype=float)
            ci_hi_arr = np.array(mc_ci_hi, dtype=float)
            zero_arr = np.array(mc_zero_flags, dtype=bool)

            # Plot valid MC points with error bars
            valid = ~np.isnan(mc_arr)
            if np.any(valid):
                yerr_lo = np.maximum(0.0, mc_arr[valid] - ci_lo_arr[valid])
                yerr_hi = np.maximum(0.0, ci_hi_arr[valid] - mc_arr[valid])
                (sc,) = ax.semilogy(  # noqa: F841  # noqa: F841
                    mc_ebn0_arr[valid],
                    mc_arr[valid],
                    linestyle="None",
                    marker=MODULATION_MARKERS[mod],
                    markersize=5,
                    color=MODULATION_COLORS[mod],
                    label=f"{mod} MC",
                )
                ax.errorbar(
                    mc_ebn0_arr[valid],
                    mc_arr[valid],
                    yerr=[yerr_lo, yerr_hi],
                    fmt="None",
                    ecolor=MODULATION_COLORS[mod],
                    alpha=0.5,
                    capsize=3,
                )

            # Plot zero-error points as downward triangles at 95% upper bound
            zero_valid = zero_arr & ~np.isnan(ci_hi_arr)
            if np.any(zero_valid):
                ax.scatter(
                    mc_ebn0_arr[zero_valid],
                    ci_hi_arr[zero_valid],
                    marker="v",
                    s=40,
                    color=MODULATION_COLORS[mod],
                    alpha=0.4,
                    zorder=5,
                    label=f"{mod} 0-error ↓3/N" if np.sum(zero_valid) > 0 else "",
                )

        ax.axhline(1e-2, color="k", lw=0.8, ls="--", alpha=0.5, label="BER target 1e-2")
        ax.set_xlabel("$E_b/N_0$ (dB)", fontsize=12)
        ax.set_ylabel("Bit Error Rate (BER)", fontsize=12)
        ax.set_ylim([1e-6, 0.6])
        ax.set_title(
            f"BER vs Eb/N0 — {channel_type} Channel\n"
            "Solid lines: THEORETICAL (exact Gray-coded)  |  Markers: SIMULATED (Monte Carlo)",
            fontsize=11,
        )
        ax.legend(fontsize=7, ncol=2)
        ax.grid(True, which="both", alpha=0.3)
        plt.tight_layout()
        out_path = os.path.join(FIG_DIR, fig_filename)
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"    Saved: {out_path}")

    df_ber = pd.DataFrame(all_rows)
    csv_path = os.path.join(RES_DIR, "ber_validation.csv")
    df_ber.to_csv(csv_path, index=False)
    print(f"    Saved: {csv_path}")
    return df_ber


# ---------------------------------------------------------------------------
# CSV — Modulation switching thresholds
# ---------------------------------------------------------------------------


def run_threshold_export() -> pd.DataFrame:
    print("  [+] Modulation switching thresholds...")
    thresholds = derive_switching_thresholds(ber_target=DEFAULT_CONFIG.ber_target)
    rows = []
    for mod, t in thresholds.items():
        k = int(np.log2(MODULATION_ORDERS[mod]))
        rows.append(
            {
                "modulation": mod,
                "M": MODULATION_ORDERS[mod],
                "k_bits_per_symbol": k,
                "ebn0_linear_threshold": t["ebn0_linear"],
                "ebn0_db_threshold": t["ebn0_db"],
                "esn0_linear_threshold": t["esn0_linear"],
                "esn0_db_threshold": t["esn0_db"],
                "ber_target": DEFAULT_CONFIG.ber_target,
                "rb_snr_gain_25_to_1_db": rb_snr_gain_db(25, 1),
                "rb_snr_gain_25_to_5_db": rb_snr_gain_db(25, 5),
                "data_label": "THEORETICAL (derived from exact AWGN BER)",
            }
        )
    df_thr = pd.DataFrame(rows)
    csv_path = os.path.join(RES_DIR, "modulation_thresholds.csv")
    df_thr.to_csv(csv_path, index=False)
    print(f"    Saved: {csv_path}")
    return df_thr


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def main() -> None:
    t0 = time.time()
    print("=" * 60)
    print("RuralLink — Phase 02–03 Scientific Smoke Experiments")
    print("=" * 60)

    distances_km = np.linspace(DEFAULT_CONFIG.distance_min_km, DEFAULT_CONFIG.distance_max_km, 200)

    run_path_loss(distances_km)
    df_lb = run_snr_vs_distance(distances_km)
    df_ber = run_ber_validation()
    df_thr = run_threshold_export()

    print()
    print("--- Link Budget Validation Summary (sample) ---")
    print(
        df_lb[["freq_mhz", "n_rb", "distance_km", "snr_db", "noise_dbm"]]
        .head(6)
        .to_string(index=False)
    )

    print()
    print("--- Modulation Switching Thresholds (Eb/N0 at BER=1e-2) ---")
    print(df_thr[["modulation", "ebn0_db_threshold", "esn0_db_threshold"]].to_string(index=False))

    print()
    print("--- BER Validation Sample (AWGN, non-zero errors) ---")
    awgn_nonzero = df_ber[(df_ber.channel == "AWGN") & (df_ber.n_errors > 0)].copy()
    print(
        awgn_nonzero[["modulation", "ebn0_db", "n_errors", "ber_simulated", "ber_theoretical"]]
        .head(8)
        .to_string(index=False)
    )

    elapsed = time.time() - t0
    print(f"\nAll experiments complete in {elapsed:.1f} s.")
    print("=" * 60)


if __name__ == "__main__":
    main()
