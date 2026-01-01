#!/usr/bin/env python3
# ruff: noqa: E402

"""
Open-EZ PDE: Roncz Canard Core Generator
========================================

This script generates the Roncz R1145MS canard foam core.
SAFETY: This airfoil is MANDATORY - it prevents rain-induced pitch-down.

Usage:
    python scripts/generate_canard.py

Outputs:
    - output/STEP/canard_core.step    (CAD exchange format)
    - output/STL/canard_core.stl      (3D printing jigs)
    - output/DXF/canard_core_root.dxf (Root template)
    - output/DXF/canard_core_tip.dxf  (Tip template)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import config
from core.structures import CanardGenerator


def main():
    """Generate the Roncz canard foam core and export artifacts."""

    print("=" * 60)
    print("Open-EZ PDE: Roncz R1145MS Canard Core Generator")
    print("=" * 60)
    print()

    # Validate configuration
    errors = config.validate()
    if errors:
        print("CONFIGURATION ERRORS:")
        for err in errors:
            print(f"  - {err}")
        print()

    # Show configuration summary
    print(config.summary())

    # Output directories
    step_dir = project_root / "output" / "STEP"
    stl_dir = project_root / "output" / "STL"
    dxf_dir = project_root / "output" / "DXF"

    # Ensure directories exist
    for d in [step_dir, stl_dir, dxf_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Initialize the canard generator
    print("\n[1/4] Initializing Canard Generator...")
    canard = CanardGenerator()
    print(f"      Airfoil: {canard.root_airfoil.name}")
    print(f"      Span: {canard.span / 12:.2f} ft")
    print(f"      Root Chord: {canard.root_chord} in")
    print(f"      Tip Chord: {canard.tip_chord} in")
    print(f"      Sweep: {canard.sweep_angle}°")

    # Generate geometry
    print("\n[2/4] Generating Lofted Geometry...")
    try:
        canard.generate_geometry()
        print("      Loft successful.")
    except Exception as e:
        print(f"      ERROR: Geometry generation failed: {e}")
        print("      This may occur if CadQuery is not installed.")
        print("      Install with: pip install cadquery")
        return 1

    # Export STEP
    print("\n[3/4] Exporting CAD Files...")
    try:
        step_file = canard.export_step(step_dir)
        print(f"      STEP: {step_file}")
    except Exception as e:
        print(f"      STEP export failed: {e}")

    try:
        stl_file = canard.export_stl(stl_dir)
        print(f"      STL:  {stl_file}")
    except Exception as e:
        print(f"      STL export failed: {e}")

    # Export DXF templates
    print("\n[4/4] Exporting Manufacturing Templates...")
    try:
        canard.export_dxf(dxf_dir)
        print(f"      DXF templates written to: {dxf_dir}")
    except Exception as e:
        print(f"      DXF export failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print("""
Next Steps:
-----------
1. Review output/STEP/canard_core.step in your CAD viewer
2. Use output/DXF templates for verification against legacy plans
3. Generate G-code with: python scripts/generate_gcode.py canard

SAFETY REMINDER:
----------------
The Roncz R1145MS airfoil is MANDATORY for the canard.
The original GU25-5(11)8 causes dangerous lift loss in rain.
DO NOT substitute airfoils without full aerodynamic analysis.
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
