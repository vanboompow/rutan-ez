#!/usr/bin/env python3
"""
Batch STL export and optional headless slicing hooks.

This script wires the geometry pipeline to common slicers for unattended
fixture printing. It derives jigs from actual geometry surfaces so printed
fixtures register precisely against the modeled parts.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, Callable, List

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import config  # noqa: E402
from core.structures import CanardGenerator  # noqa: E402
from core.jigs import IncidenceBlock, DrillingGuide  # noqa: E402


ComponentFactory = Callable[[], object]


def _canard_surface() -> CanardGenerator:
    canard = CanardGenerator()
    canard.generate_geometry()
    return canard


def _incidence_block() -> IncidenceBlock:
    canard = _canard_surface()
    surface = canard.geometry.faces(">Z")
    return IncidenceBlock(
        name="canard_incidence_block",
        mount_surface=surface,
        incidence_deg=config.geometry.canard_incidence,
        description="Incidence block derived from canard upper surface",
    )


def _drilling_guide() -> DrillingGuide:
    canard = _canard_surface()
    surface = canard.geometry.faces(">Z")
    bbox = surface.val().BoundingBox()
    x_offset = (bbox.xlen * 0.4) / 2
    holes: List[tuple] = [(-x_offset, 0.0), (x_offset, 0.0)]
    return DrillingGuide(
        name="canard_pilot_guide",
        mount_surface=surface,
        hole_positions=holes,
        hole_diameter=0.201,  # #7 drill pilot
        description="Twin-bushing drill guide aligned to canard reference surface",
    )


def get_factories() -> Dict[str, ComponentFactory]:
    return {
        "canard_core": CanardGenerator,
        "canard_incidence_block": _incidence_block,
        "canard_pilot_guide": _drilling_guide,
    }


def slicer_command(args, stl_path: Path, output_dir: Path) -> List[str]:
    if args.slicer == "cura":
        cmd = [args.slicer_command or "CuraEngine", "slice"]
        if args.slicer_config:
            cmd += ["-j", args.slicer_config]
        cmd += ["-o", str(output_dir / f"{stl_path.stem}.gcode"), "-l", str(stl_path)]
        return cmd

    cmd = [args.slicer_command or "prusa-slicer", "--no-gui", "--export-gcode"]
    if args.slicer_config:
        cmd += ["--load", args.slicer_config]
    cmd += ["--output", str(output_dir / f"{stl_path.stem}.gcode"), str(stl_path)]
    return cmd


def run_exports(args) -> List[Path]:
    factories = get_factories()
    selected = factories.keys() if "all" in args.components else args.components

    stl_dir = project_root / args.output
    stl_dir.mkdir(parents=True, exist_ok=True)

    exported: List[Path] = []
    for name in selected:
        factory = factories.get(name)
        if factory is None:
            print(f"[WARN] Unknown component '{name}' - skipping")
            continue

        try:
            component = factory()
            stl_path = component.export_stl(
                stl_dir,
                tolerance=args.tolerance,
                infill=args.infill,
                shells=args.shells,
                orientation=args.orientation,
            )
            print(f"[OK] Exported {stl_path}")
            exported.append(stl_path)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[ERROR] Failed to export {name}: {exc}")

    return exported


def run_slicer(args, stl_paths: List[Path]) -> None:
    if not args.invoke_slicer:
        return

    if not stl_paths:
        print("[INFO] No STL files exported; skipping slicer invocation")
        return

    gcode_dir = project_root / args.gcode_output
    gcode_dir.mkdir(parents=True, exist_ok=True)

    for stl_path in stl_paths:
        cmd = slicer_command(args, stl_path, gcode_dir)
        print(f"[INFO] Slicing {stl_path.name} -> {cmd}")
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"[WARN] Slicer returned {result.returncode} for {stl_path.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch export STLs and optionally slice them.")
    parser.add_argument("--components", nargs="+", default=["canard_core", "canard_incidence_block", "canard_pilot_guide"], help="Components to export or 'all' for every fixture")
    parser.add_argument("--output", default="output/STL", help="Directory for STL output (relative to repo root)")
    parser.add_argument("--tolerance", type=float, default=0.01, help="Tessellation tolerance in inches")
    parser.add_argument("--infill", type=float, default=None, help="Optional infill percentage hint")
    parser.add_argument("--shells", type=int, default=None, help="Optional perimeter/shell count")
    parser.add_argument("--orientation", default=None, help="Orientation description stored in the manifest")
    parser.add_argument("--invoke-slicer", action="store_true", help="Run headless slicer after export")
    parser.add_argument("--slicer", choices=["prusa", "cura"], default="prusa", help="Which slicer CLI to call")
    parser.add_argument("--slicer-command", default=None, help="Override slicer executable (prusa-slicer or CuraEngine)")
    parser.add_argument("--slicer-config", default=None, help="Path to PrusaSlicer/Cura config")
    parser.add_argument("--gcode-output", default="output/GCODE", help="Directory for generated G-code")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stl_paths = run_exports(args)
    run_slicer(args, stl_paths)
    return 0


if __name__ == "__main__":
    sys.exit(main())
