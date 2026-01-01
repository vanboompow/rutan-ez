#!/usr/bin/env python3
"""
Open-EZ PDE: Main Entry Point
=============================

Parametric Design Environment for the modernized Long-EZ.

Usage:
    python main.py --generate-all     Generate all components
    python main.py --canard           Generate canard only
    python main.py --wing             Generate wing only
    python main.py --validate         Validate configuration
    python main.py --compliance       Generate compliance report

All dimensions derive from config/aircraft_config.py (SSOT).
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config


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


def generate_canard() -> None:
    """Generate canard foam core."""
    from core.structures import CanardGenerator
    from core.compliance import compliance_task_tracker

    print("\n--- Generating Canard ---")
    canard = CanardGenerator()

    step_dir = project_root / "output" / "STEP"
    stl_dir = project_root / "output" / "STL"
    dxf_dir = project_root / "output" / "DXF"
    docs_dir = project_root / "output" / "docs"

    for d in [step_dir, stl_dir, dxf_dir, docs_dir]:
        d.mkdir(parents=True, exist_ok=True)

    try:
        canard.generate_geometry()
        canard.export_step(step_dir)
        canard.export_stl(stl_dir)
        canard.export_dxf(dxf_dir)
        compliance_task_tracker.record_generation(
            component="canard",
            artifact="cad",
            note="Canard CAD exported for builder-operated hot-wire tooling.",
        )
        layup_file = compliance_task_tracker.write_layup_schedule("canard", docs_dir)
        compliance_task_tracker.record_generation(
            component="canard",
            artifact="layup_schedule",
            note=f"Layup schedule captured in {layup_file.name} for DAR review.",
        )
        print(f"  Canard core exported to output/")
    except Exception as e:
        print(f"  Error generating canard: {e}")


def generate_wing() -> None:
    """Generate main wing foam cores."""
    from core.structures import WingGenerator
    from core.aerodynamics import airfoil_factory
    from core.compliance import compliance_task_tracker

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
        description="Long-EZ main wing with Eppler 1230 modified"
    )

    step_dir = project_root / "output" / "STEP"
    docs_dir = project_root / "output" / "docs"
    step_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    try:
        wing.generate_geometry()
        wing.cut_spar_trough()
        wing.export_step(step_dir)
        compliance_task_tracker.record_generation(
            component="wing",
            artifact="cad",
            note="Wing CAD loft exported for builder-operated cutting.",
        )
        layup_file = compliance_task_tracker.write_layup_schedule("wing", docs_dir)
        compliance_task_tracker.record_generation(
            component="wing",
            artifact="layup_schedule",
            note=f"Wing layup schedule documented in {layup_file.name}.",
        )
        print(f"  Main wing exported to output/STEP/")
    except Exception as e:
        print(f"  Error generating wing: {e}")


def generate_compliance_report() -> None:
    """Generate FAA compliance report."""
    from core.compliance import compliance_task_tracker, compliance_tracker

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

    checklist_file = compliance_task_tracker.write_checklist(docs_dir)
    print(f"  Checklist written to: {checklist_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Open-EZ Parametric Design Environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py --validate         Check configuration
    python main.py --generate-all     Generate all components
    python main.py --canard           Generate canard only

For more information, see README.md
        """
    )

    parser.add_argument(
        "--generate-all",
        action="store_true",
        help="Generate all aircraft components"
    )
    parser.add_argument(
        "--canard",
        action="store_true",
        help="Generate canard foam core only"
    )
    parser.add_argument(
        "--wing",
        action="store_true",
        help="Generate main wing only"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration only"
    )
    parser.add_argument(
        "--compliance",
        action="store_true",
        help="Generate FAA compliance report"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show configuration summary"
    )

    args = parser.parse_args()

    # Default to showing summary if no args
    if len(sys.argv) == 1:
        print(config.summary())
        parser.print_help()
        return 0

    print("=" * 60)
    print(f"Open-EZ PDE v{config.version}")
    print(f"Baseline: {config.baseline}")
    print("=" * 60)

    if args.summary:
        print(config.summary())
        return 0

    if args.validate:
        return 0 if validate_config() else 1

    # Validate before generating
    if not validate_config():
        print("\nAborting due to configuration errors.")
        return 1

    if args.generate_all:
        generate_canard()
        generate_wing()
        generate_compliance_report()

    if args.canard:
        generate_canard()

    if args.wing:
        generate_wing()

    if args.compliance:
        generate_compliance_report()

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
