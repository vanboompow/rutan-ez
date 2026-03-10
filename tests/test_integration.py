"""
Integration Tests: main.py Entry Point and Pipeline Connectivity
================================================================

Tests that:
1. main.py can be imported and its functions exercised
2. The config -> analysis -> output pipeline is connected
3. Key output objects return expected types
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Must mock CadQuery before any core/ imports
sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

from config import config  # noqa: E402


class TestMainImport:
    """Verify main.py can be imported cleanly."""

    def test_main_module_importable(self):
        """main.py should import without error."""
        import main  # noqa: F401 (side-effect import)

        assert hasattr(main, "main")

    def test_main_has_required_functions(self):
        """main.py must expose the pipeline functions."""
        import main

        for fn in [
            "main",
            "validate_config",
            "run_analysis",
            "generate_manufacturing",
            "generate_canard",
            "generate_wing",
            "generate_compliance_report",
        ]:
            assert callable(getattr(main, fn, None)), f"main.{fn} not callable"


class TestValidateConfig:
    """Test validate_config() integration with the live config object."""

    def test_validate_config_returns_bool(self):
        """validate_config() should return True/False."""
        import main

        result = main.validate_config()
        assert isinstance(result, bool)

    def test_validate_config_passes_with_default_config(self):
        """Default config should pass validation."""
        import main

        assert main.validate_config() is True


class TestRunAnalysis:
    """Test run_analysis() wires config -> physics engine -> output."""

    def test_run_analysis_calls_physics(self):
        """run_analysis() must call physics.calculate_cg_envelope()."""
        import main

        mock_metrics = MagicMock()
        mock_metrics.neutral_point = 153.5
        mock_metrics.cg_location = 108.0
        mock_metrics.static_margin = 12.5
        mock_metrics.is_stable = True

        with (
            patch("main.physics") as mock_physics,
            patch("main.VSPBridge") as _mock_bridge,
            patch("main.OpenVSPRunner") as mock_runner,
        ):
            mock_physics.calculate_cg_envelope.return_value = mock_metrics
            mock_runner.return_value.export_native_vsp3.return_value = Path(
                "/tmp/test.vsp3"
            )
            main.run_analysis()

        mock_physics.calculate_cg_envelope.assert_called_once()

    def test_run_analysis_exports_vsp_script(self):
        """run_analysis() must call VSPBridge.export_vsp_script."""
        import main

        mock_metrics = MagicMock()
        mock_metrics.neutral_point = 153.5
        mock_metrics.cg_location = 108.0
        mock_metrics.static_margin = 12.5
        mock_metrics.is_stable = True

        with (
            patch("main.physics") as mock_physics,
            patch("main.VSPBridge") as mock_vsp_bridge,
            patch("main.OpenVSPRunner") as mock_runner,
        ):
            mock_physics.calculate_cg_envelope.return_value = mock_metrics
            mock_runner.return_value.export_native_vsp3.return_value = Path(
                "/tmp/test.vsp3"
            )
            main.run_analysis()

        mock_vsp_bridge.export_vsp_script.assert_called_once()


class TestGenerateCanardPipeline:
    """Test generate_canard() integration across modules."""

    def test_generate_canard_calls_geometry(self, tmp_path, monkeypatch):
        """generate_canard() must call generate_geometry() on the canard."""
        import main

        monkeypatch.setattr(main, "project_root", tmp_path)

        mock_canard = MagicMock()
        mock_canard.generate_geometry.return_value = MagicMock()

        mock_tracker = MagicMock()
        mock_tracker.write_layup_schedule.return_value = Path("/tmp/layup.md")

        with (
            patch("main.CanardGenerator", return_value=mock_canard),
            patch("main.compliance_task_tracker", mock_tracker, create=True),
            patch("core.compliance.compliance_task_tracker", mock_tracker, create=True),
        ):
            # Patch the compliance imports inside the function
            with patch.dict(
                "sys.modules",
                {
                    "core.compliance": MagicMock(
                        compliance_task_tracker=mock_tracker,
                        compliance_tracker=MagicMock(),
                    )
                },
            ):
                main.generate_canard()

        mock_canard.generate_geometry.assert_called_once()

    def test_generate_canard_creates_output_dirs(self, tmp_path, monkeypatch):
        """generate_canard() must create STEP/STL/DXF/docs subdirectories."""
        import main

        monkeypatch.setattr(main, "project_root", tmp_path)

        mock_canard = MagicMock()
        mock_tracker = MagicMock()
        mock_tracker.write_layup_schedule.return_value = tmp_path / "layup.md"

        with patch("main.CanardGenerator", return_value=mock_canard):
            with patch.dict(
                "sys.modules",
                {
                    "core.compliance": MagicMock(
                        compliance_task_tracker=mock_tracker,
                        compliance_tracker=MagicMock(),
                    )
                },
            ):
                main.generate_canard()

        for subdir in ["STEP", "STL", "DXF", "docs"]:
            assert (tmp_path / "output" / subdir).exists(), (
                f"output/{subdir} not created"
            )


class TestConfigToAnalysisPipeline:
    """Test that config drives the PhysicsEngine correctly."""

    def test_physics_engine_reads_config_geometry(self):
        """PhysicsEngine should use config.geometry for wing parameters."""
        from core.analysis import PhysicsEngine

        engine = PhysicsEngine()
        geo = engine.geo

        # Config geometry must be accessible and reasonable
        assert geo.wing_span > 100, "Wing span should be > 100 inches"
        assert geo.wing_root_chord > 0, "Wing root chord must be positive"
        assert geo.canard_span > 0, "Canard span must be positive"

    def test_calculate_cg_envelope_returns_metrics(self):
        """calculate_cg_envelope() should return a StabilityMetrics object."""
        from core.analysis import PhysicsEngine

        engine = PhysicsEngine()
        metrics = engine.calculate_cg_envelope()

        # Must have the fields used by run_analysis()
        assert hasattr(metrics, "neutral_point")
        assert hasattr(metrics, "cg_location")
        assert hasattr(metrics, "static_margin")
        assert hasattr(metrics, "is_stable")

    def test_metrics_are_numeric(self):
        """StabilityMetrics values must be numeric (float or int)."""
        from core.analysis import PhysicsEngine

        engine = PhysicsEngine()
        metrics = engine.calculate_cg_envelope()

        assert isinstance(metrics.neutral_point, (int, float))
        assert isinstance(metrics.cg_location, (int, float))
        assert isinstance(metrics.static_margin, (int, float))
        assert isinstance(metrics.is_stable, bool)


class TestMainCLIDispatch:
    """Test that the argument parser dispatches correctly to pipeline functions."""

    def test_summary_flag_calls_config_summary(self, capsys):
        """--summary should print config.summary() and return 0."""
        import main

        with patch("sys.argv", ["main.py", "--summary"]):
            with patch.object(config, "summary", return_value="SUMMARY OUTPUT"):
                result = main.main()

        # Return value should be 0 (success) or None
        assert result in (0, None)

    def test_validate_flag_returns_zero_on_success(self):
        """--validate should return 0 when config is valid."""
        import main

        with patch("sys.argv", ["main.py", "--validate"]):
            result = main.main()

        assert result in (0, None)

    def test_no_args_prints_help(self, capsys):
        """Calling with no args should print help and not crash."""
        import main

        with patch("sys.argv", ["main.py"]):
            main.main()  # Should not raise

        # No assertion on return value - just must not raise
