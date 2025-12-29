# **Genesis Prompt Engineering for the Modernized Long-EZ: A Comprehensive Framework for Parametric Design, Regulatory Compliance, and Automated Manufacturing**

## **1\. Introduction: The Digital Renaissance of the Long-EZ**

The Rutan Long-EZ, designated as Model 61, stands as a singular achievement in the history of general aviation. Introduced in 1979 by Burt Rutan, the aircraft fundamentally disrupted the homebuilt market by offering efficiency, range, and safety margins—specifically stall resistance—that were previously unattainable in amateur-built aircraft.1 Its moldless composite construction method, utilizing hot-wired foam cores encapsulated in fiberglass, democratized the fabrication of complex aerodynamic shapes, allowing builders to construct airframes in garages without the need for expensive industrial tooling. However, the ecosystem supporting the Long-EZ has fragmented significantly in the decades following the closure of the Rutan Aircraft Factory (RAF). The release of the design into the public domain, while legally liberating, created a vacuum of technical authority.

Today, the aspiring Long-EZ builder confronts a chaotic landscape. The "Open-EZ" project, an attempt to crowd-source and preserve the plans, exists in a state of disarray across various repositories, most notably cobelu/Long-EZ and its forks.3 These repositories contain a heterogeneous mix of scanned PDFs, markdown text, and unverified CAD files, often suffering from dimensional inconsistencies, scaling artifacts, and a lack of semantic data structure.3 Furthermore, the original designs, based on 1970s technology, do not account for modern advancements such as high-torque electric propulsion, digital avionics, or computer-numerical-control (CNC) manufacturing methods.6

This report articulates a rigorous systems engineering strategy to resolve these challenges. The objective is to define a "Genesis Prompt"—a foundational instruction set for a sophisticated coding model (Large Language Model or LLM)—to architect a **Parametric Design Environment (PDE)**. This environment will not merely digitize the legacy plans; it will fundamentally re-engineer the aircraft as a software repository. By treating the aircraft's physical definition as executable Python code, we can leverage modern libraries such as CadQuery for geometry generation 8 and OpenVSP for aerodynamic validation.9 This "Plans-as-Code" paradigm enables the automated generation of manufacturing artifacts (G-code, STL jigs) and ensures dynamic compliance with FAA Title 14 CFR Part 21 regulations.10 The ultimate goal is to facilitate the incremental improvement of the platform, transforming the Long-EZ from a static historical artifact into a living, evolving open-source aerospace project.

## ---

**2\. Repository Forensics and the State of "Open-EZ"**

### **2.1 The Architecture of cobelu/Long-EZ**

A deep forensic analysis of the cobelu/Long-EZ GitHub repository reveals both the potential and the limitations of the current open-source preservation efforts. The repository acts as a central hub for the "Open-EZ" initiative, a community-driven effort to digitize the Long-EZ plans.3 The structure of the repository, however, reflects a documentation project rather than an engineering project. The primary content consists of Markdown files transcribing the original "Section I: Manufacturing Manual" and "Section II: Engine Installation".3 While this makes the text searchable and version-controllable, the critical geometric data—the "Section I Appendix" containing the A1 through A14 full-scale drawings—remains trapped in raster formats.12

The reliance on raster images (scans) for engineering definition is a critical failure point. Builders attempting to print these PDFs often encounter scaling errors due to printer calibration or PDF conversion artifacts.5 A discrepancy of even 1% in the printing of a bulkhead template can result in a geometric mismatch of nearly 0.25 inches across the fuselage width, leading to structural alignment issues during the "boxing" phase of construction.13 Furthermore, the repository lacks a cohesive geometric kernel; there is no "master model" that drives the dimensions. If a dimensional conflict exists—such as the known conflict regarding the F22 bulkhead position relative to the fuselage strakes 13—there is no algorithmic source of truth to resolve it. The conflicting data points simply coexist in different files, leaving the builder to arbitrate based on forum folklore rather than engineering determinism.

### **2.2 Forks and Fragmentation**

The analysis of forks, such as aidan-mueller/Long-EZ, indicates a lack of divergent development.4 Most forks appear to be passive copies rather than active branches contributing new engineering data. This stagnation suggests that the barrier to entry for contributing technical improvements is too high. In a traditional open-source software project, a contributor can submit a "pull request" with a few lines of code to fix a bug. In the current Long-EZ ecosystem, "fixing a bug" requires redrawing a CAD file, converting it to PDF, and uploading a binary blob, which is opaque to version control diff tools.3

