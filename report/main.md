# Physics-Informed Estimation of Lithium-Ion Battery State of Charge and Degradation Under Elevated Ambient Temperatures

**Author:** Independent Computational Research Project  
**Affiliation:** Computational Energy Systems & Applied Physics  
**Date:** October 2026  
**Repository:** `battery-bms-temperature-project`

---

## Abstract

Accurate state-of-charge (SOC) estimation in lithium-ion battery management systems (BMS) is essential for operational safety, cycle life preservation, and energy utilization. However, elevated ambient operating temperatures and progressive capacity/resistance degradation introduce non-negligible model parametric uncertainties and sensor drift that degrade open-loop Coulomb counting. This work develops a reduced-order electrothermal and aging-aware equivalent-circuit model for controlled sensitivity analysis of battery SOC estimation. It demonstrates behaviour under stated assumptions; it does not identify parameters from new experiments or establish a chemistry-independent degradation law. 

A first-order (1-RC) Thévenin equivalent circuit model (ECM) is coupled to a lumped single-node thermal differential equation with Arrhenius-governed resistance dynamics and empirical capacity fade surrogates parameterized for a commercial Panasonic NCR18650B (3.2 Ah) NCA/Graphite cell. Across a fully factorial $3 \times 3 \times 2 \times 2 = 36$-scenario matrix spanning ambient temperatures ($25\,^\circ\text{C}, 35\,^\circ\text{C}, 45\,^\circ\text{C}$), state-of-health levels ($\text{SOH} = 1.00, 0.90, 0.80$), and load profiles (steady discharge vs. dynamic pulse cycles), an Extended Kalman Filter (EKF) observer is evaluated against nominal Coulomb counting. 

Results demonstrate that while Coulomb counting accumulates severe root-mean-square errors (RMSE up to $15.01\%$) due to unmodeled capacity loss, sensor bias, and initial state offsets, the physics-informed EKF maintains root-mean-square errors below $0.89\%$ across all scenarios, achieving an average RMSE of $0.38\%$ and converging within 5 seconds under a $-15\%$ initial state offset. Tornado sensitivity analysis reveals that initial state uncertainty ($\pm 20\%$) and capacity fade ($\text{SOH} = 0.80$) dominate estimation drift, whereas ambient thermal elevation primarily modulates internal ohmic dissipation ($28.1\,^\circ\text{C}$ to $47.2\,^\circ\text{C}$). Limitations inherent to lumped single-node approximations and empirical degradation laws are discussed alongside prospective laboratory validation protocols.

---

## 1. Introduction

Lithium-ion energy storage systems represent the foundation of modern electrified transportation and stationary grid storage. Within battery management systems (BMS), real-time estimation of internal states—predominantly the State of Charge (SOC, $z \in [0, 1]$) and State of Health (SOH)—is vital for state prediction, thermal runaway prevention, and charging regulation (Plett 2004; Mehta & Gupta 2024). Unlike voltage and temperature, SOC cannot be measured directly with physical sensors; it must be inferred from observable terminal metrics, namely terminal voltage ($V_t$), applied current ($I$), and surface temperature ($T$).

In commercial applications, open-loop current integration (Coulomb counting) serves as the traditional baseline due to its computational simplicity. However, Coulomb counting suffers from fundamental vulnerabilities:
1. Susceptibility to unmodeled initial state offsets ($\hat{z}_0 \neq z_0$);
2. Systematic drift driven by current sensor measurement bias and precision noise;
3. Divergence when true cell capacity fades due to cycling or aging ($Q_{\max} < Q_{\text{nom}}$), while the estimator relies on the factory nameplate rating ($Q_{\text{nom}}$).

These challenges are exacerbated in harsh environmental operating conditions, particularly elevated ambient temperatures ($35\,^\circ\text{C}$ to $45\,^\circ\text{C}$). Thermal excitation enhances solid-state diffusion and reaction kinetics (reducing internal resistance via Arrhenius relationships), but simultaneously accelerates chemical degradation mechanisms such as solid electrolyte interphase (SEI) growth, transition metal dissolution, and irreversible lithium inventory loss (Mattia et al. 2025; Sun et al. 2026).

### 1.1 Research Questions

