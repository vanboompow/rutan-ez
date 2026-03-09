# Comprehensive Review: Safety-Critical Physics & Manufacturing Improvements

> **Status: ARCHIVED -- Review Completed (February 2026)**
>
> This review prompt was created for the `feature/physics-mfg-improvements` branch
> (commit `fbe15f6`), which has since been merged to main. The 4-agent review team
> (physics, test, integration, git-safety) completed their review with all checks passing.
> Retained as a reference for the review methodology and as documentation of known
> limitations identified during that review cycle.

## Instructions for Reviewer

You are reviewing a 1,554-line changeset to **Open-EZ PDE**, aircraft design software for the Rutan Long-EZ (Model 61). This is safety-of-flight code -- errors can produce airframes that kill builders. Your review must be forensic.

**Branch**: `feature/physics-mfg-improvements` (1 commit: `fbe15f6`)
**Base**: `main` (commit `da0c71f`)
**Test suite**: 77 tests (22 pre-existing + 55 new), all passing

### Review Requirements

Apply the following review lenses **independently**, reporting findings under each:

1. **Physics Correctness** -- Every formula must be traceable to a named reference (Anderson, Raymer, Bruhn, Phillips, Schlichting, Bisplinghoff). Check dimensional consistency, sign conventions, unit conversions, and boundary behavior.
2. **Safety Regression** -- No existing behavior may change silently. The 22 pre-existing tests must still exercise the same code paths with identical semantics. Any behavioral shift (even if tests pass) must be flagged.
3. **Code Quality** -- API contracts, error handling, edge cases, naming, encapsulation. No dead code, no unreachable branches, no silent failures.
4. **Test Adequacy** -- Are the 55 new tests actually testing the implementation (not reimplementing the formula in the test)? Are there missing edge cases? Do any tests pass vacuously?
5. **Config Integrity** -- SSOT principle: every number in source code must either derive from `config/aircraft_config.py` or be a mathematical/physical constant with a citation. Flag any magic numbers.
6. **Regulatory Compliance** -- FAA 14 CFR 21.191(g) (51% rule), 14 CFR 23.629 (flutter), AC 20-27G (certification). Are compliance checks correctly gated?

---

## What Was Changed (13 files, +1554 / -53 lines)

### Source Files Modified (7)

| File | Lines Changed | Purpose |
|------|--------------|---------|
| `config/aircraft_config.py` | +79 | Added `FlightConditionParams`, `StructuralWeightParams`, `AeroLimitsParams`, `FlutterParams`; added fields to `GeometricParams`, `ManufacturingParams`, `ComplianceParams` |
| `core/analysis.py` | +242 / -53 | Rewrote `_init_standard_weights()`, `calculate_neutral_point()`, `check_canard_stall_priority()`, `add_fuel()`, `calculate_reynolds()`; added `calculate_envelope_margins()` |
| `core/base.py` | +25 | Added `ComplianceError` exception; compliance gate in `FoamCore.export_gcode()` |
| `core/aerodynamics.py` | +95 | Added `Airfoil.offset_inward()` with TE collapse protection |
| `core/manufacturing.py` | +63 | Enhanced `_apply_kerf_offset()` for per-point arrays; added curvature-based feed modulation, velocity ratio clamping, `calculate_velocity_coupled_kerf()` |
| `core/simulation/fea_adapter.py` | +221 | Added `TorsionSection`, `analyze_torsion()`, `build_wing_torsion_section()`, `FlutterEstimator` |
| `core/__init__.py` | +3 | Added `atmosphere` to lazy imports |

### New Files (6)

| File | Lines | Purpose |
|------|-------|---------|
| `core/atmosphere.py` | 52 | ISA standard atmosphere (troposphere) |
| `tests/test_ssot_weights.py` | 241 | Phase 1: atmosphere, W&B, Reynolds, CG envelope (21 tests) |
| `tests/test_canard_stall_and_downwash.py` | 153 | Phase 2: stall priority, downwash, MAC (10 tests) |
| `tests/test_torsion_flutter.py` | 157 | Phase 3: torsion, flutter, mass balance (12 tests) |
| `tests/test_manufacturing_accuracy.py` | 165 | Phase 4: skin deduction, TE collapse (6 tests) |
| `tests/test_compliance_gate.py` | 111 | Phase 5: compliance gate (6 tests) |

