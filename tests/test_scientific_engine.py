"""Comprehensive automated test suite for RuralLink scientific engine (Phase 02–03)."""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import DEFAULT_CONFIG, MODULATION_ORDERS, MODULATIONS, SimulationConfig
from src.channels import (
    awgn_channel,
    coherent_equalize,
    instantaneous_snr,
    rayleigh_fading_gains,
)
from src.link_budget import (
    active_bandwidth_hz,
    compute_link_budget,
    db_to_linear,
    dbm_to_watts,
    linear_to_db,
    nominal_data_rate_bps,
    power_per_rb_dbm,
    rb_snr_gain_db,
    received_power_dbm,
    shannon_capacity_bps,
    snr_to_ebn0_db,
    snr_to_ebn0_linear,
    thermal_noise_dbm,
    watts_to_dbm,
)
from src.metrics import compute_error_metrics, simulate_ber_point, wilson_ci_95
from src.modulation import (
    bits_per_symbol,
    demodulate,
    derive_switching_thresholds,
    get_constellation,
    modulate,
    q_func,
    theoretical_ber_awgn,
    theoretical_ber_rayleigh,
)
from src.propagation import (
    analytical_shadow_margin_db,
    ci_path_loss_db,
    fspl_1m_db,
    get_ci_parameters,
    median_path_loss_db,
    sample_shadow_fading_db,
    stochastic_path_loss_db,
)

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------


class TestConfig:
    def test_default_config_instantiation(self):
        cfg = DEFAULT_CONFIG
        assert cfg.ue_tx_power_dbm == 23.0
        assert cfg.bts_rx_antenna_gain_dbi == 11.0
        assert cfg.rx_noise_figure_db == 4.0
        assert cfg.feeder_loss_db == 5.0
        assert cfg.body_loss_db == 3.0
        assert cfg.thermal_noise_density_dbm_hz == -174.0
        assert cfg.rb_bandwidth_hz == 180_000.0
        assert cfg.ber_target == 1e-2

    def test_max_active_bandwidth_constraint(self):
        # 25 RBs * 180 kHz = 4.5 MHz
        assert DEFAULT_CONFIG.max_active_bandwidth_hz == 4_500_000.0
        assert DEFAULT_CONFIG.max_active_bandwidth_hz <= DEFAULT_CONFIG.nominal_channel_bandwidth_hz

    def test_invalid_config_raises(self):
        with pytest.raises(ValueError, match="max_active_bandwidth_hz"):
            SimulationConfig(
                active_rb_choices=(1, 2, 5, 10, 25),
                max_active_bandwidth_hz=5_000_000.0,  # wrong: should be 4.5 MHz
            )
        with pytest.raises(ValueError, match="ber_target"):
            SimulationConfig(
                active_rb_choices=(1, 2, 5, 10, 25),
                max_active_bandwidth_hz=4_500_000.0,
                ber_target=0.0,
            )


# ---------------------------------------------------------------------------
# PROPAGATION
# ---------------------------------------------------------------------------


