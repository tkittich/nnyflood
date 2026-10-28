# Comprehensive System Audit Prompt (English) — Multi-Pillar Red-Team Review

> **How to use**: Copy the complete markdown text below this block and provide it to an independent external AI auditor (e.g., Claude 3.5 Sonnet, GPT-4o / OpenAI o1, Gemini 1.5 Pro) or a senior hydraulic/data science peer reviewer with access to this repository.  
> **Last Updated**: October 28, 2026 (round 9: reference-date sensitivity now covers all six basins with a per-orbit reference-date table in Report 3; L3 learned-model results rendered in Report 4 §7b; goal-7 retired ledger moved to data; new Dimension 14 on JSON-to-HTML rendering gaps; stricter evidence rules after round 8) | Covers all 3 Pillars (six numbered reports — 1, 2, 3, 4, 7, 8 — plus the Policy Brief), Astronomical Tidal Harmonics, 2D Compound Risk Matrix, 2D Hypsometric Ongkharak Basin Tipping Point, Active Storage Reality, 39y Operational Economics, ONEP EIA Critiques, **plus the 19–27 Oct additions (third batch: goal-6 Sentinel-1 stage-2 reference scenes re-paired by relative orbit with a pre-registered audit and a GISTDA cross-check, along-channel reach length, own radar series for Chachoengsao; second batch: tide timestamp rule, multi-year harmonics, anchored compound matrix, 1-D sub-reach sensitivity, 3-D model rebuilt on the continuous surface, road×valley crossings, verification badges, two-layer literal gate): DEM bias correction + satellite waterline tests, the rain-driven 2-D Ongkharak model, whole-basin Bang Pakong / Chachoengsao analysis (Report 3 §4.7, labelled exploratory), GISTDA daily-product handling, and the OCR toolchain (Typhoon vs Indra OCR, VLM pilot)**.

---

# Independent Audit & Red-Team Review: Hydrological Investigation Project `nnyflood`

## 1. Auditor Role & Mission Objective

You are an **Independent Senior Hydraulic Engineer and Lead Data Science Auditor (Red-Team Reviewer)** conducting a rigorous, evidence-based peer review of the **nnyflood** hydrological investigation codebase and technical reports.

The project investigates catastrophic flooding in Thailand through empirical data, remote sensing, and physical hydraulic modeling across **3 Core Pillars (7 Goals)**:
1. **Pillar 1 (Goals 1–5): Nakhon Nayok River Basin (Sep 26–29, 2026 Flash Flood)**  
   - Attribution of upstream rainfall band vs. Khun Dan Prakan Chon Dam release (rain : dam share; the headline split and its lag band are in `analysis/canonical_numbers.json` → `values.dam_share` and `analysis/attribution_share.json`).
   - 1D Hydrodynamic Routing model (`analysis/hydraulic_1d_routing.py`) routing flood waves with Muskingum–Cunge (weight X clamped to 0, i.e. a linear-reservoir cascade — not a full Saint-Venant solve) from Ny.1B to Ny.7 (18.3 km key reach, 43 km full basin).
   - Cross-sectional rating curves, levee-crest capacity, and simulated peak travel time along the modelled reach (values are in `analysis/hydraulic_1d_routing_summary.json` and `analysis/canonical_numbers.json`; none is quoted here). The modelled reach length (18.3 km) is **not** a surveyed channel chainage: the straight-line distance between the two station coordinates is about 7.8 km (a sinuosity of 2.35 would be needed) — open item R7-23. The gap between observed peak lag at Ny.7 and the simulated travel time is attributed to overland/floodplain detention, which is an interpretation, not a measurement. Sub-reach sensitivity (n_sub 1/2/3/6/12/24/48; headline kept at 12 by the pre-registered rule `docs/ROUTING1D_SUBREACH_PREREG.md`) is in the grid-convergence block of the summary.
   - Gate-Control vs Routing Trap case study at Tha Chang regulator (`report/build_expert_report.py` Section 6.5.1c).
   - Khun Dan 22-year operational baseline (premature-filling days ahead of the median: see `analysis/canonical_numbers.json` → `values.khundan_22y.headline_metrics.year_2026_anomaly`) and stress analysis of 6 medium reservoirs.
   - Machine learning stage prediction (Model v1: 11 features, Ridge regression; error figures are in `analysis/canonical_numbers.json` → `model_v1` — do not rely on any number quoted in this prompt).
2. **Pillar 2 (Goal 6): 6 National River Basins & 2011 Mega-Flood Benchmark**  
   - Multi-reservoir comparative operation across 24 major dams (EGAT hydroelectric vs. RID irrigation), including the Pa Sak (RID) vs. Mae Klong (EGAT) 22-year governance benchmark (Pasak: three documented definitions in `goal6/canonical.json → pasak_year_counts` — above upper rule curve on any day 20/22 years, in Aug–Sep 16/22, above normal storage 17/24 years; vs EGAT dams maintaining dedicated flood headroom).
   - National stress index covering the medium reservoirs across Thailand (figures such as mean storage percent and the number of reservoirs over 100% are in `analysis/goal6/canonical.json`; this prompt quotes none of them).
   - 46-year ERA5 rainfall rarity and recurrence interval modeling.
   - L3 Coastal-Coupled Model (`analysis/goal6_l3_coastal_model.py`): Coupling Chao Phraya River stage at C.12 Samsen with Bangkok Bridge tidal telemetry (CPY015). Skill figures (RMSE, improvement vs persistence and vs a tide-aware persistence baseline, bootstrap intervals, usable-hours coverage) are in `analysis/goal6/l3_coastal_summary.json` and the goal6 canonical; the 10-minute CPY015 series is sampled at minute :00 only (rule fixed 25 Oct 2026 — earlier numbers used the :50 record and are retired; the fix changed the sign of one headline comparison, so trust no figure quoted outside the canonical).
   - Astronomical Tidal Harmonics decomposition (`analysis/goal6_l3_coastal_harmonics.py` $\rightarrow$ `l3_coastal_harmonics` in the goal6 canonical): 10 constituents with nodal factors (f, u) fitted on the multi-year CPY015 record (data before 20 Sep 2026; rule `docs/HARMONICS_REFIT_PREREG.md`), evaluating 1–3 day tidal forecast skill on a common sample across leads.
   - Compound Flood Risk Matrix (`analysis/compound_flood_risk.py`): Non-linear backwater interaction between upstream river discharge and storm surge, with 4 benchmark rows: 2011 (inputs estimated, unsourced), 2026 observed, and 2 hypothetical scenarios. Since 26 Oct a second, **anchored** matrix (observed stage plus a measured tide gain with a band across periods; rule `docs/COMPOUND_ANCHORED_PREREG.md`) sits beside the original in Report 4 §8.1; the original equation is kept unchanged and is still uncalibrated.
