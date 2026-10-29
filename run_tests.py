"""
Comprehensive Test Runner for Battery BMS Temperature Project.

Executes all unit tests with strict isolation to avoid rootdir scanning issues.
"""

import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_all_tests():
    print(f"Running unit test suite from: {PROJECT_ROOT}")
    args = [
        "-c", str(PROJECT_ROOT / "pyproject.toml"),
        "-p", "no:asyncio",
        "-p", "no:anyio",
        "--rootdir", str(PROJECT_ROOT),
        str(PROJECT_ROOT / "tests"),
        "-v",
    ]
    exit_code = pytest.main(args)
    if exit_code == 0:
        print("\nAll unit tests passed successfully!")
    else:
        print(f"\nUnit tests failed with exit code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    run_all_tests()
