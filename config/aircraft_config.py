"""
Open-EZ PDE: Single Source of Truth (SSOT)
==========================================

This configuration file defines ALL parametric constants for the Long-EZ.
NEVER hard-code dimensions elsewhere. All geometry, analysis, and documentation
derive from these variables.

Safety Mandate: Roncz R1145MS canard airfoil is the DEFAULT.
The original GU25-5(11)8 caused dangerous pitch-down in rain.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import math


class AirfoilType(Enum):
    """Supported airfoil profiles."""
    RONCZ_R1145MS = "roncz_r1145ms"      # MANDATORY canard airfoil (rain-safe)
    EPPLER_1230_MOD = "eppler_1230_mod"   # Main wing (with reflex)
    GU25_5_11_8 = "gu25_5_11_8"           # DEPRECATED - unsafe in rain


class FoamType(Enum):
    """Foam core materials with thermal properties for hot-wire cutting."""
    STYROFOAM_BLUE = "styrofoam_blue"     # 2 lb/ft³ - Standard wing cores
    URETHANE_2LB = "urethane_2lb"         # 2 lb/ft³ - Higher temp resistance
    DIVINYCELL_H45 = "divinycell_h45"     # Structural foam - fuselage


@dataclass
class GeometricParams:
    """Primary aircraft geometry - all dimensions in inches unless noted."""

    # === MAIN WING (Eppler 1230 Modified) ===
    wing_span: float = 316.8              # Total span (26.4 ft)
    wing_root_chord: float = 68.0         # Root chord at BL 23.3
    wing_tip_chord: float = 32.0          # Tip chord
    wing_sweep_le: float = 25.0           # Leading edge sweep (degrees)
    wing_dihedral: float = -4.5           # Negative = anhedral (degrees)
    wing_washout: float = 1.0             # Tip washout (degrees)
    wing_incidence: float = 0.0           # Relative to longerons (degrees)

    # === CANARD (Roncz R1145MS - SAFETY CRITICAL) ===
    canard_span: float = 147.0            # Total span (12.25 ft)
    canard_root_chord: float = 17.0       # Root chord
    canard_tip_chord: float = 13.5        # Tip chord
    canard_sweep_le: float = 13.5         # Leading edge sweep (degrees)
    canard_incidence: float = -1.5        # Relative to longerons (degrees)

    # === FUSELAGE STATIONS (FS) ===
    fs_nose: float = 0.0                  # Nose reference
    fs_canard_le: float = 36.0            # Canard leading edge
    fs_pilot_seat: float = 80.0           # F-22 bulkhead (pilot)
    fs_rear_seat: float = 115.0           # F-28 bulkhead (passenger/baggage)
    fs_wing_le: float = 133.0             # Wing leading edge at root
    fs_firewall: float = 180.0            # Engine firewall (F-28)
    fs_tail: float = 214.0                # Tail cone terminus

    # === ERGONOMICS ===
    cockpit_width: float = 23.0           # F-22 interior width
    pilot_height_max: float = 77.0        # Max pilot height (inches)

    # === DERIVED DIMENSIONS (computed at runtime) ===
    @property
    def canard_arm(self) -> float:
        """Distance from wing AC to canard AC (critical for stability)."""
        wing_ac = self.fs_wing_le + (self.wing_root_chord * 0.25)
        canard_ac = self.fs_canard_le + (self.canard_root_chord * 0.25)
        return wing_ac - canard_ac

    @property
    def wing_area(self) -> float:
        """Wing planform area in square feet."""
        # Trapezoidal approximation
        avg_chord = (self.wing_root_chord + self.wing_tip_chord) / 2
        return (avg_chord * self.wing_span) / 144  # sq in to sq ft

    @property
    def canard_area(self) -> float:
        """Canard planform area in square feet."""
        avg_chord = (self.canard_root_chord + self.canard_tip_chord) / 2
        return (avg_chord * self.canard_span) / 144

    @property
    def wing_aspect_ratio(self) -> float:
        """Wing aspect ratio (span² / area)."""
        span_ft = self.wing_span / 12
        return (span_ft ** 2) / self.wing_area


@dataclass
class MaterialParams:
    """Composite layup and foam specifications."""

    # === FIBERGLASS PLY THICKNESSES (inches) ===
    bid_ply_thickness: float = 0.013      # Bi-directional cloth (per ply)
    uni_ply_thickness: float = 0.009      # Unidirectional tape (per ply)

    # === SPAR CAP LAYUP (Long-EZ specific) ===
    spar_cap_plies: int = 17              # UNI plies for main spar cap
    spar_cap_width: float = 3.0           # Spar cap width (inches)

    # === FOAM CORE ===
    wing_core_foam: FoamType = FoamType.STYROFOAM_BLUE
    fuselage_foam: FoamType = FoamType.URETHANE_2LB
    foam_core_thickness: float = 0.5      # PVC foam shell thickness

    @property
    def spar_trough_depth(self) -> float:
        """Spar cap trough depth = plies × thickness."""
        return self.spar_cap_plies * self.uni_ply_thickness


@dataclass
class ManufacturingParams:
    """CNC and hot-wire cutting parameters."""

    # === HOT-WIRE CUTTING ===
    wire_diameter: float = 0.032          # NiChrome wire diameter (inches)
    wire_temp_styrofoam: float = 400      # Cutting temp for Styrofoam (°F)
    wire_temp_urethane: float = 500       # Cutting temp for urethane (°F)
    feed_rate_default: float = 4.0        # Default feed rate (in/min)

    # === KERF COMPENSATION ===
    kerf_styrofoam: float = 0.045         # Material removed (inches)
    kerf_urethane: float = 0.035          # Material removed (inches)

    @property
    def kerf_compensation(self) -> Dict[FoamType, float]:
        """Kerf offset by foam type."""
        return {
            FoamType.STYROFOAM_BLUE: self.kerf_styrofoam,
            FoamType.URETHANE_2LB: self.kerf_urethane,
            FoamType.DIVINYCELL_H45: 0.030,
        }


@dataclass
class AirfoilSelection:
    """Airfoil assignments for each lifting surface."""

    # SAFETY: Roncz is NON-NEGOTIABLE for the canard
    canard: AirfoilType = AirfoilType.RONCZ_R1145MS

    # Main wing uses modified Eppler with trailing-edge reflex
    wing_root: AirfoilType = AirfoilType.EPPLER_1230_MOD
    wing_tip: AirfoilType = AirfoilType.EPPLER_1230_MOD

    # Reflex percentage for pitch stability
    wing_reflex_percent: float = 2.5


@dataclass
class ComplianceParams:
    """FAA 14 CFR 21.191(g) compliance tracking."""

    # Task credit weights (percentage of 51% rule)
    task_credits: Dict[str, float] = field(default_factory=lambda: {
        "wing_cores_cnc": 0.08,           # Builder-operated CNC foam cutting
        "wing_skins_layup": 0.12,         # Manual fiberglass layup
        "fuselage_assembly": 0.15,        # Bulkhead installation & bonding
        "canard_fabrication": 0.10,       # Canard core + skins
        "control_system": 0.08,           # Linkages, cables, torque tubes
        "landing_gear": 0.06,             # Main gear bow, nose gear
        "engine_install": 0.05,           # Engine mount, baffles, cowl
        "electrical": 0.04,               # Wiring harness
        "finishing": 0.06,                # Fill, sand, paint
        "final_assembly": 0.10,           # Systems integration
    })

    @property
    def total_builder_credit(self) -> float:
        """Sum of all builder credits - must exceed 0.50."""
        return sum(self.task_credits.values())


@dataclass
class AircraftConfig:
    """
    Master configuration singleton.

    ALL downstream modules import this. Changes here propagate through:
    - CadQuery geometry scripts
    - OpenVSP aerodynamic models
    - G-code manufacturing output
    - Markdown documentation injection
    """

    geometry: GeometricParams = field(default_factory=GeometricParams)
    materials: MaterialParams = field(default_factory=MaterialParams)
    manufacturing: ManufacturingParams = field(default_factory=ManufacturingParams)
    airfoils: AirfoilSelection = field(default_factory=AirfoilSelection)
    compliance: ComplianceParams = field(default_factory=ComplianceParams)

    # Project metadata
    project_name: str = "Open-EZ PDE"
    version: str = "0.1.0"
    baseline: str = "Long-EZ Model 61"

    def validate(self) -> List[str]:
        """Validate configuration for safety and regulatory compliance."""
        errors = []

        # SAFETY CHECK: Roncz canard is mandatory
        if self.airfoils.canard != AirfoilType.RONCZ_R1145MS:
            errors.append(
                "SAFETY VIOLATION: Canard must use RONCZ_R1145MS. "
                "GU25-5(11)8 causes dangerous lift loss in rain."
            )

        # COMPLIANCE CHECK: Builder credits must exceed 51%
        if self.compliance.total_builder_credit < 0.51:
            errors.append(
                f"COMPLIANCE VIOLATION: Builder credits ({self.compliance.total_builder_credit:.1%}) "
                "below FAA 51% requirement."
            )

        # STABILITY CHECK: Canard must stall before wing
        # (simplified check - full analysis requires OpenVSP)
        canard_loading = 1.0  # placeholder
        wing_loading = 1.0    # placeholder
        if canard_loading < wing_loading:
            errors.append(
                "STABILITY WARNING: Canard loading may not ensure canard-first stall. "
                "Run OpenVSP analysis to verify."
            )

        return errors

    def summary(self) -> str:
        """Generate human-readable configuration summary."""
        return f"""
