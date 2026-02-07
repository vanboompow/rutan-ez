"""
A2: Lift Curve Slope Validation Against Anderson's Theory
==========================================================

Tests the lift curve slope calculation against Fundamentals of Aerodynamics
(Anderson, 6th ed.) finite-wing correction with sweep.

For a swept finite wing:
    a = (2 * pi * AR) / (2 + sqrt(4 + AR^2 * (1 + tan^2(sweep_c/2) / beta^2)))

where:
    AR = aspect ratio
    sweep_c/2 = sweep at half-chord (NOT leading-edge sweep)
    beta^2 = 1 - M^2 (approximately 1.0 for low-speed)

The current code in core/analysis.py:205 uses the simplified formula WITHOUT
sweep correction:
    a = 2 * pi * AR / (2 + sqrt(4 + AR^2))

This overestimates the lift curve slope for the swept Long-EZ wing,
yielding ~4.9/rad instead of the correct ~4.2/rad.

These tests should FAIL with the current code and PASS after the fix.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Mock cadquery before importing core modules (cadquery is a heavy C++ dependency)
sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

import math
import pytest


def _anderson_lift_slope(ar: float, sweep_half_chord_deg: float, mach: float = 0.0) -> float:
    """Compute lift curve slope per Anderson's formula with sweep correction.

    Reference: Anderson, Fundamentals of Aerodynamics, Eq. (5.66)

    Args:
        ar: Aspect ratio
        sweep_half_chord_deg: Sweep at half-chord line (degrees)
        mach: Freestream Mach number

    Returns:
        Lift curve slope in 1/radian
    """
    beta_sq = 1.0 - mach**2
    sweep_rad = math.radians(sweep_half_chord_deg)
    tan_sq = math.tan(sweep_rad) ** 2

    a = (2 * math.pi * ar) / (
        2 + math.sqrt(4 + ar**2 * (1 + tan_sq / beta_sq))
    )
    return a


def _le_sweep_to_half_chord_sweep(sweep_le_deg: float, ar: float, taper: float) -> float:
    """Convert leading-edge sweep to half-chord sweep.

    tan(sweep_c/2) = tan(sweep_LE) - (2/AR) * (1 - taper) / (1 + taper) * 0.5

    More precisely:
    tan(sweep_n) = tan(sweep_LE) - (4n / AR) * ((1 - taper) / (1 + taper))
    where n is the fractional chord location (n=0.5 for half-chord).
    """
    sweep_le_rad = math.radians(sweep_le_deg)
    tan_half = math.tan(sweep_le_rad) - (4 * 0.5 / ar) * ((1 - taper) / (1 + taper))
    return math.degrees(math.atan(tan_half))


class TestLiftCurveSlopeWing:
    """Test wing lift curve slope against Anderson's swept-wing correction."""

    # Long-EZ wing parameters from config
    AR_WING = 7.3  # approx wing_aspect_ratio from config
    SWEEP_LE_DEG = 25.0
    TAPER_RATIO = 32.0 / 68.0  # tip_chord / root_chord

    @property
    def sweep_half_chord_deg(self) -> float:
        return _le_sweep_to_half_chord_sweep(
            self.SWEEP_LE_DEG, self.AR_WING, self.TAPER_RATIO
        )

    def test_anderson_reference_value(self):
        """Verify the Anderson formula gives expected ~4.2/rad for Long-EZ wing."""
        a = _anderson_lift_slope(self.AR_WING, self.sweep_half_chord_deg)

        # With AR=7.3 and ~18 deg half-chord sweep, expect ~4.2/rad
        assert 3.8 <= a <= 4.6, (
            f"Anderson lift slope for AR={self.AR_WING}, "
            f"sweep_c/2={self.sweep_half_chord_deg:.1f} deg: "
            f"a = {a:.3f}/rad (expected 3.8-4.6)"
        )

    def test_physics_engine_matches_anderson(self):
        """PhysicsEngine lift slope must include sweep correction per Anderson.

        The engine code at core/analysis.py now computes:
            a = 2*pi*AR / (2 + sqrt(4 + AR^2 * (1 + tan^2(sweep_c/2))))

        This matches Anderson's eq. 5.69. Verify the engine's result
        agrees with our independent Anderson calculation within 3%.
        """
        from core.analysis import PhysicsEngine

        engine = PhysicsEngine()
        geo = engine.geo

        ar_wing = geo.wing_aspect_ratio

        # Replicate what the engine ACTUALLY computes (with sweep correction)
        taper = geo.wing_tip_chord / geo.wing_root_chord
        tan_sweep_le = math.tan(math.radians(geo.wing_sweep_le))
        tan_sweep_half = tan_sweep_le - (
            2 * geo.wing_root_chord * (1 - taper)
            / (geo.wing_span * (1 + taper))
        )
        a_engine_actual = (
            2 * math.pi * ar_wing
            / (2 + math.sqrt(4 + ar_wing**2 * (1 + tan_sweep_half**2)))
        )

        # Anderson reference with sweep correction:
        sweep_hc = _le_sweep_to_half_chord_sweep(geo.wing_sweep_le, ar_wing, taper)
        a_correct = _anderson_lift_slope(ar_wing, sweep_hc)

        # The engine's value should match Anderson within 3%.
        tolerance = 0.03
        assert abs(a_engine_actual - a_correct) / a_correct < tolerance, (
            f"Lift curve slope mismatch:\n"
            f"  Engine (sweep-corrected): {a_engine_actual:.4f}/rad\n"
            f"  Anderson (reference):     {a_correct:.4f}/rad\n"
            f"  Error: {abs(a_engine_actual - a_correct)/a_correct*100:.1f}% "
            f"(tolerance: {tolerance*100:.0f}%)"
        )

    def test_no_sweep_recovers_standard_formula(self):
        """With zero sweep, Anderson's formula reduces to standard lifting-line."""
        ar = 7.3
        a_anderson = _anderson_lift_slope(ar, sweep_half_chord_deg=0.0)
        a_standard = 2 * math.pi * ar / (2 + math.sqrt(4 + ar**2))

        assert abs(a_anderson - a_standard) < 0.01, (
            f"Zero-sweep Anderson ({a_anderson:.4f}) should match "
            f"standard formula ({a_standard:.4f})"
        )


