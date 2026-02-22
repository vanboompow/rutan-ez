# Open-EZ PDE: Master Implementation Plan

This plan outlines the journey from "Imaging" (Parametric Logic & Design) to "Completion" (G-Code generation for prototype production).

## Phase 1: The Digital Foundation (Infrastructure & Ontology)
**Focus:** Establishing the "Single Source of Truth" (SSOT).
*   **[OPS] CI/CD Setup:** Initialize automated linting and a lightweight geometry smoke test (`python scripts/smoke_test.py`).
*   **[ARCH] aircraft_config.py:** Build the global parameters singleton (WINGSPAN, ROOT_CHORD, etc.).
*   **[ARCH] AirfoilFactory:** Implement `.dat` parsing logic with `scipy.interpolate.CubicSpline` for smooth surface generation.
*   **[GOV] ComplianceTracker:** Implement the `TaskAudit` logger to start tracking 51% rule credits for code-generated components.

## Phase 2: Aerodynamic Intelligence (The Roncz Mandate)
**Focus:** Flight safety and parametric stability.
*   **[AERO] OpenVSP Bridge:** Create the `vsp_integration.py` to map CadQuery parameters to VSP geometries.
*   **[AERO] Stability Gates:** Script automated Neutral Point (NP) and CoG analysis.
*   **[ARCH] Canard Lofting:** Implement the Roncz R1145MS geometry with "Rain Slot" and "Vortilon" support.
*   **[ARCH] MassProperties:** Link every `AircraftComponent` to a mass/material density to calculate real-time CoG.

## Phase 3: Manufacturing Automation (The Smart Workshop)
**Focus:** Translating digital design to physical foam.
*   **[MFG] GCodeEngine:** Develop the 4-axis hot-wire synchronization logic for tapered wings (Root-to-Tip timing).
*   **[MFG] Kerf Management:** Implement foam density-based kerf correction in G-code generation.
*   **[MFG] JigFactory:** Generate STL files for incidence cradles and drill guides.
*   **[ARCH] DXF Wrapper:** Automated export of bulkhead profiles for laser/water-jet cutting.

## Phase 4: Full Airframe Synthesis
**Focus:** Structural integration and configuration validation.
*   **[ARCH] Fuselage Generator:** Implement the F-22 (Pilot) to F-28 (Firewall) lofting sequence.
*   **[AERO] Full-Vehicle CFD:** Conduct final drag polar and lift slope verification in OpenVSP.
*   **[GOV] FAA Audit:** Generate the final Form 8000-38 checklist based on the project history.
*   **[OPS] Documentation:** Compile the "Living Build Manual" by injecting code-derived dimensions into Markdown templates.

## Phase 5: Prototype Production Sprint
**Focus:** Physical output of the first assembly.
*   **Goal:** Production of the **Main Wing Spar & Troughs**.
*   **Process:** Run the "4-Step Protocol" (Definition -> Physics -> Implementation -> Audit).
*   **Output:** A ZIP artifact containing: `wing.gcode`, `incidence_jig.stl`, `compliance_summary.pdf`.

---

## The "Complete Session" Protocol (Operationalizing the Work)

To complete the work, every coding session follows this rhythm:

1.  **[OPS] LOAD:** Identify the specific Component from the Roadmap.
2.  **[ARCH] CODE:** Write/Refine the CadQuery logic.
3.  **[AERO] TEST:** Run the VSP physics check.
4.  **[MFG] COMPILE:** Generate G-Code artifacts.
5.  **[OPS] SAVE:** Commit to Git and update the `ComplianceTracker`.
