"""
D-Box Composite Section Model Validation
==========================================

Tests for the DBoxSection dataclass and DBoxBeamAdapter that compute realistic
wing tip deflection via spanwise-varying EI and numerical integration.

The cap-only I-beam model produces I = 0.000895 in^4 (EI ~ 2,500 lb-in^2),
yielding absurd 89,169" deflection under 450 lbf elliptic load at half-span.

The D-box adds upper/lower skins (BID) from LE to 25% chord plus a shear web,
increasing I by 3-4 orders of magnitude and producing realistic 5-15" deflection.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Mock cadquery before importing core modules (cadquery is a heavy C++ dependency)
sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

from config import config


class TestDBoxConfigFields:
    """Config must parameterize D-box geometry from SSOT."""

    def test_dbox_chord_fraction_exists(self):
        """MaterialParams must have dbox_chord_fraction field."""
        assert hasattr(config.materials, "dbox_chord_fraction"), (
            "MaterialParams missing dbox_chord_fraction"
        )
        assert config.materials.dbox_chord_fraction == 0.25

    def test_dbox_skin_plies_exists(self):
        """MaterialParams must have dbox_skin_plies field."""
        assert hasattr(config.materials, "dbox_skin_plies"), (
            "MaterialParams missing dbox_skin_plies"
        )
        assert config.materials.dbox_skin_plies == 2

    def test_dbox_web_foam_thickness_exists(self):
        """MaterialParams must have dbox_web_foam_thickness_in field."""
        assert hasattr(config.materials, "dbox_web_foam_thickness_in"), (
            "MaterialParams missing dbox_web_foam_thickness_in"
        )
        assert config.materials.dbox_web_foam_thickness_in == 0.25

    def test_spar_cap_ply_schedule_exists(self):
        """MaterialParams must have spar_cap_ply_schedule field."""
        assert hasattr(config.materials, "spar_cap_ply_schedule"), (
            "MaterialParams missing spar_cap_ply_schedule"
        )
        schedule = config.materials.spar_cap_ply_schedule
        assert isinstance(schedule, list)
        assert len(schedule) >= 5, "Schedule must have at least 5 stations"
        assert schedule[0] == 17, "Root ply count should be 17"


class TestDBoxSectionEI:
    """DBoxSection must compute EI orders of magnitude higher than cap-only."""

    def test_root_ei_exceeds_one_million(self):
        """DBoxSection at root chord (68") must compute EI > 1e6 lb-in^2.

        Cap-only EI ~ 2,500 lb-in^2 (I = 0.000895 in^4, E = 2.8e6 psi).
        D-box EI must be 3-4 orders of magnitude larger.
        """
        from core.simulation.fea_adapter import DBoxSection

        section = DBoxSection(
            chord_in=config.geometry.wing_root_chord,  # 68"
            spar_cap_plies=config.materials.spar_cap_plies,  # 17
        )
        ei = section.ei_bending
        assert ei > 1e6, (
            f"Root D-box EI = {ei:.0f} lb-in^2, expected > 1,000,000.\n"
            f"Cap-only EI is ~2,500. D-box should be 3-4 orders of magnitude larger."
        )

    def test_tip_ei_less_than_root(self):
        """DBoxSection at tip chord (32") must have EI < root EI (taper check)."""
        from core.simulation.fea_adapter import DBoxSection

        root_section = DBoxSection(
            chord_in=config.geometry.wing_root_chord,
            spar_cap_plies=config.materials.spar_cap_plies,
        )
        tip_section = DBoxSection(
            chord_in=config.geometry.wing_tip_chord,
            spar_cap_plies=config.materials.spar_cap_ply_schedule[-1],
        )
        assert tip_section.ei_bending < root_section.ei_bending, (
            f"Tip EI ({tip_section.ei_bending:.0f}) should be less than "
            f"root EI ({root_section.ei_bending:.0f}) due to chord taper and ply schedule."
        )

    def test_ei_positive(self):
        """All EI components must be positive (physical sanity)."""
        from core.simulation.fea_adapter import DBoxSection

        section = DBoxSection(
            chord_in=50.0,
            spar_cap_plies=14,
        )
        assert section.ei_bending > 0, "EI must be positive"


class TestDBoxBeamAdapter:
    """DBoxBeamAdapter must produce realistic deflection via spanwise-varying EI."""

    def test_elliptic_dbox_deflection_range(self):
        """analyze_elliptic_dbox(span=158.4, load=450) produces realistic tip deflection.

        Half-span = 158.4 in, elliptic 450 lbf total load.
        Cap-only model gives 89,169" (absurd). D-box should give 1-15".
        The D-box EI (10-100M lb-in^2) produces 2-3" deflection at 450 lbf,
        which is realistic for a composite Long-EZ wing structure.
        """
        from core.simulation.fea_adapter import DBoxBeamAdapter

        adapter = DBoxBeamAdapter()
        half_span = config.geometry.wing_span / 2  # 158.4 in
        result = adapter.analyze_elliptic_dbox(span_in=half_span, total_load_lbf=450.0)

        assert 1.0 <= result.tip_deflection_in <= 15.0, (
            f"D-box tip deflection = {result.tip_deflection_in:.2f} in, "
            f"expected 1-15 in range.\n"
            f"Cap-only gives 89,169 in. D-box EI is 3-4 orders of magnitude larger."
        )

    def test_minimum_stations(self):
        """DBoxBeamAdapter must use at least 5 spanwise stations."""
        from core.simulation.fea_adapter import DBoxBeamAdapter

        adapter = DBoxBeamAdapter()
        half_span = config.geometry.wing_span / 2
        result = adapter.analyze_elliptic_dbox(span_in=half_span, total_load_lbf=450.0)

        assert result.n_stations >= 5, (
            f"Used {result.n_stations} stations, need at least 5 for accuracy"
        )

    def test_station_ei_varies(self):
        """EI must vary along the span (not constant — tapered wing)."""
        from core.simulation.fea_adapter import DBoxBeamAdapter

        adapter = DBoxBeamAdapter()
        half_span = config.geometry.wing_span / 2
        result = adapter.analyze_elliptic_dbox(span_in=half_span, total_load_lbf=450.0)

        ei_values = result.station_ei
        assert len(set(ei_values)) > 1, (
            "All station EI values are identical — section properties must vary with taper"
        )
        # Root EI should be largest (widest chord, most plies)
        assert ei_values[0] == max(ei_values), (
            f"Root EI ({ei_values[0]:.0f}) should be the maximum, "
            f"but max is {max(ei_values):.0f}"
        )

    def test_result_has_stress(self):
        """DBoxResult must include max bending stress."""
        from core.simulation.fea_adapter import DBoxBeamAdapter

        adapter = DBoxBeamAdapter()
        half_span = config.geometry.wing_span / 2
        result = adapter.analyze_elliptic_dbox(span_in=half_span, total_load_lbf=450.0)

        assert result.max_stress_psi > 0, "Max bending stress must be positive"

    def test_deflection_scales_with_load(self):
        """Doubling load should approximately double deflection (linear theory)."""
        from core.simulation.fea_adapter import DBoxBeamAdapter

        adapter = DBoxBeamAdapter()
        half_span = config.geometry.wing_span / 2

        result_1 = adapter.analyze_elliptic_dbox(span_in=half_span, total_load_lbf=225.0)
        result_2 = adapter.analyze_elliptic_dbox(span_in=half_span, total_load_lbf=450.0)

        ratio = result_2.tip_deflection_in / result_1.tip_deflection_in
        assert abs(ratio - 2.0) < 0.05, (
            f"Deflection should scale linearly. Ratio: {ratio:.4f} (expected ~2.0)"
        )