---

## Phase-by-Phase Implementation Details

### Phase 1: SSOT Consolidation & Dynamic W&B

#### 1A: Config-Driven Structural Weights

**Before**: `core/analysis.py:_init_standard_weights()` hardcoded 10 weight items including `"Engine (O-235) 250.0 lb @ 195.0"`.

**After**: Structural weights come from `config.structural_weights` (new `StructuralWeightParams` dataclass). Propulsion weights come from `core.systems.get_propulsion_system().get_weight_items()` with a try/except fallback to hardcoded O-235 values.

**Review focus**:
- Does the fallback in `analysis.py:148-153` produce identical W&B to the old hardcoded list? The old code had engine at FS 195, the fallback uses `fs_firewall + 15.0 = 180 + 15 = 195`. Verify this matches.
- The original had `"Pilot (170 lb)" @ FS 80` and `"Fuel (26 gal) @ FS 127.5"` as hardcoded items. These are NO LONGER in `_init_standard_weights()`. Are they now orphaned, or are they expected to be added via `add_payload()` and `add_fuel()`? **This is a potential silent behavior change.**
- `StructuralWeightParams` default weights: `wing=85, canard=25, fuselage=120, gear=45, electrical=25, instruments=15, interior=20` sum to 335 lb structural. Old code summed to 640 lb including engine/pilot/fuel. The new empty weight (structural + propulsion fallback = 335 + 305 = 640) matches, but pilot and fuel are excluded. **The meaning of "empty weight" has changed.**

#### 1B: ISA Standard Atmosphere

**Implementation** (`core/atmosphere.py`):
```
T = 518.67 - 0.003566 * h_ft                    [Rankine]
p = 2116.22 * (T / 518.67)^5.2561               [lb/ft^2]
rho = 0.002377 * (T / 518.67)^4.2561            [slug/ft^3]
mu = 3.737e-7 * (T/518.67)^1.5 * (518.67+198.72)/(T+198.72)  [Sutherland]
```

**Review focus**:
- Exponent 5.2561 for pressure and 4.2561 for density. Anderson uses `g/(R*L) = 5.2559` and `g/(R*L) - 1 = 4.2559`. The value 5.2561 is used here. **Verify whether the 0.0002 difference matters at 36,000 ft.** At troposphere ceiling, T_ratio = (518.67 - 0.003566*36089)/518.67 = 0.7519. Difference: 0.7519^5.2561 vs 0.7519^5.2559 ≈ negligible (<0.001%).
- No altitude bounds checking. `temperature(40000)` returns negative Rankine. `density(40000)` returns negative density raised to fractional power → **NaN or complex number**. Should there be a clamp at tropopause (36,089 ft)?
- Sutherland constant `_MU_REF = 3.737e-7`. This is NOT the standard Sutherland reference viscosity (which is 1.716e-5 at T_ref=518.67R). This appears to be a pre-combined coefficient: `mu_ref * (T_ref + S) / T_ref^1.5`. Verify: `1.716e-5 * (518.67 + 198.72) / 518.67^1.5 = 1.716e-5 * 717.39 / 11808.7 = 1.042e-6`. That doesn't match 3.737e-7. **Double-check the Sutherland formulation against Anderson Table A.2.**

#### 1C: Reynolds Number

**Before**: `rho = 0.001869`, `mu = 3.637e-7` hardcoded.
**After**: Uses `atmosphere.density(altitude_ft)` and `atmosphere.viscosity(altitude_ft)`.