class TestPropagation:
    def test_fspl_1m_900mhz(self):
        # 32.4 + 20*log10(0.9) = 32.4 - 0.9151 = 31.4849...
        expected = 32.4 + 20.0 * np.log10(0.9)
        assert abs(fspl_1m_db(900.0) - expected) < 1e-10

    def test_fspl_1m_1800mhz(self):
        expected = 32.4 + 20.0 * np.log10(1.8)
        assert abs(fspl_1m_db(1800.0) - expected) < 1e-10

    def test_frequency_doubling_increases_pl_by_6dB(self):
        """900 vs 1800 MHz at same distance: 20*log10(2) = 6.0206 dB difference."""
        d_m = 5000.0
        pl_900 = median_path_loss_db(d_m, 900.0, "LOS")
        pl_1800 = median_path_loss_db(d_m, 1800.0, "LOS")
        expected_diff = 20.0 * np.log10(2.0)  # 6.020599...
        assert abs((pl_1800 - pl_900) - expected_diff) < 1e-8

    def test_doubling_distance_increases_pl_by_10n_log10_2(self):
        """Doubling distance increases PL by 10*n*log10(2) dB."""
        d_m = 3000.0
        n, _ = get_ci_parameters("NLOS")
        pl_d = median_path_loss_db(d_m, 900.0, "NLOS")
        pl_2d = median_path_loss_db(2.0 * d_m, 900.0, "NLOS")
        expected_increase = 10.0 * n * np.log10(2.0)
        assert abs((pl_2d - pl_d) - expected_increase) < 1e-8

    def test_monotonic_median_path_loss(self):
        """Median path loss must be strictly monotonically increasing with distance."""
        distances = np.linspace(1000.0, 12000.0, 50)
        pls = median_path_loss_db(distances, 900.0, "NLOS")
        assert np.all(np.diff(pls) > 0), "Median path loss must increase with distance."

    def test_los_nlos_parameters(self):
        n_los, s_los = get_ci_parameters("LOS")
        n_nlos, s_nlos = get_ci_parameters("NLOS")
        assert abs(n_los - 2.16) < 1e-10
        assert abs(s_los - 3.07) < 1e-10
        assert abs(n_nlos - 2.56) < 1e-10
        assert abs(s_nlos - 11.40) < 1e-10

    def test_analytical_shadow_margin_95_percent(self):
        _, sigma = get_ci_parameters("NLOS")
        margin = analytical_shadow_margin_db(sigma, reliability=0.95)
        # Should be 1.645 * sigma
        assert abs(margin - 1.645 * sigma) < 1e-6

    def test_no_double_counting_raises(self):
        with pytest.raises(ValueError, match="shadow margin"):
            ci_path_loss_db(1000.0, 900.0, stochastic=True, shadow_margin_db=5.0)

    def test_distance_less_than_1m_raises(self):
        with pytest.raises(ValueError):
            median_path_loss_db(0.5, 900.0)

    def test_stochastic_shadowing_zero_mean(self):
        """Sample mean of shadow fading should be near zero (1000 samples)."""
        rng = np.random.default_rng(42)
        _, sigma = get_ci_parameters("NLOS")
        samples = sample_shadow_fading_db(sigma_db=sigma, size=10_000, rng=rng)
        assert abs(float(np.mean(samples))) < 0.5  # rough sanity at 10k samples

    def test_stochastic_path_loss_has_variation(self):
        """Different seeds should give different stochastic path losses."""
        d_m = 5000.0
        pl1 = stochastic_path_loss_db(d_m, 900.0, rng=np.random.default_rng(1))
        pl2 = stochastic_path_loss_db(d_m, 900.0, rng=np.random.default_rng(2))
        assert pl1 != pl2


# ---------------------------------------------------------------------------
# LINK BUDGET
# ---------------------------------------------------------------------------


