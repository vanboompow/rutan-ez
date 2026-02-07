# Open-EZ PDE Due Diligence Report

## Scope
This report consolidates the requested architecture deep-dive across:
- **SSOT integrity audit** (`config/aircraft_config.py` as source of truth)
- **Compliance-driven manufacturing gate proposal**
- **ElectricEZ product hypotheses**
- **Developer onboarding dependency graph**

---

## Phase 1 — SSOT Leakage Audit (Debt Map)

### A. High-risk SSOT leaks (hard-coded values in `core/` and `scripts/`)

| Area | Evidence | Leak Type | Risk |
|---|---|---|---|
| `core/analysis.py` baseline W&B | `_init_standard_weights()` hard-codes wing/canard/fuselage/engine weights and arms (e.g., `85.0`, `250.0`, `195.0`). | Config bypass | CG can diverge from propulsion/geometry config silently. |
| `core/analysis.py` fuel modeling | `add_fuel(..., arm: float = 95.0)` and `gallons * 6.0` are fixed. | Physics constants outside config | Inconsistent fuel arm if tank geometry or strake model changes. |
| `core/systems.py` propulsion mounts | Multiple geometry constants for firewall and mounting (`18.0`, `20.0`, `0.040`, HV hole maps, etc.). | Manufacturing geometry encoded in code | Changes require code edits, not config tweaks; non-deterministic across subsystems. |
| `core/manufacturing.py` process DB | Kerf/temp/feed calibration values duplicated in `GCodeEngine.processes` instead of reading `config.manufacturing`. | SSOT duplication | Calibration drift between config and generated G-code. |
| `core/structures.py` fuselage profiles | Bulkhead dimensions include hard-coded widths/heights/floor positions. | Parametric geometry partially externalized | Structural geometry no longer fully from SSOT, undermining reproducibility. |
| `scripts/*` operational defaults | Several scripts instantiate components with implicit defaults and ad-hoc flow (manual staging + manual verification). | Process leak | Human-in-the-loop overhead and inconsistent outcomes per run. |

### B. Roncz Mandate enforceability audit

**Findings:** enforcement is **partly architectural, partly discipline-based**.

- Strong enforcement exists in the airfoil factory path: `get_canard_airfoil()` always returns Roncz and warns if config is changed.
- `CanardGenerator` uses `AirfoilFactory().get_canard_airfoil()` and records metadata indicating Roncz safety mandate.
- `AircraftConfig.validate()` flags non-Roncz as a safety violation.

**Gap:** Any custom call path that bypasses `CanardGenerator` and directly calls low-level constructors/loaders can still instantiate non-Roncz surfaces for non-canard contexts without strict type-level constraints. Net: **good guardrails, not absolute compile-time policy enforcement**.

### C. Propulsion → CG propagation audit

**Finding:** propagation is **not automatic end-to-end**.

- `core/systems.py` computes propulsion weights in `get_weight_items()` for Lycoming/ElectricEZ.
- `core/analysis.py` maintains an internal, hard-coded baseline weight table in `PhysicsEngine._init_standard_weights()` and does **not** ingest propulsion system weight items automatically.
- There is no event bridge or composition root that injects `get_propulsion_system(...).get_weight_items()` into `PhysicsEngine` before CG analysis.

**Consequence:** switching propulsion in config can modify systems outputs without automatically shifting analysis CG unless the developer manually wires data.

---

## Phase 2 — Compliance-Driven Architecture Proposal (Gatekeeper Agent)

### Problem
Current manufacturing flow permits G-code generation regardless of compliance state. A human effectively acts as regulatory QA.

### Proposal
Promote `ComplianceTracker` to a **build gate** integrated with manufacturing orchestration.

### Target architecture

1. Add a `ManufacturingOrchestrator` service:
   - Inputs: `component`, `foam_name`, build context, optional task evidence.
   - Calls `ComplianceTracker.preflight(...)` before any `GCodeEngine.generate_component_gcode(...)`.
2. Add `ComplianceTracker.preflight_manufacturing(task_ids, method, strict=True)`:
   - Verifies task existence and permitted method (`BUILDER_CNC`/`BUILDER_MANUAL`).
   - Computes projected credit and blocks generation when projected compliance drops below policy threshold or evidence is missing.
3. `GCodeEngine` becomes a pure execution backend.
4. CI hook (`scripts/run_ci_checks.py`) runs compliance preflight on manufacturing-targeted changes.

### Enforcement behavior
- **Fail-closed**: reject G-code artifact generation on compliance violation.
- Emit machine-readable violation report JSON.
- Allow explicit override only with signed audit note (`--override-with-waiver <file>`).

### Example interface contract
```python
result = orchestrator.generate_gcode_with_compliance(
    component=canard,
    foam_name="styrofoam_blue",
    task_ids=["canard_cores"],
    method=ManufacturingMethod.BUILDER_CNC,
)
# Raises ComplianceGateError if 51% constraints/evidence policy violated.
```

