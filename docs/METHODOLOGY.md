# Methodology — Mathematical Specification (Phase 02)

**Status:** Locked — Phase 03 implementation complete. Any change to equations or scientific assumptions must be recorded in `docs/DECISIONS.md` with mathematical justification.

---

## 1. Scope and Assumptions

RuralLink is an adapted, simplified link-level simulator for a power-limited uplink—**not** a full LTE/5G-NR protocol stack or an exact replication of any single paper.

- **Single-user, power-limited uplink:** Total UE transmit power $P_t = 23\text{ dBm}$ is fixed regardless of the number of active Resource Blocks ($N_{\text{RB}}$).
- **Noise-limited system:** No co-channel or adjacent-channel interference is modeled.
- **Uncoded digital modulation:** BPSK, QPSK, 16-QAM, and 64-QAM without forward error correction (FEC), pilots, cyclic prefix (CP), or scheduling/protocol overhead.
- **Complex baseband equivalent:** All modulation, channel, and detection operations are performed in complex baseband with average symbol energy $E_s = 1$.
- **Ideal synchronization and CSI:** Perfect timing, carrier frequency synchronization, and coherent channel state information (CSI) at the receiver.
- **Channel models:** Flat AWGN or flat Rayleigh fading, combined with log-normal large-scale shadowing.
- **Environment:** Hypothetical Indonesian rural/3T scenario using Park et al. (2023) 1400 MHz CI parameters extrapolated to 900/1800 MHz and Yogapratama Table IV hardware parameters. No geographic field calibration or actual LTE throughput claims are made.
- **Data labeling:** Every output is explicitly labeled as **theoretical**, **simulated** (Monte Carlo, bit-level), or **illustrative**.

The architecture separates five layers:
1. **Propagation** (`src/propagation.py`)
2. **Link Budget** (`src/link_budget.py`)
3. **Modulation & Theoretical BER** (`src/modulation.py`)
4. **Channel & Reception** (`src/channels.py`)
5. **Metrics & Validation** (`src/metrics.py`)

*(Joint adaptive optimization in `src/adaptive.py` is reserved for Phase 04.)*

---

## 2. Default Parameters

Centralized in `config.py` with explicit units and validation:

| Parameter | Symbol | Default Value | Units | Source / Basis |
|---|---|---|---|---|
| Carrier frequencies | $f_c$ | `900, 1800` | MHz | Research scope (Indonesian rural LTE) |
| Nominal channel bandwidth | $B_{\text{ch}}$ | `5.0e6` (`5`) | Hz (MHz) | Yogapratama Table IV |
| Active RB choices | $N_{\text{RB}}$ | `[1, 2, 5, 10, 25]` | RBs | Sub-band allocation grid ($\le 25$ RBs) |
| RB bandwidth | $B_{\text{RB}}$ | `180,000` | Hz | LTE PRB width (Reddy Table 1) |
| Max active bandwidth | $B_{\text{active,max}}$ | `4.5e6` | Hz | $25 \times 180\text{ kHz}$ |
| UE transmit power | $P_t$ | `23.0` | dBm | Yogapratama Table IV / Reddy Table 1 |
| UE antenna gain | $G_t$ | `0.0` | dBi | Yogapratama Table IV |
| BTS receive antenna gain | $G_r$ | `11.0` | dBi | Yogapratama Table IV |
| Feeder loss | $L_{\text{feeder}}$ | `5.0` | dB | Yogapratama Table IV |
| Body loss | $L_{\text{body}}$ | `3.0` | dB | Yogapratama Table IV |
| Receiver noise figure | $\mathrm{NF}$ | `4.0` | dB | Yogapratama Table IV |
| Thermal noise density | $N_0^{\text{th}}$ | `-174.0` | dBm/Hz | $k_B T_0$ at $290\text{ K}$ |
| Distance range | $d$ | `1.0 – 12.0` | km | Rural cell evaluation range |
| Target BER | $\mathrm{BER}_{\text{target}}$ | `1e-2` | — | Khan (2025) Table 9 |
| Target outage probability | $P_{\text{out,target}}$ | `0.05` (`5%`) | — | 95% reliability target |
| Modulations | — | `BPSK, QPSK, 16-QAM, 64-QAM` | — | Uncoded $M \in \{2, 4, 16, 64\}$ |
| Default random seed | `seed` | `42` | — | Deterministic reproducibility |

---

## 3. Propagation Model (`src/propagation.py`)

