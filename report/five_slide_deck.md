# Presentation Deck: Physics-Informed Battery State Estimation

---

## Slide 1: Title & Motivation

### Physics-Informed Estimation of Lithium-Ion Battery SOC and Degradation Under Elevated Ambient Temperatures
*An Independent Computational Energy Systems Study for Graduate Research*

* **The Core Challenge:** Accurate State of Charge (SOC) estimation is critical for battery safety and life, but unobservable directly. Open-loop Coulomb counting drifts under capacity degradation, sensor bias, and initial error.
* **Environmental Complexity:** Elevated ambient temperatures ($25\,^\circ\text{C}$ to $45\,^\circ\text{C}$) alter electrolyte kinetics (Arrhenius resistance reduction) while accelerating long-term capacity fade.
* **Research Focus:** Within a transparent, disclosed electrothermal model, quantify estimator sensitivity across 36 automated scenario combinations and 75 Monte Carlo robustness evaluations.

---

## Slide 2: Mathematical Framework & Coupled Physics

### 1-RC Thévenin Model Coupled to Lumped Thermal ODE
* **Electrical Dynamics:**
  $$V_t = \text{OCV}(z) - I R_0(T, \text{SOH}) - v_p$$
  $$\frac{dv_p}{dt} = -\frac{v_p}{R_1 C_1} + \frac{I}{C_1}, \quad \frac{dz}{dt} = -\frac{\eta I}{3600 Q_{\max}}$$
* **Arrhenius Resistance Scaling:**
  $$R_j(T, \text{SOH}) = R_{j,\text{ref}} \exp\left[\frac{E_{a,j}}{R_g}\left(\frac{1}{T} - \frac{1}{T_{\text{ref}}}\right)\right][1 + \alpha_j(1 - \text{SOH})]$$
* **Lumped Thermal ODE:**
  $$C_{\text{th}} \frac{dT}{dt} = Q_{\text{gen}} - hA(T - T_{\text{amb}}), \quad Q_{\text{gen}} = I^2 R_0 + I v_p$$
* **Observer Design:** Discrete Extended Kalman Filter (EKF) tracking $[z, v_p]^T$ via analytical Jacobians and Joseph-stabilized covariance updates.

---

## Slide 3: Verification & Invariant Testing

### Strict Verification and Deterministic Reproducibility
* **Unit Testing (100% Pass):**
  * Zero-current relaxation: $v_p$ decays to zero ($5\tau_1 = 300\,\text{s}$), SOC remains constant to $10^{-12}$.
  * Analytical discharge: simulated drawdown matches theoretical slope with zero error ($< 10^{-9}$).
  * OCV Monotonicity: PCHIP spline interpolation ensures $d\text{OCV}/dz > 0$ across all $z \in [0, 1]$.
  * Joseph Covariance Stabilizer: guarantees symmetry and positive semi-definiteness ($P = P^T, \lambda_i \ge 0$).
* **Numerical Convergence:** Standard $\Delta t = 1.0\,\text{s}$ vs fine $\Delta t = 0.5\,\text{s}$ yields $< 0.01\%$ relative deviation in energy and peak temperature.

---

## Slide 4: Quantitative Results & Scenario Analysis

### Extended Kalman Filter Outperforms Coulomb Counting Across Matrix
* **Baseline Error Recovery:** Under $-15\%$ initial SOC error, EKF converges to within $\pm 0.02\%$ in $< 5\,\text{s}$ (RMSE: $0.34\%$), whereas Coulomb counting retains $-15.00\%$ permanent offset.
* **Degradation Sensitivity ($\text{SOH} = 0.80$):** As available capacity shrinks to $2.56\,\text{Ah}$, nominal Coulomb counting accumulates catastrophic errors (final error $+6.25\%$), whereas EKF maintains $\text{RMSE} < 0.55\%$.
* **Thermal Modulation:** Elevated temperature decreases internal resistance ($42\,\text{m}\Omega \to 26\,\text{m}\Omega$), reducing overpotentials and improving EKF tracking fidelity ($0.34\% \to 0.17\%$ RMSE).
* **Tornado Ranking:** Initial state offset ($10.02\%$) and capacity fade ($4.77\%$) dominate estimation error, while ambient temperature ($0.25\%$) and load dynamics ($0.15\%$) play secondary roles.

---

## Slide 5: Graduate Research Roadmap & Next Steps

### Transitioning from Computational Models to Experimental Validation
* **Model Limitations Disclosed:** Single-node thermal model (assumes negligible Biot number); empirical aging surrogate; simulation evidence based on literature parameters (Barletta et al. 2022).
* **Proposed Experimental Extension:**
  1. Parameterize 2-RC electrothermal models via environmental chamber HPPC & EIS testing at $25\,^\circ\text{C}, 35\,^\circ\text{C}, 45\,^\circ\text{C}$.
  2. Implement physics-based reduced-order models (SPMe / DFN) for internal lithium concentration tracking.
  3. Deploy and benchmark real-time observer algorithms on embedded automotive microcontrollers (ARM Cortex-M).
