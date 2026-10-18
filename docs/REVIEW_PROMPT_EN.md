# Comprehensive System Audit Prompt (English) — Multi-Pillar Red-Team Review

> **How to use**: Copy the complete markdown text below this block and provide it to an independent external AI auditor (e.g., Claude 3.5 Sonnet, GPT-4o / OpenAI o1, Gemini 1.5 Pro) or a senior hydraulic/data science peer reviewer with access to this repository.  
> **Last Updated**: October 18, 2026 | Covers all 3 Pillars (8 Reports + Policy Brief), Astronomical Tidal Harmonics, 2D Compound Risk Matrix, 2D Hypsometric Ongkharak Basin Tipping Point, Active Storage Reality, 39y Operational Economics, and ONEP EIA Critiques.

---

# Independent Audit & Red-Team Review: Hydrological Investigation Project `nnyflood`

## 1. Auditor Role & Mission Objective

You are an **Independent Senior Hydraulic Engineer and Lead Data Science Auditor (Red-Team Reviewer)** conducting a rigorous, evidence-based peer review of the **nnyflood** hydrological investigation codebase and technical reports.

The project investigates catastrophic flooding in Thailand through empirical data, remote sensing, and physical hydraulic modeling across **3 Core Pillars (7 Goals)**:
1. **Pillar 1 (Goals 1–5): Nakhon Nayok River Basin (Sep 26–29, 2026 Flash Flood)**  
   - Attribution of upstream rainfall band vs. Khun Dan Prakan Chon Dam release (88:12 ratio).
   - 1D Hydrodynamic Routing model (`analysis/hydraulic_1d_routing.py`) solving Saint-Venant kinematic/diffusive wave propagation from Ny.1B to Ny.7 (18.3 km key reach, 43 km full basin).
   - Cross-sectional rating curves, levee-crest capacity ($666.3\ m^3/s$ at Ny.1B; $617.4\ m^3/s$ at Ny.7, terrace onset at $486.9\ m^3/s$), and simulated peak travel time along the modelled reach ($3.25$ hours for 18.3 km). Observed peak lag at Ny.7 is $9.0\text{ h}$, indicating significant overland/floodplain detention along the unconfined reach.
   - Gate-Control vs Routing Trap case study at Tha Chang regulator (`report/build_expert_report.py` Section 6.5.1c).
   - Khun Dan 22-year operational baseline (36.5 days premature filling ahead of median) and stress analysis of 6 medium reservoirs.
   - Machine learning stage prediction (Model v1: 11 features, Ridge regression, +6h RMSE $0.17\ m$).
2. **Pillar 2 (Goal 6): 6 National River Basins & 2011 Mega-Flood Benchmark**  
   - Multi-reservoir comparative operation across 24 major dams (EGAT hydroelectric vs. RID irrigation), including the Pa Sak (RID) vs. Mae Klong (EGAT) 22-year governance benchmark (Pasak exceeded upper rule curve in 17 of 22 years, median 107%, vs EGAT dams maintaining dedicated flood headroom).
   - National stress index covering 461 medium reservoirs across Thailand (mean 87.2% capacity, 94 reservoirs overflowing with 516.2 MCM surcharge).
   - 46-year ERA5 rainfall rarity and recurrence interval modeling.
   - L3 Coastal-Coupled Model (`analysis/goal6_l3_coastal_model.py`): Coupling Chao Phraya River stage at C.12 Samsen with Bangkok Bridge tidal telemetry (CPY015). Reported +6h linear RMSE falls from 73.6 cm to 35.9 cm (51.2%); usable test coverage is 57.1% of the declared window.
   - Astronomical Tidal Harmonics decomposition (`analysis/goal6_canonical.py` $\rightarrow$ `l3_coastal_harmonics`): Classical harmonic constituents ($M_2, S_2, K_1, O_1$) decomposed across 4 key estuarine stations (C.29, BKK001, GLF002, GLF003) evaluating 1–3 day tidal forecast skill.
   - Compound Flood Risk Matrix (`analysis/compound_flood_risk.py`): Non-linear backwater interaction between upstream river discharge and storm surge, benchmarked against 5 historical flood events (2011, 2021, 2022, 2024, 2026).
