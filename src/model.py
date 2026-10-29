"""
Electrothermal Battery Cell Model Module.

Implements a 1-RC Thévenin Equivalent Circuit Model (ECM) coupled to a
lumped-parameter single-node thermal ODE and Arrhenius/SOH resistance scaling.
"""

from dataclasses import dataclass
import logging
from typing import Tuple, Dict, Any, Optional
import numpy as np
from src.ocv import OCVModel

logger = logging.getLogger(__name__)


@dataclass
class CellState:
    """Represents the complete dynamic physical state of the battery cell."""
    soc: float           # State of charge fraction in [0, 1]
    vp: float            # Polarization voltage across RC branch in Volts
    temperature_k: float # Lumped core temperature in Kelvin
    q_max: float         # Available maximum capacity in Ah
    soh: float           # State of Health fraction (q_max / q_nom)
    neq: float           # Equivalent full cycles accumulated


class BatteryCell:
    """
    Coupled electrothermal 1-RC Thévenin cell model.
    Sign convention: Positive current I > 0 indicates discharge; I < 0 indicates charge.
    """

    def __init__(
        self,
        q_nom: float = 3.20,
        t_ref: float = 298.15,
        r0_ref: float = 0.042,
        r1_ref: float = 0.025,
        c1: float = 2400.0,
        ea_0: float = 22000.0,
        ea_1: float = 20000.0,
        alpha_0: float = 0.80,
        alpha_1: float = 0.50,
        cth: float = 42.0,
        ha: float = 0.050,
        rg: float = 8.314,
        eta: float = 1.00,
        v_min: float = 2.50,
        v_max: float = 4.20,
        ocv_model: Optional[OCVModel] = None,
    ):
        self.q_nom = float(q_nom)
        self.t_ref = float(t_ref)
        self.r0_ref = float(r0_ref)
        self.r1_ref = float(r1_ref)
        self.c1 = float(c1)
        self.ea_0 = float(ea_0)
        self.ea_1 = float(ea_1)
        self.alpha_0 = float(alpha_0)
        self.alpha_1 = float(alpha_1)
        self.cth = float(cth)
        self.ha = float(ha)
        self.rg = float(rg)
        self.eta = float(eta)
        self.v_min = float(v_min)
        self.v_max = float(v_max)
        
        self.ocv = ocv_model if ocv_model is not None else OCVModel()

    def get_r0(self, temperature_k: float, soh: float) -> float:
        """
        Calculate ohmic resistance R0(T, SOH) via Arrhenius law and linear SOH fade:
        R0(T, SOH) = R0_ref * exp[(Ea_0 / Rg) * (1/T - 1/Tref)] * [1 + alpha_0 * (1 - SOH)]
        """
        arrhenius_factor = np.exp((self.ea_0 / self.rg) * (1.0 / temperature_k - 1.0 / self.t_ref))
        aging_factor = 1.0 + self.alpha_0 * (1.0 - soh)
        return float(self.r0_ref * arrhenius_factor * aging_factor)

    def get_r1(self, temperature_k: float, soh: float) -> float:
        """
        Calculate polarization resistance R1(T, SOH) via Arrhenius law and linear SOH fade:
        R1(T, SOH) = R1_ref * exp[(Ea_1 / Rg) * (1/T - 1/Tref)] * [1 + alpha_1 * (1 - SOH)]
        """
        arrhenius_factor = np.exp((self.ea_1 / self.rg) * (1.0 / temperature_k - 1.0 / self.t_ref))
        aging_factor = 1.0 + self.alpha_1 * (1.0 - soh)
        return float(self.r1_ref * arrhenius_factor * aging_factor)

    def terminal_voltage(self, state: CellState, current_a: float) -> float:
        """
        Calculate instantaneous terminal voltage:
        Vt = OCV(z) - I * R0(T, SOH) - vp
        """
        r0 = self.get_r0(state.temperature_k, state.soh)
        ocv_val = self.ocv.evaluate(state.soc)
        return float(ocv_val - current_a * r0 - state.vp)

    def heat_generation(self, state: CellState, current_a: float) -> float:
        """
        Compute total heat generation Qgen = I^2 * R0 + I * vp.
        Clamped to non-negative to avoid unphysical cooling since reversible entropic
        heat is omitted by deliberate model scope decision.
        """
        r0 = self.get_r0(state.temperature_k, state.soh)
        q_gen = (current_a ** 2) * r0 + current_a * state.vp
        return float(max(0.0, q_gen))

    def step(
        self,
        state: CellState,
        current_a: float,
        dt: float,
        t_amb: float,
    ) -> Tuple[CellState, Dict[str, float]]:
        """
        Advance cell state by time step dt using exact zero-order-hold discretization.
        Returns the updated state and diagnostic metrics.
        """
        # 1. Electrical RC and Ohmic properties
        r0 = self.get_r0(state.temperature_k, state.soh)
        r1 = self.get_r1(state.temperature_k, state.soh)
        tau1 = r1 * self.c1

        # 2. Polarization voltage update (ZOH exponential solution)
        exp_factor = np.exp(-dt / tau1)
        next_vp = state.vp * exp_factor + current_a * r1 * (1.0 - exp_factor)

        # 3. SOC update via charge conservation: dz/dt = -eta * I / (3600 * Qmax)
        delta_soc = -(self.eta * current_a * dt) / (3600.0 * state.q_max)
        next_soc_raw = state.soc + delta_soc
        
        # Log and clamp saturation
        if next_soc_raw < 0.0 or next_soc_raw > 1.0:
            logger.warning(
                "SOC saturation event: raw SOC = %.5f clamped to [0, 1].", next_soc_raw
            )
        next_soc = float(np.clip(next_soc_raw, 0.0, 1.0))

        # 4. Thermal update: Cth dT/dt = Qgen - hA(T - Tamb)
        # Analytical solution for constant Qgen over dt:
        # T(t+dt) = Tamb + Qgen/hA + (T(t) - Tamb - Qgen/hA) * exp(-hA/Cth * dt)
        q_gen = self.heat_generation(state, current_a)
        thermal_exp = np.exp(-(self.ha / self.cth) * dt)
        t_steady = t_amb + (q_gen / self.ha)
        next_t = float(t_steady + (state.temperature_k - t_steady) * thermal_exp)

        # 5. Throughput tracking for equivalent cycles: dNeq = |I| dt / (2 * 3600 * Qnom)
        d_neq = abs(current_a) * dt / (7200.0 * self.q_nom)
        next_neq = state.neq + d_neq

        # Construct next state
        next_state = CellState(
            soc=next_soc,
            vp=float(next_vp),
            temperature_k=next_t,
            q_max=state.q_max,
            soh=state.soh,
            neq=next_neq,
        )

        vt = self.terminal_voltage(next_state, current_a)

        metrics = {
            "vt": vt,
            "q_gen": q_gen,
            "r0": r0,
            "r1": r1,
            "tau1": tau1,
        }

        return next_state, metrics