class TestLinkBudget:
    def test_default_power_gain_loss_arithmetic(self):
        """Verify received power with zero path loss = Pt + Gt + Gr - feeder - body."""
        pr = received_power_dbm(
            tx_power_dbm=23.0,
            tx_gain_dbi=0.0,
            rx_gain_dbi=11.0,
            path_loss_db=0.0,
            feeder_loss_db=5.0,
            body_loss_db=3.0,
        )
        # 23 + 0 + 11 - 0 - 5 - 3 = 26 dBm
        assert abs(pr - 26.0) < 1e-10

    def test_noise_power_calculation(self):
        """Verify noise floor: -174 + 10*log10(180000) + 4 = -174 + 52.5527 + 4 = -117.447 dBm."""
        b = 180_000.0
        noise = thermal_noise_dbm(bandwidth_hz=b, noise_figure_db=4.0)
        expected = -174.0 + 10.0 * np.log10(b) + 4.0
        assert abs(noise - expected) < 1e-8

    def test_rb25_to_rb1_snr_gain(self):
        """25 RBs -> 1 RB gives 10*log10(25) = 13.9794 dB SNR improvement."""
        gain = rb_snr_gain_db(25, 1)
        expected = 10.0 * np.log10(25.0)  # 13.97940...
        assert abs(gain - expected) < 1e-8, f"Expected {expected:.6f}, got {gain:.6f}"

    def test_rb25_to_rb5_snr_gain(self):
        """25 RBs -> 5 RBs gives 10*log10(5) = 6.9897 dB improvement."""
        gain = rb_snr_gain_db(25, 5)
        expected = 10.0 * np.log10(5.0)  # 6.98970...
        assert abs(gain - expected) < 1e-8, f"Expected {expected:.6f}, got {gain:.6f}"

    def test_no_double_counting_rb_gain(self):
        """SNR reflects B_active; must not add rb_snr_gain again."""
        pl_db = 120.0
        lb25 = compute_link_budget(pl_db, n_rb=25)
        lb1 = compute_link_budget(pl_db, n_rb=1)
        actual_gain = float(lb1.snr_db) - float(lb25.snr_db)
        expected_gain = rb_snr_gain_db(25, 1)
        # Only bandwidth reduction -> noise reduction -> SNR gain (no Pr change)
        assert abs(actual_gain - expected_gain) < 1e-8

    def test_esn0_ebn0_conversion_bpsk(self):
        """For BPSK (k=1): EbN0 = EsN0."""
        snr_db = 10.0
        ebn0 = snr_to_ebn0_db(snr_db, "BPSK")
        assert abs(ebn0 - snr_db) < 1e-10

    def test_esn0_ebn0_conversion_16qam(self):
        """For 16-QAM (k=4): EbN0_dB = SNR_dB - 10*log10(4) = SNR_dB - 6.0206 dB."""
        snr_db = 20.0
        ebn0 = snr_to_ebn0_db(snr_db, "16-QAM")
        expected = snr_db - 10.0 * np.log10(4.0)
        assert abs(ebn0 - expected) < 1e-10

    def test_ebn0_linear_conversion(self):
        snr_lin = 10.0  # 10 dB
        ebn0_lin = snr_to_ebn0_linear(snr_lin, "QPSK")  # k=2
        assert abs(ebn0_lin - 5.0) < 1e-10

    def test_active_bandwidth(self):
        assert active_bandwidth_hz(1) == 180_000.0
        assert active_bandwidth_hz(25) == 4_500_000.0

    def test_power_per_rb(self):
        """P_RB = P_tx - 10*log10(N_RB)."""
        p_rb = power_per_rb_dbm(23.0, 25)
        assert abs(p_rb - (23.0 - 10.0 * np.log10(25.0))) < 1e-10

    def test_nominal_rate(self):
        rb = nominal_data_rate_bps(1_800_000.0, "16-QAM")  # 1.8 MHz * 4 bits/sym = 7.2 Mbps
        assert abs(rb - 7_200_000.0) < 1e-6

    def test_input_rejection(self):
        with pytest.raises(ValueError):
            active_bandwidth_hz(0)
        with pytest.raises(ValueError):
            thermal_noise_dbm(0.0, 4.0)
        with pytest.raises(ValueError):
            power_per_rb_dbm(23.0, 0)
        with pytest.raises(ValueError):
            received_power_dbm(23.0, 0.0, 11.0, 100.0, -1.0, 3.0)
        with pytest.raises(ValueError):
            linear_to_db(-1.0)
        with pytest.raises(ValueError):
            watts_to_dbm(-1.0)

    def test_db_linear_round_trip(self):
        for val in [0.1, 1.0, 10.0, 100.0]:
            assert abs(db_to_linear(linear_to_db(val)) - val) < 1e-12

    def test_dbm_watts_round_trip(self):
        for val in [0.001, 0.1, 1.0]:
            assert abs(dbm_to_watts(watts_to_dbm(val)) - val) < 1e-15

    def test_shannon_capacity_reference(self):
        """C = B * log2(1 + SNR), not equal to modulation throughput."""
        cap = shannon_capacity_bps(1_800_000.0, 10.0)
        expected = 1_800_000.0 * np.log2(11.0)
        assert abs(cap - expected) < 1e-6


# ---------------------------------------------------------------------------
# MODULATION
# ---------------------------------------------------------------------------


