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
from typing import Dict, List, Optional, Tuple


class AirfoilType(Enum):
    """Supported airfoil profiles."""

    RONCZ_R1145MS = "roncz_r1145ms"  # MANDATORY canard airfoil (rain-safe)
    EPPLER_1230_MOD = "eppler_1230_mod"  # Main wing (with reflex)
    GU25_5_11_8 = "gu25_5_11_8"  # DEPRECATED - unsafe in rain


class FoamType(Enum):
    """Foam core materials with thermal properties for hot-wire cutting."""

    STYROFOAM_BLUE = "styrofoam_blue"  # 2 lb/ft³ - Standard wing cores
    URETHANE_2LB = "urethane_2lb"  # 2 lb/ft³ - Higher temp resistance
    DIVINYCELL_H45 = "divinycell_h45"  # Structural foam - fuselage


class BuildMethod(Enum):
    """Fuselage construction method."""

    BOW_FOAM = "bow_foam"  # Classic Rutan: flat slabs bowed into curves
    CNC_MILLED = "cnc_milled"  # Modern: 5-axis CNC milled foam blocks


class PropulsionType(Enum):
    """Powerplant options."""

    LYCOMING_O235 = "lycoming_o235"  # 115 HP gasoline (baseline)
    LYCOMING_O320 = "lycoming_o320"  # 150 HP gasoline (performance)
    ELECTRIC_LIFEPO4 = "electric_lifepo4"  # LiFePO4 battery electric
    ELECTRIC_NMC = "electric_nmc"  # NMC battery electric (higher density)


class GrainConstraint(Enum):
    """Material grain/fiber orientation constraints for nesting."""

    NONE = "none"  # No grain constraint
    PARALLEL = "parallel"  # Grain must align with primary load path
    PERPENDICULAR = "perpendicular"  # Grain perpendicular to load path
    SPECIFIC = "specific"  # Specific angle required (see grain_angle)


@dataclass
class Ply:
    """Single composite ply definition."""

    material: str
    orientation: float
    thickness: Optional[float] = None


@dataclass
class LaminateDefinition:
    """Stack of plies used for layups and manufacturing prep."""

    name: str
    plies: List[Ply] = field(default_factory=list)
    notes: str = ""

    def total_thickness(self, ply_lookup: Dict[str, float]) -> float:
        """Compute total laminate thickness using a ply thickness lookup."""
        thickness = 0.0
        for ply in self.plies:
            base = ply.thickness
            if base is None:
                base = ply_lookup.get(ply.material.lower(), 0.0)
            thickness += base
        return thickness

    def cut_order_steps(self) -> List[str]:
        """Describe recommended CAM steps for this laminate."""
        return ["engrave_labels", "pocket_features", "profile_cut"]


@dataclass
class GeometricParams:
    """Primary aircraft geometry - all dimensions in inches unless noted."""

    # === MAIN WING (Eppler 1230 Modified) ===
    wing_span: float = 316.8  # Total span (26.4 ft)
    wing_root_chord: float = 68.0  # Root chord at BL 23.3
    wing_tip_chord: float = 32.0  # Tip chord
    wing_sweep_le: float = 25.0  # Leading edge sweep (degrees)
    wing_dihedral: float = -4.5  # Negative = anhedral (degrees)
    wing_washout: float = 1.0  # Tip washout (degrees)
    wing_incidence: float = 0.0  # Relative to longerons (degrees)

    # === CANARD (Roncz R1145MS - SAFETY CRITICAL) ===
    canard_span: float = 147.0  # Total span (12.25 ft)
    canard_root_chord: float = 17.0  # Root chord
    canard_tip_chord: float = 13.5  # Tip chord
    canard_sweep_le: float = 13.5  # Leading edge sweep (degrees)
    canard_incidence: float = -1.5  # Relative to longerons (degrees)

    # === FUSELAGE STATIONS (FS) ===
    fs_nose: float = 0.0  # Nose reference
    fs_canard_le: float = 36.0  # Canard leading edge
    fs_pilot_seat: float = 80.0  # F-22 bulkhead (pilot)
    fs_rear_seat: float = 115.0  # F-28 bulkhead (passenger/baggage)
    fs_wing_le: float = 133.0  # Wing leading edge at root
    fs_firewall: float = 180.0  # Engine firewall (F-28)
    fs_tail: float = 214.0  # Tail cone terminus

    # === ERGONOMICS ===
    cockpit_width: float = 23.0  # F-22 interior width
    pilot_height_max: float = 77.0  # Max pilot height (inches)

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
        return (span_ft**2) / self.wing_area


