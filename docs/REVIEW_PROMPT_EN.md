# Comprehensive System Audit Prompt (English) — Multi-Pillar Red-Team Review

> **How to use**: Copy the complete markdown text below this block and provide it to an independent external AI auditor (e.g., Claude 3.5 Sonnet, GPT-4o / OpenAI o1, Gemini 1.5 Pro) or a senior hydraulic/data science peer reviewer with access to this repository.  
> **Last Updated**: October 25, 2026 | Covers all 3 Pillars (8 Reports + Policy Brief), Astronomical Tidal Harmonics, 2D Compound Risk Matrix, 2D Hypsometric Ongkharak Basin Tipping Point, Active Storage Reality, 39y Operational Economics, ONEP EIA Critiques, **plus the 19–25 Oct additions: DEM bias correction + satellite waterline tests, the rain-driven 2-D Ongkharak model, whole-basin Bang Pakong / Chachoengsao analysis (Report 3 §4.7, labelled exploratory), GISTDA daily-product handling, and the OCR toolchain (Typhoon vs Indra OCR, VLM pilot)**.

---

# Independent Audit & Red-Team Review: Hydrological Investigation Project `nnyflood`

## 1. Auditor Role & Mission Objective

You are an **Independent Senior Hydraulic Engineer and Lead Data Science Auditor (Red-Team Reviewer)** conducting a rigorous, evidence-based peer review of the **nnyflood** hydrological investigation codebase and technical reports.

The project investigates catastrophic flooding in Thailand through empirical data, remote sensing, and physical hydraulic modeling across **3 Core Pillars (7 Goals)**:
1. **Pillar 1 (Goals 1–5): Nakhon Nayok River Basin (Sep 26–29, 2026 Flash Flood)**  
   - Attribution of upstream rainfall band vs. Khun Dan Prakan Chon Dam release (88:12 ratio).
   - 1D Hydrodynamic Routing model (`analysis/hydraulic_1d_routing.py`) routing flood waves with Muskingum–Cunge (weight X clamped to 0, i.e. a linear-reservoir cascade — not a full Saint-Venant solve) from Ny.1B to Ny.7 (18.3 km key reach, 43 km full basin).
   - Cross-sectional rating curves, levee-crest capacity ($666.3\ m^3/s$ at Ny.1B; $617.4\ m^3/s$ at Ny.7, terrace onset at $486.9\ m^3/s$), and simulated peak travel time along the modelled reach ($3.25$ hours for 18.3 km). Observed peak lag at Ny.7 is $9.0\text{ h}$, indicating significant overland/floodplain detention along the unconfined reach.
   - Gate-Control vs Routing Trap case study at Tha Chang regulator (`report/build_expert_report.py` Section 6.5.1c).
   - Khun Dan 22-year operational baseline (36.5 days premature filling ahead of median) and stress analysis of 6 medium reservoirs.
   - Machine learning stage prediction (Model v1: 11 features, Ridge regression, +6h RMSE $0.17\ m$).
2. **Pillar 2 (Goal 6): 6 National River Basins & 2011 Mega-Flood Benchmark**  
   - Multi-reservoir comparative operation across 24 major dams (EGAT hydroelectric vs. RID irrigation), including the Pa Sak (RID) vs. Mae Klong (EGAT) 22-year governance benchmark (Pasak: three documented definitions in `goal6/canonical.json → pasak_year_counts` — above upper rule curve on any day 20/22 years, in Aug–Sep 16/22, above normal storage 17/24 years; vs EGAT dams maintaining dedicated flood headroom).
   - National stress index covering 461 medium reservoirs across Thailand (mean 87.2% capacity, 94 reservoirs overflowing with 516.2 MCM surcharge).
   - 46-year ERA5 rainfall rarity and recurrence interval modeling.
   - L3 Coastal-Coupled Model (`analysis/goal6_l3_coastal_model.py`): Coupling Chao Phraya River stage at C.12 Samsen with Bangkok Bridge tidal telemetry (CPY015). Reported +6h linear RMSE falls from 79.6 cm down to 37.4 cm (53.0%); usable test coverage is 47.1% (226 usable hours) of the declared window.
   - Astronomical Tidal Harmonics decomposition (`analysis/goal6_canonical.py` $\rightarrow$ `l3_coastal_harmonics`): Classical harmonic constituents ($M_2, S_2, K_1, O_1$) fitted on the single Bangkok-Bridge tide gauge CPY015 evaluating 1–3 day tidal forecast skill.
   - Compound Flood Risk Matrix (`analysis/compound_flood_risk.py`): Non-linear backwater interaction between upstream river discharge and storm surge, with 4 benchmark rows: 2011 (inputs estimated, unsourced), 2026 observed, and 2 hypothetical scenarios.