This computational study is designed to answer four core scientific questions within a disclosed reduced-order model:
1. *Voltage Response:* How does the modeled terminal voltage response change with ambient temperature under identical load profiles?
2. *Coulomb Counting Error Accumulation:* How much SOC error does nominal-capacity Coulomb counting accumulate when true capacity degrades?
3. *Observer Error Reduction:* Does an Extended Kalman Filter (EKF) observer robustly eliminate error relative to Coulomb counting under sensor noise, systematic current bias, and initial state offsets?
4. *Dominant Physical Factor:* Within this model, which factor exerts the largest effect on estimation fidelity: ambient temperature, load profile dynamics, capacity fade, or internal resistance growth?

---

## 2. Related Work and Theoretical Background

Electrochemical state estimation spans a hierarchy of model complexities. Full electrochemical physics models, such as the Doyle–Fuller–Newman (DFN) and pseudo-two-dimensional (P2D) partial differential equation frameworks, capture concentration gradients, pore-scale transport, and Butler–Volmer reaction kinetics (Sulzer et al. 2021). While scientifically rigorous, P2D models demand dozens of microstructural parameters that are difficult to identify non-destructively and entail prohibitive computational overhead for embedded real-time microcontrollers.

Conversely, equivalent-circuit models (ECMs) represent electrochemical behavior via lumped electrical networks (Sun et al. 2026; Barletta et al. 2022). The first-order Thévenin ECM utilizes an open-circuit voltage source, an ohmic resistance $R_0$, and a single parallel resistor-capacitor ($R_1 \parallel C_1$) branch representing activation and concentration polarization. Barletta et al. (2022) demonstrated that parameterizing a 1-RC Thévenin model against experimental pulse discharge data on commercial Panasonic NCR18650B cylindrical cells yields terminal voltage root-mean-square errors below $20\,\text{mV}$, validating its balance of physical expressiveness and computational speed.

Thermal coupling is critical: internal cell temperature governs both instantaneous overpotentials and degradation rates. Mehta & Gupta (2024) and Mattia et al. (2025) reviewed electrothermal coupling methodologies, highlighting that lumped zero-dimensional thermal models accurately track core temperatures in cylindrical 18650 cells under moderate $C$-rates ($\le 1C$), where Biot numbers remain sufficiently small ($\text{Bi} < 0.1$) to justify negligible internal spatial thermal gradients.

For closed-loop state estimation, Kalman filtering frameworks (specifically Extended Kalman Filters and Unscented Kalman Filters) have emerged as the industry standard (Plett 2004; Sun et al. 2026). By incorporating terminal voltage measurement feedback through analytical linearization (Jacobians) and stochastic error covariance tracking, the EKF enables asymptotic convergence even in the presence of corrupted initial conditions.

---

## 3. Mathematical Modeling & Methodology

### 3.1 Sign Convention and State Variables

Throughout this study, we adhere strictly to the discharge-positive sign convention:
* Current $I > 0$: Cell is discharging.
* Current $I < 0$: Cell is charging.
* Current $I = 0$: Cell is in open-circuit relaxation.

The physical battery cell state vector is defined as:
$$\mathbf{x}_{\text{phys}} = \begin{bmatrix} z & v_p & T & Q_{\max} & \text{SOH} & N_{\text{eq}} \end{bmatrix}^T$$
where $z \in [0, 1]$ represents the true SOC fraction, $v_p$ (V) is the polarization voltage across the RC branch, $T$ (K) is the lumped core temperature, $Q_{\max}$ (Ah) is the available capacity, $\text{SOH} = Q_{\max} / Q_{\text{nom}}$ is the state of health, and $N_{\text{eq}}$ is the accumulated equivalent full cycle count.

### 3.2 Electrical Dynamics (1-RC Thévenin Model)

The terminal voltage $V_t$ and polarization dynamics are governed by:
$$V_t(t) = \text{OCV}(z(t)) - I(t) R_0(T, \text{SOH}) - v_p(t)$$
$$\frac{dv_p(t)}{dt} = -\frac{v_p(t)}{R_1(T, \text{SOH}) C_1} + \frac{I(t)}{C_1}$$
$$\frac{dz(t)}{dt} = -\frac{\eta I(t)}{3600 Q_{\max}}$$

where $\eta = 1.00$ is the coulombic discharge efficiency, and $C_1 = 2400.0\,\text{F}$ is the polarization capacitance ($\tau_1 = R_1 C_1 \approx 60\,\text{s}$).

