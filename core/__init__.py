"""Open-EZ PDE Core Module

Uses lazy imports to avoid pulling heavy CAD dependencies when only compliance
utilities are required (e.g., generating FAA paperwork on a headless host).
"""

from importlib import import_module
from typing import Any

__all__ = [
    "AircraftComponent",
    "AirfoilFactory",
    "Airfoil",
    "WingGenerator",
    "Fuselage",
    "ComplianceTracker",
    "ComplianceTaskTracker",
    "TaskRole",
]

_LAZY_IMPORTS = {
    "AircraftComponent": "core.base",
    "AirfoilFactory": "core.aerodynamics",
    "Airfoil": "core.aerodynamics",
    "WingGenerator": "core.structures",
    "Fuselage": "core.structures",
    "ComplianceTracker": "core.compliance",
    "ComplianceTaskTracker": "core.compliance",
    "TaskRole": "core.compliance",
}


def __getattr__(name: str) -> Any:
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module 'core' has no attribute '{name}'")

    module = import_module(_LAZY_IMPORTS[name])
    return getattr(module, name)


