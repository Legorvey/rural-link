"""Baseband AWGN and Rayleigh fading channel models with coherent reception."""

import numpy as np


def awgn_channel(
    symbols: np.ndarray,
    esn0_linear: float,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Pass unit-energy symbols (Es=1) through complex AWGN: y = x + w."""
    if esn0_linear <= 0.0:
        raise ValueError("esn0_linear must be strictly positive.")
    sym_arr = np.asarray(symbols, dtype=np.complex128)
    generator = rng if rng is not None else np.random.default_rng()
    n0 = 1.0 / float(esn0_linear)
    sigma = np.sqrt(n0 * 0.5)
    noise = sigma * (
        generator.standard_normal(sym_arr.shape) + 1j * generator.standard_normal(sym_arr.shape)
    )
    return sym_arr + noise


def rayleigh_fading_gains(
    n_symbols: int,
    rng: np.random.Generator | None = None,
    block_size: int = 1,
) -> np.ndarray:
    """Generate complex circularly symmetric Rayleigh channel gains h with E[|h|^2] = 1.

    block_size=1 gives independent symbol-by-symbol fading; block_size > 1 holds
    each fading realization constant over a coherence block.
    """
    if n_symbols < 0:
        raise ValueError("n_symbols must be non-negative.")
    if block_size < 1:
        raise ValueError("block_size must be >= 1.")
    if n_symbols == 0:
        return np.empty(0, dtype=np.complex128)

    generator = rng if rng is not None else np.random.default_rng()
    n_blocks = int(np.ceil(n_symbols / block_size))
    h_blocks = (
        generator.standard_normal(n_blocks) + 1j * generator.standard_normal(n_blocks)
    ) / np.sqrt(2.0)

    if block_size == 1:
        return h_blocks.astype(np.complex128)
    return np.repeat(h_blocks, block_size)[:n_symbols].astype(np.complex128)


def rayleigh_channel(
    symbols: np.ndarray,
    esn0_linear: float,
    rng: np.random.Generator | None = None,
    block_size: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Pass unit-energy symbols through flat Rayleigh fading + AWGN: y = h*x + w."""
    if esn0_linear <= 0.0:
        raise ValueError("esn0_linear must be strictly positive.")
    sym_arr = np.asarray(symbols, dtype=np.complex128).ravel()
    generator = rng if rng is not None else np.random.default_rng()
    h = rayleigh_fading_gains(n_symbols=sym_arr.size, rng=generator, block_size=block_size)
    faded = h * sym_arr
    received = awgn_channel(faded, esn0_linear=esn0_linear, rng=generator)
    return received, h


def coherent_equalize(received: np.ndarray, h: np.ndarray, eps: float = 1e-15) -> np.ndarray:
    """Coherent zero-forcing equalization with perfect CSI: x_hat = y / h."""
    rx_arr = np.asarray(received, dtype=np.complex128)
    h_arr = np.asarray(h, dtype=np.complex128)
    if rx_arr.shape != h_arr.shape:
        raise ValueError("received and h must have identical shapes.")
    # Guard against exact zero division while preserving phase
    mag = np.abs(h_arr)
    safe_h = np.where(mag < eps, eps + 0j, h_arr)
    return rx_arr / safe_h


def instantaneous_snr(avg_snr_linear: float | np.ndarray, h: np.ndarray) -> np.ndarray:
    """Compute instantaneous faded SNR: gamma_inst = gamma_avg * |h|^2."""
    if np.any(np.asarray(avg_snr_linear, dtype=float) <= 0.0):
        raise ValueError("avg_snr_linear must be strictly positive.")
    h_arr = np.asarray(h, dtype=np.complex128)
    return np.asarray(avg_snr_linear, dtype=float) * (np.abs(h_arr) ** 2)
