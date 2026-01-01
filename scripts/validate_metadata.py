"""Validate artifact metadata in output/.

Designed for CI to refuse artifacts lacking provenance.
"""
# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.metadata import REQUIRED_FIELDS


ARTIFACT_EXTENSIONS = {".step", ".stl", ".tap", ".gcode", ".dxf"}


def find_artifacts(output_dir: Path) -> Iterable[Path]:
    """Yield all artifacts under output_dir matching supported extensions."""
    if not output_dir.exists():
        return []

    return (
        path
        for path in output_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in ARTIFACT_EXTENSIONS
    )


def validate_metadata_file(artifact_path: Path) -> Tuple[bool, str]:
    """Validate metadata alongside an artifact."""
    metadata_path = artifact_path.parent / f"{artifact_path.stem}.metadata.json"
    if not metadata_path.exists():
        return False, f"Missing metadata for {artifact_path}"

    try:
        payload = json.loads(metadata_path.read_text())
    except json.JSONDecodeError:
        return False, f"Invalid JSON in {metadata_path}"

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        return False, f"Metadata missing fields {missing} for {artifact_path}"

    for key in ("revision", "config_hash", "contributor"):
        if not str(payload.get(key, "")).strip():
            return False, f"Metadata field '{key}' empty for {artifact_path}"

    if payload.get("artifact") != artifact_path.name:
        return False, f"Metadata artifact mismatch for {artifact_path}"

    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate output metadata")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Output directory to scan",
    )
    args = parser.parse_args()

    artifacts = list(find_artifacts(args.output))
    if not artifacts:
        print(f"No artifacts found under {args.output}. Nothing to validate.")
        return 0

    failures = []
    for artifact in artifacts:
        ok, reason = validate_metadata_file(artifact)
        if not ok:
            failures.append(reason)

    if failures:
        print("\nMETADATA VALIDATION FAILED:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print(f"Validated metadata for {len(artifacts)} artifact(s) in {args.output}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