3. **Pillar 3 (Goal 7): Chao Phraya 2 Bypass Floodway Project**  
   - 135.9-km Pasak–Gulf of Thailand new diversion canal (total Chainat–Pasak–Gulf floodway network, design discharge $600\ m^3/s$).
   - Embankment profile analysis: elevated dike (+3.8 to +6.4 m MSL, 2.5–4.8 m above ground across Nakhon Nayok plain).
   - 2D Hypsometric Stage-Area-Volume Analysis of Ongkharak Depression (`analysis/goal7_ongkharak_2d_depression.py`): the primary DEM is now **FABDEM corrected with a height-dependent bias table learned from DEMPro 5 m windows** (`analysis/goal7_dem_bias_correction.py`; Ongkharak lies outside the DEMPro windows, so ±0.7–1.0 m uncertainty applies): district $512.8\text{ km}^2$, median $+1.22\text{ m MSL}$ (the raw Copernicus median was $+3.20$ m — the old "+3.20 m Route 305 tipping point" is **superseded**; the raw/corrected sensitivity table is in the reports). Bucket-fill fits to Sentinel-1 flood masks (IoU 0.31 / 0.25) are a baseline, not a validated model.
   - Canal Active Storage Reality (`analysis/goal7_operational_economics.py`): Total static volume $68.5\text{ MCM}$ (derived from approved EIA cross-section $504\text{ m}^2 \times 135.9\text{ km}$), with a 2.0 m dead storage pool (an analyst assumption, $15.5\text{ MCM}$ for the 51.0 m bed width, 1:3 inner slopes), leaving **$53.0\text{ MCM}$** usable volume ($\approx 24.5\text{ hours}$ to fill an empty canal at $600\text{ m}^3/s$; a canal already at design level has only the freeboard volume as buffer). Legacy draft values ($55.4\text{ MCM}$ total / $41.6\text{ MCM}$ active) and the discredited 54.5 m bed-width reading ($16.2$ / $52.3$ / $24.2$) have been retired.
   - S.26 39-Year Operational Profile: Transferred flood volume averages $1,970\text{ MCM/yr}$; canal operates at full capacity equivalent to only $38.3\text{ days/year}$ (10.5% annual utilization, idle $>10\text{ months/year}$).
   - Life-Cycle Economics & Bang Ban Comparison: Annualized capital + OPEX at 7% discount rate is $13,416\text{ MB/year}$; levelized unit cost of diverted floodwater is $6.81\text{ THB/m}^3$ ($8.17$ at 9%, $10.35$ at 12%), compared to $0.50–2.50\text{ THB/m}^3$ for retention basins and existing canal upgrades. Risk of delay and cost escalation benchmarked against Bang Ban–Bang Sai (8y $\rightarrow$ 11.5–15y, 1.93–2.14 hundred billion THB).
   - ONEP EIA rejection history (3 committee rounds): letter ทส 1010.6/2233 dated **18 Feb 2562** (the earlier "14 Feb" was a retired error), ทส 1010.6/18346 dated 25 Nov 2564, ทส 1009.6/6077 dated 18 Mar 2567 — dates verified on page images; row citations ("หัวข้อ N ข้อ M") checked against the complete Typhoon OCR of the letters (R7-17, `tests/test_rejection_letter.py`); round 1 has 16 rows, rounds 2–3 three rows each (selected items, not exhaustive).
   - Nuclear Facility & Critical Infrastructure Proximity: Thailand Institute of Nuclear Technology (TINT) Ongkharak research reactor at a map pin supplied by the project owner, $14.1221^\circ\text{ N}, 101.0275^\circ\text{ E}$ (not a surveyed boundary; 5.78 km east of km 57 of an unofficial canal alignment).
   - 87 cross-drainage structures cataloged (34 inverted siphons) with severe dry-season siltation risk.
   - ONWR Water Chart GIS layer overlay (`analysis/goal7_waterchart_overlay.py`): 16.8 km (47%) spatial intersection with designated floodway zones.
   - Counterfactual Hydraulic Simulation (`analysis/goal7_counterfactual_simulation.py`): an ILLUSTRATIVE simulation on synthetic sine hydrographs (stored under `illustrative_only` in goal7 canonical; not rendered in any report; its outputs must not be treated as results).
   - **DEM validation (new)**: waterline tests of 3 DEMs against Sentinel-1 flood edges (`analysis/goal7_dem_waterline_test.py`) and 9 yearly GISTDA flood polygons (`goal7_dem_gistda_waterline_test.py`); mitrearth 77-province + national packs (non-commercial licence), GISTDA 15-year flood frequency along the canal corridor, SLR vs canal, DEMPro vs EIA ground line.
   - **Rain-driven 2-D hydraulic model (new)** (`analysis/goal7_ongkharak_hydraulic_2d.py`, `goal7_event_rain.py`): local-inertial shallow-water solver on a ~90 m grid; Ny.7 discharge inflow (rating curve ±20%), channel-bed conditioning, 48-station daily rain (IDW), lumped infiltration f and drainage k. Reported: river inflow alone IoU ≤ 0.01; with rain IoU 0.40–0.43 (27 Sep fit) / 0.28–0.32 (2 Oct, not refit); **the best (f, k) sits at the edge of the tested grid in both rounds**; precision ≈ 0.43–0.48; stored water is large. Appears in Report 8 (academic) and, in plain language, in Report 7.
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
3. **Read first**: `HANDOFF.md` (25 Oct section), `docs/GOAL7_PLAN.md` §27–28.1, `docs/OCR_WORKFLOW_V2.md`, `docs/REMOTE_SENSING_APIS.md`, `docs/OFFLINE_DATA_BACKLOG.md` (R7-17..R7-22), `analysis/goal7/gaps.json`.
3a. **Validate Using Concrete Commands**:
   - Run the unified 4-step verification runner: `python tools/verify_all.py` (all steps must pass).
   - Check the project knowledge catalog: `python catalog.py check` and `python catalog.py audit`.
   - Run full test suite: `pytest` (expected ≈ 274 passed; if Windows subprocess tests fail with `WinError 50`, rerun with stdin detached).
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

