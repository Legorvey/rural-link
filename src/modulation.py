"""Gray-coded digital modulation, ML demapping, theoretical BER, and thresholds."""

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import erfc

from config import MODULATION_ORDERS, MODULATIONS


def _validate_modulation(modulation: str) -> int:
    if modulation not in MODULATION_ORDERS:
        raise ValueError(
            f"Unsupported modulation {modulation!r}. Expected one of {tuple(MODULATION_ORDERS)}."
        )
    return MODULATION_ORDERS[modulation]


def bits_per_symbol(modulation: str) -> int:
    """Return k = log2(M) bits per symbol for a supported modulation."""
    m_val = _validate_modulation(modulation)
    return int(np.log2(m_val))


def _gray_pam_table(k_dim: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (levels, bit_patterns) for 2^k_dim Gray-coded PAM, unnormalized odd integers."""
    n_levels = 1 << k_dim
    indices = np.arange(n_levels, dtype=np.int64)
    gray_codes = (indices ^ (indices >> 1)).astype(np.int64)
    # Odd integer levels: -(n_levels - 1), ..., +(n_levels - 1)
    levels = (2 * indices - (n_levels - 1)).astype(float)
    bit_patterns = np.zeros((n_levels, k_dim), dtype=np.uint8)
    for b in range(k_dim):
        bit_patterns[:, b] = (gray_codes >> (k_dim - 1 - b)) & 1
    # Map integer Gray code -> level via lookup array indexed by gray_code
    gray_to_level = np.empty(n_levels, dtype=float)
    gray_to_level[gray_codes] = levels
    return gray_to_level, bit_patterns


def _pam_scale(modulation: str) -> float:
    """Normalization scale so average complex symbol energy E[|x|^2] = 1."""
    if modulation == "BPSK":
        return 1.0
    if modulation == "QPSK":
        return 1.0 / np.sqrt(2.0)
    if modulation == "16-QAM":
        return 1.0 / np.sqrt(10.0)
    if modulation == "64-QAM":
        return 1.0 / np.sqrt(42.0)
    raise ValueError(f"Unsupported modulation: {modulation!r}")


def _map_pam_bits(bits_2d: np.ndarray, k_dim: int, scale: float) -> np.ndarray:
    """Map (N_sym, k_dim) bits to scaled Gray-coded PAM levels."""
    gray_to_level, _ = _gray_pam_table(k_dim)
    weights = 1 << np.arange(k_dim - 1, -1, -1, dtype=np.int64)
    int_vals = bits_2d.astype(np.int64) @ weights
    return gray_to_level[int_vals] * scale


def _demap_pam_values(values: np.ndarray, k_dim: int, scale: float) -> np.ndarray:
    """Exact 1D nearest-neighbor ML slicing for Gray-coded PAM, returning (N_sym, k_dim) bits."""
    n_levels = 1 << k_dim
    _, bit_patterns = _gray_pam_table(k_dim)
    unscaled = values / scale
    # Nearest odd integer in [-(n_levels - 1), +(n_levels - 1)]
    idx = np.rint((unscaled + (n_levels - 1)) * 0.5).astype(np.int64)
    idx = np.clip(idx, 0, n_levels - 1)
    return bit_patterns[idx]


def modulate(bits: np.ndarray, modulation: str) -> tuple[np.ndarray, int]:
    """Map binary array (0/1) to unit-energy complex baseband symbols.

    Returns (symbols, n_pad_bits). Arbitrary bit lengths are zero-padded to a
    multiple of k = log2(M) and n_pad_bits is returned for exact trimming.
    """
    k = bits_per_symbol(modulation)
    bit_arr = np.asarray(bits, dtype=np.uint8).ravel()
    if bit_arr.size == 0:
        return np.empty(0, dtype=np.complex128), 0
    if np.any((bit_arr != 0) & (bit_arr != 1)):
        raise ValueError("Input bits must contain only 0 and 1.")

    rem = bit_arr.size % k
    n_pad = (k - rem) if rem != 0 else 0
    if n_pad > 0:
        bit_arr = np.concatenate([bit_arr, np.zeros(n_pad, dtype=np.uint8)])

    grouped = bit_arr.reshape(-1, k)
    scale = _pam_scale(modulation)

    if modulation == "BPSK":
        real_part = _map_pam_bits(grouped, k_dim=1, scale=scale)
        symbols = real_part.astype(np.complex128)
    else:
        k_dim = k // 2
        i_part = _map_pam_bits(grouped[:, :k_dim], k_dim=k_dim, scale=scale)
        q_part = _map_pam_bits(grouped[:, k_dim:], k_dim=k_dim, scale=scale)
        symbols = (i_part + 1j * q_part).astype(np.complex128)

    return symbols, n_pad


def demodulate(
    received_symbols: np.ndarray,
    modulation: str,
    n_pad_bits: int = 0,
) -> np.ndarray:
    """Nearest-neighbor ML hard-decision demapping to binary array (0/1)."""
    k = bits_per_symbol(modulation)
    if n_pad_bits < 0 or n_pad_bits >= k:
        raise ValueError(f"n_pad_bits must be in [0, {k - 1}].")
    sym_arr = np.asarray(received_symbols, dtype=np.complex128).ravel()
    if sym_arr.size == 0:
        return np.empty(0, dtype=np.uint8)

    scale = _pam_scale(modulation)
    if modulation == "BPSK":
        bits_2d = _demap_pam_values(sym_arr.real, k_dim=1, scale=scale)
    else:
        k_dim = k // 2
        i_bits = _demap_pam_values(sym_arr.real, k_dim=k_dim, scale=scale)
        q_bits = _demap_pam_values(sym_arr.imag, k_dim=k_dim, scale=scale)
        bits_2d = np.hstack([i_bits, q_bits])

    flat_bits = bits_2d.ravel()
    if n_pad_bits > 0:
        flat_bits = flat_bits[:-n_pad_bits]
    return flat_bits


def get_constellation(modulation: str) -> tuple[np.ndarray, list[str]]:
    """Return all unique normalized constellation symbols and their Gray bit labels."""
    k = bits_per_symbol(modulation)
    m_val = 1 << k
    labels = [format(i, f"0{k}b") for i in range(m_val)]
    all_bits = np.array([[int(ch) for ch in lbl] for lbl in labels], dtype=np.uint8).ravel()
    symbols, n_pad = modulate(all_bits, modulation)
    assert n_pad == 0
    return symbols, labels


def q_func(x: float | np.ndarray) -> float | np.ndarray:
    """Gaussian Q-function Q(x) = 0.5 * erfc(x / sqrt(2))."""
    arr = np.asarray(x, dtype=float)
    res = 0.5 * erfc(arr / np.sqrt(2.0))
    return float(res) if np.ndim(x) == 0 else res


def _exact_gray_qam_ber_scalar(ebn0_lin: np.ndarray, m_val: int) -> np.ndarray:
    """Exact Gray-coded square M-QAM BER in AWGN (Cho & Yoon, 2002)."""
    k = int(np.log2(m_val))
    sqrt_m = int(np.sqrt(m_val))
    k_dim = k // 2
    scale_arg = np.sqrt((3.0 * k / (2.0 * (m_val - 1))) * ebn0_lin)

    ber_total = np.zeros_like(ebn0_lin, dtype=float)
    for j in range(1, k_dim + 1):
        upper_i = int((1.0 - 2.0 ** (-j)) * sqrt_m)
        pb_j = np.zeros_like(ebn0_lin, dtype=float)
        for i in range(upper_i):
            sign = -1.0 if (int(np.floor(i * (2 ** (j - 1)) / sqrt_m)) % 2 == 1) else 1.0
            weight = (2 ** (j - 1)) - np.floor((i * (2 ** (j - 1)) / sqrt_m) + 0.5)
            pb_j += (sign * weight / sqrt_m) * erfc((2 * i + 1) * scale_arg)
        ber_total += pb_j
    return ber_total / k_dim


def theoretical_ber_awgn(
    ebn0_linear: float | np.ndarray,
    modulation: str,
    method: str = "exact",
) -> float | np.ndarray:
    """Theoretical bit error rate in AWGN vs linear Eb/N0.

    - BPSK / QPSK: exact Q(sqrt(2 * Eb/N0)).
    - 16-QAM / 64-QAM: exact Gray-coded expression (Cho & Yoon, 2002) when
      method='exact', or standard nearest-neighbor approximation when method='approx'.
    """
    m_val = _validate_modulation(modulation)
    arr = np.asarray(ebn0_linear, dtype=float)
    if np.any(arr <= 0.0):
        raise ValueError("ebn0_linear must be strictly positive.")

    if modulation in ("BPSK", "QPSK"):
        res = q_func(np.sqrt(2.0 * arr))
    elif method == "exact":
        res = _exact_gray_qam_ber_scalar(arr, m_val)
    elif method == "approx":
        k = np.log2(m_val)
        sqrt_m = np.sqrt(m_val)
        res = (4.0 / k) * (1.0 - 1.0 / sqrt_m) * q_func(np.sqrt(3.0 * k * arr / (m_val - 1.0)))
    else:
        raise ValueError(f"Unknown method {method!r}. Expected 'exact' or 'approx'.")

    return float(res) if np.ndim(ebn0_linear) == 0 else res


def theoretical_ber_rayleigh(
    ebn0_linear: float | np.ndarray,
    modulation: str,
) -> float | np.ndarray:
    """Theoretical average BER in flat Rayleigh fading vs average linear Eb/N0.

    - BPSK / QPSK: exact closed-form 0.5 * (1 - sqrt(gamma_b / (1 + gamma_b))).
    - 16-QAM / 64-QAM: numerical integration of exact conditional AWGN BER over
      exponentially distributed instantaneous channel power gain u ~ Exp(1).
    """
    _validate_modulation(modulation)
    arr = np.asarray(ebn0_linear, dtype=float)
    if np.any(arr <= 0.0):
        raise ValueError("ebn0_linear must be strictly positive.")

    if modulation in ("BPSK", "QPSK"):
        res = 0.5 * (1.0 - np.sqrt(arr / (1.0 + arr)))
        return float(res) if np.ndim(ebn0_linear) == 0 else res

    flat = np.atleast_1d(arr).ravel()
    out = np.empty_like(flat, dtype=float)
    for idx, gamma_b in enumerate(flat):
        val, _ = quad(
            lambda u, gb=float(gamma_b): (
                float(theoretical_ber_awgn(u * gb, modulation)) * np.exp(-u)
            ),
            1e-12,
            np.inf,
            epsabs=1e-12,
            epsrel=1e-9,
            limit=100,
        )
        out[idx] = val

    reshaped = out.reshape(arr.shape)
    return float(reshaped.item()) if np.ndim(ebn0_linear) == 0 else reshaped


def derive_switching_thresholds(
    ber_target: float = 1e-2,
    modulations: tuple[str, ...] = MODULATIONS,
) -> dict[str, dict[str, float]]:
    """Numerically solve AWGN BER(Eb/N0) = ber_target for each modulation.

    Returns dict mapping modulation -> {ebn0_linear, ebn0_db, esn0_linear, esn0_db}.
    """
    if not (0.0 < ber_target < 0.5):
        raise ValueError("ber_target must be in (0, 0.5).")

    thresholds: dict[str, dict[str, float]] = {}
    for mod in modulations:
        k = bits_per_symbol(mod)

        def objective(ebn0_db: float, m_name: str = mod) -> float:
            ebn0_lin = 10.0 ** (ebn0_db / 10.0)
            return float(theoretical_ber_awgn(ebn0_lin, m_name, method="exact")) - ber_target

        ebn0_db_star = float(brentq(objective, -20.0, 40.0, xtol=1e-10))
        ebn0_lin_star = float(10.0 ** (ebn0_db_star / 10.0))
        esn0_lin_star = float(ebn0_lin_star * k)
        esn0_db_star = float(ebn0_db_star + 10.0 * np.log10(float(k)))
        thresholds[mod] = {
            "ebn0_linear": ebn0_lin_star,
            "ebn0_db": ebn0_db_star,
            "esn0_linear": esn0_lin_star,
            "esn0_db": esn0_db_star,
        }
    return thresholds
