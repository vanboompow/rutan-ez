# Forge Knowledge Export: aviation

_Domain: aviation | Pages matched by keyword_

---

## 3D printed aircraft tooling jigs and molds

# 3D Printed Aircraft Tooling, Jigs, and Molds

## Overview

3D printing has transformed the production of tooling, jigs, and fixtures for aircraft manufacturing. What once required weeks of CNC machining from solid metal blocks can now be produced in days through additive manufacturing, with cost savings starting at 50% and weight reductions up to 80% [b728e305]. The technology spans from desktop FDM printers producing alignment jigs to large-format additive manufacturing (LFAM) systems creating meter-scale molds for fuselage components.

## Large-Format Additive Manufacturing for Aerospace Tooling

### Caracol Heron AM System

Caracol's Heron AM platform produces aircraft tooling including trim and drill tools, cold lamination tools, jigs, fixtures, and master molds for composite fabrication. Their system processes composite materials with thermoplastic matrices including PP, ABS, PC, and PEI [b728e305].

Key production results for a fuselage trimming and drilling tool:
- Material: ABS + Glass Fiber
- Size: 1650mm x 1000mm x 400mm
- Tolerances: 0.2mm after CNC post-processing
- Weight reduction: up to 80%
- Lead time: reduced from 12 weeks to 5-6 weeks
- Cost savings: starting from 50% [b728e305]

### Thermwood LSAM

Thermwood's LSAM systems use a "near net shape" approach -- printing slightly oversized parts at high speed, then trimming to final dimensions on the same machine. The systems process high-temperature thermoplastic composites suitable for molds and tooling, producing solid, virtually void-free structures that can sustain vacuum in an autoclave [93092128]. Available build volumes extend up to 40 feet in length [93092128].

### Legacy Industries

Legacy Industries operates both Thermwood LSAM systems (240" x 120" x 60" envelope) and Stratasys F900 FDM printers (36" x 24" x 36" envelope). Their LSAM can extrude materials with melt temperatures up to 850F, including ABS, Polycarbonate, ULTEM, and Dahltram 350 [5f8f1c29].

## Desktop and Mid-Scale 3D Printed Jigs and Fixtures

### Benefits Over Traditional Manufacturing

3D printed jigs and fixtures offer several advantages over conventionally machined tooling:

- **Cost reduction**: 70-90% savings compared to outsourced machined fixtures [6681052b]
- **Speed**: Print in hours versus days or weeks for traditional fabrication [d2dc9592]
- **Design freedom**: Complex geometries, integrated cooling channels, and ergonomic handles that would be impossible to machine [536421c7]
- **On-demand production**: Print only when needed, eliminating warehousing costs [6681052b]
- **Lighter weight**: Thermoplastic jigs are significantly lighter than metal alternatives [d2dc9592]

### Materials for 3D Printed Tooling

Common materials for aerospace jigs and fixtures include:

| Material | Key Property | Application |
|----------|-------------|-------------|
| Nylon 12CF | High stiffness, heat resistant | Structural fixtures |
| Polycarbonate | Heat resistant >120C | Mid-temperature tooling |
| ABS-ESD7 | Static dissipative | Electronics assembly |
| ASA | UV resistant | Outdoor fixtures |
| ULTEM (PEI) | Outstanding thermal/mechanical | Autoclave-compatible tooling |

[6681052b] [d2dc9592]

## Airbus Wire-DED Titanium Printing

Airbus has begun serial integration of wire-Directed Energy Deposition (w-DED) 3D printed titanium parts into A350 production. This technique uses a robotic arm with titanium wire, melting it layer-by-layer to create near-net-shape structural parts up to 7 meters long. The process dramatically reduces the "buy-to-fly" ratio -- traditional forging wastes 80-95% of raw titanium, while w-DED prevents most waste at source [f6a5e0de].

## CNC Machined vs. 3D Printed Jigs

Traditional CNC-machined jigs remain superior for high-precision, high-volume applications requiring tight tolerances and thermal stability under extreme conditions. Nickel-based superalloys are still preferred for aerospace jigs subjected to high temperatures and pressures [9656bab4]. However, 3D printing excels for prototyping, low-volume production, and applications where rapid iteration and design freedom outweigh the need for maximum durability [536421c7].

## Industry Certifications

Aerospace 3D printing increasingly requires formal quality certifications. A3D Manufacturing received AS9100 certification from the IAQG, ensuring all procedures and components meet the most rigorous safety and quality standards for aviation, defense, and space applications [37e3fa07]. Caracol has also qualified its production process with AS/EN 9100 certification [b728e305].

## Future Outlook

The trend is toward hybrid manufacturing workflows that combine additive and subtractive processes. Parts are 3D printed near-net-shape and then CNC-machined to final tolerances, capturing the speed and material efficiency of additive manufacturing while achieving the precision of traditional machining [b728e305] [93092128]. As materials science advances and build volumes increase, 3D printed tooling will continue displacing traditional methods across the aerospace supply chain.

---

## 3D printed wing rib templates alignment jigs

# 3D Printed Wing Rib Templates and Alignment Jigs

## Overview

3D printing has become a practical tool for creating wing ribs, alignment jigs, and assembly fixtures for model aircraft construction. The technology enables precise airfoil reproduction, rapid iteration on structural designs, and consistent production of identical parts -- capabilities that are particularly valuable for homebuilt and RC aircraft where traditional balsa-and-plywood construction meets modern CAD-driven manufacturing.

## 3D Printed Wing Ribs

### Design Approaches

Wing rib design for 3D printing follows two main approaches: ribs as structural components printed directly, and ribs as templates or jigs that guide traditional construction.

**Direct-printed ribs** are used as the actual structural elements in the wing. One RC builder designed 3mm-thick ribs with an 8-inch chord using Onshape (free online CAD), incorporating slots for 1/4" balsa leading and trailing edges and a commonly available wooden yardstick as the main spar. The design proved "very nicely scalable" and performed well in flight [819909c7].

**Multi-material printed ribs** represent the cutting edge of the approach. Using advanced filaments like LW-PLA (lightweight PLA), LW-ASA, and PAHT-CF (carbon fiber reinforced) on dual-material printers like the Bambu Lab H2D, builders can optimize aerodynamic structure, minimize weight, and maximize mechanical resilience in a single print [ca47c056] [b253ebc3].

### Continuous Perimeter Printing (Vase Mode)

Tom Stanton developed a technique for printing wing sections as one continuously extruded line using vase mode. The process involves:

1. Importing an airfoil profile from the Airfoil Tools website into Fusion 360
2. Creating internal ribs in a diagonal grid pattern with lightening holes along the wing length
3. Adding a central cylinder for a carbon fiber wing spar
4. Splitting the ribs into four quadrants that combine with the outer shell
5. Printing the entire structure as a continuous external perimeter [eabd19a0]

This method is particularly effective with lightweight PLA, which can ooze badly during normal printing but performs well when extruded continuously. The technique took about three weeks of experimentation to develop and works primarily for straight wings with a continuous profile [eabd19a0].

## Alignment Jigs for Wing Construction

### Purpose and Function

In model building, jigs hold and align structures during construction. A jig moves (guiding the tool or workpiece), while a fixture stays stationary [5f71994f]. For wing building, jigs ensure that ribs are correctly positioned, aligned, and spaced during assembly.

The key benefit of jigs is consistency -- each item produced using a jig will be identical. Many model builders invest time in making molds and jigs specifically because they want all components to be identical, even when hand-carving individual parts would be faster [5f71994f].

### 3D Printed Jigs and Fixtures for Manufacturing

3D printing has transformed jig and fixture production across manufacturing:

- **Cost**: 70-90% savings compared to outsourced machined fixtures [46b88e97]
- **Speed**: Direct CAD-to-print workflow with typical lead time reduction from weeks to hours [ce512a03]
- **Iteration**: Faster delivery enables more design iterations, improving performance [ce512a03]
- **Complexity**: Internal lattice structures, integrated clamping mechanisms, and ergonomic features that would be impossible to machine [46b88e97]

### Design Best Practices

When designing 3D printed jigs and fixtures:

- **Print orientation**: Align layers with the primary load direction to maximize strength [ce512a03]
- **Chamfers and fillets**: Add to all sharp edges to reduce stress concentrations [ce512a03]
- **Integrated clamping**: Build clamps, screws, and slots directly into the design to minimize additional hardware [ce512a03]
- **Material selection**: Nylon 12CF for high stiffness, PC for heat resistance, ABS-ESD7 for static-dissipative applications [46b88e97]

## Wing Rib Alignment Considerations

### Swept Wing Rib Orientation

For swept wings, rib alignment is a significant design decision. Mark Drela recommended that the desired airfoil be perpendicular to the leading edge, based on the principle that airflow is mostly perpendicular to the LE over the critical leading edge portion of the airfoil [fc5beb8f].

However, this is debated in the RC community. Some builders note that at low sweep angles, flow direction is not far from the free stream direction. Most early swept-wing fighter aircraft had ribs perpendicular to the LE, but they operated at large sweep angles around 45 degrees [fc5beb8f]. The practical compromise for most builders is to align ribs with the flight direction at low sweep angles and perpendicular to the LE at high sweep angles.

### Airfoil Profile Tools

The Profili software suite provided airfoil management tools for model builders for over 20 years, supporting CNC milling, hot wire foam cutting, and 3D printing. It has been superseded by devFoil at devcad.com, which handles wings, fuselages, and generic parts [ec5d1de5].

## Production Tooling for Wing Building

For builders producing multiple identical fixtures, proper tooling setup is critical. One prolific model builder described his production workflow requiring nine separate sawing operations, three drill press setups, and multiple sanding operations per fixture. After building dedicated jigs for his table saw, he could cut an entire set of fixtures in the time it previously took to cut two or three by hand [5f71994f].

The lesson translates directly to 3D printing: investing time in designing proper jigs and fixtures -- even jigs for making jigs -- pays dividends when producing multiple components. 3D printing eliminates most of the setup time that makes traditional jig-making expensive for small batches [46b88e97].

---

## Aa 5B Tiger Common Squawks Airworthiness Directives

# AA-5B Tiger Common Squawks Airworthiness Directives

The AA-5B Tiger is a model of aircraft manufactured by Tiger Aircraft LLC (formerly American General Aircraft Corporation and Grumman American Aviation Corporation). Several airworthiness directives (ADs) have been issued for this model, particularly concerning structural integrity and maintenance requirements.

## Airworthiness Directives Overview

In a proposed rulemaking issued on May 19, 2005, the Federal Aviation Administration (FAA) proposed to revise Airworthiness Directive (AD) 95-19-15, which applies to all Tiger Aircraft LLC Models AA-5, AA-5A, AA-5B, and AG-5B airplanes. This AD was initially issued to address issues related to the wing attach shoulder bolts and spar clearance.

According to the notice, AD 95-19-15 required inspection of the wing attach shoulder bolts for fretting, scoring, wear, or enlarged mounting holes and replacement of any damaged parts. Additionally, it required repair of any damaged areas and inspection of the wing spar at the center spar clearance gap for excessive clearance, with shimming of the spar if necessary [source id="8f8a4181"].

## Applicability and Modifications

The proposed AD aimed to update the applicability of AD 95-19-15 by limiting the serial numbers for Model AG-5B airplanes. This modification was made in response to new service information received by the FAA, which indicated that not all AG-5B aircraft were subject to the same structural concerns as previously identified.

The purpose of this revised AD was to prevent wing attach shoulder bolt failure, which could lead to structural damage of the wing/fuselage and potentially result in failure [source id="8f8a4181"].

## Comments and Public Participation

The FAA invited public comments on the proposed AD, with a deadline of July 18, 2005. Comments could be submitted through various channels including the DOT Docket website, regulations.gov, mail, fax, or hand delivery to the Docket Management Facility in Washington, DC.

The FAA also encouraged submission of written relevant data, views, or arguments regarding the proposal. Comments were to include the docket number "FAA–2005–20968; Directorate Identifier 94–CE–15–AD" at the beginning of each submission [source id="8f8a4181"].

## Contact Information

For further information regarding this proposed AD, individuals were directed to contact Richard Beckwith, Aerospace Engineer, at 1600 Stewart Avenue, Suite 410, Westbury, NY 11590. Contact details included a telephone number (516–794–5531) and facsimile number (516–794–5531) [source id="8f8a4181"].

To obtain the service information identified in this proposed AD, individuals were instructed to contact American General Aircraft Corporation at P.O. Box 5737, Greenville, MS 38704 [source id="8f8a4181"].

<!-- FORGE:PLACEHOLDER source_id="29bfc95c" -->
<!-- FORGE:PLACEHOLDER source_id="8f8a4181" -->

---

## CNC hot wire foam cutting aircraft wings

# CNC Hot Wire Foam Cutting for Aircraft Wings

## Overview

CNC hot wire foam cutting is a computer-controlled manufacturing process that uses an electrically heated wire to precisely shape foam materials into aerodynamic wing cores and other aircraft components. The technique is widely used in RC model aviation, UAV development, and experimental homebuilt aircraft construction, offering repeatable accuracy and smooth surface finishes that are difficult to achieve with manual methods [3aa21ae4][7a01fc03].

## How It Works

A CNC hot wire foam cutter uses a thin nichrome wire stretched between two movable towers. When electric current passes through the wire, it heats up and melts a narrow path (called the kerf) through the foam rather than physically cutting it [7ce87b8d]. The system requires four independent axes -- two horizontal and two vertical -- to create tapered and swept wing shapes where the root and tip airfoil profiles differ [3aa21ae4]. The wire traces one airfoil template on each side simultaneously, interpolating the shape between them.

The cutting speed must be carefully controlled: too fast and the wire drags, distorting the profile; too slow and excessive foam melts away, widening the kerf [7a01fc03]. A well-configured machine produces a smooth cut surface requiring minimal post-processing [3aa21ae4].

## Compatible Foam Types

Three primary foam types are used for wing cutting [ea5415fb][4309b88b]:

- **EPS (Expanded Polystyrene)**: The most common and least expensive option. Lightweight (15-30 kg/m3), cuts quickly, but has a beaded granular structure that can produce slightly rougher surfaces [bf383d33].
- **XPS (Extruded Polystyrene)**: Denser, smoother closed-cell structure. Produces very clean cuts but requires slower wire speed. Available in colored boards (blue, pink, green) at hardware stores [4309b88b].
- **EPP (Expanded Polypropylene)**: Flexible and impact-resistant -- ideal for RC combat and trainer aircraft. Cuts slowly but produces nearly indestructible foam cores [ea5415fb].

Foam quality matters significantly. Fresh foam from manufacturers can contain moisture that cools the cutting wire and causes ridges. Foam should be stored in a warm, dry location for several weeks before cutting to allow moisture to evaporate and internal stresses to relax [4b524099].

## Machine Construction

Building a CNC hot wire cutter is mechanically straightforward. The essential components include [3aa21ae4][1f2d8805]:

- **Frame**: Plywood, aluminum extrusion, or steel tubing
- **Linear motion**: Smooth rods with lead screws, or drawer slides
- **Stepper motors**: One per axis (four total)
- **Controller**: Arduino Mega 2560 with RAMPS 1.4 shield, or dedicated CNC controller
- **Power supply**: For both stepper motors and the hot wire
- **Nichrome wire**: Typically 26-30 gauge for smaller builds

The machine only needs enough rigidity to withstand the tension of the stretched wire -- cutting forces are minimal [3aa21ae4]. Total build cost for a DIY system runs approximately $200-280 USD using open-source hardware and software [a332961d].

## Software Toolchain

The software workflow consists of three stages [3aa21ae4][ec5d1de5]:

1. **Airfoil selection**: Coordinates obtained from databases like the UIUC Airfoil Coordinates Database
2. **G-code generation**: Software such as Wing G-code, Jedicut, DevWing Foam, or FoamXL converts airfoil profiles and wing planform geometry into 4-axis G-code [194c02a0][d941527e]
3. **Machine control**: GRBL-based firmware on Arduino, or Mach3/LinuxCNC on a PC, interprets the G-code and drives the stepper motors

Profili and DevFoam are popular commercial options that handle both airfoil design and G-code generation, supporting features like spar slots, lightening holes, and sheeting allowances [ec5d1de5][194c02a0].

## Calibration and Quality

Accurate cuts require careful calibration [1f2d8805]:

- **Steps per millimeter**: Each axis must move precisely the commanded distance, verified against a steel rule
- **Wire temperature**: Controlled via current regulation. A microprocessor-based power supply adjusts current dynamically during tapered cuts where wire length changes [d72c23f2]
- **Kerf compensation**: The width of foam melted by the wire (typically 0.5-1.5mm) must be accounted for in the G-code to achieve the correct final dimensions [1f2d8805]

