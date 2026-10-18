# Hydrological Audit & Red-Team Report: `nnyflood`

**Auditor Role:** Independent Senior Hydraulic Engineer & Lead Data Science Auditor (Red-Team Reviewer)  
**Evaluated Repository:** `E:\theera\code\flood` @ commit `02ba87c`  
**Execution Date:** 2026-10-18  
**Operating Mode:** Strictly Read-Only audit of codebase, data pipelines, and generated reports.

---

## 1. Executive Summary

### Overall Scientific & Engineering Reliability: **Medium for Pillar 1 (Nakhon Nayok), Low–Medium for Pillars 2–3 (National Benchmarks & Chao Phraya 2 Bypass)**

The `nnyflood` project displays a commendable standard of **software craftsmanship, automated verification, and honest self-disclosure** in several foundational areas. The testing infrastructure is active, canonical ledgers enforce consistency across older modules, and negative empirical results (such as the collapse of the Tha Chang gate-control correlation) are openly acknowledged in analysis notes. 

However, an engineering audit reveals a sharp divergence between **system provenance discipline** and **physical-mathematical validity**:
1. **Pillar 1 (Nakhon Nayok Basin)**: While cross-sectional geometry is grounded in surveyed field profiles, the core 1D hydrodynamic routing model is not a true Saint-Venant hydraulic solver. It is a Muskingum-Cunge hydrologic routing routine where 96.7% of flood flows produce negative weighting parameters ($X < 0$), forcing hard-clamping to $X = 0$ (a linear reservoir cascade). Furthermore, the composite Manning rating at Ny.1B is non-monotonic (conveyance drops above bankfull crest due to sudden wetted perimeter expansion), and the headline "9.0 m³/s overbank spill rate" is derived by subtracting two numbers calculated under incompatible hydraulic conveyance methods.
2. **Pillar 2 (National Benchmarks & Coastal ML)**: The L3 coastal-coupled machine learning model's headline 53.0% RMSE gain at +6h is measured against an artificial "uncoupled" baseline that performs *worse* than naive persistence. When evaluated against a fair tide-aware persistence benchmark, the coupled model degrades sharply at medium leads (**−41.3% at +24h, −45.1% at +48h**). Furthermore, the astronomical harmonics narrative reports "outstanding operational skill" while its own table demonstrates negative $R^2$ (−0.293) and negative skill gain relative to persistence (−3.0% at +12h, −2.7% at +24h).
3. **Pillar 3 (Chao Phraya 2 Bypass)**: The most critical policy findings rest on uncalibrated synthetic functions rather than empirical simulations. The 2011 and 2026 counterfactual runs are driven by idealized sine curves ($2200 + 2486\sin^{1.3}(t)$); the "0.53 m stage reduction" is an artifact of dividing peak diversion by an arbitrary literal ($dq/dh = 1,100\text{ m}^2/\text{s}$); the "Route 305 overtopping tipping point at +3.20 m MSL" is a hardcoded Python float identical to the Copernicus DEM median; and the published caption asserting "1m LiDAR merged with FABDEM" is factually inaccurate, as the codebase solely processes 30m Copernicus GLO-30 DSM.

### Top 3 Validated System Strengths
1. **Mechanical Quality Gates & Reproducible Invariants**: 139 of 140 automated tests pass cleanly (`verify_all.py` passes 3 of 4 core phases; SHA-256 data manifests confirm raw file integrity). Complex economic equations (Capital Recovery Factor, levelized cost of diverted water at 7%, 9%, and 12%) reproduce to the exact decimal.
2. **Self-Disclosure of Negative Modeling Results**: The codebase does not bury failed experiments. The Tha Chang case study (`analysis/thachang_leadtime.md`) transparently documents how a +0.963 short-window correlation collapsed to 0.002–0.003 across multi-season validation, warning against the "spurious correlation trap" in regulated channels.
3. **Causal Data Pipeline Design**: Machine learning pipelines enforce temporal causality without look-ahead data leakage. In `analysis/goal6_l3_coastal_model.py:245`, training rows whose future target timestamp falls within the testing window are rigorously purged, and rainfall features rely strictly on prior-calendar-day NASA POWER accumulations.

### Top 3 Critical Vulnerabilities Requiring Immediate Mitigation
1. **Synthetic Scenarios Presented as Empirical Counterfactuals (F-01)**: The 2011 mega-flood peak shaving (4,394.5 MCM diverted, 38.8% absorbed, 0.53 m stage drop) is entirely derived from an assumed mathematical sine wave, an unsourced safe discharge threshold ($2,600\text{ m}^3/\text{s}$), and an arbitrary linear rating factor ($1,100\text{ m}^2/\text{s}$). It does not model tidal lockouts or coastal backwater.
2. **Tautological Route 305 Tipping Point & Misattributed DEM Provenance (F-02, F-03)**: The +3.20 m MSL tipping point ($257.2\text{ km}^2$, 50.1% flooded) is hardcoded and mathematically equals the median elevation of the 30m DEM. The claim that this represents road overtopping lacks road crown elevation surveys, and the published claim of using "1m LiDAR / FABDEM" is contradicted by the exclusive use of 30m Copernicus DSM.
3. **Severe Narrative-to-Data Inversion in Astronomical Harmonics & Coastal ML (F-04, F-05)**: The harmonics report text claims "outstanding predictive skill" and "operational readiness" for Bangkok flood defense despite the model producing negative $R^2$ and negative skill gain against persistence across +12h to +48h leads.

---

## 2. Findings Matrix

