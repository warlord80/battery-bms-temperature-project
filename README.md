# Physics-Informed Estimation of Lithium-Ion Battery State of Charge and Degradation Under Elevated Ambient Temperatures

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Tests: Passing](https://img.shields.io/badge/Tests-9%2F9%20Passing-success.svg)](tests/)
[![Report: PDF](https://img.shields.io/badge/Report-PDF%20(2.3MB)-red.svg)](report/main.pdf)
[![Summary: 1--Page%20PDF](https://img.shields.io/badge/Summary-1--Page%20PDF-orange.svg)](report/professor_outreach_summary.pdf)

An independent computational research repository investigating electrothermal dynamics, degradation surrogates, and state-of-charge (SOC) estimation fidelity in lithium-ion battery management systems (BMS).

> **Core Research Claim:**  
> This work develops a reduced-order electrothermal and aging-aware equivalent-circuit model for controlled sensitivity analysis of battery SOC estimation. It demonstrates behaviour under stated assumptions; it does not identify parameters from new experiments or establish a chemistry-independent degradation law.

---

## 🚀 Quickstart & One-Command Reproduction

The entire research pipeline—from unit verification to baseline simulations, 36 core scenario evaluations, 75 multi-seed Monte Carlo robustness sweeps, and master figure compilation—runs deterministically with a single command:

```bash
# Clone the repository
git clone https://github.com/warlord80/battery-bms-temperature-project.git
cd battery-bms-temperature-project

# Install dependencies (or use environment.yml)
pip install -r requirements.txt

# Run the master automated pipeline (~60-90 seconds)
python run_pipeline.py
```

> 💡 **Interactive Exploration:** You can also view the pre-computed interactive notebook directly on GitHub: [**`notebooks/01_interactive_exploration.ipynb`**](https://github.com/warlord80/battery-bms-temperature-project/blob/main/notebooks/01_interactive_exploration.ipynb).

To run individual modular milestones:
```bash
python run_tests.py              # Executes isolated 9-test unit suite
python scripts/01_prepare_data.py # Validates parameter tables & OCV lookup
python scripts/02_run_baseline.py # Runs baseline simulation & time-step checks
python scripts/03_run_scenarios.py# Automates 36 core factorial comparisons
python scripts/04_run_robustness.py # Executes 5-factor Monte Carlo sweeps
python scripts/05_make_figures.py # Compiles all 8 publication figures
```

---

## 🔬 Scientific & Physical Framework

This project investigates a commercial cylindrical cell (standard **Panasonic NCR18650B**, rated $3.20\,\text{Ah}$ NCA/Graphite) via a coupled multi-physics reduced-order model:

1. **Electrical Dynamics (1-RC Thévenin ECM):**
   $$V_t = \text{OCV}(z) - I R_0(T, \text{SOH}) - v_p$$
   $$\frac{dv_p}{dt} = -\frac{v_p}{R_1 C_1} + \frac{I}{C_1}, \quad \frac{dz}{dt} = -\frac{\eta I}{3600 Q_{\max}}$$
   *Sign convention:* Positive current ($I > 0$) indicates discharge.
2. **Arrhenius Temperature & SOH Resistance Scaling:**
   $$R_j(T, \text{SOH}) = R_{j,\text{ref}} \exp\left[ \frac{E_{a,j}}{R_g} \left( \frac{1}{T} - \frac{1}{T_{\text{ref}}} \right) \right] \left[ 1 + \alpha_j (1 - \text{SOH}) \right] \quad (j \in \{0, 1\})$$
3. **Lumped Single-Node Thermal ODE:**
   $$C_{\text{th}} \frac{dT}{dt} = Q_{\text{gen}} - hA(T - T_{\text{amb}}), \quad Q_{\text{gen}} = I^2 R_0 + I v_p$$
   Enforces non-negative irreversible dissipation ($Q_{\text{gen}} \ge 0$).
4. **Closed-Loop State Estimation (EKF):**
   Tracks state vector $\mathbf{x} = [z, v_p]^T$ via analytical process/measurement Jacobians and the Joseph-stabilized covariance formulation ($\mathbf{P}_{k|k}$) for guaranteed positive semi-definiteness.

---

## 📊 Summary of Key Findings

| Operating Condition | Coulomb Counting (Open-Loop) | Extended Kalman Filter (Closed-Loop) | Key Mechanism |
|---|---|---|---|
| **Baseline (25 °C, SOH 1.0, Dynamic)** | $\text{RMSE} = 15.00\%$, Final err $= -15.00\%$ | **$\text{RMSE} = 0.34\%$**, Final err $= +0.00\%$ | EKF eliminates $-15\%$ initial offset in $< 5\,\text{s}$. |
| **Degraded Cell (25 °C, SOH 0.80)** | Severe divergence (final err $= +6.25\%$) | **$\text{RMSE} = 0.53\%$**, Final err $= +0.00\%$ | CC over-predicts charge because true capacity shrunk. |
| **Elevated Temp (45 °C, SOH 1.0)** | $\text{RMSE} = 15.00\%$ (unaltered) | **$\text{RMSE} = 0.17\%$** (superior tracking) | Lower internal resistance reduces overpotential error. |
| **Current Bias (+1.0%)** | Continuous drift ($+0.50\%$ SOC/hr) | **$< 0.05\%$** residual error | Voltage innovation cancels systematic sensor drift. |

### Sensitivity Tornado Ranking
1. **Initial State Offset ($\pm 20\%$):** Impact $= 10.02\%$ (Dominant factor)
2. **Capacity Fade ($\text{SOH}: 1.0 \to 0.8$):** Impact $= 4.77\%$ (Severe for open-loop)
3. **Current Sensor Bias ($\pm 1\%$):** Impact $= 0.50\%$ (Accumulates linearly)
4. **Ambient Temperature ($25 \to 45\,^\circ\text{C}$):** Impact $= 0.25\%$ (Thermal modulation)
5. **Load Dynamics (Steady vs Pulse):** Impact $= 0.15\%$ (Transient modulation)

---

## 📁 Repository Structure

```text
battery-bms-temperature-project/
├── LICENSE                         # MIT License
├── README.md                       # Master project overview & reproduction guide
├── environment.yml                 # Conda virtual environment specification
├── pyproject.toml                  # Python package & pytest configuration
├── run_pipeline.py                 # Single-command end-to-end research orchestrator
├── run_tests.py                    # Isolated unit test runner
├── data/
│   ├── DATA_CARD.md                # Full provenance & cell specification data card
│   ├── raw/                        # Reference OCV lookup tables
│   └── processed/
│       └── parameter_table.csv     # Provenance table (sourced vs. assumptions)
├── configs/
│   ├── baseline.yaml               # Baseline simulation parameters
│   ├── scenarios.yaml              # Core 36-scenario & robustness settings
│   └── estimator_tuning.yaml       # EKF covariance tuning & boundary limits
├── src/
│   ├── model.py                    # Coupled electrothermal 1-RC ECM
│   ├── ocv.py                      # Strictly monotonic PCHIP OCV interpolation
│   ├── estimators.py               # Coulomb Counter & Joseph-stabilized EKF
│   ├── simulation.py               # Drive cycle generation & simulation engine
│   └── plotting.py                 # Master publication figure formatting
├── scripts/
│   ├── 01_prepare_data.py          # Data validation script
│   ├── 02_run_baseline.py          # Baseline simulation & time-step convergence
│   ├── 03_run_scenarios.py         # Automated core 36-scenario matrix
│   ├── 04_run_robustness.py        # 75-run Monte Carlo robustness & sensitivity
│   └── 05_make_figures.py          # Visual compilation & verification
├── tests/
│   ├── test_model.py               # Zero-current relaxation & charge conservation
│   ├── test_estimators.py          # Covariance symmetry & EKF convergence
│   └── test_units_and_bounds.py    # Physical boundaries & non-negative heat
├── results/
│   ├── tables/                     # Baseline, core matrix, & robustness CSV tables
│   └── figures/                    # 8 publication-grade high-resolution figures
└── report/
    ├── main.md                     # Comprehensive 12-page academic report
    ├── references.bib              # Verified BibTeX bibliography
    ├── professor_outreach_summary.md # 1-page outreach summary for faculty emails
    └── five_slide_deck.md          # 5-slide project summary presentation
```

---

## 📈 Publication Figures (in `results/figures/`)

* **Figure 1:** `fig1_model_schematic.png` — Coupled electrothermal model and observer architecture block diagram.
* **Figure 2:** `fig2_ocv_and_resistance.png` — Sourced OCV(z) curve, analytical derivative, and Arrhenius resistance scaling.
* **Figure 3:** `fig3_baseline_timeseries.png` — Aligned baseline current, terminal voltage, true vs. estimated SOC, and temperature.
* **Figure 4:** `fig4_error_dynamics.png` — SOC estimation error dynamics comparing Coulomb counting against the EKF observer.
* **Figure 5:** `fig5_temperature_soh_heatmap.png` — Factorial Temperature $\times$ SOH heatmap of estimation RMSE.
* **Figure 6:** `fig6_aging_surrogate.png` — Available capacity fade and resistance growth trajectories over 1000 equivalent cycles.
* **Figure 7:** `fig7_robustness_errorbars.png` — Multi-seed Monte Carlo robustness analysis across four disturbance factors.
* **Figure 8:** `fig8_sensitivity_tornado.png` — Parameter sensitivity and impact ranking (Tornado diagram).

---

## ⚖️ Scientific Integrity & Reproducibility Statement

* **Simulation Evidence:** All data are generated from deterministic computational simulations. Outputs are never labeled as measured laboratory or field data.
* **Parameter Provenance:** Every electrical and thermal parameter is cited from peer-reviewed literature (Barletta et al. 2022; Mehta & Gupta 2024; Mattia et al. 2025). Transparent scenario assumptions are explicitly flagged in `parameter_table.csv` and tested for sensitivity.
* **Unit Testing:** 9 automated tests verify physical invariants (mass/charge conservation, exponential relaxation, covariance positive definiteness) before results are produced.

---

## 📜 Citation

If you use or reference this codebase in your research or applications, please cite:

```bibtex
@software{battery_bms_temperature_2026,
  author = {Computational Battery Lab},
  title = {Physics-informed estimation of lithium-ion battery state of charge and degradation under elevated ambient temperatures},
  year = {2026},
  url = {https://github.com/warlord80/battery-bms-temperature-project}
}
```
