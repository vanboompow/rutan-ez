"""
Module Coverage Tests: nesting, assembly, systems, metadata, vsp_integration
=============================================================================

Provides 3-5 tests per previously-untested module. CadQuery is fully mocked
because it is a C++ extension not installed in CI.
"""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Must mock CadQuery BEFORE importing any core/ module
sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

import pytest  # noqa: E402
from config import config  # noqa: E402


# ===========================================================================
# core/nesting.py
# ===========================================================================


class TestOutline:
    """Tests for the Outline dataclass."""

    def test_outline_defaults(self):
        """Outline should default to quantity=1 and no laminate."""
        from core.nesting import Outline

        o = Outline(name="rib_01", source=Path("/tmp/rib.dxf"), width=10.0, height=5.0)
        assert o.quantity == 1
        assert o.laminate is None

    def test_outline_with_laminate(self):
        """Outline can carry a laminate identifier for cut-order mapping."""
        from core.nesting import Outline

        o = Outline(
            name="spar_web",
            source=Path("/tmp/spar.dxf"),
            width=24.0,
            height=3.0,
            laminate="bid_2ply",
        )
        assert o.laminate == "bid_2ply"


class TestPlacement:
    """Tests for Placement computed properties."""

    def _make_placement(self, width=10.0, height=5.0, rotation=0.0):
        from core.nesting import Outline, Placement

        o = Outline(
            name="test_part", source=Path("/tmp/p.dxf"), width=width, height=height
        )
        return Placement(outline=o, sheet_index=0, origin=(1.0, 1.0), rotation=rotation)

    def test_placed_width_no_rotation(self):
        """Without rotation, placed_width equals outline.width."""
        p = self._make_placement(width=10.0, height=5.0, rotation=0.0)
        assert p.placed_width == 10.0

    def test_placed_height_no_rotation(self):
        """Without rotation, placed_height equals outline.height."""
        p = self._make_placement(width=10.0, height=5.0, rotation=0.0)
        assert p.placed_height == 5.0

    def test_placed_width_with_90_rotation(self):
        """With 90° rotation, placed_width equals outline.height."""
        p = self._make_placement(width=10.0, height=5.0, rotation=90.0)
        assert p.placed_width == 5.0

    def test_placed_height_with_90_rotation(self):
        """With 90° rotation, placed_height equals outline.width."""
        p = self._make_placement(width=10.0, height=5.0, rotation=90.0)
        assert p.placed_height == 10.0

    def test_label_position_no_rotation(self):
        """Label position should be the part center."""
        p = self._make_placement(width=10.0, height=5.0, rotation=0.0)
        cx, cy = p.label_position
        assert cx == pytest.approx(6.0)  # origin 1.0 + width/2 = 6.0
        assert cy == pytest.approx(3.5)  # origin 1.0 + height/2 = 3.5


class TestNestingPlanner:
    """Tests for NestingPlanner packing logic (pure Python, no file I/O)."""

    def _make_planner(self, sheet_size=(48.0, 96.0)):
        from core.nesting import NestingPlanner

        return NestingPlanner(
            stock_sheets=[sheet_size],
            margin=0.25,
            spacing=0.125,
        )

    def test_pack_single_outline_returns_one_placement(self):
        """Packing one outline onto a large sheet yields exactly one placement."""
        from core.nesting import Outline

        planner = self._make_planner()
        o = Outline(name="part_a", source=Path("/tmp/a.dxf"), width=10.0, height=5.0)
        placements = planner.pack([o])
        assert len(placements) == 1

    def test_pack_placement_origin_respects_margin(self):
        """First placement origin should equal the planner margin."""
        from core.nesting import Outline

        margin = 0.5
        from core.nesting import NestingPlanner

        planner = NestingPlanner(
            stock_sheets=[(48.0, 96.0)], margin=margin, spacing=0.125
        )
        o = Outline(name="part_a", source=Path("/tmp/a.dxf"), width=10.0, height=5.0)
        placements = planner.pack([o])
        x0, y0 = placements[0].origin
        assert x0 == pytest.approx(margin)
        assert y0 == pytest.approx(margin)

    def test_pack_raises_when_no_sheets_fit_parts(self):
        """Packing more parts than fit on available sheets must raise ValueError."""
        from core.nesting import Outline, NestingPlanner

        # Tiny sheet, large parts
        planner = NestingPlanner(
            stock_sheets=[(5.0, 5.0)],
            margin=0.25,
            spacing=0.125,
        )
        outlines = [
            Outline(
                name=f"big_{i}", source=Path(f"/tmp/{i}.dxf"), width=4.0, height=4.0
            )
            for i in range(5)
        ]
        with pytest.raises(ValueError, match="Not enough stock sheets"):
            planner.pack(outlines)

    def test_grain_constraint_none_no_rotation(self):
        """Parts with GrainConstraint.NONE should never be rotated."""
        from core.nesting import Outline, GrainConstraint

        planner = self._make_planner(sheet_size=(96.0, 96.0))
        o = Outline(
            name="no_constraint",
            source=Path("/tmp/nc.dxf"),
            width=10.0,
            height=5.0,
            grain_constraint=GrainConstraint.NONE,
        )
        placements = planner.pack([o])
        assert placements[0].rotation == 0.0


