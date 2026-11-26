(function () {
  "use strict";

  const MOD_COLOR = {
    "64-QAM": "#1E3A8A",
    "16-QAM": "#0D9488",
    "QPSK": "#3B82F6",
    "BPSK": "#D97706",
    "Outage": "#E2E8F0",
  };
  const FREQ_COLORS = {
    700: "#1D4ED8",
    900: "#0F2A47",
    1800: "#0F766E",
  };
  const STRAT_COLORS = {
    S0: "#64748B",
    S1: "#7FA6C9",
    S2: "#B45309",
    S3: "#0F766E",
    R0: "#0F2A47",
  };
  const MC_BIT_LABELS = {
    100: "10² (100)",
    1000: "10³ (1.000)",
    10000: "10⁴ (10.000)",
    100000: "10⁵ (100.000)",
    1000000: "10⁶ (1.000.000)",
  };

  const SNR_W = 660;
  const SNR_H = 310;
  const SNR_PAD = { l: 52, r: 22, t: 18, b: 40 };
  const PREVIEW_MAX_BITS = 10000;

  const DEFAULTS = {
    freq_mhz: 900,
    env: "NLOS",
    shadow: "median",
    channel: "AWGN",
    dist_km: 5.0,
    tx_power_dbm: 23,
    ber_target: 0.01,
    strategy: "S3",
    rb_manual: 25,
    mod_manual: "QPSK",
    n_bits: 100000,
    zone_strategy: "S3",
    show_reliability: false,
    mc_view: "opt_vs_s0",
    live_mc: true,
  };

  const state = { ...DEFAULTS };
  let lastOpData = null;
  let lastZonesData = null; // distance-independent radial zones + S3 radius summary
  let lastStochDistData = null; // distance-dependent outage + strategy table
  let lastValidMcResult = null;
  let lastValidMcKey = null;
  let lastValidMcMeta = null;
  let mcStatusMode = "idle"; // idle | updating | ready | stale | error | outage
  let mcLastError = "";
  let workbenchApiError = "";

  let resultsData = null;
  let resultsEnv = "NLOS";
  const resultsStrategies = new Set(["S0", "S1", "S2", "S3", "R0"]);
  let methodologyLoaded = false;
  let glossaryCache = null;

  const opCache = new Map();
  const zoneCache = new Map();
  const stochDistCache = new Map();
  const mcCache = new Map();

  let opSeq = 0;
  let stochSeq = 0;
  let mcSeq = 0;
  let workbenchSeq = 0;
  let opController = null;
  let stochController = null;
  let mcController = null;
  let mcInFlight = false;

  let analyticalTimer = null;
  let mcSettleTimer = null;
  let mcDragThrottleAt = 0;
  let dragRafId = null;
  let isDraggingSnr = false;
  let activePointerId = null;

  function fmtIdNum(val, decimals) {
    return Number(val).toFixed(decimals).replace(".", ",");
  }

  function currentMcParamKey() {
    return JSON.stringify({
      f: state.freq_mhz,
      e: state.env,
      s: state.shadow,
      d: state.dist_km,
      p: state.tx_power_dbm,
      b: state.ber_target,
      st: state.strategy,
      rb: state.rb_manual,
      mod: state.mod_manual,
      nb: state.n_bits,
    });
  }

  function currentZoneKey() {
    return JSON.stringify({
      e: state.env,
      p: state.tx_power_dbm,
      b: state.ber_target,
      zs: state.zone_strategy,
    });
  }

  function setActiveSegment(attr, value) {
    document.querySelectorAll(`[${attr}]`).forEach((btn) => {
      const match = String(btn.getAttribute(attr)) === String(value);
      btn.classList.toggle("active", match);
      btn.setAttribute("aria-pressed", match ? "true" : "false");
    });
  }

  function syncControlsFromState() {
    setActiveSegment("data-freq", state.freq_mhz);
    setActiveSegment("data-env", state.env);
    setActiveSegment("data-shadow", state.shadow);
    setActiveSegment("data-channel", state.channel);
    setActiveSegment("data-ber", state.ber_target);
    setActiveSegment("data-rb", state.rb_manual);
    setActiveSegment("data-mod", state.mod_manual);
    setActiveSegment("data-nbits", state.n_bits);
    setActiveSegment("data-mcview", state.mc_view);

    document.getElementById("rngDist").value = String(state.dist_km);
    document.getElementById("rngPt").value = String(state.tx_power_dbm);
    document.getElementById("selStrat").value = state.strategy;
    document.getElementById("selZoneStrat").value = state.zone_strategy;
    document.getElementById("chkLiveMc").checked = Boolean(state.live_mc);

    const manual = state.strategy === "MANUAL";
    document.querySelectorAll("[data-rb], [data-mod]").forEach((btn) => {
      btn.disabled = !manual;
    });

    document.getElementById("lblFreq").textContent = `${state.freq_mhz} MHz`;
    document.getElementById("lblEnv").textContent = state.env;
    document.getElementById("hintEnv").textContent =
      state.env === "LOS"
        ? "Park (2023): n = 2,16 · σ = 3,07 dB."
        : "Park (2023): n = 2,56 · σ = 11,40 dB.";
    document.getElementById("lblShadow").textContent =
      state.shadow === "median" ? "Median" : "Margin 95%";
    document.getElementById("lblChannel").textContent =
      state.channel === "AWGN" ? "AWGN" : "Rayleigh (CSI)";
    document.getElementById("lblDist").textContent = `${fmtIdNum(state.dist_km, 2)} km`;
    document.getElementById("lblPt").textContent = `${state.tx_power_dbm} dBm`;
    document.getElementById("lblTargetBer").textContent =
      state.ber_target === 0.001 ? "10⁻³" : "10⁻²";
    document.getElementById("hintStrat").textContent = manual
      ? "Mode manual: RB dan modulasi dikunci."
      : "Mode adaptif: optimizer memilih modulasi & RB.";
    document.getElementById("lblRbManual").textContent = `${state.rb_manual} RB`;
    document.getElementById("lblModManual").textContent = state.mod_manual;
    document.getElementById("lblMcBits").textContent = MC_BIT_LABELS[state.n_bits] || `${state.n_bits}`;
    document.getElementById("mcSmallSampleWarn").hidden = state.n_bits >= 100000;
  }

  function setupCanvas(id, logicalW, logicalH) {
    const cv = document.getElementById(id);
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const targetW = Math.round(logicalW * dpr);
    const targetH = Math.round(logicalH * dpr);
    if (cv.width !== targetW || cv.height !== targetH) {
      cv.width = targetW;
      cv.height = targetH;
    }
    const ctx = cv.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, logicalW, logicalH);
    return { ctx, W: logicalW, H: logicalH };
  }

  function showWorkbenchError(msg) {
    workbenchApiError = msg;
    const bar = document.getElementById("apiErrorBanner");
    if (!bar) return;
    bar.hidden = false;
    bar.textContent = workbenchApiError;
  }

  function clearWorkbenchError() {
    if (!workbenchApiError) return;
    workbenchApiError = "";
    const bar = document.getElementById("apiErrorBanner");
    if (!bar) return;
    bar.hidden = true;
    bar.textContent = "";
  }

  async function fetchJson(url, options) {
    const resp = await fetch(url, options);
    if (!resp.ok) {
      let detail = `HTTP ${resp.status}`;
      try {
        const body = await resp.json();
        if (body && body.detail) detail = body.detail;
      } catch (_) {}
      throw new Error(detail);
    }
    return resp.json();
  }

  function clearTelemetryOnError() {
    ["kpiPl", "kpiPr", "kpiNoise", "kpiSnr", "kpiMod", "kpiBer", "kpiRate", "kpiOutage"].forEach((id) => {
      document.getElementById(id).textContent = "-";
    });
  }

  function updateTelemetryBer() {
    if (!lastOpData) return;
    const act = lastOpData.active;
    const inOutage = !act.ok;
    if (state.channel === "AWGN") {
      document.getElementById("kpiBerLabel").textContent = "BER AWGN (Teori)";
      document.getElementById("kpiBer").textContent =
        inOutage || act.ber_awgn === null ? "n/a" : act.ber_awgn.toExponential(2);
      document.getElementById("kpiBerSub").textContent = `Target ≤ ${state.ber_target}`;
      return;
    }

    if (state.strategy === "MANUAL") {
      document.getElementById("kpiBerLabel").textContent = "BER Rayleigh";
      document.getElementById("kpiBer").textContent =
        inOutage || act.ber_rayleigh === null ? "n/a" : act.ber_rayleigh.toExponential(2);
      document.getElementById("kpiBerSub").textContent = "Tanpa CSI (manual)";
      return;
    }

    const condBer =
      lastStochDistData &&
      lastStochDistData.active_outage &&
      typeof lastStochDistData.active_outage.fading_cond_ber_mean === "number"
        ? lastStochDistData.active_outage.fading_cond_ber_mean
        : null;
    document.getElementById("kpiBerLabel").textContent = "BER CSI";
    document.getElementById("kpiBer").textContent =
      condBer === null ? "n/a" : condBer.toExponential(2);
    document.getElementById("kpiBerSub").textContent = `Adaptif ≤ ${state.ber_target} · SIMULATED`;
  }

  function renderOperatingPoint(data) {
    lastOpData = data;
    const act = data.active;
    const inOutage = !act.ok;

    document.getElementById("kpiPl").textContent = `${fmtIdNum(act.pl_db, 1)} dB`;
    document.getElementById("kpiPlSub").textContent = `Margin ${fmtIdNum(act.margin_db, 1)} dB · THEORETICAL`;
    document.getElementById("kpiPr").textContent = `${fmtIdNum(act.pr_dbm, 1)} dBm`;
    document.getElementById("kpiPrSub").textContent = `P/RB ${fmtIdNum(act.p_rb_dbm, 1)} dBm`;
    document.getElementById("kpiNoise").textContent = `${fmtIdNum(act.noise_dbm, 1)} dBm`;
    document.getElementById("kpiNoiseSub").textContent = `BW ${fmtIdNum(act.b_hz / 1e6, 2)} MHz`;

    const snrEl = document.getElementById("kpiSnr");
    snrEl.textContent = `${fmtIdNum(act.snr_db, 1)} dB`;
    snrEl.className = `t-value${inOutage ? " bad" : ""}`;
    document.getElementById("kpiSnrSub").textContent = inOutage
      ? "Di bawah ambang"
      : `Eb/N0 ${fmtIdNum(act.ebn0_db, 1)} dB`;

    const modEl = document.getElementById("kpiMod");
    modEl.textContent = inOutage ? "Outage" : `${act.mod} × ${act.rb} RB`;
    modEl.className = `t-value${inOutage ? " bad" : ""}`;
    document.getElementById("kpiModSub").textContent =
      state.strategy === "MANUAL" ? "Manual" : `Strategi ${state.strategy}`;

    updateTelemetryBer();

    document.getElementById("kpiRate").textContent = inOutage
      ? "Outage"
      : `${fmtIdNum(act.rate_mbps, 2)} Mbit/s`;
    document.getElementById("kpiRateSub").textContent = inOutage
      ? "Tanpa transmisi"
      : `Uncoded · Shannon ${fmtIdNum(act.shannon_mbps, 2)}`;

    const base = data.baseline_s0;
    const pairEl = document.getElementById("mcPairSummary");
    if (pairEl) {
      pairEl.textContent =
        `Aktif: ${inOutage ? "Outage" : `${act.mod} × ${act.rb} RB`} | S0: ${base.ok ? "QPSK × 25 RB" : "Outage"}`;
    }
    document.getElementById("btnRunMc").disabled = inOutage;

    data.by_freq.forEach((item) => {
      const f = item.freq_mhz;
      const a = item.active;
      document.getElementById(`cmpSnr${f}`).textContent = `${fmtIdNum(a.snr_db, 1)} dB`;
      document.getElementById(`cmpMod${f}`).textContent = a.ok ? `${a.mod} (${a.rb})` : "Outage";
    });

    document.getElementById("snrChartTitle").textContent =
      `Kurva SNR vs Jarak (${state.env} · THEORETICAL)`;
    document.getElementById("freqTableTitle").textContent =
      `Perbandingan Frekuensi (${fmtIdNum(state.dist_km, 2)} km · ${state.env})`;
    document.getElementById("stratTableTitle").textContent =
      `Perbandingan Strategi (${fmtIdNum(state.dist_km, 2)} km · ${state.freq_mhz} MHz ${state.env})`;

    drawSnrChart(data);
    renderFreqComparisonTable(data, lastZonesData);
  }

  function renderStochastic(data, zoneKey) {
    if (zoneKey === currentZoneKey()) {
      if (data.zones) {
        lastZonesData = {
          zones: data.zones,
          freq_summary_s3: data.freq_summary_s3,
        };
        zoneCache.set(zoneKey, lastZonesData);
      } else if (zoneCache.has(zoneKey)) {
        lastZonesData = zoneCache.get(zoneKey);
      }
    }

    lastStochDistData = {
      active_outage: data.active_outage,
      strategy_comparison: data.strategy_comparison,
      freq_summary_s3: data.freq_summary_s3,
    };

    if (state.strategy === "MANUAL" || !data.active_outage) {
      document.getElementById("kpiOutage").textContent = "n/a";
      document.getElementById("kpiOutageSub").textContent = "mode manual";
    } else {
      const prob =
        state.channel === "AWGN"
          ? data.active_outage.shadow_outage_prob
          : data.active_outage.fading_outage_prob;
      document.getElementById("kpiOutage").textContent = `${fmtIdNum(prob * 100, 1)}%`;
      document.getElementById("kpiOutageSub").textContent =
        state.channel === "AWGN" ? "Shadowing · SIMULATED" : "+Rayleigh CSI · SIMULATED";
    }

    updateTelemetryBer();

    const s3Summary = (lastZonesData && lastZonesData.freq_summary_s3) || data.freq_summary_s3 || [];
    s3Summary.forEach((item) => {
      document.getElementById(`cmpCov${item.freq_mhz}`).textContent = item.radius_fading_label;
    });

    if (lastZonesData) drawCoverageMap(lastZonesData);
    renderStrategyTable(data);
    if (lastOpData) renderFreqComparisonTable(lastOpData, lastZonesData);
  }

  const STRAT_SHORT = {
    S0: "Fixed QPSK 25 RB",
    S1: "Adaptif Mod",
    S2: "Adaptif BW",
    S3: "Joint Adaptif",
    R0: "Fixed BPSK 1 RB",
  };

  function renderStrategyTable(stochData) {
    const tbody = document.querySelector("#tblStrategyCmp tbody");
    tbody.innerHTML = stochData.strategy_comparison
      .map((r) => {
        const condTxt =
          r.fading_cond_ber_mean === null ? "n/a" : r.fading_cond_ber_mean.toExponential(1);
        const activeCls = r.scenario === state.strategy ? ' class="active-row"' : "";
        const shortLabel = STRAT_SHORT[r.scenario] || r.label;
        const cfgTxt = r.median_config.replace(" x ", " × ");
        return `<tr${activeCls}>
          <td><strong>${r.scenario}</strong> · ${shortLabel}</td>
          <td>${cfgTxt}</td>
          <td>${fmtIdNum(r.median_rate_mbps, 2)}</td>
          <td>${fmtIdNum(r.shadow_outage_pct, 1)}%</td>
          <td>${fmtIdNum(r.fading_outage_pct, 1)}%</td>
          <td>${fmtIdNum(r.fading_effective_rate_mbps, 2)}</td>
          <td>${condTxt}</td>
        </tr>`;
      })
      .join("");
  }

  function renderFreqComparisonTable(opData, zoneData) {
    const tbody = document.querySelector("#tblFreqCmp tbody");
    const radMap = new Map();
    if (zoneData && zoneData.freq_summary_s3) {
      zoneData.freq_summary_s3.forEach((r) => radMap.set(r.freq_mhz, r));
    }
    tbody.innerHTML = opData.by_freq
      .map((item) => {
        const s3 = item.s3;
        const rad = radMap.get(item.freq_mhz);
        const s3Cfg = s3.ok ? `${s3.mod} × ${s3.rb} RB` : "Outage";
        const s3Rate = s3.ok ? fmtIdNum(s3.rate_mbps, 2) : "outage";
        const activeCls = item.freq_mhz === state.freq_mhz ? ' class="active-row"' : "";
        return `<tr${activeCls}>
          <td><strong>${item.freq_mhz}</strong></td>
          <td>${fmtIdNum(item.pl_db, 1)}</td>
          <td>${fmtIdNum(item.snr_25rb_db, 1)}</td>
          <td>${fmtIdNum(item.snr_1rb_db, 1)}</td>
          <td>${s3Cfg}</td>
          <td>${s3Rate}</td>
          <td>${rad ? rad.radius_median_label : "-"}</td>
          <td>${rad ? rad.radius_fading_label : "-"}</td>
        </tr>`;
      })
      .join("");
  }

  function lookupSnrOnCachedCurves(opData, freqMhz, rb, distKm) {
    if (!opData || !opData.snr_curves || !opData.distances_km) return opData ? opData.active.snr_db : 0;
    const curves = opData.snr_curves[String(freqMhz)];
    if (!curves) return opData.active.snr_db;
    let series = curves.rb_1;
    if (rb === 25) series = curves.rb_25;
    else if (rb !== 1 && curves.rb_active) series = curves.rb_active;
    else if (rb !== 1 && Math.abs(distKm - opData.active.dist_km) < 1e-6) return opData.active.snr_db;

    const dists = opData.distances_km;
    let bestIdx = 0;
    let bestDiff = Infinity;
    for (let i = 0; i < dists.length; i += 1) {
      const diff = Math.abs(dists[i] - distKm);
      if (diff < bestDiff) {
        bestDiff = diff;
        bestIdx = i;
      }
    }
    return series[bestIdx];
  }

  function drawSnrChart(data) {
    if (!data) return;
    const { ctx, W, H } = setupCanvas("cvSnr", SNR_W, SNR_H);
    const pad = SNR_PAD;
    const pw = W - pad.l - pad.r;
    const ph = H - pad.t - pad.b;

    const allVals = [];
    Object.values(data.snr_curves).forEach((c) => {
      allVals.push(...c.rb_1, ...c.rb_25);
      if (c.rb_active) allVals.push(...c.rb_active);
    });
    Object.values(data.thresholds).forEach((t) => allVals.push(t.esn0_db));
    const yMin = Math.floor(Math.min(-15, ...allVals) / 10) * 10;
    const yMax = Math.ceil(Math.max(45, ...allVals) / 10) * 10;

    const xToPx = (d) => pad.l + ((d - 1.0) / 11.0) * pw;
    const yToPx = (s) => pad.t + ((yMax - Math.max(yMin, Math.min(yMax, s))) / (yMax - yMin)) * ph;

    ctx.strokeStyle = "#E2E8F0";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#475569";
    ctx.font = "11px sans-serif";

    for (let y = yMin; y <= yMax; y += 10) {
      const py = yToPx(y);
      ctx.beginPath();
      ctx.moveTo(pad.l, py);
      ctx.lineTo(W - pad.r, py);
      ctx.stroke();
      ctx.textAlign = "right";
      ctx.fillText(`${y} dB`, pad.l - 6, py + 4);
    }

    for (let d = 1; d <= 12; d += 1) {
      const px = xToPx(d);
      ctx.beginPath();
      ctx.moveTo(px, pad.t);
      ctx.lineTo(px, H - pad.b);
      ctx.stroke();
      ctx.textAlign = "center";
      ctx.fillText(`${d} km`, px, H - 18);
    }

    const drawCrispLabel = (text, x, y, align, fillColor) => {
      ctx.save();
      ctx.textAlign = align;
      ctx.lineJoin = "round";
      ctx.lineWidth = 3.5;
      ctx.strokeStyle = "rgba(255, 255, 255, 0.92)";
      ctx.strokeText(text, x, y);
      ctx.fillStyle = fillColor;
      ctx.fillText(text, x, y);
      ctx.restore();
    };

    ["QPSK", "16-QAM", "64-QAM"].forEach((mod) => {
      const th = data.thresholds[mod];
      if (!th) return;
      const py = yToPx(th.esn0_db);
      ctx.save();
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = "#94A3B8";
      ctx.lineWidth = 1.1;
      ctx.beginPath();
      ctx.moveTo(pad.l, py);
      ctx.lineTo(W - pad.r, py);
      ctx.stroke();
      ctx.restore();
      drawCrispLabel(`${mod} (${th.esn0_db.toFixed(1)} dB)`, W - pad.r - 4, py - 4, "right", "#334155");
    });

    const dists = data.distances_km;
    [700, 900, 1800].forEach((f) => {
      const curves = data.snr_curves[String(f)];
      const col = FREQ_COLORS[f];

      const drawSeries = (vals, dash, width) => {
        ctx.save();
        ctx.strokeStyle = col;
        ctx.lineWidth = width;
        ctx.setLineDash(dash);
        ctx.beginPath();
        vals.forEach((v, idx) => {
          const px = xToPx(dists[idx]);
          const py = yToPx(v);
          if (idx === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        });
        ctx.stroke();
        ctx.restore();
      };

      drawSeries(curves.rb_1, [], f === state.freq_mhz && data.active.rb === 1 ? 3.0 : 1.7);
      drawSeries(curves.rb_25, [3, 3], f === state.freq_mhz && data.active.rb === 25 ? 2.8 : 1.5);
      if (curves.rb_active) {
        drawSeries(curves.rb_active, [7, 3], 2.8);
      }
    });

    // Active distance cursor & draggable yellow operating-point marker
    const cx = xToPx(state.dist_km);
    ctx.save();
    ctx.setLineDash([5, 4]);
    ctx.strokeStyle = "#B45309";
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ctx.moveTo(cx, pad.t);
    ctx.lineTo(cx, H - pad.b);
    ctx.stroke();
    ctx.restore();

    const activeSnr = isDraggingSnr
      ? lookupSnrOnCachedCurves(data, state.freq_mhz, data.active.rb, state.dist_km)
      : data.active.snr_db;
    const pyAct = yToPx(activeSnr);

    if (isDraggingSnr) {
      ctx.fillStyle = "rgba(217, 119, 6, 0.22)";
      ctx.beginPath();
      ctx.arc(cx, pyAct, 12, 0, 2 * Math.PI);
      ctx.fill();
    }

    ctx.fillStyle = data.active.ok ? "#F59E0B" : "#9A1B1B";
    ctx.strokeStyle = "#0F172A";
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    ctx.arc(cx, pyAct, 6.2, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();

    // Compact readout tag beside dragged marker
    ctx.font = "bold 11px sans-serif";
    const align = cx > W - 120 ? "right" : "left";
    const tagX = cx > W - 120 ? cx - 10 : cx + 10;
    const tagY = Math.max(pad.t + 14, Math.min(H - pad.b - 6, pyAct - 10));
    drawCrispLabel(`${fmtIdNum(state.dist_km, 2)} km · ${fmtIdNum(activeSnr, 1)} dB`, tagX, tagY, align, "#0F172A");

    // Legend
    [700, 900, 1800].forEach((f, idx) => {
      const lx = pad.l + 8;
      const ly = pad.t + 14 + idx * 16;
      ctx.fillStyle = FREQ_COLORS[f];
      ctx.fillRect(lx, ly - 5, 16, 3);
      ctx.fillStyle = "#0F172A";
      ctx.font = "11px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(`${f} MHz${f === state.freq_mhz ? " (aktif)" : ""}`, lx + 22, ly);
    });
  }

  function drawConstellations() {
    const { ctx, W, H } = setupCanvas("cvConst", 600, 275);
    const chKey = state.channel === "AWGN" ? "awgn" : "rayleigh";

    if (mcStatusMode === "outage") {
      ctx.fillStyle = "#9A1B1B";
      ctx.font = "600 13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Konfigurasi aktif dalam keadaan outage (tidak ada transmisi).", W / 2, H / 2);
      return;
    }

    if (!lastValidMcResult) {
      ctx.fillStyle = "#475569";
      ctx.font = "13px sans-serif";
      ctx.textAlign = "center";
      const msg =
        mcStatusMode === "error"
          ? "Simulasi Monte Carlo gagal; tidak ada data ditampilkan."
          : "Menyiapkan sampel I/Q nyata dari mesin Python...";
      ctx.fillText(msg, W / 2, H / 2);
      return;
    }

    const isCurrent =
      mcStatusMode === "ready" && lastValidMcKey === currentMcParamKey();

    let panels = [];
    if (state.mc_view === "opt_vs_s0") {
      panels = [
        { title: `Dioptimalkan: ${lastValidMcResult.opt.modulation}`, res: lastValidMcResult.opt },
        {
          title: `Baseline S0: ${lastValidMcResult.base ? lastValidMcResult.base.modulation : "Outage"}`,
          res: lastValidMcResult.base,
        },
      ];
    } else {
      panels = [700, 900, 1800].map((f) => {
        const r =
          lastValidMcResult.by_freq && lastValidMcResult.by_freq[String(f)]
            ? lastValidMcResult.by_freq[String(f)]
            : null;
        return { title: `${f} MHz: ${r ? r.modulation : "Outage"}`, res: r };
      });
    }

    const gap = 12;
    const colW = (W - gap * (panels.length + 1)) / panels.length;

    panels.forEach((p, idx) => {
      const x0 = gap + idx * (colW + gap);
      const cx = x0 + colW / 2;
      const cy = H / 2 + 10;
      const scale = Math.min(colW, H - 56) / 3.6;

      ctx.strokeStyle = "#E2E8F0";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x0 + 6, cy);
      ctx.lineTo(x0 + colW - 6, cy);
      ctx.moveTo(cx, 30);
      ctx.lineTo(cx, H - 14);
      ctx.stroke();

      ctx.fillStyle = isCurrent ? "#0F2A47" : "#475569";
      ctx.font = "bold 11.5px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(p.title, cx, 18);

      if (!p.res) {
        ctx.fillStyle = "#9A1B1B";
        ctx.font = "bold 12px sans-serif";
        ctx.fillText("OUTAGE", cx, cy - 6);
        ctx.font = "11px sans-serif";
        ctx.fillText("(tidak ada transmisi)", cx, cy + 12);
        return;
      }

      const smp = p.res[`samples_${chKey}`];
      ctx.fillStyle = "#B45309";
      ctx.globalAlpha = isCurrent ? 0.6 : 0.42;
      for (let i = 0; i < smp.i.length; i += 1) {
        const px = cx + smp.i[i] * scale;
        const py = cy - smp.q[i] * scale;
        if (px > x0 + 3 && px < x0 + colW - 3 && py > 28 && py < H - 12) {
          ctx.fillRect(px - 1.5, py - 1.5, 3, 3);
        }
      }
      ctx.globalAlpha = 1.0;

      const ideal = p.res.ideal_constellation;
      ctx.strokeStyle = isCurrent ? "#0F2A47" : "#475569";
      ctx.lineWidth = 1.6;
      for (let i = 0; i < ideal.i.length; i += 1) {
        const ix = cx + ideal.i[i] * scale;
        const iy = cy - ideal.q[i] * scale;
        ctx.beginPath();
        ctx.moveTo(ix - 3.5, iy - 3.5);
        ctx.lineTo(ix + 3.5, iy + 3.5);
        ctx.moveTo(ix + 3.5, iy - 3.5);
        ctx.lineTo(ix - 3.5, iy + 3.5);
        ctx.stroke();
      }
    });
  }

  function drawCoverageMap(zoneData) {
    const { ctx, W, H } = setupCanvas("cvMap", 1180, 295);
    if (!zoneData || !zoneData.zones) return;

    const centers = [W * 0.17, W * 0.5, W * 0.83];
    const R_px = 104;
    const rMaxKm = 12.0;
    const cy = H / 2 + 2;

    zoneData.zones.forEach((zone, idx) => {
      const cx = centers[idx];
      const isSelectedFreq = zone.freq_mhz === state.freq_mhz;

      // Clean base cell disk (12 km)
      ctx.fillStyle = MOD_COLOR.Outage;
      ctx.beginPath();
      ctx.arc(cx, cy, R_px, 0, 2 * Math.PI);
      ctx.fill();

      // Seamless filled modulation zones (no harsh white ring strokes)
      const sortedRings = [...zone.rings].sort((a, b) => b.outer_km - a.outer_km);
      sortedRings.forEach((ring) => {
        if (ring.modulation === "Outage") return;
        const rPx = (ring.outer_km / rMaxKm) * R_px;
        ctx.fillStyle = MOD_COLOR[ring.modulation] || MOD_COLOR.Outage;
        ctx.beginPath();
        ctx.arc(cx, cy, rPx, 0, 2 * Math.PI);
        ctx.fill();
      });

      // Simple clean outer boundary
      ctx.strokeStyle = isSelectedFreq ? "#0F2A47" : "#334155";
      ctx.lineWidth = isSelectedFreq ? 1.8 : 1.3;
      ctx.beginPath();
      ctx.arc(cx, cy, R_px, 0, 2 * Math.PI);
      ctx.stroke();

      // Optional 95% reliability rings (OFF by default)
      if (state.show_reliability) {
        if (zone.radius_stochastic_km > 0) {
          ctx.save();
          ctx.setLineDash([5, 4]);
          ctx.strokeStyle = "rgba(15, 42, 71, 0.78)";
          ctx.lineWidth = 1.7;
          ctx.beginPath();
          ctx.arc(cx, cy, (zone.radius_stochastic_km / rMaxKm) * R_px, 0, 2 * Math.PI);
          ctx.stroke();
          ctx.restore();
        }
        if (zone.radius_fading_km > 0) {
          ctx.save();
          ctx.setLineDash([2, 3]);
          ctx.strokeStyle = "rgba(180, 83, 9, 0.9)";
          ctx.lineWidth = 1.9;
          ctx.beginPath();
          ctx.arc(cx, cy, (zone.radius_fading_km / rMaxKm) * R_px, 0, 2 * Math.PI);
          ctx.stroke();
          ctx.restore();
        }
      }

      // Subtle BTS-to-UE radial guide + BTS center + UE marker
      const uePx = cx + (state.dist_km / rMaxKm) * R_px;
      ctx.strokeStyle = "rgba(15, 23, 42, 0.28)";
      ctx.lineWidth = 1.1;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(uePx, cy);
      ctx.stroke();

      // BTS center marker
      ctx.fillStyle = "#FFFFFF";
      ctx.strokeStyle = "#0F172A";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(cx, cy, 4.4, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      // UE position marker (matches draggable yellow SNR operating point)
      ctx.fillStyle = "#F59E0B";
      ctx.strokeStyle = "#0F172A";
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      ctx.arc(uePx, cy, 4.8, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      // Clean mini-map title & radius summary
      ctx.fillStyle = isSelectedFreq ? "#0F2A47" : "#334155";
      ctx.font = "bold 12.5px sans-serif";
      ctx.textAlign = "center";
      const freqTag = isSelectedFreq ? " · Aktif" : "";
      ctx.fillText(`${zone.freq_mhz} MHz${freqTag}`, cx, 20);

      ctx.fillStyle = "#475569";
      ctx.font = "11px sans-serif";
      ctx.fillText(
        `Median: ${zone.radius_median_label} · Andal 95%: ${zone.radius_fading_label}`,
        cx,
        H - 10
      );
    });
  }

  function formatMcSummaryGrid(resObj, metaLine, metaClass) {
    const opt = resObj.opt;
    const base = resObj.base;
    const activeTxt = `${opt.modulation} · Eb/N0 ${fmtIdNum(opt.ebn0_db, 2)} dB · ${opt.n_bits.toLocaleString("id-ID")} bit`;
    const awgnTxt = `${opt.mc_ber_awgn.toExponential(2)} MC (teori ${opt.theory_ber_awgn.toExponential(2)})`;
    const rayTxt = `${opt.mc_ber_rayleigh.toExponential(2)} MC (teori ${opt.theory_ber_rayleigh.toExponential(2)}, non-CSI)`;
    const baseTxt = base
      ? `QPSK × 25 RB · AWGN ${base.mc_ber_awgn.toExponential(2)} · Rayleigh ${base.mc_ber_rayleigh.toExponential(2)}`
      : "Outage (tidak ada transmisi)";

    return `
      <div class="mc-stats-meta ${metaClass || ""}">${metaLine}</div>
      <div class="mc-kv-grid">
        <span class="mc-kv-key">Aktif</span><span class="mc-kv-val">${activeTxt}</span>
        <span class="mc-kv-key">BER AWGN</span><span class="mc-kv-val">${awgnTxt}</span>
        <span class="mc-kv-key">BER Rayleigh</span><span class="mc-kv-val">${rayTxt}</span>
        <span class="mc-kv-key">Baseline S0</span><span class="mc-kv-val">${baseTxt}</span>
      </div>
    `;
  }

  function renderMcStats() {
    const statsBox = document.getElementById("mcStatsBox");

    if (mcStatusMode === "outage") {
      statsBox.innerHTML = `<div class="mc-stats-muted">Konfigurasi aktif dalam keadaan outage (tidak ada transmisi).</div>`;
      drawConstellations();
      return;
    }

    const isCurrent =
      mcStatusMode === "ready" &&
      lastValidMcResult &&
      lastValidMcKey === currentMcParamKey();

    if (isCurrent) {
      const isPreview = Boolean(lastValidMcResult.is_preview);
      const metaLine = isPreview
        ? `Pratinjau ${lastValidMcResult.opt.n_bits.toLocaleString("id-ID")} bit · simulasi penuh menyusul...`
        : `SIMULATED · ${lastValidMcResult.opt.n_bits.toLocaleString("id-ID")} bit (${lastValidMcResult.opt.n_symbols.toLocaleString("id-ID")} simbol)`;
      statsBox.innerHTML = formatMcSummaryGrid(
        lastValidMcResult,
        metaLine,
        isPreview ? "updating" : ""
      );
      drawConstellations();
      return;
    }

    if (lastValidMcResult && lastValidMcMeta) {
      const prevDesc = `${fmtIdNum(lastValidMcMeta.dist_km, 2)} km, ${lastValidMcMeta.freq_mhz} MHz`;
      const metaLine =
        mcStatusMode === "updating"
          ? `Memperbarui… hasil sebelumnya (${prevDesc})`
          : mcStatusMode === "error"
            ? `Gagal memperbarui (${mcLastError || "error"}) · hasil sebelumnya (${prevDesc})`
            : `Parameter berubah · hasil sebelumnya (${prevDesc})`;
      const metaCls = mcStatusMode === "error" ? "error" : "updating";
      statsBox.innerHTML = formatMcSummaryGrid(lastValidMcResult, metaLine, metaCls);
    } else if (mcStatusMode === "error") {
      statsBox.innerHTML = `<div class="mc-stats-meta error">Simulasi Monte Carlo gagal: ${mcLastError || "silakan jalankan ulang."}</div>`;
    } else {
      statsBox.innerHTML = `<div class="mc-stats-muted">Menyiapkan simulasi Monte Carlo...</div>`;
    }
    drawConstellations();
  }

  function invalidateMcView() {
    if (lastValidMcResult && lastValidMcKey !== currentMcParamKey()) {
      mcStatusMode = state.live_mc ? "updating" : "stale";
      renderMcStats();
    }
  }

  async function refreshOperatingPoint() {
    const payload = {
      freq_mhz: state.freq_mhz,
      env: state.env,
      channel: state.channel,
      shadow: state.shadow,
      dist_km: state.dist_km,
      tx_power_dbm: state.tx_power_dbm,
      ber_target: state.ber_target,
      strategy: state.strategy,
      rb_manual: state.rb_manual,
      mod_manual: state.mod_manual,
    };
    const key = JSON.stringify(payload);
    if (opCache.has(key)) {
      ++opSeq;
      if (opController) opController.abort();
      clearWorkbenchError();
      renderOperatingPoint(opCache.get(key));
      return opCache.get(key);
    }

    const seq = ++opSeq;
    if (opController) opController.abort();
    opController = new AbortController();

    try {
      const data = await fetchJson("/api/operating-point", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: key,
        signal: opController.signal,
      });
      if (seq !== opSeq) return null;
      opCache.set(key, data);
      clearWorkbenchError();
      renderOperatingPoint(data);
      return data;
    } catch (err) {
      if (err.name === "AbortError" || seq !== opSeq) return null;
      clearTelemetryOnError();
      showWorkbenchError(`Gagal memuat titik operasi dari API Python: ${err.message}`);
      return null;
    }
  }

  async function refreshStochastic() {
    const zoneKey = currentZoneKey();
    const hasZonesCached = zoneCache.has(zoneKey);
    const payload = {
      freq_mhz: state.freq_mhz,
      env: state.env,
      dist_km: state.dist_km,
      tx_power_dbm: state.tx_power_dbm,
      ber_target: state.ber_target,
      active_strategy: state.strategy,
      zone_strategy: state.zone_strategy,
      include_zones: !hasZonesCached,
    };
    const distCacheKey = JSON.stringify({
      f: state.freq_mhz,
      e: state.env,
      d: state.dist_km,
      p: state.tx_power_dbm,
      b: state.ber_target,
      st: state.strategy,
    });

    if (hasZonesCached && stochDistCache.has(distCacheKey)) {
      ++stochSeq;
      if (stochController) stochController.abort();
      renderStochastic(stochDistCache.get(distCacheKey), zoneKey);
      return;
    }

    const seq = ++stochSeq;
    if (stochController) stochController.abort();
    stochController = new AbortController();

    try {
      const data = await fetchJson("/api/stochastic-analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: stochController.signal,
      });
      if (seq !== stochSeq || zoneKey !== currentZoneKey()) return;
      // Cache only distance-dependent fields so zones are never cross-contaminated across zone_strategy
      stochDistCache.set(distCacheKey, {
        active_outage: data.active_outage,
        strategy_comparison: data.strategy_comparison,
        freq_summary_s3: data.freq_summary_s3,
      });
      renderStochastic(data, zoneKey);
    } catch (err) {
      if (err.name === "AbortError" || seq !== stochSeq) return;
      showWorkbenchError(`Gagal memuat analisis stokastik dari API Python: ${err.message}`);
    }
  }

  async function executeMonteCarlo(isPreview) {
    if (lastOpData && !lastOpData.active.ok) {
      mcStatusMode = "outage";
      renderMcStats();
      return;
    }

    const reqBits = isPreview ? Math.min(state.n_bits, PREVIEW_MAX_BITS) : state.n_bits;
    const mode = state.mc_view;
    const paramKey = currentMcParamKey();
    const cacheKey = JSON.stringify({ paramKey, mode, reqBits, isPreview });

    if (mcCache.has(cacheKey)) {
      const cached = mcCache.get(cacheKey);
      lastValidMcResult = cached;
      lastValidMcKey = paramKey;
      lastValidMcMeta = {
        dist_km: state.dist_km,
        freq_mhz: state.freq_mhz,
        env: state.env,
        n_bits: cached.opt.n_bits,
        is_preview: Boolean(cached.is_preview),
      };
      mcLastError = "";
      mcStatusMode = "ready";
      renderMcStats();
      return;
    }

    const seq = ++mcSeq;
    if (mcController) mcController.abort();
    mcController = new AbortController();
    mcInFlight = true;
    mcLastError = "";
    mcStatusMode = "updating";
    renderMcStats();

    try {
      const data = await fetchJson("/api/monte-carlo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          freq_mhz: state.freq_mhz,
          env: state.env,
          channel: state.channel,
          shadow: state.shadow,
          dist_km: state.dist_km,
          tx_power_dbm: state.tx_power_dbm,
          ber_target: state.ber_target,
          strategy: state.strategy,
          rb_manual: state.rb_manual,
          mod_manual: state.mod_manual,
          n_bits: reqBits,
          mode,
          is_preview: isPreview,
        }),
        signal: mcController.signal,
      });
      if (seq !== mcSeq) return;
      mcCache.set(cacheKey, data);
      lastValidMcResult = data;
      lastValidMcKey = paramKey;
      lastValidMcMeta = {
        dist_km: state.dist_km,
        freq_mhz: state.freq_mhz,
        env: state.env,
        n_bits: data.opt.n_bits,
        is_preview: Boolean(data.is_preview),
      };
      mcStatusMode = "ready";
      renderMcStats();
    } catch (err) {
      if (err.name === "AbortError" || seq !== mcSeq) return;
      mcLastError = err.message || "Error";
      if (String(err.message).includes("outage")) {
        mcStatusMode = "outage";
      } else {
        mcStatusMode = "error";
      }
      renderMcStats();
    } finally {
      if (seq === mcSeq) {
        mcInFlight = false;
      }
    }
  }

  function scheduleLiveMc(isContinuousDrag) {
    if (!state.live_mc) {
      mcStatusMode = lastOpData && !lastOpData.active.ok ? "outage" : "stale";
      renderMcStats();
      return;
    }
    clearTimeout(mcSettleTimer);

    if (isContinuousDrag) {
      const now = performance.now();
      if (!mcInFlight && now - mcDragThrottleAt >= 220) {
        mcDragThrottleAt = now;
        executeMonteCarlo(true);
      }
      mcSettleTimer = setTimeout(() => {
        executeMonteCarlo(false);
      }, 280);
      return;
    }

    mcSettleTimer = setTimeout(() => {
      executeMonteCarlo(false);
    }, 120);
  }

  function scheduleVisualDragFrame() {
    if (dragRafId !== null) return;
    dragRafId = requestAnimationFrame(() => {
      dragRafId = null;
      syncControlsFromState();
      if (lastOpData) drawSnrChart(lastOpData);
      if (lastZonesData) drawCoverageMap(lastZonesData);
    });
  }

  async function refreshAllWorkbench(mode) {
    // mode: "discrete" | "drag_move" | "drag_settle"
    const seq = ++workbenchSeq;
    syncControlsFromState();
    invalidateMcView();

    if (mode === "drag_move") {
      scheduleVisualDragFrame();
      clearTimeout(analyticalTimer);
      analyticalTimer = setTimeout(async () => {
        if (seq !== workbenchSeq) return;
        const op = await refreshOperatingPoint();
        if (seq !== workbenchSeq || !op) return;
        refreshStochastic();
        if (!op.active.ok) {
          mcStatusMode = "outage";
          renderMcStats();
        } else if (mcStatusMode === "outage") {
          scheduleLiveMc(true);
        }
      }, 65);
      scheduleLiveMc(true);
      return;
    }

    clearTimeout(analyticalTimer);
    const op = await refreshOperatingPoint();
    if (seq !== workbenchSeq || !op) return;
    refreshStochastic();
    if (!op.active.ok) {
      mcStatusMode = "outage";
      renderMcStats();
    } else {
      scheduleLiveMc(false);
    }
  }

  // ---------------- DRAGGABLE SNR CHART (POINTER EVENTS) ----------------
  function pointerEventToDistKm(clientX) {
    const cv = document.getElementById("cvSnr");
    const rect = cv.getBoundingClientRect();
    const xLogical = ((clientX - rect.left) / Math.max(rect.width, 1)) * SNR_W;
    const pw = SNR_W - SNR_PAD.l - SNR_PAD.r;
    const raw = 1.0 + ((xLogical - SNR_PAD.l) / pw) * 11.0;
    const clamped = Math.max(1.0, Math.min(12.0, raw));
    return Math.round(clamped * 4) / 4;
  }

  const cvSnr = document.getElementById("cvSnr");
  cvSnr.addEventListener("pointerdown", (e) => {
    if (e.button !== undefined && e.button !== 0 && e.pointerType === "mouse") return;
    const rect = cvSnr.getBoundingClientRect();
    const xLogical = ((e.clientX - rect.left) / Math.max(rect.width, 1)) * SNR_W;
    if (xLogical < SNR_PAD.l - 14 || xLogical > SNR_W - SNR_PAD.r + 14) return;

    isDraggingSnr = true;
    activePointerId = e.pointerId;
    cvSnr.classList.add("dragging");
    try {
      cvSnr.setPointerCapture(e.pointerId);
    } catch (_) {}
    e.preventDefault();

    const nextDist = pointerEventToDistKm(e.clientX);
    if (nextDist !== state.dist_km) {
      state.dist_km = nextDist;
      refreshAllWorkbench("drag_move");
    } else {
      scheduleVisualDragFrame();
    }
  });

  cvSnr.addEventListener("pointermove", (e) => {
    if (!isDraggingSnr || e.pointerId !== activePointerId) return;
    e.preventDefault();
    const nextDist = pointerEventToDistKm(e.clientX);
    if (nextDist !== state.dist_km) {
      state.dist_km = nextDist;
      refreshAllWorkbench("drag_move");
    }
  });

  function finishSnrDrag(e) {
    if (!isDraggingSnr || (e && activePointerId !== null && e.pointerId !== activePointerId)) return;
    isDraggingSnr = false;
    cvSnr.classList.remove("dragging");
    if (activePointerId !== null) {
      try {
        cvSnr.releasePointerCapture(activePointerId);
      } catch (_) {}
      activePointerId = null;
    }
    refreshAllWorkbench("drag_settle");
  }

  cvSnr.addEventListener("pointerup", finishSnrDrag);
  cvSnr.addEventListener("pointercancel", finishSnrDrag);

  // ---------------- TAB B: RESULTS ----------------
  async function loadResultsTab() {
    if (resultsData) return;
    const loading = document.getElementById("resultsLoading");
    const errEl = document.getElementById("resultsError");
    loading.hidden = false;
    errEl.hidden = true;
    try {
      resultsData = await fetchJson("/api/results");
      initResultsControls();
      renderResultsView();
    } catch (err) {
      errEl.hidden = false;
      errEl.textContent = `Gagal memuat hasil penelitian: ${err.message}`;
    } finally {
      loading.hidden = true;
    }
  }

  function initResultsControls() {
    const checksHost = document.getElementById("resStratChecks");
    checksHost.innerHTML = ["S0", "S1", "S2", "S3", "R0"]
      .map(
        (s) =>
          `<label><input type="checkbox" value="${s}" ${resultsStrategies.has(s) ? "checked" : ""} /> ${s}</label>`
      )
      .join("");
    checksHost.querySelectorAll("input[type='checkbox']").forEach((cb) => {
      cb.addEventListener("change", () => {
        if (cb.checked) resultsStrategies.add(cb.value);
        else resultsStrategies.delete(cb.value);
        renderResultsView();
      });
    });

    document.getElementById("pubFiguresGrid").innerHTML = resultsData.figures
      .map(
        (fig) => `<div class="figure-card">
          <img src="${fig.url}" alt="Grafik ${fig.title}" width="640" height="400" loading="lazy" />
          <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
            <span style="font-size:12.5px; font-weight:600;">${fig.title}</span>
            <a class="btn-secondary" style="min-height:36px; padding:6px 10px; font-size:12px;" href="${fig.url}" download="${fig.filename}">Unduh PNG</a>
          </div>
        </div>`
      )
      .join("");

    document.getElementById("pubCsvDownloads").innerHTML = resultsData.csv_files
      .map(
        (c) => `<a class="btn-secondary" href="${c.url}" download="${c.filename}">Unduh ${c.filename}</a>`
      )
      .join("");

    document.getElementById("pubSummaryMd").textContent = resultsData.summary_md || "";
  }

  function drawPubChart(canvasId, yField, scale, yMax, yLabel) {
    const { ctx, W, H } = setupCanvas(canvasId, 580, 270);
    if (!resultsData) return;

    const padL = 48;
    const padR = 14;
    const padT = 26;
    const padB = 34;
    const subGap = 24;
    const subW = (W - padL - padR - subGap) / 2;
    const ph = H - padT - padB;

    [900, 1800].forEach((freq, idx) => {
      const x0 = padL + idx * (subW + subGap);
      const xToPx = (d) => x0 + ((d - 1.0) / 11.0) * subW;
      const yToPx = (v) => padT + ((yMax - Math.max(0, Math.min(yMax, v))) / yMax) * ph;

      ctx.strokeStyle = "#E2E8F0";
      ctx.lineWidth = 1;
      ctx.fillStyle = "#475569";
      ctx.font = "10.5px sans-serif";
      const steps = 4;
      for (let i = 0; i <= steps; i += 1) {
        const yv = (yMax / steps) * i;
        const py = yToPx(yv);
        ctx.beginPath();
        ctx.moveTo(x0, py);
        ctx.lineTo(x0 + subW, py);
        ctx.stroke();
        if (idx === 0) {
          ctx.textAlign = "right";
          ctx.fillText(String(Math.round(yv)), x0 - 5, py + 3);
        }
      }
      [1, 4, 8, 12].forEach((d) => {
        const px = xToPx(d);
        ctx.beginPath();
        ctx.moveTo(px, padT);
        ctx.lineTo(px, H - padB);
        ctx.stroke();
        ctx.textAlign = "center";
        ctx.fillText(`${d} km`, px, H - 14);
      });

      ctx.fillStyle = "#0F2A47";
      ctx.font = "bold 12px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`${freq} MHz (${resultsEnv})`, x0 + subW / 2, 16);

      if (yField === "fading_outage_prob") {
        const pyTarget = yToPx(5);
        ctx.save();
        ctx.setLineDash([4, 3]);
        ctx.strokeStyle = "#B45309";
        ctx.beginPath();
        ctx.moveTo(x0, pyTarget);
        ctx.lineTo(x0 + subW, pyTarget);
        ctx.stroke();
        ctx.restore();
      }

      resultsStrategies.forEach((sc) => {
        const pts = resultsData.curves
          .filter((r) => r.freq_mhz === freq && r.environment === resultsEnv && r.scenario === sc)
          .sort((a, b) => a.distance_km - b.distance_km);
        if (!pts.length) return;
        ctx.strokeStyle = STRAT_COLORS[sc] || "#0F172A";
        ctx.lineWidth = sc === "S3" ? 2.6 : 1.8;
        ctx.beginPath();
        pts.forEach((p, i) => {
          const px = xToPx(p.distance_km);
          const py = yToPx(p[yField] * scale);
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        });
        ctx.stroke();
      });
    });

    ctx.fillStyle = "#475569";
    ctx.font = "10.5px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(yLabel, 6, 15);
  }

  function renderResultsView() {
    if (!resultsData) return;
    setActiveSegment("data-resenv", resultsEnv);
    const filteredCurves = resultsData.curves.filter(
      (r) => r.environment === resultsEnv && resultsStrategies.has(r.scenario)
    );
    const maxRate = Math.max(
      10,
      ...filteredCurves.map((r) => r.fading_effective_rate_bps * 1e-6)
    );
    drawPubChart("cvResOutage", "fading_outage_prob", 100, 100, "%");
    drawPubChart("cvResRate", "fading_effective_rate_bps", 1e-6, Math.ceil(maxRate / 5) * 5, "Mbit/s");

    const sumRows = resultsData.summary.filter(
      (r) => r.environment === resultsEnv && resultsStrategies.has(r.scenario)
    );
    document.querySelector("#tblPubSummary tbody").innerHTML = sumRows.length
      ? sumRows
          .map(
            (r) => `<tr>
              <td>${r.freq_mhz}</td>
              <td><strong>${r.scenario}</strong>: ${r.label}</td>
              <td>${r.radius_median_label}</td>
              <td>${r.radius_stochastic_label}</td>
              <td>${r.radius_fading_label}</td>
            </tr>`
          )
          .join("")
      : `<tr><td colspan="5">Pilih minimal satu strategi untuk menampilkan ringkasan.</td></tr>`;

    document.getElementById("pubFindingsList").innerHTML =
      "<strong>Temuan terverifikasi dari CSV (tepi sel, 2 km, NLOS, shadowing + Rayleigh CSI):</strong> " +
      resultsData.findings_nlos_2km
        .map(
          (f) =>
            `${f.freq_mhz} MHz: S0 outage ${fmtIdNum(f.s0_outage_pct, 1)}% (${fmtIdNum(f.s0_rate_mbps, 2)} Mbit/s) vs S3 outage ${fmtIdNum(f.s3_outage_pct, 1)}% (${fmtIdNum(f.s3_rate_mbps, 2)} Mbit/s)`
        )
        .join(" | ");

    document.querySelector("#tblPubMc tbody").innerHTML = resultsData.mc_validation
      .map(
        (r) => `<tr>
          <td>${r.freq_mhz}</td>
          <td>${r.environment}</td>
          <td>${r.distance_km}</td>
          <td>${r.modulation}</td>
          <td>${r.n_rb}</td>
          <td>${Number(r.ebn0_db).toFixed(2)}</td>
          <td>${Number(r.theory_ber_awgn).toExponential(2)}</td>
          <td>${Number(r.mc_ber_awgn).toExponential(2)}</td>
          <td>${Number(r.theory_ber_rayleigh).toExponential(2)}</td>
          <td>${Number(r.mc_ber_rayleigh).toExponential(2)}</td>
        </tr>`
      )
      .join("");
  }

  // ---------------- TAB C: METHODOLOGY ----------------
  async function loadMethodologyTab() {
    if (methodologyLoaded) return;
    const loading = document.getElementById("methLoading");
    const errEl = document.getElementById("methError");
    loading.hidden = false;
    errEl.hidden = true;
    try {
      const data = await fetchJson("/api/methodology");
      methodologyLoaded = true;
      const cfg = data.config;
      const ci = data.ci_parameters;

      document.getElementById("methBullets").innerHTML = [
        `<li><strong>Propagasi CI:</strong> LOS n = ${ci.LOS.n}, σ = ${ci.LOS.sigma_db} dB; NLOS n = ${ci.NLOS.n}, σ = ${ci.NLOS.sigma_db} dB (Park dkk. 2023, ekstrapolasi 1400 MHz, keputusan D8).</li>`,
        `<li><strong>Link budget:</strong> daya UE maks ${cfg.ue_tx_power_dbm} dBm, Gr = ${cfg.bts_rx_antenna_gain_dbi} dBi, feeder ${cfg.feeder_loss_db} dB, body ${cfg.body_loss_db} dB, NF = ${cfg.rx_noise_figure_db} dB. Daya terbagi rata pada N_RB aktif.</li>`,
        `<li><strong>BER &amp; Monte Carlo:</strong> QAM Gray-coded eksak Cho &amp; Yoon (2002); MC bit-level pada AWGN dan Rayleigh independen dengan ekualisasi ZF sempurna.</li>`,
        `<li><strong>Adaptasi Rayleigh CSI sesaat:</strong> tiap realisasi memilih opsi (modulasi, N_RB) dengan laju tertinggi yang memenuhi ambang AWGN pada Eb/N0 sesaat; BER rata-rata Rayleigh tanpa CSI tidak dipakai sebagai kriteria switching.</li>`,
        `<li><strong>Strategi:</strong> ${data.strategies.map((s) => `${s.code} (${s.label})`).join("; ")}. Semua memakai realisasi bersama (seed ${cfg.default_seed}).</li>`,
      ].join("");

      const paramRows = [
        ["Frekuensi utama", `${cfg.carrier_frequencies_mhz.join(", ")} MHz`, "Cakupan riset 3T"],
        ["Lebar pita kanal / RB", `${cfg.nominal_channel_bandwidth_mhz} MHz / ${cfg.rb_bandwidth_khz} kHz`, "Yogapratama Table IV & Reddy Table 1"],
        ["Pilihan N_RB", cfg.active_rb_choices.join(", "), "Grid alokasi sub-band (≤ 25 RB)"],
        ["Daya pancar UE maks", `${cfg.ue_tx_power_dbm} dBm`, "Batas keras uplink (hard cap)"],
        ["Antena & rugi-rugi", `Gt ${cfg.ue_antenna_gain_dbi} dBi, Gr ${cfg.bts_rx_antenna_gain_dbi} dBi, feeder ${cfg.feeder_loss_db} dB, body ${cfg.body_loss_db} dB`, "Yogapratama Table IV"],
        ["Noise figure & thermal", `NF ${cfg.rx_noise_figure_db} dB, N0 ${cfg.thermal_noise_density_dbm_hz} dBm/Hz`, "Yogapratama Table IV"],
        ["Rentang & outage target", `${cfg.distance_min_km}-${cfg.distance_max_km} km, outage ≤ ${(cfg.outage_target * 100).toFixed(0)}%`, "Evaluasi keandalan 95%"],
      ];
      document.querySelector("#tblMethParams tbody").innerHTML = paramRows
        .map((r) => `<tr><td><strong>${r[0]}</strong></td><td>${r[1]}</td><td>${r[2]}</td></tr>`)
        .join("");

      const t2 = data.thresholds["1e-2"];
      const t3 = data.thresholds["1e-3"];
      document.querySelector("#tblMethThresholds tbody").innerHTML = ["BPSK", "QPSK", "16-QAM", "64-QAM"]
        .map(
          (m) => `<tr>
            <td><strong>${m}</strong></td>
            <td>${t2[m].ebn0_db.toFixed(2)} dB</td>
            <td>${t2[m].esn0_db.toFixed(2)} dB</td>
            <td>${t3[m].ebn0_db.toFixed(2)} dB</td>
            <td>${t3[m].esn0_db.toFixed(2)} dB</td>
          </tr>`
        )
        .join("");
    } catch (err) {
      errEl.hidden = false;
      errEl.textContent = `Gagal memuat metodologi: ${err.message}`;
    } finally {
      loading.hidden = true;
    }
  }

  // ---------------- TAB D: ENCYCLOPEDIA ----------------
  async function loadGlossaryTab() {
    if (!glossaryCache) {
      const loading = document.getElementById("glossLoading");
      const errEl = document.getElementById("glossError");
      loading.hidden = false;
      errEl.hidden = true;
      try {
        glossaryCache = await fetchJson("/api/glossary");
        const sel = document.getElementById("selGlossCat");
        sel.innerHTML =
          '<option value="Semua kategori">Semua kategori</option>' +
          glossaryCache.categories.map((c) => `<option value="${c}">${c}</option>`).join("");
      } catch (err) {
        errEl.hidden = false;
        errEl.textContent = `Gagal memuat ensiklopedia: ${err.message}`;
        return;
      } finally {
        loading.hidden = true;
      }
    }
    renderGlossaryTable();
  }

  function renderGlossaryTable() {
    if (!glossaryCache) return;
    const q = document.getElementById("inpGlossSearch").value.trim().toLowerCase();
    const cat = document.getElementById("selGlossCat").value;

    const filtered = glossaryCache.entries.filter((e) => {
      if (cat !== "Semua kategori" && e.kategori !== cat) return false;
      if (!q) return true;
      return (
        e.istilah.toLowerCase().includes(q) ||
        e.kepanjangan.toLowerCase().includes(q) ||
        e.penjelasan.toLowerCase().includes(q) ||
        e.persamaan.toLowerCase().includes(q) ||
        e.kategori.toLowerCase().includes(q)
      );
    });

    document.getElementById("glossCount").textContent =
      `Menampilkan ${filtered.length} dari ${glossaryCache.total_count} istilah (${glossaryCache.categories.length} kategori).`;
    document.getElementById("glossEmpty").hidden = filtered.length > 0;

    const escapeHtml = (s) =>
      String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

    document.querySelector("#tblGlossary tbody").innerHTML = filtered
      .map(
        (e) => `<tr>
          <td><strong>${escapeHtml(e.istilah)}</strong></td>
          <td>${escapeHtml(e.kepanjangan)}</td>
          <td>${escapeHtml(e.penjelasan)}</td>
          <td><code>${escapeHtml(e.persamaan)}</code></td>
        </tr>`
      )
      .join("");
  }

  // ---------------- NAVIGATION & EVENTS ----------------
  function switchTab(tabName) {
    const panels = {
      workbench: "panelWorkbench",
      results: "panelResults",
      methodology: "panelMethodology",
      encyclopedia: "panelEncyclopedia",
    };
    document.querySelectorAll("[data-tab]").forEach((btn) => {
      const active = btn.dataset.tab === tabName;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
    Object.entries(panels).forEach(([k, id]) => {
      document.getElementById(id).hidden = k !== tabName;
    });
    if (tabName === "results") loadResultsTab();
    if (tabName === "methodology") loadMethodologyTab();
    if (tabName === "encyclopedia") loadGlossaryTab();
  }

  document.querySelectorAll("[data-tab]").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  document.querySelectorAll("[data-freq]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.freq_mhz = Number(btn.dataset.freq);
      refreshAllWorkbench("discrete");
    });
  });

  document.querySelectorAll("[data-env]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.env = btn.dataset.env;
      refreshAllWorkbench("discrete");
    });
  });

  document.querySelectorAll("[data-shadow]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.shadow = btn.dataset.shadow;
      refreshAllWorkbench("discrete");
    });
  });

  document.querySelectorAll("[data-channel]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.channel = btn.dataset.channel;
      syncControlsFromState();
      if (lastValidMcResult && lastValidMcKey === currentMcParamKey() && mcStatusMode === "ready") {
        if (lastStochDistData) {
          renderStochastic(
            {
              ...lastStochDistData,
              zones: null,
            },
            currentZoneKey()
          );
        } else {
          refreshStochastic();
        }
        renderMcStats();
      } else {
        refreshAllWorkbench("discrete");
      }
    });
  });

  document.querySelectorAll("[data-ber]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.ber_target = Number(btn.dataset.ber);
      refreshAllWorkbench("discrete");
    });
  });

  document.querySelectorAll("[data-rb]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.rb_manual = Number(btn.dataset.rb);
      refreshAllWorkbench("discrete");
    });
  });

  document.querySelectorAll("[data-mod]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.mod_manual = btn.dataset.mod;
      refreshAllWorkbench("discrete");
    });
  });

  document.querySelectorAll("[data-nbits]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.n_bits = Number(btn.dataset.nbits);
      refreshAllWorkbench("discrete");
    });
  });

  document.querySelectorAll("[data-mcview]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.mc_view = btn.dataset.mcview;
      setActiveSegment("data-mcview", state.mc_view);
      if (state.mc_view === "by_freq" && lastValidMcResult && (!lastValidMcResult.by_freq || !Object.keys(lastValidMcResult.by_freq).length)) {
        if (state.live_mc) {
          executeMonteCarlo(false);
          return;
        }
      }
      drawConstellations();
    });
  });

  document.getElementById("chkLiveMc").addEventListener("change", (e) => {
    state.live_mc = Boolean(e.target.checked);
    syncControlsFromState();
    if (state.live_mc && mcStatusMode !== "ready") {
      scheduleLiveMc(false);
    }
  });

  document.getElementById("selStrat").addEventListener("change", (e) => {
    state.strategy = e.target.value;
    if (["S0", "S1", "S2", "S3", "R0"].includes(state.strategy)) {
      state.zone_strategy = state.strategy;
    }
    refreshAllWorkbench("discrete");
  });

  document.getElementById("selZoneStrat").addEventListener("change", (e) => {
    state.zone_strategy = e.target.value;
    syncControlsFromState();
    refreshStochastic();
  });

  document.getElementById("chkShowReliability").addEventListener("change", (e) => {
    state.show_reliability = Boolean(e.target.checked);
    const cap = document.getElementById("mapCaption");
    if (cap) {
      cap.textContent = state.show_reliability
        ? "Zona warna: median PL · Putus navy: batas 95% shadowing · Titik amber: batas 95% (+Rayleigh CSI) · S3 dapat menghasilkan zona modulasi berulang karena perubahan jumlah Resource Block."
        : "Zona warna: median PL (1–12 km) · S3 dapat menghasilkan zona modulasi berulang karena perubahan jumlah Resource Block.";
    }
    if (lastZonesData) drawCoverageMap(lastZonesData);
  });

  document.getElementById("rngDist").addEventListener("input", (e) => {
    state.dist_km = Number(e.target.value);
    refreshAllWorkbench("drag_move");
  });
  document.getElementById("rngDist").addEventListener("change", (e) => {
    state.dist_km = Number(e.target.value);
    refreshAllWorkbench("drag_settle");
  });

  document.getElementById("rngPt").addEventListener("input", (e) => {
    state.tx_power_dbm = Number(e.target.value);
    refreshAllWorkbench("drag_move");
  });
  document.getElementById("rngPt").addEventListener("change", (e) => {
    state.tx_power_dbm = Number(e.target.value);
    refreshAllWorkbench("drag_settle");
  });

  document.getElementById("btnPreset").addEventListener("click", () => {
    const keepLive = state.live_mc;
    Object.assign(state, DEFAULTS, { live_mc: keepLive });
    refreshAllWorkbench("discrete");
  });

  document.getElementById("btnRunMc").addEventListener("click", () => {
    clearTimeout(mcSettleTimer);
    executeMonteCarlo(false);
  });

  document.querySelectorAll("[data-resenv]").forEach((btn) => {
    btn.addEventListener("click", () => {
      resultsEnv = btn.dataset.resenv;
      renderResultsView();
    });
  });

  document.getElementById("inpGlossSearch").addEventListener("input", renderGlossaryTable);
  document.getElementById("selGlossCat").addEventListener("change", renderGlossaryTable);

  refreshAllWorkbench("discrete");
})();
