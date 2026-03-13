"""
Precision Validation Tests: Phase 4/5 Calibrated Tolerance Targets
===================================================================

Encodes precision tolerances for calibrated Long-EZ physics model:
  - VAL-01: Stability (NP, CG fwd, CG aft) at 2"/1" tolerance vs. published Long-EZ specs
  - VAL-02: Airfoil config values (CLmax, alpha_0L) vs. wind tunnel reference data
  - VAL-04: Performance (stall speed, gross weight) vs. published specs

PURPOSE: Active precision validation. VAL-01 tests pass after Phase 5 calibration of
fs_wing_le (133.0 → 125.61) and CG margin percentages (17.21%/7.65% from Rutan CP-29).
All four previously-xfail tests now pass as normal assertions. See calibration_log.json.

DO NOT MODIFY existing tests in test_physics_external_validation.py or
test_datum_resolution.py — those are sanity checks with generous tolerances.
This file provides precision measurement at calibrated tolerances.
"""

import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from unittest.mock import MagicMock  # noqa: E402

sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

import pytest  # noqa: E402

from config import config  # noqa: E402

REF_DATA_PATH = REPO_ROOT / "data" / "validation" / "reference_data.json"


def _load_ref_data() -> dict:
    """Load reference_data.json from the repository root."""
    with open(REF_DATA_PATH) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# VAL-01: Stability precision (NP, CG fwd, CG aft) — calibrated Phase 5
# ---------------------------------------------------------------------------


# Resolved Phase 5: calibrated fs_wing_le from NP delta analysis (delta <2")
def test_np_precision_2inch():
    """VAL-01: Computed NP translated to published datum must be within 2\" of 108.0.

    Known status: XFAIL. The config.geometry.fs_wing_le=133 uses an internal datum
    value that places NP ~5.79\" aft of the published value. Phase 5 corrects this
    by calibrating fs_wing_le against the published FS datum.

    This test documents:
      - Target tolerance: 2.0\" (from reference_data.json neutral_point_fs.tolerance_abs)
      - Reference value: 108.0\" (published FS datum, RAF CP-29)
      - Expected delta until Phase 5 fixes: ~5.79\"
    """
    from core.analysis import PhysicsEngine

    data = _load_ref_data()
    ref_np = data["aircraft_specs"]["neutral_point_fs"]["value"]
    tolerance = data["aircraft_specs"]["neutral_point_fs"]["tolerance_abs"]

    engine = PhysicsEngine()
    metrics = engine.calculate_cg_envelope()
    computed_np_published = config.geometry.to_published_datum(metrics.neutral_point)
    delta = abs(computed_np_published - ref_np)

    assert delta <= tolerance, (
        f"NP precision check FAILED (expected for Phase 4): "
        f"computed NP = {computed_np_published:.2f}\" (published datum), "
        f"reference = {ref_np:.1f}\", delta = {delta:.2f}\" exceeds {tolerance:.1f}\" tolerance. "
        f"Internal NP = {metrics.neutral_point:.2f}\". "
        f"Phase 5 target: calibrate fs_wing_le to reduce delta to <{tolerance:.1f}\"."
    )


# Resolved Phase 5: calibrated fs_wing_le corrects CG fwd limit (delta <1")
def test_cg_fwd_limit_precision():
    """VAL-01: Computed CG forward limit (published datum) must be within 1\" of 99.0.

    Known status: XFAIL. The same fs_wing_le datum error that affects NP also
    shifts the computed CG envelope fwd limit away from the published 99.0\" FS.

    This test documents:
      - Target tolerance: 1.0\" (from reference_data.json cg_range_fwd_fs.tolerance_abs)
      - Reference value: 99.0\" (published FS datum, RAF CP-29)
    """
    from core.analysis import PhysicsEngine

    data = _load_ref_data()
    ref_cg_fwd = data["aircraft_specs"]["cg_range_fwd_fs"]["value"]
    tolerance = data["aircraft_specs"]["cg_range_fwd_fs"]["tolerance_abs"]

    engine = PhysicsEngine()
    metrics = engine.calculate_cg_envelope()
    computed_cg_fwd_published = config.geometry.to_published_datum(metrics.cg_range_fwd)
    delta = abs(computed_cg_fwd_published - ref_cg_fwd)

    assert delta <= tolerance, (
        f"CG fwd limit precision check FAILED (expected for Phase 4): "
        f"computed CG fwd = {computed_cg_fwd_published:.2f}\" (published datum), "
        f"reference = {ref_cg_fwd:.1f}\", delta = {delta:.2f}\" exceeds {tolerance:.1f}\" tolerance. "
        f"Internal CG fwd = {metrics.cg_range_fwd:.2f}\". "
        f"Phase 5 target: calibrate geometry parameters to reduce delta to <{tolerance:.1f}\"."
    )


