"""
Unit tests for state estimators: Coulomb Counter and Extended Kalman Filter (EKF).
Verifies covariance symmetry, positive definiteness, and filter convergence.
"""

import pytest
import numpy as np
from src.ocv import OCVModel
from src.model import BatteryCell, CellState
from src.estimators import CoulombCounter, ExtendedKalmanFilter


def test_ekf_covariance_positive_semidefinite():
    """Test 5: EKF covariance P must remain symmetric and positive semidefinite throughout simulation."""
    ocv = OCVModel()
    ekf = ExtendedKalmanFilter(ocv_model=ocv, soc_init=0.65)

    # Simulate 500 arbitrary measurement steps
    np.random.seed(42)
    current_meas = 1.60
    
    for _ in range(500):
        # Synthetic noisy voltage around 3.8 V
        vt_meas = 3.80 + np.random.normal(0, 0.005)
        ekf.step(vt_meas=vt_meas, current_meas_a=current_meas, dt=1.0)

        # Check symmetry: P == P^T
        assert np.allclose(ekf.P, ekf.P.T, atol=1e-12), "Covariance matrix lost symmetry!"

        # Check positive semi-definiteness via eigenvalues: lambda_i >= 0
        eigenvals = np.linalg.eigvals(ekf.P)
        assert np.all(eigenvals >= -1e-12), f"Covariance has negative eigenvalues: {eigenvals}"


def test_ekf_converges_from_incorrect_initial_soc():
    """Verify that EKF corrects an initial -15% SOC error (0.65 vs 0.80 true)."""
    cell = BatteryCell()
    ocv = OCVModel()
    t_amb = 298.15
    
    # Ground truth cell initialized at SOC = 0.80
    true_state = CellState(soc=0.80, vp=0.0, temperature_k=t_amb, q_max=3.20, soh=1.00, neq=0.0)
    
    # EKF initialized with wrong guess SOC = 0.65
    ekf = ExtendedKalmanFilter(ocv_model=ocv, soc_init=0.65)
    
    # Coulomb counter also initialized at 0.65
    cc = CoulombCounter(q_assumed=3.20, soc_init=0.65)
    
    current_a = 1.60 # 0.5C discharge
    dt = 1.0
    
    for step_idx in range(600): # 10 minutes
        true_state, metrics = cell.step(true_state, current_a=current_a, dt=dt, t_amb=t_amb)
        vt_true = metrics["vt"]
        
        # Step estimators
        ekf.step(vt_meas=vt_true, current_meas_a=current_a, dt=dt)
        cc.step(current_meas_a=current_a, dt=dt)
        
    # After 10 minutes (600 s), EKF error must be drastically lower than initial 0.15 error
    ekf_error = abs(ekf.soc - true_state.soc)
    cc_error = abs(cc.soc - true_state.soc)
    
    assert ekf_error < 0.02, f"EKF failed to converge within 2% SOC error! Final EKF error = {ekf_error}"
    assert cc_error >= 0.14, f"Coulomb counting was expected to remain offset, got {cc_error}"
    assert ekf_error < cc_error, "EKF did not outperform open-loop Coulomb counting!"
