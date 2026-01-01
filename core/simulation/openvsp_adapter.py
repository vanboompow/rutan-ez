"""Lightweight OpenVSP adapter for aerodynamic regression tests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

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
        """Estimate lift-curve slope (CL/deg) with washout sensitivity."""

        base = 0.1  # per degree for slender, low-speed wings
        washout_penalty = 0.005 * config.geometry.wing_washout
        return max(base - washout_penalty, 0.06)

    def _cm_reflex_offset(self) -> float:
        """Estimate baseline pitching moment contribution from reflex."""

        reflex = config.airfoils.wing_reflex_percent
        return -0.012 - 0.0015 * reflex

    def _drag_offset(self) -> float:
        wetted_area_ft2 = (config.geometry.wing_area + config.geometry.canard_area)
        return 0.016 + 1e-4 * wetted_area_ft2

    def run_vspaero(self, alphas: Sequence[float] | None = None) -> List[AeroPolar]:
        """Generate aerodynamic polars for a set of angles of attack."""

        alphas = list(alphas) if alphas is not None else [-4, 0, 4, 8, 12]
        cl_slope = self._cl_slope_per_deg()
        cm0 = self._cm_reflex_offset() - 0.002 * config.geometry.canard_incidence
        cd0 = self._drag_offset()

        results: List[AeroPolar] = []
        for alpha in alphas:
            cl = cl_slope * alpha
            cm = cm0 - 0.0008 * alpha
            cd = cd0 + 0.01 * (cl ** 2) + 0.0004 * abs(alpha)
            results.append(AeroPolar(alpha_deg=alpha, cl=cl, cm=cm, cd=cd))
        return results

    def lift_curve_slope(self, alphas: Iterable[float] | None = None) -> float:
        """Compute dCL/dalpha from generated polars."""

        polars = self.run_vspaero(alphas)
        if len(polars) < 2:
            return 0.0

        alpha0, alpha1 = polars[0].alpha_deg, polars[1].alpha_deg
        cl0, cl1 = polars[0].cl, polars[1].cl
        if alpha1 == alpha0:
            return 0.0
        return (cl1 - cl0) / (alpha1 - alpha0)

    def serialize_polars(self, alphas: Sequence[float] | None = None, target: Path | None = None) -> Path:
        """Write polar data to JSON for downstream reporting."""

        polars = [p.__dict__ for p in self.run_vspaero(alphas)]
        target = target or (self.output_root / "vspaero_polars.json")
        with open(target, "w", encoding="utf-8") as f:
            json.dump(polars, f, indent=2)
        return target