@dataclass
class MaterialParams:
    """Composite layup and foam specifications."""

    # === FIBERGLASS PLY THICKNESSES (inches) ===
    bid_ply_thickness: float = 0.013  # Bi-directional cloth (per ply)
    uni_ply_thickness: float = 0.009  # Unidirectional tape (per ply)

    # === SPAR CAP LAYUP (Long-EZ specific) ===
    spar_cap_plies: int = 17  # UNI plies for main spar cap
    spar_cap_width: float = 3.0  # Spar cap width (inches)

    # === FOAM CORE ===
    wing_core_foam: FoamType = FoamType.STYROFOAM_BLUE
    fuselage_foam: FoamType = FoamType.URETHANE_2LB
    foam_core_thickness: float = 0.5  # PVC foam shell thickness

    # === LAMINATE SCHEDULES ===
    laminates: Dict[str, LaminateDefinition] = field(
        default_factory=lambda: {
            "wing_skin": LaminateDefinition(
                name="wing_skin",
                plies=[
                    Ply(material="bid", orientation=45.0),
                    Ply(material="bid", orientation=-45.0),
                    Ply(material="uni", orientation=0.0),
                    Ply(material="bid", orientation=45.0),
                ],
                notes="Baseline Long-EZ wing skin schedule",
            ),
            "canard_skin": LaminateDefinition(
                name="canard_skin",
                plies=[
                    Ply(material="bid", orientation=30.0),
                    Ply(material="bid", orientation=-30.0),
                    Ply(material="bid", orientation=45.0),
                ],
                notes="Roncz canard surface layup",
            ),
        }
    )

    @property
    def spar_trough_depth(self) -> float:
        """Spar cap trough depth = plies × thickness."""
        return self.spar_cap_plies * self.uni_ply_thickness

    @property
    def ply_thickness_lookup(self) -> Dict[str, float]:
        """Map laminate material names to nominal ply thickness."""
        return {
            "bid": self.bid_ply_thickness,
            "uni": self.uni_ply_thickness,
        }


@dataclass
class ManufacturingIntent:
    """Describes a manufacturing artifact and its expected fidelity."""

    artifact: str
    format: str
    tolerance: float
    description: str = ""


@dataclass
class ComponentManufacturingIntent:
    """Per-component manufacturing outputs for CAM and templates."""

    printable_jigs: ManufacturingIntent
    cnc_foam: ManufacturingIntent
    sheet_templates: ManufacturingIntent