Templates made from 1.5mm plywood, formica, or aluminum sheet are used to verify cut accuracy against the intended airfoil profile [4b524099].

## Commercial Machines

For those who prefer to purchase rather than build, commercial options range from hobby-grade to industrial [7373517c][d72c23f2][ea5415fb]:

- **RCFoamCutter**: Laser-cut, powder-coated 4-axis machines starting under $1,000 [ea5415fb]
- **CNC Multitool CUT1610S**: German-made machines with variable wire length up to 1,250mm and sophisticated current control [d72c23f2]
- **Foamlinx**: Full-range machines from small sign cutters to large industrial systems, starting at $3,500 with lifetime support [7373517c]

## Post-Cutting Processing

Foam cores are typically finished by [cad117ab][38bc63c8]:

- Sheeting with balsa wood or obechi veneer for structural reinforcement
- Laminating with fiberglass cloth using epoxy resin
- Vacuum bagging the assembly to achieve optimal fiber-to-resin ratio and bond quality
- Covering with heat-shrink film for lightweight RC applications

The combination of CNC-cut foam cores with fiberglass or carbon fiber skins through vacuum bagging produces wings with excellent strength-to-weight ratios and aerodynamic accuracy [cad117ab][38bc63c8].

## Applications

CNC hot wire foam cutting serves diverse applications across aviation and beyond [7a01fc03][f1326167]:

- **RC model aircraft**: Wing cores, fuselages, and tail surfaces
- **UAV/drone development**: Rapid iteration of airframe prototypes
- **Experimental homebuilt aircraft**: Full-scale wing mold blanks and structural cores
- **Architectural models**: Building facades and site contours
- **Lost-foam casting**: Patterns for metal casting
- **Signs and displays**: Dimensional letters and logos

---

## EAA homebuilt aircraft inspection checklist

# EAA Homebuilt Aircraft Inspection Checklist

## Overview

All Experimental/Amateur-Built (E-AB) aircraft require a yearly condition inspection performed in accordance with the scope and detail of 14 CFR Part 43, Appendix D [ae0eaac1][e011659a]. This inspection is the E-AB equivalent of the annual inspection required for certificated aircraft, though the standard is different: rather than demonstrating compliance with a type certificate, an E-AB aircraft must be found to be "in a condition for safe operation" [ae0eaac1]. The Experimental Aircraft Association (EAA) provides extensive resources, technical counselors, and flight advisors to support builders through both the construction and inspection processes [104d74f7].

## Who Can Perform the Inspection

Two categories of individuals are authorized to perform and sign off an E-AB condition inspection [ae0eaac1][e011659a]:

1. **Repairman Certificate holder**: The builder of the aircraft who applied for and received an FAA Repairman Certificate. This certificate is specific to one aircraft -- if you build multiple aircraft, you need a separate certificate for each [e011659a].
2. **Licensed A&P mechanic**: Any certificated Airframe and Powerplant mechanic. Unlike certificated aircraft annuals, an Inspection Authorization (IA) is not required for E-AB condition inspections [ae0eaac1].

Anyone can perform maintenance and repair work on an E-AB aircraft throughout the year -- the Repairman Certificate or A&P is only required to sign off the condition inspection itself [e011659a].

## Pre-Inspection Preparation

Before starting the inspection [ae0eaac1][76dc7670]:

- **Clean the aircraft** inside and out, including the engine compartment. If it is not clean, you cannot properly assess its condition [ae0eaac1].
- **Verify paperwork**: Airworthiness certificate displayed in the aircraft, registration on board, operating limitations present, weight and balance current, and all items matching the data plate [ae0eaac1].
- **Remove panels and access covers**: All exterior panels should be open or removed. Remove the cowling, wheel pants (if installed), and spinner. Remove enough interior to expose the entire control system for inspection [e011659a].
- **Use a checklist**: Multiple examples are available online and from kit manufacturers. Van's Aircraft, for instance, provides some of the most detailed checklists in the industry [76dc7670].

## Inspection Scope (FAR Part 43, Appendix D)

The FAA regulation covers the inspection process systematically [ae0eaac1]:

### Fuselage and Hull
- Inspect fabric, skin, and composite surfaces for deterioration, distortion, cracking, delamination, or insecure attachment of fittings [ae0eaac1]
- Check systems and components for improper installation, apparent defects, and unsatisfactory operation
- Examine doors, static ports, fuel drains, antennas, fairings, and control cables [ae0eaac1]

### Wings and Center Section
- Inspect all surfaces, internal structure, and mechanisms for damage, wear, and proper operation
- Check control surfaces for freedom of movement, proper rigging, and security of attachment
- Examine fuel tanks, lines, and fittings for leaks and security

### Empennage
- Inspect horizontal and vertical stabilizers, elevators, and rudder
- Check attach points, hinges, and control linkages
- Verify trim systems operate correctly

### Landing Gear
- Inspect gear legs, wheels, brakes, and tires
- Check for cracks, corrosion, and proper alignment
- Verify gear doors and fairings are secure

### Engine and Propeller
- Inspect engine mounts, baffles, and exhaust system
- Check all hoses, lines, and fittings for leaks and deterioration
- Examine propeller for nicks, cracks, and proper torque
- Verify all engine controls operate through full range

### Instruments and Avionics
- Verify instruments are functioning and properly marked
- Check vacuum or pressure systems
- Inspect wiring for chafing, proper routing, and secure connections

## Common Problem Areas

Experienced inspectors consistently identify recurring issues [e011659a][bb74f972][34d98618]:

- **Fuel system integrity**: Fuel system testing has become a critical focus for both EAA and FAA. Expect DARs and inspectors to insist on thorough fuel system checks [104d74f7]
- **Exhaust system cracks**: A leading cause of in-flight carbon monoxide exposure
- **Control cable wear**: Particularly at pulleys and fairleads
- **Electrical connections**: Corrosion and loose connections, especially at battery terminals and ground points
- **Hose deterioration**: Fuel and oil hoses degrade over time and with exposure to engine heat
- **Hardware security**: Missing cotter pins, safety wire, and improperly torqued fasteners

## The Logbook Entry

Upon completion, the inspector attests to the following [ae0eaac1]:

> "I certify that this aircraft has been inspected on [date] in accordance with the scope and detail of 14 CFR Part 43, Appendix D, and was found to be in a condition for safe operation."

The entry must include the aircraft's total time in service, and the name, signature, certificate number, and type of certificate held by the person performing the inspection [ae0eaac1].

## First Flight and Phase I Testing

Before first flight, builders must also address [104d74f7]:

- **Permanent registration**: Must be in hand (not just applied for) before the DAR appointment
- **Program letter**: Defining the Phase I flight test area and base airport
- **Weight and balance**: Documented empty weight and CG, forward and rear CG loading
- **Three-view photos**: Front, side, and top views of the completed aircraft
- **Builder's log with photos**: FAA inspectors appreciate thorough photographic documentation [58a9e0fd]

Key advisory circulars for first flight preparation [104d74f7]:
- **AC 43.13-1B**: Acceptable Methods, Techniques, and Practices for Aircraft Inspection, Repair & Alterations
- **AC 20-27G**: Certification and Operation of Amateur-Built Aircraft
- **AC 90-89B**: Amateur-Built Aircraft and Ultralight Flight Test Handbook
- **AC 90-116**: Additional Pilot Program for Phase I Flight Test

## Non-Builder Owners

Buyers of previously built E-AB aircraft face additional considerations [1035dd13][006dad9a]:

- A non-builder cannot obtain a Repairman Certificate for an aircraft they did not build -- an A&P must perform condition inspections [006dad9a]
- Research the build quality thoroughly before purchase, including reviewing the builder's log and maintenance records [1035dd13]
- EAA's *Non-Builder Owner's Guide to Amateur-Built Aircraft* provides detailed checklists specific to purchasing used homebuilts [1035dd13]

## EAA Resources

The EAA provides several support channels [104d74f7][006dad9a]:

- **Technical Counselors**: Experienced builders who provide in-person guidance during construction and inspection
- **Flight Advisors**: Pilots experienced in experimental aircraft who assist with first flight planning and flight testing
- **EAA SportAir Workshops**: Hands-on classes covering composites, sheet metal, welding, and other building skills
- **EAA Flight Test Manual**: Task-based approach to safely conducting Phase I flight testing [444a99a9]
- **Local EAA chapters**: Connect with builders and inspectors in your area

---

## Eppler 1230 modified wing airfoil

# Eppler 1230 Modified Wing Airfoil

## Overview

The Eppler 1230 (E1230) is a general aviation airfoil designed by Richard Eppler, widely known as the wing airfoil used on Burt Rutan's Long-EZ and Defiant canard aircraft [3c24fdb2]. It belongs to the Eppler family of airfoils -- a series of over 200 profiles designed using Eppler's conformal-mapping method for airfoil design combined with boundary-layer analysis [428cf738]. The E1230 is characterized by its relatively thick profile and significant camber, optimized for efficient cruise flight at moderate Reynolds numbers typical of general aviation.

## Geometric Properties

The E1230 has the following key geometric parameters [3c24fdb2][6ed77aed][b5f527bc]:

| Parameter | Value |
|-----------|-------|
| Maximum thickness | 17.4-17.5% chord at ~30% chord |
| Maximum camber | 3.6% at ~25-26% chord |
| Coordinate source | UIUC Airfoil Coordinates Database |

The airfoil features a relatively blunt leading edge with maximum thickness located at approximately 30% chord, providing good stall characteristics and structural depth for spar placement [3c24fdb2]. The forward location of maximum camber (around 25-26% chord) generates significant lift at moderate angles of attack [6ed77aed].

## Aerodynamic Performance

Xfoil predictions for the E1230 show performance across a range of Reynolds numbers [3c24fdb2]:

| Reynolds Number | Ncrit | Max Cl/Cd | At angle |
|----------------|-------|-----------|----------|
| 50,000 | 9 | 16.7 | 0.25 deg |
| 100,000 | 9 | 35.8 | 4.0 deg |
| 200,000 | 9 | 56.7 | 7.25 deg |
| 500,000 | 9 | 85.6 | 8.75 deg |
| 1,000,000 | 9 | 111.2 | 9.5 deg |
| 1,000,000 | 5 | 104.9 | 9.0 deg |

At higher Reynolds numbers typical of full-scale general aviation flight (Re > 500,000), the E1230 achieves excellent lift-to-drag ratios exceeding 85:1, making it well-suited for efficient cruise [3c24fdb2]. An academic study determined the E1230 to be optimal for electric-powered racing aircraft based on its lift and drag characteristics, with a maximum analytical lift coefficient of 1.8001, validated by ANSYS CFD at 1.84 [54933b2a].

## Eppler's Design Method

Richard Eppler developed a combined computational method integrating three components [428cf738]:

1. **Conformal-mapping inverse design**: Computes airfoil shapes from specified velocity distributions, similar to Lighthill's method but more direct for multi-point design problems
2. **Panel method analysis**: Distributed surface singularity method for analyzing potential flow around given airfoil shapes
3. **Integral boundary-layer method**: Uses momentum and energy equations to predict boundary-layer development, applicable across Reynolds numbers from 20,000 to 100 million

This approach allowed Eppler to design airfoils with prescribed boundary-layer characteristics -- particularly controlling the transition from laminar to turbulent flow -- by shaping the pressure distribution to maintain favorable pressure gradients over the forward portion of the airfoil [428cf738]. The E1230 reflects this philosophy with its aft pressure recovery designed to delay transition and reduce drag.

## Available Analysis Data

Comprehensive aerodynamic data for the E1230 is available from multiple sources [b5f527bc][6ed77aed]:

- **Basic polars**: Cl vs alpha, Cd vs alpha, Cm vs alpha, Cl/Cd vs alpha
- **Compressibility effects**: Performance variation with Mach number
- **Roughness effects**: Degradation of performance with surface contamination
- **Plain flap effects**: Cl,max vs flap deflection for 25%, 30%, 35%, and 40% flap chord ratios
- **Data source comparison**: Cross-referencing between JavaFoil+Calcfoil, XFOIL, and NeuralFoil predictions

Coordinate data is available in both Lednicer and Selig formats from the UIUC Airfoil Coordinates Database [3c24fdb2][22bdc676].

## Applications

### Long-EZ and Defiant
The E1230 was specifically selected for the main wing of Rutan's Long-EZ and Defiant designs [3c24fdb2]. These canard-configuration homebuilt aircraft required a main wing airfoil that could provide high lift at cruise, gentle stall characteristics, and adequate structural depth for the composite sandwich construction used in these aircraft.

### Electric Powered Racing Aircraft
Research on electric-powered racing airplane design identified the E1230 as the optimal airfoil based on combined lift and drag performance [54933b2a]. Electric propulsion benefits from the E1230's high Cl/Cd ratio because reduced drag directly extends range and endurance, which are critical limitations for battery-powered flight.

### General Aviation Applications
The E1230's 17.5% thickness provides structural depth for spar and fuel tank integration while maintaining good aerodynamic efficiency [b5f527bc]. The forward camber location produces a nose-down pitching moment that is manageable in conventional and canard configurations.

## Modern Analysis Tools

While Eppler's original PROFILE program remains historically important, current students and designers are recommended to use [428cf738]:

- **XFOIL**: Interactive program by Mark Drela and Harold Youngren for subsonic airfoil design and analysis -- the de facto standard for airfoil analysis today [428cf738]
- **NeuralFoil**: Physics-informed machine learning tool by Peter Sharpe for rapid aerodynamic prediction [b5f527bc]
- **Bigfoil.com**: Comprehensive online database with polars, flap effects, and comparison data across multiple analysis codes [b5f527bc]
- **Airfoil Tools**: Online resource with coordinate data, Xfoil-generated polars, and comparison utilities [3c24fdb2]

## Context in Airfoil Design History

The E1230 emerged from a period of rapid advancement in computational airfoil design [df0a4568]. Following the NACA laminar flow series of the 1930s-40s, designers like Eppler, Wortmann, and later Drela advanced the field by coupling potential flow solutions with boundary-layer theory to design airfoils with specific performance targets [df0a4568]. This approach -- designing for a desired boundary-layer development rather than simply testing shapes -- represented a fundamental shift in airfoil engineering that continues to underpin modern design practice [428cf738].

---

## Grumman AA-5B Tiger maintenance and ownership

# Grumman AA-5B Tiger Maintenance and Ownership

## Overview and History

The Grumman AA-5B Tiger is a four-seat, fixed-gear, single-engine aircraft first produced in late 1974 as a 1975 model. It was the outcome of a redesign of the AA-5 Traveler, featuring a Lycoming O-360-A4K engine producing 180 hp and a 139-knot cruise speed [08e0fd8f]. Gross weight was increased to 2,400 lb compared to the AA-5/AA-5A's 2,200 lb [08e0fd8f]. A total of 1,323 AA-5B Tigers were built before Gulfstream ceased production in 1979 [0d22e5ac]. American General later built roughly 150 AG-5B models in the early 1990s, and Tiger Aircraft in Virginia built approximately 50 more AG-5B models before closing in 2007 [0d22e5ac].

## Construction and Design

The Tiger uses revolutionary aluminum-honeycomb sandwich fuselage panels and rivetless bonded skins inherited from the AA-1 Yankee design [0d22e5ac]. The aircraft features a sliding canopy that can be left open in flight, a castering nosewheel steered by differential braking, and a fuel selector with Left, Right, and Off positions [7ea199c0]. The top cowling is hinged in the middle with fasteners on both sides, allowing easy engine access [d27005f1].

## Performance

Real-world Tigers consistently deliver 130 to 139 knots in cruise [7ea199c0] [b187fc7a]. At sea level and standard temperatures, the Tiger climbs at 850 FPM, roughly on par with competition [0d22e5ac]. With a climb prop, Tigers may see 1,000 FPM [7ea199c0]. Fuel burn is approximately 8.5-10.6 GPH, making it one of the more efficient four-seat aircraft [1faaa1f7] [d27005f1]. The 51-gallon fuel capacity provides about four hours of endurance with reserve [7ea199c0].

## Cost of Ownership

Used Tigers typically sell for $85,000 to $120,000 depending on condition and avionics [1faaa1f7]. Typical IFR-equipped aircraft run 1,450 to 1,500 pounds empty, leaving about 900 pounds of useful load [0d22e5ac].

