# Data Card: Panasonic NCR18650B Equivalent-Circuit & Thermal Parameters

## Overview
This data card documents the origin, chemistry, format, and governance of the parameters and reference curves utilized in this computational simulation study.

## Cell Specifications
- **Cell Model**: Panasonic NCR18650B Cylindrical Lithium-ion Cell
- **Form Factor**: 18650 (18 mm diameter, 65 mm height, ~45.5 g mass)
- **Positive Electrode (Cathode)**: $\text{LiNi}_{0.8}\text{Co}_{0.15}\text{Al}_{0.05}\text{O}_2$ (NCA)
- **Negative Electrode (Anode)**: Graphite
- **Nominal Capacity ($Q_{\text{nom}}$)**: $3.20\,\text{Ah}$ ($3200\,\text{mAh}$) rated ($3.35\,\text{Ah}$ typical)
- **Nominal Voltage**: $3.6\,\text{V}$
- **Operating Voltage Range**: $2.50\,\text{V}$ to $4.20\,\text{V}$
- **Maximum Continuous Discharge Current**: $2C$ ($6.4\,\text{A}$)

## Provenance and Primary Literature Sources
1. **Electrical ECM & OCV–SOC**:
   - **Source**: Barletta, G., DiPrima, P., & Papurello, D. (2022). *Thévenin’s Battery Model Parameter Estimation Based on Simulink*. Energies, 15(17), 6207.
   - **DOI**: [10.3390/en15176207](https://doi.org/10.3390/en15176207)
   - **Licence**: CC BY 4.0 Open Access.
   - **Fit / Validation**: Provides experimentally extracted 1-RC Thévenin parameters ($R_0 = 42\,\text{m}\Omega$, $R_1 = 25\,\text{m}\Omega$, $C_1 = 2400\,\text{F}$) and discrete OCV-SOC lookup points across $z \in [0, 1]$ under pulsed discharge protocols at $25\,^\circ\text{C}$.

2. **Electrothermal & Activation Kinetics**:
   - **Source**: Mehta, R., & Gupta, A. K. (2024). *Mathematical modelling of electrochemical, thermal and degradation processes in lithium-ion cells—A comprehensive review*. Renewable and Sustainable Energy Reviews, 192, 114264.
   - **DOI**: [10.1016/j.rser.2023.114264](https://doi.org/10.1016/j.rser.2023.114264)
   - **Fit / Validation**: Sourced activation energies ($E_{a,0} = 22.0\,\text{kJ/mol}$, $E_{a,1} = 20.0\,\text{kJ/mol}$) for Arrhenius resistance scaling with temperature.

3. **Lumped Thermal Properties**:
   - **Source**: Mattia, L., Beiranvand, H., Zamboni, W., & Liserre, M. (2025). *Lithium-ion battery thermal modelling and characterisation: A comprehensive review*. Journal of Energy Storage, 129, 117114.
   - **DOI**: [10.1016/j.est.2025.117114](https://doi.org/10.1016/j.est.2025.117114)
   - **Fit / Validation**: Sourced thermal mass for standard 18650 cells ($C_{\text{th}} = 42\,\text{J/K}$, representing $m \cdot c_p$) and natural convection heat transfer coefficient ($hA = 0.050\,\text{W/K}$).

4. **Synthetic Estimator Noise & Covariances**:
   - **Source**: Sun, X. et al. (2026). *Equivalent Circuit Models for Lithium-Ion Batteries: A Comprehensive Review*. Electronics, 15(9), 1968.
   - **DOI**: [10.3390/electronics15091968](https://doi.org/10.3390/electronics15091968)
   - **Fit / Validation**: Guides typical BMS sensor noise standard deviations ($\sigma_v = 5\,\text{mV}$, $\sigma_i = 20\,\text{mA}$) and discrete EKF observer matrices.

## Assumptions & Sensitivity Status
- Resistance aging sensitivity factors ($\alpha_0 = 0.80$, $\alpha_1 = 0.50$) are explicitly flagged as transparent scenario surrogates rather than universal electrochemical laws.
- In accordance with the project integrity rules, these assumed parameters are subjected to multi-factor sensitivity analysis across the matrix.
