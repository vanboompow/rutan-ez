# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open-EZ PDE is a "Plans-as-Code" Parametric Design Environment for modernizing the Rutan Long-EZ (Model 61) aircraft. It transforms fragmented legacy plans into executable Python code with aerodynamic validation.

## Tech Stack

- **Python 3.10+**
- **CadQuery** (OpenCASCADE B-Rep kernel) - script-centric geometry generation
- **OpenVSP** (NASA) - aerodynamic validation via vortex lattice solver
- **NumPy/SciPy** - numerical analysis, airfoil spline interpolation
- **ezdxf** - legacy DXF parsing

## Build Commands

```bash
pip install -r requirements.txt
python main.py --generate-all  # Produces STEP, DXF, G-code outputs
```

## Architecture

### Core Design Principle: Single Source of Truth (SSOT)
All dimensions derive from `config/aircraft_config.py`. Never hard-code dimensions - use derived variables. Changes to config propagate through geometry, analysis, and documentation.

### Directory Structure
- `config/` - Aircraft configuration (pilot height, engine, structural preferences)
- `core/` - Geometry classes (AircraftComponent base class)
- `data/airfoils/` - .dat files (Selig/Lednicer format)
- `output/` - Generated artifacts (STEP/, STL/, DXF/, GCODE/, VSP/)

### Key Modules
- **AirfoilFactory**: Ingests .dat files, applies CubicSpline smoothing, handles trailing-edge closure
- **WingGenerator**: Lofting with sweep, dihedral, washout; spar cap trough subtraction based on ply counts
- **GCodeWriter**: 4-axis hot-wire synchronization for CNC foam cutting
- **ComplianceTracker**: FAA Form 8000-38 credit tally for 51% Rule

### Base Class Pattern
All components inherit from `AircraftComponent` with mandatory methods:
- `generate_geometry()` - CadQuery solid generation
- `export_dxf()` - Manufacturing artifact export

## Critical Safety Mandate

**Default to Roncz R1145MS canard airfoil** - not optional. The original GU25-5(11)8 airfoil causes dangerous lift loss in rain. The Roncz design prevents pitch-down moments from surface contamination.

## Airfoil Processing

When working with airfoil data:
1. Parse .dat files from UIUC database format
2. Apply `scipy.interpolate.CubicSpline` for smoothing
3. Use Savitzky-Golay filter to remove digitization noise
4. Ensure closed trailing edge
5. Support `apply_washout(angle)` and `apply_reflex(percent)` methods

## Manufacturing Output

- **G-code**: 4-axis paths with root/tip synchronization, kerf compensation based on wire diameter and foam density
- **STL**: Incidence jigs, drill guides, vortilon templates
- **DXF**: Laser-cut bulkheads

## Regulatory Compliance

The system must generate **Fabrication Aids**, not finished parts, to maintain FAA amateur-built status. The ComplianceTracker tallies builder credits to ensure >50% builder contribution per 14 CFR Part 21.191(g).
