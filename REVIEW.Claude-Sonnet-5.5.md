# Hydrological Audit & Red-Team Report: nnyflood

**Reviewer**: Claude Sonnet 5.5 · **Date**: 2026-10-18 · **Mode**: read-only (no repo file modified except this report)
**Commit audited**: `02ba87c` (worktree clean after `verify_all.py`; `git status --short` empty)

**Commands executed (all exit 0)**
| Command | Result |
|---|---|
| `python catalog.py check` / `audit` | 105 catalogue paths exist; 33 docs registered |
| `python tools/verify_all.py` | 4/4 steps pass (catalog 0.05 s · integrity 2.94 s · lint 1.03 s · `pytest tests/` 25.5 s) |
| `pytest tests/test_thai_language_lint.py tests/test_legal_compliance.py tests/test_privacy.py` | 18 passed |

> **Scope honesty.** I did a code-level and artefact-level audit of the files named in Dimensions 1–7. I did **not** re-derive the Khun Dan 22-year baseline, the 461-reservoir stress index, ERA5 rarity, ML Model v1 (Ridge, 11 features), the waterchart overlay, or read PDF pages. I did not render the HTML reports visually. Every finding below cites a file/line or a command I ran.

---

## 1. Executive Summary

- **Overall Scientific & Engineering Reliability**: **Medium for Pillar 1 (self-disclosing, with caveats), Low–Medium for Pillars 2–3 (several headline numbers rest on synthetic, hard-coded, or mislabeled inputs).**
- **Key System Strengths**
  1. Unusually honest self-disclosure in code/JSON (`hydraulic_1d_routing_summary.json` caveats, `compound_flood_risk.py:37-41`, `goal7_counterfactual_simulation.py:157-164`). Several findings below are admissions that never reach the headline text.
  2. Strong mechanical quality gates: all 140 tests pass, SHA-256 integrity, lint, catalogue. Arithmetic I recomputed independently reproduces (CRF, levelised cost, Manning capacity, buffer hours, DEM hypsometry).
  3. Correct methodological instincts: purge of train rows whose target lies in the test window (`goal6_l3_coastal_model.py:245`), common sample across leads, tide-aware persistence baseline, rank check, and the Tha Chang gate-control "spurious correlation" case.
- **Critical Vulnerabilities & Limitations**
  1. **Goal 7 headline claims are not computed results**: the 2011/2026 "counterfactual" runs on `2200 + 2486·sin^1.3 + noise` hydrographs; the "Route 305 tipping point at +3.20 m" is a hard-coded literal that equals the DEM median; the dead storage (21.0 MCM) is not reproducible from the stated geometry.
  2. **Coastal ML and harmonics headline vs. evidence**: the "−53 %" RMSE gain is against a baseline that is *worse than persistence*; against the fair baseline the model loses by 41–45 % at +24/+48 h. The harmonics findings text claims "outstanding skill" while its own table shows negative R² and negative skill.
  3. **Stale/undocumented values across layers**: the audit brief's own numbers (73.6→35.9 cm, 51.2 %, 57.1 %, −1.9 %, 5 benchmarks, 4 harmonic stations) do not exist in any artefact; Goal 7 report builders hard-code metric literals despite the canonical-contract rule.

---

## 2. Findings Matrix

