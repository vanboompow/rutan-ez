"""
STL jig generation for wing incidence cradles, drill guides, and vortilon templates.

Outputs are keyed to spanwise stations so builders can maintain incidence,
leading-edge drilling, and vortex generator alignment when cutting foam cores.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import cadquery as cq

from config import config
from core.aerodynamics import airfoil_factory
from core.structures import WingGenerator


@dataclass
class JigResult:
    """Record of a generated jig artifact."""

    station_label: str
    jig_type: str
    path: Path


class JigGenerator:
    """Generate STL helper tooling for foam core alignment and drilling."""

    def __init__(self, n_stations: int = 3) -> None:
        self.n_stations = n_stations
        self._wing = WingGenerator(
            name="wing_jig_reference",
            root_airfoil=airfoil_factory.get_wing_airfoil(apply_reflex=True),
            tip_airfoil=airfoil_factory.get_wing_airfoil(apply_reflex=True),
            span=config.geometry.wing_span,
            root_chord=config.geometry.wing_root_chord,
            tip_chord=config.geometry.wing_tip_chord,
            sweep_angle=config.geometry.wing_sweep_le,
            dihedral_angle=config.geometry.wing_dihedral,
            washout=config.geometry.wing_washout,
            n_stations=max(3, n_stations + 2),
            description="Wing jig reference geometry",
        )
        self._stations = self._wing._compute_stations()

    def generate_jigs(self, output_dir: Path) -> Dict[str, List[JigResult]]:
        """Build all jigs for the configured wing stations."""
        output_dir.mkdir(parents=True, exist_ok=True)

        results: Dict[str, List[JigResult]] = {
            "incidence_cradles": [],
            "drill_guides": [],
            "vortilon_templates": [],
        }

        selected = self._stations[1 : self.n_stations + 1]
        for station in selected:
            label = f"bl{int(round(station.butt_line))}" if station.butt_line else "root"

            cradle = self._build_incidence_cradle(station)
            cradle_path = output_dir / f"incidence_cradle_{label}.stl"
            cq.exporters.export(cradle, str(cradle_path), exportType="STL")
            results["incidence_cradles"].append(JigResult(label, "incidence_cradle", cradle_path))

            guide = self._build_drill_guide(station)
            guide_path = output_dir / f"drill_guide_{label}.stl"
            cq.exporters.export(guide, str(guide_path), exportType="STL")
            results["drill_guides"].append(JigResult(label, "drill_guide", guide_path))

            vortilon = self._build_vortilon_template(station)
            vortilon_path = output_dir / f"vortilon_template_{label}.stl"
            cq.exporters.export(vortilon, str(vortilon_path), exportType="STL")
            results["vortilon_templates"].append(
                JigResult(label, "vortilon_template", vortilon_path)
            )

        return results

    def _build_incidence_cradle(self, station) -> cq.Workplane:
        """Create a cradle that matches the local airfoil incidence."""
        chord = station.chord
        width = 4.0
        thickness = 1.0

        base = cq.Workplane("XY").box(chord + 1.0, width, thickness, centered=(True, True, False))

        pocket_wire = station.airfoil.get_cadquery_wire(chord)
        pocket = cq.Workplane("XY").add(pocket_wire).extrude(thickness * 0.6)

        cradle = base.cut(pocket)
        if abs(station.twist) > 1e-3:
            cradle = cradle.rotate((0, 0, 0), (1, 0, 0), station.twist)

        alignment_slot = (
            cq.Workplane("XY")
            .rect(chord * 0.1, width * 0.8)
            .extrude(thickness)
            .translate((chord * 0.4, 0, thickness * 0.2))
        )
        cradle = cradle.cut(alignment_slot)
        return cradle

    def _build_drill_guide(self, station) -> cq.Workplane:
        """Create a drill guide block for hardpoints or pitot plumbing."""
        chord = station.chord
        guide = cq.Workplane("XY").box(chord * 0.4, 2.0, 0.75, centered=(True, True, False))

        hole_offset = chord * 0.1
        for x in (-hole_offset, hole_offset):
            guide = guide.faces(">Z").workplane().pushPoints([(x, 0)]).hole(0.25)

        return guide.translate((chord * 0.05, 0, 0))

    def _build_vortilon_template(self, station) -> cq.Workplane:
        """Laser-cut style template for vortilon shaping at the station."""
        chord = station.chord
        profile = station.airfoil.get_cadquery_wire(chord)

        # Trim to the forward 35% of the chord for vortilon placement
        bbox = profile.BoundingBox()
        cutoff = bbox.xmin + (bbox.xlen * 0.35)

        trim_plane = cq.Plane(origin=(cutoff, 0, 0), normal=(1, 0, 0))
        section = (
            cq.Workplane("XY")
            .add(profile)
            .split(keepTop=True, plane=trim_plane)
            .extrude(0.25)
        )

        backing = cq.Workplane("XY").box(chord * 0.4, 1.0, 0.15, centered=(False, True, False))
        return backing.union(section.translate((0, 0, 0.05)))
