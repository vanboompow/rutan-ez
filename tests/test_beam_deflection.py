"""
A3: Beam Deflection Validation for Distributed vs Point Loads
==============================================================

Tests that the FEA adapter correctly handles both point loads and distributed
loads on the wing spar.

Euler-Bernoulli beam theory:
  - Point load at tip:        delta = P * L^3 / (3 * E * I)
  - Uniform distributed load: delta = w * L^4 / (8 * E * I)

The ratio of distributed to point load deflection (for equivalent total load):
  distributed / point = (wL^4 / 8EI) / (PL^3 / 3EI)
  where w = P/L (same total load), so:
  = (P/L * L^4 / 8EI) / (PL^3 / 3EI)
  = (PL^3 / 8EI) / (PL^3 / 3EI)
  = 3/8 = 0.375

The current code in core/simulation/fea_adapter.py only has analyze_cantilever
(point load). It lacks an analyze_distributed method for uniform loading.

For a wing spar, the aerodynamic load is distributed (roughly elliptical),
so using only point-load deflection significantly overestimates deflection.

Test A3a: Verify analyze_cantilever gives correct values for known inputs.
Test A3b: Verify that analyze_distributed method exists and gives correct values.
          (This should FAIL because the method doesn't exist yet.)
Test A3c: Verify the 3/8 ratio between distributed and point load deflection.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Mock cadquery before importing core modules (cadquery is a heavy C++ dependency)
sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

import math
import pytest


class TestPointLoadDeflection:
    """Verify existing analyze_cantilever against analytical solutions."""

    # Known spar section from config defaults
    WIDTH = 3.0        # inches
    HEIGHT = 0.153     # 17 plies * 0.009 in/ply
    MODULUS = 2.8e6    # psi (UNI glass bending modulus)

    @property
    def inertia(self) -> float:
        """I = bh^3/12"""
        return (self.WIDTH * self.HEIGHT**3) / 12.0

    def test_known_cantilever_deflection(self):
        """Verify point-load deflection against hand calculation.

        For P=450 lbf at L=79.2 in (half-span of 158.4/2 = 79.2):
            delta = P * L^3 / (3 * E * I)
        """
        from core.simulation.fea_adapter import BeamFEAAdapter, BeamSection

        section = BeamSection(
            width_in=self.WIDTH,
            height_in=self.HEIGHT,
            modulus_psi=self.MODULUS,
        )
        adapter = BeamFEAAdapter(section=section)

        P = 450.0   # lbf
        L = 79.2     # inches (half-span)

        result = adapter.analyze_cantilever(span_in=L, tip_load_lbf=P)

        # Analytical solution
        I = self.inertia
        expected_deflection = (P * L**3) / (3 * self.MODULUS * I)

        assert abs(result.tip_deflection_in - expected_deflection) / expected_deflection < 0.001, (
            f"Point load deflection mismatch:\n"
            f"  Computed: {result.tip_deflection_in:.4f} in\n"
            f"  Expected: {expected_deflection:.4f} in\n"
            f"  Error: {abs(result.tip_deflection_in - expected_deflection)/expected_deflection*100:.2f}%"
        )

    def test_known_cantilever_stress(self):
        """Verify max bending stress against hand calculation.

        sigma_max = M * c / I = P * L * (h/2) / I
        """
        from core.simulation.fea_adapter import BeamFEAAdapter, BeamSection

        section = BeamSection(
            width_in=self.WIDTH,
            height_in=self.HEIGHT,
            modulus_psi=self.MODULUS,
        )
        adapter = BeamFEAAdapter(section=section)

        P = 450.0
        L = 79.2

        result = adapter.analyze_cantilever(span_in=L, tip_load_lbf=P)

        I = self.inertia
        c = self.HEIGHT / 2
        expected_stress = (P * L * c) / I

        assert abs(result.max_stress_psi - expected_stress) / expected_stress < 0.001, (
            f"Max stress mismatch:\n"
            f"  Computed: {result.max_stress_psi:.1f} psi\n"
            f"  Expected: {expected_stress:.1f} psi"
        )

    def test_deflection_scales_with_load(self):
        """Doubling the load should double the deflection (linear theory)."""
        from core.simulation.fea_adapter import BeamFEAAdapter, BeamSection

        section = BeamSection(
            width_in=self.WIDTH,
            height_in=self.HEIGHT,
            modulus_psi=self.MODULUS,
        )
        adapter = BeamFEAAdapter(section=section)

        L = 79.2
        result_1 = adapter.analyze_cantilever(span_in=L, tip_load_lbf=100.0)
        result_2 = adapter.analyze_cantilever(span_in=L, tip_load_lbf=200.0)

        ratio = result_2.tip_deflection_in / result_1.tip_deflection_in
        assert abs(ratio - 2.0) < 0.001, (
            f"Deflection should scale linearly with load. Ratio: {ratio:.6f}"
        )


class TestDistributedLoadDeflection:
    """Test distributed load analysis (currently missing from BeamFEAAdapter)."""

    WIDTH = 3.0
    HEIGHT = 0.153
    MODULUS = 2.8e6

    @property
    def inertia(self) -> float:
        return (self.WIDTH * self.HEIGHT**3) / 12.0

    def test_distributed_method_exists(self):
        """BeamFEAAdapter must have an analyze_distributed method.

        The current code only has analyze_cantilever (point load).
        For wing spar analysis, a distributed load model is essential because
        aerodynamic lift is distributed along the span.

        This test should FAIL until analyze_distributed is implemented.
        """
        from core.simulation.fea_adapter import BeamFEAAdapter, BeamSection

        section = BeamSection(
            width_in=self.WIDTH,
            height_in=self.HEIGHT,
            modulus_psi=self.MODULUS,
        )
        adapter = BeamFEAAdapter(section=section)

        assert hasattr(adapter, 'analyze_distributed'), (
            "BeamFEAAdapter is missing 'analyze_distributed' method. "
            "Wing spar analysis requires distributed load capability: "
            "delta = w * L^4 / (8 * E * I)"
        )

    def test_distributed_load_known_value(self):
        """Verify distributed load deflection against analytical solution.

        For uniform load w (lbf/in) on cantilever of length L:
            delta_max = w * L^4 / (8 * E * I)

        The API takes total_load_lbf (w = total/L internally).
        """
        from core.simulation.fea_adapter import BeamFEAAdapter, BeamSection

        section = BeamSection(
            width_in=self.WIDTH,
            height_in=self.HEIGHT,
            modulus_psi=self.MODULUS,
        )
        adapter = BeamFEAAdapter(section=section)

        L = 79.2     # inches (half-span)
        P_total = 450.0  # total distributed load (lbf)
        w = P_total / L  # lbf/in

        result = adapter.analyze_distributed(span_in=L, total_load_lbf=P_total)

        I = self.inertia
        expected_deflection = (w * L**4) / (8 * self.MODULUS * I)

        assert abs(result.tip_deflection_in - expected_deflection) / expected_deflection < 0.01, (
            f"Distributed load deflection mismatch:\n"
            f"  Computed: {result.tip_deflection_in:.4f} in\n"
            f"  Expected: {expected_deflection:.4f} in"
        )

    def test_distributed_vs_point_load_ratio(self):
        """For the same total load, distributed deflection is 3/8 of point load.

        Point: delta_P = P*L^3 / (3*E*I)
        Distributed (w=P/L): delta_w = (P/L)*L^4 / (8*E*I) = P*L^3 / (8*E*I)

        Ratio: delta_w / delta_P = (P*L^3 / 8EI) / (P*L^3 / 3EI) = 3/8 = 0.375
        """
        from core.simulation.fea_adapter import BeamFEAAdapter, BeamSection

        section = BeamSection(
            width_in=self.WIDTH,
            height_in=self.HEIGHT,
            modulus_psi=self.MODULUS,
        )
        adapter = BeamFEAAdapter(section=section)

        P = 450.0
        L = 79.2

        result_point = adapter.analyze_cantilever(span_in=L, tip_load_lbf=P)
        result_dist = adapter.analyze_distributed(span_in=L, total_load_lbf=P)

        ratio = result_dist.tip_deflection_in / result_point.tip_deflection_in
        expected_ratio = 3.0 / 8.0  # 0.375

        assert abs(ratio - expected_ratio) < 0.01, (
            f"Distributed/point deflection ratio should be 3/8 = 0.375\n"
            f"  Got: {ratio:.6f}\n"
            f"  Point deflection: {result_point.tip_deflection_in:.4f} in\n"
            f"  Distributed deflection: {result_dist.tip_deflection_in:.4f} in"
        )


class TestBeamSectionProperties:
    """Sanity checks on the BeamSection data class."""

    def test_inertia_calculation(self):
        """Verify I = bh^3/12 for rectangular section."""
        from core.simulation.fea_adapter import BeamSection

        section = BeamSection(width_in=3.0, height_in=0.153, modulus_psi=2.8e6)
        expected = (3.0 * 0.153**3) / 12.0
        assert abs(section.inertia - expected) < 1e-12, (
            f"Inertia mismatch: {section.inertia} vs {expected}"
        )

    def test_spar_section_from_config(self):
        """Verify default spar section matches config values."""
        from core.simulation.fea_adapter import BeamFEAAdapter
        from config import config

        adapter = BeamFEAAdapter()
        expected_height = config.materials.spar_cap_plies * config.materials.uni_ply_thickness

        assert abs(adapter.section.height_in - expected_height) < 1e-6, (
            f"Spar height should be {expected_height} "
            f"({config.materials.spar_cap_plies} plies x "
            f"{config.materials.uni_ply_thickness} in), "
            f"got {adapter.section.height_in}"
        )
        assert abs(adapter.section.width_in - config.materials.spar_cap_width) < 1e-6
