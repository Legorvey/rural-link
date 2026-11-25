"""BER/SER error metrics, statistical confidence bounds, and Monte Carlo runner."""

from dataclasses import dataclass

import numpy as np

from config import DEFAULT_SEED
from src.channels import awgn_channel, coherent_equalize, rayleigh_channel
from src.modulation import bits_per_symbol, demodulate, modulate


@dataclass(frozen=True)
class ErrorMetrics:
    """Statistical summary of bit/symbol errors from a simulation run."""

    n_bits: int
    n_bit_errors: int
    ber: float
    n_symbols: int
    n_symbol_errors: int | None
    ser: float | None
    ci_lower: float | None
    ci_upper: float | None
    is_upper_bound_only: bool
    assume_independent: bool


def wilson_ci_95(n_errors: int, n_trials: int) -> tuple[float, float, bool]:
    """Compute 95% confidence bounds for independent binomial trials.

    When n_errors == 0, returns (0.0, 3.0 / n_trials, True) using the rule of three
    for a one-sided approximate 95% upper bound.
    """
    if n_trials < 1:
        raise ValueError("n_trials must be >= 1.")
    if n_errors < 0 or n_errors > n_trials:
        raise ValueError("n_errors must be in [0, n_trials].")

    if n_errors == 0:
        return 0.0, min(1.0, 3.0 / float(n_trials)), True

    z = 1.959963984540054
    z2 = z * z
    n = float(n_trials)
    p_hat = float(n_errors) / n
    denom = 1.0 + z2 / n
    center = (p_hat + z2 / (2.0 * n)) / denom
    half_width = (z * np.sqrt((p_hat * (1.0 - p_hat) + z2 / (4.0 * n)) / n)) / denom
    return max(0.0, float(center - half_width)), min(1.0, float(center + half_width)), False


def compute_error_metrics(
    tx_bits: np.ndarray,
    rx_bits: np.ndarray,
    tx_symbols: np.ndarray | None = None,
    rx_symbols_decided: np.ndarray | None = None,
    assume_independent: bool = True,
) -> ErrorMetrics:
    """Compare transmitted vs recovered bits (and optional symbols) with CI bounds."""
    tx_b = np.asarray(tx_bits, dtype=np.uint8).ravel()
    rx_b = np.asarray(rx_bits, dtype=np.uint8).ravel()
    if tx_b.size == 0 or tx_b.size != rx_b.size:
        raise ValueError("tx_bits and rx_bits must be non-empty and equal length.")

    n_bits = int(tx_b.size)
    n_bit_errors = int(np.count_nonzero(tx_b != rx_b))
    ber = float(n_bit_errors) / float(n_bits)

    n_symbols = 0
    n_symbol_errors: int | None = None
    ser: float | None = None
    if tx_symbols is not None and rx_symbols_decided is not None:
        tx_s = np.asarray(tx_symbols).ravel()
        rx_s = np.asarray(rx_symbols_decided).ravel()
        if tx_s.size != rx_s.size:
            raise ValueError("tx_symbols and rx_symbols_decided must have equal length.")
        n_symbols = int(tx_s.size)
        n_symbol_errors = int(np.count_nonzero(~np.isclose(tx_s, rx_s, atol=1e-9)))
        ser = float(n_symbol_errors) / float(n_symbols) if n_symbols > 0 else 0.0

    if assume_independent:
        ci_low, ci_high, is_upper = wilson_ci_95(n_bit_errors, n_bits)
    else:
        ci_low, ci_high, is_upper = None, None, False

    return ErrorMetrics(
        n_bits=n_bits,
        n_bit_errors=n_bit_errors,
        ber=ber,
        n_symbols=n_symbols,
        n_symbol_errors=n_symbol_errors,
        ser=ser,
        ci_lower=ci_low,
        ci_upper=ci_high,
        is_upper_bound_only=is_upper,
        assume_independent=assume_independent,
    )


def simulate_ber_point(
    modulation: str,
    ebn0_db: float,
    n_bits: int,
    channel_type: str = "AWGN",
    seed: int = DEFAULT_SEED,
    block_size: int = 1,
    batch_size_bits: int = 200_000,
    constellation_sample_size: int = 0,
) -> tuple[ErrorMetrics, np.ndarray | None]:
    """Run batched bit-level Monte Carlo simulation at a single Eb/N0 point."""
    if n_bits < 1:
        raise ValueError("n_bits must be >= 1.")
    if batch_size_bits < 1:
        raise ValueError("batch_size_bits must be >= 1.")
    ch = channel_type.strip().upper()
    if ch not in ("AWGN", "RAYLEIGH"):
        raise ValueError(f"Unsupported channel_type {channel_type!r}.")

    k = bits_per_symbol(modulation)
    ebn0_lin = 10.0 ** (float(ebn0_db) / 10.0)
    esn0_lin = ebn0_lin * float(k)
    rng = np.random.default_rng(seed)

    total_bits = 0
    total_bit_errors = 0
    total_symbols = 0
    total_symbol_errors = 0
    constellation_sample: np.ndarray | None = None

    # Align batch size to a multiple of k to avoid artificial padding inside batches
    aligned_batch = max(k, (batch_size_bits // k) * k)
    remaining = int(n_bits)

    while remaining > 0:
        cur_bits = min(remaining, aligned_batch)
        tx_bits = rng.integers(0, 2, size=cur_bits, dtype=np.uint8)
        tx_sym, n_pad = modulate(tx_bits, modulation)

        if ch == "AWGN":
            rx_sym = awgn_channel(tx_sym, esn0_linear=esn0_lin, rng=rng)
            eq_sym = rx_sym
        else:
            rx_sym, h = rayleigh_channel(
                tx_sym, esn0_linear=esn0_lin, rng=rng, block_size=block_size
            )
            eq_sym = coherent_equalize(rx_sym, h)

        if constellation_sample is None and constellation_sample_size > 0:
            constellation_sample = eq_sym[:constellation_sample_size].copy()

        rx_bits = demodulate(eq_sym, modulation, n_pad_bits=n_pad)
        decided_sym, _ = modulate(rx_bits, modulation)

        total_bits += int(tx_bits.size)
        total_bit_errors += int(np.count_nonzero(tx_bits != rx_bits))
        total_symbols += int(tx_sym.size)
        total_symbol_errors += int(np.count_nonzero(~np.isclose(tx_sym, decided_sym, atol=1e-9)))
        remaining -= cur_bits

    assume_indep = (ch == "AWGN") or (block_size == 1)
    if assume_indep:
        ci_low, ci_high, is_upper = wilson_ci_95(total_bit_errors, total_bits)
    else:
        ci_low, ci_high, is_upper = None, None, False

    metrics = ErrorMetrics(
        n_bits=total_bits,
        n_bit_errors=total_bit_errors,
        ber=float(total_bit_errors) / float(total_bits),
        n_symbols=total_symbols,
        n_symbol_errors=total_symbol_errors,
        ser=float(total_symbol_errors) / float(total_symbols),
        ci_lower=ci_low,
        ci_upper=ci_high,
        is_upper_bound_only=is_upper,
        assume_independent=assume_indep,
    )
    return metrics, constellation_sample
