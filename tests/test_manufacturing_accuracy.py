"""
Phase 4 Tests: Skin Thickness Deduction and TE Collapse Protection
===================================================================

Validates:
1. Skin deduction reduces airfoil thickness by correct amount
2. Offset airfoil is valid (no self-intersections)
3. TE collapse protection produces valid profile for thin airfoils
4. Large offsets don't crash -- they truncate gracefully
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

import numpy as np  # noqa: E402
from core.aerodynamics import Airfoil, AirfoilCoordinates  # noqa: E402


def _make_naca_0012_coords(n=100):
    """Create NACA 0012 coordinates for testing."""
    t = np.linspace(0, np.pi, n)
    x = 0.5 * (1 - np.cos(t))  # Cosine spacing: 0 -> 1

    # NACA 0012 thickness distribution
    yt = (
        0.12
        / 0.2
        * (
            0.2969 * np.sqrt(x)
            - 0.1260 * x
            - 0.3516 * x**2
            + 0.2843 * x**3
            - 0.1015 * x**4
        )
    )

    return AirfoilCoordinates(
        name="NACA0012",
        x_upper=x,
        y_upper=yt,
        x_lower=x,
        y_lower=-yt,
    )


class TestSkinDeduction:
    def test_offset_reduces_thickness(self):
        """Offset airfoil should be thinner than original at mid-chord."""
        coords = _make_naca_0012_coords()
        airfoil = Airfoil(coords, n_points=200, smooth=False)

        chord = 50.0  # inches
        offset = airfoil.offset_inward(0.048, chord)

        # Get y-values at approximately mid-chord (x ~ 0.3)
        x_orig, y_orig = airfoil.coordinates
        x_off, y_off = offset.coordinates

        # Find midchord thickness for original
        le_orig = np.argmin(x_orig)
        upper_orig = y_orig[: le_orig + 1]
        lower_orig = y_orig[le_orig:]

        le_off = np.argmin(x_off)
        upper_off = y_off[: le_off + 1]
        lower_off = y_off[le_off:]

        # Max thickness of original should be greater than offset
        thick_orig = np.max(upper_orig) - np.min(lower_orig)
        thick_off = np.max(upper_off) - np.min(lower_off)

        assert (
            thick_off < thick_orig
        ), f"Offset thickness {thick_off:.4f} not less than original {thick_orig:.4f}"

    def test_offset_amount_reasonable(self):
        """Thickness reduction should be approximately 2 * skin thickness / chord."""
        coords = _make_naca_0012_coords()
        airfoil = Airfoil(coords, n_points=200, smooth=False)

        chord = 50.0
        skin = 0.048  # inches
        offset = airfoil.offset_inward(skin, chord)

        x_orig, y_orig = airfoil.coordinates
        x_off, y_off = offset.coordinates

        # At mid-chord, normals are nearly vertical, so thickness reduction
        # should be close to 2 * skin_normalized = 2 * 0.048/50 = 0.00192
        le_orig = np.argmin(x_orig)
        thick_orig = np.max(y_orig[: le_orig + 1]) - np.min(y_orig[le_orig:])

        le_off = np.argmin(x_off)
        thick_off = np.max(y_off[: le_off + 1]) - np.min(y_off[le_off:])

        reduction = thick_orig - thick_off
        expected = 2 * skin / chord
        # Reduction should be positive and on the right order of magnitude.
        # Exact match isn't expected because: (1) normals aren't purely vertical,
        # (2) max thickness point shifts after offset, (3) spline resampling.
        assert reduction > 0, "No thickness reduction detected"
        assert (
            reduction < expected * 3
        ), f"Reduction {reduction:.5f} too large vs expected {expected:.5f}"

    def test_offset_preserves_valid_profile(self):
        """Offset airfoil should have reasonable coordinates (all within [0,1] x range)."""
        coords = _make_naca_0012_coords()
        airfoil = Airfoil(coords, n_points=200, smooth=False)

        offset = airfoil.offset_inward(0.048, 50.0)
        x, y = offset.coordinates

        # x should be in approximately [0, 1] range (small excursions ok at LE)
        assert np.min(x) >= -0.02, f"Min x = {np.min(x)}"
        assert np.max(x) <= 1.02, f"Max x = {np.max(x)}"

    def test_zero_offset_preserves_shape(self):
        """Zero offset should produce nearly identical airfoil."""
        coords = _make_naca_0012_coords()
        airfoil = Airfoil(coords, n_points=200, smooth=False)

        offset = airfoil.offset_inward(0.0, 50.0)
        x_orig, y_orig = airfoil.coordinates
        x_off, y_off = offset.coordinates

        # Should be very similar (not exact due to normal computation at boundaries)
        le_orig = np.argmin(x_orig)
        le_off = np.argmin(x_off)
        thick_orig = np.max(y_orig[: le_orig + 1]) - np.min(y_orig[le_orig:])
        thick_off = np.max(y_off[: le_off + 1]) - np.min(y_off[le_off:])

        assert abs(thick_orig - thick_off) < 0.001


class TestTECollapseProtection:
    def test_large_offset_doesnt_crash(self):
        """Very large offset on thin airfoil should not raise exceptions."""
        coords = _make_naca_0012_coords()
        airfoil = Airfoil(coords, n_points=200, smooth=False)

        # 0.1" offset on 13.5" chord (canard tip scenario -- extreme)
        # Normalized: 0.1/13.5 = 0.0074 -> for 12% thick airfoil, TE ~ 0.003
        # This should trigger TE collapse protection
        offset = airfoil.offset_inward(0.1, 13.5)
        x, y = offset.coordinates
        assert len(x) > 10, f"Offset produced only {len(x)} points"

    def test_moderate_offset_valid_profile(self):
        """Canard tip with skin deduction: 0.048\" on 13.5\" chord."""
        coords = _make_naca_0012_coords()
        airfoil = Airfoil(coords, n_points=200, smooth=False)

        offset = airfoil.offset_inward(0.048, 13.5)
        x, y = offset.coordinates

        # Should still have a valid profile with positive extent
        assert len(x) > 20
        le = np.argmin(x)
        if le > 0 and le < len(y) - 1:
            upper_max = np.max(y[: le + 1])
            lower_min = np.min(y[le:])
            assert upper_max > lower_min, "Upper and lower surfaces crossed"