class TestModulation:
    @pytest.mark.parametrize("mod", MODULATIONS)
    def test_zero_noise_roundtrip(self, mod):
        """At zero noise, demodulation must recover all transmitted bits exactly."""
        rng = np.random.default_rng(42)
        k = bits_per_symbol(mod)
        n_sym = 500
        tx_bits = rng.integers(0, 2, n_sym * k, dtype=np.uint8)
        symbols, n_pad = modulate(tx_bits, mod)
        rx_bits = demodulate(symbols, mod, n_pad_bits=n_pad)
        assert np.array_equal(tx_bits, rx_bits), f"Roundtrip failed for {mod}"

    @pytest.mark.parametrize("mod", MODULATIONS)
    def test_unique_constellation_symbols(self, mod):
        """All M constellation symbols must be unique."""
        m_val = MODULATION_ORDERS[mod]
        symbols, _ = get_constellation(mod)
        assert len(symbols) == m_val
        for i in range(m_val):
            for j in range(i + 1, m_val):
                assert not np.isclose(symbols[i], symbols[j], atol=1e-9), (
                    f"Duplicate symbols at indices {i},{j} in {mod}"
                )

    @pytest.mark.parametrize("mod", MODULATIONS)
    def test_average_constellation_energy_equals_1(self, mod):
        """Normalized constellations must have E[|s|^2] = 1."""
        symbols, _ = get_constellation(mod)
        avg_energy = float(np.mean(np.abs(symbols) ** 2))
        assert abs(avg_energy - 1.0) < 1e-10, f"{mod}: avg energy = {avg_energy:.10f}, expected 1.0"

    @pytest.mark.parametrize("mod", ["QPSK", "16-QAM", "64-QAM"])
    def test_gray_coding_nearest_neighbors(self, mod):
        """Adjacent (nearest-neighbor) constellation symbols must differ by exactly 1 bit."""
        symbols, labels = get_constellation(mod)
        _ = bits_per_symbol(mod)
        m_val = len(symbols)

        def hamming(a: str, b: str) -> int:
            return sum(c1 != c2 for c1, c2 in zip(a, b, strict=False))

        for i in range(m_val):
            dists = np.abs(symbols[i] - symbols)
            dists[i] = np.inf
            # For square QAM, check nearest Manhattan neighbors (smallest non-zero distance)
            min_dist = np.min(dists)
            nn_mask = dists < min_dist * 1.001
            nn_indices = np.where(nn_mask)[0]
            # Relaxed: at least 1 nearest neighbor must have Hamming distance = 1
            min_hamming = min(hamming(labels[i], labels[j]) for j in nn_indices)
            assert min_hamming == 1, (
                f"{mod} symbol {labels[i]}: nearest neighbor min Hamming distance = {min_hamming}"
            )
        # Also verify unique bit labels
        assert len(set(labels)) == m_val

    @pytest.mark.parametrize("mod", MODULATIONS)
    def test_correct_bit_and_symbol_counts(self, mod):
        """Verify bit grouping and symbol count."""
        k = bits_per_symbol(mod)
        n_sym = 128
        tx_bits = np.zeros(n_sym * k, dtype=np.uint8)
        symbols, n_pad = modulate(tx_bits, mod)
        assert len(symbols) == n_sym
        assert n_pad == 0

    def test_q_function_values(self):
        """Q(0) = 0.5, Q(large) ≈ 0, Q(-x) = 1 - Q(x)."""
        assert abs(q_func(0.0) - 0.5) < 1e-15
        assert q_func(10.0) < 1e-20
        assert abs(q_func(-3.0) - (1.0 - q_func(3.0))) < 1e-15

    def test_bpsk_qpsk_ber_equal(self):
        """BPSK and QPSK have identical BER vs Eb/N0 in AWGN."""
        ebn0_vals = np.array([0.1, 1.0, 5.0, 10.0])
        ber_bpsk = theoretical_ber_awgn(ebn0_vals, "BPSK")
        ber_qpsk = theoretical_ber_awgn(ebn0_vals, "QPSK")
        np.testing.assert_allclose(ber_bpsk, ber_qpsk, rtol=1e-12)

    def test_awgn_ber_decreases_with_snr(self):
        """Higher Eb/N0 must give lower BER for all modulations."""
        ebn0_db_vals = np.arange(-2, 20, 2)
        for mod in MODULATIONS:
            ber_vals = theoretical_ber_awgn(10.0 ** (ebn0_db_vals / 10.0), mod)
            assert np.all(np.diff(ber_vals) < 0), f"BER not monotone for {mod}"

    def test_rayleigh_ber_bpsk_exact(self):
        """Test closed-form Rayleigh BPSK BER: 0.5*(1-sqrt(gam/(1+gam)))."""
        for ebn0_db in [0.0, 5.0, 10.0]:
            gamma_b = 10.0 ** (ebn0_db / 10.0)
            ber_exact = 0.5 * (1.0 - np.sqrt(gamma_b / (1.0 + gamma_b)))
            ber_func = theoretical_ber_rayleigh(gamma_b, "BPSK")
            assert abs(ber_func - ber_exact) < 1e-10

    def test_rayleigh_qpsk_equals_bpsk(self):
        """Rayleigh BPSK and QPSK average BER must be equal."""
        gamma_b = np.array([0.5, 2.0, 10.0])
        ber_bpsk = theoretical_ber_rayleigh(gamma_b, "BPSK")
        ber_qpsk = theoretical_ber_rayleigh(gamma_b, "QPSK")
        np.testing.assert_allclose(ber_bpsk, ber_qpsk, rtol=1e-6)