| ID | Severity | Component / Target | Root Cause Summary | Recommended Action |
|---|---|---|---|---|
| F-01 | **Critical** | `analysis/goal7_counterfactual_simulation.py:112-146` | 2011 and 2026 hydrographs are synthetic sine + noise; reported "4,394.5 MCM / 38.8 % / 0.53 m" and "prevented overbank 100 %" are properties of the assumed shape and a hand-set `dq_dh=1100` | Retitle as *illustrative scenario*, remove from headline/TLDR, or drive with real C.2/C.13/S.26 daily series |
| F-02 | **Critical** | `analysis/goal7_ongkharak_2d_depression.py:72`, DEM 30 m | "+3.20 m Route 305 crown" is a literal with no survey source; +3.20 ≈ DEM median (3.1986) so "50.1 % of district" is true by construction | Obtain crown survey/LiDAR for the road; relabel as "median-elevation level"; propagate DEM uncertainty |
| F-03 | **High** | `analysis/goal6/l3_coastal_summary.json:54-55,62,85,108` | Headline 53.0 % uses an "uncoupled" baseline (79.6 cm) that is worse than persistence (63.6 cm). Vs tide-aware persistence: +23.4 % at +6 h, **−41.3 % / −45.1 %** at +24/+48 h | Lead with tide-aware baseline; state coupled model is not useful beyond ~+6–12 h |
| F-04 | **High** | `analysis/goal6/l3_coastal_harmonics_findings.md:18-25` ← `goal6_l3_coastal_harmonics.py:271-275` | Narrative is hard-coded and contradicts the table (R² −0.293/−0.285, skill +2.9/−3.0/−2.7/−4.2 %); "+-3.0 %" format bug | Generate the conclusion from the numbers; delete "โดดเด่น/ใช้งานได้" claims |
| F-05 | **High** | `analysis/goal7_operational_economics.py:24-61,112-137` | 38.3 d/yr = 1,988 MCM ÷ 51.84 assumes *all* Pasak flow is divertible; `days_extreme` capped at arbitrary 80 (true 130); 1,970 vs 1,988 MCM inconsistent; alternatives' unit costs are unsourced literals | Source or drop the alternatives table; divide by actually divertible volume from routed series |
| F-06 | **High** | `report/goal7_build_public.py:364,405,407,516`; `goal7_build_policy_brief.py:62,66,129,176,196-197`; `goal7_build_academic.py:281,289,290` | Metric literals hard-coded in builders (violates AGENTS contract rule 2 spirit; test does not scan Goal 7) | Render from `analysis/goal7/canonical.json`; extend scan test to goal7 builders |
| F-07 | **High** | `analysis/hydraulic_1d_routing_summary.json` (`rating_sensitivity.ny1b`), `hydraulic_1d_routing.py:111-120` | Composite rating at Ny.1B is **non-monotonic**: Q(10.60 m)=666.3 > Q(11.00 m)=578.4 cms; "bankfull 666.3" is method-dependent (divided: 893.0, +34 %; flat slope: 488.9, −27 %) | Report capacity as a range; fix conveyance method (divided/monotone) before quoting 666.3 |
| F-08 | **High** | `hydraulic_1d_routing.py:154`, summary `muskingum_x_note`, `grid_convergence` | Model is Muskingum–Cunge, not Saint-Venant: no momentum, no backwater, no floodplain storage, no lateral inflow. Raw X<0 on 96.7 % of probe flows, clamped to 0; peak varies 591.7→638.9 cms (+8 %) with `n_sub`; sim 3.25 h vs observed H→H 9.0 h | Describe as lumped hydrologic routing; do not attribute 9.0 h to floodplain detention (untested) |
| F-09 | **Medium** | `analysis/compound_flood_risk.py:46-48` | `c1=0.132`, exponent 1.28 fit exactly through 2 points (2 params, 2 constraints) → zero validation; no Q×tide term | Label as 2-point scenario, not "backwater curve"; fit on 2011/2021/2022 telemetry |
| F-10 | **Medium** | `compound_flood_risk.py:92-121` vs brief | Code has **4** benchmarks, none of 2021/2022/2024; brief claims 5 classified events | Add real events or correct the brief/reports |
| F-11 | **Medium** | `goal6_l3_coastal_harmonics.py:73-124,134,183-188` | Harmonics fitted at one station (CPY015) only; GLF002 and C.29 appear nowhere; no purge of train rows whose target is in test (lead 24/48); phases referenced to arbitrary `t0`; 4 constituents on ~80 d cannot separate K1/P1 | Fit each station with proper Greenwich-epoch harmonic analysis (e.g. UTide); purge by `t+lead`; or drop the "4 stations" claim |
| F-12 | **Medium** | `goal6_l3_coastal_model.py:82-93,196` | iid bootstrap on 226 autocorrelated hourly points (CI too narrow); `CPY015` is an upriver city-reach gauge ~10 km from C.12, so "tide" shares river signal; GBDT +6 h 76.7 cm vs linear 37.4 cm (trees cannot extrapolate to the flood peak) | Block bootstrap; test with GLF001 (true mouth); report GBDT as extrapolation failure |
| F-13 | **Medium** | `analysis/goal7_operational_economics.py:348-351,355-359`; `goal7_blocks.py:542` | Dead storage 21.0 MCM has no calculation; stated geometry (b=48 m, 7 m deep, side slope 1.5–2.5) gives total 55.7–62.3 and 2 m pool **13.9–14.4 MCM**; "geotechnically necessary 2.0 m" has no source; flat-pool volume ignores bed profile (−4.5 m coast vs +5.36 m embankment) | Document cross-section; derive volumes in code; cite geotech basis or label "assumption" |
| F-14 | **Medium** | `goal7_operational_economics.py:58-62` | 30-yr life for earthworks (CRF 0.0806) vs 50 yr (0.0725 → 6.15 THB/m³); flat OPEX 519 MB; benefit side absent, so "THB/m³ diverted" compares unlike things | Present life-cycle sensitivity (life 30/50/100) and add benefit/avoided-damage metric |
| F-15 | **Medium** | `analysis/goal6_pasak_24y_baseline.py:25-26,55,66,123-137,185` | "Exceeded upper rule curve" implemented as `peak ≥ constant 871.5`; counts partial 2569; compares 17/24 (Pasak) vs 9/22 (Khun Dan) with different denominators; record peak 1,177.22 > `MAX_CAP` 1,036.16 unexplained; silent literal fallbacks in `.get(..., 1177.22)` | Use the seasonal URC; align year windows; explain >MAX_CAP; remove fallback literals |
| F-16 | **Medium** | `compound_flood_risk.py:74-81` / thresholds | 2.70 m critical vs crest 2.80–3.00 leaves 0.10–0.30 m with model error ±0.12 m (self-reported); fine as watch level but "critical" label mixes crest and freeboard | Add uncertainty bands to matrix cells |
| F-17 | **Low** | `analysis/goal7_counterfactual_simulation.py:123,142`; `:224,237` | "Tidal efficiency" never below 0.80 (never a lockout); chart line `#27ae60` contrast **2.87:1** < 3.0 WCAG for data marks | Add zero-discharge tidal windows; darken to e.g. `#1b7f3b` (5.07) |
| F-18 | **Low** | `docs/REVIEW_PROMPT_EN.md:26,85` | Audit brief carries numbers that exist nowhere (`grep 73.6` hits only the brief) | Regenerate the brief from canonical JSON |
| F-19 | **Low** | `tools/verify_all.py:67-73` | Step 2 accepts exit code 2 ("missing files") as pass | Fail or warn explicitly when data are missing |

