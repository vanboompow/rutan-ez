# Architecture Roadmap for 3D Printing, CNC, and Physics Validation

This roadmap translates the current Open-EZ PDE foundations into a production-ready architecture that can drive 3D-printed tooling, CNC hot-wire foam cutting, and physics-based testing. It assumes the **Single Source of Truth (SSOT)** lives in `config/aircraft_config.py` and that geometry primitives extend the base classes in `core/`.

## Objectives
- Guarantee every manufacturing artifact (G-code, STL, DXF) is generated from SSOT-derived geometry.
- Provide reusable pipelines for 3D-printed fixtures and 4-axis hot-wire toolpaths.
- Add physics-test harnesses that validate loads, aero, and mass properties before releasing artifacts.

## Baseline Capabilities
- **Geometry core:** `core/base.py` defines `AircraftComponent` and `FoamCore` with STEP/STL/DXF export hooks. `core/structures.py` implements `WingGenerator`, `CanardGenerator`, and `Fuselage` lofting, while `core/aerodynamics.py` ingests and processes airfoils.
- **Configuration:** `config/aircraft_config.py` captures geometry, materials, manufacturing, and compliance parameters as the SSOT.
- **Compliance:** `core/compliance.py` tracks FAA 51% rule tasks and builder credit.

## Proposed Architecture Improvements

### 1) Repository Layout & Data Flow
- **Outputs by modality:** add structured subfolders under `output/` (`step/`, `stl/`, `gcode/`, `reports/`, `vsp/`) with helper utilities that route exports from any `AircraftComponent` subclass to the correct target.
- **Analysis workspace:** create `analysis/` for physics and aero test harnesses (OpenVSP XML builders, structural load cases, mass-properties checks) with per-run artifacts written to `output/reports/`.
- **Data contracts:** define `pydantic`-style schemas (or dataclasses with validators) for airfoil, station, and material inputs to enforce SSOT integrity before geometry or manufacturing code executes.

### 2) Manufacturing Pipeline for CNC & 3D Printing
- **Toolpath core (`core/manufacturing/`):**
  - `gcode_writer.py`: encapsulate 4-axis synchronization, kerf compensation per foam type, and feed-rate scheduling tied to `config.manufacturing`.
  - `segmenter.py`: split long wings/canards into foam-block-friendly spans, generating per-block root/tip profiles and registration marks.
  - `stock_setup.py`: capture fixture coordinate systems, wire temperature presets, and safe-travel envelopes for different machines.
- **Fixture & jig generation (`core/fixtures/`):**
  - `incidence_jigs.py`: generate cradle STLs at configurable butt-lines with flat datum faces for assembly alignment.
  - `drill_guides.py`: parametric guides for engine mount, landing gear, and control-tube bores with chamfers and drill bushings.
  - `vortilon_templates.py`: printable leading-edge clip geometry keyed to Roncz airfoil surfaces.
- **Manufacturing QA:** integrate templated checks that compare target profiles to post-offset toolpaths (e.g., point cloud deviation, chord/LE/TE alignment) and flag deltas exceeding tolerance.

### 3) Physics & Test Automation
- **Aerodynamic validation:** expose an `OpenVSPBuilder` that converts SSOT geometry into .vsp3 files, runs vortex-lattice sweeps, and returns stability margins and CL/CM curves into structured JSON.
- **Structural evaluation:** add lightweight FEA hooks (e.g., CalculiX or OpenCASCADE mesh export) driven by load cases defined in `analysis/load_cases.py` (gusts, landing loads, torsion). Report factors of safety and displacement envelopes alongside geometry metadata.
- **Mass properties:** include inertia estimation and CG envelope checks tied to component metadata; block commits or artifact export when the CG window is violated.
- **Automated regression:** wire `pytest` suites that instantiate representative components (canard, wing panel, bulkhead) and assert geometry validity, toolpath generation success, and physics checks above minimum thresholds.

### 4) CLI & Orchestration Enhancements
- Extend `main.py` into a task-driven CLI (`python main.py generate --all` / `--stl` / `--gcode` / `--analysis`) that orchestrates geometry creation, manufacturing exports, and physics tests in one command.
- Provide dependency-injection of config overrides (YAML/JSON) so builders can sweep parameters (e.g., washout, spar depth) without editing Python source.
- Emit run manifests (component hashes, config snapshot, timestamps) to `output/reports/` for traceability and FAA compliance documentation.

### 5) Documentation & Contributor Experience
- Add architecture diagrams illustrating data flow from `config/` → `core/geometry` → `core/manufacturing` → `analysis/` → `output/`.
- Supply contributor templates for adding new components (skeletal class inheriting `AircraftComponent`, test scaffold, and CLI hook) to standardize incoming PRs.
- Create safety guardrails in documentation that reiterate Roncz-canard enforcement, kerf calibration steps, and CNC operator responsibilities.

## Phased Delivery Plan
1. **Foundation:** codify output directory helpers, establish `analysis/` and `core/manufacturing/` packages, and harden SSOT validation.
2. **Manufacturing enablement:** implement toolpath writer, segmenter, and initial jig generators; integrate CLI targets for `--stl` and `--gcode`.
3. **Physics validation:** deliver OpenVSP and structural test harnesses with pytest-backed regression gates; publish automated build reports.
4. **Builder UX:** finalize documentation, contributor templates, and compliance-ready manifests to support repeatable CNC/3D printing workflows.
