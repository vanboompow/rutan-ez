"""
Open-EZ PDE: Jig Factory
=========================

Generates 3D-printable assembly aids and fuselage jigs.

1. JigFactory: Incidence cradles, drill guides, vortilon templates.
2. FuselageJigFactory: Build strongback, bulkhead saddles, foam slabs.

These were previously embedded in core/manufacturing.py.

Backward compatibility: ``from core.manufacturing import JigFactory`` still
works because manufacturing.py re-exports this name.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

import cadquery as cq
import numpy as np

if TYPE_CHECKING:
    from .structures import BulkheadProfile, Fuselage

from .base import AircraftComponent  # noqa: E402
from config import config  # noqa: E402

logger = logging.getLogger(__name__)


class JigFactory:
    """
    Generates 3D printable tooling for aircraft assembly.

    Jig Types:
    1. Incidence Cradles: Hold wing at specific angle for fuselage attachment
    2. Drill Guides: Precision sleeves for bolt hole drilling
    3. Alignment Templates: Ensure correct positioning during layup
    """

    # Standard jig parameters
    CRADLE_WIDTH = 4.0  # Thickness in spanwise direction
    CRADLE_HEIGHT = 5.0  # Height from table surface
    CRADLE_LENGTH = 20.0  # Chordwise extent
    WALL_THICKNESS = 0.25  # Structural wall thickness
    CLEARANCE = 0.02  # Fit clearance for wing

    @staticmethod
    def generate_incidence_cradle(
        wing_component: AircraftComponent,
        station_bl: float,
        incidence_angle: float,
        cradle_width: float = 4.0,
        base_height: float = 5.0,
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
            has_geometry = wing_geom is not None
        except (ValueError, AttributeError):
            wing_geom = None
            has_geometry = False

        # Base block dimensions
        length = JigFactory.CRADLE_LENGTH
        width = cradle_width
        height = base_height + 3.0  # Extra height for wing contour

        # Create base block
        cradle = cq.Workplane("XY").box(length, width, height, centered=False)

        if has_geometry and wing_geom is not None:
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
                cutter = cutter.translate((0, -width / 2, base_height))

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
                cradle.translate((-pivot_x, 0, -pivot_z))
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
        base_height: float,
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
        cutter = cq.Workplane("XZ").polyline(points).close().extrude(width)

        return cradle.cut(cutter)

    @staticmethod
    def _add_structural_features(
        cradle: cq.Workplane, length: float, width: float, height: float
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
        cradle: cq.Workplane, length: float, width: float, station_bl: float
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
        flange_diameter: Optional[float] = None,
        flange_thickness: float = 0.25,
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
        guide = guide.faces("<Z").circle(inner_d / 2).cutThruAll()

        return guide

    @staticmethod
    def generate_vortilon_template(
        height: float = 2.5, base_length: float = 3.0, thickness: float = 0.125
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

            def _build_geometry(self):
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
                incidence_angle=config.geometry.wing_incidence,
            )
            cq.exporters.export(jig_root, str(output_dir / "JIG_wing_root_BL23.stl"))
        except Exception as e:
            print(f"  Warning: Could not generate wing root jig: {e}")

        # Wing mid-span jig (BL 79)
        try:
            jig_mid = JigFactory.generate_incidence_cradle(
                placeholder,
                station_bl=79.0,
                incidence_angle=config.geometry.wing_incidence,
            )
            cq.exporters.export(jig_mid, str(output_dir / "JIG_wing_mid_BL79.stl"))
        except Exception as e:
            print(f"  Warning: Could not generate wing mid jig: {e}")

        # Canard root jig
        try:
            jig_canard = JigFactory.generate_incidence_cradle(
                placeholder,
                station_bl=0.0,
                incidence_angle=config.geometry.canard_incidence,
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


class FuselageJigFactory:
    """
    Generate assembly fixtures for fuselage construction.

    The Long-EZ fuselage is built using one of two methods:
    1. BOW_FOAM (Classic Rutan): Flat foam slabs bowed into curved sides
    2. CNC_MILLED: 5-axis milled foam blocks for precision

    This factory generates the tooling required for either approach:
    - Build strongback (external alignment frame)
    - Bulkhead saddles (position locators)
    - Foam slab patterns (for bow_foam method)
    - Block alignment features (for cnc_milled method)
    """

    # Strongback lumber dimensions (standard 2x4)
    RAIL_WIDTH = 1.5  # Actual 2x4 width
    RAIL_HEIGHT = 3.5  # Actual 2x4 height
    CROSSBRACE_SPACING = 12.0  # inches between braces
    SADDLE_THICKNESS = 0.75  # Plywood saddle thickness
    ALIGNMENT_PIN_DIA = 0.25  # 1/4" dowel pins
    CENTERLINE_MARK_DEPTH = 0.1  # Laser/router engraving depth

    @staticmethod
    def generate_build_strongback(
        fuselage: "Fuselage",
        stations: Optional[List[float]] = None,
        table_width: float = 36.0,
        table_length: float = 240.0,
    ) -> cq.Assembly:
        """
        Create external 'canoe' frame for fuselage alignment.

        The strongback holds bulkheads at exact FS positions during:
        - Foam slab bonding
        - Skin layup
        - Internal systems routing

        Args:
            fuselage: Fuselage component with profiles
            stations: Optional list of stations; defaults to fuselage profiles
            table_width: Width of work table (inches)
            table_length: Length of work table (inches)

        Returns:
            CadQuery Assembly with:
            - Longitudinal rails (2x4 lumber profiles)
            - Cross-braces at each bulkhead station
            - Adjustable bulkhead saddles
            - Centerline laser alignment marks
        """
        assembly = cq.Assembly()

        # Get station positions from fuselage profiles
        if stations is None:
            stations = [p.station for p in fuselage._profiles if p.width > 1.0]

        rail_w = FuselageJigFactory.RAIL_WIDTH
        rail_h = FuselageJigFactory.RAIL_HEIGHT

        # Longitudinal rails (left and right)
        rail_spacing = table_width - 2 * rail_w
        rail_length = max(stations) - min(stations) + 24.0  # Extra length at ends

        left_rail = cq.Workplane("XY").box(rail_length, rail_w, rail_h, centered=False)
        right_rail = left_rail.translate((0, rail_spacing + rail_w, 0))

        assembly.add(left_rail, name="rail_left", color=cq.Color("burlywood"))
        assembly.add(right_rail, name="rail_right", color=cq.Color("burlywood"))

        # Cross-braces at each station
        for i, station in enumerate(stations):
            brace_x = station - min(stations) + 12.0  # Offset from rail start
            crossbrace = (
                cq.Workplane("XY")
                .center(brace_x, 0)
                .box(rail_w, table_width, rail_h, centered=False)
                .translate((0, 0, rail_h))  # Stack on top of rails
            )
            assembly.add(
                crossbrace, name=f"brace_FS{station:.0f}", color=cq.Color("burlywood")
            )

        # Add centerline reference groove
        centerline_y = table_width / 2
        centerline = (
            cq.Workplane("XY")
            .center(rail_length / 2, centerline_y)
            .rect(rail_length - 4.0, 0.125)
            .extrude(-FuselageJigFactory.CENTERLINE_MARK_DEPTH)
            .translate((0, 0, rail_h * 2))
        )
        assembly.add(centerline, name="centerline_mark", color=cq.Color("red"))

        return assembly

    @staticmethod
    def generate_bulkhead_saddle(
        profile: "BulkheadProfile",
        tolerance: float = 0.030,
        saddle_depth: float = 2.0,
    ) -> cq.Workplane:
        """
        Saddle fixture that locates bulkhead in strongback.

        Features:
        - Negative of bulkhead perimeter (with tolerance)
        - Registration pins at centerline
        - Vertical reference notches
        - Mounting tabs for strongback rails

        Args:
            profile: BulkheadProfile defining the cross-section
            tolerance: Fit clearance (inches)
            saddle_depth: Depth of the bulkhead pocket

        Returns:
            CadQuery Workplane with saddle geometry
        """
        # Base saddle dimensions
        base_width = profile.width + 4.0  # Extra width for mounting tabs
        base_height = profile.height + 3.0  # Extra height for support
        thickness = FuselageJigFactory.SADDLE_THICKNESS

        # Create base plate
        saddle = cq.Workplane("XY").rect(base_width, base_height).extrude(thickness)

        # Create bulkhead pocket (negative of profile + tolerance)
        pocket_w = profile.width / 2 + tolerance
        pocket_h = profile.height / 2 + tolerance

        if pocket_w > 0.5 and pocket_h > 0.5:
            # Elliptical pocket matching bulkhead
            pocket = (
                cq.Workplane("XY")
                .center(0, profile.floor_height + pocket_h)
                .ellipse(pocket_h, pocket_w)
                .extrude(saddle_depth)
            )
            saddle = saddle.cut(pocket)

        # Add registration pin holes at centerline
        pin_dia = FuselageJigFactory.ALIGNMENT_PIN_DIA
        pin_positions = [
            (0, profile.floor_height - 0.5),  # Below floor
            (0, profile.floor_height + profile.height + 0.5),  # Above top
        ]

        for px, py in pin_positions:
            pin_hole = (
                cq.Workplane("XY")
                .center(px, py)
                .circle(pin_dia / 2)
                .extrude(thickness * 2)
            )
            saddle = saddle.cut(pin_hole)

        # Add vertical reference notches (for level alignment)
        notch_width = 0.25
        notch_depth = 0.5
        notch_positions = [
            (-base_width / 2 + notch_depth / 2, 0),
            (base_width / 2 - notch_depth / 2, 0),
        ]

        for nx, ny in notch_positions:
            notch = (
                cq.Workplane("XY")
                .center(nx, ny)
                .rect(notch_depth, notch_width)
                .extrude(thickness)
            )
            saddle = saddle.cut(notch)

        # Add mounting tabs with screw holes
        tab_width = 1.5
        tab_length = 1.0
        screw_dia = 0.1875  # #10 screw

        tab_positions = [
            (-base_width / 2 - tab_length / 2, -base_height / 2 + tab_width / 2),
            (-base_width / 2 - tab_length / 2, base_height / 2 - tab_width / 2),
            (base_width / 2 + tab_length / 2, -base_height / 2 + tab_width / 2),
            (base_width / 2 + tab_length / 2, base_height / 2 - tab_width / 2),
        ]

        for tx, ty in tab_positions:
            tab = (
                cq.Workplane("XY")
                .center(tx, ty)
                .rect(tab_length, tab_width)
                .extrude(thickness)
            )
            saddle = saddle.union(tab)

            # Add screw hole
            screw_hole = (
                cq.Workplane("XY")
                .center(tx, ty)
                .circle(screw_dia / 2)
                .extrude(thickness * 2)
            )
            saddle = saddle.cut(screw_hole)

        # Engrave station number
        # (Placeholder - real implementation would use text engraving)
        station_mark = (
            cq.Workplane("XY")
            .center(0, -base_height / 2 + 0.75)
            .rect(1.5, 0.25)
            .extrude(-0.05)
            .translate((0, 0, thickness))
        )
        saddle = saddle.cut(station_mark)

        return saddle

    @staticmethod
    def generate_fuselage_foam_slabs(
        fuselage: "Fuselage",
        build_method: str = "bow_foam",
        max_block_length: float = 48.0,
    ) -> Dict[str, cq.Workplane]:
        """
        Decompose fuselage OML into manufacturable foam pieces.

        BOW_FOAM method (Classic Rutan):
        - Extract side panels as developable surfaces
        - Generate flat slab outlines with score lines for bowing
        - Mark fiducial points for alignment during assembly

        CNC_MILLED method:
        - Slice fuselage into 48" max blocks along FS axis
        - Generate 5-axis toolpath-ready geometry
        - Add alignment dowel holes at block joints

        Args:
            fuselage: Fuselage component
            build_method: "bow_foam" or "cnc_milled"
            max_block_length: Maximum block length for CNC (inches)

        Returns:
            Dict keyed by part name: 'left_side', 'right_side',
            'bottom', 'nose_block_1', etc.
        """
        slabs: Dict[str, cq.Workplane] = {}

        profiles = [p for p in fuselage._profiles if p.width > 1.0]
        if not profiles:
            return slabs

        if build_method == "bow_foam":
            slabs = FuselageJigFactory._generate_bow_foam_slabs(fuselage, profiles)
        elif build_method == "cnc_milled":
            slabs = FuselageJigFactory._generate_cnc_blocks(
                fuselage, profiles, max_block_length
            )
        else:
            raise ValueError(f"Unknown build method: {build_method}")

        return slabs

    @staticmethod
    def _generate_bow_foam_slabs(
        fuselage: "Fuselage",
        profiles: List["BulkheadProfile"],
    ) -> Dict[str, cq.Workplane]:
        """
        Generate flat foam slabs for the bow_foam build method.

        The Long-EZ uses flat foam slabs that are bowed into curved
        fuselage sides. This generates the flat patterns with:
        - Profile outlines at each station
        - Score lines for controlled bending
        - Fiducial marks for alignment
        """
        slabs: Dict[str, cq.Workplane] = {}

        # Calculate flat pattern dimensions
        _total_length = max(p.station for p in profiles) - min(
            p.station for p in profiles
        )
        max_height = max(p.height for p in profiles)

        # Side panels (left and right are symmetric)
        # Flat pattern approximates the developed surface
        side_points = []
        for profile in profiles:
            # Top edge point
            side_points.append((profile.station, profile.height / 2))

        # Add bottom edge (reverse direction)
        for profile in reversed(profiles):
            side_points.append((profile.station, -profile.height / 2))

        # Create side panel outline
        if len(side_points) >= 3:
            side_panel = (
                cq.Workplane("XY")
                .polyline(side_points)
                .close()
                .extrude(config.materials.foam_core_thickness)
            )

            # Add score lines for bending (perpendicular to length)
            score_spacing = 6.0  # inches between score lines
            min_station = min(p.station for p in profiles)
            max_station = max(p.station for p in profiles)

            score_depth = config.materials.foam_core_thickness * 0.3

            for x in np.arange(min_station + score_spacing, max_station, score_spacing):
                height_at_x = max_height  # Simplified
                score = (
                    cq.Workplane("XY")
                    .center(x, 0)
                    .rect(0.125, height_at_x)
                    .extrude(score_depth)
                    .translate(
                        (0, 0, config.materials.foam_core_thickness - score_depth)
                    )
                )
                side_panel = side_panel.cut(score)

            # Add alignment marks at each station
            for profile in profiles:
                mark = (
                    cq.Workplane("XY")
                    .center(profile.station, 0)
                    .circle(0.125)
                    .extrude(-0.1)
                    .translate((0, 0, config.materials.foam_core_thickness))
                )
                side_panel = side_panel.cut(mark)

            slabs["left_side"] = side_panel
            slabs["right_side"] = side_panel.mirror("XZ")

        # Bottom panel
        bottom_points = []
        for profile in profiles:
            bottom_points.append((profile.station, profile.width / 2))
        for profile in reversed(profiles):
            bottom_points.append((profile.station, -profile.width / 2))

        if len(bottom_points) >= 3:
            bottom_panel = (
                cq.Workplane("XY")
                .polyline(bottom_points)
                .close()
                .extrude(config.materials.foam_core_thickness)
            )
            slabs["bottom"] = bottom_panel

        # Turtle deck (upper rear fuselage)
        # Simplified as a single curved panel
        turtle_start = config.geometry.fs_rear_seat
        turtle_profiles = [p for p in profiles if p.station >= turtle_start]

        if len(turtle_profiles) >= 2:
            turtle_points = []
            for profile in turtle_profiles:
                turtle_points.append((profile.station, profile.width / 2))
            for profile in reversed(turtle_profiles):
                turtle_points.append((profile.station, -profile.width / 2))

            if len(turtle_points) >= 3:
                turtle_deck = (
                    cq.Workplane("XY")
                    .polyline(turtle_points)
                    .close()
                    .extrude(config.materials.foam_core_thickness)
                )
                slabs["turtle_deck"] = turtle_deck

        return slabs

    @staticmethod
    def _generate_cnc_blocks(
        fuselage: "Fuselage",
        profiles: List["BulkheadProfile"],
        max_block_length: float,
    ) -> Dict[str, cq.Workplane]:
        """
        Generate CNC-milled foam blocks.

        Slices the fuselage into sections that fit CNC machine envelope,
        with alignment features at joints.
        """
        slabs: Dict[str, cq.Workplane] = {}

        min_station = min(p.station for p in profiles)
        max_station = max(p.station for p in profiles)
        total_length = max_station - min_station

        # Calculate number of blocks needed
        num_blocks = int(np.ceil(total_length / max_block_length))
        block_length = total_length / num_blocks

        dowel_dia = FuselageJigFactory.ALIGNMENT_PIN_DIA
        dowel_depth = 1.0

        for i in range(num_blocks):
            block_start = min_station + i * block_length
            block_end = min_station + (i + 1) * block_length

            # Find profiles within this block
            block_profiles = [
                p for p in profiles if block_start <= p.station <= block_end
            ]

            if not block_profiles:
                continue

            # Approximate block with bounding box
            max_width = max(p.width for p in block_profiles)
            max_height = max(p.height for p in block_profiles)

            block = (
                cq.Workplane("XY")
                .box(block_length, max_width, max_height, centered=False)
                .translate((block_start, -max_width / 2, 0))
            )

            # Add alignment dowel holes at joints (except first/last faces)
            if i > 0:
                # Holes on front face
                for dy in [-max_width / 4, max_width / 4]:
                    for dz in [max_height / 4, 3 * max_height / 4]:
                        hole = (
                            cq.Workplane("YZ")
                            .center(dy, dz)
                            .circle(dowel_dia / 2)
                            .extrude(dowel_depth)
                            .translate((block_start, 0, 0))
                        )
                        block = block.cut(hole)

            if i < num_blocks - 1:
                # Holes on rear face
                for dy in [-max_width / 4, max_width / 4]:
                    for dz in [max_height / 4, 3 * max_height / 4]:
                        hole = (
                            cq.Workplane("YZ")
                            .center(dy, dz)
                            .circle(dowel_dia / 2)
                            .extrude(dowel_depth)
                            .translate((block_end - dowel_depth, 0, 0))
                        )
                        block = block.cut(hole)

            # Add block number engraving
            label = (
                cq.Workplane("XY")
                .center(block_start + block_length / 2, 0)
                .rect(2.0, 0.5)
                .extrude(-0.1)
                .translate((0, 0, max_height))
            )
            block = block.cut(label)

            slabs[f"block_{i + 1}"] = block

        return slabs

    @staticmethod
    def export_fuselage_jigs(
        fuselage: "Fuselage",
        output_dir: Path,
        build_method: str = "bow_foam",
    ) -> List[Path]:
        """
        Export complete fuselage jig set.

        Generates:
        - Build strongback (assembly drawing)
        - Bulkhead saddles (STL for CNC/3D print)
        - Foam slab patterns (DXF for laser cutting)

        Args:
            fuselage: Fuselage component
            output_dir: Output directory
            build_method: "bow_foam" or "cnc_milled"

        Returns:
            List of generated file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_files: List[Path] = []

        # Generate saddles for each bulkhead
        for profile in fuselage._profiles:
            if profile.width > 1.0:  # Skip degenerate profiles
                try:
                    saddle = FuselageJigFactory.generate_bulkhead_saddle(profile)
                    saddle_path = output_dir / f"SADDLE_FS{profile.station:.0f}.stl"
                    cq.exporters.export(saddle, str(saddle_path))
                    generated_files.append(saddle_path)
                    logger.info(f"Generated saddle: {saddle_path.name}")
                except Exception as e:
                    logger.warning(
                        f"Could not generate saddle for FS{profile.station}: {e}"
                    )

        # Generate foam slabs
        try:
            slabs = FuselageJigFactory.generate_fuselage_foam_slabs(
                fuselage, build_method=build_method
            )
            for name, slab in slabs.items():
                slab_path = output_dir / f"SLAB_{name}.step"
                cq.exporters.export(slab, str(slab_path))
                generated_files.append(slab_path)
                logger.info(f"Generated slab: {slab_path.name}")

                # Also export DXF for laser cutting
                try:
                    dxf_path = output_dir / f"SLAB_{name}.dxf"
                    cq.exporters.export(slab, str(dxf_path), exportType="DXF")
                    generated_files.append(dxf_path)
                except Exception:
                    pass  # DXF export may fail for 3D geometry
        except Exception as e:
            logger.warning(f"Could not generate foam slabs: {e}")

        # Generate strongback assembly
        try:
            strongback = FuselageJigFactory.generate_build_strongback(fuselage)
            strongback_path = output_dir / "STRONGBACK_assembly.step"
            strongback.save(str(strongback_path))
            generated_files.append(strongback_path)
            logger.info(f"Generated strongback: {strongback_path.name}")
        except Exception as e:
            logger.warning(f"Could not generate strongback: {e}")

        return generated_files


__all__ = ["JigFactory", "FuselageJigFactory"]