# Resolved Phase 5: calibrated fs_wing_le corrects CG aft limit (delta <1")
def test_cg_aft_limit_precision():
    """VAL-01: Computed CG aft limit (published datum) must be within 1\" of 104.0.

    Known status: XFAIL. Same fs_wing_le datum error shifts CG aft limit from
    published 104.0\" FS.

    This test documents:
      - Target tolerance: 1.0\" (from reference_data.json cg_range_aft_fs.tolerance_abs)
      - Reference value: 104.0\" (published FS datum, RAF CP-29)
    """
    from core.analysis import PhysicsEngine

    data = _load_ref_data()
    ref_cg_aft = data["aircraft_specs"]["cg_range_aft_fs"]["value"]
    tolerance = data["aircraft_specs"]["cg_range_aft_fs"]["tolerance_abs"]

    engine = PhysicsEngine()
    metrics = engine.calculate_cg_envelope()
    computed_cg_aft_published = config.geometry.to_published_datum(metrics.cg_range_aft)
    delta = abs(computed_cg_aft_published - ref_cg_aft)

    assert delta <= tolerance, (
        f"CG aft limit precision check FAILED (expected for Phase 4): "
        f"computed CG aft = {computed_cg_aft_published:.2f}\" (published datum), "
        f"reference = {ref_cg_aft:.1f}\", delta = {delta:.2f}\" exceeds {tolerance:.1f}\" tolerance. "
        f"Internal CG aft = {metrics.cg_range_aft:.2f}\". "
        f"Phase 5 target: calibrate geometry parameters to reduce delta to <{tolerance:.1f}\"."
    )


# ---------------------------------------------------------------------------
# VAL-02: Airfoil config vs. wind tunnel reference data — should PASS
# ---------------------------------------------------------------------------


def test_roncz_clmax_matches_wind_tunnel():
    """VAL-02: config.aero_limits.canard_clmax must be within 0.05 of wind tunnel 1.35.

    The Roncz R1145MS wind tunnel report (Purdue, 1984) measured CLmax = 1.35 at
    Re = 3,000,000. config.aero_limits.canard_clmax was set from this data — expected PASS.
    """
    data = _load_ref_data()
    ref_clmax = data["airfoil_data"]["roncz_r1145ms"]["cl_max"]["value"]
    tolerance = 0.05

    computed_clmax = config.aero_limits.canard_clmax
    delta = abs(computed_clmax - ref_clmax)

    assert delta <= tolerance, (
        f"Roncz R1145MS CLmax mismatch: "
        f"config = {computed_clmax:.3f}, wind tunnel = {ref_clmax:.3f}, "
        f"delta = {delta:.4f} exceeds {tolerance:.2f} tolerance. "
        f"config.aero_limits.canard_clmax must match Roncz wind tunnel data."
    )


def test_roncz_alpha_0l_matches_wind_tunnel():
    """VAL-02: config.aero_limits.canard_alpha_0L must be within 0.5 deg of wind tunnel -3.0.

    The Roncz R1145MS wind tunnel data gives alpha_zero_lift = -3.0 deg.
    config.aero_limits.canard_alpha_0L was set from this data — expected PASS.
    """
    data = _load_ref_data()
    ref_alpha_0l = data["airfoil_data"]["roncz_r1145ms"]["alpha_zero_lift_deg"]["value"]
    tolerance = 0.5  # degrees

    computed_alpha_0l = config.aero_limits.canard_alpha_0L
    delta = abs(computed_alpha_0l - ref_alpha_0l)

    assert delta <= tolerance, (
        f"Roncz R1145MS alpha_0L mismatch: "
        f"config = {computed_alpha_0l:.2f} deg, wind tunnel = {ref_alpha_0l:.2f} deg, "
        f"delta = {delta:.3f} deg exceeds {tolerance:.1f} deg tolerance. "
        f"config.aero_limits.canard_alpha_0L must match Roncz wind tunnel data."
    )


