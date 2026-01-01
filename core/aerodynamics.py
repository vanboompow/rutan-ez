"""
Aerodynamics façade module.

Re-exports the airfoil ingestion utilities so callers can continue to
import ``AirfoilFactory``/``Airfoil`` from ``core.aerodynamics`` while
the implementation lives in :mod:`core.airfoil_factory`.
"""

from .airfoil_factory import Airfoil, AirfoilCoordinates, AirfoilFactory, airfoil_factory

__all__ = [
    "Airfoil",
    "AirfoilCoordinates",
    "AirfoilFactory",
    "airfoil_factory",
]