@dataclass
class ManufacturingParams:
    """CNC and hot-wire cutting parameters."""

    # === HOT-WIRE CUTTING ===
    wire_diameter: float = 0.032  # NiChrome wire diameter (inches)
    wire_temp_styrofoam: float = 400  # Cutting temp for Styrofoam (°F)
    wire_temp_urethane: float = 500  # Cutting temp for urethane (°F)
    feed_rate_default: float = 4.0  # Default feed rate (in/min)

    # === KERF COMPENSATION ===
    kerf_styrofoam: float = 0.045  # Material removed (inches)
    kerf_urethane: float = 0.035  # Material removed (inches)

    # === NESTING / SHEET STOCK ===
    stock_sheets: List[Tuple[float, float]] = field(
        default_factory=lambda: [
            (24.0, 48.0),  # Typical foam block face
            (48.0, 96.0),  # Full plywood sheet
        ]
    )
    default_dogbone_radius: float = 0.0625
    default_fillet_radius: float = 0.125
    engraving_depth: float = 0.02

    # === FABRICATION INTENT ===
    component_intents: Dict[str, ComponentManufacturingIntent] = field(
        default_factory=lambda: {
            "wing": ComponentManufacturingIntent(
                printable_jigs=ManufacturingIntent(
                    artifact="wing_alignment_jig",
                    format="STL",
                    tolerance=0.01,
                    description="3D printed tip/rib fixtures to hold foam cores",
                ),
                cnc_foam=ManufacturingIntent(
                    artifact="wing_foam_core",
                    format="GCODE",
                    tolerance=0.02,
                    description="4-axis hot-wire toolpath with kerf offsets",
                ),
                sheet_templates=ManufacturingIntent(
                    artifact="wing_root_tip_templates",
                    format="DXF",
                    tolerance=0.01,
                    description="Laser or waterjet templates for foam blanks",
                ),
            ),
            "canard": ComponentManufacturingIntent(
                printable_jigs=ManufacturingIntent(
                    artifact="canard_alignment_jig",
                    format="STL",
                    tolerance=0.01,
                    description="Roncz canard washout and alignment fixtures",
                ),
                cnc_foam=ManufacturingIntent(
                    artifact="canard_foam_core",
                    format="GCODE",
                    tolerance=0.02,
                    description="Hot-wire toolpath honoring Roncz airfoil",
                ),
                sheet_templates=ManufacturingIntent(
                    artifact="canard_root_tip_templates",
                    format="DXF",
                    tolerance=0.01,
                    description="Templates for canard foam blocks",
                ),
            ),
            "bulkhead": ComponentManufacturingIntent(
                printable_jigs=ManufacturingIntent(
                    artifact="bulkhead_jig",
                    format="STL",
                    tolerance=0.01,
                    description="Bonding jigs to hold bulkheads square",
                ),
                cnc_foam=ManufacturingIntent(
                    artifact="bulkhead_blank",
                    format="DXF",
                    tolerance=0.02,
                    description="Router-ready outlines for foam or plywood blanks",
                ),
                sheet_templates=ManufacturingIntent(
                    artifact="bulkhead_templates",
                    format="DXF",
                    tolerance=0.01,
                    description="Full-size bulkhead profiles for tracing",
                ),
            ),
            "fuselage": ComponentManufacturingIntent(
                printable_jigs=ManufacturingIntent(
                    artifact="fuselage_assembly_jig",
                    format="STL",
                    tolerance=0.02,
                    description="3D printed pads/locators for longerons and bulkheads",
                ),
                cnc_foam=ManufacturingIntent(
                    artifact="fuselage_shell",
                    format="DXF",
                    tolerance=0.03,
                    description="Panel nest files for CNC-routed side and bottom panels",
                ),
                sheet_templates=ManufacturingIntent(
                    artifact="fuselage_panel_templates",
                    format="DXF",
                    tolerance=0.02,
                    description="Printable side/bottom templates for manual cutting",
                ),
            ),
        }
    )

    @property
    def kerf_compensation(self) -> Dict[FoamType, float]:
        """Kerf offset by foam type."""
        return {
            FoamType.STYROFOAM_BLUE: self.kerf_styrofoam,
            FoamType.URETHANE_2LB: self.kerf_urethane,
            FoamType.DIVINYCELL_H45: 0.030,
        }

    # === FUSELAGE BUILD SETTINGS ===
    fuselage_build_method: BuildMethod = BuildMethod.BOW_FOAM
    max_cnc_block_length: float = 48.0  # Max CNC machine width (inches)
    auto_segment_wings: bool = True  # Auto-segment wings for CNC

    # === STRONGBACK / JIG SETTINGS ===
    strongback_table_width: float = 36.0  # Work table width (inches)
    strongback_table_length: float = 240.0  # Work table length (inches)


