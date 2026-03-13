"""
Generate Accuracy Report: Per-Metric Grading Against External Reference Data
=============================================================================

This script grades every validated Long-EZ metric (NP, CG fwd/aft, static margin,
stall speed, CLmax, alpha_0L, weights, wing area) against curated values from
reference_data.json and vspaero_native_polars.json. No self-referential sources
(physics_baseline.json) are permitted.

Output: data/validation/accuracy_report.json

Purpose: Provide the machine-readable accuracy report Phase 6 uses to lock
regression tests. Traceability enforcement breaks the self-referential
validation loop established by physics_baseline.json.

Usage:
    cd /path/to/open-ez
    python3 scripts/generate_accuracy_report.py
    python3 main.py --accuracy-report   (identical output)
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

# --- CadQuery/OCP mock MUST be set before any core/ imports -----------------
# Analysis modules import CadQuery lazily. Without this mock, importing
# core.analysis raises ImportError in environments without CadQuery installed.
sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Core grading logic
# ---------------------------------------------------------------------------


def grade_metric(
    computed: float,
    reference: float,
    tolerance_abs: float | None = None,
    tolerance_pct: float | None = None,
) -> tuple[str, float, float]:
    """
    Grade a computed metric against a reference value.

    Grading bands:
        PASS:      error <= tolerance
        MARGINAL:  tolerance < error <= 2 * tolerance
        FAIL:      error > 2 * tolerance
        UNGRADED:  no tolerance specified

    Args:
        computed: Computed value from the physics model.
        reference: Reference (published / wind-tunnel) value.
        tolerance_abs: Absolute tolerance (same units as values).
        tolerance_pct: Percentage tolerance (0-100 scale, e.g. 5.0 = 5%).
            Only used if tolerance_abs is None.

    Returns:
        Tuple of (grade_str, error_abs, error_pct) where:
            - grade_str: one of "PASS", "MARGINAL", "FAIL", "UNGRADED"
            - error_abs: absolute error |computed - reference|
            - error_pct: percentage error (relative to |reference|), 0.0 if reference==0
    """
    error_abs = abs(computed - reference)
    if reference != 0.0:
        error_pct = error_abs / abs(reference) * 100.0
    else:
        error_pct = 0.0

    # Determine which tolerance band to use
    if tolerance_abs is not None:
        tol = tolerance_abs
        error_for_grading = error_abs
    elif tolerance_pct is not None:
        tol = tolerance_pct
        error_for_grading = error_pct
    else:
        return ("UNGRADED", round(error_abs, 6), round(error_pct, 6))

    if error_for_grading <= tol:
        grade = "PASS"
    elif error_for_grading <= 2.0 * tol:
        grade = "MARGINAL"
    else:
        grade = "FAIL"

    return (grade, round(error_abs, 6), round(error_pct, 6))


def validate_sources(report: dict, ref_data: dict) -> None:
    """
    Validate that all metric sources in the report are traceable and not self-referential.

    Raises:
        ValueError: If any metric source:
            - Contains "physics_baseline.json" (self-referential, forbidden)
            - Is not a recognized reference_data.json key or "vspaero_native"

    Args:
        report: The accuracy report dict (must have "metrics" list).
        ref_data: The loaded reference_data.json dict.
    """
    # Build valid source set from reference_data.json keys
    valid_sources: set[str] = {"vspaero_native"}
    for section in ("aircraft_specs", "airfoil_data"):
        section_data = ref_data.get(section, {})
        for top_key, top_val in section_data.items():
            # Top-level key: e.g. reference_data.json:aircraft_specs.neutral_point_fs
            valid_sources.add(f"reference_data.json:{section}.{top_key}")
            # Also allow nested keys (e.g. airfoil_data.roncz_r1145ms.cl_max)
            if isinstance(top_val, dict):
                for sub_key in top_val:
                    valid_sources.add(
                        f"reference_data.json:{section}.{top_key}.{sub_key}"
                    )

    for metric in report.get("metrics", []):
        source = metric.get("source", "")
        if "physics_baseline.json" in source:
            raise ValueError(
                f"Metric '{metric.get('metric_id')}' source '{source}' references "
                f"physics_baseline.json — self-referential sources are forbidden. "
                f"All sources must trace to reference_data.json or vspaero_native."
            )
        if source not in valid_sources:
            raise ValueError(
                f"Metric '{metric.get('metric_id')}' source '{source}' "
                f"not in valid source set. Expected one of: {sorted(valid_sources)[:5]}..."
            )


def load_vspaero_provenance(data_dir: Path) -> dict:
    """
    Load VSPAERO provenance metadata from vspaero_native_polars.json.

    Returns a dict with vsp_version, run_timestamp, solver_settings.
    Falls back to a placeholder dict if the file is missing.

    Args:
        data_dir: Directory containing vspaero_native_polars.json.

    Returns:
        Dict with provenance metadata.
    """
    polars_path = data_dir / "vspaero_native_polars.json"
    if not polars_path.exists():
        return {
            "vsp_version": "not_available",
            "run_timestamp": "not_available",
            "solver_settings": {},
            "note": "vspaero_native_polars.json not found — no native VSPAERO data",
        }

    with open(polars_path, encoding="utf-8") as f:
        polars = json.load(f)

    return {
        "vsp_version": polars.get("vsp_version", "unknown"),
        "run_timestamp": polars.get("timestamp", "unknown"),
        "solver_settings": polars.get("solver_settings", {}),
    }


def collect_metrics(
    ref_data: dict,
    config_module: object,
    engine: object,
) -> list[dict]:
    """
    Compute all validated metrics and assemble metric dicts.

    Each metric dict contains:
        metric_id, description, computed, reference, tolerance_abs, tolerance_pct,
        error_abs, error_pct, grade, source, units

    Args:
        ref_data: Loaded reference_data.json.
        config_module: The config module (config object with .geometry, .aero_limits, etc.).
        engine: PhysicsEngine instance with .calculate_cg_envelope() method.

    Returns:
        List of metric dicts.
    """
    metrics: list[dict] = []
    specs = ref_data["aircraft_specs"]
    airfoils = ref_data["airfoil_data"]
    geo = config_module.geometry  # type: ignore[attr-defined]

    # -------------------------------------------------------------------------
    # Stability metrics (from PhysicsEngine)
    # -------------------------------------------------------------------------
    stability = engine.calculate_cg_envelope()  # type: ignore[union-attr]

    # --- Neutral Point ---
    np_ref_entry = specs["neutral_point_fs"]
    computed_np_pub = geo.to_published_datum(stability.neutral_point)
    np_grade, np_err_abs, np_err_pct = grade_metric(
        computed_np_pub,
        np_ref_entry["value"],
        tolerance_abs=np_ref_entry.get("tolerance_abs"),
        tolerance_pct=np_ref_entry.get("tolerance_pct"),
    )
    metrics.append(
        {
            "metric_id": "neutral_point_fs",
            "description": "Longitudinal Neutral Point (published datum)",
            "computed": round(computed_np_pub, 4),
            "reference": np_ref_entry["value"],
            "tolerance_abs": np_ref_entry.get("tolerance_abs"),
            "tolerance_pct": np_ref_entry.get("tolerance_pct"),
            "error_abs": np_err_abs,
            "error_pct": np_err_pct,
            "grade": np_grade,
            "source": "reference_data.json:aircraft_specs.neutral_point_fs",
            "units": "inches (published FS datum)",
        }
    )

    # --- CG Forward Limit ---
    cg_fwd_entry = specs["cg_range_fwd_fs"]
    computed_cg_fwd_pub = geo.to_published_datum(stability.cg_range_fwd)
    cg_fwd_grade, cg_fwd_err_abs, cg_fwd_err_pct = grade_metric(
        computed_cg_fwd_pub,
        cg_fwd_entry["value"],
        tolerance_abs=cg_fwd_entry.get("tolerance_abs"),
        tolerance_pct=cg_fwd_entry.get("tolerance_pct"),
    )
    metrics.append(
        {
            "metric_id": "cg_range_fwd_fs",
            "description": "Forward CG limit (published datum)",
            "computed": round(computed_cg_fwd_pub, 4),
            "reference": cg_fwd_entry["value"],
            "tolerance_abs": cg_fwd_entry.get("tolerance_abs"),
            "tolerance_pct": cg_fwd_entry.get("tolerance_pct"),
            "error_abs": cg_fwd_err_abs,
            "error_pct": cg_fwd_err_pct,
            "grade": cg_fwd_grade,
            "source": "reference_data.json:aircraft_specs.cg_range_fwd_fs",
            "units": "inches (published FS datum)",
        }
    )

    # --- CG Aft Limit ---
    cg_aft_entry = specs["cg_range_aft_fs"]
    computed_cg_aft_pub = geo.to_published_datum(stability.cg_range_aft)
    cg_aft_grade, cg_aft_err_abs, cg_aft_err_pct = grade_metric(
        computed_cg_aft_pub,
        cg_aft_entry["value"],
        tolerance_abs=cg_aft_entry.get("tolerance_abs"),
        tolerance_pct=cg_aft_entry.get("tolerance_pct"),
    )
    metrics.append(
        {
            "metric_id": "cg_range_aft_fs",
            "description": "Aft CG limit (published datum)",
            "computed": round(computed_cg_aft_pub, 4),
            "reference": cg_aft_entry["value"],
            "tolerance_abs": cg_aft_entry.get("tolerance_abs"),
            "tolerance_pct": cg_aft_entry.get("tolerance_pct"),
            "error_abs": cg_aft_err_abs,
            "error_pct": cg_aft_err_pct,
            "grade": cg_aft_grade,
            "source": "reference_data.json:aircraft_specs.cg_range_aft_fs",
            "units": "inches (published FS datum)",
        }
    )

    # --- Static Margin ---
    sm_entry = specs["static_margin_pct"]
    # StabilityMetrics.static_margin is already stored in percent (margin * 100.0
    # at analysis.py line 367). Do NOT multiply by 100 again.
    computed_sm = stability.static_margin
    sm_grade, sm_err_abs, sm_err_pct = grade_metric(
        computed_sm,
        sm_entry["value"],
        tolerance_abs=sm_entry.get("tolerance_abs"),
        tolerance_pct=sm_entry.get("tolerance_pct"),
    )
    metrics.append(
        {
            "metric_id": "static_margin_pct",
            "description": "Longitudinal static margin (% MAC)",
            "computed": round(computed_sm, 4),
            "reference": sm_entry["value"],
            "tolerance_abs": sm_entry.get("tolerance_abs"),
            "tolerance_pct": sm_entry.get("tolerance_pct"),
            "error_abs": sm_err_abs,
            "error_pct": sm_err_pct,
            "grade": sm_grade,
            "source": "reference_data.json:aircraft_specs.static_margin_pct",
            "units": "percent MAC",
        }
    )

    # -------------------------------------------------------------------------
    # Performance metrics
    # -------------------------------------------------------------------------

    # --- Stall Speed (first-principles, published reference areas) ---
    stall_entry = specs["stall_speed_ktas"]
    wing_area_sqft = specs["wing_area_sqft"]["value"]  # 94.2 sqft (published)
    canard_area_sqft = specs["canard_area_sqft"]["value"]  # 15.6 sqft (published)
    total_area_sqft = wing_area_sqft + canard_area_sqft
    W = config_module.flight_condition.gross_weight_lb  # type: ignore[attr-defined]
    rho = 0.002377  # slug/ft^3 sea-level standard atmosphere
    cl_max = config_module.aero_limits.canard_clmax  # type: ignore[attr-defined]  # canard stalls first
    v_fps = math.sqrt(2.0 * W / (rho * total_area_sqft * cl_max))
    computed_stall_ktas = v_fps / 1.6878  # 1 knot = 1.6878 ft/s

    stall_grade, stall_err_abs, stall_err_pct = grade_metric(
        computed_stall_ktas,
        stall_entry["value"],
        tolerance_abs=stall_entry.get("tolerance_abs"),
        tolerance_pct=stall_entry.get("tolerance_pct"),
    )
    metrics.append(
        {
            "metric_id": "stall_speed_ktas",
            "description": "Canard stall speed at gross weight (first-principles, published areas)",
            "computed": round(computed_stall_ktas, 4),
            "reference": stall_entry["value"],
            "tolerance_abs": stall_entry.get("tolerance_abs"),
            "tolerance_pct": stall_entry.get("tolerance_pct"),
            "error_abs": stall_err_abs,
            "error_pct": stall_err_pct,
            "grade": stall_grade,
            "source": "reference_data.json:aircraft_specs.stall_speed_ktas",
            "units": "knots TAS",
            "convention_note": (
                f"Uses published reference areas: "
                f"wing={wing_area_sqft} sqft + canard={canard_area_sqft} sqft = "
                f"{total_area_sqft} sqft. CLmax={cl_max} (canard stalls first)."
            ),
        }
    )

    # --- Max Gross Weight (exact match — no tolerance in reference_data) ---
    mgw_entry = specs["max_gross_weight_lb"]
    computed_mgw = config_module.flight_condition.gross_weight_lb  # type: ignore[attr-defined]
    # tolerance_abs=null in reference_data → use exact match (tolerance_abs=0.0)
    mgw_grade, mgw_err_abs, mgw_err_pct = grade_metric(
        computed_mgw,
        mgw_entry["value"],
        tolerance_abs=0.0,  # exact match required (FAA-approved hard limit)
        tolerance_pct=None,
    )
    metrics.append(
        {
            "metric_id": "max_gross_weight_lb",
            "description": "Maximum gross weight (FAA-approved, hard limit)",
            "computed": round(computed_mgw, 4),
            "reference": mgw_entry["value"],
            "tolerance_abs": 0.0,
            "tolerance_pct": None,
            "error_abs": mgw_err_abs,
            "error_pct": mgw_err_pct,
            "grade": mgw_grade,
            "source": "reference_data.json:aircraft_specs.max_gross_weight_lb",
            "units": "pounds",
        }
    )

    # --- Empty Weight ---
    ew_entry = specs["empty_weight_lb"]
    sw = config_module.structural_weights  # type: ignore[attr-defined]
    # Sum all structural component weights from config
    computed_empty_weight = (
        sw.wing_weight_lb
        + sw.canard_weight_lb
        + sw.fuselage_weight_lb
        + sw.landing_gear_weight_lb
        + sw.electrical_weight_lb
        + sw.instruments_weight_lb
        + sw.interior_weight_lb
        # Engine/propulsion: O-235 standard weights
        + 250.0  # Engine (O-235)
        + 25.0   # Prop & Spinner
        + 30.0   # Engine Accessories
    )
    ew_grade, ew_err_abs, ew_err_pct = grade_metric(
        computed_empty_weight,
        ew_entry["value"],
        tolerance_abs=ew_entry.get("tolerance_abs"),
        tolerance_pct=ew_entry.get("tolerance_pct"),
    )
    metrics.append(
        {
            "metric_id": "empty_weight_lb",
            "description": "Estimated empty weight (structural + propulsion components)",
            "computed": round(computed_empty_weight, 4),
            "reference": ew_entry["value"],
            "tolerance_abs": ew_entry.get("tolerance_abs"),
            "tolerance_pct": ew_entry.get("tolerance_pct"),
            "error_abs": ew_err_abs,
            "error_pct": ew_err_pct,
            "grade": ew_grade,
            "source": "reference_data.json:aircraft_specs.empty_weight_lb",
            "units": "pounds",
        }
    )

    # -------------------------------------------------------------------------
    # Airfoil metrics (from config.aero_limits, against wind tunnel reference)
    # -------------------------------------------------------------------------

    # --- Canard CLmax (Roncz R1145MS) ---
    roncz_clmax_entry = airfoils["roncz_r1145ms"]["cl_max"]
    computed_canard_clmax = config_module.aero_limits.canard_clmax  # type: ignore[attr-defined]
    c_clmax_grade, c_clmax_err_abs, c_clmax_err_pct = grade_metric(
        computed_canard_clmax,
        roncz_clmax_entry["value"],
        tolerance_abs=0.05,   # Matching test_precision_validation.py
        tolerance_pct=None,
    )
    metrics.append(
        {
            "metric_id": "canard_clmax",
            "description": "Canard (Roncz R1145MS) maximum lift coefficient",
            "computed": round(computed_canard_clmax, 6),
            "reference": roncz_clmax_entry["value"],
            "tolerance_abs": 0.05,
            "tolerance_pct": None,
            "error_abs": c_clmax_err_abs,
            "error_pct": c_clmax_err_pct,
            "grade": c_clmax_grade,
            "source": "reference_data.json:airfoil_data.roncz_r1145ms.cl_max",
            "units": "dimensionless",
        }
    )

    # --- Wing CLmax (Eppler 1230) ---
    eppler_clmax_entry = airfoils["eppler_1230"]["cl_max"]
    computed_wing_clmax = config_module.aero_limits.wing_clmax  # type: ignore[attr-defined]
    w_clmax_grade, w_clmax_err_abs, w_clmax_err_pct = grade_metric(
        computed_wing_clmax,
        eppler_clmax_entry["value"],
        tolerance_abs=0.05,   # Matching test_precision_validation.py
        tolerance_pct=None,
    )
    metrics.append(
        {
            "metric_id": "wing_clmax",
            "description": "Main wing (Eppler 1230) maximum lift coefficient",
            "computed": round(computed_wing_clmax, 6),
            "reference": eppler_clmax_entry["value"],
            "tolerance_abs": 0.05,
            "tolerance_pct": None,
            "error_abs": w_clmax_err_abs,
            "error_pct": w_clmax_err_pct,
            "grade": w_clmax_grade,
            "source": "reference_data.json:airfoil_data.eppler_1230.cl_max",
            "units": "dimensionless",
        }
    )

    # --- Canard alpha_0L (Roncz R1145MS) ---
    roncz_a0l_entry = airfoils["roncz_r1145ms"]["alpha_zero_lift_deg"]
    computed_canard_alpha_0l = config_module.aero_limits.canard_alpha_0L  # type: ignore[attr-defined]
    c_a0l_grade, c_a0l_err_abs, c_a0l_err_pct = grade_metric(
        computed_canard_alpha_0l,
        roncz_a0l_entry["value"],
        tolerance_abs=0.5,    # Matching test_precision_validation.py (degrees)
        tolerance_pct=None,
    )
    metrics.append(
        {
            "metric_id": "canard_alpha_0l_deg",
            "description": "Canard (Roncz R1145MS) zero-lift angle of attack",
            "computed": round(computed_canard_alpha_0l, 6),
            "reference": roncz_a0l_entry["value"],
            "tolerance_abs": 0.5,
            "tolerance_pct": None,
            "error_abs": c_a0l_err_abs,
            "error_pct": c_a0l_err_pct,
            "grade": c_a0l_grade,
            "source": "reference_data.json:airfoil_data.roncz_r1145ms.alpha_zero_lift_deg",
            "units": "degrees",
        }
    )

    # --- Wing alpha_0L (Eppler 1230) ---
    eppler_a0l_entry = airfoils["eppler_1230"]["alpha_zero_lift_deg"]
    computed_wing_alpha_0l = config_module.aero_limits.wing_alpha_0L  # type: ignore[attr-defined]
    w_a0l_grade, w_a0l_err_abs, w_a0l_err_pct = grade_metric(
        computed_wing_alpha_0l,
        eppler_a0l_entry["value"],
        tolerance_abs=0.5,    # Matching test_precision_validation.py (degrees)
        tolerance_pct=None,
    )
    metrics.append(
        {
            "metric_id": "wing_alpha_0l_deg",
            "description": "Main wing (Eppler 1230) zero-lift angle of attack",
            "computed": round(computed_wing_alpha_0l, 6),
            "reference": eppler_a0l_entry["value"],
            "tolerance_abs": 0.5,
            "tolerance_pct": None,
            "error_abs": w_a0l_err_abs,
            "error_pct": w_a0l_err_pct,
            "grade": w_a0l_grade,
            "source": "reference_data.json:airfoil_data.eppler_1230.alpha_zero_lift_deg",
            "units": "degrees",
        }
    )

    # -------------------------------------------------------------------------
    # Geometry metrics
    # -------------------------------------------------------------------------

    # --- Wing Area ---
    wing_area_entry = specs["wing_area_sqft"]
    computed_wing_area_sqft = geo.wing_area  # config.geometry.wing_area (already in sqft)
    wa_grade, wa_err_abs, wa_err_pct = grade_metric(
        computed_wing_area_sqft,
        wing_area_entry["value"],
        tolerance_abs=wing_area_entry.get("tolerance_abs"),
        tolerance_pct=wing_area_entry.get("tolerance_pct"),
    )
    metrics.append(
        {
            "metric_id": "wing_area_sqft",
            "description": "Main wing planform area",
            "computed": round(computed_wing_area_sqft, 4),
            "reference": wing_area_entry["value"],
            "tolerance_abs": wing_area_entry.get("tolerance_abs"),
            "tolerance_pct": wing_area_entry.get("tolerance_pct"),
            "error_abs": wa_err_abs,
            "error_pct": wa_err_pct,
            "grade": wa_grade,
            "source": "reference_data.json:aircraft_specs.wing_area_sqft",
            "units": "square feet",
            "convention_note": (
                "Code computes full trapezoidal planform area (~110 sqft). "
                "Published reference uses RAF semi-panel convention (94.2 sqft). "
                "FAIL grade expected — convention difference, not a physics error. "
                "See reference_data.json notes for full explanation."
            ),
        }
    )

    return metrics


def build_report(metrics: list[dict], vspaero_provenance: dict) -> dict:
    """
    Build the full accuracy report dict from graded metrics and provenance.

    Args:
        metrics: List of graded metric dicts from collect_metrics().
        vspaero_provenance: VSPAERO provenance dict from load_vspaero_provenance().

    Returns:
        Complete accuracy report dict ready for JSON serialization.
    """
    # Count grades
    grade_counts: dict[str, int] = {"pass": 0, "marginal": 0, "fail": 0, "ungraded": 0}
    for m in metrics:
        g = m["grade"].lower()
        if g in grade_counts:
            grade_counts[g] += 1

    return {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "vspaero_provenance": vspaero_provenance,
            "traceability": (
                "All metric sources trace to reference_data.json (external published/measured) "
                "or vspaero_native. No sources from physics_baseline.json (self-referential). "
                "Verified by validate_sources() at generation time."
            ),
        },
        "summary": {
            "total": len(metrics),
            "pass": grade_counts["pass"],
            "marginal": grade_counts["marginal"],
            "fail": grade_counts["fail"],
            "ungraded": grade_counts["ungraded"],
        },
        "metrics": metrics,
    }


def generate_accuracy_report(output_path: Path | None = None) -> Path:
    """
    Main entry point: generate accuracy_report.json.

    Loads reference data, runs the physics engine, grades all validated metrics,
    enforces source traceability, and writes the report.

    Args:
        output_path: Optional output path override. Defaults to
            <repo_root>/data/validation/accuracy_report.json.

    Returns:
        Path where the report was written.

    Raises:
        ValueError: If any metric source resolves to physics_baseline.json.
    """
    from config import config  # noqa: E402 — deferred import for CadQuery mock safety
    from core.analysis import PhysicsEngine  # noqa: E402

    data_dir = REPO_ROOT / "data" / "validation"
    data_dir.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = data_dir / "accuracy_report.json"

    # Load reference data
    ref_data_path = data_dir / "reference_data.json"
    with open(ref_data_path, encoding="utf-8") as f:
        ref_data = json.load(f)

    # Load VSPAERO provenance
    vspaero_provenance = load_vspaero_provenance(data_dir)

    # Instantiate physics engine and collect metrics
    engine = PhysicsEngine()
    metrics = collect_metrics(ref_data, config, engine)

    # Build report structure
    report = build_report(metrics, vspaero_provenance)

    # Enforce traceability — raises ValueError on violations
    validate_sources(report, ref_data)

    # Write JSON output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return output_path


def main() -> None:
    """CLI entry point: generate accuracy report and print summary to stdout."""
    report_path = generate_accuracy_report()

    # Load and print summary
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    summary = report["summary"]
    print(f"\nAccuracy Report: {report_path}")
    print(f"Generated: {report['metadata']['generated']}")
    print(f"\nSummary ({summary['total']} metrics):")
    print(f"  PASS:     {summary['pass']}")
    print(f"  MARGINAL: {summary['marginal']}")
    print(f"  FAIL:     {summary['fail']}")
    print(f"  UNGRADED: {summary['ungraded']}")
    print()

    # Print metric table
    print(f"{'Metric ID':<35} {'Grade':<10} {'Computed':>12} {'Reference':>12} {'Error Abs':>12}")
    print("-" * 90)
    for m in report["metrics"]:
        print(
            f"{m['metric_id']:<35} "
            f"{m['grade']:<10} "
            f"{m['computed']:>12.4f} "
            f"{m['reference']:>12.4f} "
            f"{m['error_abs']:>12.4f}"
        )


if __name__ == "__main__":
    main()