The "Open-EZ" initiative also suffers from a lack of integration with the "Canard Pusher" newsletters (CPs). These newsletters, published by Rutan after the initial release of the plans, contain mandatory updates, safety directives, and aerodynamic modifications.15 While some repositories attempt to index these CPs 12, they are rarely integrated into the plans themselves. A builder must cross-reference the original manufacturing manual with dozens of newsletters to ensure airworthiness. The proposed Genesis Prompt must instruct the design environment to ingest these updates as *constraints* in the code, ensuring that the generated plans are "post-CP" compliant by default.

### **2.3 The "Roncz" Data Gap**

One of the most significant data gaps identified in the research is the handling of the Roncz R1145MS canard airfoil. The original Long-EZ utilized the GU25-5(11)8 airfoil, which was later found to suffer from significant lift degradation when contaminated by rain or insects, leading to a dangerous pitch-down moment.16 The Roncz 1145MS was designed to mitigate this.17 However, the Open-EZ repositories often contain conflicting or low-fidelity representations of this airfoil. Builders frequently request "coordinates" or "templates" on forums, indicating that a canonical, high-fidelity definition is missing from the central repositories.19

The research indicates that the coordinates for the Roncz 1145MS are available in the UIUC Airfoil Database and other aerodynamic archives 21, but they are often in "Lednicer" or "Selig" text formats that require parsing. Furthermore, the "modified" Eppler 1230 airfoil used on the main wing involves a reflex modification that is rarely quantified in public coordinates.20 The Genesis Prompt must address this by defining a robust "Airfoil Ingestion Module" that can parse these disparate data formats, apply spline smoothing to remove digitization noise, and mathematically apply the requisite geometric twists and reflexes defined in the Canard Pusher updates.23

## ---

**3\. Theoretical Framework: The Parametric Design Environment**

### **3.1 The Shift from Geometric Dimensioning to Algorithmic Definition**

The central thesis of this modernization effort is the transition from **Geometric Dimensioning and Tolerancing (GD\&T)** on static drawings to **Parametric Logic** in code. In a traditional workflow, a designer draws a line of length $L$. In a parametric workflow, the designer defines a function $f(x)$ that generates the line. This distinction is profound for the Long-EZ because the aircraft is organic; its fuselage is a lofted shape that changes continuously along the longitudinal axis (fuselage station).

Current "Open-EZ" plans provide cross-sections at specific stations (e.g., F-22, F-28). If a builder wishes to stretch the cockpit to accommodate a taller pilot—a common modification known as the "Long-EZ Extended Nose" 24—they must manually interpolate the new bulkhead shapes, a process prone to error. A parametric environment defined by the Genesis Prompt would treat the fuselage as a loft operation over a list of Bezier curves. The "stretch" becomes a single variable change (fuselage\_length \+= 4.0), and the software automatically recalculates every intermediate bulkhead, floor panel, and control linkage length.

### **3.2 The Role of Large Language Models in Engineering**

Large Language Models (LLMs) possess a unique capability relevant to this project: the ability to translate natural language specifications into structured code. However, LLMs struggle with direct spatial reasoning; they cannot "visualize" a 3D model effectively. They can, however, write excellent Python code that *describes* a 3D model.

This insight drives the selection of the software stack. We require a geometric kernel that is **script-centric** rather than **GUI-centric**. Tools like SolidWorks or Fusion 360 rely on manual point-and-click operations, which are inaccessible to an LLM. OpenSCAD is script-based but lacks the advanced boundary representation (B-Rep) capabilities needed for complex aerodynamic surfaces.25 **CadQuery**, a Python library based on the OpenCASCADE kernel, emerges as the optimal solution.8 Its fluent API allows an LLM to construct geometry using semantic sentences (e.g., Workplane("XY").extrude(10)), bridging the gap between linguistic intent and geometric realization.

### **3.3 The Single Source of Truth (SSOT)**

The design environment must establish a "Single Source of Truth" (SSOT) to eliminate the data inconsistencies observed in the cobelu repo. This SSOT will take the form of a master configuration file, aircraft\_config.py.

* **Global Variables:** This file will define the primary independent variables: WINGSPAN, ROOT\_CHORD, AIRFOIL\_SELECTION, PILOT\_STATION, ENGINE\_MASS.  
* **Derived Variables:** All other dimensions must be dependent variables. For example, the CANARD\_ARM (distance from wing AC to canard AC) should not be a hard-coded number but a calculated value derived from the required static margin and the CG limits.  
* **Propagation:** The Genesis Prompt must instruct the coding model to structure the application such that a change in aircraft\_config.py triggers a cascade of updates through the CadQuery geometry scripts, the OpenVSP aerodynamic analysis, and the Markdown documentation generators.

## ---

**4\. Software Stack Selection and Justification**

### **4.1 Core Geometry Engine: CadQuery**

