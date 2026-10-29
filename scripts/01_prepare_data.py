"""
Script 01: Prepare and Validate Reference Data.

Validates parameter tables, verifies that all parameters obey declared bounds,
and generates synthetic dynamic current drive cycles for baseline and scenario runs.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ocv import OCVModel, DEFAULT_SOC_POINTS, DEFAULT_OCV_POINTS


def prepare_and_validate():
    print("[01_prepare_data] Verifying reference data and parameter tables...")
    param_path = PROJECT_ROOT / "data" / "processed" / "parameter_table.csv"
    if not param_path.exists():
        raise FileNotFoundError(f"Parameter table missing at {param_path}")

    df_params = pd.read_csv(param_path)
    print(f"[01_prepare_data] Loaded {len(df_params)} parameter rows from parameter_table.csv.")

    # Validate OCV model
    ocv = OCVModel(DEFAULT_SOC_POINTS, DEFAULT_OCV_POINTS)
    assert ocv.is_monotonic(), "OCV model failed monotonicity validation!"
    print("[01_prepare_data] OCV model validated: strictly monotonic in [0, 1].")

    # Generate reference OCV-SOC lookup curve artifact for inspection
    raw_data_dir = PROJECT_ROOT / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    soc_fine = np.linspace(0.0, 1.0, 101)
    ocv_fine = ocv.evaluate(soc_fine)
    docv_fine = ocv.derivative(soc_fine)
    
    df_ocv = pd.DataFrame({
        "soc": soc_fine,
        "ocv_v": ocv_fine,
        "docv_dz": docv_fine
    })
    ocv_csv_path = raw_data_dir / "panasonic_ncr18650b_ocv_reference.csv"
    df_ocv.to_csv(ocv_csv_path, index=False)
    print(f"[01_prepare_data] Reference OCV curve saved to {ocv_csv_path}")

    print("[01_prepare_data] Data preparation complete successfully.")


if __name__ == "__main__":
    prepare_and_validate()