Standard Close-In (CI) free-space reference path loss model with reference distance $d_0 = 1\text{ m}$ (Park et al., 2023, Eq. 3):

$$\mathrm{PL}(f_{\text{GHz}}, d_m)\text{ [dB]} = 32.4 + 20\log_{10}(f_{\text{GHz}}) + 10 \, n \log_{10}(d_m) + X_\sigma$$

where $f_{\text{GHz}} = f_{\text{MHz}} / 1000$, $d_m \ge 1\text{ m}$, and $X_\sigma \sim \mathcal{N}(0, \sigma^2)$ in dB.

- **LOS (Park 2023, Table II, 1400 MHz):** $n = 2.16$, $\sigma = 3.07\text{ dB}$.
- **NLOS (Park 2023, Table II, 1400 MHz):** $n = 2.56$, $\sigma = 11.40\text{ dB}$.
- **Median path loss:** $X_\sigma = 0$.
- **Stochastic path loss:** $X_\sigma$ sampled i.i.d. from $\mathcal{N}(0, \sigma^2)$.
- **Optional analytical 95% shadow margin:** $M_{\text{SF},95\%} = 1.645 \times \sigma$ (dB), corresponding to $\Phi^{-1}(0.95) \approx 1.64485$.
- **Strict guardrails:**
  - Do **not** use the diffraction-adjusted exponent without a diffraction loss component $\phi$.
  - Do **not** apply the deterministic shadow margin on top of random shadowing $X_\sigma$ in the same reliability calculation (no double counting).

---

## 4. Link Budget & Energy Normalization (`src/link_budget.py`)

All quantities maintain strict unit separation (`dB`, `dBm`, `W`, `Hz`, `MHz`, `m`, `km`):

$$\begin{aligned}
P_r\text{ [dBm]} &= P_t\text{ [dBm]} + G_t\text{ [dBi]} + G_r\text{ [dBi]} - \mathrm{PL}\text{ [dB]} - L_{\text{feeder}}\text{ [dB]} - L_{\text{body}}\text{ [dB]} \\
B_{\text{active}}\text{ [Hz]} &= N_{\text{RB}} \times 180{,}000 \\
N_{\text{dBm}}\text{ [dBm]} &= -174 + 10\log_{10}(B_{\text{active}}) + \mathrm{NF}\text{ [dB]} \\
\mathrm{SNR}_{\text{dB}} &= P_r\text{ [dBm]} - N_{\text{dBm}}\text{ [dBm]} \\
\mathrm{SNR}_{\text{linear}} &= 10^{\mathrm{SNR}_{\text{dB}} / 10} \\
P_{\text{RB}}\text{ [dBm]} &= P_t\text{ [dBm]} - 10\log_{10}(N_{\text{RB}})
\end{aligned}$$

- **Bandwidth-reduction SNR gain:** When reducing active RBs from $N_{\text{RB,base}}$ to $N_{\text{RB,new}}$ at constant total $P_t$, the noise power decreases by $10\log_{10}(N_{\text{RB,base}} / N_{\text{RB,new}})$:
  $$\Delta \mathrm{SNR}_{\text{dB}} = 10\log_{10}\left(\frac{N_{\text{RB,base}}}{N_{\text{RB,new}}}\right)$$
  For $25 \to 1$ RB: $+13.9794\text{ dB}$; for $25 \to 5$ RBs: $+6.9897\text{ dB}$. This gain is **already captured** by $B_{\text{active}}$ in $N_{\text{dBm}}$ and must **never** be added a second time.

### Energy Normalization, Data Rate, and Spectral Efficiency
Assuming ideal symbol rate $R_s = B_{\text{active}}$ (symbols/s) and $k = \log_2(M)$ bits/symbol:
$$\begin{aligned}
\frac{E_s}{N_0} &= \mathrm{SNR}_{\text{linear}}, \qquad \frac{E_b}{N_0} = \frac{\mathrm{SNR}_{\text{linear}}}{k} \\
\left(\frac{E_b}{N_0}\right)_{\text{dB}} &= \mathrm{SNR}_{\text{dB}} - 10\log_{10}(k) \\
R_b\text{ [bps]} &= B_{\text{active}} \cdot k \\
\eta_{\text{active}} &= \frac{R_b}{B_{\text{active}}} = k\text{ [bps/Hz]}, \qquad \eta_{\text{channel}} = \frac{R_b}{5 \times 10^6}\text{ [bps/Hz]}
\end{aligned}$$

