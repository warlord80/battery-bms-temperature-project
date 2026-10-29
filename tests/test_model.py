"""
Unit tests for the 1-RC Thévenin electrothermal model and OCV curve.
Verifies conservation laws, decay kinetics, and physical properties.
"""

import pytest
import numpy as np
from src.ocv import OCVModel
from src.model import BatteryCell, CellState


def test_ocv_monotonicity():
    """Test 4: OCV must be strictly monotonic across the entire SOC range [0, 1]."""
    ocv = OCVModel()
    assert ocv.is_monotonic(n_eval=2000), "OCV curve is not strictly monotonic!"
    
    # Check boundaries
    assert np.isclose(ocv.evaluate(0.0), 2.50, atol=1e-3)
    assert np.isclose(ocv.evaluate(1.0), 4.20, atol=1e-3)
    
    # Check derivatives are positive everywhere
    z_eval = np.linspace(0.01, 0.99, 100)
    derivs = ocv.derivative(z_eval)
    assert np.all(derivs > 0), "OCV derivative dOCV/dz must be strictly positive!"


def test_zero_current_relaxation():
    """Test 1: At zero current, SOC remains constant and vp decays exponentially to zero."""
    cell = BatteryCell()
    initial_vp = 0.050 # 50 mV polarization
    initial_soc = 0.80
    t_amb = 298.15
    
    state = CellState(
        soc=initial_soc,
        vp=initial_vp,
        temperature_k=t_amb,
        q_max=3.20,
        soh=1.00,
        neq=0.0
    )
    
    dt = 1.0
    tau1 = cell.r1_ref * cell.c1 # 0.025 * 2400 = 60 seconds
    
    # Step forward 5 time constants (300 seconds)
    for _ in range(300):
        state, metrics = cell.step(state, current_a=0.0, dt=dt, t_amb=t_amb)
        
    assert np.isclose(state.soc, initial_soc, atol=1e-12), "SOC changed during zero-current rest!"
    assert state.vp < 0.001, f"vp did not decay towards zero! Remaining vp = {state.vp}"
    assert np.isclose(state.vp, initial_vp * np.exp(-300.0 / tau1), atol=1e-5)


def test_constant_discharge_analytical_rate():
    """Test 2: At constant discharge before saturation, SOC matches the analytical rate exactly."""
    cell = BatteryCell()
    initial_soc = 0.80
    current_a = 1.60 # 0.5C discharge
    dt = 1.0
    steps = 1800 # 30 minutes
    t_amb = 298.15
    
    state = CellState(
        soc=initial_soc,
        vp=0.0,
        temperature_k=t_amb,
        q_max=3.20,
        soh=1.00,
        neq=0.0
    )
    
    for _ in range(steps):
        state, _ = cell.step(state, current_a=current_a, dt=dt, t_amb=t_amb)
        
    # Analytical expected delta SOC: delta_soc = -(1.60 * 1800) / (3600 * 3.20) = -0.25
    expected_soc = initial_soc - (current_a * (steps * dt)) / (3600.0 * 3.20)
    assert np.isclose(state.soc, expected_soc, atol=1e-9), (
        f"Simulated SOC ({state.soc}) differs from analytical prediction ({expected_soc})"
    )


def test_arrhenius_and_aging_resistance_trends():
    """Verify that R0 decreases with elevated temperature and increases with degradation."""
    cell = BatteryCell()
    
    # Temperature effect: higher T -> lower resistance (Arrhenius semiconductor/electrolyte behavior)
    r0_25c = cell.get_r0(temperature_k=298.15, soh=1.0)
    r0_35c = cell.get_r0(temperature_k=308.15, soh=1.0)
    r0_45c = cell.get_r0(temperature_k=318.15, soh=1.0)
    
    assert r0_25c > r0_35c > r0_45c, "R0 must decrease with increasing temperature!"
    
    # Aging effect: lower SOH -> higher resistance
    r0_soh100 = cell.get_r0(temperature_k=298.15, soh=1.00)
    r0_soh90 = cell.get_r0(temperature_k=298.15, soh=0.90)
    r0_soh80 = cell.get_r0(temperature_k=298.15, soh=0.80)
    
    assert r0_soh80 > r0_soh90 > r0_soh100, "R0 must increase as SOH degrades!"
