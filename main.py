#!/usr/bin/env python3
"""
Open-EZ PDE: Main Entry Point (Upgraded)
========================================

Usage:
    python main.py --generate-all     Generate all artifacts (CAD, CNC, Docs)
    python main.py --analysis         Run physics/stability checks
    python main.py --jigs             Generate 3D printable tooling

"""

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config  # noqa: E402
from core.structures import CanardGenerator, WingGenerator  # noqa: E402
from core.analysis import physics, VSPBridge, OpenVSPRunner  # noqa: E402
from core.manufacturing import JigFactory  # noqa: E402


def validate_config() -> bool:
    """Validate aircraft configuration."""
    print("Validating configuration...")
    errors = config.validate()

    if errors:
        print("\nCONFIGURATION ERRORS:")
        for err in errors:
            print(f"  [!] {err}")
        return False

    print("  Configuration valid.")
    return True


def validate_physics() -> bool:
    """Run lightweight physics regressions against stored baselines."""
    from core.simulation.regression import RegressionRunner

    print("\n--- Validating Physics Models ---")
    report_dir = project_root / "output" / "reports"
    baseline = project_root / "tests" / "snapshots" / "physics_baseline.json"

    runner = RegressionRunner()
    passed, current, failures = runner.compare_to_baseline(
        baseline_path=baseline, report_dir=report_dir
    )

    if passed:
        print("  Physics regressions PASSED")
    else:
        print("  Physics regressions FAILED:")
        for failure in failures:
            print(f"   - {failure}")

    polars_path = project_root / "output" / "reports" / "vspaero_polars.json"
    runner.aero.serialize_polars(target=polars_path)
    return passed


def run_analysis():
    """Run physics stability checks."""
    print("\n--- Running Flight Physics Analysis ---")
    metrics = physics.calculate_cg_envelope()

    print(f"  Neutral Point: {metrics.neutral_point:.2f} in")
    print(f"  Estimated CG:  {metrics.cg_location:.2f} in")
    print(f"  Static Margin: {metrics.static_margin:.1f}%")

    if metrics.is_stable:
        print("  STATUS: STABLE (Margin within 5-20% safe range)")
    else:
        print("  STATUS: WARNING - Review Weight & Balance")

    # Export VSP
    vsp_dir = project_root / "output" / "VSP"
    vsp_dir.mkdir(parents=True, exist_ok=True)
    VSPBridge.export_vsp_script(vsp_dir / "model.vspscript")
    print("  OpenVSP script exported to output/VSP/")

    # Export native VSP3 model with control surfaces
    runner = OpenVSPRunner()
    vsp3_path = runner.export_native_vsp3(vsp_dir / "long_ez.vsp3")
    print(f"  Native VSP model: {vsp3_path}")


def generate_manufacturing():
    """Generate physical production artifacts."""
    print("\n--- Generating Manufacturing Artifacts ---")

    # 1. CNC G-Code (Foam Cores)
    gcode_dir = project_root / "output" / "GCODE"
    gcode_dir.mkdir(parents=True, exist_ok=True)

    canard = CanardGenerator()
    canard.export_gcode(gcode_dir)
    print(f"  CNC: Canard G-code written to {gcode_dir}")

    # 2. 3D Printable Jigs
    stl_dir = project_root / "output" / "STL"
    stl_dir.mkdir(parents=True, exist_ok=True)

    # Example: Generate incidence jigs
    canard.export_jigs(stl_dir)
    JigFactory.export_all_jigs(stl_dir)
    print(f"  3D PRINT: Assembly jigs written to {stl_dir}")


def generate_canard() -> None:
    """Generate canard foam core."""
    print("\n--- Generating Canard ---")
    canard = CanardGenerator()

    step_dir = project_root / "output" / "STEP"
    stl_dir = project_root / "output" / "STL"
    dxf_dir = project_root / "output" / "DXF"

    for d in [step_dir, stl_dir, dxf_dir]:
        d.mkdir(parents=True, exist_ok=True)

    try:
        canard.generate_geometry()
        canard.export_step(step_dir)
        canard.export_stl(stl_dir)
        canard.export_dxf(dxf_dir)
        print("  Canard core exported to output/")
    except Exception as e:
        print(f"  Error generating canard: {e}")


