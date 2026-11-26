"""RuralLink workbench: Streamlit front end over the validated Python engine.

All numbers, curves and constellation samples come from src/ (no scientific math lives here).
Design direction: light engineering workbench, parameter rail on the left, compact telemetry
strip, one accent (teal) plus one contrast color (amber) for stochastic results.
Antislop dials: ENERGY 1 / RHYTHM 2 / MOTION 1. Teal marks THEORETICAL, amber marks SIMULATED,
so color carries the data-provenance label that AGENTS.md requires.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import DEFAULT_CONFIG, PROJECT_NAME, RESEARCH_TITLE
from src.adaptive import (
    SCENARIOS,
    evaluate_scenario_curves,
    select_operating_point,
    summarize_coverage,
    validate_operating_point,
)
from src.link_budget import compute_link_budget
from src.modulation import derive_switching_thresholds, get_constellation
from src.propagation import median_path_loss_db

CFG = DEFAULT_CONFIG
TEAL, AMBER, INK, GREY = "#0F766E", "#B45309", "#0F172A", "#64748B"
DISTANCES_KM = np.round(np.arange(CFG.distance_min_km, CFG.distance_max_km + 1e-9, 0.25), 4)

st.set_page_config(page_title=PROJECT_NAME, layout="wide")
st.markdown(
    """
<style>
.block-container {padding-top: 1.4rem; max-width: 1400px;}
[data-testid="stMetric"] {background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 4px;
  padding: 0.5rem 0.8rem;}