| Finding ID | Severity | Component / Target File | Root Cause Summary | Recommended Action |
|---|---|---|---|---|
| **F-01** | **Critical** | `analysis/goal7_counterfactual_simulation.py:112-146` | 2011/2026 hydrographs are synthetic sine functions + noise; 0.53 m stage cut is an arbitrary division by $1,100\text{ m}^2/\text{s}$; tidal lockout floored at 0.80–0.84. | Label as an idealized illustrative scenario; replace with observed C.2/C.13/S.26 daily series; model actual zero-flow tidal lockouts. |
| **F-02** | **Critical** | `analysis/goal7_ongkharak_2d_depression.py:71-72` | "+3.20 m Route 305 tipping point" is a hardcoded float equal to the DEM median (3.1986 m); "50.1% flooded" is an algebraic identity of the median. | Obtain surveyed DOH road crown profile; register road crown gap in `gaps.json`; relabel as median scenario level. |
| **F-03** | **Critical** | `report/goal7_blocks.py:526` | Published report asserts analysis was conducted on "แบบจำลองระดับความสูงภูมิประเทศ 1 ม. (LiDAR ผสาน FABDEM)", but code strictly loads 30m Copernicus DSM. | Correct published report to reflect actual Copernicus 30m DSM provenance; verify vertical error bounds. |
| **F-04** | **High** | `analysis/goal6/l3_coastal_harmonics_findings.md:18-26` | Narrative claims "outstanding skill" and "ready for operational use" despite table showing negative $R^2$ (−0.293) and negative skill vs persistence (−3.0%, −2.7%). | Synthesize conclusions programmatically from metric values; remove operational readiness claims; fix `+-3.0%` format bug. |
| **F-05** | **High** | `analysis/goal6/l3_coastal_summary.json:54-118` | Headline 53.0% gain at +6h is measured against a degraded uncoupled baseline; coupled model loses to tide-aware persistence by −41.3% at +24h and −45.1% at +48h. | Frame model performance against tide-aware persistence; explicitly disclose that ML coupling degrades beyond +12h. |
| **F-06** | **High** | `analysis/hydraulic_1d_routing_summary.json:62-80`, `hydraulic_1d_routing.py:111-120` | Composite Manning rating at Ny.1B is non-monotonic ($Q$ drops from 666.3 to 578.4 m³/s at stage 11.0m); "9.0 m³/s overbank spill" subtracts incompatible methods. | Adopt monotonic divided-channel conveyance; retract 9.0 m³/s overbank spill claim; quote capacity as an uncertainty range. |
| **F-07** | **High** | `analysis/hydraulic_1d_routing.py:137, 153-154, 228-243` | Model is Muskingum-Cunge with $X$ clamped to 0 on 96.7% of flows (linear cascade); spatial refinement at fixed $\Delta t = 900\text{ s}$ violates Courant stability. | Re-evaluate convergence under constant Courant number ($\Delta t \propto \Delta x$); re-classify model as hydrologic routing without backwater dynamics. |
| **F-08** | **High** | `analysis/compound_flood_risk.py:46-49` | Formulates $\partial H_{C12}/\partial H_{tide} = 1.0$ without calibration; empirical telemetry shows $0.705 \pm 0.016$ ($18\sigma$ rejection), artificially shifting risk classes. | Fit tidal attenuation coefficient from multi-year telemetry; incorporate stage-discharge-tide interaction term. |
| **F-09** | **High** | `analysis/goal7_operational_economics.py:348-354` | 21.0 MCM dead storage depth (2.0 m) is mathematically irreconcilable with stated canal geometry (48 m bed width yields 13.9–14.4 MCM); 2.0 m geotechnical basis unsourced. | Recompute dead storage from exact trapezoidal cross-section; cite soft Bangkok clay geomechanics or label as assumption. |
| **F-10** | **High** | `report/goal7_build_public.py:362-364`, `report/goal7_build_policy_brief.py:62, 66` | Key hydrological and economic metrics are hardcoded as text literals in Goal 7 builders; test scanner only monitors Goal 6. | Extend `test_builder_source_has_no_metric_literals` to Goal 7; render all numerical figures directly from canonical JSON. |
| **F-11** | **Medium** | `analysis/compound_flood_risk.py:92-121` vs Brief | Script contains only 4 benchmarks, 2 of which are hypothetical scenarios; 2021, 2022, and 2024 historical events are absent from the code. | Clarify benchmark inventory in documentation; incorporate verified telemetry for 2021, 2022, and 2024. |
| **F-12** | **Medium** | `analysis/goal6_l3_coastal_harmonics.py:127-150` vs Brief | Harmonics decomposition is executed exclusively on CPY015 (1 station); claimed decomposition across 4 stations (C.29, BKK001, GLF002, GLF003) is absent. | Restrict claims to Bangkok Bridge (CPY015), or execute harmonic decomposition across the other estuarine gauges. |
| **F-13** | **Medium** | `analysis/goal7_operational_economics.py:43-61` | 38.3 days/year operation assumes 100% of Pa Sak runoff is diverted; alternatives benchmark unit costs (0.50–2.50 THB/m³) are unsourced literals. | Cite engineering studies for alternatives benchmark; clarify that 38.3 days is a full-capacity volumetric equivalent, not operational duration. |
| **F-14** | **Medium** | `analysis/goal6_pasak_24y_baseline.py:25, 54-55` | "Exceeded Rule Curve" is implemented as storage exceeding a static constant (871.5 MCM) rather than the dynamic seasonal Upper Rule Curve. | Compare against monthly/daily seasonal URC curves; align comparative windows between Khun Dan and Pa Sak. |
| **F-15** | **Medium** | `tests/test_legal_compliance.py:120` | PDPA scanner skips files $> 3\text{ MB}$, completely exempting the two largest published citizen HTML reports (4.79 MB and 3.87 MB). | Replace file size limit with streaming chunk reader; wire up uncalled `THAI_CITIZEN_ID` regex pattern. |
| **F-16** | **Low** | `analysis/goal7_counterfactual_simulation.py:224, 237` | Counterfactual hydrograph plot uses `#27ae60` on white, yielding contrast 2.899:1 (fails WCAG AA 3.0:1 requirement for graphical data marks). | Darken stroke color to `#1e8449` or `#196f3d` to achieve contrast $> 3.5:1$. |
| **F-17** | **Low** | `catalog.py:613-625` & `test_standards_integrity.py:72` | Reverse catalog audit fails with exit code 1 whenever audit review files (`REVIEW.*.md`) are placed in the root directory. | Add `REVIEW.*.md` pattern or audit directory to `DOC_SURFACES` / catalog registration rules. |

---

## 3. Deep-Dive Technical Findings

### [F-01] Chao Phraya 2 Counterfactual Simulation is an Idealized Sine Model
- **Location**: `analysis/goal7_counterfactual_simulation.py:112-146, 157-164`; `analysis/goal7/counterfactual_simulation_summary.json`
- **Empirical Evidence**:
  ```python
  # analysis/goal7_counterfactual_simulation.py:115
  inflow_2554 = 2200.0 + 2486.0 * (np.sin(t_54) ** 1.3)
  inflow_2554 += np.random.normal(0, 45.0, n_days_54)
  # line 139
  inflow_2569 = 1600.0 + 1380.0 * (np.sin(t_69) ** 2.2)
  # line 159
  "stage_reduction_assumption": "dh = dQ / 1,100 ตร.ม./วิ ... สมมติฐานที่เขียนไว้ ยังไม่สอบเทียบกับภาคตัดขวางที่อยุธยา"
  ```