---

## 3. Targeted Audit Dimensions

### Dimension 1: 1D Hydrodynamic Routing & Local Hydraulics (Nakhon Nayok River)
* **Target Files**: `analysis/hydraulic_1d_routing.py` $\rightarrow$ `analysis/hydraulic_1d_routing_summary.json`, `report/build_expert_report.py`
* **Audit Checklist**:
   1. Does the Muskingum–Cunge (X = 0) routing accurately represent wave attenuation and backwater effects along the 18.3 km Ny.1B–Ny.7 reach?
   2. Are the bankfull discharges ($666.3\ m^3/s$ at Ny.1B and $617.4\ m^3/s$ at Ny.7) mathematically sound given the surveyed cross-sections (`data/23_rid_swoc/raw/rid_telemetry_cross_sections.json` and `data/19_rid_cross_sections/`) and Manning’s equation?
   3. Is the simulated travel time ($3.25\text{ h}$ over the 18.3 km modelled reach) physically coherent with the surveyed bed slope ($S_0 \approx 0.00035–0.00065$) and Manning's roughness coefficient ($n \approx 0.0437$)? Assess how overland/floodplain detention accounts for the observed $9.0\text{ h}$ lag at Ny.7.
   4. Evaluate the Gate-Control vs Routing Trap case study at Tha Chang (km 21.3): does the analysis correctly separate gate operation effects from upstream river routing?

