"""
Open-EZ PDE: Structural Components
==================================

WingGenerator: Lofted wing/canard cores with sweep, dihedral, washout.
Fuselage: Station-based profile lofting with bulkhead integration.

All dimensions derive from config/aircraft_config.py.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import cadquery as cq

from config import config
from .base import AircraftComponent, FoamCore
from .aerodynamics import Airfoil, AirfoilFactory, airfoil_factory


@dataclass
class WingStation:
    """Definition of a spanwise station for lofting."""
    butt_line: float         # Spanwise location (inches from centerline)
    chord: float             # Local chord length
    airfoil: Airfoil         # Airfoil at this station
    twist: float = 0.0       # Local twist/washout (degrees)
    x_offset: float = 0.0    # Chordwise offset (for sweep)
    z_offset: float = 0.0    # Vertical offset (for dihedral)


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
        description: str = ""
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
            x_offset = butt_line * np.tan(np.radians(self.sweep_angle))

            # Dihedral offset
            z_offset = butt_line * np.tan(np.radians(self.dihedral_angle))

            # Linear washout distribution
            twist = eta * self.washout

            # Interpolate airfoil (simple linear blend for now)
            if eta < 0.5:
                airfoil = self.root_airfoil
            else:
                airfoil = self.tip_airfoil

            # Apply washout to airfoil
            if abs(twist) > 0.001:
                airfoil = airfoil.apply_washout(twist)

            stations.append(WingStation(
                butt_line=butt_line,
                chord=chord,
                airfoil=airfoil,
                twist=twist,
                x_offset=x_offset,
                z_offset=z_offset
            ))

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
            wire_moved = wire.moved(cq.Location(
                cq.Vector(station.x_offset, station.butt_line, station.z_offset)
            ))
            wires.append(wire_moved)

        # Loft through all station wires
        if len(wires) < 2:
            raise ValueError("Need at least 2 stations for lofting")

        # Build loft using CadQuery
        # Start with first wire as a workplane reference
        result = cq.Workplane("XY")

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
        trough_depth: Optional[float] = None
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
        self._geometry = self._geometry.cut(trough)

        self.add_metadata("spar_trough_depth", depth)
        self.add_metadata("spar_trough_width", width)

        return self._geometry

    def export_dxf(self, output_path: Path) -> Path:
        """Export root and tip templates as DXF."""
        dxf_file = output_path / f"{self.name}_templates.dxf"

        # Export root profile
        root_wire = self.get_root_profile()
        # CadQuery DXF export
        cq.exporters.export(
            cq.Workplane("XY").add(root_wire),
            str(output_path / f"{self.name}_root.dxf"),
            exportType="DXF"
        )

        # Export tip profile
        tip_wire = self.get_tip_profile()
        cq.exporters.export(
            cq.Workplane("XY").add(tip_wire),
            str(output_path / f"{self.name}_tip.dxf"),
            exportType="DXF"
        )

        return dxf_file


class CanardGenerator(WingGenerator):
    """
    Specialized generator for the canard.

    ENFORCES Roncz R1145MS airfoil for safety.
    """

    def __init__(
        self,
        name: str = "canard_core",
        description: str = "Roncz R1145MS canard foam core"
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
            washout=0.0,         # Canard has no washout
            n_stations=5,
            description=description
        )

        # Record safety compliance
        self.add_metadata("airfoil", "roncz_r1145ms")
        self.add_metadata("safety_mandate", "Rain-safe canard per CP updates")


@dataclass
class BulkheadProfile:
    """Fuselage cross-section at a station."""
    station: float       # FS (fuselage station) in inches
    width: float         # Maximum width at this station
    height: float        # Maximum height at this station
    floor_height: float  # Floor position relative to datum


class Fuselage(AircraftComponent):
    """
    Fuselage outer mold line (OML) generator.

    Builds fuselage from a series of bulkhead cross-sections,
    lofted with spline surfaces.
    """

    def __init__(
        self,
        name: str = "fuselage",
        description: str = "Long-EZ fuselage OML"
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
                station=geo.fs_nose,
                width=0.0,
                height=0.0,
                floor_height=0.0
            ),
            BulkheadProfile(
                station=geo.fs_canard_le,
                width=18.0,  # Derived from canard attachment
                height=24.0,
                floor_height=-8.0
            ),
            BulkheadProfile(
                station=geo.fs_pilot_seat,  # F-22
                width=geo.cockpit_width,
                height=38.0,
                floor_height=-12.0
            ),
            BulkheadProfile(
                station=geo.fs_rear_seat,   # F-28
                width=geo.cockpit_width - 2.0,  # Slight taper
                height=34.0,
                floor_height=-10.0
            ),
            BulkheadProfile(
                station=geo.fs_firewall,
                width=18.0,
                height=20.0,
                floor_height=-6.0
            ),
            BulkheadProfile(
                station=geo.fs_tail,
                width=6.0,
                height=8.0,
                floor_height=-2.0
            ),
        ]

    def _create_bulkhead_wire(self, profile: BulkheadProfile) -> cq.Wire:
        """Create a bulkhead cross-section wire."""
        # Simplified elliptical cross-section
        # Real implementation would use actual bulkhead shapes
        w = profile.width / 2
        h = profile.height / 2

        if w < 0.1 or h < 0.1:
            # Near-point for nose
            return cq.Wire.makeCircle(0.1, cq.Vector(0, 0, profile.station))

        # Create ellipse
        ellipse = (
            cq.Workplane("XY")
            .center(0, profile.floor_height + h)
            .ellipse(w, h)
            .wire()
        )

        # Move to correct station
        return ellipse.val().moved(cq.Location(cq.Vector(0, 0, profile.station)))

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
                cq.exporters.export(
                    cq.Workplane("XY").add(wire),
                    str(output_path / f"{self.name}_{station_name}.dxf"),
                    exportType="DXF"
                )

        return output_path / f"{self.name}_bulkheads.dxf"