def generate_wing() -> None:
    """Generate main wing foam cores."""
    from core.aerodynamics import airfoil_factory

    print("\n--- Generating Main Wing ---")

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
        description="Long-EZ main wing with Eppler 1230 modified",
    )

    step_dir = project_root / "output" / "STEP"
    step_dir.mkdir(parents=True, exist_ok=True)

    try:
        wing.generate_geometry()
        wing.cut_spar_trough()
        wing.export_step(step_dir)
        print("  Main wing exported to output/STEP/")

        # Wing segmentation for CNC machines
        if config.manufacturing.auto_segment_wings:
            gcode_dir = project_root / "output" / "GCODE"
            dxf_dir = project_root / "output" / "DXF"
            gcode_dir.mkdir(parents=True, exist_ok=True)
            dxf_dir.mkdir(parents=True, exist_ok=True)

            wing_segments = wing.generate_segments(
                max_block_length=config.manufacturing.max_cnc_block_length
            )

            for i, segment in enumerate(wing_segments):
                segment.generate_geometry()
                segment.cut_spar_trough()
                segment.export_gcode(gcode_dir)
                segment.export_dxf(dxf_dir)

            print(f"  Wing segmented into {len(wing_segments)} CNC blocks")
            print(f"  G-code written to {gcode_dir}")
            print(f"  DXF templates written to {dxf_dir}")

    except Exception as e:
        print(f"  Error generating wing: {e}")


def generate_compliance_report() -> None:
    """Generate FAA compliance report."""
    from core.compliance import compliance_tracker

    print("\n--- Generating Compliance Report ---")

    docs_dir = project_root / "output" / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Generate markdown report
    report = compliance_tracker.generate_report()
    report_file = docs_dir / "compliance_report.md"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"  Report written to: {report_file}")

    # Export JSON data
    json_file = compliance_tracker.export_json(docs_dir)
    print(f"  JSON data written to: {json_file}")


def nest_sheets() -> None:
    """Nest generated DXFs onto stock sheet sizes."""
    from core.nesting import NestingPlanner

    print("\n--- Nesting DXF Sheets ---")
    dxf_dir = project_root / "output" / "DXF"
    nested_dir = project_root / "output" / "nested"

    if not dxf_dir.exists():
        print("  No DXF directory found. Run geometry exports first.")
        return

    planner = NestingPlanner(
        stock_sheets=config.manufacturing.stock_sheets,
        margin=0.25,
        spacing=0.125,
        dogbone_radius=config.manufacturing.default_dogbone_radius,
        fillet_radius=config.manufacturing.default_fillet_radius,
    )

    laminate_keys = list(config.materials.laminates.keys())
    default_laminate = laminate_keys[0] if laminate_keys else None

    outlines = planner.load_outlines(dxf_dir, laminate=default_laminate)
    if not outlines:
        print("  No DXF outlines found to nest.")
        return

    laminate_orders = {
        name: lam.cut_order_steps() for name, lam in config.materials.laminates.items()
    }

    placements = planner.pack(outlines)
    manifest = planner.export(
        placements,
        nested_dir,
        engraving_depth=config.manufacturing.engraving_depth,
        laminate_cut_orders=laminate_orders,
    )

    print(f"  Nested sheets written to: {nested_dir}")
    print(f"  Manifest written to: {manifest}")


def main():
    parser = argparse.ArgumentParser(description="Open-EZ PDE Environment")
    parser.add_argument(
        "--generate-all", action="store_true", help="Generate CAD, CNC, and Docs"
    )
    parser.add_argument("--analysis", action="store_true", help="Run physics analysis")
    parser.add_argument("--jigs", action="store_true", help="Generate 3D printing jigs")
    parser.add_argument("--canard", action="store_true", help="Generate canard only")
    parser.add_argument("--wing", action="store_true", help="Generate main wing only")
    parser.add_argument(
        "--validate", action="store_true", help="Validate configuration only"
    )
    parser.add_argument(
        "--validate-physics",
        action="store_true",
        help="Validate aerodynamic/structural regressions",
    )
    parser.add_argument(
        "--compliance", action="store_true", help="Generate FAA compliance report"
    )
    parser.add_argument(
        "--nest-sheets", action="store_true", help="Nest DXF outlines onto stock sheets"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show configuration summary"
    )

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        return

    print(f"Open-EZ PDE v{config.version} [{config.baseline}]")

    if args.summary:
        print(config.summary())
        return 0

    if args.validate:
        return 0 if validate_config() else 1

    if args.validate_physics:
        return 0 if validate_physics() else 1

    # Validate before generating
    if not validate_config():
        print("\nAborting due to configuration errors.")
        return 1

    if args.analysis or args.generate_all:
        run_analysis()

    if args.jigs or args.generate_all:
        generate_manufacturing()

    if args.generate_all:
        generate_canard()
        generate_wing()
        generate_compliance_report()

    if args.canard and not args.generate_all:
        generate_canard()

    if args.wing and not args.generate_all:
        generate_wing()

    if args.compliance and not args.generate_all:
        generate_compliance_report()

    if args.nest_sheets:
        nest_sheets()

    print("\nDone.")


if __name__ == "__main__":
    main()