def test_eppler_clmax_matches_wind_tunnel():
    """VAL-02: config.aero_limits.wing_clmax must be within 0.05 of wind tunnel 1.45.

    The Eppler 1230 wind tunnel / UIUC database gives CLmax = 1.45.
    config.aero_limits.wing_clmax was set from this data — expected PASS.
    """
    data = _load_ref_data()
    ref_clmax = data["airfoil_data"]["eppler_1230"]["cl_max"]["value"]
    tolerance = 0.05

    computed_clmax = config.aero_limits.wing_clmax
    delta = abs(computed_clmax - ref_clmax)

    assert delta <= tolerance, (
        f"Eppler 1230 CLmax mismatch: "
        f"config = {computed_clmax:.3f}, wind tunnel = {ref_clmax:.3f}, "
        f"delta = {delta:.4f} exceeds {tolerance:.2f} tolerance. "
        f"config.aero_limits.wing_clmax must match Eppler 1230 wind tunnel data."
    )


def test_eppler_alpha_0l_matches_wind_tunnel():
    """VAL-02: config.aero_limits.wing_alpha_0L must be within 0.5 deg of wind tunnel -2.0.

    The Eppler 1230 wind tunnel data gives alpha_zero_lift = -2.0 deg.
    config.aero_limits.wing_alpha_0L was set from this data — expected PASS.
    """
    data = _load_ref_data()
    ref_alpha_0l = data["airfoil_data"]["eppler_1230"]["alpha_zero_lift_deg"]["value"]
    tolerance = 0.5  # degrees

    computed_alpha_0l = config.aero_limits.wing_alpha_0L
    delta = abs(computed_alpha_0l - ref_alpha_0l)

    assert delta <= tolerance, (
        f"Eppler 1230 alpha_0L mismatch: "
        f"config = {computed_alpha_0l:.2f} deg, wind tunnel = {ref_alpha_0l:.2f} deg, "
        f"delta = {delta:.3f} deg exceeds {tolerance:.1f} deg tolerance. "
        f"config.aero_limits.wing_alpha_0L must match Eppler 1230 wind tunnel data."
    )


def test_airfoil_cm_zero_in_reference_data():
    """VAL-02 schema check: reference_data.json must contain cm_zero for both airfoils.

    This is a schema integrity check — the config does not implement section Cm0
    (no config.aero_limits.canard_cm0 or wing_cm0 field). The reference data
    must carry the wind tunnel Cm0 values so Phase 5+ can use them for
    pitching moment validation.

    Expected values from wind tunnel data:
      - roncz_r1145ms.cm_zero = -0.05 (Purdue tunnel, 1984)
      - eppler_1230.cm_zero = -0.02 (Stuttgart / UIUC database)
    """
    data = _load_ref_data()
    airfoil_data = data["airfoil_data"]

    # Roncz R1145MS cm_zero must exist and be numeric
    assert "cm_zero" in airfoil_data["roncz_r1145ms"], (
        "reference_data.json missing roncz_r1145ms.cm_zero field. "
        "Wind tunnel Cm0 is required for Phase 5 pitching moment validation."
    )
    roncz_cm0 = airfoil_data["roncz_r1145ms"]["cm_zero"]["value"]
    assert isinstance(roncz_cm0, (int, float)), (
        f"roncz_r1145ms.cm_zero.value must be numeric, got {type(roncz_cm0)}"
    )
    assert roncz_cm0 < 0, (
        f"Roncz R1145MS cm_zero should be negative (nose-down), got {roncz_cm0}"
    )

    # Eppler 1230 cm_zero must exist and be numeric
    assert "cm_zero" in airfoil_data["eppler_1230"], (
        "reference_data.json missing eppler_1230.cm_zero field. "
        "Wind tunnel Cm0 is required for Phase 5 pitching moment validation."
    )
    eppler_cm0 = airfoil_data["eppler_1230"]["cm_zero"]["value"]
    assert isinstance(eppler_cm0, (int, float)), (
        f"eppler_1230.cm_zero.value must be numeric, got {type(eppler_cm0)}"
    )
    assert eppler_cm0 < 0, (
        f"Eppler 1230 cm_zero should be negative (nose-down tendency), got {eppler_cm0}"
    )