@dataclass
class StrakeConfig:
    """Strake geometry for wing-fuselage integration."""

    # === GEOMETRY ===
    fs_leading_edge: float = 110.0  # Forward extent (FS inches)
    fs_trailing_edge: float = 145.0  # Blends into wing box
    inboard_width: float = 8.0  # At fuselage junction (inches)
    outboard_taper: float = 0.6  # Width reduction ratio at BL 23.3

    # === TANKAGE ===
    tank_volume_gal: float = 26.0  # Per side (fuel mode)
    baffle_spacing: float = 6.0  # Anti-slosh baffle spacing (inches)

    # === E-Z BATTERY CONVERSION ===
    battery_cell_pitch: float = 2.625  # LiFePO4 prismatic spacing (inches)
    battery_module_count: int = 8  # Modules per strake (16 total)
    battery_cell_capacity_ah: float = 100.0  # Cell capacity
    battery_cells_series: int = 16  # 16S = 48V nominal
    battery_cells_parallel: int = 4  # 4P for capacity


@dataclass
class PropulsionConfig:
    """Powerplant configuration for CG and firewall generation."""

    propulsion_type: PropulsionType = PropulsionType.LYCOMING_O235

    # === IC ENGINE DEFAULTS (O-235) ===
    engine_mass_kg: float = 113.0  # 250 lb dry
    engine_cg_arm_in: float = 8.0  # Forward of firewall
    fuel_capacity_gal: float = 52.0  # Total fuel (26 gal per strake)
    fuel_consumption_gph: float = 6.5  # Cruise consumption

    # === ELECTRIC DEFAULTS (LiFePO4) ===
    motor_mass_kg: float = 35.0  # EMRAX 228 MV
    motor_power_kw: float = 100.0  # 134 hp continuous
    battery_capacity_kwh: float = 25.6  # 16S4P configuration
    battery_voltage_v: float = 51.2  # 16S nominal

    @property
    def is_electric(self) -> bool:
        """Check if propulsion is electric."""
        return self.propulsion_type in (
            PropulsionType.ELECTRIC_LIFEPO4,
            PropulsionType.ELECTRIC_NMC,
        )

    @property
    def battery_energy_density_wh_kg(self) -> float:
        """Energy density based on battery chemistry."""
        if self.propulsion_type == PropulsionType.ELECTRIC_LIFEPO4:
            return 150.0  # LiFePO4
        elif self.propulsion_type == PropulsionType.ELECTRIC_NMC:
            return 250.0  # NMC
        return 0.0

    @property
    def battery_mass_kg(self) -> float:
        """Computed battery mass from capacity and density."""
        if not self.is_electric:
            return 0.0
        return (self.battery_capacity_kwh * 1000) / self.battery_energy_density_wh_kg


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
    task_credits: Dict[str, float] = field(
        default_factory=lambda: {
            "wing_cores_cnc": 0.08,  # Builder-operated CNC foam cutting
            "wing_skins_layup": 0.12,  # Manual fiberglass layup
            "fuselage_assembly": 0.15,  # Bulkhead installation & bonding
            "canard_fabrication": 0.10,  # Canard core + skins
            "control_system": 0.08,  # Linkages, cables, torque tubes
            "landing_gear": 0.06,  # Main gear bow, nose gear
            "engine_install": 0.05,  # Engine mount, baffles, cowl
            "electrical": 0.04,  # Wiring harness
            "finishing": 0.06,  # Fill, sand, paint
            "final_assembly": 0.10,  # Systems integration
        }
    )

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
    strakes: StrakeConfig = field(default_factory=StrakeConfig)
    propulsion: PropulsionConfig = field(default_factory=PropulsionConfig)

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
        wing_loading = 1.0  # placeholder
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
FAA 51% Status: {"PASS" if self.compliance.total_builder_credit >= 0.51 else "FAIL"}
"""


# Singleton instance - import this throughout the project
config = AircraftConfig()

# Validate on import
_errors = config.validate()
if _errors:
    import warnings

    for err in _errors:
        warnings.warn(err, UserWarning)