### 3.3 Sourced Thermodynamic Open-Circuit Voltage

The equilibrium open-circuit voltage $\text{OCV}(z)$ is parameterized from experimental titration data reported by Barletta et al. (2022) for the Panasonic NCR18650B cell. To guarantee strict physical monotonicity and prevent unphysical oscillatory derivatives, piecewise cubic Hermite interpolating polynomials (PCHIP) are implemented. The resulting function satisfies:
$$\frac{d\text{OCV}(z)}{dz} > 0 \quad \forall z \in [0, 1]$$
with boundary potentials $\text{OCV}(0.0) = 2.50\,\text{V}$ and $\text{OCV}(1.0) = 4.20\,\text{V}$.

### 3.4 Arrhenius Temperature & SOH Resistance Scaling

Ohmic resistance $R_0$ and polarization resistance $R_1$ are modeled as coupled functions of core temperature and capacity fade:
$$R_j(T, \text{SOH}) = R_{j,\text{ref}} \exp\left[ \frac{E_{a,j}}{R_g} \left( \frac{1}{T} - \frac{1}{T_{\text{ref}}} \right) \right] \left[ 1 + \alpha_j (1 - \text{SOH}) \right] \quad (j \in \{0, 1\})$$

where $T_{\text{ref}} = 298.15\,\text{K}$ ($25\,^\circ\text{C}$), $R_g = 8.314\,\text{J}/(\text{mol}\cdot\text{K})$, $E_{a,0} = 22.0\,\text{kJ/mol}$, $E_{a,1} = 20.0\,\text{kJ/mol}$ (Mehta & Gupta 2024), $\alpha_0 = 0.80$, and $\alpha_1 = 0.50$. Under this formulation:
* Elevated temperatures accelerate ionic mobility in the electrolyte, reducing resistance ($\partial R_j / \partial T < 0$).
* Capacity degradation elevates resistance via active surface area loss and SEI growth ($\partial R_j / \partial \text{SOH} < 0$).

### 3.5 Lumped Thermal Energy Balance

Thermal dynamics are governed by a first-order lumped parameter ODE:
$$C_{\text{th}} \frac{dT(t)}{dt} = Q_{\text{gen}}(t) - hA \left( T(t) - T_{\text{amb}} \right)$$

where $C_{\text{th}} = m \cdot c_p = 42.0\,\text{J/K}$ is the cell heat capacity ($m \approx 45\,\text{g}$, $c_p \approx 933\,\text{J}/(\text{kg}\cdot\text{K})$), and $hA = 0.050\,\text{W/K}$ is the overall convective cooling factor under natural convection in air (Mattia et al. 2025). 

Total heat generation comprises irreversible Joule heating and polarization dissipation:
$$Q_{\text{gen}}(t) = I(t)^2 R_0 + I(t) v_p(t)$$
To ensure physical realism given the intentional omission of reversible entropic overpotentials ($I T \frac{\partial \text{OCV}}{\partial T}$), $Q_{\text{gen}}$ is constrained to be non-negative ($\max(0, Q_{\text{gen}})$).

### 3.6 State Estimation Algorithms

#### 3.6.1 Baseline: Nominal Coulomb Counting
The baseline Coulomb counter integrates measured current $I_{\text{meas}}$ assuming factory nominal capacity $Q_{\text{nom}} = 3.20\,\text{Ah}$:
$$\hat{z}_{\text{cc}}(k+1) = \hat{z}_{\text{cc}}(k) - \frac{\eta I_{\text{meas}}(k) \Delta t}{3600 Q_{\text{nom}}}$$
where $I_{\text{meas}}(k) = I_{\text{true}}(k) + I_{\text{bias}} + w_i(k)$, with $w_i \sim \mathcal{N}(0, \sigma_i^2)$.

