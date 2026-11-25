"""Uplink link budget, RB power/bandwidth allocation, energy normalization, and nominal rates."""

from dataclasses import dataclass

import numpy as np

from config import DEFAULT_CONFIG, MODULATION_ORDERS


@dataclass(frozen=True)
class LinkBudgetResult:
    """Container for uplink link budget quantities with explicit units."""

    n_rb: int
    b_active_hz: float
    path_loss_db: float | np.ndarray
    pr_dbm: float | np.ndarray
    noise_dbm: float
    power_per_rb_dbm: float
    snr_db: float | np.ndarray
    snr_linear: float | np.ndarray


def db_to_linear(db: float | np.ndarray) -> float | np.ndarray:
    """Convert decibel ratio to linear ratio."""
    arr = np.asarray(db, dtype=float)
    res = np.power(10.0, arr / 10.0)
    return float(res) if np.ndim(db) == 0 else res


def linear_to_db(linear: float | np.ndarray) -> float | np.ndarray:
    """Convert positive linear ratio to decibels."""
    arr = np.asarray(linear, dtype=float)
    if np.any(arr <= 0.0):
        raise ValueError("Linear ratio must be strictly positive for dB conversion.")
    res = 10.0 * np.log10(arr)
    return float(res) if np.ndim(linear) == 0 else res


def dbm_to_watts(dbm: float | np.ndarray) -> float | np.ndarray:
    """Convert power in dBm to watts."""
    arr = np.asarray(dbm, dtype=float)
    res = np.power(10.0, (arr - 30.0) / 10.0)
    return float(res) if np.ndim(dbm) == 0 else res


def watts_to_dbm(watts: float | np.ndarray) -> float | np.ndarray:
    """Convert positive power in watts to dBm."""
    arr = np.asarray(watts, dtype=float)
    if np.any(arr <= 0.0):
        raise ValueError("Power in watts must be strictly positive.")
    res = 10.0 * np.log10(arr) + 30.0
    return float(res) if np.ndim(watts) == 0 else res


def active_bandwidth_hz(n_rb: int, rb_bandwidth_hz: float = 180_000.0) -> float:
    """Compute active uplink bandwidth B_active = N_RB * rb_bandwidth_hz."""
    if not isinstance(n_rb, (int, np.integer)) or isinstance(n_rb, bool) or n_rb < 1:
        raise ValueError("n_rb must be a positive integer.")
    if rb_bandwidth_hz <= 0.0:
        raise ValueError("rb_bandwidth_hz must be positive.")
    return float(int(n_rb) * rb_bandwidth_hz)


def power_per_rb_dbm(tx_power_dbm: float, n_rb: int) -> float:
    """Compute transmit power per RB (dBm) under constant total UE transmit power."""
    if not isinstance(n_rb, (int, np.integer)) or isinstance(n_rb, bool) or n_rb < 1:
        raise ValueError("n_rb must be a positive integer.")
    return float(tx_power_dbm - 10.0 * np.log10(float(n_rb)))


def rb_snr_gain_db(n_rb_baseline: int, n_rb_new: int) -> float:
    """Analytical SNR gain from reducing active RBs at constant total transmit power.

    Note: Never add this gain again when SNR already uses B_active = n_rb_new * 180 kHz.
    """
    if n_rb_baseline < 1 or n_rb_new < 1:
        raise ValueError("RB counts must be positive integers.")
    return float(10.0 * np.log10(float(n_rb_baseline) / float(n_rb_new)))


def received_power_dbm(
    tx_power_dbm: float,
    tx_gain_dbi: float,
    rx_gain_dbi: float,
    path_loss_db: float | np.ndarray,
    feeder_loss_db: float,
    body_loss_db: float,
) -> float | np.ndarray:
    """Compute received power Pr_dBm = Pt + Gt + Gr - PL - feeder_loss - body_loss."""
    if feeder_loss_db < 0.0 or body_loss_db < 0.0:
        raise ValueError("Feeder and body losses must be non-negative (dB).")
    pl_arr = np.asarray(path_loss_db, dtype=float)
    pr = tx_power_dbm + tx_gain_dbi + rx_gain_dbi - pl_arr - feeder_loss_db - body_loss_db
    return float(pr) if np.ndim(path_loss_db) == 0 else pr


def thermal_noise_dbm(
    bandwidth_hz: float,
    noise_figure_db: float,
    noise_density_dbm_hz: float = -174.0,
) -> float:
    """Compute receiver noise power: -174 + 10*log10(B_active) + NF_dB."""
    if bandwidth_hz <= 0.0:
        raise ValueError("Bandwidth must be positive (Hz).")
    if noise_figure_db < 0.0:
        raise ValueError("Noise figure must be non-negative (dB).")
    return float(noise_density_dbm_hz + 10.0 * np.log10(bandwidth_hz) + noise_figure_db)


