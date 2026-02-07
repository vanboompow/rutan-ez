"""Lightweight OpenVSP adapter for aerodynamic regression tests."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from config import config


@dataclass
class AeroPolar:
    """Aerodynamic coefficients for a single angle of attack."""

    alpha_deg: float
    cl: float
    cm: float
    cd: float


class OpenVSPAdapter:
    """Generate simplified OpenVSP-like aerodynamic data.

    The real project depends on OpenVSP and VSPAERO for stability and drag
    polars. For CI environments without OpenVSP installed, this adapter
    synthesizes representative results using configuration-driven heuristics.
    """

    def __init__(self, output_root: Path | None = None):
        self.output_root = output_root or Path("output") / "vsp"
        self.output_root.mkdir(parents=True, exist_ok=True)

    def export_vsp3(self) -> Path:
        """Write a VSP3-compatible payload to disk.

        The file is JSON for readability but captures the required geometry
        metadata so that OpenVSP can be driven in environments where the real
        toolchain is available.
        """

        payload = {
            "project": config.project_name,
            "baseline": config.baseline,
            "geometry": {
                "wing_span_in": config.geometry.wing_span,
                "wing_root_chord_in": config.geometry.wing_root_chord,
                "wing_tip_chord_in": config.geometry.wing_tip_chord,
                "wing_sweep_deg": config.geometry.wing_sweep_le,
                "wing_dihedral_deg": config.geometry.wing_dihedral,
                "wing_washout_deg": config.geometry.wing_washout,
                "canard_span_in": config.geometry.canard_span,
                "canard_root_chord_in": config.geometry.canard_root_chord,
                "canard_tip_chord_in": config.geometry.canard_tip_chord,
                "canard_incidence_deg": config.geometry.canard_incidence,
            },
            "airfoils": {
                "canard": config.airfoils.canard.value,
                "wing_root": config.airfoils.wing_root.value,
                "wing_tip": config.airfoils.wing_tip.value,
                "wing_reflex_percent": config.airfoils.wing_reflex_percent,
            },
        }

        target = self.output_root / "open_ez.vsp3.json"
        with open(target, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return target

    def _cl_slope_per_deg(self) -> float:
        """Estimate lift-curve slope (CL/deg) with finite-wing and washout correction.

        Uses lifting-line theory: a = 2*pi*AR / (AR + 2) converted to per-degree,
        then applies a washout penalty.
        """
        ar = config.geometry.wing_aspect_ratio
        # Lifting-line slope in per-radian, then convert to per-degree
        a_rad = (2.0 * math.pi * ar) / (ar + 2.0)
        base = a_rad * (math.pi / 180.0)
        washout_penalty = 0.005 * config.geometry.wing_washout
        return max(base - washout_penalty, 0.06)

    def _cm_reflex_offset(self) -> float:
        """Estimate baseline pitching moment contribution from reflex."""

        reflex = config.airfoils.wing_reflex_percent
        return -0.012 - 0.0015 * reflex

    def _drag_offset(self) -> float:
        wetted_area_ft2 = config.geometry.wing_area + config.geometry.canard_area
        return 0.016 + 1e-4 * wetted_area_ft2

    def run_vspaero(
        self,
        alphas: Sequence[float] | None = None,
        cl_max: float = 1.4,
    ) -> List[AeroPolar]:
        """Generate aerodynamic polars for a set of angles of attack.

        Args:
            alphas: Sequence of angles of attack in degrees.
            cl_max: Maximum lift coefficient before stall rolloff (default 1.4
                    for Long-EZ airfoils).
        """

        alphas = list(alphas) if alphas is not None else [-4, 0, 4, 8, 12]
        cl_slope = self._cl_slope_per_deg()
        cm0 = self._cm_reflex_offset() - 0.002 * config.geometry.canard_incidence
        cd0 = self._drag_offset()

        # Induced drag parameters
        ar = config.geometry.wing_aspect_ratio
        e = config.geometry.wing_oswald_e

        # Stall angle where linear CL reaches cl_max
        alpha_stall = cl_max / cl_slope if cl_slope > 0 else 90.0

        results: List[AeroPolar] = []
        for alpha in alphas:
            cl_linear = cl_slope * alpha

            # Viterna post-stall model: gradual rolloff after cl_max
            if cl_linear > cl_max:
                excess = alpha - alpha_stall
                cl = cl_max - 0.05 * excess ** 2
            else:
                cl = cl_linear

            cm = cm0 - 0.0008 * alpha
            # Proper induced drag: CD_i = CL^2 / (pi * e * AR)
            cd = cd0 + cl ** 2 / (math.pi * e * ar)
            results.append(AeroPolar(alpha_deg=alpha, cl=cl, cm=cm, cd=cd))
        return results

    def lift_curve_slope(self, alphas: Sequence[float] | None = None) -> float:
        """Compute dCL/dalpha from generated polars."""

        polars = self.run_vspaero(alphas)
        if len(polars) < 2:
            return 0.0

        alpha0, alpha1 = polars[0].alpha_deg, polars[1].alpha_deg
        cl0, cl1 = polars[0].cl, polars[1].cl
        if alpha1 == alpha0:
            return 0.0
        return (cl1 - cl0) / (alpha1 - alpha0)

    def serialize_polars(
        self, alphas: Sequence[float] | None = None, target: Path | None = None
    ) -> Path:
        """Write polar data to JSON for downstream reporting."""

        polars = [p.__dict__ for p in self.run_vspaero(alphas)]
        target = target or (self.output_root / "vspaero_polars.json")
        with open(target, "w", encoding="utf-8") as f:
            json.dump(polars, f, indent=2)
        return target