#### 3.6.2 Observer: Extended Kalman Filter (EKF)
The EKF tracks state vector $\mathbf{x} = [z, v_p]^T$ with scalar measurement $y = V_{t,\text{meas}}$.
* **Prediction Step (Time Update):**
  $$\hat{\mathbf{x}}_{k|k-1} = \begin{bmatrix} \hat{z}_{k-1|k-1} - \frac{\eta I_{\text{meas}}(k-1) \Delta t}{3600 Q_{\text{est}}} \\ \hat{v}_{p, k-1|k-1} e^{-\Delta t / \tau_1} + I_{\text{meas}}(k-1) R_1 (1 - e^{-\Delta t / \tau_1}) \end{bmatrix}$$
  $$\mathbf{P}_{k|k-1} = \mathbf{F}_k \mathbf{P}_{k-1|k-1} \mathbf{F}_k^T + \mathbf{Q}$$
  where the process Jacobian is:
  $$\mathbf{F}_k = \begin{bmatrix} 1 & 0 \\ 0 & e^{-\Delta t / \tau_1} \end{bmatrix}$$
  and $\mathbf{Q} = \text{diag}(10^{-6}, 10^{-5})$.

* **Correction Step (Measurement Update):**
  The measurement prediction is $\hat{y}_k = \text{OCV}(\hat{z}_{k|k-1}) - I_{\text{meas}}(k) R_0 - \hat{v}_{p, k|k-1}$.
  The measurement Jacobian is derived analytically:
  $$\mathbf{H}_k = \left. \frac{\partial h}{\partial \mathbf{x}} \right|_{\hat{\mathbf{x}}_{k|k-1}} = \begin{bmatrix} \left. \frac{d\text{OCV}}{dz} \right|_{\hat{z}_{k|k-1}} & -1.0 \end{bmatrix}$$
  The innovation residual is $\tilde{y}_k = y_{k,\text{meas}} - \hat{y}_k$, with innovation variance $S_k = \mathbf{H}_k \mathbf{P}_{k|k-1} \mathbf{H}_k^T + R$.
  The Kalman gain is:
  $$\mathbf{K}_k = \mathbf{P}_{k|k-1} \mathbf{H}_k^T S_k^{-1}$$
  The state is updated as $\hat{\mathbf{x}}_{k|k} = \hat{\mathbf{x}}_{k|k-1} + \mathbf{K}_k \tilde{y}_k$.
  To guarantee symmetry and positive semi-definiteness under finite machine precision, the error covariance is updated via the Joseph stabilized formulation:
  $$\mathbf{P}_{k|k} = (\mathbf{I} - \mathbf{K}_k \mathbf{H}_k) \mathbf{P}_{k|k-1} (\mathbf{I} - \mathbf{K}_k \mathbf{H}_k)^T + \mathbf{K}_k R \mathbf{K}_k^T$$

---

## 4. Verification & Core Results

### 4.1 Numerical Convergence and Unit Invariants

Prior to scenario execution, the model was subjected to strict unit tests:
1. *Zero-Current Relaxation:* Under $I = 0$, true SOC remained constant ($\Delta z < 10^{-12}$) while initial polarization $v_p(0) = 50\,\text{mV}$ decayed to $< 1\,\text{mV}$ over $5\tau_1$, matching $v_p(t) = v_p(0) \exp(-t/\tau_1)$ to within $10^{-5}\,\text{V}$.
2. *Analytical Discharge Rate:* Under constant $0.5C$ discharge ($1.6\,\text{A}$) for 1800 s, simulated SOC matched analytical charge drawdown ($\Delta z = -0.25000$) with zero deviation ($< 10^{-9}$).
3. *Time-Step Invariance:* Simulating the baseline dynamic pulse cycle at standard $\Delta t = 1.0\,\text{s}$ ($3600$ steps) versus fine $\Delta t = 0.5\,\text{s}$ ($7200$ steps) yielded delivered energy of $3.868\,\text{Wh}$ ($0.003\%$ relative difference) and identical peak cell temperature ($28.15\,^\circ\text{C}$, $0.006\%$ difference), confirming numerical convergence.

### 4.2 Baseline Dynamic Tracking

Figure 3 illustrates the baseline dynamic cycle at $T_{\text{amb}} = 25\,^\circ\text{C}$ and $\text{SOH} = 1.00$ initialized with a $-15\%$ SOC error ($\hat{z}_0 = 0.65$ vs. $z_0 = 0.80$).

| Metric | Coulomb Counting ($\Delta t = 1\,\text{s}$) | Extended Kalman Filter ($\Delta t = 1\,\text{s}$) |
|---|---|---|
| **SOC RMSE [%]** | $15.003\%$ | **$0.343\%$** |
| **SOC MAE [%]** | $15.003\%$ | **$0.125\%$** |
| **Final SOC Error [%]** | $-15.002\%$ | **$+0.002\%$** |
| **Recovery Time ($\le 2\%$)** | Did not recover | **$1.0\,\text{s}$** |
| **Peak Cell Temperature** | $28.15\,^\circ\text{C}$ | $28.15\,^\circ\text{C}$ |