[data-testid="stMetricLabel"] p {font-size: 0.78rem; color: #475569;}
[data-testid="stMetricValue"] {font-size: 1.25rem; font-variant-numeric: tabular-nums;}
button:focus-visible, [role="radio"]:focus-visible, input:focus-visible {
  outline: 2px solid #2563EB !important; outline-offset: 2px;}
button, [role="tab"], label {cursor: pointer;}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Running engine: path loss, link budget, shadowing draws")
def cached_curves(env: str, tx_dbm: float, n_draws: int, scenarios: tuple[str, ...]):
    parts = [
        evaluate_scenario_curves(
            f,
            env,
            DISTANCES_KM,
            scenarios,
            tx_power_dbm=tx_dbm,
            n_draws=n_draws,
            seed=CFG.default_seed,
        )
        for f in CFG.carrier_frequencies_mhz
    ]
    curves = pd.concat(parts, ignore_index=True)
    return curves, summarize_coverage(curves, CFG)


@st.cache_data(show_spinner="Running bit-level Monte Carlo")
def cached_validation(modulation: str, ebn0_db: float, n_bits: int):
    return validate_operating_point(modulation, ebn0_db, n_bits, seed=CFG.default_seed)


def fmt_rate(bps: float) -> str:
    return "outage" if bps <= 0 else f"{bps / 1e6:.2f} Mbit/s"


# ---------------- left parameter rail ----------------
with st.sidebar:
    st.header("Parameters")
    freq = st.radio(
        "Carrier frequency (MHz)", CFG.carrier_frequencies_mhz, format_func=lambda x: f"{x:.0f}"
    )
    env = st.radio("Propagation", ("LOS", "NLOS"), index=1, horizontal=True)
    tx_dbm = st.slider(
        "UE transmit power (dBm)",
        0.0,
        float(CFG.ue_tx_power_dbm),
        float(CFG.ue_tx_power_dbm),
        1.0,
        help="Capped at the approved 23 dBm maximum.",
    )
    dist = st.slider(
        "Probe distance (km)", float(CFG.distance_min_km), float(CFG.distance_max_km), 5.0, 0.25
    )
    chosen = st.multiselect(
        "Scenarios",
        list(SCENARIOS),
        default=list(SCENARIOS),
        format_func=lambda s: f"{s}: {SCENARIOS[s]['label']}",
    )
    n_draws = st.select_slider("Shadowing draws per distance", (500, 1000, 2000, 5000), value=2000)
    st.caption(
        f"BER target {CFG.ber_target:g}. Outage target {CFG.outage_target:.0%}. "
        "Seed 42. Runs offline."
    )

st.title(PROJECT_NAME)
st.caption(RESEARCH_TITLE)

if not chosen:
    st.info("Select at least one scenario in the left rail to see coverage results.")
    st.stop()

try:
    curves, summary = cached_curves(env, float(tx_dbm), int(n_draws), tuple(chosen))
    thr = derive_switching_thresholds(CFG.ber_target, CFG.modulations)
    pl = float(median_path_loss_db(dist * 1000.0, freq, env))
    sel = select_operating_point(pl, "S3", tx_dbm, CFG, thr)
except ValueError as exc:
    st.error(f"Parameter rejected by the engine: {exc}")
    st.stop()

# ---------------- telemetry strip ----------------
ref_sc = "S3" if "S3" in chosen else chosen[0]
idx = int(sel.index[0])
mod, rb = sel.options[idx] if idx >= 0 else ("none", 0)
snr_full = compute_link_budget(pl, n_rb=max(CFG.active_rb_choices), tx_power_dbm=tx_dbm).snr_db
row = curves[
    (curves.freq_mhz == freq)
    & (curves.environment == env)
    & (curves.scenario == ("S3" if "S3" in chosen else chosen[0]))
    & np.isclose(curves.distance_km, dist)
]
outage = float(row.shadow_outage_prob.iloc[0]) if len(row) else float("nan")
cols = st.columns(6)
cols[0].metric("Path loss, median (THEORETICAL)", f"{pl:.1f} dB")
cols[1].metric("SNR at 25 RB", f"{snr_full:.1f} dB")
cols[2].metric("Joint choice (S3)", f"{mod} x {rb} RB" if idx >= 0 else "none")
cols[3].metric("Nominal rate", fmt_rate(float(sel.rate_bps[0])))
cols[4].metric("Eb/N0 margin", "n/a" if idx < 0 else f"{float(sel.ebn0_margin_db[0]):.1f} dB")
cols[5].metric(
    f"Shadow outage, {row.scenario.iloc[0] if len(row) else '-'} (SIMULATED)", f"{outage:.1%}"
)

tab_cov, tab_op, tab_mc, tab_method = st.tabs(
    ["Coverage zones", "Operating points", "Bit-level validation", "Method and labels"]
)

# ---------------- coverage zones ----------------
with tab_cov:
    s = summary[summary.environment == env]
    left, right = st.columns([1, 1])
    with left:
        st.subheader(f"Coverage radius, {env}")
        fig = go.Figure()
        for f, shade in zip(CFG.carrier_frequencies_mhz, (1.0, 0.55), strict=True):
            g = s[s.freq_mhz == f]
            fig.add_bar(
                y=g.scenario,
                x=g.radius_median_km,
                orientation="h",
                name=f"{f:.0f} MHz median (THEORETICAL)",
                marker_color=TEAL,
                opacity=shade,
            )
            fig.add_bar(
                y=g.scenario,
                x=g.radius_stochastic_km,
                orientation="h",
                name=f"{f:.0f} MHz outage<=5% (SIMULATED)",
                marker_color=AMBER,
                opacity=shade,
            )
        fig.update_layout(
            barmode="group",
            height=420,
            margin=dict(l=10, r=10, t=10, b=10),
            template="plotly_white",
            xaxis_title="Radius (km). Values at 12 km reach the end of the evaluated range.",
            legend=dict(orientation="h", y=-0.28),
            font=dict(color=INK),
        )
        st.plotly_chart(fig, width="stretch")
        st.caption(
            "Median-path-loss coverage is deterministic. It is not a reliability figure: the amber "
            "bars apply seeded log-normal shadowing and require outage of 5% or less."
        )
    with right:
        st.subheader(f"Outage vs distance, {ref_sc}")
        g = curves[(curves.environment == env) & (curves.scenario == ref_sc)]
        fig2 = go.Figure()
        for f, color in zip(CFG.carrier_frequencies_mhz, (TEAL, GREY), strict=True):
            h = g[g.freq_mhz == f]
            fig2.add_scatter(
                x=h.distance_km,
                y=h.shadow_outage_prob * 100,
                name=f"{f:.0f} MHz shadowing",
                line=dict(color=color),
            )
            fig2.add_scatter(
                x=h.distance_km,
                y=h.fading_outage_prob * 100,
                name=f"{f:.0f} MHz shadowing + Rayleigh (CSI)",
                line=dict(color=color, dash="dash"),
            )
        fig2.add_hline(
            y=CFG.outage_target * 100,
            line_dash="dot",
            line_color=AMBER,
            annotation_text="5% target",
        )
        fig2.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=10, b=10),
            template="plotly_white",
            xaxis_title="Distance (km)",
            yaxis_title="Outage (%) (SIMULATED)",
            legend=dict(orientation="h", y=-0.28),
        )
        st.plotly_chart(fig2, width="stretch")
    st.dataframe(
        s[
            [
                "freq_mhz",
                "scenario",
                "radius_median_label",
                "radius_margin95_label",
                "radius_stochastic_label",
                "radius_fading_label",
            ]
        ].rename(
            columns={
                "radius_median_label": "median PL",
                "radius_margin95_label": "95% margin",
                "radius_stochastic_label": "shadowing outage<=5%",
                "radius_fading_label": "shadowing+Rayleigh outage<=5%",
            }
        ),
        hide_index=True,
        width="stretch",
    )

