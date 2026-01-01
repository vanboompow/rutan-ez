# Open-EZ Parametric Design Environment (PDE) ✈️💻

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
* **Language:** Python 3.10+
* **Geometry Engine:** [CadQuery](https://github.com/CadQuery/cadquery) (OpenCASCADE B-Rep kernel)
* **Aerodynamics:** [OpenVSP](https://openvsp.org/)
* **Numerical Analysis:** NumPy, SciPy
* **Compliance:** Automated FAA Form 8000-38 (51% Rule) tracking

## Getting Started
1. **Clone the Repo:** `git clone https://github.com/your-org/open-ez-pde.git`
2. **Install Dependencies:** `pip install -r requirements.txt`
3. **Configure Your Build:** Edit `config/aircraft_config.py` to set your pilot height, engine choice, and structural preferences.
4. **Generate Artifacts:** Run `python main.py --generate-all` to produce STEP, DXF, and G-code outputs.
5. **Provenance & CI:** All artifacts in `output/` now emit a `*.metadata.json` file capturing git revision, configuration hash, and contributor. CI can call `python scripts/run_ci_checks.py` to ensure both configuration validity and artifact provenance before accepting generated files.

## Regulatory Notice
This project is intended for educational purposes and as a **Fabrication Aid** for amateur builders. Users are responsible for ensuring their specific build complies with local aviation authority regulations (e.g., FAA 14 CFR Part 21.191(g)).

---
*Inspired by the innovative spirit of Burt Rutan.* 