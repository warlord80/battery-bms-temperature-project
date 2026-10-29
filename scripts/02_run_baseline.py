"""
Script 02: Run Baseline Simulation and Convergence Evaluation.

Executes baseline simulation at dt = 1.0 s and fine step dt = 0.5 s:
- True Initial SOC: 0.80, Estimator Initial SOC: 0.65 (-15% error)
- Ambient Temperature: 25 °C (298.15 K)
- SOH: 1.00 (Fresh cell, Qmax = 3.20 Ah)
- Load: Dynamic Pulse Profile (3600 s)
- Compares Coulomb Counting against Extended Kalman Filter
- Evaluates numerical time-step convergence
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
from src.plotting import plot_baseline_aligned


def run_baseline():
    print("[02_run_baseline] Loading baseline configuration...")
    config_path = PROJECT_ROOT / "configs" / "baseline.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Output directories
    results_tables = PROJECT_ROOT / "results" / "tables"
    results_figures = PROJECT_ROOT / "results" / "figures"
    results_tables.mkdir(parents=True, exist_ok=True)
    results_figures.mkdir(parents=True, exist_ok=True)

    ocv = OCVModel()

    # 1. Instantiate Ground Truth Cell
    cell = BatteryCell(
        q_nom=cfg["cell"]["Qnom"],
        t_ref=cfg["cell"]["Tref"],
        r0_ref=cfg["electrical"]["R0_ref"],
        r1_ref=cfg["electrical"]["R1_ref"],
        c1=cfg["electrical"]["C1"],
        ea_0=cfg["electrical"]["Ea_0"],
        ea_1=cfg["electrical"]["Ea_1"],
        alpha_0=cfg["electrical"]["alpha_0"],
        alpha_1=cfg["electrical"]["alpha_1"],
        cth=cfg["thermal"]["Cth"],
        ha=cfg["thermal"]["hA"],
        ocv_model=ocv,
    )

    true_init_state = CellState(
        soc=cfg["initial_conditions"]["true_soc"],
        vp=cfg["initial_conditions"]["true_vp"],
        temperature_k=cfg["initial_conditions"]["T_init"],
        q_max=cfg["cell"]["Qnom"] * cfg["initial_conditions"]["soh"],
        soh=cfg["initial_conditions"]["soh"],
        neq=0.0,
    )

    duration_s = 3600.0
    seed = cfg["experiment"]["random_seed"]

    # ----------------------------------------------------
    # RUN 1: Standard Time Step dt = 1.0 s
    # ----------------------------------------------------
    dt_std = cfg["time"]["dt"]
    current_profile_1s = generate_current_profile("dynamic_pulse", duration_s=duration_s, dt=dt_std)

    cc_1s = CoulombCounter(
        q_assumed=cfg["cell"]["Qnom"],
        soc_init=cfg["initial_conditions"]["est_soc"]
    )
    ekf_1s = ExtendedKalmanFilter(
        ocv_model=ocv,
        q_est=cfg["cell"]["Qnom"],
        r0_est=cfg["electrical"]["R0_ref"],
        r1_est=cfg["electrical"]["R1_ref"],
        c1_est=cfg["electrical"]["C1"],
        soc_init=cfg["initial_conditions"]["est_soc"],
        vp_init=cfg["initial_conditions"]["est_vp"],
    )

    print(f"[02_run_baseline] Running dt = {dt_std} s simulation (steps = {len(current_profile_1s)})...")
    df_1s, metrics_1s = run_single_simulation(
        cell=cell,
        coulomb_counter=cc_1s,
        ekf=ekf_1s,
        current_profile=current_profile_1s,
        dt=dt_std,
        t_amb_k=cfg["thermal"]["Tamb"],
        true_init_state=true_init_state,
        sigma_v=cfg["sensor_noise"]["sigma_v"],
        sigma_i=cfg["sensor_noise"]["sigma_i"],
        i_bias=cfg["sensor_noise"]["i_bias"],
        random_seed=seed,
    )

    # ----------------------------------------------------
    # RUN 2: Fine Time Step dt = 0.5 s (Convergence Check)
    # ----------------------------------------------------
    dt_fine = cfg["time"]["dt_fine"]
    current_profile_05s = generate_current_profile("dynamic_pulse", duration_s=duration_s, dt=dt_fine)

    cc_05s = CoulombCounter(
        q_assumed=cfg["cell"]["Qnom"],
        soc_init=cfg["initial_conditions"]["est_soc"]
    )
    ekf_05s = ExtendedKalmanFilter(
        ocv_model=ocv,
        q_est=cfg["cell"]["Qnom"],
        r0_est=cfg["electrical"]["R0_ref"],
        r1_est=cfg["electrical"]["R1_ref"],
        c1_est=cfg["electrical"]["C1"],
        soc_init=cfg["initial_conditions"]["est_soc"],
        vp_init=cfg["initial_conditions"]["est_vp"],
    )

    print(f"[02_run_baseline] Running dt = {dt_fine} s simulation (steps = {len(current_profile_05s)})...")
    df_05s, metrics_05s = run_single_simulation(
        cell=cell,
        coulomb_counter=cc_05s,
        ekf=ekf_05s,
        current_profile=current_profile_05s,
        dt=dt_fine,
        t_amb_k=cfg["thermal"]["Tamb"],
        true_init_state=true_init_state,
        sigma_v=cfg["sensor_noise"]["sigma_v"],
        sigma_i=cfg["sensor_noise"]["sigma_i"],
        i_bias=cfg["sensor_noise"]["i_bias"],
        random_seed=seed,
    )

    # Save time-series
    ts_csv = results_tables / "baseline_timeseries_dt1s.csv"
    df_1s.to_csv(ts_csv, index=False)
    print(f"[02_run_baseline] Baseline timeseries saved to {ts_csv}")

    # Plot aligned baseline figure
    fig3_path = results_figures / "fig3_baseline_timeseries.png"
    plot_baseline_aligned(df_1s, fig3_path)

    # Convergence comparison summary
    comparison = {
        "Metric": [
            "SOC RMSE Coulomb Counting [%]",
            "SOC RMSE EKF [%]",
            "Final SOC Error Coulomb Counting [%]",
            "Final SOC Error EKF [%]",
            "EKF Recovery Time (|error| <= 2%) [s]",
            "Delivered Energy [Wh]",
            "Peak Cell Temperature [°C]"
        ],
        "dt = 1.0 s": [
            f"{metrics_1s['soc_rmse_cc_pct']:.3f}",
            f"{metrics_1s['soc_rmse_ekf_pct']:.3f}",
            f"{metrics_1s['final_error_cc_pct']:.3f}",
            f"{metrics_1s['final_error_ekf_pct']:.3f}",
            f"{metrics_1s['recovery_time_2pct_s']:.1f}",
            f"{metrics_1s['delivered_energy_wh']:.3f}",
            f"{metrics_1s['peak_temp_c']:.2f}",
        ],
        "dt = 0.5 s": [
            f"{metrics_05s['soc_rmse_cc_pct']:.3f}",
            f"{metrics_05s['soc_rmse_ekf_pct']:.3f}",
            f"{metrics_05s['final_error_cc_pct']:.3f}",
            f"{metrics_05s['final_error_ekf_pct']:.3f}",
            f"{metrics_05s['recovery_time_2pct_s']:.1f}",
            f"{metrics_05s['delivered_energy_wh']:.3f}",
            f"{metrics_05s['peak_temp_c']:.2f}",
        ],
        "Relative Difference [%]": [
            f"{abs(metrics_1s['soc_rmse_cc_pct'] - metrics_05s['soc_rmse_cc_pct']) / max(1e-6, metrics_1s['soc_rmse_cc_pct']) * 100:.3f}%",
            f"{abs(metrics_1s['soc_rmse_ekf_pct'] - metrics_05s['soc_rmse_ekf_pct']) / max(1e-6, metrics_1s['soc_rmse_ekf_pct']) * 100:.3f}%",
            f"{abs(metrics_1s['final_error_cc_pct'] - metrics_05s['final_error_cc_pct']) / max(1e-6, abs(metrics_1s['final_error_cc_pct'])) * 100:.3f}%",
            f"{abs(metrics_1s['final_error_ekf_pct'] - metrics_05s['final_error_ekf_pct']) / max(1e-6, abs(metrics_1s['final_error_ekf_pct'])) * 100:.3f}%",
            f"{abs(metrics_1s['recovery_time_2pct_s'] - metrics_05s['recovery_time_2pct_s']):.1f} s (abs diff)",
            f"{abs(metrics_1s['delivered_energy_wh'] - metrics_05s['delivered_energy_wh']) / max(1e-6, metrics_1s['delivered_energy_wh']) * 100:.3f}%",
            f"{abs(metrics_1s['peak_temp_c'] - metrics_05s['peak_temp_c']) / max(1e-6, metrics_1s['peak_temp_c']) * 100:.3f}%",
        ]
    }
    df_comp = pd.DataFrame(comparison)
    metrics_csv = results_tables / "baseline_convergence_metrics.csv"
    df_comp.to_csv(metrics_csv, index=False)

    print("\n" + "="*80)
    print("BASELINE CONVERGENCE & COMPARISON SUMMARY")
    print("="*80)
    print(df_comp.to_string(index=False))
    print("="*80)
    print(f"Metrics table saved to: {metrics_csv}\n")


if __name__ == "__main__":
    run_baseline()