3. **Pillar 3 (Goal 7): Chao Phraya 2 Bypass Floodway Project**  
   - 135.9-km Pasak–Gulf of Thailand new diversion canal (total Chainat–Pasak–Gulf floodway network, design discharge $600\ m^3/s$).
   - Embankment profile analysis: elevated dike (+3.8 to +6.4 m MSL, 2.5–4.8 m above ground across Nakhon Nayok plain).
   - 2D Hypsometric Stage-Area-Volume Analysis of Ongkharak Depression (`analysis/goal7_ongkharak_2d_depression.py`): Topographical basin modeling ($513.1\text{ km}^2$, median $+3.19\text{ m MSL}$) derived from 1m LiDAR/FABDEM; critical tipping point at **$+3.20\text{ m MSL}$** ($126.22\text{ MCM}$, $257.2\text{ km}^2$, 50.1% of district) where floodwater overtops Route 305 (Rangsit–Nakhon Nayok road), spilling directly into the Rangsit canal network.
   - Canal Active Storage Reality (`analysis/goal7_operational_economics.py`): Static volume $55.4\text{ MCM}$, mandatory 2.0 m dead storage ($21.0\text{ MCM}$) to prevent bank slope failure in soft Bangkok clay, leaving only **$34.4\text{ MCM}$** active storage buffer ($\approx 15.9\text{ hours}$ buffer at $600\text{ m}^3/s$).
   - S.26 39-Year Operational Profile: Transferred flood volume averages $1,970\text{ MCM/yr}$; canal operates at full capacity equivalent to only $38.3\text{ days/year}$ (10.5% annual utilization, idle $>10\text{ months/year}$).
   - Life-Cycle Economics & Bang Ban Comparison: Annualized capital + OPEX at 7% discount rate is $13,416\text{ MB/year}$; levelized unit cost of diverted floodwater is $6.81\text{ THB/m}^3$ ($8.17$ at 9%, $10.35$ at 12%), compared to $0.50–2.50\text{ THB/m}^3$ for retention basins and existing canal upgrades. Risk of delay and cost escalation benchmarked against Bang Ban–Bang Sai (8y $\rightarrow$ 11.5–15y, 1.93–2.14 hundred billion THB).
   - ONEP EIA Rejection Order (Letter ทส 1010.6/2233, 18 Feb 2562): 16 critical objection categories from the Expert Committee (คชก.) including Ongkharak fault status, Thiessen rainfall averaging, 7-year return period misinterpretation, 3-year construction impossibility / inflated EIRR, fish biomass anomaly, and missing cross-drainage management plans.
   - 87 cross-drainage structures cataloged (34 inverted siphons) with severe dry-season siltation risk.
   - ONWR Water Chart GIS layer overlay (`analysis/goal7_waterchart_overlay.py`): 16.8 km (47%) spatial intersection with designated floodway zones.
   - Counterfactual Hydraulic Simulation (`analysis/goal7_counterfactual_simulation.py`): Evaluating peak shaving during 2011 (4,394.5 MCM diverted, 38.8% of excess volume absorbed, 0.53 m stage reduction) and 2026 conditions.

### Your Target:
**Identify errors, physical inconsistencies, mathematical flaws, data leakage, unwarranted assumptions, discrepancies with canonical datasets, and legal/defamation risks across all code, data pipelines, and generated reports.**  
Do not offer generic compliments or superficial stylistic edits. Report concrete technical findings backed by exact `file:line` references, raw data citations, or reproducible terminal executions.

---

## 2. Mandatory Rules of Engagement

