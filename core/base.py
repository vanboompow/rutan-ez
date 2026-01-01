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

    def export_step(self, output_path: Path) -> Path:
        """
        Export 3D geometry as STEP file for CAM software.

        Args:
            output_path: Directory for STEP output

        Returns:
            Path to the exported STEP file
        """
        output_path.mkdir(parents=True, exist_ok=True)
        step_file = output_path / f"{self.name}.step"
        cq.exporters.export(self._geometry, str(step_file))
        self._write_artifact_metadata(step_file, artifact_type="STEP")
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
        output_path.mkdir(parents=True, exist_ok=True)
        stl_file = output_path / f"{self.name}.stl"
        cq.exporters.export(
            self._geometry,
            str(stl_file),
            exportType="STL",
            tolerance=tolerance
        )
        self._write_artifact_metadata(stl_file, artifact_type="STL")
        return stl_file

    def _write_artifact_metadata(self, artifact_path: Path, artifact_type: str) -> None:
        """Persist standard metadata next to an exported artifact."""
        from .metadata import write_artifact_metadata

        write_artifact_metadata(
            artifact_path=artifact_path,
            component=self,
            artifact_type=artifact_type,
        )

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
        output_path.mkdir(parents=True, exist_ok=True)
        gcode_path = writer.write(output_path / f"{self.name}.tap")
        self._write_artifact_metadata(gcode_path, artifact_type="GCODE")
        return gcode_path


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
        description: str = ""
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

    @abstractmethod
    def get_profile(self) -> cq.Wire:
        """Return the 2D bulkhead outline."""
        pass
