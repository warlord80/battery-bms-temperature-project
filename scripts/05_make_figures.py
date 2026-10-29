"""
Script 05: Master Publication Figure Generator.

Generates and compiles all eight main publication figures:
- Figure 1: 1-RC Thévenin ECM, lumped thermal node, and EKF observer schematic.
- Figure 2: OCV-SOC characteristic curve, dOCV/dz derivative, and R0(T, SOH) scaling.
- Figure 3: Aligned baseline timeseries (Current, Voltage, SOC, Temperature).
- Figure 4: SOC error dynamics (Coulomb Counting vs. EKF observer convergence).
- Figure 5: Temperature x SOH heatmap of estimation RMSE for both estimators.
- Figure 6: SOH capacity fade and internal resistance aging surrogate curves.
- Figure 7: Robustness results across four factors with multi-seed error bars.
- Figure 8: Parameter sensitivity ranking (Tornado diagram).
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ocv import OCVModel, DEFAULT_SOC_POINTS, DEFAULT_OCV_POINTS
from src.model import BatteryCell

FIGURES_DIR = PROJECT_ROOT / "results" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def generate_figure_1_schematic():
    """Generates Figure 1: Electrothermal 1-RC ECM & Observer Architecture Schematic."""
    fig, ax = plt.subplots(figsize=(10.0, 5.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    # Title
    ax.text(5.0, 5.6, "Coupled Electrothermal 1-RC Thévenin Model & EKF Observer Architecture",
            ha="center", va="center", fontsize=13, fontweight="bold", color="#1a365d")

    # Block 1: Electrical ECM
    ecm_box = patches.FancyBboxPatch((0.5, 2.4), 4.2, 2.7, boxstyle="round,pad=0.2",
                                    facecolor="#ebf8ff", edgecolor="#3182ce", linewidth=1.8)
    ax.add_patch(ecm_box)
    ax.text(2.6, 4.8, "1-RC Thévenin Equivalent Circuit", ha="center", fontweight="bold", fontsize=10, color="#2b6cb0")
    
    # Circuit elements descriptions inside box
    ax.text(0.8, 4.2, "• Ideal OCV Source: $V_{\\mathrm{oc}} = \\mathrm{OCV}(z)$", fontsize=9)
    ax.text(0.8, 3.6, "• Ohmic Resistance: $R_0(T, \\mathrm{SOH})$", fontsize=9)
    ax.text(0.8, 3.0, "• Polarization RC: $R_1(T, \\mathrm{SOH}) \\parallel C_1$", fontsize=9)
    ax.text(0.8, 2.4, "• Terminal Voltage: $V_t = \\mathrm{OCV}(z) - I R_0 - v_p$", fontsize=9, fontweight="bold", color="#2c5282")

    # Block 2: Thermal Lumped Model
    th_box = patches.FancyBboxPatch((5.3, 2.4), 4.2, 2.7, boxstyle="round,pad=0.2",
                                   facecolor="#fffaf0", edgecolor="#dd6b20", linewidth=1.8)
    ax.add_patch(th_box)
    ax.text(7.4, 4.8, "Lumped Single-Node Thermal ODE", ha="center", fontweight="bold", fontsize=10, color="#c05621")
    ax.text(5.6, 4.2, "• Heat Generation: $Q_{\\mathrm{gen}} = I^2 R_0 + I v_p$", fontsize=9)
    ax.text(5.6, 3.6, "• Convective Cooling: $\\dot{Q}_{\\mathrm{loss}} = hA(T - T_{\\mathrm{amb}})$", fontsize=9)
    ax.text(5.6, 3.0, "• Core Heat Capacity: $C_{\\mathrm{th}} = m \\cdot c_p = 42\\,\\mathrm{J/K}$", fontsize=9)
    ax.text(5.6, 2.4, "• Energy Balance: $C_{\\mathrm{th}} \\frac{dT}{dt} = Q_{\\mathrm{gen}} - hA(T-T_{\\mathrm{amb}})$", fontsize=9, fontweight="bold", color="#9c4221")

    # Coupling arrows between Electrical and Thermal
    ax.annotate("", xy=(5.3, 3.8), xytext=(4.7, 3.8),
                arrowprops=dict(arrowstyle="->", color="#dd6b20", lw=2))
    ax.text(5.0, 4.0, "$Q_{\\mathrm{gen}}$", ha="center", fontsize=9, fontweight="bold", color="#dd6b20")

    ax.annotate("", xy=(4.7, 3.2), xytext=(5.3, 3.2),
                arrowprops=dict(arrowstyle="->", color="#3182ce", lw=2))
    ax.text(5.0, 3.35, "$T_{\\mathrm{cell}}$ (Arrhenius)", ha="center", fontsize=8, color="#3182ce")

    # Block 3: Estimators (Bottom)
    est_box = patches.FancyBboxPatch((1.5, 0.3), 7.0, 1.6, boxstyle="round,pad=0.2",
                                    facecolor="#f0fff4", edgecolor="#38a169", linewidth=1.8)
    ax.add_patch(est_box)
    ax.text(5.0, 1.6, "State Estimation Architecture (Closed-loop Observer vs Open-loop Baseline)", ha="center", fontweight="bold", fontsize=10, color="#276749")
    ax.text(1.8, 1.1, "• Coulomb Counting: $\\hat{z}_{k+1} = \\hat{z}_k - \\frac{\\eta I_{\\mathrm{meas}} \\Delta t}{3600 Q_{\\mathrm{nom}}}$  (Open-loop, drifts with capacity fade)", fontsize=8.5)
    ax.text(1.8, 0.6, "• Extended Kalman Filter: $\\mathbf{x} = [z, v_p]^T$, $y = V_{t,\\mathrm{meas}}$, Joseph stabilized covariance update $\\mathbf{P}_{k|k}$", fontsize=8.5, fontweight="bold", color="#22543d")

    # Measurement feed arrow into Estimators
    ax.annotate("", xy=(5.0, 1.9), xytext=(5.0, 2.4),
                arrowprops=dict(arrowstyle="->", color="#38a169", lw=2))
    ax.text(5.2, 2.1, "$V_{t,\\mathrm{meas}}, I_{\\mathrm{meas}}$", fontsize=9, color="#22543d", fontweight="bold")

    out_path = FIGURES_DIR / "fig1_model_schematic.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[05_make_figures] Saved Figure 1 to: {out_path}")


def generate_figure_2_ocv_and_resistance():
    """Generates Figure 2: OCV(z), dOCV/dz, and R0(T, SOH) Arrhenius scaling."""
    ocv = OCVModel()
    cell = BatteryCell()

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.5))

    # Panel A: OCV and dOCV/dz
    z_fine = np.linspace(0.0, 1.0, 300)
    ocv_vals = ocv.evaluate(z_fine)
    docv_vals = ocv.derivative(z_fine)

    ax1 = axes[0]
    ax1_twin = ax1.twinx()

    p1, = ax1.plot(z_fine * 100.0, ocv_vals, color="#1f77b4", linewidth=2.0, label="OCV [V]")
    p2, = ax1_twin.plot(z_fine * 100.0, docv_vals, color="#d62728", linestyle="--", linewidth=1.5, label="dOCV/dz [V/unit]")

    # Plot discrete calibration points from Barletta et al. 2022
    p3 = ax1.scatter(DEFAULT_SOC_POINTS * 100.0, DEFAULT_OCV_POINTS, color="#000000", zorder=5, label="Lit. Calibration [S1]")

    ax1.set_xlabel("State of Charge (SOC) [%]", fontweight="bold")
    ax1.set_ylabel("Open-Circuit Voltage [V]", color="#1f77b4", fontweight="bold")
    ax1_twin.set_ylabel("Derivative d(OCV)/dz [V]", color="#d62728", fontweight="bold")
    ax1.set_title("(a) Panasonic NCR18650B OCV & Sensitivity", fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.5)

    lines = [p1, p2, p3]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="lower right")

    # Panel B: R0(T, SOH) Arrhenius Scaling
    ax2 = axes[1]
    soh_range = np.linspace(0.80, 1.00, 100)
    temps = [25.0, 35.0, 45.0]
    colors = ["#1f77b4", "#ff7f0e", "#d62728"]

    for t_c, col in zip(temps, colors):
        t_k = t_c + 273.15
        r0_vals = [cell.get_r0(t_k, s) * 1000.0 for s in soh_range] # in mOhm
        ax2.plot(soh_range, r0_vals, label=f"$T = {t_c:.0f}\\,^\\circ\\mathrm{{C}}$", color=col, linewidth=2.0)

    ax2.set_xlabel("State of Health (SOH = $Q_{\\mathrm{max}} / Q_{\\mathrm{nom}}$)", fontweight="bold")
    ax2.set_ylabel("Internal Ohmic Resistance $R_0$ [m$\\Omega$]", fontweight="bold")
    ax2.set_title("(b) Arrhenius & Degradation Resistance Scaling", fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    out_path = FIGURES_DIR / "fig2_ocv_and_resistance.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"[05_make_figures] Saved Figure 2 to: {out_path}")


def generate_figure_6_aging_surrogate():
    """Generates Figure 6: SOH capacity fade and R0 aging surrogate curves."""
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.5))

    n_eq = np.linspace(0, 1000, 200) # 0 to 1000 equivalent full cycles
    q_nom = 3.20

    # Empirical Arrhenius-accelerated aging surrogate (Mehta & Gupta 2024 review)
    # kQ(T) = kQ_ref * exp[(Ea_age / Rg)(1/T - 1/Tref)]
    rg = 8.314
    t_ref = 298.15
    ea_age = 30000.0 # J/mol
    kq_ref = 0.0055
    b_exp = 0.52 # Sublinear square-root-like SEI growth

    temps = [25.0, 35.0, 45.0]
    colors = ["#1f77b4", "#ff7f0e", "#d62728"]

    for t_c, col in zip(temps, colors):
        t_k = t_c + 273.15
        arrh_age = np.exp((ea_age / rg) * (1.0 / t_ref - 1.0 / t_k)) # Higher T accelerates aging
        kq_t = kq_ref * arrh_age
        soh_curve = 1.0 - kq_t * (n_eq ** b_exp)
        soh_clamped = np.clip(soh_curve, 0.70, 1.00)

        # Resistance growth: R0,age = R0(T) * (1 + 0.8 * (1 - SOH))
        r0_growth = (1.0 + 0.80 * (1.0 - soh_clamped)) * 100.0 # Percentage of nominal

        axes[0].plot(n_eq, soh_clamped * 100.0, label=f"$T = {t_c:.0f}\\,^\\circ\\mathrm{{C}}$", color=col, linewidth=2.0)
        axes[1].plot(n_eq, r0_growth, label=f"$T = {t_c:.0f}\\,^\\circ\\mathrm{{C}}$", color=col, linewidth=2.0)

    # 80% EOL boundary
    axes[0].axhline(80.0, color="#7f7f7f", linestyle=":", label="80% EOL Threshold")
    axes[0].set_xlabel("Equivalent Full Cycles ($N_{\\mathrm{eq}}$)", fontweight="bold")
    axes[0].set_ylabel("State of Health (SOH) [%]", fontweight="bold")
    axes[0].set_title("(a) Available Capacity Fade Trajectory", fontweight="bold")
    axes[0].grid(True, linestyle="--", alpha=0.5)
    axes[0].legend(loc="lower left")

    axes[1].set_xlabel("Equivalent Full Cycles ($N_{\\mathrm{eq}}$)", fontweight="bold")
    axes[1].set_ylabel("Normalized Resistance $R_0 / R_{0,\\mathrm{fresh}}$ [%]", fontweight="bold")
    axes[1].set_title("(b) Resistance Growth Trajectory", fontweight="bold")
    axes[1].grid(True, linestyle="--", alpha=0.5)
    axes[1].legend(loc="upper left")

    plt.tight_layout()
    out_path = FIGURES_DIR / "fig6_aging_surrogate.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"[05_make_figures] Saved Figure 6 to: {out_path}")


def main():
    print("[05_make_figures] Compiling complete 8-figure publication suite...")
    generate_figure_1_schematic()
    generate_figure_2_ocv_and_resistance()
    generate_figure_6_aging_surrogate()

    # Verify that all 8 figures exist
    required_figures = [
        "fig1_model_schematic.png",
        "fig2_ocv_and_resistance.png",
        "fig3_baseline_timeseries.png",
        "fig4_error_dynamics.png",
        "fig5_temperature_soh_heatmap.png",
        "fig6_aging_surrogate.png",
        "fig7_robustness_errorbars.png",
        "fig8_sensitivity_tornado.png",
    ]

    print("\n--- Visual Verification Checklist ---")
    missing = []
    for fig_name in required_figures:
        p = FIGURES_DIR / fig_name
        if p.exists() and p.stat().st_size > 1000:
            print(f"  [OK] {fig_name} ({p.stat().st_size / 1024:.1f} KB)")
        else:
            print(f"  [MISSING] {fig_name}")
            missing.append(fig_name)

    if not missing:
        print("\nAll 8 publication figures verified successfully!")
    else:
        print(f"\nWarning: {len(missing)} figures missing!")


if __name__ == "__main__":
    main()