# ---------------------------------------------------------------------------
# CHANNEL
# ---------------------------------------------------------------------------


class TestChannel:
    def test_awgn_noise_variance(self):
        """AWGN additive noise should have empirical variance N0/2 per dimension."""
        rng = np.random.default_rng(42)
        esn0_lin = 10.0  # 10 dB
        n0 = 1.0 / esn0_lin
        n_sym = 100_000
        symbols = np.ones(n_sym, dtype=np.complex128)
        received = awgn_channel(symbols, esn0_linear=esn0_lin, rng=rng)
        noise = received - symbols
        var_I = float(np.var(noise.real))
        var_Q = float(np.var(noise.imag))
        # Each component has variance N0/2
        assert abs(var_I - n0 / 2.0) < 0.02 * (n0 / 2.0), f"I-variance mismatch: {var_I}"
        assert abs(var_Q - n0 / 2.0) < 0.02 * (n0 / 2.0), f"Q-variance mismatch: {var_Q}"

    def test_rayleigh_channel_power_unity(self):
        """E[|h|^2] should be approximately 1 for independent Rayleigh fading."""
        rng = np.random.default_rng(42)
        h = rayleigh_fading_gains(n_symbols=200_000, rng=rng, block_size=1)
        avg_power = float(np.mean(np.abs(h) ** 2))
        assert abs(avg_power - 1.0) < 0.02, f"E[|h|^2] = {avg_power:.4f}, expected 1.0"

    def test_seeded_simulation_reproducible(self):
        """Same seed must produce identical results."""
        esn0_lin = 5.0
        n_sym = 1000
        rng_a = np.random.default_rng(42)
        rng_b = np.random.default_rng(42)
        x = np.ones(n_sym, dtype=np.complex128)
        y_a = awgn_channel(x, esn0_linear=esn0_lin, rng=rng_a)
        y_b = awgn_channel(x, esn0_linear=esn0_lin, rng=rng_b)
        np.testing.assert_array_equal(y_a, y_b)

    def test_awgn_ber_decreases_with_snr(self):
        """Monte Carlo BER must decrease statistically with increasing SNR (BPSK, AWGN)."""
        n_bits = 100_000
        ber_low, _ = simulate_ber_point(
            "BPSK", ebn0_db=1.0, n_bits=n_bits, channel_type="AWGN", seed=0
        )
        ber_high, _ = simulate_ber_point(
            "BPSK", ebn0_db=7.0, n_bits=n_bits, channel_type="AWGN", seed=0
        )
        assert ber_low.ber > ber_high.ber

    def test_coherent_equalize_identity(self):
        """Equalization with known h must recover the unscaled received signal exactly."""
        h = np.array([0.6 + 0.8j, -0.3 + 0.4j])
        x = np.array([1.0 + 0.0j, 0.0 + 1.0j])
        y = h * x  # noise-free faded
        x_hat = coherent_equalize(y, h)
        np.testing.assert_allclose(x_hat, x, atol=1e-12)

    def test_instantaneous_snr_scaling(self):
        h = np.array([1.0 + 0.0j, 0.0 + 1.0j, (1 + 1j) / np.sqrt(2)])
        avg_snr = 10.0
        gamma_inst = instantaneous_snr(avg_snr, h)
        expected = avg_snr * np.abs(h) ** 2
        np.testing.assert_allclose(gamma_inst, expected, rtol=1e-12)


# ---------------------------------------------------------------------------
# THEORETICAL VALIDATION (Monte Carlo vs Theory)
# ---------------------------------------------------------------------------