CadQuery is selected as the primary geometry engine due to its unique combination of Python integration and industrial-grade kernel power.8 Unlike mesh-based modelers (e.g., Blender), CadQuery uses B-Rep (Boundary Representation), which defines shapes via precise mathematical surfaces (NURBS). This is non-negotiable for aerospace applications where the surface continuity of a wing directly impacts drag and lift.

* **Scriptability:** CadQuery scripts are pure Python. This allows the use of standard libraries like numpy for coordinate manipulation and scipy for airfoil spline interpolation.26  
* **Export Capabilities:** CadQuery natively supports export to STEP (for CAM), STL (for 3D printing), and DXF (for laser cutting).8 This covers the entire spectrum of manufacturing needs for a modern Long-EZ.  
* **Headless Execution:** The ability to run without a GUI allows the design environment to be integrated into CI/CD pipelines. We can run automated regression tests on the geometry every time a change is committed to the repository.27

### **4.2 Aerodynamic Validation: OpenVSP**

OpenVSP (Vehicle Sketch Pad), developed by NASA, provides the necessary aerodynamic feedback loop. While CadQuery handles the *physical* definition (how to build it), OpenVSP handles the *performance* definition (how it flies).9

* **API Integration:** OpenVSP includes a Python API, allowing the parametric parameters from aircraft\_config.py to be mapped directly to VSP geometries.9  
* **Analysis:** The Genesis Prompt will instruct the environment to run vspaero, a vortex lattice solver included with OpenVSP, to calculate lift slopes, drag polars, and stability derivatives.28 This ensures that modifications (e.g., changing the canard aspect ratio) do not push the aircraft into an unstable regime.

### **4.3 Documentation and Version Control: Git & Markdown**

The project will reside in a Git repository to solve the versioning issues of the past. Markdown is chosen for documentation because it renders natively on GitHub and can be auto-generated by Python scripts.3 The build manual will not be a static document but a "compiled" artifact, where dimensions and instructions are injected from the CAD data during the build process.

## ---

**5\. The Genesis Prompt Architecture**

The core deliverable of this research is the plan for the "Genesis Prompt." This prompt is a meta-instruction—a prompt to create the system that creates the aircraft. It must be structured to guide a powerful coding model (e.g., GPT-4o, Claude 3.5 Sonnet) through the creation of a complex software architecture.

### **5.1 Phase 1: Ontology and Initialization**

The first phase of the prompt must establish the directory structure and the "mental model" of the aircraft.

* **Prompt Instruction:** "You are the Chief Architect of the Open-EZ Parametric Project. Initialize a Python repository structure. Create a config/ directory for physical constants, a core/ directory for geometric classes, and an output/ directory for manufacturing artifacts. Define a base class AircraftComponent that enforces the implementation of generate\_geometry() and export\_dxf() methods."  
* **Reasoning:** This enforces object-oriented discipline. Every part of the aircraft (wing, bulkhead, landing gear) is an object that inherits standard behaviors, ensuring consistency in how parts are generated and exported.

### **5.2 Phase 2: The Airfoil Ingestion Engine**

Given the critical importance of the Roncz 1145MS and Eppler 1230 airfoils, the prompt must explicitly detail how to handle aerodynamic data.

* **Prompt Instruction:** "Implement an Airfoil class in core/aerodynamics.py. This class must verify and parse .dat files (Selig/Lednicer format). It must use scipy.interpolate.CubicSpline to smooth the coordinates and ensure a closed loop at the trailing edge. Implement a method get\_cadquery\_wire() that returns a CadQuery wire object scaled to a specified chord length."  
* **Data Integration:** The prompt should provide the specific URLs or file paths to the UIUC database for the Roncz 1145MS coordinates to ensure the model knows where to source the ground truth.21 It must also include logic to handle the "rain slot" or surface treatments if specified in the config.

### **5.3 Phase 3: The Lofting Logic (Wings and Canard)**

The wings of the Long-EZ are complex lofted shapes with sweep, dihedral, and washout (twist).

* **Prompt Instruction:** "Create a Wing class. The constructor should accept root\_airfoil, tip\_airfoil, span, sweep\_angle, dihedral\_angle, and washout. Use CadQuery's loft() operation to generate the solid core. **Crucially**, implement a boolean subtraction method cut\_spar\_trough() that calculates the trough depth based on the number of unidirectional fiberglass plies defined in config.materials. Reference the 'Cozy vs. Long-EZ' spar cap depth distinction to ensure the correct Long-EZ schedule is applied."  
* **Research Context:** This addresses the specific confusion between Cozy and Long-EZ spar caps found in the forums.19 The depth of the trough determines the structural thickness of the spar; an error here could lead to catastrophic wing failure.

### **5.4 Phase 4: The Fuselage Generator**

The fuselage requires a different approach: constructing a surface from a series of planar profiles.

