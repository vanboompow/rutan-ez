"""
Unit tests for generate_accuracy_report.py — RED phase (TDD Task 1).

Tests the core grade_metric and validate_sources logic before the full
implementation exists. Run with:
    python3 -m pytest tests/test_accuracy_report_unit.py -x -v
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# CadQuery/OCP mock MUST be set before any core/ imports
sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402


# ---------------------------------------------------------------------------
# Tests for grade_metric()
# ---------------------------------------------------------------------------


def test_grade_metric_pass():
    from scripts.generate_accuracy_report import grade_metric

    grade, err_abs, err_pct = grade_metric(109.0, 108.0, tolerance_abs=2.0)
    assert grade == "PASS"
    assert abs(err_abs - 1.0) < 1e-9
    assert err_pct > 0


def test_grade_metric_marginal():
    from scripts.generate_accuracy_report import grade_metric

    # Error = 2.5, tolerance = 2.0 → between 1x and 2x tolerance
    grade, err_abs, err_pct = grade_metric(110.5, 108.0, tolerance_abs=2.0)
    assert grade == "MARGINAL"
    assert abs(err_abs - 2.5) < 1e-9


def test_grade_metric_fail():
    from scripts.generate_accuracy_report import grade_metric

    # Error = 5.0, tolerance = 2.0 → exceeds 2x tolerance
    grade, err_abs, err_pct = grade_metric(113.0, 108.0, tolerance_abs=2.0)
    assert grade == "FAIL"
    assert abs(err_abs - 5.0) < 1e-9


def test_grade_metric_ungraded():
    from scripts.generate_accuracy_report import grade_metric

    # No tolerance specified → UNGRADED
    grade, err_abs, err_pct = grade_metric(1425.0, 1425.0)
    assert grade == "UNGRADED"


def test_grade_metric_exact_boundary_pass():
    from scripts.generate_accuracy_report import grade_metric

    # Error exactly at tolerance = PASS
    grade, err_abs, _ = grade_metric(110.0, 108.0, tolerance_abs=2.0)
    assert grade == "PASS"
    assert abs(err_abs - 2.0) < 1e-9


def test_grade_metric_exact_boundary_marginal():
    from scripts.generate_accuracy_report import grade_metric

    # Error exactly at 2x tolerance = MARGINAL (boundary inclusive)
    grade, err_abs, _ = grade_metric(112.0, 108.0, tolerance_abs=2.0)
    assert grade == "MARGINAL"
    assert abs(err_abs - 4.0) < 1e-9


def test_grade_metric_pct_tolerance():
    from scripts.generate_accuracy_report import grade_metric

    # Pct tolerance: 5% of 56 = 2.8; error = 1.0 → PASS
    grade, err_abs, err_pct = grade_metric(57.0, 56.0, tolerance_pct=5.0)
    assert grade == "PASS"
    assert abs(err_pct - (1.0 / 56.0 * 100.0)) < 1e-6


# ---------------------------------------------------------------------------
# Tests for validate_sources()
# ---------------------------------------------------------------------------


def test_validate_sources_raises_on_physics_baseline():
    from scripts.generate_accuracy_report import validate_sources

    report = {
        "metrics": [
            {
                "metric_id": "neutral_point_fs",
                "source": "physics_baseline.json:neutral_point",
            }
        ]
    }
    ref_data = {"aircraft_specs": {"neutral_point_fs": {}}, "airfoil_data": {}}
    with pytest.raises(ValueError, match="physics_baseline.json"):
        validate_sources(report, ref_data)


def test_validate_sources_raises_on_unknown_source():
    from scripts.generate_accuracy_report import validate_sources

    report = {
        "metrics": [
            {
                "metric_id": "foo_bar",
                "source": "some_random_file.json:foo_bar",
            }
        ]
    }
    ref_data = {"aircraft_specs": {"neutral_point_fs": {}}, "airfoil_data": {}}
    with pytest.raises(ValueError, match="not in valid source set"):
        validate_sources(report, ref_data)


def test_validate_sources_accepts_reference_data_source():
    from scripts.generate_accuracy_report import validate_sources

    report = {
        "metrics": [
            {
                "metric_id": "neutral_point_fs",
                "source": "reference_data.json:aircraft_specs.neutral_point_fs",
            }
        ]
    }
    ref_data = {"aircraft_specs": {"neutral_point_fs": {}}, "airfoil_data": {}}
    # Should not raise
    validate_sources(report, ref_data)


def test_validate_sources_accepts_vspaero_native():
    from scripts.generate_accuracy_report import validate_sources

    report = {
        "metrics": [
            {
                "metric_id": "some_polar_metric",
                "source": "vspaero_native",
            }
        ]
    }
    ref_data = {"aircraft_specs": {}, "airfoil_data": {}}
    # Should not raise
    validate_sources(report, ref_data)
