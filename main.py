#!/usr/bin/env python3
"""
Open-EZ PDE: Main Entry Point
=============================

Parametric Design Environment for the modernized Long-EZ.

Usage:
    python main.py --generate-all     Generate all components
    python main.py --canard           Generate canard only
    python main.py --wing             Generate wing only
    python main.py --generate-gcode   Emit synchronized hot-wire G-code
    python main.py --generate-jigs    Emit STL drill/incidence/vortilon jigs
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
        print(f"  Canard core exported to output/")
    except Exception as e:
        print(f"  Error generating canard: {e}")


def generate_wing() -> None:
    """Generate main wing foam cores."""
    from core.structures import WingGenerator
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
        description="Long-EZ main wing with Eppler 1230 modified"
    )

    step_dir = project_root / "output" / "STEP"
    step_dir.mkdir(parents=True, exist_ok=True)

    try:
        wing.generate_geometry()
        wing.cut_spar_trough()
        wing.export_step(step_dir)
        print(f"  Main wing exported to output/STEP/")
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


def generate_gcode() -> None:
    """Generate synchronized hot-wire G-code for wing and canard cores."""
    from core.structures import WingGenerator, CanardGenerator
    from core.aerodynamics import airfoil_factory

    print("\n--- Generating Hot-Wire G-code ---")

    manuf = config.manufacturing
    kerf_lookup = manuf.kerf_compensation
    foam_type = config.materials.wing_core_foam
    kerf = kerf_lookup.get(foam_type, manuf.kerf_styrofoam)

    gcode_dir = project_root / "output" / "gcode"
    gcode_dir.mkdir(parents=True, exist_ok=True)

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
        description="Long-EZ main wing hot-wire toolpath",
    )

    canard = CanardGenerator()

    for label, component in (("Main wing", wing), ("Canard", canard)):
        try:
            path = component.export_gcode(
                gcode_dir, kerf_offset=kerf, feed_rate=manuf.feed_rate_default
            )
            print(f"  {label} G-code: {path}")
        except Exception as e:
            print(f"  Error generating {label.lower()} G-code: {e}")


def generate_jigs() -> None:
    """Output STL drill guides, incidence cradles, and vortilon templates."""
    from core.manufacturing import JigGenerator

    print("\n--- Generating Jig STL Files ---")
    stl_dir = project_root / "output" / "stl"
    stl_dir.mkdir(parents=True, exist_ok=True)

    generator = JigGenerator()
    results = generator.generate_jigs(stl_dir)

    for jig_type, items in results.items():
        for item in items:
            print(f"  {jig_type} [{item.station_label}]: {item.path}")


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
        "--generate-gcode",
        action="store_true",
        help="Generate synchronized 4-axis hot-wire G-code"
    )
    parser.add_argument(
        "--generate-jigs",
        action="store_true",
        help="Generate STL incidence cradles, drill guides, and vortilon templates"
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
        generate_gcode()
        generate_jigs()

    if args.canard:
        generate_canard()

    if args.wing:
        generate_wing()

    if args.generate_gcode:
        generate_gcode()

    if args.generate_jigs:
        generate_jigs()

    if args.compliance:
        generate_compliance_report()

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