* **Prompt Instruction:** "Develop a Fuselage class defined by a sequence of Bulkhead objects stationed along the longitudinal Z-axis. Use a spline loft to create the Outer Mold Line (OML). Implement a shell() operation to create the 0.5-inch PVC foam core thickness. Include a method to generate the F-22 bulkhead geometry specifically, ensuring the pilot seat width matches the 23-inch specification."  
* **Integration:** This solves the F-22 dimensional conflict 13 by making the bulkhead width a derivative of the PILOT\_WIDTH parameter. If the plans are ambiguous, the code enforces the ergonomic requirement.

### **5.5 Phase 5: Manufacturing Artifact Generation**

To efficiently homebuild the aircraft, the environment must output tooling data.

* **Prompt Instruction:** "Implement a GCodeGenerator module. This module should take a Wing object and slice it into segments (e.g., 4-foot sections for standard foam blocks). For each section, generate the XY (root) and UV (tip) coordinate paths for a 4-axis CNC hot-wire cutter. Output the data as standard G-code compatible with Mach3/GRBL controllers."  
* **Modernization:** This replaces the manual method of nailing physical templates to foam blocks 29, drastically reducing labor time and increasing profile fidelity.7

## ---

**6\. Aerodynamic Modernization: The Roncz Imperative**

### **6.1 The History of the Rain Canard**

The original Long-EZ utilized the GU25-5(11)8 airfoil on the canard. While efficient, this airfoil had a "cusped" leading edge and a pressure recovery distribution that was highly sensitive to surface contamination. In rain, the boundary layer would trip prematurely, causing a loss of lift. Since the canard provides the lifting force to balance the nose-down moment, a loss of lift results in an uncommanded pitch-down—a frightening characteristic for a pilot.16

John Roncz, a brilliant aerodynamicist, developed the R1145MS to solve this. It features a less aggressive pressure recovery and is tolerant of rain and bugs.18 The "Open-EZ" repositories often fail to emphasize that this is not an option; it is a **safety mandate**.

### **6.2 Parametric Implementation of the Roncz Airfoil**

The Genesis Prompt must ensure the Airfoil class defaults to the Roncz geometry.

* **Coordinate Smoothing:** Raw data from the UIUC database can contain "quantization noise" from the original digitization process. The prompt must instruct the model to apply a smoothing algorithm (e.g., Savitzky-Golay filter) to the coordinates before generating the CAD spline. This prevents "ripples" in the CNC-cut foam that would require excessive sanding.30  
* **Vortilons:** The Roncz canard often utilizes "vortilons" (vortex generators on the leading edge) to preserve aileron/elevator authority at high angles of attack. The design environment should include a module to generate 3D-printable vortilon templates that snap onto the canard leading edge for precise positioning.23

## ---

**7\. Manufacturing Modernization: The Smart Workshop**

### **7.1 CNC Hot-Wire Automation**

The traditional method of building a Long-EZ involves printing paper templates, gluing them to plywood, cutting the plywood, sanding it smooth, nailing it to a block of foam, and manually dragging a hot wire over the templates.29 This is labor-intensive and error-prone.  
The proposed design environment automates this via the GCodeGenerator module.

* **4-Axis Cutting:** A tapered wing requires the root and tip to be cut at different speeds. The G-code generator must calculate the feed rates such that the wire arrives at the trailing edge of the root and tip simultaneously.  
* **Kerf Compensation:** The hot wire melts a path wider than its diameter (kerf). The software must calculate the offset path based on the wire diameter and foam density (Styrofoam vs. Divinycell) defined in config.materials. This ensures the final core is dimensionally perfect.7

### **7.2 3D Printed Jigs and Fixtures**

The advent of consumer 3D printing allows for the creation of disposable tooling.

* **Wing Incidence Jigs:** Setting the wing incidence and sweep is a critical assembly step requiring complex measurements. The Genesis Prompt will instruct the generation of "Incidence Cradles." These are STL models that conform to the exact airfoil shape at a specific station (e.g., BL 50\) and have a flat bottom parallel to the longerons. The builder simply prints the cradle, sets it on the table, and rests the wing core in it, guaranteeing perfect alignment.31  
* **Drill Guides:** For the engine mount and landing gear extrusion, the system can generate drill guides that sleeve over the parts, ensuring holes are drilled perpendicular and on-center.

### **7.3 Laser-Cut Bulkheads**

The Fuselage module's DXF export capability allows builders to send the bulkhead files to online laser-cutting services. This eliminates the need to transfer patterns from paper to foam/wood by hand, increasing the accuracy of the fuselage box structure.33

## ---

**8\. Systems Engineering: Electric Propulsion and Avionics**

### **8.1 The Electric Long-EZ ("E-Z")**

The Long-EZ is an ideal candidate for electric conversion due to its low drag and efficient airframe.2 However, converting a design intended for a 250lb Lycoming O-235 requires structural re-engineering.