# ---------------------------------------------------------------------------
# VAL-04: Performance validation (stall speed, gross weight)
# ---------------------------------------------------------------------------


# Resolved Phase 5: stall speed passes with published reference areas (VAL-04 XPASS confirmed)
def test_stall_speed_within_5pct():
    """VAL-04: First-principles stall speed must be within 5% of published 56 KTAS.

    Computation uses:
      - Published reference areas: 94.2 sqft (wing) + 15.6 sqft (canard) = 109.8 sqft total
        (NOT config areas — per Pitfall 3 in Phase 4 research: area convention mismatch)
      - config.flight_condition.gross_weight_lb = 1425 lb
      - config.aero_limits.canard_clmax = 1.35 (canard stalls first — limiting CLmax)
      - Sea-level density: 0.002377 slug/ft^3

    Formula: V_stall_fps = sqrt(2 * W / (rho * S * CLmax))
             V_stall_ktas = V_stall_fps / 1.6878

    Reference: RAF CP-29 Performance section, p.20 — canard stall at gross weight.
    """
    data = _load_ref_data()
    ref_stall_ktas = data["aircraft_specs"]["stall_speed_ktas"]["value"]
    tolerance_abs = data["aircraft_specs"]["stall_speed_ktas"]["tolerance_abs"]

    # Published reference areas from RAF CP-31 (use these, NOT config areas)
    wing_area_sqft = data["aircraft_specs"]["wing_area_sqft"]["value"]    # 94.2 sqft
    canard_area_sqft = data["aircraft_specs"]["canard_area_sqft"]["value"]  # 15.6 sqft
    total_area_sqft = wing_area_sqft + canard_area_sqft                    # 109.8 sqft

    W = config.flight_condition.gross_weight_lb                             # 1425 lb
    rho = 0.002377  # slug/ft^3 (sea-level standard atmosphere)
    S = total_area_sqft                                                     # 109.8 sqft
    cl_max = config.aero_limits.canard_clmax                                # 1.35 (canard stalls first)

    v_fps = math.sqrt(2.0 * W / (rho * S * cl_max))
    v_ktas = v_fps / 1.6878  # 1 knot = 1.6878 ft/s

    delta = abs(v_ktas - ref_stall_ktas)
    tolerance_pct = 0.05 * ref_stall_ktas  # 5% of 56 KTAS = 2.8 KTAS

    assert delta <= tolerance_pct, (
        f"Stall speed first-principles check: "
        f"computed V_stall = {v_ktas:.1f} KTAS, "
        f"published = {ref_stall_ktas} KTAS, "
        f"delta = {delta:.2f} KTAS exceeds 5% tolerance ({tolerance_pct:.2f} KTAS). "
        f"Areas used: wing={wing_area_sqft} sqft + canard={canard_area_sqft} sqft = {S} sqft. "
        f"W={W} lb, rho={rho} slug/ft^3, CLmax={cl_max}. "
        f"Phase 5 target: lift distribution modeling to match 56 KTAS within 5%."
    )


def test_gross_weight_matches_published():
    """VAL-04: config.flight_condition.gross_weight_lb must equal published 1425 lb exactly.

    This is an exact match check — no tolerance. The FAA-approved maximum gross
    weight for Long-EZ Model 61 is a hard regulatory limit, not an estimate.
    The config must match this value precisely.

    Reference: RAF CP-29, Weight & Balance section, p.12.
    """
    data = _load_ref_data()
    ref_gross_weight = data["aircraft_specs"]["max_gross_weight_lb"]["value"]

    computed_gross_weight = config.flight_condition.gross_weight_lb

    assert computed_gross_weight == ref_gross_weight, (
        f"Gross weight mismatch: "
        f"config.flight_condition.gross_weight_lb = {computed_gross_weight}, "
        f"published max gross weight = {ref_gross_weight} lb. "
        f"This must be an exact match — no tolerance on FAA gross weight limit."
    )
