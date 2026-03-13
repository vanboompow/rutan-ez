"""
Generate Cross-Validation Data: VSPAERO Native vs. Surrogate
=============================================================

This script:
1. Regenerates `data/validation/vspaero_native_polars.json` using the real
   VSPAERO VLM solver (requires OpenVSP 3.48.2 with Python bindings).
2. Produces `data/validation/surrogate_cross_validation.json` — a per-metric
   discrepancy table comparing the OpenVSPAdapter surrogate against native VLM
   output at the SAME 19-point alpha array.

Purpose: Establish a quantitative baseline of surrogate vs. native agreement so
Phase 5 can prioritize calibration targets.

IMPORTANT: No pass/fail thresholds are applied. This is measure-only per the
Phase 4 CONTEXT.md locked decision. Phase 5 decides calibration.

Usage:
    cd /path/to/open-ez
    python3.13 scripts/generate_cross_validation.py
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

# --- CadQuery/OCP mock MUST be set before any core/ imports -----------------
# Core modules import CadQuery at module level (or lazily). Without this mock,
# importing core.vsp_integration raises ImportError in environments that have
# OpenVSP but not CadQuery.
sys.modules.setdefault("cadquery", MagicMock())
sys.modules.setdefault("OCP", MagicMock())

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from core.vsp_integration import VSPIntegration  # noqa: E402
from core.simulation.openvsp_adapter import OpenVSPAdapter  # noqa: E402


# 19-point alpha array: -4 to 14 degrees, 1-degree steps
ALPHA_RANGE = (-4, 14, 19)
ALPHAS_19 = [float(a) for a in range(-4, 15)]  # -4, -3, ..., 14


def regenerate_native(data_dir: Path) -> dict:
    """
    Run the real VSPAERO VLM sweep and write vspaero_native_polars.json.

    Args:
        data_dir: Directory to write the polar JSON (must be writable).

    Returns:
        The polar result dict from _run_native_sweep().

    Raises:
        RuntimeError: If OpenVSP is not available or returns mock data.
    """
    bridge = VSPIntegration()

    if not bridge.has_vsp:
        raise RuntimeError(
            "OpenVSP Python API is not importable. "
            "Run scripts/install_openvsp.sh and retry with python3.13."
        )

    polar_output = data_dir / "vspaero_native_polars.json"
    print(f"[native] Running VSPAERO VLM sweep ({ALPHA_RANGE[2]} alpha points)...")
    result = bridge._run_native_sweep(ALPHA_RANGE, polar_output=polar_output)

    vsp_version = result.get("vsp_version", "")
    if "mock" in vsp_version.lower():
        raise RuntimeError(
            f"VSPAERO returned mock data (vsp_version='{vsp_version}'). "
            "Real OpenVSP bindings required for cross-validation."
        )

    points = result["points"]
    cl_values = [p["cl"] for p in points]
    print(
        f"[native] Version: {vsp_version}, "
        f"{len(points)} points, "
        f"CL range [{min(cl_values):.4f}, {max(cl_values):.4f}]"
    )
    print(f"[native] Written to {polar_output}")
    return result


def get_surrogate_polars(alphas: list[float]) -> list[dict]:
    """
    Run the OpenVSPAdapter surrogate at the specified alpha values.

    Forces the surrogate to evaluate at the same 19-point alpha array as the
    native sweep so the comparison is valid.

    Args:
        alphas: List of angles of attack in degrees (should match native array).

    Returns:
        List of dicts with keys: alpha_deg, cl, cd, cm.
    """
    adapter = OpenVSPAdapter()
    polars = adapter.run_vspaero(alphas)
    return [
        {"alpha_deg": p.alpha_deg, "cl": p.cl, "cd": p.cd, "cm": p.cm}
        for p in polars
    ]


def build_discrepancy_table(
    native_points: list[dict],
    surrogate_points: list[dict],
) -> dict:
    """
    Build per-point and per-metric discrepancy table (native - surrogate).

    Args:
        native_points: List of dicts from VSPAERO native sweep.
        surrogate_points: List of dicts from OpenVSPAdapter surrogate.

    Returns:
        Structured discrepancy dict with comparison array and summary stats.
    """
    # Align by alpha — build index keyed by rounded alpha
    surrogate_by_alpha = {
        round(p["alpha_deg"], 6): p for p in surrogate_points
    }

    comparison = []
    alpha_deg_list = []

    for nat in native_points:
        alpha = nat["alpha_deg"]
        sur = surrogate_by_alpha.get(round(alpha, 6))
        if sur is None:
            # Attempt nearest-alpha fallback
            closest = min(
                surrogate_points,
                key=lambda p: abs(p["alpha_deg"] - alpha),
            )
            if abs(closest["alpha_deg"] - alpha) > 0.5:
                # No matching surrogate point — skip
                print(
                    f"[warn] No surrogate point within 0.5 deg of alpha={alpha:.1f}; skipping"
                )
                continue
            sur = closest

        alpha_deg_list.append(alpha)
        comparison.append(
            {
                "alpha_deg": alpha,
                "cl_native": nat["cl"],
                "cl_surrogate": sur["cl"],
                "cl_delta": nat["cl"] - sur["cl"],
                "cd_native": nat["cd"],
                "cd_surrogate": sur["cd"],
                "cd_delta": nat["cd"] - sur["cd"],
                "cm_native": nat["cm"],
                "cm_surrogate": sur["cm"],
                "cm_delta": nat["cm"] - sur["cm"],
            }
        )

    def _stats(deltas: list[float]) -> dict:
        n = len(deltas)
        if n == 0:
            return {"mean_delta": 0.0, "rms_delta": 0.0, "max_abs_delta": 0.0}
        mean_delta = sum(deltas) / n
        rms_delta = math.sqrt(sum(d**2 for d in deltas) / n)
        max_abs_delta = max(abs(d) for d in deltas)
        return {
            "mean_delta": round(mean_delta, 6),
            "rms_delta": round(rms_delta, 6),
            "max_abs_delta": round(max_abs_delta, 6),
        }

    cl_deltas = [c["cl_delta"] for c in comparison]
    cd_deltas = [c["cd_delta"] for c in comparison]
    cm_deltas = [c["cm_delta"] for c in comparison]

    return {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "native_source": "VSPAERO VLM (real)",
            "surrogate_source": "OpenVSPAdapter (lifting-line + Viterna)",
            "alpha_count": len(comparison),
            "note": (
                "Measure-only. No pass/fail thresholds. "
                "Phase 5 decides calibration."
            ),
        },
        "alpha_deg": alpha_deg_list,
        "comparison": comparison,
        "summary": {
            "cl": _stats(cl_deltas),
            "cd": _stats(cd_deltas),
            "cm": _stats(cm_deltas),
        },
    }


def _print_summary_table(discrepancy: dict) -> None:
    """Print a human-readable summary of discrepancy statistics to stdout."""
    summary = discrepancy["summary"]
    n = discrepancy["metadata"]["alpha_count"]
    print(f"\n{'=' * 60}")
    print(f"Surrogate Cross-Validation Summary  ({n} alpha points)")
    print(f"{'=' * 60}")
    print(f"{'Metric':<10}  {'Mean Delta':>12}  {'RMS Delta':>12}  {'Max |Delta|':>12}")
    print(f"{'-' * 10}  {'-' * 12}  {'-' * 12}  {'-' * 12}")
    for metric in ("cl", "cd", "cm"):
        s = summary[metric]
        print(
            f"{metric.upper():<10}  "
            f"{s['mean_delta']:>12.5f}  "
            f"{s['rms_delta']:>12.5f}  "
            f"{s['max_abs_delta']:>12.5f}"
        )
    print(f"{'=' * 60}")
    print("Note: delta = native - surrogate. No pass/fail thresholds.")
    print("Phase 5 will use this table to prioritize calibration targets.\n")


def main() -> None:
    """Entry point: regenerate native polars and produce cross-validation JSON."""
    data_dir = REPO_ROOT / "data" / "validation"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Regenerate native VSPAERO polars
    native_result = regenerate_native(data_dir)
    native_points = native_result["points"]

    # Step 2: Run surrogate at the SAME 19-point alpha array
    print(f"[surrogate] Running OpenVSPAdapter at {len(ALPHAS_19)} alpha points...")
    surrogate_points = get_surrogate_polars(ALPHAS_19)
    print(f"[surrogate] Got {len(surrogate_points)} polar points")

    # Step 3: Build discrepancy table
    discrepancy = build_discrepancy_table(native_points, surrogate_points)

    # Step 4: Write cross-validation JSON
    out_path = data_dir / "surrogate_cross_validation.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(discrepancy, f, indent=2)
    print(f"[cross-val] Written to {out_path}")

    # Step 5: Print human-readable summary
    _print_summary_table(discrepancy)


if __name__ == "__main__":
    main()