# ---------------- operating points ----------------
with tab_op:
    g = curves[
        (curves.freq_mhz == freq)
        & (curves.environment == env)
        & (curves.scenario == ("S3" if "S3" in chosen else chosen[0]))
    ]
    st.subheader(f"{g.scenario.iloc[0]} choice vs distance at {freq:.0f} MHz {env}")
    fig3 = go.Figure()
    for sc in chosen:
        h = curves[
            (curves.freq_mhz == freq) & (curves.environment == env) & (curves.scenario == sc)
        ]
        fig3.add_scatter(
            x=h.distance_km, y=h.median_rate_bps / 1e6, mode="lines", line_shape="hv", name=sc
        )
    fig3.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        template="plotly_white",
        xaxis_title="Distance (km)",
        yaxis_title="Nominal rate (Mbit/s) (THEORETICAL)",
        legend=dict(orientation="h", y=-0.25),
    )
    st.plotly_chart(fig3, width="stretch")
    st.dataframe(
        g[
            [
                "distance_km",
                "path_loss_median_db",
                "median_modulation",
                "median_n_rb",
                "median_rate_bps",
                "shadow_outage_prob",
            ]
        ],
        hide_index=True,
        width="stretch",
    )
    st.download_button(
        "Download curves (CSV)",
        curves.to_csv(index=False).encode(),
        "adaptive_coverage_curves.csv",
        "text/csv",
    )

# ---------------- bit-level validation ----------------
with tab_mc:
    st.subheader("Bit-level Monte Carlo at the S3 operating point")
    if idx < 0:
        st.info("No feasible operating point at this distance: the probe distance is in outage.")
    else:
        ebn0_db = float(sel.ebn0_margin_db[0]) + thr[mod]["ebn0_db"]
        n_bits = st.select_slider("Bits per channel", (100_000, 500_000, 1_000_000), value=100_000)
        st.write(f"Operating point: **{mod}**, N_RB = {rb}, Eb/N0 = {ebn0_db:.2f} dB.")
        if st.button("Run Monte Carlo transmission"):
            st.session_state["mc"] = cached_validation(mod, ebn0_db, int(n_bits))
        v = st.session_state.get("mc")
        if v is None:
            st.info("Press the button to transmit random bits through the engine channels.")
        else:
            c = st.columns(4)
            c[0].metric("BER theory AWGN", f"{v['theory_ber_awgn']:.2e}")
            c[1].metric("BER MC AWGN (SIMULATED)", f"{v['mc_ber_awgn']:.2e}")
            c[2].metric("BER theory Rayleigh", f"{v['theory_ber_rayleigh']:.2e}")
            c[3].metric("BER MC Rayleigh (SIMULATED)", f"{v['mc_ber_rayleigh']:.2e}")
            st.caption(
                f"{v['modulation']} at Eb/N0 {v['ebn0_db']:.2f} dB, {v['n_bits']:,} bits. "
                "Switching uses the AWGN threshold on slow-varying SNR. Rayleigh BER shows the cost of "
                "fast fading, it is not used to choose the modulation."
            )
            ref, _ = get_constellation(v["modulation"])
            cc = st.columns(2)
            for col, key, title in (
                (cc[0], "samples_awgn", "AWGN"),
                (cc[1], "samples_rayleigh", "Rayleigh, equalized"),
            ):
                sm = v[key]
                f4 = go.Figure()
                f4.add_scatter(
                    x=sm.real,
                    y=sm.imag,
                    mode="markers",
                    marker=dict(size=4, color=AMBER, opacity=0.55),
                    name="received (SIMULATED)",
                )
                f4.add_scatter(
                    x=np.real(ref),
                    y=np.imag(ref),
                    mode="markers",
                    marker=dict(size=8, color=INK, symbol="x"),
                    name="ideal",
                )
                f4.update_layout(
                    height=360,
                    margin=dict(l=10, r=10, t=30, b=10),
                    template="plotly_white",
                    title=title,
                    xaxis_title="I",
                    yaxis_title="Q",
                    yaxis_scaleanchor="x",
                    legend=dict(orientation="h", y=-0.25),
                )
                col.plotly_chart(f4, width="stretch")

# ---------------- method ----------------
with tab_method:
    st.markdown(
        f"""
**Model.** Close-In path loss (Park 2023 LOS/NLOS parameters), noise-limited uplink budget with power
split over active resource blocks, UE power capped at {CFG.ue_tx_power_dbm:.0f} dBm, 900 and 1800 MHz.

**Optimizer.** Each (modulation, N_RB) option is feasible when Eb/N0 reaches the exact AWGN threshold for
BER = {CFG.ber_target:g}. The feasible option with the highest nominal rate B x log2(M) is chosen.
Thresholds (Eb/N0, dB): {", ".join(f"{m} {thr[m]['ebn0_db']:.2f}" for m in CFG.modulations)}.

**Scenarios.** {"; ".join(f"{k} {v['label']}" for k, v in SCENARIOS.items())}.

**Labels.** THEORETICAL (teal): closed-form and median path loss. SIMULATED (amber): shadowing draws and
bit-level Monte Carlo. Rates are nominal and uncoded. No result here is a field measurement.
"""
    )
