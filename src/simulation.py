"""
Simulation Orchestration Module.

Coordinates battery electrothermal dynamics, synthetic sensor noise models,
and simultaneous state estimation (Coulomb Counting and EKF).
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from src.model import BatteryCell, CellState
from src.estimators import CoulombCounter, ExtendedKalmanFilter
from src.metrics import compute_estimation_metrics


def generate_current_profile(
    profile_type: str,
    duration_s: float = 3600.0,
    dt: float = 1.0,
) -> np.ndarray:
    """
    Generate discharge current time series (positive current = discharge).
    """
    n_steps = int(np.round(duration_s / dt))
    time_array = np.arange(n_steps) * dt

    if profile_type == "steady_moderate":
        # Constant 0.5C discharge (1.6 A for 3.2 Ah cell)
        return np.full(n_steps, 1.60, dtype=float)

    elif profile_type == "dynamic_pulse":
        # Dynamic profile with pulse discharge, peak pulses, and rests
        currents = np.zeros(n_steps, dtype=float)
        period = 900.0 # 15-minute repeat block
        for i, t in enumerate(time_array):
            t_mod = t % period
            if t_mod < 240.0:        # 4 min 0.5C pulse
                currents[i] = 1.60
            elif t_mod < 360.0:      # 2 min rest
                currents[i] = 0.0
            elif t_mod < 480.0:      # 2 min 1.0C pulse (3.2 A)
                currents[i] = 3.20
            elif t_mod < 600.0:      # 2 min rest
                currents[i] = 0.0
            elif t_mod < 800.0:      # 3 min 20 s 0.25C pulse (0.8 A)
                currents[i] = 0.80
            else:                    # Rest until next cycle
                currents[i] = 0.0
        return currents

    else:
        raise ValueError(f"Unknown current profile type: {profile_type}")


def run_single_simulation(
    cell: BatteryCell,
    coulomb_counter: CoulombCounter,
    ekf: ExtendedKalmanFilter,
    current_profile: np.ndarray,
    dt: float,
    t_amb_k: float,
    true_init_state: CellState,
    sigma_v: float = 0.005,
    sigma_i: float = 0.020,
    i_bias: float = 0.0,
    random_seed: Optional[int] = None,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Executes a coupled electrothermal simulation with sensor noise and state estimators.
    """
    rng = np.random.default_rng(random_seed)
    n_steps = len(current_profile)

    # Pre-allocate records
    records = []
    current_state = true_init_state

    # Tracking for recovery time to within 2 percentage points (|error| <= 0.02)
    recovery_time_ekf = None
    candidate_recovery_time = None
    recovered_consecutive = 0

    for k in range(n_steps):
        t_curr = k * dt
        i_true = current_profile[k]

        # Generate synthetic sensor observations
        # Disclosed sensor noise and bias
        i_noise = rng.normal(0.0, sigma_i) if sigma_i > 0 else 0.0
        i_meas = i_true + i_bias + i_noise

        # Calculate true terminal voltage before advance
        vt_true = cell.terminal_voltage(current_state, i_true)
        v_noise = rng.normal(0.0, sigma_v) if sigma_v > 0 else 0.0
        vt_meas = vt_true + v_noise

        # Step estimators
        soc_cc = coulomb_counter.step(current_meas_a=i_meas, dt=dt)
        soc_ekf, vp_ekf, innovation = ekf.step(vt_meas=vt_meas, current_meas_a=i_meas, dt=dt)

        # Track errors
        soc_true = current_state.soc
        err_cc = soc_cc - soc_true
        err_ekf = soc_ekf - soc_true

        # Track EKF recovery time
        if recovery_time_ekf is None:
            if abs(err_ekf) <= 0.02:
                if candidate_recovery_time is None:
                    candidate_recovery_time = t_curr
                recovered_consecutive += 1
                if recovered_consecutive >= 5: # Stable for 5 seconds
                    recovery_time_ekf = candidate_recovery_time
            else:
                candidate_recovery_time = None
                recovered_consecutive = 0

        # Record point
        records.append({
            "time_s": t_curr,
            "i_true_a": i_true,
            "i_meas_a": i_meas,
            "vt_true_v": vt_true,
            "vt_meas_v": vt_meas,
            "soc_true": soc_true,
            "soc_cc": soc_cc,
            "soc_ekf": soc_ekf,
            "error_cc": err_cc,
            "error_ekf": err_ekf,
            "vp_true_v": current_state.vp,
            "vp_ekf_v": vp_ekf,
            "temp_cell_k": current_state.temperature_k,
            "temp_cell_c": current_state.temperature_k - 273.15,
            "q_gen_w": cell.heat_generation(current_state, i_true),
        })

        # Advance cell physics
        current_state, _ = cell.step(
            state=current_state,
            current_a=i_true,
            dt=dt,
            t_amb=t_amb_k,
        )

        # Cutoff check: if voltage drops below V_min, stop discharge
        if current_state.soc <= 0.0 or vt_true <= cell.v_min:
            break

    df = pd.DataFrame(records)

    # Compute summary metrics
    # Note: soc error is in percentage points (100 * error)
    soc_rmse_cc = float(np.sqrt(np.mean((df["error_cc"] * 100.0) ** 2)))
    soc_mae_cc = float(np.mean(np.abs(df["error_cc"] * 100.0)))
    soc_rmse_ekf = float(np.sqrt(np.mean((df["error_ekf"] * 100.0) ** 2)))
    soc_mae_ekf = float(np.mean(np.abs(df["error_ekf"] * 100.0)))
    
    final_err_cc = float(df["error_cc"].iloc[-1] * 100.0)
    final_err_ekf = float(df["error_ekf"].iloc[-1] * 100.0)

    # Delivered energy in Watt-hours: sum(Vt * I * dt) / 3600
    delivered_energy_wh = float(np.sum(df["vt_true_v"] * df["i_true_a"] * dt) / 3600.0)
    usable_capacity_ah = float(np.sum(df["i_true_a"] * dt) / 3600.0)
    peak_temp_c = float(df["temp_cell_c"].max())

    metrics = {
        "soc_rmse_cc_pct": soc_rmse_cc,
        "soc_mae_cc_pct": soc_mae_cc,
        "soc_rmse_ekf_pct": soc_rmse_ekf,
        "soc_mae_ekf_pct": soc_mae_ekf,
        "final_error_cc_pct": final_err_cc,
        "final_error_ekf_pct": final_err_ekf,
        "recovery_time_2pct_s": float(recovery_time_ekf) if recovery_time_ekf is not None else float("nan"),
        "delivered_energy_wh": delivered_energy_wh,
        "usable_capacity_ah": usable_capacity_ah,
        "peak_temp_c": peak_temp_c,
        "steps_simulated": len(df),
    }

    return df, metrics
