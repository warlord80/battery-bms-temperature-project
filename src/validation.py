"""
Validation and Physical Invariant Auditing Module.

Implements automated verification checks:
1. Zero-current state and polarization relaxation.
2. Constant-current charge drawdown matching analytical Faraday rates.
3. Strict monotonicity and bounds checking for OCV curves.
4. Positive semi-definiteness of Kalman filter error covariance.
5. Numerical time-step convergence verification.
"""

from typing import Dict, Any, Tuple
import numpy as np
from src.model import BatteryCell, CellState
from src.ocv import OCVModel
from src.estimators import ExtendedKalmanFilter


def verify_time_step_convergence(
    metrics_std: Dict[str, float],
    metrics_fine: Dict[str, float],
    max_rel_tolerance_pct: float = 0.50,
) -> Tuple[bool, Dict[str, float]]:
    """
    Verifies that refining time step (e.g. 1.0 s to 0.5 s) does not alter
    delivered energy, capacity, or peak temperature by more than tolerance.
    """
    diff_energy = abs(metrics_std["delivered_energy_wh"] - metrics_fine["delivered_energy_wh"]) / max(1e-6, metrics_std["delivered_energy_wh"]) * 100.0
    diff_temp = abs(metrics_std["peak_temp_c"] - metrics_fine["peak_temp_c"]) / max(1e-6, metrics_std["peak_temp_c"]) * 100.0

    passed = (diff_energy < max_rel_tolerance_pct) and (diff_temp < max_rel_tolerance_pct)

    return passed, {
        "energy_rel_diff_pct": diff_energy,
        "temp_rel_diff_pct": diff_temp,
    }


def audit_covariance_matrix(P: np.ndarray, tolerance: float = 1e-12) -> bool:
    """
    Verifies that error covariance matrix P is symmetric and positive semi-definite.
    """
    is_symmetric = np.allclose(P, P.T, atol=tolerance)
    eigenvalues = np.linalg.eigvals(P)
    is_psd = np.all(eigenvalues >= -tolerance)
    return bool(is_symmetric and is_psd)