---

## 3. Deep-Dive Technical Findings

### [F-01] Counterfactual 2011/2026 diversion is a synthetic exercise
- **Location**: `analysis/goal7_counterfactual_simulation.py:112-118,127,139,88-89`; `analysis/goal7/counterfactual_simulation_summary.json`
- **Evidence**:
  - `inflow_2554 = 2200 + 2486·sin(t)^1.3 + N(0,45)`; `inflow_2569 = 1600 + 1380·sin(t)^2.2 + N(0,25)`. Metadata itself says `SYNTHETIC` (`:157`).
  - Output: 2011 / 600 cms → diverted **4,394.5 MCM**, share **38.8 %**, peak cut 582.9 cms → `582.9/1100 = 0.5299 ≈ 0.53 m` (my recomputation).
  - With the canal, **83 of 122 days still exceed the 2,600 cms "safe" limit** (vs 102 without): only 19 days saved. Downstream peak remains ~4,103 cms.
  - `safe_cap_ayutthaya=2600` is "ไม่มีเอกสารอ้างอิงใน repo" (`:126`). `dq_dh=1100` is "สมมติฐานที่เขียนไว้" (`:85`); the file's own comment says valid range gives 0.12–0.97 m.
  - 2026 600 and 1,000 cms cases are identical (215.8 MCM) so the expansion is untested.
  - Chart title `goal7_counterfactual_simulation.py:240` asserts "ป้องกันน้ำล้นตลิ่งได้สมบูรณ์" and legend `:237` "คุมน้ำให้อยู่ในตลิ่ง 100%" on a synthetic wave.
- **Critique**: The share and stage reduction are functions of the chosen peak/base ratio and a guessed stage–discharge slope, not of hydrology. The diversion rule at `:54-55` also over-diverts (full capacity once `q_in > safe+500` regardless of excess). No lockout, backwater, or storage behaviour is modelled even though Dimension 5.3 and ONEP item 1.6 (`goal7_operational_economics.py:251-252`) raise exactly that.
- **Proposed solution**: (a) Use observed daily C.2/C.13/S.26 for 2554 as inputs; (b) replace `dq_dh` with a surveyed Ayutthaya rating and report a 600–5,000 range; (c) add an outlet constraint `q_out ≤ f(tide)` that reaches 0; (d) rewrite chart titles to "scenario"; (e) never headline 0.53 m without the range.