3. **Pillar 3 (Goal 7): Chao Phraya 2 Bypass Floodway Project**  
   - 135.9-km Pasak–Gulf of Thailand new diversion canal (total Chainat–Pasak–Gulf floodway network, design discharge $600\ m^3/s$).
   - Embankment profile analysis: elevated dike (+3.8 to +6.4 m MSL, 3.2–4.8 m above ground across Nakhon Nayok plain; the earlier 2.5–4.8 m range is retired — see `analysis/goal7/retired.json`).
   - 2D Hypsometric Stage-Area-Volume Analysis of Ongkharak Depression (`analysis/goal7_ongkharak_2d_depression.py`): results are reported as a **range across four height surfaces** (Copernicus raw, FABDEM raw, the original stepped FABDEM bias table, and a continuous monotone correction learned from DEMPro 5 m windows — rule fixed before the run in `docs/DEM_CORRECTION_PREREG.md`). No surface is called most accurate; Ongkharak lies outside the DEMPro windows so the transfer uncertainty is reported from the leave-one-window-out results. Single values (e.g. a median) must always name their surface; check the sensitivity table and `range_across_dems` in the canonical.
   - Canal Active Storage Reality (`analysis/goal7_operational_economics.py`): Total static volume $68.5\text{ MCM}$ (derived from approved EIA cross-section $504\text{ m}^2 \times 135.9\text{ km}$), with a 2.0 m dead storage pool (an analyst assumption, $15.5\text{ MCM}$ for the 51.0 m bed width, 1:3 inner slopes), leaving **$53.0\text{ MCM}$** usable volume ($\approx 24.5\text{ hours}$ to fill an empty canal at $600\text{ m}^3/s$; a canal already at design level has only the freeboard volume as buffer). Legacy draft values ($55.4\text{ MCM}$ total / $41.6\text{ MCM}$ active) and the discredited 54.5 m bed-width reading ($16.2$ / $52.3$ / $24.2$) have been retired.
   - S.26 39-Year Operational Profile: Transferred flood volume averages $1,970\text{ MCM/yr}$; canal operates at full capacity equivalent to only $38.3\text{ days/year}$ (10.5% annual utilization, idle $>10\text{ months/year}$); the 1,970 MCM/yr denominator has no traceable source (R7-02), and a 50-year life sensitivity sits in the economics block.
   - Life-Cycle Economics & Bang Ban Comparison: annualized capital + OPEX and the levelized unit cost of diverted floodwater at 7/9/12% discount rates are in `analysis/goal7/canonical.json` → `operational_economics.lifecycle_economics` (the variant using the 519 MB/yr OPEX is a labelled alternative, not the headline). Risk of delay and cost escalation is benchmarked against Bang Ban–Bang Sai via `bangban_bangsai_case` (scenario durations and budgets are canonical values; quote none from this prompt).
   - ONEP EIA rejection history (3 committee rounds): letter ทส 1010.6/2233 dated **18 Feb 2562** (the earlier "14 Feb" was a retired error), ทส 1010.6/18346 dated 25 Nov 2564, ทส 1009.6/6077 dated 18 Mar 2567 — dates verified on page images; row citations ("หัวข้อ N ข้อ M") checked against the complete Typhoon OCR of the letters (R7-17, `tests/test_rejection_letter.py`); round 1 has 16 rows, rounds 2–3 three rows each (selected items, not exhaustive).
   - Nuclear Facility & Critical Infrastructure Proximity: Thailand Institute of Nuclear Technology (TINT) Ongkharak research reactor at a map pin supplied by the project owner, $14.1221^\circ\text{ N}, 101.0275^\circ\text{ E}$ (not a surveyed boundary; 5.78 km east of km 57 of an unofficial canal alignment).
   - Cross-drainage structure counts: the project documents give **different counts** (87 / 99 / 130 under different definitions) and the 87 figure could not be reproduced from its source; the quantity registry marks it *disputed* (`analysis/goal7/quantities.json` → `structure_count`). Check that every report states the definition it uses.
   - ONWR Water Chart GIS layer overlay (`analysis/goal7_waterchart_overlay.py`): 16.8 km (47%) spatial intersection with designated floodway zones.
   - Counterfactual Hydraulic Simulation (`analysis/goal7_counterfactual_simulation.py`): an ILLUSTRATIVE simulation on synthetic sine hydrographs (stored under `illustrative_only` in goal7 canonical; not rendered in any report; its outputs must not be treated as results).
   - **DEM validation (new)**: waterline tests of four height surfaces against Sentinel-1 flood edges (`analysis/goal7_dem_waterline_test.py`) and yearly GISTDA flood polygons (`goal7_dem_gistda_waterline_test.py`); mitrearth 77-province + national packs (non-commercial licence), GISTDA 15-year flood frequency along the canal corridor, SLR vs canal, DEMPro vs EIA ground line.
   - **Rain-driven 2-D hydraulic model (new)** (`analysis/goal7_ongkharak_hydraulic_2d.py`, `goal7_event_rain.py`; rerun 25 Oct on four height surfaces under the pre-registered rule `docs/HYDRAULIC2D_RERUN_PREREG.md`): local-inertial shallow-water solver on a ~90 m grid; Ny.7 discharge inflow (project rating curve), channel-bed conditioning, 48-station daily rain (IDW), lumped infiltration f and drainage k. Overlap scores, precision, over-prediction ratio, a per-run water budget (closure error), and an inflow x0.8/x1.2 sensitivity are in the canonical `ongkharak_hydraulic_2d`; no number is quoted here. Check whether the best (f, k) still sits at the grid edge and that the report says so only if it does.
   - **Whole-basin Bang Pakong / Chachoengsao analysis (new)** (`analysis/goal7_bangpakong_chachoengsao.py`, `goal7_bangpakong_fetch.py`, `goal7_gistda_stac_daily.py`): basin framing via HydroBASINS lev08, elevation-zone vs province variance explained, gauge-above-bank durations (thaiwater 10-min series), GISTDA 30/7/3/1-day snapshots and **daily per-scene STAC products** (available only to 17 Oct; none for 16 Sep–1 Oct). Also rendered in Report 3 §4.7 as an explicitly *post-hoc/exploratory* section (`report/goal6_bp_downstream.py`, canonical key `bp_downstream`).
   - **Document toolchain (new)**: Typhoon-OCR (GPU) vs **Indra OCR (CPU)** vs Unlimited-OCR layout vs a vision-language-model pilot (`docs/OCR_WORKFLOW_V2.md`, `analysis/goal7_indra_text_eval.py`, `goal7_ocr_accuracy_vs_textlayer.py`, `goal7_vlm_pilot.py`, `goal7_ocr_v2.py`). All OCR/VLM outputs are drafts; canonical numbers are supposed to come from the PDF text layer or from page images read by hand with saved evidence hashes.

