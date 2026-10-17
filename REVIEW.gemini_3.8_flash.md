# Hydrological Audit & Red-Team Report: nnyflood

**Auditor Profile**: Independent Senior Hydraulic Engineer & Lead Data Science Auditor (Red-Team Reviewer)  
**Target Repository**: `tkittich/nnyflood` (Pillars 1–3, Goals 1–7)  
**Evaluation Date**: October 17, 2026  
**Verification Tools Executed**: `tools/verify_all.py`, `catalog.py check`, `pytest tests/`, `verify_data_integrity.py`  

---

## 1. Executive Summary

- **Overall Scientific & Engineering Reliability**: **Medium (Conditional)**  
  The codebase exhibits exceptional empirical telemetry ingestion, strict Thai language linting, robust legal/PDPA compliance, and a disciplined canonical ledger architecture. However, substantial hydrodynamic oversimplifications, synthetic input hydrographs masquerading as empirical observations, uncoupled constant boundary conditions, and internal rating curve contradictions prevent it from attaining an unqualified "High" engineering reliability rating for mission-critical hydraulic design.

- **Key System Strengths**:
  1. **Disciplined Provenance & Automated Quality Gates**: 100% pass rate across 121 pytest unit/integration tests, zero unhandled data integrity mismatches, and fully automated verification (`tools/verify_all.py`).
  2. **Empirical Multi-Reservoir Baseline Modeling**: High-precision 22-year (Khun Dan) and 24-year (Pasak) reservoir mass balance analysis that accurately disentangles normal conservation storage, surcharge retention pools, and structural dam overtopping without sensationalism.
  3. **Multi-Scale Estuarine Machine Learning**: Innovative integration of semidiurnal astronomical tidal harmonics ($M_2$) and upstream river telemetry at C.12 Samsen, successfully achieving a 50.5% RMSE reduction at a +6h lead time.

- **Critical Vulnerabilities & Limitations**:
  1. **Synthetic Hydrographs Labeled as Historical Measurements**: In `analysis/goal7_counterfactual_simulation.py`, the 2011 mega-flood and 2026 inflow series are generated from idealized sine functions with artificial Gaussian noise rather than official RID telemetry (C.13 / S.26 / C.29A), while chart legends labeled them as observed discharge.
  2. **Uncoupled Constant Boundary Conditions in "Coastal ML"**: In `analysis/goal6_l3_coastal_model.py`, the SWAN wave height feature is a single static post-event scalar ($H_s = 0.0968\text{ m}$) broadcast across all 2,400 hourly timesteps, contributing zero real predictive variance.
  3. **Unresolved Rating Contradiction at Station Ny.1B**: The canonical ledger and telemetry pipeline maintain mutually contradictory bankfull discharge estimates for Ny.1B ($244.6\text{ m}^3/\text{s}$ vs. $666.3\text{ m}^3/\text{s}$), stemming from uncorrected datum shifts and out-of-bank extrapolation beyond official rating curves.

---

## 2. Findings Matrix

