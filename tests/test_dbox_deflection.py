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


class TestNominalSparCheckDBox:
    """nominal_spar_check() must return D-box results alongside cap-only legacy keys."""

    def test_dbox_tip_deflection_key_exists(self):
        """nominal_spar_check() must return 'dbox_tip_deflection_in' key."""
        from core.simulation.fea_adapter import BeamFEAAdapter

        adapter = BeamFEAAdapter()
        result = adapter.nominal_spar_check()
        assert "dbox_tip_deflection_in" in result, (
            f"Missing 'dbox_tip_deflection_in' key. Keys: {list(result.keys())}"
        )

    def test_dbox_tip_deflection_range(self):
        """D-box tip deflection should be in 1-15 inch range."""
        from core.simulation.fea_adapter import BeamFEAAdapter

        adapter = BeamFEAAdapter()
        result = adapter.nominal_spar_check()
        defl = result["dbox_tip_deflection_in"]
        assert 1.0 <= defl <= 15.0, (
            f"D-box tip deflection = {defl:.2f} in, expected 1-15 in range"
        )

    def test_legacy_tip_deflection_preserved(self):
        """nominal_spar_check() must still return 'tip_deflection_in' (cap-only, backward compat)."""
        from core.simulation.fea_adapter import BeamFEAAdapter

        adapter = BeamFEAAdapter()
        result = adapter.nominal_spar_check()
        assert "tip_deflection_in" in result, (
            "Missing legacy 'tip_deflection_in' key — breaks RegressionRunner"
        )
        assert "max_stress_psi" in result, (
            "Missing legacy 'max_stress_psi' key — breaks RegressionRunner"
        )

    def test_dbox_spar_cap_tsai_wu_margin(self):
        """Spar cap Tsai-Wu margin must be positive (structure adequate)."""
        from core.simulation.fea_adapter import BeamFEAAdapter

        adapter = BeamFEAAdapter()
        result = adapter.nominal_spar_check()
        assert "dbox_spar_cap_tsai_wu_margin" in result
        assert result["dbox_spar_cap_tsai_wu_margin"] > 0, (
            f"Spar cap Tsai-Wu margin = {result['dbox_spar_cap_tsai_wu_margin']:.4f}, must be > 0"
        )

    def test_dbox_skin_tsai_wu_margin(self):
        """D-box skin Tsai-Wu margin must be positive."""
        from core.simulation.fea_adapter import BeamFEAAdapter

        adapter = BeamFEAAdapter()
        result = adapter.nominal_spar_check()
        assert "dbox_skin_tsai_wu_margin" in result
        assert result["dbox_skin_tsai_wu_margin"] > 0, (
            f"D-box skin Tsai-Wu margin = {result['dbox_skin_tsai_wu_margin']:.4f}, must be > 0"
        )

    def test_dbox_web_shear_margin(self):
        """Shear web margin must be positive."""
        from core.simulation.fea_adapter import BeamFEAAdapter

        adapter = BeamFEAAdapter()
        result = adapter.nominal_spar_check()
        assert "dbox_web_shear_margin" in result
        assert result["dbox_web_shear_margin"] > 0, (
            f"Web shear margin = {result['dbox_web_shear_margin']:.4f}, must be > 0"
        )

    def test_dbox_foam_compression_margin(self):
        """Foam compression margin must be positive."""
        from core.simulation.fea_adapter import BeamFEAAdapter

        adapter = BeamFEAAdapter()
        result = adapter.nominal_spar_check()
        assert "dbox_foam_compression_margin" in result
        assert result["dbox_foam_compression_margin"] > 0, (
            f"Foam compression margin = {result['dbox_foam_compression_margin']:.4f}, must be > 0"
        )


