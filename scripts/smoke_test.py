#!/usr/bin/env python3
"""
Lightweight geometry smoke test.

- Validates the SSOT configuration
- Generates canard and wing geometry
- Optionally exports STEP/STL/DXF/G-code artifacts
- Optionally probes the OpenVSP Python API
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

from config import config
from core.aerodynamics import airfoil_factory
from core.base import FoamCore
from core.structures import CanardGenerator, WingGenerator


def _validate_configuration() -> None:
    errors = config.validate()
    if errors:
        raise RuntimeError("Configuration validation failed: " + "; ".join(errors))


def _run_openvsp_probe(allow_missing: bool) -> None:
    try:
        import openvsp as vsp  # type: ignore
    except ImportError:
        message = (
            "OpenVSP Python API not available. "
            "Install openvsp>=3.35.0 to run physics checks."
        )
        if allow_missing:
            print(f"[warn] {message}")
            return
        raise RuntimeError(message)

    try:
        vsp.ClearVSPModel()
        vsp.AddGeom("WING", "probe")
        vsp.ClearVSPModel()
    except Exception as exc:  # pragma: no cover - depends on native binding
        raise RuntimeError(f"OpenVSP probe failed: {exc}") from exc


def _export_component(component: FoamCore, out_root: Path, fast: bool) -> Dict[str, Path]:
    step_dir = out_root / "STEP"
    stl_dir = out_root / "STL"
    dxf_dir = out_root / "DXF"
    gcode_dir = out_root / "GCODE"
    for target in (step_dir, stl_dir, dxf_dir, gcode_dir):
        target.mkdir(parents=True, exist_ok=True)

    artifacts: Dict[str, Path] = {}

    geometry = component.generate_geometry()
    if geometry is None:
        raise RuntimeError(f"{component.name} did not return geometry")

    if fast:
        return {"geometry": Path("<in-memory>")}

    artifacts["step"] = component.export_step(step_dir)
    artifacts["stl"] = component.export_stl(stl_dir)
    artifacts["dxf"] = component.export_dxf(dxf_dir)
    artifacts["gcode"] = component.export_gcode(
        gcode_dir,
        kerf_offset=config.manufacturing.kerf_compensation[config.materials.wing_core_foam],
        feed_rate=config.manufacturing.feed_rate_default,
    )

    return artifacts


def run_smoke(
    out_root: Path,
    fast: bool,
    require_openvsp: bool,
    allow_missing_openvsp: bool,
) -> List[Dict[str, Path]]:
    _validate_configuration()
    if require_openvsp:
        _run_openvsp_probe(allow_missing=allow_missing_openvsp)

    wing_airfoil = airfoil_factory.get_wing_airfoil(apply_reflex=True)
    wing = WingGenerator(
        name="main_wing",
        root_airfoil=wing_airfoil,
        tip_airfoil=wing_airfoil,
        span=config.geometry.wing_span,
        root_chord=config.geometry.wing_root_chord,
        tip_chord=config.geometry.wing_tip_chord,
        sweep_angle=config.geometry.wing_sweep_le,
        dihedral_angle=config.geometry.wing_dihedral,
        washout=config.geometry.wing_washout,
        description="Smoke test wing"
    )

    canard = CanardGenerator()

    results = [
        _export_component(canard, out_root, fast=fast),
        _export_component(wing, out_root, fast=fast),
    ]

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Geometry smoke test runner")
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("output/smoke"),
        help="Directory for smoke test artifacts",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip file exports to keep the smoke test lightweight",
    )
    parser.add_argument(
        "--check-openvsp",
        action="store_true",
        help="Probe the OpenVSP Python API before generating geometry",
    )
    parser.add_argument(
        "--allow-missing-openvsp",
        action="store_true",
        help="Downgrade missing OpenVSP to a warning",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_openvsp = args.check_openvsp and not args.allow_missing_openvsp

    try:
        artifacts = run_smoke(
            out_root=args.artifacts_dir,
            fast=args.fast,
            require_openvsp=require_openvsp,
            allow_missing_openvsp=args.allow_missing_openvsp,
        )
    except Exception as exc:
        print(f"[error] Smoke test failed: {exc}")
        return 1

    print("Smoke test completed")
    if not args.fast:
        for bundle in artifacts:
            for kind, path in bundle.items():
                print(f" - {kind}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