### Your Target:
1. **Rigorous Defect Identification**: Identify errors, physical inconsistencies, mathematical flaws, data leakage, unwarranted assumptions, discrepancies with canonical datasets, and legal/defamation risks across all code, data pipelines, and generated reports.
2. **Intra-Report & Cross-Report Consistency Audit**: Systematically scan for conflicting numbers, contradictory statements, or metric drift *within each individual report* and *across corresponding reports* (Public vs. Academic vs. Policy Brief).
3. **Strategic & Consistency Recommendations**: Provide actionable high-level suggestions on overall project methodology, hydraulic realism, and institutional mechanisms to permanently enforce cross-report data consistency.  
Do not offer generic compliments or superficial stylistic edits. Report concrete technical findings backed by exact `file:line` references, raw data citations, or reproducible terminal executions.

---

## 2. Mandatory Rules of Engagement

1. **Strictly Read-Only**: Do not modify files, do not commit or push to git, and never execute destructive commands (`git reset`, `git clean`, `rm -rf`).
2. **No Hallucinations or Phantom References**: Every identified finding must cite a verified `path/to/file:line`, a specific PDF page, or the exact output of a command you executed.
3. **Read first**: `HANDOFF.md` (latest section), `docs/GOAL7_PLAN.md` §32–34 and the pre-registration documents (`docs/*_PREREG.md` — check commit order: each rule must be committed before the run it governs), `docs/OCR_WORKFLOW_V2.md`, `docs/REMOTE_SENSING_APIS.md`, `docs/OFFLINE_DATA_BACKLOG.md` (R6/R7 statuses), `analysis/goal7/gaps.json`, `docs/DATA_REQUEST_PACK.md` (what is blocked on outside data), `docs/reviews/TRIAGE_ROUND7_2026-10-25.md` and `docs/reviews/TRIAGE_ROUND8_2026-10-27.md` (findings already triaged, including what was fixed, what sits in the backlog, and what was deliberately declined — if you re-find one, say whether it is still reproducible; do not present it as new). Items declined on purpose and recorded in round-8 §13: the legacy-unreviewed literal-allowlist entries (published prose of Reports 1–2) and three clean-ups inside the frozen 2-D analysis chain; re-raise them only with a new argument.
3b. **Evidence discipline (added after round 8)**: three of four round-8 reviews contained claims that did not match the repository. Known false claims — check any similar assertion against the repo before making it: ONEP letter numbers such as `1007/5823` (the reports cite ทส 1010.6/2233, ทส 1010.6/18346, ทส 1009.6/6077); a 1.2 km reactor distance (map-pin distance is in the canonical, about 5.8 km); an exponential-decay form of the compound-flood equation (the code uses a power law in Q); Sentinel-1 orbits "135/69" (the orbits used are in `s1_ref_sensitivity*.json`); and "the 60% rain share appears nowhere in reader text" (it does, in Reports 1–2). Rules: (a) if you cannot open `report/*.html`, say so and exclude every finding that depends on rendered text — do not infer absence from a builder; (b) quote the number and the command or `file:line` that produced it; (c) never give a score, grade or confidence figure you did not derive; (d) a finding that sits only in your own reading of an English summary of the project, not in a file, is not a finding.
3a. **Validate Using Concrete Commands**:
   - Run the unified 4-step verification runner: `python tools/verify_all.py` (all steps must pass).
   - Check the project knowledge catalog: `python catalog.py check` and `python catalog.py audit`.
   - Run full test suite: `pytest` (expected ≈ 330 passed; if Windows subprocess tests fail with `WinError 50`, rerun with stdin detached).
   - Compare all metrics against canonical ledgers: `analysis/canonical_numbers.json`, `analysis/goal6/canonical.json`, and `analysis/goal7/canonical.json`.
4. **Inspect Generated HTML Reports Directly**:
   - Report 1 (Public): `report/น้ำท่วมนครนายก2569_ประชาชน.html`
   - Report 2 (Academic): `report/น้ำท่วมนครนายก2569_วิชาการ.html`
   - Report 3 (Regional): `report/ระลอกปลายกย2569.html`
   - Report 4 (National Benchmark): `report/ชุดเทียบมาตรฐาน2554.html`
   - Report 7 (Chao Phraya 2 Public): `report/คลองเจ้าพระยา2_ประชาชน.html`
   - Report 8 (Chao Phraya 2 Academic): `report/คลองเจ้าพระยา2_วิชาการ.html`
   - Policy Brief (White Paper): `report/สมุดปกขาว_เจ้าพระยา2.html`