Annual ownership costs for a cash purchase at 100 flight hours per year run approximately $16,300, or $163 per flight hour [1faaa1f7]. Fixed annual costs include hangar/tie-down ($720-$1,200), insurance ($1,500-$2,000), and annual inspection ($800-$1,200) [1faaa1f7]. The fixed-gear design provides a significant insurance advantage, saving approximately $1,500-$2,500 per year compared to retractable-gear aircraft [1faaa1f7].

## Engine

The Lycoming O-360-A4K is a 180 hp engine with a carburetor (Marvel Schebler 10-5219), REM38E spark plugs, and 12V electrical system [cc92aa45]. TBO is 2,000 hours or 12 years, whichever comes first [b14c8c00]. Lycoming offers new, rebuilt, and overhauled engines through their Exchange Program [cc92aa45].

## Key Maintenance Considerations

### Bondline Inspections

The bonded aluminum construction requires specialized inspection techniques. The FAA has proposed airworthiness directives requiring inspection of stabilizers, wings, and fuselage for bondline corrosion and delamination every 12 months [6e87c6cc]. The AD affecting AA-5A and AA-5B models would require inspection for "bondline separation, corrosion, and previous repair" [6e87c6cc]. Inspectors unfamiliar with proper Grumman bondline inspection techniques are a concern [bfc544ca].

### Wing Attach Shoulder Bolts

AD 95-19-15 R1 requires inspection of wing attach shoulder bolts for fretting, scoring, wear, or enlarged/elongated mounting holes, as well as inspection of the wing spar at the center spar clearance gap [de4defca]. Four reports of wing attach shoulder bolt failure prompted this AD.

### Horizontal Stabilizer

The AD 2021-14-12 applies only to AA-1, AA-1A, AA-1B, AA-1C, and AA-5 aircraft -- it does not apply to AA-5A, AA-5B, or AG-5B models which utilize a different design for the horizontal stabilizer [b200b0f8]. However, SAIB CE-04-34 recommends detailed visual inspections of the horizontal stabilizer forward spar attachment structure for AA-5A and AA-5B models at every annual/100-hour inspection [86b41ffa].

### Pre-Purchase Advice

Experts recommend buying the best plane you can afford rather than seeking a bargain project [f93ef5ce]. A thorough pre-buy should include a full annual inspection by the checklist in the factory maintenance manual -- 13 pages for the AA-5x series [f93ef5ce]. Annual inspections take approximately 16-20 hours and are typically flat-rated around $2,000 [8dc1f604].

## Popular Modifications

- **Power Flow Tuned Exhaust System**: Adds 10-15 hp, improves climb by 100-150 FPM, reduces CHTs by 15-30 degrees, and reduces fuel burn by 0.5-1.5 GPH [86e24973]
- **MT Propeller 3-blade**: Improved climb performance, shorter takeoff distance, lower noise [dea47c5b]
- **Trio Pro Pilot Autopilot**: FAA STC-approved, plug-and-play install [6a7f0b97]
- **Garmin G3X Touch / GFC 500**: AML STC covering the Tiger for glass cockpit upgrade [0d22e5ac]
- **ElectroAir Electronic Ignition**: Improved starting, lower fuel burn, better high-altitude operation [f93ef5ce]
- **Griggs Auxiliary Fuel Tank**: Adds fuel capacity in the baggage compartment [1d723868]

## Fleet Support

Parts inventories and rights are currently held by FletchAir in Texas, where Dave Fletcher maintains fleet support and modification efforts [0d22e5ac]. True Flight Aerospace holds the type certificates and has received PMA authorization for manufacturing commonly needed parts [b200b0f8]. A comprehensive service bulletin index is maintained by the Grumman Parts Alliance [96d808d1].

---

## Grumman Tiger annual inspection checklist

# Grumman Tiger Annual Inspection Checklist

## Regulatory Basis

FAR 43.15(c)(1) requires that each person performing an annual or 100-hour inspection use a checklist that includes the scope and detail of items contained in Appendix D to Part 43 [527daf73]. The checklist may be of the person's own design, one provided by the manufacturer, or one obtained from another source [527daf73]. The AA-5 Series Maintenance Manual contains a comprehensive annual or 100-hour inspection procedure checklist specific to the Tiger [527daf73] [8698f87e].

## Pre-Inspection Requirements

Before beginning the inspection, the mechanic must remove or open all necessary inspection plates, access doors, fairings, and cowling, and thoroughly clean the aircraft and engine [b674cb06]. The inspection should check for conformity with FAA Specifications, Airworthiness Directives, and Tiger Aircraft Service Bulletins and Letters [527daf73]. Reference should be made to the applicable maintenance handbook, service bulletins, installation instructions, and vendor specifications for torque values, clearances, settings, tolerances, and other specification data [527daf73].

## Inspection Areas Per FAR 43 Appendix D

### Fuselage and Hull Group
- Fabric and skin for deterioration, distortion, evidence of failure, and defective or insecure attachment of fittings [b674cb06]
- Systems and components for improper installation, apparent defects, and unsatisfactory operation [b674cb06]

### Cabin and Cockpit Group
- General cleanliness and loose equipment that might foul controls [b674cb06]
- Seats and safety belts for poor condition and apparent defects [b674cb06]
- Windows and windshields for deterioration and breakage [b674cb06]
- Instruments for poor condition, mounting, marking, and improper operation [b674cb06]
- Flight and engine controls for improper installation and operation [b674cb06]
- Batteries for improper installation and charge [b674cb06]

### Engine and Nacelle Group
- Engine section for visual evidence of excessive oil, fuel, or hydraulic leaks [b674cb06]
- Studs and nuts for improper torquing and obvious defects [b674cb06]
- Internal engine for cylinder compression and metal particles on screens and sump drain plugs [b674cb06]
- Engine mount for cracks, looseness of mounting [b674cb06]
- Flexible vibration dampeners for poor condition and deterioration [b674cb06]
- Engine controls for defects, improper travel, and improper safetying [b674cb06]
- Lines, hoses, and clamps for leaks, improper condition, and looseness [b674cb06]
- Exhaust stacks for cracks, defects, and improper attachment [b674cb06]
- Cowling for cracks and defects [b674cb06]

### Landing Gear Group
- All units for poor condition and insecurity of attachment [b674cb06]
- Shock absorbing devices for improper oleo fluid level [b674cb06]
- Wheels for cracks, defects, and condition of bearings [b674cb06]
- Tires for wear and cuts [b674cb06]
- Brakes for improper adjustment [b674cb06]

### Wing and Center Section
- All components for poor general condition, skin deterioration, distortion, evidence of failure, and insecurity of attachment [b674cb06]

### Empennage Assembly
- All components for poor general condition, skin deterioration, distortion, evidence of failure, insecure attachment, and improper component operation [b674cb06]

### Propeller Group
- Propeller assembly for cracks, nicks, binds, and oil leakage [b674cb06]
- Bolts for improper torquing and lack of safetying [b674cb06]

## Tiger-Specific Inspection Items

### Bondline Inspection
The bonded aluminum construction of the AA-5 series requires specific attention to bondline integrity. The FAA has proposed ADs requiring inspection of stabilizers, wings, and fuselage for bondline separation, corrosion, and previous repair [340357b8]. Inspectors must be familiar with proper Grumman bondline inspection techniques as specified in the Maintenance Manual [340357b8].

### Horizontal Stabilizer Forward Spar
SAIB CE-04-34 and subsequent maintenance manual updates recommend detailed visual inspections of the horizontal stabilizer forward spar attachment structure and surrounding area at every annual/100-hour inspection, and after hard landings, tail strikes, or any other notable impact in the tail area [86b41ffa].

### Lycoming O-360-A4K Engine
The Tiger's engine is a four-cylinder horizontally opposed engine producing 180 hp at 2,700 RPM with an 8.5:1 compression ratio and Marvel Schebler carburetor [54cbb3bd] [1c304e8b]. Key engine specifications include 361 cubic inches displacement, 5.125-inch bore, and 4.375-inch stroke [1c304e8b].

## Practical Considerations

### Annual Inspection Scope and Cost
A basic annual inspection takes approximately 16-20 hours and typically costs around $2,000, including labor for oil change with oil and filter, cleaning and gapping spark plugs, and a 14-page checklist inspection [8dc1f604]. The first annual with a new mechanic is usually the most expensive [8dc1f604]. Some items like wheel bearing repacking, elevator trim servicing, and Power Flow exhaust lubrication are generally done biannually [8dc1f604].

### Finding the Right Mechanic
It is imperative that the facility conducting maintenance is well-versed in Grumman aircraft and its bonded structures [b200b0f8]. GOPA maintains a list of Grumman maintenance facilities recommended by members [2bd95894]. Grumman Proficiency Series videos by David Fletcher and John Sjaardema provide guidance on proper inspection and maintenance techniques [28de8149].

### Reference Resources
- AA-5 Series Maintenance Manual (last revised March 1, 2004 by Tiger Aircraft LLC) [8698f87e]
- AA-5 Series Parts Manual [3f0b3bc4]
- Grumman Standard Repair Manual [3f0b3bc4]
- GOPA Resources page with annual inspection guides for AA-5 series and AG-5B [2bd95894]

### Performance Modifications Affecting Inspection
If the aircraft has a Power Flow tuned exhaust system installed, the stainless steel exhaust system should be inspected and lubricated per the manufacturer's recommendations [86e24973]. Dynamic propeller balancing to within 0.2 IPS is recommended upon installation and every two to four years thereafter [4e5337a0].

---

## Grumman Tiger Avionics Upgrades Panel

# Grumman Tiger Avionics Upgrades Panel

The Grumman Tiger is a four-seat, single-engine aircraft introduced in 1975, featuring an 180-horsepower Lycoming O-360-A4K engine. The Tiger is known for its nimble handling, fast cruise speeds, and distinctive fighter-style sliding canopy. It has a history of being well-supported by owners and mechanics who understand its unique design, though it is not without its quirks in terms of aerodynamics and climb performance. The aircraft has undergone several design iterations, with the Tiger and Cheetah being essentially the same airframe with different engines.

## Avionics Upgrades

The avionics upgrades for the Grumman Tiger are part of a broader modernization effort, particularly highlighted in the context of the AOPA Sweepstakes aircraft. The original instrument panel of the Tiger has been well-maintained but remains largely as it was when the aircraft left the factory in 1978. Several avionics systems, including the Loran navigation system, are no longer operational.

### Modern Avionics Installation

In preparation for the AOPA Sweepstakes, the Tiger's instrument panel was to be replaced with a custom-designed glass cockpit featuring Garmin technology. This upgrade was intended to significantly modernize the aircraft's avionics suite, improving navigation, communication, and situational awareness for pilots. The installation of the new panel was performed at J.A. Air Center, Aurora Municipal Airport (ARR) in Aurora, Illinois, where craftsmen were responsible for the complete overhaul of the cockpit. This modernization effort was meant to bring the Tiger up to contemporary standards for both performance and safety [c9c8f676].

### Performance Enhancements

In addition to the avionics upgrade, other performance improvements were planned for the aircraft. These included the installation of an electric constant-speed composite propeller provided by MT-Propeller, which promised to increase the Tiger's efficiency and performance. This combination of an electric propeller with the Lycoming O-360 engine was expected to deliver benefits such as a shorter takeoff roll, higher climb rate, and faster cruise speed or improved fuel efficiency [c9c8f676].

### Interior and Exterior Redesign

The interior of the aircraft was also slated for a redesign, with plans to address the worn-out seats and outdated cabin features. Render777 in Park Ridge, New Jersey, was involved in conceptualizing a stylish and comfortable interior design for the aircraft. Additionally, the exterior paint scheme was to be updated with a new look that better suited the Tiger's aesthetic and performance profile [c9c8f676].

## Aircraft Specifications

The Grumman Tiger is a high-performance aircraft with a cruise speed of up to 139 knots. It is equipped with an 180-horsepower Lyoming O-360-A4K engine, which contributes to its superior speed compared to other aircraft in its class. The Tiger's handling is described as crisp and responsive, with a climb rate that is competitive with other aircraft in its category. The aircraft's gross weight is 2400 pounds, with a typical useful load of about 900 pounds for fuel and passengers.

## Historical Context

The Tiger was introduced in the mid-1970s as an evolution of the Grumman Traveler, which was based on the Jim Bede AA-1 Yankee. The Tiger's design incorporated improvements such as larger fuel tanks, a more efficient cowling, and a more powerful engine. The aircraft was produced by Grumman from 1975 to 1979, with later versions built by American General and Tiger Aircraft. The design was also adapted into the Cheetah, which retained the 150-horsepower engine [b187fc7a].

## Future of the Tiger

Despite its age, the Grumman Tiger remains a popular choice among pilots and collectors. The aircraft's performance characteristics and handling qualities continue to attract attention, and the availability of modern avionics upgrades makes it an appealing candidate for modernization [b187fc7a]]

---

## Grumman Tiger type club community resources

# Grumman Tiger Type Club and Community Resources

## GOPA: The Official Type Club

The Grumman Owners and Pilots Association (GOPA), formerly the American Yankee Association (AYA), is the official type club for all models of American, Grumman, Gulfstream, American General, and Tiger LLC light aircraft [a4647c05]. It is a non-profit organization originally incorporated in Massachusetts, now in California [a4647c05].

### History
The AYA was formed in June 1976 by a group of AA-1 Yankee owners headed by Ken Blackman and Dicey Miller. A total of 17 aircraft met at an EAA fly-in in Merced, California on June 3-5, 1976 [a4647c05]. The organization grew to a peak of over 2,000 members. In 1978, the by-laws were amended to include all models built by American Aviation, Grumman American, Gulfstream Aerospace, American General Aircraft, and Tiger LLC [a4647c05]. Membership had mushroomed to 1,500 by 1987 and stabilized at 2,000 through the 1990s [a4647c05].

### Mission
GOPA's mission is "Safety, First and Always." The organization promotes a culture of safety, training, and technical resources for all Grumman owners and pilots [1006ca92]. Research shows that type club members have a lower number of accidents than non-type club members flying the same type of aircraft [340357b8].

### Member Benefits
GOPA membership provides [caf94068] [0318ef6b]:
- Access to the Member Directory
- 45+ years of Grumman Star newsletters
- "Ask the Experts" forum for professional answers
- Maintenance files, documentation, and manuals
- List of GOPA-recommended Grumman maintenance facilities
- Pilot Proficiency Program manuals
- Video library covering maintenance and operations
- Free classified ads for aviation-related items
- Discounts from select Grumman vendors
- Group insurance policy covering hull and liability

### The International Grumman Star
The bimonthly news magazine (previously called The American Star) is a 24+ page publication covering the latest Grumman maintenance, operations, classifieds, and type club stories [340357b8].

### Events
GOPA sponsors regional, national, and international events including annual conventions (North America and Europe), regional fly-ins across 8 regions, and activities like flour bombing, spot landing, precision taxiing, and the unique Grumman Limbo [340357b8]. The GOPA 2026 Convention is planned for Baraboo/Wisconsin Dells, WI [dad763bb].

## Training Programs

### Pilot Familiarization Program (PFP)
GOPA's PFP provides access to experienced Grumman CFIs specifically vetted by GOPA. Programs train to proficiency rather than a set number of hours, covering the type's unique handling characteristics such as the castering nosewheel [340357b8] [a4647c05].

### Cockpit Cool
This program trains companion non-pilots to handle basic emergency situations with aircraft control, communication, navigation, and emergency landings [340357b8].

## Fleet Support Organizations

### True Flight Aerospace
True Flight Aerospace holds the type certificates for the Grumman line. They have received FAA Parts Manufacturing Authorization (PMA) and are increasing availability of commonly needed and specialty parts [b3325187]. They have thousands of NOS (new old stock) parts available, produce new parts including the Cheetah carburetor duct and 14V/28V fuel boost pumps, and are working on a fuel-injected Tiger with an IO-360 powerplant [b3325187]. Contact: 229-242-6337 or Info@TrueFlightAerospace.com [b3325187].

### FletchAir
Dave Fletcher at FletchAir in Texas maintains parts inventories and fleet support/modification efforts. FletchAir is widely respected in the Grumman community [0d22e5ac] [b187fc7a].

### Grumman Parts Alliance (GPA)
The GPA at gpa.grumman-parts.com provides Marvel Carburetor manuals, Cleveland Brake manuals, component maintenance manuals, product catalogs, and Sensenich propeller repair manuals [944c6f16]. They also maintain the Grumman Pilots YouTube channel with 443+ videos and 426 subscribers [f93ef5ce].

## Online Communities

### GrummanPilots.org
The GOPA website at grummanpilots.org hosts resources including pre-buy inspection tips, aging aircraft best practices, annual inspection guides for AA-1, AA-5, and GA-7 series, and model-specific information pages [2bd95894] [08e0fd8f].

