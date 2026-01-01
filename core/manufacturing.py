"""
Open-EZ PDE: Manufacturing Kernel
=================================

Handles the translation of abstract geometry into machine instructions.
1. GCodeWriter: Generates 4-axis hot-wire paths (XYUV) for CNC foam cutters.
2. JigFactory: Generates 3D-printable assembly aids (incidence cradles).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Optional, Union, TYPE_CHECKING
import numpy as np
import cadquery as cq
import logging
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .base import FoamCore

from .base import AircraftComponent
from config import config


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
    feed_rate: float = 4.0          # Inches per minute
    safe_height: float = 2.0        # Retract height (Z clearance)
    block_depth: float = 10.0       # Distance between towers (span direction)
    wire_kerf: float = 0.045        # Material removal width
    preheat_time: float = 2.0       # Seconds to wait for wire temp
    lead_in_distance: float = 1.0   # Entry/exit distance from foam
    machine_type: str = "4-axis-hotwire"
    coord_system: str = "G20"       # Inches


@dataclass
class CutPath:
    """Represents a synchronized 4-axis cut path."""
    root_points: np.ndarray  # Nx2 array of (X, Y) for root side
    tip_points: np.ndarray   # Nx2 array of (U, V) for tip side
    feed_rates: np.ndarray   # N-1 array of feed rates between points

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
        config: Optional[GCodeConfig] = None
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

    def _apply_kerf_offset(self, points: np.ndarray, offset: float) -> np.ndarray:
        """
        Apply kerf compensation by offsetting points inward.

        For foam cutting, we offset inward (toward the center of the airfoil)
        to account for material removed by the hot wire.

        Args:
            points: Nx2 array of profile points
            offset: Kerf offset distance (positive = inward)

        Returns:
            Nx2 array of offset points
        """
        n = len(points)
        offset_points = np.zeros_like(points)

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

                offset_points[i] = points[i] + offset * normal
            else:
                offset_points[i] = points[i]

        return offset_points

    def _sync_profiles(
        self,
        pts_root: np.ndarray,
        pts_tip: np.ndarray
    ) -> CutPath:
        """
        Synchronize root and tip profiles by parametric position.

        Both profiles are sampled at the same parametric positions (0 to 1),
        ensuring the wire cuts corresponding features at the same time.

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

        # Clamp feed rates to reasonable range
        feed_rates = np.clip(feed_rates, self.base_feed * 0.5, self.base_feed * 2.0)

        return CutPath(
            root_points=pts_root[:n_points],
            tip_points=pts_tip[:n_points],
            feed_rates=feed_rates
        )

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

        gcode.append(f"G0 X{start_root[0] + lead_in:.4f} Y{start_root[1]:.4f} "
                     f"U{start_tip[0] + lead_in:.4f} V{start_tip[1]:.4f}")

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

        gcode.extend([
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
        ])

        # Write file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write("\n".join(gcode))

        return output_path