5. **Legal & Defamation Compliance (`docs/LEGAL_REVIEW.md`)**:
   - Critiques must target **water management systems, operational rules, design assumptions, and physical infrastructure**, never individual public servants or personal culpability.
   - Ensure complete absence of personally identifiable information (PDPA compliance).
6. **Language & Formatting Integrity**:
   - Official HTML reports are in Thai (`report/*.html`). Quote Thai text verbatim when citing sources; your audit findings should be in English.
7. **Where to save your report**: write it to `docs/reviews/REVIEW.<model>.<commit>.md` (not the repo root — `tests/test_tool_registry.py` counts root `*.md` files and turns `verify_all.py` red).

---

## 3. Targeted Audit Dimensions

### Dimension 1: 1D Hydrodynamic Routing & Local Hydraulics (Nakhon Nayok River)
* **Target Files**: `analysis/hydraulic_1d_routing.py` $\rightarrow$ `analysis/hydraulic_1d_routing_summary.json`, `report/build_expert_report.py`
* **Audit Checklist**:
   1. Does the Muskingum–Cunge (X = 0) routing accurately represent wave attenuation and backwater effects along the 18.3 km Ny.1B–Ny.7 reach?
   2. Are the bankfull discharges ($666.3\ m^3/s$ at Ny.1B and $617.4\ m^3/s$ at Ny.7) mathematically sound given the surveyed cross-sections (`data/23_rid_swoc/raw/rid_telemetry_cross_sections.json` and `data/19_rid_cross_sections/`) and Manning’s equation?
   3. Is the simulated travel time ($3.25\text{ h}$ over the 18.3 km modelled reach) physically coherent with the surveyed bed slope ($S_0 \approx 0.00035–0.00065$) and Manning's roughness coefficient ($n \approx 0.0437$)? Assess how overland/floodplain detention accounts for the observed $9.0\text{ h}$ lag at Ny.7.
   4. Evaluate the Gate-Control vs Routing Trap case study at Tha Chang: does the analysis correctly separate gate operation effects from upstream river routing?
   5. Sub-reach sensitivity: do the non-clamped variants (n_sub 1/2/3) and the kernel/X diagnostics change the conclusion, and does the report keep the headline at the pre-registered value rather than the best-looking one?
   6. The reach length (18.3 km) versus the 7.8 km straight line between stations: is this disclosed wherever a travel time is quoted? A pre-registered measurement from the mitrearth river layer (`docs/REACH_LENGTH_PREREG.md`, `analysis/goal7/reach_length.json`) fell inside the ±20% agreement band, so the model was left unchanged — is the 'unsourced 18.3 km' wording present in Report 2 §6.6.4, and is the measured value (a generalised line, probably short) never presented as a surveyed chainage?

### Dimension 2: Estuarine Machine Learning & Astronomical Tidal Harmonics
* **Target Files**: `analysis/goal6_l3_coastal_model.py` $\rightarrow$ `analysis/goal6/l3_coastal_summary.json`, `analysis/goal6_l3_coastal_harmonics.py`, `analysis/goal6_canonical.py`
* **Audit Checklist**:
   1. The model couples Bangkok Bridge sea tides (CPY015) only — SWAN wave heights are excluded as a single post-event snapshot. Read the improvement figures versus persistence **and** versus the tide-aware persistence baseline from the summary (they were recomputed after the minute-:00 rule; the sign of the +6 h comparison against the tide-aware baseline changed). Is there any **temporal data leakage** (look-ahead bias) between the causal trailing 24 h rainfall feature and the target lead time?
   1a. Since 28 Oct the learned-model results (both baselines, bootstrap intervals) are rendered in Report 4, in the subsection titled 'แบบจำลองเชิงเส้นผสานข้อมูลทะเล เทียบฐานสองแบบ' (the builder calls it 7b; the HTML carries no such number). Check the table against `l3_coastal_summary.json`, that its prose is computed (a sign flip would change the wording), and that the limitation sentences are stated plainly (single season, short test window, one tide station).
   2. Is the chronological train/test split strictly maintained (train up to 19 Sep; declared test window from 20 Sep, usable coverage ending early October)? Are training samples whose target falls inside the test window purged? Does the report state the test-window coverage plainly?
   3. Harmonics: with 10 constituents and nodal corrections fitted on a multi-year record, are amplitudes and phases physically plausible for the Gulf of Thailand (mixed, diurnal-dominant tide)? Is the fit end-date strictly before the test window, and is the common-sample rule across leads respected in the reported errors? Does the text avoid claiming the harmonic model beats the learned model where the summary says otherwise?

### Dimension 3: Compound Flood Risk Matrix (River Discharge vs. Storm Surge)
* **Target Files**: `analysis/compound_flood_risk.py` $\rightarrow$ `analysis/compound_flood_risk_summary.json`, `report/goal6_build_report4_draft.py`
* **Audit Checklist**:
   1. Inspect the non-linear backwater formulation:
      $$H_{C12} = H_{tide} + \Delta h_{wave} + c_1 \cdot \left(\frac{Q}{1000}\right)^{1.28}$$
      Is the empirical exponent (1.28) dimensionally consistent and physically sound across both low-flow ($Q < 1000\ m^3/s$) and extreme-flow ($Q > 3500\ m^3/s$) regimes?
   2. Are the 4 warning thresholds (Normal $<2.00$ m, Watch $2.00–2.40$ m, Warning $2.40–2.70$ m, Bangkok Overtopping Critical $>2.70$ m) adequately aligned with actual Bangkok floodwall crest elevations (+2.80 to +3.00 m MSL)?
   3. The coefficient $c_1 = 0.132$ is **not calibrated** against multi-year telemetry (the repository holds 2026 only), and the formulation assumes $\partial H_{C12}/\partial H_{tide} = 1.0$ with no explicit $Q \times \text{tide}$ interaction term. How much of the reported C.12 stage is an assumption rather than a computed result?
   4. Evaluate the 4 benchmark rows (2011 estimated, 2026 observed, 2 hypothetical) and the gap between modelled and telemetered stage in 2026.
   5. **Anchored matrix (Report 4 §8.1)**: it replaces the assumed unit tide response by a measured gain with a band across periods. Do the critical-cell counts differ materially from the original, and does the report say plainly that the anchored variant rests on a single season and is not a validated forecast? Was the rule committed before the run (`docs/COMPOUND_ANCHORED_PREREG.md`, commit order)?