| Finding ID | Severity | Component / Target File | Root Cause Summary | Recommended Action |
|---|---|---|---|---|
| **F-01** | **Critical** | `analysis/goal7_counterfactual_simulation.py:102,123` | 2011 and 2026 counterfactual flood hydrographs are idealized sine waves rather than empirical RID hydrographs. | Ingest historical daily discharge series from C.13 (Chao Phraya) and S.26 (Rama VI). |
| **F-02** | **Critical** | `analysis/build_canonical_numbers.py:127` vs. `analysis/hydraulic_1d_routing.py:158` | Dual conflicting canonical bankfull discharges for Ny.1B ($244.6\text{ m}^3/\text{s}$ vs. $666.3\text{ m}^3/\text{s}$). | Harmonize datum reference and calibrate multi-stage composite rating curve. |
| **F-03** | **High** | `analysis/goal7_counterfactual_simulation.py:108,126` | Constant 84–100% tidal diversion efficiency ignores coastal backwater choking during astronomical spring tides. | Implement 1D backwater equation or reduce gravity diversion efficiency to 15–20% during peak surge. |
| **F-04** | **High** | `analysis/compound_flood_risk.py:39-42` | Linear superposition of discharge and tide neglects hydrodynamic backwater flattening ($\partial^2 H / \partial Q \partial H_{tide} \equiv 0$). | Introduce non-linear coupling term or calibrate 2D shallow-water surrogate. |
| **F-05** | **High** | `analysis/goal6_l3_coastal_model.py:102-111` | SWAN wave height input is a single scalar post-event mean ($H_s = 0.0968\text{ m}$) broadcast to all hours. | Connect dynamic hindcast/reanalysis wave timeseries or explicitly remove static feature. |
| **F-06** | **High** | `analysis/goal6_l3_coastal_model.py:113` | Documented 2020–2026 training span is actually restricted to July 1 – Sept 20, 2026 ($N=1,130$ hours). | Correct documentation and model metadata to reflect actual 3-month sample size. |
| **F-07** | **Medium** | `analysis/compound_flood_risk.py:96,160` | Inconsistent 2026 event tidal stage ($1.91\text{ m}$ in JSON vs. $2.12\text{ m}$ on chart), shifting risk band from Watch to Warning. | Synchronize plotting marker with canonical CPY015 peak ($1.91\text{ m}$). |
| **F-08** | **Medium** | `analysis/hydraulic_1d_routing.py:8,148` | Kgt.30 cross-section loaded but completely unused; no downstream boundary condition implemented. | Remove unused file references or implement downstream stage-controlled routing. |
| **F-09** | **Medium** | `data/20_multistation_levels/st61.csv`, `st62.csv` | Asynchronous Q and H peaks within the same station (+6.5h at Ny.1B, -8.75h at Ny.7) invalidate raw `argmax` travel times. | Calculate flood wave celerity via cross-correlation of stage ($H$) series rather than unverified $Q$. |
| **F-10** | **Low** | `analysis/goal7_counterfactual_simulation.py:77` | Stage reduction uses hardcoded divisor `1100.0`, contradicting the inline comment derivation ($B \times v \approx 375$). | Reconcile mathematical derivation with empirical stage-discharge sensitivity. |

---

## 3. Deep-Dive Technical Findings

### [F-01] Synthetic Hydrographs Labeled as Historical Inflow Series
- **Location**: `analysis/goal7_counterfactual_simulation.py:99-106, 120-125`
- **Empirical Evidence**:
  ```python
  # Lines 101-105:
  inflow_2554 = 2200.0 + 2486.0 * (np.sin(t_54) ** 1.3)
  inflow_2554 += np.random.normal(0, 45.0, n_days_54)

  # Lines 123-124:
  inflow_2569 = 1600.0 + 1380.0 * (np.sin(t_69) ** 2.2)
  inflow_2569 += np.random.normal(0, 25.0, n_days_69)
  ```
- **Hydraulic & Data Science Critique**:  
  The counterfactual evaluation of the Chao Phraya 2 Bypass Canal ($600\text{ m}^3/\text{s}$ design capacity) claims to demonstrate that the project would have absorbed $4,394.5\text{ MCM}$ (40.0% of excess flood volume) during the 2011 mega-flood. However, the inflow entering Ayutthaya is not constructed from observed RID daily discharge logs at C.13 (Chao Phraya Dam) and S.26 (Rama VI Dam). Instead, it is an idealized mathematical waveform generated by exponentiated sine curves with synthetic Gaussian noise. This obscures realistic multi-peak storm hydrographs, prolonged upstream retention plateaus, and genuine operational gate adjustments.
- **Proposed Solution**:  
  Replace synthetic formulas with actual daily gauged records from `data/23_rid_swoc/raw/` for August 1 – November 30, 2011, and September 15 – October 15, 2026. If synthetic curves must be used for sensitivity tests, explicitly label them as "Parametric Synthetic Scenario" rather than "Actual 2554 / 2569 Flood".

---