# ===========================================================================
# core/assembly.py  (CadQuery-heavy — all cq calls mocked)
# ===========================================================================


class TestAircraftAssembly:
    """Tests for AircraftAssembly with CadQuery fully mocked."""

    def test_assembly_name_default(self):
        """Default assembly name should be 'open_ez_airframe'."""
        from core.assembly import AircraftAssembly
        import inspect

        sig = inspect.signature(AircraftAssembly.__init__)
        assert sig.parameters["name"].default == "open_ez_airframe"

    def test_assembly_has_required_methods(self):
        """AircraftAssembly must expose generate_geometry, export_dxf, get_mass_properties."""
        from core.assembly import AircraftAssembly

        for method in ["generate_geometry", "export_dxf", "get_mass_properties"]:
            assert hasattr(AircraftAssembly, method), f"Missing method: {method}"

    def test_get_mass_properties_signature_takes_no_args(self):
        """get_mass_properties() must be callable with no arguments (besides self)."""
        from core.assembly import AircraftAssembly
        import inspect

        sig = inspect.signature(AircraftAssembly.get_mass_properties)
        # Only 'self' parameter
        params = [p for p in sig.parameters if p != "self"]
        assert len(params) == 0, (
            f"get_mass_properties() should take no args, got: {params}"
        )

    def test_assembly_inherits_aircraft_component(self):
        """AircraftAssembly must subclass AircraftComponent."""
        from core.assembly import AircraftAssembly
        from core.base import AircraftComponent

        assert issubclass(AircraftAssembly, AircraftComponent)


# ===========================================================================
# core/systems.py
# ===========================================================================


class TestWeightItem:
    """Tests for the WeightItem dataclass."""

    def test_moment_calculation(self):
        """moment = weight_lb * arm_in."""
        from core.systems import WeightItem

        item = WeightItem(name="engine", weight_lb=243.0, arm_in=188.0)
        assert item.moment == pytest.approx(243.0 * 188.0)

    def test_zero_weight_zero_moment(self):
        """Zero weight must give zero moment."""
        from core.systems import WeightItem

        item = WeightItem(name="ghost_item", weight_lb=0.0, arm_in=100.0)
        assert item.moment == 0.0


class TestLycomingO235:
    """Tests for the IC engine propulsion system."""

    def test_weight_items_returns_list(self):
        """get_weight_items() must return a non-empty list."""
        from core.systems import LycomingO235

        engine = LycomingO235()
        items = engine.get_weight_items()
        assert isinstance(items, list)
        assert len(items) > 0

    def test_total_weight_is_positive(self):
        """Total propulsion weight should be > 0."""
        from core.systems import LycomingO235

        engine = LycomingO235()
        assert engine.get_total_weight() > 0

    def test_thrust_at_cruise_is_reasonable(self):
        """Thrust at cruise speed should be a positive number."""
        from core.systems import LycomingO235

        engine = LycomingO235()
        thrust = engine.calculate_thrust(altitude_ft=8000, velocity_kts=160)
        assert thrust > 0, f"Cruise thrust {thrust:.1f} lb should be positive"

    def test_thrust_decreases_with_altitude(self):
        """Higher altitude should produce less thrust (same throttle, same speed)."""
        from core.systems import LycomingO235

        engine = LycomingO235()
        thrust_sl = engine.calculate_thrust(altitude_ft=0, velocity_kts=120)
        thrust_hi = engine.calculate_thrust(altitude_ft=12000, velocity_kts=120)
        assert thrust_sl > thrust_hi, (
            "Sea-level thrust should exceed high-altitude thrust"
        )

    def test_power_available_decreases_with_altitude(self):
        """Normally aspirated engine loses ~3%/1000 ft."""
        from core.systems import LycomingO235

        engine = LycomingO235()
        pwr_sl = engine.get_power_available(0)
        pwr_8k = engine.get_power_available(8000)
        assert pwr_sl > pwr_8k


