"""
G-code generation utilities for synchronized 4-axis hot-wire cutting.

The GCodeWriter consumes matched root/tip airfoil profiles, applies kerf
compensation, and emits Mach3/GRBL-compatible toolpaths that keep both
carriages synchronized across the span.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import cadquery as cq
import numpy as np


class GCodeWriter:
    """Generate synchronized 4-axis hot-wire G-code files."""

    def __init__(
        self,
        root_profile: cq.Wire,
        tip_profile: cq.Wire,
        kerf_offset: float = 0.045,
        feed_rate: float = 4.0,
        safe_height: float = 5.0,
        units: str = "inch",
    ) -> None:
        """Initialize the writer.

        Args:
            root_profile: Airfoil wire at the root side of the span.
            tip_profile: Airfoil wire at the tip side of the span.
            kerf_offset: Kerf compensation (moves points outward).
            feed_rate: Linear feed rate in units/min.
            safe_height: Clearance height for rapid moves.
            units: "inch" or "mm" (controls G20/G21).
        """
        self.root_profile = root_profile
        self.tip_profile = tip_profile
        self.kerf_offset = kerf_offset
        self.feed_rate = feed_rate
        self.safe_height = safe_height
        self.units = units.lower()

    def write(self, filepath: Path, n_points: int = 240) -> Path:
        """Create the G-code file.

        Args:
            filepath: Target file path (e.g., output/gcode/wing.tap).
            n_points: Number of synchronized stations around the profile.

        Returns:
            Path to the written G-code file.
        """
        root_pts = self._prepare_profile(self.root_profile, n_points)
        tip_pts = self._prepare_profile(self.tip_profile, n_points)

        lines: List[str] = []
        lines.append("(Open-EZ PDE hot-wire toolpath)")
        lines.append("(Synchronized 4-axis cut; Mach3/GRBL format)")
        lines.append(f"(Kerf compensation: {self.kerf_offset:.4f} in)")
        lines.append("G90 ; absolute positioning")
        lines.append("G94 ; units per minute feed")
        lines.append("G20" if self.units == "inch" else "G21")
        lines.append(
            f"G0 X0.000 Y0.000 Z{self.safe_height:.3f} A{self.safe_height:.3f}"
        )
        lines.append("M3 ; energize hot wire")

        for root, tip in zip(root_pts, tip_pts):
            lines.append(
                "G1 "
                f"X{root[0]:.4f} Y{tip[0]:.4f} "
                f"Z{root[1]:.4f} A{tip[1]:.4f} "
                f"F{self.feed_rate:.2f}"
            )

        lines.append(
            f"G0 X0.000 Y0.000 Z{self.safe_height:.3f} A{self.safe_height:.3f}"
        )
        lines.append("M5 ; de-energize")
        lines.append("M30")

        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text("\n".join(lines) + "\n")
        return filepath

    def _prepare_profile(self, wire: cq.Wire, n_points: int) -> List[Tuple[float, float]]:
        points = self._profile_points(wire, n_points)
        offset = self._apply_kerf(points, self.kerf_offset)
        return offset

    @staticmethod
    def _profile_points(wire: cq.Wire, n_points: int) -> List[Tuple[float, float]]:
        """Discretize a CadQuery wire into XY tuples."""
        raw_points: List[Tuple[float, float]] = []
        for vec in wire.discretize(n_points):
            raw_points.append((float(vec.x), float(vec.y)))

        # Close the loop if needed
        if raw_points and raw_points[0] != raw_points[-1]:
            raw_points.append(raw_points[0])

        return raw_points

    @staticmethod
    def _apply_kerf(
        points: Sequence[Tuple[float, float]], kerf: float
    ) -> List[Tuple[float, float]]:
        """Offset points outward from centroid for kerf compensation."""
        if not points:
            return []

        pts = np.asarray(points)
        centroid = np.mean(pts, axis=0)

        compensated: List[Tuple[float, float]] = []
        for x, y in pts:
            vec = np.array([x, y]) - centroid
            norm = np.linalg.norm(vec)
            if norm < 1e-6:
                compensated.append((float(x), float(y)))
                continue
            direction = vec / norm
            new_pt = vec + direction * kerf
            compensated.append(tuple((new_pt + centroid).tolist()))

        return compensated

    @staticmethod
    def synchronize_profiles(
        root_points: Iterable[Tuple[float, float]],
        tip_points: Iterable[Tuple[float, float]],
        n_samples: int,
    ) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """Resample two polylines to the same number of points."""
        root_synced = GCodeWriter._resample(root_points, n_samples)
        tip_synced = GCodeWriter._resample(tip_points, n_samples)
        return root_synced, tip_synced

    @staticmethod
    def _resample(points: Iterable[Tuple[float, float]], n_samples: int) -> List[Tuple[float, float]]:
        pts = np.asarray(list(points), dtype=float)
        if len(pts) == 0:
            return []

        # Arc-length parameterization
        diffs = np.diff(pts, axis=0, append=pts[:1])
        ds = np.sqrt((diffs[:, 0] ** 2) + (diffs[:, 1] ** 2))
        s = np.concatenate([[0], np.cumsum(ds)])
        s_norm = s / s[-1] if s[-1] != 0 else np.linspace(0, 1, len(pts) + 1)

        target = np.linspace(0, 1, n_samples)
        x_interp = np.interp(target, s_norm, np.append(pts[:, 0], pts[0, 0]))
        y_interp = np.interp(target, s_norm, np.append(pts[:, 1], pts[0, 1]))
        return list(zip(x_interp.tolist(), y_interp.tolist()))
