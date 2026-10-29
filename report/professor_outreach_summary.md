# Research Summary: Physics-Informed Battery State Estimation Under Temperature & Aging

**Candidate:** Independent Graduate Applicant  
**Target Disciplines:** Applied Physics | Energy Systems | Computational Engineering | Control Systems  
**Project Repository:** `battery-bms-temperature-project` (Fully reproducible Python research codebase)

---

### Executive Statement

> *"I independently developed a reproducible computational study of lithium-ion battery state-of-charge (SOC) estimation under coupled thermal and degradation scenarios. Using a 1-RC Thévenin equivalent-circuit model coupled to a lumped single-node thermal ODE, I compared open-loop Coulomb counting against a closed-loop Extended Kalman Filter (EKF) across 36 automated scenarios and 75 multi-seed Monte Carlo robustness runs. The study showed that while Coulomb counting accumulates severe drift (RMSE up to $15.01\%$) under capacity fade and sensor bias, the EKF observer maintains RMSE below $0.89\%$ across all operating conditions and converges within 5 seconds under $-15\%$ initial state error. Tornado sensitivity analysis revealed that initial state uncertainty ($\pm 20\%$) and capacity fade ($\text{SOH} = 0.80$) dominate estimation drift, while elevated temperature ($25\,^\circ\text{C}$ to $45\,^\circ\text{C}$) primarily modulates internal ohmic overpotentials via Arrhenius kinetics. I am eager to extend this foundation through experimental parameter identification (HPPC/EIS) and embedded BMS hardware-in-the-loop validation in a graduate energy storage research group."*

---

### Core Quantitative Findings

| Research Dimension | Coulomb Counting Baseline | Extended Kalman Filter (EKF) | Physical Takeaway |
|---|---|---|---|
| **Baseline Tracking (25 °C, SOH 1.0)** | $\text{RMSE} = 15.00\%$, Final error $= -15.00\%$ | **$\text{RMSE} = 0.34\%$**, Final error $= +0.00\%$ | EKF eliminates initial $-15\%$ SOC error in $< 5\,\text{s}$ via voltage feedback. |
| **Aging Impact (SOH = 0.80)** | Severe divergence (final error swings to $+6.25\%$) | **$\text{RMSE} = 0.53\%$**, Final error $= +0.00\%$ | Open-loop integration over-predicts remaining energy as true capacity fades. |
| **Elevated Temp (45 °C)** | $\text{RMSE} = 15.00\%$ (unaltered) | **$\text{RMSE} = 0.17\%$** (superior tracking) | Lower internal resistance ($R_0$) tightens terminal coupling to the true OCV curve. |
| **Current Sensor Bias (+1.0%)** | Constant drift of $+0.50\%$ SOC/hr | **$< 0.05\%$** residual error | EKF innovation updates continuously counter systematic current sensor drift. |

---

### Methodology & Technical Rigor

* **Physical Governing Models:** First-order (1-RC) Thévenin ECM coupled to a single-node lumped thermal model ($C_{\text{th}} \frac{dT}{dt} = Q_{\text{gen}} - hA(T - T_{\text{amb}})$) with Arrhenius-governed internal resistance scaling and empirical capacity fade surrogates.
* **Cell Chemistry Provenance:** Parameterized for a commercial Panasonic NCR18650B ($3.2\,\text{Ah}$ NCA/Graphite cell) sourced from peer-reviewed literature (Barletta et al., *Energies* 2022; Mehta & Gupta, *RSER* 2024).
* **Closed-Loop Observer Design:** Discrete Extended Kalman Filter tracking state vector $\mathbf{x} = [z, v_p]^T$ utilizing exact analytical Jacobians and the Joseph-stabilized covariance formulation ($\mathbf{P}_{k|k}$) for numerical positive semi-definiteness.
* **Testing & Verification:** Comprehensive unit test suite (`pytest`) verifying zero-current relaxation kinetics ($\tau_1 = 60\,\text{s}$), analytical charge conservation, OCV strict monotonicity, and time-step convergence ($\Delta t = 1.0\,\text{s}$ vs. $0.5\,\text{s}$ yielding $< 0.01\%$ variance).
* **Reproducibility:** Single-command execution pipeline (`python run_pipeline.py`) reproducing all 36 core scenarios, 75 robustness evaluations, and 8 publication figures in under 90 seconds.

---

### Prospective Graduate Research Alignment

Having demonstrated end-to-end computational modeling, algorithmic observer design, and sensitivity analysis, I am seeking graduate research opportunities focused on:
1. **Electrochemical Modeling:** Advancing from equivalent circuits to Doyle–Fuller–Newman (DFN) and reduced-order physics models (SPMe) for internal lithium concentration tracking.
2. **Experimental Characterization:** Conducting environmental chamber cycling, HPPC, and electrochemical impedance spectroscopy (EIS) to parameterize degradation kinetics.
3. **Advanced Battery Management (BMS):** Developing embedded state-of-health (SOH), state-of-power (SOP), and thermal runaway prediction algorithms for next-generation electric vehicle powertrains.

*Full code, datasets, test logs, and 12-page research report available at repository root.*