- **Hydraulic & Data Science Critique**:
  1. The reported headline findings—diverting $4,394.5\text{ MCM}$ (38.8% of excess volume) and shaving $0.53\text{ m}$ of flood stage during the 2011 mega-flood—are direct mathematical artifacts of the synthetic equation parameters. The $0.53\text{ m}$ stage drop is obtained simply by dividing peak diverted flow ($582.9\text{ m}^3/\text{s}$) by the handpicked factor $1,100\text{ m}^2/\text{s}$ ($582.9 / 1100 = 0.5299\text{ m}$).
  2. The simulation code comments explicitly acknowledge that `safe_cap_ayutthaya = 2600.0` has no supporting reference document in the repository (`:126`).
  3. Tidal lockout at the Gulf of Thailand outlet is artificially suppressed: line 123 sets tidal efficiency to `0.92 + 0.08 * cos(...)`, meaning efficiency is clamped between 0.84 and 1.00. The code metadata admits (`:161-162`) that the canal is never subjected to real tidal lockouts or zero-discharge periods, even though coastal backwater during high sea tides would physically stall gravitational discharge.
  4. Despite these structural simplifications, chart titles in lines 237 and 240 claim "ป้องกันน้ำล้นตลิ่งได้สมบูรณ์" (completely prevented overbank flooding) and "คุมน้ำให้อยู่ในตลิ่ง 100%".
- **Proposed Solution**: Re-run the simulation using actual daily discharge records from C.2 (Nakhon Sawan), C.13 (Chao Phraya Dam), and S.26 (Rama VI Dam); replace the $1,100\text{ m}^2/\text{s}$ factor with a hydraulic rating curve surveyed at Ayutthaya (e.g., C.35 / Bang Sai); model a true tidal boundary head differential ($h_{canal} - h_{gulf}$) that allows zero discharge and reverse head; retitle figures as "Idealized Scenario Simulations".

---

### [F-02] Route 305 Overtopping Tipping Point (+3.20 m MSL) Equals DEM Median
- **Location**: `analysis/goal7_ongkharak_2d_depression.py:71-72`; `analysis/goal7/ongkharak_2d_depression_summary.json`
- **Empirical Evidence**:
  ```python
  # analysis/goal7_ongkharak_2d_depression.py:72
  stage_spill_route305 = next(c for c in curve if abs(c["stage_msl_m"] - 3.20) < 0.05)
  ```
  Executing statistical analysis on `dem_30m.npy` within the Ongkharak mask yields:
  - Valid area: $513.13\text{ km}^2$ (570,144 cells of $30\text{m} \times 30\text{m}$).
  - Elevation Percentiles: $P_{10} = 2.45\text{ m}$, $P_{25} = 2.81\text{ m}$, **$P_{50} (\text{Median}) = 3.1986\text{ m MSL}$**, $P_{75} = 3.75\text{ m}$, $P_{90} = 4.88\text{ m}$.
  - Inundated fraction at $+3.20\text{ m}$: exactly $50.1\%$.
- **Hydraulic & Data Science Critique**:
  1. The float `3.20` is hardcoded directly into the Python script. A thorough repository search reveals no Department of Highways (DOH) road cross-section, crown elevation survey, or engineering drawing establishing Route 305's elevation at $+3.20\text{ m MSL}$.
  2. Because the algorithm implements an unconstrained flat-pool bathtub fill (`ong_valid <= h_val`), the percentage of pixels submerged at $+3.20\text{ m}$ is $\approx 50\%$ *by definition of the median*. Presenting "at +3.20 m MSL, exactly 50.1% of the district ($257.2\text{ km}^2$) is inundated" as an empirical discovery is circular reasoning.
  3. The bathtub sweep ignores hydraulic connectivity, culverts, drainage gates, and road embankments. Water does not automatically overtop a highway into the Rangsit network simply because the flat regional terrain model reaches that level.
- **Proposed Solution**: Acquire official DOH / RID longitudinal road profiles for Route 305; identify the actual minimum elevation of the road crown and low saddles; register `route305_crown_elevation` as an open gap in `analysis/goal7/gaps.json`; replace "ชี้ชัดจุดเปลี่ยนวิกฤต" in report narratives with "สมมติฐานระดับอ้างอิงความสูงมัธยฐาน".

---

### [F-03] False Topographical Provenance: Copernicus 30m DSM Misrepresented as 1m LiDAR
- **Location**: `report/goal7_blocks.py:526`; `report/goal7_build_public.py:361`
- **Empirical Evidence**:
  ```python
  # report/goal7_blocks.py:526
  f"วิเคราะห์จากแบบจำลองระดับความสูงภูมิประเทศ 1 ม. (<code>LiDAR</code> ผสาน <code>FABDEM</code> และ <code>Copernicus</code> 30 ม.) — ชี้ชัดจุดเปลี่ยนวิกฤตที่ระดับ +3.20 ม.รทก."
  ```
  Checking the actual input path in `analysis/goal7_ongkharak_2d_depression.py:20`:
  ```python
  DEM_PATH = ROOT / "data/13_sentinel1_copernicus/derived/dem_30m.npy"
  ```
- **Hydraulic & Data Science Critique**:
  The calculation script exclusively loads `dem_30m.npy`, which is a 30m Copernicus GLO-30 Digital Surface Model (DSM). No 1m LiDAR or FABDEM files were loaded or processed in the generation of the hypsometric curve. Copernicus DSM measures top-of-canopy and building elevations rather than bare ground, introducing typical vertical errors of $\pm 2.0$ to $4.0\text{ m}$ in agricultural and semi-urban floodplains. Attributing 1m LiDAR precision to a 30m global radar surface model represents an unsubstantiated provenance claim.
- **Proposed Solution**: Correct the published text in `goal7_blocks.py` and `goal7_build_public.py` to state that the curve is derived from Copernicus 30m DSM; attach vertical uncertainty bands ($\pm 0.5–1.0\text{ m}$) to the stage-area-volume tables to reflect DEM noise.

---

### [F-04] Astronomical Harmonics Narrative Contradicts Negative Performance Metrics
- **Location**: `analysis/goal6/l3_coastal_harmonics_findings.md:18-26`; `analysis/goal6_l3_coastal_harmonics.py:266, 271-275`
- **Empirical Evidence**:
  From `analysis/goal6/l3_coastal_harmonics_findings.md`:
  | Forecast Lead | Model RMSE (m) | Persistence RMSE (m) | $R^2$ | Skill Gain vs Persistence (%) |
  |---|---:|---:|---:|---:|
  | **+6 Hours** | 0.600 | 0.618 | **−0.293** | +2.9% |
  | **+12 Hours** | 0.595 | 0.577 | **−0.285** | **+−3.0%** |
  | **+24 Hours** | 0.218 | 0.212 | 0.826 | **+−2.7%** |
  | **+48 Hours** | 0.392 | 0.376 | 0.375 | **+−4.2%** |

  Immediately followed by Section 3:
  ```markdown
  2. ทักษะการพยากรณ์โดดเด่นที่ระยะ +12 ชม. และ +24 ชม.: ในระยะที่คลื่นกึ่งรายวัน (M2/S2) และรายวัน (K1/O1) 
     มีบทบาทสำคัญ โมเดลให้ค่าความคลาดเคลื่อนต่ำกว่าฐานเทียบเดิมอย่างมีนัยสำคัญ
  3. พร้อมนำไปใช้งานในระบบเฝ้าระวังระดับน้ำ กทม.
  ```
