"""
Script 04: Robustness and Sensitivity Suite with Multi-Seed Monte Carlo Analysis.

Evaluates 5 robustness factors across >= 5 random seeds:
1. Initial SOC error: -20%, -10%, +10%, +20%
2. Current sensor bias: -1.0%, -0.5%, 0.0%, +0.5%, +1.0%
3. Voltage sensor noise std: 2 mV, 5 mV, 10 mV
4. Estimator R0 parameter mismatch: -10%, 0%, +10%
5. Relative sensitivity ranking (Tornado analysis).

Exports:
- results/tables/robustness_study_metrics.csv
- results/tables/sensitivity_tornado_ranking.csv
- results/figures/fig7_robustness_errorbars.png
- results/figures/fig8_sensitivity_tornado.png
"""

import sys
from pathlib import Path
import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ocv import OCVModel
from src.model import BatteryCell, CellState
from src.estimators import CoulombCounter, ExtendedKalmanFilter
from src.simulation import generate_current_profile, run_single_simulation


def run_robustness():
    print("[04_run_robustness] Loading scenario and baseline configurations...")
    b_cfg_path = PROJECT_ROOT / "configs" / "baseline.yaml"
    s_cfg_path = PROJECT_ROOT / "configs" / "scenarios.yaml"

    with open(b_cfg_path, "r", encoding="utf-8") as f:
        b_cfg = yaml.safe_load(f)
    with open(s_cfg_path, "r", encoding="utf-8") as f:
        s_cfg = yaml.safe_load(f)

    results_tables = PROJECT_ROOT / "results" / "tables"
    results_figures = PROJECT_ROOT / "results" / "figures"
    results_tables.mkdir(parents=True, exist_ok=True)
    results_figures.mkdir(parents=True, exist_ok=True)

    ocv = OCVModel()
    seeds = s_cfg["robustness_study"]["random_seeds"]
    dt = b_cfg["time"]["dt"]
    duration_s = 3600.0

    # Nominal cell setup (25 C, SOH 1.0)
    def create_nominal_cell():
        return BatteryCell(
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

    current_profile = generate_current_profile("dynamic_pulse", duration_s=duration_s, dt=dt)
    nominal_current_mag = 1.60

    robustness_records = []

    # -------------------------------------------------------------------------
    # Factor 1: Initial SOC Error (-20%, -10%, +10%, +20%)
    # -------------------------------------------------------------------------
    print("[04_run_robustness] Evaluating Factor 1: Initial SOC Error...")
    true_soc = 0.80
    init_soc_offsets = [-0.20, -0.10, 0.10, 0.20]
    for offset in init_soc_offsets:
        est_init_soc = float(np.clip(true_soc + offset, 0.05, 0.95))
        for seed in seeds:
            cell = create_nominal_cell()
            true_state = CellState(soc=true_soc, vp=0.0, temperature_k=298.15, q_max=3.20, soh=1.0, neq=0.0)
            cc = CoulombCounter(q_assumed=3.20, soc_init=est_init_soc)
            ekf = ExtendedKalmanFilter(ocv_model=ocv, soc_init=est_init_soc, r0_est=cell.r0_ref, r1_est=cell.r1_ref, c1_est=cell.c1)

            _, m = run_single_simulation(
                cell=cell, coulomb_counter=cc, ekf=ekf,
                current_profile=current_profile, dt=dt, t_amb_k=298.15,
                true_init_state=true_state, random_seed=seed
            )
            robustness_records.append({
                "factor": "Initial SOC Offset",
                "level_str": f"{offset*100:+.0f}%",
                "level_num": offset,
                "seed": seed,
                "soc_rmse_cc_pct": m["soc_rmse_cc_pct"],
                "soc_rmse_ekf_pct": m["soc_rmse_ekf_pct"],
                "final_error_cc_pct": m["final_error_cc_pct"],
                "final_error_ekf_pct": m["final_error_ekf_pct"],
                "recovery_time_s": m["recovery_time_2pct_s"],
            })

    # -------------------------------------------------------------------------
    # Factor 2: Current Bias (-1.0%, -0.5%, 0.0%, +0.5%, +1.0% of 1.6A)
    # -------------------------------------------------------------------------
    print("[04_run_robustness] Evaluating Factor 2: Current Sensor Bias...")
    bias_fractions = [-0.010, -0.005, 0.0, 0.005, 0.010]
    for b_frac in bias_fractions:
        i_bias = b_frac * nominal_current_mag
        for seed in seeds:
            cell = create_nominal_cell()
            true_state = CellState(soc=true_soc, vp=0.0, temperature_k=298.15, q_max=3.20, soh=1.0, neq=0.0)
            cc = CoulombCounter(q_assumed=3.20, soc_init=0.65)
            ekf = ExtendedKalmanFilter(ocv_model=ocv, soc_init=0.65, r0_est=cell.r0_ref, r1_est=cell.r1_ref, c1_est=cell.c1)

            _, m = run_single_simulation(
                cell=cell, coulomb_counter=cc, ekf=ekf,
                current_profile=current_profile, dt=dt, t_amb_k=298.15,
                true_init_state=true_state, i_bias=i_bias, random_seed=seed
            )
            robustness_records.append({
                "factor": "Current Bias",
                "level_str": f"{b_frac*100:+.1f}%",
                "level_num": b_frac,
                "seed": seed,
                "soc_rmse_cc_pct": m["soc_rmse_cc_pct"],
                "soc_rmse_ekf_pct": m["soc_rmse_ekf_pct"],
                "final_error_cc_pct": m["final_error_cc_pct"],
                "final_error_ekf_pct": m["final_error_ekf_pct"],
                "recovery_time_s": m["recovery_time_2pct_s"],
            })

    # -------------------------------------------------------------------------
    # Factor 3: Voltage Noise Std (2 mV, 5 mV, 10 mV)
    # -------------------------------------------------------------------------
    print("[04_run_robustness] Evaluating Factor 3: Voltage Noise...")
    v_noises = [0.002, 0.005, 0.010]
    for sigma_v in v_noises:
        for seed in seeds:
            cell = create_nominal_cell()
            true_state = CellState(soc=true_soc, vp=0.0, temperature_k=298.15, q_max=3.20, soh=1.0, neq=0.0)
            cc = CoulombCounter(q_assumed=3.20, soc_init=0.65)
            ekf = ExtendedKalmanFilter(ocv_model=ocv, soc_init=0.65, r0_est=cell.r0_ref, r1_est=cell.r1_ref, c1_est=cell.c1, r_cov=sigma_v**2)

            _, m = run_single_simulation(
                cell=cell, coulomb_counter=cc, ekf=ekf,
                current_profile=current_profile, dt=dt, t_amb_k=298.15,
                true_init_state=true_state, sigma_v=sigma_v, random_seed=seed
            )
            robustness_records.append({
                "factor": "Voltage Noise",
                "level_str": f"{sigma_v*1000:.0f} mV",
                "level_num": sigma_v,
                "seed": seed,
                "soc_rmse_cc_pct": m["soc_rmse_cc_pct"],
                "soc_rmse_ekf_pct": m["soc_rmse_ekf_pct"],
                "final_error_cc_pct": m["final_error_cc_pct"],
                "final_error_ekf_pct": m["final_error_ekf_pct"],
                "recovery_time_s": m["recovery_time_2pct_s"],
            })

    # -------------------------------------------------------------------------
    # Factor 4: Estimator R0 Mismatch (-10%, 0%, +10%)
    # -------------------------------------------------------------------------
    print("[04_run_robustness] Evaluating Factor 4: Estimator R0 Mismatch...")
    r0_offsets = [-0.10, 0.0, 0.10]
    for r_off in r0_offsets:
        r0_est = cell.r0_ref * (1.0 + r_off)
        for seed in seeds:
            cell = create_nominal_cell()
            true_state = CellState(soc=true_soc, vp=0.0, temperature_k=298.15, q_max=3.20, soh=1.0, neq=0.0)
            cc = CoulombCounter(q_assumed=3.20, soc_init=0.65)
            ekf = ExtendedKalmanFilter(ocv_model=ocv, soc_init=0.65, r0_est=r0_est, r1_est=cell.r1_ref, c1_est=cell.c1)

            _, m = run_single_simulation(
                cell=cell, coulomb_counter=cc, ekf=ekf,
                current_profile=current_profile, dt=dt, t_amb_k=298.15,
                true_init_state=true_state, random_seed=seed
            )
            robustness_records.append({
                "factor": "R0 Parameter Mismatch",
                "level_str": f"{r_off*100:+.0f}%",
                "level_num": r_off,
                "seed": seed,
                "soc_rmse_cc_pct": m["soc_rmse_cc_pct"],
                "soc_rmse_ekf_pct": m["soc_rmse_ekf_pct"],
                "final_error_cc_pct": m["final_error_cc_pct"],
                "final_error_ekf_pct": m["final_error_ekf_pct"],
                "recovery_time_s": m["recovery_time_2pct_s"],
            })

    df_rob = pd.DataFrame(robustness_records)
    rob_csv = results_tables / "robustness_study_metrics.csv"
    df_rob.to_csv(rob_csv, index=False)
    print(f"[04_run_robustness] Robustness data saved to: {rob_csv}")

    # Aggregate by factor and level (Mean +/- Std)
    df_agg = df_rob.groupby(["factor", "level_str", "level_num"]).agg(
        cc_rmse_mean=("soc_rmse_cc_pct", "mean"),
        cc_rmse_std=("soc_rmse_cc_pct", "std"),
        ekf_rmse_mean=("soc_rmse_ekf_pct", "mean"),
        ekf_rmse_std=("soc_rmse_ekf_pct", "std"),
        final_cc_mean=("final_error_cc_pct", "mean"),
        final_ekf_mean=("final_error_ekf_pct", "mean"),
    ).reset_index()

    # -------------------------------------------------------------------------
    # Plot Figure 7: Robustness Results with Uncertainty Bars
    # -------------------------------------------------------------------------
    fig7_path = results_figures / "fig7_robustness_errorbars.png"
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 8.5))

    factors = ["Initial SOC Offset", "Current Bias", "Voltage Noise", "R0 Parameter Mismatch"]
    ax_list = axes.flatten()

    for idx, factor_name in enumerate(factors):
        sub_df = df_agg[df_agg["factor"] == factor_name].sort_values("level_num")
        ax = ax_list[idx]

        x_labels = sub_df["level_str"].tolist()
        x_pos = np.arange(len(x_labels))

        # Bar width
        w = 0.35
        ax.bar(x_pos - w/2, sub_df["cc_rmse_mean"], yerr=sub_df["cc_rmse_std"], width=w, label="Coulomb Counting", color="#d62728", capsize=4, alpha=0.85)
        ax.bar(x_pos + w/2, sub_df["ekf_rmse_mean"], yerr=sub_df["ekf_rmse_std"], width=w, label="EKF Observer", color="#1f77b4", capsize=4, alpha=0.85)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_labels)
        ax.set_ylabel("SOC RMSE [%]")
        ax.set_title(f"Sensitivity to {factor_name}", fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.5)
        if idx == 0:
            ax.legend(loc="upper left")

    plt.tight_layout()
    fig.savefig(fig7_path, dpi=300)
    plt.close(fig)
    print(f"[04_run_robustness] Saved Figure 7 to: {fig7_path}")

    # -------------------------------------------------------------------------
    # Tornado Sensitivity Analysis (Answer to Question 4 in Brief):
    # Which factor has the largest effect: Ambient Temp, Load Profile, Capacity Fade, or Resistance Growth?
    # -------------------------------------------------------------------------
    # We load core matrix to extract main effects on final SOC error / RMSE
    matrix_csv = results_tables / "core_matrix_36_scenarios.csv"
    df_matrix = pd.read_csv(matrix_csv)

    # 1. Capacity Fade effect (SOH 1.00 to 0.80) on Coulomb Counting RMSE:
    cc_soh_spread = df_matrix.groupby("soh")["soc_rmse_cc_pct"].mean().max() - df_matrix.groupby("soh")["soc_rmse_cc_pct"].mean().min()
    # 2. Ambient Temperature effect (25 to 45 C) on EKF RMSE:
    ekf_temp_spread = df_matrix.groupby("temp_c")["soc_rmse_ekf_pct"].mean().max() - df_matrix.groupby("temp_c")["soc_rmse_ekf_pct"].mean().min()
    # 3. Load profile effect:
    load_spread = df_matrix.groupby("load_profile")["soc_rmse_ekf_pct"].mean().max() - df_matrix.groupby("load_profile")["soc_rmse_ekf_pct"].mean().min()
    # 4. Current sensor bias effect (from robustness study):
    bias_spread = df_agg[df_agg["factor"] == "Current Bias"]["cc_rmse_mean"].max() - df_agg[df_agg["factor"] == "Current Bias"]["cc_rmse_mean"].min()
    # 5. Initial SOC error effect:
    init_err_spread = df_agg[df_agg["factor"] == "Initial SOC Offset"]["cc_rmse_mean"].max() - df_agg[df_agg["factor"] == "Initial SOC Offset"]["cc_rmse_mean"].min()

    tornado_data = pd.DataFrame([
        {"Factor": "Initial SOC Uncertainty (±20%)", "Impact_Range_Pct": init_err_spread, "Domain": "State Initialization"},
        {"Factor": "Capacity Fade (SOH 1.0 -> 0.8)", "Impact_Range_Pct": cc_soh_spread, "Domain": "Cell Aging"},
        {"Factor": "Current Sensor Bias (±1%)", "Impact_Range_Pct": bias_spread, "Domain": "Instrumentation"},
        {"Factor": "Ambient Temperature (25-45 °C)", "Impact_Range_Pct": ekf_temp_spread, "Domain": "Environment"},
        {"Factor": "Load Profile Dynamics (Steady vs Pulse)", "Impact_Range_Pct": load_spread, "Domain": "Operating Profile"},
    ]).sort_values("Impact_Range_Pct", ascending=True)

    tornado_csv = results_tables / "sensitivity_tornado_ranking.csv"
    tornado_data.to_csv(tornado_csv, index=False)
    print(f"[04_run_robustness] Sensitivity ranking saved to: {tornado_csv}")

    # Plot Figure 8: Sensitivity / Tornado Plot
    fig8_path = results_figures / "fig8_sensitivity_tornado.png"
    fig, ax = plt.subplots(figsize=(9.0, 4.5))

    y_pos = np.arange(len(tornado_data))
    ax.barh(y_pos, tornado_data["Impact_Range_Pct"], color="#2b5c8f", alpha=0.85, edgecolor="#1a365d")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(tornado_data["Factor"], fontweight="medium")
    ax.set_xlabel("Sensitivity Spread on Estimation Error [percentage points]", fontweight="bold")
    ax.set_title("Figure 8: Sensitivity & Parameter Impact Ranking (Tornado Analysis)", fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)

    for i, val in enumerate(tornado_data["Impact_Range_Pct"]):
        ax.text(val + 0.15, i, f"{val:.2f}%", va="center", fontweight="bold", color="#1a365d")

    plt.tight_layout()
    fig.savefig(fig8_path, dpi=300)
    plt.close(fig)
    print(f"[04_run_robustness] Saved Figure 8 to: {fig8_path}")

    print("\n" + "="*80)
    print("SENSITIVITY & TORNADO RANKING SUMMARY")
    print("="*80)
    print(tornado_data.to_string(index=False))
    print("="*80 + "\n")


if __name__ == "__main__":
    run_robustness()
