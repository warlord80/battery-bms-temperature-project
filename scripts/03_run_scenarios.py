"""
Script 03: Run Core 36-Scenario Matrix.

Automates all 36 comparative scenarios:
- Temperatures: 25 °C, 35 °C, 45 °C
- SOH: 1.00, 0.90, 0.80
- Loads: Steady moderate (0.5C) vs Dynamic pulse
- Estimators: Coulomb Counting vs EKF
Generates results/tables/core_matrix_36_scenarios.csv, Figure 4, and Figure 5.
"""

import sys
from pathlib import Path
import yaml
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ocv import OCVModel
from src.model import BatteryCell, CellState
from src.estimators import CoulombCounter, ExtendedKalmanFilter
from src.simulation import generate_current_profile, run_single_simulation
from src.plotting import plot_error_comparison, plot_heatmap_core_matrix


def run_all_scenarios():
    print("[03_run_scenarios] Loading scenario configurations...")
    config_path = PROJECT_ROOT / "configs" / "scenarios.yaml"
    baseline_cfg_path = PROJECT_ROOT / "configs" / "baseline.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    with open(baseline_cfg_path, "r", encoding="utf-8") as f:
        b_cfg = yaml.safe_load(f)

    results_tables = PROJECT_ROOT / "results" / "tables"
    results_figures = PROJECT_ROOT / "results" / "figures"
    results_tables.mkdir(parents=True, exist_ok=True)
    results_figures.mkdir(parents=True, exist_ok=True)

    ocv = OCVModel()
    temps_c = cfg["core_matrix"]["temperatures_c"]
    soh_levels = cfg["core_matrix"]["soh_levels"]
    loads = cfg["core_matrix"]["loads"]
    
    dt = b_cfg["time"]["dt"]
    duration_s = 3600.0
    seed = b_cfg["experiment"]["random_seed"]

    scenario_rows = []
    baseline_df_for_plot = None

    scenario_idx = 1
    total_runs = len(temps_c) * len(soh_levels) * len(loads)

    print(f"[03_run_scenarios] Executing {total_runs} simulation runs (evaluating 36 estimator conditions)...")

    for temp_c in temps_c:
        temp_k = temp_c + 273.15
        for soh in soh_levels:
            for load_type in loads:
                # Cell configuration under specific SOH
                cell = BatteryCell(
                    q_nom=b_cfg["cell"]["Qnom"],
                    t_ref=b_cfg["cell"]["Tref"],
                    r0_ref=b_cfg["electrical"]["R0_ref"],
                    r1_ref=b_cfg["electrical"]["R1_ref"],
                    c1=b_cfg["electrical"]["C1"],
                    ea_0=b_cfg["electrical"]["Ea_0"],
                    ea_1=b_cfg["electrical"]["Ea_1"],
                    alpha_0=b_cfg["electrical"]["alpha_0"],
                    alpha_1=b_cfg["electrical"]["alpha_1"],
                    cth=b_cfg["thermal"]["Cth"],
                    ha=b_cfg["thermal"]["hA"],
                    ocv_model=ocv,
                )

                true_q_max = b_cfg["cell"]["Qnom"] * soh
                true_state = CellState(
                    soc=b_cfg["initial_conditions"]["true_soc"], # 0.80
                    vp=0.0,
                    temperature_k=temp_k,
                    q_max=true_q_max,
                    soh=soh,
                    neq=0.0,
                )

                # Estimator configurations (both initialize at SOC = 0.65)
                # Coulomb counting assumes nominal Qnom = 3.20 Ah
                cc = CoulombCounter(
                    q_assumed=b_cfg["cell"]["Qnom"],
                    soc_init=b_cfg["initial_conditions"]["est_soc"]
                )
                
                # EKF initialized with nominal parameters
                ekf = ExtendedKalmanFilter(
                    ocv_model=ocv,
                    q_est=b_cfg["cell"]["Qnom"],
                    r0_est=cell.get_r0(temp_k, soh=1.0), # Estimator unaware of true degradation
                    r1_est=cell.get_r1(temp_k, soh=1.0),
                    c1_est=b_cfg["electrical"]["C1"],
                    soc_init=b_cfg["initial_conditions"]["est_soc"],
                    vp_init=0.0,
                )

                current_profile = generate_current_profile(load_type, duration_s=duration_s, dt=dt)

                df_run, metrics = run_single_simulation(
                    cell=cell,
                    coulomb_counter=cc,
                    ekf=ekf,
                    current_profile=current_profile,
                    dt=dt,
                    t_amb_k=temp_k,
                    true_init_state=true_state,
                    sigma_v=b_cfg["sensor_noise"]["sigma_v"],
                    sigma_i=b_cfg["sensor_noise"]["sigma_i"],
                    i_bias=b_cfg["sensor_noise"]["i_bias"],
                    random_seed=seed,
                )

                # Save baseline df for fig 4 (25 C, SOH 1.0, dynamic pulse)
                if temp_c == 25.0 and soh == 1.00 and load_type == "dynamic_pulse":
                    baseline_df_for_plot = df_run

                # Record results
                row = {
                    "scenario_id": f"SCEN_{scenario_idx:02d}",
                    "temp_c": temp_c,
                    "temp_k": temp_k,
                    "soh": soh,
                    "q_max_ah": true_q_max,
                    "load_profile": load_type,
                    "soc_rmse_cc_pct": metrics["soc_rmse_cc_pct"],
                    "soc_mae_cc_pct": metrics["soc_mae_cc_pct"],
                    "final_error_cc_pct": metrics["final_error_cc_pct"],
                    "soc_rmse_ekf_pct": metrics["soc_rmse_ekf_pct"],
                    "soc_mae_ekf_pct": metrics["soc_mae_ekf_pct"],
                    "final_error_ekf_pct": metrics["final_error_ekf_pct"],
                    "ekf_recovery_time_s": metrics["recovery_time_2pct_s"],
                    "delivered_energy_wh": metrics["delivered_energy_wh"],
                    "usable_capacity_ah": metrics["usable_capacity_ah"],
                    "peak_temp_c": metrics["peak_temp_c"],
                    "temp_rise_k": metrics["peak_temp_c"] - temp_c,
                }
                scenario_rows.append(row)
                scenario_idx += 1

    df_matrix = pd.DataFrame(scenario_rows)
    matrix_csv = results_tables / "core_matrix_36_scenarios.csv"
    df_matrix.to_csv(matrix_csv, index=False)
    print(f"[03_run_scenarios] Core matrix results (18 runs / 36 conditions) saved to: {matrix_csv}")

    # Generate Figure 4: Error dynamics
    if baseline_df_for_plot is not None:
        fig4_path = results_figures / "fig4_error_dynamics.png"
        plot_error_comparison(baseline_df_for_plot, fig4_path)

    # Generate Figure 5: Heatmaps
    fig5_path = results_figures / "fig5_temperature_soh_heatmap.png"
    plot_heatmap_core_matrix(df_matrix, fig5_path)

    print("\n" + "="*80)
    print("CORE MATRIX SCENARIO SUMMARY (Sample)")
    print("="*80)
    print(df_matrix[["scenario_id", "temp_c", "soh", "load_profile", "soc_rmse_cc_pct", "soc_rmse_ekf_pct", "peak_temp_c"]].to_string(index=False))
    print("="*80 + "\n")


if __name__ == "__main__":
    run_all_scenarios()