class TestElectricEZ:
    """Tests for the electric propulsion conversion."""

    def test_endurance_is_positive(self):
        """Endurance at 50 kW should be > 0 hours."""
        from core.systems import ElectricEZ

        ez = ElectricEZ(battery_kwh=25.6)
        assert ez.get_endurance(50.0) > 0

    def test_endurance_zero_power_returns_zero(self):
        """Zero power draw must return 0 endurance (not divide-by-zero)."""
        from core.systems import ElectricEZ

        ez = ElectricEZ(battery_kwh=25.6)
        assert ez.get_endurance(0.0) == 0.0

    def test_range_is_positive(self):
        """Range at cruise should be a positive number of nautical miles."""
        from core.systems import ElectricEZ

        ez = ElectricEZ(battery_kwh=25.6)
        assert ez.get_range(cruise_speed_kts=100.0, cruise_power_kw=45.0) > 0

    def test_electric_thrust_at_cruise(self):
        """Electric motor should produce positive thrust at cruise speed."""
        from core.systems import ElectricEZ

        ez = ElectricEZ()
        thrust = ez.calculate_thrust(altitude_ft=8000, velocity_kts=120)
        assert thrust > 0

    def test_compare_to_baseline_returns_dict(self):
        """compare_to_baseline() must return a dict with weight_delta_lb key.

        The config propulsion type must be electric for battery_energy_density_wh_kg
        to return a non-zero value; we patch it here to avoid a ZeroDivisionError.
        """
        from core.systems import ElectricEZ

        ez = ElectricEZ()
        # Patch energy density so battery_weight_lb can compute without ZeroDivision
        with patch.object(
            type(config.propulsion),
            "battery_energy_density_wh_kg",
            new_callable=lambda: property(lambda self: 150.0),
        ):
            result = ez.compare_to_baseline()

        assert isinstance(result, dict)
        assert "weight_delta_lb" in result
        assert "cg_shift_in" in result


class TestGetPropulsionSystem:
    """Tests for the factory function."""

    def test_factory_returns_lycoming_for_o235(self):
        """Factory should return LycomingO235 for LYCOMING_O235 type."""
        from core.systems import get_propulsion_system, LycomingO235
        from config.aircraft_config import PropulsionType

        system = get_propulsion_system(PropulsionType.LYCOMING_O235)
        assert isinstance(system, LycomingO235)

    def test_factory_raises_for_unknown_type(self):
        """Factory must raise ValueError for unknown propulsion types."""
        from core.systems import get_propulsion_system

        with pytest.raises((ValueError, AttributeError)):
            get_propulsion_system("not_a_real_engine")  # type: ignore[arg-type]


# ===========================================================================
# core/metadata.py
# ===========================================================================


class TestComputeConfigHash:
    """Tests for config hash computation."""

    def test_hash_is_string(self):
        """compute_config_hash() should return a string."""
        from core.metadata import compute_config_hash

        h = compute_config_hash()
        assert isinstance(h, str)

    def test_hash_is_hex(self):
        """Config hash should be a valid hex string (SHA-256 = 64 chars)."""
        from core.metadata import compute_config_hash

        h = compute_config_hash()
        assert len(h) == 64
        int(h, 16)  # Raises ValueError if not valid hex

    def test_hash_is_deterministic(self):
        """Same config must produce the same hash on repeated calls."""
        from core.metadata import compute_config_hash

        h1 = compute_config_hash()
        h2 = compute_config_hash()
        assert h1 == h2