* **CG Management:** The electric motor is significantly lighter than the piston engine. To maintain the Center of Gravity (CG), batteries must be placed forward, or the motor mount extended aft. The Parametric Design Environment allows the builder to input the weight of their chosen motor (e.g., Emrax 268\) and batteries. The MassProperties module then iteratively adjusts the motor mount length or battery position to center the CG within the safe range (FS 97 to FS 103).1  
* **Battery Integration:** The strakes (wing roots) traditionally hold fuel. In an electric version, these volumes can house battery packs. The Genesis Prompt should request a StrakeBatteryMount class that generates a structural cassette for 18650 or 21700 cells, integrated with cooling channels that leverage the strake's leading-edge airflow.36  
* **Structural Loads:** The torque characteristics of electric motors (instant torque) differ from piston engines. The prompt must instruct the creation of a "High-Torque Firewall" reinforcement pattern, modifying the layup schedule of the F-28 bulkhead to handle the transient loads.6

### **8.2 Modern Avionics Integration**

The original instrument panel was designed for analog 3-1/8" gauges. Modern builders use EFIS screens (e.g., Garmin G3X, Dynon SkyView).

* **Panel Generator:** The Fuselage module should include a PanelLayout script. This script accepts a list of avionics components (dimensions defined in a library) and uses a bin-packing algorithm to suggest an optimal layout on the F-22 bulkhead. It then exports a DXF for water-jet cutting the panel.37  
* **Wiring Channels:** The original plans ran wires through conduit buried in the foam. The modern environment can model these conduits explicitly, ensuring they are large enough for CAN-bus and shielded ethernet cables required by modern avionics.

## ---

**9\. Regulatory Compliance Engine: Automating the 51% Rule**

### **9.1 The Regulatory Challenge of Automation**

A significant risk in modernizing homebuilding is running afoul of FAA Title 14 CFR Part 21.191(g), which mandates that the "major portion" of the aircraft be fabricated and assembled by the amateur builder.10 The FAA uses the "Amateur-Built Fabrication and Assembly Checklist" (Form 8000-38) to determine eligibility.10  
If the design environment generates G-code that allows a machine to do "all the work," the builder might be considered a manufacturer, not an amateur.

### **9.2 The "Fabrication Aid" Strategy**

To mitigate this, the Genesis Prompt must structure the output as **Fabrication Aids**, not finished parts.

* **Logic:** The FAA distinguishes between *fabricating* (making the part) and *processing* (using a tool). Cutting foam cores with a CNC hot wire is generally considered "fabrication" if the builder sets up and operates the machine.38 However, the *primary* structure of the Long-EZ is the fiberglass skin, not the foam core.  
* **Compliance Module:** The prompt must verify that the environment does *not* try to automate the layup process (which is impossible for a homebuilder anyway). Instead, it should generate detailed "Layup Schedules" (Markdown tables) that guide the builder through the manual process.  
* **Checklist Tracking:** The environment should include a ComplianceTracker class. As the builder selects options (e.g., "CNC Wing Cores"), the tracker updates a digital copy of Form 8000-38.  
  * *Task:* "Fabricate Wing Cores" \-\> *Method:* "Builder-operated CNC" \-\> *Credit:* "Builder".  
  * Task: "Assemble Fuselage" \-\> Method: "Jig-assisted bonding" \-\> Credit: "Builder".  
    This ensures that at the end of the project, the builder has a pre-calculated checklist to present to the DAR, proving that they meet the \>50% requirement.40

### **9.3 The Builder's Log**

The prompt should instruct the generation of a "Digital Traveler" or builder's log. This is a dynamic website or Markdown document that lists every step. It includes placeholders for the builder to upload photos of their progress, creating an immutable record of the construction provenance required for airworthiness certification.41

## ---

**10\. Implementation Roadmap and Conclusion**

### **10.1 Phase 1: Data Archaeology and Calibration**

The first step is to use the ezdxf library 34 to parse the legacy DXF files from the cobelu repository. These must be audited against the dimensions in the scanned PDF manuals. Where discrepancies exist (e.g., F-22 width), the logic defined in the Fuselage class (derived from pilot ergonomics) will override the legacy drawing. This phase establishes the "Golden Config" file.

### **10.2 Phase 2: The Geometry Kernel Build**

Using the Genesis Prompt, the developer will instantiate the CadQuery scripts. The primary focus will be on the "Wing Factory"—generating the lofted Roncz canard and Eppler wings. These scripts will be validated by exporting STLs and comparing them to 3D scans of existing, flying Long-EZs (if data is available) or by manual verification against physical templates.42

### **10.3 Phase 3: Community Release and "Forking"**