### Impact
- Removes per-commit manual regulatory inspection burden.
- Converts compliance from documentation artifact to executable policy.

---

## Phase 3 — ElectricEZ Testable Hypotheses (5–10)

Focus area: coupling between `core/systems.py` (ElectricEZ) and `core/vsp_integration.py` (aero model metadata/sweep).

1. **Cooling geometry coupling hypothesis**  
   If StrakeGenerator exposes `generate_cooling_plenum(heat_rejection_kw)` sourced from propulsion thermal metrics, then battery thermal margin at climb power can improve while reducing manual duct redesign cycles by >30%.

2. **Battery CG fidelity hypothesis**  
   If battery module positions are exported as distributed mass stations (not single strake midpoint arm), CG prediction error versus measured empty-weight can be reduced by >20%.

3. **Metadata parity hypothesis**  
   If `VSPIntegration.export_parametric_metadata()` includes propulsion mode, battery mass, cooling inlet area, and prop diameter, surrogate sweep outputs will correlate better with propulsion variant changes (fewer false “no-delta” results).

4. **Geometry-driven drag hypothesis**  
   If firewall cooling inlet and cable-penetration geometry in ElectricEZ is reflected in VSP wetted-area proxies, predicted cruise drag delta can be bounded within ±10% of flight-test estimates.

5. **Range prediction hypothesis**  
   If `ElectricEZ.get_endurance()` and `get_range()` consume aerodynamic drag curves from VSP sweep instead of fixed cruise power assumptions, predicted range error can be reduced by >15%.

6. **Config unification hypothesis**  
   If ElectricEZ constants (mount geometry, HV routing, cooling aperture sizing) are moved from code constants to `PropulsionConfig`/`ManufacturingParams`, configuration portability and build reproducibility will increase (fewer code edits per variant).

7. **Canard-propulsion interaction hypothesis**  
   If propulsion mass distribution updates trigger automatic canard/wing trim analysis, static margin excursions during conversion scenarios can be detected earlier (before artifact generation).

8. **Strake battery cassette hypothesis**  
   If strake cassette geometry is generated directly from `battery_cell_pitch/module_count` plus service-clearance policy, installation time can drop by ~25% with fewer fit-check iterations.

---

## Phase 4 — Developer Onboarding Guide (Compounding Knowledge Loop)

## Dependency Graph

```text
Config (config/aircraft_config.py)
  -> Geometry (core/structures.py + core/aerodynamics.py)
    -> Analysis (core/analysis.py + core/vsp_integration.py)
      -> Manufacturing (core/manufacturing.py)
        -> Compliance (core/compliance.py + audit scripts)
```

### 1) Config (SSOT)
- All canonical dimensions, materials, propulsion defaults, and compliance weights should originate here.
- Any constant repeated elsewhere is technical debt unless justified as universal physics constant.

### 2) Geometry (CadQuery)
- `AirfoilFactory` provides profile ingestion and smoothing.
- `CanardGenerator` enforces Roncz path; main wing/fuselage generators consume config geometry.
- Segmentation and jig generation are geometry-to-manufacturing bridges.

### 3) Analysis (Physics/OpenVSP)
- `PhysicsEngine` computes MAC/NP/static margin and simplified canard stall safety checks.
- `VSPIntegration` exports metadata and runs native/surrogate sweeps.
- Current debt: propulsion mass is not automatically composed into analysis state.

### 4) Manufacturing (G-code/Jigs)
- `GCodeWriter` handles synchronized XYUV cut path generation.
- `GCodeEngine` applies foam process parameters and writes machine output.
- Current debt: process calibration table duplicates config knowledge.

### 5) Compliance (51% Rule)
- `ComplianceTracker` tracks task completion, method, and credit accumulation.
- Should become an active gate for manufacturing generation, not passive reporting only.

---

## Priority Backlog (Suggested Execution Order)

1. **P0 Safety/SSOT:** Introduce `MassPropertiesConfig` and move `PhysicsEngine._init_standard_weights()` constants into config.
2. **P0 Integration:** Add automatic propulsion weight injection into analysis session.
3. **P1 Compliance Automation:** Implement gatekeeper preflight before G-code generation.
4. **P1 Manufacturing SSOT:** Replace `GCodeEngine.processes` literals with `config.manufacturing`-derived mapping.
5. **P2 ElectricEZ/VSP Coupling:** Extend VSP metadata to include propulsion + cooling + battery distribution parameters.

---

## Concise Due Diligence Conclusion

The repository is structurally aligned with a Plans-as-Code strategy, but SSOT leakage in analysis/manufacturing constants and missing automatic propulsion→CG composition create deterministic risk. Roncz safety is strongly guarded yet not mathematically impossible to bypass. Converting compliance into an executable manufacturing gate is the highest leverage change for reducing builder friction while improving regulatory assurance.