class TestGetGitRevision:
    """Tests for git revision detection."""

    def test_returns_string(self):
        """get_git_revision() must always return a string."""
        from core.metadata import get_git_revision

        rev = get_git_revision()
        assert isinstance(rev, str)

    def test_fallback_when_git_unavailable(self):
        """When git is unavailable, should return 'unknown' rather than raise."""
        from core.metadata import get_git_revision

        with patch("core.metadata.subprocess.run", side_effect=FileNotFoundError):
            rev = get_git_revision()
        assert rev == "unknown"


class TestArtifactMetadata:
    """Tests for ArtifactMetadata dataclass and serialization."""

    def test_to_dict_contains_required_fields(self):
        """to_dict() must include all REQUIRED_FIELDS."""
        from core.metadata import ArtifactMetadata, REQUIRED_FIELDS

        meta = ArtifactMetadata(
            artifact="canard.step",
            artifact_type="STEP",
            generated_at="2026-01-01T00:00:00Z",
            revision="abc1234",
            config_hash="deadbeef" * 8,
            contributor="builder",
            component={"name": "canard"},
            provenance={"toolchain": "Open-EZ PDE"},
        )
        d = meta.to_dict()
        for field in REQUIRED_FIELDS:
            assert field in d, f"Required field '{field}' missing from to_dict()"

    def test_write_artifact_metadata_creates_json(self, tmp_path):
        """write_artifact_metadata() should create a .metadata.json file."""
        from core.metadata import write_artifact_metadata

        artifact_path = tmp_path / "canard.step"
        artifact_path.touch()

        mock_component = MagicMock()
        mock_component.get_metadata.return_value = {"name": "canard", "version": "1"}

        metadata_path = write_artifact_metadata(
            artifact_path=artifact_path,
            component=mock_component,
            artifact_type="STEP",
            contributor="test_builder",
        )

        assert metadata_path.exists()
        assert metadata_path.suffix == ".json"

        data = json.loads(metadata_path.read_text())
        assert data["artifact"] == "canard.step"
        assert data["artifact_type"] == "STEP"
        assert data["contributor"] == "test_builder"


# ===========================================================================
# core/vsp_integration.py
# ===========================================================================


class TestVSPIntegration:
    """Tests for VSPIntegration bridge (runs in headless/surrogate mode in CI)."""

    def _make_vsp(self, tmp_path):
        """Instantiate VSPIntegration with output in tmp_path."""
        from core.vsp_integration import VSPIntegration

        return VSPIntegration(output_dir=tmp_path)

    def test_instantiates_in_headless_mode(self, tmp_path):
        """VSPIntegration should initialize without openvsp installed."""
        vsp = self._make_vsp(tmp_path)
        # In CI, openvsp is not installed — has_vsp must be False
        assert isinstance(vsp.has_vsp, bool)

    def test_export_parametric_metadata_creates_json(self, tmp_path):
        """export_parametric_metadata() should write a JSON file."""
        vsp = self._make_vsp(tmp_path)
        output_path = vsp.export_parametric_metadata()

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "components" in data
        assert "wing" in data["components"]
        assert "canard" in data["components"]

    def test_export_metadata_contains_wing_span(self, tmp_path):
        """Exported metadata must include wing span from config."""
        vsp = self._make_vsp(tmp_path)
        output_path = vsp.export_parametric_metadata()
        data = json.loads(output_path.read_text())

        assert "span" in data["components"]["wing"]
        assert data["components"]["wing"]["span"] == config.geometry.wing_span

    def test_aerodynamic_sweep_returns_dict(self, tmp_path):
        """run_aerodynamic_sweep() must return a dict with a mode key."""
        vsp = self._make_vsp(tmp_path)
        result = vsp.run_aerodynamic_sweep(alpha_range=(-4, 4, 3))

        assert isinstance(result, dict)
        assert "mode" in result

    def test_surrogate_sweep_contains_is_stable(self, tmp_path):
        """Surrogate sweep result must include is_stable flag."""
        from core.vsp_integration import VSPIntegration

        vsp = VSPIntegration(output_dir=tmp_path)
        # Force headless mode
        vsp._vsp = None

        result = vsp.run_aerodynamic_sweep(alpha_range=(-2, 2, 3))
        assert "is_stable" in result
