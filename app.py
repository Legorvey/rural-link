"""RuralLink: workbench interaktif Streamlit di atas mesin Python tervalidasi (src/).

Design Read (Antislop): instrumen riset telekomunikasi satu halaman untuk proyeksi kelas,
bahasa visual workbench teknik terang (terinspirasi prototypes/dashboard_rurallink.html),
dial ENERGY 1 / RHYTHM 2 / MOTION 1.
Alasan desain (R-31):
- Palet: latar terang (#F4F6F9), panel putih berbatas (#CBD5E1), navy (#0F2A47) untuk judul
  dan data analitis (THEORETICAL), teal (#0F766E) sebagai aksen tunggal, amber (#B45309) untuk
  hasil simulasi (SIMULATED) serta penanda jarak aktif, dan merah gelap (#9A1B1B) untuk outage.
- Rail parameter kiri + telemetry strip horizontal + seluruh visualisasi utama dalam satu tab
  agar presenter dapat membandingkan SNR, konstelasi nyata, zona radial, dan tabel strategi
  tanpa berpindah tab.
- Font sistem saja: tanpa aset jaringan, aman untuk mode offline.
Seluruh angka, kurva, zona, dan sampel konstelasi berasal dari src/.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from config import DEFAULT_CONFIG, PROJECT_NAME, RESEARCH_TITLE, SimulationConfig
from src.adaptive import (
    SCENARIOS,
    evaluate_scenario_curves,
    select_operating_point,
    summarize_coverage,
    validate_operating_point,
)
from src.link_budget import active_bandwidth_hz, compute_link_budget, nominal_data_rate_bps
from src.modulation import (
    bits_per_symbol,
    derive_switching_thresholds,
    get_constellation,
    theoretical_ber_awgn,
    theoretical_ber_rayleigh,
)
from src.propagation import analytical_shadow_margin_db, get_ci_parameters, median_path_loss_db

CFG = DEFAULT_CONFIG
ROOT = Path(__file__).resolve().parent
RES = ROOT / "outputs" / "results"
FIG = ROOT / "outputs" / "figures"

NAVY, TEAL, AMBER, SLATE, GREY, INK = (
    "#0F2A47",
    "#0F766E",
    "#B45309",
    "#1D4ED8",
    "#64748B",
    "#0F172A",
)
FREQ_OPTIONS = (700.0, 900.0, 1800.0)
FREQ_COLOR = {700.0: SLATE, 900.0: NAVY, 1800.0: TEAL}
MC_BIT_CHOICES = (100, 1_000, 10_000, 100_000, 1_000_000)
MC_BIT_LABELS = {
    100: "10²",
    1_000: "10³",
    10_000: "10⁴",
    100_000: "10⁵",
    1_000_000: "10⁶",
}
MOD_COLOR = {
    "BPSK": "#B45309",
    "QPSK": "#7FA6C9",
    "16-QAM": "#0F766E",
    "64-QAM": "#0F2A47",
    "Outage": "#D5DBE3",
}
DISTANCES_KM = np.round(np.arange(CFG.distance_min_km, CFG.distance_max_km + 1e-9, 0.25), 4)
N_DRAWS = 5000  # sama dengan eksperimen publikasi (experiments/run_adaptive.py)
TEAM = "Aditya, Zahran, Baihaqy, Jeyd, Rizqul, Yusril"
STRATEGY_LABEL = {k: f"{k}: {v['label']}" for k, v in SCENARIOS.items()} | {
    "MANUAL": "Manual: RB dan modulasi dikunci pengguna"
}

st.set_page_config(page_title="RuralLink | Kelompok 1", layout="wide")
st.markdown(
    """