1. **Strictly Read-Only**: Do not modify files, do not commit or push to git, and never execute destructive commands (`git reset`, `git clean`, `rm -rf`).
2. **No Hallucinations or Phantom References**: Every identified finding must cite a verified `path/to/file:line`, a specific PDF page, or the exact output of a command you executed.
3. **Validate Using Concrete Commands**:
   - Run the unified 4-step verification runner: `python tools/verify_all.py` (all steps must pass).
   - Check the project knowledge catalog: `python catalog.py check` and `python catalog.py audit`.
   - Run full test suite: `pytest`.
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
   1. Does the simplified Saint-Venant kinematic / diffusive wave routing accurately represent wave attenuation and backwater effects along the 18.3 km Ny.1B–Ny.7 reach?
   2. Are the bankfull discharges ($666.3\ m^3/s$ at Ny.1B and $617.4\ m^3/s$ at Ny.7) mathematically sound given the surveyed cross-sections (`data/23_rid_swoc/raw/rid_telemetry_cross_sections.json` and `data/19_rid_cross_sections/`) and Manning’s equation?
   3. Is the simulated travel time ($3.25\text{ h}$ over the 18.3 km modelled reach) physically coherent with the surveyed bed slope ($S_0 \approx 0.00035–0.00065$) and Manning's roughness coefficient ($n \approx 0.0437$)? Assess how overland/floodplain detention accounts for the observed $9.0\text{ h}$ lag at Ny.7.
   4. Evaluate the Gate-Control vs Routing Trap case study at Tha Chang (km 21.3): does the analysis correctly separate gate operation effects from upstream river routing?

### Dimension 2: Estuarine Machine Learning & Astronomical Tidal Harmonics
* **Target Files**: `analysis/goal6_l3_coastal_model.py` $\rightarrow$ `analysis/goal6/l3_coastal_summary.json`, `analysis/goal6_canonical.py`
* **Audit Checklist**:
   1. The model couples Bangkok Bridge sea tides (CPY015) only — SWAN wave heights are excluded as a single post-event snapshot. Coupling cuts +6h RMSE by 51.2% (from 73.6 cm down to 35.9 cm for Linear Regression, and 23.4% for GBDT), while at +24h it does not improve the linear model (−1.9%). Is there any **temporal data leakage** (look-ahead bias) between the causal trailing 24h rainfall feature and target lead time?
   2. Is the chronological train/test split strictly maintained (Train: 2026 wet season up to Sep 19; Test: declared Sep 20 – Oct 9, 2026, usable coverage ends Oct 2 13:00, 57.1% coverage)? Are training samples whose target falls inside the test window purged?
   3. Examine the astronomical tidal harmonics ($M_2, S_2, K_1, O_1$) decomposition across C.29, BKK001, GLF002, GLF003: are harmonic amplitudes and phase angles physically consistent with Gulf of Thailand amphidromic dynamics?

### Dimension 3: Compound Flood Risk Matrix (River Discharge vs. Storm Surge)
* **Target Files**: `analysis/compound_flood_risk.py` $\rightarrow$ `analysis/compound_flood_risk_summary.json`, `report/goal6_build_report4_draft.py`
* **Audit Checklist**:
   1. Inspect the non-linear backwater formulation:
      $$H_{C12} = H_{tide} + \Delta h_{wave} + c_1 \cdot \left(\frac{Q}{1000}\right)^{1.28}$$
      Is the empirical exponent (1.28) dimensionally consistent and physically sound across both low-flow ($Q < 1000\ m^3/s$) and extreme-flow ($Q > 3500\ m^3/s$) regimes?
   2. Are the 4 warning thresholds (Normal $<2.00$ m, Watch $2.00–2.40$ m, Warning $2.40–2.70$ m, Bangkok Overtopping Critical $>2.70$ m) adequately aligned with actual Bangkok floodwall crest elevations (+2.80 to +3.00 m MSL)?
   3. The coefficient $c_1 = 0.132$ is **not calibrated** against multi-year telemetry (the repository holds 2026 only), and the formulation assumes $\partial H_{C12}/\partial H_{tide} = 1.0$ with no explicit $Q \times \text{tide}$ interaction term. How much of the reported C.12 stage is an assumption rather than a computed result?
   4. Evaluate the 5 historical benchmark classifications (2011 extreme fluvial, 2021 moderate pluvial, 2022 high compound, 2024 pluvial, 2026 low-medium).

