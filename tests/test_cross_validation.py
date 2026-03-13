"""
Schema Validation Tests for Surrogate Cross-Validation JSON
=============================================================

Validates the structure and integrity of:
  - data/validation/vspaero_native_polars.json  (real VSPAERO VLM output)
  - data/validation/surrogate_cross_validation.json  (native vs. surrogate
    discrepancy table)

IMPORTANT: These tests are measure-only schema checks. They do NOT assert
pass/fail thresholds on CL/CD/CM discrepancy values. Per Phase 4 CONTEXT.md
locked decision: cross-validation is measure-only; Phase 5 decides calibration.

No OpenVSP imports, no physics computations — pure JSON schema validation.
Runs in the default Python environment (no openvsp required).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Standard preamble: make REPO_ROOT importable and mock CadQuery
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# CadQuery mock — required before any core/ imports (none used here, but keeps
# the pattern consistent with all other tests in this suite)
sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

DATA_DIR = REPO_ROOT / "data" / "validation"
NATIVE_POLARS_PATH = DATA_DIR / "vspaero_native_polars.json"
CROSS_VAL_PATH = DATA_DIR / "surrogate_cross_validation.json"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def native_polars() -> dict:
    """Load vspaero_native_polars.json once for the test module."""
    assert NATIVE_POLARS_PATH.exists(), (
        f"Native polars file not found: {NATIVE_POLARS_PATH}\n"
        "Run: python3.13 scripts/generate_cross_validation.py"
    )
    with open(NATIVE_POLARS_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def cross_validation() -> dict:
    """Load surrogate_cross_validation.json once for the test module."""
    assert CROSS_VAL_PATH.exists(), (
        f"Cross-validation file not found: {CROSS_VAL_PATH}\n"
        "Run: python3.13 scripts/generate_cross_validation.py"
    )
    with open(CROSS_VAL_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Test 1: Native polars must not be mock data
# ---------------------------------------------------------------------------


def test_native_polars_not_mock(native_polars: dict) -> None:
    """vspaero_native_polars.json must contain a real VSPAERO version string.

    Guards against regression back to mock data. Any version string containing
    'mock' indicates the real VSPAERO solver was not used.
    """
    vsp_version = native_polars.get("vsp_version", "")
    assert "mock" not in vsp_version.lower(), (
        f"vsp_version '{vsp_version}' contains 'mock'. "
        "Regenerate with: python3.13 scripts/generate_cross_validation.py"
    )
    # Must be non-empty
    assert vsp_version, "vsp_version is empty"


# ---------------------------------------------------------------------------
# Test 2: Native polars has exactly 19 points covering -4 to 14 degrees
# ---------------------------------------------------------------------------


def test_native_polars_has_19_points(native_polars: dict) -> None:
    """Native polars must have exactly 19 alpha points from -4 to 14 degrees."""
    points = native_polars.get("points", [])
    assert len(points) == 19, (
        f"Expected 19 polar points, got {len(points)}"
    )

    alphas = [p["alpha_deg"] for p in points]
    assert min(alphas) == pytest.approx(-4.0, abs=0.1), (
        f"Alpha min expected -4.0, got {min(alphas)}"
    )
    assert max(alphas) == pytest.approx(14.0, abs=0.1), (
        f"Alpha max expected 14.0, got {max(alphas)}"
    )

    # Each point must have required aerodynamic keys
    required_keys = {"alpha_deg", "cl", "cd", "cm"}
    for i, pt in enumerate(points):
        missing = required_keys - pt.keys()
        assert not missing, f"Point {i} missing keys: {missing}"


# ---------------------------------------------------------------------------
# Test 3: Cross-validation JSON exists with required schema
# ---------------------------------------------------------------------------


def test_cross_validation_json_exists_and_valid(cross_validation: dict) -> None:
    """surrogate_cross_validation.json must have required top-level keys.

    Required structure:
      - metadata: dict with generation info
      - comparison: non-empty list of per-alpha dicts
      - summary: dict with cl/cd/cm sub-dicts containing mean/rms/max stats
    """
    # Top-level keys
    required_top = {"metadata", "comparison", "summary"}
    missing_top = required_top - cross_validation.keys()
    assert not missing_top, f"Cross-validation JSON missing keys: {missing_top}"

    # comparison must be a non-empty list
    comparison = cross_validation["comparison"]
    assert isinstance(comparison, list), "comparison must be a list"
    assert len(comparison) > 0, "comparison list must not be empty"

    # Each comparison entry must have the expected columns
    required_cols = {
        "alpha_deg",
        "cl_native", "cl_surrogate", "cl_delta",
        "cd_native", "cd_surrogate", "cd_delta",
        "cm_native", "cm_surrogate", "cm_delta",
    }
    for i, entry in enumerate(comparison):
        missing_cols = required_cols - entry.keys()
        assert not missing_cols, f"comparison[{i}] missing columns: {missing_cols}"

    # summary must have cl, cd, cm with the three stat fields
    summary = cross_validation["summary"]
    required_metrics = {"cl", "cd", "cm"}
    missing_metrics = required_metrics - summary.keys()
    assert not missing_metrics, f"summary missing metrics: {missing_metrics}"

    required_stat_fields = {"mean_delta", "rms_delta", "max_abs_delta"}
    for metric in required_metrics:
        stat = summary[metric]
        missing_stats = required_stat_fields - stat.keys()
        assert not missing_stats, (
            f"summary[{metric}] missing fields: {missing_stats}"
        )
        # Stats must be finite numbers
        for field in required_stat_fields:
            val = stat[field]
            assert isinstance(val, (int, float)), (
                f"summary[{metric}][{field}] must be numeric, got {type(val)}"
            )


# ---------------------------------------------------------------------------
# Test 4: Alpha arrays in native polars and cross-validation must match
# ---------------------------------------------------------------------------


def test_cross_validation_alpha_arrays_match(
    native_polars: dict,
    cross_validation: dict,
) -> None:
    """Alpha arrays in vspaero_native_polars.json and surrogate_cross_validation.json
    must match — same count and same alpha values — for a valid comparison.
    """
    native_alphas = sorted(p["alpha_deg"] for p in native_polars["points"])
    cv_alphas = sorted(cross_validation["alpha_deg"])

    assert len(native_alphas) == len(cv_alphas), (
        f"Alpha count mismatch: native={len(native_alphas)}, "
        f"cross-val={len(cv_alphas)}"
    )

    for i, (nat, cv) in enumerate(zip(native_alphas, cv_alphas)):
        assert nat == pytest.approx(cv, abs=0.01), (
            f"Alpha mismatch at index {i}: native={nat}, cross-val={cv}"
        )


# ---------------------------------------------------------------------------
# Test 5: Documentation marker — no accuracy thresholds enforced
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="Documentation marker — no assertions needed")
def test_cross_validation_no_pass_fail_assertions() -> None:
    """Cross-validation is measure-only per Phase 4 CONTEXT.md.

    No accuracy thresholds are enforced in this test suite.
    Discrepancy data (CL/CD/CM deltas) is recorded in
    data/validation/surrogate_cross_validation.json for Phase 5 review.
    Phase 5 will decide calibration priorities based on these measurements.

    See: .planning/phases/04-validation-test-infrastructure-cross-validation/
         04-CONTEXT.md — locked decision: measure-only, no pass/fail.
    """
    pass
