"""Centralized typed configuration and scientific defaults for RuralLink."""

from dataclasses import dataclass

PROJECT_NAME = "RuralLink"
RESEARCH_TITLE = (
    "Analisis Peningkatan Jangkauan Uplink melalui Modulasi Adaptif dan Alokasi Bandwidth "
    "pada Frekuensi 900 MHz dan 1800 MHz di Wilayah 3T Indonesia"
)
SCIENTIFIC_ENGINE_IMPLEMENTED = True
DEFAULT_SEED = 42

MODULATIONS: tuple[str, ...] = ("BPSK", "QPSK", "16-QAM", "64-QAM")
MODULATION_ORDERS: dict[str, int] = {
    "BPSK": 2,
    "QPSK": 4,
    "16-QAM": 16,
    "64-QAM": 64,
}

# Close-In (CI) path loss parameters from Park et al. (2023), Table II, 1400 MHz.
# Format: environment -> (path_loss_exponent_n, shadow_fading_std_db)
CI_PATH_LOSS_PARAMS: dict[str, tuple[float, float]] = {
    "LOS": (2.16, 3.07),
    "NLOS": (2.56, 11.40),
}

SHADOW_Z_95 = 1.645


@dataclass(frozen=True)
class SimulationConfig:
    """Typed simulation parameters with explicit units and validation."""

    carrier_frequencies_mhz: tuple[float, ...] = (900.0, 1800.0)
    nominal_channel_bandwidth_hz: float = 5_000_000.0
    active_rb_choices: tuple[int, ...] = (1, 2, 5, 10, 25)
    rb_bandwidth_hz: float = 180_000.0
    max_active_bandwidth_hz: float = 4_500_000.0

    # Uplink RF parameters adapted from Yogapratama Table IV & Reddy Table 1
    ue_tx_power_dbm: float = 23.0
    ue_antenna_gain_dbi: float = 0.0
    bts_rx_antenna_gain_dbi: float = 11.0
    feeder_loss_db: float = 5.0
    body_loss_db: float = 3.0
    rx_noise_figure_db: float = 4.0
    thermal_noise_density_dbm_hz: float = -174.0

    # Evaluation range and reliability targets
    distance_min_km: float = 1.0
    distance_max_km: float = 12.0
    ber_target: float = 1e-2
    outage_target: float = 0.05

    modulations: tuple[str, ...] = MODULATIONS
    default_seed: int = DEFAULT_SEED

    # Monte Carlo bit budgets
    quick_n_bits: int = 100_000
    research_n_bits: int = 1_000_000

    def __post_init__(self) -> None:
        if not self.carrier_frequencies_mhz or any(f <= 0.0 for f in self.carrier_frequencies_mhz):
            raise ValueError("Carrier frequencies must be positive (MHz).")
        if self.nominal_channel_bandwidth_hz <= 0.0:
            raise ValueError("Nominal channel bandwidth must be positive (Hz).")
        if self.rb_bandwidth_hz <= 0.0:
            raise ValueError("RB bandwidth must be positive (Hz).")
        if not self.active_rb_choices or any(rb < 1 for rb in self.active_rb_choices):
            raise ValueError("Active RB choices must be positive integers.")
        expected_max_bw = max(self.active_rb_choices) * self.rb_bandwidth_hz
        if abs(self.max_active_bandwidth_hz - expected_max_bw) > 1e-6:
            raise ValueError(
                "max_active_bandwidth_hz must equal max(active_rb_choices) * rb_bandwidth_hz."
            )
        if self.max_active_bandwidth_hz > self.nominal_channel_bandwidth_hz:
            raise ValueError("max_active_bandwidth_hz cannot exceed nominal_channel_bandwidth_hz.")
        if self.feeder_loss_db < 0.0 or self.body_loss_db < 0.0 or self.rx_noise_figure_db < 0.0:
            raise ValueError("Losses and noise figure must be non-negative (dB).")
        if self.distance_min_km <= 0.0 or self.distance_max_km < self.distance_min_km:
            raise ValueError("Distance range must satisfy 0 < distance_min_km <= distance_max_km.")
        if not (0.0 < self.ber_target < 0.5):
            raise ValueError("ber_target must be in (0, 0.5).")
        if not (0.0 < self.outage_target < 1.0):
            raise ValueError("outage_target must be in (0, 1).")
        if not self.modulations or any(m not in MODULATION_ORDERS for m in self.modulations):
            raise ValueError(f"Unsupported modulation in {self.modulations}.")
        if self.quick_n_bits < 1 or self.research_n_bits < 1:
            raise ValueError("Monte Carlo bit budgets must be positive.")


DEFAULT_CONFIG = SimulationConfig()