### Dimension 4: 2D Hypsometric Basin Curve & Route 305 Overtopping Tipping Point
* **Target Files**: `analysis/goal7_ongkharak_2d_depression.py` $\rightarrow$ `analysis/goal7/ongkharak_2d_depression_summary.json`, `report/goal7_blocks.py`
* **Audit Checklist**:
   1. Inspect the 2D hypsometric stage-area-volume curve for Ongkharak depression ($513.1\text{ km}^2$, median elevation $+3.19\text{ m MSL}$): is the numerical integration over 1m LiDAR/FABDEM mathematically robust?
   2. Audit the critical tipping point at $+3.20\text{ m MSL}$ ($126.22\text{ MCM}$, $257.2\text{ km}^2$): does physical survey data confirm that Route 305 road crown elevation is indeed $+3.20\text{ m MSL}$?
   3. Assess the hydraulic consequence of road overtopping: does the model account for the shift from closed-basin detention to open discharge into the Rangsit canal network?

### Dimension 5: Chao Phraya 2 Active Storage Reality & Counterfactual Simulation
* **Target Files**: `analysis/goal7_operational_economics.py`, `analysis/goal7_counterfactual_simulation.py`
* **Audit Checklist**:
   1. The active storage calculation deducts a 2.0 m dead storage ($21.0\text{ MCM}$) from the $55.4\text{ MCM}$ total canal volume, leaving $34.4\text{ MCM}$ usable buffer. Is maintaining a 2.0 m minimum water level geotechnically necessary for slope stability in soft Bangkok clay?
   2. With $34.4\text{ MCM}$ active storage, the canal provides only $15.9\text{ hours}$ of buffer at $600\text{ m}^3/s$. Does this expose the project to rapid overflow if Gulf pumping is restricted during high sea tides?
   3. In the 2011 counterfactual simulation, what hydraulic bottlenecks arise if tidal lockouts or coastal backwater restrict outlet discharge?

### Dimension 6: Operational Economics, Life-Cycle Cost & Dam Governance
* **Target Files**: `analysis/goal7_operational_economics.py`, `report/goal7_build_policy_brief.py`, `analysis/goal6_pasak_24y_baseline.py`
* **Audit Checklist**:
   1. Examine the S.26 39-year operational profile: is the conclusion that the diversion canal operates at full capacity for only $38.3\text{ days/year}$ (10.5% annual utilization) statistically sound?
   2. Audit the life-cycle economic assessment: at a 7% discount rate, total annual capital and maintenance cost is $13,416\text{ MB/year}$, yielding $6.81\text{ THB/m}^3$ diverted. Are the Capital Recovery Factor ($CRF$) and OPEX assumptions standard?
   3. Review the 16 ONEP/คชก. critique categories from Letter ทส 1010.6/2233: are all objections accurately documented against primary source records?
   4. Verify the 22-year comparative dam governance (Pa Sak RID vs Mae Klong EGAT): are the definitions of Upper Rule Curve exceedance and conservation headroom applied consistently?

### Dimension 7: Canonical Invariants, Legal & PDPA Compliance, and Quality Gates
* **Target Files**: `analysis/canonical_numbers.json`, `analysis/goal6/canonical.json`, `analysis/goal7/canonical.json`, `report/*.py`
* **Audit Checklist**:
   1. Are any key hydrological metrics or summary statistics hardcoded as numerical literals in report builders instead of referencing canonical JSON files?
   2. Run `pytest tests/test_thai_language_lint.py` — ensure zero banned jargon, zero collision patterns, and zero registered typos exist in documentation.
   3. Run `pytest tests/test_legal_compliance.py` and `tests/test_privacy.py` — verify strict compliance with defamation laws (system-level critique, no personal culpability) and PDPA (no personally identifiable citizen information).
   4. Verify that visual charts and maps comply with WCAG AA contrast standards (minimum contrast 4.5:1 for body text, 3.0:1 for graphical data marks).

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

## 4. Verified Invariants (Passed Spot-Checks)
List metrics, equations, and data pipelines that were checked against primary sources and confirmed 100% accurate, including verification method used.

## 5. Information Gaps & Required Field Data
List any parameters that cannot currently be audited due to unreleased agency data (e.g., gate discharge logs, high-resolution bathymetry).
```