As evident from Figure 4, Coulomb counting retains its initial $-15\%$ offset permanently, while the EKF observer exploits terminal voltage measurement feedback to eliminate the error within seconds, maintaining tracking within $\pm 0.05\%$ SOC thereafter.

### 4.3 Core 36-Scenario Matrix Analysis

The complete factorial matrix evaluated 18 physical simulation runs, each simultaneously evaluating Coulomb counting and the EKF (36 estimator conditions).

| Temp [$^\circ\text{C}$] | SOH | Load Profile | Peak Temp [$^\circ\text{C}$] | CC RMSE [%] | EKF RMSE [%] | CC Final Err [%] | EKF Final Err [%] |
|---|---|---|---|---|---|---|---|
| **25.0** | 1.00 | Steady 0.5C | 28.11 | 15.01% | **0.89%** | -15.01% | +0.01% |
| **25.0** | 1.00 | Dynamic Pulse | 28.15 | 15.00% | **0.34%** | -15.00% | +0.00% |
| **25.0** | 0.90 | Steady 0.5C | 28.30 | 12.34% | **0.60%** | -5.56% | +0.01% |
| **25.0** | 0.90 | Dynamic Pulse | 28.34 | 13.15% | **0.31%** | -8.06% | +0.00% |
| **25.0** | 0.80 | Steady 0.5C | 28.50 | 9.47% | **0.55%** | +6.25% | +0.01% |
| **25.0** | 0.80 | Dynamic Pulse | 28.54 | 10.99% | **0.53%** | +0.63% | +0.00% |
| **35.0** | 1.00 | Steady 0.5C | 37.41 | 15.01% | **0.53%** | -15.01% | +0.00% |
| **35.0** | 1.00 | Dynamic Pulse | 37.47 | 15.00% | **0.23%** | -15.00% | +0.00% |
| **35.0** | 0.90 | Steady 0.5C | 37.56 | 12.34% | **0.33%** | -5.56% | +0.00% |
| **35.0** | 0.90 | Dynamic Pulse | 37.63 | 13.15% | **0.27%** | -8.06% | +0.00% |
| **35.0** | 0.80 | Steady 0.5C | 37.72 | 9.47% | **0.43%** | +6.25% | +0.01% |
| **35.0** | 0.80 | Dynamic Pulse | 37.78 | 10.99% | **0.45%** | +0.63% | +0.00% |
| **45.0** | 1.00 | Steady 0.5C | 46.89 | 15.01% | **0.33%** | -15.01% | +0.00% |
| **45.0** | 1.00 | Dynamic Pulse | 46.97 | 15.00% | **0.17%** | -15.00% | +0.00% |
| **45.0** | 0.90 | Steady 0.5C | 47.01 | 12.34% | **0.23%** | -5.56% | +0.00% |
| **45.0** | 0.90 | Dynamic Pulse | 47.09 | 13.15% | **0.23%** | -8.06% | +0.00% |
| **45.0** | 0.80 | Steady 0.5C | 47.13 | 9.47% | **0.38%** | +6.25% | +0.00% |
| **45.0** | 0.80 | Dynamic Pulse | 47.21 | 10.99% | **0.38%** | +0.63% | +0.00% |

#### Key Empirical Insights from Core Matrix:
1. **Coulomb Counting Degradation Divergence:** When $\text{SOH} = 0.80$, the cell's true capacity is $2.56\,\text{Ah}$, yet Coulomb counting continues dividing charge by $3.20\,\text{Ah}$. Consequently, during discharge the true cell reaches zero charge much faster than Coulomb counting predicts, leading to catastrophic overestimates of remaining charge (final error swings from $-15.0\%$ to $+6.25\%$).
2. **Thermal Modulation of Observer Fidelity:** Counter-intuitively, elevated ambient temperatures improve EKF estimation accuracy: at $\text{SOH} = 1.00$, EKF RMSE decreases from $0.34\%$ at $25\,^\circ\text{C}$ to $0.17\%$ at $45\,^\circ\text{C}$. This occurs because higher temperatures reduce internal ohmic resistance $R_0$ (via Arrhenius activation), diminishing the magnitude of $I R_0$ overpotential drops and making the terminal voltage measurement more tightly coupled to the true thermodynamic open-circuit voltage $\text{OCV}(z)$.