### [F-02] Route 305 "tipping point" equals the DEM median; crown elevation unsourced
- **Location**: `analysis/goal7_ongkharak_2d_depression.py:20,35-72`; `goal7/ongkharak_2d_depression_summary.json` (`route305_overtopping`)
- **Evidence** (my command on `dem_30m.npy` + district mask):
  - `shape=(2132,2277)`, 570,144 valid cells = **513.13 km²** (30 m cells); percentiles `[5,25,50,75,95] = [2.26, 2.81, 3.1986, 3.75, 5.51]`.
  - Stage → area/volume: 2.70 → 97.7 km²/38.3 MCM · 2.95 → 173.0/71.8 · **3.20 → 257.0/126.2** · 3.45 → 323.3/198.9 · 3.70 → 377.1/287.1.
  - Area gradient at 3.2 m: 27.6 km² per 0.1 m. A ±0.5 m vertical error moves the "tipping" area by 100–150 km² and volume by ~70 MCM.
  - `grep "305" analysis/goal7` finds no road crown elevation; only bridge width in `eia_structs.json:725-726`. The value 3.20 appears first at `:72` and in a text description `:104`.
- **Critique**:
  1. The input is **Copernicus 30 m DEM (a surface model)**, not "1 m LiDAR/FABDEM" as the brief states. Vertical error in flat paddy/urban terrain of ±2–4 m is typical; datum is EGM2008 vs Thai "รทก." with no stated offset.
  2. A bathtub fill (`ong_valid <= h`) fills all cells below the level regardless of hydraulic connectivity, road/canal embankments, or drainage. It cannot show "overtopping"; Route 305 is not in the model at all.
  3. The 50.1 % share at 3.20 is the median, i.e. tautological.
  4. Question 2 in the docstring (agreement with Sentinel-1 at +2.35 m) is never computed; the "41.5 km² / 17.8 MCM" strings at `:90,97` are literals.
  5. Stage from gauge TNy10 is a channel level applied as a flat pool across a 513 km² district.
- **Proposed solution**: survey the road crown (RID/DOH profile) and use the lowest saddle along the road; use an embankment-burned LiDAR DEM with connectivity (flood-fill from outlet); present area/volume as bands over a DEM-error distribution; compute the S-1 agreement or delete the claim.

### [F-03] Coastal-model headline versus a baseline that loses to persistence
- **Location**: `analysis/goal6/l3_coastal_summary.json:50-118`; `analysis/goal6_l3_coastal_model.py:193-196,252-258`
- **Evidence**:
  | Lead | persistence | tide-aware persistence | linear base | linear coastal | gain vs base | vs tide-aware (95 % CI) |
  |---|---|---|---|---|---|---|
  | +6 h | 63.6 | 48.9 | 79.6 | 37.4 | 53.0 % | **+23.4 % [13.3, 32.8]** |
  | +24 h | 21.8 | 14.3 | 21.0 | 20.2 | 4.0 % | **−41.3 % [−66.5, −19.5]** |
  | +48 h | 39.1 | 23.4 | 37.2 | 34.0 | 8.6 % | **−45.1 % [−69.7, −23.3]** |
  GBDT: 88.8→76.7 (+13.5 %), 38.3→38.5, 48.2→52.4 (−8.7 %).
- **Critique**: The uncoupled model (no tide) cannot capture a ~1 m semi-diurnal/diurnal tidal oscillation in C.12, so a 53 % improvement is the cost of omitting the dominant forcing, not forecast skill. The coastal linear model is **worse than a tide-aware persistence by 41–45 % at ≥24 h**. Note: the tide-aware baseline at `:257` uses *observed* tide at `t+lead`, which is more information than the model uses (only `tide0`), so the comparison is not even apples-to-apples; a fair coupled model should consume harmonic-predicted tide at `t+lead`, which is public information.
- **Proposed solution**: add `astro_tide(t+lead)` as a feature (from the harmonic module); report skill only versus tide-aware persistence; withdraw "ผสานทะเลช่วย" claims for ≥24 h.