The repository will be released on GitHub. Builders can then "fork" the aircraft. A builder in Denver might fork the repo and adjust config.py for a high-altitude airport (longer wingspan, turbo-normalized engine mount). A builder in Europe might adjust it for the Rotax 915iS. The Git history will track these diverging evolutions, preventing the data loss that occurred with the original plans.3

### **10.4 Conclusion**

The proposed Parametric Design Environment represents a fundamental shift in how experimental aircraft are conceived and built. By moving from static plans to dynamic code, we solve the historical problems of data degradation, ambiguous modifications, and regulatory compliance. The "Genesis Prompt" is the key to unlocking this potential, leveraging the power of modern AI to act as a force multiplier for the homebuilder. This approach honors the innovative spirit of Burt Rutan while equipping the next generation of aviators with the tools of the 21st century. The Long-EZ, reborn in Python, becomes not just a plane, but a platform.

## ---

**11\. Appendix: The Genesis Prompt Specification**

Role: You are the Lead Systems Architect for the Open-EZ Modernization Project.  
Objective: Create a Python-based Parametric Design Environment (PDE) for the Rutan Long-EZ.  
Constraint: All geometry must be generated via CadQuery. All aerodynamics must be validated via OpenVSP.  
**Section 1: Data Structures**

1. Define a Configuration singleton in config.py. It must hold:  
   * geometric\_params: span, chord, sweep, airfoil\_types.  
   * material\_params: foam\_density, fiberglass\_ply\_thickness.  
   * compliance\_params: builder\_task\_credits.

Section 2: Geometry Generation  
2\. Implement AirfoilFactory:  
\* Load .dat files from data/airfoils/.  
\* Apply scipy.interpolate.CubicSpline for smoothing.  
\* Implement apply\_washout(angle) and apply\_reflex(percent).  
3\. Implement WingGenerator:  
\* Input: Airfoil objects, geometry params.  
\* Output: CadQuery solid for the foam core.  
\* Feature: Automatically generate the spar cap trough by subtracting a volume equal to ply\_count \* ply\_thickness.  
Section 3: Manufacturing  
4\. Implement GCodeWriter:  
\* Input: Wing surface geometry.  
\* Output: 4-axis G-code (.tap) for hot-wire cutters.  
\* Logic: Synchronize root and tip movement ratios.  
5\. Implement JigFactory:  
\* Generate IncidenceCradle STLs based on the lower surface of the wing at specified butt-lines.  
Section 4: Documentation & Compliance  
6\. Implement ManualGenerator:  
\* Parse config.py.  
\* Read template Markdown files from docs/templates/.  
\* Inject calculated dimensions (e.g., {{SPAR\_CAP\_WIDTH}}) into the text.  
\* Render final PDF manual.  
7\. Implement ComplianceReport:  
\* Tally builder credits based on selected manufacturing methods.  
\* Render a filled FAA Form 8000-38.  
**Final Instruction:** Code must be modular, heavily commented, and PEP8 compliant. Treat the aircraft as a software library.

#### **Works cited**

