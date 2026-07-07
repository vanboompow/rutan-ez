# Open-EZ Wrapup Signoff

**Date:** 2026-05-23
**Status:** Parked (5 weeks stale at session start, now clean)
**Branch:** main, in sync with origin/main
**Last commit:** `docs: refresh Forge knowledge exports (3dprinting, aviation, bridges)`

## Project framing (current)

Plans-as-Code parametric design for Rutan Long-EZ (Model 61). Personal aviation
project — Ryan bought the original paper plans in Apr 2026 to actually build one.
The earlier "AeroForge validation reference" framing is **superseded**; no startup
thesis attached. Code lives on as a personal modernization of legacy plans.

## What has shipped

- **v1.0 — Physics & Structural Foundations** (2026-02-28): 6 phases. Physics
  fixes (washout, Anderson lift curve, canard efficiency, distributed loads,
  piecewise MAC, induced drag), structural analysis (BeamFEA, Buckling, CLT
  Tsai-Wu via composite FEA), aero (Reynolds, stall, reflex ramp). 22 validation
  tests.
- **v1.1 — Physical Validation & Calibration** (2026-03-13, 4 days, 7 phases,
  97 commits, 17,367 LOC, 241 tests passing): RAF CP-29/CP-31 reference dataset
  with provenance, D-box composite structural model (deflection 89,169" -> 2.34"),
  OpenVSP 3.48.2 VSPAERO VLM integration with CI surrogate fallback, 12-metric
  accuracy report (9 PASS), fs_wing_le calibrated 133->125.61" against Rutan CP-29.
- Original 5-phase implementation plan: SSOT config, AirfoilFactory, Roncz
  R1145MS mandate, GCodeWriter (4-axis hot-wire), ComplianceTracker
  (FAA Form 8000-38), full airframe synthesis, timestamped output packages.

## What is parked / known gaps

- Wing area discrepancy: full trapezoidal 110 sqft vs RAF semi-panel 94.2 sqft.
- Empty weight: partial structural model vs community builds (821-891 lb).
- `fs_wing_le` 125.61" pending CP-31 physical confirmation.
- `altitude_ft` ignored in Reynolds calc (hardcoded 8000 ft).
- No v1.2 milestone scoped. No active sprint backlog (all phases complete;
  `sprint_backlog.md` retained as historical record).

## Session triage

Only dirty files were three Forge knowledge exports (3D printing, aviation,
bridges contexts) — refreshed reference material, not source changes.
Single atomic commit, pushed to origin/main. No surprises, no secrets touched.
Untracked artifacts (`__pycache__`, `Unnamed.vspaero`, `whacked.tri`) are
correctly gitignored.

## Next touch

Most likely trigger: Ryan starting the physical build with the paper plans.
At that point useful additions would be:
- Resolve wing-area convention mismatch against builders' community numbers
- Physical CP-31 confirmation of `fs_wing_le`
- Altitude-aware Reynolds (parametric vs hardcoded 8000 ft)
- Empty-weight model completion to land in 821-891 lb community range
- Layup-by-layup composite schedule export aligned to actual build sequence

## Files to read first when returning

1. `CLAUDE.md` — architecture, SSOT principle, key modules
2. `README.md` — project overview, safety notice, Roncz mandate
3. `.planning/MILESTONES.md` — full v1.0 and v1.1 deliverables + carry-forward gaps
4. `config/aircraft_config.py` — SSOT for all dimensions
5. `core/` — geometry, analysis, structures, manufacturing, vsp_integration
6. `output/compliance/FAA_compliance_audit.md` — 51% Rule credit state
7. `sprint_backlog.md` — historical record of completed sprints