### Dimension 2: Estuarine Machine Learning & Astronomical Tidal Harmonics
* **Target Files**: `analysis/goal6_l3_coastal_model.py` $\rightarrow$ `analysis/goal6/l3_coastal_summary.json`, `analysis/goal6_canonical.py`
* **Audit Checklist**:
   1. The model couples Bangkok Bridge sea tides (CPY015) only — SWAN wave heights are excluded as a single post-event snapshot. Coupling cuts +6h RMSE by 53.0% (from 79.6 cm down to 37.4 cm for Linear Regression, and 23.4% vs tide-aware persistence), while at +24h linear improvement vs tide-aware persistence is negative (−41.3%). Is there any **temporal data leakage** (look-ahead bias) between the causal trailing 24h rainfall feature and target lead time?
   2. Is the chronological train/test split strictly maintained (Train: 2026 wet season up to Sep 19; Test: declared Sep 20 – Oct 9, 2026, usable coverage ends Oct 2 13:00, 47.1% coverage)? Are training samples whose target falls inside the test window purged?
   3. Examine the astronomical tidal harmonics ($M_2, S_2, K_1, O_1$) decomposition at CPY015 only: are harmonic amplitudes and phase angles physically consistent with Gulf of Thailand amphidromic dynamics?

### Dimension 3: Compound Flood Risk Matrix (River Discharge vs. Storm Surge)
* **Target Files**: `analysis/compound_flood_risk.py` $\rightarrow$ `analysis/compound_flood_risk_summary.json`, `report/goal6_build_report4_draft.py`
* **Audit Checklist**:
   1. Inspect the non-linear backwater formulation:
      $$H_{C12} = H_{tide} + \Delta h_{wave} + c_1 \cdot \left(\frac{Q}{1000}\right)^{1.28}$$
      Is the empirical exponent (1.28) dimensionally consistent and physically sound across both low-flow ($Q < 1000\ m^3/s$) and extreme-flow ($Q > 3500\ m^3/s$) regimes?
   2. Are the 4 warning thresholds (Normal $<2.00$ m, Watch $2.00–2.40$ m, Warning $2.40–2.70$ m, Bangkok Overtopping Critical $>2.70$ m) adequately aligned with actual Bangkok floodwall crest elevations (+2.80 to +3.00 m MSL)?
   3. The coefficient $c_1 = 0.132$ is **not calibrated** against multi-year telemetry (the repository holds 2026 only), and the formulation assumes $\partial H_{C12}/\partial H_{tide} = 1.0$ with no explicit $Q \times \text{tide}$ interaction term. How much of the reported C.12 stage is an assumption rather than a computed result?
   4. Evaluate the 4 benchmark rows (2011 estimated, 2026 observed, 2 hypothetical) and the 0.12 m gap between modelled (2.36) and telemetered (2.24) stage in 2026.