1. Rutan Long-EZ \- Pima Air & Space Museum, accessed December 28, 2025, [https://pimaair.org/museum-aircraft/rutan-long-ez/](https://pimaair.org/museum-aircraft/rutan-long-ez/)  
2. Rutan Long-EZ \- Wikipedia, accessed December 28, 2025, [https://en.wikipedia.org/wiki/Rutan\_Long-EZ](https://en.wikipedia.org/wiki/Rutan_Long-EZ)  
3. Rutan Long-EZ \- GitHub, accessed December 28, 2025, [https://github.com/cobelu/Long-EZ](https://github.com/cobelu/Long-EZ)  
4. aidan-mueller \- GitHub, accessed December 28, 2025, [https://github.com/aidan-mueller](https://github.com/aidan-mueller)  
5. Open EZ Rev 6 Plans and Dwgs \- The Canard Zone Forums, accessed December 28, 2025, [https://www.canardzone.com/forums/topic/35783-open-ez-rev-6-plans-and-dwgs/](https://www.canardzone.com/forums/topic/35783-open-ez-rev-6-plans-and-dwgs/)  
6. Rutans' Long EZ – Unusual Performance\! Review, History and Specs\! \- YouTube, accessed December 28, 2025, [https://www.youtube.com/watch?v=Om3bgYKjWzo](https://www.youtube.com/watch?v=Om3bgYKjWzo)  
7. CNC cut foam cores \- The Canard Zone Forums, accessed December 28, 2025, [https://www.canardzone.com/forums/topic/17132-cnc-cut-foam-cores/](https://www.canardzone.com/forums/topic/17132-cnc-cut-foam-cores/)  
8. CadQuery/cadquery: A python parametric CAD scripting framework based on OCCT, accessed December 28, 2025, [https://github.com/CadQuery/cadquery](https://github.com/CadQuery/cadquery)  
9. OpenVSP Python API Documentation — Project name not set documentation, accessed December 28, 2025, [https://openvsp.org/pyapi\_docs/latest/](https://openvsp.org/pyapi_docs/latest/)  
10. Amateur-Built Fabrication and Assembly Checklist Job Aid \- Federal Aviation Administration, accessed December 28, 2025, [https://www.faa.gov/sites/faa.gov/files/aircraft/gen\_av/ultralights/amateur\_built/Am\_Blt\_Chklist\_Job\_Aid.pdf](https://www.faa.gov/sites/faa.gov/files/aircraft/gen_av/ultralights/amateur_built/Am_Blt_Chklist_Job_Aid.pdf)  
11. CAD drawings for Long-EZ. (Link to ez.org) \- The Canard Zone Forums, accessed December 28, 2025, [https://www.canardzone.com/forums/topic/16688-cad-drawings-for-long-ez-link-to-ezorg/](https://www.canardzone.com/forums/topic/16688-cad-drawings-for-long-ez-link-to-ezorg/)  
12. The Long EZ Build, accessed December 28, 2025, [http://www.aryjglantz.com/2013/03/the-long-ez.html](http://www.aryjglantz.com/2013/03/the-long-ez.html)  
13. Nose gear modelling, and F22 position \- The Canard Zone Forums, accessed December 28, 2025, [https://www.canardzone.com/forums/topic/39927-nose-gear-modelling-and-f22-position/](https://www.canardzone.com/forums/topic/39927-nose-gear-modelling-and-f22-position/)  
14. Open-EZ CAD Drawings \- The Canard Zone Forums, accessed December 28, 2025, [https://www.canardzone.com/forums/topic/18014-open-ez-cad-drawings/](https://www.canardzone.com/forums/topic/18014-open-ez-cad-drawings/)  
15. Free public/domain/open source airplane plans ? : r/homebuilt \- Reddit, accessed December 28, 2025, [https://www.reddit.com/r/homebuilt/comments/1jnvhed/free\_publicdomainopen\_source\_airplane\_plans/](https://www.reddit.com/r/homebuilt/comments/1jnvhed/free_publicdomainopen_source_airplane_plans/)  
16. Upgrades \- Dreams of Flight, accessed December 28, 2025, [http://www.flightdreams.org/upgrades.html](http://www.flightdreams.org/upgrades.html)  
17. Airfoils \- Aerofiles, accessed December 28, 2025, [http://www.aerofiles.com/airfoils.html](http://www.aerofiles.com/airfoils.html)  
18. John Roncz \- Wikipedia, accessed December 28, 2025, [https://en.wikipedia.org/wiki/John\_Roncz](https://en.wikipedia.org/wiki/John_Roncz)  
19. roncz canard cad drawing \- Forums, accessed December 28, 2025, [https://www.canardzone.com/forums/topic/17366-roncz-canard-cad-drawing/](https://www.canardzone.com/forums/topic/17366-roncz-canard-cad-drawing/)  
20. Aerofoil co-ordinates \- canard-aviators@canardzone.groups.io, accessed December 28, 2025, [https://canardzone.groups.io/g/canard-aviators/topic/aerofoil\_co\_ordinates/54428038](https://canardzone.groups.io/g/canard-aviators/topic/aerofoil_co_ordinates/54428038)  
21. UIUC Airfoil Data Site \- UIUC Applied Aerodynamics Group, accessed December 28, 2025, [https://m-selig.ae.illinois.edu/ads/coord\_database.html](https://m-selig.ae.illinois.edu/ads/coord_database.html)  
22. Airfoil Updates \- UIUC Applied Aerodynamics Group, accessed December 28, 2025, [https://m-selig.ae.illinois.edu/ads\_history.html](https://m-selig.ae.illinois.edu/ads_history.html)  
23. airfoils.txt \- COZY Builders, accessed December 28, 2025, [http://cozybuilders.org/mail\_list/topics97/airfoils.txt](http://cozybuilders.org/mail_list/topics97/airfoils.txt)  
24. Chapter 22 – Nose & Nose Gear Wiring \- A Long EZ Push, accessed December 28, 2025, [https://www.longezpush.com/chapter-22-nose-nose-gear-wiring/](https://www.longezpush.com/chapter-22-nose-nose-gear-wiring/)  
25. Modeling a parametric RC airplane \- what software? : r/cad \- Reddit, accessed December 28, 2025, [https://www.reddit.com/r/cad/comments/qilqj4/modeling\_a\_parametric\_rc\_airplane\_what\_software/](https://www.reddit.com/r/cad/comments/qilqj4/modeling_a_parametric_rc_airplane_what_software/)  
26. A Script-Based CAD System for Aerodynamic Design \- AIAA, accessed December 28, 2025, [https://arc.aiaa.org/doi/pdfplus/10.2514/6.2019-3069](https://arc.aiaa.org/doi/pdfplus/10.2514/6.2019-3069)  
27. CadQuery Examples \- Pythonhosted.org, accessed December 28, 2025, [https://pythonhosted.org/cadquery/examples.html](https://pythonhosted.org/cadquery/examples.html)  
28. OpenVSP Tutorial: A Better Export for CAD \- YouTube, accessed December 28, 2025, [https://www.youtube.com/watch?v=PhTQYZ7x9SQ](https://www.youtube.com/watch?v=PhTQYZ7x9SQ)  
29. Ch. 3 \- Education \- Foam cutting \- What have I gotten myself into\!, accessed December 28, 2025, [https://longezproject.blogspot.com/2011/12/ch-3-foam-cutting-part-4.html](https://longezproject.blogspot.com/2011/12/ch-3-foam-cutting-part-4.html)  
30. CNC Foam for Long-EZ : r/homebuilt \- Reddit, accessed December 28, 2025, [https://www.reddit.com/r/homebuilt/comments/1jtjxk5/cnc\_foam\_for\_longez/](https://www.reddit.com/r/homebuilt/comments/1jtjxk5/cnc_foam_for_longez/)  
31. Model Airplane Building Jig : r/Scalemodel \- Reddit, accessed December 28, 2025, [https://www.reddit.com/r/Scalemodel/comments/1lqzzve/model\_airplane\_building\_jig/](https://www.reddit.com/r/Scalemodel/comments/1lqzzve/model_airplane_building_jig/)  
32. Rutan Long EZ by Croissant | Download free STL model \- Printables.com, accessed December 28, 2025, [https://www.printables.com/model/868221-rutan-long-ez](https://www.printables.com/model/868221-rutan-long-ez)  
33. georgeh1ll/Easy-DXF-Viewer: Python/Windows .dxf Viewer with Measurements \- GitHub, accessed December 28, 2025, [https://github.com/georgeh1ll/Easy-DXF-Viewer](https://github.com/georgeh1ll/Easy-DXF-Viewer)  
34. ezdxf \- PyPI, accessed December 28, 2025, [https://pypi.org/project/ezdxf/](https://pypi.org/project/ezdxf/)  
35. Long-ESA › Sustainable Skies, accessed December 28, 2025, [https://sustainableskies.org/tag/long-esa/](https://sustainableskies.org/tag/long-esa/)  
36. Build Log RichModel Long-EZ 60 Electric Conversion \- RC Groups, accessed December 28, 2025, [https://www.rcgroups.com/forums/showthread.php?1435355-RichModel-Long-EZ-60-Electric-Conversion](https://www.rcgroups.com/forums/showthread.php?1435355-RichModel-Long-EZ-60-Electric-Conversion)  
37. I want to buy a long eze. Any advice? \- AUS/NZ General Discussion \- Aircraft Pilots, accessed December 28, 2025, [https://www.aircraftpilots.com/forums/topic/27450-i-want-to-buy-a-long-eze-any-advice/](https://www.aircraftpilots.com/forums/topic/27450-i-want-to-buy-a-long-eze-any-advice/)  
38. FAA 51% Rule \- EAA, accessed December 28, 2025, [https://www.eaa.org/eaa/aircraft-building/builderresources/getting-started/selection-articles/faa-51-rule](https://www.eaa.org/eaa/aircraft-building/builderresources/getting-started/selection-articles/faa-51-rule)  
39. 51% rule \- Backcountry Pilot, accessed December 28, 2025, [https://backcountrypilot.org/forum/51-rule-16585](https://backcountrypilot.org/forum/51-rule-16585)  
40. Amateur-Built Fabrication and Assembly Checklist (2021) Fixed Wing, accessed December 28, 2025, [https://www.faa.gov/sites/faa.gov/files/aircraft/gen\_av/ultralights/amateur\_built/RANS\_S21\_Outbound\_Builder.pdf](https://www.faa.gov/sites/faa.gov/files/aircraft/gen_av/ultralights/amateur_built/RANS_S21_Outbound_Builder.pdf)  
41. Long-EZ Build Log – Patrik's projects, accessed December 28, 2025, [https://blog.familjenjonsson.org/blog/long-ez-build-log/](https://blog.familjenjonsson.org/blog/long-ez-build-log/)  
42. Special performance canard (Roncz) \- Template measurements, accessed December 28, 2025, [https://www.canardzone.com/forums/topic/17725-special-performance-canard-roncz-template-measurements/](https://www.canardzone.com/forums/topic/17725-special-performance-canard-roncz-template-measurements/)