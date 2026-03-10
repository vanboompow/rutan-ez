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

    def _run_native_sweep(
        self,
        alpha_range: Tuple[float, float, int],
        polar_output: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Drive the real OpenVSP/VSPAERO VLM solver.

        Builds Long-EZ geometry, runs VSPAERO sweep, extracts CL/CD/CM polars,
        writes results to data/validation/vspaero_native_polars.json.
        """
        vsp = self._vsp
        geom = config.geometry

        logger.info("Executing native VSPAERO sweep...")

        # 1. Clear and rebuild geometry
        vsp.ClearVSPModel()

        # Main wing
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

        # Canard
        canard_id = vsp.AddGeom("WING", "")
        vsp.SetGeomName(canard_id, "Canard")
        vsp.SetParmVal(canard_id, "Span", "XSec_1", geom.canard_span / 2)
        vsp.SetParmVal(canard_id, "Root_Chord", "XSec_1", geom.canard_root_chord)
        vsp.SetParmVal(canard_id, "Tip_Chord", "XSec_1", geom.canard_tip_chord)
        vsp.SetParmVal(canard_id, "Sweep", "XSec_1", geom.canard_sweep_le)
        vsp.SetParmVal(canard_id, "X_Rel_Location", "XForm", geom.canard_le_fs)
        vsp.SetParmVal(canard_id, "Z_Rel_Location", "XForm", geom.canard_le_wl)

        # Winglets
        winglet_id = vsp.AddGeom("WING", "")
        vsp.SetGeomName(winglet_id, "Winglet")
        vsp.SetParmVal(winglet_id, "Span", "XSec_1", geom.winglet_height)
        vsp.SetParmVal(winglet_id, "Root_Chord", "XSec_1", geom.winglet_root_chord)
        vsp.SetParmVal(winglet_id, "Tip_Chord", "XSec_1", geom.winglet_tip_chord)
        vsp.SetParmVal(winglet_id, "Dihedral", "XSec_1", 90.0)
        vsp.SetParmVal(
            winglet_id,
            "X_Rel_Location",
            "XForm",
            geom.wing_le_fs + geom.wing_span / 2 * math.tan(math.radians(geom.wing_sweep_le)),
        )
        vsp.SetParmVal(winglet_id, "Y_Rel_Location", "XForm", geom.wing_span / 2)

        # Fuselage
        fuse_id = vsp.AddGeom("FUSELAGE", "")
        vsp.SetGeomName(fuse_id, "Fuselage")
        vsp.SetParmVal(fuse_id, "Length", "Design", geom.fuselage_length)

        # 1b. Finalize geometry and write to disk for VSPAERO
        vsp.Update()
        vsp3_path = str(Path("output/VSP/long_ez_vspaero.vsp3").resolve())
        vsp.SetVSP3FileName(vsp3_path)
        vsp.WriteVSPFile(vsp3_path)
        logger.info("VSP model written to %s", vsp3_path)

        # Compute DegenGeom — VSPAERO reads these files, not the .vsp3 directly
        vsp.ComputeDegenGeom(vsp.SET_ALL, vsp.DEGEN_GEOM_CSV_TYPE)

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

        # 3. Execute
        logger.info("Running VSPAERO VLM sweep (%d alpha points)...", n_pts)
        results_id = vsp.ExecAnalysis("VSPAEROSweep")

        # 4. Extract results
        cl_arr: List[float] = list(vsp.GetDoubleResults(results_id, "CL"))
        cd_arr: List[float] = list(vsp.GetDoubleResults(results_id, "CD"))
        cm_arr: List[float] = list(vsp.GetDoubleResults(results_id, "CMy"))

        # Build alpha array
        if n_pts > 1:
            step = (alpha_end - alpha_start) / (n_pts - 1)
            alphas = [alpha_start + i * step for i in range(n_pts)]
        else:
            alphas = [alpha_start]

        # Pad or trim arrays to n_pts if needed
        def _pad(arr: List[float], length: int) -> List[float]:
            if len(arr) >= length:
                return arr[:length]
            return arr + [0.0] * (length - len(arr))

        cl_arr = _pad(cl_arr, n_pts)
        cd_arr = _pad(cd_arr, n_pts)
        cm_arr = _pad(cm_arr, n_pts)

        points = [
            {"alpha_deg": alphas[i], "cl": cl_arr[i], "cd": cd_arr[i], "cm": cm_arr[i]}
            for i in range(n_pts)
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