### [F-04] Harmonics narrative contradicts its own table
- **Location**: `analysis/goal6/l3_coastal_harmonics_findings.md:18-25`; generator `goal6_l3_coastal_harmonics.py:266,271-275`
- **Evidence**: table: +6 h R² −0.293, +12 h −0.285, skill **+2.9 / +-3.0 / +-2.7 / +-4.2 %**; narrative: "ทักษะการพยากรณ์โดดเด่นที่ระยะ +12 ชม. และ +24 ชม. … ต่ำกว่าฐานเทียบเดิมอย่างมีนัยสำคัญ" and "พร้อมนำไปใช้งานในระบบเฝ้าระวังระดับน้ำ กทม.". The narrative strings are literals independent of results. Report 4 caption (`report/goal6_build_report4_draft.py:307`) quotes R² = 0.826 at +24 h while the same row shows model RMSE 0.218 m > persistence 0.212 m (R² of a persistent series is trivially high).
- **Critique**: Evidence-contradicting conclusions presented as validation; also contradicts F-03. Harmonic purge omitted (`:183-188`): a row at 2026-09-18 with `lead=48` trains on a target inside the test window. Test counts differ (262/261/274/274) from the L3 sample (226), so the two tables are not comparable.
- **Proposed solution**: generate sentences from computed skill sign; add the same purge as `goal6_l3_coastal_model.py:245`; fix the `+-` formatting.

### [F-05] 38.3 days/year utilisation and 6.81 THB/m³ rest on an upper-bound volume
- **Location**: `goal7_operational_economics.py:24-61,112-137`
- **Evidence**: `flood_season_mean_mcm=1988.0` ÷ `51.84` = **38.35**; `diverted_volume_mcm=1970.0` (`:61`) ÷ 51.84 = 38.0; `days_flood = min(6741/51.84, 80.0)` → capped (uncapped 130.0; flood-season max 5830/51.84 = 112.5) while the report says "60–80 วัน" (`goal7_build_public.py:405`). Alternatives table (`:112-137`: 0.50–1.20, 1.10–1.80, 1.50–2.50 THB/m³) carries no citation.
- **Critique**: (1) It treats the entire S.26 flood-season flow as diversion volume, ignoring that S.26 is only one source, that the canal can only take water when downstream stage demands it, and that the days metric is a volume-equivalent, not operating days. (2) Utilisation of a flood-control asset is normally low; low volume-equivalent utilisation says nothing on avoided damages. (3) Using mean of a skewed series. (4) Costs of "retention basins" per m³ are compared to a different service.
- **Proposed solution**: derive diverted volume from the simulated operating rule on the real series (F-01), report distribution (P10/P50/P90) and cite alternative costs or remove them.

### [F-06] Goal 7 builders hard-code metrics
- **Location**: see matrix. Example: `report/goal7_build_policy_brief.py:62` (`13,416`), `:66` (`6.81`), `:196` (`12,897`); `goal7_build_public.py:364` (`126.22`, `257.2`, `50.1`).
- **Critique**: AGENTS.md requires canonical-driven numbers; `test_goal6_consistency` only scans Goal 6. A change in `canonical.json` (which `goal7_ongkharak_2d_depression.py:116` rewrites on every run) will silently desynchronise reports. Note the same script **writes into canonical.json** (`:113-118`), contradicting "never hand-edit canonical".
- **Proposed solution**: template these sentences from JSON; add Goal 7 scan to the consistency test; separate the writer of canonical.

### [F-07] Non-monotonic rating at Ny.1B undermines "666.3 m³/s"
- **Evidence** (`hydraulic_1d_routing_summary.json`): composite Q at 6.86/10.60/11.00 m = 191.2 / **666.3** / **578.4**; divided = 225.3 / 893.0 / 1,009.1; flat-slope composite 488.9 / 424.4. The summary's `ny1b_hydraulics` records `peak_q_cms 675.3` at stage 11.0 m, i.e. above the composite value for that stage. Ny.7: composite 617.4 at 8.21 m vs divided 842.8.
- **Independent check** (Manning, Ny.7 at S=0.00035, n=0.0437, A=606.9 m²): R≈3.7 m → V≈1.02 m/s → Q≈620 cms ✓ consistent with 617.4, so the arithmetic is sound **given composite conveyance**; the issue is the method choice. Composite roughness on a compound section reduces Q when overbank area is added (the classic discontinuity), producing the Q decrease above 10.6 m.
- **Critique**: n was calibrated at Ny.7 only (metadata `manning_n_note`), then applied unchanged to Ny.1B with 1.86× steeper slope. Bankfull "capacity" therefore has a 489–893 cms spread. Also RID's declared bank level is 8.81 m versus the surveyed crest 10.60 m (`ny1b_hydraulics.note`): the statement "peak 0.4 m above bankfull" depends entirely on that definition.
- **Proposed solution**: use divided-channel (monotone) conveyance with per-section n or report range 489–893; show 8.81 m as the RID level.

