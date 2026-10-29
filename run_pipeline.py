"""
Master Execution Pipeline for Battery BMS Temperature Project.

A single documented command reproduces all data tables, simulations,
unit tests, and publication figures from scratch.

Usage:
    python run_pipeline.py
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

def run_step(description: str, command: list):
    print("\n" + "="*80)
    print(f"STEP: {description}")
    print(f"COMMAND: {' '.join(command)}")
    print("="*80)
    res = subprocess.run(command, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print(f"\n[ERROR] Pipeline failed at step: {description} (exit code {res.returncode})")
        sys.exit(res.returncode)

def main():
    print("="*80)
    print("STARTING FULL REPRODUCIBLE RESEARCH PIPELINE")
    print(f"Repository Root: {PROJECT_ROOT}")
    print("="*80)

    # 1. Run unit test suite
    run_step("1. Unit and Physics Invariant Test Suite", [sys.executable, "run_tests.py"])

    # 2. Data Preparation & Validation
    run_step("2. Reference Data Validation", [sys.executable, "scripts/01_prepare_data.py"])

    # 3. Baseline Simulation & Convergence
    run_step("3. Baseline Simulation & Convergence Evaluation", [sys.executable, "scripts/02_run_baseline.py"])

    # 4. Core 36-Scenario Factorial Matrix
    run_step("4. Core 36-Scenario Factorial Matrix", [sys.executable, "scripts/03_run_scenarios.py"])

    # 5. Multi-Seed Robustness & Sensitivity Suite
    run_step("5. Multi-Seed Robustness Suite (75 Monte Carlo runs)", [sys.executable, "scripts/04_run_robustness.py"])

    # 6. Master Visual Compilation
    run_step("6. Publication Figures Compilation", [sys.executable, "scripts/05_make_figures.py"])

    print("\n" + "="*80)
    print("RESEARCH PIPELINE COMPLETED SUCCESSFULLY!")
    print("All tables saved in: results/tables/")
    print("All figures saved in: results/figures/")
    print("="*80)

if __name__ == "__main__":
    main()
