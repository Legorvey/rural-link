"""RuralLink: instrumen riset Streamlit di atas mesin Python tervalidasi (src/).

Design Read (Antislop): instrumen riset telekomunikasi untuk proyeksi kelas, bahasa visual
workbench teknik terang, dial ENERGY 1 / RHYTHM 2 / MOTION 1.
Alasan desain (R-31):
- Palet: netral terang + navy (judul, data analitis) + teal (aksen tunggal) + amber (hasil simulasi).
  Warna membawa label asal data: navy/teal = THEORETICAL, amber = SIMULATED.
- Rail parameter kiri + telemetry strip: dasar dari prototipe Zahran (prototypes/).
- Font sistem saja: tanpa aset jaringan, aman untuk mode offline.
Seluruh angka, kurva, dan sampel konstelasi berasal dari src/. Tidak ada kalkulasi ilmiah di sini.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from config import DEFAULT_CONFIG, PROJECT_NAME, RESEARCH_TITLE
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
NAVY, TEAL, AMBER, GREY, INK = "#0F2A47", "#0F766E", "#B45309", "#64748B", "#0F172A"
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
.block-container {padding-top: 4rem; max-width: 1500px;}
[data-testid="stMain"] {overflow-y: auto;}
h1, h2, h3 {color: #0F2A47;}
.rl-head {border-bottom: 2px solid #0F766E; padding-bottom: .5rem; margin-bottom: .8rem;}
.rl-head h1 {font-size: 1.7rem; margin: 0; padding: 0;}
.rl-head p {margin: .15rem 0 0 0; color: #334155; font-size: .9rem;}
.rl-strip {display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  border: 1px solid #CBD5E1; background: #FFFFFF; margin: .4rem 0 .8rem 0;}
.rl-cell {padding: .45rem .7rem; border-right: 1px solid #E2E8F0; min-width: 0;}
.rl-cell:last-child {border-right: none;}
.rl-l {font-size: .72rem; color: #475569; line-height: 1.2;}
.rl-v {font-size: 1.12rem; font-weight: 600; color: #0F2A47; font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere; line-height: 1.25;}
.rl-s {font-size: .7rem; color: #475569;}
.rl-sim .rl-v {color: #B45309;}
.rl-bad .rl-v {color: #9A1B1B;}
.rl-note {border-left: 3px solid #0F766E; padding: .3rem .7rem; background: #FFFFFF;
  font-size: .85rem; color: #1E293B; margin: .3rem 0 .6rem 0;}
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
def thresholds() -> dict:
    return derive_switching_thresholds(CFG.ber_target, CFG.modulations)


@st.cache_data(show_spinner="Menjalankan mesin Python: path loss, link budget, realisasi bersama")
def cached_curves(env: str, tx_dbm: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    curves = pd.concat(
        [
            evaluate_scenario_curves(
                f, env, DISTANCES_KM, tuple(SCENARIOS), tx_dbm, N_DRAWS, CFG.default_seed, CFG
            )
            for f in CFG.carrier_frequencies_mhz
        ],
        ignore_index=True,
    )
    return curves, summarize_coverage(curves, CFG)


@st.cache_data(show_spinner="Monte Carlo bit-level sedang berjalan")
def cached_mc(modulation: str, ebn0_db: float, n_bits: int) -> dict:
    return validate_operating_point(modulation, ebn0_db, n_bits, seed=CFG.default_seed)


def read_csv(name: str) -> pd.DataFrame | None:
    p = RES / name
    return pd.read_csv(p) if p.exists() else None


def evaluate_link(freq, env, dist, ptx, shadow, strat, rb_manual, mod_manual) -> dict:
    """Satu titik link dari mesin: path loss, link budget, pilihan konfigurasi, BER analitis."""
    thr = thresholds()
    _, sigma = get_ci_parameters(env)
    margin = (
        analytical_shadow_margin_db(sigma, 1.0 - CFG.outage_target) if shadow == "margin95" else 0.0
    )
    pl = float(median_path_loss_db(dist * 1000.0, freq, env)) + margin
    if strat == "MANUAL":
        mod, rb = mod_manual, int(rb_manual)
        ok_option = True
    else:
        sel = select_operating_point(pl, strat, ptx, CFG, thr)
        idx = int(sel.index[0])
        ok_option = idx >= 0
        if ok_option:
            mod, rb = sel.options[idx]
        else:
            mod, rb = "Outage", min(r for _, r in sel.options)
    lb = compute_link_budget(pl, n_rb=rb, tx_power_dbm=ptx)
    out = {
        "pl": pl,
        "margin": margin,
        "pr": float(lb.pr_dbm),
        "noise": float(lb.noise_dbm),
        "snr": float(lb.snr_db),
        "rb": rb,
        "mod": mod,
        "b_hz": active_bandwidth_hz(rb, CFG.rb_bandwidth_hz),
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
    """Telemetry strip. Setiap sel: (label, nilai, sub, kelas)."""
    html = "".join(
        f'<div class="rl-cell {c}"><div class="rl-l">{a}</div><div class="rl-v">{b}</div>'
        f'<div class="rl-s">{s}</div></div>'
        for a, b, s, c in cells
    )
    st.markdown(f'<div class="rl-strip">{html}</div>', unsafe_allow_html=True)


def seg(label: str, options, key: str, disabled: bool = False, fmt=str):
    st.session_state.setdefault(key, options[0] if key not in DEFAULTS else DEFAULTS[key])
    val = st.segmented_control(
        label, options, key=key, format_func=fmt, selection_mode="single", disabled=disabled
    )
    return val if val is not None else (DEFAULTS.get(key) or options[0])


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
}
for _k, _v in DEFAULTS.items():
    st.session_state.setdefault(_k, _v)


def apply_preset() -> None:
    """Preset tepi sel: 900 MHz NLOS 5 km, baseline S0 gagal, S3 melayani."""
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.session_state.pop("mc", None)


# ------------------------------------------------------------------ header
st.markdown(
    f"""<div class="rl-head"><h1>{PROJECT_NAME}: Simulator Jangkauan Uplink Adaptif</h1>
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
        help="900 MHz NLOS, 5 km, 23 dBm, S3. Baseline S0 mengalami outage di jarak ini.",
    )
    freq = seg(
        "Frekuensi pembawa (MHz)",
        list(CFG.carrier_frequencies_mhz),
        "freq",
        fmt=lambda x: f"{x:.0f}",
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
        "Strategi", list(STRATEGY_LABEL), format_func=STRATEGY_LABEL.get, key="strat"
    )
    manual = strat == "MANUAL"
    st.caption(
        "Mode manual: RB dan modulasi di bawah dikunci pengguna."
        if manual
        else "Mode adaptif: optimizer memilih modulasi dan RB. Kontrol manual dinonaktifkan."
    )
    rb_m = seg("Jumlah RB (manual)", list(CFG.active_rb_choices), "rb", disabled=not manual)
    mod_m = seg("Modulasi (manual)", list(CFG.modulations), "mod", disabled=not manual)
    n_bits = st.select_slider(
        "Bit per kanal (Monte Carlo)", (100_000, 500_000, 1_000_000), key="nbits"
    )
    st.caption(
        f"Target BER {CFG.ber_target:g}. Target outage {CFG.outage_target:.0%}. Seed {CFG.default_seed}. Berjalan offline."
    )

