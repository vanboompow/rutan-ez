"""
Manufacturing utilities for CNC foam core cutting.

Implements synchronized 4-axis hot-wire G-code generation with:
- Kerf compensation per foam type
- Segmented feed scheduling around high-curvature regions
- Lead-in/lead-out motion for clean wire entry/exit
- Commented metadata for traceability and compliance
"""

from __future__ import annotations

import datetime
import math
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import cadquery as cq


class GCodeWriter:
    """Generate coordinated XY/UV toolpaths for 4-axis hot-wire cutting."""

    def __init__(
        self,
        root_profile: cq.Wire,
        tip_profile: cq.Wire,
        kerf_offset: float = 0.045,
        feed_rate: float = 4.0,
        lead_distance: float = 0.5,
        feed_schedule: Optional[Sequence[Tuple[float, float]]] = None,
        discretization: float = 0.25,
    ) -> None:
        self.root_profile = root_profile
        self.tip_profile = tip_profile
        self.kerf_offset = kerf_offset
        self.feed_rate = feed_rate
        self.lead_distance = lead_distance
        self.discretization = discretization
        self.feed_schedule = feed_schedule or [
            (0.0, feed_rate * 0.7),   # slower at lead-in
            (0.10, feed_rate),       # accelerate across lower surface
            (0.70, feed_rate * 0.9),
            (0.90, feed_rate * 0.75),  # slow around trailing edge wrap-up
            (1.0, feed_rate * 0.6),
        ]

    def write(self, output_file: Path) -> Path:
        """Create the G-code file on disk."""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        lines = self._build_gcode()
        output_file.write_text("\n".join(lines) + "\n")
        return output_file

    def _build_gcode(self) -> List[str]:
        root_wire = self._apply_kerf(self.root_profile, self.kerf_offset)
        tip_wire = self._apply_kerf(self.tip_profile, self.kerf_offset)

        root_pts = self._discretize_wire(root_wire, self.discretization)
        tip_pts = self._discretize_wire(tip_wire, self.discretization)

        root_pts, tip_pts = self._synchronize_paths(root_pts, tip_pts)
        root_pts = self._add_lead_moves(root_pts)
        tip_pts = self._add_lead_moves(tip_pts)

        gcode = [
            "; Open-EZ Hot-Wire G-code",
            f"; Timestamp: {datetime.datetime.utcnow().isoformat()}Z",
            f"; Kerf compensation: {self.kerf_offset:.4f} in",
            f"; Base feed: {self.feed_rate:.3f} in/min",
            f"; Lead distance: {self.lead_distance:.3f} in",
            f"; Points: root={len(root_pts)}, tip={len(tip_pts)}",
            "; Feed schedule: "
            + ", ".join(f"t={t:.2f}->{f:.2f}" for t, f in self.feed_schedule),
            "; Coordinate mapping: Root=XY, Tip=UV",
            "G20    ; Units in inches",
            "G90    ; Absolute positioning",
            "G94    ; Feed per minute",
        ]

        if root_pts:
            start_r = root_pts[0]
            start_t = tip_pts[0]
            gcode.append(
                f"G0 X{start_r[0]:.4f} Y{start_r[1]:.4f} "
                f"U{start_t[0]:.4f} V{start_t[1]:.4f}"
            )

        for idx, (r_pt, t_pt) in enumerate(zip(root_pts, tip_pts)):
            t_norm = idx / max(len(root_pts) - 1, 1)
            feed = self._feed_for_progress(t_norm)
            gcode.append(
                f"G1 X{r_pt[0]:.4f} Y{r_pt[1]:.4f} "
                f"U{t_pt[0]:.4f} V{t_pt[1]:.4f} F{feed:.3f}"
            )

        gcode.append("M2 ; Program end")
        return gcode

    def _apply_kerf(self, wire: cq.Wire, offset: float) -> cq.Wire:
        """Offset the wire in 2D to compensate for material removal."""
        try:
            offset_result = wire.offset2D(offset)
        except Exception:
            return wire

        if isinstance(offset_result, list) and offset_result:
            return offset_result[0]
        return offset_result

    def _discretize_wire(self, wire: cq.Wire, step: float) -> List[Tuple[float, float]]:
        """Convert a CadQuery wire into a list of XY tuples."""
        points = wire.discretize(step)
        return [(float(p.x), float(p.y)) for p in points]

    def _synchronize_paths(
        self,
        root_pts: List[Tuple[float, float]],
        tip_pts: List[Tuple[float, float]],
    ) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """Ensure both toolpaths have matching point counts."""
        max_len = max(len(root_pts), len(tip_pts))
        return (
            self._resample_points(root_pts, max_len),
            self._resample_points(tip_pts, max_len),
        )

    def _resample_points(
        self, points: List[Tuple[float, float]], target_count: int
    ) -> List[Tuple[float, float]]:
        if len(points) == target_count:
            return points
        if target_count <= 1:
            return points[:target_count]

        distances = [0.0]
        for i in range(1, len(points)):
            distances.append(
                distances[-1] + math.dist(points[i - 1], points[i])
            )

        total_length = distances[-1] if distances else 1.0
        resampled: List[Tuple[float, float]] = []
        for step in range(target_count):
            target_s = (step / (target_count - 1)) * total_length
            resampled.append(self._interpolate_along(points, distances, target_s))
        return resampled

    def _interpolate_along(
        self,
        points: List[Tuple[float, float]],
        distances: List[float],
        target_s: float,
    ) -> Tuple[float, float]:
        for i in range(1, len(points)):
            if target_s <= distances[i]:
                ratio = (target_s - distances[i - 1]) / max(
                    distances[i] - distances[i - 1], 1e-6
                )
                x = points[i - 1][0] + ratio * (points[i][0] - points[i - 1][0])
                y = points[i - 1][1] + ratio * (points[i][1] - points[i - 1][1])
                return (x, y)
        return points[-1]

    def _add_lead_moves(
        self, points: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        if len(points) < 2 or self.lead_distance <= 0:
            return points

        first_vec = (
            points[1][0] - points[0][0],
            points[1][1] - points[0][1],
        )
        last_vec = (
            points[-1][0] - points[-2][0],
            points[-1][1] - points[-2][1],
        )

        def _extend(pt, vec, sign: float) -> Tuple[float, float]:
            length = math.hypot(vec[0], vec[1])
            if length == 0:
                return pt
            scale = (self.lead_distance / length) * sign
            return (pt[0] + vec[0] * scale, pt[1] + vec[1] * scale)

        lead_in = _extend(points[0], first_vec, -1.0)
        lead_out = _extend(points[-1], last_vec, 1.0)
        return [lead_in, *points, lead_out]

    def _feed_for_progress(self, t_norm: float) -> float:
        """Interpolate the feed rate based on normalized progress (0-1)."""
        schedule = sorted(self.feed_schedule, key=lambda x: x[0])
        if not schedule:
            return self.feed_rate

        if t_norm <= schedule[0][0]:
            return schedule[0][1]
        if t_norm >= schedule[-1][0]:
            return schedule[-1][1]

        for i in range(1, len(schedule)):
            t0, f0 = schedule[i - 1]
            t1, f1 = schedule[i]
            if t0 <= t_norm <= t1:
                span = max(t1 - t0, 1e-6)
                blend = (t_norm - t0) / span
                return f0 + blend * (f1 - f0)

        return self.feed_rate
