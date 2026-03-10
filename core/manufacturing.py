"""
Open-EZ PDE: Manufacturing Kernel
=================================

Handles the translation of abstract geometry into machine instructions.
1. GCodeWriter: Generates 4-axis hot-wire paths (XYUV) for CNC foam cutters.
2. JigFactory:  Generates 3D-printable assembly aids (incidence cradles).
   (extracted to core.jig_factory — re-exported here for backward compat)

Module layout
-------------
- HotWireProcess  – foam + wire calibration parameters
- GCodeConfig     – CNC machine configuration
- CutPath         – synchronized 4-axis cut path
- GCodeWriter     – 4-axis G-code generation
- GCodeEngine     – high-level orchestrator for batch G-code generation

JigFactory and FuselageJigFactory are re-exported from core.jig_factory.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, TYPE_CHECKING

import cadquery as cq
import numpy as np

from config import config

# Re-exports for backward compatibility
from .jig_factory import JigFactory, FuselageJigFactory  # noqa: F401

logger = logging.getLogger(__name__)

# NOTE: Circular dependency — structures.py runtime-imports JigFactory from
# this module.  The imports below MUST stay behind TYPE_CHECKING to break the
# cycle; they are only needed for type annotations, not at runtime.
if TYPE_CHECKING:
    from .base import FoamCore


@dataclass
class HotWireProcess:
    """Defines the relationship between material and cutting parameters."""

    foam_type: str
    wire_temp_f: float
    kerf_in: float
    max_feed_ipm: float
    notes: str = ""


@dataclass
class GCodeConfig:
    """CNC Machine Configuration."""

    feed_rate: float = 4.0  # Inches per minute
    safe_height: float = 2.0  # Retract height (Z clearance)
    block_depth: float = 10.0  # Distance between towers (span direction)
    wire_kerf: float = 0.045  # Material removal width
    preheat_time: float = 2.0  # Seconds to wait for wire temp
    lead_in_distance: float = 1.0  # Entry/exit distance from foam
    machine_type: str = "4-axis-hotwire"
    coord_system: str = "G20"  # Inches


@dataclass
class CutPath:
    """Represents a synchronized 4-axis cut path."""

    root_points: np.ndarray  # Nx2 array of (X, Y) for root side
    tip_points: np.ndarray  # Nx2 array of (U, V) for tip side
    feed_rates: np.ndarray  # N-1 array of feed rates between points

    @property
    def num_points(self) -> int:
        return len(self.root_points)


class GCodeWriter:
    """
    4-Axis G-Code Generator for Tapered Wings.

    Solves the "Synchronization Problem":
    Since the root chord is longer than the tip chord, the root axis (XY)
    must move faster than the tip axis (UV) so the wire enters and exits
    the foam block at the exact same time.

    The wire must traverse both profiles simultaneously by parametric position,
    not by arc length. This means the XY axes move proportionally faster for
    longer root chords.
    """

    def __init__(
        self,
        root_profile: cq.Wire,
        tip_profile: cq.Wire,
        kerf_offset: float = 0.045,
        feed_rate: float = 4.0,
        config: Optional[GCodeConfig] = None,
    ):
        self.root = root_profile
        self.tip = tip_profile
        self.kerf = kerf_offset
        self.base_feed = feed_rate
        self.config = config or GCodeConfig(feed_rate=feed_rate, wire_kerf=kerf_offset)

    def _discretize_wire(self, wire: cq.Wire, num_points: int = 100) -> np.ndarray:
        """
        Convert a CadQuery wire into an ordered array of 2D points.

        Uses arc-length parameterization for uniform point distribution.

        Args:
            wire: CadQuery Wire object representing the airfoil profile
            num_points: Number of points to sample along the wire

        Returns:
            Nx2 numpy array of (x, y) coordinates
        """
        points = []

        # Get all edges from the wire
        edges = wire.Edges()

        if not edges:
            # Fallback: generate points from wire bounding box
            bbox = wire.BoundingBox()
            # Create simple rectangular approximation
            for i in range(num_points):
                t = i / (num_points - 1)
                x = bbox.xmin + t * (bbox.xmax - bbox.xmin)
                y = 0.0
                points.append((x, y))
            return np.array(points)

        # Calculate total arc length
        total_length = sum(e.Length() for e in edges)

        # Sample points uniformly by arc length
        target_spacing = total_length / (num_points - 1)

        accumulated_length = 0.0
        point_idx = 0

        for edge in edges:
            edge_length = edge.Length()

            # Sample this edge
            while accumulated_length <= edge_length and point_idx < num_points:
                # Parameter t for this edge (0 to 1)
                if edge_length > 0:
                    t = accumulated_length / edge_length
                else:
                    t = 0.0

                # Get 3D point at parameter t
                try:
                    pt = edge.positionAt(t)
                    points.append((pt.x, pt.y))
                except Exception:
                    # Fallback if positionAt fails
                    start = edge.startPoint()
                    end = edge.endPoint()
                    x = start.x + t * (end.x - start.x)
                    y = start.y + t * (end.y - start.y)
                    points.append((x, y))

                point_idx += 1
                accumulated_length += target_spacing

            # Adjust for next edge
            accumulated_length -= edge_length

        # Ensure we have exactly num_points
        while len(points) < num_points:
            # Duplicate last point if needed
            points.append(points[-1] if points else (0.0, 0.0))

        return np.array(points[:num_points])

    def _apply_kerf_offset(
        self,
        points: np.ndarray,
        offset,
    ) -> np.ndarray:
        """
        Apply kerf compensation by offsetting points inward.

        For foam cutting, we offset inward (toward the center of the airfoil)
        to account for material removed by the hot wire.

        Supports per-point kerf via array offset (for velocity-coupled kerf).

        Args:
            points: Nx2 array of profile points
            offset: Scalar kerf distance or Nx1 array of per-point offsets

        Returns:
            Nx2 array of offset points
        """
        n = len(points)
        offset_points = np.zeros_like(points)

        # Support scalar or per-point offset
        if np.isscalar(offset):
            offsets = np.full(n, offset)
        else:
            offsets = np.asarray(offset)
            if len(offsets) != n:
                offsets = np.full(n, float(offsets[0]) if len(offsets) > 0 else 0.0)

        for i in range(n):
            # Get neighboring points for normal calculation
            prev_idx = (i - 1) % n
            next_idx = (i + 1) % n

            # Tangent vector (average of forward and backward)
            tangent = points[next_idx] - points[prev_idx]
            tangent_len = np.linalg.norm(tangent)

            if tangent_len > 1e-10:
                tangent = tangent / tangent_len

                # Normal vector (perpendicular, pointing inward)
                # For clockwise-ordered airfoil, rotate tangent -90 degrees
                normal = np.array([-tangent[1], tangent[0]])

                # Determine if we need to flip normal to point inward
                # Check if offset would move point toward centroid
                centroid = np.mean(points, axis=0)
                to_centroid = centroid - points[i]

                if np.dot(normal, to_centroid) < 0:
                    normal = -normal

                offset_points[i] = points[i] + offsets[i] * normal
            else:
                offset_points[i] = points[i]

        return offset_points

    def _sync_profiles(self, pts_root: np.ndarray, pts_tip: np.ndarray) -> CutPath:
        """
        Synchronize root and tip profiles by parametric position.

        Both profiles are sampled at the same parametric positions (0 to 1),
        ensuring the wire cuts corresponding features at the same time.

        Enhancements:
        - Curvature-based slowdown at LE/TE (> 0.5 rad turning angle)
        - Velocity ratio clamping (max 2.5:1 root/tip speed)

        Args:
            pts_root: Nx2 array of root profile points
            pts_tip: Nx2 array of tip profile points

        Returns:
            CutPath with synchronized coordinates and feed rates
        """
        n_points = min(len(pts_root), len(pts_tip))

        # Calculate segment lengths for feed rate computation
        root_segments = np.linalg.norm(np.diff(pts_root[:n_points], axis=0), axis=1)
        tip_segments = np.linalg.norm(np.diff(pts_tip[:n_points], axis=0), axis=1)

        # Feed rate must be based on the longer segment (limiting factor)
        # The wire speed is limited by whichever side has to move faster
        max_segments = np.maximum(root_segments, tip_segments)

        # Normalize feed rates - base feed applies to average segment length
        avg_segment = np.mean(max_segments) if len(max_segments) > 0 else 1.0
        feed_rates = self.base_feed * (avg_segment / np.maximum(max_segments, 1e-6))

        # === Curvature-based feed rate modulation ===
        # At high-curvature points (LE/TE), reduce feed to prevent wire drag.
        # Use max turning angle across root and tip to apply penalty once per
        # segment, preventing double-stacking that could drop to 0.36x.
        for i in range(1, len(root_segments)):
            max_angle = 0.0
            for pts, segments in [(pts_root, root_segments), (pts_tip, tip_segments)]:
                if i < len(segments) and i + 1 < n_points:
                    v1 = pts[i] - pts[i - 1]
                    v2 = pts[i + 1] - pts[i]
                    cross = v1[0] * v2[1] - v1[1] * v2[0]
                    dot = np.dot(v1, v2)
                    max_angle = max(max_angle, abs(np.arctan2(cross, dot)))
            if max_angle > 0.5:  # > ~29 deg turning angle
                feed_rates[i - 1] *= 0.6  # 40% slowdown at LE (applied once)

        # === Velocity ratio clamping ===
        # Prevent root/tip speed differential exceeding 2.5:1
        for i in range(len(root_segments)):
            if root_segments[i] > 1e-10 and tip_segments[i] > 1e-10:
                ratio = max(root_segments[i], tip_segments[i]) / min(
                    root_segments[i], tip_segments[i]
                )
                if ratio > 2.5:
                    feed_rates[i] *= 1.25  # Speed up to reduce over-melt

        # Clamp feed rates to reasonable range
        feed_rates = np.clip(feed_rates, self.base_feed * 0.3, self.base_feed * 2.0)

        return CutPath(
            root_points=pts_root[:n_points],
            tip_points=pts_tip[:n_points],
            feed_rates=feed_rates,
        )

    @staticmethod
    def calculate_velocity_coupled_kerf(
        base_kerf: float, base_feed: float, feed_rates: np.ndarray
    ) -> np.ndarray:
        """Compute per-point kerf offsets coupled to feed rate.

        Slower feed -> longer dwell -> wider kerf due to radiant heat.
        kerf_local = base_kerf * sqrt(base_feed / local_feed)

        Args:
            base_kerf: Baseline kerf offset in inches
            base_feed: Baseline feed rate in/min
            feed_rates: Array of local feed rates

        Returns:
            Array of per-point kerf offsets
        """
        return base_kerf * np.sqrt(base_feed / np.maximum(feed_rates, 0.1))

    def _find_start_point(self, points: np.ndarray) -> int:
        """
        Find optimal starting point for the cut (trailing edge).

        We start at the trailing edge to minimize wire stress during entry.

        Args:
            points: Nx2 array of profile points

        Returns:
            Index of the trailing edge point
        """
        # Trailing edge is typically at maximum X
        return int(np.argmax(points[:, 0]))

    def _reorder_from_start(self, points: np.ndarray, start_idx: int) -> np.ndarray:
        """Reorder points to start from specified index."""
        return np.roll(points, -start_idx, axis=0)

    def generate_cut_path(self, num_points: int = 100) -> CutPath:
        """
        Generate the complete synchronized cut path.

        Args:
            num_points: Number of sample points per profile

        Returns:
            CutPath with all cutting coordinates
        """
        # Discretize both wires
        root_pts = self._discretize_wire(self.root, num_points)
        tip_pts = self._discretize_wire(self.tip, num_points)

        # Apply kerf compensation
        root_pts = self._apply_kerf_offset(root_pts, self.kerf)
        tip_pts = self._apply_kerf_offset(tip_pts, self.kerf)

        # Find and align start points (trailing edge)
        root_start = self._find_start_point(root_pts)
        tip_start = self._find_start_point(tip_pts)

        root_pts = self._reorder_from_start(root_pts, root_start)
        tip_pts = self._reorder_from_start(tip_pts, tip_start)

        # Synchronize profiles
        return self._sync_profiles(root_pts, tip_pts)

    def write(self, output_path: Path, num_points: int = 100) -> Path:
        """
        Generate and save the 4-axis G-code file.

        Args:
            output_path: Path for the output .tap file
            num_points: Number of sample points per profile

        Returns:
            Path to the written file
        """
        # Generate synchronized cut path
        cut_path = self.generate_cut_path(num_points)

        # Build G-code
        gcode = [
            "( ========================================= )",
            "( Open-EZ PDE: 4-Axis Wing Core            )",
            f"( Generated: {config.project_name} v{config.version} )",
            "( ========================================= )",
            "",
            "( Machine Setup )",
            "G90 ( Absolute positioning )",
            "G20 ( Units: Inches )",
            f"F{self.base_feed:.2f} ( Default Feed Rate IPM )",
            "",
            "( Safety: Retract to safe height )",
            f"G0 Z{self.config.safe_height:.3f}",
            "",
            "( Preheat wire )",
            "M3 ( Spindle/Heat ON )",
            f"G4 P{self.config.preheat_time:.1f} ( Wait for wire temp )",
            "",
            "( Lead-in: Move to start position )",
        ]

        # Start position with lead-in
        start_root = cut_path.root_points[0]
        start_tip = cut_path.tip_points[0]
        lead_in = self.config.lead_in_distance

        gcode.append(
            f"G0 X{start_root[0] + lead_in:.4f} Y{start_root[1]:.4f} "
            f"U{start_tip[0] + lead_in:.4f} V{start_tip[1]:.4f}"
        )

        # Plunge to cutting height
        gcode.append("G0 Z0 ( Plunge to cut level )")
        gcode.append("")
        gcode.append("( Begin synchronized cut )")

        # Main cutting loop with adaptive feed rates
        for i in range(cut_path.num_points):
            x, y = cut_path.root_points[i]
            u, v = cut_path.tip_points[i]

            # Use segment-specific feed rate (except for first point)
            if i > 0 and i - 1 < len(cut_path.feed_rates):
                feed = cut_path.feed_rates[i - 1]
                gcode.append(f"G1 X{x:.4f} Y{y:.4f} U{u:.4f} V{v:.4f} F{feed:.2f}")
            else:
                gcode.append(f"G1 X{x:.4f} Y{y:.4f} U{u:.4f} V{v:.4f}")

        # Close the loop (return to start)
        x, y = cut_path.root_points[0]
        u, v = cut_path.tip_points[0]
        gcode.append(f"G1 X{x:.4f} Y{y:.4f} U{u:.4f} V{v:.4f} ( Close loop )")

        gcode.extend(
            [
                "",
                "( Lead-out )",
                f"G1 X{x + lead_in:.4f} Y{y:.4f} U{u + lead_in:.4f} V{v:.4f}",
                "",
                "( Shutdown )",
                "M5 ( Heat OFF )",
                f"G0 Z{self.config.safe_height:.3f} ( Retract )",
                "G0 X0 Y0 U0 V0 ( Return home )",
                "M30 ( Program End )",
                "",
                f"( Total points: {cut_path.num_points} )",
                f"( Kerf compensation: {self.kerf:.4f} in )",
            ]
        )

        # Write file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write("\n".join(gcode))

        return output_path


class GCodeEngine:
    """
    High-level orchestrator for manufacturing output.

    Manages:
    - Material-specific process calibration (Kerf vs Speed)
    - Batch generation for multiple wing segments
    - Automated artifact naming and storage
    """

    def __init__(self, output_root: Union[Path, str] = Path("output/gcode")):
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)

        # Calibration database (Foam Type -> Process)
        self.processes = {
            "styrofoam_blue": HotWireProcess(
                foam_type="styrofoam_blue",
                wire_temp_f=400.0,
                kerf_in=0.045,
                max_feed_ipm=5.0,
                notes="Standard wing foam",
            ),
            "urethane_2lb": HotWireProcess(
                foam_type="urethane_2lb",
                wire_temp_f=500.0,
                kerf_in=0.035,
                max_feed_ipm=3.5,
                notes="High-temp fuselage foam",
            ),
            "divinycell_h45": HotWireProcess(
                foam_type="divinycell_h45",
                wire_temp_f=550.0,
                kerf_in=0.030,
                max_feed_ipm=2.0,
                notes="Structural PVC foam",
            ),
        }

    def get_process(self, foam_type: str) -> HotWireProcess:
        """Retrieve calibrated process for a specific foam."""
        return self.processes.get(foam_type.lower(), self.processes["styrofoam_blue"])

    def generate_component_gcode(
        self, component: "FoamCore", foam_name: str = "styrofoam_blue"
    ) -> Path:
        """
        Calibrate and export G-code for a whole component.
        """
        process = self.get_process(foam_name)

        # Configure the writer based on calibrated process
        mfg_config = GCodeConfig(
            feed_rate=process.max_feed_ipm, wire_kerf=process.kerf_in
        )

        writer = GCodeWriter(
            root_profile=component.get_root_profile(),
            tip_profile=component.get_tip_profile(),
            kerf_offset=process.kerf_in,
            feed_rate=process.max_feed_ipm,
            config=mfg_config,
        )

        target_file = self.output_root / f"{component.name}.tap"
        return writer.write(target_file)

    def calibrate_kerf(self, foam_type: str, measured_kerf: float):
        """Update calibration for a specific material after a test cut."""
        if foam_type in self.processes:
            self.processes[foam_type].kerf_in = measured_kerf
            logger.info(f"Calibrated {foam_type} kerf to {measured_kerf:.4f} in")
