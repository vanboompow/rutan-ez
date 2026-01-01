import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

pytest.importorskip("cadquery", exc_type=ImportError)

from core.structures import CanardGenerator
from core.manufacturing import GCodeEngine, JigFactory
from config import config

def test_manufacturing_pipeline():
    print("🚀 Starting Manufacturing Pipeline Test...")
    
    # 1. Initialize Canard (Safety Critical)
    print("   Creating Canard core...")
    canard = CanardGenerator()
    canard.generate_geometry()
    
    # 2. Add Spar Troughs
    print("   Cutting spar troughs...")
    canard.cut_spar_trough()
    
    # 3. Use GCodeEngine to generate manufacturing output
    print("   Generating G-Code via GCodeEngine...")
    engine = GCodeEngine(output_root=Path("output/test_mfg"))
    gcode_path = engine.generate_component_gcode(canard, foam_name="styrofoam_blue")
    print(f"   ✅ G-Code generated: {gcode_path}")
    
    # 4. Generate Jigs
    print("   Generating assembly jigs...")
    jig_dir = Path("output/test_mfg/jigs")
    jig_dir.mkdir(parents=True, exist_ok=True)
    
    # Root cradle
    cradle = JigFactory.generate_incidence_cradle(
        canard, 
        station_bl=0.0, 
        incidence_angle=config.geometry.canard_incidence
    )
    import cadquery as cq
    cq.exporters.export(cradle, str(jig_dir / "canard_root_jig.stl"))
    print(f"   ✅ Jig generated: {jig_dir / 'canard_root_jig.stl'}")
    
    # 5. Export DXF
    print("   Exporting DXF templates...")
    dxf_path = canard.export_dxf(Path("output/test_mfg/dxf"))
    print(f"   ✅ DXF templates exported: {dxf_path}")
    
    print("\n🎉 Manufacturing Pipeline Test Completed Successfully!")

if __name__ == "__main__":
    test_manufacturing_pipeline()
