"""Simulation adapters for aerodynamic and structural validation."""

from .openvsp_adapter import AeroPolar, OpenVSPAdapter
from .fea_adapter import BeamResult, BeamSection, BeamFEAAdapter, DBoxSection, DBoxResult, DBoxBeamAdapter
from .regression import RegressionRunner, RegressionScenario, ScenarioResult

__all__ = [
    "AeroPolar",
    "OpenVSPAdapter",
    "BeamResult",
    "BeamSection",
    "BeamFEAAdapter",
    "DBoxSection",
    "DBoxResult",
    "DBoxBeamAdapter",
    "RegressionRunner",
    "RegressionScenario",
    "ScenarioResult",
]
