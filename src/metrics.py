"""
Metrics Evaluation Module.

Computes standard battery performance and state estimation metrics:
- Root Mean Squared Error (RMSE) in percentage points
- Mean Absolute Error (MAE) in percentage points
- Final SOC error in percentage points
- Recovery time to within 2 percentage points of truth
- Delivered energy in Watt-hours
- Usable charge capacity in Ampere-hours
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd


def compute_estimation_metrics(
    time_s: np.ndarray,
    soc_true: np.ndarray,
    soc_est: np.ndarray,
    vt_true_v: np.ndarray,
    i_true_a: np.ndarray,
    temp_cell_c: np.ndarray,
    dt: float,
    threshold_pct: float = 2.0,
) -> Dict[str, float]:
    """
    Computes comprehensive tracking accuracy and energy metrics.
    All SOC errors are reported in percentage points (0 to 100).
    """
    error_pct = (soc_est - soc_true) * 100.0

    rmse = float(np.sqrt(np.mean(error_pct ** 2)))
    mae = float(np.mean(np.abs(error_pct)))
    final_error = float(error_pct[-1])

    # Recovery time tracking (|error| <= threshold_pct)
    recovery_time = None
    consecutive_recovered = 0
    candidate_time = None

    for t, err in zip(time_s, error_pct):
        if abs(err) <= threshold_pct:
            if candidate_time is None:
                candidate_time = t
            consecutive_recovered += 1
            if consecutive_recovered >= 5: # Stable for at least 5 steps
                recovery_time = candidate_time
                break
        else:
            candidate_time = None
            consecutive_recovered = 0

    # Electrical and thermal integration
    delivered_energy_wh = float(np.sum(vt_true_v * i_true_a * dt) / 3600.0)
    usable_capacity_ah = float(np.sum(i_true_a * dt) / 3600.0)
    peak_temp_c = float(np.max(temp_cell_c))

    return {
        "rmse_pct": rmse,
        "mae_pct": mae,
        "final_error_pct": final_error,
        "recovery_time_s": float(recovery_time) if recovery_time is not None else float("nan"),
        "delivered_energy_wh": delivered_energy_wh,
        "usable_capacity_ah": usable_capacity_ah,
        "peak_temp_c": peak_temp_c,
    }