class TestDBoxFlutterIntegration:
    """FlutterEstimator must use D-box EI for bending frequency."""

    def test_bending_frequency_increases_with_dbox(self):
        """D-box EI >> cap-only EI means higher natural bending frequency.

        Cap-only EI ~ 2,500 lb-in^2, D-box EI ~ 101M lb-in^2.
        omega_h ~ sqrt(EI) so bending frequency should increase dramatically.
        The old cap-only bending frequency is ~0.13 Hz. D-box should be >> that.
        """
        from core.simulation.fea_adapter import FlutterEstimator

        est = FlutterEstimator()
        freq = est.bending_frequency_hz()
        # With D-box EI ~101M vs cap-only ~2500, freq should increase by sqrt(40000) ~ 200x
        # Old cap-only freq was ~0.13 Hz, so D-box should be >> 1 Hz
        assert freq > 1.0, (
            f"Bending frequency {freq:.2f} Hz too low — D-box EI should produce >> 1 Hz. "
            f"If this is ~0.13 Hz, FlutterEstimator is still using cap-only EI."
        )

    def test_flutter_check_safe_with_dbox(self):
        """Flutter check must pass with D-box model (improved stiffness)."""
        from core.simulation.fea_adapter import FlutterEstimator

        est = FlutterEstimator()
        result = est.check_flutter()
        assert result["is_safe"], (
            f"Flutter not safe: speed={result['flutter_speed_ktas']:.0f} KTAS, "
            f"required={result['required_speed_ktas']:.0f} KTAS"
        )

    def test_frequency_ratio_above_one(self):
        """Torsion/bending frequency ratio should be > 1.0 for composite wings.

        With D-box EI increasing bending frequency significantly,
        the ratio torsion/bending should be > 1.0 (typical for well-designed wings).
        """
        from core.simulation.fea_adapter import FlutterEstimator

        est = FlutterEstimator()
        result = est.check_flutter()
        ratio = result["frequency_ratio"]
        assert ratio > 1.0, (
            f"Frequency ratio {ratio:.2f} should be > 1.0 with D-box model. "
            f"Bending={result['bending_freq_hz']:.2f} Hz, "
            f"Torsion={result['torsion_freq_hz']:.2f} Hz"
        )


class TestDBoxWeight:
    """D-box weight estimate must be in reasonable range."""

    def test_dbox_weight_method_exists(self):
        """DBoxBeamAdapter must have estimate_dbox_weight_lb method."""
        from core.simulation.fea_adapter import DBoxBeamAdapter

        adapter = DBoxBeamAdapter()
        assert hasattr(adapter, "estimate_dbox_weight_lb"), (
            "DBoxBeamAdapter missing estimate_dbox_weight_lb method"
        )

    def test_dbox_weight_range(self):
        """D-box weight (skins + web, one wing half) should be 5-25 lb.

        This is the structural glass weight for the D-box skins and web only,
        excluding spar caps. For a Long-EZ wing with ~13 ft half-span,
        2-ply BID skins over 25% chord at 0.065 lb/in^3 density, ~8 lb
        is physically correct (thin skins over relatively small chord fraction).
        """
        from core.simulation.fea_adapter import DBoxBeamAdapter

        adapter = DBoxBeamAdapter()
        half_span = config.geometry.wing_span / 2
        weight = adapter.estimate_dbox_weight_lb(half_span)
        assert 5.0 <= weight <= 25.0, (
            f"D-box weight = {weight:.2f} lb, expected 5-25 lb per wing half"
        )


class TestDBoxExports:
    """core.simulation must export D-box classes."""

    def test_dbox_section_importable(self):
        """DBoxSection must be importable from core.simulation."""
        from core.simulation import DBoxSection
        assert DBoxSection is not None

    def test_dbox_result_importable(self):
        """DBoxResult must be importable from core.simulation."""
        from core.simulation import DBoxResult
        assert DBoxResult is not None

    def test_dbox_beam_adapter_importable(self):
        """DBoxBeamAdapter must be importable from core.simulation."""
        from core.simulation import DBoxBeamAdapter
        assert DBoxBeamAdapter is not None
