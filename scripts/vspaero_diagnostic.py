"""
VSPAERO Diagnostic Script — Plan 03-06 Task 1
==============================================

Minimal standalone script that isolates the VSPAERO VLM pipeline from the
full Long-EZ model. Uses a single rectangular wing to reveal whether issues
are in geometry complexity or fundamental API usage.

Run with:
    python3.13 scripts/vspaero_diagnostic.py
"""

import math
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Step 0: Import openvsp
# ---------------------------------------------------------------------------
try:
    import openvsp as vsp
    print(f"[OK] openvsp imported — version: {vsp.GetVSPVersion()}")
except ImportError as e:
    print(f"[FAIL] Cannot import openvsp: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Step 1: Clear model and add a single rectangular wing
# ---------------------------------------------------------------------------
print("\n--- Step 1: Build geometry ---")
vsp.ClearVSPModel()
print("[OK] Model cleared")

wing_id = vsp.AddGeom("WING", "")
vsp.SetGeomName(wing_id, "DiagWing")

# Simple rectangular wing: span=100 in, chord=20 in, no sweep/dihedral
vsp.SetParmVal(wing_id, "Span", "XSec_1", 100.0)
vsp.SetParmVal(wing_id, "Root_Chord", "XSec_1", 20.0)
vsp.SetParmVal(wing_id, "Tip_Chord", "XSec_1", 20.0)
vsp.SetParmVal(wing_id, "Sweep", "XSec_1", 0.0)
vsp.SetParmVal(wing_id, "Dihedral", "XSec_1", 0.0)
vsp.SetParmVal(wing_id, "X_Rel_Location", "XForm", 0.0)
vsp.SetParmVal(wing_id, "Y_Rel_Location", "XForm", 0.0)
vsp.SetParmVal(wing_id, "Z_Rel_Location", "XForm", 0.0)

print(f"[OK] Wing added — ID: {wing_id}")

# ---------------------------------------------------------------------------
# Step 2: First Update
# ---------------------------------------------------------------------------
print("\n--- Step 2: First vsp.Update() ---")
vsp.Update()
print("[OK] Update complete")

# Check geom count
all_geoms = vsp.FindGeoms()
print(f"[INFO] Total geoms in model: {len(all_geoms)}")
for gid in all_geoms:
    print(f"       geom_id={gid} name={vsp.GetGeomName(gid)}")

# ---------------------------------------------------------------------------
# Step 3: Create user set for thin surfaces, add wing
# ---------------------------------------------------------------------------
print("\n--- Step 3: Set up thin surface set ---")

# SET_FIRST_USER = 3 in most OpenVSP builds
THIN_SET = vsp.SET_FIRST_USER
print(f"[INFO] THIN_SET index: {THIN_SET}")

# Name the set for clarity
vsp.SetSetName(THIN_SET, "ThinSurfaces")
print(f"[OK] Set {THIN_SET} named 'ThinSurfaces'")

# Add wing to thin set
vsp.SetSetFlag(wing_id, THIN_SET, True)
flag = vsp.GetSetFlag(wing_id, THIN_SET)
print(f"[OK] Wing in THIN_SET: {flag}")

# ---------------------------------------------------------------------------
# Step 4: Second Update after set classification
# ---------------------------------------------------------------------------
print("\n--- Step 4: Second vsp.Update() after SetSetFlag ---")
vsp.Update()
print("[OK] Second update complete")

# ---------------------------------------------------------------------------
# Step 5: Set reference wing
# ---------------------------------------------------------------------------
print("\n--- Step 5: Set VSPAERO reference wing ---")
vsp.SetVSPAERORefWingID(wing_id)
print("[OK] Reference wing set")

# ---------------------------------------------------------------------------
# Step 6: Export VSPGEOM — try both approaches
# ---------------------------------------------------------------------------
print("\n--- Step 6: Export VSPGEOM ---")
out_dir = Path("output/VSP")
out_dir.mkdir(parents=True, exist_ok=True)

vsp3_path = str((out_dir / "diag_wing.vsp3").resolve())
vsp.SetVSP3FileName(vsp3_path)
vsp.WriteVSPFile(vsp3_path)
print(f"[OK] VSP3 file written: {vsp3_path}")

# Option A: Only thin surfaces (SET_NONE for thick body set)
vspgeom_path_a = vsp3_path.replace(".vsp3", "_optA.vspgeom")
print(f"\n[INFO] Trying Option A: ExportFile(path, SET_NONE, EXPORT_VSPGEOM, False, THIN_SET)")
vsp.ExportFile(vspgeom_path_a, vsp.SET_NONE, vsp.EXPORT_VSPGEOM, False, THIN_SET)
if Path(vspgeom_path_a).exists():
    size_a = Path(vspgeom_path_a).stat().st_size
    print(f"[OK] Option A .vspgeom exists — size: {size_a} bytes")
    # Read first few lines to check coordinates
    with open(vspgeom_path_a) as f:
        lines = f.readlines()[:20]
    print(f"[INFO] Option A first {len(lines)} lines:")
    for line in lines:
        print(f"       {line.rstrip()}")
else:
    print(f"[FAIL] Option A .vspgeom not found at {vspgeom_path_a}")

# Option B: SET_ALL for thick set (current approach)
vspgeom_path_b = vsp3_path.replace(".vsp3", "_optB.vspgeom")
print(f"\n[INFO] Trying Option B: ExportFile(path, SET_ALL, EXPORT_VSPGEOM, False, THIN_SET)")
vsp.ExportFile(vspgeom_path_b, vsp.SET_ALL, vsp.EXPORT_VSPGEOM, False, THIN_SET)
if Path(vspgeom_path_b).exists():
    size_b = Path(vspgeom_path_b).stat().st_size
    print(f"[OK] Option B .vspgeom exists — size: {size_b} bytes")
    # Read first few lines to check coordinates
    with open(vspgeom_path_b) as f:
        lines = f.readlines()[:20]
    print(f"[INFO] Option B first {len(lines)} lines:")
    for line in lines:
        print(f"       {line.rstrip()}")
else:
    print(f"[FAIL] Option B .vspgeom not found at {vspgeom_path_b}")

# ---------------------------------------------------------------------------
# Step 7: Discover VSPAEROSweep analysis inputs
# ---------------------------------------------------------------------------
print("\n--- Step 7: Discover VSPAEROSweep inputs ---")
try:
    input_names = vsp.GetAnalysisInputNames("VSPAEROSweep")
    print(f"[OK] VSPAEROSweep has {len(input_names)} inputs:")
    for name in input_names:
        print(f"     - {name}")
except Exception as e:
    print(f"[FAIL] GetAnalysisInputNames failed: {e}")

# ---------------------------------------------------------------------------
# Step 8: Configure and run VSPAEROSweep at single alpha point
# ---------------------------------------------------------------------------
print("\n--- Step 8: Run VSPAEROSweep at alpha=5 deg ---")

vsp.SetAnalysisInputDefaults("VSPAEROSweep")

# Set geometry file path (Option A — only thin set)
try:
    vsp.SetStringAnalysisInput("VSPAEROSweep", "GeomSet", [str(THIN_SET)])
    print(f"[OK] Set GeomSet = {THIN_SET}")
except Exception as e:
    print(f"[WARN] Could not set GeomSet: {e}")

# Single alpha point at 5 degrees
vsp.SetDoubleAnalysisInput("VSPAEROSweep", "AlphaStart", [5.0])
vsp.SetDoubleAnalysisInput("VSPAEROSweep", "AlphaEnd", [5.0])
vsp.SetIntAnalysisInput("VSPAEROSweep", "AlphaNpts", [1])

# Incompressible
vsp.SetDoubleAnalysisInput("VSPAEROSweep", "MachStart", [0.0])

# Y-symmetry (half model)
vsp.SetIntAnalysisInput("VSPAEROSweep", "Symmetry", [1])

# Reference geometry: simple rectangular wing
ref_area = 100.0 * 20.0  # span * chord = 2000 sq in
ref_span = 200.0          # full span (both sides)
ref_chord = 20.0          # chord
vsp.SetDoubleAnalysisInput("VSPAEROSweep", "Sref", [ref_area])
vsp.SetDoubleAnalysisInput("VSPAEROSweep", "bref", [ref_span])
vsp.SetDoubleAnalysisInput("VSPAEROSweep", "cref", [ref_chord])

print("[INFO] Running VSPAEROSweep...")
try:
    results_id = vsp.ExecAnalysis("VSPAEROSweep")
    print(f"[OK] ExecAnalysis complete — results_id: {results_id}")
except Exception as e:
    print(f"[FAIL] ExecAnalysis raised exception: {e}")
    results_id = None

# ---------------------------------------------------------------------------
# Step 9: Extract and print results
# ---------------------------------------------------------------------------
print("\n--- Step 9: Extract results ---")
if results_id:
    try:
        cl_arr = list(vsp.GetDoubleResults(results_id, "CL"))
        cd_arr = list(vsp.GetDoubleResults(results_id, "CD"))
        cm_arr = list(vsp.GetDoubleResults(results_id, "CMy"))
        print(f"[OK] CL array: {cl_arr}")
        print(f"[OK] CD array: {cd_arr}")
        print(f"[OK] CM array: {cm_arr}")
        if cl_arr and cl_arr[0] != 0.0:
            print(f"[OK] VSPAERO SOLVED: CL={cl_arr[0]:.4f} at alpha=5 deg")
        elif cl_arr:
            print(f"[WARN] VSPAERO returned CL=0 — solver may not have iterated")
        else:
            print(f"[FAIL] CL array is empty — VSPAERO did not produce results")
    except Exception as e:
        print(f"[FAIL] GetDoubleResults failed: {e}")
else:
    print("[SKIP] No results_id, skipping extraction")

# ---------------------------------------------------------------------------
# Step 10: Check VSPAERO stdout file for iteration info
# ---------------------------------------------------------------------------
print("\n--- Step 10: Check VSPAERO output files ---")
vsp3_dir = out_dir.resolve()
vspaero_stdout = list(vsp3_dir.glob("*.vspaero")) + list(vsp3_dir.glob("*.history"))
print(f"[INFO] VSPAERO output files in {vsp3_dir}:")
for f in sorted(vsp3_dir.iterdir()):
    print(f"       {f.name} ({f.stat().st_size} bytes)")

# Check for .history file (indicates iterations ran)
history_files = list(vsp3_dir.glob("*.history"))
if history_files:
    for hf in history_files:
        print(f"\n[INFO] History file: {hf.name}")
        with open(hf) as f:
            lines = f.readlines()
        if lines:
            print(f"       First line: {lines[0].rstrip()}")
            print(f"       Last line: {lines[-1].rstrip()}")
            print(f"       Total iterations: {len(lines)}")
        else:
            print("       [EMPTY] No iterations recorded")
else:
    print("[WARN] No .history file found — VSPAERO may not have iterated")

# Check for .polar file
polar_files = list(vsp3_dir.glob("*.polar"))
if polar_files:
    for pf in polar_files:
        print(f"\n[INFO] Polar file: {pf.name}")
        with open(pf) as f:
            content = f.read()
        print(f"       Content:\n{content[:500]}")
else:
    print("[WARN] No .polar file found")

print("\n--- Diagnostic complete ---")
