"""
CI-safe tests for VSPIntegration native/surrogate sweep.

Tests run on both Python 3.14 (no openvsp, surrogate path) and
Python 3.13 (with openvsp, native path).
"""

import json
import sys
import textwrap
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
# Helpers: mock VSP + fake .polar file
# ---------------------------------------------------------------------------

_ALPHAS_19 = [float(a) for a in range(-4, 15)]
_CLS_19 = [0.08 * a for a in _ALPHAS_19]
_CDS_19 = [0.020 + 0.001 * abs(a) for a in _ALPHAS_19]
_CMS_19 = [-0.02 - 0.001 * a for a in _ALPHAS_19]


def _write_fake_polar(path: Path, alphas=None, cls=None, cds=None, cms=None) -> None:
    """Write a minimal VSPAERO .polar file with the expected 3-line header format."""
    if alphas is None:
        alphas, cls, cds, cms = _ALPHAS_19, _CLS_19, _CDS_19, _CMS_19

    # 3 header lines matching real VSPAERO .polar format
    header = (
        "                                                                    "
        "Surface Integration Forces and Moments -->\n"
        "                                                                    "
        "Surf-Surf-\n"
    )
    # Column header line — must include the 4 columns we parse
    col_header = (
        "      Beta             Mach             AoA             Re/1e6"
        "             CLo             CLi            CLtot"
        "              CDo              CDi             CDtot"
        "              CSo              CSi            CStot"
        "               L/D              E"
        "               CMox             CMoy             CMoz"
        "             CMix             CMiy             CMiz"
        "             CMxtot           CMytot           CMztot\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(header)
        f.write(col_header)
        for aoa, cl, cd, cm in zip(alphas, cls, cds, cms):
            # 23 columns; we only fill in the ones we parse
            row = (
                f"  0.000000000000   0.000000000000"
                f"   {aoa:.6f}  10.000000000000"
                f"   0.000000   {cl:.6f}   {cl:.6f}"  # CLo, CLi, CLtot
                f"   0.000000   {cd:.6f}   {cd:.6f}"  # CDo, CDi, CDtot
                f"   0.000000   0.000000   0.000000"  # CSo, CSi, CStot
                f"   0.000000   0.000000"  # L/D, E
                f"   0.000000   0.000000   0.000000"  # CMox, CMoy, CMoz
                f"   0.000000   {cm:.6f}   0.000000"  # CMix, CMiy, CMiz
                f"   0.000000   {cm:.6f}   0.000000\n"  # CMxtot, CMytot, CMztot
            )
            f.write(row)


def _make_vsp_mock(tmp_path: Path) -> MagicMock:
    """
    Build a minimal mock of the openvsp module for schema tests.

    The mock patches ExecAnalysis to write a fake .polar file at the path
    VSPAERO would produce, so _parse_vspaero_polar() finds real data.
    """
    vsp = MagicMock()
    vsp.GetVSPVersion.return_value = "3.48.2-mock"
    vsp.SET_NONE = -1
    vsp.SET_ALL = 0
    vsp.EXPORT_VSPGEOM = 5  # arbitrary int

    # AddGeom returns a fake geom ID
    vsp.AddGeom.return_value = "MOCKGEOMID"

    # ExportFile writes a minimal .vspgeom placeholder
    def mock_export_file(path, *args, **kwargs):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("# vspgeom v3\n1\n1 1 1\n")

    vsp.ExportFile.side_effect = mock_export_file

    # ExecAnalysis writes a fake .polar file alongside the .vsp3 set by SetVSP3FileName
    _vsp3_path: list = []

    def mock_set_vsp3(path):
        _vsp3_path.clear()
        _vsp3_path.append(path)

    vsp.SetVSP3FileName.side_effect = mock_set_vsp3

    def mock_exec_analysis(name):
        if _vsp3_path:
            polar_path = Path(_vsp3_path[0]).with_suffix(".polar")
            _write_fake_polar(polar_path)
        return "results_001"

    vsp.ExecAnalysis.side_effect = mock_exec_analysis
    return vsp


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


def test_native_return_schema_with_mock_vsp(tmp_path):
    """_run_native_sweep() returns correct schema when vsp mock is injected."""
    vsp_mock = _make_vsp_mock(tmp_path)

    from core.vsp_integration import VSPIntegration

    bridge = VSPIntegration(output_dir=tmp_path / "vsp")
    bridge._vsp = vsp_mock

    # Use tmp_path to avoid overwriting real data/validation/vspaero_native_polars.json
    # with mock data (vsp_version would contain "mock", breaking test_cross_validation.py)
    result = bridge._run_native_sweep((-4, 14, 19), polar_output=tmp_path / "native_polars.json")

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
    vsp_mock = _make_vsp_mock(tmp_path)

    from core.vsp_integration import VSPIntegration

    bridge = VSPIntegration(output_dir=tmp_path / "vsp")
    bridge._vsp = vsp_mock

    # Use tmp_path to avoid overwriting real data/validation/vspaero_native_polars.json
    # with mock data (same isolation fix as test_native_return_schema_with_mock_vsp)
    result = bridge._run_native_sweep((-4, 14, 19), polar_output=tmp_path / "native_polars.json")

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
    vsp_mock = _make_vsp_mock(tmp_path)

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
# Test 5a: _parse_vspaero_polar unit test — reads correctly from fake .polar file
# ---------------------------------------------------------------------------


def test_parse_vspaero_polar_unit(tmp_path):
    """_parse_vspaero_polar() correctly parses a fake .polar file."""
    from core.vsp_integration import VSPIntegration

    polar_path = tmp_path / "test.polar"
    _write_fake_polar(polar_path)

    alphas, cls, cds, cms = VSPIntegration._parse_vspaero_polar(polar_path, 19)

    assert len(alphas) == 19
    assert alphas[0] == pytest.approx(-4.0, abs=0.01)
    assert alphas[-1] == pytest.approx(14.0, abs=0.01)
    # CL at alpha=4 (index 8) should be 0.08 * 4 = 0.32
    assert cls[8] == pytest.approx(0.32, abs=0.01)
    # All CDs should be positive
    assert all(cd > 0 for cd in cds)


# ---------------------------------------------------------------------------
# Test 5b: Runtime fallback — if _run_native_sweep raises, returns surrogate
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