### Grumman Proficiency Series
Available at grummanproficiency.com, this resource features videos by David Fletcher and John Sjaardema covering proper pre-buy and annual inspection procedures, canopy track maintenance, and more [28de8149].

### Parts Suppliers
- Safe Skies Parts (safeskiesparts.com) carries a variety of Grumman aircraft parts [7e0df74f]
- Fraction Air Parts (fractionairparts.com) offers used parts for AA-1, AA-5, Tiger, and Cheetah models with money-back guarantee [4c093ae2]

## The Aircraft: AA-5B Tiger at a Glance

The AA-5B Tiger was produced from late 1974 to 1979, with 1,323 built by Grumman American [08e0fd8f] [7df37339]. It features a Lycoming O-360-A4K 180 hp engine, 139-knot cruise speed, 2,400 lb gross weight, and the signature sliding canopy [08e0fd8f]. The Wikipedia article on the Grumman American AA-5 notes that a total of 3,282 aircraft across the AA-5/AG-5 series were manufactured between 1971 and 2006 [7df37339].

## MOSAIC Rule Impact

According to True Flight Aerospace, the FAA's MOSAIC final rule will make the entire family of Grumman single-engine aircraft eligible in the Light Sport category, potentially opening the door for more pilots to enjoy these aircraft and enabling practical modernization and improvements [b3325187].

---

## Long-EZ composite construction techniques

# Long-EZ Composite Construction Techniques

## Overview

The Rutan Long-EZ is a tandem two-seat homebuilt aircraft designed by Burt Rutan, first flown on June 12, 1979 [64cc136f]. It uses Rutan's moldless foam-core composite sandwich construction method -- a technique that revolutionized homebuilt aircraft and was later adopted in production and commercial aircraft [7eee2f2c]. The aircraft features a canard configuration, swept wing with wingtip rudders, and a pusher engine with a range of over 2,000 miles on 52 gallons of fuel [64cc136f].

## Moldless Composite Sandwich Construction

Rutan's innovation was adopting composite repair techniques not for repair but to build an entire aircraft without molds [7eee2f2c]. The method involves cutting or hot-wiring profiles from blocks of high-density poly foam, sanding to exact dimensions, and laying fiberglass and epoxy over the foam [abbb537e]. The result is a light, sleek airframe with efficient aerodynamics [abbb537e].

The construction manual, *Moldless Composite Sandwich Aircraft Construction*, is still used by Scaled Composites to train new employees [2c7f672b] [d0134177]. It presents practical techniques for working with composites (glass, resins, foam cores, and fillers) and includes a series of in-shop exercises to develop skills [2c7f672b].

## Materials

### Foam Cores
The Long-EZ uses several types of foam for different structural applications. Builders must follow specific guidelines for foam selection as different densities and types serve different structural purposes [af764be2]. Clark Foam was originally specified but alternatives like Glastafoam and InsulFoam IX 2 lb density foam have been used as replacements [4357cc58].

### Fiberglass Cloth
Two primary types of fiberglass cloth are used [af764be2]:
- **UNI (unidirectional)**: Fibers running primarily in one direction for maximum strength along the fiber axis
- **BID (bidirectional)**: Fibers woven at 45 degrees for shear strength and torsional rigidity

The weight and properties of fiberglass cloth affect layup ratios. Aircraft Spruce supplies 8.8 oz/yd^2 BID that weighs approximately 6.5 oz per standard panel piece, which may differ from the original plans assumptions [7740daa8].

### Epoxy Systems
Epoxy selection is critical for structural integrity. MGS epoxy and other systems have been extensively discussed in the builder community [4357cc58]. Key considerations include pot life, mixing ratios, and post-cure requirements [4357cc58]. Temperature control during cure is important -- some builders construct heat tents for better curing [4357cc58].

### Fillers
- **Microspheres**: Mixed with epoxy for lightweight filling and fairing
- **Flox (flocked cotton)**: Mixed with epoxy for structural bonding joints [af764be2]

## Hot-Wire Foam Cutting

Hot-wire cutting is the primary technique for shaping foam cores, especially wing cores. A fine nichrome wire (approximately 0.017 inch diameter) is heated by electrical current to cut through foam cleanly [bf4b138b] [2c9e92b2]. The wire follows templates (positive or negative) attached to each end of the foam block to produce the desired airfoil shape.

Key considerations:
- The cut quality depends entirely on template quality -- templates must be smooth and strong [bf4b138b]
- A 24-volt battery charger is commonly used as a power source [2c9e92b2]
- For tapered swept wings, the wire must travel at different speeds at each end to account for different chord lengths [2c9e92b2]
- Volkswagen pushrods can serve as flex supports for the wire [2c9e92b2]

## Layup Techniques

### Wet Layup Process
The standard Long-EZ construction technique is hand wet layup [7740daa8]:
1. Wet out the foam surface with epoxy
2. Lay fiberglass cloth over the wetted surface
3. Saturate the cloth with epoxy using brushes or squeegees
4. Remove air bubbles and excess resin

### Cloth-to-Resin Ratios
The ideal ratio is critical for structural integrity. The plans indicate that "if you've done an excellent job, the resin should weigh about half of the cloth," yielding approximately a 67:33 cloth-to-resin ratio [7740daa8]. Vacuum bagging can achieve down to 70:30 ratios [7740daa8]. Hand layup typically achieves 35-45% fiber weight fraction, while vacuum methods reach 55-65% [680357c7].

### Plastic Peel-Ply Technique
An advanced technique involves wetting out glass between two sheets of plastic, allowing aggressive squeegeeing without disturbing the fabric or introducing air [7740daa8]. This method achieves vacuum-bag-quality results (68:32 cloth-to-resin ratio) with hand layup simplicity. The resulting layup is notably more transparent, indicating fewer trapped air bubbles [7740daa8].

### Avoiding Resin-Starved Layups
Even light compression (less than 1/3 PSI) with paper towels over peel ply can create resin-starved layups that are structurally weak [4f4ef58f]. The key difference with vacuum bagging is controlled, uniform pressure distribution and careful resin content management [4f4ef58f].

## Construction Process

### Plans and Resources
The plans consist of a 26-chapter manufacturing manual with step-by-step instructions and 14 full-scale drawings (A1 through A14), plus engine installation manuals, an owner's manual, and landing brake drawings [2e1c1162]. Updates were published in *The Canard Pusher* newsletter, which contains vital mandatory design updates [2e1c1162].

Plans are no longer sold by RAF but electronic versions exist through the Open-EZ community, though some drawing scales may be skewed and should not be used as official templates without verification [2e1c1162].

### Critical Modifications
Two major optional modifications from the Canard Pushers [2e1c1162] [64cc136f]:
1. **Roncz canard**: Replaces the original GU airfoil to eliminate rain trim change. Identified by swept-up tips. Produces more lift, enabling less span and reduced drag [64cc136f]
2. **High-performance rudders**: Fill the full span of the winglet for increased directional control authority in crosswind operations [2e1c1162]

### Weight Management
Empty weight is a critical concern. An O-235 powered Long-EZ should ideally come in at 850 pounds without a starter [abbb537e]. Excessive weight cannot be fixed after construction -- it impacts performance and compromises the G-load safety margin [abbb537e]. Because Long-EZs were not assembled from factory-built kits, construction workmanship varies greatly, making experienced evaluation essential before purchase [abbb537e].

## Community Support

The Canard Owners and Builders Association (COBA) at canardowners.com maintains an extensive library of technical resources, including indexed articles, supplier lists, and epoxy guidance from experts like Gary Hunter [4357cc58]. The organization evolved from the Central States Association and serves as the primary support network for Long-EZ builders and owners [abbb537e].

The EAA (Experimental Aircraft Association) provides resources including a free online builder's log for members [4357cc58], and NC State University has a donated Long-EZ used to demonstrate pilot controls, control surfaces, and the canard configuration to aerospace engineering students [53245163].

---

## Lycoming O-235 engine installation maintenance

# Lycoming O-235 Engine Installation and Maintenance

## Engine Overview

The Lycoming O-235 is a family of four-cylinder, direct-drive, horizontally opposed, air-cooled piston aircraft engines with a displacement of 233 cubic inches (3.82 L), producing between 100 and 125 horsepower depending on the variant [07b2b389]. First certified by the FAA on February 11, 1942, under Type Certificate No. E-223, the engine features aluminum alloy cylinders, a chrome-nickel-molybdenum steel crankshaft, dual magneto ignition, and Marvel-Schebler carburetion [07b2b389].

### Key Specifications

| Specification | Value |
|---|---|
| Configuration | Horizontally opposed 4-cylinder |
| Displacement | 233.3 cubic inches (3.82 L) |
| Bore | 4.375 inches (111.1 mm) |
| Stroke | 3.875 inches (98.4 mm) |
| Compression Ratio | 6.75:1 to 9.7:1 |
| Power Output | 100-125 hp at 2,450-2,800 RPM |
| Dry Weight | ~244 lbs (111 kg) |
| Fuel Type | 100LL AvGas |
| Oil Capacity | 6 quarts |

[b728201f] [07b2b389]

## Notable Variants

- **O-235-C1**: 115 hp at 2,800 RPM, 246 lb dry weight, 6.75:1 compression ratio for 80-octane fuel [07b2b389]
- **O-235-F1**: 125 hp at 2,800 RPM, 9.7:1 compression for 100-octane fuel [07b2b389]
- **O-235-L2C**: 115 hp (or 125 hp per some sources), optimized for modern low-lead fuels with provisions for constant-speed propellers. Used in the Cessna 152 and Beech Skipper [07b2b389] [400df355] [50a8fa8b]
- **O-235-N2C**: Known for improved fuel efficiency, producing 118 hp [b728201f]

## Aircraft Applications

The O-235 powers a wide range of aircraft [07b2b389] [b728201f]:
- Piper PA-11 Cub and PA-18 Super Cub
- Cessna 150/152 series
- Grumman American AA-1
- Piper PA-28-140 Cherokee
- Rutan Long-EZ (primary powerplant per plans)
- Diamond DA20 Katana
- Various experimental and homebuilt aircraft

## Engine Installation

### Mount Types
The O-235 uses a dynafocal engine mount configuration. When installing on homebuilt aircraft like the Zenith series, AN7 bolts are required for mounting the engine to the dynafocal mount ring [1139e90f]. The O-235 and O-290 share the same length engine mount (approximately 12 inches from firewall to the back of the mount ring), but the O-320 mount is approximately 2 inches shorter [aaabba5f]. The O-290 required a conical engine mount, and not all O-235 variants share the same isolation dampener configuration [aaabba5f].

### Engine Mount Inspection
Common trouble-shooting items include cracked engine mounts causing rough engine operation [a5f0da53]. Engine mounts should be inspected for cracks, looseness of mounting, and looseness of engine to mount during every annual inspection.

## Maintenance

### Regular Maintenance Items
- **Oil changes**: Regular oil changes are crucial for engine health [b728201f]
- **Magneto checks**: Periodic checks and maintenance of the dual magneto ignition system [b728201f]
- **Spark plugs**: Cleaning and gapping at each annual inspection
- **Cylinder compression**: Checked during annual inspection; weak compression indicates improper internal condition [a5f0da53]

### Troubleshooting Guide

| Problem | Probable Cause | Remedy |
|---|---|---|
| Rough engine | Cracked engine mount | Replace mount [a5f0da53] |
| Rough engine | Unbalanced propeller | Check propeller balance [a5f0da53] |
| Low oil pressure | Insufficient oil | Fill sump to proper level [a5f0da53] |
| Low oil pressure | Dirty oil strainers | Remove and clean strainers [a5f0da53] |
| High oil temperature | Insufficient air cooling | Check inlet/outlet for obstruction [a5f0da53] |
| High oil temperature | Clogged oil lines | Remove and clean oil strainers [a5f0da53] |
| High oil temperature | Excessive blow-by | Usually worn/stuck rings; complete overhaul required [a5f0da53] |

### Time Between Overhaul (TBO)
The O-235 typically requires overhaul after 2,000 hours, with TBO extended to 2,400 hours for qualifying models using genuine Lycoming parts, particularly those with 6.75:1 compression or updated high-compression pistons [07b2b389]. Most piston engines have TBO recommendations ranging from 1,800 to 2,400 flight hours [0b0cfe77].

### Overhaul Considerations
During overhaul, technicians examine cylinders, pistons, valves, crankshaft, cam lobes, fuel pumps, magnetos, alternators, and spark plugs [0b0cfe77]. "Major overhaul" and "light overhaul" are marketing terms -- the FAA recognizes only overhaul or repair [c32b42ec]. An overhaul does not technically require replacement of anything; components found within overhaul limits can be reused [c32b42ec].

### Pricing

| Condition | Price Range |
|---|---|
| New engines | $25,000-$35,000 |
| Overhauled engines | $15,000-$25,000 |
| Used engines (running) | $8,000-$15,000 |
| Core engines (for rebuild) | $3,000-$8,000 |

[b728201f]

Penn Yan Aero, with over 80 years of experience, guarantees overhauled engines for three years or until OEM TBO expires, whichever comes first [3c2f00f2]. Their FAA-approved proprietary techniques are trusted enough that manufacturers collaborate with them on product improvements [3c2f00f2].

## Engine Improvements

### L-Series Upgrades
The L-series models incorporated wide-cylinder-flange designs with thicker base flanges, enhancing structural integrity and eliminating the need for separate hold-down plates [07b2b389]. Reinforced components including increased-strength pistons (part number LW-18729) were introduced for high-compression variants starting June 1986 [07b2b389]. Updated crankcases with twin pressurized main oil galleys optimize lubrication and reduce early failures [07b2b389].

### Comparison with Modern Alternatives
The Rotax 912 differs from the O-235 in that it has liquid-cooled heads (vs. fully air-cooled), uses a 2.43:1 reduction gearbox, and weighs significantly less [feec7f70]. The Rotax 912 is more fuel efficient and can run on automotive fuel, but the O-235 has a longer TBO (2,400 hours vs. 2,000 hours for the Rotax 912) and a more established maintenance infrastructure [feec7f70].

## Training Resources

Lycoming offers a 5-day, 40-hour Service School training program at Williamsport Regional Airport that includes 4 hours daily of theory and 4 hours of hands-on training working on O-360 engines [38814726]. The training hours qualify for IA renewal under FAR 65.93(a)(4) [38814726]. Cost is $1,740 per session.

## Parts and Support

Air Power Inc. is the largest global distributor of Lycoming aircraft engines, carrying factory-new, overhauled, and ready-to-ship engines and genuine parts [7bcebb52] [be964066]. Norvic in the UK is an EASA Part 145-authorized Lycoming specialist offering overhaul, shock load inspection, and exchange services [400df355] [50a8fa8b].

---

## OpenVSP aerodynamic analysis tutorial

# OpenVSP: Aerodynamic Analysis Tutorial

## What Is OpenVSP?

OpenVSP (Open Vehicle Sketch Pad) is an open-source parametric aircraft geometry tool originally developed by NASA [5b91f273]. It allows users to quickly create 3D models of aircraft defined by common engineering parameters, which can then be processed into formats suitable for engineering analysis [d0ca269e]. Written in C and C++, OpenVSP runs on Windows, macOS, and Linux and is released under the NASA Open Source Agreement (NOSA) [5b91f273].

The predecessors to OpenVSP, including VSP and Rapid Aircraft Modeler (RAM), were developed by J.R. Gloudemans and others for NASA beginning in the early 1990s [5b91f273]. OpenVSP v2.0 was released as open source in January 2012, with development led by Rob McDonald since then [5b91f273, d0ca269e].

## Getting Started: The User Interface

OpenVSP displays a graphical user interface built with FLTK upon launch [5b91f273]. Two windows open: a workspace where the 3D model is displayed and a Geometry Browser that lists individual components (fuselage, wings, etc.). Components can be selected, added, or deleted similarly to a feature tree in CAD software like SolidWorks [5b91f273].

OpenVSP also provides API capabilities accessible via Matlab, Python, or AngelScript for automated workflows [5b91f273].

## Geometry Modeling

OpenVSP offers a library of basic geometries common to aircraft design that users modify and assemble [5b91f273]:

- Wing, pod, fuselage, and propeller components
- Advanced components including body of revolution, duct, and conformal geometry
- Mesh import capabilities for STL, CART3D (.tri), and PLOT3D formats
- Point cloud import with parametric surface fitting

### Building a Model Step by Step

The NASA OpenVSP Ground School provides a structured modeling tutorial [690ec18e]:

1. **Add a background image** from reference sources (three-view drawings, POH dimensions) to guide model creation [690ec18e]
2. **Create the fuselage** using cross-section placement and skinning to match reference drawings [690ec18e]
3. **Shape the fuselage** by adding cross-sections at inflection points and using skinning [690ec18e]
4. **Create the wing** matching top-view planform, adjusting section parameters and using Smart Input fields [690ec18e]
5. **Create the vertical tail** ensuring intersection with the fuselage and proper symmetry [690ec18e]
6. **Place wings and set airfoils** adjusting Z-location, dihedral, and airfoil profiles using AF files or NACA parameters [690ec18e]
7. **Add nacelles** using Duct, Body of Revolution, Fuselage, or Stack components [690ec18e]

### Airfoil Modification

Wing cross-sections can be modified under the Modify tab with parameters for shift (Delta X/C, Delta Y/C), rotation (Theta/pitch), scale, and leading edge shift [89b3de67]. Trailing edge closure options allow creation of blunt trailing edges [89b3de67].

## Analysis Tools

OpenVSP includes multiple built-in analysis capabilities [5b91f273]:

### VSPAERO

VSPAERO is the primary aerodynamic analysis tool, developed by David Kinney at NASA Ames [fa751e7f]. It provides vortex lattice method (VLM) or panel method-based aerodynamic and flight dynamic analysis, designed from the ground up to leverage OpenVSP geometries and the DegenGeom thin-surface representation [fa751e7f].

Key VSPAERO capabilities include:

- **Case setup**: Flow conditions, reference values (area, span, chord) configured in the Overview tab [fa751e7f]
- **Advanced settings**: Propeller/rotor configurations, stall estimation, wake behavior, and stability analyses [fa751e7f]
- **Viewer**: Visualizes pressure contours, vorticity, trailing wake, and cut planes for volumetric flow properties [fa751e7f]
- **Results Manager**: Plots convergence histories, spanwise load distributions, drag polars (CDtot vs CL), and Cp distributions [fa751e7f]

Reference values (bref for rolling/yawing moments, cref for pitching moment) can be input manually or taken from any Wing component in the model [fa751e7f].

Note: OpenVSP v3.45 introduced major changes to the VSPAERO solver with version 7, and updated tutorials are being created [fa751e7f].

### Other Analysis Tools

- **CompGeom**: Mesh generation with model intersection and trimming [5b91f273]
- **Mass Properties Analysis**: Computes center of gravity and moment of inertia [5b91f273]
- **Projected Area Analysis**: Computes projected areas [5b91f273]
- **CFD Mesh**: Generates meshes for external CFD software [5b91f273]
- **FEA Mesh / FEA Structure**: Generates meshes and internal structures (ribs, spars) for finite element analysis [5b91f273]
- **Wave Drag Analysis**: Estimates wave drag for transonic/supersonic geometries [5b91f273]
- **Parasite Drag Analysis**: Estimates parasite drag based on wetted area and skin friction coefficient [5b91f273]
- **DegenGeom**: Generates simplified representations (point, beam, camber surface models) [5b91f273]

## Working with Meshes and Point Clouds

Meshes in OpenVSP can come from internal tools (CompGeom, CFDMesh) or external imports [6119fa6c]. Point clouds are created by converting a mesh wireframe to a set of points or importing from a PTS file [6119fa6c].

Applications include matching parametric components to existing geometry manually or using the Fit Model tool for greater accuracy, and assigning mass properties to watertight meshes [6119fa6c].

## Export and Compatibility

OpenVSP geometry can be exported as [5b91f273]:

- STL, CART3D (.tri), PLOT3D
- STEP and IGES (for CAD interoperability)
- OBJ, SVG, DXF, X3D

These formats enable use in external CFD (e.g., with Cart3D, SU2) or FEA software.

## OpenVSP in the Broader Ecosystem

OpenVSP sits within a rich ecosystem of open-source aeronautical engineering tools [66e839f3, 571c73f8]. Complementary tools include:

- **AVL** (GNU GPL): Vortex lattice code for aerodynamic analysis
- **Digital Datcom** (public domain): Stability and control estimation
- **Dakota** (GNU LGPL): Optimization and uncertainty quantification
- **XFOIL**: 2D airfoil analysis (commonly used alongside OpenVSP)
- **FLOWUnsteady**: Unsteady aerodynamics using vortex particle methods, which can leverage OpenVSP geometry [40912a61, e3676064]

## Learning Resources

- **OpenVSP Ground School**: NASA's online tutorial program with video demonstrations for users of all levels [89c2257a, d0ca269e]
- **OpenVSP Google Group**: Community discussion forum for modeling and analysis questions [d0ca269e]
- **API Documentation**: C++/AngelScript and Python API docs for automated use [d0ca269e]
- **OpenVSP Airshow**: Community model repository (successor to VSP Hangar, launched August 2024) [5b91f273]
- **Annual OpenVSP Workshop**: Offline event for developers and users (held annually since 2012) [5b91f273]

---

## Roncz R1145MS canard airfoil

# Roncz R1145MS Canard Airfoil

## Overview

The Roncz R1145MS is a custom airfoil designed by John Roncz specifically for the canard (forward wing) of the Rutan Long-EZ homebuilt aircraft. It was developed to solve the "rain trim change" problem experienced by Long-EZ pilots and was first announced in January 1985 in Canard Pusher newsletter #43 [7790743d, 64cc136f]. The airfoil replaced the original GU25-5(11)8 airfoil used on both the VariEze and Long-EZ canards, and has since become the standard canard airfoil for most Long-EZ builds and derivative aircraft [3e85e531, 7bd08a16].

## The Rain Trim Change Problem

The standard Long-EZ canard, using the GU25-5(11)8 airfoil, exhibited a nose-down trim change when flying into rain [7790743d]. This required pilots to apply aft force on the stick to maintain altitude, typically trimmed out using the bungee trim system. For most pilots, this was a minor annoyance. However, some builder/pilots reported more pronounced effects, with a few cases where there was not enough trim authority to fly hands-off in rain [7790743d].

Burt Rutan and John Roncz spent approximately two years investigating the phenomenon [7790743d]. The effort included:

- Building and testing five completely different canards with different airfoils
- Extensive flight testing with documented data
- Video camera documentation of tuft behavior on each airfoil
- Measurement of lift and hinge moments with and without rain
- Development of a method to simulate rain effects
- Computer modeling that could duplicate flight test results

## Design and Characteristics

Using computational tools validated against flight test data, John Roncz designed the R1145MS airfoil from scratch [7790743d]. Key characteristics:

- **Negligible rain trim change**: Rain adds only about 2 knots to stall speed, compared to the significant trim disruption of the GU airfoil [7790743d, 64cc136f]
- **Higher lift production**: Produces considerably more lift than the original GU25-5(11)8 airfoil -- more than any airfoil tested during the development program [7790743d]
- **Reduced span requirement**: The higher lift enables a shorter canard span (130 inches tip-to-tip vs 140 inches for the GU canard), reducing wetted area and thus drag [7790743d, 64cc136f]
- **Low drag**: The basic airfoil has very low drag characteristics [7790743d]
- **Correct stick forces**: The trailing edge shape provides proper stick forces without external devices [7790743d]
- **Speed improvement**: Max speed increased up to 3 knots compared to the GU canard [3e85e531]

## Airfoil Geometry

The R1145MS airfoil coordinates are publicly available [c5861553]. The airfoil exists in two forms: a single-element airfoil and a two-element airfoil (with flap). The flap file includes the pivot point [7546a285].

The single-element airfoil data file (R1145MS.dat) contains 177 coordinate points defining the upper and lower surfaces. The coordinates show a cambered airfoil profile optimized for the canard application, with the trailing edge designed to produce appropriate hinge moments for elevator control [c5861553].

A related Roncz design, the "Roncz Low Drag Flying Wing Airfoil" (Marske-7), shows maximum thickness of 12.1% at 42.8% chord and maximum camber of 2.8% at 39.1% chord -- though this is a different airfoil optimized for flying wing applications [86a3459f].

## Vortilons and Integration

An important implementation detail: the Roncz canard mandates the use of six vortilons on the main wing [3e85e531]. These small aerodynamic devices manage the vortex interaction between the canard wake and the main wing, ensuring proper stall characteristics. The Roncz-designed curled-up wing tips, first seen on Mike and Sally Melvill's N26MS, are specifically optimized to enhance the vortex coming off the tip of the canard and position it in the "sweet spot" over each main wing [7790743d].

## Construction

The canard is constructed using hot-wire cut Styrofoam cores covered with fiberglass [3e85e531, ee1cea6d]. The construction process involves:

1. **Core joining**: Two main foam cores are aligned and joined with micro to form a straight 9-foot piece, which forms the backbone of the 11-foot canard [3e85e531]
2. **Shear web**: The leading edge is cut off, the shear web is glassed on, then the leading edge is bonded back [ee1cea6d]
3. **Lift tabs**: Two lift tabs are installed near the center as main fuselage attach points [ee1cea6d]
4. **Spar caps**: Multiple layers of unidirectional fiberglass are laid into troughs in the cores, tapering toward the outboard edges [ee1cea6d]
5. **Skin layup**: Bottom skin is applied first, then the "fishtail" is removed and the top skin is contoured and applied [ee1cea6d]
6. **Elevator hinge points**: Dense foam inserts are placed where metal hinges will mount [ee1cea6d]

## Aircraft Applications

### Long-EZ
The R1145MS is the standard canard airfoil for the Long-EZ, recommended as a replacement for the original GU25-5(11)8 [64cc136f, 3e85e531]. Most Long-EZs built after 1985 use the Roncz canard.

### Cozy Mark IV
The Cozy Mark IV uses the RM1145S (a variant designation) for its canard [ee1cea6d]. As with the Long-EZ, the airfoil was adopted specifically because it does not exhibit pitch change in rain [ee1cea6d].

### Berkut 360
The Berkut 360, a heavily modified Long-EZ derivative with retractable landing gear and carbon fiber construction, has always used the Roncz 1145MS canard airfoil [7bd08a16]. The airfoil's tolerance of insect and rain contamination was cited as a key advantage over the original GU airfoil [7bd08a16].

### VariEze (Not Recommended)
Rutan explicitly stated that the R1145MS canard is NOT recommended for the VariEze [7790743d]. The VariEze's main wing airfoil works very hard to maintain attached flow even with the GU canard, and the new higher-lift canard may ruin the stall characteristics of a VariEze [7790743d].

## Historical Significance

The R1145MS represents a significant achievement in homebuilt aircraft airfoil design. John Roncz, described as an "airfoil designer par excellence" by Burt Rutan [7790743d], used computational aerodynamic tools to solve a real-world flight safety concern. The airfoil's coordinates were added to the UIUC Airfoil Coordinates Database in November 2024, contributed by David Lednicer [7546a285].

The R1145MS airfoil is a rare example of a purpose-built airfoil specifically designed to address contamination sensitivity (rain, insects) while simultaneously improving performance -- a design constraint not typically encountered in conventional aircraft airfoil design.

---

## Starlink Mini general aviation aircraft installation

# Starlink Mini: General Aviation Aircraft Installation

## Overview

The Starlink Mini has emerged as the first practical broadband internet solution sized for small general aviation (GA) aircraft [0b2e9049, 189a4d19]. Measuring roughly 11.5 by 10 inches and weighing about 2.5 pounds, it draws 20-40 watts of continuous power (60W peak at startup) and delivers download speeds between 50-100 Mbps [28f5adee, 8afa5991]. For GA pilots, this means real-time weather radar, continuous NOTAM updates, passenger entertainment, and reliable communication at altitude -- capabilities that previously cost tens of thousands of dollars [e8896fa5].

## Hardware Specifications

| Specification | Value |
|---|---|
| Dimensions | 11.75" x 10.2" x 1.45" (298.5mm x 259mm x 38.5mm) |
| Weight | 2.43 lbs (1.1 kg) |
| Power Input | 12-48V DC, 60W max |
| Peak Power Draw | 60W (startup) |
| Continuous Power Draw | 20-40W (average ~25W) |
| WiFi | Built-in WiFi 5 (802.11ac), dual-band |
| Download Speed | 50-100 Mbps typical |
| Latency | 25-60 ms |
| Field of View | 110 degrees |

Sources: [45f14a0f, 67c0908d, 8afa5991]

## Legality and FAA Compliance

According to Starlink's official guidance, "for smaller General Aviation aircraft or for aircraft that we do not have an STC for yet, Starlink Mini may be used as a Portable Electronic Device (PED), on the interior of an aircraft only" [f3b9bbc7]. It can be used in accordance with FAA Advisory Circular 91.21-1D "Use of Portable Electronic Devices Aboard Aircraft" [f3b9bbc7, e0df51e4].

Key compliance points:
- Starlink Mini has NOT been certified or approved by the FAA or other civil aviation authorities [f3b9bbc7]
- It is the aircraft operator's responsibility to determine safe antenna positioning that does not interfere with aircraft operation [f3b9bbc7]
- Pilots should contact their local FSDO to ensure operational requirements are met [f3b9bbc7]
- For experimental/homebuilt aircraft, the regulatory path is cleaner but documentation of non-interference with avionics is still required [28f5adee]

Avionics Networks offers a Pilot Aviation Kit (PAK) with DO-160G Section 21 EMI testing, vibration-dampening brackets, and safety restraint systems for more rigorous compliance [e0df51e4].

## Service Plans and Pricing (March 2026 Update)

In March 2026, Starlink introduced aviation-specific plans that replaced the previously affordable Roam plans for aircraft use [c9b01e79, 7c5d1d0f, 8afa5991]:

| Plan | Monthly Cost | Included Data | Speed Limit | Coverage |
|---|---|---|---|---|
| Aviation 300MPH | $250 | 20 GB | Up to 300 mph (482 km/h) | Land + 12nm coastal |
| Aviation 450MPH | $1,000 | 20 GB | Up to 450 mph (724 km/h) | Land + ocean |
| Roam/Priority (legacy) | $50-65 | 50-100 GB | <100 mph only | Restricted |

Sources: [c9b01e79, 8afa5991, 7c5d1d0f]

The pricing change was controversial. Over 9,000 pilots signed a Change.org petition, and AOPA sent a letter to Elon Musk calling the previous service "a transformational advancement for aviation" and a "meaningful enhancement to operational safety" [7c5d1d0f]. The rate increases "create a pricing structure that will place the service beyond the reach of a significant portion of the global general aviation community" [7c5d1d0f].

Identity verification (passport, tail number, aircraft type) is now required for aviation plans [c9b01e79].

## Power Solutions

The 60W startup draw is the critical design constraint. Most standard cigarette lighter jacks in GA aircraft are fused for only 36-45 watts, insufficient for Starlink's peak requirements [8afa5991].

### Option 1: Dedicated Aviation USB-C Outlet (28V Aircraft)

The True Blue Power TA360 Max Power USB Charger is the gold standard -- a TSO'd, aviation-certified USB-C outlet delivering 100W [8afa5991]. Requires professional A&P installation. Critical limitation: requires 22-32 VDC input, so it will NOT work in 14V aircraft (most older C172s, Pipers) [8afa5991].

### Option 2: Direct DC Wiring

Since the Starlink Mini accepts 12-48V DC directly, wire a dedicated, fused circuit to the avionics bus, bypassing the weak cigarette lighter [8afa5991]. This is the most elegant solution for 14V aircraft. Requires A&P sign-off, proper wire gauge, and appropriate fusing [8afa5991].

### Option 3: Portable Battery Pack

LiFePO4 battery packs with USB-C Power Delivery can run the Starlink Mini for entire flights without aircraft modifications [8afa5991, 189a4d19]:

- **Flight Gear Smart Battery Pack Max**: High-output USB-C with real-time watt display, ~3 hours runtime [189a4d19]
- **Ravion Battery**: Clips directly to the Mini for extended endurance, up to ~9 hours [189a4d19]

This is ideal for renters or pilots who want zero aircraft modifications.

### Cirrus-Specific Power

The Cirrus center console cigarette jack is NOT capable of providing enough power [c9b01e79]. Cirrus has released a service bulletin for a dedicated power solution, and for older G1/G2/G3 airframes, a dedicated 28-volt TSO'd cigarette lighter receptacle installed by an A&P is recommended [c9b01e79].

## Mounting Solutions

### Suction Cup Window Mounts

Particularly effective in aircraft with rear windows like the Cirrus SR22 [45f14a0f, f3b9bbc7]:

- 3D-printed corner mounts friction-fit to the Mini with suction cup slots [45f14a0f]
- Print in ABS or ASA for heat tolerance; scale up 0.8% for shrinkage [45f14a0f]
- Caution: GA aircraft are unpressurized, so suction forces decrease with altitude [45f14a0f]
- Consider window bond condition before suspending terminal weight [45f14a0f]