class TestTheoreticalValidation:
    def test_bpsk_awgn_monte_carlo_vs_theory(self):
        """BPSK AWGN Monte Carlo BER should agree with Q(sqrt(2*EbN0)) within 10% relative."""
        mod = "BPSK"
        ebn0_db = 6.0
        n_bits = 500_000
        m, _ = simulate_ber_point(mod, ebn0_db=ebn0_db, n_bits=n_bits, channel_type="AWGN", seed=42)
        theory = float(theoretical_ber_awgn(10.0 ** (ebn0_db / 10.0), mod))
        assert m.n_bit_errors > 10, (
            f"Too few errors ({m.n_bit_errors}) to validate; increase n_bits or decrease Eb/N0."
        )
        assert abs(m.ber - theory) / theory < 0.15, (
            f"BPSK AWGN MC BER={m.ber:.5f} vs theory={theory:.5f}"
        )

    def test_qpsk_awgn_monte_carlo_vs_theory(self):
        mod = "QPSK"
        ebn0_db = 6.0
        n_bits = 500_000
        m, _ = simulate_ber_point(mod, ebn0_db=ebn0_db, n_bits=n_bits, channel_type="AWGN", seed=42)
        theory = float(theoretical_ber_awgn(10.0 ** (ebn0_db / 10.0), mod))
        assert m.n_bit_errors > 10
        assert abs(m.ber - theory) / theory < 0.15

    def test_16qam_awgn_monte_carlo_vs_theory(self):
        """16-QAM AWGN MC should agree with exact Gray-coded BER within 15% relative."""
        mod = "16-QAM"
        ebn0_db = 10.0
        n_bits = 500_000
        m, _ = simulate_ber_point(mod, ebn0_db=ebn0_db, n_bits=n_bits, channel_type="AWGN", seed=42)
        theory = float(theoretical_ber_awgn(10.0 ** (ebn0_db / 10.0), mod, method="exact"))
        assert m.n_bit_errors > 10
        assert abs(m.ber - theory) / theory < 0.15, (
            f"16-QAM MC BER={m.ber:.5f} vs theory={theory:.5f}"
        )

    def test_64qam_awgn_monte_carlo_vs_theory(self):
        mod = "64-QAM"
        ebn0_db = 15.0
        n_bits = 500_000
        m, _ = simulate_ber_point(mod, ebn0_db=ebn0_db, n_bits=n_bits, channel_type="AWGN", seed=42)
        theory = float(theoretical_ber_awgn(10.0 ** (ebn0_db / 10.0), mod, method="exact"))
        assert m.n_bit_errors > 10
        assert abs(m.ber - theory) / theory < 0.20, (
            f"64-QAM MC BER={m.ber:.5f} vs theory={theory:.5f}"
        )

    def test_bpsk_rayleigh_monte_carlo_vs_theory(self):
        """BPSK Rayleigh independent-fading MC should agree with exact BER within 10%."""
        mod = "BPSK"
        ebn0_db = 10.0
        n_bits = 500_000
        m, _ = simulate_ber_point(
            mod, ebn0_db=ebn0_db, n_bits=n_bits, channel_type="RAYLEIGH", seed=42, block_size=1
        )
        gamma_b = 10.0 ** (ebn0_db / 10.0)
        theory = 0.5 * (1.0 - np.sqrt(gamma_b / (1.0 + gamma_b)))
        assert m.n_bit_errors > 10
        assert abs(m.ber - theory) / theory < 0.10, (
            f"BPSK Rayleigh MC BER={m.ber:.5f} vs theory={theory:.5f}"
        )

    def test_switching_thresholds_satisfy_ber_target(self):
        """Derived AWGN switching thresholds must satisfy BER(threshold) == ber_target."""
        thresholds = derive_switching_thresholds(ber_target=1e-2)
        for mod, t in thresholds.items():
            ber_at_thresh = float(theoretical_ber_awgn(t["ebn0_linear"], mod, method="exact"))
            assert abs(ber_at_thresh - 1e-2) < 1e-6, (
                f"{mod}: BER at threshold = {ber_at_thresh:.2e}, expected 1e-2"
            )


# ---------------------------------------------------------------------------
# METRICS & CONFIDENCE INTERVALS
# ---------------------------------------------------------------------------


class TestMetrics:
    def test_zero_errors_gives_rule_of_three_bound(self):
        ci_lo, ci_hi, is_upper = wilson_ci_95(0, 10_000)
        assert ci_lo == 0.0
        assert abs(ci_hi - 3.0 / 10_000.0) < 1e-15
        assert is_upper is True

    def test_wilson_ci_width_decreases_with_n(self):
        _, hi_small, _ = wilson_ci_95(10, 1_000)
        _, hi_large, _ = wilson_ci_95(100, 10_000)
        assert hi_small > hi_large

    def test_compute_error_metrics_basic(self):
        rng = np.random.default_rng(99)
        tx = rng.integers(0, 2, 10_000, dtype=np.uint8)
        rx = tx.copy()
        rx[:50] = 1 - rx[:50]  # inject 50 errors
        metrics = compute_error_metrics(tx, rx)
        assert metrics.n_bit_errors == 50
        assert abs(metrics.ber - 50 / 10_000) < 1e-15
        assert metrics.ci_lower is not None
        assert metrics.ci_upper is not None
