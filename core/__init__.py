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
    "physics",
    # Weight & Balance (own module, also re-exported from core.analysis)
    "WeightBalance",
    "WeightItem",
    # OpenVSP Runner (own module, also re-exported from core.analysis)
    "OpenVSPRunner",
    "AerodynamicPoint",
    "TrimSweepResult",
    "CLMaxResult",
    "StructuralMeshManifest",
    "openvsp_runner",
    # Atmosphere
    "atmosphere",
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
    "GCodeConfig": "core.manufacturing",
    "CutPath": "core.manufacturing",
    # JigFactory lives in core.jig_factory; also re-exported by core.manufacturing
    "JigFactory": "core.jig_factory",
    # Analysis module (PhysicsEngine, VSPBridge, StabilityMetrics)
    "PhysicsEngine": "core.analysis",
    "VSPBridge": "core.analysis",
    "StabilityMetrics": "core.analysis",
    "physics": "core.analysis",
    # Weight & Balance — canonical home is core.weight_balance
    "WeightBalance": "core.weight_balance",
    "WeightItem": "core.weight_balance",
    # OpenVSP Runner — canonical home is core.openvsp_runner
    "OpenVSPRunner": "core.openvsp_runner",
    "AerodynamicPoint": "core.openvsp_runner",
    "TrimSweepResult": "core.openvsp_runner",
    "CLMaxResult": "core.openvsp_runner",
    "StructuralMeshManifest": "core.openvsp_runner",
    "openvsp_runner": "core.openvsp_runner",
    # Atmosphere
    "atmosphere": "core.atmosphere",
}


def __getattr__(name: str) -> Any:
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module 'core' has no attribute '{name}'")

    module = import_module(_LAZY_IMPORTS[name])
    return getattr(module, name)