- **Hydraulic & Data Science Critique**:
  1. The narrative in Section 3 is a static text block hardcoded into `goal6_l3_coastal_harmonics.py:271-275`. It asserts that the model demonstrates "outstanding forecasting skill at +12h and +24h" and is "significantly better than persistence," directly inverting the empirical results in its own table, where the model performs *worse* than persistence by −3.0% at +12h, −2.7% at +24h, and −4.2% at +48h.
  2. At +6h and +12h, $R^2$ is negative (−0.293 and −0.285), demonstrating that the harmonic model performs worse than a simple horizontal line at the empirical mean.
  3. The string formatting logic in line 266 (`f"+{le['skill_gain_vs_persistence_pct']}%"`) produces the corrupted token `+-3.0%` for negative values.
- **Proposed Solution**: Refactor `goal6_l3_coastal_harmonics.py` to synthesize descriptive narrative dynamically based on the sign of skill gains; explicitly state that the standalone 4-constituent harmonic model fails to outperform persistence across +12h to +48h; delete claims of operational readiness until predictive skill is established.

---

### [F-05] L3 Coastal-Coupled Model Relies on an Unfair Baseline and Breaks Down at $\ge 24\text{ h}$
- **Location**: `analysis/goal6/l3_coastal_summary.json:50-118`; `analysis/goal6_l3_coastal_model.py:193-196, 252-258`
- **Empirical Evidence**:
  Summary metrics from `l3_coastal_summary.json`:
  - **+6h Lead**: Persistence RMSE = 63.6 cm; Tide-aware persistence RMSE = 48.9 cm; Linear Base (uncoupled) RMSE = **79.6 cm**; Linear Coastal (coupled) RMSE = **37.4 cm**.
    - Reported Gain vs Linear Base: **+53.0%**.
    - Actual Gain vs Tide-Aware Persistence: **+23.4%** (95% CI [13.3, 32.8]%).
  - **+24h Lead**: Persistence RMSE = 21.8 cm; Tide-aware persistence RMSE = 14.3 cm; Linear Coastal RMSE = 20.2 cm.
    - Gain vs Tide-Aware Persistence: **−41.3%** (95% CI [−66.5, −19.5]%).
  - **+48h Lead**: Persistence RMSE = 39.1 cm; Tide-aware persistence RMSE = 23.4 cm; Linear Coastal RMSE = 34.0 cm.
    - Gain vs Tide-Aware Persistence: **−45.1%** (95% CI [−69.7, −23.3]%).
- **Hydraulic & Data Science Critique**:
  1. The headline claim of a "53.0% error reduction" at +6h is achieved by comparing against an artificial baseline (`linear_base_rmse_cm = 79.6 cm`) that deliberately omits tidal forcing. In an estuarine river reach governed by a ~1m semi-diurnal tidal excursion, omitting tide produces a baseline that is markedly inferior even to naive persistence (63.6 cm). Benchmarked against a proper tide-aware persistence baseline, the true gain is 23.4%.
  2. At lead times of +24h and +48h, the coupled model degrades significantly, producing errors that are **41.3% and 45.1% worse than tide-aware persistence**. The model is physically uninformative beyond 12 hours.
  3. GBDT models exhibit severe tree extrapolation failure: at +6h, GBDT coastal RMSE is 76.7 cm—more than double the linear model's 37.4 cm—because decision trees cannot extrapolate beyond the maximum training stage when predicting unprecedented flood peaks.
- **Proposed Solution**: Prominently lead with the tide-aware persistence benchmark in all published reports; restrict claims of ML tidal coupling utility strictly to short-range windows ($\le 6–12\text{ h}$); clearly document tree-based model extrapolation failure during extreme flood peaks.

---

### [F-06] Non-Monotonic Composite Conveyance at Ny.1B Undermines the "9.0 m³/s Spill Rate"
- **Location**: `analysis/hydraulic_1d_routing_summary.json:62-80`; `analysis/hydraulic_1d_routing.py:104-120`; `report/น้ำท่วมนครนายก2569_วิชาการ.html:324`
- **Empirical Evidence**:
  Rating sensitivity table at Ny.1B (`hydraulic_1d_routing_summary.json`):
  - Stage 6.86 m: $Q_{composite} = 191.2\text{ m}^3/\text{s}$, $Q_{divided} = 225.3\text{ m}^3/\text{s}$.
  - Stage 10.60 m (bankfull crest): $Q_{composite} = \mathbf{666.3\text{ m}^3/\text{s}}$, $Q_{divided} = \mathbf{893.0\text{ m}^3/\text{s}}$.
  - Stage 11.00 m (observed flood peak): $Q_{composite} = \mathbf{578.4\text{ m}^3/\text{s}}$, $Q_{divided} = \mathbf{1,009.1\text{ m}^3/\text{s}}$.
  - Academic report line 324 states:
    `"ระดับน้ำสูงสุดวัดได้ 11.00 ม.รทก. (คิดเป็นอัตราการไหล 675.3 ลบ.ม./วินาที) สูงกว่าสันตลิ่งจริง 0.40 ม. เกิดการไหลล้นข้ามสันตลิ่งออกท่วมพื้นที่ริมตลิ่งด้วยอัตราส่วนเกิน 9.0 ลบ.ม./วินาที"`
- **Hydraulic & Data Science Critique**:
  1. The composite Manning formulation $Q = \frac{1}{n} A R^{2/3} \sqrt{S} = \frac{1}{n} \frac{A^{5/3}}{P^{2/3}} \sqrt{S}$ exhibits a well-known mathematical discontinuity on compound natural cross-sections. When stage rises from 10.60 m to 11.00 m, the water surface spills onto the broad overbank terrace, causing wetted perimeter $P$ to expand dramatically while overbank area $A$ remains small. Consequently, $P^{2/3}$ increases faster than $A^{5/3}$, resulting in calculated discharge dropping by $87.9\text{ m}^3/\text{s}$ (from 666.3 down to 578.4 m³/s).
  2. The headline "9.0 m³/s overbank spill rate" ($675.3 - 666.3 = 9.0\text{ m}^3/\text{s}$) is an invalid mathematical subtraction between two incompatible numbers: 666.3 m³/s is the composite rating capacity at 10.60 m, while 675.3 m³/s was taken from an external linear interpolation or divided rating. Under composite rating, flow at 11.00 m is 578.4 m³/s (which would imply negative spill), whereas under divided conveyance, capacity is 893.0 m³/s and peak flow is 1,009.1 m³/s (difference of $116.1\text{ m}^3/\text{s}$).
  3. Citing a 9.0 m³/s spill rate as the physical mechanism that flooded upstream communities along a 120-meter wide river is unphysical; 9.0 m³/s represents just 1.3% of the river discharge, far below the standard $\pm 5–10\%$ measurement uncertainty of river gauging.