### Custom Brackets

Leverage existing hardware (luggage netting kit mounts) for secure, repeatable installs without compromising structural integrity [f3b9bbc7].

### Cirrus OEM Solution

In October 2025, Cirrus Aircraft announced an official Starlink Cabin "skylight" window mount and power solution, available through Cirrus Service Centers [c9b01e79].

### Placement Guidelines

- Flat placement with clearest sky view is recommended [f3b9bbc7]
- Vertical placement against cabin windows typically gives poor connectivity [f3b9bbc7]
- Dashboard placement may be degraded by window material and deicing technology [f3b9bbc7]
- Orient the terminal facing north in the Northern Hemisphere [f3b9bbc7]
- Remove when parked, especially in heat [45f14a0f]

## Practical Use Cases

Real-world applications for GA pilots [e8896fa5, 0b2e9049, 189a4d19]:

- **Enhanced weather**: High-resolution NEXRAD radar, satellite imagery, real-time lightning data far richer than FIS-B
- **Continuous NOTAM/TFR updates**: Real-time airspace restriction changes
- **Communication**: VoIP calls to FBOs, text messaging, email
- **Dynamic flight planning**: Live wind charts, web-based planning tools
- **Passenger entertainment**: Streaming video, web browsing
- **Safety**: PIREP filing, coordination and emergency communications in remote areas

## Important Limitations

- **Starlink does NOT replace ADS-B** for weather or traffic [189a4d19]. Treat internet weather as supplemental
- **Data management is critical**: Enable Low Data Mode on iPad/iPhone WiFi to prevent background iCloud sync from burning data [189a4d19]
- **Distraction risk is real**: One pilot reported streaming an NFL game grabbed his attention within seconds in flight [189a4d19]. Adopt sterile cockpit procedures and disconnect before descent
- **Coverage gaps**: While Starlink covers most areas, connectivity can drop in heavy tree cover, during weather, or in certain orientations [350d093c]
- **Plan changes can happen abruptly**: Starlink has repeatedly changed pricing and speed limits, sometimes breaking existing setups [7c5d1d0f, c9b01e79]

---

## Aerodynamics Of The Long Ez Canard

# Aerodynamics of the Long-EZ Canard

The Long-EZ is a well-known experimental aircraft designed by Paul Poberezky, featuring a distinctive canard configuration. The aerodynamic characteristics of its canard design play a crucial role in its flight performance and stability.

## Canard Configuration Overview

The Long-EZ employs a canard configuration, which places the horizontal stabilizer (canard) in front of the main wing. This design is intended to improve lift distribution, reduce drag, and enhance control authority during low-speed flight. The canard provides additional lift and helps in managing the aircraft's center of gravity (CG) position, which is essential for maintaining stability during various flight phases.



## Aerodynamic Advantages

The canard design of the Long-EZ offers several aerodynamic benefits:

- **Enhanced Lift Distribution**: The canard generates lift in front of the main wing, which helps to reduce the load on the main wing and improves overall lift efficiency. This configuration allows for better stall characteristics compared to conventional tail configurations.
- **Improved Control Authority**: The canard provides additional control authority, particularly at low speeds and high angles of attack. This makes the aircraft more responsive to control inputs during critical phases like takeoff and landing.
- **Reduced Drag**: By optimizing the lift distribution, the canard configuration can reduce induced drag, contributing to better fuel efficiency and performance.

## Flight Characteristics

The Long-EZ's canard design contributes to its unique flight characteristics:

- **Stall Behavior**: The aircraft exhibits a benign stall behavior, with the canard generating lift even at high angles of attack. This characteristic makes it safer to fly in low-speed conditions.
- **Trim and Stability**: The canard configuration allows for better trim control, enabling the aircraft to maintain stable flight with minimal pilot input. The design also provides a natural tendency to pitch up during stall conditions, enhancing safety.



## Design Considerations

The design of the Long-EZ's canard is influenced by several factors:

- **Wing Geometry**: The main wing and canard are designed to work in harmony, with the canard generating lift that complements the main wing's performance.
- **Center of Gravity (CG) Management**: The canard configuration allows for a more flexible CG range, which is essential for safe flight operations.
- **Control Surface Integration**: The canard's control surfaces are carefully integrated to ensure effective pitch control throughout the flight envelope.

## Conclusion

The aerodynamic design of the Long-EZ's canard configuration is a key element in its overall performance. By leveraging the advantages of the canard layout, the aircraft achieves improved lift distribution, enhanced control authority, and safer flight characteristics. These features make it an interesting case study in experimental aircraft design.

---

## aircraft LLC ownership tax depreciation section 168k

# Aircraft LLC Ownership, Tax Depreciation, and Section 168(k)

## Ownership Structures

### LLC Ownership
Separating aircraft ownership from operating companies via an LLC serves valid business purposes including liability protection, ownership differences, and managerial flexibility [996222cb]. However, this structure introduces tax complexity, particularly around passive activity rules and bonus depreciation eligibility [996222cb][aea58bc6].

### Multi-Owner Structures
Two primary options exist for multi-owner aircraft [aea58bc6]:
- **LLC ownership**: Each owner holds a piece of the LLC. This creates passive activity issues since the LLC operates as a rental company generating passive losses, and related-party leasing rules under IRC Sec 280F often disqualify bonus depreciation [aea58bc6].
- **Co-ownership**: Each owner holds a registered, undivided interest. Owners can elect out of partnership treatment and handle tax planning independently, often the only option allowing bonus depreciation deductions [aea58bc6].

## Depreciation Framework

### Standard MACRS Depreciation
Non-commercial business aircraft are classified as 5-year property under the General Depreciation System (GDS) [059328e7][20088688]. Without bonus depreciation, the schedule is: Year 1: 20%, Year 2: 32%, Year 3: 19.2%, Year 4: 11.52%, Year 5: 11.52%, Year 6: 5.76% [43c8fa77][a01434fc]. Unlike business automobiles, aircraft depreciation has no annual dollar caps [43c8fa77][a01434fc].

### Section 179 Expensing
Section 179 allows immediate deduction of qualifying property cost up to annual limits [555676e9][47665827]:
- 2025 maximum deduction: $1.22 million (per some sources) to $2.5 million (per others reflecting OBBBA updates) [555676e9][47665827]
- Phase-out threshold begins at $3.05-$4.0 million in total asset purchases [555676e9][47665827]
- Cannot create or increase a net operating loss [555676e9]
- Requires more than 50% qualified business use [555676e9]
- Best suited for aircraft in the $500K-$1.2M range [555676e9]

## Section 168(k) Bonus Depreciation

### Current Law Under OBBBA (One Big Beautiful Bill Act)
The OBBBA, signed July 4, 2025, permanently reinstated 100% bonus depreciation for qualified property acquired and placed in service after January 19, 2025 [e0017cfd][059328e7][47665827]. This eliminates the TCJA phase-down schedule that had reduced bonus depreciation to 40% for 2025 [059328e7][e0017cfd].

Key provisions [059328e7][fba77f27][47665827]:
- 100% first-year deduction for qualifying aircraft
- Applies to both new and used aircraft (new to the taxpayer)
- Aircraft must have MACRS recovery period of 20 years or less (5-year property qualifies easily)
- Must meet the predominant business use test (>50% qualified business use)
- No annual dollar limit (unlike Section 179)
- Can create a net operating loss [47665827]

### Qualification Requirements
Four requirements must be met [2a91d9f1][fba77f27]:
1. Property must be of a specified type (tangible property with recovery period of 20 years or less)
2. Original use must commence with the taxpayer, or used property must meet acquisition requirements
3. Property must be placed in service within the specified time period
4. Property must be acquired by the taxpayer after September 27, 2017

### The "Purchase" Requirement
Section 168(k) references Section 179(d)(2) for the definition of "purchase" [fd05a340]:
- No acquisition from related parties (family limited to spouse, ancestors, lineal descendants)
- No acquisition between controlled group members
- Basis cannot be determined by reference to the seller's basis (excludes inherited property)
- No bonus depreciation on Section 754 step-up adjustments [fd05a340]

## Critical Compliance Areas

### Business Use Testing
Two tests apply under IRC Section 280F [2a91d9f1][a01434fc]:
- **25% Test**: Must have at least 25% qualified business use
- **50% Test**: Total business use (including properly taxed compensation flights) must exceed 50%

If qualified business use drops to 50% or below, Section 179 and bonus depreciation may be limited or recaptured [3cee2a6a][9d039280].

### Recordkeeping
Aircraft are "listed property" requiring more rigorous substantiation than other equipment [c2967df0][9d039280]. Required records include:
- Flight logs showing date, route, purpose, passengers, and hours [3cee2a6a]
- Categorization of every flight as business, personal, commuting, or entertainment [9d039280]
- Tracking by occupied seat hours or occupied seat miles [c2967df0]
- Separate accounting for spouse and family travel (deductible only if the person is an employee traveling for bona fide business purpose) [c2967df0]

### IRS Audit Campaign
In February 2024, the IRS announced a dedicated compliance campaign targeting business aircraft use, initially opening approximately four dozen audits of corporations and complex partnerships [9d039280][28e9a594]. The IRS is developing a database of corporate jet activity using "advanced analytics" to identify audit targets [28e9a594]. Deduction amounts can reach tens of millions of dollars per return [28e9a594].

Key audit focus areas [9d039280]:
- Proper allocation between business and personal use
- Income imputation for personal use (SIFL rates vs. charter rates)
- Post-TCJA entertainment flight deduction disallowances under Section 274
- Hobby loss challenges under Section 183

## Passive Activity Rules

The passive activity loss rules (IRC Section 469) prevent losses from passive activities from offsetting active income [996222cb][82afcd4b][6178923b]. An aircraft entity can become passive if it is treated as a "rental" activity or if the individual does not "materially participate" (generally 500+ hours annually) [6178923b][82afcd4b].

### Grouping Election
Taxpayers may group their aircraft entity with an operating company for passive activity purposes if the group makes a logical economic unit [996222cb]. Starting in 2011, individuals must file specific grouping disclosures on tax returns; failure to disclose may cause each entity to be viewed separately [996222cb].

### Hobby Loss Rule (Section 183)
The IRS can classify aircraft leasing arrangements as hobbies, taxing gross income while disallowing all deductions [8079d4e9]. Nine factors determine profit motive, with particular risk for arrangements that operate at a loss, have depreciating assets, and involve extensive personal usage [8079d4e9]. The Morton v. United States case established that a "unified business enterprise" theory can protect aircraft deductions when the aircraft serves profitable related businesses [d281917a].

---

## aircraft canard stall characteristics safety

# Aircraft Canard Stall Characteristics and Safety

## What Are Canard Wings?

A canard is a small forewing or foreplane placed forward of the main wing of a fixed-wing aircraft [6b1e40f7]. The term derives from the French word for "duck," inspired by the Santos-Dumont 14-bis of 1906 whose forward-surface configuration resembled a duck stretching its neck [8f488d8c][6b1e40f7]. Despite appearing on the first powered airplane -- the Wright Flyer of 1903 -- canard designs were not built in quantity until the Saab Viggen jet fighter in 1967 [6b1e40f7].

## Types of Canard Configurations

### Lifting Canard
The canard shares the lifting load with the main wing, providing additional lift particularly during takeoff. The canard must stall before the main wing for safety, which constrains the main wing design [8f488d8c]. Both surfaces produce upward lift, unlike conventional tailplanes that typically generate downforce [cbc50e20].

### Control Canard
Functions primarily as a pitch control surface rather than a significant lift contributor. Offers more precise pitch control but less total lift benefit [8f488d8c].

### Three-Surface Configuration
Combines a foreplane, central wing, and tailplane. The third tail surface does not stall and provides better controllability during canard stall events, avoiding the pitch oscillations that pure canard designs can experience [c87ab800]. The Piaggio P.180 Avanti uses this configuration to reduce wing size, weight, and drag [c87ab800].

## Stall Behavior: The Central Safety Question

### The Canard-First Stall Principle

In a properly designed canard aircraft, the canard surface stalls before the main wing, dropping the nose automatically and preventing the full-wing stall that causes sudden loss of lift [cbc50e20][8f488d8c][07921b00]. This is often described as making canard aircraft "stall-proof" -- more accurately, the main wing maintains flying speed while the canard's stall limits the maximum angle of attack [ba681ecf].

### How It Compares to Conventional Tailplanes

In conventional aircraft, the wing stalls first and the tailplane helps push the nose down for recovery -- a predictable and well-understood behavior [cbc50e20]. With canards, the safety mechanism relies on the forward surface stalling before the aft surface, which requires careful design of airfoil selection, wing loading ratios, and center-of-gravity management [d87d24e8][8f488d8c].

### When Canard Stall Protection Fails

Poorly designed canards can cause dangerous conditions [cbc50e20][8f488d8c]:

- **Deep stall**: If the turbulent wake from a stalled canard disrupts airflow over the main wing, both surfaces may lose effectiveness simultaneously [c87ab800][2a8b168f]. Unlike T-tail aircraft where deep stall is a known risk, canard aircraft have potential for deep stall through a different mechanism [2a8b168f].
- **Pitch instability**: The Wright Brothers discovered that forward control surfaces tend to destabilize pitch. They added weights to the nose and eventually abandoned canards by 1910 [6b1e40f7][8f488d8c].
- **Pitch oscillations**: In pure canard designs, the foreplane can repeatedly stall and recover, causing nose-up/nose-down oscillations. The three-surface configuration addresses this by providing a non-stalling tail for damping [c87ab800].
- **CG sensitivity**: Canard aircraft are very sensitive to center-of-gravity location. Improper loading can defeat the canard-first stall sequence [ba681ecf][acd91660].

## Real-World Safety Data

Analysis of homebuilt canard aircraft accident data reveals nuanced results [ba681ecf]:

- **Pilot miscontrol rates are lower**: Overall canard aircraft suffer pilot miscontrol accidents about 25% less often than the general homebuilt fleet (29% vs. 39%), supporting the stall-resistance claim.
- **Judgment errors are higher**: The occurrence of judgment errors in the canard fleet is slightly higher than the overall homebuilt rate, resulting in roughly equivalent total pilot error rates.
- **Fuel starvation is elevated**: Canard aircraft with multiple fuel tanks and no "both" valve position see more fuel management errors.
- **Airspeed-related accidents still occur**: Despite the "can't stall" reputation, the NTSB still identified cases where accidents were blamed on the pilot's airspeed control, though at a lower rate (~10% vs. 16%).
- **Ground handling problems**: The Quickie series earned a bad reputation for ground handling, with 65% of its accidents occurring during ground-handling phases, attributed to factors including maingear mounted on canard wingtips [ba681ecf].

## Notable Canard Aircraft

### Homebuilt/Experimental
- **Long-EZ** (638 registered): Burt Rutan's improved successor to the VariEze, with an O-235 Lycoming engine and 94 sq ft total wing area. Addressed VariEze problems including visibility, stick forces, and CG sensitivity [acd91660][ba681ecf].
- **VariEze** (606 registered): Pioneered low-cost foam and fiberglass construction. Rutan discovered that his "unspinnable" design could, in certain unusual combinations of CG, weight, and speed, be forced to depart into a spin [acd91660].
- **Velocity** (311 registered): Later canard design with improved handling characteristics.
- **Beechcraft Starship**: Commercial canard with variable-geometry foreplane, composite construction, and Pratt & Whitney turboprops. Only 53 built; production ceased 1995 due to poor sales at $3.9M (comparable to faster Citation V or Learjet 31) [3b9de4cf].

### Military
- **Saab Viggen/Gripen**: Revived modern canards, using fly-by-wire to manage inherent instability for superior maneuverability [6b1e40f7][07921b00].
- **Eurofighter Typhoon, Dassault Rafale**: Modern fighters using canards with computer-controlled stability systems to solve the stability challenge that makes canards dangerous in unaugmented aircraft [cbc50e20][07921b00].

## Regulatory Framework

FAR 25.207 establishes stall warning requirements for transport category aircraft: stall warning must begin at a speed exceeding the stall identification speed by not less than 5 knots or 5% CAS, whichever is greater [276c9478][93618e8e]. The pilot must be able to prevent stalling when recovery begins no less than 3 seconds after stall warning onset in icing conditions [276c9478]. These regulations apply regardless of configuration, including canard designs.

## Aerodynamic Trade-offs

For statically stable aircraft, the canard configuration introduces several aerodynamic penalties [d87d24e8]:

