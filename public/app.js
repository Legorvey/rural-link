(function () {
  "use strict";

  const MOD_COLOR = {
    "64-QAM": "#0F2A47",
    "16-QAM": "#0F766E",
    "QPSK": "#7FA6C9",
    "BPSK": "#B45309",
    "Outage": "#D5DBE3",
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
    mc_view: "opt_vs_s0",
  };

  const state = { ...DEFAULTS };
  let activeTab = "workbench";
  let lastOpData = null;
  let lastStochData = null;
  let mcResult = null;
  let mcKey = null;
  let resultsData = null;
  let resultsEnv = "NLOS";
  let resultsStrategies = new Set(["S0", "S1", "S2", "S3", "R0"]);
  let methodologyLoaded = false;
  let glossaryCache = null;

  const opCache = new Map();
  const stochCache = new Map();
  let opController = null;
  let stochController = null;
  let mcController = null;
  let sliderDebounceTimer = null;

  function fmtIdNum(val, decimals) {
    return Number(val).toFixed(decimals).replace(".", ",");
  }

  function currentParamKey() {
    return JSON.stringify({
      f: state.freq_mhz,
      e: state.env,
      s: state.shadow,
      c: state.channel,
      d: state.dist_km,
      p: state.tx_power_dbm,
      b: state.ber_target,
      st: state.strategy,
      rb: state.rb_manual,
      mod: state.mod_manual,
      nb: state.n_bits,
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

    const manual = state.strategy === "MANUAL";
    document.querySelectorAll("[data-rb], [data-mod]").forEach((btn) => {
      btn.disabled = !manual;
    });

    document.getElementById("lblFreq").textContent = `${state.freq_mhz} MHz`;
    document.getElementById("lblEnv").textContent = state.env;
    document.getElementById("hintEnv").textContent =
      state.env === "LOS"
        ? "LOS standar Park (2023): n = 2,16; σ = 3,07 dB."
        : "NLOS standar Park (2023): n = 2,56; σ = 11,40 dB.";
    document.getElementById("lblShadow").textContent =
      state.shadow === "median" ? "Median" : "Margin 95%";
    document.getElementById("lblChannel").textContent =
      state.channel === "AWGN" ? "AWGN" : "Rayleigh (CSI)";
    document.getElementById("lblDist").textContent = `${fmtIdNum(state.dist_km, 2)} km`;
    document.getElementById("lblPt").textContent = `${state.tx_power_dbm} dBm`;
    document.getElementById("lblTargetBer").textContent =
      state.ber_target === 0.001 ? "10⁻³" : "10⁻²";
    document.getElementById("hintStrat").textContent = manual
      ? "Mode manual: RB dan modulasi di bawah dikunci pengguna."
      : "Mode adaptif: optimizer memilih modulasi dan RB.";
    document.getElementById("lblRbManual").textContent = `${state.rb_manual} RB`;
    document.getElementById("lblModManual").textContent = state.mod_manual;
    document.getElementById("lblMcBits").textContent = MC_BIT_LABELS[state.n_bits] || `${state.n_bits}`;
    document.getElementById("mcSmallSampleWarn").hidden = state.n_bits >= 100000;

    const expBanner = document.getElementById("exploratoryBanner");
    if (state.freq_mhz === 700 || state.ber_target !== 0.01) {
      expBanner.hidden = false;
      expBanner.textContent = `Catatan suplemen: konfigurasi aktif (${state.freq_mhz} MHz, BER ${state.ber_target}) termasuk analisis sensitivitas tambahan di luar riset utama 900/1800 MHz pada BER 1e-2 (Tab Hasil Penelitian tetap).`;
    } else {
      expBanner.hidden = true;
    }
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
    const el = document.getElementById("apiErrorBanner");
    el.textContent = msg;
    el.hidden = false;
  }

  function clearWorkbenchError() {
    document.getElementById("apiErrorBanner").hidden = true;
  }

  async function fetchJson(url, options) {
    const resp = await fetch(url, options);
    if (!resp.ok) {
      let detail = `HTTP ${resp.status}`;
      try {
        const body = await resp.json();
        if (body && body.detail) detail = body.detail;
      } catch (_) {
        // ignore JSON parse failure
      }
      throw new Error(detail);
    }
    return resp.json();
  }

  function clearTelemetryOnError() {
    ["kpiPl", "kpiPr", "kpiNoise", "kpiSnr", "kpiMod", "kpiBer", "kpiRate", "kpiOutage"].forEach((id) => {
      document.getElementById(id).textContent = "-";
    });
  }

  function renderOperatingPoint(data) {
    lastOpData = data;
    const act = data.active;
    const inOutage = !act.ok;

    document.getElementById("kpiPl").textContent = `${fmtIdNum(act.pl_db, 1)} dB`;
    document.getElementById("kpiPlSub").textContent = `margin ${fmtIdNum(act.margin_db, 1)} dB (THEORETICAL)`;
    document.getElementById("kpiPr").textContent = `${fmtIdNum(act.pr_dbm, 1)} dBm`;
    document.getElementById("kpiPrSub").textContent = `P/RB ${fmtIdNum(act.p_rb_dbm, 1)} dBm`;
    document.getElementById("kpiNoise").textContent = `${fmtIdNum(act.noise_dbm, 1)} dBm`;
    document.getElementById("kpiNoiseSub").textContent = `B ${fmtIdNum(act.b_hz / 1e6, 2)} MHz`;

    const snrEl = document.getElementById("kpiSnr");
    snrEl.textContent = `${fmtIdNum(act.snr_db, 1)} dB`;
    snrEl.className = `t-value${inOutage ? " bad" : ""}`;
    document.getElementById("kpiSnrSub").textContent = inOutage
      ? "tanpa opsi layak"
      : `Eb/N0 ${fmtIdNum(act.ebn0_db, 1)} dB`;

    const modEl = document.getElementById("kpiMod");
    modEl.textContent = inOutage ? "Outage" : `${act.mod} × ${act.rb} RB`;
    modEl.className = `t-value${inOutage ? " bad" : ""}`;
    document.getElementById("kpiModSub").textContent =
      state.strategy === "MANUAL" ? "manual" : `optimizer (${state.strategy})`;

    document.getElementById("kpiBerLabel").textContent =
      state.channel === "AWGN" ? "BER AWGN" : "BER Rayleigh (tanpa CSI)";
    const berVal = state.channel === "AWGN" ? act.ber_awgn : act.ber_rayleigh;
    document.getElementById("kpiBer").textContent =
      inOutage || berVal === null ? "n/a" : berVal.toExponential(2);
    document.getElementById("kpiBerSub").textContent = `target ${state.ber_target}`;

    document.getElementById("kpiRate").textContent = inOutage
      ? "outage"
      : `${fmtIdNum(act.rate_mbps, 2)} Mbit/s`;
    document.getElementById("kpiRateSub").textContent = inOutage
      ? "tanpa transmisi"
      : `Shannon ${fmtIdNum(act.shannon_mbps, 2)} Mbit/s`;

    const outBanner = document.getElementById("outageBanner");
    if (state.strategy === "MANUAL" && !act.ok && act.mod !== "Outage") {
      outBanner.hidden = false;
      outBanner.className = "notice-bar warn";
      outBanner.textContent = `Konfigurasi manual tidak layak: Eb/N0 ${fmtIdNum(act.ebn0_db, 1)} dB lebih rendah dari ambang ${fmtIdNum(act.ebn0_threshold_db, 2)} dB untuk ${act.mod} (BER ${state.ber_target}). Link dinyatakan outage.`;
    } else if (inOutage) {
      outBanner.hidden = false;
      outBanner.className = "notice-bar error";
      outBanner.textContent =
        "Tidak ada kombinasi modulasi dan RB yang memenuhi BER target pada jarak ini. Kurangi jarak atau naikkan daya pancar UE.";
    } else {
      outBanner.hidden = true;
    }

    const base = data.baseline_s0;
    document.getElementById("mcPairSummary").textContent =
      `Aktif: ${inOutage ? "Outage" : `${act.mod} × ${act.rb} RB`} | S0: ${base.ok ? "QPSK × 25 RB" : "Outage"}`;

    const runBtn = document.getElementById("btnRunMc");
    runBtn.disabled = inOutage;

    data.by_freq.forEach((item) => {
      const f = item.freq_mhz;
      const a = item.active;
      document.getElementById(`cmpSnr${f}`).textContent = `${fmtIdNum(a.snr_db, 1)} dB`;
      document.getElementById(`cmpMod${f}`).textContent = a.ok ? `${a.mod} (${a.rb})` : "Outage";
    });

    document.getElementById("snrChartTitle").textContent =
      `Kurva SNR terhadap Jarak (${state.env}, margin ${fmtIdNum(act.margin_db, 1)} dB, THEORETICAL)`;
    document.getElementById("freqTableTitle").textContent =
      `Perbandingan Frekuensi pada ${fmtIdNum(state.dist_km, 2)} km (${state.env})`;
    document.getElementById("stratTableTitle").textContent =
      `Fixed vs Adaptif pada ${fmtIdNum(state.dist_km, 2)} km (${state.freq_mhz} MHz ${state.env})`;

    drawSnrChart(data);
    renderFreqComparisonTable(data, lastStochData);
    updateMcStateUI();
  }

  function renderStochastic(data) {
    lastStochData = data;
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
        state.channel === "AWGN" ? "SIMULATED, shadowing" : "SIMULATED, +Rayleigh CSI";
    }

    data.freq_summary_s3.forEach((item) => {
      document.getElementById(`cmpCov${item.freq_mhz}`).textContent = item.radius_fading_label;
    });

    drawCoverageMap(data);
    renderStrategyTable(data);
    if (lastOpData) renderFreqComparisonTable(lastOpData, data);
  }

  function renderStrategyTable(stochData) {
    const tbody = document.querySelector("#tblStrategyCmp tbody");
    tbody.innerHTML = stochData.strategy_comparison
      .map((r) => {
        const condTxt =
          r.fading_cond_ber_mean === null ? "n/a" : r.fading_cond_ber_mean.toExponential(1);
        return `<tr>
          <td><strong>${r.scenario}</strong>: ${r.label}</td>
          <td>${r.median_config}</td>
          <td>${fmtIdNum(r.median_rate_mbps, 2)} Mbit/s</td>
          <td>${fmtIdNum(r.shadow_outage_pct, 1)}%</td>
          <td>${fmtIdNum(r.fading_outage_pct, 1)}%</td>
          <td>${fmtIdNum(r.fading_effective_rate_mbps, 2)} Mbit/s</td>
          <td>${condTxt}</td>
        </tr>`;
      })
      .join("");
  }

  function renderFreqComparisonTable(opData, stochData) {
    const tbody = document.querySelector("#tblFreqCmp tbody");
    const radMap = new Map();
    if (stochData && stochData.freq_summary_s3) {
      stochData.freq_summary_s3.forEach((r) => radMap.set(r.freq_mhz, r));
    }
    tbody.innerHTML = opData.by_freq
      .map((item) => {
        const s3 = item.s3;
        const rad = radMap.get(item.freq_mhz);
        const s3Cfg = s3.ok ? `${s3.mod} × ${s3.rb} RB` : "Outage";
        const s3Rate = s3.ok ? `${fmtIdNum(s3.rate_mbps, 2)} Mbit/s` : "outage";
        return `<tr>
          <td><strong>${item.freq_mhz} MHz</strong></td>
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

  function drawSnrChart(data) {
    const { ctx, W, H } = setupCanvas("cvSnr", 660, 310);
    const pad = { l: 52, r: 22, t: 18, b: 40 };
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

    // Cho-Yoon Es/N0 thresholds
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
      ctx.fillStyle = "#334155";
      ctx.textAlign = "right";
      ctx.fillText(`${mod} (${th.esn0_db.toFixed(1)} dB)`, W - pad.r - 4, py - 4);
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

    // Active distance cursor & operating point
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

    const pyAct = yToPx(data.active.snr_db);
    ctx.fillStyle = data.active.ok ? "#B45309" : "#9A1B1B";
    ctx.strokeStyle = "#0F172A";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(cx, pyAct, 5.2, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();

    // Legend
    [700, 900, 1800].forEach((f, idx) => {
      const lx = pad.l + 8;
      const ly = pad.t + 14 + idx * 16;
      ctx.fillStyle = FREQ_COLORS[f];
      ctx.fillRect(lx, ly - 5, 16, 3);
      ctx.fillStyle = "#0F172A";
      ctx.textAlign = "left";
      ctx.fillText(`${f} MHz${f === state.freq_mhz ? " (aktif)" : ""}`, lx + 22, ly);
    });
  }

  function drawConstellations() {
    const { ctx, W, H } = setupCanvas("cvConst", 600, 275);
    const chKey = state.channel === "AWGN" ? "awgn" : "rayleigh";

    if (!mcResult || mcKey !== currentParamKey()) {
      ctx.fillStyle = "#475569";
      ctx.font = "13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(
        mcResult
          ? "Parameter berubah. Jalankan ulang Monte Carlo untuk konstelasi aktif."
          : "Tekan 'Jalankan Monte Carlo' untuk menampilkan sampel I/Q nyata dari mesin Python.",
        W / 2,
        H / 2
      );
      return;
    }

    let panels = [];
    if (state.mc_view === "opt_vs_s0") {
      panels = [
        { title: `Dioptimalkan: ${mcResult.opt.modulation}`, res: mcResult.opt },
        {
          title: `Baseline S0: ${mcResult.base ? mcResult.base.modulation : "Outage"}`,
          res: mcResult.base,
        },
      ];
    } else {
      panels = [700, 900, 1800].map((f) => {
        const r = mcResult.by_freq[String(f)] || null;
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

      ctx.fillStyle = "#0F2A47";
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
      ctx.globalAlpha = 0.6;
      for (let i = 0; i < smp.i.length; i += 1) {
        const px = cx + smp.i[i] * scale;
        const py = cy - smp.q[i] * scale;
        if (px > x0 + 3 && px < x0 + colW - 3 && py > 28 && py < H - 12) {
          ctx.fillRect(px - 1.5, py - 1.5, 3, 3);
        }
      }
      ctx.globalAlpha = 1.0;

      const ideal = p.res.ideal_constellation;
      ctx.strokeStyle = "#0F2A47";
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

  function drawCoverageMap(stochData) {
    const { ctx, W, H } = setupCanvas("cvMap", 1180, 305);
    if (!stochData || !stochData.zones) return;

    const centers = [W * 0.17, W * 0.5, W * 0.83];
    const R_px = 104;
    const rMaxKm = 12.0;
    const cy = H / 2 + 4;

    stochData.zones.forEach((zone, idx) => {
      const cx = centers[idx];

      // Draw outer-to-inner concentric filled circles from Python rings
      const sortedRings = [...zone.rings].sort((a, b) => b.outer_km - a.outer_km);
      sortedRings.forEach((ring) => {
        const rPx = (ring.outer_km / rMaxKm) * R_px;
        ctx.fillStyle = MOD_COLOR[ring.modulation] || MOD_COLOR.Outage;
        ctx.beginPath();
        ctx.arc(cx, cy, rPx, 0, 2 * Math.PI);
        ctx.fill();
        ctx.strokeStyle = "#FFFFFF";
        ctx.lineWidth = 0.8;
        ctx.stroke();
      });

      // Outer 12 km cell border
      ctx.strokeStyle = "#0F172A";
      ctx.lineWidth = 1.3;
      ctx.beginPath();
      ctx.arc(cx, cy, R_px, 0, 2 * Math.PI);
      ctx.stroke();

      // Reliable radius rings
      if (zone.radius_stochastic_km > 0) {
        ctx.save();
        ctx.setLineDash([6, 4]);
        ctx.strokeStyle = "#0F2A47";
        ctx.lineWidth = 2.2;
        ctx.beginPath();
        ctx.arc(cx, cy, (zone.radius_stochastic_km / rMaxKm) * R_px, 0, 2 * Math.PI);
        ctx.stroke();
        ctx.restore();
      }
      if (zone.radius_fading_km > 0) {
        ctx.save();
        ctx.setLineDash([2, 3]);
        ctx.strokeStyle = "#B45309";
        ctx.lineWidth = 2.4;
        ctx.beginPath();
        ctx.arc(cx, cy, (zone.radius_fading_km / rMaxKm) * R_px, 0, 2 * Math.PI);
        ctx.stroke();
        ctx.restore();
      }

      // BTS & active UE markers
      ctx.fillStyle = "#0F172A";
      ctx.beginPath();
      ctx.arc(cx, cy, 4, 0, 2 * Math.PI);
      ctx.fill();

      const uePx = cx + (state.dist_km / rMaxKm) * R_px;
      ctx.fillStyle = "#FFFFFF";
      ctx.strokeStyle = "#0F172A";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(uePx, cy, 4.5, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "#0F2A47";
      ctx.font = "bold 12.5px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`${zone.freq_mhz} MHz | ${state.env}, ${zone.scenario}`, cx, 20);

      ctx.fillStyle = "#334155";
      ctx.font = "11px sans-serif";
      ctx.fillText(
        `Median: ${zone.radius_median_label} · Andal 95%: ${zone.radius_fading_label}`,
        cx,
        H - 12
      );
    });
  }

  function updateMcStateUI() {
    const notice = document.getElementById("mcStateNotice");
    const statsBox = document.getElementById("mcStatsBox");
    const inOutage = lastOpData && !lastOpData.active.ok;
    const chKey = state.channel === "AWGN" ? "awgn" : "rayleigh";

    if (inOutage) {
      notice.hidden = false;
      notice.className = "notice-bar info";
      notice.textContent = "Tidak ada transmisi yang dapat disimulasikan pada konfigurasi outage.";
      statsBox.hidden = true;
      drawConstellations();
      return;
    }

    if (!mcResult) {
      notice.hidden = false;
      notice.className = "notice-bar info";
      notice.textContent = `Belum dijalankan. Tekan Jalankan Monte Carlo untuk mengirim ${state.n_bits.toLocaleString("id-ID")} bit acak melalui kanal AWGN dan Rayleigh.`;
      statsBox.hidden = true;
      drawConstellations();
      return;
    }

    if (mcKey !== currentParamKey()) {
      notice.hidden = false;
      notice.className = "notice-bar warn";
      notice.textContent =
        "Parameter berubah sejak simulasi terakhir. Hasil sebelumnya disembunyikan agar tidak dianggap sebagai hasil aktif; jalankan ulang Monte Carlo.";
      statsBox.hidden = true;
      drawConstellations();
      return;
    }

    notice.hidden = true;
    statsBox.hidden = false;
    const lines = [
      ["Dioptimalkan", mcResult.opt],
      ["Baseline S0", mcResult.base],
    ].map(([name, res]) => {
      if (!res) return `<div><strong>${name}:</strong> outage, tidak ada transmisi.</div>`;
      const err = res[`mc_errors_${chKey}`];
      const ciL = res[`ci_low_${chKey}`];
      const ciH = res[`ci_high_${chKey}`];
      const ciTxt =
        err === 0
          ? `, CI 95% [0.0e+0, ${ciH.toExponential(1)}] (0 error, batas atas rule-of-three)`
          : `, CI 95% [${ciL.toExponential(1)}, ${ciH.toExponential(1)}]`;
      return `<div><strong>${name}</strong> (${res.modulation}, Eb/N0 ${fmtIdNum(res.ebn0_db, 2)} dB, ${res.n_bits.toLocaleString("id-ID")} bit / ${res.n_symbols.toLocaleString("id-ID")} simbol, sampel konstelasi ${res[`n_samples_${chKey}`]}): BER MC AWGN ${res.mc_ber_awgn.toExponential(2)} (teori ${res.theory_ber_awgn.toExponential(2)}); Rayleigh tanpa CSI ${res.mc_ber_rayleigh.toExponential(2)} (teori ${res.theory_ber_rayleigh.toExponential(2)})${ciTxt}.</div>`;
    });
    statsBox.innerHTML = lines.join("");
    drawConstellations();
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
      clearWorkbenchError();
      renderOperatingPoint(opCache.get(key));
      return;
    }
    if (opController) opController.abort();
    opController = new AbortController();
    document.getElementById("apiLoadingBanner").hidden = false;
    try {
      const data = await fetchJson("/api/operating-point", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: key,
        signal: opController.signal,
      });
      opCache.set(key, data);
      clearWorkbenchError();
      renderOperatingPoint(data);
    } catch (err) {
      if (err.name === "AbortError") return;
      clearTelemetryOnError();
      showWorkbenchError(`Gagal memuat titik operasi dari API Python: ${err.message}`);
    } finally {
      document.getElementById("apiLoadingBanner").hidden = true;
    }
  }

  async function refreshStochastic() {
    const payload = {
      freq_mhz: state.freq_mhz,
      env: state.env,
      dist_km: state.dist_km,
      tx_power_dbm: state.tx_power_dbm,
      ber_target: state.ber_target,
      active_strategy: state.strategy,
      zone_strategy: state.zone_strategy,
    };
    const key = JSON.stringify(payload);
    if (stochCache.has(key)) {
      renderStochastic(stochCache.get(key));
      return;
    }
    if (stochController) stochController.abort();
    stochController = new AbortController();
    try {
      const data = await fetchJson("/api/stochastic-analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: key,
        signal: stochController.signal,
      });
      stochCache.set(key, data);
      renderStochastic(data);
    } catch (err) {
      if (err.name === "AbortError") return;
      showWorkbenchError(`Gagal memuat analisis stokastik dari API Python: ${err.message}`);
    }
  }

  async function runMonteCarlo() {
    const btn = document.getElementById("btnRunMc");
    const notice = document.getElementById("mcStateNotice");
    if (mcController) mcController.abort();
    mcController = new AbortController();

    btn.disabled = true;
    notice.hidden = false;
    notice.className = "notice-bar info";
    notice.textContent = `Menjalankan simulasi Monte Carlo bit-level (${state.n_bits.toLocaleString("id-ID")} bit)...`;
    document.getElementById("mcStatsBox").hidden = true;

    const runParamKey = currentParamKey();
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
          n_bits: state.n_bits,
        }),
        signal: mcController.signal,
      });
      mcResult = data;
      mcKey = runParamKey;
      updateMcStateUI();
    } catch (err) {
      if (err.name === "AbortError") return;
      notice.hidden = false;
      notice.className = "notice-bar error";
      notice.textContent = `Monte Carlo gagal: ${err.message}`;
    } finally {
      btn.disabled = lastOpData ? !lastOpData.active.ok : false;
    }
  }

  function refreshAllWorkbench(immediate) {
    syncControlsFromState();
    updateMcStateUI();
    if (immediate) {
      clearTimeout(sliderDebounceTimer);
      refreshOperatingPoint();
      refreshStochastic();
      return;
    }
    clearTimeout(sliderDebounceTimer);
    sliderDebounceTimer = setTimeout(() => {
      refreshOperatingPoint();
      refreshStochastic();
    }, 90);
  }

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
    activeTab = tabName;
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
      refreshAllWorkbench(true);
    });
  });

  document.querySelectorAll("[data-env]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.env = btn.dataset.env;
      refreshAllWorkbench(true);
    });
  });

  document.querySelectorAll("[data-shadow]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.shadow = btn.dataset.shadow;
      refreshAllWorkbench(true);
    });
  });

  document.querySelectorAll("[data-channel]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.channel = btn.dataset.channel;
      refreshAllWorkbench(true);
    });
  });

  document.querySelectorAll("[data-ber]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.ber_target = Number(btn.dataset.ber);
      refreshAllWorkbench(true);
    });
  });

  document.querySelectorAll("[data-rb]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.rb_manual = Number(btn.dataset.rb);
      refreshAllWorkbench(true);
    });
  });

  document.querySelectorAll("[data-mod]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.mod_manual = btn.dataset.mod;
      refreshAllWorkbench(true);
    });
  });

  document.querySelectorAll("[data-nbits]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.n_bits = Number(btn.dataset.nbits);
      refreshAllWorkbench(true);
    });
  });

  document.querySelectorAll("[data-mcview]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.mc_view = btn.dataset.mcview;
      setActiveSegment("data-mcview", state.mc_view);
      drawConstellations();
    });
  });

  document.getElementById("selStrat").addEventListener("change", (e) => {
    state.strategy = e.target.value;
    if (["S0", "S1", "S2", "S3", "R0"].includes(state.strategy)) {
      state.zone_strategy = state.strategy;
    }
    refreshAllWorkbench(true);
  });

  document.getElementById("selZoneStrat").addEventListener("change", (e) => {
    state.zone_strategy = e.target.value;
    refreshAllWorkbench(true);
  });

  document.getElementById("rngDist").addEventListener("input", (e) => {
    state.dist_km = Number(e.target.value);
    refreshAllWorkbench(false);
  });

  document.getElementById("rngPt").addEventListener("input", (e) => {
    state.tx_power_dbm = Number(e.target.value);
    refreshAllWorkbench(false);
  });

  document.getElementById("btnPreset").addEventListener("click", () => {
    Object.assign(state, DEFAULTS);
    mcResult = null;
    mcKey = null;
    refreshAllWorkbench(true);
  });

  document.getElementById("btnRunMc").addEventListener("click", runMonteCarlo);

  document.querySelectorAll("[data-resenv]").forEach((btn) => {
    btn.addEventListener("click", () => {
      resultsEnv = btn.dataset.resenv;
      renderResultsView();
    });
  });

  document.getElementById("inpGlossSearch").addEventListener("input", renderGlossaryTable);
  document.getElementById("selGlossCat").addEventListener("change", renderGlossaryTable);

  refreshAllWorkbench(true);
})();
