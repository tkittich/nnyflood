# Independent Audit & Red-Team Review: Hydrological Investigation Project `nnyflood`
**Document Version**: Round 8 External Red-Team Audit  
**Auditor**: Senior Hydraulic Engineer & Lead Data Science Auditor (Gemini 3.8 Flash)  
**Target Commit**: `78cc138`  
**Date**: October 27, 2026  
**Scope**: Full Repository Audit across 3 Pillars (Goals 1–7, Reports 1–8 & Policy Brief, Pre-Registration Protocols, Canonical Databases, and Verification Quality Gates)  
**Operating Mode**: Strictly Read-Only Audit (No code or data modifications performed)

---

## 1. Executive Summary

### 1.1 Overall Scientific and Engineering Reliability Assessment
**Overall Rating: Medium-High (8.4 / 10.0)**

The `tkittich/nnyflood` repository represents a remarkably transparent, mathematically rigorous, and reproducible civic hydraulic modeling and public policy audit platform. Unlike traditional gray-literature reports or ad-hoc consultancy studies, the analytical foundation of `nnyflood` is enforced through continuous software integration principles:
- Every major scientific methodology revision is governed by an explicit, version-controlled pre-registration document (`docs/*_PREREG.md`) committed to Git *prior* to executing calculations.
- Data integrity across 2,963 input/output files is locked by SHA-256 cryptographic hashes (`tools/verify_data_integrity.py`), reporting **0 mismatches and 0 missing files**.
- Front-end reports are generated programmatically via unified Python builders pulling from single-source-of-truth canonical JSON registries (`analysis/canonical_numbers.json`, `analysis/goal6/canonical.json`, `analysis/goal7/canonical.json`).

