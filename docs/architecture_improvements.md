# Architecture Improvements for CNC + 3D Printing with Physics Validation

This roadmap lists concrete improvements needed to evolve the repository into a production-grade parametric environment that outputs CNC/3D-print-ready artifacts and validates them with physics-aware checks.

## Objectives
- Treat geometry, manufacturing, and physics logic as cohesive layers driven by the SSOT in `config/`.
- Support both subtractive (CNC) and additive (3D printing) fabrication without duplicating logic.
- Provide automated validation loops (aero + structural + kinematic) before releasing toolpaths.

## Layered Architecture
1. **Configuration Layer (SSOT)**
   - Harden `config/aircraft_config.py` as the only source for dimensions, materials, and process settings.
   - Add manufacturing presets: foam density, kerf data, printer nozzle/filament properties, and default tolerances.
   - Create validation schemas (e.g., Pydantic) to enforce units and ranges before geometry generation.

2. **Geometry Kernel (`core/`)**
   - Extend `core.base.AircraftComponent` metadata to track coordinate systems, mass properties, and fabrication method (CNC vs. print).
   - Add parametric builders for high-value parts: strake ribs, fuselage bulkheads, winglets, and control surfaces.
   - Normalize datum usage (nose station, waterline, buttline) across components to avoid alignment drift.

3. **Manufacturing Layer**
   - **Foam/CNC:**
     - Finalize `GCodeWriter` hot-wire synchronization with kerf compensation tables and safety travel envelopes.
     - Generate CNC templates (DXF) with alignment features, QR-code identifiers, and datum marks.
   - **3D Printing:**
     - Introduce a `PrintJig` component type to emit STL/3MF jigs for incidence, drilling, and layup alignment.
     - Provide print-specific slicing hints (wall count, infill patterns) via metadata blocks in exported 3MF.
     - Add lattice/lightweighting utilities for large-format prints to reduce mass while preserving stiffness.

4. **Physics & Testing Layer**
   - **Aerodynamics:** Keep `core.aerodynamics.AirfoilFactory` as the gatekeeper and integrate OpenVSP runs with regression baselines per configuration change.
   - **Structures:** Add a `structures` subpackage for simplified FEA (e.g., wing spar bending, bulkhead compression) using mesh exports from CadQuery.
   - **Kinematics:** Introduce control-surface travel checks and hinge moment estimates; validate clearance envelopes for CNC-cut parts.
   - **Mass Properties:** Automate inertial calculations from generated solids (volume * density) and enforce CG range checks before manufacturing outputs are released.

5. **Pipelines & Tooling**
   - Establish a `scripts/pipeline.py` entrypoint that runs: config validation → geometry generation → physics checks → export (STEP/DXF/STL/G-code).
   - Cache reusable artifacts (processed airfoils, mesh conversions) to speed CI.
   - Add structured logs and per-artifact manifests (JSON) that record config hashes, timestamps, and physics results.

6. **Testing Strategy**
   - Unit tests for geometry contracts (e.g., trailing-edge closure, datum alignment, clearance checks).
   - Golden-mastery tests for G-code header/footer structure and STL manifoldness using mesh validators.
   - Integration tests that run a minimal aircraft config through the full pipeline and assert physics envelopes (lift curve slope, bending margin).

## Incremental Delivery Plan
- **Milestone A:** Config schemas + metadata enrichment for `AircraftComponent`, plus manifest generation.
- **Milestone B:** Manufacturing layer split (CNC vs. printing) with jig abstractions and kerf/print presets.
- **Milestone C:** Physics harness integrating OpenVSP and lightweight FEA, wired into CI gates.
- **Milestone D:** End-to-end pipeline script with caching, structured logs, and artifact manifests; add regression tests.