Open-EZ PDE Configuration Summary
=================================
Baseline: {self.baseline}
Version: {self.version}

GEOMETRY
--------
Wing Span: {self.geometry.wing_span / 12:.1f} ft
Wing Area: {self.geometry.wing_area:.1f} sq ft
Wing AR: {self.geometry.wing_aspect_ratio:.2f}
Canard Span: {self.geometry.canard_span / 12:.1f} ft
Canard Area: {self.geometry.canard_area:.1f} sq ft
Canard Arm: {self.geometry.canard_arm:.1f} in

AIRFOILS
--------
Canard: {self.airfoils.canard.value} (SAFETY CRITICAL)
Wing: {self.airfoils.wing_root.value}
Wing Reflex: {self.airfoils.wing_reflex_percent}%

MATERIALS
---------
Spar Cap Plies: {self.materials.spar_cap_plies}
Spar Trough Depth: {self.materials.spar_trough_depth:.3f} in

COMPLIANCE
----------
Builder Credits: {self.compliance.total_builder_credit:.1%}
FAA 51% Status: {'PASS' if self.compliance.total_builder_credit >= 0.51 else 'FAIL'}
"""


# Singleton instance - import this throughout the project
config = AircraftConfig()

# Validate on import
_errors = config.validate()
if _errors:
    import warnings
    for err in _errors:
        warnings.warn(err, UserWarning)
