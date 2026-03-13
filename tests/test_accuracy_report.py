"""
Accuracy Report Schema, Traceability, and Integrity Tests
==========================================================

Phase 5 Plan 02 — validates accuracy_report.json and calibration_log.json
against their required schemas and traceability constraints.

Fixtures:
    accuracy_report  -- loaded from data/validation/accuracy_report.json
    calibration_log  -- loaded from data/validation/calibration_log.json
    ref_data         -- loaded from data/validation/reference_data.json

Tests:
    test_report_schema           -- required keys and types
    test_source_traceability     -- no physics_baseline.json; all sources valid
    test_summary_counts          -- summary counts match detailed metrics
    test_calibration_log_schema  -- calibration_log structure and integrity
    test_all_grades_valid        -- every grade is PASS/MARGINAL/FAIL/UNGRADED
    test_report_not_empty        -- at least 10 metrics (the 11+ documented ones)

Usage:
    python3 -m pytest tests/test_accuracy_report.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

# CadQuery/OCP mock MUST be set before any core/ imports
sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

ACCURACY_REPORT_PATH = REPO_ROOT / "data" / "validation" / "accuracy_report.json"
CALIBRATION_LOG_PATH = REPO_ROOT / "data" / "validation" / "calibration_log.json"
REF_DATA_PATH = REPO_ROOT / "data" / "validation" / "reference_data.json"

# Required metric-level keys
REQUIRED_METRIC_KEYS = {
    "metric_id",
    "description",
    "computed",
    "reference",
    "grade",
    "source",
    "units",
}

VALID_GRADES = {"PASS", "MARGINAL", "FAIL", "UNGRADED"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def accuracy_report() -> dict:
    """Load accuracy_report.json, skipping if not yet generated."""
    if not ACCURACY_REPORT_PATH.exists():
        pytest.skip(
            "accuracy_report.json not found — run scripts/generate_accuracy_report.py first"
        )
    with open(ACCURACY_REPORT_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def calibration_log() -> dict:
    """Load calibration_log.json, skipping if not yet created."""
    if not CALIBRATION_LOG_PATH.exists():
        pytest.skip(
            "calibration_log.json not found — created during Phase 5 calibration"
        )
    with open(CALIBRATION_LOG_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def ref_data() -> dict:
    """Load reference_data.json (always present)."""
    with open(REF_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_report_schema(accuracy_report: dict) -> None:
    """Accuracy report must have required top-level structure and metric fields."""
    # Top-level keys
    assert "metadata" in accuracy_report, "Report missing 'metadata' key"
    assert "summary" in accuracy_report, "Report missing 'summary' key"
    assert "metrics" in accuracy_report, "Report missing 'metrics' key"

    # Metadata required fields
    metadata = accuracy_report["metadata"]
    assert "generated" in metadata, "metadata missing 'generated' timestamp"
    assert "vspaero_provenance" in metadata, "metadata missing 'vspaero_provenance'"

    # Summary required fields
    summary = accuracy_report["summary"]
    for key in ("total", "pass", "fail"):
        assert key in summary, f"summary missing '{key}' key"

    # Each metric must have required keys and correct types
    metrics = accuracy_report["metrics"]
    assert isinstance(metrics, list), "metrics must be a list"
    assert len(metrics) > 0, "metrics list must not be empty"

    for m in metrics:
        missing = REQUIRED_METRIC_KEYS - set(m.keys())
        assert not missing, (
            f"Metric '{m.get('metric_id', '?')}' missing required keys: {missing}"
        )
        # computed and reference must be numeric
        assert isinstance(m["computed"], (int, float)), (
            f"Metric '{m['metric_id']}' 'computed' must be numeric, got {type(m['computed'])}"
        )
        assert isinstance(m["reference"], (int, float)), (
            f"Metric '{m['metric_id']}' 'reference' must be numeric, got {type(m['reference'])}"
        )


def test_source_traceability(accuracy_report: dict, ref_data: dict) -> None:
    """
    Every metric source must trace to reference_data.json or vspaero_native.

    Hard constraints:
    - No source may contain "physics_baseline.json" (self-referential, forbidden)
    - Every source must start with "reference_data.json:" or equal "vspaero_native"
    """
    metrics = accuracy_report["metrics"]

    for m in metrics:
        metric_id = m.get("metric_id", "?")
        source = m.get("source", "")

        # Hard block: no physics_baseline.json sources
        assert "physics_baseline.json" not in source, (
            f"Metric '{metric_id}' source '{source}' references physics_baseline.json — "
            f"self-referential sources are forbidden. Traceability requirement violated."
        )

        # Source must start with reference_data.json: or equal vspaero_native
        assert source.startswith("reference_data.json:") or source == "vspaero_native", (
            f"Metric '{metric_id}' source '{source}' does not trace to "
            f"reference_data.json or vspaero_native. "
            f"All sources must have external provenance."
        )


def test_summary_counts(accuracy_report: dict) -> None:
    """
    Summary counts must exactly match the detailed metric grades.

    Verifies:
    - summary.total == len(metrics)
    - summary.pass == count of PASS grades in metrics
    - summary.marginal (if present) == count of MARGINAL grades
    - summary.fail == count of FAIL grades
    """
    metrics = accuracy_report["metrics"]
    summary = accuracy_report["summary"]

    # Count grades from the detailed metrics
    grade_counts: dict[str, int] = {
        "PASS": 0,
        "MARGINAL": 0,
        "FAIL": 0,
        "UNGRADED": 0,
    }
    for m in metrics:
        grade = m.get("grade", "UNGRADED")
        grade_counts[grade] = grade_counts.get(grade, 0) + 1

    assert summary["total"] == len(metrics), (
        f"summary.total={summary['total']} != len(metrics)={len(metrics)}"
    )
    assert summary["pass"] == grade_counts["PASS"], (
        f"summary.pass={summary['pass']} != counted PASS grades={grade_counts['PASS']}"
    )
    assert summary.get("marginal", 0) == grade_counts["MARGINAL"], (
        f"summary.marginal={summary.get('marginal', 0)} != counted MARGINAL={grade_counts['MARGINAL']}"
    )
    assert summary.get("fail", 0) == grade_counts["FAIL"], (
        f"summary.fail={summary.get('fail', 0)} != counted FAIL grades={grade_counts['FAIL']}"
    )
    assert summary.get("ungraded", 0) == grade_counts["UNGRADED"], (
        f"summary.ungraded={summary.get('ungraded', 0)} != counted UNGRADED={grade_counts['UNGRADED']}"
    )


def test_calibration_log_schema(calibration_log: dict) -> None:
    """
    Calibration log must have required structure and non-trivial changes.

    Verifies:
    - Top-level keys: metadata, calibrations
    - At least 1 calibration entry
    - Each calibration has: parameter, old_value, new_value, source
    - old_value != new_value (something actually changed)
    """
    assert "metadata" in calibration_log, "calibration_log missing 'metadata'"
    assert "calibrations" in calibration_log, "calibration_log missing 'calibrations'"

    calibrations = calibration_log["calibrations"]
    assert isinstance(calibrations, list), "'calibrations' must be a list"
    assert len(calibrations) >= 1, (
        "calibrations list must have at least 1 entry — Phase 5 must have changed something"
    )

    required_keys = {"parameter", "old_value", "new_value", "source"}
    for cal in calibrations:
        missing = required_keys - set(cal.keys())
        assert not missing, (
            f"Calibration entry '{cal.get('parameter', '?')}' missing keys: {missing}"
        )
        assert cal["old_value"] != cal["new_value"], (
            f"Calibration '{cal['parameter']}': old_value == new_value "
            f"({cal['old_value']}) — no actual change was made"
        )


def test_all_grades_valid(accuracy_report: dict) -> None:
    """Every metric grade must be one of PASS, MARGINAL, FAIL, UNGRADED."""
    metrics = accuracy_report["metrics"]
    for m in metrics:
        grade = m.get("grade")
        assert grade in VALID_GRADES, (
            f"Metric '{m.get('metric_id', '?')}' has invalid grade '{grade}'. "
            f"Expected one of: {sorted(VALID_GRADES)}"
        )


def test_report_not_empty(accuracy_report: dict) -> None:
    """
    Report must contain at least 10 metrics.

    The plan documents 12 validated metrics (NP, CG fwd/aft, static margin,
    stall speed, max gross weight, empty weight, canard/wing CLmax,
    canard/wing alpha_0L, wing area). Minimum 10 allows for future refactoring
    of borderline metrics without breaking the test.
    """
    metrics = accuracy_report["metrics"]
    assert len(metrics) >= 10, (
        f"Report has only {len(metrics)} metrics — expected at least 10. "
        f"All validated metrics (NP, CG fwd/aft, static margin, stall speed, "
        f"max gross weight, empty weight, CLmax x2, alpha_0L x2, wing area) must be present."
    )
