"""
Open-EZ PDE: OpenVSP Integration Bridge
========================================

Formal interface to NASA's Vehicle Sketch Pad (OpenVSP).
Provides parametric geometry mapping and analysis execution.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
import json

from config import config

logger = logging.getLogger(__name__)

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
            logger.info("OpenVSP Python API detected successfully.")
            # VSP requires initialization
            vsp.VSPCheckIsInit()
            return vsp
        except ImportError:
            logger.warning("OpenVSP Python API not found. Integration will run in 'Headless/Surrogate' mode.")
            return None
        except Exception as e:
            logger.error(f"Error initializing OpenVSP: {e}")
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
                    "reflex_pct": airfoils.wing_reflex_percent
                },
                "canard": {
                    "span": geo.canard_span,
                    "root_chord": geo.canard_root_chord,
                    "tip_chord": geo.canard_tip_chord,
                    "sweep": geo.canard_sweep_le,
                    "incidence": geo.canard_incidence,
                    "airfoil": airfoils.canard.value
                }
            }
        }

        output_path = self.output_dir / "pde_vsp_metadata.json"
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        
        return output_path

    def run_aerodynamic_sweep(self, alpha_range: Tuple[float, float, int] = (-4, 12, 5)) -> Dict[str, Any]:
        """
        Execute an AoA sweep using VSPAERO or surrogate.
        
        Returns:
            Dictionary containing lift, drag, and moment coefficients.
        """
        if self.has_vsp:
            return self._run_native_sweep(alpha_range)
        else:
            return self._run_surrogate_sweep(alpha_range)

    def _run_native_sweep(self, alpha_range: Tuple[float, float, int]) -> Dict[str, Any]:
        """Drive the real OpenVSP/VSPAERO solver."""
        # This would involve:
        # 1. Clearing VSP world
        # 2. Building geometry via VSP API
        # 3. Setting up VSPAERO analysis
        # 4. Extracting results
        logger.info("Executing native VSPAERO sweep...")
        # Placeholder for real VSP API calls
        return {"mode": "native", "results": "FIXME: Implement native VSP calls"}

    def _run_surrogate_sweep(self, alpha_range: Tuple[float, float, int]) -> Dict[str, Any]:
        """Fall back to the PhysicsEngine surrogate results."""
        from .analysis import physics
        
        alphas = list(range(int(alpha_range[0]), int(alpha_range[1]) + 1, int((alpha_range[1]-alpha_range[0])/max(1, alpha_range[2]-1))))
        
        # Capture metrics for multiple points (simplified)
        sweep_data = []
        for a in alphas:
            # We use the physics engine's summary/metrics which are tuned for Long-EZ
            # Note: real implementation would iterate physics.calculate_cl_cd(a)
            sweep_data.append({
                "alpha": a,
                "cl": 0.1 * a, # mockup
                "cm": -0.02 # mockup
            })
            
        return {
            "mode": "surrogate",
            "sweep": sweep_data,
            "is_stable": physics.calculate_cg_envelope().is_stable
        }

# Singleton instance
vsp_bridge = VSPIntegration()
