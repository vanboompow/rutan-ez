# Open-EZ Parametric Design Environment (PDE)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## The Project

The Open-EZ PDE is a community-driven "Plans-as-Code" repository dedicated to the modernization of the Rutan Long-EZ (Model 61). We are transforming legacy 1970s aircraft plans into a living, version-controlled, and aerodynamically validated parametric design environment.

## The Problem

Legacy Long-EZ documentation is currently fragmented across unverified CAD files and scanned PDFs. These "raster" formats are prone to scaling errors that can lead to structural failure or dangerous misalignments during construction.

## The Solution: Plans-as-Code

By treating the aircraft's physical definition as executable **Python code**, we achieve:

* **Geometric Determinism:** Dimensions are derived from an algorithmic "Single Source of Truth" (SSOT) rather than static drawings.
* **Safety Mandates:** The system defaults to the **Roncz R1145MS "Rain Canard"** to prevent lift loss in wet conditions.
* **Manufacturing Automation:** Native generation of G-code for 4-axis CNC foam cutting and STL files for 3D-printable assembly jigs.
* **Aero Validation:** Direct integration with NASA's **OpenVSP** for stability and performance analysis.

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.10+ | Core platform |
| Geometry Engine | [CadQuery](https://github.com/CadQuery/cadquery) | OpenCASCADE B-Rep kernel for solid modeling |
| Aerodynamics | [OpenVSP](https://openvsp.org/) | NASA vortex lattice solver for stability analysis |
| Numerical Analysis | NumPy, SciPy | Airfoil spline interpolation, structural calculations |
| DXF Parsing | [ezdxf](https://github.com/mozman/ezdxf) | Legacy plan import and manufacturing DXF export |
| Compliance | ComplianceTracker | Automated FAA Form 8000-38 (51% Rule) credit tally |

## Getting Started

```bash
# Clone the repo
git clone https://github.com/quartermint/open-ez.git
cd open-ez

# Install dependencies
pip install -r requirements.txt

# Configure your build
# Edit config/aircraft_config.py to set pilot height, engine choice, and structural preferences

# Generate artifacts
python main.py --generate-all
```

This produces STEP, DXF, STL, and G-code outputs in the `output/` directory. All artifacts emit a `*.metadata.json` file capturing git revision, configuration hash, and contributor for full provenance tracking.

## Project Structure

```
open-ez/
  config/          Aircraft configuration (pilot height, engine, structural preferences)
  core/            Geometry classes, aerodynamics, manufacturing, compliance
  data/airfoils/   Airfoil .dat files (Selig/Lednicer format)
  output/          Generated artifacts (STEP/, STL/, DXF/, GCODE/, VSP/)
  scripts/         CI checks, smoke tests, generation scripts
  tests/           Physics regression, compliance gates, manufacturing accuracy
```

## Safety Disclaimer

> **This project involves safety-critical aviation design.** Outputs from this tool are intended as **Fabrication Aids** for amateur-built aircraft, not as certified engineering drawings or finished parts. All geometry, aerodynamic data, and manufacturing outputs are in active development and have **not been validated against physical hardware**.
>
> **Builders are solely responsible** for verifying all dimensions, structural calculations, and aerodynamic properties against independent sources before using any output from this project in aircraft construction. Errors in aircraft geometry can result in **structural failure, loss of control, or fatal accidents**.
>
> **The Roncz R1145MS canard airfoil is mandatory.** The original GU25-5(11)8 airfoil causes dangerous lift loss in rain due to surface contamination sensitivity. This project enforces the Roncz design as the default and will reject configurations that bypass it.

## Contributing

Contributions are welcome. This project uses pre-commit hooks and CI checks to enforce quality on every pull request.

### Setup

```bash
pip install -r requirements-dev.txt
pre-commit install
```

### Before Submitting a PR

1. **Lint and type-check:** `pre-commit run --all-files` (enforces ruff-format, mypy)
2. **Smoke test:** `python scripts/smoke_test.py` to verify STEP/STL/DXF/G-code artifact generation
3. **Physics validation:** Add `--check-openvsp` to the smoke test if you have the OpenVSP Python API installed
4. **Tests:** `pytest` to run the full test suite (physics regression, compliance gates, manufacturing accuracy)

### Safety Gates

PRs that do any of the following will not be accepted:

* Bypass or remove the Roncz R1145MS canard airfoil default
* Break configuration validation or SSOT propagation
* Skip OpenVSP aerodynamic checks
* Remove or weaken compliance tracking

## Regulatory Notice

This project is intended for educational purposes and as a **Fabrication Aid** for amateur builders operating under the Experimental Aircraft category. The ComplianceTracker module tallies builder fabrication credits to help ensure the aircraft qualifies for amateur-built status.

Users are responsible for ensuring their specific build complies with local aviation authority regulations, including but not limited to:

* **USA:** FAA 14 CFR Part 21.191(g) — Experimental, Amateur-Built
* **EASA:** CS-STAN / national authority guidance for amateur-built aircraft
* **Other jurisdictions:** Consult your national aviation authority

## License

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full text.

```
Copyright 2026 quartermint

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
```

---

*Inspired by the innovative spirit of Burt Rutan.*
