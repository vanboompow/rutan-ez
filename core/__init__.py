"""Open-EZ PDE Core Module."""

__all__ = [
    "AircraftComponent",
    "AirfoilFactory",
    "Airfoil",
    "WingGenerator",
    "Fuselage",
    "ComplianceTracker",
]


def __getattr__(name):
    if name == "AircraftComponent":
        from .base import AircraftComponent

        return AircraftComponent
    if name == "AirfoilFactory":
        from .aerodynamics import AirfoilFactory

        return AirfoilFactory
    if name == "Airfoil":
        from .aerodynamics import Airfoil

        return Airfoil
    if name == "WingGenerator":
        from .structures import WingGenerator

        return WingGenerator
    if name == "Fuselage":
        from .structures import Fuselage

        return Fuselage
    if name == "ComplianceTracker":
        from .compliance import ComplianceTracker

        return ComplianceTracker
    raise AttributeError(f"module 'core' has no attribute {name}")