### [F-08] The "1D hydrodynamic" model is Muskingum–Cunge without backwater or floodplain storage
- **Evidence**: `hydraulic_1d_routing.py:132` ("Muskingum-Cunge"), `:146-162` (only inflow at Ny.1B, no lateral term), `:154` (`x_param = max(0.0, min(0.45, x_param))`), summary `x_param_probe`: `x_raw_min −3.364`, `negative_share 0.967`; `grid_convergence`: q_peak 591.7 / 613.0 / 627.5 / 638.9 and RMSE_Q 126.4→131.1 with n_sub 6/12/24/48; `rmse_stage_cm 106.0`, `stage_bias_cm −80.1`; `model_scope_note`: no downstream boundary (Kgt.30).
- **Critique**:
  1. Muskingum–Cunge solves a kinematic/diffusion approximation with a fixed storage relation; it cannot represent backwater (the Dimension 1.1 question) or floodplain detention. With `X=0` it is a linear reservoir cascade; the JSON's phrase "เดินเป็นคลื่นแพร่" is imprecise. Negative raw X means the sub-reach length is shorter than the Cunge criterion `Δx ≥ Q/(B·S·c)`; refining the grid worsens it and explains non-convergence (peak +8 %).
  2. Sim 3.25 h over 18.3 km ⇒ celerity ≈ 1.56 m/s. For Manning with the stated slope/section at 600 cms, V≈1.0–1.4 m/s and `c≈1.3–1.67·V` ≈ 1.3–2.3 m/s, so 3.25 h is physically *coherent with a no-storage channel* — and ~2.8× faster than the observed H→H 9.0 h. The academic report (`น้ำท่วมนครนายก2569_วิชาการ.html:339`) correctly says the two numbers "เทียบกันตรง ๆ ไม่ได้", but the brief's reading ("9.0 h indicates overland detention") is **not supported by any model run**; the model has no floodplain. The real finding is: the model overestimates wave speed or the stage peaks lag because of rating/gauge effects (Q peaks lead H by 6.5 h at Ny.1B and **−8.75 h** at Ny.7).
- **Proposed solution**: state "hydrologic routing, calibrated at a single station"; add a storage-cell (floodplain) test and a Q→Q observed lag; if backwater matters implement dynamic wave (e.g., HEC-RAS/1D Preissmann) with Kgt.30 boundary.

### [F-09/F-16] Compound-flood formula: two points, no interaction, undefined uncertainty
- **Location**: `compound_flood_risk.py:35-49,74-81,92-121`
- **Evidence** (recomputed): `0.132·2.5^1.28 = 0.4265` → stage 2.51 at tide 2.00 ✓; `0.132·3.5^1.28 = 0.656` → 3.04 at tide 2.30 ✓. Both quoted check points are reproduced *exactly because they are the two fit constraints* (docstring `:38-40`). `∂H/∂tide = 1` (additive). 2026 stage 2.36 vs observed 2.24 (+12 cm). 2011: `Q=3750, tide=2.35` → 3.15 m, "ไม่มีแหล่งอ้างอิง" (JSON limitations).
- **Critique**: Dimensional consistency is fine (c1 in metres, Q normalised), but exponent 1.28 is within the 1.3–1.7 range for a rating-type law and **cannot be validated** with two parameters and two points. At Q→0 the term vanishes, meaning the river contributes no level at low flow, which is not physical for a tidal river with channel slope. Additive tide ignores flood-ebb damping of tide amplitude by high discharge (a well-documented interaction). The 4 benchmarks do not include 2021/2022/2024 (F-10); the brief claims classifications for them.
- **Proposed solution**: fit `H_C12 = a + b·tide + c·Q^m + d·Q·tide` on C.12/CPY015/C.29A multi-year telemetry; carry ±1σ residual into the risk bands.

### [F-11/F-12] Harmonics and coupling design flaws
- Station coverage: `grep GLF00` returns GLF001/GLF003 only; **GLF002 and C.29 are absent** from `goal6_l3_coastal_harmonics.py`; only `4_CPY015` is decomposed (`:130,147`). The brief's "4 key estuarine stations" is unsupported by code.
- Extracted amplitudes (`findings.md:9-12`): M2 0.430 m, S2 0.295, K1 **0.603**, O1 0.413. Diurnal dominance is plausible for the upper Gulf of Thailand, but these are the *apparent* signals at a gauge inside the river (non-tidal river level and seasonal level included in the 80-day window, unresolved P1/S1/K2). Phase is relative to the first training timestamp (`:75-76`), not Greenwich, so it cannot be compared with amphidromic literature. I cannot certify physical consistency from these outputs.
- CPY015 (Bangkok Bridge) is in the city reach; C.12 is a few km upstream. A feature from CPY015 shares river signal with the target, so improvement is spatial autocorrelation rather than independent boundary forcing. GLF001 (the true mouth) is available (`l1_findings.md:33`) but not used.
- Imputation counters (`l3_coastal_summary.json:34-44`): `h6` imputed in 358/1,317 rows (27 %), `h3` 195, `h1` 86 — substituting `h0` for missing lags biases the lag-difference features toward zero.
- Leakage: **none found for rain** (previous-day NASA POWER, `:175-179`; matches `rain_note`); purge present for the coastal model. The brief's phrase "causal trailing 24 h rainfall" is inaccurate — it is a previous-calendar-day total from a single point. Selection effect: rows require a target at t+48 (`:148`), mildly favouring windows with complete data.