### Dimension 4: 2D Hypsometric Basin Curve & Route 305 Overtopping Tipping Point
* **Target Files**: `analysis/goal7_ongkharak_2d_depression.py` $\rightarrow$ `analysis/goal7/ongkharak_2d_depression_summary.json`, `report/goal7_blocks.py`
* **Audit Checklist**:
   1. Inspect the 2D hypsometric stage-area-volume curve for the Ongkharak depression: is the integration robust, and is the **DEM-sensitivity table / range across four surfaces** presented honestly (does any text quote a single median, area or IoU without naming its height surface, or present one surface as the best)? Note that for a threshold-defined flood any monotone height correction leaves flooded extent unchanged and only relabels levels.
   2. The Route 305 crown elevation is still absent from every source (gap `route305_crown_elevation`). Verify that no report presents a Route 305 overtopping level as fact.
   3. Assess the hydraulic consequence of road overtopping: does the model account for the shift from closed-basin detention to open discharge into the Rangsit canal network?
   4. The mitrearth road×valley layer gives crossing points inside Ongkharak (Highway 305 included) with **bare-ground heights from two surfaces, not road-surface levels**. Verify no text treats them as crown elevations.

### Dimension 5: Chao Phraya 2 Active Storage Reality & Counterfactual Simulation
* **Target Files**: `analysis/goal7_operational_economics.py`, `analysis/goal7_counterfactual_simulation.py`
* **Audit Checklist**:
   1. The active storage calculation deducts a 2.0 m dead storage ($15.5\text{ MCM}$, analyst assumption) from the total EIA canal volume ($68.5\text{ MCM}$), leaving **$53.0\text{ MCM}$** usable volume ($\approx 24.5\text{ hours}$ to fill an empty canal at $600\text{ m}^3/s$). Is maintaining a 2.0 m minimum water level geotechnically necessary for slope stability in soft Bangkok clay?
   2. Even with $53.0\text{ MCM}$ active storage, filling an empty canal takes only $\approx 24.5\text{ hours}$ (with the canal already at design level the buffer is only the freeboard volume) at $600\text{ m}^3/s$. Does this expose the project to rapid overflow if Gulf pumping is restricted during high sea tides?
   3. In the 2011 counterfactual simulation, what hydraulic bottlenecks arise if tidal lockouts or coastal backwater restrict outlet discharge?

### Dimension 6: Operational Economics, Life-Cycle Cost & Dam Governance
* **Target Files**: `analysis/goal7_operational_economics.py`, `report/goal7_build_policy_brief.py`, `analysis/goal6_pasak_24y_baseline.py`
* **Audit Checklist**:
   1. Examine the S.26 39-year operational profile: is the conclusion that the diversion canal operates at full capacity for only $38.3\text{ days/year}$ (10.5% annual utilization) statistically sound?
   2. Audit the life-cycle economic assessment: at a 7% discount rate (see `operational_economics.lifecycle_economics` for the current annual cost and unit cost), are the Capital Recovery Factor ($CRF$) and OPEX assumptions standard?
   3. Review the ONEP/คชก. rows for rounds 1–3 (letters ทส 1010.6/2233, 1010.6/18346, 1009.6/6077): does each row cite an item that exists in the letter OCR (`analysis/goal7/rejection_letter_items.json`), and are letter numbers/dates consistent across canonical, reports and `tests/test_rejection_letter.py`?
   4. Verify the 22-year comparative dam governance (Pa Sak RID vs Mae Klong EGAT): are the definitions of Upper Rule Curve exceedance and conservation headroom applied consistently?

### Dimension 7: Canonical Invariants, Legal & PDPA Compliance, and Quality Gates
* **Target Files**: `analysis/canonical_numbers.json`, `analysis/goal6/canonical.json`, `analysis/goal7/canonical.json`, `report/*.py`
* **Audit Checklist**:
   1. Are any key hydrological metrics or summary statistics hardcoded as numerical literals in report builders instead of referencing canonical JSON files?
   2. Run `pytest tests/test_thai_language_lint.py` — ensure zero banned jargon, zero collision patterns, and zero registered typos exist in documentation.
   3. Run `pytest tests/test_legal_compliance.py` and `tests/test_privacy.py` — verify strict compliance with defamation laws (system-level critique, no personal culpability) and PDPA (no personally identifiable citizen information).
   4. Verify that visual charts and maps comply with WCAG AA contrast standards (minimum contrast 4.5:1 for body text, 3.0:1 for graphical data marks).
   5. **Two-layer literal gate** (`tools/number_inventory.py`, allowlists `analysis/goal7/literal_allowlist*.json`): try to defeat it — add a hard-coded number equal to a value in the canonical JSON and see whether the traced layer catches it; try a `ร้อยละ N` phrase. Is any allowlist entry stale or hiding a metric?
   5a. The literal allowlist now carries reviewed statuses (`method_parameter`, `source_quote_verified` with a `source_constant`, `source_quote_unverified`, `legacy_unreviewed`). Spot-check a `source_quote_verified` entry against the PDF text-layer page cited in `source_constants.json`; count how many entries remain unreviewed.
   6. **Verification badges** (`report/assets/verification.json`, `tools/write_verification.py`): does a badge show a tick only when its gate really passed? Break one gate in a scratch copy and confirm the tick disappears.

