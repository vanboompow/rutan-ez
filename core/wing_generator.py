"""
Wing lofting utilities for foam cores.

Provides a parametric ``WingGenerator`` with sweep, dihedral, washout,
and spar-trough subtraction hooks, plus a ``CanardGenerator``
pre-configured for the Roncz R1145MS safety mandate.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

import cadquery as cq
import numpy as np

from config import config
from .airfoil_factory import Airfoil, AirfoilFactory
from .base import FoamCore


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
    """Generates lofted wing and canard foam cores."""

    def __init__(
        self,
        name: str,
        root_airfoil: Airfoil,
        tip_airfoil: Airfoil,
        span: Optional[float] = None,
        root_chord: Optional[float] = None,
        tip_chord: Optional[float] = None,
        sweep_angle: Optional[float] = None,
        dihedral_angle: Optional[float] = None,
        washout: float = 0.0,
        n_stations: int = 5,
        spar_trough_hook: Optional[Callable[[cq.Workplane, "WingGenerator"], cq.Workplane]] = None,
        description: str = "",
    ):
        super().__init__(name, description)

        geo = config.geometry
        self.span = span if span is not None else geo.wing_span
        self.root_chord = root_chord if root_chord is not None else geo.wing_root_chord
        self.tip_chord = tip_chord if tip_chord is not None else geo.wing_tip_chord
        self.sweep_angle = sweep_angle if sweep_angle is not None else geo.wing_sweep_le
        self.dihedral_angle = dihedral_angle if dihedral_angle is not None else geo.wing_dihedral
        self.washout = washout if washout is not None else geo.wing_washout
        self.n_stations = n_stations
        self._spar_trough_hook = spar_trough_hook

        self.root_airfoil = root_airfoil
        self.tip_airfoil = tip_airfoil

        self._stations: List[WingStation] = []
        self.add_metadata("taper_ratio", geo.wing_taper_ratio)
        self.add_metadata("foam_core_material", config.materials.wing_core_foam.value)
        self.add_metadata("foam_density_lbft3", config.materials.foam_density(config.materials.wing_core_foam))

    @property
    def semi_span(self) -> float:
        """Half-span for the current panel."""
        return self.span / 2

    def _compute_stations(self) -> List[WingStation]:
        stations = []
        for i in range(self.n_stations):
            eta = i / (self.n_stations - 1)
            butt_line = eta * self.semi_span

            chord = self.root_chord + eta * (self.tip_chord - self.root_chord)
            x_offset = butt_line * np.tan(np.radians(self.sweep_angle))
            z_offset = butt_line * np.tan(np.radians(self.dihedral_angle))
            twist = eta * self.washout

            airfoil = self.root_airfoil if eta < 0.5 else self.tip_airfoil
            if abs(twist) > 1e-3:
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
        self._stations = self._compute_stations()
        if len(self._stations) < 2:
            raise ValueError("Need at least 2 stations for lofting")

        wires = []
        for station in self._stations:
            wire = station.airfoil.get_cadquery_wire(station.chord)
            wire_moved = wire.moved(
                cq.Location(cq.Vector(station.x_offset, station.butt_line, station.z_offset))
            )
            wires.append(wire_moved)

        faces = [cq.Face.makeFromWires(w) for w in wires]
        lofted = cq.Solid.makeLoft([cq.Wire.assembleEdges(f.Edges()) for f in faces])
        self._geometry = cq.Workplane("XY").add(lofted)
        return self._geometry

    def get_root_profile(self) -> cq.Wire:
        if not self._stations:
            self._stations = self._compute_stations()
        return self._stations[0].airfoil.get_cadquery_wire(self._stations[0].chord)

    def get_tip_profile(self) -> cq.Wire:
        if not self._stations:
            self._stations = self._compute_stations()
        return self._stations[-1].airfoil.get_cadquery_wire(self._stations[-1].chord)

    def _build_spar_trough(
        self,
        spar_x_start: float,
        spar_width: Optional[float],
        trough_depth: Optional[float],
    ) -> cq.Workplane:
        width = spar_width if spar_width is not None else config.materials.spar_cap_width
        depth = trough_depth if trough_depth is not None else config.materials.spar_trough_depth

        trough_length = self.semi_span + 1.0
        trough = (
            cq.Workplane("XY")
            .center(self.root_chord * spar_x_start, 0)
            .rect(width, trough_length * 2)
            .extrude(depth)
        )
        return trough

    def cut_spar_trough(
        self,
        spar_x_start: float = 0.25,
        spar_width: Optional[float] = None,
        trough_depth: Optional[float] = None,
    ) -> cq.Workplane:
        if self._geometry is None:
            self.generate_geometry()

        trough = self._build_spar_trough(spar_x_start, spar_width, trough_depth)
        self._geometry = self._geometry.cut(trough)

        if self._spar_trough_hook:
            self._geometry = self._spar_trough_hook(self._geometry, self)

        self.add_metadata("spar_trough_depth", trough_depth or config.materials.spar_trough_depth)
        self.add_metadata("spar_trough_width", spar_width or config.materials.spar_cap_width)
        return self._geometry

    def export_dxf(self, output_path: Path) -> Path:
        dxf_file = output_path / f"{self.name}_templates.dxf"

        root_wire = self.get_root_profile()
        cq.exporters.export(
            cq.Workplane("XY").add(root_wire),
            str(output_path / f"{self.name}_root.dxf"),
            exportType="DXF",
        )

        tip_wire = self.get_tip_profile()
        cq.exporters.export(
            cq.Workplane("XY").add(tip_wire),
            str(output_path / f"{self.name}_tip.dxf"),
            exportType="DXF",
        )

        return dxf_file


class CanardGenerator(WingGenerator):
    """Specialized generator for the Roncz R1145MS canard."""

    def __init__(self, name: str = "canard_core", description: str = "Roncz R1145MS canard foam core"):
        factory = AirfoilFactory()
        roncz = factory.get_canard_airfoil()
        geo = config.geometry

        super().__init__(
            name=name,
            root_airfoil=roncz,
            tip_airfoil=roncz,
            span=geo.canard_span,
            root_chord=geo.canard_root_chord,
            tip_chord=geo.canard_tip_chord,
            sweep_angle=geo.canard_sweep_le,
            dihedral_angle=0.0,
            washout=0.0,
            n_stations=5,
            description=description,
        )

        self.add_metadata("airfoil", "roncz_r1145ms")
        self.add_metadata("canard_span_in", geo.canard_span)
        self.add_metadata("canard_semi_span_in", geo.canard_semi_span)
        self.add_metadata("foam_core_material", config.materials.wing_core_foam.value)
