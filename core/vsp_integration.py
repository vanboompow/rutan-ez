"""
Open-EZ PDE: OpenVSP Integration Bridge
========================================

Formal interface to NASA's Vehicle Sketch Pad (OpenVSP).
Provides parametric geometry mapping and analysis execution.
"""

import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from config import config

logger = logging.getLogger(__name__)

# Output path for native polar results
_NATIVE_POLARS_PATH = Path("data/validation/vspaero_native_polars.json")


class VSPIntegration:
    """
    Main bridge for OpenVSP interactions.

    Handles:
    - Native OpenVSP API detection and initialization
    - Mapping PDE config to VSP parameters
    - Exporting .vsp3 and .vsp3.json models
    - Driving VSPAERO for stability/drag analysis
    """

    def __init__(self, output_dir: Union[Path, str] = Path("output/vsp")):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._vsp = self._try_import_vsp()

    def _try_import_vsp(self) -> Optional[Any]:
        """Attempt to load the OpenVSP Python API."""
        try:
            import openvsp as vsp

            version = vsp.GetVSPVersion()
            logger.info("OpenVSP %s detected successfully.", version)
            return vsp
        except ImportError:
            logger.warning(
                "OpenVSP Python API not found. Integration will run in 'Headless/Surrogate' mode."
            )
            return None
        except Exception as e:
            logger.error("Error initializing OpenVSP: %s", e)
            return None

    @property
    def has_vsp(self) -> bool:
        """True if the real OpenVSP API is available."""
        return self._vsp is not None

    def export_parametric_metadata(self) -> Path:
        """
        Export current configuration as a VSP-compatible JSON metadata file.
        This allows the real OpenVSP tool to ingest PDE parameters.
        """
        geo = config.geometry
        airfoils = config.airfoils

        data = {
            "pde_version": config.version,
            "timestamp": None,  # To be filled by runner
            "components": {
                "wing": {
                    "span": geo.wing_span,
                    "root_chord": geo.wing_root_chord,
                    "tip_chord": geo.wing_tip_chord,
                    "sweep": geo.wing_sweep_le,
                    "dihedral": geo.wing_dihedral,
                    "washout": geo.wing_washout,
                    "incidence": geo.wing_incidence,
                    "root_airfoil": airfoils.wing_root.value,
                    "reflex_pct": airfoils.wing_reflex_percent,
                },
                "canard": {
                    "span": geo.canard_span,
                    "root_chord": geo.canard_root_chord,
                    "tip_chord": geo.canard_tip_chord,
                    "sweep": geo.canard_sweep_le,
                    "incidence": geo.canard_incidence,
                    "airfoil": airfoils.canard.value,
                },
            },
        }

        output_path = self.output_dir / "pde_vsp_metadata.json"
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        return output_path

    def run_aerodynamic_sweep(
        self, alpha_range: Tuple[float, float, int] = (-4, 14, 19)
    ) -> Dict[str, Any]:
        """
        Execute an AoA sweep using VSPAERO or surrogate.

        Args:
            alpha_range: (alpha_start, alpha_end, n_points) tuple.
                         Default is -4 to 14 deg in 1-deg steps (19 points).

        Returns:
            Dictionary with mode, points (list of alpha_deg/cl/cd/cm dicts),
            and solver metadata.
        """
        if self.has_vsp:
            try:
                return self._run_native_sweep(alpha_range)
            except Exception as exc:
                logger.warning(
                    "Native VSPAERO sweep failed (%s), falling back to surrogate.", exc
                )
                return self._run_surrogate_sweep(alpha_range)
        else:
            return self._run_surrogate_sweep(alpha_range)

    @staticmethod
    def _parse_vspaero_polar(polar_path: Path, n_pts: int) -> Tuple[List[float], List[float], List[float], List[float]]:
        """
        Parse a VSPAERO .polar file and extract AoA, CLtot, CDtot, CMytot columns.

        The .polar file format (OpenVSP 3.48.2) is fixed-width with 3 header lines:
          Line 1: section group labels
          Line 2: sub-group labels
          Line 3: column names (space-separated)
          Lines 4+: data rows

        Returns: (alphas, cls, cds, cms) as lists of floats.

        Background: GetDoubleResults() does not populate results from VSPGEOM-mode
        VLM analyses in OpenVSP 3.48.2 Python bindings. Direct polar-file parsing
        is the correct approach for this version.
        """
        if not polar_path.exists():
            raise FileNotFoundError(f"VSPAERO .polar file not found: {polar_path}")

        with open(polar_path) as f:
            lines = f.readlines()

        # Strip the 3 header lines
        header_lines = 3
        data_lines = [ln for ln in lines[header_lines:] if ln.strip()]

        if not data_lines:
            raise ValueError(f"No data rows found in {polar_path}")

        # Parse column names from line 3 (index 2)
        col_names = lines[2].split()
        try:
            idx_aoa = col_names.index("AoA")
            idx_cl = col_names.index("CLtot")
            idx_cd = col_names.index("CDtot")
            idx_cm = col_names.index("CMytot")
        except ValueError as e:
            raise ValueError(f"Expected column not found in polar header: {e}") from e

        alphas, cls, cds, cms = [], [], [], []
        for row in data_lines:
            vals = row.split()
            if len(vals) <= max(idx_aoa, idx_cl, idx_cd, idx_cm):
                continue
            alphas.append(float(vals[idx_aoa]))
            cls.append(float(vals[idx_cl]))
            cds.append(float(vals[idx_cd]))
            cms.append(float(vals[idx_cm]))

        return alphas, cls, cds, cms

    def _run_native_sweep(
        self,
        alpha_range: Tuple[float, float, int],
        polar_output: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Drive the real OpenVSP/VSPAERO VLM solver.

        Builds Long-EZ geometry, runs VSPAERO sweep, extracts CL/CD/CM polars,
        writes results to data/validation/vspaero_native_polars.json.

        Key implementation notes for OpenVSP 3.48.2:
        - VSPGEOM filename must share the same base path as the VSP3 file.
          VSPAERO derives its input path from the current VSP3 filename.
        - ExportFile: thick_set=SET_NONE, thin_set=THIN_SET (user set 3).
          Only WING geoms (wing, canard, winglet) are added to THIN_SET.
          Fuselage and thick bodies are NOT added, so they are excluded.
        - GetDoubleResults() does not populate from VSPGEOM-mode VLM analysis;
          results are parsed from the .polar file after ExecAnalysis().
        - VLM models lifting surfaces only; fuselage excluded for solver stability.
        """
        vsp = self._vsp
        geom = config.geometry

        logger.info("Executing native VSPAERO sweep...")

        # 1. Clear and rebuild geometry
        vsp.ClearVSPModel()

        # CRITICAL: OpenVSP WING geoms default to Sym_Planar_Flag=2.0 (XZ plane symmetry),
        # which causes ExportFile to generate BOTH halves in the VSPGEOM (full span,
        # Y=-span/2 to +span/2, 2 surface copies). VSPAERO with Symmetry=1 expects a
        # HALF-SPAN model (Y=0 to +span/2, 1 surface copy) and mirrors it internally.
        # When given both halves, VSPAERO crashes with "Could not find global edge for
        # trailing wake!" due to duplicate trailing-edge topology.
        # Fix: explicitly set Sym_Planar_Flag=0.0 (no OpenVSP symmetry) on all lifting
        # surface geoms. We define the right half-span only; VSPAERO handles mirroring.
        NO_SYM_FLAG = 0.0

        # Main wing — right half only (Y=0 to +wing_span/2).
        # VSPAERO Symmetry=1 will mirror it to create the full-span solution.
        wing_id = vsp.AddGeom("WING", "")
        vsp.SetGeomName(wing_id, "MainWing")
        vsp.SetParmVal(wing_id, "Span", "XSec_1", geom.wing_span / 2)
        vsp.SetParmVal(wing_id, "Root_Chord", "XSec_1", geom.wing_root_chord)
        vsp.SetParmVal(wing_id, "Tip_Chord", "XSec_1", geom.wing_tip_chord)
        vsp.SetParmVal(wing_id, "Sweep", "XSec_1", geom.wing_sweep_le)
        vsp.SetParmVal(wing_id, "Dihedral", "XSec_1", geom.wing_dihedral)
        vsp.SetParmVal(wing_id, "Twist", "XSec_1", -geom.wing_washout)
        vsp.SetParmVal(wing_id, "X_Rel_Location", "XForm", geom.wing_le_fs)
        vsp.SetParmVal(wing_id, "Z_Rel_Location", "XForm", geom.wing_le_wl)
        vsp.SetParmVal(wing_id, "Sym_Planar_Flag", "Sym", NO_SYM_FLAG)  # Half-span only

        # Canard — right half only (Y=0 to +canard_span/2).
        canard_id = vsp.AddGeom("WING", "")
        vsp.SetGeomName(canard_id, "Canard")
        vsp.SetParmVal(canard_id, "Span", "XSec_1", geom.canard_span / 2)
        vsp.SetParmVal(canard_id, "Root_Chord", "XSec_1", geom.canard_root_chord)
        vsp.SetParmVal(canard_id, "Tip_Chord", "XSec_1", geom.canard_tip_chord)
        vsp.SetParmVal(canard_id, "Sweep", "XSec_1", geom.canard_sweep_le)
        vsp.SetParmVal(canard_id, "X_Rel_Location", "XForm", geom.canard_le_fs)
        vsp.SetParmVal(canard_id, "Z_Rel_Location", "XForm", geom.canard_le_wl)
        vsp.SetParmVal(canard_id, "Sym_Planar_Flag", "Sym", NO_SYM_FLAG)  # Half-span only

        # Note: Winglets and fuselage are intentionally omitted from the VLM model.
        # VLM (vortex lattice method) models lifting surfaces only. Fuselage exclusion
        # avoids thick/thin surface mixing. Winglets at dihedral=90 deg add tip-node
        # complexity; their contribution to the pitch polar is small.

        # 1b. Update geometry
        vsp.Update()

        # 1c. Classify lifting surfaces as thin VLM panels using a user set.
        #     Only wing and canard are added to THIN_SET.
        THIN_SET = vsp.SET_FIRST_USER  # User set index 3
        vsp.SetSetName(THIN_SET, "ThinSurfaces")
        vsp.SetSetFlag(wing_id, THIN_SET, True)
        vsp.SetSetFlag(canard_id, THIN_SET, True)
        # Call Update() after set classification to finalize membership
        vsp.Update()

        # 1d. Write VSP3 file.
        # CRITICAL: VSPAERO derives its geometry filenames from the VSP3 base path.
        # The .vspgeom must share the same base path as the .vsp3 file.
        vsp3_path = str(Path("output/VSP/long_ez_vspaero.vsp3").resolve())
        vsp.SetVSP3FileName(vsp3_path)
        vsp.WriteVSPFile(vsp3_path)
        logger.info("VSP model written to %s", vsp3_path)

        # 1e. Export VSPGEOM: thick_set=SET_NONE (no thick displacement bodies),
        #     thin_set=THIN_SET (only WING geoms, not fuselage).
        #     The VSPGEOM filename must match the VSP3 base name exactly.
        vspgeom_path = vsp3_path.replace(".vsp3", ".vspgeom")
        vsp.ExportFile(vspgeom_path, vsp.SET_NONE, vsp.EXPORT_VSPGEOM, False, THIN_SET)
        logger.info("VSPGEOM exported to %s (%d bytes)", vspgeom_path, Path(vspgeom_path).stat().st_size)

        # Set reference wing for VSPAERO Sref/bref/cref
        vsp.SetVSPAERORefWingID(wing_id)

        # 2. Set up VSPAERO analysis
        alpha_start = float(alpha_range[0])
        alpha_end = float(alpha_range[1])
        n_pts = int(alpha_range[2])

        vsp.SetAnalysisInputDefaults("VSPAEROSweep")
        # Alpha sweep
        vsp.SetDoubleAnalysisInput("VSPAEROSweep", "AlphaStart", [alpha_start])
        vsp.SetDoubleAnalysisInput("VSPAEROSweep", "AlphaEnd", [alpha_end])
        vsp.SetIntAnalysisInput("VSPAEROSweep", "AlphaNpts", [n_pts])
        # Incompressible (Mach 0)
        vsp.SetDoubleAnalysisInput("VSPAEROSweep", "MachStart", [0.0])
        # Y-symmetry (half model)
        vsp.SetIntAnalysisInput("VSPAEROSweep", "Symmetry", [1])
        # Reference geometry from config
        # Wing mean aerodynamic chord (average of root and tip for trapezoidal wing)
        wing_mac = (geom.wing_root_chord + geom.wing_tip_chord) / 2.0
        vsp.SetDoubleAnalysisInput("VSPAEROSweep", "Sref", [geom.wing_area])
        vsp.SetDoubleAnalysisInput("VSPAEROSweep", "bref", [geom.wing_span])
        vsp.SetDoubleAnalysisInput("VSPAEROSweep", "cref", [wing_mac])

        # 3. Execute — VSPAERO runs as a subprocess; results go to disk (.polar file)
        logger.info("Running VSPAERO VLM sweep (%d alpha points)...", n_pts)
        vsp.ExecAnalysis("VSPAEROSweep")

        # 4. Parse results from .polar file (GetDoubleResults does not populate
        #    in OpenVSP 3.48.2 VSPGEOM-mode VLM analysis)
        polar_file_path = Path(vsp3_path.replace(".vsp3", ".polar"))
        logger.info("Parsing VSPAERO polars from %s", polar_file_path)
        alphas, cl_arr, cd_arr, cm_arr = self._parse_vspaero_polar(polar_file_path, n_pts)

        if not alphas:
            raise RuntimeError(
                f"VSPAERO polar file exists but contains no data rows: {polar_file_path}"
            )

        logger.info(
            "VSPAERO solved: %d points, CL range [%.3f, %.3f]",
            len(alphas), min(cl_arr), max(cl_arr),
        )

        points = [
            {"alpha_deg": alphas[i], "cl": cl_arr[i], "cd": cd_arr[i], "cm": cm_arr[i]}
            for i in range(len(alphas))
        ]

        vsp_version = str(vsp.GetVSPVersion())
        solver_settings = {
            "method": "VLM",
            "mach": 0.0,
            "symmetry": True,
            "alpha_range": [alpha_start, alpha_end],
            "n_points": n_pts,
        }

        # 5. Write polar JSON
        output_data = {
            "source": "vspaero_native",
            "vsp_version": vsp_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "solver_settings": solver_settings,
            "points": points,
        }

        out_path = Path(polar_output) if polar_output is not None else _NATIVE_POLARS_PATH
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(output_data, f, indent=2)
        logger.info("Native VSPAERO polars written to %s", out_path)

        return {
            "mode": "native",
            "source": "vspaero_native",
            "points": points,
            "solver_settings": solver_settings,
            "vsp_version": vsp_version,
        }

    def _run_surrogate_sweep(
        self, alpha_range: Tuple[float, float, int]
    ) -> Dict[str, Any]:
        """Fall back to OpenVSPAdapter surrogate results."""
        from .simulation.openvsp_adapter import OpenVSPAdapter

        alpha_start = float(alpha_range[0])
        alpha_end = float(alpha_range[1])
        n_pts = int(alpha_range[2])

        if n_pts > 1:
            step = (alpha_end - alpha_start) / (n_pts - 1)
            alphas = [alpha_start + i * step for i in range(n_pts)]
        else:
            alphas = [alpha_start]

        adapter = OpenVSPAdapter()
        polars = adapter.run_vspaero(alphas=alphas)
        points = [
            {"alpha_deg": p.alpha_deg, "cl": p.cl, "cd": p.cd, "cm": p.cm}
            for p in polars
        ]
        # Include is_stable for backward compatibility with existing consumers
        from .analysis import physics
        return {
            "mode": "surrogate",
            "source": "openvsp_adapter",
            "points": points,
            "is_stable": physics.calculate_cg_envelope().is_stable,
        }


# Singleton instance
vsp_bridge = VSPIntegration()
if vsp_bridge.has_vsp:
    try:
        vsp_version = vsp_bridge._vsp.GetVSPVersion()
        logger.info("OpenVSP %s detected - native VSPAERO available", vsp_version)
    except Exception:
        logger.info("OpenVSP detected - native VSPAERO available")
