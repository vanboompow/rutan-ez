# Open-EZ PDE Core Module
"""Lightweight package bootstrap.

This package intentionally avoids importing heavy optional dependencies
such as CadQuery at module import time. CI runners used for linting and
runtime smoke tests may not have the system libraries CadQuery requires
(e.g., ``libGL``), so we lazily import submodules only when their
attributes are requested. This keeps lightweight consumers like the
OpenVSP surrogate tests working without needing full CAD tooling.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

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
    "OpenVSPRunner",
    "AerodynamicPoint",
    "TrimSweepResult",
    "CLMaxResult",
    "StructuralMeshManifest",
    "openvsp_runner",
]

_MODULE_MAP = {
    # Base
    "AircraftComponent": "core.base",
    # Aerodynamics
    "AirfoilFactory": "core.aerodynamics",
    "Airfoil": "core.aerodynamics",
    # Structures
    "WingGenerator": "core.structures",
    "CanardGenerator": "core.structures",
    "Fuselage": "core.structures",
    # Compliance
    "ComplianceTracker": "core.compliance",
    # Manufacturing
    "GCodeWriter": "core.manufacturing",
    "JigFactory": "core.manufacturing",
    "GCodeConfig": "core.manufacturing",
    "CutPath": "core.manufacturing",
    # Analysis
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


def __getattr__(name: str):
    """Lazily import attributes to avoid heavy dependencies at import time."""

    module_name = _MODULE_MAP.get(name)
    if module_name is None:
        raise AttributeError(f"module 'core' has no attribute '{name}'")

    module = importlib.import_module(module_name)
    return getattr(module, name)


if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from .base import AircraftComponent
    from .aerodynamics import AirfoilFactory, Airfoil
    from .structures import WingGenerator, CanardGenerator, Fuselage
    from .compliance import ComplianceTracker
    from .manufacturing import GCodeWriter, JigFactory, GCodeConfig, CutPath
    from .analysis import (
        PhysicsEngine,
        VSPBridge,
        StabilityMetrics,
        WeightBalance,
        WeightItem,
        physics,
        OpenVSPRunner,
        AerodynamicPoint,
        TrimSweepResult,
        CLMaxResult,
        StructuralMeshManifest,
        openvsp_runner,
    )