### [F-02] Conflicting Dual Canonical Bankfull Discharges for Station Ny.1B
- **Location**: `analysis/canonical_numbers.json` (lines 127 vs. 211) & `analysis/build_canonical_numbers.py`
- **Empirical Evidence**:
  - `analysis/canonical_numbers.json:127`: `"ny1b_q_bankfull": 244.6`
  - `analysis/canonical_numbers.json:211`: `"r1d_ny1b_q_bankfull": 666.3`
  - Surveyed cross-section `Ny.1B_profile.csv` calculates bankfull conveyance at elevation $+10.60\text{ m MSL}$ as $666.3\text{ m}^3/\text{s}$ ($A = 471.8\text{ m}^2, n = 0.0437, S = 0.00065$).
  - RID official telemetry metadata (`data/23_rid_swoc/raw/rid_telemetry_cross_sections.json`) reports `braelevel: 8.81 m` and `QMax: 266.9 m³/s`.
- **Hydraulic & Data Science Critique**:  
  There is a $2.7\times$ discrepancy between the two bankfull figures in the same repository. The lower figure ($244.6\text{ m}^3/\text{s}$) corresponds to the within-bank capacity before water spills onto the low right-bank terrace at $+8.81\text{ m MSL}$. The higher figure ($666.3\text{ m}^3/\text{s}$) integrates the entire cross-section up to $+10.60\text{ m MSL}$, applying a single uniform Manning's roughness coefficient ($n = 0.0437$). Applying channel roughness to heavily vegetated floodplains overestimates conveyance by 30–50%. Furthermore, having both numbers listed as canonical invariants violates the single-source-of-truth contract.
- **Proposed Solution**:  
  Formally define two distinct metrics in `canonical_numbers.json`:
  1. `ny1b_main_channel_bankfull_q_cms = 244.6` (at bank elevation $+8.81\text{ m MSL}$)
  2. `ny1b_valley_full_q_cms = 666.3` (at top-of-dike elevation $+10.60\text{ m MSL}$, divided using composite roughness $n_{channel}=0.038, n_{floodplain}=0.075$).

---

### [F-03] Over-Optimistic Tidal Diversion Efficiency for Chao Phraya 2 Floodway
- **Location**: `analysis/goal7_counterfactual_simulation.py:108, 126`
- **Empirical Evidence**:
  ```python
  # Line 108:
  tide_eff_54 = 0.92 + 0.08 * np.cos(np.linspace(0, 8 * math.pi, n_days_54))
  ```
- **Hydraulic & Data Science Critique**:  
  The counterfactual model assumes that the 111-km bypass canal maintains an efficiency of 84% to 100% (average 92%) regardless of tide phase. In reality, the lower reach of the canal slopes across flat delta terrain ($S_0 \approx 1:30,000$) discharging into the Gulf of Thailand. During astronomical spring tides, high sea levels (+2.00 to +2.40 m MSL) penetrate deep inland, reversing or severely choking gravity drainage. In fact, `report/goal7_build_public.py:576` explicitly documents that gravity drainage drops to $100\text{ m}^3/\text{s}$ (~17% efficiency) during peak tide. The simulation's assumption of continuous 84–100% capacity would require a massive $500\text{ m}^3/\text{s}$ pumping station, which is absent from official EIA gravity canal designs.
- **Proposed Solution**:  
  Couple canal drainage efficiency to daily sea level at Fort Chula / CPY015:
  $$\eta_{tide}(t) = \max\left(0.15, \frac{H_{canal\_head} - H_{tide}(t)}{H_{canal\_head} - H_{mean\_sea}}\right)$$
  Recompute the 2011 absorbed volume under true gravity lockout conditions.

---

### [F-04] Additive Linear Superposition in Compound Flood Risk Formulation
- **Location**: `analysis/compound_flood_risk.py:30-43`
- **Empirical Evidence**:
  $$H_{C12} = H_{tide} + \Delta h_{wave} + c_1 \cdot \left(\frac{Q}{1000}\right)^{1.28}$$
  where $c_1 = 0.132$, $\Delta h_{wave} = 0.08\text{ m}$.
- **Hydraulic & Data Science Critique**:  
  This equation treats estuarine flood stage as a simple uncoupled summation. In open-channel fluid dynamics, the stage at C.12 Samsen is governed by the non-linear interaction of river discharge and coastal boundary head. High downstream tide increases water depth $y$, increasing flow area $A$ and hydraulic radius $R$, which *reduces* friction slope $S_f = n^2 Q^2 / (A^2 R^{4/3})$. Under this equation, $\partial H_{C12} / \partial H_{tide} \equiv 1.0$ at all times, meaning a 10 cm tide rise at the river mouth transmits 100% undamped to C.12 regardless of upstream river discharge. This violates Saint-Venant shallow water physics.