**Review focus**:
- At 8000 ft, the old hardcoded mu was `3.637e-7`. Does `atmosphere.viscosity(8000)` return a value within 1% of this? The test `test_reynolds_8000ft_regression` checks Re is in range 5.5-6.5M (±8.5% tolerance). **This is too loose for a regression test.** A physics regression should be within 2%.
- Unit conversion: `velocity_fps = velocity_kts * 1.6878`. Standard conversion is 1 knot = 1.68781 ft/s. The value 1.6878 is acceptable (0.0001% error).

#### 1D: CG Envelope

`calculate_envelope_margins()` checks 4 corners: light/heavy pilot × min/max fuel.

**Review focus**:
- `empty_items = [i for i in self._weight_balance.items if i.category not in ("payload", "fuel")]`. This filters by string category. If any code adds items with category typos (e.g., "Fuel" vs "fuel"), they'll be included in empty weight. **Case-sensitive string matching is fragile.**
- `fuel_arm = sw.fuel_arm_in` uses a single arm for all fuel. The Long-EZ has TWO strake tanks with slightly different arms depending on fill level. This is a simplification, not a bug, but should be documented.
- The method accesses `config.propulsion.fuel_capacity_gal` for max fuel but `fc.fuel_reserve_gal` for min fuel. These are on different config objects. Verify both exist with correct defaults.

---

### Phase 2: Canard Stall & Downwash

#### 2A: Effective Stall Angle with Reynolds Scaling

**Formula** (`analysis.py:531-539`):
```python
alpha_stall_canard = degrees(clmax_canard / a_canard) + al.canard_alpha_0L - self.geo.canard_incidence
alpha_stall_wing = degrees(clmax_wing / a_wing) + al.wing_alpha_0L - self.geo.wing_incidence
```

**Review focus**:
- `degrees(clmax / a)` computes `degrees(CL / (dCL/dalpha_rad))` which equals the angle in degrees at which the airfoil reaches CLmax, assuming linear CL-alpha. This is correct for pre-stall regime.
- `al.canard_alpha_0L` is -3.0 degrees. `self.geo.canard_incidence` is -1.5 degrees. So: `alpha_stall_canard = degrees(CLmax/a) + (-3.0) - (-1.5) = degrees(CLmax/a) - 1.5`. The sign of incidence subtraction: a **nose-down** incidence of -1.5 deg means the canard sees 1.5 deg LESS alpha than the aircraft, so it stalls at a HIGHER aircraft alpha. Subtracting incidence (which is negative) adds to alpha_stall. **Verify this is the correct convention for the Long-EZ where canard incidence is negative (nose-down).**
- Reynolds scaling: `clmax_canard = al.canard_clmax * (re_canard / re_ref) ** 0.1`. The exponent 0.1 comes from Raymer Sec. 12.5. For Re_canard ~ 750K and Re_ref = 3M: `(0.75/3.0)^0.1 = 0.25^0.1 = 0.871`. So CLmax_canard = 1.35 * 0.871 = 1.18. **This is a 12.9% reduction. Is 0.1 the right exponent for laminar-flow airfoils (Roncz R1145MS)?** Most references cite 0.05-0.15 depending on the airfoil family. 0.1 is midrange and conservative.
- The approach speed `fc.approach_speed_ktas = 60` is used for Re calculation. But approach speed depends on CLmax, which depends on Re. **This is circular.** The plan acknowledged this ("iteratively") but the implementation uses a fixed approach speed. Flag as a known limitation.

#### 2B: Phillips Downwash with Vertical Separation

**Formula** (`analysis.py:301-305`):
```python
h = self.geo.canard_vertical_offset_in
b_c = self.geo.canard_span
vert_factor = 1.0 / (1.0 + (2.0 * h / b_c) ** 2)
d_eps_dalpha = (2.0 / (math.pi * ar_canard)) * a_canard * vert_factor
eta_canard = 1.0 - d_eps_dalpha
```

