"""
Open-EZ PDE: Physics & Analysis Bridge
======================================

Calculates flight stability metrics and bridges to OpenVSP.
Ensures the aircraft is flyable *before* cutting foam.

Key Metrics:
- Neutral Point (NP): The point about which the aircraft has zero pitch moment
- Static Margin: Distance from CG to NP as % of MAC (5-20% is stable)
- Canard Stall Priority: Canard must stall before wing for safety

Module layout
-------------
- StabilityMetrics    – dataclass of key stability indicators
- PhysicsEngine       – internal solver for stability and W&B
- VSPBridge           – exports parametric geometry to OpenVSP format

Weight & Balance types have been extracted to core.weight_balance.
OpenVSP runner types have been extracted to core.openvsp_runner.
Both are re-exported here for backward compatibility so that existing
``from core.analysis import WeightItem, WeightBalance, OpenVSPRunner`` calls
continue to work unchanged.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple
import json
import math

from config import config

# ---------------------------------------------------------------------------
# Re-exports for backward compatibility
# ---------------------------------------------------------------------------
from .weight_balance import WeightBalance, WeightItem  # noqa: F401
from .openvsp_runner import (  # noqa: F401
    AerodynamicPoint,
    CLMaxResult,
    OpenVSPRunner,
    StructuralMeshManifest,
    TrimSweepResult,
    openvsp_runner,
)


@dataclass
class StabilityMetrics:
    """Key flight safety indicators."""

    cg_location: float  # Center of Gravity (FS inches)
    neutral_point: float  # Aerodynamic Center (FS inches)
    static_margin: float  # % MAC (Mean Aerodynamic Chord)
    is_stable: bool  # Margin > 5% and < 20%

    # Additional metrics
    mac: float = 0.0  # Mean Aerodynamic Chord
    cg_range_fwd: float = 0.0  # Forward CG limit
    cg_range_aft: float = 0.0  # Aft CG limit

    def summary(self) -> str:
        """Generate human-readable stability summary."""
        geo = config.geometry
        status = "STABLE" if self.is_stable else "UNSTABLE"
        return f"""
Stability Analysis Summary
==========================
Neutral Point:    FS {self.neutral_point:.2f} (internal) / FS {geo.to_published_datum(self.neutral_point):.2f} (published)
Center of Gravity: FS {self.cg_location:.2f} (internal) / FS {geo.to_published_datum(self.cg_location):.2f} (published)
Mean Aero Chord:  {self.mac:.2f} in
Static Margin:    {self.static_margin:.1f}% MAC

CG Envelope:
  Forward Limit:  FS {self.cg_range_fwd:.2f} (internal) / FS {geo.to_published_datum(self.cg_range_fwd):.2f} (published)
  Aft Limit:      FS {self.cg_range_aft:.2f} (internal) / FS {geo.to_published_datum(self.cg_range_aft):.2f} (published)