- **Proposed Solution**:  
  Incorporate a cross-product attenuation term:
  $$H_{C12} = H_{tide} \cdot \exp\left(-\frac{x}{L_d}\right) + \Delta h_{wave} + c_1 \left(\frac{Q}{1000}\right)^\alpha \cdot \left(1 - \beta \frac{H_{tide}}{y_0}\right)$$
  Calibrate coefficients $\alpha, \beta$ against simultaneous C.12, C.29A, and CPY015 telemetry during high and low flow regimes.

---

### [F-05] Pseudo-Coupled SWAN Wave Feature in L3 Coastal Machine Learning Model
- **Location**: `analysis/goal6_l3_coastal_model.py:102-111, 176`
- **Empirical Evidence**:
  ```python
  swan_hs = 0.8
  if SWAN_FILE.exists():
      sw = json.loads(SWAN_FILE.read_text(encoding="utf-8"))
      waves = [float(s["wave_height_sig_m"]) for s in sw if s.get("wave_height_sig_m") is not None]
      if waves:
          swan_hs = float(np.mean(waves))  # Evaluates to 0.0968 m
  feat_coastal = feat_base + [tide0, tide_diff, tide_head, tide_phase_sin, tide_phase_cos, swan_hs]
  ```
- **Hydraulic & Data Science Critique**:  
  `SWAN_FILE` (`data/25_gulf_marine_tides/raw/gulf_wave_summary.json`) contains only 31 spatial stations recorded at a single snapshot (`2026-10-16T19:00:00+07:00`). The script computes the mean across these 31 points ($0.0968\text{ m}$) and appends this identical scalar to every single hour across the entire July–October 2026 dataset. In linear regression, a zero-variance column is absorbed into the intercept; in GBDT, it cannot serve as a split candidate. The claim that the model couples SWAN wave heights is scientifically invalid—the model is driven solely by CPY015 tide telemetry and astronomical phase harmonics.
- **Proposed Solution**:  
  Either acquire hourly dynamic SWAN wave height reanalysis timeseries matching the training/testing period, or remove `swan_hs` from the feature vector and update project documentation to accurately state that the model is "Tidal-Coupled" rather than "Wave-Coupled".

---

### [F-06] Sample Size and Historical Scope Mismatch in Coastal Model Documentation
- **Location**: `analysis/goal6_l3_coastal_model.py:113` vs. `docs/REVIEW_PROMPT_EN.md`
- **Empirical Evidence**:
  - `docs/REVIEW_PROMPT_EN.md` checklist: *"Train: 2020–2026 wet seasons up to Sep 20; Test: Sep 20 – Oct 9, 2026"*
  - Code implementation:
    ```python
    start_dt = dt.datetime(2026, 7, 1, 0, 0)
    end_dt = dt.datetime(2026, 10, 9, 23, 0)
    ```
  - Summary artifact (`analysis/goal6/l3_coastal_summary.json`): $N_{train} = 1,130$, $N_{test} = 262$.
- **Hydraulic & Data Science Critique**:  
  The documentation describes a multi-year training regime across 6 wet seasons (2020–2026). In fact, the model is trained exclusively on 47 effective days (July 1 to September 20, 2026). While a 1,130-hour sample size is sufficient for a 14-parameter linear regression, it is severely undersized for non-linear gradient-boosted decision trees (HistGradientBoostingRegressor), explaining why GBDT overfits and performs worse than Linear Regression at +24h and +48h.
- **Proposed Solution**:  
  Update all technical reports and prompts to state the true sample scope (July 1 – September 20, 2026). If multi-year data is available in `data/22_goal6_network/`, expand the hourly loader to ingest 2020–2025 records.

---

### [F-07] Discrepant Historical Benchmark Parameters in Compound Risk Matrix
- **Location**: `analysis/compound_flood_risk.py:96` vs. `:160`
- **Empirical Evidence**:
  - In `historical_benchmarks` JSON table (line 96):
    `"q_bangsai_m3s": 2250, "tide_msl_m": 1.91, "c12_stage_msl_m": 2.36` (Categorized as `watch`)
  - In matplotlib plot routine (line 160):
    `("2569 (จริง)", 2250, 2.12, "blue", "o")`
    which evaluates to `c12_stage_msl_m = 2.57` (Categorized as `warning`).