---

## 5. Robustness & Multi-Seed Sensitivity Analysis

To rigorously assess estimator stability under stochastic and systematic disturbances, 75 Monte Carlo simulations were executed across 5 independent random seeds ($42, 101, 2024, 777, 9999$).

### 5.1 Robustness Factor Performance

1. **Initial State Offset ($\pm 10\%, \pm 20\%$):** Coulomb counting retains $100\%$ of the initial offset, yielding RMSEs of $10.0\%$ to $20.0\%$. In contrast, the EKF converges within $1.0\,\text{s}$ to $4.0\,\text{s}$, with overall RMSE remaining below $0.46\%$.
2. **Current Sensor Bias ($\pm 0.5\%, \pm 1.0\%$):** Over 1 hour of operation, a $+1.0\%$ current bias ($+16\,\text{mA}$) causes Coulomb counting to drift by an additional $+0.50\%$ SOC. The EKF observer voltage correction bounds the bias drift to $< 0.05\%$.
3. **Voltage Sensor Noise ($2\,\text{mV}, 5\,\text{mV}, 10\,\text{mV}$):** Varying measurement noise standard deviation by a factor of 5 produced negligible change in EKF RMSE ($0.343\% \pm 0.002\%$), demonstrating effective measurement noise rejection by the Kalman filter.
4. **Estimator $R_0$ Parameter Mismatch ($\pm 10\%$):** Introducing intentional $\pm 10\%$ error in the observer's internal resistance parameter shifted steady-state EKF error by only $0.08\%$, confirming that polarization and OCV tracking dominate state observation.

### 5.2 Tornado Sensitivity Ranking

To answer Research Question 4, the relative impact of each physical and operational parameter was quantified across its full operational range.

| Rank | Parameter / Factor | Impact Range [Percentage Points] | Physical Domain |
|---|---|---|---|
| **1** | **Initial SOC Uncertainty ($\pm 20\%$)** | **$10.02\%$** | State Initialization |
| **2** | **Capacity Fade ($\text{SOH}: 1.0 \to 0.8$)** | **$4.77\%$** | Cell Aging / Degradation |
| **3** | **Current Sensor Bias ($\pm 1\%$)** | **$0.50\%$** | Sensor Instrumentation |
| **4** | **Ambient Temperature ($25\,^\circ\text{C} \to 45\,^\circ\text{C}$)** | **$0.25\%$** | Environmental Coupling |
| **5** | **Load Profile Dynamics (Steady vs. Pulse)** | **$0.15\%$** | Operating Regimes |

**Scientific Resolution:** Within this reduced-order electrothermal model, state initialization uncertainty and capacity fade are the primary drivers of SOC estimation error, while ambient temperature and load profile dynamics exert secondary modulations.

---

## 6. Discussion

### 6.1 Physical Mechanisms Driving Estimator Divergence
The fundamental divergence between Coulomb counting and EKF observers originates in their respective mathematical structures:
* Coulomb counting is an **open-loop integrator** of the form $\dot{z} = -I / Q$. It possess zero feedback, meaning any initial error or integrated disturbance $\int w_i dt$ is mathematically permanent ($\lim_{t \to \infty} \text{Var}(z_{\text{cc}}) = \infty$).
* The Extended Kalman Filter is a **closed-loop observer** with state-dependent gain $\mathbf{K}_k$. When the true state departs from the estimate, the innovation $\tilde{y} = V_{t,\text{meas}} - \hat{V}_t$ acts as a restoring force through the non-zero derivative $\frac{d\text{OCV}}{dz}$, guaranteeing asymptotic stability ($\mathbf{P}_k \to \mathbf{P}_{\infty}$).

### 6.2 Influence of Elevated Temperature
Elevated temperature exerts two opposing effects:
1. *Short-Term Electrical Advantage:* Arrhenius kinetics accelerate charge transfer, reducing $R_0$ and $R_1$. Consequently, overpotential uncertainties contribute less error to terminal voltage predictions, yielding superior EKF tracking (RMSE drops from $0.34\%$ at $25\,^\circ\text{C}$ to $0.17\%$ at $45\,^\circ\text{C}$).
2. *Long-Term Degradation Penalty:* As depicted in the aging surrogate (Figure 6), sustained operation at $45\,^\circ\text{C}$ accelerates SEI growth and available capacity loss, cutting cycle life by over $40\%$ relative to $25\,^\circ\text{C}$.

