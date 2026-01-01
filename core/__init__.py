"""Open-EZ PDE Core Module.

Lazy-load heavy dependencies like CadQuery so lightweight simulation modules
can run inside CI containers without OpenCASCADE system libraries.
"""

import importlib
from types import ModuleType
from typing import Any

__all__ = [
    "AircraftComponent",
    "AirfoilFactory",
    "Airfoil",
    "WingGenerator",
    "Fuselage",
    "ComplianceTracker",
]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module 'core' has no attribute '{name}'")

    module_map = {
        "AircraftComponent": ("core.base", "AircraftComponent"),
        "AirfoilFactory": ("core.aerodynamics", "AirfoilFactory"),
        "Airfoil": ("core.aerodynamics", "Airfoil"),
        "WingGenerator": ("core.structures", "WingGenerator"),
        "Fuselage": ("core.structures", "Fuselage"),
        "ComplianceTracker": ("core.compliance", "ComplianceTracker"),
    }

    module_name, attr = module_map[name]
    module: ModuleType = importlib.import_module(module_name)
    return getattr(module, attr)