**Review focus**:
- Phillips formulation: `d(eps)/d(alpha) = (2/(pi*AR)) * a`. This is the FAR-FIELD downwash derivative. Near the wing (which is ~10 chord lengths behind the canard), the actual downwash is stronger. Phillips Ch. 9 discusses this correction but it's not applied here. **Is the far-field approximation adequate for the Long-EZ where canard-to-wing separation is ~97 inches (< 6 canard chords)?**
- `b_c = self.geo.canard_span` = 147 inches = total span. In the formula `(2h/b_c)`, should `b_c` be semi-span (73.5") or full span (147")? Phillips uses full span in the denominator. Verify against the textbook equation.
- `eta_canard = 1.0 - d_eps_dalpha`. For default values: `d_eps_dalpha = (2/(pi*8.65)) * 4.7 * 0.974 = 0.339`. So `eta = 0.661`. **But the plan says eta ~ 0.815.** This discrepancy needs investigation. The `a_canard` value (~4.7 rad^-1 for AR~8.65) may be different than the plan assumed. **Recompute eta with the actual a_canard from Anderson eq. 5.69 for AR=8.65, sweep_half for the canard.**
- What if `h = 0`? Then `vert_factor = 1.0`, full downwash. What if `h` is very large? `vert_factor → 0`, no downwash, `eta → 1.0`. Both limits are correct.
- `eta_canard` can go negative if `d_eps_dalpha > 1.0`. For very high AR canards, `(2/(pi*AR))*a` could exceed 1. Should there be a clamp: `eta_canard = max(0.0, 1.0 - d_eps_dalpha)`?

#### 2C: Canard MAC for AC

**Formula** (`analysis.py:249-254`):
```python
canard_taper = self.geo.canard_tip_chord / self.geo.canard_root_chord
mac_canard = (2/3) * self.geo.canard_root_chord * (1 + canard_taper + canard_taper**2) / (1 + canard_taper)
ac_canard = self.geo.fs_canard_le + 0.25 * mac_canard
```

**Review focus**:
- The MAC formula is correct for a trapezoidal planform.
- `ac_canard = fs_canard_le + 0.25 * mac_canard`. This assumes the canard MAC LE is at `fs_canard_le`. For a swept canard, the MAC LE is aft of `fs_canard_le` by `y_mac * tan(sweep_LE)`. **The sweep correction is missing.** For the canard with 13.5° sweep and `y_mac = (span/6) * (1+2*taper)/(1+taper)`: `y_mac = (73.5/3) * (1+2*0.794)/(1+0.794) = 24.5 * 1.443 = 35.4"`. Sweep offset: `35.4 * tan(13.5°) = 35.4 * 0.240 = 8.5"`. **This is a significant error: canard AC should be 8.5" further aft than computed.** This would shift NP aft by several inches.
- Compare: the wing MAC LE calculation at line 179-181 DOES include sweep correction via `y_mac_wing * tan(sweep_LE)`. The canard calculation OMITS this. **Inconsistency.**
- Note: `config.geometry.canard_arm` property at line 131-135 uses `canard_root_chord * 0.25` (not MAC). This property is used elsewhere (VSP bridge). It was NOT updated. **Another inconsistency.**

---

### Phase 3: Torsional Stiffness & Flutter

#### 3A: Bredt-Batho GJ

**Formula** (`fea_adapter.py:569-572`):
```python
ds_over_t = sum(ds / t for ds, t in self.perimeter_segments)
return 4.0 * self.enclosed_area_sq_in ** 2 * self.shear_modulus_psi / ds_over_t
```

