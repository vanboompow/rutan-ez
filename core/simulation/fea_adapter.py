"""Lightweight beam and plate analysis for spars and jigs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from config import config


@dataclass
class BeamSection:
    """Simple rectangular section for bending analysis."""

    width_in: float
    height_in: float
    modulus_psi: float

    @property
    def inertia(self) -> float:
        """Area moment of inertia about the neutral axis (in^4)."""
        return (self.width_in * (self.height_in ** 3)) / 12


@dataclass
class BeamResult:
    """Result of a cantilever beam calculation."""

    tip_deflection_in: float
    max_stress_psi: float


class BeamFEAAdapter:
    """Euler-Bernoulli beam estimator for rapid spar checks."""

    def __init__(self, section: BeamSection | None = None):
        spar_height = config.materials.spar_cap_plies * config.materials.uni_ply_thickness
        section = section or BeamSection(
            width_in=config.materials.spar_cap_width,
            height_in=spar_height,
            modulus_psi=2.8e6,  # typical UNI glass modulus in bending
        )
        self.section = section

    def analyze_cantilever(self, span_in: float, tip_load_lbf: float) -> BeamResult:
        """Compute tip deflection and max stress for a point load at the tip."""

        L = span_in
        E = self.section.modulus_psi
        inertia = self.section.inertia

        tip_deflection = (tip_load_lbf * (L ** 3)) / (3 * E * inertia)
        max_stress = (tip_load_lbf * L * (self.section.height_in / 2)) / inertia
        return BeamResult(tip_deflection_in=tip_deflection, max_stress_psi=max_stress)

    def nominal_spar_check(self) -> Dict[str, float]:
        """Evaluate the main spar at half-span under a representative load."""

        half_span = config.geometry.wing_span / 2
        load = 450.0  # lbf at tip for gust + maneuver reserve
        result = self.analyze_cantilever(span_in=half_span, tip_load_lbf=load)
        return {
            "tip_deflection_in": result.tip_deflection_in,
            "max_stress_psi": result.max_stress_psi,
        }

    def jig_flatness_check(self, plate_thickness_in: float = 0.75) -> Dict[str, float]:
        """Approximate plate stiffness for jig tables used during layup."""

        modulus = 1.5e6  # plywood modulus (psi)
        width = 24.0
        height = plate_thickness_in
        plate_section = BeamSection(width_in=width, height_in=height, modulus_psi=modulus)
        half_span = 36.0
        load = 50.0
        result = BeamFEAAdapter(section=plate_section).analyze_cantilever(span_in=half_span, tip_load_lbf=load)
        return {
            "tip_deflection_in": result.tip_deflection_in,
            "max_stress_psi": result.max_stress_psi,
        }