Optional Shannon capacity reference (never labeled as modulation throughput):
$$C\text{ [bps]} = B_{\text{active}} \log_2(1 + \mathrm{SNR}_{\text{linear}})$$

---

## 5. Digital Modulation & Theoretical BER (`src/modulation.py`)

### Constellations and Gray Mapping
- **BPSK ($M=2, k=1$):** $\{-1, +1\}$ (`0 -> -1`, `1 -> +1`), $E_s = 1$.
- **QPSK ($M=4, k=2$):** $\frac{1}{\sqrt{2}}(\pm 1 \pm j)$ with Gray-coded 2-bit labels, $E_s = 1$.
- **16-QAM ($M=16, k=4$):** Square constellation on $\{-3, -1, +1, +3\}/\sqrt{10}$ with 2-bit Gray code per dimension, $E_s = 1$.
- **64-QAM ($M=64, k=6$):** Square constellation on $\{-7, \ldots, +7\}/\sqrt{42}$ with 3-bit Gray code per dimension, $E_s = 1$.
- **Demapping:** Exact ML nearest-neighbor per dimension (1D PAM slicing).

### Theoretical BER

Let $Q(x) = \frac{1}{2}\operatorname{erfc}(x/\sqrt{2})$ and $\gamma_b = E_b/N_0$ (linear).

1. **AWGN — BPSK and Gray-coded QPSK (exact):**
   $P_b = Q\left(\sqrt{2\gamma_b}\right)$

2. **AWGN — Square Gray-coded $M$-QAM:**
   - Exact (Cho & Yoon, 2002) implemented and used for thresholds.
   - Nearest-neighbor approximation available as `method='approx'` for reference only.

3. **Rayleigh Fading — BPSK and QPSK (exact closed-form):**
   $P_b = \frac{1}{2}\left(1 - \sqrt{\frac{\bar{\gamma}_b}{1 + \bar{\gamma}_b}}\right)$

4. **Rayleigh Fading — Square $M$-QAM:**
   Numerical integration of exact conditional AWGN BER over exponentially distributed instantaneous SNR via `scipy.integrate.quad`.

5. **Switching Thresholds:**
   Derived numerically via `scipy.optimize.brentq` on exact AWGN BER = $10^{-2}$.

**Verified switching thresholds at BER = 1e-2 (AWGN):**
| Modulation | Eb/N0 (dB) | Es/N0 (dB) |
|---|---|---|
| BPSK | 4.32 | 4.32 |
| QPSK | 4.32 | 7.33 |
| 16-QAM | 7.88 | 13.90 |
| 64-QAM | 11.95 | 19.74 |

---

## 6. Channel Engine (`src/channels.py`)

For normalized transmitted symbols $x$ ($\mathbb{E}[|x|^2] = 1$) and linear symbol SNR $\gamma_s = E_s / N_0$, noise variance $N_0 = 1 / \gamma_s$:
- **AWGN:** $y = x + w$, where $w = \sqrt{N_0/2}\,(n_I + j\,n_Q)$, $n_I, n_Q \sim \mathcal{N}(0, 1)$ i.i.d.
- **Rayleigh (Independent & Block):** $y = h \odot x + w$, $h = (h_I + j\,h_Q)/\sqrt{2}$, $\mathbb{E}[|h|^2] = 1$.
- **Coherent reception (perfect CSI):** Zero-forcing equalization $\hat{x} = y / h$ with safety floor.
- **SNR Distinction:** Median SNR (median PL) vs. Shadowed average SNR (stochastic PL) vs. Instantaneous faded SNR ($\gamma_{\text{inst}} = \gamma_{\text{avg}} |h|^2$).

---

## 7. Statistical Validation (`src/metrics.py`)

- **Sample targets:** Quick = `100,000` bits; Research = `1,000,000` bits.
- **Confidence intervals:** Wilson 95% CI for binomial; rule-of-three ($3/N$) upper bound when zero errors observed.
- **Block-fading caveat:** Independent-bit CIs are not valid for correlated block-fading samples.

---

## 8. Known Implementation Limitations

- CI path loss parameters are from Park (2023) at 1400 MHz and extrapolated to 900/1800 MHz — not measured in Indonesian terrain.
- No interference, Doppler, multi-path, or pilot overhead modeled.
- Shannon capacity shown as reference only; actual achievable rate is the nominal uncoded rate $R_b = B_{\text{active}} k$.
- Joint adaptive optimization (`src/adaptive.py`) reserved for Phase 04.
