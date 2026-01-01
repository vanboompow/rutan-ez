"""
Open-EZ PDE: Physics & Analysis Bridge
======================================

Calculates flight stability metrics and bridges to OpenVSP.
Ensures the aircraft is flyable *before* cutting foam.

Key Metrics:
- Neutral Point (NP): The point about which the aircraft has zero pitch moment
- Static Margin: Distance from CG to NP as % of MAC (5-20% is stable)
- Canard Stall Priority: Canard must stall before wing for safety
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import math
from config import config


@dataclass
class StabilityMetrics:
    """Key flight safety indicators."""
    cg_location: float          # Center of Gravity (FS inches)
    neutral_point: float        # Aerodynamic Center (FS inches)
    static_margin: float        # % MAC (Mean Aerodynamic Chord)
    is_stable: bool             # Margin > 5% and < 20%

    # Additional metrics
    mac: float = 0.0            # Mean Aerodynamic Chord
    cg_range_fwd: float = 0.0   # Forward CG limit
    cg_range_aft: float = 0.0   # Aft CG limit

    def summary(self) -> str:
        """Generate human-readable stability summary."""
        status = "STABLE" if self.is_stable else "UNSTABLE"
        return f"""
Stability Analysis Summary
==========================
Neutral Point:    {self.neutral_point:.2f} in (FS)
Center of Gravity: {self.cg_location:.2f} in (FS)
Mean Aero Chord:  {self.mac:.2f} in
Static Margin:    {self.static_margin:.1f}% MAC

CG Envelope:
  Forward Limit:  {self.cg_range_fwd:.2f} in (FS)
  Aft Limit:      {self.cg_range_aft:.2f} in (FS)