Status: {status}
"""


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
        """Initialize weight items from SSOT config and propulsion factory."""
        sw = config.structural_weights

        # Structural weights from config
        self._weight_balance.add_item(
            "Wing Structure", sw.wing_weight_lb, sw.wing_arm_in, "fixed"
        )
        self._weight_balance.add_item(
            "Canard", sw.canard_weight_lb, sw.canard_arm_in, "fixed"
        )
        self._weight_balance.add_item(
            "Fuselage", sw.fuselage_weight_lb, sw.fuselage_arm_in, "fixed"
        )
        self._weight_balance.add_item(
            "Landing Gear", sw.landing_gear_weight_lb, sw.landing_gear_arm_in, "fixed"
        )
        self._weight_balance.add_item(
            "Electrical", sw.electrical_weight_lb, sw.electrical_arm_in, "fixed"
        )
        self._weight_balance.add_item(
            "Instruments", sw.instruments_weight_lb, sw.instruments_arm_in, "fixed"
        )
        self._weight_balance.add_item(
            "Interior", sw.interior_weight_lb, sw.interior_arm_in, "fixed"
        )

        # Propulsion weights from factory (engine, prop, accessories)
        try:
            from .systems import get_propulsion_system

            propulsion = get_propulsion_system()
            for item in propulsion.get_weight_items():
                self._weight_balance.add_item(
                    item.name, item.weight_lb, item.arm_in, "propulsion"
                )
        except (ImportError, Exception):
            # Fallback: use hardcoded O-235 weights if propulsion module unavailable
            fs_firewall = config.geometry.fs_firewall
            self._weight_balance.add_item(
                "Engine (O-235)", 250.0, fs_firewall + 15.0, "propulsion"
            )
            self._weight_balance.add_item(
                "Prop & Spinner", 25.0, fs_firewall + 25.0, "propulsion"
            )
            self._weight_balance.add_item(
                "Engine Accessories", 30.0, fs_firewall + 10.0, "propulsion"
            )

    def calculate_mac(self) -> Tuple[float, float]:
        """
        Calculate Mean Aerodynamic Chord and its location for strake+wing planform.

        Computes MAC piecewise: strake segment + outer wing segment, then
        combines using area-weighted averaging. The strake contributes
        significant area near the root and shifts the overall MAC forward.

        Returns:
            Tuple of (MAC length, MAC leading edge FS location)
        """
        cr = self.geo.wing_root_chord
        ct = self.geo.wing_tip_chord
        taper = ct / cr

        # === Outer wing segment (BL 23.3 to tip) ===
        # Standard trapezoidal MAC formula
        mac_wing = (2 / 3) * cr * (1 + taper + taper**2) / (1 + taper)

        # Spanwise location of wing MAC (from root, BL 23.3)
        semi_span = self.geo.wing_span / 2
        y_mac_wing = (semi_span / 3) * (1 + 2 * taper) / (1 + taper)

        # Leading edge location of wing MAC (accounting for sweep)
        x_mac_le_wing = self.geo.fs_wing_le + y_mac_wing * math.tan(
            math.radians(self.geo.wing_sweep_le)
        )

        # Wing planform area (sq in) for one side
        wing_avg_chord = (cr + ct) / 2
        s_wing_side = wing_avg_chord * semi_span  # sq in, one side

        # === Strake segment ===
        # The strakes extend from the fuselage to BL 23.3, contributing
        # significant lifting area near the root.
        strake_cfg = config.strakes if hasattr(config, "strakes") else None
        if strake_cfg is not None:
            strake_span = 23.3  # BL at wing root junction
            strake_chord_inboard = (
                strake_cfg.fs_trailing_edge - strake_cfg.fs_leading_edge
            )
            strake_chord_outboard = cr  # Blends into wing root
            strake_avg_chord = (strake_chord_inboard + strake_chord_outboard) / 2
            s_strake_side = strake_avg_chord * strake_span  # sq in, one side

            # Strake MAC (trapezoidal)
            strake_taper = (
                strake_chord_outboard / strake_chord_inboard
                if strake_chord_inboard > 0
                else 1.0
            )
            mac_strake = (
                (2 / 3)
                * strake_chord_inboard
                * (1 + strake_taper + strake_taper**2)
                / (1 + strake_taper)
            )

            # Strake MAC LE location (strake starts at fs_leading_edge)
            _y_mac_strake = (
                (strake_span / 3) * (1 + 2 * strake_taper) / (1 + strake_taper)
            )
            x_mac_le_strake = strake_cfg.fs_leading_edge  # Minimal sweep on strake

            # === Area-weighted combination ===
            s_total = s_wing_side + s_strake_side
            mac = (mac_wing * s_wing_side + mac_strake * s_strake_side) / s_total
            x_mac_le = (
                x_mac_le_wing * s_wing_side + x_mac_le_strake * s_strake_side
            ) / s_total
        else:
            # Fallback: simple trapezoidal (no strake config)
            mac = mac_wing
            x_mac_le = x_mac_le_wing

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

        # Canard AC at 25% MAC with sweep offset (matching wing pattern)
        canard_taper = self.geo.canard_tip_chord / self.geo.canard_root_chord
        mac_canard = (
            (2 / 3)
            * self.geo.canard_root_chord
            * (1 + canard_taper + canard_taper**2)
            / (1 + canard_taper)
        )
        canard_semi_span = self.geo.canard_span / 2
        y_mac_canard = (
            (canard_semi_span / 3) * (1 + 2 * canard_taper) / (1 + canard_taper)
        )
        x_mac_le_canard = self.geo.fs_canard_le + y_mac_canard * math.tan(
            math.radians(self.geo.canard_sweep_le)
        )
        ac_canard = x_mac_le_canard + 0.25 * mac_canard

        # Lift Curve Slopes using lifting line theory with sweep correction
        # Anderson eq. 5.69:
        # a = 2*pi*AR / (2 + sqrt(4 + AR^2 * (1 + tan^2(sweep_half) / beta^2)))
        # where sweep_half is sweep at half-chord line, beta^2 = 1 - M^2
        ar_wing = self.geo.wing_aspect_ratio

        # Calculate canard aspect ratio
        ar_canard = (self.geo.canard_span / 12) ** 2 / s_canard  # span in feet

        # Half-chord sweep from LE sweep and taper ratio
        # tan(sweep_c/2) = tan(sweep_LE) - 2*cr*(1-lambda)/(b*(1+lambda))
        taper_wing = self.geo.wing_tip_chord / self.geo.wing_root_chord
        tan_sweep_le_wing = math.tan(math.radians(self.geo.wing_sweep_le))
        tan_sweep_half_wing = tan_sweep_le_wing - (
            2
            * self.geo.wing_root_chord
            * (1 - taper_wing)
            / (self.geo.wing_span * (1 + taper_wing))
        )

        taper_canard = self.geo.canard_tip_chord / self.geo.canard_root_chord
        tan_sweep_le_canard = math.tan(math.radians(self.geo.canard_sweep_le))
        tan_sweep_half_canard = tan_sweep_le_canard - (
            2
            * self.geo.canard_root_chord
            * (1 - taper_canard)
            / (self.geo.canard_span * (1 + taper_canard))
        )

        # beta^2 = 1 - M^2 (approx 1.0 for low-speed, M < 0.25)
        beta_sq = 1.0

        # Lift curve slopes (per radian) with sweep correction
        a_wing = (
            2
            * math.pi
            * ar_wing
            / (2 + math.sqrt(4 + ar_wing**2 * (1 + tan_sweep_half_wing**2 / beta_sq)))
        )
        a_canard = (
            2
            * math.pi
            * ar_canard
            / (
                2
                + math.sqrt(4 + ar_canard**2 * (1 + tan_sweep_half_canard**2 / beta_sq))
            )
        )

        # Canard downwash on wing with vertical separation (Phillips, Ch. 9)
        #
        # Far-field downwash derivative:
        #   d(epsilon)/d(alpha) = (2 / (pi * AR_c)) * a_c
        # With vertical offset h between canard and wing plane:
        #   d(epsilon)/d(alpha) *= 1 / (1 + (2*h / b_c)^2)
        # Canard efficiency factor: eta = 1 - d(epsilon)/d(alpha)
        h = self.geo.canard_vertical_offset_in  # vertical separation
        b_c = self.geo.canard_span  # canard span (inches)
        vert_factor = 1.0 / (1.0 + (2.0 * h / b_c) ** 2)
        d_eps_dalpha = (2.0 / (math.pi * ar_canard)) * a_canard * vert_factor
        eta_canard = 1.0 - d_eps_dalpha

        # Calculate NP
        numerator = (a_wing * s_wing * ac_wing) + (
            a_canard * s_canard * ac_canard * eta_canard
        )
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
            cg_range_aft=cg_range_aft,
        )

    def calculate_envelope_margins(self) -> Dict[str, Dict[str, float]]:
        """Check CG stays within stable envelope across pilot/fuel extremes.

        Evaluates 4-corner scenarios: light/heavy pilot x min/max fuel.
        Each must produce CG within forward (20% margin) and aft (5% margin)
        limits relative to the neutral point.

        Returns:
            Dict mapping scenario name to {cg, margin_pct, is_safe}.
        """
        fc = config.flight_condition
        sw = config.structural_weights
        np_loc = self.calculate_neutral_point()
        mac, _ = self.calculate_mac()
        cg_fwd = np_loc - 0.20 * mac
        cg_aft = np_loc - 0.05 * mac

        # Build empty-weight snapshot (excludes pilot and fuel)
        empty_items = [
            i
            for i in self._weight_balance.items
            if i.category not in ("payload", "fuel")
        ]
        empty_weight = sum(i.weight for i in empty_items)
        empty_moment = sum(i.moment for i in empty_items)

        fuel_density = sw.fuel_density_lb_per_gal
        fuel_arm = sw.fuel_arm_in
        pilot_arm = config.geometry.fs_pilot_seat

        scenarios = {
            "light_pilot_min_fuel": (fc.pilot_weight_min_lb, fc.fuel_reserve_gal),
            "heavy_pilot_max_fuel": (
                fc.pilot_weight_max_lb,
                config.propulsion.fuel_capacity_gal,
            ),
            "heavy_pilot_min_fuel": (fc.pilot_weight_max_lb, fc.fuel_reserve_gal),
            "light_pilot_max_fuel": (
                fc.pilot_weight_min_lb,
                config.propulsion.fuel_capacity_gal,
            ),
        }

        results = {}
        for name, (pilot_lb, fuel_gal) in scenarios.items():
            fuel_lb = fuel_gal * fuel_density
            total_w = empty_weight + pilot_lb + fuel_lb
            total_m = empty_moment + pilot_lb * pilot_arm + fuel_lb * fuel_arm
            cg = total_m / total_w if total_w > 0 else 0.0
            margin_pct = (np_loc - cg) / mac * 100.0 if mac > 0 else 0.0
            results[name] = {
                "cg": cg,
                "margin_pct": margin_pct,
                "is_safe": cg_fwd <= cg <= cg_aft,
            }
        return results

    def add_payload(self, name: str, weight: float, arm: float):
        """Add a payload item to weight & balance."""
        self._weight_balance.add_item(name, weight, arm, "payload")

    def add_fuel(self, gallons: float, arm: float = None):
        """Add fuel to weight & balance using config fuel density."""
        if arm is None:
            arm = config.structural_weights.fuel_arm_in
        density = config.structural_weights.fuel_density_lb_per_gal
        self._weight_balance.add_item(
            f"Fuel ({gallons:.1f} gal)", gallons * density, arm, "fuel"
        )

    def get_weight_balance(self) -> WeightBalance:
        """Get current weight & balance state."""
        return self._weight_balance

    @staticmethod
    def calculate_reynolds(
        velocity_kts: float = 160.0, chord_in: float = 50.0, altitude_ft: float = 8000.0
    ) -> float:
        """Calculate Reynolds number at given flight conditions.

        Re = rho * V * c / mu

        Uses ISA standard atmosphere model for density and viscosity.

        Args:
            velocity_kts: Airspeed in knots
            chord_in: Chord length in inches
            altitude_ft: Pressure altitude in feet

        Returns:
            Reynolds number (dimensionless)
        """
        from .atmosphere import density, viscosity

        rho = density(altitude_ft)
        mu = viscosity(altitude_ft)

        # Convert units
        velocity_fps = velocity_kts * 1.6878  # knots to ft/s
        chord_ft = chord_in / 12.0  # inches to feet

        return rho * velocity_fps * chord_ft / mu

    @staticmethod
    def skin_friction_coefficient(reynolds: float) -> float:
        """Turbulent flat-plate skin friction coefficient.

        Cf = 0.455 / (log10(Re))^2.58

        Reference: Schlichting boundary layer theory
        """
        if reynolds <= 0:
            return 0.0
        return 0.455 / (math.log10(reynolds) ** 2.58)

    def check_canard_stall_priority(self) -> Tuple[bool, str]:
        """
        Verify that canard stalls before wing (safety critical).

        Compares effective stall angles accounting for:
        - Sweep-corrected lift curve slopes (Anderson eq. 5.69)
        - Reynolds-scaled CLmax (Raymer Sec. 12.5): CLmax * (Re/Re_ref)^0.1
        - Incidence angle differences

        The canard must stall at a lower aircraft alpha than the wing.

        Returns:
            Tuple of (is_safe, message)
        """
        from .atmosphere import density, viscosity

        al = config.aero_limits
        fc = config.flight_condition

        # Lift curve slopes (reuse NP calculation logic)
        ar_wing = self.geo.wing_aspect_ratio
        ar_canard = (self.geo.canard_span / 12) ** 2 / self.geo.canard_area

        taper_wing = self.geo.wing_tip_chord / self.geo.wing_root_chord
        tan_le_wing = math.tan(math.radians(self.geo.wing_sweep_le))
        tan_half_wing = tan_le_wing - (
            2
            * self.geo.wing_root_chord
            * (1 - taper_wing)
            / (self.geo.wing_span * (1 + taper_wing))
        )

        taper_canard = self.geo.canard_tip_chord / self.geo.canard_root_chord
        tan_le_canard = math.tan(math.radians(self.geo.canard_sweep_le))
        tan_half_canard = tan_le_canard - (
            2
            * self.geo.canard_root_chord
            * (1 - taper_canard)
            / (self.geo.canard_span * (1 + taper_canard))
        )

        a_wing = (
            2
            * math.pi
            * ar_wing
            / (2 + math.sqrt(4 + ar_wing**2 * (1 + tan_half_wing**2)))
        )
        a_canard = (
            2
            * math.pi
            * ar_canard
            / (2 + math.sqrt(4 + ar_canard**2 * (1 + tan_half_canard**2)))
        )

        # Reynolds-scaled CLmax (Raymer Sec. 12.5)
        # At approach speed, compute Re for each surface using representative chord
        alt = fc.design_altitude_ft
        rho = density(alt)
        mu = viscosity(alt)
        v_fps = fc.approach_speed_ktas * 1.6878  # knots to ft/s

        # Representative chords: use MAC
        mac_canard = (
            (2 / 3)
            * self.geo.canard_root_chord
            * (1 + taper_canard + taper_canard**2)
            / (1 + taper_canard)
        )
        mac_wing, _ = self.calculate_mac()
        chord_canard_ft = mac_canard / 12.0
        chord_wing_ft = mac_wing / 12.0

        re_canard = rho * v_fps * chord_canard_ft / mu
        re_wing = rho * v_fps * chord_wing_ft / mu

        # Scale CLmax: CLmax_actual = CLmax_ref * (Re/Re_ref)^0.1
        re_ref = al.clmax_reference_re
        clmax_canard = al.canard_clmax * (re_canard / re_ref) ** 0.1
        clmax_wing = al.wing_clmax * (re_wing / re_ref) ** 0.1

        # Effective stall AoA for each surface (degrees)
        # alpha_stall = CLmax / a (rad) converted to deg, adjusted for zero-lift AoA and incidence
        alpha_stall_canard = (
            math.degrees(clmax_canard / a_canard)
            + al.canard_alpha_0L
            - self.geo.canard_incidence
        )
        alpha_stall_wing = (
            math.degrees(clmax_wing / a_wing)
            + al.wing_alpha_0L
            - self.geo.wing_incidence
        )

        margin_deg = alpha_stall_wing - alpha_stall_canard
        is_safe = margin_deg >= al.min_stall_margin_deg

        msg = (
            f"Canard stall margin: {margin_deg:.1f} deg "
            f"(min required: {al.min_stall_margin_deg:.1f} deg). "
            f"CLmax_canard={clmax_canard:.3f} (Re={re_canard:.0f}), "
            f"CLmax_wing={clmax_wing:.3f} (Re={re_wing:.0f})"
        )
        if not is_safe:
            msg = "WARNING: " + msg

        return (is_safe, msg)

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
                "cg_aft_limit": metrics.cg_range_aft,
            },
            "canard_safety": {"stall_priority_ok": canard_safe, "message": canard_msg},
            "weight_balance": {
                "empty_weight": self._weight_balance.total_weight,
                "empty_cg": self._weight_balance.cg_location,
                "items": [
                    {"name": item.name, "weight": item.weight, "arm": item.arm}
                    for item in self._weight_balance.items
                ],
            },
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
            '  string wid = AddGeom("WING", "");',
            '  SetGeomName(wid, "MainWing");',
            "",
            "  // Wing planform",
            f'  SetParmVal(wid, "Span", "XSec_1", {geo.wing_span / 2});',
            f'  SetParmVal(wid, "Root_Chord", "XSec_1", {geo.wing_root_chord});',
            f'  SetParmVal(wid, "Tip_Chord", "XSec_1", {geo.wing_tip_chord});',
            f'  SetParmVal(wid, "Sweep", "XSec_1", {geo.wing_sweep_le});',
            f'  SetParmVal(wid, "Dihedral", "XSec_1", {geo.wing_dihedral});',
            "",
            "  // Wing position",
            f'  SetParmVal(wid, "X_Rel_Location", "XForm", {geo.fs_wing_le});',
            '  SetParmVal(wid, "Y_Rel_Location", "XForm", 0);',
            '  SetParmVal(wid, "Z_Rel_Location", "XForm", 0);',
            "",
            "  // Wing incidence",
            f'  SetParmVal(wid, "X_Rel_Rotation", "XForm", {geo.wing_incidence});',
            "",
            "  // Airfoil (placeholder - would need actual airfoil import)",
            "  // ChangeXSecShape(GetXSec(GetXSecSurf(wid, 0), 0), XS_FILE_AIRFOIL);",
            "",
            "  //--- CANARD ---",
            '  string cid = AddGeom("WING", "");',
            '  SetGeomName(cid, "Canard");',
            "",
            "  // Canard planform",
            f'  SetParmVal(cid, "Span", "XSec_1", {geo.canard_span / 2});',
            f'  SetParmVal(cid, "Root_Chord", "XSec_1", {geo.canard_root_chord});',
            f'  SetParmVal(cid, "Tip_Chord", "XSec_1", {geo.canard_tip_chord});',
            f'  SetParmVal(cid, "Sweep", "XSec_1", {geo.canard_sweep_le});',
            "",
            "  // Canard position",
            f'  SetParmVal(cid, "X_Rel_Location", "XForm", {geo.fs_canard_le});',
            '  SetParmVal(cid, "Y_Rel_Location", "XForm", 0);',
            '  SetParmVal(cid, "Z_Rel_Location", "XForm", 0);',
            "",
            "  // Canard incidence",
            f'  SetParmVal(cid, "X_Rel_Rotation", "XForm", {geo.canard_incidence});',
            "",
            "  //--- FUSELAGE ---",
            '  string fid = AddGeom("FUSELAGE", "");',
            '  SetGeomName(fid, "Fuselage");',
            "",
            f"  double fuse_length = {geo.fs_tail - geo.fs_nose};",
            '  SetParmVal(fid, "Length", "Design", fuse_length);',
            "",
            "  // Fuselage cross-sections",
            f"  // Cockpit width: {geo.cockpit_width} in",
            "",
            "  //--- VERTICAL STABILIZERS (Winglets) ---",
            '  string vid = AddGeom("WING", "");',
            '  SetGeomName(vid, "Winglet_L");',
            '  SetParmVal(vid, "Span", "XSec_1", 30);',
            '  SetParmVal(vid, "Sweep", "XSec_1", 45);',
            f'  SetParmVal(vid, "X_Rel_Location", "XForm", {geo.fs_wing_le + geo.wing_root_chord});',
            f'  SetParmVal(vid, "Y_Rel_Location", "XForm", {geo.wing_span / 2});',
            '  SetParmVal(vid, "X_Rel_Rotation", "XForm", 90);',
            "",
            "  // Mirror for right winglet",
            '  string vid2 = AddGeom("WING", "");',
            '  SetGeomName(vid2, "Winglet_R");',
            "  // (similar settings, mirrored)",
            "",
            "  //--- UPDATE MODEL ---",
            "  Update();",
            "",
            "  // Save model",
            '  // WriteVSPFile("long_ez.vsp3", SET_ALL);',
            "",
            '  Print("Open-EZ model generated successfully.");',
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
                "x": config.geometry.fs_wing_le / 12
                + config.geometry.wing_root_chord * 0.25 / 12,
                "y": 0,
                "z": 0,
            },
        }

        output_path = Path(output_path)
        with open(output_path, "w") as f:
            json.dump(settings, f, indent=2)

        return output_path


# Module Instance
physics = PhysicsEngine()
