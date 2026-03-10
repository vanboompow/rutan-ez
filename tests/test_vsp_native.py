"""
CI-safe tests for VSPIntegration native/surrogate sweep.

Tests run on both Python 3.14 (no openvsp, surrogate path) and
Python 3.13 (with openvsp, native path).
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# HAS_OPENVSP guard — never crashes on ImportError
HAS_OPENVSP = False
try:
    import openvsp  # noqa: F401

    HAS_OPENVSP = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Test 1: Surrogate fallback when openvsp is not importable
# ---------------------------------------------------------------------------


def test_surrogate_fallback_when_openvsp_unavailable():
    """run_aerodynamic_sweep() returns mode='surrogate' when openvsp missing."""
    # Force openvsp to be absent by patching _try_import_vsp
    with patch(
        "core.vsp_integration.VSPIntegration._try_import_vsp", return_value=None
    ):
        from core.vsp_integration import VSPIntegration

        bridge = VSPIntegration()
        result = bridge.run_aerodynamic_sweep()

    assert result["mode"] == "surrogate"
    assert "points" in result
    assert len(result["points"]) > 0
    # Each point must have required keys
    for pt in result["points"]:
        assert "alpha_deg" in pt
        assert "cl" in pt
        assert "cd" in pt
        assert "cm" in pt


# ---------------------------------------------------------------------------
# Test 2: Native return schema (requires real openvsp OR mock)
# ---------------------------------------------------------------------------


def _make_vsp_mock():
    """Build a minimal mock of the openvsp module for schema tests."""
    vsp = MagicMock()
    vsp.GetVSPVersion.return_value = "3.48.2-mock"

    # ExecAnalysis returns a fake results ID
    vsp.ExecAnalysis.return_value = "results_001"

    # GetDoubleResults returns 19-point arrays for CL/CD/CMy
    n = 19
    alphas = [float(a) for a in range(-4, 15)]
    cls = [0.08 * a for a in alphas]
    cds = [0.020 + 0.001 * abs(a) for a in alphas]
    cms = [-0.02 - 0.001 * a for a in alphas]

    def get_double_results(res_id, key, *args, **kwargs):
        mapping = {"CL": cls, "CD": cds, "CMy": cms, "CDi": cds, "CDo": cds}
        return mapping.get(key, [0.0] * n)

    vsp.GetDoubleResults.side_effect = get_double_results
    return vsp


def test_native_return_schema_with_mock_vsp(tmp_path):
    """_run_native_sweep() returns correct schema when vsp mock is injected."""
    vsp_mock = _make_vsp_mock()

    from core.vsp_integration import VSPIntegration

    bridge = VSPIntegration(output_dir=tmp_path / "vsp")
    bridge._vsp = vsp_mock

    result = bridge._run_native_sweep((-4, 14, 19))

    assert result["mode"] == "native"
    assert result["source"] == "vspaero_native"
    assert "points" in result
    assert "solver_settings" in result
    assert "vsp_version" in result

    pts = result["points"]
    assert len(pts) == 19
    for pt in pts:
        assert "alpha_deg" in pt
        assert "cl" in pt
        assert "cd" in pt
        assert "cm" in pt


# ---------------------------------------------------------------------------
# Test 3: Alpha sweep range — native uses -4 to 14 in 1-deg steps (19 points)
# ---------------------------------------------------------------------------


def test_native_alpha_sweep_range(tmp_path):
    """Native sweep uses exactly -4 to 14 deg in 1-deg steps = 19 points."""
    vsp_mock = _make_vsp_mock()

    from core.vsp_integration import VSPIntegration

    bridge = VSPIntegration(output_dir=tmp_path / "vsp")
    bridge._vsp = vsp_mock

    result = bridge._run_native_sweep((-4, 14, 19))

    pts = result["points"]
    assert len(pts) == 19
    alphas = [pt["alpha_deg"] for pt in pts]
    assert alphas[0] == pytest.approx(-4.0, abs=0.01)
    assert alphas[-1] == pytest.approx(14.0, abs=0.01)


# ---------------------------------------------------------------------------
# Test 4: Polar file written to data/validation/vspaero_native_polars.json
# ---------------------------------------------------------------------------


def test_polar_file_written_after_native_sweep(tmp_path):
    """After native sweep, vspaero_native_polars.json exists with correct schema."""
    vsp_mock = _make_vsp_mock()

    from core.vsp_integration import VSPIntegration

    bridge = VSPIntegration(output_dir=tmp_path / "vsp")
    bridge._vsp = vsp_mock

    # Point output to tmp_path so we don't pollute the real data dir
    polar_path = tmp_path / "vspaero_native_polars.json"
    result = bridge._run_native_sweep((-4, 14, 19), polar_output=polar_path)

    assert polar_path.exists(), "Polar JSON file was not created"
    data = json.loads(polar_path.read_text())

    assert data["source"] == "vspaero_native"
    assert "vsp_version" in data
    assert "timestamp" in data
    assert "solver_settings" in data
    assert "points" in data
    assert len(data["points"]) == 19


# ---------------------------------------------------------------------------
# Test 5: Runtime fallback — if _run_native_sweep raises, returns surrogate
# ---------------------------------------------------------------------------


def test_runtime_exception_falls_back_to_surrogate():
    """If native sweep raises an exception, run_aerodynamic_sweep falls back to surrogate."""
    vsp_mock = MagicMock()

    from core.vsp_integration import VSPIntegration

    bridge = VSPIntegration()
    bridge._vsp = vsp_mock  # Has VSP (so native path chosen)

    with patch.object(bridge, "_run_native_sweep", side_effect=RuntimeError("VSPAERO crash")):
        result = bridge.run_aerodynamic_sweep()

    assert result["mode"] == "surrogate"
    assert "points" in result


# ---------------------------------------------------------------------------
# Tests that require real OpenVSP (skipped in CI)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_OPENVSP, reason="OpenVSP not installed")
def test_real_native_sweep_produces_polars():
    """Real native sweep produces 19 polar points with physical CL values."""
    from core.vsp_integration import VSPIntegration

    bridge = VSPIntegration()
    assert bridge.has_vsp, "OpenVSP should be available"

    result = bridge.run_aerodynamic_sweep((-4, 14, 19))

    assert result["mode"] == "native"
    assert len(result["points"]) == 19

    # Physical sanity: CL at alpha=4 should be roughly 0.2-0.6 for a Long-EZ
    pt_4deg = next(p for p in result["points"] if abs(p["alpha_deg"] - 4.0) < 0.5)
    assert 0.1 < pt_4deg["cl"] < 1.0, f"CL at 4 deg out of range: {pt_4deg['cl']}"