**Review focus**:
- The formula is correct (Bruhn Ch. A6).
- `build_wing_torsion_section()` at line 602-603: `spar_height = mat.spar_cap_plies * mat.uni_ply_thickness`. This is the spar cap thickness (17 * 0.009 = 0.153"), NOT the spar height. The spar height should be the airfoil thickness at the spar location (~10% of chord). The next line: `d_box_depth = chord_in * 0.10` is the correct spar height. But the `if d_box_depth < spar_height` guard is backward -- `chord * 0.10` for a 50" chord is 5.0", which is always >> 0.153". **The guard is dead code.** Not harmful, but misleading.
- Segment 1: `(d_box_depth, skin_t * 2)` -- front spar web is 2× skin thickness (inner + outer skin). This assumes the spar web is only skin, no additional glass. For the Long-EZ, the spar web has additional BID layup. **Conservative (under-estimates GJ).**
- Segment 4: `(d_box_depth, spar_cap_w)` -- aft closure using spar cap width (3.0") as "thickness". This models the spar cap as a solid 3" thick closure. **This is wrong.** The aft closure of the D-box is NOT 3" thick solid material. It's the spar cap (0.153" thick, 3" wide). The Bredt-Batho `ds/t` for this segment should use the spar cap thickness, not width. Using width (3.0") makes this segment contribute almost nothing to ds/t (d_box_depth/3.0 ≈ 2.27), which INFLATES GJ. Should be `(d_box_depth, spar_height)` where spar_height = 0.153". This would make ds/t = 5.0/0.153 = 32.7 instead of 2.27, significantly reducing GJ.

#### 3B: Flutter Estimator

**Bending frequency** (`fea_adapter.py:650-662`):
```python
omega_h = (3.52 / L ** 2) * math.sqrt(EI / mu)
```

**Review focus**:
- Coefficient 3.52 is for a cantilevered beam 1st mode. Correct reference: Blevins, "Formulas for Natural Frequency and Mode Shape", Table 8-1.
- `mu = wing_weight_lb / g / (2.0 * half_span_in)`. Weight is divided by `2 * half_span_in = wing_span`. But `wing_weight_lb = 85` is total wing weight. So `mu = 85 / 386.1 / 316.8 = 6.95e-4 slug/in`. This distributes the full wing weight over the full span. But L = `self.span_in = wing_span / 2 = 158.4"` (semi-span). So we're computing the frequency for a half-wing cantilever with mass density = total_wing_weight / full_span. **This is correct** (each half carries half the total mass distributed over half the span, giving the same linear density).
- `EI = beam.section.modulus_psi * beam.section.inertia`. What are these values? They come from `BeamFEAAdapter()` which uses the spar cap section from config. **EI is for the spar cap only, not the full wing box.** This under-estimates EI, which under-estimates bending frequency, which is conservative for flutter (flutter speed estimate is driven by torsion frequency).

**Torsion frequency** (`fea_adapter.py:664-685`):
```python
omega_theta = (math.pi / (2.0 * L)) * math.sqrt(GJ / I_theta)
```

- `I_theta = mu * self.chord_in ** 2 / 12.0`. This is the polar mass moment for a uniform rod of width = chord. For an airfoil, this is a crude approximation. Mass is concentrated in skins and spar, not uniformly distributed. **Could overestimate I_theta by 2-3×, which would underestimate torsion frequency by sqrt(2-3), underestimating flutter speed.** Check if this makes the analysis non-conservative.

**Flutter speed** (`fea_adapter.py:687-701`):
```python
v_flutter_fps = omega_theta * b / math.pi
```

- This formula `V = omega_theta * b / pi` is a rough heuristic, not a standard reference formula. Theodorsen's classical flutter analysis is much more involved (requires reduced frequency, mass ratio, etc.). **Cite the specific source for this simplified formula.** If it's from the plan, the plan should have cited it. If it's a custom heuristic, label it as such with a safety factor discussion.

#### 3C: Control Surface Mass Balance

- This is purely a config declaration check. It reads `config.flutter.elevon_mass_balance_pct` and flags if < 100%. **The implementation is correct for its stated purpose.** No physics computation, just a policy check.

---

### Phase 4: Manufacturing Accuracy

#### 4A: Skin Thickness Deduction (`Airfoil.offset_inward()`)

**Implementation** (`aerodynamics.py:231-324`):
- Splits coordinates at `argmax(x)` (TE)
- Computes finite-difference normals at each point
- Offsets upper surface down, lower surface up by `t_norm = thickness/chord`
- TE collapse protection: walks from TE toward LE, caps where upper ≤ lower

**Review focus**:
- Normal direction: For upper surface (`direction=-1`), `nx = -(-dy/length) * (-1) = -dy/length`. For a point near mid-chord where dy/dx > 0 going toward TE, dy > 0, dx > 0, so tangent = (dx, dy), normal = (dy/length, -dx/length) * (-1) = (-dy/length, dx/length)... **Manually trace through one point to verify the offset goes INWARD, not outward.** An outward offset would produce foam cores that are LARGER than the OML, causing the finished wing to be oversized.
- `offset_surface(xu, yu, -1)` for upper: with `direction = -1`, `ny = dx / length * (-1)`. At the upper surface trailing section where dx > 0 (going right toward TE) and dy < 0 (curving down toward TE), `ny = dx/length * (-1)` is negative. This moves the upper surface DOWN. For the upper surface, inward = down. **Correct.**
- TE collapse: The walk starts from the TE end of both surfaces. Upper goes `nu-1-i` (backward from TE), lower goes `i` (forward from TE = its starting point). When `yu_off[u_idx] <= yl_off[l_idx]`, it collapses. **But these are comparing y-values at different x-stations.** The upper TE point has x near 1.0, and the lower TE point also has x near 1.0, so for i=0 they're at the same x. For i=1, upper is one step back from TE and lower is one step forward from TE. If points are uniformly spaced, they're at similar x-stations. **Approximately correct but not exact.**
- After collapse, `new_coords` reconstructs with reversed lower surface (`xl_off[::-1], yl_off[::-1]`). This reversal converts TE→LE ordering back to LE→TE for `AirfoilCoordinates`. **Verify AirfoilCoordinates expects LE→TE for x_lower.**
- `n_points=len(xu_off) + len(xl_off) - 1`: The `-1` accounts for the shared TE point. **But after truncation, do xu_off and xl_off still share a TE point?** After collapse at index `cut_u/cut_l`, the upper ends at `xu_off[cut_u-1]` and lower starts at `xl_off[cut_l]`. These were set to the same avg_y but may have different x-values. **The n_points calculation may be off by 1.**

#### 4B: Hot-Wire Feed Rate & Kerf

**Curvature detection** (`manufacturing.py:260-269`):
```python
v1 = pts_root[i] - pts_root[i - 1]
v2 = pts_root[i + 1] - pts_root[i]
cross = v1[0] * v2[1] - v1[1] * v2[0]
dot = np.dot(v1, v2)
angle = abs(np.arctan2(cross, dot))
```

**Review focus**:
- This correctly computes the turning angle between consecutive segments. The 2D cross product is correct.
- `i + 1 < n_points` guard exists, but the ternary falls back to `pts_tip[i + 1] - pts_tip[i] if i + 1 < n_points else v1`. **On the last iteration where `i + 1 >= n_points`, `v2 = v1` means `angle = 0`, no slowdown.** This silently skips the TE, which may actually be a high-curvature point. Minor but notable.
- `feed_rates[i - 1] *= 0.6` can be applied TWICE (once for root curvature, once for tip). If both root and tip have high curvature at the same station, `feed_rates[i-1] *= 0.6 * 0.6 = 0.36`. This stacks below the 0.3 clamp, so the clamp catches it. **But the intent was 40% slowdown, not 64% slowdown.** Should use `min()` instead of `*=`.

**Velocity-coupled kerf** (`manufacturing.py:289-305`):
```python
return base_kerf * np.sqrt(base_feed / np.maximum(feed_rates, 0.1))
```
- Formula is physically motivated: dwell time ~ 1/feed, heat penetration ~ sqrt(time).
- `np.maximum(feed_rates, 0.1)` prevents division by zero. At feed = 0.1 in/min: kerf = base * sqrt(4.0/0.1) = base * 6.32. **A 6× kerf widening at near-zero feed seems excessive.** Should the floor be higher (e.g., `base_feed * 0.3`)?

---

### Phase 5: Compliance Gate

**Implementation** (`base.py:204-216`):
```python
credit = config.compliance.total_builder_credit
if config.compliance.strict_compliance and credit < 0.51:
    raise ComplianceError(...)
elif credit < 0.51:
    import logging
    logging.warning(...)
```

**Review focus**:
- `total_builder_credit` sums all values in `task_credits` dict. Default sum = 0.84. **Should the threshold be 0.51 or 0.50?** FAA 14 CFR 21.191(g) says "major portion" which is interpreted as >50%. Using 0.51 adds 1% margin. Acceptable.
- The `import logging` inside the `elif` block is a conditional import. Works, but PEP 8 recommends top-level imports. Minor style issue.
- Tests in `test_compliance_gate.py` don't actually call `export_gcode()`. They manually replicate the compliance check logic inline. **These tests don't verify the actual gate in base.py.** They test the formula `if strict and credit < 0.51: raise`, not the integration. A test that instantiates a `FoamCore` subclass and calls `export_gcode()` would be stronger (but requires CadQuery mocking).

---

## Specific Items to Verify by Hand

### Hand Calculation #1: ISA Density at 8000 ft
```
T = 518.67 - 0.003566 * 8000 = 518.67 - 28.528 = 490.142 R
T_ratio = 490.142 / 518.67 = 0.9450
rho = 0.002377 * 0.9450^4.2561
log(0.9450) = -0.02456
4.2561 * (-0.02456) = -0.10455
rho = 0.002377 * e^(-0.10455) = 0.002377 * 0.9007 = 0.002141?

Wait -- 0.9450^4.2561:
  ln(0.9450) = -0.05657
  4.2561 * (-0.05657) = -0.24079
  e^(-0.24079) = 0.78616
  rho = 0.002377 * 0.78616 = 0.001869

✓ Matches expected 0.001869 slug/ft³
```

### Hand Calculation #2: Canard MAC
```
cr = 17.0, ct = 13.5, taper = 13.5/17.0 = 0.7941
MAC = (2/3) * 17.0 * (1 + 0.7941 + 0.7941²) / (1 + 0.7941)
    = (2/3) * 17.0 * (1 + 0.7941 + 0.6306) / 1.7941
    = (2/3) * 17.0 * 2.4247 / 1.7941
    = (2/3) * 17.0 * 1.3514
    = (2/3) * 22.974
    = 15.316 inches

Test expects ~15.35. Hand calc gives 15.316. Δ = 0.034. Within tolerance.
```

### Hand Calculation #3: Bredt-Batho GJ for 10x5 tube
```
A = 50 sq in
ds/t: 2*(10/0.05) + 2*(5/0.05) = 400 + 200 = 600
GJ = 4 * 50² * 1e6 / 600 = 4 * 2500 * 1e6 / 600 = 10e9 / 600 = 16,666,667 lb-in²
```
Test verifies this exactly. ✓

### Hand Calculation #4: Stall angle (default config)
```
a_canard (AR=8.65, sweep_half ≈ 8°):
  Anderson 5.69: a = 2π*8.65 / (2 + sqrt(4 + 8.65²*(1+tan²(8°))))
  tan(8°) = 0.1405, tan²(8°) = 0.01974
  denom = 2 + sqrt(4 + 74.82*(1.01974)) = 2 + sqrt(4 + 76.30) = 2 + sqrt(80.30) = 2 + 8.961 = 10.961
  a_canard = 54.35 / 10.961 = 4.959 rad⁻¹

CLmax_canard (Re-scaled):
  At 60 KTAS, 8000 ft: rho = 0.001869, mu = viscosity(8000)
  V = 60 * 1.6878 = 101.3 fps
  MAC_canard = 15.32 in = 1.277 ft
  Re_canard = 0.001869 * 101.3 * 1.277 / mu(8000)

  Need mu(8000). Sutherland: mu = 3.737e-7 * (490.14/518.67)^1.5 * (518.67+198.72)/(490.14+198.72)
  (490.14/518.67)^1.5 = 0.9450^1.5 = 0.9170
  (717.39)/(688.86) = 1.0414
  mu = 3.737e-7 * 0.9170 * 1.0414 = 3.737e-7 * 0.9550 = 3.569e-7

  Re_canard = 0.001869 * 101.3 * 1.277 / 3.569e-7 = 0.2418 / 3.569e-7 = 677,600

  CLmax_canard = 1.35 * (677600 / 3e6)^0.1 = 1.35 * (0.2259)^0.1
  (0.2259)^0.1 = e^(0.1*ln(0.2259)) = e^(0.1*(-1.4875)) = e^(-0.14875) = 0.8618
  CLmax_canard = 1.35 * 0.8618 = 1.163

alpha_stall_canard = degrees(1.163 / 4.959) + (-3.0) - (-1.5)
                   = degrees(0.2346) - 1.5
                   = 13.44 - 1.5
                   = 11.94 deg

For wing (similar exercise with wing dimensions):
  ...exercise left for reviewer...
  Expected margin: ~4-6 deg (canard stalls first)
```

---

## Known Limitations Acknowledged in Implementation

1. **Approach speed is fixed** at 60 KTAS for Reynolds calculation (circular dependency not resolved)
2. **NP datum issue**: `fs_wing_le = 133` may use wrong datum, causing NP ~45" aft of published value
3. **Canard AC sweep correction missing** (see Phase 2C review above)
4. **Far-field downwash** used where near-field may be more appropriate
5. **Spar-cap-only EI** in flutter analysis (conservative)
6. **Uniform chord mass distribution** for I_theta (crude approximation)
7. **Flutter speed formula** is a simplified heuristic, not Theodorsen classical analysis

---

## Files to Read (in order)

```
config/aircraft_config.py          # SSOT config (read FIRST for context)
core/atmosphere.py                 # ISA atmosphere model
core/analysis.py                   # Physics engine (largest change)
core/simulation/fea_adapter.py     # Torsion + flutter (lines 545-766)
core/aerodynamics.py               # offset_inward() (lines 231-324)
core/base.py                       # ComplianceError + gate (lines 16-18, 184-216)
core/manufacturing.py              # Kerf + feed rate (lines 167-305)
core/__init__.py                   # Lazy import addition
tests/test_ssot_weights.py         # 21 tests
tests/test_canard_stall_and_downwash.py  # 10 tests
tests/test_torsion_flutter.py      # 12 tests
tests/test_manufacturing_accuracy.py     # 6 tests
tests/test_compliance_gate.py      # 6 tests
```

## Running the Tests

```bash
cd /Users/ryanstern/rutan-ez/.worktrees/physics-mfg-improvements
source .venv/bin/activate
python3 -m pytest tests/ -v   # All 77 should pass
```

---

## Checklist for Reviewer Sign-Off

- [ ] All formulas traceable to named references with correct dimensional analysis
- [ ] No silent behavioral changes to existing code paths
- [ ] No magic numbers without config backing or physical constant citation
- [ ] Edge cases handled (zero inputs, extreme altitudes, self-intersecting offsets)
- [ ] Tests verify actual implementation, not reimplemented formulas
- [ ] Unit conversions verified: knots↔ft/s, inches↔feet, radians↔degrees, slugs↔lb
- [ ] Sign conventions consistent: incidence, washout, sweep, normal directions
- [ ] Canard AC sweep correction addressed (flagged as missing)
- [ ] Bredt-Batho aft closure segment uses correct dimension (flagged as questionable)
- [ ] Compliance gate tests exercise actual export_gcode() code path
- [ ] Sutherland viscosity coefficient verified against Anderson Table A.2
- [ ] eta_canard value sanity-checked against plan expectation (0.815 vs computed)
- [ ] Flutter speed formula has adequate citation or safety factor discussion