- **Hydraulic & Data Science Critique**:  
  The summary JSON states that the September 2026 flood produced a C.12 stage of $+2.36\text{ m MSL}$ (falling safely in the yellow "Watch" category $<2.40\text{ m}$). However, the generated PNG image (`report/assets/compound_flood_risk_matrix.png`) plots the 2026 event at Tide $= +2.12\text{ m MSL}$, displaying a stage of $+2.57\text{ m MSL}$ squarely in the orange "Warning" zone. This visual discrepancy creates confusion for public stakeholders assessing whether the 2026 flood breached municipal warning thresholds.
- **Proposed Solution**:  
  Change line 160 to use the verified CPY015 peak tide:
  ```python
  ("2569 (จริง)", 2250, 1.91, "blue", "o"),
  ```
  and re-run `python analysis/compound_flood_risk.py`.

---

## 4. Verified Invariants (Passed Spot-Checks)

The following components were audited and verified to be mathematically, empirically, and procedurally correct:

1. **Pasak Dam 24-Year Baseline & Surcharge Storage Separation**:
   - `analysis/goal6_pasak_24y_baseline.py` correctly reads 8,425 days from `data/23_rid_swoc/raw/pasak_dam_history_2003_2026.json`.
   - Verified that peak storage in 2010 ($1,177.22\text{ MCM}$, 135.1%) and 2011 ($1,086.34\text{ MCM}$, 124.7%) correctly utilized the designed surcharge retention buffer below the physical crest elevation ($+44.5\text{ m MSL}$) without structural dam overtopping.
2. **Khun Dan 22-Year Baseline Anomaly Calculation**:
   - `analysis/goal2_khundan_22y_baseline.py` correctly parses 7,811 daily records.
   - The median peak storage day-of-year is confirmed at Day 306.5 (early November), verifying that the September 27 peak in 2026 occurred **36.5 days earlier than historical median**, marking it as one of only two September peaks in 22 years (2013 and 2026).
3. **Causal Boundary in Trailing Rainfall Engineering**:
   - `analysis/goal6_l3_coastal_model.py:158-159` computes $R_{24}$ using the strictly preceding calendar date `d_prev = t_curr - 1 day`. Re-execution confirms zero look-ahead data leakage across the lead window.
4. **Automated Thai Language and Typo Registry Linting**:
   - `pytest tests/test_thai_language_lint.py` passed all 10 test suites, confirming zero banned loanwords ("พีค", "คาลิเบรต", "baseline"), zero grammatical collision patterns, and correct hierarchical substitution.
5. **Data File Integrity and Standards Governance**:
   - All 84 registered files in `catalog.py` exist on disk (`catalog.py check` passed).
   - `tools/verify_all.py` completed with 0 errors across SHA-256 raw checks, linting, and 121 unit tests.

---

## 5. Information Gaps & Required Field Data

The following critical hydraulic parameters currently rely on empirical approximations due to unreleased agency data:

1. **High-Resolution Bathymetry of Nakhon Nayok River (Reach Ny.1B to Ny.7)**:
   - Current 1D Muskingum-Cunge routing interpolates between only two surveyed cross-sections across 18.3 km. Meander geometry, riffle-pool sequences, and bridge pier contractions are unrepresented. Detailed river bathymetry (ADCP cross-sections every 500 m) is required.
2. **RID Radial Spillway & Sluice Gate Operation Logs (Khun Dan Dam)**:
   - Daily SWOC records only provide aggregate daily outflow (`DMD_Outflow_curr`). Minute-by-minute gate opening logs (radial spillway vs. bottom outlet conduits) are unavailable, preventing direct physical verification of gate maneuver timing during the night of September 26, 2026.
3. **Chao Phraya 2 Bypass Canal Headworks & Flap-Gate Specs**:
   - Siphon headloss coefficients, diversion weir intake curves at Chainat, and flap-gate specifications at the Gulf of Thailand outlet remain locked within unpublished Royal Irrigation Department detailed engineering design reports (2023–2026 revisions).
