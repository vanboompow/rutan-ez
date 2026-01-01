"""Open-EZ PDE Core Module

Uses lazy imports to avoid pulling heavy CAD dependencies when only compliance
utilities are required (e.g., generating FAA paperwork on a headless host).
"""

from importlib import import_module
from typing import Any

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
    "ComplianceTaskTracker",
    "TaskRole",
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

_LAZY_IMPORTS = {
    "AircraftComponent": "core.base",
    "AirfoilFactory": "core.aerodynamics",
    "Airfoil": "core.aerodynamics",
    "WingGenerator": "core.structures",
    "CanardGenerator": "core.structures",
    "Fuselage": "core.structures",
    "ComplianceTracker": "core.compliance",
    "ComplianceTaskTracker": "core.compliance",
    "TaskRole": "core.compliance",
    "GCodeWriter": "core.manufacturing",
    "JigFactory": "core.manufacturing",
    "GCodeConfig": "core.manufacturing",
    "CutPath": "core.manufacturing",
    "PhysicsEngine": "core.analysis",
    "VSPBridge": "core.analysis",
    "StabilityMetrics": "core.analysis",
    "WeightBalance": "core.analysis",
    "WeightItem": "core.analysis",
    "physics": "core.analysis",
    "OpenVSPRunner": "core.analysis",
    "AerodynamicPoint": "core.analysis",
    "TrimSweepResult": "core.analysis",
    "CLMaxResult": "core.analysis",
    "StructuralMeshManifest": "core.analysis",
    "openvsp_runner": "core.analysis",
}


def __getattr__(name: str) -> Any:
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module 'core' has no attribute '{name}'")

    module = import_module(_LAZY_IMPORTS[name])
    return getattr(module, name)
