"""Beam and composite laminate analysis for spars and structural components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import math

import numpy as np

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
        return (self.width_in * (self.height_in**3)) / 12


@dataclass
class BeamResult:
    """Result of a cantilever beam calculation."""

    tip_deflection_in: float
    max_stress_psi: float


class BeamFEAAdapter:
    """Euler-Bernoulli beam estimator for rapid spar checks."""

    def __init__(self, section: BeamSection | None = None):
        spar_height = (
            config.materials.spar_cap_plies * config.materials.uni_ply_thickness
        )
        section = section or BeamSection(
            width_in=config.materials.spar_cap_width,
            height_in=spar_height,
            modulus_psi=2.8e6,  # typical UNI glass modulus in bending
        )
        self.section = section

    def analyze_cantilever(self, span_in: float, tip_load_lbf: float) -> BeamResult:
        """Compute tip deflection and max stress for a point load at the tip."""

        length = span_in
        modulus = self.section.modulus_psi
        inertia = self.section.inertia

        tip_deflection = (tip_load_lbf * (length**3)) / (3 * modulus * inertia)
        max_stress = (tip_load_lbf * length * (self.section.height_in / 2)) / inertia
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
        plate_section = BeamSection(
            width_in=width, height_in=height, modulus_psi=modulus
        )
        half_span = 36.0
        load = 50.0
        result = BeamFEAAdapter(section=plate_section).analyze_cantilever(
            span_in=half_span, tip_load_lbf=load
        )
        return {
            "tip_deflection_in": result.tip_deflection_in,
            "max_stress_psi": result.max_stress_psi,
        }


# E-Glass/Epoxy material properties (psi)
UNI_GLASS_PROPERTIES = {
    "E1": 5.5e6, "E2": 1.2e6, "G12": 0.6e6, "nu12": 0.28,
    "F1t": 150000, "F1c": 100000, "F2t": 5000, "F2c": 20000, "F6": 10000,
    "density": 0.072,
}

BID_GLASS_PROPERTIES = {
    "E1": 2.6e6, "E2": 2.6e6, "G12": 0.5e6, "nu12": 0.13,
    "F1t": 40000, "F1c": 35000, "F2t": 40000, "F2c": 35000, "F6": 12000,
    "density": 0.065,
}

MATERIAL_PROPERTIES = {
    "uni": UNI_GLASS_PROPERTIES, "uni_glass": UNI_GLASS_PROPERTIES,
    "bid": BID_GLASS_PROPERTIES, "bid_glass": BID_GLASS_PROPERTIES,
}


@dataclass
class CompositePly:
    """Single composite ply with orientation and material properties."""

    material: str
    thickness_in: float
    angle_deg: float

    @property
    def properties(self) -> Dict[str, float]:
        return MATERIAL_PROPERTIES.get(self.material.lower(), UNI_GLASS_PROPERTIES)

    def stiffness_matrix_local(self) -> np.ndarray:
        """Reduced stiffness matrix [Q] in local coordinates."""
        props = self.properties
        E1, E2, G12, nu12 = props["E1"], props["E2"], props["G12"], props["nu12"]
        nu21 = nu12 * E2 / E1
        denom = 1 - nu12 * nu21
        return np.array([
            [E1 / denom, nu12 * E2 / denom, 0],
            [nu21 * E1 / denom, E2 / denom, 0],
            [0, 0, G12]
        ])

    def stiffness_matrix_global(self) -> np.ndarray:
        """Transformed stiffness matrix [Q_bar] in global coordinates."""
        Q = self.stiffness_matrix_local()
        theta = math.radians(self.angle_deg)
        c, s = math.cos(theta), math.sin(theta)
        T_inv = np.array([
            [c**2, s**2, -2*c*s],
            [s**2, c**2, 2*c*s],
            [c*s, -c*s, c**2 - s**2]
        ])
        return T_inv @ Q @ T_inv.T


@dataclass
class CompositeSection:
    """Multi-ply laminate section with CLT analysis."""

    plies: List[CompositePly]
    width_in: float

    @property
    def total_thickness(self) -> float:
        return sum(p.thickness_in for p in self.plies)

    def abd_matrices(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Classical Laminate Theory [A], [B], [D] matrices."""
        h_total = self.total_thickness
        z_bottom = -h_total / 2
        A, B, D = np.zeros((3, 3)), np.zeros((3, 3)), np.zeros((3, 3))

        for ply in self.plies:
            z_top = z_bottom + ply.thickness_in
            z_mid = (z_top + z_bottom) / 2
            Q_bar = ply.stiffness_matrix_global()
            A += Q_bar * ply.thickness_in
            B += Q_bar * ply.thickness_in * z_mid
            D += Q_bar * (z_top**3 - z_bottom**3) / 3
            z_bottom = z_top
        return A, B, D

    def equivalent_bending_stiffness(self) -> float:
        """D11 bending stiffness for spanwise loading."""
        _, _, D = self.abd_matrices()
        return D[0, 0] * self.width_in

    def tsai_wu_margin(self, stress_state: np.ndarray) -> float:
        """Tsai-Wu failure criterion margin (>0 is safe)."""
        sigma_1, sigma_2, tau_12 = stress_state
        F1t = min(p.properties["F1t"] for p in self.plies)
        F1c = min(p.properties["F1c"] for p in self.plies)
        F2t = min(p.properties["F2t"] for p in self.plies)
        F2c = min(p.properties["F2c"] for p in self.plies)
        F6 = min(p.properties["F6"] for p in self.plies)

        f1 = 1.0/F1t - 1.0/F1c
        f2 = 1.0/F2t - 1.0/F2c
        f11 = 1.0 / (F1t * F1c)
        f22 = 1.0 / (F2t * F2c)
        f66 = 1.0 / (F6**2)
        f12 = -0.5 * math.sqrt(f11 * f22)

        F = (f1*sigma_1 + f2*sigma_2 + f11*sigma_1**2 + f22*sigma_2**2 +
             f66*tau_12**2 + 2*f12*sigma_1*sigma_2)
        return 1.0 - F