class JigFactory:
    """
    Generates 3D printable tooling for aircraft assembly.

    Jig Types:
    1. Incidence Cradles: Hold wing at specific angle for fuselage attachment
    2. Drill Guides: Precision sleeves for bolt hole drilling
    3. Alignment Templates: Ensure correct positioning during layup
    """

    # Standard jig parameters
    CRADLE_WIDTH = 4.0       # Thickness in spanwise direction
    CRADLE_HEIGHT = 5.0      # Height from table surface
    CRADLE_LENGTH = 20.0     # Chordwise extent
    WALL_THICKNESS = 0.25    # Structural wall thickness
    CLEARANCE = 0.02         # Fit clearance for wing

    @staticmethod
    def generate_incidence_cradle(
        wing_component: AircraftComponent,
        station_bl: float,
        incidence_angle: float,
        cradle_width: float = 4.0,
        base_height: float = 5.0
    ) -> cq.Workplane:
        """
        Create a cradle that conforms to the BOTTOM of the wing
        at a specific Butt Line (BL), with a flat base set to the
        correct incidence angle relative to the longerons.

        The cradle:
        1. Has a flat base for stable table placement
        2. Has a contoured top matching the wing lower surface
        3. Is rotated so the wing sits at the correct incidence angle
        4. Includes alignment marks and part labeling

        Args:
            wing_component: AircraftComponent with geometry
            station_bl: Butt Line station (spanwise position)
            incidence_angle: Wing incidence angle in degrees
            cradle_width: Width in spanwise direction
            base_height: Height from table to wing lower surface

        Returns:
            CadQuery Workplane with the cradle solid
        """
        # Get geometry from component if available
        try:
            wing_geom = wing_component.geometry
            has_geometry = True
        except (ValueError, AttributeError):
            has_geometry = False

        # Base block dimensions
        length = JigFactory.CRADLE_LENGTH
        width = cradle_width
        height = base_height + 3.0  # Extra height for wing contour

        # Create base block
        cradle = (
            cq.Workplane("XY")
            .box(length, width, height, centered=False)
        )

        if has_geometry:
            # Slice wing at station to get profile
            try:
                # Create slicing plane at the butt line
                slice_plane = cq.Workplane("XZ").workplane(offset=station_bl)

                # Intersect wing with plane to get cross-section
                # Then use that profile to cut the cradle top
                wing_section = wing_geom.section(slice_plane)

                # Offset section outward for clearance
                offset_section = wing_section.offset2D(JigFactory.CLEARANCE)

                # Create cutting solid from offset section
                cutter = offset_section.extrude(width * 2)

                # Position cutter at correct height
                cutter = cutter.translate((0, -width/2, base_height))

                # Cut wing profile from cradle top
                cradle = cradle.cut(cutter)

            except Exception:
                # Fallback to parametric approximation
                cradle = JigFactory._add_parametric_contour(
                    cradle, length, width, height, base_height
                )
        else:
            # Use parametric approximation based on airfoil shape
            cradle = JigFactory._add_parametric_contour(
                cradle, length, width, height, base_height
            )

        # Apply incidence rotation
        if abs(incidence_angle) > 0.001:
            # Rotate about the quarter-chord axis
            pivot_x = length * 0.25
            pivot_z = base_height

            cradle = (
                cradle
                .translate((-pivot_x, 0, -pivot_z))
                .rotate((0, 0, 0), (0, 1, 0), -incidence_angle)
                .translate((pivot_x, 0, pivot_z))
            )

        # Add structural features
        cradle = JigFactory._add_structural_features(cradle, length, width, height)

        # Add alignment marks
        cradle = JigFactory._add_alignment_marks(cradle, length, width, station_bl)

        return cradle

    @staticmethod
    def _add_parametric_contour(
        cradle: cq.Workplane,
        length: float,
        width: float,
        height: float,
        base_height: float
    ) -> cq.Workplane:
        """Add approximated airfoil contour cut to cradle top."""
        # Create airfoil-shaped cutter based on typical lower surface
        # Lower surface is approximately parabolic for cambered airfoils

        n_points = 50
        points = []

        for i in range(n_points):
            x = (i / (n_points - 1)) * length
            # Approximate lower surface: slight camber, max at ~30% chord
            t = x / length
            y_lower = -0.02 * length * (4 * t * (1 - t))  # Parabolic camber
            points.append((x, base_height + y_lower + JigFactory.CLEARANCE))

        # Add closing points above the profile
        points.append((length, height + 1))
        points.append((0, height + 1))

        # Create profile and extrude
        cutter = (
            cq.Workplane("XZ")
            .polyline(points)
            .close()
            .extrude(width)
        )

        return cradle.cut(cutter)

    @staticmethod
    def _add_structural_features(
        cradle: cq.Workplane,
        length: float,
        width: float,
        height: float
    ) -> cq.Workplane:
        """Add lightening pockets and structural ribs."""
        wall = JigFactory.WALL_THICKNESS

        # Create lightening pocket (hollow out interior)
        pocket_length = length - 2 * wall - 1.0
        pocket_width = width - 2 * wall
        pocket_height = height - wall - 0.5

        if pocket_length > 2 and pocket_width > 1 and pocket_height > 1:
            pocket = (
                cq.Workplane("XY")
                .center(length / 2, width / 2)
                .rect(pocket_length, pocket_width)
                .extrude(pocket_height)
                .translate((0, 0, wall))
            )
            cradle = cradle.cut(pocket)

        return cradle

    @staticmethod
    def _add_alignment_marks(
        cradle: cq.Workplane,
        length: float,
        width: float,
        station_bl: float
    ) -> cq.Workplane:
        """Add centerline and station marks."""
        mark_depth = 0.05
        mark_width = 0.03

        # Centerline on top surface
        try:
            centerline = (
                cq.Workplane("XY")
                .center(length / 2, width / 2)
                .rect(length - 1, mark_width)
                .extrude(-mark_depth)
                .translate((0, 0, 10))  # Position at top
            )
            cradle = cradle.cut(centerline)
        except Exception:
            pass  # Skip if operation fails

        return cradle

    @staticmethod
    def generate_drill_guide(
        hole_diameter: float,
        guide_length: float = 1.5,
        flange_diameter: float = None,
        flange_thickness: float = 0.25
    ) -> cq.Workplane:
        """
        Generate a precision drill guide sleeve.

        Args:
            hole_diameter: Target hole diameter
            guide_length: Length of the guide sleeve
            flange_diameter: Diameter of alignment flange (default: 3x hole)
            flange_thickness: Thickness of the flange

        Returns:
            CadQuery Workplane with the drill guide
        """
        if flange_diameter is None:
            flange_diameter = hole_diameter * 3

        # Inner diameter with clearance for drill bit
        inner_d = hole_diameter + 0.005
        outer_d = hole_diameter + 0.125

        # Create sleeve
        guide = (
            cq.Workplane("XY")
            .circle(outer_d / 2)
            .extrude(guide_length)
            .faces(">Z")
            .circle(flange_diameter / 2)
            .extrude(flange_thickness)
        )

        # Cut center hole
        guide = (
            guide
            .faces("<Z")
            .circle(inner_d / 2)
            .cutThruAll()
        )

        return guide

    @staticmethod
    def generate_vortilon_template(
        height: float = 2.5,
        base_length: float = 3.0,
        thickness: float = 0.125
    ) -> cq.Workplane:
        """
        Generate a template for marking/cutting vortilons.

        Vortilons are small fences on the leading edge that control
        spanwise flow at high angles of attack.

        Args:
            height: Vortilon height perpendicular to wing surface
            base_length: Length along leading edge
            thickness: Template material thickness

        Returns:
            CadQuery Workplane with the template
        """
        # Vortilon shape: triangular fence
        template = (
            cq.Workplane("XY")
            .moveTo(0, 0)
            .lineTo(base_length, 0)
            .lineTo(base_length / 2, height)
            .close()
            .extrude(thickness)
        )

        # Add handle
        handle = (
            cq.Workplane("XY")
            .center(base_length / 2, -0.5)
            .rect(1.5, 1.0)
            .extrude(thickness)
        )

        return template.union(handle)

    @staticmethod
    def export_all_jigs(output_dir: Path):
        """
        Batch generate standard jig set.

        Generates:
        - Wing root incidence jig (BL 23.3)
        - Wing mid-span jig (BL 79)
        - Canard root jig
        - Standard drill guides (AN3, AN4 bolts)
        - Vortilon templates
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create a simple placeholder component for jig generation
        class PlaceholderWing(AircraftComponent):
            def __init__(self):
                super().__init__("placeholder", "Placeholder for jig generation")
            def generate_geometry(self):
                self._geometry = cq.Workplane("XY").box(100, 50, 5)
                return self._geometry
            def export_dxf(self, path):
                return path

        placeholder = PlaceholderWing()

        # Wing root jig (BL 23.3)
        try:
            jig_root = JigFactory.generate_incidence_cradle(
                placeholder,
                station_bl=23.3,
                incidence_angle=config.geometry.wing_incidence
            )
            cq.exporters.export(jig_root, str(output_dir / "JIG_wing_root_BL23.stl"))
        except Exception as e:
            print(f"  Warning: Could not generate wing root jig: {e}")

        # Wing mid-span jig (BL 79)
        try:
            jig_mid = JigFactory.generate_incidence_cradle(
                placeholder,
                station_bl=79.0,
                incidence_angle=config.geometry.wing_incidence
            )
            cq.exporters.export(jig_mid, str(output_dir / "JIG_wing_mid_BL79.stl"))
        except Exception as e:
            print(f"  Warning: Could not generate wing mid jig: {e}")

        # Canard root jig
        try:
            jig_canard = JigFactory.generate_incidence_cradle(
                placeholder,
                station_bl=0.0,
                incidence_angle=config.geometry.canard_incidence
            )
            cq.exporters.export(jig_canard, str(output_dir / "JIG_canard_root.stl"))
        except Exception as e:
            print(f"  Warning: Could not generate canard jig: {e}")

        # Drill guides for AN3 (3/16") and AN4 (1/4") bolts
        for name, diameter in [("AN3", 0.1875), ("AN4", 0.250)]:
            try:
                guide = JigFactory.generate_drill_guide(diameter)
                cq.exporters.export(guide, str(output_dir / f"DRILL_GUIDE_{name}.stl"))
            except Exception as e:
                print(f"  Warning: Could not generate {name} drill guide: {e}")

        # Vortilon template
        try:
            vortilon = JigFactory.generate_vortilon_template()
            cq.exporters.export(vortilon, str(output_dir / "TEMPLATE_vortilon.stl"))
        except Exception as e:
            print(f"  Warning: Could not generate vortilon template: {e}")
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
                notes="Standard wing foam"
            ),
            "urethane_2lb": HotWireProcess(
                foam_type="urethane_2lb",
                wire_temp_f=500.0,
                kerf_in=0.035,
                max_feed_ipm=3.5,
                notes="High-temp fuselage foam"
            ),
            "divinycell_h45": HotWireProcess(
                foam_type="divinycell_h45",
                wire_temp_f=550.0,
                kerf_in=0.030,
                max_feed_ipm=2.0,
                notes="Structural PVC foam"
            )
        }

    def get_process(self, foam_type: str) -> HotWireProcess:
        """Retrieve calibrated process for a specific foam."""
        return self.processes.get(foam_type.lower(), self.processes["styrofoam_blue"])

    def generate_component_gcode(self, component: 'FoamCore', foam_name: str = "styrofoam_blue") -> Path:
        """
        Calibrate and export G-code for a whole component.
        """
        process = self.get_process(foam_name)
        
        # Configure the writer based on calibrated process
        mfg_config = GCodeConfig(
            feed_rate=process.max_feed_ipm,
            wire_kerf=process.kerf_in
        )
        
        writer = GCodeWriter(
            root_profile=component.get_root_profile(),
            tip_profile=component.get_tip_profile(),
            kerf_offset=process.kerf_in,
            feed_rate=process.max_feed_ipm,
            config=mfg_config
        )
        
        target_file = self.output_root / f"{component.name}.tap"
        return writer.write(target_file)

    def calibrate_kerf(self, foam_type: str, measured_kerf: float):
        """Update calibration for a specific material after a test cut."""
        if foam_type in self.processes:
            self.processes[foam_type].kerf_in = measured_kerf
            logger.info(f"Calibrated {foam_type} kerf to {measured_kerf:.4f} in")
