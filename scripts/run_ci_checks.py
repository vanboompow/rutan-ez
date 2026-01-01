"""CI entrypoint for Open-EZ PDE.

Runs config validation and ensures artifact metadata is present.
"""
# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import config
from scripts.validate_metadata import main as validate_metadata_main


def run_config_validation() -> int:
    errors = config.validate()
    if errors:
        print("Configuration validation failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("Configuration validation passed.")
    return 0


def main() -> int:
    exit_codes = [run_config_validation()]
    exit_codes.append(validate_metadata_main())

    return 1 if any(code != 0 for code in exit_codes) else 0


if __name__ == "__main__":
    sys.exit(main())