- Induced drag at off-design points is higher than conventional configurations
- The main wing requires more area because it must maintain stall margin
- The smaller canard surface needs the highest lift coefficient at the smallest Reynolds number -- normally the reverse would be better
- The landing gear must retract into the fuselage because the wing is too far aft of the CG

These disadvantages largely disappear for unstable fighter aircraft using fly-by-wire, explaining why military applications have been more successful than civil ones [d87d24e8].

---

## aircraft dry lease Part 91 compliance

# Aircraft Dry Lease and Part 91 Compliance

## What Is an Aircraft Dry Lease?

A private aircraft "dry lease" is an arrangement where an aircraft owner/lessor leases an aircraft to a lessee/operator without providing a crew [dfe6dd6a]. The lessee provides its own crew, exercises operational control of all flights, and operates the aircraft under 14 C.F.R. Part 91 rather than the more restrictive Part 135 (charter) regulations [dfe6dd6a].

## Dry Lease vs. Charter (Part 135)

The distinction between a dry lease and a charter arrangement has significant operational and financial implications [dfe6dd6a]:

| Factor | Dry Lease (Part 91) | Charter (Part 135) |
|---|---|---|
| Crew | Lessee provides own crew | Operator provides crew |
| Operational Control | Lessee has full control | Certificate holder has control |
| Certificate Required | Neither party needs one | Active charter certificate required |
| Maintenance Standards | FAA Part 91 compliance | More extensive Part 135 requirements |
| Airport Restrictions | Fewer restrictions | Runway length requirements apply |
| Instrument Approaches | No onsite weather reporting required | Only airports with onsite weather reporting |
| Federal Excise Tax | Generally not due on lease payments | Tax applies to charter fees |
| Sales Tax | Often assessed on lease payments | Varies by jurisdiction |

[dfe6dd6a]

## Key Terms in a Dry Lease Agreement

A written dry lease agreement should address the following essential elements [dfe6dd6a]:

### Parties and Term
Identify the lessor and lessee's legal name, address, and place of organization. Specify the duration of the lease and whether it is exclusive or non-exclusive. For non-exclusive leases, define how often the lessee may use the aircraft and the reservation procedures [dfe6dd6a].

### Operational Control
The agreement must specify clearly that the lessee has operational control during each flight. The lessee must acknowledge and accept the responsibility and potential liability associated with exercising operational control [dfe6dd6a]. This is the critical element that distinguishes a dry lease from a wet lease or charter arrangement.

### Delivery, Storage, and Return
Define where the aircraft will be delivered and returned, any storage restrictions, and return conditions. For non-exclusive leases where the aircraft returns after each round trip, the process for returning, inspecting, and passing off control should be detailed with specificity [dfe6dd6a].

### Financial Terms
Identify whether lease payments are fixed or hourly/per-use, payment frequency, and due dates. State sales tax will likely be assessed on all rent payments [dfe6dd6a].

### Expenses and Maintenance
Specify which party pays for operating expenses (fuel, oil, landing fees), storage, maintenance, and inspection costs. The party responsible for securing and directing maintenance should warrant that the aircraft will be kept in compliance with FAA regulations [dfe6dd6a]. Under a dry lease, crew hiring and payment must be arranged and paid for by the lessee [dfe6dd6a].

### Insurance
Both parties should carry appropriate liability insurance. The agreement should specify minimum coverage amounts, require the other party to be named as additional insured, and require certificates of insurance be provided prior to any flight operations [dfe6dd6a].

### Truth-in-Leasing
Federal law requires a truth-in-leasing clause for large aircraft (over 12,500 lbs MTOW). The clause must contain specific certifications by the parties regarding operational control and maintenance responsibility. The lessee must also provide the FAA with a copy of the lease (or relevant portions) within 24 hours of execution [dfe6dd6a].

### Home Base and Tax Considerations
The aircraft's home base is a primary factor used by the IRS in determining situs for state and local taxation. While federal excise tax generally does not apply if the lease is properly structured, other taxes including state sales tax, personal property tax, and use tax may be applicable [dfe6dd6a].

## Part 91 Operational Advantages

Operating under Part 91 rather than Part 135 provides several operational advantages [dfe6dd6a]:

- No requirement for the operator to hold a charter certificate
- Fewer airport restrictions (no mandatory runway length minimums)
- Ability to conduct instrument approaches at airports without onsite weather reporting
- Reduced maintenance and servicing regulatory overhead
- No federal excise tax on transportation (when properly structured)
- Greater scheduling flexibility without charter certificate limitations

## Compliance Considerations

Despite the reduced regulatory burden, dry lease operators must still comply with all applicable Part 91 regulations governing aircraft airworthiness, pilot qualifications, flight rules, and maintenance standards. The lessee bears full responsibility for safe operation and regulatory compliance during the lease period [dfe6dd6a].

---

## experimental aircraft FAA 51 percent rule amateur built

# Experimental Aircraft: FAA 51 Percent Rule for Amateur-Built

## Overview

The FAA's "51 percent rule" is the cornerstone regulation governing amateur-built experimental aircraft in the United States. Codified in 14 CFR 21.191(g), it defines an amateur-built aircraft as one where "the major portion of which has been fabricated and assembled by person(s) who undertook the construction project solely for their own education or recreation" [e614fcf3][4a9372dd]. The "major portion" means more than 50 percent of the fabrication and assembly tasks required to make the aircraft airworthy must be completed by amateur builders [51195dae].

## Regulatory Framework

### The Experimental Category
"Experimental" is a category of Special Airworthiness Certificate [39e1d8ec][2bd411ad]. The FAA issues experimental certificates for eight defined purposes, including operating amateur-built aircraft, exhibition, air racing, and research and development [39e1d8ec]. The amateur-built category (purpose 7) accounts for approximately 95% of all custom-built aircraft [39e1d8ec].

