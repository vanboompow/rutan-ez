# Open-EZ PDE Core Module
"""Lightweight package exports with lazy loading.

The previous implementation eagerly imported all core submodules. That pulled
CadQuery into the import chain even for utilities that don't require 3D CAD
support, which fails in minimal CI environments lacking `libGL.so.1`. To keep
runtime-only checks green, we now defer heavy imports until the corresponding
symbols are first accessed.
"""

from importlib import import_module
from typing import TYPE_CHECKING

# Explicit re-exports for type checkers
if TYPE_CHECKING:  # pragma: no cover - import only for static analysis
    from .analysis import (
        AerodynamicPoint,
        CLMaxResult,
        OpenVSPRunner,
        StructuralMeshManifest,
        TrimSweepResult,
        VSPBridge,
        physics,
        PhysicsEngine,
        StabilityMetrics,
        WeightBalance,
        WeightItem,
    )
    from .aerodynamics import Airfoil, AirfoilFactory
    from .base import AircraftComponent
    from .compliance import ComplianceTracker
    from .manufacturing import CutPath, GCodeConfig, GCodeWriter, JigFactory
    from .structures import CanardGenerator, Fuselage, WingGenerator

__all__ = [
    # Base
    "AircraftComponent",
    # Aerodynamics
    "AirfoilFactory",
    "Airfoil",
    # Structures
    "WingGenerator",
    "CanardGenerator",
    "Fuselage",
    # Compliance
    "ComplianceTracker",
    # Manufacturing
    "GCodeWriter",
    "JigFactory",
    "GCodeConfig",
    "CutPath",
    # Analysis
    "PhysicsEngine",
    "VSPBridge",
    "StabilityMetrics",
    "WeightBalance",
    "WeightItem",
    "physics",
    # OpenVSP Runner
    "OpenVSPRunner",
    "AerodynamicPoint",
    "TrimSweepResult",
    "CLMaxResult",
    "StructuralMeshManifest",
    "openvsp_runner",
]


_MODULE_MAP = {
    # Base
    "AircraftComponent": ("core.base", "AircraftComponent"),
    # Aerodynamics
    "AirfoilFactory": ("core.aerodynamics", "AirfoilFactory"),
    "Airfoil": ("core.aerodynamics", "Airfoil"),
    # Structures
    "WingGenerator": ("core.structures", "WingGenerator"),
    "CanardGenerator": ("core.structures", "CanardGenerator"),
    "Fuselage": ("core.structures", "Fuselage"),
    # Compliance
    "ComplianceTracker": ("core.compliance", "ComplianceTracker"),
    # Manufacturing
    "GCodeWriter": ("core.manufacturing", "GCodeWriter"),
    "JigFactory": ("core.manufacturing", "JigFactory"),
    "GCodeConfig": ("core.manufacturing", "GCodeConfig"),
    "CutPath": ("core.manufacturing", "CutPath"),
    # Analysis
    "PhysicsEngine": ("core.analysis", "PhysicsEngine"),
    "VSPBridge": ("core.analysis", "VSPBridge"),
    "StabilityMetrics": ("core.analysis", "StabilityMetrics"),
    "WeightBalance": ("core.analysis", "WeightBalance"),
    "WeightItem": ("core.analysis", "WeightItem"),
    "physics": ("core.analysis", "physics"),
    "OpenVSPRunner": ("core.analysis", "OpenVSPRunner"),
    "AerodynamicPoint": ("core.analysis", "AerodynamicPoint"),
    "TrimSweepResult": ("core.analysis", "TrimSweepResult"),
    "CLMaxResult": ("core.analysis", "CLMaxResult"),
    "StructuralMeshManifest": ("core.analysis", "StructuralMeshManifest"),
    "openvsp_runner": ("core.analysis", "openvsp_runner"),
}


def __getattr__(name):
    if name not in _MODULE_MAP:
        raise AttributeError(f"module 'core' has no attribute '{name}'")

    module_name, attribute = _MODULE_MAP[name]
    module = import_module(module_name)
    value = getattr(module, attribute)
    globals()[name] = value
    return value