- **Proposed Solution**: Discard the single-channel composite conveyance method in favor of monotonic divided-channel conveyance (separating main channel and floodplains with distinct Manning's $n$); remove the "9.0 m³/s" spill figure and its causal narrative from all published reports; express bankfull capacity as an explicit range ($488.9–893.0\text{ m}^3/\text{s}$).

---

### [F-07] 1D Routing Formulation is Muskingum-Cunge with Clamped Negative Parameters
- **Location**: `analysis/hydraulic_1d_routing.py:123-164, 228-243`; `analysis/hydraulic_1d_routing_summary.json:8-17, 111-133`
- **Empirical Evidence**:
  ```python
  # analysis/hydraulic_1d_routing.py:153-154
  x_param = 0.5 * (1.0 - q_ref / (b_avg * slope * c_wave * dx_sub))
  x_param = max(0.0, min(0.45, x_param))  # เสถียรภาพตัวแปร
  ```
  `hydraulic_1d_routing_summary.json` confirms:
  - `x_raw_min = -3.364`, `x_raw_max = 0.219`, `negative_share = 0.967` (raw $X$ is negative across 96.7% of the discharge range).
  - Grid convergence study at fixed $\Delta t = 900\text{ s}$:
    - $n_{sub} = 6$: $Q_{peak} = 591.7\text{ m}^3/\text{s}$, RMSE = 126.4 m³/s.
    - $n_{sub} = 12$: $Q_{peak} = 613.0\text{ m}^3/\text{s}$, RMSE = 128.8 m³/s.
    - $n_{sub} = 24$: $Q_{peak} = 627.5\text{ m}^3/\text{s}$, RMSE = 130.2 m³/s.
    - $n_{sub} = 48$: $Q_{peak} = 638.9\text{ m}^3/\text{s}$, RMSE = 131.1 m³/s.
- **Hydraulic & Data Science Critique**:
  1. The model is Muskingum-Cunge hydrologic routing, not a full 1D hydrodynamic (Saint-Venant) solver. It contains no momentum conservation equation, no downstream stage boundary condition (Kgt.30), no backwater modeling capability, and no lateral inflow/spill exchange.
  2. The Cunge spatial parameter criterion requires $\Delta x \ge \frac{q}{B \cdot S_0 \cdot c}$. When $\Delta x$ is small (as occurs when dividing the reach into 12–48 sub-reaches), this condition is violated and raw $X$ becomes negative across 96.7% of flood flows. Clamping $X = 0.0$ degenerates the formulation into a cascade of linear storage reservoirs, introducing heavy artificial numerical diffusion.
  3. The grid convergence experiment held time step constant at $\Delta t = 900\text{ s}$ while reducing $\Delta x$. For $n_{sub} \ge 24$, the routing reach travel time $K = \Delta x / c$ drops below $400\text{ s}$, violating the numerical stability constraint $\Delta t \le 2K(1 - X)$. This instability explains why peak discharge increased by +8.0% and RMSE degraded at finer grid resolutions.
- **Proposed Solution**: Explicitly re-label the module as "Muskingum-Cunge Hydrologic Routing" rather than "1D Hydrodynamic Routing"; calibrate $K$ and $X$ from observed reach attenuation; if backwater or floodplain storage is required, implement a true 1D dynamic wave formulation (e.g. Preissmann 4-point implicit scheme or HEC-RAS 1D unsteady flow).

---

### [F-08] Compound Flood Risk Formula Assumes Rigid Unit Tidal Transfer
- **Location**: `analysis/compound_flood_risk.py:31-50, 67-88`
- **Empirical Evidence**:
  ```python
  # analysis/compound_flood_risk.py:46-48
  c1 = 0.132
  head_loss = c1 * ((q_bangsai / 1000.0) ** 1.28)
  stage = tide_msl + wave_setup_m + head_loss
  ```
  Code comments in lines 37-41 concede:
  `"สถานะการสอบเทียบ (ตรวจ 17 ต.ค. 69): ยังไม่สอบเทียบหลายปี — ไม่มีสคริปต์สอบเทียบ และไม่มี artifact ของการ fit ใน repo · c1 และเลขชี้กำลังเป็นค่าประมาณที่ตั้งให้ผ่านจุดตรวจ 2 จุด ... ไม่ใช่การถดถอยจากอนุกรมเวลา"`
- **Hydraulic & Data Science Critique**:
  1. The formulation strictly imposes $\frac{\partial H_{C12}}{\partial H_{tide}} = 1.000$, asserting that sea level rises at the river mouth propagate without damping or amplification to C.12 Samsen (~35 km upstream). Regressing empirical hourly telemetry between C.12 and CPY015 over the 1,931 common hours in the repository yields an empirical transfer slope of **$0.705 \pm 0.016$** in the tidal frequency band. The assumed unit slope is rejected at $18\sigma$ statistical significance.
  2. The upstream discharge head loss term $c_1 (Q/1000)^{1.28}$ was fitted to exactly two points ($Q=2500, H_{tide}=2.00 \rightarrow 2.51\text{ m}$; $Q=3500, H_{tide}=2.30 \rightarrow 3.04\text{ m}$). Fitting two parameters ($c_1$ and the exponent 1.28) through two data points leaves zero degrees of freedom, providing zero out-of-sample validation.
  3. The model completely omits non-linear discharge-tide interaction terms ($Q \times H_{tide}$), ignoring how high fluvial momentum suppresses tidal wave propagation and increases ebb friction.
- **Proposed Solution**: Calibrate a multi-parameter empirical response surface $H_{C12} = \beta_0 + \beta_1 H_{tide} + \beta_2 Q^{\alpha} + \beta_3 (Q \cdot H_{tide})$ using multi-year telemetry from C.12, CPY015, and C.29A; attach confidence intervals to matrix cell predictions.

---

### [F-09] Canal Dead Storage Volume Mathematically Inconsistent with Geometry
- **Location**: `analysis/goal7_operational_economics.py:345-360`; `report/goal7_blocks.py:542`
- **Empirical Evidence**:
  Stated parameters:
  - Canal length $L = 135.9\text{ km} = 135,900\text{ m}$.
  - Bed width $b = 48.0\text{ m}$.
  - Design depth $H = 7.0\text{ m}$, Side slopes $z = 1.5$ to $2.5$.
  - Stated values: `total_storage_mcm = 55.4`, `dead_storage_depth_m = 2.0`, `dead_storage_mcm = 21.0`, `active_storage_mcm = 34.4`, `buffer_duration_hours = 15.9`.
- **Hydraulic & Data Science Critique**:
  1. Computing the trapezoidal volume for a 2.0 m water layer:
     - For side slope $z = 1.5$: $A_{dead} = [48.0 + 1.5(2.0)] \times 2.0 = 51.0 \times 2.0 = 102.0\text{ m}^2$.  
       $V_{dead} = 102.0\text{ m}^2 \times 135,900\text{ m} = 13,861,800\text{ m}^3 = \mathbf{13.86\text{ MCM}}$.
     - For side slope $z = 2.5$: $A_{dead} = [48.0 + 2.5(2.0)] \times 2.0 = 53.0 \times 2.0 = 106.0\text{ m}^2$.  
       $V_{dead} = 106.0\text{ m}^2 \times 135,900\text{ m} = 14,405,400\text{ m}^3 = \mathbf{14.41\text{ MCM}}$.
  2. To achieve the stated $21.0\text{ MCM}$ in a 2.0 m depth over 135.9 km, the average water surface width would need to be $\frac{21,000,000}{135,900 \times 2.0} = \mathbf{77.26\text{ m}}$, whereas the actual top width at 2.0 m depth is only $54.0–58.0\text{ m}$. The $21.0\text{ MCM}$ figure is mathematically impossible under the stated cross-section.
  3. If true dead storage is $\approx 14.0\text{ MCM}$, the active storage buffer is $55.4 - 14.0 = \mathbf{41.4\text{ MCM}}$ (yielding a buffer duration of $\approx \mathbf{19.2\text{ hours}}$ at $600\text{ m}^3/\text{s}$, rather than 15.9 hours).
  4. The technical assertion that maintaining a 2.0 m dead storage pool is "geotechnically necessary to prevent slope failure in soft Bangkok clay" is completely unsourced in the repository.
- **Proposed Solution**: Derive canal dead and active storage volumes programmatically from surveyed cross-sections; adjust the active storage figure to $\approx 41.4\text{ MCM}$ and buffer duration to $19.2\text{ hours}$; cite geotechnical slope stability analysis or label the 2.0 m minimum pool as an engineering assumption.

---

### [F-10] Hardcoded Numerical Metric Literals in Goal 7 Report Builders
- **Location**: `report/goal7_build_policy_brief.py:62, 66, 129, 196-197`; `report/goal7_build_public.py:364, 407, 516`; `report/goal7_build_academic.py:289-290`
- **Empirical Evidence**:
  - `report/goal7_build_policy_brief.py:62`: `'      <div id="res_annual" ...>13,416</div>\n'`
  - `report/goal7_build_policy_brief.py:66`: `'      <div id="res_cost_m3" ...>6.81</div>\n'`
  - `report/goal7_build_policy_brief.py:196`: `"พบว่ามีภาระเงินลงทุนรายปี 12,897 ล้านบาท/ปี รวมกับค่าบำรุงรักษาเป็น <b>13,416 ล้านบาท/ปี</b> "`
  - `report/goal7_build_public.py:364`: `"ด้วยปริมาตรสะสมสูงถึง <b>126.22 ล้าน ลบ.ม.</b> ครอบคลุมพื้นที่ 257.2 ตร.กม. (ร้อยละ 50.1 ของอำเภอ) "`
  - `tests/test_goal6_consistency.py:111-139` only checks an 11-item hardcoded blacklist across Goal 6 builders.
- **Hydraulic & Data Science Critique**:
  This directly breaches the core architectural contract in `AGENTS.md` ("builder ห้ามพิมพ์ตัวเลข metric เป็น literal — TLDR/บท/ตารางเรนเดอร์จาก JSON เท่านั้น"). If canonical economic or hydrological parameters are updated, Goal 7 reports will silently desynchronize from the underlying analysis.
- **Proposed Solution**: Template all numerical values in `goal7_build_*.py` directly from `analysis/goal7/canonical.json`; extend `test_builder_source_has_no_metric_literals` to cover all scripts in `report/`.

---

### [F-11] Historical Benchmark Classifications Diverge from Code Inventory
- **Location**: `analysis/compound_flood_risk.py:92-121`
- **Empirical Evidence**:
  The commissioning brief states:
  > "Compound Flood Risk Matrix ... benchmarked against 5 historical flood events (2011, 2021, 2022, 2024, 2026)."
  
  Inspection of `historical_benchmarks` in `analysis/compound_flood_risk.py`:
  1. `มหาอุทกภัยปี 2554 (จุดสูงสุด ต.ค. 54)`
  2. `ระลอกปลาย ก.ย. 2569 (เหตุการณ์จริง)`
  3. `กรณีสมมติ: ระลอก 2569 หากเกิดน้ำทะเลหนุนสูงสุด (+2.40 ม.)`
  4. `กรณีสมมติ: ผันน้ำด้วยคลองเจ้าพระยา 2 (-600 ลบ.ม./วิ)`
- **Hydraulic & Data Science Critique**:
  The codebase contains only 4 benchmarks, two of which are hypothetical scenarios rather than historical occurrences. Historical flood events from 2021, 2022, and 2024 are completely absent from `compound_flood_risk.py`.
- **Proposed Solution**: Align documentation with actual code capabilities; incorporate historical peak discharge and tidal telemetry for 2021, 2022, and 2024 into `compound_flood_risk.py`.

---

### [F-12] Astronomical Harmonics Fitted Exclusively on One Station
- **Location**: `analysis/goal6_l3_coastal_harmonics.py:127-150`
- **Empirical Evidence**:
  The commissioning brief claims:
  > "Classical harmonic constituents ($M_2, S_2, K_1, O_1$) decomposed across 4 key estuarine stations (C.29, BKK001, GLF002, GLF003)..."
  
  In `goal6_l3_coastal_harmonics.py`:
  ```python
  c12_data = load_hourly(RAW_L1 / "2599_C.12_2026_hourly.json")
  cpy015_data = load_hourly(RAW_L1 / "4_CPY015_2026_hourly.json")
  bkk001_data = load_hourly(RAW_L1 / "11_BKK001_2026_hourly.json")
  # line 147
  harmonics_meta, harmonics_fn = fit_astronomical_harmonics(train_dts, train_cpy015)
  ```
- **Hydraulic & Data Science Critique**:
  Harmonic decomposition is performed only on station CPY015 (Bangkok Bridge). Stations GLF002, GLF003, and C.29 are never decomposed. Furthermore, phases are referenced to an arbitrary local timestamp ($t_0 = \text{2026-07-01 00:00}$) rather than Greenwich Mean Time, rendering them incomparable to standard amphidromic tidal atlases.
- **Proposed Solution**: Expand `goal6_l3_coastal_harmonics.py` to extract constituents across all 4 estuarine stations, or amend the documentation to reflect that only CPY015 was analyzed; reference phase angles to Greenwich equilibrium arguments ($V_0 + u$).

---

### [F-13] S.26 Full-Capacity Operating Days and Alternative Costs Rest on Upper-Bound Assumptions
- **Location**: `analysis/goal7_operational_economics.py:24-68, 112-137`
- **Empirical Evidence**:
  ```python
  # line 43
  days_avg = round(s26_stats["flood_season_mean_mcm"] / cap_day, 1)  # 1988.0 / 51.84 = 38.3 วัน
  # line 44
  days_flood = round(min(s26_stats["annual_max_mcm"] / cap_day, 80.0), 1)
  # line 61
  diverted_volume_mcm = 1970.0  # vs 1988.0 in line 32
  ```
- **Hydraulic & Data Science Critique**:
  1. The figure of 38.3 days/year assumes that *100% of the entire flood-season runoff* at S.26 is diverted into the canal at full capacity ($600\text{ m}^3/\text{s}$). In reality, diversion occurs only when downstream river stages exceed flood stage thresholds and intake gates can physically operate.
  2. The maximum flood year days calculation in line 44 ($6,741 / 51.84 = 130.0\text{ days}$) is arbitrarily capped at `80.0` days to match a predetermined narrative ("60–80 วัน").
  3. The alternatives benchmark table (lines 112–137) lists unit costs for retention basins (0.50–1.20 THB/m³) and polders (1.50–2.50 THB/m³) as raw unsourced string literals.
- **Proposed Solution**: Derive annual diverted volumes from a routed daily series reflecting hydraulic operating rules; cite primary engineering sources for alternative flood mitigation costs.

---

### [F-14] Pa Sak 24-Year Exceedance Evaluated Against Static Capacity Rather than Seasonal Rule Curve
- **Location**: `analysis/goal6_pasak_24y_baseline.py:25, 53-56, 185`
- **Empirical Evidence**:
  ```python
  NORMAL_CAP = 871.5  # constant
  for r in y_rows:
      q = float(r.get("DMD_QUse_curr") or 0)
      if q >= NORMAL_CAP:
          days_over_normal += 1
  ```
- **Hydraulic & Data Science Critique**:
  A reservoir Rule Curve is a dynamic seasonal trajectory, deliberately lower during July–September to maintain flood control headspace, and rising toward 100% conservation capacity in November. Evaluating "URC exceedance" against a fixed constant number ($871.5\text{ MCM}$) misclassifies standard reservoir operations as exceedances. Furthermore, comparing Khun Dan over 22 years (9/22) against Pa Sak over 24 years (17/24) creates an inconsistent baseline comparison.
- **Proposed Solution**: Digitized the official RID seasonal Upper Rule Curve for Pa Sak Dam; evaluate daily storage against the corresponding day-of-year URC threshold; align analysis windows across comparative dams.

---

### [F-15] PDPA Compliance Scanner Silently Bypasses Published Reports Exceeding 3 MB
- **Location**: `tests/test_legal_compliance.py:45, 111-135`
- **Empirical Evidence**:
  ```python
  # line 45
  THAI_CITIZEN_ID = re.compile(r"(?<![\d])\b[1-8]\d{12}\b(?![\d])")
  # line 120
  if not fpath.exists() or fpath.stat().st_size > 3_000_000:
      continue
  ```
  File size inspection:
  - `report/น้ำท่วมนครนายก2569_ประชาชน.html`: **4,790,483 bytes (4.79 MB)**
  - `report/ระลอกปลายกย2569.html`: **3,869,394 bytes (3.87 MB)**
- **Hydraulic & Data Science Critique**:
  Because both published HTML reports exceed 3,000,000 bytes, `test_enhanced_pdpa_no_citizen_identities()` skips them entirely. Consequently, the two largest public-facing documents in the repository are completely unmonitored for phone numbers and land title deeds. Furthermore, `THAI_CITIZEN_ID` is compiled on line 45 but never called anywhere in the test function.
- **Proposed Solution**: Remove the 3 MB file size bypass, utilizing streaming or chunked reading; wire `THAI_CITIZEN_ID.search(text)` into the assertion loop.

---

### [F-16] WCAG AA Graphical Contrast Failure in Counterfactual Simulation Plots
- **Location**: `analysis/goal7_counterfactual_simulation.py:224, 237`
- **Empirical Evidence**:
  The hydrograph line for the Chao Phraya 2 bypass scenario is styled with `color="#27ae60"` on a white background (`#ffffff`).
  - Relative luminance of `#27ae60`: $L = 0.3122$.
  - Contrast ratio against white: $\frac{1.0 + 0.05}{0.3122 + 0.05} = \mathbf{2.899:1}$.
  - WCAG 2.1 AA Criterion 1.4.11 requires a minimum contrast of **3.0:1** for graphical objects and data marks.
- **Hydraulic & Data Science Critique**:
  The color fails WCAG AA legibility criteria for graphical marks, making the simulated hydrograph difficult to distinguish for visually impaired users.
- **Proposed Solution**: Darken `#27ae60` to `#1e8449` ($L = 0.201$, contrast **4.18:1**) or `#196f3d` ($L = 0.146$, contrast **5.36:1**).

---

### [F-17] Reverse Catalog Audit Fails on Unregistered Root Review Files
- **Location**: `catalog.py:613-625`; `tests/test_standards_integrity.py:71-76`
- **Empirical Evidence**:
  Running `python catalog.py audit` or `python tools/verify_all.py` fails with:
  ```
  AssertionError: พบเอกสารที่ยังไม่ลงทะเบียนใน catalog.py (root *.md หรือ docs/*.md):
    REVIEW.Claude-Sonnet-5.5.md
    REVIEW.deepseek-v4.1-flash-free.md
    REVIEW.space-bunny-free.md
  ```
- **Hydraulic & Data Science Critique**:
  `test_all_top_level_docs_are_registered` enforces that every markdown file matching `*.md` at the root must be registered in `catalog.CORE_GOVERNANCE`. When external audit reviewers follow the standard instruction to output `REVIEW.<model>.md` in the root directory, the test suite breaks.
- **Proposed Solution**: Update `DOC_SURFACES` in `catalog.py` to exclude `REVIEW.*.md`, or establish an approved subfolder `docs/reviews/` for external audit reports.

---

## 4. Verified Invariants (Passed Spot-Checks)

The following metrics, equations, and data pipelines were independently audited and verified to be 100% mathematically and methodologically correct:

| Invariant Item | Audit Verification Method | Result & Exact Value | Verification Status |
|---|---|---|:---:|
| **Capital Recovery Factor (CRF) & Levelized Cost** | Independent Python recalculation of $CRF = \frac{r(1+r)^n}{(1+r)^n - 1}$ across 30-year life. | $r=7\% \rightarrow CRF = 0.080586$, Annualized CAPEX = $12,897.4\text{ MB}$, Total = $13,416.4\text{ MB}$, Unit Cost = **$6.81\text{ THB/m}^3$**; $r=9\% \rightarrow 0.097336 \rightarrow$ **$8.17\text{ THB/m}^3$**; $r=12\% \rightarrow 0.124144 \rightarrow$ **$10.35\text{ THB/m}^3$**. | **PASS (100% faithful)** |
| **Canal Conveyance Volume** | Dimensional unit analysis: $600\text{ m}^3/\text{s} \times 86,400\text{ s} / 10^6$. | Exactly **$51.84\text{ MCM/day}$**. | **PASS** |
| **Emergency Storage Buffer Duration** | Arithmetic check: $34.4\text{ MCM} / 51.84\text{ MCM/day} \times 24\text{ h}$. | Exactly **$15.93\text{ hours}$** (arithmetically verified for the stated $34.4\text{ MCM}$ active pool). | **PASS** |
| **Ongkharak Basin DEM Hypsometry** | Independent recomputation on `dem_30m.npy` masked with `mask_district_อำเภอองครักษ์.npy`. | Total Area = $513.13\text{ km}^2$; Inundated area at +3.20m = $257.0\text{ km}^2$; Volume = $126.22\text{ MCM}$; Mean depth = $0.49\text{ m}$ (exact byte match across all 36 elevation tiers). | **PASS** |
| **Temporal Train/Test Purging in Coastal ML** | Code inspection of `goal6_l3_coastal_model.py:245`. | Training records whose target lead time ($t + \text{lead}$) falls on or after 2026-09-20 are purged ($N_{train} = 1087, 1078, 1066$ for $+6, +24, +48\text{ h}$). | **PASS** |
| **Prior-Day Rainfall Feature Causality** | Code inspection of `goal6_l3_coastal_model.py:175-179`. | NASA POWER rainfall is strictly extracted from the previous calendar day; zero forward-looking leakage. | **PASS** |
| **Full Unit & Integration Test Suite** | Execution of `pytest tests/ -k "not test_all_top_level_docs_are_registered"`. | **139 passed in 22.29s** across artifacts, contrast, core, goal6, goal7, integrity, legal, naming, privacy, and language lint. | **PASS** |
| **Legal Compliance & Privacy Safeguards** | Execution of `pytest tests/test_legal_compliance.py tests/test_privacy.py`. | **18 passed in 10.73s**; zero defamatory terms, 3-tier disclaimer stacks confirmed on all 7 published reports. | **PASS** |
| **Thai Language & Typo Integrity** | Execution of `pytest tests/test_thai_language_lint.py`. | Zero registered typos, zero banned technical jargon variants, zero word collisions. | **PASS** |
| **Raw Data Integrity & Catalog Coverage** | Execution of `catalog.py check` & `verify_data_integrity.py --quick`. | 105 catalogue paths exist on disk; all SHA-256 raw checksums match. | **PASS** |

---

## 5. Information Gaps & Required Field Data

The following critical parameters cannot be fully audited or verified due to missing primary source agency data:

1. **Route 305 Road Crown Profile & Saddle Survey**:
   - *Requirement*: Official Department of Highways (DOH) longitudinal centerline elevation survey and bridge approach elevations along Route 305 (Rangsit–Nakhon Nayok Road) to establish the true physical overtopping threshold.
2. **Multi-Year Hourly Discharge Telemetry ($Q$) for C.12, CPY015, and C.29A**:
   - *Requirement*: Archived multi-year telemetry from the Royal Irrigation Department (RID) and Marine Department to calibrate the non-linear compound flood backwater formulation and determine empirical estuarine tidal wave attenuation.
3. **Chao Phraya 2 Canal Cross-Sectional Geometry & Bed Longitudinal Profile**:
   - *Requirement*: Official detailed design CAD / cross-sectional survey from RID to resolve the discrepancy between stated geometry ($b=48\text{ m}, h=7\text{ m}$) and the $21.0\text{ MCM}$ dead storage volume.
4. **Geotechnical Embankment & Clay Slope Stability Analysis**:
   - *Requirement*: Geotechnical soil mechanics reports justifying the mandatory $2.0\text{ m}$ minimum water cushion required to prevent rapid drawdown slope failure in soft Bangkok clay.
5. **Tha Chang Regulator Hourly Gate Logbooks**:
   - *Requirement*: Official operational logbooks recording gate opening heights and discharge rates at Tha Chang regulator to empirically test the "gate control vs routing trap" hypothesis.
6. **High-Resolution Bare-Earth LiDAR for Ongkharak Basin**:
   - *Requirement*: 1m bare-earth DTM (filtering out vegetation canopy and buildings) referenced to the Thai National Vertical Datum (ม.รทก.) to replace the 30m Copernicus radar surface model.
7. **Long-Term Sea Level Records for Harmonic Analysis**:
   - *Requirement*: Multi-year continuous hourly tidal gauge data from Fort Chula (GLF001) and Bangkok Bridge (CPY015) to perform rigorous Greenwich-epoch tidal harmonic analysis with nodal corrections and constituent separation ($K_1 / P_1$).

---

## 6. Auditor Sign-Off & Suggested Priority Order

1. **Priority 1 (Integrity & Physical Grounding)**: Address **F-01**, **F-02**, **F-03**, and **F-04**. Remove claims that counterfactuals and tipping points are empirically derived; correct the 1m LiDAR provenance assertion; reconcile the astronomical harmonics narrative with actual table numbers.
2. **Priority 2 (Model Framing & Capacity Realism)**: Address **F-05**, **F-06**, **F-07**, and **F-09**. Frame the L3 coastal ML model against tide-aware persistence; fix the non-monotonic composite conveyance curve at Ny.1B; retract the 9.0 m³/s spill rate; correct canal dead storage volume calculations.
3. **Priority 3 (Consistency & Robustness)**: Address **F-08**, **F-10**, **F-14**, and **F-15**. Calibrate the compound backwater model against multi-year telemetry; eliminate hardcoded metric literals in Goal 7 report builders; fix the PDPA scanner file-size bypass.
4. **Priority 4 (Documentation & Standards)**: Address **F-11**, **F-12**, **F-13**, **F-16**, and **F-17**. Darken plot line colors to satisfy WCAG AA; update the catalog reverse audit to accommodate review files.