All amateur-built aircraft are experimental, but not all experimental aircraft are amateur-built [2bd411ad]. The "Experimental" designation was originally intended for development test aircraft and was adopted for homebuilts in the early 1950s as a path of least bureaucratic effort when the Civil Aviation Authority (FAA's predecessor) created a formal licensing structure for privately built aircraft [2bd411ad].

### What the Builder Must Do
The builder must provide evidence to the FAA that [4a9372dd]:
1. The major portion (more than 51%) of fabrication and assembly was completed by the amateur builder(s)
2. The project was undertaken solely for educational and recreational purposes
3. The aircraft complies with acceptable aeronautical standards and practices

### Operating Limitations
Aircraft with experimental amateur-built certificates carry specific restrictions [4a9372dd]:
- No carrying persons or property for compensation or hire
- Phase I flight testing must be completed before carrying passengers
- Operations limited to specific geographic areas during Phase I
- "EXPERIMENTAL" must be displayed near the entrance to the aircraft [982cc55a]

## The Kit Industry

The vast majority of amateur-built aircraft are assembled from manufacturer-provided kits [4a9372dd][982cc55a]. The kit manufacturer designs the aircraft and produces components up to a maximum of 49% completion. The remaining 51% or more of fabrication and assembly tasks must be performed by the amateur builder [982cc55a].

### Kit Evaluation
The FAA evaluates kits through a National Kit Evaluation Team (NKET) that validates new kits and verifies that manufacturers sell kits with a majority of work remaining for the builder [ae1eb2b7]. Evaluated kits are posted on the FAA's approved list with breakdowns of what percentage of work the manufacturer performs versus what remains for the builder [a7eb6562].

### Quick-Build Kits
Many manufacturers offer "fast-build" or "quick-build" options where additional components are pre-fabricated, pushing the manufacturer's contribution closer to the 49% limit [982cc55a]. These options must be separately evaluated and approved by the FAA to ensure compliance [a7eb6562].

## The Fabrication and Assembly Checklist

The FAA uses the "Amateur-Built Aircraft Fabrication and Assembly Checklist (2009)" as an aid in determining compliance with the 51% rule [51195dae]. This checklist is required when:

- Commercial assistance was used during construction [51195dae]
- The builder modified an FAA-approved kit in ways affecting the major portion determination
- The aircraft was built from prefabricated major components
- Salvaged or used parts from type-certificated aircraft were incorporated
- The kit has not been evaluated by the FAA [51195dae]

The checklist contained in Appendix 8 of Advisory Circular 20-27G lists fabrication and assembly tasks across all major aircraft systems with columns for the kit manufacturer, amateur builder, and commercial assistance [0d5b7947][d8bfdb59].

## Commercial Assistance

Builders may hire professionals to assist with construction, but this commercial assistance must not prevent the builder from meeting the 51% threshold [a7eb6562][51195dae]:

- Work performed by commercial assistance providers counts against the builder's total -- it goes into a separate column that does not credit toward the 51% [a7eb6562]
- The burden of proof is on the applicant, not the FAA -- the builder must "show" compliance through photographic documentation, build logs, and other evidence [a7eb6562]
- The FAA does not provide pre-approval for the effect of commercial assistance; builders should contact their local FAA office to discuss plans before proceeding [a7eb6562]

### Completion Centers
"Completion centers" or "build centers" exist that provide assembly services ranging from tool rental and storage to total aircraft assembly [65f72c1a]. While builder assistance programs are generally tolerated, centers that assemble critical airframe components outside the owner's presence likely violate the regulations [65f72c1a]. Some owners have been found to falsely certify that they built the majority of their aircraft, a practice the courts have condemned [65f72c1a].

## Regulatory Evolution

The 51 percent rule has evolved through several rulemaking efforts:

- **2006 ARC**: The first Amateur-Built Aircraft Aviation Rulemaking Committee examined the advisory material [ae1eb2b7]
- **2008 ARC**: A reformed committee proposed the controversial "20/20/11" formula (20% fabrication, 20% assembly, 11% as either) which was later withdrawn after builder community opposition [ae1eb2b7]
- **AC 20-27G and Order 8130.2F Change 4**: The final revised policy eliminated the percentage-based build formula, broadened the definition of fabrication, and created a uniform standard for new kit approval [1dd968be]

Key elements of the current policy [1dd968be]:
- Builders can build and fly almost any aircraft they can create
- Existing FAA-approved kits are grandfathered under the revised rule
- Clear guidance for builders who want to hire professional assistance
- The NKET provides uniform evaluation standards for new kits

## The Repairman Certificate

Builders who complete their aircraft can apply for a Repairman Certificate from the FAA, which authorizes them to perform the required annual condition inspection on that specific aircraft [ae0eaac1]. To obtain this certificate, the builder must have fabrication knowledge sufficient to maintain the aircraft [51195dae]. The certificate applies only to the specific aircraft built -- not to other aircraft, even of the same type [e011659a].

Non-builder owners of E-AB aircraft must use a licensed A&P mechanic for condition inspections, as they cannot obtain a Repairman Certificate for an aircraft they did not build [ae0eaac1].

## Certification Process

To obtain an experimental airworthiness certificate [58a9e0fd][104d74f7]:

1. Complete aircraft registration (permanent, not just applied for)
2. Submit notarized FAA Form 8130-12 (Eligibility Statement) certifying major portion compliance
3. Provide three-view drawings or photos, weight and balance data, and program letter
4. Schedule inspection with a Designated Airworthiness Representative (DAR) or FAA inspector
5. Pass the physical inspection of the completed aircraft
6. Receive operating limitations defining Phase I flight test area and requirements

The FAA's online Airworthiness Certificate Application (AWC) program has digitized this process, requiring computer access and document scanning [58a9e0fd].

---

## fiberglass layup vacuum bagging homebuilt aircraft

# Fiberglass Layup and Vacuum Bagging for Homebuilt Aircraft

## Overview

Vacuum bagging is a composite fabrication technique that uses atmospheric pressure to compress fiber-reinforced laminate against a mold during cure, producing parts with superior strength-to-weight ratios compared to hand layup alone [ff028761][48d22c7c]. The technique removes trapped air between layers, compacts fiber plies for efficient force transmission, reduces humidity, and optimizes the fiber-to-resin ratio -- the critical factor determining a composite structure's mechanical performance [ff028761]. For homebuilt aircraft, vacuum bagging enables builders to produce professional-quality composite components including wing skins, cowlings, fairings, fuselage panels, and structural bulkheads [cbf6c062][5d23bb0d].

## The Physics of Vacuum Bagging

Atmospheric pressure at sea level exerts approximately 14.7 psi (29.92 inches of mercury) uniformly in all directions [ff028761]. When air is evacuated from a sealed bag enclosing a laminate, the pressure differential between the atmosphere outside and the vacuum inside creates a uniform clamping force across the entire part surface, regardless of shape complexity [48d22c7c]. This approach turns the entire atmosphere into a perfectly uniform press [48d22c7c].

## Fiber-to-Resin Ratio

The key benefit of vacuum bagging is maximizing the fiber-to-resin ratio [ff028761]:

- **Hand layup**: Typically uses excess of 100% fabric weight in resin
- **Vacuum bagged**: Targets approximately 60% resin content
- **Aerospace-grade**: Can achieve as low as 40% resin content

Reinforcement fibers (fiberglass, carbon, Kevlar) provide structural strength, while resin alone is brittle. Excess resin adds weight without proportional strength gain. Vacuum pressure squeezes out excess resin while ensuring complete fiber saturation, achieving the optimal balance [ff028761].

## Materials and Equipment

### Vacuum Pump
Select a pump rated for the bag size and desired vacuum rate. Most homebuilder applications use rotary vane or diaphragm pumps [ff028761]. A pump should achieve full vacuum in less than five to eight minutes on the largest bag you plan to use. Smaller pumps can work but are more vulnerable to leaks [ff028761].

### Vacuum Bag Stack (from part outward)

1. **Release film or peel ply**: Placed directly on the laminate. Prevents subsequent layers from bonding to the part. Creates a clean, bond-ready surface after cure [cbf6c062][48d22c7c].

2. **Perforated release film (FEP)**: Controls resin bleed-out through calibrated perforations. Perforation size and spacing determine how much excess resin escapes the laminate [cbf6c062]. Too open leads to resin starvation; too closed produces resin-rich laminates [48d22c7c].

3. **Bleeder/breather fabric**: Absorbs excess resin and provides air pathways for uniform vacuum distribution across the part surface [cbf6c062]. Common materials include purpose-made bleeder fabrics, fiberglass cloth, or even paper towels for small projects [38bc63c8]. Without breather, vacuum cannot distribute evenly [48d22c7c].

4. **Vacuum bag film**: Flexible polymer film (nylon or polyethylene) sealed to the mold with sealant tape. Must be oversized by 15-30% and pleated for complex shapes [48d22c7c][cbf6c062].

### Additional Equipment
- Vacuum gauge and regulator for monitoring and adjusting pressure [38bc63c8]
- Resin trap to prevent resin from reaching the pump
- Sealant tape (butyl rubber) for creating airtight seals
- Quick-disconnect fittings for vacuum line management [38bc63c8]

## The Layup Process

### Preparation
Clean and prepare the mold surface with release agent [48d22c7c]. Pre-cut all reinforcement materials and organize them in layup sequence. Mix epoxy resin per manufacturer specifications -- typical systems like West Systems 105/206 provide approximately 30 minutes of working time [cad117ab].

### Wet Layup Method
1. Apply resin to the mold surface or first reinforcement layer
2. Place reinforcement plies, wetting each layer with resin using a roller or squeegee
3. Build up layers according to the laminate schedule (weight, number, and orientation of plies)
4. Add core material (foam or honeycomb) if applicable
5. Apply release film, bleeder, breather, and bag film
6. Seal the bag and pull vacuum [ff028761][48d22c7c]

### Prepreg Method
Prepreg materials (pre-impregnated with resin) are laid up dry, then vacuum bagged and cured with heat in an oven or autoclave [a370d9d3]. This method provides the most consistent fiber-to-resin ratios but requires controlled material storage and processing temperature.

## Core Materials for Aircraft Structures

Foam core sandwich construction is standard in composite homebuilt aircraft [f3ce2da3]:

- **Divinycell (PVC)**: Industrial-grade closed-cell foam. Continuous operating temperature ~160 F. More affordable option [f3ce2da3].
- **Rohacell (PMI)**: Polymethacrylimide foam with 30-60% higher mechanical properties than equal-density PVC. Operating temperature ~275 F. Higher cost [f3ce2da3].
- **End-grain balsa**: Traditional core material with excellent compression properties. Susceptible to moisture absorption.

Finer cell foams absorb less resin into open surface cells, producing lighter layups [f3ce2da3]. Pre-treating foam surfaces with a squeegee coat of neat epoxy before layup helps control resin uptake.

## Quality Targets

Well-executed vacuum bagging achieves [48d22c7c]:
- Void content below 1-2%
- Controlled fiber volume fraction of 40-60%
- Uniform laminate thickness
- Dramatically improved fatigue life compared to hand layup

## Aircraft-Specific Applications

### Wing Construction
CNC-machined or foam-carved mold blanks are used to produce wing skin molds [5d23bb0d]. Low-density tooling foam (6-30 lb/ft3) is assembled into mold blanks, CNC-machined to the wing profile, surface-treated, and used for vacuum-bagged layups [5d23bb0d]. For the homebuilder, producing non-production-quality molds suitable for prototypes and one-offs is now affordable with dropping CNC shop rates [5d23bb0d].

### Bulkheads and Ribs
Composite ribs and formers can be fabricated as flat sandwich panels (CNC-cut from stock) or molded in female molds with integrated bonding flanges [3a560b5c]. Molded ribs avoid the need for secondary filleting and taping during wing closeout.

### Repair and Replacement Parts
When original molds are unavailable, replacement parts can be fabricated by creating a mold directly from the aircraft surface. A sheet of scrap aluminum is clamped against the existing structure, and a plywood backing with flox/epoxy slurry captures the shape for use as a layup mold [e72e26b8].

## Resin Systems

For homebuilt aircraft composites [3800d305][88521c66]:
- **Epoxy**: Preferred for structural aircraft applications. Strong, durable, and resistant to fuel. West Systems and Aeropoxy are popular choices.
- **Epoxy Vinylester**: Combines epoxy-like strength with easier processing. High tensile-elongation strength, water resistance, and fatigue resistance. Used in float construction [88521c66].
- **Polyester**: Lowest cost but inferior strength and fuel resistance. Not recommended for primary aircraft structure.

Temperature and humidity control during layup is critical -- resin cure characteristics are sensitive to environmental conditions [3800d305].

## Learning Resources

- **EAA SportAir Composite Workshops**: Hands-on classes covering layup techniques, vacuum bagging, hot-wire foam cutting, and resin systems [3800d305]
- **Composite Basics (7th Edition)**: Covers theory, sandwich structures, tooling, and vacuum bagging for amateur-built aircraft [c83ba993]
- **Understanding Composite Construction**: Elementary theory through detailed vacuum bagging procedures suitable for homebuilders [a94a484d]
- **Aircraft Spruce Vacuum Bagging Technical Book**: Basic components and procedures for vacuum bagging systems [b9921f73]
- **KITPLANES Magazine series**: Detailed articles on rapid prototyping, mold making, coupon testing, and production layup procedures [5d23bb0d][f3ce2da3]

---

## foam core wing construction hot wire cutting

# Foam Core Wing Construction and Hot Wire Cutting

## Overview

Foam core wing construction is a method of building aircraft wings using precisely shaped foam blocks as the structural core, which is then covered with a reinforcing skin of fiberglass, carbon fiber, balsa wood, or heat-shrink film [2c7420d2][316f6770]. Hot wire cutting is the primary technique for shaping foam cores into accurate airfoil profiles. The method is used extensively in RC model aviation, UAV development, and experimental homebuilt aircraft, offering advantages in precision, weight, strength, and repairability over traditional built-up wood construction [2c7420d2].

## Why Foam Wings

Foam core wings offer several advantages over built-up balsa construction [2c7420d2]:

- **Strength**: EPS foam has a compression strength of approximately 1,000 pounds per square foot. The honeycomb-like cell structure distributes loads efficiently [2c7420d2].
- **Weight**: EPS foam weighs approximately 1 pound per cubic foot versus 4-12 pounds per cubic foot for balsa. The finished wing weights are comparable because balsa is used in a skeleton fashion, but the foam wing is stronger [2c7420d2].
- **Precision**: CNC or template-guided hot wire cutting produces inherently accurate airfoil profiles, whereas built-up structures accumulate tolerance errors across many individual parts [2c7420d2].
- **Repairability**: Foam is quick and easy to cut and patch. Some repairs can be performed at the flying field [2c7420d2].
- **Cost**: Foam is inexpensive and widely available as building insulation [2c7420d2].

## Hot Wire Cutting Principles

Hot wire cutting uses an electrically heated wire (typically nichrome alloy) to melt a precise path through foam [7ce87b8d][bf4b138b]. The wire does not physically cut in the traditional sense -- it vaporizes or melts the foam immediately in front of it, producing an extremely smooth surface with minimal dust or debris [7ce87b8d].

### Wire Selection
Nichrome wire is preferred for its high electrical resistance, stability at elevated temperatures, and durability [62cd6976]:

| Gauge (AWG) | Best For |
|-------------|---------|
| 26-32 | Small tabletop cutters, thin foam, precision work |
| 21-24 | Versatile middle ground for most wing cutting |
| 16-20 | Large foam blocks, higher power applications |
| 11-16 | Very stiff wire for tight curves and complex shapes |

A good starting gauge for general wing cutting is 21 AWG. A variable power supply is the most valuable upgrade for adjusting wire temperature across different foam types and thicknesses [62cd6976].

### Critical Parameters
Three variables determine cut quality [7ce87b8d]:

1. **Wire temperature**: Too cold and the wire drags; too hot and it melts too wide a path or snaps
2. **Wire tension**: Must be sufficient to keep the wire straight and prevent sagging
3. **Cutting speed**: Must match temperature so foam melts just ahead of the wire without contact. As a rough guide, approximately 200mm per minute for XPS [31406517]

## Manual Hot Wire Cutting

The simplest approach uses a bow-style cutter guided along templates [9b2dbe6d][5b5147c0]:

### Equipment
- **Hot wire bow**: Frame of hardwood or lightweight tubing (25mm x 13mm typical) with the wire stretched between the ends. Tension maintained by springs, bungee cord, or turnbuckles [fedbd47c][9b2dbe6d].
- **Power supply**: Options include battery chargers, LiPo batteries (3S-4S), Nintendo GameCube adapters, or purpose-built variable power supplies [3ddebb81][92d46c88]. A dimmer switch provides simple temperature control [ffa1938a].
- **Templates**: Cut from rigid, heat-resistant material -- formica, MDF, aluminum sheet, or carbon fiber. Must be smooth and free of ridges that would catch the wire [4b524099][3ddebb81].

### Cutting Technique
1. Pin templates to opposite ends of the foam block, aligned on the chord line
2. Tension the wire and heat it
3. Two operators simultaneously guide the wire along each template, coordinating speed to maintain uniform wire position
4. Number template edges (1-10 from leading to trailing edge) to synchronize movement between operators [ffa1938a]

The wire dwells longer on the smaller end of a tapered wing, which can cause over-melting. Gravity-assisted cutters address this by using weights to control wire feed rate automatically [5b5147c0].

## CNC Hot Wire Cutting

CNC systems automate the cutting process using computer-controlled stepper motors to drive the wire along programmed airfoil coordinates [a332961d][3aa21ae4].

### Machine Architecture
A 4-axis CNC cutter has two towers, each with horizontal (X) and vertical (Y) axes. The four axes can move independently, enabling tapered and swept wing shapes where root and tip profiles differ [3aa21ae4]. The machine needs only enough rigidity to withstand wire tension -- cutting forces are minimal [3aa21ae4].

### Software Workflow
1. Select airfoil coordinates from databases (UIUC, Airfoil Tools)
2. Generate 4-axis G-code using software like DevWing Foam, Jedicut, Wing G-code, or FoamXL [d941527e][69d2d048][194c02a0]
3. Define wing planform, taper, sweep, washout, spar locations, and lightening holes
4. Simulate the cut in 3D to verify parameters before cutting [69d2d048]
5. Send G-code to the machine controller (GRBL on Arduino, Mach3, or LinuxCNC) [3aa21ae4]

### Build Cost
A DIY CNC foam cutter using Arduino Mega + RAMPS 1.4 and free software costs approximately $200-280 USD [a332961d]. Components include plywood or MDF frame, smooth rods with lead screws, stepper motors, and controller electronics [3aa21ae4].

## Foam Materials

### EPS (Expanded Polystyrene)
White, beaded foam commonly available as building insulation. Lightweight and inexpensive but quality varies -- insulation-grade foam can have dense lumps that cause wire drag. Use only virgin foam and store it dry for several weeks before cutting [4b524099][9b2dbe6d].

### XPS (Extruded Polystyrene)
Colored boards (blue, pink, green) with smooth, uniform closed-cell structure. Produces very clean cuts and superior mechanical properties but requires slower cutting speed. Available in 30mm and 50mm thick boards at hardware stores [3ddebb81][31406517].

### EPP (Expanded Polypropylene)
Flexible and virtually indestructible -- ideal for trainer and combat aircraft. Cuts slowly and requires heat treatment during manufacturing to relieve internal stresses [4b524099].

## Post-Cutting: Sheeting and Skinning

After cutting, foam cores are reinforced with an outer skin [cad117ab][31406517]:

### Balsa Sheeting
Thin balsa strips (1/16" to 1/8") are glued to the foam core using epoxy. Vacuum bagging the assembly while epoxy cures produces a remarkably strong bond. The resulting structure is stronger than either material alone [cad117ab].

### Fiberglass/Carbon Fiber Skinning
Lightweight fiberglass (3/4 oz) or carbon fiber cloth is laminated to the foam core with epoxy. Vacuum bagging optimizes the fiber-to-resin ratio and eliminates voids [cad117ab]. Mylar film can serve as a smooth release surface for mouldless wing construction [31406517].

### Film Covering
For lightweight RC applications, heat-shrink films (MonoKote, Ultracote) are applied directly over sealed foam or sheeted cores.

## Adhesives for Foam Construction

Foam-safe adhesives are critical since many solvents dissolve polystyrene [c7f6395a]:

- **Foam-safe CA (cyanoacrylate)**: Contact-style adhesive that bonds foam, carbon fiber, and wood without attacking foam. Flying strength in 10-20 minutes [c7f6395a].
- **Epoxy (30-minute)**: Strongest option for structural joints. Can be accelerated with gentle heat [c7f6395a].
- **3M-77 spray adhesive**: Suitable for temporary bonds and foam-to-foam joining of blocks [9b2dbe6d].
- **Foam-Cure (silicone-based)**: Crystal clear, flexible, works with all foam types including EPP and EPO [c7f6395a].

## Advanced Techniques

### Spar Integration
CNC cutters can create spar slots, servo pockets, landing gear pockets, and wire channels directly during the core cutting process [a4853dc6]. Carbon fiber spar caps inlaid into CNC-cut depressions produce wings with targeted reinforcement that would be impossible with manual cutting [a4853dc6].

### Mouldless Construction
Wings can be built without traditional molds by wrapping Mylar film around a foam core with carbon or fiberglass fabric, then vacuum bagging the assembly. The Mylar provides a smooth, non-stick surface that releases cleanly after cure [31406517].

### Professional Services
Companies like Mohr Composites and Eureka Aircraft offer CNC hot wire cutting services for custom wing cores in all foam types, from RC models to experimental aircraft scale [a4853dc6][2c7420d2].

---

## Github Aweirddev Flights Fast Robust Google Flights Scraper Api For Python Probably

# GitHub - AWeirdDev/flights: Fast, robust Google Flights scraper (API) for Python. (Probably)

<!-- FORGE:PLACEHOLDER source_id=d1757b74 -->

This repository presents a Python-based API for scraping Google Flights data, emphasizing speed and reliability. It is designed to provide developers with an efficient method for extracting flight information from Google Flights.

## Key Features

- **Fast**: Optimized for quick data retrieval.
- **Robust**: Built to handle various edge cases and errors in flight data extraction.
- **Python API**: Offers a user-friendly interface for Python developers to integrate flight scraping into their applications.

## Usage Context

The tool is likely intended for developers who require automated access to flight information, possibly for applications such as price tracking, travel planning tools, or competitive analysis.

## Source Details

- **Repository Name**: GitHub - AWeirdDev/flights
- **Description**: Fast, robust Google Flights scraper (API) for Python. (Probably)
- **Tags**: capacities/weblink
- **Status**: imported
- **Created**: 2025-12-19T15:00:41.946Z
- **Last Enriched**: 2026-04-10T23:06:28Z

<!-- FORGE:PLACEHOLDER source_id=d1757b74 -->

---

## lost PLA casting aircraft parts

# Lost PLA Casting for Aircraft Parts

## Overview

Lost PLA casting is a modern adaptation of the ancient lost-wax casting process that uses 3D-printed PLA (Polylactic Acid) patterns instead of hand-carved wax. The technique is relevant to aircraft part fabrication, particularly for homebuilders and experimental aircraft owners who need custom or replacement metal components. However, the available source material for this specific intersection of topics is limited, with sources covering related but distinct areas: casting defects and quality control, PLA material properties, and aircraft parts documentation.

## Casting Fundamentals

### Common Casting Defects

Understanding casting defects is essential for producing airworthy metal parts. The primary categories of casting defects include [83ebb14b] [bff8398f]:

- **Gas porosity**: Blowholes, open holes, and pinholes caused by gas entrapment or rapid solidification, creating internal voids that weaken structural integrity [83ebb14b]
- **Shrinkage cavities**: Formed due to volumetric contraction during uneven or uncontrolled solidification [83ebb14b]
- **Cold shut**: Occurs when molten metal streams fail to fuse properly, creating weak bonding lines that can lead to crack propagation [bff8398f]
- **Misrun**: Results from insufficient metal flow, causing incomplete cavity filling and dimensional inaccuracies [bff8398f]
- **Metal penetration**: Appears as rough surfaces when molten metal fuses into the sand or mold material [83ebb14b]

### Defect Prevention

Key prevention strategies applicable to aircraft part casting [83ebb14b] [bff8398f]:
- Control moisture content in mold materials
- Use appropriate grain sizes and permeability
- Ensure proper venting to prevent gas entrapment
- Optimize pouring temperature and speed
- Apply directional solidification principles in mold design
- Perform adequate fluxing of molten metal to remove impurities

### Detection Methods

Critical components such as aircraft parts must be free from major defects, as they could result in catastrophic failure [bff8398f]. Common inspection methods include:
- X-ray and radiography for internal porosity and shrinkage
- Ultrasonic testing for internal defects and flakes
- Dye penetrant testing for surface cracks and cold shuts
- Visual and dimensional inspection for surface and geometric defects [2fee2d43] [bff8398f]

## Casting vs. Forging for Aircraft Parts

Forging generally produces stronger, more reliable parts with fewer internal defects due to refined grain structure and compressive processing forces [2fee2d43]. Key differences:

| Factor | Casting | Forging |
|--------|---------|---------|
| Process | Molten metal solidification | Plastic deformation under compression |
| Grain structure | Random, as-solidified | Aligned, refined |
| Common defects | Porosity, shrinkage, blowholes | Laps, cracks, die shift |
| Strength | Generally lower | Higher due to grain alignment |
| Cost efficiency | Better for complex shapes | Better for high-strength requirements |
| Suitability | Non-structural or low-stress parts | Load-bearing, safety-critical parts |

For aircraft applications, cast parts are generally acceptable only for non-structural or low-stress components, while safety-critical parts should be forged or machined from billet [2fee2d43].

## PLA Material Properties

PLA is a biodegradable thermoplastic commonly used in FDM (Fused Deposition Modeling) 3D printing. Research into hybrid FDM-injection molding techniques shows that PLA samples can achieve tensile properties up to 68.38 MPa, comparable to injection-molded batches [1fd29f9b]. However, PLA's role in lost-PLA casting is as a sacrificial pattern material that is burned out during the casting process, not as a structural material in the final part.

Key FDM parameters affecting pattern quality include infill density, layer thickness, and print orientation [1fd29f9b]. Higher infill density produces more dimensionally accurate patterns but requires more material and longer burn-out times.

## Aircraft Parts Documentation Requirements

Any cast parts used on certified aircraft must comply with FAA documentation requirements. Aircraft maintenance records must include detailed logs of all parts, inspections, and repairs [d1b3919d]. For experimental/amateur-built aircraft, the builder has more latitude but should still maintain thorough documentation of manufacturing processes, material specifications, and inspection results.

Lost or incomplete aircraft logbooks can render an aircraft unairworthy and significantly reduce its value -- by as much as 30% [fb50ce5d]. All parts, whether cast or otherwise, should be fully documented in the aircraft's maintenance records.

## Practical Considerations

For homebuilders considering lost PLA casting for aircraft parts:
1. Limit cast parts to non-structural applications unless the casting can be thoroughly inspected and tested
2. Use appropriate alloys (aluminum, bronze) suited to the application
3. Perform NDT (non-destructive testing) on finished castings
4. Document the entire process for maintenance records
5. Consider whether forging or machining from billet would produce a safer part for structural applications

---