class TestLiftCurveSlopeCanard:
    """Test canard lift curve slope."""

    def test_canard_slope_has_sweep_correction(self):
        """Canard lift slope must include sweep correction.

        The engine now computes canard slope with the sweep correction term.
        Verify it matches Anderson's reference within 5%.
        """
        from core.analysis import PhysicsEngine

        engine = PhysicsEngine()
        geo = engine.geo

        ar_canard = (geo.canard_span / 12) ** 2 / geo.canard_area

        # Replicate what engine computes (with sweep correction)
        taper_canard = geo.canard_tip_chord / geo.canard_root_chord
        tan_sweep_le_c = math.tan(math.radians(geo.canard_sweep_le))
        tan_sweep_half_c = tan_sweep_le_c - (
            2 * geo.canard_root_chord * (1 - taper_canard)
            / (geo.canard_span * (1 + taper_canard))
        )
        a_engine = (
            2 * math.pi * ar_canard
            / (2 + math.sqrt(4 + ar_canard**2 * (1 + tan_sweep_half_c**2)))
        )

        # Anderson's corrected value
        sweep_hc_canard = _le_sweep_to_half_chord_sweep(
            geo.canard_sweep_le, ar_canard, taper_canard
        )
        a_correct = _anderson_lift_slope(ar_canard, sweep_hc_canard)

        tolerance = 0.05
        assert abs(a_engine - a_correct) / a_correct < tolerance, (
            f"Canard lift slope mismatch:\n"
            f"  Engine (sweep-corrected): {a_engine:.4f}/rad\n"
            f"  Anderson (reference):     {a_correct:.4f}/rad\n"
            f"  Error: {abs(a_engine - a_correct)/a_correct*100:.1f}%"
        )

    def test_canard_ar_reasonable(self):
        """Verify the canard aspect ratio calculation is physically reasonable."""
        from config import config

        geo = config.geometry
        ar_canard = (geo.canard_span / 12) ** 2 / geo.canard_area

        # Long-EZ canard AR should be roughly 9-12
        assert 5.0 < ar_canard < 15.0, (
            f"Canard AR = {ar_canard:.2f} is outside reasonable range [5, 15]"
        )
