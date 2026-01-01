"""
Airfoil ingestion and smoothing utilities.

This module ingests UIUC-style ``.dat`` files (Selig or Lednicer variants),
cleans the coordinates with cubic splines + Savitzky-Golay filtering,
and guarantees a closed trailing edge for CAD-friendly output.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import cadquery as cq
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import savgol_filter

from config import AirfoilType, config


@dataclass
class AirfoilCoordinates:
    """Raw airfoil coordinate data."""

    name: str
    x_upper: np.ndarray
    y_upper: np.ndarray
    x_lower: np.ndarray
    y_lower: np.ndarray

    @property
    def x(self) -> np.ndarray:
        """Combined x coordinates (upper then lower, reversed)."""
        return np.concatenate([self.x_upper, self.x_lower[::-1]])

    @property
    def y(self) -> np.ndarray:
        """Combined y coordinates (upper then lower, reversed)."""
        return np.concatenate([self.y_upper, self.y_lower[::-1]])


class Airfoil:
    """
    Processed airfoil ready for CAD generation.

    Applies:
    - CubicSpline interpolation for smooth curves
    - Savitzky-Golay filtering to remove digitization noise
    - Trailing-edge closure
    - Washout and reflex transformations
    """

    def __init__(
        self,
        coords: AirfoilCoordinates,
        n_points: int = 200,
        smooth: bool = True,
    ):
        """Initialize airfoil from raw coordinates."""
        self.name = coords.name
        self._raw = coords
        self._n_points = n_points

        self._x, self._y = self._process_coordinates(coords, n_points, smooth)
        self._close_trailing_edge()

    def _process_coordinates(
        self, coords: AirfoilCoordinates, n_points: int, smooth: bool
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Apply spline interpolation and optional smoothing."""
        x_raw = coords.x
        y_raw = coords.y

        dx = np.diff(x_raw)
        dy = np.diff(y_raw)
        ds = np.sqrt(dx**2 + dy**2)
        s = np.concatenate([[0], np.cumsum(ds)])
        s_norm = s / s[-1]

        cs_x = CubicSpline(s_norm, x_raw)
        cs_y = CubicSpline(s_norm, y_raw)

        t_new = np.linspace(0, 1, n_points)
        x_new = cs_x(t_new)
        y_new = cs_y(t_new)

        if smooth and n_points >= 11:
            window = min(11, n_points // 2 * 2 - 1)
            y_new = savgol_filter(y_new, window, 3)

        return x_new, y_new

    def _close_trailing_edge(self) -> None:
        """Ensure trailing edge is closed (upper meets lower)."""
        if abs(self._y[0] - self._y[-1]) > 1e-6:
            y_te = (self._y[0] + self._y[-1]) / 2
            self._y[0] = y_te
            self._y[-1] = y_te

    @property
    def coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return processed (x, y) coordinates."""
        return self._x.copy(), self._y.copy()

    def apply_washout(self, angle_deg: float) -> "Airfoil":
        """Apply washout (twist) rotation about quarter-chord."""
        theta = np.radians(angle_deg)
        cos_t, sin_t = np.cos(theta), np.sin(theta)

        x_pivot = 0.25
        x_shifted = self._x - x_pivot
        y_shifted = self._y

        x_rot = x_shifted * cos_t + y_shifted * sin_t + x_pivot
        y_rot = -x_shifted * sin_t + y_shifted * cos_t

        new_coords = AirfoilCoordinates(
            name=f"{self.name}_washout_{angle_deg}deg",
            x_upper=x_rot[: len(x_rot) // 2],
            y_upper=y_rot[: len(y_rot) // 2],
            x_lower=x_rot[len(x_rot) // 2 :][::-1],
            y_lower=y_rot[len(y_rot) // 2 :][::-1],
        )
        return Airfoil(new_coords, self._n_points, smooth=False)

    def apply_reflex(self, percent: float) -> "Airfoil":
        """Apply trailing-edge reflex for pitch stability."""
        reflex_start = 0.70
        reflex_amount = percent / 100.0

        x_new = self._x.copy()
        y_new = self._y.copy()

        for i in range(len(x_new)):
            if x_new[i] > reflex_start:
                t = (x_new[i] - reflex_start) / (1.0 - reflex_start)
                y_new[i] += reflex_amount * t * (1 - t) * 4

        new_coords = AirfoilCoordinates(
            name=f"{self.name}_reflex_{percent}pct",
            x_upper=x_new[: len(x_new) // 2],
            y_upper=y_new[: len(y_new) // 2],
            x_lower=x_new[len(x_new) // 2 :][::-1],
            y_lower=y_new[len(y_new) // 2 :][::-1],
        )
        return Airfoil(new_coords, self._n_points, smooth=False)

    def scale(self, chord: float) -> Tuple[np.ndarray, np.ndarray]:
        """Scale airfoil to specified chord length."""
        return self._x * chord, self._y * chord

    def get_cadquery_wire(self, chord: float) -> cq.Wire:
        """Generate CadQuery wire at specified chord."""
        x_scaled, y_scaled = self.scale(chord)
        points = [(float(x), float(y), 0.0) for x, y in zip(x_scaled, y_scaled)]
        wire = cq.Workplane("XY").spline(points, includeCurrent=False).close().wire()
        return wire.val()

    def get_cadquery_face(self, chord: float) -> cq.Face:
        """Generate CadQuery face (filled airfoil) at specified chord."""
        wire = self.get_cadquery_wire(chord)
        return cq.Face.makeFromWires(wire)


class AirfoilFactory:
    """Factory for loading and managing airfoil profiles."""

    DATA_DIR = Path(__file__).parent.parent / "data" / "airfoils"
    AIRFOIL_FILES = {
        AirfoilType.RONCZ_R1145MS: "roncz_r1145ms.dat",
        AirfoilType.EPPLER_1230_MOD: "eppler_1230_mod.dat",
        AirfoilType.GU25_5_11_8: "gu25_5_11_8.dat",
    }

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or self.DATA_DIR
        self._cache: dict = {}

    def load(self, airfoil_type: AirfoilType, n_points: int = 200, smooth: bool = True) -> Airfoil:
        """Load an airfoil by enum."""
        cache_key = (airfoil_type, n_points, smooth)
        if cache_key in self._cache:
            return self._cache[cache_key]

        filename = self.AIRFOIL_FILES.get(airfoil_type)
        if filename is None:
            raise ValueError(f"Unknown airfoil type: {airfoil_type}")

        filepath = self.data_dir / filename
        coords = self._parse_dat_file(filepath)
        airfoil = Airfoil(coords, n_points, smooth)
        self._cache[cache_key] = airfoil
        return airfoil

    def load_from_file(self, filepath: Path, n_points: int = 200, smooth: bool = True) -> Airfoil:
        """Load an airfoil from an arbitrary .dat file."""
        coords = self._parse_dat_file(filepath)
        return Airfoil(coords, n_points, smooth)

    def _orient_section(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Ensure a section runs from leading edge to trailing edge."""
        if len(x) == 0:
            return x, y
        if x[0] > x[-1]:
            x = x[::-1]
            y = y[::-1]
        return x, y

    def _parse_dat_file(self, filepath: Path) -> AirfoilCoordinates:
        """Parse UIUC-format .dat file (Selig or Lednicer)."""
        if not filepath.exists():
            raise FileNotFoundError(f"Airfoil data file not found: {filepath}")

        with open(filepath, "r") as f:
            lines = f.readlines()

        name = lines[0].strip()
        sections: List[List[Tuple[float, float]]] = []
        current: List[Tuple[float, float]] = []

        for line in lines[1:]:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                if current:
                    sections.append(current)
                    current = []
                continue

            parts = stripped.split()
            if len(parts) >= 2:
                try:
                    x = float(parts[0])
                    y = float(parts[1])
                    current.append((x, y))
                except ValueError:
                    continue

        if current:
            sections.append(current)

        if not sections:
            raise ValueError(f"No coordinate data in {filepath}")

        # Lednicer often provides separate upper/lower sections split by a blank line
        if len(sections) >= 2:
            upper = np.array(sections[0])
            lower = np.array(sections[1])
            x_upper, y_upper = self._orient_section(upper[:, 0], upper[:, 1])
            x_lower, y_lower = self._orient_section(lower[:, 0], lower[:, 1])
        else:
            coords = np.array(sections[0])
            x_all = coords[:, 0]
            y_all = coords[:, 1]
            le_idx = int(np.argmin(x_all))

            x_upper = x_all[: le_idx + 1][::-1]
            y_upper = y_all[: le_idx + 1][::-1]
            x_lower = x_all[le_idx:]
            y_lower = y_all[le_idx:]

        return AirfoilCoordinates(
            name=name,
            x_upper=x_upper,
            y_upper=y_upper,
            x_lower=x_lower,
            y_lower=y_lower,
        )

    def get_canard_airfoil(self) -> Airfoil:
        """Get the safety-mandated Roncz R1145MS canard airfoil."""
        if config.airfoils.canard != AirfoilType.RONCZ_R1145MS:
            import warnings

            warnings.warn(
                "SAFETY: Overriding canard airfoil to Roncz R1145MS. GU25-5(11)8 is unsafe in rain.",
                UserWarning,
            )
        return self.load(AirfoilType.RONCZ_R1145MS)

    def get_wing_airfoil(self, apply_reflex: bool = True) -> Airfoil:
        """Get the main wing airfoil with optional reflex."""
        airfoil = self.load(config.airfoils.wing_root)
        if apply_reflex and config.airfoils.wing_reflex_percent > 0:
            airfoil = airfoil.apply_reflex(config.airfoils.wing_reflex_percent)
        return airfoil


airfoil_factory = AirfoilFactory()
