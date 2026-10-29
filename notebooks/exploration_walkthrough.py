"""
Interactive Exploration Walkthrough for Battery Electrothermal & Estimator Model.

Allows interactive inspection of:
- OCV curve and derivatives
- Temperature and SOH resistance scaling
- Live step-by-step EKF observer tracking
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ocv import OCVModel
from src.model import BatteryCell, CellState
from src.estimators import CoulombCounter, ExtendedKalmanFilter
from src.simulation import generate_current_profile, run_single_simulation


def main():
    print("=== Battery Electrothermal Model Interactive Exploration ===")
    ocv = OCVModel()
    cell = BatteryCell()

    print(f"Cell Rated Capacity: {cell.q_nom} Ah")
    print(f"Reference Ohmic Resistance (25 C): {cell.r0_ref * 1000:.1f} mOhm")
    print(f"Ohmic Resistance at 45 C: {cell.get_r0(318.15, 1.0) * 1000:.1f} mOhm")
    print(f"Ohmic Resistance at 25 C (SOH 0.80): {cell.get_r0(298.15, 0.8) * 1000:.1f} mOhm")

    # Quick demo run
    init_state = CellState(soc=0.80, vp=0.0, temperature_k=298.15, q_max=3.20, soh=1.0, neq=0.0)
    cc = CoulombCounter(soc_init=0.65)
    ekf = ExtendedKalmanFilter(ocv_model=ocv, soc_init=0.65)

    profile = generate_current_profile("dynamic_pulse", duration_s=600.0, dt=1.0)
    df, metrics = run_single_simulation(
        cell=cell,
        coulomb_counter=cc,
        ekf=ekf,
        current_profile=profile,
        dt=1.0,
        t_amb_k=298.15,
        true_init_state=init_state,
        random_seed=42,
    )

    print("\n--- 10-Minute Demo Results ---")
    print(f"True Initial SOC: {init_state.soc * 100:.1f}% | Initial Guess: 65.0%")
    print(f"Coulomb Counting Final SOC Error: {metrics['final_error_cc_pct']:.2f}%")
    print(f"EKF Observer Final SOC Error: {metrics['final_error_ekf_pct']:.2f}%")
    print(f"EKF Convergence Time (within 2%): {metrics['recovery_time_2pct_s']} seconds")


if __name__ == "__main__":
    main()
