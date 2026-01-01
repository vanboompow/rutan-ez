"""
Open-EZ PDE: Parametric Jigs and Fixtures
========================================

Jigs derived directly from component geometry to enforce incidence,
alignment, and drilling accuracy.
"""

from typing import List, Tuple
import cadquery as cq

from .base import AircraftComponent


class IncidenceBlock(AircraftComponent):
    """
    Fixture to hold a lifting surface at a prescribed incidence angle.

    The block dimensions are derived from the provided contact surface so the
    clamp pocket matches the airfoil section footprint.
    """

    def __init__(
        self,
        name: str,
        mount_surface: cq.Workplane,
        incidence_deg: float,
        seat_depth: float = 0.2,
        clearance: float = 0.125,
        bolt_spacing: float = 1.25,
        bolt_diameter: float = 0.25,
        description: str = "Incidence block derived from geometry",
    ):
        super().__init__(name, description)
        self.mount_surface = mount_surface
        self.incidence_deg = incidence_deg
        self.seat_depth = seat_depth
        self.clearance = clearance
        self.bolt_spacing = bolt_spacing
        self.bolt_diameter = bolt_diameter

    def _derive_blank(self) -> cq.Workplane:
        bbox = self.mount_surface.val().BoundingBox()
        length = bbox.xlen + 2 * self.clearance
        width = bbox.ylen + 2 * self.clearance
        height = bbox.zlen + (self.seat_depth * 2)
        return cq.Workplane("XY").box(length, width, height, centered=(True, True, False))

    def _bolt_pattern(self, base: cq.Workplane, height: float) -> cq.Workplane:
        spacing = self.bolt_spacing / 2
        points = [
            (spacing, spacing),
            (-spacing, spacing),
            (spacing, -spacing),
            (-spacing, -spacing),
        ]
        return base.workplane(offset=height * 0.5).pushPoints(points).hole(self.bolt_diameter)

    def generate_geometry(self) -> cq.Workplane:
        bbox = self.mount_surface.val().BoundingBox()
        blank = self._derive_blank()

        pocket = (
            cq.Workplane("XY")
            .workplane(offset=blank.val().BoundingBox().zlen - self.seat_depth)
            .box(bbox.xlen + self.clearance, bbox.ylen + self.clearance, self.seat_depth + 0.01, centered=(True, True, False))
        )

        block = blank.cut(pocket)
        block = self._bolt_pattern(block, blank.val().BoundingBox().zlen)

        if abs(self.incidence_deg) > 0.0:
            block = block.rotate((0, 0, 0), (0, 1, 0), self.incidence_deg)

        self._geometry = block
        self.add_metadata("incidence_deg", self.incidence_deg)
        self.add_metadata("seat_depth", self.seat_depth)
        self.add_metadata("bolt_pattern", {
            "spacing": self.bolt_spacing,
            "diameter": self.bolt_diameter,
        })
        return self._geometry

    def export_dxf(self, output_path):
        raise NotImplementedError("DXF export not implemented for jigs")


class DrillingGuide(AircraftComponent):
    """
    Drill bushing guide derived from a contact surface and hole pattern.

    Hole positions are defined in the surface's local XY frame so designers can
    pass through CNC-derived coordinates without manual translation.
    """

    def __init__(
        self,
        name: str,
        mount_surface: cq.Workplane,
        hole_positions: List[Tuple[float, float]],
        hole_diameter: float = 0.1875,
        guide_height: float = 0.75,
        pilot_depth: float = 0.5,
        clearance: float = 0.125,
        description: str = "Drilling guide derived from geometry",
    ):
        super().__init__(name, description)
        self.mount_surface = mount_surface
        self.hole_positions = hole_positions
        self.hole_diameter = hole_diameter
        self.guide_height = guide_height
        self.pilot_depth = pilot_depth
        self.clearance = clearance

    def _derive_blank(self) -> cq.Workplane:
        bbox = self.mount_surface.val().BoundingBox()
        length = bbox.xlen + 2 * self.clearance
        width = bbox.ylen + 2 * self.clearance
        return cq.Workplane("XY").box(length, width, self.guide_height, centered=(True, True, False))

    def generate_geometry(self) -> cq.Workplane:
        blank = self._derive_blank()
        guide = blank.workplane(offset=self.guide_height - self.pilot_depth).pushPoints(self.hole_positions).hole(self.hole_diameter)
        self._geometry = guide
        self.add_metadata("hole_count", len(self.hole_positions))
        self.add_metadata("hole_diameter", self.hole_diameter)
        self.add_metadata("pilot_depth", self.pilot_depth)
        return self._geometry

    def export_dxf(self, output_path):
        raise NotImplementedError("DXF export not implemented for jigs")