### Dimension 8: Intra-Report & Cross-Report Data Consistency
* **Target Files**: All generated reports (`report/*.html`), report builders (`report/*.py`), and policy brief (`report/สมุดปกขาว_เจ้าพระยา2.html`)
* **Audit Checklist**:
   1. **Intra-Report Consistency (ภายในฉบับเดียวกัน)**: Scan each report from beginning to end. Are there conflicting numbers or contradictory claims within the same document? (e.g., body prose vs. summary boxes, tables, chart captions, or footnotes; or claims that information is "unknown" while concrete coordinates/pins are provided elsewhere in the same report).
   2. **Cross-Report Consistency (ข้ามฉบับข้ามระดับ)**: Compare corresponding metrics across different reports:
      - Public Report 1 vs Academic Report 2 (Nakhon Nayok).
      - Regional Report 3 vs National Benchmark Report 4 (Goal 6).
      - Public Report 7 vs Academic Report 8 vs Policy Brief (Goal 7).
      Do metrics drift between versions (e.g., canal reach lengths, bed widths, storage volumes, expropriation acreages, cost estimates, or discount rate assumptions)?
   3. **Source Reconciliation Framing**: Where multiple historical or differing agency numbers exist (e.g., bed width 51.0 m — confirmed by EIA Fig 2.3.2-11 and P = 95.27 m — vs the discredited 54.5 m; canal length 135.655/135.7/135.9; 160,046 MB vs 165,000 MB budget; 55.4 MCM vs 68.5 MCM storage), are they explicitly framed as reconciled variants with source attribution, rather than presented as conflicting facts?
   4. **Retired Ledger Verification**: Confirm that no retired/deprecated numbers or defensive gap excuses linger in any generated report.

### Dimension 9: DEM Correction, Satellite Waterline Tests & Mitrearth/GISTDA Layers
* **Target Files**: `analysis/goal7_dem_bias_correction.py`, `analysis/goal7_dem_waterline_test.py`, `analysis/goal7_dem_gistda_waterline_test.py`, `analysis/goal7_mitrearth_*.py`, `analysis/goal7/dem_bias_correction.json`
* **Audit Checklist**:
   1. The correction is a continuous, monotone function fitted once on pooled FABDEM/DEMPro points (pre-registered rule) and applied to FABDEM elsewhere, including Ongkharak and the Bang Pakong lowlands; the original stepped table is kept only as a sensitivity case. Is the extrapolation justified? Do the leave-one-window-out results (same reference as the fit, so only a spatial hold-out) and the 24-point EIA ground-line check (eye-read ±0.2 m) support the stated error range? Is the stepped table's max jump still disclosed?
   2. Waterline tests: on Sentinel-1 edges the stepped table showed the narrowest edge-height spread, but the continuous correction gives the same ratio as raw FABDEM — i.e. the stepped table's advantage came from its discontinuities, not from accuracy; yearly GISTDA polygons are inconclusive. Do the reports say this, and is any preference for a corrected surface over-claimed? (Note: the later rain model ranks raw Copernicus slightly higher.)
   3. mitrearth data licence (non-commercial) and PDPA: villages are counted, not named — verify.

### Dimension 10: Rain-Driven 2-D Hydraulic Model (Ongkharak) — Identifiability & Post-hoc Choices
* **Target Files**: `analysis/goal7_ongkharak_hydraulic_2d.py`, `analysis/goal7_event_rain.py`, `analysis/goal7/ongkharak_hydraulic_2d*.json`, `report/goal7_blocks.py` (`tbl_hydraulic_2d`, `prose_hydraulic_2d`, `prose_rain_public`)
* **Audit Checklist**:
   1. Solver: local-inertial scheme with time-step control (cap 8 s, depth-based CFL with a +1 m margin), critical outflow at domain edges, daily rain spread uniformly and offset by 7 h. Is the water budget closed in every run (closure error in `rain_best[*].budget`), and is the share leaving through the open edges disclosed? Is the one-cell river the only inflow path, with tributaries and dam releases omitted?
   2. **Post-hoc grid changes**: the first no-rain grid (channel depth 3–5 m) produced no overbank flow and was replaced by 0.5–2 m after the result was seen; the rain grid was extended once because the best (f, k) was at the edge — and **is still at the edge**. Are both disclosures present in the text? Is "parameters not identifiable" stated plainly?
   3. Are IoU / precision / recall computed consistently against the Sentinel-1 masks inside the model window, and does the public-report box avoid implying forecasting skill? Is the simulated area quoted with the corrected cell area (an earlier constant understated it by 2.3%)?
   3a. **Water budget**: every run carries a budget (closure error against the 5% label threshold). A large share of the water leaves through the open domain edges — is this shown next to the overlap scores, and does the text say the edge condition, not only the infiltration/drainage choice, shapes the result? Is the ±20% inflow sensitivity reported as it is, without turning it into a conclusion about the project?
   3b. **Determinism check**: re-running the old surfaces must reproduce the old scores to three decimals — verify in the summary.
   4. Check the claim "river overflow alone explains almost nothing": could the missing channel geometry (a one-cell river) rather than the mechanism explain it?

### Dimension 11: Bang Pakong Basin / Chachoengsao — GISTDA Product Semantics & the Post-hoc Section
* **Target Files**: `analysis/goal7_bangpakong_chachoengsao.py`, `analysis/goal7_gistda_stac_daily.py`, `analysis/goal7/bangpakong_chachoengsao.json`, `docs/REMOTE_SENSING_APIS.md` §2–2.1, `report/goal6_bp_downstream.py`, Report 3 §4.7
* **Audit Checklist**:
   1. The GISTDA 30/7-day layers are multi-scene composites (every feature lists all scenes); polygon geometry area is about 2× `f_area` (permanent water excluded). Are areas taken from `f_area` consistently, and are cross-day comparisons avoided where scene coverage differs (the 7-day layer fell from 357 to 124 km² only because wide Sentinel-1 scenes left the window)?
   2. The daily STAC archive lacks 16 Sep–1 Oct and ends 17 Oct; the "still flooded" conclusion rests on the BPK003 gauge (above bank 29 days up to 24 Oct), not on area numbers. Check the wording in Reports 7/8 and Report 3 §4.7.
   2a. Own Sentinel-1 water maps for Chachoengsao (26 Sep–26 Oct; `analysis/goal7_s1_chachoengsao_recent.py`, rule `docs/S1_CHACHOENGSAO_RECENT_PREREG.md`): pairing is by relative orbit with a pre-event reference; per-pass coverage must accompany every area and cross-pass areas must not be compared. A wrong boundary file was caught and corrected before results were read (prereg §6) — verify the log is honest and the rule itself did not change.
   3. Report 3 §4.7 is labelled exploratory (post-hoc, outside Q1–Q7). Is the label visible, and do the numbers equal `canonical.bp_downstream` (test: `tests/test_bp_downstream.py`)?
   4. Credential hygiene: GISTDA API responses embed the API key in their links. Search tracked files, reports and logs for key material (`api_key=` values, `.gistda_api.json`, `.cdse_s3.json`). One key exposure occurred in an interactive session transcript on 25 Oct (rotation recommended).