### Dimension 4: 2D Hypsometric Basin Curve & Route 305 Overtopping Tipping Point
* **Target Files**: `analysis/goal7_ongkharak_2d_depression.py` $\rightarrow$ `analysis/goal7/ongkharak_2d_depression_summary.json`, `report/goal7_blocks.py`
* **Audit Checklist**:
   1. Inspect the 2D hypsometric stage-area-volume curve for the Ongkharak depression ($512.8\text{ km}^2$, median $+1.22\text{ m MSL}$ on the corrected FABDEM; raw Copernicus median $+3.2$ m): is the integration robust, and is the **DEM-sensitivity table** presented honestly (does any text still imply the raw $+3.20$ m median or the 119.91 MCM / 256.3 km² figures)?
   2. The Route 305 crown elevation is still absent from every source (gap `route305_crown_elevation`). Verify that no report presents a Route 305 overtopping level as fact.
   3. Assess the hydraulic consequence of road overtopping: does the model account for the shift from closed-basin detention to open discharge into the Rangsit canal network?

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
   2. Audit the life-cycle economic assessment: at a 7% discount rate, total annual capital and maintenance cost is $13,416\text{ MB/year}$, yielding $6.81\text{ THB/m}^3$ diverted. Are the Capital Recovery Factor ($CRF$) and OPEX assumptions standard?
   3. Review the ONEP/คชก. rows for rounds 1–3 (letters ทส 1010.6/2233, 1010.6/18346, 1009.6/6077): does each row cite an item that exists in the letter OCR (`analysis/goal7/rejection_letter_items.json`), and are letter numbers/dates consistent across canonical, reports and `tests/test_rejection_letter.py`?
   4. Verify the 22-year comparative dam governance (Pa Sak RID vs Mae Klong EGAT): are the definitions of Upper Rule Curve exceedance and conservation headroom applied consistently?

### Dimension 7: Canonical Invariants, Legal & PDPA Compliance, and Quality Gates
* **Target Files**: `analysis/canonical_numbers.json`, `analysis/goal6/canonical.json`, `analysis/goal7/canonical.json`, `report/*.py`
* **Audit Checklist**:
   1. Are any key hydrological metrics or summary statistics hardcoded as numerical literals in report builders instead of referencing canonical JSON files?
   2. Run `pytest tests/test_thai_language_lint.py` — ensure zero banned jargon, zero collision patterns, and zero registered typos exist in documentation.
   3. Run `pytest tests/test_legal_compliance.py` and `tests/test_privacy.py` — verify strict compliance with defamation laws (system-level critique, no personal culpability) and PDPA (no personally identifiable citizen information).
   4. Verify that visual charts and maps comply with WCAG AA contrast standards (minimum contrast 4.5:1 for body text, 3.0:1 for graphical data marks).

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
   1. The bias table is learned in the Chao Phraya plain windows of DEMPro 5 m and applied to FABDEM elsewhere (including the Bang Pakong lowlands and Ongkharak). Is the extrapolation justified? Do the leave-one-window-out validation and the EIA ground-line check (24 points, eye-read ±0.2 m) support the claimed error range? Is DEMPro itself independent of the EIA (gap `dempro_source`)?
   2. Waterline tests: the edge-height spread ratio is only modestly lower for the corrected DEM on Sentinel-1 edges (about 0.69–0.71 vs 0.76–0.83) and **inconclusive** on GISTDA yearly polygons. Do the reports present them as supporting evidence only? Is the corrected-DEM preference over-claimed anywhere? (Note: the later rain model ranks raw Copernicus slightly higher.)
   3. mitrearth data licence (non-commercial) and PDPA: villages are counted, not named — verify.

### Dimension 10: Rain-Driven 2-D Hydraulic Model (Ongkharak) — Identifiability & Post-hoc Choices
* **Target Files**: `analysis/goal7_ongkharak_hydraulic_2d.py`, `analysis/goal7_event_rain.py`, `analysis/goal7/ongkharak_hydraulic_2d*.json`, `report/goal7_blocks.py` (`tbl_hydraulic_2d`, `prose_hydraulic_2d`, `prose_rain_public`)
* **Audit Checklist**:
   1. Solver: local-inertial scheme with time-step control (cap 8 s, depth-based CFL with a +1 m margin), critical outflow at domain edges, daily rain spread uniformly and offset by 7 h. Any stability or mass-balance concern (stored vs inflow)? Is the Ny.7 rating curve (±20%) the only inflow, with tributaries and dam releases omitted?
   2. **Post-hoc grid changes**: the first no-rain grid (channel depth 3–5 m) produced no overbank flow and was replaced by 0.5–2 m after the result was seen; the rain grid was extended once because the best (f, k) was at the edge — and **is still at the edge**. Are both disclosures present in the text? Is "parameters not identifiable" stated plainly?
   3. Are IoU / precision / recall computed consistently against the Sentinel-1 masks inside the model window (129 / 99 km²), and does the public-report box avoid implying forecasting skill?
   4. Check the claim "river overflow alone explains almost nothing": could the missing channel geometry (a one-cell river) rather than the mechanism explain it?