try:
    curves, summary = cached_curves(env, float(ptx))
    thr = thresholds()
    link = evaluate_link(freq, env, dist, ptx, shadow, strat, rb_m, mod_m)
except ValueError as exc:
    st.error(f"Parameter ditolak oleh mesin: {exc}")
    st.stop()

tab_sim, tab_cov, tab_res, tab_met = st.tabs(
    ["A. Simulator langsung", "B. Visualisasi cakupan", "C. Hasil penelitian", "D. Metodologi"]
)

# ================================================================== A. LIVE SIMULATOR
with tab_sim:
    row = curves[
        (curves.freq_mhz == freq)
        & (curves.environment == env)
        & np.isclose(curves.distance_km, dist)
    ].set_index("scenario")
    cur = row.loc[strat] if strat in row.index else None
    in_outage = not link["ok"]
    ber_main = link.get("ber_awgn") if chan == "AWGN" else link.get("ber_ray")
    ber_label = "BER analitis AWGN" if chan == "AWGN" else "BER rata-rata Rayleigh tanpa CSI"
    if cur is None:
        outage_txt, outage_sub = "n/a", "mode manual"
    elif chan == "AWGN":
        outage_txt, outage_sub = f"{cur.shadow_outage_prob:.1%}", "SIMULATED, shadowing"
    else:
        outage_txt, outage_sub = (
            f"{cur.fading_outage_prob:.1%}",
            "SIMULATED, shadowing + Rayleigh CSI",
        )
    strip(
        [
            (
                "Path loss CI (THEORETICAL)",
                f"{link['pl']:.1f} dB",
                f"margin shadowing {link['margin']:.1f} dB",
                "",
            ),
            ("Daya terima Pr", f"{link['pr']:.1f} dBm", f"P per RB {link['p_rb']:.1f} dBm", ""),
            (
                "Noise floor",
                f"{link['noise']:.1f} dBm",
                f"B aktif {link['b_hz'] / 1e6:.2f} MHz",
                "",
            ),
            (
                "SNR (Es/N0)",
                f"{link['snr']:.1f} dB",
                f"Eb/N0 {link['ebn0']:.1f} dB" if not in_outage else "tanpa konfigurasi layak",
                "",
            ),
            (
                "Konfigurasi aktif",
                "Outage" if in_outage else f"{link['mod']} x {link['rb']} RB",
                "optimizer" if not manual else "manual",
                "rl-bad" if in_outage else "",
            ),
            (
                ber_label,
                "n/a" if in_outage or ber_main is None else f"{ber_main:.2e}",
                f"target {CFG.ber_target:g}",
                "",
            ),
            ("Laju nominal", fmt_rate(link["rate"]), "tanpa coding, bukan throughput LTE", ""),
            ("Probabilitas outage", outage_txt, outage_sub, "rl-sim"),
        ]
    )
    if manual and not link["ok"] and link["mod"] != "Outage":
        st.warning(
            f"Konfigurasi manual tidak layak: Eb/N0 {link['ebn0']:.1f} dB lebih rendah dari ambang "
            f"{thr[link['mod']]['ebn0_db']:.2f} dB untuk {link['mod']}. Link dinyatakan outage."
        )
    if in_outage and not manual:
        st.error(
            "Tidak ada kombinasi modulasi dan RB yang memenuhi BER target pada jarak ini. Coba kurangi jarak atau naikkan daya."
        )

    c1, c2 = st.columns([1.15, 1])
    with c1:
        st.markdown("**SNR vs jarak (median path loss, THEORETICAL)**")
        _, sig = get_ci_parameters(env)
        off = link["margin"]
        fig = go.Figure()
        styles = {
            (900.0, 1): (NAVY, "solid"),
            (900.0, 25): (NAVY, "dot"),
            (1800.0, 1): (TEAL, "solid"),
            (1800.0, 25): (TEAL, "dot"),
        }
        for (f, rb), (color, dash) in styles.items():
            pl_d = np.asarray(median_path_loss_db(DISTANCES_KM * 1000.0, f, env), dtype=float) + off
            snr_d = np.atleast_1d(compute_link_budget(pl_d, n_rb=rb, tx_power_dbm=ptx).snr_db)
            fig.add_scatter(
                x=DISTANCES_KM,
                y=snr_d,
                name=f"{f:.0f} MHz, {rb} RB",
                line=dict(color=color, dash=dash, width=2),
            )
        for m in CFG.modulations:
            if m == "BPSK":
                continue
            fig.add_hline(
                y=thr[m]["esn0_db"],
                line_dash="dot",
                line_color="#94A3B8",
                line_width=1,
                annotation_text=f"{m} (Es/N0 {thr[m]['esn0_db']:.1f} dB)",
                annotation_position="top right",
                annotation_font_size=10,
            )
        fig.add_vline(x=dist, line_color=AMBER, line_width=1.5)
        fig.update_layout(
            height=360,
            margin=dict(l=10, r=10, t=10, b=10),
            template="plotly_white",
            xaxis_title="Jarak (km)",
            yaxis_title="SNR (dB)",
            legend=dict(orientation="h", y=-0.25),
        )
        st.plotly_chart(fig, width="stretch")
        st.caption(
            "Garis penuh: 1 RB (jangkauan maksimum). Titik: 25 RB. Garis abu: ambang Es/N0 pada BER 1e-2 (QPSK sama dengan BPSK pada Eb/N0, berbeda 3 dB pada Es/N0)."
        )
    with c2:
        st.markdown("**Simulasi Monte Carlo bit-level (SIMULATED)**")
        base = evaluate_link(freq, env, dist, ptx, shadow, "S0", rb_m, mod_m)
        st.write(
            f"Dioptimalkan: **{'Outage' if in_outage else link['mod'] + ' x ' + str(link['rb']) + ' RB'}**. "
            f"Baseline S0: **{'Outage' if not base['ok'] else 'QPSK x 25 RB'}**."
        )
        key_now = (freq, env, dist, ptx, shadow, strat, rb_m, mod_m, n_bits)
        if st.button("Jalankan simulasi Monte Carlo", key="run_mc", disabled=in_outage):
            st.session_state["mc"] = {
                "key": key_now,
                "opt": cached_mc(link["mod"], link["ebn0"], int(n_bits)),
                "base": cached_mc(base["mod"], base["ebn0"], int(n_bits)) if base["ok"] else None,
            }
        mc = st.session_state.get("mc")
        if in_outage:
            st.info("Tidak ada transmisi yang dapat disimulasikan pada konfigurasi outage.")
        elif mc is None:
            st.info(
                "Tekan tombol untuk mengirim bit acak melalui kanal AWGN dan Rayleigh dari mesin Python."
            )
        elif mc["key"] != key_now:
            st.warning(
                "Parameter berubah sejak simulasi terakhir. Jalankan ulang untuk memperbarui hasil."
            )
        else:
            ch = "awgn" if chan == "AWGN" else "rayleigh"
            for name, res in (("Dioptimalkan", mc["opt"]), ("Baseline S0", mc["base"])):
                if res is None:
                    st.write(f"**{name}**: outage, tidak ada transmisi.")
                    continue
                ci = res[f"ci_low_{ch}"], res[f"ci_high_{ch}"]
                ci_txt = "" if ci[0] is None else f", CI 95% [{ci[0]:.1e}, {ci[1]:.1e}]"
                st.write(
                    f"**{name}** ({res['modulation']}, Eb/N0 {res['ebn0_db']:.2f} dB, {res['n_bits']:,} bit): "
                    f"BER MC AWGN {res['mc_ber_awgn']:.2e} (teori {res['theory_ber_awgn']:.2e}); "
                    f"BER MC Rayleigh tanpa CSI {res['mc_ber_rayleigh']:.2e} (teori {res['theory_ber_rayleigh']:.2e}){ci_txt}."
                )
            st.caption(
                "Rayleigh tanpa CSI adalah BER rata-rata atas seluruh fading. Dengan CSI sesaat, link hanya mengirim "
                "saat Eb/N0 sesaat memenuhi ambang, sehingga BER bersyarat paling tinggi 1e-2 (lihat outage di strip)."
            )

    mc = st.session_state.get("mc")
    if mc and mc["key"] == key_now and not in_outage:
        st.markdown(
            f"**Konstelasi diterima, kanal {'AWGN' if chan == 'AWGN' else 'Rayleigh (diekualisasi ZF)'}: sampel nyata dari mesin Python**"
        )
        ch = "awgn" if chan == "AWGN" else "rayleigh"
        cols = st.columns(2)
        for col, name, res in (
            (cols[0], "Dioptimalkan", mc["opt"]),
            (cols[1], "Baseline S0", mc["base"]),
        ):
            if res is None:
                col.info(f"{name}: outage, tidak ada sampel.")
                continue
            smp = res[f"samples_{ch}"]
            ref, _ = get_constellation(res["modulation"])
            f4 = go.Figure()
            f4.add_scatter(
                x=smp.real,
                y=smp.imag,
                mode="markers",
                name="diterima (SIMULATED)",
                marker=dict(size=4, color=AMBER, opacity=0.55),
            )
            f4.add_scatter(
                x=np.real(ref),
                y=np.imag(ref),
                mode="markers",
                name="titik ideal",
                marker=dict(size=9, color=NAVY, symbol="x"),
            )
            f4.update_layout(
                height=330,
                margin=dict(l=10, r=10, t=30, b=10),
                template="plotly_white",
                title=f"{name}: {res['modulation']}",
                xaxis_title="I",
                yaxis_title="Q",
                yaxis_scaleanchor="x",
                legend=dict(orientation="h", y=-0.25),
            )
            col.plotly_chart(f4, width="stretch")

    st.markdown(
        f"**Perbandingan strategi pada {dist:g} km, {freq:.0f} MHz {env}** (realisasi shadowing dan fading yang sama untuk semua strategi)"
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
            "Outage shadowing": (r.shadow_outage_prob * 100).round(1).astype(str) + "%",
            "Outage shadowing+Rayleigh CSI": (r.fading_outage_prob * 100).round(1).astype(str)
            + "%",
            "Laju efektif CSI (Mbit/s)": (r.fading_effective_rate_bps / 1e6).round(2),
            "BER bersyarat rata-rata": r.fading_cond_ber_mean.map(
                lambda x: "n/a" if pd.isna(x) else f"{x:.1e}"
            ),
        }
    )
    st.dataframe(tbl, hide_index=True, width="stretch")
    st.caption(
        "Laju efektif menghitung outage sebagai 0. Laju nominal tanpa coding, bukan throughput LTE."
    )

    st.markdown("**Perbandingan frekuensi pada jarak yang sama**")
    ft = []
    for f in CFG.carrier_frequencies_mhz:
        lk = evaluate_link(f, env, dist, ptx, shadow, "S3", rb_m, mod_m)
        s3 = summary[(summary.freq_mhz == f) & (summary.scenario == "S3")].iloc[0]
        ft.append(
            {
                "Frekuensi": f"{f:.0f} MHz",
                "Path loss (dB)": round(lk["pl"], 1),
                "SNR 25 RB (dB)": round(
                    float(compute_link_budget(lk["pl"], n_rb=25, tx_power_dbm=ptx).snr_db), 1
                ),
                "SNR 1 RB (dB)": round(
                    float(compute_link_budget(lk["pl"], n_rb=1, tx_power_dbm=ptx).snr_db), 1
                ),
                "Pilihan S3": "Outage" if lk["mod"] == "Outage" else f"{lk['mod']} x {lk['rb']} RB",
                "Laju nominal": fmt_rate(lk["rate"]),
                "Radius median S3": s3.radius_median_label,
                "Radius 5% outage + fading": s3.radius_fading_label,
            }
        )
    st.dataframe(pd.DataFrame(ft), hide_index=True, width="stretch")

