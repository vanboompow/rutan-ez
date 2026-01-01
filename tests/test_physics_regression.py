from pathlib import Path
import sys

# Ensure repository root on path for direct test execution
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from core.simulation.regression import RegressionRunner  # noqa: E402


def test_physics_regressions_match_baseline(tmp_path):
    baseline = Path(__file__).parent / "snapshots" / "physics_baseline.json"
    runner = RegressionRunner(tolerance=0.05)
    passed, current, failures = runner.compare_to_baseline(
        baseline_path=baseline, report_dir=tmp_path
    )

    assert passed, f"Physics regression failures: {failures}"
    # Spot check metrics are captured
    assert "wing_reflex_moment" in current
    assert "cl_per_deg" in current["lift_curve_slope"]