### Dimension 11: Bang Pakong Basin / Chachoengsao — GISTDA Product Semantics & the Post-hoc Section
* **Target Files**: `analysis/goal7_bangpakong_chachoengsao.py`, `analysis/goal7_gistda_stac_daily.py`, `analysis/goal7/bangpakong_chachoengsao.json`, `docs/REMOTE_SENSING_APIS.md` §2–2.1, `report/goal6_bp_downstream.py`, Report 3 §4.7
* **Audit Checklist**:
   1. The GISTDA 30/7-day layers are multi-scene composites (every feature lists all scenes); polygon geometry area is about 2× `f_area` (permanent water excluded). Are areas taken from `f_area` consistently, and are cross-day comparisons avoided where scene coverage differs (the 7-day layer fell from 357 to 124 km² only because wide Sentinel-1 scenes left the window)?
   2. The daily STAC archive lacks 16 Sep–1 Oct and ends 17 Oct; the "still flooded" conclusion rests on the BPK003 gauge (above bank 29 days up to 24 Oct), not on area numbers. Check the wording in Reports 7/8 and Report 3 §4.7.
   3. Report 3 §4.7 is labelled exploratory (post-hoc, outside Q1–Q7). Is the label visible, and do the numbers equal `canonical.bp_downstream` (test: `tests/test_bp_downstream.py`)?
   4. Credential hygiene: GISTDA API responses embed the API key in their links. Search tracked files, reports and logs for key material (`api_key=` values, `.gistda_api.json`, `.cdse_s3.json`). One key exposure occurred in an interactive session transcript on 25 Oct (rotation recommended).

### Dimension 12: OCR / Document-Extraction Integrity
* **Target Files**: `docs/OCR_WORKFLOW_V2.md`, `analysis/goal7/ocr_accuracy_vs_textlayer.json`, `analysis/goal7/indra_vs_typhoon.json`, `analysis/goal7/vlm_pilot_scores.json`, `analysis/goal7/gap_reprobe*.json`, `analysis/goal7/source_constants.json`
* **Audit Checklist**:
   1. On 30 text-layer pages (exact ground truth) Indra OCR averages character similarity 0.94 vs Typhoon 0.85 (numbers found 98% vs 94%). Is the sample (clean printed pages, 2 with tables) described as limited? Is any claim extended to degraded scans?
   2. Trace every number in `source_constants.json` and the reports to its stated method (`text_layer` or hand-read page image + hash). Is any canonical value traceable only to Typhoon/VLM table output? (Example of unreliable OCR: clarification attachment 1, p.42, several culvert rows misread by Typhoon.)
   3. Negative statements ("not found", gaps) depend on OCR recall; `goal7_gap_reprobe.py` searched Typhoon + Indra + text layer and six leads were read without closing any gap. Are open gaps still phrased as "not found in the sources we hold" rather than "does not exist"?
   4. The VLM pilot uses a numeric-match scorer (an earlier string-match bug undercounted — fixed); table-strip accuracy is about 93% (4 wrong digits of 57) for the best readers. Are VLM outputs consistently labelled drafts and kept out of reports?
   5. Known environment quirk: on Windows the pytest subprocess tests can fail once with `WinError 50` (stdin handle); rerun with input detached before reporting a failure.

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
