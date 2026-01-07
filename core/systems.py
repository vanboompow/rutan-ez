"""
Open-EZ PDE: Propulsion & Systems Module
=========================================

Provides abstract propulsion system interface and concrete implementations:
- LycomingO235: Baseline IC engine (115 HP)
- ElectricEZ: LiFePO4 battery electric conversion

Each propulsion type generates:
- Firewall geometry (F-28 modifications)
- Weight & balance contributions
- Thrust/power calculations

The E-Z conversion automatically recalculates CG and modifies the firewall
geometry to handle different torque loads from the electric motor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
import math

import cadquery as cq
import numpy as np

from config import config
from config.aircraft_config import PropulsionType

if TYPE_CHECKING:
    from .analysis import WeightItem


@dataclass
class WeightItem:
    """Single weight component for W&B calculations."""

    name: str
    weight_lb: float
    arm_in: float  # CG arm from datum (FS inches)
    category: str = "fixed"  # fixed, fuel, payload, propulsion

    @property
    def moment(self) -> float:
        """Weight moment (lb-in)."""
        return self.weight_lb * self.arm_in


class Propulsion(ABC):
    """
    Abstract propulsion system base class.

    All propulsion systems must provide:
    - Weight contribution for W&B
    - Firewall geometry generation
    - Thrust calculation at given flight condition
    """

    def __init__(self, name: str = "propulsion"):
        self.name = name
        self._firewall_geometry: Optional[cq.Workplane] = None

    @abstractmethod
    def get_weight_items(self) -> List[WeightItem]:
        """Return list of weight components for W&B."""
        pass

    @abstractmethod
    def generate_firewall_geometry(self) -> cq.Workplane:
        """Generate F-28 firewall with mounting provisions."""
        pass

    @abstractmethod
    def calculate_thrust(
        self,
        altitude_ft: float,
        velocity_kts: float,
        throttle: float = 1.0,
    ) -> float:
        """
        Compute available thrust at flight condition.

        Args:
            altitude_ft: Pressure altitude
            velocity_kts: True airspeed
            throttle: Throttle setting (0.0 to 1.0)

        Returns:
            Thrust in pounds
        """
        pass

    @abstractmethod
    def get_power_available(self, altitude_ft: float) -> float:
        """Return available power in HP at altitude."""
        pass

    def get_total_weight(self) -> float:
        """Sum of all propulsion weight items."""
        return sum(item.weight_lb for item in self.get_weight_items())

    def get_propulsion_cg(self) -> float:
        """Compute propulsion system CG location."""
        items = self.get_weight_items()
        total_moment = sum(item.moment for item in items)
        total_weight = sum(item.weight_lb for item in items)
        if total_weight > 0:
            return total_moment / total_weight
        return config.geometry.fs_firewall


class LycomingO235(Propulsion):
    """
    Baseline Long-EZ powerplant: Lycoming O-235-L2C.

    Specifications:
    - 115 HP @ 2700 RPM
    - 235 cubic inch displacement
    - Dry weight: 243 lb (with accessories)
    - Fuel consumption: 6.5 GPH cruise
    """

    # Engine specifications
    DISPLACEMENT_CI = 235.0
    RATED_HP = 115.0
    RATED_RPM = 2700
    DRY_WEIGHT_LB = 243.0
    FUEL_GPH_CRUISE = 6.5
    PROP_DIAMETER_IN = 60.0

    # Installation weights
    ENGINE_MOUNT_WEIGHT = 15.0  # Lord mount, tubes
    EXHAUST_WEIGHT = 12.0
    BAFFLES_WEIGHT = 5.0
    COWLING_WEIGHT = 18.0
    PROP_WEIGHT = 35.0  # Fixed pitch wood/composite

    def __init__(self):
        super().__init__("lycoming_o235")
        self.prop_efficiency = 0.82  # Typical cruise efficiency

    def get_weight_items(self) -> List[WeightItem]:
        """Return all engine installation weight items."""
        fs_firewall = config.geometry.fs_firewall

        return [
            WeightItem(
                name="engine_dry",
                weight_lb=self.DRY_WEIGHT_LB,
                arm_in=fs_firewall + 8.0,  # Engine CG forward of firewall
                category="propulsion",
            ),
            WeightItem(
                name="engine_mount",
                weight_lb=self.ENGINE_MOUNT_WEIGHT,
                arm_in=fs_firewall + 2.0,
                category="propulsion",
            ),
            WeightItem(
                name="exhaust_system",
                weight_lb=self.EXHAUST_WEIGHT,
                arm_in=fs_firewall + 12.0,
                category="propulsion",
            ),
            WeightItem(
                name="baffles",
                weight_lb=self.BAFFLES_WEIGHT,
                arm_in=fs_firewall + 6.0,
                category="propulsion",
            ),
            WeightItem(
                name="cowling",
                weight_lb=self.COWLING_WEIGHT,
                arm_in=fs_firewall + 15.0,
                category="propulsion",
            ),
            WeightItem(
                name="propeller",
                weight_lb=self.PROP_WEIGHT,
                arm_in=fs_firewall + 20.0,
                category="propulsion",
            ),
        ]

    def generate_firewall_geometry(self) -> cq.Workplane:
        """
        Generate standard F-28 firewall for O-235.

        Features:
        - 4-bolt Lord mount pattern
        - Exhaust pipe clearance (asymmetric cutout)
        - Fuel line penetrations
        - Throttle/mixture cable routing
        - 0.032" 2024-T3 aluminum skin
        """
        # Firewall dimensions (from Long-EZ plans)
        width = 18.0  # inches
        height = 20.0  # inches
        thickness = 0.032  # aluminum skin

        # Base plate
        firewall = (
            cq.Workplane("YZ")
            .rect(width, height)
            .extrude(thickness)
            .translate((config.geometry.fs_firewall, 0, 0))
        )

        # Engine mount bolt pattern (4-bolt Lord pattern)
        mount_pattern = [
            (6.0, 4.0),
            (-6.0, 4.0),
            (6.0, -4.0),
            (-6.0, -4.0),
        ]

        for y, z in mount_pattern:
            hole = (
                cq.Workplane("YZ")
                .center(y, z)
                .circle(0.375)  # 3/8" bolt holes
                .extrude(thickness * 2)
                .translate((config.geometry.fs_firewall - thickness, 0, 0))
            )
            firewall = firewall.cut(hole)

        # Exhaust pipe clearance (right side, asymmetric)
        exhaust_cutout = (
            cq.Workplane("YZ")
            .center(-5.0, -6.0)
            .ellipse(2.5, 2.0)
            .extrude(thickness * 2)
            .translate((config.geometry.fs_firewall - thickness, 0, 0))
        )
        firewall = firewall.cut(exhaust_cutout)

        # Fuel line penetrations
        fuel_holes = [(4.0, 8.0), (4.5, 7.5)]  # Main and return
        for y, z in fuel_holes:
            hole = (
                cq.Workplane("YZ")
                .center(y, z)
                .circle(0.25)  # 1/4" fuel line
                .extrude(thickness * 2)
                .translate((config.geometry.fs_firewall - thickness, 0, 0))
            )
            firewall = firewall.cut(hole)

        # Throttle/mixture cable grommets
        cable_holes = [(-7.0, 6.0), (-7.0, 5.0)]
        for y, z in cable_holes:
            hole = (
                cq.Workplane("YZ")
                .center(y, z)
                .circle(0.375)  # Cable grommet
                .extrude(thickness * 2)
                .translate((config.geometry.fs_firewall - thickness, 0, 0))
            )
            firewall = firewall.cut(hole)

        # Add stiffening beads (simplified as rectangular ribs)
        bead_height = 0.25
        for z_offset in [-5.0, 0.0, 5.0]:
            bead = (
                cq.Workplane("YZ")
                .center(0, z_offset)
                .rect(width - 2, 0.5)
                .extrude(bead_height)
                .translate((config.geometry.fs_firewall + thickness, 0, 0))
            )
            firewall = firewall.union(bead)

        self._firewall_geometry = firewall
        return firewall

    def calculate_thrust(
        self,
        altitude_ft: float,
        velocity_kts: float,
        throttle: float = 1.0,
    ) -> float:
        """
        Compute propeller thrust using momentum theory.

        Accounts for:
        - Density altitude effects on power
        - Propeller efficiency vs advance ratio
        """
        # Density ratio (simplified standard atmosphere)
        rho_ratio = math.exp(-altitude_ft / 25000)

        # Power available (HP)
        power_hp = self.get_power_available(altitude_ft) * throttle

        # Convert velocity to ft/s
        velocity_fps = velocity_kts * 1.688

        # Propeller advance ratio
        n_rps = self.RATED_RPM / 60  # Revolutions per second
        J = velocity_fps / (n_rps * self.PROP_DIAMETER_IN / 12)

        # Efficiency vs advance ratio (simplified)
        if J < 0.5:
            eta = 0.5 + 0.4 * J
        elif J < 1.5:
            eta = 0.7 + 0.12 * (J - 0.5)
        else:
            eta = max(0.5, 0.82 - 0.1 * (J - 1.5))

        # Thrust = Power × efficiency / velocity
        if velocity_fps > 10:
            thrust_lb = (power_hp * 550 * eta) / velocity_fps
        else:
            # Static thrust approximation
            thrust_lb = power_hp * 4.0  # ~4 lb/hp static

        return thrust_lb

    def get_power_available(self, altitude_ft: float) -> float:
        """Power available accounting for altitude."""
        # Normally aspirated: power drops ~3% per 1000 ft
        altitude_factor = 1.0 - 0.03 * (altitude_ft / 1000)
        altitude_factor = max(0.5, altitude_factor)
        return self.RATED_HP * altitude_factor


class ElectricEZ(Propulsion):
    """
    E-Z conversion to electric powerplant.

    Default configuration:
    - EMRAX 228 motor (100 kW continuous, 200 kW peak)
    - LiFePO4 battery (16S4P, 25.6 kWh)
    - 51.2V nominal system voltage

    The electric conversion provides:
    - Instant torque (no spool-up time)
    - Reduced vibration
    - Different firewall loads (no exhaust, different mount)
    - Battery in strakes instead of fuel
    """

    # Motor specifications (EMRAX 228 MV)
    MOTOR_POWER_KW = 100.0  # Continuous
    MOTOR_PEAK_KW = 200.0  # Peak (2 min)
    MOTOR_WEIGHT_LB = 77.0  # 35 kg
    MOTOR_KV = 85  # RPM per volt
    MOTOR_EFFICIENCY = 0.96

    # Controller specifications
    CONTROLLER_WEIGHT_LB = 22.0
    CONTROLLER_EFFICIENCY = 0.98

    # Propeller (larger for efficiency at lower RPM)
    PROP_DIAMETER_IN = 66.0
    PROP_WEIGHT_LB = 25.0  # Carbon fiber

    # System weights
    WIRING_WEIGHT_LB = 15.0
    COOLING_WEIGHT_LB = 8.0

    def __init__(self, battery_kwh: float = 25.6):
        super().__init__("electric_ez")
        self.battery_capacity_kwh = battery_kwh
        self.prop_efficiency = 0.85

        # Battery configuration (LiFePO4 16S)
        self.cells_series = 16
        self.cells_parallel = 4
        self.nominal_voltage = 51.2  # 3.2V × 16

    @property
    def battery_weight_lb(self) -> float:
        """Compute battery weight from capacity and chemistry."""
        prop_cfg = config.propulsion
        energy_density = prop_cfg.battery_energy_density_wh_kg
        weight_kg = (self.battery_capacity_kwh * 1000) / energy_density
        return weight_kg * 2.205  # Convert to lb

    def get_weight_items(self) -> List[WeightItem]:
        """Return all electric propulsion weight items."""
        fs_firewall = config.geometry.fs_firewall
        strake_cg = (config.strakes.fs_leading_edge + config.strakes.fs_trailing_edge) / 2

        items = [
            WeightItem(
                name="motor",
                weight_lb=self.MOTOR_WEIGHT_LB,
                arm_in=fs_firewall + 4.0,  # Motor is lighter, more forward
                category="propulsion",
            ),
            WeightItem(
                name="controller",
                weight_lb=self.CONTROLLER_WEIGHT_LB,
                arm_in=fs_firewall - 5.0,  # Behind firewall
                category="propulsion",
            ),
            WeightItem(
                name="propeller",
                weight_lb=self.PROP_WEIGHT_LB,
                arm_in=fs_firewall + 12.0,
                category="propulsion",
            ),
            WeightItem(
                name="wiring",
                weight_lb=self.WIRING_WEIGHT_LB,
                arm_in=(fs_firewall + strake_cg) / 2,  # Distributed
                category="propulsion",
            ),
            WeightItem(
                name="cooling_system",
                weight_lb=self.COOLING_WEIGHT_LB,
                arm_in=fs_firewall - 2.0,
                category="propulsion",
            ),
            WeightItem(
                name="battery_pack",
                weight_lb=self.battery_weight_lb,
                arm_in=strake_cg,  # Batteries in strakes
                category="propulsion",
            ),
        ]

        return items

    def generate_firewall_geometry(self) -> cq.Workplane:
        """
        Generate modified F-28 firewall for electric motor.

        Differences from IC engine:
        - No exhaust cutout (cleaner structure)
        - Different motor mount pattern (EMRAX face mount)
        - High-voltage cable penetrations with grommets
        - Cooling duct integration
        - Structural stiffening for instant torque loads
        """
        # Firewall dimensions
        width = 18.0
        height = 20.0
        thickness = 0.040  # Slightly thicker for torque loads

        # Base plate
        firewall = (
            cq.Workplane("YZ")
            .rect(width, height)
            .extrude(thickness)
            .translate((config.geometry.fs_firewall, 0, 0))
        )

        # EMRAX motor mount pattern (bolt circle)
        # EMRAX 228 has 8-bolt pattern on 200mm PCD
        bolt_circle_radius = 200 / 25.4 / 2  # Convert mm to inches
        num_bolts = 8

        for i in range(num_bolts):
            angle = 2 * math.pi * i / num_bolts
            y = bolt_circle_radius * math.cos(angle)
            z = bolt_circle_radius * math.sin(angle)

            hole = (
                cq.Workplane("YZ")
                .center(y, z)
                .circle(0.3125)  # 5/16" bolts
                .extrude(thickness * 2)
                .translate((config.geometry.fs_firewall - thickness, 0, 0))
            )
            firewall = firewall.cut(hole)

        # Motor shaft center hole
        shaft_hole = (
            cq.Workplane("YZ")
            .circle(1.5)  # Large for motor housing clearance
            .extrude(thickness * 2)
            .translate((config.geometry.fs_firewall - thickness, 0, 0))
        )
        firewall = firewall.cut(shaft_hole)

        # High-voltage cable penetrations (Phase A, B, C + DC cables)
        hv_positions = [
            (6.0, 7.0),   # Phase A
            (6.5, 6.0),   # Phase B
            (7.0, 5.0),   # Phase C
            (-6.0, 7.0),  # DC+
            (-6.5, 6.0),  # DC-
        ]

        for y, z in hv_positions:
            # Larger holes with grommet provisions
            hole = (
                cq.Workplane("YZ")
                .center(y, z)
                .circle(0.5)  # 1" diameter for HV cables
                .extrude(thickness * 2)
                .translate((config.geometry.fs_firewall - thickness, 0, 0))
            )
            firewall = firewall.cut(hole)

        # Cooling duct inlet
        cooling_inlet = (
            cq.Workplane("YZ")
            .center(0, -7.0)
            .rect(6.0, 2.0)
            .extrude(thickness * 2)
            .translate((config.geometry.fs_firewall - thickness, 0, 0))
        )
        firewall = firewall.cut(cooling_inlet)

        # Torque reaction ribs (electric motors have instant torque)
        rib_thickness = 0.5
        for angle in [45, 135, 225, 315]:
            angle_rad = math.radians(angle)
            rib_length = 6.0
            y1 = 2.0 * math.cos(angle_rad)
            z1 = 2.0 * math.sin(angle_rad)
            y2 = (2.0 + rib_length) * math.cos(angle_rad)
            z2 = (2.0 + rib_length) * math.sin(angle_rad)

            rib = (
                cq.Workplane("YZ")
                .moveTo(y1, z1)
                .lineTo(y2, z2)
                .lineTo(y2 + 0.3 * math.sin(angle_rad), z2 - 0.3 * math.cos(angle_rad))
                .lineTo(y1 + 0.3 * math.sin(angle_rad), z1 - 0.3 * math.cos(angle_rad))
                .close()
                .extrude(rib_thickness)
                .translate((config.geometry.fs_firewall + thickness, 0, 0))
            )
            firewall = firewall.union(rib)

        self._firewall_geometry = firewall
        return firewall

    def calculate_thrust(
        self,
        altitude_ft: float,
        velocity_kts: float,
        throttle: float = 1.0,
    ) -> float:
        """
        Compute propeller thrust for electric motor.

        Electric motors maintain torque at altitude (no density effect on power).
        Only propeller efficiency is affected by density.
        """
        # Electric power available (constant with altitude)
        power_kw = self.get_power_available(altitude_ft) * throttle
        power_hp = power_kw * 1.341  # Convert to HP

        # System efficiency
        system_efficiency = self.MOTOR_EFFICIENCY * self.CONTROLLER_EFFICIENCY

        # Convert velocity to ft/s
        velocity_fps = velocity_kts * 1.688

        # RPM at this voltage
        rpm = self.MOTOR_KV * self.nominal_voltage

        # Propeller advance ratio
        n_rps = rpm / 60
        J = velocity_fps / (n_rps * self.PROP_DIAMETER_IN / 12) if n_rps > 0 else 0

        # Propeller efficiency
        if J < 0.5:
            eta_prop = 0.55 + 0.35 * J
        elif J < 1.5:
            eta_prop = 0.72 + 0.13 * (J - 0.5)
        else:
            eta_prop = max(0.6, 0.85 - 0.08 * (J - 1.5))

        # Density ratio affects propeller thrust at altitude
        rho_ratio = math.exp(-altitude_ft / 25000)
        eta_prop *= math.sqrt(rho_ratio)  # Reduced efficiency at altitude

        # Thrust
        overall_efficiency = system_efficiency * eta_prop

        if velocity_fps > 10:
            thrust_lb = (power_hp * 550 * overall_efficiency) / velocity_fps
        else:
            # Static thrust
            thrust_lb = power_hp * 5.0  # Higher static thrust ratio for electric

        return thrust_lb

    def get_power_available(self, altitude_ft: float) -> float:
        """
        Power available from electric motor.

        Electric motors maintain full power at altitude (unlike IC engines).
        Only slight reduction due to cooling air density.
        """
        # Minimal power reduction with altitude (cooling limited)
        if altitude_ft > 15000:
            altitude_factor = 1.0 - 0.01 * (altitude_ft - 15000) / 1000
        else:
            altitude_factor = 1.0

        return self.MOTOR_POWER_KW * max(0.9, altitude_factor)

    def get_endurance(self, power_kw: float) -> float:
        """
        Calculate endurance at given power draw.

        Args:
            power_kw: Average power consumption

        Returns:
            Endurance in hours
        """
        if power_kw <= 0:
            return 0.0

        usable_capacity = self.battery_capacity_kwh * 0.90  # 90% usable
        return usable_capacity / power_kw

    def get_range(self, cruise_speed_kts: float, cruise_power_kw: float) -> float:
        """
        Calculate range at cruise conditions.

        Args:
            cruise_speed_kts: Cruise true airspeed
            cruise_power_kw: Cruise power consumption

        Returns:
            Range in nautical miles
        """
        endurance_hr = self.get_endurance(cruise_power_kw)
        return cruise_speed_kts * endurance_hr

    def generate_battery_mounts(self) -> Dict[str, cq.Workplane]:
        """
        Generate strake battery mounting structure.

        Returns dict with:
        - 'cell_cradle': Individual LiFePO4 cell holders
        - 'module_tray': 4-cell module tray
        - 'bms_bracket': Battery management system mount
        """
        mounts: Dict[str, cq.Workplane] = {}

        strake_cfg = config.strakes

        # Individual cell cradle (fits 2.5" x 6" x 8" prismatic cell)
        cell_width = 2.5
        cell_height = 6.0
        cell_depth = 8.0
        wall = 0.125

        cell_cradle = (
            cq.Workplane("XY")
            .rect(cell_width + 2 * wall, cell_depth + 2 * wall)
            .extrude(cell_height + wall)
            .faces(">Z")
            .shell(-wall)
        )
        mounts["cell_cradle"] = cell_cradle

        # 4-cell module tray (4P parallel group)
        module_width = 4 * (cell_width + wall)
        module_tray = (
            cq.Workplane("XY")
            .rect(module_width + 2 * wall, cell_depth + 2 * wall)
            .extrude(cell_height + 2 * wall)
            .faces(">Z")
            .shell(-wall)
        )

        # Add cell dividers
        for i in range(1, 4):
            divider = (
                cq.Workplane("YZ")
                .rect(cell_depth, cell_height)
                .extrude(wall)
                .translate((wall + i * (cell_width + wall), wall, wall))
            )
            module_tray = module_tray.union(divider)

        mounts["module_tray"] = module_tray

        # BMS bracket
        bms_bracket = (
            cq.Workplane("XY")
            .rect(4.0, 6.0)
            .extrude(0.25)
            .faces(">Z")
            .workplane()
            .rect(3.0, 5.0)
            .extrude(1.0)
        )
        mounts["bms_bracket"] = bms_bracket

        return mounts

    def compare_to_baseline(self) -> Dict[str, float]:
        """
        Compare electric conversion to baseline O-235.

        Returns dict with weight/CG/performance deltas.
        """
        baseline = LycomingO235()

        baseline_weight = baseline.get_total_weight()
        electric_weight = self.get_total_weight()

        baseline_cg = baseline.get_propulsion_cg()
        electric_cg = self.get_propulsion_cg()

        return {
            "weight_delta_lb": electric_weight - baseline_weight,
            "cg_shift_in": electric_cg - baseline_cg,
            "baseline_weight_lb": baseline_weight,
            "electric_weight_lb": electric_weight,
            "baseline_cg_in": baseline_cg,
            "electric_cg_in": electric_cg,
            "endurance_hr_at_50kw": self.get_endurance(50.0),
            "range_nm_at_100kts": self.get_range(100.0, 45.0),
        }


def get_propulsion_system(
    propulsion_type: PropulsionType = None,
) -> Propulsion:
    """
    Factory function to create appropriate propulsion system.

    Args:
        propulsion_type: Type of propulsion (from config if None)

    Returns:
        Propulsion instance
    """
    if propulsion_type is None:
        propulsion_type = config.propulsion.propulsion_type

    if propulsion_type == PropulsionType.LYCOMING_O235:
        return LycomingO235()
    elif propulsion_type == PropulsionType.LYCOMING_O320:
        # O-320 is similar to O-235 but more powerful
        engine = LycomingO235()
        engine.RATED_HP = 150.0
        engine.DRY_WEIGHT_LB = 268.0
        engine.name = "lycoming_o320"
        return engine
    elif propulsion_type in (PropulsionType.ELECTRIC_LIFEPO4, PropulsionType.ELECTRIC_NMC):
        return ElectricEZ(battery_kwh=config.propulsion.battery_capacity_kwh)
    else:
        raise ValueError(f"Unknown propulsion type: {propulsion_type}")


__all__ = [
    "Propulsion",
    "LycomingO235",
    "ElectricEZ",
    "WeightItem",
    "get_propulsion_system",
]