### Dimension 12: OCR / Document-Extraction Integrity
* **Target Files**: `docs/OCR_WORKFLOW_V2.md`, `analysis/goal7/ocr_accuracy_vs_textlayer.json`, `analysis/goal7/indra_vs_typhoon.json`, `analysis/goal7/vlm_pilot_scores.json`, `analysis/goal7/gap_reprobe*.json`, `analysis/goal7/source_constants.json`
* **Audit Checklist**:
   1. On 30 text-layer pages (exact ground truth) Indra OCR averages character similarity 0.94 vs Typhoon 0.85 (numbers found 98% vs 94%). Is the sample (clean printed pages, 2 with tables) described as limited? Is any claim extended to degraded scans?
   2. Trace every number in `source_constants.json` and the reports to its stated method (`text_layer` or hand-read page image + hash). Is any canonical value traceable only to Typhoon/VLM table output? (Example of unreliable OCR: clarification attachment 1, p.42, several culvert rows misread by Typhoon.)
   3. Negative statements ("not found", gaps) depend on OCR recall; `goal7_gap_reprobe.py` searched Typhoon + Indra + text layer and six leads were read without closing any gap. Are open gaps still phrased as "not found in the sources we hold" rather than "does not exist"?
   4. The VLM pilot uses a numeric-match scorer (an earlier string-match bug undercounted — fixed); table-strip accuracy is about 93% (4 wrong digits of 57) for the best readers. Are VLM outputs consistently labelled drafts and kept out of reports?
   4a. Poster-board pages that previously failed for GPU memory were re-read in overlapping tiles (`analysis/goal7_ocr_poster_tiles.py`); these outputs are drafts for text search only. Confirm none feeds a canonical number.
   5. Known environment quirk: on Windows the pytest subprocess tests can fail once with `WinError 50` (stdin handle); rerun with input detached before reporting a failure.

### Dimension 13: Goal-6 Sentinel-1 Flood Maps — Reference-Scene Pairing, Audit and GISTDA Cross-Check
* **Target Files**: `analysis/goal6_s1_stage2_water.py`, `analysis/s1_orbit.py`, `analysis/goal6_s1_reference_audit.py`, `analysis/goal6_s1_gistda_crosscheck.py`, `analysis/goal6/s1_reference_audit.md`, `analysis/goal6/s1_gistda_crosscheck.md`, `docs/S1_REFERENCE_AUDIT_PREREG.md`, `docs/S1_GISTDA_CROSSCHECK_PREREG.md`, `docs/S1_PASS_MOSAIC_PREREG.md`, `docs/S1_REF_SENSITIVITY_PASAK_PREREG.md`, `docs/S1_REF_SENSITIVITY_REST_PREREG.md`, `analysis/goal6_s1_ref_sensitivity.py`, `analysis/goal6/s1_ref_sensitivity.md`, Report 3 (limitation 7 and the per-basin peak tables), `analysis/goal6/canonical.json` (`flood_peak_km2`, `max_extent_*`, `s1_landcover`, `s1_gistda_crosscheck`, `s1_ref_sensitivity`, retired ledger)
* **Audit Checklist**:
   1. History: until 27 Oct the change-detection reference was 'the earliest scene of the same HH:MM group', which gave some tracks a reference acquired during the flood (compared with itself, so the published value was 0 by construction) and sometimes paired scenes of *different* relative orbits. The pairing is now by relative orbit with the latest scene before 24 Sep 00:00 UTC. Verify in code that no HH:MM proxy remains, that reference scenes themselves are excluded (`reference == scene`), and that unpaired scenes are listed rather than silently dropped.
   2. Sequence of decisions: audit prereg committed before any scene was fetched; the audit was diagnostic only; adoption was a separate owner decision recorded in the prereg (§6) before the code change. Check commit order (`git log`) and that the audit did not alter published numbers on its own.
   3. Consequences: per-basin peaks for three basins rose several-fold and a published conclusion (one basin 'mostly permanent water') was retired. Are the retired values in the ledger, are status documents current, and does any report or document still carry the old values or that conclusion? The stage-2 unit is now the pass (relative orbit × day, all slices mosaicked, with a coverage fraction), and per-basin peaks are still lower bounds because no single pass covers a whole basin. Check that no document still calls a per-slice figure a basin peak, and that the retired ledger holds the superseded per-slice values.
   4. GISTDA cross-check: the domain is lowland ∩ scene footprint ∩ provinces that have a GISTDA 30-day layer. An implementation error (clipped per-province boundary layers) was found from an implausible domain share and fixed before interpreting results (prereg §5). Is the comparable share of radar area shown beside precision/recall? Is the text clear that GISTDA's 30-day layer is a multi-scene composite, not ground truth, and that the rule was calibrated only at Nakhon Nayok?
   5. Pass mosaic and all-days maximum extent (`docs/S1_PASS_MOSAIC_PREREG.md`, written before computation): the union of water over all passes is reported *beside* the per-pass peak and is not simultaneous flooding. Verify that no text presents the union as a flood extent at one moment, and that the per-basin peak is the largest single pass, not the union.
   6. Reference-date sensitivity — **now all six basins** (Bang Pakong and Pasak first; Maeklong, Thachin, Ping–Chao Phraya upper and Chao Phraya lower–Bangkok added 28 Oct under `docs/S1_REF_SENSITIVITY_REST_PREREG.md`, committed before the catalogue query, download or computation; file list and hashes in `data/22_goal6_network/manifest.md`). The alternative reference is the latest same-orbit pass at least 6 days older than the primary reference; a 'control' is the primary-reference pass measured against the alternative. Recompute from `analysis/goal6/s1_ref_sensitivity*.json` and compare with Report 3. Points to probe: (i) the 10% label is a table label, not a pass/fail gate — Maeklong lands just over it and Ping–CP just under; are both printed as they are, and does any sentence turn a near-threshold result into a verdict? (ii) per-pass percentage changes from bases below 1 km² (Pasak reaches a very large percentage) must not be over-read; (iii) controls range from near zero to over 1,000 km² (Ping–CP); the new per-orbit table of primary-reference dates (Report 3, built from canonical `s1_ref_dates`) shows the largest control is on an orbit imaged on the morning of the rain-start day, yet another orbit imaged two days later has small controls — is the report content to state this as a fact and not draw a causal story? (iv) ICT versus UTC: scene filenames are UTC, the report prints Thai time — check the conversion on at least two scenes; (v) the per-basin peak is still the largest single pass, a lower bound, and 'sensitive' must not be read as 'wrong'.
   6a. Prereg hygiene for the 28 Oct run: `git log` must show `docs/S1_REF_SENSITIVITY_REST_PREREG.md` before any `data/22_goal6_network` download entry and before the result files; the owner approved the exact scene list and size before download; per-file SHA-256 are in `data/22_goal6_network/raw/s1_audit/_progress_sens_rest.json`. Confirm the result commit did not change any headline number or the retired ledger (the prereg says a change there means stop and ask).
   7. Residual risks to probe: seasonal paddy water counted as 'new water' (now tested only through the reference-date shift, not by crop calendar); different acquisition geometry between tracks; scenes that do not cover whole basins; no field validation outside Nakhon Nayok; GISTDA domain only partial for Maeklong; a one-season reference (late Aug–Sep 2026 only) for every basin.

