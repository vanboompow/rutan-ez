# Open-EZ PDE Core Module
#
# Importing the full geometry stack eagerly pulls in optional system
# dependencies (CadQuery, OpenVSP bindings, etc.). To keep light-weight
# consumers and CI smoke tests working in headless environments, we lazily
# import submodules only when their symbols are accessed.

from importlib import import_module
from typing import Any, Callable, Dict

__all__ = [
    "AircraftComponent",
    "AirfoilFactory",
    "Airfoil",
    "WingGenerator",
    "CanardGenerator",
    "Fuselage",
    "ComplianceTracker",
    "GCodeWriter",
    "JigFactory",
    "GCodeConfig",
    "CutPath",
    "PhysicsEngine",
    "VSPBridge",
    "StabilityMetrics",
    "WeightBalance",
    "WeightItem",
    "physics",
    "OpenVSPRunner",
    "AerodynamicPoint",
    "TrimSweepResult",
    "CLMaxResult",
    "StructuralMeshManifest",
    "openvsp_runner",
]


_lazy_loaders: Dict[str, Callable[[], Any]] = {
    "AircraftComponent": lambda: getattr(import_module("core.base"), "AircraftComponent"),
    "AirfoilFactory": lambda: getattr(import_module("core.aerodynamics"), "AirfoilFactory"),
    "Airfoil": lambda: getattr(import_module("core.aerodynamics"), "Airfoil"),
    "WingGenerator": lambda: getattr(import_module("core.structures"), "WingGenerator"),
    "CanardGenerator": lambda: getattr(import_module("core.structures"), "CanardGenerator"),
    "Fuselage": lambda: getattr(import_module("core.structures"), "Fuselage"),
    "ComplianceTracker": lambda: getattr(import_module("core.compliance"), "ComplianceTracker"),
    "GCodeWriter": lambda: getattr(import_module("core.manufacturing"), "GCodeWriter"),
    "JigFactory": lambda: getattr(import_module("core.manufacturing"), "JigFactory"),
    "GCodeConfig": lambda: getattr(import_module("core.manufacturing"), "GCodeConfig"),
    "CutPath": lambda: getattr(import_module("core.manufacturing"), "CutPath"),
    "PhysicsEngine": lambda: getattr(import_module("core.analysis"), "PhysicsEngine"),
    "VSPBridge": lambda: getattr(import_module("core.analysis"), "VSPBridge"),
    "StabilityMetrics": lambda: getattr(import_module("core.analysis"), "StabilityMetrics"),
    "WeightBalance": lambda: getattr(import_module("core.analysis"), "WeightBalance"),
    "WeightItem": lambda: getattr(import_module("core.analysis"), "WeightItem"),
    "physics": lambda: getattr(import_module("core.analysis"), "physics"),
    "OpenVSPRunner": lambda: getattr(import_module("core.analysis"), "OpenVSPRunner"),
    "AerodynamicPoint": lambda: getattr(import_module("core.analysis"), "AerodynamicPoint"),
    "TrimSweepResult": lambda: getattr(import_module("core.analysis"), "TrimSweepResult"),
    "CLMaxResult": lambda: getattr(import_module("core.analysis"), "CLMaxResult"),
    "StructuralMeshManifest": lambda: getattr(import_module("core.analysis"), "StructuralMeshManifest"),
    "openvsp_runner": lambda: getattr(import_module("core.analysis"), "openvsp_runner"),
}


def __getattr__(name: str) -> Any:
    if name not in _lazy_loaders:
        raise AttributeError(f"module 'core' has no attribute '{name}'")

    value = _lazy_loaders[name]()
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
