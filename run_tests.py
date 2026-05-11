import argparse
import subprocess
import sys
from pathlib import Path


TEST_GROUPS = {
    "unit": [
        "tests/feedback_unit_test.py",
        "tests/health_check_unit_test.py",
        "tests/image_utils_unit_test.py",
        "tests/quality_check_unit_test.py",
        "tests/capture_server_unit_test.py",
        "tests/manual_capture_unit_test.py",
        "tests/camera_service_unit_test.py",
    ],
    "integration": [
        "tests/fras_client_integration_test.py",
        "tests/capture_server_integration_test.py",
        "tests/main_integration_test.py",
    ],
    "system": [
        "tests/capture_server_system_test.py",
        "tests/device_readiness_system_test.py",
    ],
    "load-stress": [
        "tests/quality_pipeline_load_stress_test.py",
    ],
    "security-performance": [
        "tests/security_performance_test.py",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run FRAS Raspberry Pi test groups.")
    parser.add_argument(
        "group",
        choices=["all", *TEST_GROUPS.keys()],
        nargs="?",
        default="all",
        help="Test group to run.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parent
    if args.group == "all":
        test_files = [test_file for group in TEST_GROUPS.values() for test_file in group]
    else:
        test_files = TEST_GROUPS[args.group]

    command = [sys.executable, "-m", "unittest", *test_files]
    return subprocess.call(command, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
