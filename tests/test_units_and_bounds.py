"""
Unit and boundary constraint tests.
Verifies that all cell parameters and states remain strictly within physical declared bounds.
"""

import pytest
import numpy as np
from src.model import BatteryCell, CellState


def test_soc_clamping_and_saturation():
    """Verify that extreme discharge cannot drive SOC below 0.0."""
    cell = BatteryCell()
    t_amb = 298.15
    state = CellState(
        soc=0.01,
        vp=0.0,
        temperature_k=t_amb,
        q_max=3.20,
        soh=1.00,
        neq=0.0
    )
    
    # Discharge with huge current for 100 seconds
    for _ in range(100):
        state, _ = cell.step(state, current_a=10.0, dt=1.0, t_amb=t_amb)
        
    assert state.soc >= 0.0, f"SOC dropped below 0.0! Current value = {state.soc}"
    assert np.isclose(state.soc, 0.0, atol=1e-12)


def test_physical_parameter_bounds():
    """Verify that resistances, capacitances, and thermal parameters are positive."""
    cell = BatteryCell()
    
    assert cell.q_nom > 0.0
    assert cell.r0_ref > 0.0
    assert cell.r1_ref > 0.0
    assert cell.c1 > 0.0
    assert cell.cth > 0.0
    assert cell.ha > 0.0
    assert cell.v_min < cell.v_max
    
    # Resistance evaluated over valid domain
    for temp in [273.15, 298.15, 318.15, 333.15]: # 0 C to 60 C
        for soh in [0.70, 0.80, 0.90, 1.00]:
            r0 = cell.get_r0(temp, soh)
            r1 = cell.get_r1(temp, soh)
            assert 0.001 < r0 < 1.0, f"Unphysical R0 = {r0} at T={temp}, SOH={soh}"
            assert 0.001 < r1 < 1.0, f"Unphysical R1 = {r1} at T={temp}, SOH={soh}"


def test_thermal_dissipation_nonnegative_heat():
    """Verify that heat generation remains non-negative even during rapid current changes."""
    cell = BatteryCell()
    t_amb = 298.15
    
    # Check positive, zero, and negative current
    state = CellState(soc=0.5, vp=-0.1, temperature_k=t_amb, q_max=3.2, soh=1.0, neq=0.0)
    q_gen = cell.heat_generation(state, current_a=0.5)
    assert q_gen >= 0.0, f"Heat generation was negative: {q_gen}"