Nevertheless, rigorous physical and hydrodynamic inspection reveals critical vulnerabilities in the downstream pipeline:
1. **Front-End Pipeline Disconnect (Silent Table Drop)**: In [report/goal7_blocks.py:237,258](file:///e:/theera/code/flood/report/goal7_blocks.py#L237-L258), two major hydraulic summary tables (`tbl_ongkharak_water_balance` and `tbl_reach_hydraulic_vectors`) fail silently to render (`""`) in both public and academic Goal 7 HTML deliverables because `analysis/goal7_ongkharak_hydraulics.py` is not integrated into the canonical builder pipeline.
2. **Conveyance Inversion under Overbank Flow**: In [analysis/hydraulic_1d_routing_summary.json:73-82](file:///e:/theera/code/flood/analysis/hydraulic_1d_routing_summary.json#L73-L82), composite Manning rating calculations at station Ny.1B cause conveyance to drop from $666.30\text{ m}^3/\text{s}$ at stage 10.60 m to $578.43\text{ m}^3/\text{s}$ at stage 11.00 m (-87.87 m³/s drop despite a 40 cm increase in flood stage) due to sudden wetted perimeter expansion on the terrace.
3. **Spatial Discretization Non-Convergence**: In the 1D Muskingum-Cunge routing model, refining the sub-reach grid from $n_{\text{sub}}=1$ to $n_{\text{sub}}=48$ steadily increases RMSE (from 126.1 to 131.1 m³/s). The headline parameter $n_{\text{sub}}=12$ functions as an empirical tuning coefficient that matches physical diffusion to numerical diffusion rather than a converged numerical solution.
4. **Unreviewed Literal Technical Debt**: The Goal 7 literal allowlist contains 76 out of 102 entries (74.5%) categorized as `legacy_unreviewed` or `source_quote_unverified`, creating a bypass around canonical provenance tracking.

---

### 1.2 Top 3 Methodological Strengths
1. **Pre-Registration Timing Invariant**: Across all 11 pre-registered protocols (`docs/*_PREREG.md`), commit timestamps strictly precede the corresponding analytical code runs, eliminating post-hoc parameter tweaking and p-hacking.
2. **End-to-End Automated Verification (`tools/verify_all.py`)**: The entire repository is governed by a 5-step test runner validating catalog entries (124 items), data file hashes (2,963 files), toolchain availability, coding standards, and 321 pytest unit tests with zero failures.
3. **Remote Sensing Geometry & Relative Orbit Pairing**: Sentinel-1 SAR flood extent mapping explicitly accounts for ascending vs. descending satellite look angles and pre-event acquisition dates, correcting systemic undercounting in the Pa Sak, Tha Chin, and Mae Klong basins.

---

### 1.3 Top 3 Methodological Vulnerabilities & Technical Risks
1. **Silent Front-End Rendering Dropping Key Proofs**: Public and academic readers of the Goal 7 reports receive blank spaces instead of the Ongkharak basin water balance and reach velocity tables.
2. **Non-Monotonic 1D Hydraulic Rating Curves**: Using a single composite Manning formulation across compound river-floodplain cross-sections violates basic fluid mechanics by predicting decreasing discharge during rising overbank flood stages.
3. **Compound Flood Risk Backwater Attenuation Oversimplification**: The compound flood risk model couples upstream discharge with Gulf of Thailand storm surge using an idealized exponential spatial decay ($c_1 = 0.132\text{ m}^{-1}$) that neglects hydrodynamic phase alignment and tidal momentum propagation.

---

## 2. Findings Matrix

| Finding ID | Severity | Target File & Line | Short Description | Recommended Action |
| :--- | :--- | :--- | :--- | :--- |
| **F-01** | **High** | [report/goal7_blocks.py:237,258](file:///e:/theera/code/flood/report/goal7_blocks.py#L237-L258) | `tbl_ongkharak_water_balance()` and `tbl_reach_hydraulic_vectors()` return `""` due to missing `ongkharak_hydraulics` key in `canonical.json`. | Run and merge `analysis/goal7_ongkharak_hydraulics.py` into `analysis/goal7/canonical.json`, and assert table presence in tests. |
| **F-02** | **Medium-High** | [analysis/hydraulic_1d_routing.py:165-210](file:///e:/theera/code/flood/analysis/hydraulic_1d_routing.py#L165-L210) | Single composite Manning equation produces conveyance foldback (-87.87 m³/s) at Ny.1B when stage rises from 10.60 m to 11.00 m. | Transition exclusively to the Divided Channel Method (DCM) above bankfull stage. |
| **F-03** | **Medium** | [analysis/hydraulic_1d_routing_summary.json:115-135](file:///e:/theera/code/flood/analysis/hydraulic_1d_routing_summary.json#L115-L135) | Spatial discretization non-convergence in Muskingum-Cunge: RMSE worsens as sub-reaches increase ($n_{\text{sub}} = 1 \to 48$). | Explicitly document $n_{\text{sub}}=12$ as an empirical diffusion matching choice; plan migration to 1D dynamic wave routing. |
| **F-04** | **Medium** | [analysis/compound_flood_risk.py:88-142](file:///e:/theera/code/flood/analysis/compound_flood_risk.py#L88-L142) | Compound flood risk matrix assumes uncalibrated exponential backwater decay ($c_1=0.132$) without tidal-hydrograph phase lag. | Couple tide and river discharge through unsteady Saint-Venant backwater simulations calibrated to C.29A and CPY015. |
| **F-05** | **Medium** | [analysis/goal7/literal_allowlist.json](file:///e:/theera/code/flood/analysis/goal7/literal_allowlist.json) | 76 of 102 (74.5%) literal allowlist entries remain unverified (`legacy_unreviewed` or `source_quote_unverified`). | Review remaining 76 entries against primary PDF sources and migrate verified constants into `source_constants.json`. |
| **F-06** | **Medium** | [analysis/goal7/ongkharak_hydraulic_2d.json](file:///e:/theera/code/flood/analysis/goal7/ongkharak_hydraulic_2d.json) | Truncated rectangular 2D domain causes substantial boundary leakage (53.58 MCM of 219.36 MCM total inflow). | Align 2D computational domain boundaries with physical highway embankments and natural watershed divides. |
| **F-07** | **Low-Medium**| [analysis/goal6/l3_coastal_summary.json:115-135](file:///e:/theera/code/flood/analysis/goal6/l3_coastal_summary.json#L115-L135) | CPY015 annual mean datum swings between 0.204 m and 0.743 m MSL across multi-year series, degrading forecast skill. | Detrend seasonal upstream discharge mounding before extracting astronomical tidal constituents and training neural/linear models. |

---

## 3. Deep-Dive Technical Findings

### Finding F-01: Silent Table Rendering Defect in Goal 7 HTML Deliverables
- **Severity**: **High**
- **Category**: Front-End Pipeline Integration & Reporting Defect
- **Exact Location**:
  - [report/goal7_blocks.py:237,258](file:///e:/theera/code/flood/report/goal7_blocks.py#L237-L258)
  - [report/goal7_build_public.py:363-364](file:///e:/theera/code/flood/report/goal7_build_public.py#L363-L364)
  - [report/goal7_build_academic.py:859-860](file:///e:/theera/code/flood/report/goal7_build_academic.py#L859-L860)
- **Evidence & Reproduction**:
  In `report/goal7_blocks.py`:
  ```python
  def tbl_ongkharak_water_balance(C: dict) -> str:
      H = C.get("ongkharak_hydraulics", {}).get("water_balance", {})
      if not H:
          return ""
      ...
  def tbl_reach_hydraulic_vectors(C: dict) -> str:
      vecs = C.get("ongkharak_hydraulics", {}).get("reach_vectors", [])
      if not vecs:
          return ""
      ...
  ```
  Both `report/goal7_build_public.py` (lines 363–364) and `report/goal7_build_academic.py` (lines 859–860) include these table generators:
  ```python
  tbl_reach_hydraulic_vectors(canonical),
  tbl_ongkharak_water_balance(canonical),
  ```
  However, inspecting `analysis/goal7/canonical.json` reveals that the key `"ongkharak_hydraulics"` does not exist. The standalone script `analysis/goal7_ongkharak_hydraulics.py` produces `analysis/goal7/ongkharak_hydraulics.json`, but it is never executed or merged into canonical storage by `analysis/goal7_analysis.py` or `analysis/build_canonical_numbers.py`.
  
  *Audit Discovery*: During the Round 7 triage ([docs/reviews/TRIAGE_ROUND7_2026-10-25.md:83](file:///e:/theera/code/flood/docs/reviews/TRIAGE_ROUND7_2026-10-25.md#L83)), this defect was previously submitted with a minor typo in the reviewer note (`ongkhark` instead of `ongkharak`). The triage dismissed the finding as "cannot reproduce / code spells `ongkharak_hydraulics` correctly". Because the reviewer misspelled the key name, the triage overlooked the underlying reality: `canonical.json` genuinely lacks the dictionary, and both tables evaluate to empty strings `""` in the rendered public and academic HTML reports.
- **Engineering & Methodological Impact**:
  The public and academic reports are missing empirical tabular evidence detailing the Ongkharak water balance and reach hydraulic vectors, weakening the substantiation of the flood attenuation mechanism.
- **Recommended Action**:
  1. Integrate `analysis/goal7_ongkharak_hydraulics.py` into the canonical build chain (`analysis/goal7_analysis.py`).
  2. Add an explicit assertion in `tests/test_goal7_report.py` ensuring that `report/คลองเจ้าพระยา2_ประชาชน.html` and `report/คลองเจ้าพระยา2_วิชาการ.html` contain non-empty `<table class="tbl-water-balance">` elements.

---

### Finding F-02: Conveyance Inversion under Overbank Flow at Station Ny.1B
- **Severity**: **Medium-High**
- **Category**: 1D Open-Channel Hydraulics & Rating Curve Monotonicity
- **Exact Location**:
  - [analysis/hydraulic_1d_routing_summary.json:73-82](file:///e:/theera/code/flood/analysis/hydraulic_1d_routing_summary.json#L73-L82)
  - [analysis/hydraulic_1d_routing.py:165-210](file:///e:/theera/code/flood/analysis/hydraulic_1d_routing.py#L165-L210)
  - [analysis/ny1b_hydraulic_geometry.py](file:///e:/theera/code/flood/analysis/ny1b_hydraulic_geometry.py)
- **Evidence & Reproduction**:
  Examining the composite section rating table in `hydraulic_1d_routing_summary.json`:
  ```json
  {
    "stage_m": 10.6,
    "composite_conveyance_cms": 666.30,
    "divided_conveyance_cms": 724.15,
    "composite_P_m": 88.0,
    "composite_R_m": 6.84
  },
  {
    "stage_m": 11.0,
    "composite_conveyance_cms": 578.43,
    "divided_conveyance_cms": 1009.11,
    "composite_P_m": 142.0,
    "composite_R_m": 4.79
  }
  ```
  When the stage increases from 10.60 m (bankfull) to 11.00 m (+0.40 m depth), composite conveyance plummets from $666.30\text{ m}^3/\text{s}$ down to $578.43\text{ m}^3/\text{s}$—a reduction of $87.87\text{ m}^3/\text{s}$ (-13.2%).
  
  *Physical Cause*: The single composite Manning equation calculates hydraulic radius as $R = A / P$. At 10.60 m, the flow is confined within the main channel ($P = 88.0\text{ m}$). At 11.00 m, water spills onto the broad floodplain terrace, rapidly expanding the wetted perimeter to $P = 142.0\text{ m}$. This causes $R$ to drop from $6.84\text{ m}$ to $4.79\text{ m}$. In Manning's equation:
  $$Q = \frac{1}{n} A R^{2/3} S_0^{1/2}$$
  the decrease in $R^{2/3}$ ($3.60 \to 2.84$, a 21.1% drop) overpowers the 10% increase in flow area $A$, creating a non-physical negative rating slope.
- **Engineering & Methodological Impact**:
  A non-monotonic rating curve violates the second law of thermodynamics in steady open-channel flow and introduces numerical instabilities into hydraulic routing solvers. If applied directly in flood routing, it artificially restricts peak flow capacity once water overtops the banks.
- **Recommended Action**:
  Standardize on the Divided Channel Method (DCM) for all overbank stages in `analysis/ny1b_hydraulic_geometry.py` and `analysis/hydraulic_1d_routing.py`. DCM computes main channel and floodplain conveyances independently ($K_{\text{total}} = K_{\text{main}} + K_{\text{left}} + K_{\text{right}}$), correctly predicting a monotonic increase to $1009.11\text{ m}^3/\text{s}$ at stage 11.00 m.

---

### Finding F-03: Spatial Discretization Non-Convergence in Muskingum-Cunge Routing
- **Severity**: **Medium**
- **Category**: Numerical Hydraulics & Spatial Mesh Convergence
- **Exact Location**:
  - [analysis/hydraulic_1d_routing_summary.json:115-135](file:///e:/theera/code/flood/analysis/hydraulic_1d_routing_summary.json#L115-L135)
  - [docs/ROUTING1D_SUBREACH_PREREG.md](file:///e:/theera/code/flood/docs/ROUTING1D_SUBREACH_PREREG.md)
  - [analysis/hydraulic_1d_routing.py](file:///e:/theera/code/flood/analysis/hydraulic_1d_routing.py)
- **Evidence & Reproduction**:
  The sub-reach spatial sensitivity test evaluates simulated downstream hydrographs at station Ny.7 across varying sub-reach subdivisions ($n_{\text{sub}}$):
  - $n_{\text{sub}} = 1$: RMSE = $126.1\text{ m}^3/\text{s}$
  - $n_{\text{sub}} = 3$: RMSE = $126.9\text{ m}^3/\text{s}$
  - $n_{\text{sub}} = 6$: RMSE = $127.8\text{ m}^3/\text{s}$
  - $n_{\text{sub}} = 12$: RMSE = $128.8\text{ m}^3/\text{s}$ (Pre-registered headline parameter)
  - $n_{\text{sub}} = 24$: RMSE = $129.9\text{ m}^3/\text{s}$
  - $n_{\text{sub}} = 48$: RMSE = $131.1\text{ m}^3/\text{s}$
- **Engineering & Methodological Impact**:
  In a convergent numerical scheme, refining the grid ($\Delta x \to 0$) causes the error to asymptotically approach zero or reach a stable numerical plateau. Here, the error monotonically increases as spatial resolution is refined. In the Muskingum-Cunge scheme, numerical diffusion is given by:
  $$D_{\text{num}} = \frac{c \Delta x}{2} (1 - 2X)$$
  When $n_{\text{sub}}$ increases ($\Delta x$ decreases), numerical diffusion decreases, stripping away artificial attenuation. The apparent agreement with observed peak attenuation at $n_{\text{sub}}=12$ is an artifact of matching physical floodplain detention to numerical grid diffusion. The pre-registration contract `docs/ROUTING1D_SUBREACH_PREREG.md` successfully locked the parameter against p-hacking, but physically, $n_{\text{sub}}=12$ remains an empirical tuning parameter rather than a converged spatial discretization.
- **Recommended Action**:
  Document transparently in Section 6 of Report 2 that Muskingum-Cunge spatial discretization is constrained by numerical diffusion matching rather than formal mesh convergence. In the next modeling phase, replace the linear reservoir cascade with a 1D Saint-Venant hydraulic solver.

---

### Finding F-04: Compound Flood Risk Matrix Backwater & Tide Gain Discrepancy
- **Severity**: **Medium**
- **Category**: Estuarine-Riverine Compound Inundation Modeling
- **Exact Location**:
  - [analysis/compound_flood_risk_summary.json:10-50](file:///e:/theera/code/flood/analysis/compound_flood_risk_summary.json#L10-L50)
  - [analysis/compound_flood_risk.py:88-142](file:///e:/theera/code/flood/analysis/compound_flood_risk.py#L88-L142)
  - [docs/COMPOUND_ANCHORED_PREREG.md](file:///e:/theera/code/flood/docs/COMPOUND_ANCHORED_PREREG.md)
- **Evidence & Reproduction**:
  In `compound_flood_risk_summary.json`, the original model evaluated critical inundation cells where stage exceeds levee protection ($>2.70\text{ m}$ MSL):
  - Original formula ($\partial H/\partial H_{\text{tide}} = 1.0$): **48 critical cells**.
  - Anchored model (measured empirical gain = 0.771, 95% CI [0.718, 0.790]): **24 critical cells** (gain low: 23, gain high: 25).
  
  Anchoring to empirical telemetry reduces the count of critical risk cells by exactly 50%. However, both formulations compute backwater stage via an uncalibrated static exponential decay:
  $$H(x) = H_{\text{river}}(x) + \alpha \cdot H_{\text{tide}} \cdot e^{-c_1 x}$$
  where $c_1 = 0.132\text{ m}^{-1}$ is assumed uniformly along the lower estuary.
- **Engineering & Methodological Impact**:
  In low-gradient tidal rivers, backwater profiles are inherently dynamic and discharge-dependent: high upstream river discharge steepens the hydraulic gradient and suppresses tidal wave penetration, whereas low river discharge permits tidal surges to penetrate dozens of kilometers inland. Using a static attenuation parameter without phase alignment between peak river discharge and semi-diurnal spring tides distorts hazard zoning in the Bangkok metropolitan reach.
- **Recommended Action**:
  Formulate $c_1$ as a dynamic function of upstream discharge $Q_{\text{river}}$ based on synchronous historical records from C.29A (Bang Sai) and CPY015 (Bangkok Bridge), or transition the compound flood risk matrix to a 1D hydrodynamic backwater model.

---

### Finding F-05: Literal Allowlist Technical Debt & Unverified Source Quotations
- **Severity**: **Medium**
- **Category**: Code Quality, Data Traceability & Pipeline Governance
- **Exact Location**:
  - [analysis/goal7/literal_allowlist.json](file:///e:/theera/code/flood/analysis/goal7/literal_allowlist.json)
  - [tools/number_inventory.py](file:///e:/theera/code/flood/tools/number_inventory.py)
- **Evidence & Reproduction**:
  Auditing all 102 entries in `analysis/goal7/literal_allowlist.json`:
  - `source_quote_verified`: 12 entries (11.8%)
  - `method_parameter`: 14 entries (13.7%)
  - `source_quote_unverified`: 21 entries (20.6%)
  - `legacy_unreviewed`: 55 entries (53.9%)
  
  Total unverified or legacy entries: **76 out of 102 (74.5%)**.
- **Engineering & Methodological Impact**:
  The two-tier number inventory system (`tools/number_inventory.py`) was instituted to enforce the principle that no hardcoded numeric metrics appear in report builders. While the allowlist prevents build failures, having nearly three-quarters of the entries classified as `legacy_unreviewed` or `source_quote_unverified` creates an integrity loophole where unverified survey dates, historical reservoir volumes, and compensation numbers can slip into public-facing text without automated provenance checks.
- **Recommended Action**:
  Conduct a focused audit sprint to eliminate `legacy_unreviewed` entries. Migrate all verified project numbers into `analysis/goal7/source_constants.json` with explicit primary PDF document citations and page numbers.

---

### Finding F-06: 2D Local-Inertial Hydraulic Model Parameter Unidentifiability & Boundary Leakage
- **Severity**: **Medium**
- **Category**: 2D Hydrodynamic Modeling & Domain Delineation
- **Exact Location**:
  - [analysis/goal7/ongkharak_hydraulic_2d.json](file:///e:/theera/code/flood/analysis/goal7/ongkharak_hydraulic_2d.json)
  - [analysis/goal7/ongkharak_hydraulic_2d_rain.json](file:///e:/theera/code/flood/analysis/goal7/ongkharak_hydraulic_2d_rain.json)
- **Evidence & Reproduction**:
  In `ongkharak_hydraulic_2d_rain.json`, the local-inertial shallow-water solver maintains strict mass conservation ($<0.01\%$ closure error). For the $219.36\text{ MCM}$ total inflow budget:
  - Basin depression storage: $132.41\text{ MCM}$ (60.4%)
  - Infiltration loss: $33.37\text{ MCM}$ (15.2%)
  - Boundary outflow leakage: **$53.58\text{ MCM}$ (24.4%)**
- **Engineering & Methodological Impact**:
  Because the computational domain is defined by an arbitrary rectangular bounding box rather than a physical hydrological catchment boundary, nearly one-quarter of the total water volume drains out of the grid edges. Consequently, calibrating Manning's roughness $n$ and infiltration rate $k$ against satellite flood extents encounters parameter equifinality/unidentifiability: the optimal $(f, k)$ values sit at the boundary of the parameter search space because excess volume is vented through open model edges rather than interacting with the floodplain topography.
- **Recommended Action**:
  Delineate the 2D computational domain along real physical barriers—specifically the elevated embankments of Highway 305 and Highway 33—and apply closed (no-flow) boundary conditions along true topographic divides.

---

### Finding F-07: Tidal Telemetry Datum Drift & Multi-Year Harmonic Swings
- **Severity**: **Low-Medium**
- **Category**: Estuarine Hydrology & Signal Processing
- **Exact Location**:
  - [analysis/goal6/l3_coastal_summary.json:115-135](file:///e:/theera/code/flood/analysis/goal6/l3_coastal_summary.json#L115-L135)
  - [analysis/goal6_coastal_l3.py](file:///e:/theera/code/flood/analysis/goal6_coastal_l3.py)
- **Evidence & Reproduction**:
  Astronomical harmonic analysis on 96,514 hourly records (BE 2555–2569) at station CPY015 yields robust tidal constituent amplitudes ($M_2 = 0.4836\text{ m}, K_1 = 0.5432\text{ m}, S_2 = 0.2380\text{ m}$). However, the fitted annual mean water level ($S_0$) drifts significantly across years:
  - BE 2558: $S_0 = 0.204\text{ m}$ MSL
  - BE 2565: $S_0 = 0.743\text{ m}$ MSL
  
  This represents a $+0.539\text{ m}$ shift in mean water level over a 7-year period.
- **Engineering & Methodological Impact**:
  In estuarine rivers, mean water level is heavily influenced by seasonal river runoff pushing against tidal water. Failing to separate upstream discharge mounding from the astronomical datum distorts the tidal forecast baseline, causing the +6h linear predictive model to underperform the tide-aware persistence baseline (-24.9% skill improvement, 95% CI [-59.7, 9.7]%, spanning zero).
- **Recommended Action**:
  Fit a two-stage harmonic model that incorporates upstream discharge from C.29A as a continuous covariate to remove seasonal hydrological mounding before fitting astronomical constituent phases and amplitudes.

---

## 4. Intra-Report & Cross-Report Consistency Audit

### 4.1 Numerical Alignment Across Reports and Canonical Databases
A systematic cross-check was conducted between the canonical registries, generated HTML reports, and technical documentation. Major historical discrepancies identified in earlier audit rounds have been fully resolved:

| Parameter | Conflicting Legacy Value | Current Reconciled Canonical | Storage Key in Canonical | Alignment Status |
| :--- | :--- | :--- | :--- | :--- |
| **Chao Phraya 2 Canal Bed Width** | 54.5 m (legacy RID concept) | **51.0 m** | `goal7/canonical.json` $\to$ `cp2_specs.bottom_width_m` | **Reconciled & Locked** |
| **Total Canal Static Storage** | 55.4 MCM (uncalibrated) | **68.5 MCM** ($504\text{ m}^2 \times 135.9\text{ km}$) | `goal7/canonical.json` $\to$ `cp2_specs.total_volume_mcm` | **Reconciled & Locked** |
| **Canal Active Storage** | 41.6 MCM / 55.4 MCM | **53.0 MCM** (less 2.0 m dead storage: 15.5 MCM) | `goal7/canonical.json` $\to$ `cp2_specs.active_storage_mcm` | **Reconciled & Locked** |
| **Total Canal Alignment Length** | 134.8 km | **135.9 km** | `goal7/canonical.json` $\to$ `cp2_specs.length_km` | **Reconciled & Locked** |
| **Empty Canal Filling Time** | 25.6 hours | **24.5 hours** (at design $600\text{ m}^3/\text{s}$) | `goal7/canonical.json` $\to$ `cp2_specs.active_fill_time_hours` | **Reconciled & Locked** |
| **S.26 Annual Diversion Utilization** | Arbitrary estimates | **10.49%** (equivalent to 38.3 days/year) | `goal7/canonical.json` $\to$ `s26_operational_profile.utilization_rate`| **Reconciled & Locked** |
| **Ny.1B–Ny.7 Channel Reach Length** | 7.77 km (straight-line) | **18.30 km** (sinuosity 1.94 per Mitrearth) | `goal7/reach_length.json` $\to$ `sinuous_length_km` | **Reconciled & Locked** |

---

### 4.2 Legal Compliance, Defamation Guardrails & PDPA Audit
The repository was audited against `docs/LEGAL_REVIEW.md` and automated compliance suites:
1. **ONEP EIA Rejection History Traceability**:
   The report accurately records the three formal rejections by the ONEP Expert Committee:
   - Round 1: Meeting 10/2550 (19 Oct 2550) $\to$ Letter ทส 1007/5823 (27 Dec 2550)
   - Round 2: Meeting 7/2561 (20 Jun 2561) $\to$ Letter ทส 1009.5/8760 (10 Jul 2561)
   - Round 3: Meeting 13/2566 (20 Dec 2566) $\to$ Letter ทส 1009.5/17565 (28 Dec 2566)
   All citations quote official committee resolutions neutrally without defamatory personal framing.
2. **Nuclear Research Facility Proximity**:
   The report notes that the Thailand Institute of Nuclear Technology (TINT) TRR-1 research reactor lies approximately 1.2 km from the canal corridor, with appropriate neutral engineering disclaimers regarding environmental impact assessments.
3. **Automated Privacy Compliance**:
   Executing `pytest tests/test_legal_compliance.py tests/test_privacy.py` confirms that 8/8 tests pass with zero personal data leaks.

---

## 5. Verified Invariants (Things the Codebase Gets Right)

1. **Pre-Registration Commit Precedence**:
   All 11 pre-registration documents (`docs/*_PREREG.md`) were verified via `git log --follow`. In every instance, the pre-registration protocol was committed to the repository *before* executing the calculations.
2. **Automated Verification Pipeline (`tools/verify_all.py`)**:
   The 5-stage automated quality gate completes with return code 0:
   - `catalog.py check`: 124 cataloged files verified on disk.
   - `verify_data_integrity.py`: 2,963 files checked with **0 MISMATCH, 0 MISSING**.
   - `doctor.py`: Verified tool registry and system environment.
   - `pytest lint & consistency`: 53 tests passed.
   - `pytest tests/`: **321 unit tests passed in 115.37s**.
3. **Internal Hydraulic Mass Conservation**:
   The 2D finite-volume solver (`analysis/goal7_ongkharak_hydraulic_2d.py`) achieves $<0.01\%$ volume discrepancy over 100,000+ computational time steps.
4. **Sentinel-1 SAR Relative Orbit Matching**:
   SAR flood mapping strictly pairs images acquired under the same relative orbit (descending track 135 / ascending track 69), preventing false-positive flood detection caused by differing terrain look angles.
5. **Universal Accessibility (WCAG AA)**:
   All generated HTML reports satisfy WCAG AA contrast thresholds ($\ge 4.5:1$ for body text, $\ge 3.0:1$ for UI graphical elements) and link dynamically to `report/assets/verification.json`.

---

## 6. Information Gaps & Required Field Data

The following critical field assets should be prioritized for formal acquisition via the Official Information Act (FOI / พ.ร.บ. ข้อมูลข่าวสารฯ):

| Priority | Asset Description | Managing Authority | Role in Refining Model |
| :---: | :--- | :--- | :--- |
| **P-1** | **Route 305 Embankment Elevation Profile** | Department of Highways (DOH) | High-resolution LiDAR or as-built crown elevations to model Route 305 as a true hydraulic barrier. |
| **P-2** | **Khun Dan & Tha Chang Hourly Gate Logs** | Royal Irrigation Department (RID) | Synchronous gate opening logs during Sep–Oct 2024 to separate dam releases from ungauged tributary runoff. |
| **P-3** | **Bang Pakong Soft Clay Geotechnical Boreholes** | RID / DPT | Shear strength and consolidation profiles to evaluate canal bank stability and excavation heave risks. |
| **P-4** | **Station S.26 Continuous Daily Discharge Records** | RID Hydrology Division | 39-year continuous daily discharge series to establish the empirical diversion probability distribution. |
| **P-5** | **CPY015 Tidal Gauge Benchmark Leveling History** | Marine Department | Historical benchmark leveling surveys to isolate physical datum shifts from estuarine flood mounding. |

---

## 7. Overall System Suggestions & Consistency Recommendations

1. **Resolve Finding F-01 Immediately**:
   Update `analysis/goal7_analysis.py` to execute `analysis/goal7_ongkharak_hydraulics.py` and populate `canonical["ongkharak_hydraulics"]`. Add an explicit test in `tests/test_goal7_report.py` ensuring that `tbl_ongkharak_water_balance()` and `tbl_reach_hydraulic_vectors()` render non-empty HTML tables.
2. **Adopt Divided Channel Method (DCM) for Overbank Flow**:
   Replace composite Manning rating curves in `analysis/ny1b_hydraulic_geometry.py` with DCM to eliminate the non-physical $-87.87\text{ m}^3/\text{s}$ conveyance inversion at stage 11.00 m.
3. **Transition to 1D Dynamic Wave Hydraulic Routing**:
   Replace the empirical Muskingum-Cunge spatial tuning parameter ($n_{\text{sub}} = 12$) with a 1D implicit Saint-Venant solver, allowing rigorous representation of downstream backwater effects from the Bang Pakong confluence.
4. **Clean Up Literal Allowlist Technical Debt**:
   Audit the 76 unverified entries in `analysis/goal7/literal_allowlist.json` and migrate verified numbers into `analysis/goal7/source_constants.json` with primary PDF document citations.
5. **Align 2D Computational Mesh with Physical Watershed Boundaries**:
   Delineate the 2D Ongkharak depression model along real physical highway embankments and natural ridge lines rather than a rectangular bounding box, eliminating artificial boundary leakage (which currently vents 24.4% of the water balance).
