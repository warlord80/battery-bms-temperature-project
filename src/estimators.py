"""
State Estimation Module: Coulomb Counting Baseline and Extended Kalman Filter (EKF).

Implements:
1. CoulombCounter: Open-loop charge integration using assumed nominal capacity Qnom.
2. ExtendedKalmanFilter: Closed-loop model-based observer for state vector [z, vp]^T
   using exact analytical process/measurement Jacobians and the Joseph stabilized
   covariance update for numerical robustness.
"""

from typing import Tuple, Optional
import numpy as np
from src.ocv import OCVModel


class CoulombCounter:
    """
    Open-loop Coulomb Counting baseline estimator.
    Accumulates SOC error in the presence of initial state offsets,
    current sensor bias, and capacity degradation (Qmax < Qnom).
    """

    def __init__(self, q_assumed: float = 3.20, eta: float = 1.00, soc_init: float = 0.65):
        self.q_assumed = float(q_assumed) # Nominal capacity (Ah)
        self.eta = float(eta)
        self.soc = float(soc_init)

    def step(self, current_meas_a: float, dt: float) -> float:
        """
        Discrete time update: zhat(k+1) = zhat(k) - eta * Imeas * dt / (3600 * Qassumed)
        """
        delta_soc = -(self.eta * current_meas_a * dt) / (3600.0 * self.q_assumed)
        self.soc = float(np.clip(self.soc + delta_soc, 0.0, 1.0))
        return self.soc


class ExtendedKalmanFilter:
    """
    Physics-informed Extended Kalman Filter observer for Lithium-ion cells.
    State vector: x = [z, vp]^T (SOC fraction, polarization voltage in Volts).
    Measurement: Terminal voltage y = Vt.
    """

    def __init__(
        self,
        ocv_model: OCVModel,
        q_est: float = 3.20,
        r0_est: float = 0.042,
        r1_est: float = 0.025,
        c1_est: float = 2400.0,
        eta: float = 1.00,
        soc_init: float = 0.65,
        vp_init: float = 0.0,
        p0_z: float = 0.010,
        p0_vp: float = 0.0001,
        q_z: float = 1.0e-6,
        q_vp: float = 1.0e-5,
        r_cov: float = 2.5e-5,
    ):
        self.ocv = ocv_model
        self.q_est = float(q_est)
        self.r0_est = float(r0_est)
        self.r1_est = float(r1_est)
        self.c1_est = float(c1_est)
        self.eta = float(eta)

        # State vector: x = [z, vp]^T
        self.x = np.array([float(soc_init), float(vp_init)], dtype=float)

        # Error covariance matrix P (2x2)
        self.P = np.array([
            [float(p0_z), 0.0],
            [0.0, float(p0_vp)]
        ], dtype=float)

        # Process noise covariance Q (2x2)
        self.Q = np.array([
            [float(q_z), 0.0],
            [0.0, float(q_vp)]
        ], dtype=float)

        # Measurement noise variance R (scalar)
        self.R = float(r_cov)

    @property
    def soc(self) -> float:
        return float(self.x[0])

    @property
    def vp(self) -> float:
        return float(self.x[1])

    def get_process_jacobian(self, dt: float) -> np.ndarray:
        """
        Analytical Jacobian of state transition f(x, u) with respect to state x:
        F = [[1, 0], [0, exp(-dt / tau1)]]
        """
        tau1 = self.r1_est * self.c1_est
        exp_factor = float(np.exp(-dt / tau1))
        return np.array([
            [1.0, 0.0],
            [0.0, exp_factor]
        ], dtype=float)

    def get_measurement_jacobian(self, z_prior: float) -> np.ndarray:
        """
        Analytical Jacobian of measurement equation h(x, u) with respect to state x:
        H = [dOCV/dz, -1.0]
        """
        docv_dz = float(self.ocv.derivative(z_prior))
        return np.array([[docv_dz, -1.0]], dtype=float)

    def predict(self, current_meas_a: float, dt: float):
        """
        Time update (prediction step):
        x_{k|k-1} = f(x_{k-1|k-1}, u_{k-1})
        P_{k|k-1} = F * P_{k-1|k-1} * F^T + Q
        """
        tau1 = self.r1_est * self.c1_est
        exp_factor = float(np.exp(-dt / tau1))

        # Predict states
        delta_soc = -(self.eta * current_meas_a * dt) / (3600.0 * self.q_est)
        z_pred = float(np.clip(self.x[0] + delta_soc, 0.0, 1.0))
        vp_pred = float(self.x[1] * exp_factor + current_meas_a * self.r1_est * (1.0 - exp_factor))
        self.x = np.array([z_pred, vp_pred], dtype=float)

        # Predict covariance
        F = self.get_process_jacobian(dt)
        self.P = F @ self.P @ F.T + self.Q

        # Maintain exact symmetry
        self.P = 0.5 * (self.P + self.P.T)

    def update(self, vt_meas: float, current_meas_a: float) -> Tuple[float, float]:
        """
        Measurement update (correction step):
        Computes Kalman gain and updates state using Joseph-stabilized covariance formulation.
        Returns: (innovation, innovation_variance)
        """
        z_prior = self.x[0]
        vp_prior = self.x[1]

        # Predicted measurement: y_pred = OCV(z) - I * R0 - vp
        ocv_pred = self.ocv.evaluate(z_prior)
        vt_pred = ocv_pred - current_meas_a * self.r0_est - vp_prior

        # Innovation (residual)
        innovation = vt_meas - vt_pred

        # Measurement Jacobian H
        H = self.get_measurement_jacobian(z_prior) # Shape (1, 2)

        # Innovation covariance S = H * P * H^T + R
        S = float((H @ self.P @ H.T).item() + self.R)

        # Kalman gain K = P * H^T * S^-1 (Shape 2x1)
        K = (self.P @ H.T) / S # Shape (2, 1)

        # State correction
        self.x = self.x + (K.flatten() * innovation)
        
        # Enforce physical state bounds
        self.x[0] = float(np.clip(self.x[0], 0.0, 1.0))
        self.x[1] = float(np.clip(self.x[1], -0.50, 0.50))

        # Joseph stabilized covariance update: P = (I - K*H) * P * (I - K*H)^T + K * R * K^T
        # Ensures numerical positive semi-definiteness
        I2 = np.eye(2, dtype=float)
        IKH = I2 - (K @ H)
        self.P = IKH @ self.P @ IKH.T + (K @ K.T * self.R)

        # Maintain exact symmetry
        self.P = 0.5 * (self.P + self.P.T)

        return float(innovation), S

    def step(self, vt_meas: float, current_meas_a: float, dt: float) -> Tuple[float, float, float]:
        """
        Executes a complete EKF cycle: predict then update.
        Returns: (estimated_soc, estimated_vp, innovation)
        """
        self.predict(current_meas_a, dt)
        innovation, _ = self.update(vt_meas, current_meas_a)
        return self.soc, self.vp, innovation
