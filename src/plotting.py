"""
Plotting and Publication Figure Generation Module.

Generates high-contrast, publication-quality figures with explicit labels,
legends, and units. Uses matplotlib standard formatting.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Styling configuration
plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 12,
    "lines.linewidth": 1.5,
    "grid.alpha": 0.4,
    "grid.linestyle": "--",
})


def plot_baseline_aligned(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "Baseline Electrothermal Simulation (25 °C, SOH 1.00)",
):
    """
    Figure 3: Aligned baseline current, terminal voltage, true vs estimated SOC, and cell temperature.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(4, 1, figsize=(8.5, 9.0), sharex=True)

    t_min = df["time_s"] / 60.0 # Time in minutes

    # 1. Current Profile
    axes[0].plot(t_min, df["i_true_a"], label="Applied Current (True)", color="#1f77b4")
    axes[0].set_ylabel("Current [A]")
    axes[0].set_title(title, fontweight="bold")
    axes[0].grid(True)
    axes[0].legend(loc="upper right")

    # 2. Terminal Voltage
    axes[1].plot(t_min, df["vt_true_v"], label="True $V_t$", color="#2ca02c")
    axes[1].plot(t_min, df["vt_meas_v"], label="Measured $V_{t,\\mathrm{meas}}$", color="#7f7f7f", alpha=0.35, linewidth=0.8)
    axes[1].set_ylabel("Terminal Voltage [V]")
    axes[1].grid(True)
    axes[1].legend(loc="upper right")

    # 3. State of Charge (True, CC, EKF)
    axes[2].plot(t_min, df["soc_true"] * 100.0, label="True SOC", color="#000000", linewidth=2.0)
    axes[2].plot(t_min, df["soc_cc"] * 100.0, label="Coulomb Counting (Initial Error -15%)", color="#d62728", linestyle="--")
    axes[2].plot(t_min, df["soc_ekf"] * 100.0, label="EKF Observer", color="#1f77b4", linestyle="-.")
    axes[2].set_ylabel("SOC [%]")
    axes[2].grid(True)
    axes[2].legend(loc="lower left")

    # 4. Cell Temperature
    axes[3].plot(t_min, df["temp_cell_c"], label="Cell Core Temp", color="#ff7f0e")
    axes[3].axhline(25.0, color="#7f7f7f", linestyle=":", label="Ambient ($25\\,^\\circ\\mathrm{C}$)")
    axes[3].set_ylabel("Temperature [$^\\circ$C]")
    axes[3].set_xlabel("Elapsed Time [minutes]")
    axes[3].grid(True)
    axes[3].legend(loc="upper left")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"[plotting] Saved aligned baseline figure to: {output_path}")


def plot_error_comparison(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "SOC Estimation Error Dynamics (CC vs. EKF)",
):
    """
    Figure 4: Coulomb counting vs. EKF SOC error after wrong initialization.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.0, 4.5))

    t_min = df["time_s"] / 60.0

    ax.plot(t_min, df["error_cc"] * 100.0, label="Coulomb Counting Error", color="#d62728", linestyle="--", linewidth=1.8)
    ax.plot(t_min, df["error_ekf"] * 100.0, label="EKF Observer Error", color="#1f77b4", linewidth=2.0)
    
    # 2% error threshold band
    ax.axhspan(-2.0, 2.0, color="#2ca02c", alpha=0.15, label="Target Accuracy (±2% SOC)")
    ax.axhline(0.0, color="#7f7f7f", linestyle=":", linewidth=1.0)

    ax.set_xlabel("Elapsed Time [minutes]")
    ax.set_ylabel("SOC Estimation Error [percentage points]")
    ax.set_title(title, fontweight="bold")
    ax.grid(True)
    ax.legend(loc="lower right")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"[plotting] Saved error comparison figure to: {output_path}")


def plot_heatmap_core_matrix(
    df_results: pd.DataFrame,
    output_path: Path,
):
    """
    Figure 5: Temperature x SOH heatmap of RMSE for both estimators.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Filter for dynamic pulse profile
    df_dyn = df_results[df_results["load_profile"] == "dynamic_pulse"]
    
    # Pivot tables for CC and EKF RMSE
    pivot_cc = df_dyn.pivot(index="temp_c", columns="soh", values="soc_rmse_cc_pct")
    pivot_ekf = df_dyn.pivot(index="temp_c", columns="soh", values="soc_rmse_ekf_pct")

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.5), sharey=True)

    # Colormaps
    im0 = axes[0].imshow(pivot_cc.values, cmap="YlOrRd", aspect="auto", origin="lower")
    axes[0].set_title("Coulomb Counting SOC RMSE [%]\n(Open-loop nominal baseline)", fontweight="bold")
    axes[0].set_xlabel("State of Health (SOH)")
    axes[0].set_ylabel("Ambient Temperature [°C]")
    axes[0].set_xticks(range(len(pivot_cc.columns)))
    axes[0].set_xticklabels([f"{c:.2f}" for c in pivot_cc.columns])
    axes[0].set_yticks(range(len(pivot_cc.index)))
    axes[0].set_yticklabels([f"{idx:.0f} °C" for idx in pivot_cc.index])
    
    # Overlay values
    for i in range(len(pivot_cc.index)):
        for j in range(len(pivot_cc.columns)):
            val = pivot_cc.values[i, j]
            axes[0].text(j, i, f"{val:.2f}%", ha="center", va="center", color="black" if val < 20 else "white", fontweight="bold")
    fig.colorbar(im0, ax=axes[0], label="RMSE [%]")

    im1 = axes[1].imshow(pivot_ekf.values, cmap="Blues", aspect="auto", origin="lower")
    axes[1].set_title("Extended Kalman Filter SOC RMSE [%]\n(Physics-informed observer)", fontweight="bold")
    axes[1].set_xlabel("State of Health (SOH)")
    axes[1].set_xticks(range(len(pivot_ekf.columns)))
    axes[1].set_xticklabels([f"{c:.2f}" for c in pivot_ekf.columns])
    
    for i in range(len(pivot_ekf.index)):
        for j in range(len(pivot_ekf.columns)):
            val = pivot_ekf.values[i, j]
            axes[1].text(j, i, f"{val:.3f}%", ha="center", va="center", color="black" if val < 1.0 else "white", fontweight="bold")
    fig.colorbar(im1, ax=axes[1], label="RMSE [%]")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"[plotting] Saved core matrix heatmap to: {output_path}")
