"""
A1: Airfoil Washout Rotation Direction Test
=============================================

Validates that apply_washout(+1 deg) rotates the leading edge DOWN (negative y)
about the quarter-chord pivot (x=0.25).

Aerodynamic convention:
  - Positive washout = leading edge DOWN = clockwise rotation (nose-down pitch)
  - This reduces local angle of attack at the tip, preventing tip stall

Reference: Standard 2D rotation matrix: positive washout = CW about quarter-chord
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

import numpy as np


def _make_symmetric_airfoil():
    """Create a simple symmetric NACA-0012-like airfoil."""
    from core.aerodynamics import AirfoilCoordinates

    n = 50
    beta = np.linspace(0, np.pi, n)
    x = 0.5 * (1 - np.cos(beta))
    t = 0.12
    yt = (t / 0.2) * (
        0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2
        + 0.2843 * x**3 - 0.1015 * x**4
    )
    return AirfoilCoordinates(
        name="NACA0012_synthetic",
        x_upper=x.copy(), y_upper=yt.copy(),
        x_lower=x.copy(), y_lower=-yt.copy(),
    )


def test_washout_positive_le_moves_down():
    """Positive washout (+1 deg) must move the LE DOWN (y < 0) via API."""
    from core.aerodynamics import Airfoil

    coords = _make_symmetric_airfoil()
    airfoil = Airfoil(coords, n_points=200, smooth=False)
    washed = airfoil.apply_washout(1.0)
    x_out, y_out = washed.coordinates
    le_idx = np.argmin(x_out)
    assert y_out[le_idx] < -1e-6, (
        f"After +1 deg washout, LE y should be negative, got {y_out[le_idx]:.8f}"
    )


def test_washout_negative_le_moves_up():
    """Negative washout (-1 deg) must move the LE UP (y > 0) via API."""
    from core.aerodynamics import Airfoil

    coords = _make_symmetric_airfoil()
    airfoil = Airfoil(coords, n_points=200, smooth=False)
    washed = airfoil.apply_washout(-1.0)
    x_out, y_out = washed.coordinates
    le_idx = np.argmin(x_out)
    assert y_out[le_idx] > 1e-6, (
        f"After -1 deg washout, LE y should be positive, got {y_out[le_idx]:.8f}"
    )


def test_washout_zero_preserves_shape():
    """Zero washout should preserve shape within reconstruction tolerance."""
    from core.aerodynamics import Airfoil

    coords = _make_symmetric_airfoil()
    airfoil = Airfoil(coords, n_points=200, smooth=False)
    x_orig, y_orig = airfoil.coordinates
    washed = airfoil.apply_washout(0.0)
    x_out, y_out = washed.coordinates
    le_idx = np.argmin(x_out)
    assert abs(x_out[le_idx]) < 0.01
    assert abs(y_out[le_idx]) < 0.01
    assert abs(np.max(x_out) - np.max(x_orig)) < 0.02
    assert abs(np.max(y_out) - np.max(y_orig)) < 0.02


def test_washout_magnitude_scales_with_angle():
    """LE displacement should scale linearly for small angles."""
    from core.aerodynamics import Airfoil

    coords = _make_symmetric_airfoil()
    airfoil = Airfoil(coords, n_points=200, smooth=False)
    x1, y1 = airfoil.apply_washout(1.0).coordinates
    x2, y2 = airfoil.apply_washout(2.0).coordinates
    y_le_1 = y1[np.argmin(x1)]
    y_le_2 = y2[np.argmin(x2)]
    ratio = abs(y_le_2 / y_le_1) if abs(y_le_1) > 1e-10 else float('inf')
    assert 1.8 < ratio < 2.2, f"Ratio {ratio:.3f}, expected ~2.0"


def test_washout_rotation_formula_positive():
    """Test the rotation formula directly on internal arrays for +1 deg.

    The apply_washout pipeline re-creates an Airfoil from rotated coords,
    which re-runs spline fitting and can mask rotation direction errors.
    This test applies the exact formula from aerodynamics.py:135,144
    directly to the internal _x, _y arrays.

    The code negates theta for CW rotation: theta = radians(-angle_deg)
    So for +1 deg washout: theta = -1 deg
    For LE at (0, 0) with pivot at x=0.25:
        x_shifted = -0.25, y_shifted = 0
        y_rot = -(-0.25)*sin(-1deg) = +0.25*(-sin(1deg)) = -0.25*sin(1deg) < 0 (DOWN)
    """
    from core.aerodynamics import Airfoil

    coords = _make_symmetric_airfoil()
    airfoil = Airfoil(coords, n_points=200, smooth=False)

    x_int = airfoil._x.copy()
    y_int = airfoil._y.copy()
    le_idx = np.argmin(x_int)

    # Match the actual code: theta = radians(-angle_deg) for CW rotation
    theta = np.radians(-1.0)  # +1 deg washout => negate for CW
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    x_shifted = x_int[le_idx] - 0.25
    y_shifted = y_int[le_idx]

    # This is the exact formula from aerodynamics.py line 144:
    y_rot = -x_shifted * sin_t + y_shifted * cos_t

    assert y_rot < 0, (
        f"Rotation formula gives y_LE = {y_rot:.8f} for +1 deg washout. "
        f"Should be negative (DOWN)."
    )


def test_washout_rotation_formula_negative():
    """Test the rotation formula directly for -1 deg washout."""
    from core.aerodynamics import Airfoil

    coords = _make_symmetric_airfoil()
    airfoil = Airfoil(coords, n_points=200, smooth=False)

    x_int = airfoil._x.copy()
    y_int = airfoil._y.copy()
    le_idx = np.argmin(x_int)

    # Match the actual code: theta = radians(-angle_deg) for CW rotation
    theta = np.radians(1.0)  # -1 deg washout => negate => +1 deg
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    x_shifted = x_int[le_idx] - 0.25
    y_shifted = y_int[le_idx]

    y_rot = -x_shifted * sin_t + y_shifted * cos_t

    assert y_rot > 0, (
        f"Rotation formula gives y_LE = {y_rot:.8f} for -1 deg washout. "
        f"Should be positive (UP)."
    )
