"""
Phase 5 Tests: Compliance Gate in export_gcode
================================================

Validates the actual export_gcode() code path:
1. strict_compliance=False: export succeeds even with low credit (warning logged)
2. strict_compliance=True: raises ComplianceError when credit < 51%
3. strict_compliance=True with credit >= 51%: export succeeds
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

import pytest  # noqa: E402
from core.base import ComplianceError, FoamCore  # noqa: E402
from config import config  # noqa: E402


class _TestFoamCore(FoamCore):
    """Minimal concrete FoamCore for testing the compliance gate."""

    def _build_geometry(self):
        pass

    def export_dxf(self, output_path):
        pass

    def manufacturing_plan(self, output_path):
        return {}

    def get_root_profile(self):
        return MagicMock()

    def get_tip_profile(self):
        return MagicMock()


def _run_export_gcode(strict, credit_sum):
    """Exercise the actual export_gcode() path with given compliance settings."""
    original_strict = config.compliance.strict_compliance
    original_credits = dict(config.compliance.task_credits)
    try:
        config.compliance.strict_compliance = strict
        config.compliance.task_credits = {"test": credit_sum}

        component = _TestFoamCore("test_part")
        tmp_dir = Path("/tmp/test_compliance_gate")

        # Patch GCodeWriter at its source module and metadata to avoid real I/O
        with (
            patch("core.manufacturing.GCodeWriter") as mock_gcw,
            patch.object(component, "_write_artifact_metadata"),
        ):
            mock_gcw.return_value.write.return_value = tmp_dir / "test_part.tap"
            return component.export_gcode(tmp_dir)
    finally:
        config.compliance.strict_compliance = original_strict
        config.compliance.task_credits = original_credits


class TestComplianceGate:
    def test_lenient_mode_allows_low_credit(self):
        """With strict_compliance=False, low credit should not block export."""
        result = _run_export_gcode(strict=False, credit_sum=0.10)
        assert result is not None

    def test_strict_mode_blocks_low_credit(self):
        """With strict_compliance=True and credit < 51%, export_gcode raises."""
        with pytest.raises(ComplianceError, match="51%"):
            _run_export_gcode(strict=True, credit_sum=0.30)

    def test_strict_mode_allows_sufficient_credit(self):
        """With strict_compliance=True and credit >= 51%, export succeeds."""
        result = _run_export_gcode(strict=True, credit_sum=0.55)
        assert result is not None

    def test_compliance_error_is_exception(self):
        """ComplianceError should be a proper Exception subclass."""
        assert issubclass(ComplianceError, Exception)

    def test_default_credits_exceed_51pct(self):
        """Default config task credits should exceed 51% requirement."""
        total = config.compliance.total_builder_credit
        assert total >= 0.51, f"Default credits {total:.1%} below 51%"

    def test_compliance_error_message(self):
        """ComplianceError message should contain actionable information."""
        with pytest.raises(ComplianceError, match="51%"):
            _run_export_gcode(strict=True, credit_sum=0.30)