@dataclass
class SparCapResult:
    """Spar cap structural analysis result."""

    stations: List[float]
    max_stresses: List[float]
    tsai_wu_margins: List[float]
    recommended_plies: List[int]
    weight_penalty_lb: float
    is_adequate: bool

    def summary(self) -> str:
        status = "ADEQUATE" if self.is_adequate else "REINFORCEMENT REQUIRED"
        min_margin = min(self.tsai_wu_margins)
        min_idx = self.tsai_wu_margins.index(min_margin)
        return (f"Status: {status}\n"
                f"Critical Station: {self.stations[min_idx]:.1f} in\n"
                f"Minimum Margin: {min_margin:.3f}")


class CompositeFEAAdapter:
    """Composite spar analysis with Tsai-Wu failure criterion."""

    def __init__(self, baseline_plies: int = None, ply_material: str = "uni_glass",
                 ply_thickness: float = None, spar_width: float = None):
        self.baseline_plies = baseline_plies or config.materials.spar_cap_plies
        self.ply_material = ply_material
        self.ply_thickness = ply_thickness or config.materials.uni_ply_thickness
        self.spar_width = spar_width or config.materials.spar_cap_width

    def build_section(self, ply_count: int = None, angles: List[float] = None) -> CompositeSection:
        count = ply_count or self.baseline_plies
        angles = angles or [0.0] * count
        plies = [CompositePly(self.ply_material, self.ply_thickness, a) for a in angles]
        return CompositeSection(plies=plies, width_in=self.spar_width)

    def analyze_spar_cap(self, span_in: float = None, tip_load_lbf: float = 450.0,
                         load_factor: float = 3.8, n_stations: int = 10) -> SparCapResult:
        """Verify spar cap adequacy under design loads."""
        span_in = span_in or config.geometry.wing_span / 2
        ultimate_load = tip_load_lbf * load_factor * 1.5

        station_positions = list(np.linspace(0, span_in, n_stations))
        max_stresses, margins, recommended = [], [], []

        section = self.build_section()
        h = section.total_thickness

        for pos in station_positions:
            moment = ultimate_load * (span_in - pos)
            c = h / 2
            _, _, D = section.abd_matrices()
            sigma_max = moment * c / (section.equivalent_bending_stiffness() / D[0, 0])

            stress_state = np.array([sigma_max, 0.0, 0.0])
            margin = section.tsai_wu_margin(stress_state)

            max_stresses.append(abs(sigma_max))
            margins.append(margin)

            if margin < 0.2:
                extra = max(1, int(math.ceil(self.baseline_plies * (0.25 - margin) / 0.25 * 0.3)))
                recommended.append(self.baseline_plies + extra)
            else:
                recommended.append(self.baseline_plies)

        extra_total = sum(r - self.baseline_plies for r in recommended)
        ply_density = MATERIAL_PROPERTIES[self.ply_material]["density"]
        weight_penalty = extra_total * self.spar_width * span_in * self.ply_thickness * ply_density * 2

        return SparCapResult(
            stations=station_positions, max_stresses=max_stresses,
            tsai_wu_margins=margins, recommended_plies=recommended,
            weight_penalty_lb=weight_penalty, is_adequate=all(m > 0 for m in margins)
        )
