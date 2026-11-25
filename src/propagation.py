"""Close-In (CI) rural propagation model with log-normal shadow fading.

Reference: Park et al. (2023), Eq. (3) and Table II (1400 MHz LOS/NLOS).
Parameters are extrapolated to 900/1800 MHz for comparative simulation.
"""

import numpy as np
from scipy.stats import norm

from config import CI_PATH_LOSS_PARAMS, SHADOW_Z_95


def get_ci_parameters(environment: str) -> tuple[float, float]:
    """Return (path_loss_exponent_n, shadow_fading_std_db) for LOS or NLOS."""
    env_key = environment.strip().upper()
    if env_key not in CI_PATH_LOSS_PARAMS:
        raise ValueError(
            f"Unknown environment {environment!r}. Expected one of {tuple(CI_PATH_LOSS_PARAMS)}."
        )
    return CI_PATH_LOSS_PARAMS[env_key]


def fspl_1m_db(freq_mhz: float | np.ndarray) -> float | np.ndarray:
    """Free-space path loss at d0 = 1 m: 32.4 + 20*log10(f_GHz)."""
    freq_arr = np.asarray(freq_mhz, dtype=float)
    if np.any(freq_arr <= 0.0):
        raise ValueError("Carrier frequency must be positive (MHz).")
    result = 32.4 + 20.0 * np.log10(freq_arr / 1000.0)
    return float(result) if np.ndim(freq_mhz) == 0 else result


def sample_shadow_fading_db(
    sigma_db: float,
    size: int | tuple[int, ...] | None = None,
    rng: np.random.Generator | None = None,
) -> float | np.ndarray:
    """Sample zero-mean log-normal shadow fading X_sigma ~ Normal(0, sigma_db^2) in dB."""
    if sigma_db < 0.0:
        raise ValueError("Shadow fading standard deviation must be non-negative (dB).")
    generator = rng if rng is not None else np.random.default_rng()
    if sigma_db == 0.0:
        return 0.0 if size is None else np.zeros(size, dtype=float)
    sample = generator.normal(loc=0.0, scale=sigma_db, size=size)
    return float(sample) if size is None else sample


def analytical_shadow_margin_db(sigma_db: float, reliability: float = 0.95) -> float:
    """Compute analytical one-sided shadow margin in dB (1.645 * sigma at 95%)."""
    if sigma_db < 0.0:
        raise ValueError("Shadow fading standard deviation must be non-negative (dB).")
    if not (0.5 <= reliability < 1.0):
        raise ValueError("Reliability must be in [0.5, 1.0).")
    z_val = SHADOW_Z_95 if abs(reliability - 0.95) < 1e-12 else float(norm.ppf(reliability))
    return float(z_val * sigma_db)


def ci_path_loss_db(
    distance_m: float | np.ndarray,
    freq_mhz: float | np.ndarray,
    environment: str = "NLOS",
    stochastic: bool = False,
    rng: np.random.Generator | None = None,
    shadow_margin_db: float = 0.0,
) -> float | np.ndarray:
    """Compute Close-In path loss (dB) with d0 = 1 m.

    PL_dB = 32.4 + 20*log10(f_GHz) + 10*n*log10(d_m) + X_sigma + shadow_margin_db
    """
    if stochastic and shadow_margin_db != 0.0:
        raise ValueError(
            "Do not apply a deterministic shadow margin on top of random shadowing "
            "in the same reliability calculation."
        )
    if shadow_margin_db < 0.0:
        raise ValueError("shadow_margin_db must be non-negative.")

    d_arr = np.asarray(distance_m, dtype=float)
    if np.any(d_arr < 1.0):
        raise ValueError("Distance must be >= 1.0 m (CI reference distance d0 = 1 m).")

    n_exp, sigma_db = get_ci_parameters(environment)
    pl_1m = fspl_1m_db(freq_mhz)
    pl_median = pl_1m + 10.0 * n_exp * np.log10(d_arr)

    if stochastic:
        size = None if np.ndim(pl_median) == 0 else pl_median.shape
        x_sigma = sample_shadow_fading_db(sigma_db=sigma_db, size=size, rng=rng)
        pl_total = pl_median + x_sigma
    else:
        pl_total = pl_median + shadow_margin_db

    return float(pl_total) if np.ndim(pl_total) == 0 else pl_total


def median_path_loss_db(
    distance_m: float | np.ndarray,
    freq_mhz: float | np.ndarray,
    environment: str = "NLOS",
) -> float | np.ndarray:
    """Compute median CI path loss (X_sigma = 0) in dB."""
    return ci_path_loss_db(
        distance_m=distance_m,
        freq_mhz=freq_mhz,
        environment=environment,
        stochastic=False,
        shadow_margin_db=0.0,
    )


def stochastic_path_loss_db(
    distance_m: float | np.ndarray,
    freq_mhz: float | np.ndarray,
    environment: str = "NLOS",
    rng: np.random.Generator | None = None,
) -> float | np.ndarray:
    """Compute stochastic CI path loss with random log-normal shadowing in dB."""
    return ci_path_loss_db(
        distance_m=distance_m,
        freq_mhz=freq_mhz,
        environment=environment,
        stochastic=True,
        rng=rng,
        shadow_margin_db=0.0,
    )
