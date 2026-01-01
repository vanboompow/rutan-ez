"""Physics regression scenarios anchored to configuration baselines."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

from config import config
from .fea_adapter import BeamFEAAdapter
from .openvsp_adapter import OpenVSPAdapter


@dataclass
class ScenarioResult:
    name: str
    metrics: Dict[str, float]


@dataclass
class RegressionScenario:
    name: str
    description: str
    evaluate: Callable[[OpenVSPAdapter, BeamFEAAdapter], ScenarioResult]


class RegressionRunner:
    """Run deterministic physics regressions for CI validation."""

    def __init__(self, tolerance: float = 0.05):
        self.tolerance = tolerance
        self.aero = OpenVSPAdapter()
        self.fea = BeamFEAAdapter()
        self.scenarios: List[RegressionScenario] = [
            RegressionScenario(
                name="wing_reflex_moment",
                description="Pitching moment from wing reflex and canard incidence",
                evaluate=self._wing_reflex_moment,
            ),
            RegressionScenario(
                name="lift_curve_slope",
                description="Lift-curve slope derived from VSPAERO polars",
                evaluate=self._lift_curve_slope,
            ),
            RegressionScenario(
                name="spar_tip_deflection",
                description="Main spar tip deflection under representative gust load",
                evaluate=self._spar_tip_deflection,
            ),
        ]

    def _wing_reflex_moment(
        self, aero: OpenVSPAdapter, _: BeamFEAAdapter
    ) -> ScenarioResult:
        polars = aero.run_vspaero([0])
        cm0 = polars[0].cm if polars else 0.0
        washout = config.geometry.wing_washout
        metric = cm0 - 0.0005 * washout
        return ScenarioResult(
            name="wing_reflex_moment",
            metrics={"cm_at_trim": metric},
        )

    def _lift_curve_slope(
        self, aero: OpenVSPAdapter, _: BeamFEAAdapter
    ) -> ScenarioResult:
        slope = aero.lift_curve_slope([-4, 0])
        return ScenarioResult(
            name="lift_curve_slope",
            metrics={"cl_per_deg": slope},
        )

    def _spar_tip_deflection(
        self, _: OpenVSPAdapter, fea: BeamFEAAdapter
    ) -> ScenarioResult:
        spar = fea.nominal_spar_check()
        jig = fea.jig_flatness_check()
        combined_deflection = spar["tip_deflection_in"] + 0.1 * jig["tip_deflection_in"]
        return ScenarioResult(
            name="spar_tip_deflection",
            metrics={
                "tip_deflection_in": combined_deflection,
                "spar_stress_psi": spar["max_stress_psi"],
            },
        )

    def run(self) -> List[ScenarioResult]:
        """Execute all regression scenarios."""

        results: List[ScenarioResult] = []
        for scenario in self.scenarios:
            results.append(scenario.evaluate(self.aero, self.fea))
        return results

    def to_serializable(
        self, results: Iterable[ScenarioResult]
    ) -> Dict[str, Dict[str, float]]:
        return {res.name: res.metrics for res in results}

    def load_baseline(self, baseline_path: Path) -> Dict[str, Dict[str, float]]:
        with open(baseline_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def compare_to_baseline(
        self,
        baseline_path: Path,
        report_dir: Path,
    ) -> Tuple[bool, Dict[str, Dict[str, float]], List[str]]:
        """Compare regression results to stored baseline with tolerance."""

        report_dir.mkdir(parents=True, exist_ok=True)
        baseline = self.load_baseline(baseline_path)
        current = self.to_serializable(self.run())

        failures: List[str] = []
        for name, metrics in current.items():
            if name not in baseline:
                failures.append(f"Missing baseline for {name}")
                continue

            for metric_name, value in metrics.items():
                if metric_name not in baseline[name]:
                    failures.append(f"Missing baseline metric {metric_name} for {name}")
                    continue

                reference = baseline[name][metric_name]
                if reference == 0:
                    deviation = abs(value - reference)
                else:
                    deviation = abs(value - reference) / abs(reference)

                if deviation > self.tolerance:
                    failures.append(
                        f"{name}:{metric_name} deviated by {deviation:.2%} (value {value:.4f} vs {reference:.4f})"
                    )

        report = {
            "baseline": baseline,
            "current": current,
            "tolerance": self.tolerance,
            "failures": failures,
            "status": "fail" if failures else "pass",
        }

        json_report = report_dir / "physics_validation_report.json"
        with open(json_report, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return (len(failures) == 0, current, failures)