### [F-13] Active storage "reality"
- Arithmetic reproduces: `34.4e6 / 600 / 3600 = 15.93 h` ✓.
- Geometry: with b=48 m, depth 7 m, side slope 1:1.5–1:2.5, L=135.9 km, my calculation gives total **55.7–62.3 MCM** (matches 55.4 only at m≈1.46) but the 2 m pool is **13.9–14.4 MCM**, not 21.0 MCM (`goal7_operational_economics.py:350`). Using 14 MCM, active = ~41.5 MCM, buffer ≈ 19 h.
- The 15.9 h figure is the time to fill with zero outflow; the canal will normally be flowing at design discharge so "buffer" is an emergency-pump-failure metric. The report wording "จะเต็มความจุภายในเวลาไม่ถึง 1 วัน" is arithmetically right under that assumption but not an overflow prediction.
- **Geotechnical claim**: no geotechnical source in the repo (`grep dead_storage` → only SWOC dam data). A *minimum* water level mainly protects against rapid drawdown; on a "floating" canal with embankment crest +5.36 m (`:305`), seepage/piping and high-water loading are at least as relevant. 2.0 m is an assumption and should be labelled one.

### [F-14] Life-cycle economics
- Verified independently: CRF(7 %, 30) = 0.08059 → 12,897 + 519 = **13,416.5 MB/yr** → **6.81 THB/m³** ✓; 9 % → 8.17 ✓; 12 % → 10.35 ✓.
- Sensitivity (my run): 7 %: life 50 y → 6.15; 100 y → 5.96. 9 %: 7.67 / 7.58. So the choice of a 30-year life inflates unit cost ~11 % at 7 %. Construction period (7–8 y per ONEP outcome, `:230`), interest during construction, sediment dredging, and land-price escalation are not in OPEX. Social discount rate "เกณฑ์มาตรฐาน สศช." is stated at 7 % while the comparison also shows 12 %; the policy text should name which is the official base case.

### [F-15] Dam-governance comparison definitions
- `NORMAL_CAP=871.5` constant (`:25`), test `q >= NORMAL_CAP` (`:55`, `>=` includes equality), peak by calendar year including partial 2569 (data through `2026-10-04`). A rule curve is seasonal; "upper rule curve exceedance" ≠ "over normal storage at any day of year". `AGENTS.md` already records 17/22, 16/22, 20/22 as three definitions; here a 4th (17/24, `:185`) appears next to Khun Dan 9/22.
- Record peak `1,177.22` MCM (135.1 %) exceeds `MAX_CAP 1,036.16` (the stated maximum surcharge pool, `:26,112`) by 141 MCM, while metadata calls the region above 1,036.16 an "emergency freeboard buffer" (`:113`). Either `DMD_QUse_curr` is a different quantity or the dam was operated beyond its documented pool; the code neither flags nor explains it.
- The conclusion `:190` ("ไม่ใช่ความผิดปกติเชิงบริหาร แต่เป็นหน้าที่ตามการออกแบบ") is an inference from frequency, not a documented operating mandate; this is a legal-sensitive assertion about an agency (see F-20 below). Silent `.get(..., 1177.22)` fallbacks (`:123-137`) would hide a missing-data failure.

### F-20 (Low, legal framing) — from Dimension 7.3
Tests pass (`test_legal_compliance.py`, `test_privacy.py`). Spot concerns: (a) `goal7_build_policy_brief.py:176` heading "การลงทุนแสนล้านเพื่อใช้งาน 38 วันต่อปี" is a rhetorical frame resting on F-05; (b) the claim at `goal6_pasak_24y_baseline.py:190` asserts agency intent ("หน้าที่ตามการออกแบบ") without citing the operating manual. Both target the system, not persons, but need provenance labels (fact/interpretation/assessment) per `docs/LEGAL_REVIEW.md`.