def compute_link_budget(
    path_loss_db: float | np.ndarray,
    n_rb: int = 25,
    tx_power_dbm: float = DEFAULT_CONFIG.ue_tx_power_dbm,
    tx_gain_dbi: float = DEFAULT_CONFIG.ue_antenna_gain_dbi,
    rx_gain_dbi: float = DEFAULT_CONFIG.bts_rx_antenna_gain_dbi,
    feeder_loss_db: float = DEFAULT_CONFIG.feeder_loss_db,
    body_loss_db: float = DEFAULT_CONFIG.body_loss_db,
    noise_figure_db: float = DEFAULT_CONFIG.rx_noise_figure_db,
    rb_bandwidth_hz: float = DEFAULT_CONFIG.rb_bandwidth_hz,
    noise_density_dbm_hz: float = DEFAULT_CONFIG.thermal_noise_density_dbm_hz,
) -> LinkBudgetResult:
    """Evaluate complete noise-limited uplink link budget for given path loss and N_RB."""
    b_active = active_bandwidth_hz(n_rb=n_rb, rb_bandwidth_hz=rb_bandwidth_hz)
    pr = received_power_dbm(
        tx_power_dbm=tx_power_dbm,
        tx_gain_dbi=tx_gain_dbi,
        rx_gain_dbi=rx_gain_dbi,
        path_loss_db=path_loss_db,
        feeder_loss_db=feeder_loss_db,
        body_loss_db=body_loss_db,
    )
    noise = thermal_noise_dbm(
        bandwidth_hz=b_active,
        noise_figure_db=noise_figure_db,
        noise_density_dbm_hz=noise_density_dbm_hz,
    )
    snr_db = np.asarray(pr, dtype=float) - noise
    snr_lin = db_to_linear(snr_db)
    if np.ndim(path_loss_db) == 0:
        snr_db_out: float | np.ndarray = float(snr_db)
        snr_lin_out: float | np.ndarray = float(snr_lin)
    else:
        snr_db_out = snr_db
        snr_lin_out = snr_lin

    return LinkBudgetResult(
        n_rb=int(n_rb),
        b_active_hz=b_active,
        path_loss_db=path_loss_db,
        pr_dbm=pr,
        noise_dbm=noise,
        power_per_rb_dbm=power_per_rb_dbm(tx_power_dbm, n_rb),
        snr_db=snr_db_out,
        snr_linear=snr_lin_out,
    )


def _resolve_bits_per_symbol(modulation_or_order: str | int) -> int:
    if isinstance(modulation_or_order, str):
        if modulation_or_order not in MODULATION_ORDERS:
            raise ValueError(f"Unsupported modulation: {modulation_or_order!r}")
        m_val = MODULATION_ORDERS[modulation_or_order]
    else:
        m_val = int(modulation_or_order)
    if m_val < 2 or (m_val & (m_val - 1)) != 0:
        raise ValueError("Modulation order M must be a power of 2 >= 2.")
    return int(np.log2(m_val))


def snr_to_ebn0_db(
    snr_db: float | np.ndarray,
    modulation_or_order: str | int,
) -> float | np.ndarray:
    """Convert Es/N0 (= SNR_dB under Rs = B_active) to Eb/N0 in dB."""
    k = _resolve_bits_per_symbol(modulation_or_order)
    arr = np.asarray(snr_db, dtype=float)
    res = arr - 10.0 * np.log10(float(k))
    return float(res) if np.ndim(snr_db) == 0 else res


def snr_to_ebn0_linear(
    snr_linear: float | np.ndarray,
    modulation_or_order: str | int,
) -> float | np.ndarray:
    """Convert Es/N0 (= SNR_linear under Rs = B_active) to linear Eb/N0."""
    k = _resolve_bits_per_symbol(modulation_or_order)
    arr = np.asarray(snr_linear, dtype=float)
    if np.any(arr <= 0.0):
        raise ValueError("snr_linear must be strictly positive.")
    res = arr / float(k)
    return float(res) if np.ndim(snr_linear) == 0 else res


def nominal_data_rate_bps(b_active_hz: float, modulation_or_order: str | int) -> float:
    """Compute uncoded nominal bit rate Rb = B_active * log2(M) in bps (no overhead)."""
    if b_active_hz <= 0.0:
        raise ValueError("b_active_hz must be positive.")
    k = _resolve_bits_per_symbol(modulation_or_order)
    return float(b_active_hz * k)


def spectral_efficiency(
    b_active_hz: float,
    modulation_or_order: str | int,
    nominal_channel_bw_hz: float = DEFAULT_CONFIG.nominal_channel_bandwidth_hz,
) -> tuple[float, float]:
    """Return (eta_active, eta_channel) in bps/Hz."""
    if nominal_channel_bw_hz <= 0.0:
        raise ValueError("nominal_channel_bw_hz must be positive.")
    rb = nominal_data_rate_bps(b_active_hz, modulation_or_order)
    eta_active = rb / b_active_hz
    eta_channel = rb / nominal_channel_bw_hz
    return float(eta_active), float(eta_channel)


def shannon_capacity_bps(
    b_active_hz: float,
    snr_linear: float | np.ndarray,
) -> float | np.ndarray:
    """Theoretical Shannon capacity C = B_active * log2(1 + SNR_linear) in bps.

    Reference only: never label as actual modulation throughput.
    """
    if b_active_hz <= 0.0:
        raise ValueError("b_active_hz must be positive.")
    arr = np.asarray(snr_linear, dtype=float)
    if np.any(arr < 0.0):
        raise ValueError("snr_linear must be non-negative.")
    res = b_active_hz * np.log2(1.0 + arr)
    return float(res) if np.ndim(snr_linear) == 0 else res