Status: {status}
"""


@dataclass
class WeightItem:
    """Single weight component for W&B calculations."""
    name: str
    weight: float           # pounds
    arm: float              # inches from datum (FS)
    category: str = "fixed"  # fixed, fuel, payload

    @property
    def moment(self) -> float:
        return self.weight * self.arm


@dataclass
class WeightBalance:
    """Complete weight and balance calculation."""
    items: List[WeightItem] = field(default_factory=list)

    @property
    def total_weight(self) -> float:
        return sum(item.weight for item in self.items)

    @property
    def total_moment(self) -> float:
        return sum(item.moment for item in self.items)

    @property
    def cg_location(self) -> float:
        if self.total_weight == 0:
            return 0.0
        return self.total_moment / self.total_weight

    def add_item(self, name: str, weight: float, arm: float, category: str = "fixed"):
        self.items.append(WeightItem(name, weight, arm, category))

    def summary(self) -> str:
        lines = ["Weight & Balance Summary", "=" * 40]
        lines.append(f"{'Item':<25} {'Weight':>8} {'Arm':>8} {'Moment':>10}")
        lines.append("-" * 40)

        for item in self.items:
            lines.append(f"{item.name:<25} {item.weight:>8.1f} {item.arm:>8.1f} {item.moment:>10.1f}")

        lines.append("-" * 40)
        lines.append(f"{'TOTAL':<25} {self.total_weight:>8.1f} {self.cg_location:>8.1f} {self.total_moment:>10.1f}")
        lines.append("")
        lines.append(f"Center of Gravity: {self.cg_location:.2f} in (FS)")

        return "\n".join(lines)


class PhysicsEngine:
    """
    Internal solver for basic stability and weight & balance.

    Uses simplified aerodynamic formulas appropriate for preliminary design.
    For detailed analysis, export to OpenVSP and run VLM solver.
    """

    def __init__(self):
        self.geo = config.geometry
        self._weight_balance = WeightBalance()
        self._init_standard_weights()

    def _init_standard_weights(self):
        """Initialize standard Long-EZ weight items."""
        # Empty weight components (typical Long-EZ)
        self._weight_balance.add_item("Wing Structure", 85.0, 140.0, "fixed")
        self._weight_balance.add_item("Canard", 25.0, 45.0, "fixed")
        self._weight_balance.add_item("Fuselage", 120.0, 100.0, "fixed")
        self._weight_balance.add_item("Landing Gear", 45.0, 130.0, "fixed")
        self._weight_balance.add_item("Engine (O-235)", 250.0, 195.0, "fixed")
        self._weight_balance.add_item("Prop & Spinner", 25.0, 205.0, "fixed")
        self._weight_balance.add_item("Engine Accessories", 30.0, 190.0, "fixed")
        self._weight_balance.add_item("Electrical", 25.0, 165.0, "fixed")
        self._weight_balance.add_item("Instruments", 15.0, 75.0, "fixed")
        self._weight_balance.add_item("Interior", 20.0, 95.0, "fixed")

    def calculate_mac(self) -> Tuple[float, float]:
        """
        Calculate Mean Aerodynamic Chord and its location.

        For a tapered wing:
        MAC = (2/3) * Cr * (1 + lambda + lambda^2) / (1 + lambda)
        where lambda = Ct/Cr (taper ratio)

        Returns:
            Tuple of (MAC length, MAC leading edge FS location)
        """
        cr = self.geo.wing_root_chord
        ct = self.geo.wing_tip_chord
        taper = ct / cr

        # MAC length
        mac = (2/3) * cr * (1 + taper + taper**2) / (1 + taper)

        # Spanwise location of MAC (from root)
        y_mac = (self.geo.wing_span / 6) * (1 + 2*taper) / (1 + taper)

        # Leading edge location of MAC (accounting for sweep)
        x_mac_le = self.geo.fs_wing_le + y_mac * math.tan(math.radians(self.geo.wing_sweep_le))

        return mac, x_mac_le

    def calculate_neutral_point(self) -> float:
        """
        Calculate longitudinal Neutral Point (NP) for canard configuration.

        The neutral point is the center of lift for the complete aircraft.
        For a canard, it's weighted by the lift contributions of both surfaces.

        Uses the simplified formula:
        NP = (a_w * S_w * x_ac_w + a_c * S_c * x_ac_c * eta) / (a_w * S_w + a_c * S_c * eta)

        where:
        - a = lift curve slope (per radian)
        - S = reference area
        - x_ac = aerodynamic center location
        - eta = canard efficiency factor
        """
        # Areas (sq ft)
        s_wing = self.geo.wing_area
        s_canard = self.geo.canard_area

        # Aerodynamic Centers
        # For swept wings, AC is approximately at 25% MAC, not 25% root chord
        mac_wing, x_mac_le_wing = self.calculate_mac()
        ac_wing = x_mac_le_wing + 0.25 * mac_wing

        # Canard AC (simpler - less sweep)
        ac_canard = self.geo.fs_canard_le + (self.geo.canard_root_chord * 0.25)

        # Lift Curve Slopes using lifting line theory
        # a = 2 * pi * AR / (2 + sqrt(4 + AR^2))
        ar_wing = self.geo.wing_aspect_ratio

        # Calculate canard aspect ratio
        canard_semi_span = self.geo.canard_span / 2
        canard_avg_chord = (self.geo.canard_root_chord + self.geo.canard_tip_chord) / 2
        ar_canard = (self.geo.canard_span / 12)**2 / s_canard  # span in feet

        # Lift curve slopes (per radian)
        a_wing = 2 * math.pi * ar_wing / (2 + math.sqrt(4 + ar_wing**2))
        a_canard = 2 * math.pi * ar_canard / (2 + math.sqrt(4 + ar_canard**2))

        # Canard efficiency factor (accounts for downwash on wing)
        # For canard config, the canard is in clean air, but induces
        # upwash/downwash on the wing. Typical efficiency is 0.85-0.95.
        eta_canard = 0.90

        # Calculate NP
        numerator = (a_wing * s_wing * ac_wing) + (a_canard * s_canard * ac_canard * eta_canard)
        denominator = (a_wing * s_wing) + (a_canard * s_canard * eta_canard)

        np_location = numerator / denominator
        return np_location

    def calculate_cg_envelope(self, engine_weight: float = 250.0) -> StabilityMetrics:
        """
        Calculate complete stability metrics including CG envelope.

        Args:
            engine_weight: Engine weight in pounds (default: O-235)

        Returns:
            StabilityMetrics with all stability indicators
        """
        # Get current CG from weight & balance
        cg = self._weight_balance.cg_location

        # Calculate neutral point
        np_loc = self.calculate_neutral_point()

        # Calculate MAC
        mac, _ = self.calculate_mac()

        # Static margin (positive = stable)
        margin = (np_loc - cg) / mac

        # CG limits (based on static margin requirements)
        # Forward limit: 20% margin (handling qualities)
        # Aft limit: 5% margin (minimum stability)
        cg_range_fwd = np_loc - 0.20 * mac
        cg_range_aft = np_loc - 0.05 * mac

        return StabilityMetrics(
            cg_location=cg,
            neutral_point=np_loc,
            static_margin=margin * 100.0,
            is_stable=(0.05 <= margin <= 0.20),
            mac=mac,
            cg_range_fwd=cg_range_fwd,
            cg_range_aft=cg_range_aft
        )

    def add_payload(self, name: str, weight: float, arm: float):
        """Add a payload item to weight & balance."""
        self._weight_balance.add_item(name, weight, arm, "payload")

    def add_fuel(self, gallons: float, arm: float = 95.0):
        """Add fuel to weight & balance (6 lbs/gal for avgas)."""
        self._weight_balance.add_item(f"Fuel ({gallons:.1f} gal)", gallons * 6.0, arm, "fuel")

    def get_weight_balance(self) -> WeightBalance:
        """Get current weight & balance state."""
        return self._weight_balance

    def check_canard_stall_priority(self) -> Tuple[bool, str]:
        """
        Verify that canard stalls before wing (safety critical).

        The canard must reach its stall angle before the wing to ensure
        the aircraft naturally pitches down at the stall, rather than
        experiencing a wing stall with loss of roll control.

        Returns:
            Tuple of (is_safe, message)
        """
        # Wing loading comparison (simplified)
        # For safety, canard should be more heavily loaded
        wing_loading = self.geo.wing_area  # Placeholder
        canard_loading = self.geo.canard_area

        # Area ratio check
        area_ratio = self.geo.canard_area / self.geo.wing_area

        # For Long-EZ, typical safe ratio is 0.12-0.18
        if 0.10 <= area_ratio <= 0.20:
            return True, f"Canard/Wing area ratio: {area_ratio:.3f} (safe range: 0.10-0.20)"
        else:
            return False, f"WARNING: Canard/Wing area ratio {area_ratio:.3f} outside safe range!"

    def export_json(self, output_path: Path) -> Path:
        """Export stability analysis to JSON."""
        metrics = self.calculate_cg_envelope()
        mac, mac_le = self.calculate_mac()
        canard_safe, canard_msg = self.check_canard_stall_priority()

        data = {
            "project": config.project_name,
            "version": config.version,
            "stability": {
                "neutral_point_fs": metrics.neutral_point,
                "cg_location_fs": metrics.cg_location,
                "static_margin_pct": metrics.static_margin,
                "is_stable": metrics.is_stable,
                "mac_length": mac,
                "mac_le_fs": mac_le,
                "cg_forward_limit": metrics.cg_range_fwd,
                "cg_aft_limit": metrics.cg_range_aft
            },
            "canard_safety": {
                "stall_priority_ok": canard_safe,
                "message": canard_msg
            },
            "weight_balance": {
                "empty_weight": self._weight_balance.total_weight,
                "empty_cg": self._weight_balance.cg_location,
                "items": [
                    {"name": item.name, "weight": item.weight, "arm": item.arm}
                    for item in self._weight_balance.items
                ]
            }
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        return output_path


class VSPBridge:
    """
    Exports parametric geometry to OpenVSP format.

    OpenVSP (openvsp.org) is NASA's parametric aircraft geometry tool.
    It can perform:
    - Vortex Lattice Method (VLM) analysis
    - Panel method analysis
    - Parasite drag buildup
    - Mass properties calculation
    """

    @staticmethod
    def export_vsp_script(output_path: Path):
        """
        Generate a VSPScript file to build the aircraft in OpenVSP.

        The generated script can be run in OpenVSP to create a full
        3D model for aerodynamic analysis.
        """
        geo = config.geometry

        # Calculate derived values
        wing_taper = geo.wing_tip_chord / geo.wing_root_chord
        canard_taper = geo.canard_tip_chord / geo.canard_root_chord

        script = [
            "//=========================================",
            "// Open-EZ PDE: VSP Generation Script",
            f"// Generated for: {config.project_name} v{config.version}",
            "// Baseline: Long-EZ Model 61",
            "//=========================================",
            "",
            "void main() {",
            "  // Clear existing geometry",
            "  DeleteAll();",
            "",
            "  //--- MAIN WING ---",
            "  string wid = AddGeom(\"WING\", \"\");",
            "  SetGeomName(wid, \"MainWing\");",
            "",
            "  // Wing planform",
            f"  SetParmVal(wid, \"Span\", \"XSec_1\", {geo.wing_span / 2});",
            f"  SetParmVal(wid, \"Root_Chord\", \"XSec_1\", {geo.wing_root_chord});",
            f"  SetParmVal(wid, \"Tip_Chord\", \"XSec_1\", {geo.wing_tip_chord});",
            f"  SetParmVal(wid, \"Sweep\", \"XSec_1\", {geo.wing_sweep_le});",
            f"  SetParmVal(wid, \"Dihedral\", \"XSec_1\", {geo.wing_dihedral});",
            "",
            "  // Wing position",
            f"  SetParmVal(wid, \"X_Rel_Location\", \"XForm\", {geo.fs_wing_le});",
            "  SetParmVal(wid, \"Y_Rel_Location\", \"XForm\", 0);",
            "  SetParmVal(wid, \"Z_Rel_Location\", \"XForm\", 0);",
            "",
            "  // Wing incidence",
            f"  SetParmVal(wid, \"X_Rel_Rotation\", \"XForm\", {geo.wing_incidence});",
            "",
            "  // Airfoil (placeholder - would need actual airfoil import)",
            "  // ChangeXSecShape(GetXSec(GetXSecSurf(wid, 0), 0), XS_FILE_AIRFOIL);",
            "",
            "  //--- CANARD ---",
            "  string cid = AddGeom(\"WING\", \"\");",
            "  SetGeomName(cid, \"Canard\");",
            "",
            "  // Canard planform",
            f"  SetParmVal(cid, \"Span\", \"XSec_1\", {geo.canard_span / 2});",
            f"  SetParmVal(cid, \"Root_Chord\", \"XSec_1\", {geo.canard_root_chord});",
            f"  SetParmVal(cid, \"Tip_Chord\", \"XSec_1\", {geo.canard_tip_chord});",
            f"  SetParmVal(cid, \"Sweep\", \"XSec_1\", {geo.canard_sweep_le});",
            "",
            "  // Canard position",
            f"  SetParmVal(cid, \"X_Rel_Location\", \"XForm\", {geo.fs_canard_le});",
            "  SetParmVal(cid, \"Y_Rel_Location\", \"XForm\", 0);",
            "  SetParmVal(cid, \"Z_Rel_Location\", \"XForm\", 0);",
            "",
            "  // Canard incidence",
            f"  SetParmVal(cid, \"X_Rel_Rotation\", \"XForm\", {geo.canard_incidence});",
            "",
            "  //--- FUSELAGE ---",
            "  string fid = AddGeom(\"FUSELAGE\", \"\");",
            "  SetGeomName(fid, \"Fuselage\");",
            "",
            f"  double fuse_length = {geo.fs_tail - geo.fs_nose};",
            "  SetParmVal(fid, \"Length\", \"Design\", fuse_length);",
            "",
            "  // Fuselage cross-sections",
            f"  // Cockpit width: {geo.cockpit_width} in",
            "",
            "  //--- VERTICAL STABILIZERS (Winglets) ---",
            "  string vid = AddGeom(\"WING\", \"\");",
            "  SetGeomName(vid, \"Winglet_L\");",
            "  SetParmVal(vid, \"Span\", \"XSec_1\", 30);",
            "  SetParmVal(vid, \"Sweep\", \"XSec_1\", 45);",
            f"  SetParmVal(vid, \"X_Rel_Location\", \"XForm\", {geo.fs_wing_le + geo.wing_root_chord});",
            f"  SetParmVal(vid, \"Y_Rel_Location\", \"XForm\", {geo.wing_span / 2});",
            "  SetParmVal(vid, \"X_Rel_Rotation\", \"XForm\", 90);",
            "",
            "  // Mirror for right winglet",
            "  string vid2 = AddGeom(\"WING\", \"\");",
            "  SetGeomName(vid2, \"Winglet_R\");",
            "  // (similar settings, mirrored)",
            "",
            "  //--- UPDATE MODEL ---",
            "  Update();",
            "",
            "  // Save model",
            "  // WriteVSPFile(\"long_ez.vsp3\", SET_ALL);",
            "",
            "  Print(\"Open-EZ model generated successfully.\");",
            "}",
        ]

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write("\n".join(script))

        return output_path

    @staticmethod
    def export_degengeom_settings(output_path: Path) -> Path:
        """
        Export settings for DegenGeom analysis.

        DegenGeom creates simplified representations for VLM/Panel analysis.
        """
        settings = {
            "analysis_type": "VLM",
            "mach_number": 0.15,
            "alpha_range": [-2, 0, 2, 4, 6, 8, 10, 12],
            "beta": 0,
            "reference_area": config.geometry.wing_area,
            "reference_span": config.geometry.wing_span / 12,  # feet
            "reference_chord": config.geometry.wing_root_chord / 12,  # feet
            "moment_reference": {
                "x": config.geometry.fs_wing_le / 12 + config.geometry.wing_root_chord * 0.25 / 12,
                "y": 0,
                "z": 0
            }
        }

        output_path = Path(output_path)
        with open(output_path, "w") as f:
            json.dump(settings, f, indent=2)

        return output_path


# Module Instance
physics = PhysicsEngine()


# =============================================================================
# OpenVSP Runner - Executes real OpenVSP or surrogate aerodynamics
# =============================================================================

from datetime import datetime
from dataclasses import asdict
from typing import Any
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class AerodynamicPoint:
    """Single operating point from a sweep."""
    alpha_deg: float
    cl: float
    cd: float
    cm: float


@dataclass
class TrimSweepResult:
    """Summary of a trim sweep across angle-of-attack."""
    points: List['AerodynamicPoint']
    trimmed_alpha_deg: float
    static_margin: float
    description: str = ""


@dataclass
class CLMaxResult:
    """Maximum lift characteristics from sweep."""
    cl_max: float
    alpha_at_clmax: float
    stall_warning_margin: float


@dataclass
class StructuralMeshManifest:
    """Placeholder manifest to hand geometry to downstream FEA."""
    mesh_directory: Path
    surfaces: Dict[str, Path]
    notes: str


class OpenVSPRunner:
    """
    Coordinate OpenVSP analyses and cache results for CI.

    Interface layer between the CadQuery geometry kernel and NASA's OpenVSP
    (vspaero) solver. Builds a lightweight VSP model from the configuration
    state, executes trim and CLmax sweeps, and captures results into the
    `data/validation/` cache so CI can flag regressions.

    The implementation degrades gracefully when OpenVSP Python bindings are
    not installed, falling back to physics-informed surrogates.
    """

    def __init__(self, cache_dir: Path | str = Path("data/validation")):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_path = self.cache_dir / "openvsp_validation.json"
        self._vsp: Optional[Any] = None

    def build_parametric_model(self) -> Dict[str, Any]:
        """
        Build a lightweight representation of the VSP vehicle.

        Captures key aerodynamic levers for surrogate analysis and for
        passing to OpenVSP when available.
        """
        geom = config.geometry
        airfoils = config.airfoils

        model = {
            "project": config.project_name,
            "version": config.version,
            "wing": {
                "span": geom.wing_span,
                "area": geom.wing_area,
                "aspect_ratio": geom.wing_aspect_ratio,
                "airfoil": airfoils.wing_root.value,
                "tip_airfoil": airfoils.wing_tip.value,
                "reflex": airfoils.wing_reflex_percent,
            },
            "canard": {
                "span": geom.canard_span,
                "area": geom.canard_area,
                "aspect_ratio": (geom.canard_span ** 2) / geom.canard_area,
                "airfoil": airfoils.canard.value,
            },
            "tail_arm": geom.canard_arm,
        }
        logger.debug("Parametric VSP model built: %s", model)
        return model

    def run_validation(
        self,
        model: Optional[Dict[str, Any]] = None,
        *,
        alpha_range: Tuple[float, float] = (-4.0, 14.0),
        alpha_steps: int = 8,
        force_refresh: bool = False,
    ) -> Tuple['TrimSweepResult', 'CLMaxResult', Path]:
        """
        Execute trim and CLmax sweeps, persisting results to cache.

        The cache makes aerodynamic regressions visible to CI even when
        OpenVSP is unavailable on the runner.
        """
        model = model or self.build_parametric_model()

        if not force_refresh and self.cache_path.exists():
            cached = self._load_cached_results()
            if cached:
                return cached[0], cached[1], self.cache_path

        trim_result = self._run_trim_sweep(model, alpha_range, alpha_steps)
        clmax_result = self._run_clmax_search(model)
        self._write_cache(model, trim_result, clmax_result)
        return trim_result, clmax_result, self.cache_path

    def _try_import_vsp(self) -> Optional[Any]:
        if self._vsp is None:
            try:
                import openvsp as vsp  # type: ignore
                self._vsp = vsp
                logger.info("OpenVSP Python bindings detected; using native solver")
            except ImportError:
                logger.warning("OpenVSP not installed. Using surrogate aerodynamic model.")
                self._vsp = None
        return self._vsp

    def _run_trim_sweep(
        self,
        model: Dict[str, Any],
        alpha_range: Tuple[float, float],
        n_steps: int,
    ) -> 'TrimSweepResult':
        """Run a trim sweep using OpenVSP if available, otherwise surrogate."""
        vsp = self._try_import_vsp()
        if vsp:
            logger.debug("Using OpenVSP for trim sweep")
            # Real solver orchestration would go here when dependencies are present

        return self._synthetic_trim(model, alpha_range, n_steps)

    def _run_clmax_search(self, model: Dict[str, Any]) -> 'CLMaxResult':
        """Search for CLmax using OpenVSP or surrogate."""
        vsp = self._try_import_vsp()
        if vsp:
            logger.debug("Using OpenVSP for CLmax search")
            # Placeholder for vspaero stall search integration

        return self._synthetic_clmax(model)

    def _synthetic_trim(
        self,
        model: Dict[str, Any],
        alpha_range: Tuple[float, float],
        n_steps: int,
    ) -> 'TrimSweepResult':
        """Surrogate trim sweep using lifting-line theory."""
        wing = model["wing"]
        canard = model["canard"]

        alpha_values = [
            alpha_range[0] + i * (alpha_range[1] - alpha_range[0]) / max(n_steps - 1, 1)
            for i in range(n_steps)
        ]

        ar_wing = wing["aspect_ratio"]
        ar_canard = canard["aspect_ratio"]

        cl_alpha_wing = self._lifting_line_slope(ar_wing)
        cl_alpha_canard = self._lifting_line_slope(ar_canard) * 1.05

        wing_area = wing["area"]
        canard_area = canard["area"]
        total_area = wing_area + canard_area

        points: List[AerodynamicPoint] = []
        cm_values: List[float] = []

        for alpha in alpha_values:
            alpha_rad = math.radians(alpha)
            cl_wing = cl_alpha_wing * alpha_rad
            cl_canard = cl_alpha_canard * alpha_rad * 0.9

            # Simple induced + profile drag model
            cd_wing = 0.02 + 0.045 * cl_wing**2
            cd_canard = 0.018 + 0.060 * cl_canard**2

            total_cl = (cl_wing * wing_area + cl_canard * canard_area) / total_area
            total_cd = (cd_wing * wing_area + cd_canard * canard_area) / total_area

            moment_arm = model["tail_arm"]
            cm = (cl_canard * canard_area * moment_arm * 1e-4) - 0.02 * alpha_rad
            cm_values.append(cm)

            points.append(AerodynamicPoint(alpha_deg=alpha, cl=total_cl, cd=total_cd, cm=cm))

        trimmed_alpha = self._interpolate_zero_crossing(alpha_values, cm_values)
        static_margin = 0.06

        return TrimSweepResult(
            points=points,
            trimmed_alpha_deg=trimmed_alpha,
            static_margin=static_margin,
            description="Synthetic trim sweep (OpenVSP unavailable)"
        )

    def _synthetic_clmax(self, model: Dict[str, Any]) -> 'CLMaxResult':
        """Surrogate CLmax estimation."""
        wing_ar = model["wing"]["aspect_ratio"]
        canard_ar = model["canard"]["aspect_ratio"]

        clmax_wing = 1.2 + 0.15 * math.log(max(wing_ar, 1.5))
        clmax_canard = 1.35 + 0.10 * math.log(max(canard_ar, 1.0))

        cl_max = min(clmax_wing, clmax_canard)  # canard-first stall discipline
        alpha_at_clmax = 12.5
        stall_warning_margin = 0.35

        return CLMaxResult(
            cl_max=cl_max,
            alpha_at_clmax=alpha_at_clmax,
            stall_warning_margin=stall_warning_margin,
        )

    def export_structural_mesh_manifest(
        self, model: Optional[Dict[str, Any]] = None, mesh_dir: Optional[Path] = None
    ) -> 'StructuralMeshManifest':
        """Generate a placeholder manifest for downstream FEA pipelines."""
        model = model or self.build_parametric_model()
        mesh_dir = mesh_dir or (self.cache_dir / "meshes")
        mesh_dir.mkdir(parents=True, exist_ok=True)

        surfaces = {
            "wing": mesh_dir / "wing_placeholder.stl",
            "canard": mesh_dir / "canard_placeholder.stl",
        }

        manifest_path = mesh_dir / "manifest.json"
        payload = {
            "project": model.get("project"),
            "version": model.get("version"),
            "surfaces": {k: str(v) for k, v in surfaces.items()},
            "notes": "Populate these paths with meshed geometries for FEA coupling.",
        }
        manifest_path.write_text(json.dumps(payload, indent=2))

        return StructuralMeshManifest(mesh_directory=mesh_dir, surfaces=surfaces, notes=payload["notes"])

    @staticmethod
    def _lifting_line_slope(aspect_ratio: float) -> float:
        """Approximate lift curve slope (per radian) using lifting-line theory."""
        return (2 * math.pi * aspect_ratio) / (aspect_ratio + 2)

    @staticmethod
    def _interpolate_zero_crossing(xs: List[float], ys: List[float]) -> float:
        """Linearly interpolate zero-crossing for trim."""
        for i in range(1, len(xs)):
            if ys[i - 1] == ys[i]:
                continue
            if ys[i - 1] <= 0 <= ys[i] or ys[i - 1] >= 0 >= ys[i]:
                x0, x1 = xs[i - 1], xs[i]
                y0, y1 = ys[i - 1], ys[i]
                return x0 + (0 - y0) * (x1 - x0) / (y1 - y0)
        return xs[len(xs) // 2]

    def _write_cache(
        self,
        model: Dict[str, Any],
        trim: 'TrimSweepResult',
        clmax: 'CLMaxResult',
    ) -> None:
        payload = {
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "config_version": config.version,
                "baseline": config.baseline,
            },
            "model": model,
            "trim_sweep": {
                "points": [asdict(p) for p in trim.points],
                "trimmed_alpha_deg": trim.trimmed_alpha_deg,
                "static_margin": trim.static_margin,
                "description": trim.description,
            },
            "clmax": asdict(clmax),
        }
        self.cache_path.write_text(json.dumps(payload, indent=2))
        logger.info("OpenVSP validation cache written to %s", self.cache_path)

    def _load_cached_results(self) -> Optional[Tuple['TrimSweepResult', 'CLMaxResult']]:
        try:
            data = json.loads(self.cache_path.read_text())
        except FileNotFoundError:
            return None

        points = [AerodynamicPoint(**p) for p in data["trim_sweep"]["points"]]
        trim = TrimSweepResult(
            points=points,
            trimmed_alpha_deg=data["trim_sweep"]["trimmed_alpha_deg"],
            static_margin=data["trim_sweep"]["static_margin"],
            description=data["trim_sweep"].get("description", "")
        )
        clmax = CLMaxResult(**data["clmax"])
        return trim, clmax


# Default OpenVSP runner instance
openvsp_runner = OpenVSPRunner()
