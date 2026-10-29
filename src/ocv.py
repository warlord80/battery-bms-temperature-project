"""
Open-Circuit Voltage (OCV) Modeling Module.

Provides smooth, monotonic OCV(z) interpolation and analytical first derivatives
d(OCV)/dz based on experimental data from Barletta et al. (2022) for the
Panasonic NCR18650B (3.2 Ah) lithium-ion cell.
"""

from typing import Union, Tuple
import logging
import numpy as np
from scipy.interpolate import PchipInterpolator

logger = logging.getLogger(__name__)

# Sourced OCV-SOC characteristic points for Panasonic NCR18650B (Barletta et al. 2022)
DEFAULT_SOC_POINTS = np.array([
    0.00, 0.05, 0.10, 0.20, 0.30, 0.40,
    0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00
], dtype=float)

DEFAULT_OCV_POINTS = np.array([
    2.500, 3.120, 3.330, 3.490, 3.590, 3.670,
    3.740, 3.825, 3.930, 4.030, 4.120, 4.165, 4.200
], dtype=float)


class OCVModel:
    """
    Evaluates cell open-circuit voltage and its derivative using Piecewise Cubic
    Hermite Interpolating Polynomials (PCHIP) to preserve strict monotonicity.
    """

    def __init__(
        self,
        soc_points: np.ndarray = DEFAULT_SOC_POINTS,
        ocv_points: np.ndarray = DEFAULT_OCV_POINTS,
    ):
        if len(soc_points) != len(ocv_points):
            raise ValueError("soc_points and ocv_points must have identical dimensions.")
        if not np.all(np.diff(soc_points) > 0):
            raise ValueError("soc_points must be strictly monotonically increasing.")
        if not np.all(np.diff(ocv_points) > 0):
            raise ValueError("ocv_points must be strictly monotonically increasing.")

        self.soc_points = np.asarray(soc_points, dtype=float)
        self.ocv_points = np.asarray(ocv_points, dtype=float)
        
        # PCHIP preserves monotonicity without artificial oscillations
        self._interpolator = PchipInterpolator(self.soc_points, self.ocv_points, extrapolate=False)
        self._derivative = self._interpolator.derivative()

    def evaluate(self, soc: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Evaluate OCV in Volts at a given SOC fraction z in [0, 1].
        Logs warning and clamps if SOC exceeds [0, 1].
        """
        is_scalar = np.isscalar(soc)
        z = np.atleast_1d(soc)

        # Check for saturation
        if np.any(z < 0.0) or np.any(z > 1.0):
            logger.warning("SOC saturation event detected: z outside [0, 1]. Clamping for evaluation.")

        z_clamped = np.clip(z, 0.0, 1.0)
        ocv_vals = self._interpolator(z_clamped)

        return float(ocv_vals[0]) if is_scalar else ocv_vals

    def derivative(self, soc: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Evaluate d(OCV)/dz in Volts per unit SOC fraction.
        """
        is_scalar = np.isscalar(soc)
        z = np.atleast_1d(soc)
        z_clamped = np.clip(z, 0.0, 1.0)
        docv_vals = self._derivative(z_clamped)

        return float(docv_vals[0]) if is_scalar else docv_vals

    def is_monotonic(self, n_eval: int = 1000) -> bool:
        """
        Verifies that OCV(z) is strictly monotonic across [0, 1].
        """
        z_grid = np.linspace(0.0, 1.0, n_eval)
        ocv_grid = self.evaluate(z_grid)
        return bool(np.all(np.diff(ocv_grid) > 0))
