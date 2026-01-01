"""
Open-EZ PDE: Base Component Class
=================================

All aircraft components inherit from AircraftComponent.
This enforces a consistent interface for geometry generation and export.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
import cadquery as cq
from config import config


class AircraftComponent(ABC):
    """
    Abstract base class for all aircraft components.

    Every component (wing, canard, fuselage, bulkhead) must implement:
    - generate_geometry(): Creates the CadQuery solid
    - export_dxf(): Exports 2D manufacturing profiles

    This ensures consistency across the design environment.
    """

    def __init__(self, name: str, description: str = ""):
        """
        Initialize a component.

        Args:
            name: Unique identifier (e.g., "canard_core", "f22_bulkhead")
            description: Human-readable description
        """
        self.name = name
        self.description = description
        self._geometry: Optional[cq.Workplane] = None
        self._metadata: Dict[str, Any] = {}

    @property
    def geometry(self) -> Optional[cq.Workplane]:
        """Access the generated CadQuery geometry."""
        if self._geometry is None:
            raise ValueError(
                f"Geometry not generated for {self.name}. "
                "Call generate_geometry() first."
            )
        return self._geometry

    @abstractmethod
    def generate_geometry(self) -> cq.Workplane:
        """
        Generate the CadQuery solid geometry.

        Returns:
            CadQuery Workplane containing the 3D solid.

        Implementation must:
        1. Use config parameters (never hard-code dimensions)
        2. Store result in self._geometry
        3. Return the geometry
        """
        pass

    @abstractmethod
    def export_dxf(self, output_path: Path) -> Path:
        """
        Export 2D profiles for manufacturing (laser cutting, templates).

        Args:
            output_path: Directory for DXF output

        Returns:
            Path to the exported DXF file

        Implementation must:
        1. Project geometry to 2D as appropriate
        2. Include alignment marks and part identification
        """
        pass

    @abstractmethod
    def manufacturing_plan(self, output_path: Path) -> Dict[str, Any]:
        """
        Generate manufacturing artifacts and report their tolerances.

        Args:
            output_path: Directory where manufacturing files are written.

        Returns:
            Mapping of artifact class (e.g., printable jig, CNC foam) to
            metadata describing the generated file (path, format, tolerance).
        """
        pass

    def export_step(self, output_path: Path) -> Path:
        """
        Export 3D geometry as STEP file for CAM software.

        Args:
            output_path: Directory for STEP output

        Returns:
            Path to the exported STEP file
        """
        if self._geometry is None:
            self.generate_geometry()

        step_file = output_path / f"{self.name}.step"
        cq.exporters.export(self._geometry, str(step_file))
        return step_file

    def export_stl(self, output_path: Path, tolerance: float = 0.01) -> Path:
        """
        Export 3D geometry as STL for 3D printing jigs.

        Args:
            output_path: Directory for STL output
            tolerance: Mesh tessellation tolerance (inches)

        Returns:
            Path to the exported STL file
        """
        if self._geometry is None:
            self.generate_geometry()

        stl_file = output_path / f"{self.name}.stl"
        cq.exporters.export(
            self._geometry,
            str(stl_file),
            exportType="STL",
            tolerance=tolerance
        )
        return stl_file

    def add_metadata(self, key: str, value: Any) -> None:
        """Store metadata for documentation and compliance tracking."""
        self._metadata[key] = value

    def get_metadata(self) -> Dict[str, Any]:
        """Retrieve all metadata for this component."""
        return {
            "name": self.name,
            "description": self.description,
            **self._metadata
        }

    def __repr__(self) -> str:
        status = "generated" if self._geometry else "not generated"
        return f"<{self.__class__.__name__}('{self.name}') [{status}]>"


class FoamCore(AircraftComponent):
    """
    Base class for foam core components (wings, canard).

    Adds methods specific to hot-wire cutting:
    - G-code generation
    - Kerf compensation
    - Root/tip synchronization
    """

    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
        self._root_profile: Optional[cq.Wire] = None
        self._tip_profile: Optional[cq.Wire] = None

    @abstractmethod
    def get_root_profile(self) -> cq.Wire:
        """Return the root airfoil wire for hot-wire cutting."""
        pass

    @abstractmethod
    def get_tip_profile(self) -> cq.Wire:
        """Return the tip airfoil wire for hot-wire cutting."""
        pass

    def export_gcode(
        self,
        output_path: Path,
        kerf_offset: float = 0.045,
        feed_rate: float = 4.0
    ) -> Path:
        """
        Generate 4-axis hot-wire G-code for CNC foam cutting.

        Args:
            output_path: Directory for G-code output
            kerf_offset: Wire kerf compensation (inches)
            feed_rate: Cutting feed rate (in/min)

        Returns:
            Path to the G-code file
        """
        # Defer to GCodeWriter for actual implementation
        from .manufacturing import GCodeWriter

        writer = GCodeWriter(
            root_profile=self.get_root_profile(),
            tip_profile=self.get_tip_profile(),
            kerf_offset=kerf_offset,
            feed_rate=feed_rate
        )
        return writer.write(output_path / f"{self.name}.tap")


class Bulkhead(AircraftComponent):
    """
    Base class for fuselage bulkheads.

    Bulkheads are 2D profiles extruded to foam thickness.
    Primary output is DXF for laser cutting.
    """

    def __init__(
        self,
        name: str,
        station: float,
        description: str = "",
        thickness: Optional[float] = None
    ):
        """
        Initialize a bulkhead at a fuselage station.

        Args:
            name: Bulkhead identifier (e.g., "F22", "F28")
            station: Fuselage station in inches from nose datum
            description: Purpose of bulkhead
        """
        super().__init__(name, description)
        self.station = station
        self.thickness = thickness or config.materials.foam_core_thickness

    @abstractmethod
    def get_profile(self) -> cq.Wire:
        """Return the 2D bulkhead outline."""
        pass

    def generate_geometry(self) -> cq.Workplane:
        """Extrude the 2D bulkhead profile to the specified thickness."""
        profile = self.get_profile()
        self._geometry = cq.Workplane("XY").add(profile).extrude(self.thickness)
        return self._geometry

    def export_dxf(self, output_path: Path) -> Path:
        """Export the bulkhead profile as DXF for routing or tracing."""
        profile = self.get_profile()
        output_file = output_path / f"{self.name}.dxf"
        cq.exporters.export(cq.Workplane("XY").add(profile), str(output_file), exportType="DXF")
        return output_file

    def manufacturing_plan(self, output_path: Path) -> Dict[str, Any]:
        """Create DXF templates and printable jigs for the bulkhead."""
        output_path.mkdir(parents=True, exist_ok=True)
        intents = config.manufacturing.component_intents.get("bulkhead")

        dxf_path = self.export_dxf(output_path)
        stl_path = self.export_stl(output_path, tolerance=intents.printable_jigs.tolerance)
        step_path = self.export_step(output_path)

        return {
            "sheet_templates": {
                "path": dxf_path,
                "format": intents.sheet_templates.format,
                "tolerance": intents.sheet_templates.tolerance,
                "artifact": intents.sheet_templates.artifact,
            },
            "printable_jigs": {
                "path": stl_path,
                "format": intents.printable_jigs.format,
                "tolerance": intents.printable_jigs.tolerance,
                "artifact": intents.printable_jigs.artifact,
            },
            "cad_step": {
                "path": step_path,
                "format": "STEP",
                "tolerance": None,
                "artifact": "bulkhead_solid",
            },
            "cnc_foam": {
                "path": dxf_path,
                "format": intents.cnc_foam.format,
                "tolerance": intents.cnc_foam.tolerance,
                "artifact": intents.cnc_foam.artifact,
            },
        }
