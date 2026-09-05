---
status: draft — not ratified. Ryan approves scope before any CadQuery work starts.
approver: unassigned
inputs:
  - ~/docs/research/2026-09-05-quick-build-ultralights-and-small-engines.md (§2 Part A/B, §3, §4, §5)
  - ~/open-ez/CLAUDE.md (SSOT config pattern, AircraftComponent base class, ComplianceTracker)
  - ~/sea-ez (sibling Part 103 project; shared tube/gusset fabrication skills)
---

# Affordaplane plans-as-code kickoff

## Ruling

**Next open-ez project after sea-ez's wing change lands.** Per the 2026-09-05 quick-build-
ultralights research brief §5, the Affordaplane is a natural first CadQuery exercise: simpler
geometry than sea-ez's hull, a 150-250 hour build cycle instead of a multi-phase hull program, and
a real flying result that de-risks tube/gusset fabrication skills before sea-ez needs them. This
spec scopes the kickoff; it does not authorize starting work — sea-ez's wing change is the gate.

## What the Affordaplane is

A Part 103 single-seat ultralight sold as a plans set (affordaplane.com), structured as bolted
aluminum tube with gusset joints — no welding. The research brief's Part A table lists it at 254 lb
advertised empty weight, 150-250 build hours, ~$3k total build cost, drawn for the Rotax 277/377
engine class, with the largest and most active builder community of any design surveyed (a
dedicated Facebook "Adventures & Builders" group plus long-running EAA/HomeBuiltAirplanes forum
threads). Per the brief's §4 recommendation, it beats Aerolite 103 or CGS Hawk Ultra here because
its structure matches open-ez's existing CadQuery/tube-fabrication assumptions and it has the
shortest credibly-sourced build-hour number in the survey.

## Why it fits plans-as-code

open-ez's `AircraftComponent` base class and SSOT config pattern (`config/aircraft_config.py`)
were built for the Long-EZ's composite/foam geometry, but the pattern generalizes: parametric tube
lengths, gusset plate dimensions, and drill-hole positions are exactly the kind of dimension that
should derive from one config rather than being hand-drawn per build. Bolted aluminum tube is also
a materially simpler CadQuery problem than foam-core wing lofting — no airfoil spline interpolation,
no hot-wire G-code, just tube-and-plate solids and hole patterns. That makes the Affordaplane a
good-sized second exercise for the toolchain: real enough to fly, small enough to finish.

## The Part 103 weight reality

The research brief flags a real gap between the Affordaplane's advertised 254 lb empty weight and
what builders report: one Kitplanes/forum-documented build came in at 258 lb — 4 lb over the legal
limit — with a real engine installed, and a separate Yahoo Group moderator reported stock builds
running "slightly over 350 lb," off the Part 103 reservation entirely (brief §2, Part A row 1,
footnote 30). The airframe itself is not the problem; engine weight is. The Affordaplane was drawn
for the Rotax 277 (65 lb complete with reduction drive), which is out of production — used-market sourcing only.
Closing that weight gap without giving up 25+ hp means favoring the lightest engine class the brief
surveys: Moster-class paramotor 2-strokes (Vittorazi Moster 185 Plus: 25 hp at 31-34 lb complete,
Polini Thor 250: comparable class at ~42 lb) run 30-35 lb lighter than a Rotax 277 for similar or
better power. Neither is a factory-drawn Affordaplane engine — this is this spec's own inference
from the brief's engine table, not a documented build — so the weight roll-up milestone below
checks whether a Moster-class engine plus the airframe's real, modeled structural weight actually
clears 254 lb, before money is spent on an engine.

## First three CadQuery milestones

1. **Fuselage truss as parametric tube+gusset.** Model the bolted-aluminum fuselage truss as a
   CadQuery `AircraftComponent`: tube diameter/wall thickness and gusset plate dimensions as SSOT
   config fields, joint positions derived rather than hard-coded, matching
   `config/aircraft_config.py`. Output STEP + DXF (gusset plates as laser-cut parts), per open-ez's
   existing manufacturing-output convention.
2. **Wing rib and spar.** Simpler than Long-EZ's foam-core wing — no airfoil spline smoothing
   needed unless the Affordaplane's wing section requires it (the brief doesn't specify the
   airfoil; an open item for the Facebook builders group ask below). Parametric rib spacing and
   spar cap sizing as a second `AircraftComponent`.
3. **Weight roll-up gated at 254 lb with engine.** A test, following the existing
   `ComplianceTracker`/pytest pattern, that sums modeled component masses plus a declared engine
   weight and fails past 254 lb — the milestone that tests the Moster-class-engine hypothesis
   against modeled, not advertised, airframe weight. It gates the design, it doesn't just report a
   number.

## What must be bought

The Affordaplane plans themselves, from affordaplane.com. The brief could not find a 2026 plans
price in sources retrieved — an open item, along with a real builder-reported empty weight with an
engine installed. Both should be asked directly in the Affordaplane Facebook builders group before
committing to a spar/tube gauge (brief §5, "A concrete next step for Ryan").

## What must NOT be assumed

**No Affordaplane plans content lives in this repository.** The plans are a paid, copyrighted
product from a third-party designer. This spec and any resulting code reference geometry only by
plan sheet number (e.g., "per sheet 4, gusset plate G-3") once plans are in hand — never by
transcribing dimensions, drawings, or text into config files, comments, or commit messages. This
mirrors the IP boundary open-ez already respects for the Long-EZ's original Rutan plans.

## Relation to sea-ez

sea-ez (Part 103 amphibious flying-boat) and this kickoff share a tube/gusset fabrication library
once both exist: bolted-aluminum-tube joint geometry, gusset plate patterns, and drill-jig
generation are the same CadQuery primitives whether the airframe lands on wheels or water. Building
the Affordaplane's simpler truss first is the de-risking step the research brief recommends (§5)
before sea-ez's hull-adjacent structure needs the same primitives at higher stakes. No code sharing
is proposed here — a natural follow-on once both milestone sets exist to compare.