<style>
.block-container {padding-top: 3.1rem; padding-bottom: 1.5rem; max-width: 1560px;}
[data-testid="stMain"] {overflow-y: auto;}
h1, h2, h3 {color: #0F2A47;}
.rl-head {border-bottom: 2px solid #0F766E; padding-bottom: .45rem; margin-bottom: .65rem;}
.rl-head h1 {font-size: 1.55rem; margin: 0; padding: 0; line-height: 1.2;}
.rl-head p {margin: .15rem 0 0 0; color: #334155; font-size: .86rem;}
.rl-strip {display: grid; grid-template-columns: repeat(8, minmax(0, 1fr));
  border: 1px solid #CBD5E1; border-radius: 4px; background: #FFFFFF; margin: .35rem 0 .7rem 0;}
@media (max-width: 1120px) {.rl-strip {grid-template-columns: repeat(4, minmax(0, 1fr));}}
@media (max-width: 640px) {.rl-strip {grid-template-columns: repeat(2, minmax(0, 1fr));}}
.rl-cell {padding: .42rem .58rem; border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; min-width: 0;}
.rl-cell:last-child {border-right: none;}
.rl-l {font-size: .69rem; color: #475569; line-height: 1.2; font-weight: 600;}
.rl-v {font-size: 1.04rem; font-weight: 700; color: #0F2A47; font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere; line-height: 1.25; margin-top: 1px;}
.rl-s {font-size: .68rem; color: #475569; line-height: 1.2;}
.rl-sim .rl-v {color: #B45309;}
.rl-bad .rl-v {color: #9A1B1B;}
.rl-note {border-left: 3px solid #0F766E; padding: .35rem .7rem; background: #FFFFFF;
  border-top: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0;
  font-size: .83rem; color: #1E293B; margin: .25rem 0 .55rem 0;}
.rl-note-exp {border-left-color: #B45309;}
.rl-sec {font-size: .95rem; font-weight: 700; color: #0F2A47; margin: .35rem 0 .25rem 0;}
button, [role="tab"], [role="radio"], label, summary {cursor: pointer;}
button:disabled, [disabled] {cursor: not-allowed;}
button:focus-visible, [role="tab"]:focus-visible, input:focus-visible, summary:focus-visible {
  outline: 2px solid #2563EB !important; outline-offset: 2px;}
@media (prefers-reduced-motion: reduce) {* {animation: none !important; transition: none !important;}}
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ engine wrappers
@st.cache_data
def make_config(ber_target: float) -> SimulationConfig:
    return (
        DEFAULT_CONFIG
        if np.isclose(ber_target, CFG.ber_target)
        else replace(CFG, ber_target=float(ber_target))
    )


@st.cache_data
def thresholds(ber_target: float) -> dict[str, dict[str, float]]:
    return derive_switching_thresholds(float(ber_target), CFG.modulations)


@st.cache_data(show_spinner="Menjalankan mesin Python: path loss, link budget, realisasi bersama")
def cached_freq_curves(
    freq_mhz: float, env: str, tx_dbm: float, ber_target: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cache per-frekuensi dengan seed identik agar penambahan 700 MHz tidak menghitung ulang 900/1800."""
    cfg = make_config(ber_target)
    curves = evaluate_scenario_curves(
        float(freq_mhz), env, DISTANCES_KM, tuple(SCENARIOS), tx_dbm, N_DRAWS, cfg.default_seed, cfg
    )
    return curves, summarize_coverage(curves, cfg)


def load_active_curves(
    freqs: tuple[float, ...], env: str, tx_dbm: float, ber_target: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    parts_c, parts_s = [], []
    for f in freqs:
        c, s = cached_freq_curves(float(f), env, tx_dbm, ber_target)
        parts_c.append(c)
        parts_s.append(s)
    return pd.concat(parts_c, ignore_index=True), pd.concat(parts_s, ignore_index=True)


@st.cache_data(show_spinner="Monte Carlo bit-level sedang berjalan")
def cached_mc(modulation: str, ebn0_db: float, n_bits: int) -> dict:
    return validate_operating_point(modulation, ebn0_db, n_bits, seed=CFG.default_seed)


def read_csv(name: str) -> pd.DataFrame | None:
    p = RES / name
    return pd.read_csv(p) if p.exists() else None


def freq_tag(freq_mhz: float) -> str:
    return f"{freq_mhz:.0f} MHz (eksploratori)" if freq_mhz == 700.0 else f"{freq_mhz:.0f} MHz"


def align_mc_bits(n_bits: int, modulation: str) -> int:
    """Align requested bit count upward to an exact multiple of bits_per_symbol."""
    k = bits_per_symbol(modulation)
    return max(k, ((int(n_bits) + k - 1) // k) * k)


def evaluate_link(
    freq: float,
    env: str,
    dist: float,
    ptx: float,
    shadow: str,
    strat: str,
    rb_manual: int,
    mod_manual: str,
    ber_target: float,
) -> dict:
    """Satu titik link dari mesin: path loss, link budget, pilihan konfigurasi, BER analitis."""
    cfg = make_config(ber_target)
    thr = thresholds(ber_target)
    _, sigma = get_ci_parameters(env)
    margin = (
        analytical_shadow_margin_db(sigma, 1.0 - cfg.outage_target) if shadow == "margin95" else 0.0
    )
    pl = float(median_path_loss_db(dist * 1000.0, freq, env)) + margin
    if strat == "MANUAL":
        mod, rb = mod_manual, int(rb_manual)
    else:
        sel = select_operating_point(pl, strat, ptx, cfg, thr)
        idx = int(sel.index[0])
        if idx >= 0:
            mod, rb = sel.options[idx]
        else:
            mod, rb = "Outage", min(r for _, r in sel.options)
    lb = compute_link_budget(pl, n_rb=rb, tx_power_dbm=ptx)
    out: dict = {
        "pl": pl,
        "margin": margin,
        "pr": float(lb.pr_dbm),
        "noise": float(lb.noise_dbm),
        "snr": float(lb.snr_db),
        "rb": rb,
        "mod": mod,
        "b_hz": active_bandwidth_hz(rb, cfg.rb_bandwidth_hz),
        "p_rb": float(lb.power_per_rb_dbm),
    }
    if mod == "Outage":
        out |= {"ok": False, "ebn0": np.nan, "ebn0_margin": np.nan, "rate": 0.0}
        return out
    k = bits_per_symbol(mod)
    ebn0 = out["snr"] - 10.0 * np.log10(k)
    margin_eb = ebn0 - thr[mod]["ebn0_db"]
    ok = margin_eb >= 0.0
    out |= {
        "ok": bool(ok),
        "ebn0": float(ebn0),
        "ebn0_margin": float(margin_eb),
        "rate": float(nominal_data_rate_bps(out["b_hz"], mod)) if ok else 0.0,
        "ber_awgn": float(theoretical_ber_awgn(10 ** (ebn0 / 10), mod)),
        "ber_ray": float(theoretical_ber_rayleigh(10 ** (ebn0 / 10), mod)),
    }
    return out


def fmt_rate(bps: float) -> str:
    return "outage" if bps <= 0 else f"{bps / 1e6:.2f} Mbit/s"


def strip(cells: list[tuple[str, str, str, str]]) -> None:
    """Telemetry strip horizontal. Setiap sel: (label, nilai, sub, kelas)."""
    html = "".join(
        f'<div class="rl-cell {c}"><div class="rl-l">{a}</div><div class="rl-v">{b}</div>'
        f'<div class="rl-s">{s}</div></div>'
        for a, b, s, c in cells
    )
    st.markdown(f'<div class="rl-strip">{html}</div>', unsafe_allow_html=True)


def seg(label: str, options, key: str, disabled: bool = False, fmt=str):
    if key not in st.session_state or st.session_state[key] not in options:
        fallback = DEFAULTS.get(key)
        st.session_state[key] = fallback if fallback in options else options[0]
    val = st.segmented_control(
        label, options, key=key, format_func=fmt, selection_mode="single", disabled=disabled
    )
    return val if val is not None else st.session_state[key]


DEFAULTS = {
    "freq": 900.0,
    "env": "NLOS",
    "dist": 5.0,
    "ptx": 23.0,
    "chan": "AWGN",
    "strat": "S3",
    "rb": 25,
    "mod": "QPSK",
    "shadow": "median",
    "nbits": 100_000,
    "ber_target": 1e-2,
    "zone_sc": "S3",
    "mc_view": "Dioptimalkan vs S0",
}
for _k, _v in DEFAULTS.items():
    st.session_state.setdefault(_k, _v)


def apply_preset() -> None:
    """Preset tepi sel: 900 MHz NLOS 5 km, baseline S0 gagal, S3 melayani."""
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.session_state.pop("mc", None)


def sync_zone_strategy() -> None:
    if st.session_state.get("strat") in SCENARIOS:
        st.session_state["zone_sc"] = st.session_state["strat"]


# ------------------------------------------------------------------ header
st.markdown(
    f"""<div class="rl-head"><h1>{PROJECT_NAME}: Workbench Jangkauan Uplink Adaptif</h1>
<p>{RESEARCH_TITLE}</p>
<p><b>Kelompok 1</b> | Sistem Komunikasi Digital | 2026 | {TEAM}</p></div>""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ left rail
with st.sidebar:
    st.subheader("Parameter uplink")
    st.button(
        "Preset: pemulihan tepi sel",
        on_click=apply_preset,
        key="preset_btn",
        width="stretch",
        help="900 MHz NLOS, 5 km, 23 dBm, S3, BER 1e-2. Baseline S0 mengalami outage di jarak ini.",
    )
    freq = seg(
        "Frekuensi pembawa (MHz)",
        list(FREQ_OPTIONS),
        "freq",
        fmt=lambda x: "700* (supl.)" if x == 700.0 else f"{x:.0f}",
    )
    st.caption(
        "Primer: 900 & 1800 MHz. *700 MHz: suplemen eksploratori (terinspirasi Reddy 2022 di atas model CI Park 2023)."
    )
    env = seg("Lingkungan propagasi", ["LOS", "NLOS"], "env")
    shadow = seg(
        "Shadowing",
        ["median", "margin95"],
        "shadow",
        fmt=lambda x: "Median (0 dB)" if x == "median" else "Margin 95%",
    )
    dist = st.slider(
        "Jarak UE ke BTS (km)",
        float(CFG.distance_min_km),
        float(CFG.distance_max_km),
        step=0.25,
        key="dist",
    )
    ptx = st.slider(
        "Daya pancar UE (dBm, maks 23)", 10.0, float(CFG.ue_tx_power_dbm), step=1.0, key="ptx"
    )
    chan = seg(
        "Kanal",
        ["AWGN", "Rayleigh"],
        "chan",
        fmt=lambda x: "AWGN" if x == "AWGN" else "Rayleigh (CSI sesaat)",
    )
    strat = st.selectbox(
        "Strategi",
        list(STRATEGY_LABEL),
        format_func=STRATEGY_LABEL.get,
        key="strat",
        on_change=sync_zone_strategy,
    )
    manual = strat == "MANUAL"
    st.caption(
        "Mode manual: RB dan modulasi di bawah dikunci pengguna."
        if manual
        else "Mode adaptif: optimizer memilih modulasi dan RB. Kontrol manual dinonaktifkan."
    )
    rb_m = seg("Jumlah RB (manual)", list(CFG.active_rb_choices), "rb", disabled=not manual)
    mod_m = seg("Modulasi (manual)", list(CFG.modulations), "mod", disabled=not manual)
    ber_target = seg(
        "Target BER",
        [1e-2, 1e-3],
        "ber_target",
        fmt=lambda x: "10⁻² (Primer)" if np.isclose(x, 1e-2) else "10⁻³ (Eksploratori)",
    )
    n_bits = st.select_slider(
        "Jumlah bit (Monte Carlo)",
        options=MC_BIT_CHOICES,
        format_func=lambda n: MC_BIT_LABELS[n],
        key="nbits",
    )
    st.caption(f"Ukuran sampel dipilih: {MC_BIT_LABELS[n_bits]} = {n_bits:,} bit per kanal.")
    if n_bits < 100_000:
        st.warning(
            f"Sampel kecil ({n_bits:,} bit) memiliki ketidakpastian statistik tinggi "
            "(interval kepercayaan lebar dan berpeluang 0 error pada BER rendah)."
        )

    st.caption(
        f"Target BER {ber_target:g}. Target outage {CFG.outage_target:.0%}. Seed {CFG.default_seed}. Berjalan offline."
    )

freq_options = FREQ_OPTIONS

try:
    curves, summary = load_active_curves(freq_options, env, float(ptx), float(ber_target))
    thr = thresholds(float(ber_target))
    link = evaluate_link(freq, env, dist, ptx, shadow, strat, rb_m, mod_m, float(ber_target))
except ValueError as exc:
    st.error(f"Parameter ditolak oleh mesin: {exc}")
    st.stop()

is_exploratory = (freq == 700.0) or not np.isclose(ber_target, CFG.ber_target)

tab_wb, tab_res, tab_met = st.tabs(
    ["A. Workbench interaktif", "B. Hasil penelitian (CSV & PNG)", "C. Metodologi & Batasan"]
)


def build_snr_figure(
    freqs: tuple[float, ...], active_freq: float, active_link: dict, thr_map: dict
) -> go.Figure:
    fig = go.Figure()
    off = active_link["margin"]
    for f in freqs:
        color = FREQ_COLOR[f]
        label_prefix = "700 MHz*" if f == 700.0 else f"{f:.0f} MHz"
        for rb, dash in ((1, "solid"), (25, "dot")):
            pl_d = np.asarray(median_path_loss_db(DISTANCES_KM * 1000.0, f, env), dtype=float) + off
            snr_d = np.atleast_1d(compute_link_budget(pl_d, n_rb=rb, tx_power_dbm=ptx).snr_db)
            is_active_curve = f == active_freq and rb == active_link["rb"]
            fig.add_scatter(
                x=DISTANCES_KM,
                y=snr_d,
                name=f"{label_prefix}, {rb} RB",
                line=dict(color=color, dash=dash, width=2.8 if is_active_curve else 1.6),
                hovertemplate=f"{label_prefix} ({rb} RB)<br>Jarak: %{{x:.2f}} km<br>SNR: %{{y:.2f}} dB<extra></extra>",
            )
        if f == active_freq and active_link["rb"] not in (1, 25):
            rb_a = active_link["rb"]
            pl_d = np.asarray(median_path_loss_db(DISTANCES_KM * 1000.0, f, env), dtype=float) + off
            snr_d = np.atleast_1d(compute_link_budget(pl_d, n_rb=rb_a, tx_power_dbm=ptx).snr_db)
            fig.add_scatter(
                x=DISTANCES_KM,
                y=snr_d,
                name=f"{label_prefix}, {rb_a} RB (aktif)",
                line=dict(color=color, dash="dash", width=2.6),
                hovertemplate=f"{label_prefix} ({rb_a} RB)<br>Jarak: %{{x:.2f}} km<br>SNR: %{{y:.2f}} dB<extra></extra>",
            )
    for m in CFG.modulations:
        if m == "BPSK":
            continue
        fig.add_hline(
            y=thr_map[m]["esn0_db"],
            line_dash="dot",
            line_color="#94A3B8",
            line_width=1,
            annotation_text=f"{m} ({thr_map[m]['esn0_db']:.1f} dB)",
            annotation_position="top right",
            annotation_font_size=10,
            annotation_font_color="#334155",
        )
    fig.add_vline(x=dist, line_color=AMBER, line_width=1.6, line_dash="dash")
    cfg_txt = (
        "Outage" if not active_link["ok"] else f"{active_link['mod']} x {active_link['rb']} RB"
    )
    fig.add_scatter(
        x=[dist],
        y=[active_link["snr"]],
        mode="markers",
        name=f"Titik aktif ({cfg_txt})",
        marker=dict(
            size=10,
            color=AMBER if active_link["ok"] else "#9A1B1B",
            line=dict(color=INK, width=1.5),
        ),
        hovertemplate=f"Titik aktif {freq_tag(active_freq)}<br>Jarak: {dist:g} km<br>SNR: {active_link['snr']:.2f} dB<br>{cfg_txt}<extra></extra>",
    )
    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=12, b=10),
        template="plotly_white",
        xaxis_title="Jarak (km)",
        yaxis_title="SNR (dB)",
        legend=dict(orientation="h", y=-0.26, font=dict(size=10.5)),
    )
    return fig


def build_constellation_figure(panels: list[tuple[str, dict | None]], ch_key: str) -> go.Figure:
    fg = make_subplots(
        rows=1,
        cols=len(panels),
        subplot_titles=[p[0] for p in panels],
        horizontal_spacing=0.10 if len(panels) == 2 else 0.06,
    )
    for ci, (_, res) in enumerate(panels, start=1):
        if res is None:
            fg.add_annotation(
                x=0,
                y=0,
                text="OUTAGE<br>(tidak ada transmisi)",
                showarrow=False,
                font=dict(color="#9A1B1B", size=12),
                xref=f"x{'' if ci == 1 else ci}",
                yref=f"y{'' if ci == 1 else ci}",
            )
            fg.update_xaxes(range=[-1.6, 1.6], row=1, col=ci, title_text="I")
            fg.update_yaxes(
                range=[-1.6, 1.6], row=1, col=ci, scaleanchor=f"x{'' if ci == 1 else ci}"
            )
            continue
        smp = res[f"samples_{ch_key}"]
        ref, _ = get_constellation(res["modulation"])
        fg.add_trace(
            go.Scatter(
                x=smp.real,
                y=smp.imag,
                mode="markers",
                name="diterima (SIMULATED)",
                legendgroup="sim",
                showlegend=ci == 1,
                marker=dict(size=3.8, color=AMBER, opacity=0.55),
                hoverinfo="skip",
            ),
            row=1,
            col=ci,
        )
        fg.add_trace(
            go.Scatter(
                x=np.real(ref),
                y=np.imag(ref),
                mode="markers",
                name="ideal",
                legendgroup="ideal",
                showlegend=ci == 1,
                marker=dict(size=8, color=NAVY, symbol="x"),
                hoverinfo="skip",
            ),
            row=1,
            col=ci,
        )
        fg.update_xaxes(title_text="I", range=[-1.8, 1.8], row=1, col=ci)
        fg.update_yaxes(
            title_text="Q" if ci == 1 else "",
            range=[-1.8, 1.8],
            row=1,
            col=ci,
            scaleanchor=f"x{'' if ci == 1 else ci}",
        )
    fg.update_layout(
        height=265,
        margin=dict(l=10, r=10, t=30, b=10),
        template="plotly_white",
        legend=dict(orientation="h", y=-0.28, font=dict(size=10.5)),
    )
    return fg


def build_coverage_figure(
    freqs: tuple[float, ...],
    curves_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    zsc: str,
    ue_dist_km: float,
) -> go.Figure:
    titles = [f"{freq_tag(f)} | {env}, {zsc}" for f in freqs]
    fg = make_subplots(
        rows=1,
        cols=len(freqs),
        subplot_titles=titles,
        horizontal_spacing=0.06 if len(freqs) == 2 else 0.045,
    )
    seen: set[str] = set()
    theta = np.linspace(0, 2 * np.pi, 181)
    rmax = float(CFG.distance_max_km)

    for ci, f in enumerate(freqs, start=1):
        g = curves_df[(curves_df.freq_mhz == f) & (curves_df.scenario == zsc)].sort_values(
            "distance_km"
        )
        labels = np.where(g.median_feasible, g.median_modulation, "Outage").tolist()
        d = g.distance_km.to_numpy()
        zones, start = [], 0
        for i in range(1, len(labels) + 1):
            if i == len(labels) or labels[i] != labels[start]:
                inner = 0.0 if start == 0 else float(d[start]) - 0.125
                outer = min(rmax, float(d[i - 1]) + 0.125)
                zones.append((inner, outer, labels[start]))
                start = i
        for inner, outer, lab in reversed(zones):
            fg.add_trace(
                go.Scatter(
                    x=outer * np.cos(theta),
                    y=outer * np.sin(theta),
                    mode="lines",
                    fill="toself",
                    fillcolor=MOD_COLOR[lab],
                    line=dict(color="#FFFFFF", width=1),
                    name=lab,
                    legendgroup=lab,
                    showlegend=lab not in seen,
                    hoverinfo="name+text",
                    text=f"{lab}: {inner:.2f} s.d. {outer:.2f} km",
                ),
                row=1,
                col=ci,
            )
            seen.add(lab)
        srow = summary_df[(summary_df.freq_mhz == f) & (summary_df.scenario == zsc)].iloc[0]
        for rad, lab, color, dash in (
            (
                srow.radius_stochastic_km,
                "Batas 95% andal (shadowing)",
                NAVY,
                "dash",
            ),
            (
                srow.radius_fading_km,
                "Batas 95% andal (+Rayleigh CSI)",
                AMBER,
                "dot",
            ),
        ):
            if rad > 0:
                fg.add_trace(
                    go.Scatter(
                        x=float(rad) * np.cos(theta),
                        y=float(rad) * np.sin(theta),
                        mode="lines",
                        line=dict(color=color, dash=dash, width=2.3),
                        name=lab,
                        legendgroup=lab,
                        showlegend=lab not in seen,
                        hoverinfo="name+text",
                        text=f"{f:.0f} MHz: {srow.radius_stochastic_label if dash == 'dash' else srow.radius_fading_label}",
                    ),
                    row=1,
                    col=ci,
                )
                seen.add(lab)
        fg.add_trace(
            go.Scatter(
                x=[0],
                y=[0],
                mode="markers+text",
                text=["BTS"],
                textposition="bottom center",
                marker=dict(size=9, color=INK, symbol="diamond"),
                name="BTS",
                showlegend=ci == 1,
                legendgroup="BTS",
            ),
            row=1,
            col=ci,
        )
        fg.add_trace(
            go.Scatter(
                x=[ue_dist_km],
                y=[0],
                mode="markers+text",
                text=[f"UE {ue_dist_km:g} km"],
                textposition="top center",
                marker=dict(size=9, color="#FFFFFF", line=dict(color=INK, width=2)),
                name="UE",
                showlegend=ci == 1,
                legendgroup="UE",
            ),
            row=1,
            col=ci,
        )
        fg.update_xaxes(
            range=[-13.2, 13.2], title_text="km", row=1, col=ci, zeroline=False, constrain="domain"
        )
        fg.update_yaxes(
            range=[-13.2, 13.2],
            row=1,
            col=ci,
            scaleanchor=f"x{'' if ci == 1 else ci}",
            scaleratio=1,
            constrain="domain",
            zeroline=False,
        )
    fg.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=32, b=10),
        template="plotly_white",
        legend=dict(orientation="h", y=-0.18, font=dict(size=10.5)),
    )
    return fg


# ================================================================== A. INTERACTIVE WORKBENCH
with tab_wb:
    if is_exploratory:
        st.markdown(
            '<div class="rl-note rl-note-exp"><b>Mode sensitivitas eksploratori aktif.</b> '
            f"Frekuensi aktif: {', '.join(f'{f:.0f}' for f in freq_options)} MHz; target BER: {ber_target:g}. "
            "700 MHz terinspirasi Reddy (2022) di atas model CI Park (2023) dan bukan replikasi Reddy. "
            "Konfigurasi riset utama tetap 900/1800 MHz pada BER 1e-2 (Tab B tidak berubah).</div>",
            unsafe_allow_html=True,
        )

    row = curves[
        (curves.freq_mhz == freq)
        & (curves.environment == env)
        & np.isclose(curves.distance_km, dist)
    ].set_index("scenario")
    cur = row.loc[strat] if strat in row.index else None
    in_outage = not link["ok"]
    ber_main = link.get("ber_awgn") if chan == "AWGN" else link.get("ber_ray")
    ber_label = "BER AWGN" if chan == "AWGN" else "BER Rayleigh (tanpa CSI)"
    if cur is None:
        outage_txt, outage_sub = "n/a", "mode manual"
    elif chan == "AWGN":
        outage_txt, outage_sub = f"{cur.shadow_outage_prob:.1%}", "SIMULATED, shadowing"
    else:
        outage_txt, outage_sub = (
            f"{cur.fading_outage_prob:.1%}",
            "SIMULATED, +Rayleigh CSI",
        )

    strip(
        [
            (
                "Path loss CI",
                f"{link['pl']:.1f} dB",
                f"margin {link['margin']:.1f} dB (THEORETICAL)",
                "",
            ),
            ("Daya terima Pr", f"{link['pr']:.1f} dBm", f"P/RB {link['p_rb']:.1f} dBm", ""),
            (
                "Noise floor",
                f"{link['noise']:.1f} dBm",
                f"B {link['b_hz'] / 1e6:.2f} MHz",
                "",
            ),
            (
                "SNR (Es/N0)",
                f"{link['snr']:.1f} dB",
                f"Eb/N0 {link['ebn0']:.1f} dB" if not in_outage else "tanpa opsi layak",
                "",
            ),
            (
                "Konfigurasi aktif",
                "Outage" if in_outage else f"{link['mod']} x {link['rb']} RB",
                "manual" if manual else f"optimizer ({strat})",
                "rl-bad" if in_outage else "",
            ),
            (
                ber_label,
                "n/a" if in_outage or ber_main is None else f"{ber_main:.2e}",
                f"target {ber_target:g}",
                "",
            ),
            ("Laju nominal", fmt_rate(link["rate"]), "tanpa coding (bukan LTE)", ""),
            ("Probabilitas outage", outage_txt, outage_sub, "rl-sim"),
        ]
    )

    if manual and not link["ok"] and link["mod"] != "Outage":
        st.warning(
            f"Konfigurasi manual tidak layak: Eb/N0 {link['ebn0']:.1f} dB lebih rendah dari ambang "
            f"{thr[link['mod']]['ebn0_db']:.2f} dB untuk {link['mod']} (BER {ber_target:g}). Link dinyatakan outage."
        )
    if in_outage and not manual:
        st.error(
            "Tidak ada kombinasi modulasi dan RB yang memenuhi BER target pada jarak ini. Coba kurangi jarak atau naikkan daya."
        )

    # Row 1: SNR vs Distance (left) + Bit-level MC & Side-by-side Constellations (right)
    c1, c2 = st.columns([1.1, 1], gap="medium")
    with c1:
        st.markdown(
            f'<div class="rl-sec">SNR vs jarak ({env}, margin {link["margin"]:.1f} dB, THEORETICAL)</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(build_snr_figure(freq_options, freq, link, thr), width="stretch")
        st.caption(
            f"Garis penuh: 1 RB (jangkauan maks). Titik: 25 RB. Garis horizontal: ambang Es/N0 pada BER {ber_target:g}. "
            "Garis putus amber: jarak UE aktif."
        )

    with c2:
        st.markdown(
            '<div class="rl-sec">Monte Carlo bit-level & konstelasi diterima (SIMULATED)</div>',
            unsafe_allow_html=True,
        )
        base = evaluate_link(freq, env, dist, ptx, shadow, "S0", rb_m, mod_m, float(ber_target))
        mc_ctl1, mc_ctl2 = st.columns([1, 1.15])
        mc_ctl1.write(
            f"Aktif: **{'Outage' if in_outage else link['mod'] + ' x ' + str(link['rb']) + ' RB'}** | "
            f"S0: **{'Outage' if not base['ok'] else 'QPSK x 25 RB'}**"
        )
        run_clicked = mc_ctl2.button(
            "Jalankan Monte Carlo",
            key="run_mc",
            disabled=in_outage,
            width="stretch",
        )
        key_now = (
            freq,
            env,
            dist,
            ptx,
            shadow,
            strat,
            rb_m,
            mod_m,
            int(n_bits),
            float(ber_target),
        )
        if run_clicked:
            by_freq = {}
            for f_item in freq_options:
                lk_f = evaluate_link(
                    f_item,
                    env,
                    dist,
                    ptx,
                    shadow,
                    "S3" if strat == "MANUAL" else strat,
                    rb_m,
                    mod_m,
                    float(ber_target),
                )
                by_freq[f_item] = (
                    cached_mc(lk_f["mod"], lk_f["ebn0"], align_mc_bits(n_bits, lk_f["mod"]))
                    if lk_f["ok"]
                    else None
                )
            st.session_state["mc"] = {
                "key": key_now,
                "opt": cached_mc(link["mod"], link["ebn0"], align_mc_bits(n_bits, link["mod"])),
                "base": (
                    cached_mc(base["mod"], base["ebn0"], align_mc_bits(n_bits, base["mod"]))
                    if base["ok"]
                    else None
                ),
                "by_freq": by_freq,
            }

        mc = st.session_state.get("mc")
        if in_outage:
            st.info("Tidak ada transmisi yang dapat disimulasikan pada konfigurasi outage.")
        elif mc is None:
            st.info(
                f"Belum dijalankan. Tekan Jalankan Monte Carlo untuk mengirim {n_bits:,} bit acak "
                f"(diselaraskan ke kelipatan {bits_per_symbol(link['mod'])} bit/simbol = "
                f"{align_mc_bits(n_bits, link['mod']):,} bit) melalui kanal AWGN dan Rayleigh."
            )
        elif mc["key"] != key_now:
            st.warning(
                "Parameter berubah sejak simulasi terakhir. Hasil sebelumnya disembunyikan agar tidak "
                "dianggap sebagai hasil aktif; jalankan ulang Monte Carlo."
            )
        else:
            ch = "awgn" if chan == "AWGN" else "rayleigh"
            view_mode = seg(
                "Tampilan konstelasi",
                ["Dioptimalkan vs S0", "Antar Frekuensi"],
                "mc_view",
            )
            for name, res in (("Dioptimalkan", mc["opt"]), ("Baseline S0", mc["base"])):
                if res is None:
                    st.caption(f"**{name}**: outage, tidak ada transmisi.")
                    continue
                ci = res[f"ci_low_{ch}"], res[f"ci_high_{ch}"]
                if ci[0] is None:
                    ci_txt = ""
                elif res[f"mc_errors_{ch}"] == 0:
                    ci_txt = f", CI 95% [0.0e+00, {ci[1]:.1e}] (0 error, batas atas rule-of-three)"
                else:
                    ci_txt = f", CI 95% [{ci[0]:.1e}, {ci[1]:.1e}]"
                n_sym = res["n_bits"] // bits_per_symbol(res["modulation"])
                n_smp = int(res[f"samples_{ch}"].size)
                st.caption(
                    f"**{name}** ({res['modulation']}, Eb/N0 {res['ebn0_db']:.2f} dB, "
                    f"{res['n_bits']:,} bit / {n_sym:,} simbol, sampel konstelasi {n_smp:,}): "
                    f"BER MC AWGN {res['mc_ber_awgn']:.2e} (teori {res['theory_ber_awgn']:.2e}); "
                    f"Rayleigh tanpa CSI {res['mc_ber_rayleigh']:.2e} (teori {res['theory_ber_rayleigh']:.2e}){ci_txt}."
                )
            if view_mode == "Dioptimalkan vs S0":
                panels = [
                    (f"Dioptimalkan: {mc['opt']['modulation']}", mc["opt"]),
                    (
                        f"Baseline S0: {mc['base']['modulation'] if mc['base'] else 'Outage'}",
                        mc["base"],
                    ),
                ]
            else:
                by_freq = mc.get("by_freq", {})
                panels = [
                    (
                        f"{freq_tag(f_item)}: {by_freq[f_item]['modulation'] if by_freq.get(f_item) else 'Outage'}",
                        by_freq.get(f_item),
                    )
                    for f_item in freq_options
                ]
            st.plotly_chart(build_constellation_figure(panels, ch), width="stretch")

    # Row 2: Side-by-side radial modulation coverage maps on primary dashboard
    z_hdr1, z_hdr2 = st.columns([2.2, 1])
    z_hdr1.markdown(
        '<div class="rl-sec">Peta zona modulasi radial sisi-ke-sisi (model hipotetis 1-12 km, bukan peta lapangan)</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.get("zone_sc") not in SCENARIOS:
        st.session_state["zone_sc"] = "S3"
    zsc = z_hdr2.selectbox(
        "Strategi peta zona",
        list(SCENARIOS),
        format_func=lambda s: f"{s}: {SCENARIOS[s]['label']}",
        key="zone_sc",
        label_visibility="collapsed",
    )
    st.plotly_chart(
        build_coverage_figure(freq_options, curves, summary, zsc, dist), width="stretch"
    )
    st.caption(
        "Cincin berwarna: zona median PL (deterministik, THEORETICAL). Garis putus: batas andal outage <=5% "
        "(SIMULATED, realisasi acak bersama). Radius 12 km tersensor kanan (>=12 km)."
    )

    # Row 3: Fixed vs Adaptive Strategy Comparison & Frequency Comparison Table (full width for readability)
    st.markdown(
        f'<div class="rl-sec">Fixed vs adaptif pada {dist:g} km, {freq_tag(freq)} {env}</div>',
        unsafe_allow_html=True,
    )
    r = row.reset_index()
    tbl = pd.DataFrame(
        {
            "Strategi": r.scenario.map(lambda s: f"{s}: {SCENARIOS[s]['label']}"),
            "Konfigurasi median": [
                f"{m} x {n} RB" if f else "Outage"
                for m, n, f in zip(
                    r.median_modulation, r.median_n_rb, r.median_feasible, strict=True
                )
            ],
            "Laju median (Mbit/s)": (r.median_rate_bps / 1e6).round(2),
            "Outage shadow": (r.shadow_outage_prob * 100).round(1).astype(str) + "%",
            "Outage +Rayleigh CSI": (r.fading_outage_prob * 100).round(1).astype(str) + "%",
            "Laju efektif CSI (Mbit/s)": (r.fading_effective_rate_bps / 1e6).round(2),
            "BER bersyarat": r.fading_cond_ber_mean.map(
                lambda x: "n/a" if pd.isna(x) else f"{x:.1e}"
            ),
        }
    )
    st.dataframe(tbl, hide_index=True, width="stretch")
    st.caption(
        "Semua strategi memakai realisasi shadowing & Rayleigh yang sama. Laju efektif menghitung outage sebagai 0."
    )

    st.markdown(
        f'<div class="rl-sec">Perbandingan frekuensi pada {dist:g} km ({env}, seed identik {CFG.default_seed})</div>',
        unsafe_allow_html=True,
    )
    ft = []
    for f in freq_options:
        lk = evaluate_link(f, env, dist, ptx, shadow, "S3", rb_m, mod_m, float(ber_target))
        s3 = summary[(summary.freq_mhz == f) & (summary.scenario == "S3")].iloc[0]
        ft.append(
            {
                "Frekuensi": freq_tag(f),
                "PL (dB)": round(lk["pl"], 1),
                "SNR 25 RB (dB)": round(
                    float(compute_link_budget(lk["pl"], n_rb=25, tx_power_dbm=ptx).snr_db), 1
                ),
                "SNR 1 RB (dB)": round(
                    float(compute_link_budget(lk["pl"], n_rb=1, tx_power_dbm=ptx).snr_db), 1
                ),
                "Pilihan S3": "Outage" if lk["mod"] == "Outage" else f"{lk['mod']} x {lk['rb']} RB",
                "Laju S3": fmt_rate(lk["rate"]),
                "Radius median S3": s3.radius_median_label,
                "Radius andal 95% (+fading)": s3.radius_fading_label,
            }
        )
    st.dataframe(pd.DataFrame(ft), hide_index=True, width="stretch")
    st.caption(
        "Kondisi propagasi CI dan realisasi kanal acak identik antar frekuensi untuk perbandingan setara."
    )

# ================================================================== B. RESULTS
with tab_res:
    st.markdown(
        '<div class="rl-note">Hasil publikasi dibaca langsung dari <code>outputs/</code> (900/1800 MHz, 23 dBm, '
        "BER 1e-2, seed 42, 5000 realisasi bersama, grid 1 sampai 12 km). Label: THEORETICAL = median path loss dan rumus tertutup. "
        "SIMULATED = shadowing, Rayleigh, dan Monte Carlo bit-level. Laju nominal tanpa coding, bukan throughput LTE.</div>",
        unsafe_allow_html=True,
    )
    pub_curves, pub_sum, pub_cmp, pub_mc = (
        read_csv("adaptive_coverage_curves.csv"),
        read_csv("adaptive_coverage_summary.csv"),
        read_csv("adaptive_strategy_comparison.csv"),
        read_csv("adaptive_mc_validation.csv"),
    )
    if pub_curves is None or pub_sum is None:
        st.error(
            "File hasil di outputs/results/ tidak ditemukan. Jalankan: python -m experiments.run_adaptive"
        )
    else:
        e_sel = st.radio("Lingkungan", ["LOS", "NLOS"], index=1, horizontal=True, key="res_env")
        sc_sel = st.multiselect("Strategi", list(SCENARIOS), default=list(SCENARIOS), key="res_sc")
        if not sc_sel:
            st.info("Pilih minimal satu strategi untuk menampilkan hasil.")
        else:
            p = pub_curves[(pub_curves.environment == e_sel) & pub_curves.scenario.isin(sc_sel)]
            pal = {"S0": GREY, "S1": "#7FA6C9", "S2": AMBER, "S3": TEAL, "R0": NAVY}
            cc = st.columns(2)
            for col, ycol, ttl, scale in (
                (
                    cc[0],
                    "fading_outage_prob",
                    "Outage vs jarak, shadowing + Rayleigh CSI (%, SIMULATED)",
                    100,
                ),
                (
                    cc[1],
                    "fading_effective_rate_bps",
                    "Laju efektif vs jarak (Mbit/s, SIMULATED, outage = 0)",
                    1e-6,
                ),
            ):
                fg = make_subplots(
                    rows=1,
                    cols=2,
                    subplot_titles=[f"{f:.0f} MHz" for f in CFG.carrier_frequencies_mhz],
                    shared_yaxes=True,
                )
                for ci, f in enumerate(CFG.carrier_frequencies_mhz, start=1):
                    for s in sc_sel:
                        h = p[(p.freq_mhz == f) & (p.scenario == s)]
                        fg.add_trace(
                            go.Scatter(
                                x=h.distance_km,
                                y=h[ycol] * scale,
                                name=s,
                                legendgroup=s,
                                showlegend=ci == 1,
                                line=dict(
                                    color=pal[s], width=2, shape="hv" if scale < 1 else "linear"
                                ),
                            ),
                            row=1,
                            col=ci,
                        )
                    if scale == 100:
                        fg.add_hline(
                            y=CFG.outage_target * 100,
                            line_dash="dot",
                            line_color=AMBER,
                            row=1,
                            col=ci,
                        )
                fg.update_layout(
                    height=330,
                    margin=dict(l=10, r=10, t=40, b=10),
                    template="plotly_white",
                    title=dict(text=ttl, font_size=13),
                    legend=dict(orientation="h", y=-0.2),
                )
                fg.update_xaxes(title_text="Jarak (km)")
                col.plotly_chart(fg, width="stretch")
            st.markdown(
                "**Radius cakupan (<1 km: tidak ada cakupan pada titik uji pertama; >=12 km: tersensor kanan)**"
            )
            st.dataframe(
                pub_sum[(pub_sum.environment == e_sel) & pub_sum.scenario.isin(sc_sel)][
                    [
                        "freq_mhz",
                        "scenario",
                        "label",
                        "radius_median_label",
                        "radius_stochastic_label",
                        "radius_fading_label",
                    ]
                ].rename(
                    columns={
                        "freq_mhz": "MHz",
                        "label": "Strategi",
                        "radius_median_label": "Median PL (THEORETICAL)",
                        "radius_stochastic_label": "Shadowing 5% (SIMULATED)",
                        "radius_fading_label": "Shadowing + Rayleigh CSI (SIMULATED)",
                    }
                ),
                hide_index=True,
                width="stretch",
            )
            if pub_cmp is not None:
                st.markdown(
                    "**Temuan terverifikasi dari CSV (tepi sel, 2 km, NLOS, shadowing + Rayleigh CSI)**"
                )
                for f in CFG.carrier_frequencies_mhz:
                    q = pub_cmp[
                        (pub_cmp.freq_mhz == f)
                        & (pub_cmp.environment == "NLOS")
                        & (pub_cmp.distance_km == 2.0)
                    ].set_index("scenario")
                    if {"S0", "S3"} <= set(q.index):
                        st.markdown(
                            f"- {f:.0f} MHz: S0 outage {q.loc['S0', 'fading_outage_prob']:.1%} dengan laju efektif "
                            f"{q.loc['S0', 'fading_effective_rate_bps'] / 1e6:.2f} Mbit/s, S3 outage {q.loc['S3', 'fading_outage_prob']:.1%} "
                            f"dengan {q.loc['S3', 'fading_effective_rate_bps'] / 1e6:.2f} Mbit/s."
                        )
            if pub_mc is not None:
                st.markdown("**Validasi Monte Carlo bit-level pada titik operasi S3 (SIMULATED)**")
                st.dataframe(
                    pub_mc[
                        [
                            "freq_mhz",
                            "environment",
                            "distance_km",
                            "modulation",
                            "n_rb",
                            "ebn0_db",
                            "theory_ber_awgn",
                            "mc_ber_awgn",
                            "theory_ber_rayleigh",
                            "mc_ber_rayleigh",
                        ]
                    ].round(6),
                    hide_index=True,
                    width="stretch",
                )
                st.caption(
                    "BER Rayleigh di sini adalah rata-rata tanpa CSI pada modulasi yang dipilih dari SNR lambat. Bukan BER bersyarat adaptif."
                )
        st.markdown("**Grafik hasil (PNG) dan unduhan**")
        imgs = [
            FIG / n
            for n in (
                "adaptive_coverage_radius.png",
                "adaptive_rate_vs_distance.png",
                "path_loss_vs_distance.png",
                "uplink_snr_vs_distance.png",
                "ber_awgn_validation.png",
                "ber_rayleigh_validation.png",
            )
        ]
        gc = st.columns(2)
        for i, im in enumerate(imgs):
            if im.exists():
                gc[i % 2].image(str(im), caption=im.stem.replace("_", " "))
                gc[i % 2].download_button(
                    f"Unduh {im.name}", im.read_bytes(), im.name, "image/png", key=f"dl_{im.stem}"
                )
        dc = st.columns(3)
        for i, nm in enumerate(sorted(x.name for x in RES.glob("*.csv"))):
            dc[i % 3].download_button(
                f"Unduh {nm}", (RES / nm).read_bytes(), nm, "text/csv", key=f"dl_{nm}"
            )
        sm = ROOT / "outputs" / "summary.md"
        if sm.exists():
            with st.expander("Ringkasan numerik lengkap (outputs/summary.md)"):
                st.markdown(sm.read_text(encoding="utf-8"))

# ================================================================== C. METHODOLOGY
with tab_met:
    st.markdown("#### Model dan persamaan")
    st.latex(r"PL(d) = FSPL(1\,\mathrm{m}, f) + 10\,n\,\log_{10}(d) + X_\sigma")
    st.latex(
        r"SNR_{dB} = P_t + G_t + G_r - L_{feeder} - L_{body} - PL - N_{dB},\quad N = -174 + 10\log_{10}(N_{RB}\cdot 180\,\mathrm{kHz}) + NF"
    )
    st.latex(r"E_b/N_0 = SNR / k,\quad k=\log_2 M,\quad R_b = N_{RB}\cdot 180\,\mathrm{kHz}\cdot k")
    st.markdown(
        f"""
- **Propagasi:** Close-In (CI) dengan parameter LOS n=2,16, sigma=3,07 dB dan NLOS n=2,56, sigma=11,40 dB (Park 2023, ekstrapolasi dari 1400 MHz, keputusan D8).
- **Link budget:** UE {CFG.ue_tx_power_dbm:.0f} dBm (maks), Gr {CFG.bts_rx_antenna_gain_dbi:.0f} dBi, feeder {CFG.feeder_loss_db:.0f} dB, tubuh {CFG.body_loss_db:.0f} dB, NF {CFG.rx_noise_figure_db:.0f} dB. Daya terbagi rata pada RB aktif, sehingga gain bandwidth hanya dihitung sekali.
- **BER:** Gray-coded eksak (Cho dan Yoon 2002), Monte Carlo bit-level pada kanal AWGN dan Rayleigh independen dengan ekualisasi ZF.
- **Ambang BER {ber_target:g} (aktif):** Eb/N0 (dB) {", ".join(f"{m} {thr[m]['ebn0_db']:.2f}" for m in CFG.modulations)}. Es/N0 = Eb/N0 + 10 log10 k.
- **Optimasi modulasi-bandwidth:** tiap opsi (modulasi, N_RB) layak bila Eb/N0 memenuhi ambang. Optimizer memilih opsi layak dengan laju nominal B x log2 M tertinggi. Mengurangi RB menaikkan SNR per simbol (daya terkonsentrasi, noise lebih kecil) dengan mengorbankan laju, sehingga jangkauan membesar.
- **Rayleigh:** adaptasi memakai CSI sesaat. Pada tiap realisasi, link memilih opsi dengan Eb/N0 sesaat yang memenuhi ambang AWGN. BER bersyarat adalah BER AWGN pada Eb/N0 sesaat tersebut. BER rata-rata Rayleigh tanpa CSI tidak dipakai untuk adaptasi.
- **Strategi:** {"; ".join(f"{k} {v['label']}" for k, v in SCENARIOS.items())}. Semua strategi memakai realisasi shadowing dan fading yang sama.
- **Keandalan:** cakupan median path loss bersifat deterministik dan bukan ukuran keandalan. Keandalan stokastik memakai outage 5% atau kurang.
"""
    )
    st.markdown("#### Batasan")
    st.markdown(
        """
- Konfigurasi riset utama adalah 900 dan 1800 MHz pada BER 1e-2. Opsi 700 MHz (terinspirasi Reddy 2022) dan BER 1e-3 di panel kiri adalah analisis suplemen eksploratori, bukan replikasi Reddy (2022).
- Laju nominal tanpa channel coding, overhead, dan penjadwalan. Bukan throughput LTE.
- Parameter CI diekstrapolasi dari kampanye Park (2023), belum ada data lapangan Indonesia.
- Tampilan zona adalah model radial hipotetis, bukan prediksi cakupan geografis.
- Radius yang mencapai batas 12 km bersifat tersensor kanan (>=12 km).
"""
    )
    st.markdown("#### Sumber")
    st.markdown(
        "Park dkk. (2023), parameter CI. Reddy (2022) dan Yogapratama (2015), parameter RF. Cho dan Yoon (2002), BER QAM Gray eksak. "
        "Rincian dan status verifikasi ada di `docs/REFERENCES.md` dan `docs/DECISIONS.md`."
    )
    st.markdown("#### Kredit")
    st.markdown(
        "Desain visual awal (rail parameter, telemetry strip, kurva SNR, konstelasi, zona radial) berasal dari dashboard HTML buatan **Zahran** "
        "(`prototypes/dashboard_rurallink.html`, riwayat Git asli dipertahankan). Integrasi ke Streamlit dan seluruh perhitungan berasal dari "
        f"mesin Python tim. Tim: {TEAM}."
    )