# ================================================================== B. COVERAGE
with tab_cov:
    st.markdown(
        '<div class="rl-note"><b>Model radial hipotetis.</b> Bukan peta cakupan geografis lapangan. '
        "Zona modulasi dihitung sekali per jarak radial (45 titik, 1 sampai 12 km) oleh optimizer Python, "
        "lalu digambar sebagai cincin konsentris tanpa medan, halangan, atau sektor antena.</div>",
        unsafe_allow_html=True,
    )
    zsc = st.selectbox(
        "Strategi zona",
        list(SCENARIOS),
        index=3,
        format_func=lambda s: f"{s}: {SCENARIOS[s]['label']}",
        key="zone_sc",
    )
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[f"{f:.0f} MHz {env}, {zsc}" for f in CFG.carrier_frequencies_mhz],
        horizontal_spacing=0.06,
    )
    seen: set[str] = set()
    theta = np.linspace(0, 2 * np.pi, 181)

    def circle(rad: float) -> tuple[np.ndarray, np.ndarray]:
        return rad * np.cos(theta), rad * np.sin(theta)

    rmax = float(CFG.distance_max_km)
    for ci, f in enumerate(CFG.carrier_frequencies_mhz, start=1):
        g = curves[(curves.freq_mhz == f) & (curves.scenario == zsc)].sort_values("distance_km")
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
            x, y = circle(outer)
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="lines",
                    fill="toself",
                    fillcolor=MOD_COLOR[lab],
                    line=dict(color="#FFFFFF", width=1),
                    name=lab,
                    legendgroup=lab,
                    showlegend=lab not in seen,
                    hoverinfo="name+text",
                    text=f"{lab}: {inner:.2f} a {outer:.2f} km",
                ),
                row=1,
                col=ci,
            )
            seen.add(lab)
        srow = summary[(summary.freq_mhz == f) & (summary.scenario == zsc)].iloc[0]
        for rad, lab, color, dash in (
            (
                srow.radius_stochastic_km,
                f"Radius andal 95% (shadowing) {srow.radius_stochastic_label}",
                NAVY,
                "dash",
            ),
            (
                srow.radius_fading_km,
                f"Radius andal 95% (+Rayleigh CSI) {srow.radius_fading_label}",
                AMBER,
                "dot",
            ),
        ):
            if rad > 0:
                x, y = circle(float(rad))
                fig.add_trace(
                    go.Scatter(
                        x=x,
                        y=y,
                        mode="lines",
                        line=dict(color=color, dash=dash, width=2.5),
                        name=f"{f:.0f} MHz: {lab}",
                        hoverinfo="name",
                    ),
                    row=1,
                    col=ci,
                )
        fig.add_trace(
            go.Scatter(
                x=[0],
                y=[0],
                mode="markers+text",
                text=["BTS"],
                textposition="bottom center",
                marker=dict(size=11, color=INK, symbol="diamond"),
                name="BTS",
                showlegend=ci == 1,
                legendgroup="BTS",
            ),
            row=1,
            col=ci,
        )
        fig.add_trace(
            go.Scatter(
                x=[dist],
                y=[0],
                mode="markers+text",
                text=[f"UE {dist:g} km"],
                textposition="top center",
                marker=dict(size=11, color="#FFFFFF", line=dict(color=INK, width=2.5)),
                name="UE",
                showlegend=ci == 1,
                legendgroup="UE",
            ),
            row=1,
            col=ci,
        )
    for ci in (1, 2):
        fig.update_xaxes(range=[-13, 13], title_text="km", row=1, col=ci, zeroline=False)
        fig.update_yaxes(
            range=[-13, 13], row=1, col=ci, scaleanchor=f"x{'' if ci == 1 else ci}", zeroline=False
        )
    fig.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=40, b=10),
        template="plotly_white",
        legend=dict(orientation="h", y=-0.12),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Cincin berwarna: zona median path loss (deterministik, THEORETICAL). Garis putus-putus: radius dengan outage 5% atau kurang "
        "(SIMULATED, realisasi acak bersama). Abu-abu: outage. Radius 12 km adalah batas rentang evaluasi, ditandai '>=12 km' bila tercapai."
    )
    zt = summary[summary.scenario == zsc][
        [
            "freq_mhz",
            "radius_median_label",
            "radius_margin95_label",
            "radius_stochastic_label",
            "radius_fading_label",
        ]
    ]
    zt = zt.rename(
        columns={
            "freq_mhz": "MHz",
            "radius_median_label": "Median PL (deterministik)",
            "radius_margin95_label": "Margin 95% (analitis)",
            "radius_stochastic_label": "Andal 95%, shadowing",
            "radius_fading_label": "Andal 95%, shadowing + Rayleigh CSI",
        }
    )
    st.dataframe(zt, hide_index=True, width="stretch")