---

## 7. Limitations and Future Work

To maintain strict scientific integrity, the following limitations of this study must be disclosed:
1. **Lumped Thermal Model:** The single-node thermal ODE assumes a spatially uniform core temperature. While valid for single 18650 cells at $\le 1C$ under natural convection ($\text{Bi} < 0.1$), it neglects radial thermal gradients present under fast charging ($\ge 3C$) or in dense battery modules.
2. **Empirical Aging Surrogate:** The capacity fade and resistance growth models are reduced-order empirical power-law relations rather than microstructural models of SEI layer growth, active material cracking, or lithium plating.
3. **No Direct Laboratory Measurements:** All results presented herein are reproducible computational simulations based on literature parameters (Barletta et al. 2022). They do not constitute new physical laboratory experiments.

### 7.1 Recommended Experimental Next Steps
To extend this foundation into an experimental thesis or research program:
1. Subject commercial 18650 NCA and NMC cells to hybrid pulse power characterization (HPPC) and electrochemical impedance spectroscopy (EIS) inside an environmental chamber at $25\,^\circ\text{C}$, $35\,^\circ\text{C}$, and $45\,^\circ\text{C}$.
2. Fit temperature-dependent 2-RC parameters ($R_0, R_1, C_1, R_2, C_2$) directly from experimental relaxation curves.
3. Deploy the EKF algorithm onto an embedded ARM Cortex-M microcontroller to validate real-time execution timing, fixed-point precision, and hardware-in-the-loop (HIL) performance.

---

## 8. Conclusion

This research developed and evaluated a physics-informed electrothermal and aging-aware equivalent-circuit simulation framework for lithium-ion battery state estimation. In response to the core research questions:
1. **Voltage Dynamics:** Elevated ambient temperatures reduce internal ohmic resistance from $42\,\text{m}\Omega$ at $25\,^\circ\text{C}$ to $26\,\text{m}\Omega$ at $45\,^\circ\text{C}$, mitigating overpotentials and narrowing the gap between terminal voltage and thermodynamic open-circuit voltage.
2. **Coulomb Counting Failure:** In the presence of unmodeled capacity fade ($\text{SOH} = 0.80$), nominal Coulomb counting accumulates catastrophic SOC drift (final errors exceeding $+6.2\%$), posing severe risks of cell over-discharge.
3. **EKF Observer Superiority:** The physics-informed EKF observer maintains SOC tracking RMSE below $0.89\%$ across all 36 core scenarios, effortlessly rejecting current sensor bias and correcting a $-15\%$ initial state error within $1.0$ to $5.0$ seconds.
4. **Parameter Hierarchy:** Tornado sensitivity analysis establishes that initial state error ($10.02\%$) and capacity degradation ($4.77\%$) dominate estimation error, while ambient temperature ($0.25\%$) and load dynamics ($0.15\%$) play secondary roles.

---

## 9. Appendix: Parameter Specifications & Reproducibility Audit

### 9.1 Parameter Table Summary
Full parameter provenance is recorded in `data/processed/parameter_table.csv` and documented in `data/DATA_CARD.md`. All primary electrical parameters originate from Barletta et al. (2022) [Energies 15(17), 6207], thermal constants from Mattia et al. (2025) [J. Energy Storage 129, 117114], and Arrhenius activation parameters from Mehta & Gupta (2024) [Renew. Sust. Energy Rev. 192, 114264].

### 9.2 Reproducibility Protocol
The entire simulation suite, figure generation, and tabular outputs can be recreated deterministically from a clean environment via:
```bash
python run_pipeline.py
```
This automated master pipeline runs unit tests, executes baseline convergence evaluations, simulates the 36-scenario core matrix, conducts 75 multi-seed Monte Carlo robustness sweeps, and compiles all 8 publication figures in under 90 seconds.

### 9.3 AI-Use Statement
Generative AI was employed as an interactive pair-programming assistant to format mathematical documentation, construct plotting scripts, and automate configuration pipelines under human direction. All physical equations, derivations, and simulation outputs were independently verified against peer-reviewed literature.
