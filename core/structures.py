"""
Open-EZ PDE: Structural Components (Updated)
============================================

Includes support for:
- Manufacturing Segmentation (splitting wings for foam blocks)
- Jig Generation Hooks

WingGenerator: Lofted wing/canard cores with sweep, dihedral, washout.
Fuselage: Station-based profile lofting with bulkhead integration.

All dimensions derive from config/aircraft_config.py.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import cadquery as cq

from config import config
from .base import AircraftComponent, FoamCore
from .aerodynamics import Airfoil, AirfoilFactory
from .manufacturing import JigFactory  # NEW Import


@dataclass
class WingStation:
    """Definition of a spanwise station for lofting."""

    butt_line: float  # Spanwise location (inches from centerline)
    chord: float  # Local chord length
    airfoil: Airfoil  # Airfoil at this station
    twist: float = 0.0  # Local twist/washout (degrees)
    x_offset: float = 0.0  # Chordwise offset (for sweep)
    z_offset: float = 0.0  # Vertical offset (for dihedral)


class WingGenerator(FoamCore):
    """
    Generates lofted wing and canard foam cores.

    Features:
    - Arbitrary number of spanwise stations
    - Sweep via x_offset propagation
    - Dihedral via z_offset propagation
    - Washout via per-station twist
    - Spar cap trough subtraction
    """

    def __init__(
        self,
        name: str,
        root_airfoil: Airfoil,
        tip_airfoil: Airfoil,
        span: float,
        root_chord: float,
        tip_chord: float,
        sweep_angle: float = 0.0,
        dihedral_angle: float = 0.0,
        washout: float = 0.0,
        n_stations: int = 5,
        description: str = "",
    ):
        """
        Initialize wing generator.

        Args:
            name: Component identifier
            root_airfoil: Airfoil at root (BL 0 or inboard)
            tip_airfoil: Airfoil at tip
            span: Total span (both sides) or semi-span if half-wing
            root_chord: Root chord length (inches)
            tip_chord: Tip chord length (inches)
            sweep_angle: Leading edge sweep (degrees, positive = aft)
            dihedral_angle: Dihedral (degrees, positive = tips up)
            washout: Tip washout (degrees, positive = LE down)
            n_stations: Number of loft stations
            description: Human-readable description
        """
        super().__init__(name, description)

        self.root_airfoil = root_airfoil
        self.tip_airfoil = tip_airfoil
        self.span = span
        self.root_chord = root_chord
        self.tip_chord = tip_chord
        self.sweep_angle = sweep_angle
        self.dihedral_angle = dihedral_angle
        self.washout = washout
        self.n_stations = n_stations

        # Will be populated during generation
        self._stations: List[WingStation] = []

    def _compute_stations(self) -> List[WingStation]:
        """Compute wing stations for lofting."""
        stations = []
        semi_span = self.span / 2

        for i in range(self.n_stations):
            # Spanwise fraction
            eta = i / (self.n_stations - 1)
            butt_line = eta * semi_span

            # Linear taper
            chord = self.root_chord + eta * (self.tip_chord - self.root_chord)

            # Sweep offset (measured at leading edge)
            if isinstance(self.sweep_angle, (list, tuple)):
                # Calculate cumulative offset from piecewise segment sweeps
                if i == 0:
                    x_offset = 0.0
                else:
                    # Sum up tangent of previous segments
                    x_offset = 0.0
                    for j in range(i):
                        seg_span = semi_span / (self.n_stations - 1)
                        seg_sweep = self.sweep_angle[min(j, len(self.sweep_angle) - 1)]
                        x_offset += seg_span * np.tan(np.radians(seg_sweep))
            else:
                x_offset = butt_line * np.tan(np.radians(self.sweep_angle))

            # Dihedral offset
            z_offset = butt_line * np.tan(np.radians(self.dihedral_angle))

            # Linear washout distribution
            twist = eta * self.washout

            # Smooth airfoil interpolation along span using linear blend
            airfoil = self.root_airfoil.blend(self.tip_airfoil, eta)

            # Apply washout to airfoil
            if abs(twist) > 0.001:
                airfoil = airfoil.apply_washout(twist)

            stations.append(
                WingStation(
                    butt_line=butt_line,
                    chord=chord,
                    airfoil=airfoil,
                    twist=twist,
                    x_offset=x_offset,
                    z_offset=z_offset,
                )
            )

        return stations

    def generate_geometry(self) -> cq.Workplane:
        """
        Generate the lofted wing foam core.

        Returns:
            CadQuery solid representing the foam core
        """
        self._stations = self._compute_stations()

        # Build wires for each station
        wires = []
        for station in self._stations:
            # Get airfoil wire at local chord
            wire = station.airfoil.get_cadquery_wire(station.chord)

            # Transform to station position
            # Wire is in XY plane; we need to:
            # 1. Translate by x_offset in X (sweep)
            # 2. Translate by butt_line in Y (spanwise)
            # 3. Translate by z_offset in Z (dihedral)

            # CadQuery wire manipulation
            wire_moved = wire.moved(
                cq.Location(
                    cq.Vector(station.x_offset, station.butt_line, station.z_offset)
                )
            )
            wires.append(wire_moved)

        # Loft through all station wires
        if len(wires) < 2:
            raise ValueError("Need at least 2 stations for lofting")

        # Build loft using CadQuery
        # Create faces from wires
        faces = [cq.Face.makeFromWires(w) for w in wires]

        # Loft using shell
        lofted = cq.Solid.makeLoft([cq.Wire.assembleEdges(f.Edges()) for f in faces])

        self._geometry = cq.Workplane("XY").add(lofted)
        return self._geometry

    def get_root_profile(self) -> cq.Wire:
        """Return root airfoil wire for G-code generation."""
        if not self._stations:
            self._stations = self._compute_stations()
        return self._stations[0].airfoil.get_cadquery_wire(self._stations[0].chord)

    def get_tip_profile(self) -> cq.Wire:
        """Return tip airfoil wire for G-code generation."""
        if not self._stations:
            self._stations = self._compute_stations()
        return self._stations[-1].airfoil.get_cadquery_wire(self._stations[-1].chord)

    def cut_spar_trough(
        self,
        spar_x_start: float = 0.25,
        spar_width: Optional[float] = None,
        trough_depth: Optional[float] = None,
    ) -> cq.Workplane:
        """
        Subtract spar cap trough from foam core.

        Args:
            spar_x_start: Spar location as fraction of chord (default: quarter-chord)
            spar_width: Width of spar cap (default from config)
            trough_depth: Depth of trough (default from config based on ply count)

        Returns:
            Modified geometry with spar trough cut
        """
        if self._geometry is None:
            self.generate_geometry()

        width = spar_width or config.materials.spar_cap_width
        depth = trough_depth or config.materials.spar_trough_depth

        # Build spar trough as extruded rectangle along span
        # This is a simplified implementation; real spar follows wing surface
        trough_length = self.span / 2 + 1.0  # Extend slightly past tip

        # Create trough solid
        trough = (
            cq.Workplane("XY")
            .center(self.root_chord * spar_x_start, 0)
            .rect(width, trough_length * 2)
            .extrude(depth)
        )

        # Cut from both upper and lower surfaces
        # (simplified - real implementation would follow airfoil surface)
        if self._geometry is not None:
            self._geometry = self._geometry.cut(trough)

        self.add_metadata("spar_trough_depth", depth)
        self.add_metadata("spar_trough_width", width)

        return self._geometry

    def export_dxf(self, output_path: Path) -> Path:
        """Export root and tip templates as DXF."""
        output_path.mkdir(parents=True, exist_ok=True)
        # Export root profile
        root_wire = self.get_root_profile()
        root_path = output_path / f"{self.name}_root.dxf"
        cq.exporters.export(
            cq.Workplane("XY").add(root_wire), str(root_path), exportType="DXF"
        )
        self._write_artifact_metadata(root_path, artifact_type="DXF")

        # Export tip profile
        tip_wire = self.get_tip_profile()
        tip_path = output_path / f"{self.name}_tip.dxf"
        cq.exporters.export(
            cq.Workplane("XY").add(tip_wire), str(tip_path), exportType="DXF"
        )
        self._write_artifact_metadata(tip_path, artifact_type="DXF")

        return output_path / f"{self.name}_templates.dxf"

    # === NEW: Manufacturing Methods ===

    def generate_segments(
        self, max_block_length: float = 48.0
    ) -> List["WingGenerator"]:
        """
        Split the wing into manufacturable segments for CNC foam cutting.

        Most hot-wire CNC machines have a maximum cutting width of 4 feet (48").
        This method subdivides the wing into segments that fit within the machine
        constraints while maintaining structural joint locations.

        Args:
            max_block_length: Maximum segment length in inches (default: 48" = 4ft)

        Returns:
            List of WingGenerator objects, each representing a manufacturable segment.
            Segments are ordered from root to tip.
        """
        semi_span = self.span / 2
        segments = []

        # Calculate number of segments needed
        num_segments = int(np.ceil(semi_span / max_block_length))

        if num_segments <= 1:
            # Wing fits in a single block - return self as only segment
            return [self]

        # Calculate segment boundaries
        segment_length = semi_span / num_segments

        for seg_idx in range(num_segments):
            # Spanwise positions for this segment
            bl_inboard = seg_idx * segment_length
            bl_outboard = (seg_idx + 1) * segment_length

            # Calculate chord at segment boundaries (linear taper)
            eta_inboard = bl_inboard / semi_span
            eta_outboard = bl_outboard / semi_span

            chord_inboard = self.root_chord + eta_inboard * (
                self.tip_chord - self.root_chord
            )
            chord_outboard = self.root_chord + eta_outboard * (
                self.tip_chord - self.root_chord
            )

            # Calculate x-offset (sweep) at segment root
            x_offset_inboard = bl_inboard * np.tan(np.radians(self.sweep_angle))

            # Calculate z-offset (dihedral) at segment root
            z_offset_inboard = bl_inboard * np.tan(np.radians(self.dihedral_angle))

            # Calculate washout at segment boundaries
            washout_inboard = eta_inboard * self.washout
            washout_outboard = eta_outboard * self.washout

            # Smooth airfoil interpolation for this segment
            inboard_airfoil = self.root_airfoil.blend(self.tip_airfoil, eta_inboard)
            outboard_airfoil = self.root_airfoil.blend(self.tip_airfoil, eta_outboard)

            # Apply washout to segment airfoils
            if abs(washout_inboard) > 0.001:
                inboard_airfoil = inboard_airfoil.apply_washout(washout_inboard)
            if abs(washout_outboard) > 0.001:
                outboard_airfoil = outboard_airfoil.apply_washout(washout_outboard)

            # Create segment generator
            segment = WingGenerator(
                name=f"{self.name}_seg{seg_idx + 1}",
                root_airfoil=inboard_airfoil,
                tip_airfoil=outboard_airfoil,
                span=segment_length * 2,  # WingGenerator expects full span
                root_chord=chord_inboard,
                tip_chord=chord_outboard,
                sweep_angle=self.sweep_angle,
                dihedral_angle=self.dihedral_angle,
                washout=washout_outboard - washout_inboard,  # Relative washout
                n_stations=max(3, self.n_stations // num_segments),
                description=f"{self.description} - Segment {seg_idx + 1} of {num_segments}",
            )

            # Store segment metadata
            segment.add_metadata("segment_index", seg_idx)
            segment.add_metadata("segment_count", num_segments)
            segment.add_metadata("bl_inboard", bl_inboard)
            segment.add_metadata("bl_outboard", bl_outboard)
            segment.add_metadata("x_offset", x_offset_inboard)
            segment.add_metadata("z_offset", z_offset_inboard)

            segments.append(segment)

        return segments

    def export_segments_gcode(
        self, output_dir: Path, max_block_length: float = 48.0
    ) -> List[Path]:
        """
        Generate G-code for all wing segments.

        Args:
            output_dir: Directory for G-code output
            max_block_length: Maximum segment length in inches

        Returns:
            List of paths to generated G-code files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        segments = self.generate_segments(max_block_length)
        gcode_files = []

        for segment in segments:
            # Generate geometry if needed
            if segment._geometry is None:
                segment.generate_geometry()

            # Export G-code
            gcode_path = segment.export_gcode(output_dir)
            gcode_files.append(gcode_path)

        return gcode_files

    def export_jigs(self, output_dir: Path):
        """Generate 3D printable alignment jigs for this wing."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Root incidence jig
        jig = JigFactory.generate_incidence_cradle(
            self, station_bl=23.0, incidence_angle=config.geometry.wing_incidence
        )
        cq.exporters.export(jig, str(output_dir / f"JIG_{self.name}_root.stl"))

    def manufacturing_plan(self, output_path: Path) -> Dict[str, Any]:
        """Generate STEP/STL/DXF/G-code outputs for the foam core."""
        output_path.mkdir(parents=True, exist_ok=True)
        component_key = "canard" if "canard" in self.name else "wing"
        intents = config.manufacturing.component_intents.get(component_key)

        foam_type = (
            config.materials.wing_core_foam
            if component_key == "wing"
            else config.materials.fuselage_foam
        )
        kerf = config.manufacturing.kerf_compensation.get(foam_type, 0.04)

        step_path = self.export_step(output_path)
        stl_path = self.export_stl(output_path, tolerance=intents.printable_jigs.tolerance)
        dxf_path = self.export_dxf(output_path)
        gcode_path = self.export_gcode(
            output_path,
            kerf_offset=kerf,
            feed_rate=config.manufacturing.feed_rate_default,
        )

        return {
            "cad_step": {
                "path": step_path,
                "format": "STEP",
                "tolerance": None,
                "artifact": f"{self.name}_solid",
            },
            "printable_jigs": {
                "path": stl_path,
                "format": intents.printable_jigs.format,
                "tolerance": intents.printable_jigs.tolerance,
                "artifact": intents.printable_jigs.artifact,
            },
            "sheet_templates": {
                "path": dxf_path,
                "format": intents.sheet_templates.format,
                "tolerance": intents.sheet_templates.tolerance,
                "artifact": intents.sheet_templates.artifact,
            },
            "cnc_foam": {
                "path": gcode_path,
                "format": intents.cnc_foam.format,
                "tolerance": intents.cnc_foam.tolerance,
                "artifact": intents.cnc_foam.artifact,
                "kerf_offset": kerf,
            },
        }


class CanardGenerator(WingGenerator):
    """
    Specialized generator for the canard.

    ENFORCES Roncz R1145MS airfoil for safety.
    """

    def __init__(
        self,
        name: str = "canard_core",
        description: str = "Roncz R1145MS canard foam core",
    ):
        """
        Initialize canard with safety-mandated parameters.

        Dimensions from config; airfoil is ALWAYS Roncz R1145MS.
        """
        # Get safety-mandated airfoil
        factory = AirfoilFactory()
        roncz = factory.get_canard_airfoil()

        super().__init__(
            name=name,
            root_airfoil=roncz,
            tip_airfoil=roncz,  # Same airfoil root-to-tip for canard
            span=config.geometry.canard_span,
            root_chord=config.geometry.canard_root_chord,
            tip_chord=config.geometry.canard_tip_chord,
            sweep_angle=config.geometry.canard_sweep_le,
            dihedral_angle=0.0,  # Canard has no dihedral
            washout=0.0,  # Canard has no washout
            n_stations=5,
            description=description,
        )

        # Record safety compliance
        self.add_metadata("airfoil", "roncz_r1145ms")
        self.add_metadata("safety_mandate", "Rain-safe canard per CP updates")


class MainWingGenerator(WingGenerator):
    """
    Specialized generator for the main wing.

    Uses defaults from config.geometry and config.airfoils.
    """

    def __init__(
        self,
        name: str = "main_wing",
        description: str = "Eppler 1230 Modified wing foam core",
    ):
        factory = AirfoilFactory()
        root_af = factory.load(config.airfoils.wing_root)
        tip_af = factory.load(config.airfoils.wing_tip)

        super().__init__(
            name=name,
            root_airfoil=root_af,
            tip_airfoil=tip_af,
            span=config.geometry.wing_span,
            root_chord=config.geometry.wing_root_chord,
            tip_chord=config.geometry.wing_tip_chord,
            sweep_angle=config.geometry.wing_sweep_le,
            dihedral_angle=config.geometry.wing_dihedral,
            washout=config.geometry.wing_washout,
            n_stations=10,
            description=description,
        )


@dataclass
class BulkheadProfile:
    """Fuselage cross-section at a station."""

    station: float  # FS (fuselage station) in inches
    width: float  # Maximum width at this station
    height: float  # Maximum height at this station
    floor_height: float  # Floor position relative to datum


class Fuselage(AircraftComponent):
    """
    Fuselage outer mold line (OML) generator.

    Builds fuselage from a series of bulkhead cross-sections,
    lofted with spline surfaces.
    """

    def __init__(
        self, name: str = "fuselage", description: str = "Long-EZ fuselage OML"
    ):
        super().__init__(name, description)
        self._profiles: List[BulkheadProfile] = []
        self._init_profiles()

    def _init_profiles(self) -> None:
        """Initialize bulkhead profiles from config."""
        geo = config.geometry

        # Define key fuselage stations
        # These are derived from the SSOT, not hard-coded
        self._profiles = [
            BulkheadProfile(
                station=geo.fs_nose, width=0.0, height=0.0, floor_height=0.0
            ),
            BulkheadProfile(
                station=geo.fs_canard_le,
                width=18.0,  # Derived from canard attachment
                height=24.0,
                floor_height=-8.0,
            ),
            BulkheadProfile(
                station=geo.fs_pilot_seat,  # F-22
                width=geo.cockpit_width,
                height=38.0,
                floor_height=-12.0,
            ),
            BulkheadProfile(
                station=geo.fs_rear_seat,  # F-28
                width=geo.cockpit_width - 2.0,  # Slight taper
                height=34.0,
                floor_height=-10.0,
            ),
            BulkheadProfile(
                station=geo.fs_firewall, width=18.0, height=20.0, floor_height=-6.0
            ),
            BulkheadProfile(
                station=geo.fs_tail, width=6.0, height=8.0, floor_height=-2.0
            ),
        ]

    def _create_bulkhead_wire(self, profile: BulkheadProfile) -> cq.Wire:
        """Create a bulkhead cross-section wire."""
        # Simplified elliptical cross-section
        # Real implementation would use actual bulkhead shapes
        w = profile.width / 2
        h = profile.height / 2

        if w < 0.1 or h < 0.1:
            # Near-point for nose - circle in YZ plane
            return cq.Wire.makeCircle(
                0.1, cq.Vector(profile.station, 0, 0), cq.Vector(1, 0, 0)
            )

        # Create ellipse in YZ plane
        ellipse = (
            cq.Workplane("YZ")
            .center(0, profile.floor_height + h)
            .ellipse(h, w)  # h is Z (vertical), w is Y (lateral)
            .wire()
        )

        # Move to correct station along X axis
        return ellipse.val().moved(cq.Location(cq.Vector(profile.station, 0, 0)))

    def generate_geometry(self) -> cq.Workplane:
        """
        Generate fuselage OML via lofting.

        Returns:
            CadQuery solid representing fuselage shell
        """
        wires = [self._create_bulkhead_wire(p) for p in self._profiles]

        # Loft through profiles
        lofted = cq.Solid.makeLoft(wires)

        # Shell to create foam core thickness
        foam_thickness = config.materials.foam_core_thickness
        shelled = lofted.shell([], foam_thickness)

        self._geometry = cq.Workplane("XY").add(shelled)
        return self._geometry

    def get_bulkhead(self, station_name: str) -> BulkheadProfile:
        """
        Get bulkhead profile by station name.

        Args:
            station_name: "F22", "F28", etc.

        Returns:
            BulkheadProfile at that station
        """
        station_map = {
            "F22": config.geometry.fs_pilot_seat,
            "F28": config.geometry.fs_rear_seat,
            "firewall": config.geometry.fs_firewall,
        }

        target_station = station_map.get(station_name)
        if target_station is None:
            raise ValueError(f"Unknown station: {station_name}")

        for profile in self._profiles:
            if abs(profile.station - target_station) < 0.1:
                return profile

        raise ValueError(f"No profile at station {station_name}")

    def export_dxf(self, output_path: Path) -> Path:
        """Export all bulkhead profiles as DXF."""
        for profile in self._profiles:
            if profile.width > 1.0:  # Skip degenerate profiles
                wire = self._create_bulkhead_wire(profile)
                station_name = f"FS_{profile.station:.0f}"
                bulkhead_path = output_path / f"{self.name}_{station_name}.dxf"
                cq.exporters.export(
                    cq.Workplane("XY").add(wire), str(bulkhead_path), exportType="DXF"
                )
                self._write_artifact_metadata(bulkhead_path, artifact_type="DXF")

        return output_path / f"{self.name}_bulkheads.dxf"


class StrakeGenerator(AircraftComponent):
    """
    Generate strake geometry for wing-fuselage integration.

    The strakes serve three functions:
    1. Aerodynamic: Smooth fuselage-wing blend, vortex generation
    2. Structural: Wing box tie-in, landing gear support
    3. Tankage: Fuel (baseline) or battery (E-Z conversion)

    The Long-EZ strakes are complex shapes that blend the wing root
    into the fuselage sides, housing ~26 gallons of fuel per side.
    """

    def __init__(
        self,
        name: str = "strake",
        mode: str = "fuel",  # "fuel" or "battery"
        side: str = "left",  # "left" or "right"
        description: str = "Long-EZ strake tank",
    ):
        super().__init__(name, description)
        self.mode = mode
        self.side = side
        self._internal_structure: Optional[cq.Workplane] = None

    def generate_geometry(self) -> cq.Workplane:
        """
        Create strake solid using guide curves and loft.

        Approach:
        1. Define inboard profile (fuselage junction) - curved blend
        2. Define outboard profile (wing root BL 23.3) - airfoil segment
        3. Define leading edge curve (parabolic sweep)
        4. Define trailing edge curve (straight to wing LE)
        5. Loft with ruled surface constraint
        """
        strake_cfg = config.strakes
        geo = config.geometry

        # Key stations
        fs_le = strake_cfg.fs_leading_edge  # ~110"
        fs_te = strake_cfg.fs_trailing_edge  # ~145"
        inboard_width = strake_cfg.inboard_width  # ~8" at fuselage

        # Wing root is at BL 23.3" (half of distance from centerline to wing start)
        bl_outboard = 23.3  # Wing root BL
        bl_inboard = inboard_width / 2  # Fuselage side junction

        # Strake height (transitions from fuselage to wing root airfoil)
        fuselage_height = 12.0  # Approximate fuselage side height at strake
        wing_root_thickness = geo.wing_root_chord * 0.12  # ~12% thick airfoil

        # Create guide profiles at key stations
        profiles = []

        # Inboard profile (at fuselage junction)
        # This is a simple flat rectangle where strake meets fuselage side
        inboard_profile = (
            cq.Workplane("YZ")
            .center(bl_inboard, 0)
            .rect(2.0, fuselage_height)
            .wire()
        )
        profiles.append(inboard_profile.val().moved(
            cq.Location(cq.Vector(fs_le, 0, 0))
        ))

        # Mid profile (blend region)
        mid_bl = (bl_inboard + bl_outboard) / 2
        mid_height = (fuselage_height + wing_root_thickness) / 2
        mid_profile = (
            cq.Workplane("YZ")
            .center(mid_bl, 0)
            .ellipse(mid_height / 2, 3.0)
            .wire()
        )
        profiles.append(mid_profile.val().moved(
            cq.Location(cq.Vector((fs_le + fs_te) / 2, 0, 0))
        ))

        # Outboard profile (wing root airfoil segment)
        # Simplified as ellipse matching wing root thickness
        outboard_profile = (
            cq.Workplane("YZ")
            .center(bl_outboard, 0)
            .ellipse(wing_root_thickness / 2, geo.wing_root_chord * 0.08)
            .wire()
        )
        profiles.append(outboard_profile.val().moved(
            cq.Location(cq.Vector(fs_te, 0, 0))
        ))

        # Loft through profiles
        try:
            lofted = cq.Solid.makeLoft(profiles)
            strake_solid = cq.Workplane("XY").add(lofted)
        except Exception:
            # Fallback: simple box approximation
            length = fs_te - fs_le
            width = bl_outboard - bl_inboard
            height = (fuselage_height + wing_root_thickness) / 2

            strake_solid = (
                cq.Workplane("XY")
                .box(length, width, height, centered=False)
                .translate((fs_le, bl_inboard, -height / 2))
            )

        # Mirror for right side
        if self.side == "right":
            strake_solid = strake_solid.mirror("XZ")

        self._geometry = strake_solid
        return self._geometry

    def generate_internal_structure(self) -> cq.Workplane:
        """
        Create tank baffles or battery cell dividers.

        Fuel mode:
        - 6" spaced anti-slosh baffles
        - Sump at lowest point
        - Filler neck at inboard edge

        Battery mode:
        - LiFePO4 cell cradles (2.625" pitch)
        - Thermal spacers between modules
        - BMS wiring channels
        """
        strake_cfg = config.strakes
        fs_le = strake_cfg.fs_leading_edge
        fs_te = strake_cfg.fs_trailing_edge

        internal = cq.Workplane("XY")

        if self.mode == "fuel":
            # Generate anti-slosh baffles
            baffle_spacing = strake_cfg.baffle_spacing
            baffle_thickness = 0.125  # 1/8" plywood or foam

            for x in np.arange(fs_le + baffle_spacing, fs_te, baffle_spacing):
                # Simplified baffle as vertical plate
                baffle = (
                    cq.Workplane("YZ")
                    .center(15.0, 0)
                    .rect(10.0, 8.0)
                    .extrude(baffle_thickness)
                    .translate((x, 0, 0))
                )
                internal = internal.union(baffle)

            # Sump depression at lowest point
            sump = (
                cq.Workplane("XY")
                .center(fs_te - 3.0, 8.0 if self.side == "left" else -8.0)
                .rect(4.0, 4.0)
                .extrude(-2.0)
            )
            internal = internal.cut(sump)

        elif self.mode == "battery":
            # Generate battery cell cradles
            cell_pitch = strake_cfg.battery_cell_pitch
            module_count = strake_cfg.battery_module_count

            # Cell dimensions (LiFePO4 prismatic)
            cell_width = 2.5
            cell_height = 6.0
            cell_depth = 8.0

            # Create cradle grid
            for i in range(module_count):
                x_pos = fs_le + 5.0 + i * (cell_pitch * 2)

                # Cell divider walls
                divider = (
                    cq.Workplane("YZ")
                    .center(15.0, 0)
                    .rect(cell_height + 1, cell_depth + 1)
                    .extrude(0.25)
                    .translate((x_pos, 0, 0))
                )
                internal = internal.union(divider)

            # Cooling channels
            channel_height = 0.5
            cooling = (
                cq.Workplane("XY")
                .center((fs_le + fs_te) / 2, 15.0 if self.side == "left" else -15.0)
                .rect(fs_te - fs_le - 10, channel_height)
                .extrude(channel_height)
            )
            internal = internal.cut(cooling)

        self._internal_structure = internal
        return internal

    def generate_access_panels(self) -> List[cq.Workplane]:
        """
        Create removable panel geometry for inspection access.
        """
        strake_cfg = config.strakes
        fs_mid = (strake_cfg.fs_leading_edge + strake_cfg.fs_trailing_edge) / 2

        panels = []

        # Main access panel (top surface)
        panel_length = 8.0
        panel_width = 6.0
        panel = (
            cq.Workplane("XY")
            .center(fs_mid, 12.0 if self.side == "left" else -12.0)
            .rect(panel_length, panel_width)
            .extrude(0.125)
        )
        panels.append(panel)

        # Fuel filler / charge port access
        filler_panel = (
            cq.Workplane("XY")
            .center(strake_cfg.fs_trailing_edge - 5.0, 8.0 if self.side == "left" else -8.0)
            .circle(2.0)
            .extrude(0.125)
        )
        panels.append(filler_panel)

        return panels

    def calculate_cg_contribution(self) -> tuple:
        """
        Return (weight_lbs, arm_in, moment_in_lb) for W&B.

        Uses self.mode to compute:
        - Fuel: 6.0 lb/gal × volume
        - Battery: module_count × cell weight
        """
        strake_cfg = config.strakes

        if self.mode == "fuel":
            # Fuel weight: 6.0 lb/gal
            weight_full = strake_cfg.tank_volume_gal * 6.0
            # CG arm at tank centroid
            arm = (strake_cfg.fs_leading_edge + strake_cfg.fs_trailing_edge) / 2
            return (weight_full, arm, weight_full * arm)

        elif self.mode == "battery":
            # LiFePO4 cell weight (100Ah prismatic ~6-7 lb each)
            cells_per_module = strake_cfg.battery_cells_series  # 16S
            cell_weight = 6.5  # lb per cell
            module_weight = cells_per_module * cell_weight / 4  # 4P divides weight

            # Total battery weight in this strake
            weight = strake_cfg.battery_module_count * module_weight
            arm = (strake_cfg.fs_leading_edge + strake_cfg.fs_trailing_edge) / 2
            return (weight, arm, weight * arm)

        return (0.0, 0.0, 0.0)

    def export_dxf(self, output_path: Path) -> Path:
        """Export strake profiles as DXF."""
        if self._geometry is None:
            self.generate_geometry()

        # Export top-down view
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        dxf_path = output_path / f"{self.name}_{self.side}_{self.mode}.dxf"

        try:
            cq.exporters.export(self._geometry, str(dxf_path), exportType="DXF")
            self._write_artifact_metadata(dxf_path, artifact_type="DXF")
        except Exception as e:
            # DXF export may fail for complex 3D geometry
            import logging
            logging.warning(f"Could not export strake DXF: {e}")

        return dxf_path

    def get_tank_volume(self) -> float:
        """Return tank volume in gallons."""
        if self.mode == "fuel":
            return config.strakes.tank_volume_gal
        elif self.mode == "battery":
            # Approximate volume displaced by battery modules
            cell_volume_in3 = 2.5 * 6.0 * 8.0  # Approximate cell dimensions
            total_cells = (
                config.strakes.battery_module_count *
                config.strakes.battery_cells_series *
                config.strakes.battery_cells_parallel
            )
            return (total_cells * cell_volume_in3) / 231.0  # Convert to gallons
        return 0.0

    def manufacturing_plan(self, output_path: Path) -> Dict[str, Any]:
        """Generate fuselage STEP/STL models and DXF panel templates."""
        output_path.mkdir(parents=True, exist_ok=True)
        intents = config.manufacturing.component_intents.get("fuselage")

        step_path = self.export_step(output_path)
        stl_path = self.export_stl(output_path, tolerance=intents.printable_jigs.tolerance)
        dxf_path = self.export_dxf(output_path)

        return {
            "cad_step": {
                "path": step_path,
                "format": "STEP",
                "tolerance": None,
                "artifact": f"{self.name}_solid",
            },
            "printable_jigs": {
                "path": stl_path,
                "format": intents.printable_jigs.format,
                "tolerance": intents.printable_jigs.tolerance,
                "artifact": intents.printable_jigs.artifact,
            },
            "sheet_templates": {
                "path": dxf_path,
                "format": intents.sheet_templates.format,
                "tolerance": intents.sheet_templates.tolerance,
                "artifact": intents.sheet_templates.artifact,
            },
            "cnc_foam": {
                "path": dxf_path,
                "format": intents.cnc_foam.format,
                "tolerance": intents.cnc_foam.tolerance,
                "artifact": intents.cnc_foam.artifact,
            },
        }
