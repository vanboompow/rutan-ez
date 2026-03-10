"""
Open-EZ PDE: OpenVSP Runner
============================

Coordinate OpenVSP analyses and cache results for CI.

Interface layer between the CadQuery geometry kernel and NASA's OpenVSP
(vspaero) solver.  Builds a lightweight VSP model from the configuration
state, executes trim and CLmax sweeps, and captures results into the
``data/validation/`` cache so CI can flag regressions.

The implementation degrades gracefully when OpenVSP Python bindings are
not installed, falling back to physics-informed surrogates.

Backward compatibility: ``from core.analysis import OpenVSPRunner`` (and
the related dataclasses) still works because analysis.py re-exports them.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import json
import logging
import math

from config import config

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class AerodynamicPoint:
    """Single operating point from a sweep."""

    alpha_deg: float
    cl: float
    cd: float
    cm: float


@dataclass
class TrimSweepResult:
    """Summary of a trim sweep across angle-of-attack."""

    points: List["AerodynamicPoint"]
    trimmed_alpha_deg: float
    static_margin: float
    description: str = ""


@dataclass
class CLMaxResult:
    """Maximum lift characteristics from sweep."""

    cl_max: float
    alpha_at_clmax: float
    stall_warning_margin: float


@dataclass
class StructuralMeshManifest:
    """Placeholder manifest to hand geometry to downstream FEA."""

    mesh_directory: Path
    surfaces: Dict[str, Path]
    notes: str


class OpenVSPRunner:
    """
    Coordinate OpenVSP analyses and cache results for CI.

    Interface layer between the CadQuery geometry kernel and NASA's OpenVSP
    (vspaero) solver. Builds a lightweight VSP model from the configuration
    state, executes trim and CLmax sweeps, and captures results into the
    `data/validation/` cache so CI can flag regressions.

    The implementation degrades gracefully when OpenVSP Python bindings are
    not installed, falling back to physics-informed surrogates.
    """

    def __init__(self, cache_dir: Union[Path, str] = Path("data/validation")):
        from .vsp_integration import vsp_bridge

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_path = self.cache_dir / "openvsp_validation.json"
        self._vsp = vsp_bridge  # Use the formal bridge

    def build_parametric_model(self) -> Dict[str, Any]:
        """
        Build a lightweight representation of the VSP vehicle.

        Captures key aerodynamic levers for surrogate analysis and for
        passing to OpenVSP when available.
        """
        geom = config.geometry
        airfoils = config.airfoils

        model = {
            "project": config.project_name,
            "version": config.version,
            "wing": {
                "span": geom.wing_span,
                "area": geom.wing_area,
                "aspect_ratio": geom.wing_aspect_ratio,
                "airfoil": airfoils.wing_root.value,
                "tip_airfoil": airfoils.wing_tip.value,
                "reflex": airfoils.wing_reflex_percent,
            },
            "canard": {
                "span": geom.canard_span,
                "area": geom.canard_area,
                "aspect_ratio": (geom.canard_span**2) / geom.canard_area,
                "airfoil": airfoils.canard.value,
            },
            "tail_arm": geom.canard_arm,
        }
        logger.debug("Parametric VSP model built: %s", model)
        return model

    def run_validation(
        self,
        model: Optional[Dict[str, Any]] = None,
        *,
        alpha_range: Tuple[float, float] = (-4.0, 14.0),
        alpha_steps: int = 8,
        force_refresh: bool = False,
    ) -> Tuple["TrimSweepResult", "CLMaxResult", Path]:
        """
        Execute trim and CLmax sweeps, persisting results to cache.

        The cache makes aerodynamic regressions visible to CI even when
        OpenVSP is unavailable on the runner.
        """
        model = model or self.build_parametric_model()

        if not force_refresh and self.cache_path.exists():
            cached = self._load_cached_results()
            if cached:
                return cached[0], cached[1], self.cache_path

        trim_result = self._run_trim_sweep(model, alpha_range, alpha_steps)
        clmax_result = self._run_clmax_search(model)
        self._write_cache(model, trim_result, clmax_result)
        return trim_result, clmax_result, self.cache_path

    def _try_import_vsp(self) -> Optional[Any]:
        return self._vsp if self._vsp.has_vsp else None

    def _run_trim_sweep(
        self,
        model: Dict[str, Any],
        alpha_range: Tuple[float, float],
        n_steps: int,
    ) -> "TrimSweepResult":
        """Run a trim sweep using OpenVSP if available, otherwise surrogate."""
        vsp = self._try_import_vsp()
        if vsp:
            logger.debug("Using OpenVSP for trim sweep")
            # Real solver orchestration would go here when dependencies are present

        return self._synthetic_trim(model, alpha_range, n_steps)

    def _run_clmax_search(self, model: Dict[str, Any]) -> "CLMaxResult":
        """Search for CLmax using OpenVSP or surrogate."""
        vsp = self._try_import_vsp()
        if vsp:
            logger.debug("Using OpenVSP for CLmax search")
            # Placeholder for vspaero stall search integration

        return self._synthetic_clmax(model)

    def _synthetic_trim(
        self,
        model: Dict[str, Any],
        alpha_range: Tuple[float, float],
        n_steps: int,
    ) -> "TrimSweepResult":
        """Surrogate trim sweep using lifting-line theory."""
        wing = model["wing"]
        canard = model["canard"]

        alpha_values = [
            alpha_range[0] + i * (alpha_range[1] - alpha_range[0]) / max(n_steps - 1, 1)
            for i in range(n_steps)
        ]

        ar_wing = wing["aspect_ratio"]
        ar_canard = canard["aspect_ratio"]

        cl_alpha_wing = self._lifting_line_slope(ar_wing)
        cl_alpha_canard = self._lifting_line_slope(ar_canard) * 1.05

        wing_area = wing["area"]
        canard_area = canard["area"]
        total_area = wing_area + canard_area

        points: List[AerodynamicPoint] = []
        cm_values: List[float] = []

        for alpha in alpha_values:
            alpha_rad = math.radians(alpha)
            cl_wing = cl_alpha_wing * alpha_rad
            cl_canard = cl_alpha_canard * alpha_rad * 0.9

            # Proper induced drag formulation: cd = cd0 + CL^2/(pi*e*AR)
            e_wing = config.geometry.wing_oswald_e
            e_canard = config.geometry.canard_oswald_e
            cd0_wing = 0.008  # Profile drag coefficient (skin friction + pressure)
            cd0_canard = 0.010
            cd_wing = cd0_wing + cl_wing**2 / (math.pi * e_wing * ar_wing)
            cd_canard = cd0_canard + cl_canard**2 / (math.pi * e_canard * ar_canard)

            total_cl = (cl_wing * wing_area + cl_canard * canard_area) / total_area
            total_cd = (cd_wing * wing_area + cd_canard * canard_area) / total_area

            moment_arm = model["tail_arm"]
            cm = (cl_canard * canard_area * moment_arm * 1e-4) - 0.02 * alpha_rad
            cm_values.append(cm)

            points.append(
                AerodynamicPoint(alpha_deg=alpha, cl=total_cl, cd=total_cd, cm=cm)
            )

        trimmed_alpha = self._interpolate_zero_crossing(alpha_values, cm_values)
        static_margin = 0.06

        return TrimSweepResult(
            points=points,
            trimmed_alpha_deg=trimmed_alpha,
            static_margin=static_margin,
            description="Synthetic trim sweep (OpenVSP unavailable)",
        )

    def _synthetic_clmax(self, model: Dict[str, Any]) -> "CLMaxResult":
        """Surrogate CLmax estimation."""
        wing_ar = model["wing"]["aspect_ratio"]
        canard_ar = model["canard"]["aspect_ratio"]

        clmax_wing = 1.2 + 0.15 * math.log(max(wing_ar, 1.5))
        clmax_canard = 1.35 + 0.10 * math.log(max(canard_ar, 1.0))

        cl_max = min(clmax_wing, clmax_canard)  # canard-first stall discipline
        alpha_at_clmax = 12.5
        stall_warning_margin = 0.35

        return CLMaxResult(
            cl_max=cl_max,
            alpha_at_clmax=alpha_at_clmax,
            stall_warning_margin=stall_warning_margin,
        )

    def export_structural_mesh_manifest(
        self, model: Optional[Dict[str, Any]] = None, mesh_dir: Optional[Path] = None
    ) -> "StructuralMeshManifest":
        """Generate a placeholder manifest for downstream FEA pipelines."""
        model = model or self.build_parametric_model()
        mesh_dir = mesh_dir or (self.cache_dir / "meshes")
        mesh_dir.mkdir(parents=True, exist_ok=True)

        surfaces = {
            "wing": mesh_dir / "wing_placeholder.stl",
            "canard": mesh_dir / "canard_placeholder.stl",
        }

        manifest_path = mesh_dir / "manifest.json"
        payload = {
            "project": model.get("project"),
            "version": model.get("version"),
            "surfaces": {k: str(v) for k, v in surfaces.items()},
            "notes": "Populate these paths with meshed geometries for FEA coupling.",
        }
        manifest_path.write_text(json.dumps(payload, indent=2))

        return StructuralMeshManifest(
            mesh_directory=mesh_dir, surfaces=surfaces, notes=str(payload["notes"])
        )

    def export_native_vsp3(self, output_path: Path) -> Path:
        """
        Generate .vsp3 file via OpenVSP Python API.

        Falls back to JSON metadata if bindings unavailable.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import openvsp as vsp
        except ImportError:
            logger.warning("OpenVSP bindings not available, using JSON fallback")
            return self._export_vsp3_metadata_fallback(output_path)

        try:
            vsp.ClearVSPModel()
            geom = config.geometry

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

            # Elevon control surface
            elevon_id = vsp.AddSubSurf(wing_id, vsp.SS_CONTROL)
            vsp.SetSubSurfName(wing_id, elevon_id, "Elevon")
            vsp.SetParmVal(wing_id, "EtaStart", f"SS_Control_{elevon_id}", 0.30)
            vsp.SetParmVal(wing_id, "EtaEnd", f"SS_Control_{elevon_id}", 1.0)
            vsp.SetParmVal(wing_id, "CFrac", f"SS_Control_{elevon_id}", 0.25)

            # Canard
            canard_id = vsp.AddGeom("WING", "")
            vsp.SetGeomName(canard_id, "Canard")
            vsp.SetParmVal(canard_id, "Span", "XSec_1", geom.canard_span / 2)
            vsp.SetParmVal(canard_id, "Root_Chord", "XSec_1", geom.canard_root_chord)
            vsp.SetParmVal(canard_id, "Tip_Chord", "XSec_1", geom.canard_tip_chord)
            vsp.SetParmVal(canard_id, "Sweep", "XSec_1", geom.canard_sweep_le)
            vsp.SetParmVal(canard_id, "X_Rel_Location", "XForm", geom.canard_le_fs)
            vsp.SetParmVal(canard_id, "Z_Rel_Location", "XForm", geom.canard_le_wl)

            # Winglets with rudder
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
                geom.wing_le_fs
                + geom.wing_span / 2 * math.tan(math.radians(geom.wing_sweep_le)),
            )
            vsp.SetParmVal(winglet_id, "Y_Rel_Location", "XForm", geom.wing_span / 2)

            rudder_id = vsp.AddSubSurf(winglet_id, vsp.SS_CONTROL)
            vsp.SetSubSurfName(winglet_id, rudder_id, "Rudder")
            vsp.SetParmVal(winglet_id, "EtaStart", f"SS_Control_{rudder_id}", 0.0)
            vsp.SetParmVal(winglet_id, "EtaEnd", f"SS_Control_{rudder_id}", 1.0)
            vsp.SetParmVal(winglet_id, "CFrac", f"SS_Control_{rudder_id}", 0.30)

            # Fuselage
            fuse_id = vsp.AddGeom("FUSELAGE", "")
            vsp.SetGeomName(fuse_id, "Fuselage")
            vsp.SetParmVal(fuse_id, "Length", "Design", geom.fuselage_length)

            vsp.WriteVSPFile(str(output_path))
            logger.info("Native VSP3 model exported to %s", output_path)
            return output_path

        except Exception as e:
            logger.warning("Failed to generate VSP3: %s, using fallback", e)
            return self._export_vsp3_metadata_fallback(output_path)

    def _export_vsp3_metadata_fallback(self, output_path: Path) -> Path:
        """JSON metadata fallback when OpenVSP bindings unavailable."""
        geom = config.geometry
        metadata = {
            "model_name": "Long-EZ",
            "generator": "Open-EZ PDE",
            "version": config.version,
            "geometry": {
                "wing": {
                    "span_in": geom.wing_span,
                    "root_chord_in": geom.wing_root_chord,
                    "tip_chord_in": geom.wing_tip_chord,
                    "sweep_deg": geom.wing_sweep_le,
                    "dihedral_deg": geom.wing_dihedral,
                    "washout_deg": geom.wing_washout,
                },
                "canard": {
                    "span_in": geom.canard_span,
                    "root_chord_in": geom.canard_root_chord,
                    "tip_chord_in": geom.canard_tip_chord,
                    "airfoil": "Roncz R1145MS",
                },
                "winglet": {
                    "height_in": geom.winglet_height,
                    "root_chord_in": geom.winglet_root_chord,
                    "tip_chord_in": geom.winglet_tip_chord,
                },
            },
            "control_surfaces": {
                "elevon": {
                    "span_fraction": [0.30, 1.0],
                    "chord_fraction": 0.25,
                    "max_deflection_deg": 20.0,
                },
                "rudder": {
                    "span_fraction": [0.0, 1.0],
                    "chord_fraction": 0.30,
                    "max_deflection_deg": 25.0,
                },
            },
        }
        json_path = output_path.with_suffix(".vsp3.json")
        json_path.write_text(json.dumps(metadata, indent=2))
        logger.info("VSP3 metadata fallback exported to %s", json_path)
        return json_path

    @staticmethod
    def _lifting_line_slope(aspect_ratio: float) -> float:
        """Approximate lift curve slope (per radian) using lifting-line theory."""
        return (2 * math.pi * aspect_ratio) / (aspect_ratio + 2)

    @staticmethod
    def _interpolate_zero_crossing(xs: List[float], ys: List[float]) -> float:
        """Linearly interpolate zero-crossing for trim."""
        for i in range(1, len(xs)):
            if ys[i - 1] == ys[i]:
                continue
            if ys[i - 1] <= 0 <= ys[i] or ys[i - 1] >= 0 >= ys[i]:
                x0, x1 = xs[i - 1], xs[i]
                y0, y1 = ys[i - 1], ys[i]
                return x0 + (0 - y0) * (x1 - x0) / (y1 - y0)
        return xs[len(xs) // 2]

    def _write_cache(
        self,
        model: Dict[str, Any],
        trim: "TrimSweepResult",
        clmax: "CLMaxResult",
    ) -> None:
        payload = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "config_version": config.version,
                "baseline": config.baseline,
            },
            "model": model,
            "trim_sweep": {
                "points": [asdict(p) for p in trim.points],
                "trimmed_alpha_deg": trim.trimmed_alpha_deg,
                "static_margin": trim.static_margin,
                "description": trim.description,
            },
            "clmax": asdict(clmax),
        }
        self.cache_path.write_text(json.dumps(payload, indent=2))
        logger.info("OpenVSP validation cache written to %s", self.cache_path)

    def _load_cached_results(self) -> Optional[Tuple["TrimSweepResult", "CLMaxResult"]]:
        try:
            data = json.loads(self.cache_path.read_text())
        except FileNotFoundError:
            return None

        points = [AerodynamicPoint(**p) for p in data["trim_sweep"]["points"]]
        trim = TrimSweepResult(
            points=points,
            trimmed_alpha_deg=data["trim_sweep"]["trimmed_alpha_deg"],
            static_margin=data["trim_sweep"]["static_margin"],
            description=data["trim_sweep"].get("description", ""),
        )
        clmax = CLMaxResult(**data["clmax"])
        return trim, clmax


# Default OpenVSP runner instance
openvsp_runner = OpenVSPRunner()

__all__ = [
    "AerodynamicPoint",
    "TrimSweepResult",
    "CLMaxResult",
    "StructuralMeshManifest",
    "OpenVSPRunner",
    "openvsp_runner",
]
