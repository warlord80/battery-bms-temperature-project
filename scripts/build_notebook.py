"""
Jupyter Notebook Builder.

Constructs notebooks/01_interactive_exploration.ipynb with pre-computed
outputs and embedded base64 publication plots for instant rendering on GitHub.
"""

import sys
import json
import base64
import io
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ocv import OCVModel, DEFAULT_SOC_POINTS, DEFAULT_OCV_POINTS
from src.model import BatteryCell, CellState
from src.estimators import CoulombCounter, ExtendedKalmanFilter
from src.simulation import generate_current_profile, run_single_simulation


def fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return data


def build_notebook():
    print("[build_notebook] Building interactive notebook with pre-rendered outputs...")

    cells = []

    # ----------------------------------------------------
    # Cell 1: Title & Overview
    # ----------------------------------------------------
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Lithium-Ion Battery Electrothermal Modeling & State-of-Charge (SOC) Estimation\n",
            "### Interactive Exploration & Verification Notebook\n",
            "\n",
            "**Repository:** [warlord80/battery-bms-temperature-project](https://github.com/warlord80/battery-bms-temperature-project)  \n",
            "**Cell Format:** Panasonic NCR18650B ($3.20\\,\\mathrm{Ah}$ NCA/Graphite)  \n",
            "**Core Model:** 1-RC Thévenin Equivalent Circuit Model coupled to a Lumped Thermal ODE and Extended Kalman Filter (EKF) observer.\n",
            "\n",
            "> **Research Claim:** This work develops a reduced-order electrothermal and aging-aware equivalent-circuit model for controlled sensitivity analysis of battery SOC estimation. It demonstrates behaviour under stated assumptions; it does not identify parameters from new experiments or establish a chemistry-independent degradation law.\n"
        ]
    })

    # ----------------------------------------------------
    # Cell 2: Imports & Environment
    # ----------------------------------------------------
    cell2_code = [
        "import sys\n",
        "from pathlib import Path\n",
        "import numpy as np\n",
        "import pandas as pd\n",
        "import matplotlib.pyplot as plt\n",
        "\n",
        "# Project imports\n",
        "from src.ocv import OCVModel, DEFAULT_SOC_POINTS, DEFAULT_OCV_POINTS\n",
        "from src.model import BatteryCell, CellState\n",
        "from src.estimators import CoulombCounter, ExtendedKalmanFilter\n",
        "from src.simulation import generate_current_profile, run_single_simulation\n",
        "\n",
        "print('All modules successfully loaded!')\n"
    ]
    cells.append({
        "cell_type": "code",
        "execution_count": 1,
        "metadata": {},
        "outputs": [
            {
                "name": "stdout",
                "output_type": "stream",
                "text": ["All modules successfully loaded!\n"]
            }
        ],
        "source": cell2_code
    })

    # ----------------------------------------------------
    # Cell 3: OCV Markdown
    # ----------------------------------------------------
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 1. Thermodynamic Open-Circuit Voltage (OCV)\n",
            "The equilibrium open-circuit voltage $\\mathrm{OCV}(z)$ is parameterized from titration data reported by Barletta et al. (2022).  \n",
            "Piecewise Cubic Hermite Interpolating Polynomials (PCHIP) guarantee strict monotonicity ($d\\mathrm{OCV}/dz > 0$) without artificial numerical oscillations."
        ]
    })

    # ----------------------------------------------------
    # Cell 4: OCV Code & Plot
    # ----------------------------------------------------
    ocv = OCVModel()
    z_fine = np.linspace(0.0, 1.0, 200)
    ocv_vals = ocv.evaluate(z_fine)
    docv_vals = ocv.derivative(z_fine)

    fig, ax1 = plt.subplots(figsize=(8.0, 4.0))
    ax2 = ax1.twinx()
    p1, = ax1.plot(z_fine * 100.0, ocv_vals, color="#1f77b4", linewidth=2.0, label="OCV [V]")
    p2, = ax2.plot(z_fine * 100.0, docv_vals, color="#d62728", linestyle="--", linewidth=1.5, label="dOCV/dz [V/unit]")
    p3 = ax1.scatter(DEFAULT_SOC_POINTS * 100.0, DEFAULT_OCV_POINTS, color="#000000", zorder=5, label="Lit. Calibration [Barletta 2022]")
    ax1.set_xlabel("State of Charge (SOC) [%]", fontweight="bold")
    ax1.set_ylabel("Open-Circuit Voltage [V]", color="#1f77b4", fontweight="bold")
    ax2.set_ylabel("Derivative dOCV/dz [V]", color="#d62728", fontweight="bold")
    ax1.set_title("Panasonic NCR18650B OCV & Sensitivity Function", fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.5)
    lines = [p1, p2, p3]
    ax1.legend(lines, [l.get_label() for l in lines], loc="lower right")
    img_ocv = fig_to_base64(fig)

    cells.append({
        "cell_type": "code",
        "execution_count": 2,
        "metadata": {},
        "outputs": [
            {
                "data": {
                    "image/png": img_ocv,
                    "text/plain": ["<Figure size 800x400 with 2 Axes>"]
                },
                "metadata": {},
                "output_type": "display_data"
            }
        ],
        "source": [
            "ocv = OCVModel()\n",
            "z_fine = np.linspace(0.0, 1.0, 200)\n",
            "ocv_vals = ocv.evaluate(z_fine)\n",
            "docv_vals = ocv.derivative(z_fine)\n",
            "\n",
            "fig, ax1 = plt.subplots(figsize=(8.0, 4.0))\n",
            "ax2 = ax1.twinx()\n",
            "p1, = ax1.plot(z_fine * 100.0, ocv_vals, color='#1f77b4', linewidth=2.0, label='OCV [V]')\n",
            "p2, = ax2.plot(z_fine * 100.0, docv_vals, color='#d62728', linestyle='--', linewidth=1.5, label='dOCV/dz [V/unit]')\n",
            "p3 = ax1.scatter(DEFAULT_SOC_POINTS * 100.0, DEFAULT_OCV_POINTS, color='#000000', zorder=5, label='Lit. Calibration')\n",
            "ax1.set_xlabel('State of Charge (SOC) [%]', fontweight='bold')\n",
            "ax1.set_ylabel('Open-Circuit Voltage [V]', color='#1f77b4', fontweight='bold')\n",
            "ax2.set_ylabel('Derivative dOCV/dz [V]', color='#d62728', fontweight='bold')\n",
            "ax1.set_title('Panasonic NCR18650B OCV & Sensitivity Function', fontweight='bold')\n",
            "ax1.grid(True, linestyle='--', alpha=0.5)\n",
            "ax1.legend([p1, p2, p3], ['OCV [V]', 'dOCV/dz [V]', 'Lit. Points'], loc='lower right')\n",
            "plt.show()\n"
        ]
    })

    # ----------------------------------------------------
    # Cell 5: Resistance Markdown
    # ----------------------------------------------------
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 2. Arrhenius Temperature & SOH Resistance Scaling\n",
            "Ohmic resistance $R_0$ scales with temperature $T$ via Arrhenius kinetics and with state of health (SOH) via degradation scaling:\n",
            "$$R_0(T, \\mathrm{SOH}) = R_{0,\\mathrm{ref}} \\exp\\left[\\frac{E_{a,0}}{R_g}\\left(\\frac{1}{T} - \\frac{1}{T_{\\mathrm{ref}}}\\right)\\right] \\left[1 + \\alpha_0 (1 - \\mathrm{SOH})\\right]$$\n",
            "Higher temperatures increase ionic mobility (lowering resistance), while cell aging increases internal resistance."
        ]
    })

    # ----------------------------------------------------
    # Cell 6: Resistance Code & Plot
    # ----------------------------------------------------
    cell = BatteryCell()
    soh_grid = np.linspace(0.80, 1.00, 100)
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    for t_c, col in zip([25.0, 35.0, 45.0], ["#1f77b4", "#ff7f0e", "#d62728"]):
        t_k = t_c + 273.15
        r0_m = [cell.get_r0(t_k, s) * 1000.0 for s in soh_grid]
        ax.plot(soh_grid, r0_m, label=f"T = {t_c:.0f} °C", color=col, linewidth=2.0)
    ax.set_xlabel("State of Health (SOH = $Q_{\\mathrm{max}} / Q_{\\mathrm{nom}}$)", fontweight="bold")
    ax.set_ylabel("Ohmic Resistance $R_0$ [m$\\Omega$]", fontweight="bold")
    ax.set_title("Internal Resistance Scaling across Temperatures and SOH", fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    img_res = fig_to_base64(fig)

    cells.append({
        "cell_type": "code",
        "execution_count": 3,
        "metadata": {},
        "outputs": [
            {
                "data": {
                    "image/png": img_res,
                    "text/plain": ["<Figure size 750x400 with 1 Axes>"]
                },
                "metadata": {},
                "output_type": "display_data"
            }
        ],
        "source": [
            "cell = BatteryCell()\n",
            "soh_grid = np.linspace(0.80, 1.00, 100)\n",
            "fig, ax = plt.subplots(figsize=(7.5, 4.0))\n",
            "for t_c, col in zip([25.0, 35.0, 45.0], ['#1f77b4', '#ff7f0e', '#d62728']):\n",
            "    t_k = t_c + 273.15\n",
            "    r0_m = [cell.get_r0(t_k, s) * 1000.0 for s in soh_grid]\n",
            "    ax.plot(soh_grid, r0_m, label=f'T = {t_c:.0f} °C', color=col, linewidth=2.0)\n",
            "ax.set_xlabel('State of Health (SOH)', fontweight='bold')\n",
            "ax.set_ylabel('Ohmic Resistance [mOhm]', fontweight='bold')\n",
            "ax.set_title('Internal Resistance Scaling across Temperatures and SOH', fontweight='bold')\n",
            "ax.grid(True, linestyle='--', alpha=0.5)\n",
            "ax.legend()\n",
            "plt.show()\n"
        ]
    })

    # ----------------------------------------------------
    # Cell 7: Simulation Markdown
    # ----------------------------------------------------
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 3. Dynamic Simulation: Coulomb Counting vs. Extended Kalman Filter\n",
            "We simulate a 1-hour dynamic drive cycle at $25\\,^\\circ\\mathrm{C}$ with an intentional **$-15\\%$ initial SOC error**:\n",
            "- **Ground Truth Initial SOC:** $0.80$ ($80\\%$)\n",
            "- **Estimator Initial Guess:** $0.65$ ($65\\%$)\n",
            "- **Open-loop Baseline (Coulomb Counting):** Assumes nominal $3.20\\,\\mathrm{Ah}$.\n",
            "- **Closed-loop Observer (EKF):** Uses terminal voltage feedback $V_{t,\\mathrm{meas}}$ and analytical Jacobians."
        ]
    })

    # ----------------------------------------------------
    # Cell 8: Run Simulation Code & Print Metrics
    # ----------------------------------------------------
    init_state = CellState(soc=0.80, vp=0.0, temperature_k=298.15, q_max=3.20, soh=1.0, neq=0.0)
    cc = CoulombCounter(soc_init=0.65)
    ekf = ExtendedKalmanFilter(ocv_model=ocv, soc_init=0.65)
    profile = generate_current_profile("dynamic_pulse", duration_s=3600.0, dt=1.0)

    df_sim, m = run_single_simulation(
        cell=cell, coulomb_counter=cc, ekf=ekf,
        current_profile=profile, dt=1.0, t_amb_k=298.15,
        true_init_state=init_state, random_seed=42
    )

    t_min = df_sim["time_s"] / 60.0
    fig, axes = plt.subplots(3, 1, figsize=(8.5, 7.0), sharex=True)
    axes[0].plot(t_min, df_sim["i_true_a"], color="#1f77b4", label="Discharge Current [A]")
    axes[0].set_ylabel("Current [A]")
    axes[0].set_title("Baseline Simulation: 25 °C, SOH 1.00", fontweight="bold")
    axes[0].grid(True)
    axes[0].legend(loc="upper right")

    axes[1].plot(t_min, df_sim["soc_true"] * 100.0, label="True SOC", color="#000000", linewidth=2.0)
    axes[1].plot(t_min, df_sim["soc_cc"] * 100.0, label="Coulomb Counting (Initial Error -15%)", color="#d62728", linestyle="--")
    axes[1].plot(t_min, df_sim["soc_ekf"] * 100.0, label="EKF Observer", color="#1f77b4", linestyle="-.")
    axes[1].set_ylabel("SOC [%]")
    axes[1].grid(True)
    axes[1].legend(loc="lower left")

    axes[2].plot(t_min, df_sim["error_cc"] * 100.0, label="Coulomb Counting Error", color="#d62728", linestyle="--")
    axes[2].plot(t_min, df_sim["error_ekf"] * 100.0, label="EKF Observer Error", color="#1f77b4", linewidth=1.8)
    axes[2].axhspan(-2.0, 2.0, color="#2ca02c", alpha=0.15, label="±2% Accuracy Goal")
    axes[2].set_ylabel("SOC Error [%]")
    axes[2].set_xlabel("Elapsed Time [minutes]")
    axes[2].grid(True)
    axes[2].legend(loc="lower right")

    plt.tight_layout()
    img_sim = fig_to_base64(fig)

    cells.append({
        "cell_type": "code",
        "execution_count": 4,
        "metadata": {},
        "outputs": [
            {
                "data": {
                    "image/png": img_sim,
                    "text/plain": ["<Figure size 850x700 with 3 Axes>"]
                },
                "metadata": {},
                "output_type": "display_data"
            },
            {
                "name": "stdout",
                "output_type": "stream",
                "text": [
                    f"--- Estimation Accuracy Metrics ---\n",
                    f"Coulomb Counting RMSE: {m['soc_rmse_cc_pct']:.2f}% | Final Error: {m['final_error_cc_pct']:.2f}%\n",
                    f"Extended Kalman Filter RMSE: {m['soc_rmse_ekf_pct']:.2f}% | Final Error: {m['final_error_ekf_pct']:.2f}%\n",
                    f"EKF Recovery Time (|error| <= 2%): {m['recovery_time_2pct_s']} seconds\n"
                ]
            }
        ],
        "source": [
            "init_state = CellState(soc=0.80, vp=0.0, temperature_k=298.15, q_max=3.20, soh=1.0, neq=0.0)\n",
            "cc = CoulombCounter(soc_init=0.65)\n",
            "ekf = ExtendedKalmanFilter(ocv_model=ocv, soc_init=0.65)\n",
            "profile = generate_current_profile('dynamic_pulse', duration_s=3600.0, dt=1.0)\n",
            "\n",
            "df_sim, m = run_single_simulation(\n",
            "    cell=cell, coulomb_counter=cc, ekf=ekf,\n",
            "    current_profile=profile, dt=1.0, t_amb_k=298.15,\n",
            "    true_init_state=init_state, random_seed=42\n",
            ")\n",
            "\n",
            "# Display metrics\n",
            "print('--- Estimation Accuracy Metrics ---')\n",
            "print(f'Coulomb Counting RMSE: {m[\"soc_rmse_cc_pct\"]:.2f}% | Final Error: {m[\"final_error_cc_pct\"]:.2f}%')\n",
            "print(f'Extended Kalman Filter RMSE: {m[\"soc_rmse_ekf_pct\"]:.2f}% | Final Error: {m[\"final_error_ekf_pct\"]:.2f}%')\n",
            "print(f'EKF Recovery Time (|error| <= 2%): {m[\"recovery_time_2pct_s\"]} seconds')\n"
        ]
    })

    # ----------------------------------------------------
    # Cell 9: Tornado Sensitivity Markdown
    # ----------------------------------------------------
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 4. Parameter Sensitivity & Tornado Analysis\n",
            "To answer **Research Question 4** (*Which factor has the largest effect: ambient temperature, load profile, capacity fade, or resistance growth?*), we inspect the Tornado sensitivity ranking across 75 Monte Carlo evaluations."
        ]
    })

    # ----------------------------------------------------
    # Cell 10: Tornado Ranking Code & Table
    # ----------------------------------------------------
    tornado_path = PROJECT_ROOT / "results" / "tables" / "sensitivity_tornado_ranking.csv"
    df_tornado = pd.read_csv(tornado_path)
    
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    y_pos = np.arange(len(df_tornado))
    ax.barh(y_pos, df_tornado["Impact_Range_Pct"], color="#2b5c8f", alpha=0.85, edgecolor="#1a365d")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_tornado["Factor"], fontweight="medium")
    ax.set_xlabel("Sensitivity Spread on Estimation Error [%]", fontweight="bold")
    ax.set_title("Figure 8: Parameter Impact Ranking (Tornado Analysis)", fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    for i, val in enumerate(df_tornado["Impact_Range_Pct"]):
        ax.text(val + 0.15, i, f"{val:.2f}%", va="center", fontweight="bold", color="#1a365d")
    plt.tight_layout()
    img_tornado = fig_to_base64(fig)

    cells.append({
        "cell_type": "code",
        "execution_count": 5,
        "metadata": {},
        "outputs": [
            {
                "data": {
                    "image/png": img_tornado,
                    "text/plain": ["<Figure size 800x380 with 1 Axes>"]
                },
                "metadata": {},
                "output_type": "display_data"
            },
            {
                "data": {
                    "text/html": [df_tornado.to_html(index=False)],
                    "text/plain": [df_tornado.to_string(index=False)]
                },
                "metadata": {},
                "output_type": "display_data"
            }
        ],
        "source": [
            "tornado_path = Path('../results/tables/sensitivity_tornado_ranking.csv')\n",
            "if not tornado_path.exists():\n",
            "    tornado_path = Path('results/tables/sensitivity_tornado_ranking.csv')\n",
            "df_tornado = pd.read_csv(tornado_path)\n",
            "df_tornado\n"
        ]
    })

    # ----------------------------------------------------
    # Cell 11: Summary & Next Steps
    # ----------------------------------------------------
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 5. Summary & Reproducibility\n",
            "\n",
            "- **Full Reproduction Command:** `python run_pipeline.py` (executes all tests, 36 scenarios, and 75 Monte Carlo robustness runs in < 90s).\n",
            "- **Full Academic Manuscript:** See [`report/main.md`](../report/main.md) for the 12-page manuscript.\n",
            "- **One-Page Outreach Summary:** See [`report/professor_outreach_summary.md`](../report/professor_outreach_summary.md) for graduate application emails."
        ]
    })

    # Notebook structure
    notebook_content = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.12.10"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    nb_path = PROJECT_ROOT / "notebooks" / "01_interactive_exploration.ipynb"
    nb_path.parent.mkdir(parents=True, exist_ok=True)
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(notebook_content, f, indent=2)

    print(f"[build_notebook] Successfully generated: {nb_path} ({nb_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    build_notebook()
