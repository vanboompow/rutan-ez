"""
Open-EZ PDE: Aircraft Assembly Kernel
=====================================

Integrated assembly of all airframe components.
Handles positioning, intersection checks, and full-aircraft exports.
"""

from pathlib import Path
from typing import Dict, List, Optional
import cadquery as cq

from .base import AircraftComponent
from config import config

class AircraftAssembly(AircraftComponent):
    """
    Master assembly of the entire aircraft.
    
    Coordinates:
    - Main Wing: Positioned at config.geometry.fs_wing_le
    - Canard: Positioned at config.geometry.fs_canard_le
    - Fuselage: Centered on BL 0
    - Winglets: Attached to wing tips
    """

    def __init__(self, name: str = "open_ez_airframe"):
        from .structures import MainWingGenerator, CanardGenerator, Fuselage
        super().__init__(name, "Complete airframe assembly")
        self.wing = MainWingGenerator()
        self.canard = CanardGenerator()
        self.fuselage = Fuselage()
        
        # Internal assembly store
        self._assembly = cq.Assembly(name=name)

    def generate_geometry(self) -> cq.Workplane:
        """Combine all components into a single B-Rep solid."""
        # Generate individual geometries
        wing_geo = self.wing.generate_geometry()
        canard_geo = self.canard.generate_geometry()
        fuse_geo = self.fuselage.generate_geometry()
        
        # Position them relative to FS 0
        # For the wing, we apply washout and dihedral in the generator,
        # here we just place it at its leading edge station.
        wing_pos = wing_geo.translate((config.geometry.fs_wing_le, 0, 0))
        
        # Canard is at its station
        canard_pos = canard_geo.translate((config.geometry.fs_canard_le, 0, 0))
        
        # Fuselage is nose-at-FS-nose
        fuse_pos = fuse_geo.translate((config.geometry.fs_nose, 0, 0))
        
        # Combine into one solid
        self._geometry = fuse_pos.union(wing_pos).union(canard_pos)
        
        return self._geometry

    def build_assembly(self) -> cq.Assembly:
        """Build a CadQuery Assembly for hierarchical visualization."""
        if self._geometry is None:
            self.generate_geometry()
            
        self._assembly = cq.Assembly(name=self.name)
        
        # Add components with colors
        self._assembly.add(
            self.fuselage.geometry, 
            name="Fuselage", 
            color=cq.Color("lightgray"),
            loc=cq.Location(cq.Vector(config.geometry.fs_nose, 0, 0))
        )
        
        self._assembly.add(
            self.wing.geometry, 
            name="MainWing", 
            color=cq.Color("white"),
            loc=cq.Location(cq.Vector(config.geometry.fs_wing_le, 0, 0))
        )
        
        self._assembly.add(
            self.canard.geometry, 
            name="Canard", 
            color=cq.Color("white"),
            loc=cq.Location(cq.Vector(config.geometry.fs_canard_le, 0, 0))
        )
        
        return self._assembly

    def export_dxf(self, output_path: Path) -> Path:
        """Export master layout DXF."""
        output_path.mkdir(parents=True, exist_ok=True)
        # Top view projection
        top_view = self.geometry.projectToViewport((0, 0, 1))
        dxf_file = output_path / f"{self.name}_top_layout.dxf"
        
        cq.exporters.export(top_view, str(dxf_file))
        return dxf_file

    def get_mass_properties(self) -> Dict[str, float]:
        """Calculate total volume and estimated weight."""
        if self._geometry is None:
            self.generate_geometry()
            
        # Volume in cubic inches
        total_volume = self._geometry.val().Volume()
        
        # Assuming average density of foam + glass (rough estimate)
        # foam: ~2 lb/ft3, glass: ~100 lb/ft3. Combined ~5-10 lb/ft3?
        # Let's say 0.005 lb/in3 for foam parts
        estimated_weight = total_volume * 0.005

        # Try to get center of mass, fallback to center
        try:
            cg = self._geometry.val().CenterOfMass()
        except AttributeError:
            cg = self._geometry.val().Center()
            
        return {
            "volume_in3": total_volume,
            "estimated_weight_lb": estimated_weight,
            "cg_x_fs": cg.x
        }