# ================================================================== C. RESULTS
with tab_res:
    st.markdown(
        '<div class="rl-note">Hasil publikasi dibaca dari <code>outputs/</code> (23 dBm, seed 42, 5000 realisasi bersama, '
        "grid 1 sampai 12 km). Label: THEORETICAL = median path loss dan rumus tertutup. SIMULATED = shadowing, Rayleigh, dan Monte Carlo bit-level. "
        "Laju nominal tanpa coding, bukan throughput LTE.</div>",
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
                    height=340,
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

# ================================================================== D. METHODOLOGY
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
- **Ambang BER {CFG.ber_target:g}:** Eb/N0 (dB) {", ".join(f"{m} {thr[m]['ebn0_db']:.2f}" for m in CFG.modulations)}. Es/N0 = Eb/N0 + 10 log10 k.
- **Optimasi modulasi-bandwidth:** tiap opsi (modulasi, N_RB) layak bila Eb/N0 memenuhi ambang. Optimizer memilih opsi layak dengan laju nominal B x log2 M tertinggi. Mengurangi RB menaikkan SNR per simbol (daya terkonsentrasi, noise lebih kecil) dengan mengorbankan laju, sehingga jangkauan membesar.
- **Rayleigh:** adaptasi memakai CSI sesaat. Pada tiap realisasi, link memilih opsi dengan Eb/N0 sesaat yang memenuhi ambang AWGN. BER bersyarat adalah BER AWGN pada Eb/N0 sesaat tersebut. BER rata-rata Rayleigh tanpa CSI tidak dipakai untuk adaptasi.
- **Strategi:** {"; ".join(f"{k} {v['label']}" for k, v in SCENARIOS.items())}. Semua strategi memakai realisasi shadowing dan fading yang sama.
- **Keandalan:** cakupan median path loss bersifat deterministik dan bukan ukuran keandalan. Keandalan stokastik memakai outage 5% atau kurang.
"""
    )
    st.markdown("#### Batasan")
    st.markdown(
        """
- Hanya 900 dan 1800 MHz. 700 MHz di luar cakupan penelitian.
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
