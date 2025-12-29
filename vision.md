# Strategic Intent: The Open-EZ PDE

This section defines the paradigm shift from fragmented, legacy aircraft plans to a secure, parametric engineering environment. It outlines the foundational mission of the **Open-EZ Parametric Design Environment (PDE)** and introduces the "Plans-as-Code" methodology required to evolve the Long-EZ into a 21st-century aerospace platform.

---

# Modernizing the Legend

## The Open-Source Design Environment for the Long-EZ

The Rutan Long-EZ disrupted aviation in 1979 by offering efficiency, safety, and a revolutionary composite construction method that democratized aircraft fabrication. However, since the closure of the Rutan Aircraft Factory, the technical ecosystem has fragmented into unverified CAD files and raster-based PDFs prone to dangerous scaling errors.

The **Open-EZ PDE** is the world’s first "Plans-as-Code" repository designed to turn these static historical artifacts into a living, evolving, and aerodynamically validated software library.

---

### 1.0 The Case for Modernization: Why Now?

Aspiring builders currently confront a chaotic landscape of "forum folklore" and dimensional inconsistencies. We have identified three core liabilities in the legacy ecosystem:

* 
**The Raster Failure:** Reliance on scanned PDFs leads to structural alignment issues; a 1% scaling error can result in a 0.25-inch bulkhead mismatch.


* 
**The "Roncz" Data Gap:** Critical safety updates, specifically the Roncz R1145MS canard airfoil designed to prevent lift degradation in rain, are often missing or low-fidelity in existing repositories.


* 
**The Technical Vacuum:** Original 1970s designs do not account for modern CNC manufacturing, electric propulsion, or digital avionics.



---

### 2.0 The Three Pillars of the PDE

#### I. Geometric Determinism (The Vault)

We replace static drawings with **Parametric Logic**. By treating the aircraft’s physical definition as executable Python code, dimensions are no longer hard-coded numbers but derived variables. A single variable change (e.g., stretching the nose) triggers a cascade of updates through every bulkhead and control linkage.

#### II. Aerodynamic Validation (The Intelligence Layer)

Every modification is subjected to a digital feedback loop. While our geometry engine defines how to build the craft, integrated solvers like **OpenVSP** calculate performance metrics, ensuring that structural changes do not push the aircraft into unstable regimes.

#### III. Manufacturing Velocity (The Smart Workshop)

We automate the generation of manufacturing artifacts. The system outputs G-code for 4-axis CNC hot-wire foam cutting and STL files for 3-D printed incidence jigs, replacing labor-intensive manual templates with high-fidelity digital tooling.

---

### 3.0 The Experience: A Global Standard

| For the Builder | For the Developer | For the Pilot |
| --- | --- | --- |
| <br>**Precision:** Automated G-code eliminates manual template errors.

 | <br>**Extensibility:** Contributors can submit "Pull Requests" to improve airframe logic.

 | <br>**Safety:** The Roncz R1145MS "Rain Canard" is a safety-mandated default.

 |
| <br>**Simplicity:** Build manuals are "compiled" artifacts with dimensions injected from live CAD data.

 | <br>**Validation:** Continuous Integration (CI) runs regression tests on geometry.

 | <br>**Modernity:** Native support for EFIS screen layouts and high-torque electric firewalls.

 |

---

### 4.0 The Software Stack: "Plans-as-Code"

To achieve a "Single Source of Truth," we utilize a script-centric stack that bridges linguistic intent with geometric realization:

* 
**Core Geometry:** **CadQuery** (Python-based B-Rep kernel) for precise mathematical surfaces.


* 
**Aero Validation:** **OpenVSP** (NASA-developed) for vortex lattice stability analysis.


* 
**Infrastructure:** **Git** for version control and **Markdown** for dynamic, auto-generated documentation.



---

### 5.0 Regulatory Compliance: The 51% Engine

Modernizing homebuilding requires strict adherence to **FAA Title 14 CFR Part 21.191(g)**. The PDE includes a **ComplianceTracker** that ensures automation acts as a "Fabrication Aid" rather than a commercial manufacturing process. It tallies builder credits for tasks like "Builder-operated CNC," providing a pre-calculated checklist to prove amateur-built status to regulatory authorities.

---

### 6.0 The Future: Electric Propulsion & Beyond

The Long-EZ is an ideal candidate for electric conversion ("E-Z") due to its low-drag airframe. The PDE allows for structural re-engineering by:

* 
**CG Management:** Iteratively adjusting motor mount length or battery positions to maintain safe Center of Gravity limits.


* 
**Battery Integration:** Generating structural cassettes within the wing strakes, integrated with cooling channels.



---

**We solve the data problem to secure the skies.**

The Long-EZ, reborn in Python, becomes not just a plane, but a platform for the next century of innovation.