### Dimension 14: Canonical → HTML Rendering Gaps (the class of bug round 8 found twice)
* **Why**: round 8 found a finished analysis present in a summary JSON but absent from the published page (anchored compound matrix missing from Report 4; two Report 7–8 tables silently empty because they read a canonical key that nothing produced). A builder that reads a missing key and prints nothing passes every number test.
* **Target Files**: `analysis/*_summary.json`, `analysis/goal6/canonical.json`, `analysis/goal7/canonical.json`, `report/goal6_build_report*_draft.py`, `report/goal7_blocks.py`, `report/*.html`, `tests/test_goal6_consistency.py`, `tests/test_goal7_report.py`
* **Audit Checklist**:
   1. For each top-level key of the two canonical files, find where it is rendered. List keys that no builder reads and builders that read keys the canonical does not contain (`.get(...)` with an empty default is the usual hiding place). Do not report a key as unrendered until you have searched the built HTML for its figures.
   2. For every table builder in `report/goal7_blocks.py`, build the table in a scratch process with the canonical and confirm it is non-empty; do the same for the Report 3 and 4 tables. Is there a test that fails on an empty table or an empty section heading?
   3. Section headings: does any `<h2>`/`<h3>` in the HTML have no body before the next heading?
   4. Documents that print numbers but are outside the scan (README, HANDOFF, START_HERE, GOAL*_PLAN, `docs/*.md`): compare any metric they quote with the canonical and the retired ledgers (`analysis/goal6/canonical.json → retired`, `analysis/goal7/retired.json`).
   5. Is each retired value carried with a reason and a commit, and does `test_retired_ledger_is_data_with_reasons` really read the file rather than a copy?

---

## 4. Standardized Audit Output Template

Structure your audit findings using this standardized report schema:

```markdown
# Hydrological Audit & Red-Team Report: nnyflood

## 1. Executive Summary
- **Overall Scientific & Engineering Reliability**: [High / Medium / Low]
- **Key System Strengths**: (Top 3 validated capabilities)
- **Critical Vulnerabilities & Limitations**: (Top 3 issues requiring mitigation)

## 2. Findings Matrix
| Finding ID | Severity | Component / Target File | Root Cause Summary | Recommended Action |
|---|---|---|---|---|
| F-01 | Critical / High / Medium / Low | `path/to/file:line` | ... | ... |
| F-02 | Critical / High / Medium / Low | `path/to/file:line` | ... | ... |

## 3. Deep-Dive Technical Findings
### [F-01] <Title of Finding>
- **Location**: `path/to/file:line` or `Document / Table ID`
- **Empirical Evidence**: Exact conflicting numbers, equations, or command outputs.
- **Hydraulic & Data Science Critique**: Why the current formulation or claim is physically implausible, statistically biased, or unverified.
- **Proposed Solution**: Exact code modification, physical boundary correction, or documentation adjustment.

## 4. Intra-Report & Cross-Report Consistency Audit
- **Intra-Report Conflicts**: Discrepancies found within the same report (e.g., text vs table, caption vs body).
- **Cross-Report Conflicts**: Metric drift between Public, Academic, Regional, and Policy Brief versions.
- **Reconciliation & Gap Assessment**: Are conflicting sources properly attributed and tracked in `gaps.json`?

## 5. Verified Invariants (Passed Spot-Checks)
List metrics, equations, and data pipelines that were checked against primary sources and confirmed 100% accurate, including verification method used.

## 6. Information Gaps & Required Field Data
List any parameters that cannot currently be audited due to unreleased agency data (e.g., gate discharge logs, high-resolution bathymetry).

## 7. Overall System Suggestions & Consistency Recommendations
- **Hydraulic & Methodological Recommendations**: High-level advice to improve physical realism, modeling accuracy, and policy impact.
- **Data Consistency & Governance Recommendations**: Strategic suggestions on how the project can permanently prevent multi-source contradictions, automate truth reconciliation, and streamline cross-report updates.
```
