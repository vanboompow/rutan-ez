"""
Structural components built from the SSOT configuration.

This module keeps fuselage/bulkhead generation here and delegates
lifting-surface geometry to ``wing_generator``.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List

import cadquery as cq

from config import config
from .base import AircraftComponent
from .wing_generator import CanardGenerator, WingGenerator

__all__ = [
    "BulkheadProfile",
    "Fuselage",
    "WingGenerator",
    "CanardGenerator",
]


@dataclass
class BulkheadProfile:
    """Fuselage cross-section at a station."""

    station: float       # FS (fuselage station) in inches
    width: float         # Maximum width at this station
    height: float        # Maximum height at this station
    floor_height: float  # Floor position relative to datum


class Fuselage(AircraftComponent):
    """Fuselage outer mold line (OML) generator."""

    def __init__(self, name: str = "fuselage", description: str = "Long-EZ fuselage OML"):
        super().__init__(name, description)
        self._profiles: List[BulkheadProfile] = []
        self._init_profiles()

    def _init_profiles(self) -> None:
        """Initialize bulkhead profiles from config."""
        geo = config.geometry

        self._profiles = [
            BulkheadProfile(
                station=geo.fs_nose,
                width=0.0,
                height=0.0,
                floor_height=0.0,
            ),
            BulkheadProfile(
                station=geo.fs_canard_le,
                width=18.0,
                height=24.0,
                floor_height=-8.0,
            ),
            BulkheadProfile(
                station=geo.fs_pilot_seat,
                width=geo.cockpit_width,
                height=38.0,
                floor_height=-12.0,
            ),
            BulkheadProfile(
                station=geo.fs_rear_seat,
                width=geo.cockpit_width - 2.0,
                height=34.0,
                floor_height=-10.0,
            ),
            BulkheadProfile(
                station=geo.fs_firewall,
                width=18.0,
                height=20.0,
                floor_height=-6.0,
            ),
            BulkheadProfile(
                station=geo.fs_tail,
                width=6.0,
                height=8.0,
                floor_height=-2.0,
            ),
        ]

    def _create_bulkhead_wire(self, profile: BulkheadProfile) -> cq.Wire:
        """Create a bulkhead cross-section wire."""
        w = profile.width / 2
        h = profile.height / 2

        if w < 0.1 or h < 0.1:
            return cq.Wire.makeCircle(0.1, cq.Vector(0, 0, profile.station))

        ellipse = (
            cq.Workplane("XY")
            .center(0, profile.floor_height + h)
            .ellipse(w, h)
            .wire()
        )

        return ellipse.val().moved(cq.Location(cq.Vector(0, 0, profile.station)))

    def generate_geometry(self) -> cq.Workplane:
        wires = [self._create_bulkhead_wire(p) for p in self._profiles]

        lofted = cq.Solid.makeLoft(wires)
        foam_thickness = config.materials.foam_core_thickness
        shelled = lofted.shell([], foam_thickness)

        self._geometry = cq.Workplane("XY").add(shelled)
        return self._geometry

    def get_bulkhead(self, station_name: str) -> BulkheadProfile:
        """Get bulkhead profile by station name."""
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
            if profile.width > 1.0:
                wire = self._create_bulkhead_wire(profile)
                station_name = f"FS_{profile.station:.0f}"
                cq.exporters.export(
                    cq.Workplane("XY").add(wire),
                    str(output_path / f"{self.name}_{station_name}.dxf"),
                    exportType="DXF",
                )

        return output_path / f"{self.name}_bulkheads.dxf"