### ONEP/คชก. items (Dimension 6.3)
`goal7_operational_economics.py:141-282` lists 16 round-1 items: 1.1, 1.10, 1.11, 1.12, 1.16, 3.1.5, 3.1.6, 3.2–3.3, 5.4, 5.5, 6.2, 6.3, 7.6.2.2, 13.3, 16.1, 8.6–8.7 (= 16 ✓). I did not open the source PDF, so I **cannot** confirm the wording against letter ทส 1010.6/2233; the data in `analysis/goal7/ocr_findings.json`/`eia_structs.json` are OCR with typographical corruption (e.g. `ระบายน า`), which is fine for provenance but not verbatim. Also note rounds 2 and 3 are shown with **fewer** objections (3 each) and round 3 outcome says คชก. approved in พ.ค. 2568 (`:280`); the public/policy builders emphasise round 1 (rejection) more than the final approval — check balance per LEGAL_REVIEW rule 3 (show positive/current status).

---

## 4. Verified Invariants (Passed Spot-Checks)

| Item | Method | Result |
|---|---|---|
| CRF, annual cost, unit cost at 7/9/12 % | Python recomputation | 0.08059 / 0.09734 / 0.12414 → 13,416.5 MB, 6.81 / 8.17 / 10.35 ✓ |
| 15.9 h buffer | `34.4e6/600/3600` | 15.93 h ✓ (arithmetic only) |
| 51.84 MCM/day at 600 cms | arithmetic | ✓ |
| Ny.7 bankfull 617.4 cms | Manning, n=0.0437, S=0.00035, A=606.9 | ≈620 cms ✓ (composite method) |
| Ongkharak area 513.13 km², 126.2 MCM at 3.20, 257.0 km² | Direct DEM histogram | ✓ (reproduces; see F-02 on meaning) |
| 0.53 m stage reduction | `582.9/1100` | 0.5299 ✓ (arithmetic) |
| C.12 check-points (2,500→2.51; 3,500→3.04) | Direct formula | ✓ (but are fit constraints) |
| Purge of train rows by target in coastal model | `goal6_l3_coastal_model.py:245` | present; `n_train` 1,087/1,078/1,066 vs `n_test` 226 ✓ |
| Previous-day rain feature | `:175-179` | causal, no look-ahead ✓ |
| Catalogue, integrity, language lint, legal, privacy | commands above | pass |
| Chart colours in compound matrix | WCAG calc: `#1b7f3b` 5.07, `#8a6d00` 4.92, `#b34700` 5.50, `#a12020` 7.66 | ≥3.0 ✓ |
| Counterfactual line colours | `#2980b9` 4.30, `#c0392b` 5.44, `#d35400` 4.17 ✓ · `#27ae60` **2.87 ✗** | see F-17 |

---

## 5. Information Gaps & Required Field Data

1. **Route 305 crown profile and nearby saddles** (DOH/RID survey), 1 m LiDAR for Ongkharak, and a datum offset (EGM2008→รทก.).
2. **Observed Q series** for 2554/2564/2565/2567 at C.2, C.13, S.26, C.29A to replace synthetic hydrographs and to fit the C.12 stage law with multi-year telemetry.
3. **Tha Chang gate logs** and Ny.1B–Ny.7 tributary inflows/lateral losses to calibrate and test floodplain detention.
4. **Geotechnical design** for the canal embankment (soft clay strength, drawdown criteria) justifying 2.0 m minimum water depth; canal cross-section and bed profile.
5. **Outlet-works design** (gate/pump capacity vs tide) to model lockout at the Gulf end.
6. **Pasak rule-curve table** (seasonal URC/LRC) and field definition of `DMD_QUse_curr`, plus an explanation of 1,177.22 > 1,036.16 MCM.
7. **Primary-source PDF pages** for letter ทส 1010.6/2233 and EIA tables 2.5.3-2 (p. 2-92), 2.3.2-3 (p. 2-60): not opened in this audit.
8. Harmonic constituents with Greenwich phase at GLF001/GLF002/GLF003/C.29 from long (≥1-year) records.

---

### Suggested priority order
1. F-01, F-02, F-04 (claims that contradict or lack evidence).
2. F-03, F-05, F-07, F-08 (headline framing of results).
3. F-06, F-10, F-15, F-18 (consistency and provenance).
4. F-09, F-11–F-14, F-16, F-17, F-19, F-20.
