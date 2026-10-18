# Hydrological Audit & Red-Team Report: `nnyflood`

**Auditor role:** Independent Senior Hydraulic Engineer / Lead Data Science Auditor (Red-Team)
**Repository:** `E:\theera\code\flood` @ `02ba87c` (working tree clean)
**Date:** 2026-10-18
**Mode:** Strictly read-only. No repository file was modified, created, or deleted. No git write operations. All scratch work was confined to `C:/Users/theera/AppData/Local/Temp/opencode/audit/`.

---

## 1. Executive Summary

### Overall Scientific & Engineering Reliability: **Medium** — with high variance across pillars

The project is genuinely strong on **evidence provenance and self-correction discipline**, and genuinely weak on **whether the headline hydraulic numbers are physically identified**. The two are in inverse proportion: the parts of the codebase with the best documentation are the parts with the least model risk, and the parts carrying the most policy weight (the 1D routing travel time, the Chao Phraya 2 storage/tipping-point claims) rest on hard-coded literals that the documentation presents as derived results.

**Key System Strengths (validated, not asserted):**

1. **Provenance discipline is real and verifiable.** `tools/verify_all.py` passes 4/4; `catalog.py check` 105/105; `catalog.py audit` 33/33; `pytest` **140/140 passed in 21.20 s**; `verify_data_integrity --quick` MISMATCH 0. SHA-256 manifests exist for every large raw asset. I reproduced the canonical ledgers against their generating code and they are byte-faithful (e.g. I independently recomputed all 36 rows of the Ongkharak hypsometric curve from `dem_30m.npy` — **0/36 mismatches** against the committed JSON).
2. **The negative results are published, not buried.** The Tha Chang "Gate-Control vs Routing Trap" case study (F-21) correctly demolishes its own headline: the raw short-window correlation of **+0.963** collapses to **+0.273** after detrending and to a cross-season fitted coefficient of **0.002–0.003** (`analysis/thachang_leadtime.md`, `analysis/goal4_thachang_model.md`). This is exactly the kind of self-refutation the project should be doing and rarely does.
3. **The canonical-ledger / retired-value machinery works.** The previously-recorded "17/22 vs 16/22 vs 20/22" Pasak ambiguity is now closed in `analysis/goal6/canonical.json → pasak_year_counts` with four explicitly separated definitions across two different year sets, and the builder comment at `report/goal6_build_report4_draft.py:81` documents the fix (`เดิม hardcode 17/22 ผิดจาก JSON 20/22`). I confirmed the rendered report now reads 20 of 22.

**Critical Vulnerabilities & Limitations (top 3):**

1. **Load-bearing numbers that are literals dressed as computations.** The Chao Phraya 2 "+3.20 m Route 305 tipping point" is a Python float in a `next(...)` selector (`analysis/goal7_ongkharak_2d_depression.py:72`); the "9.0 m³/s overbank discharge" is a subtraction of two mutually inconsistent quantities; the 1D travel time of 3.25 h is imposed by a hard-coded kinematic-wave celerity `c = 5v/3` in a reach where the Froude number is **0.15**. In each case the surrounding prose — including a published caption claiming "1 m LiDAR merged with FABDEM" when the input is 30 m Copernicus GLO-30 DSM — asserts a derivation that does not exist.
2. **The single largest policy figure is falsified by the project's own telemetry.** `analysis/compound_flood_risk.py` hard-codes `∂H_C12/∂H_tide = 1.0`. Regressing C.12 on CPY015 over the repo's own 1,931 common hours gives **0.827 ± 0.019** (raw) and **0.705 ± 0.016** in the tidal band. The assumed 1.000 is rejected at **18σ**. Substituting the empirical slope reclassifies **all four published risk levels**, including the Chao Phraya 2 "prevents critical flooding" scenario from `critical` → `watch`.
3. **Statistical uncertainty is reported with a method that is invalid for the data structure.** The L3 coastal model's 95 % CIs come from an iid percentile bootstrap on hourly residuals whose lag-1 autocorrelation is **+0.931 (+24 h)** and **+0.940 (+48 h)** — integrated autocorrelation time 14–16 h against `n_test = 226`. A moving-block bootstrap widens the +24 h interval from **[−0.1, 12.3] %** to **[−3.4, 23.8] %**. The published CI excludes zero by 0.1 percentage points; the correlation-aware CI does not exclude zero at all.

---

## 2. Findings Matrix

| ID | Severity | Component / Target | Root Cause Summary | Recommended Action |
|---|---|---|---|---|
| F-01 | **Critical** | `analysis/goal7_ongkharak_2d_depression.py:71-72` | "+3.20 m Route 305 tipping point" is a hard-coded Python float selected by `next(c for c in curve if abs(c["stage_msl_m"] - 3.20) < 0.05)`. No road layer, no crown elevation, no derivation anywhere. | Do not publish as a computed result. Either source the crown elevation or relabel as a scenario assumption and add a `gaps.json` entry + `# gap:` tag. |
| F-02 | **Critical** | `report/goal7_blocks.py:526` | Published caption claims "แบบจำลองระดับความสูงภูมิประเทศ 1 ม. (LiDAR ผสาน FABDEM และ Copernicus 30 ม.)". Actual input is 30 m Copernicus GLO-30 **DSM**, EPSG:4326, bilinear-resampled. No LiDAR exists in the repo. | Correct the caption to the actual provenance; add a provenance assertion test that fails if a rendered caption names a data source absent from `data/`. |
| F-03 | **Critical** | `analysis/hydraulic_1d_routing.py:150` | Kinematic-wave celerity `c_wave = (5.0/3.0)*v_est` hard-coded, but the reach is deeply subcritical (Fr = 0.13–0.22). No downstream boundary condition. | Replace with a diffusive/dynamic solver, or calibrate the storage coefficient K directly from the observed H→H lag. Withdraw 3.25 h until then. |
| F-04 | **Critical** | `analysis/hydraulic_1d_routing.py:228-243, 284-293` | Grid study varies `n_sub` at **fixed Δt = 900 s**. Stability criterion Δt ≤ 2K(1−X) is violated at n_sub ≥ 24. Restoring stability moves the answer 3–13×. | Redo the convergence study at constant Courant number; report the stability margin per configuration; treat n_sub = 12 as an unstable-adjacent artefact, not a result. |
| F-05 | **High** | `analysis/hydraulic_1d_routing_summary.json:51-53` | Boundary condition (Ny.1B `q_cms`) peaks **6.5 h after** its own stage; validation target (Ny.7 `q_cms`) peaks **8.75 h before** its own stage. The directly comparable observed Q→Q lag (**24.25 h**) is never published. | Publish the Q→Q lag alongside Q→Q model output, or convert the station series to a single rating curve. |
| F-06 | **High** | `analysis/hydraulic_1d_routing.py:176-191` | Headline "Ny.1B 666.3 vs Ny.7 617.4 m³/s" uses slope 6.5e-4 at Ny.1B and 3.5e-4 at Ny.7. On a common slope Ny.1B is **21 % lower**. `n = 0.0437` is a single-point fit to an undocumented project rating, applied to a station whose datum the repo flags as unconfirmed (GL-08). | State capacities on a common, sourced slope; attach an uncertainty band derived from the slope range, not from the conveyance method alone. |
| F-07 | **High** | `report/build_report_html.py:338`, `report/build_expert_report.py:353` | Published "อัตราน้ำบ่าล้นตลิ่ง 9.0 ลบ.ม./วินาที" and a causal claim built on it, while the model's own rating gives **578.4 m³/s** at the observed peak stage 11.00 m (less than at the crest). | Remove the 9.0 m³/s figure and the causal sentence. It is not recoverable from any rating. |
| F-08 | **Critical** | `analysis/compound_flood_risk.py:47-49` | `∂H_C12/∂H_tide = 1.0` hard-coded; repo telemetry gives 0.705 ± 0.016 (18σ rejection). All four published risk levels change. | Calibrate the tidal transfer coefficient (and make it stage-dependent). Until then, do not publish absolute risk classes. |
| F-09 | **High** | `analysis/compound_flood_risk.py:46-47` | `c1 = 0.132` and exponent `1.28` are perfectly confounded; reparameterising while preserving the single check-point moves the 2011 stage from 3.14 m to 3.58 m. | Fit both coefficients against a real time series, or drop the exponent to 1.0 and report the residual bias explicitly. |
| F-10 | **High** | `report/goal6_build_report4_draft.py:311-338` | The JSON carries four explicit limitations; the builder renders only the thresholds, benchmarks and image. Report 4 publishes the matrix with **no** caveat. | Render `metadata.limitations` into the report body (the repo already has the `# gap:` machinery for this). |
| F-11 | **High** | `analysis/goal6_l3_coastal_harmonics.py:273-274` | Findings document claims "ทักษะการพยากรณ์โดดเด่นที่ระยะ +12 ชม. และ +24 ชม." while its own table shows −3.0 % and −2.7 % (worse than persistence); claims operational readiness from R² = −0.293. | Rewrite section 3 of the findings MD from the table. Delete the operational-readiness claim. |
| F-12 | **Medium** | `analysis/goal6_l3_coastal_harmonics.py:101` | Phases are epoch-relative to `t0 = first training timestamp` and are the **negation** of the standard harmonic argument (`atan2(-b, a)` = 360 − g). No equilibrium argument, nodal factor, or inference. Fit R² = 0.8966 is never reported. | Report g and inference; document the sign convention; publish the fit R² and residual. |
| F-13 | **High** | `analysis/goal6_l3_coastal_model.py:82-93` | iid percentile bootstrap on residuals with lag-1 autocorrelation 0.93–0.94; effective n ≈ 14–16, not 226. | Switch to a moving-block bootstrap with block ≥ integrated autocorrelation time; report both. |
| F-14 | **Medium** | `analysis/goal6/canonical.json → l3_coastal_coupled`, `l3_coastal_harmonics` | Two incompatible "L3 Coastal-Coupled Model" implementations for the same target/station/period (53 % skill gain vs negative skill) are both registered with no reconciliation. | Add a reconciliation note, or supersede one. |
| F-15 | **High** | `report/goal6_build_report3_draft.py:676-677` | Hard-coded "15 ก.ย. เก็บ 8,004 ล้าน ลบ.ม." — source data has **7,986.87** on 15 Sep and **8,004.38** on 16 Sep. Second literal "7,776 → 8,202 ใน 15 วัน" spans 6 Sep → 21 Sep = **16 days**. | Render from `dam_history_all.json`; add a test that recomputes any inline dam-storage literal from source. |
| F-16 | **High** | `report/goal7_build_public.py:362,364` | Published HTML contains **both** `257.0` (canonical table) and `257.2` (prose literal) for the same stage; plus `81.3 ตร.กม. / 19.3 ล้าน ลบ.ม.` vs computed `36.84 / 19.03` (**+121 %** area error). | Render all from canonical. Extend `test_builders_have_no_crest_range_literal` to the Ongkharak block. |
| F-17 | **High** | `tests/test_goal6_consistency.py:111-139`, `tests/test_legal_compliance.py:45,120` | Literal scanner is an 11-item deny-list, one entry (`banned_literals`) is dead code. `THAI_CITIZEN_ID` defined but never called. Files > 3 MB skipped from the PDPA scan, excluding the two largest published reports. | Replace the deny-list with a numeric+unit regex scan; wire up `THAI_CITIZEN_ID`; scan report bodies via a streaming reader rather than a size gate. |
| F-18 | **Medium** | `report/goal7_build_policy_brief.py:33,45`, `report/goal7_common.py:54,97,107`, `report/report_assets.py:227,253` | WCAG AA failures: text `#d97706` on `#fff` = **3.19:1**, `#0284c7` on `#fff`/`#f6f9fb` = **4.10 / 3.87:1**; six graphical marks at **1.69–2.63:1** on white. Zero contrast coverage for any Goal 7 output. | Extend the contrast test's source list to the goal7 builders and add a DOM/cascade resolution pass. |
| F-19 | **Medium** | `analysis/canonical_numbers.json:200,202,880`, `analysis/goal7/canonical.json`, `START_HERE.md:167` | `bankfull` still overloaded (6.86 / 8.21 / 2.50 m); "12 %" carries three distinct meanings; `goal7/canonical.json` (331 KB) has **no `definitions` block**. | Add a `definitions` block to the goal7 canonical; add a collision test on key names. |
| F-20 | **Medium** | `analysis/attribution_share.json → lag_sensitivity` | The 88:12 headline varies **10.3 %–29.3 %** across the routing-lag assumption, carries no error bars, and excludes dam abstraction and the water pipeline (a one-sided bias). | Publish the lag sensitivity band with the headline, or pre-register the lag. |
| F-21 | **Medium** | `analysis/goal4_thachang_model.md`, `report/build_expert_report.py:304-309` | The null cross-season coefficient (0.002–0.003) is presented as evidence that **gates** control the stage. No gate records exist in the repo. | Restate as "no upstream signal detectable at these leads"; list gate control as one of several untested candidate mechanisms. |
| F-22 | **High** | `analysis/goal7_operational_economics.py:348-354` | `total_storage_mcm 55.4`, `dead_storage_depth_m 2.0`, `dead_storage_mcm 21.0`, `active_storage_mcm 34.4`, `buffer_duration_hours 15.9` are **all bare literals**, not computed from the section stated three lines above. 21.0 MCM in a 2.0 m layer implies a 77 m mean top width; the stated section gives 54 m. | Compute from a sourced cross-section; cite the geotechnical basis for the 2.0 m or drop the claim. |
| F-23 | **Medium** | `analysis/compound_flood_risk.py:92-121` | `historical_benchmarks` contains two entries explicitly labelled `กรณีสมมติ` (hypothetical). | Rename the key or split `historical_benchmarks` / `hypothetical_scenarios`. |
| F-24 | **Low** | Audit brief vs `analysis/goal6/l3_coastal_summary.json`, `analysis/goal4_model_v1_results.json` | The commissioning brief quotes stale figures (73.6→35.9 cm / 51.2 %; 57.1 % coverage; +6 h RMSE 0.17 m; Pasak 17/22). Canonical values are **79.6→37.4 / 53.0 %**, **47.1 %**, **0.30 m**, **20/22**. | Re-baseline external citations against `canonical.json` before the next review round. |
| F-25 | **Low** | `analysis/hydraulic_1d_routing.py:243` | Model output variance is an order of magnitude too smooth: `std(Δ²Q_sim) = 4.74` vs `std(Δ²Q_obs) = 30.02` m³/s. 48 sequential smoothing passes act as a heavy low-pass filter. | Treat the routing output as a smoothed hydrograph, not a discharge prediction; do not compare it to raw station series without noting this. |
| F-26 | **High** | `analysis/goal7_counterfactual_simulation.py:120-123, 161-162` | The outlet tidal efficiency is hard-coded as `0.92 + 0.08·cos(...)` / `0.90 + 0.10·cos(...)`, **floored at 0.84 / 0.80**. The code's own limitations text admits lockout is never represented: *"ประสิทธิภาพถูกจำกัดต่ำสุดที่ 0.80–0.84 ไม่เคยเป็น 0 ทั้งที่รายงานระบุว่าผิวน้ำในคลองจะนิ่งตอนน้ำขึ้นสูงสุด"*. | Implement a real gate/pump-outlet boundary (tide vs canal invert), or report the 38.8 % / 0 % results as upper bounds. |
| F-27 | **High** | `analysis/goal7_counterfactual_simulation.py:113-116, 128` | The 2011 inflow is `2200 + 2486·sin(0…π)^1.3` — a **61-day rise and 61-day fall**, peak 4,727 m³/s. Real 2011 at Ayutthaya peaked ~6,200 m³/s with a ~10–15 d rise and ~30 d recession. The excess-volume denominator also rests on `safe_cap_ayutthaya = 2600`, which the code comments as **having no supporting document in the repo**. | Source the safe-capacity threshold and replace the sine with a measured or published 2011 hydrograph. |
| F-28 | **Medium** | `analysis/goal7_operational_economics.py:57-61` | `annual_diverted_mcm = 1970.0` is arithmetically the same statistic as the "38.3 days/year at full capacity" utilisation figure (1,970 MCM ≡ 38.0 days at 600 m³/s). The levelised unit cost and the 10.5 % utilisation claim therefore share one unmeasured ancestor. | Present them as one assumption with a stated band, not as two independent findings. |
| F-29 | **Low** | `analysis/goal7/operational_economics.py:141-236` | The ONEP objection record is well structured — **16 `key_objections` verified**, each with an EIA section locator ("ข้อ 1.1", "ข้อ 1.10", "ข้อ 5.4" …), and the disputed EIRR (14.52 %), the 3-year construction impossibility, the Thiessen averaging objection and the 7-year return-period misinterpretation are all recorded verbatim. But only **1 of 16** carries a page citation. The letter is issued by **สผ.** (ONWR's Planning & Policy Office), not ONEP (สพน.) — a different agency. | Add page locators to the remaining 15; correct the agency attribution in external citations. |
| F-29b | **High** | `report/goal7_blocks.py:457-461` | **A one-sentence paraphrase is published under the caption "📄 ข้อความจากหนังสือราชการจริง" ("text from the actual official letter").** Its entire content is a restatement; zero letter text. It also names a subcommittee — "คชก. ด้านพัฒนาแหล่งน้ำ" — that the letter does not mention (it says only "คณะกรรมการผู้ชำนาญการฯ"). Rendered into reports 7, 8 and the policy brief. | Relabel the toggle "สรุปข้อค้นพบ (ไม่ใช่ข้อความต้นฉบับ)" or insert a verbatim excerpt; drop the unverified subcommittee name. |
| F-30 | **High** | `analysis/goal7_operational_economics.py:141-229` vs the scanned letter in `data/manual/…/EIA/` | **0 of 16 recorded objections carry a verbatim excerpt or page citation.** `eia_excerpts.json` (all 17 entries) documents **none** of them. **8 of 16** carry section labels whose chapter titles contradict the letter's actual chapters — e.g. ch. 6 of the letter is *air quality / noise and vibration*, while the repo labels fish biomass as "ข้อ 6.2". Separately, "16 ข้อสั่งการ" is a report construction: the letter is a chapter x item hierarchy running to **16+ chapters and 50+ items**. | Re-derive the 16 with page locators, or relabel "16 ประเด็นที่คัดเลือก". Fix the chapter mapping. |
| F-31 | **High** | `analysis/goal7_operational_economics.py:146` + 8 downstream sites | **4-day date contradiction, and the wrong value reaches every published surface.** The scanned letter header reads ๑๔/๒๕๖๒ (14 Feb). Internal modules agree: `goal7_analysis.py:287`, `canonical.json:1325/4162`, `data/manual/manifest.md:243`, `docs/REVIEW_PROMPT.md:65` → **14 ก.พ. 2562**. But `goal7_operational_economics.py:146` → `canonical.json:5259/5266/5273/7439` → `GOAL7_POLICY_BRIEF.md:29,102` → `goal7_build_policy_brief.py:225` → `goal7_build_public.py:502,505,506` → the shipped HTML → **18 ก.พ. 2562**. | Reconcile against the scan and propagate. Gloss BE→CE once (2562 BE = 2019 CE). |
| F-32 | **High** | `analysis/goal7_operational_economics.py:167` | The objection asserts the 3-year build made the economic return "(**EIRR 14.52%**) สูงเกินจริง". **14.52 % is not a คชก. number** — `canonical.json:1441` sources it to "บทที่ 8 หน้า 784 (สรุปผู้บริหาร)", i.e. the **EIA report's own executive summary** — the applicant's own figure. | Attribute 14.52 % to the EIA, not to the committee; or cite the letter text. |
| F-33 | **High** | `analysis/goal7_operational_economics.py:347` vs `analysis/goal7_analysis.py:307` | `bed_width_m = 48.0` is uncited and **contradicts the only sourced cross-section in the repo**: `EIA_SECTION` gives A = 504 m², D = 7.0, z1 = 3.0, z2 = 2.0 (EIA vol. 1, pp. 2-39, Fig. 2.3.2-11) → **implied bed width 54.5 m**, and 504 m² x 135.9 km = **68.5 MCM, not 55.4 MCM**. `goal7_analysis.py:510` records `"bed_m": None` — the main EIA module has no bed width at all. | Source the bed width, or delete the 55.4 MCM figure. |
| F-34 | **Medium** | `analysis/goal7_operational_economics.py:58-61` vs `analysis/goal7_analysis.py:982` | The LCC excludes land compensation **21,794,378,164 baht (13.62 % of the 160,046 MB capex)** — OCR-verified in the measures letter — and has **no opportunity-cost line at all**. Whether 160,046 already contains it is UNVERIFIED. If not: LUC 6.81 → **7.70 THB/m³** (+13.1 %). | Break out land/compensation as a separate flagged line. |
| F-35 | **Medium** | `analysis/goal7_operational_economics.py:43,45,50,52` | "days_average_year" and "annual_utilization_avg_pct" are computed from `flood_season_mean_mcm` (1,988 MCM), **not the annual mean** (2,720 MCM, line 30). The annual mean gives **52.5 days / 14.38 %** — 37 % higher. Separately `days_flood` is silently truncated by `min(6741/51.84, 80.0)`: 130.0 → **80.0**, with a comment ("สูงสุด ~60-80 วัน") that contradicts the computation. | Rename the fields or use the annual mean; remove the `min(..., 80.0)` cap. |
| F-36 | **High (process)** | `tests/test_standards_integrity.py:60-72` vs `HANDOFF.md:18` | **The repo's own governance instructions contradict each other.** `HANDOFF.md:18` tells the next AI session to save the review to the root as `REVIEW.<model_name>.md`. But `test_all_top_level_docs_are_registered` has **no allowlist** for `REVIEW.*.md` (docstring: "กฎนี้ไม่มี allowlist: ไฟล์ใหม่ต้องลงทะเบียนหรือย้ายออกจากพื้นที่"). **Following the instruction necessarily fails the suite** — observed live: 139 passed / 1 failed, listing all three `REVIEW.*.md` files. | Add `REVIEW.*.md` / `TRIAGE.*.md` to an explicit allowlist, or point deliverables at `docs/reviews/`. **Needs your decision — see §7.1.** |

---

## 3. Deep-Dive Technical Findings

### [F-01] The "+3.20 m Route 305 tipping point" is a hard-coded float, and it is the median elevation

- **Location:** `analysis/goal7_ongkharak_2d_depression.py:71-72`

  ```python
  # 3. จุดเริ่มบ่าล้นคันทางหลวง 305 (+3.20 ม.รทก.)
  stage_spill_route305 = next(c for c in curve if abs(c["stage_msl_m"] - 3.20) < 0.05)
  ```

  Propagated as literals to `report/goal7_blocks.py:511,526` and `report/goal7_build_public.py:363`.

- **Empirical evidence:**
  - `3.20` occurs nowhere in the repository as a measured quantity. `grep -rn` across `data/` and `analysis/` for a Route 305 crown elevation returns **only** a geotag coordinate (`analysis/album_geotag_map.py:34`) and a water-depth observation on the carriageway (`analysis/album_geotag_summary.md:50`: "ทล.305 กม.41+800 … ระดับน้ำ 10–35 ซม."), neither of which is a crown elevation.
  - The DEM median is **3.1986 m** (`ongkharak_2d_depression_summary.json → elevation_stats_m.median = 3.20`). Because the "curve" is a bathtub threshold sweep (`ong_valid[ong_valid <= h_val]`, lines 41-51), the stage at which exactly 50 % of the mask is submerged **is** the median by construction.
  - Consequence: `inundated_share_pct = 50.1 %` at +3.20 m is an algebraic identity, not independent evidence. The brief's pairing of "median +3.19 m" and "50.1 % of district" is the same fact stated twice.
  - `analysis/goal7/gaps.json` contains **no** entry for road-crown elevation (22 entries enumerated; the nearest is `ground_level_table`, which concerns the dam–canal longitudinal profile).

- **Hydraulic & Data Science Critique:**
  The word "ชี้ชัดจุดเปลี่ยนวิกฤต" ("clearly identifies the critical tipping point") in `report/goal7_blocks.py:526` is an overclaim. There is no independent physical criterion anywhere in the code that distinguishes 3.20 m from 3.10 m or 3.30 m. Additionally, the model has **no outflow term of any kind** — grepping the script for `weir|outflow|drain|outlet|canal|flow|routing|spill` returns only the three `volume_mcm` keys. So the 257.0 km² / 126.22 MCM triple is a static water-level map with no connectivity constraint, no time dimension and no drainage. The narrative "น้ำบ่าข้ามถนนเข้าสู่โครงข่ายคลองรังสิตโดยตรง" (water overtops the road directly into the Rangsit canal network) is attached to a grid line, not to a computed flow path.

- **Proposed Solution:** Either (a) obtain the crown elevation from ONWR/RID and re-derive the threshold from the surveyed profile, or (b) relabel +3.20 m explicitly as an assumed scenario value, register it in `analysis/goal7/gaps.json` (e.g. `route305_crown_elevation`, `status: open`), and tag the sentence with `# gap: route305_crown_elevation` so the existing test can enforce it. Delete "ชี้ชัด".

---

### [F-02] The published DEM provenance is false

- **Location:** `report/goal7_blocks.py:526`

  ```python
  f"วิเคราะห์จากแบบจำลองระดับความสูงภูมิประเทศ 1 ม. (<code>LiDAR</code> ผสาน <code>FABDEM</code> "
  f"และ <code>Copernicus</code> 30 ม.) — ชี้ชัดจุดเปลี่ยนวิกฤตที่ระดับ +3.20 ม.รทก."
  ```

- **Empirical evidence:**
  - `analysis/goal7_ongkharak_2d_depression.py:20` → `DEM_PATH = ROOT / "data/13_sentinel1_copernicus/derived/dem_30m.npy"`.
  - `analysis/s1_masks.py:65-87` builds it from `Copernicus_DSM_COG_10_*_DEM.tif` with `resampling=Resampling.bilinear` into `EPSG:4326`.
  - `data/08_dem_topography/manifest.md:5` — "Copernicus DEM GLO-30 … ความละเอียด 30 ม."
  - `data/08_dem_topography/manifest.md:18` — the product is a **DSM** (includes vegetation and buildings), not a DTM.
  - `data/08_dem_topography/fabdem/manifest.md:5` — "ความละเอียด **1 อาร์ควินาที** (~30 ม.)". This is almost certainly the origin of the "1 m" claim: **1 arcsecond, not 1 metre.**
  - `analysis/goal7/gaps.json:278` records: "ไม่พบ DEM/LiDAR ความละเอียดสูง … ดึง FABDEM แล้ว … ใช้ตรวจไขว้เท่านั้น ไม่ปิดช่องว่าง".
  - `grep -rn -i "lidar" analysis/ report/ docs/` returns only wish-list entries, never an input.

- **Critique:** This is a provenance claim in reader-facing Thai text that is contradicted by the repo's own manifest and gap ledger. It is precisely the class of statement `docs/LEGAL_REVIEW.md` §1.1 rule 1 exists to prevent ("every factual sentence must be Tier-A sourced"). A DSM (not DTM) inflates the ground surface in exactly the vegetated/built terrain whose elevation sets the storage curve.

- **Proposed Solution:** Replace the caption with the actual provenance. Add a test that extracts data-source nouns from rendered captions and asserts each has a corresponding entry in `catalog.py`/`data/*/manifest.md`.

---

### [F-03] A kinematic-wave celerity is imposed on a reach with Froude number 0.15

- **Location:** `analysis/hydraulic_1d_routing.py:147-150`

  ```python
  # ความเร็วคลื่น c = dQ/dA ≈ (5/3) * v (Manning)
  y_est = max(0.5, ((manning_n * q_ref) / (b_avg * math.sqrt(slope))) ** 0.6)
  v_est = q_ref / (b_avg * y_est)
  c_wave = (5.0 / 3.0) * v_est  # m/s
  ```

- **Empirical evidence** (recomputed from `data/19_rid_cross_sections/derived/Ny.7_profile.csv` and `data/20_multistation_levels/st62.csv`):

  | Stage (m MSL) | Q (m³/s) | A (m²) | B (m) | v (m/s) | **Fr = v/√(gA/B)** | c = 5v/3 (m/s) | kinematic TT over 18.3 km |
  |---:|---:|---:|---:|---:|---:|---:|---:|
  | 6.86 | 486.9 | 432.7 | 97.9 | 1.13 | **0.17** | 1.88 | 2.71 h |
  | 7.64 | 509.6 | 523.6 | 134.3 | 0.97 | **0.16** | 1.62 | 3.14 h |
  | 8.21 | 617.4 | 606.9 | 160.0 | 1.02 | **0.17** | 1.70 | 3.00 h |

  The observed H→H peak lag is **9.00 h** (Ny.1B peak 2026-09-27T01:00 → Ny.7 peak 2026-09-27T10:00), implying a mean celerity of **0.565 m/s**. The model's imposed celerity is **1.62 m/s** — 2.9× too fast. The 3.25 h figure sits squarely on the kinematic value, confirming it is the celerity assumption propagated, not an emergent result.

- **Critique:** The kinematic-wave approximation requires the inertia term to be negligible, i.e. Fr ≳ 1 (Chow: Fr > 2–3 for negligible backwater). At Fr = 0.15 the reach is an order of magnitude outside validity: backwater dominates, and the flood-wave celerity is set by the downstream control, not by 5v/3. The 160 m wide, 607 m² composite section at Ny.7 already contains most of the floodplain storage **inside** the modelled reach — so the project's framing of the 3.25 h vs 9.0 h gap as detention "beyond" the modelled reach is a mis-diagnosis. There is also **no downstream boundary condition at all** for a subcritical reach (`hydraulic_1d_routing_summary.json → model_scope_note` mentions only the absent Kgt.30 condition; Ny.7 itself is treated as a free outfall, which is invalid when Fr < 1).

- **Proposed Solution:** Calibrate the Muskingum storage coefficient K directly against the observed 9.0 h H→H lag rather than deriving it from `5v/3`; or run HEC-RAS in diffusive-wave mode with a Ny.7 rating-curve boundary. Until one of these exists, 3.25 h should not be quoted.

---

### [F-04] The routing is not grid-convergent, and the convergence study hides it

- **Location:** `analysis/hydraulic_1d_routing.py:284-293`

  ```python
  for ns in (6, 12, 24, 48):
      qs = run_muskingum_cunge_reach(q_obs_ny1b, dt_sec, dx_m, slope_reach2, n_channel, b_avg, n_sub=ns)
  ```

  `dt_sec` is fixed at 900 s for every configuration (line 224).

- **Empirical evidence:**

  **Stability (criterion Δt ≤ 2K(1−X), K = Δx_sub/c):**

  | n_sub | Δx_sub (m) | Q (m³/s) | c (m/s) | K (s) | 2K (s) | Δt (s) | X_raw | Stable? |
  |---:|---:|---:|---:|---:|---:|---:|---:|---|
  | 12 | 1525 | 675.3 | 1.87 | 813 | 1627 | 900 | −1.89 | yes (barely) |
  | 24 | 762.5 | 675.3 | 1.87 | 407 | 813 | 900 | −4.29 | **NO** |
  | 48 | 381.2 | 675.3 | 1.87 | 203 | 407 | 900 | −9.08 | **NO** |

  The JSON note at `hydraulic_1d_routing_summary.json:112` interprets the non-improvement of RMSE as "ผลที่ n_sub=12 เป็นค่าที่ 'พอดี' ไม่ใช่ค่าที่ลู่เข้า" (n_sub = 12 is a good fit, not a converged answer). The actual cause is **numerical instability** at n_sub ≥ 24, not a physical plateau. Oscillation confirms it — event-window turning points rise 7 → 7 → 7 → 16 → 26 → 39 for n_sub = 6, 12, 24, 48, 96, 192.

  **Non-convergence at constant Courant number** (recomputed, holding 2K/Δt = 1.81):

  | n_sub | Δt (s) | Model Q→Q lag | Peak Q (m³/s) |
  |---:|---:|---:|---:|
  | 12 | 900 | **3.25 h** | 613.0 |
  | 24 | 450 | **6.25 h** | 589.4 |
  | 48 | 225 | **12.75 h** | 552.1 |
  | 96 | 112 | **41.75 h** | 497.3 |
  | 192 | 56 | **67.25 h** | 487.0 |

  The same dimensionless ratio `2K/Δt` produces answers differing by a factor of 20. A converged scheme cannot do this.

- **Critique:** `X_raw` is negative at every flood discharge (the code's own probe records `x_raw_min = −3.364`, `negative_share = 0.967`), so `x_param` is clamped to 0 by convention (line 154) — the *most diffusive* admissible value — in a reach that is physically *more* diffusive than that. Subdividing the reach makes X_raw monotonically more negative (−1.89 → −75.6 as Δx_sub shrinks), so the clamp artefact strengthens monotonically with refinement. The published `travel_time_hours_sim = 3.25` and `q_peak_sim_cms = 613.0` are therefore properties of the arbitrary (n_sub = 12, Δt = 900 s) pair.

- **Proposed Solution:** Report the stability margin `2K(1−X)/Δt` for every configuration and refuse to publish any configuration with margin < 2. Redo the convergence study at constant Courant number. Do not describe the result as "good fit"; it is an artefact.

---

### [F-05] The boundary condition and the validation target are both internally inconsistent

- **Location:** `data/20_multistation_levels/st61.csv`, `st62.csv`; `analysis/hydraulic_1d_routing_summary.json:51-53`

- **Empirical evidence** (recomputed from the 15-minute records):

  | Quantity | Ny.1B | Ny.7 |
  |---|---|---|
  | `q_cms` peak | 675.3 @ 2026-09-26T18:30 | 648.3 @ 2026-09-27T18:45 |
  | `level_msl_m` peak | 11.00 @ 2026-09-27T01:00 | 7.68 @ 2026-09-27T10:00 |
  | **Q peak − H peak offset** | **+6.50 h** | **−8.75 h** |
  | Observed **Q→Q** lag | colspan | **24.25 h** |
  | Observed **H→H** lag | colspan | **9.00 h** |

  The code drives the routing with `q_obs_ny1b` (line 243) — the series whose peak leads/lags its own stage by 6.5 h — and validates against `q_obs_ny7`, inconsistent by −8.75 h. `Qlag − Hlag = 24.25 − 9.00 = 15.25 h = 6.50 + 8.75` exactly: **the entire 15.25 h discrepancy between the two lag measures is instrument inconsistency, not routing.**

- **Critique:** The report text (`report/build_expert_report.py:368`) correctly states that 3.25 h (Q→Q model) and 9.0 h (H→H observed) "are different hydraulic quantities that cannot be compared directly" — that is good practice and a verified strength. But the consequence is not followed through: the one directly comparable pair, **observed Q→Q 24.25 h vs model Q→Q 3.25 h (ratio 7.46×)**, is never computed or published. A reader is left with "3.25 h" and no indication that the model under-predicts the comparable observed lag by a factor of 7.5.

- **Proposed Solution:** Publish all three lags side by side (Q→Q model, Q→Q observed, H→H observed) with the Q/H offsets, so the reader can see that the model is inconsistent with its own boundary series by more than the effect being studied.

---

### [F-06] The Ny.1B-vs-Ny.7 capacity comparison is a slope artefact; `n` is a one-point fit

- **Location:** `analysis/hydraulic_1d_routing.py:176-191`

  ```python
  slope_reach1 = 0.00065   # ขุนด่านฯ -> Ny.1B
  slope_reach2 = 0.00035   # Ny.1B -> Ny.7
  n_channel = 0.0437
  ...
  q_bank_ny1b = stage_to_discharge(geom_bank_ny1b, n_channel, slope_reach1)
  q_bank_ny7  = stage_to_discharge(geom_bank_ny7,  n_channel, slope_reach2)
  ```

- **Empirical evidence:** Recomputing both stations on a **common** slope:

  | S₀ | Ny.1B @ 10.60 m | Ny.7 @ 8.213 m | ratio |
  |---:|---:|---:|---:|
  | 0.00020 | 369.6 | 466.7 | 0.79 |
  | **0.000321** (`rid_cross_section_hydraulics.py:16`) | 468.2 | 591.3 | **0.79** |
  | 0.00035 | 488.9 | 617.4 | 0.79 |
  | **0.00065** (code's value for Ny.1B) | **666.3** | 841.4 | 0.79 |

  The published "666.3 at Ny.1B vs 617.4 at Ny.7" implies Ny.1B has **8 % more** capacity. On any common slope Ny.1B has **21 % less**. The comparison is entirely a product of assigning a 1.86× larger slope to one station.

  Separately, `n = 0.0437` is fitted at **one point**. `analysis/rid_cross_section_hydraulics.py:97-106` bisects `n` so that Manning reproduces the *project's own* rating curve `Q = 242(h − 4.55)^0.66` at exactly h = 7.64 m. Ratio check across the range: Manning/project = 1.57 (h = 5.0), 1.15 (6.0), 1.16 (6.86), 1.07 (7.64), 1.08 (8.21), 1.15 (9.0). The two curves diverge by up to 57 % at low stage.

- **Critique:** The provenance of the "project rating curve" is a comment: `# อ้างอิงค่าของโปรเจค` (`rid_cross_section_hydraulics.py:5`). The chain is circular — `n` is fitted to reproduce the project rating; the project rating is then used to derive bankfull capacities; those capacities are published as Manning results. And `rid_cross_section_hydraulics.py:108` **explicitly refuses** to fit `n` at Ny.1B ("ข้าม — datum ของสถานียังไม่ยืนยัน รอ FOI สช.9"), noting the Ny.1B datum offset computes to −0.07 m against the +1.59 m convention (GL-08). The routing script nevertheless applies Ny.7's `n` to Ny.1B unconditionally and publishes 666.3. To 0.1 m³/s.

- **Proposed Solution:** Report both stations at a single sourced slope; state that Ny.1B's rating is unverifiable until FOI สช.9 closes; round capacities to the nearest 10 m³/s and attach the slope-induced band.

---

### [F-07] The published "9.0 m³/s overbank discharge" is physically impossible under the model's own rating

- **Location:** `report/build_report_html.py:338`, `report/build_expert_report.py:353`

  Rendered verbatim in both published reports:

  > "…ทำให้น้ำล้นข้ามตลิ่งสูง 0.40 เมตร และมีอัตราน้ำบ่าล้นตลิ่งออกนอกลำน้ำ **9.0 ลบ.ม./วินาที** ไหลบ่าเข้าท่วมพื้นที่ลุ่มต่ำชุมชนบ้านท่าขามและตลาดนครนายกโดยตรง"

  and, in the academic report only:

  > "…ด้วยอัตราส่วนเกิน **9.0 ลบ.ม./วินาที** ซึ่ง**อธิบายสาเหตุ**ที่พื้นที่ริมลำน้ำช่วงต้นน้ำใต้เขื่อนเริ่มถูกน้ำท่วมตั้งแต่ช่วงดึกของคืนวันที่ 26 ก.ย."

- **Empirical evidence:**
  - `canonical_numbers.json → render.ny1b_ov_q = 9.0`, i.e. 675.3 − 666.3, a subtraction of a station-reported discharge against a Manning capacity computed at an assumed slope.
  - The same script's own sensitivity table (`hydraulic_1d_routing_summary.json → rating_sensitivity.ny1b`) gives **q_composite = 578.4 m³/s at stage 11.00 m** — *lower* than the 666.3 m³/s at the 10.60 m crest, because the composite section's hydraulic radius falls as the water rises onto the floodplain.
  - Therefore the observed 675.3 m³/s **cannot pass the surveyed section at 11.00 m at all** under the model's own rating; the implied friction slope would need to be ≥ 3.71e-4 or `n` ≤ 0.0425.

- **Critique:** The academic report attaches a **causal explanation** — that 9.0 m³/s of overbank flow is why the upper riparian area flooded on the night of 26 Sep — to a quantity that is undefined under the analysis's own hydraulics. On a composite section the "overbank discharge" is not `Q_observed − Q_bankfull`; it requires a two-part (channel + floodplain) conveyance split, which the divided method does provide but which is reported only as a sensitivity band (`ny1b.peak_11.00.q_divided_cms = 1009.1`).

- **Proposed Solution:** Delete the 9.0 m³/s figure and the causal sentence. If an overbank-flow statement is needed, use the divided-channel conveyance and state it as a range.

---

### [F-08] The compound-flood model's tidal transfer coefficient is falsified by the repository's own telemetry

- **Location:** `analysis/compound_flood_risk.py:47-49`

  ```python
  head_loss = c1 * ((q_bangsai / 1000.0) ** 1.28)
  stage = tide_msl + wave_setup_m + head_loss
  ```

  with `wave_setup_m = 0.08` fixed and the `limitations` block at lines 132-138 correctly noting `∂H_C12/∂H_tide = 1.0`.

- **Empirical evidence** — regressing the repo's own C.12 on CPY015 (`data/22_goal6_network/raw/l1_bkk_lower/`, 1,931 common hours):

  | Estimator | ∂H_C12/∂H_tide | t-statistic |
  |---|---:|---:|
  | Raw OLS (r = 0.884, R² = 0.781) | **0.827 ± 0.019** | 43.1 vs its own mean; **18.0σ** from 1.000 |
  | Detrended (tidal band only, 49 h high-pass) | **0.666** | — |
  | M2 band amplitude ratio (0.167 m / 0.200 m) | **0.834** | — |
  | K1 band amplitude ratio (0.131 m / 0.184 m) | **0.710** | — |

  The model's assumption of 1.000 over-weights the tide term by **1.42×**.

  Interaction test (avoiding conditioning on the outcome): `C12 ~ 1 + CPY015 + BKK001 + CPY015×BKK001`, n = 1,779 — the interaction coefficient is **−0.0149 ± 0.0264 (t = −0.6)**, i.e. **not significant**. So the missing Q×tide term is *not* the dominant error over the observed range; the **level** of the main effect is.

- **Impact on all four published classifications** (substituting 0.705 for 1.000, holding the river term):

  | Benchmark | Published H | Published level | Empirical-tide H | Empirical level |
  |---|---:|---|---:|---|
  | 2011 mega-flood (Q = 3,750, tide +2.35) | 3.15 m | critical | 2.45 m | **warning** |
  | 2026 late-Sep event (Q = 2,250, tide +1.91) | 2.36 m | watch | 1.80 m | **normal** |
  | 2026 + max tide (Q = 2,250, tide +2.40) | 2.85 m | critical | 2.14 m | **watch** |
  | 2026 + Chao Phraya 2 (−600 m³/s) | 2.73 m | critical | 2.02 m | **watch** |

  **Every published risk level changes.**

- **Critique:** The formulation adds linearly, so at a high river stage the model maximises the tidal contribution — whereas real estuarine attenuation *suppresses* tidal penetration as the river flow rises. Even setting the 1.0 aside, 76–91 % of each reported stage is assumption: tide 74.7–87.9 %, constant wave setup 2.5–3.4 %, and only 9.2–22.8 % from the "computed" two-parameter function.

- **Proposed Solution:** Fit `∂H_C12/∂H_tide` and its stage dependence against the ≥2012 estuary record the repo already holds (`analysis/historical_estuary_summary.json`, 2.5 M rows per HANDOFF:200/225). Until then, publish relative risk (Δstage per ΔQ at fixed tide) rather than absolute risk classes.

---

### [F-09] `c1` and the exponent are perfectly confounded

- **Location:** `analysis/compound_flood_risk.py:46-47`, docstring lines 37-41

- **Empirical evidence:** Refitting `c1` to preserve the single check-point (Q = 2,500, tide +2.00 → +2.51 m) while varying the exponent:

  | exponent | c1 (re-fit) | H(2011) | H(2250, +2.40) |
  |---:|---:|---:|---:|
  | 0.80 | 0.24503 | 3.14 m | 2.95 m |
  | 1.00 | 0.20400 | 3.20 m | 2.94 m |
  | 1.28 (published) | 0.15784 | 3.29 m | 2.93 m |
  | 1.60 | 0.11772 | 3.41 m | 2.91 m |
  | 2.00 | 0.08160 | 3.58 m | 2.89 m |

  The 2011 stage moves by **0.44 m** across a purely cosmetic reparameterisation.

- **Critique:** Only the product `c1 · Q^n` is constrained by the data, so `c1` and `n` are **unidentifiable**. The docstring is commendably honest ("เป็นการตรวจความเป็นไปได้ ไม่ใช่การถดถอยจากอนุกรมเวลา"), but the rendered report (§F-10) drops that honesty entirely. Note also that an exponent **> 1** makes the absolute sensitivity `dH/dQ ∝ Q^0.28` *increase* with discharge — the opposite of real backwater behaviour in a channel that is progressively filling.

- **Proposed Solution:** Fix `n = 1.0`, fit only `c1` against a real time series, and report the residual bias as a function of discharge.

---

### [F-10] The compound model's documented limitations are dropped at the render boundary

- **Location:** `report/goal6_build_report4_draft.py:311-338`

  The builder reads `_cfr["metadata"]` but consumes only `floodwall_crest_msl_m`, the three thresholds, `historical_benchmarks` and the PNG. The four-item `limitations` array (`compound_flood_risk.py:132-138`) is never rendered.

- **Empirical evidence** — the published text in `report/ชุดเทียบมาตรฐาน2554.html` §8 reads:

  > "ในพื้นที่ลุ่มเจ้าพระยาตอนล่าง ความเสี่ยงน้ำท่วมมิได้เกิดจากน้ำเหนือหลากหรือน้ำทะเลหนุนเพียงด้านเดียว แต่เกิดจากปฏิสัมพันธ์ร่วม (Compound Flood Risk) โดยมีคันกั้นน้ำ กทม. สูงเฉลี่ย **2.80** ม.รทก. เป็นแนวป้องกันหลัก และกำหนดเกณฑ์เฝ้าระวังที่ 2.00 ม.รทก., เกณฑ์เตือนภัย 2.40 ม.รทก., และระดับวิกฤตที่ 2.70 ม.รทก."

  No statement that the coefficients are uncalibrated, that `∂H/∂H_tide` is assumed to be 1.0, that wave setup is a fixed constant, or that the 2011 and 2026 discharge inputs have no source in the repository.

- **Additional issue:** the report calls 2.80 m the "**average**" floodwall crest, but `compound_flood_risk.py:73` records the range "สันคันเฉลี่ย 2.80–3.00 ม." — and the critical threshold of 2.70 m sits **below the lowest stated crest**, so the label "วิกฤตล้นคันกั้นน้ำ" (critical / overtopping) is applied 10 cm before any overtopping is possible.

- **Proposed Solution:** Render `metadata.limitations` verbatim. Move the "critical" threshold to the crest value or relabel it "เฝ้าระวังใกล้ชิด". Present the crest as a range.

---

### [F-11] The harmonics findings document asserts skill its own table disproves

- **Location:** `analysis/goal6_l3_coastal_harmonics.py:273-274` → `analysis/goal6/l3_coastal_harmonics_findings.md`

  ```python
  "2. **ทักษะการพยากรณ์โดดเด่นที่ระยะ +12 ชม. และ +24 ชม.**: ... โมเดลให้ค่าความคลาดเคลื่อนต่ำกว่าฐานเทียบเดิมอย่างมีนัยสำคัญ",
  "3. **พร้อมนำไปใช้งานในระบบเฝ้าระวังระดับน้ำ กทม.**: ... 1–2 วันได้อย่างมีเสถียรภาพ"
  ```

- **Empirical evidence** — the same script's own output table:

  | Lead | R² | RMSE model | RMSE persistence | RMSE astro baseline | skill vs persistence | skill vs astro baseline |
  |---|---:|---:|---:|---:|---:|---:|
  | +6 h | **−0.293** | 0.600 | 0.618 | 0.563 | +2.9 % | −6.6 % |
  | +12 h | **−0.285** | 0.595 | 0.577 | 0.536 | **−3.0 %** | −10.9 % |
  | +24 h | +0.826 | 0.218 | 0.212 | **0.205** | **−2.7 %** | −6.3 % |
  | +48 h | +0.375 | 0.392 | 0.376 | 0.361 | −4.2 % | −8.6 % |

  Claim 2 names +12 h and +24 h as the outstanding leads; both are **negative** (the model is worse than persistence). Claim 3 recommends operational deployment for Bangkok warning on a model with **R² = −0.293** at +6 h. "อย่างมีนัยสำคัญ" (significantly) is asserted with no significance test anywhere in the script.

- **Additional finding:** report 4 §7's narrative sentence cherry-picks the single lead with positive R² — "ที่ระยะ +24 ชม. แบบจำลองให้ R² = 0.826 และ RMSE = 0.218 เมตร" — which is the lead where the model is *worst* relative to both baselines (0.218 vs 0.212 persistence and 0.205 astro). The full table including the negatives *is* rendered immediately below, so this is a framing defect rather than a concealment.

- **Proposed Solution:** Generate the findings summary section from the same dict that produces the table. Delete claim 3. Replace "อย่างมีนัยสำคัญ" with the measured skill and its sign.

---

### [F-12] Harmonic phase convention, epoch, and unreported fit quality

- **Location:** `analysis/goal6_l3_coastal_harmonics.py:73-124`

- **Empirical evidence:**
  - **Convention.** Line 101: `phase_rad = math.atan2(-b, a)`. For `A·cos(ωt) + B·sin(ωt) = Amp·cos(ωt − g)`, the standard harmonic argument is `g = atan2(B, A)`. The code therefore reports **360 − g**, verified for all four constituents:

    | Constituent | Reported | Standard g | 360 − g | Match |
    |---|---:|---:|---:|---|
    | M2 | 200.64 | 159.35 | 200.65 | ✔ |
    | S2 | 154.48 | 205.52 | 154.48 | ✔ |
    | K1 | 23.98 | 336.01 | 23.99 | ✔ |
    | O1 | 27.11 | 332.89 | 27.11 | ✔ |

  - **Epoch.** `t0 = times[0]` = 2026-07-01 01:00, the first training timestamp. Phases are epoch-relative and not comparable to published constituent tables.
  - **Missing diagnostics.** No equilibrium argument `g`, no nodal factor, no inference/age, no Doodson numbers. Because of this, **the brief's question "are the amplitudes and phases physically consistent with Gulf of Thailand amphidromic dynamics?" is unanswerable from this output** — the quantities needed to check it do not exist in the file.
  - **Fit quality never reported.** I recomputed it: **R² = 0.8966** on the calibration set (residual RMSE 20.6 cm vs series σ = 64.0 cm). This appears nowhere in the JSON or the MD.
  - **Resolvability — PASSED.** The calibration record is 80.9 days (1,505 h, 2026-07-01 01:00 → 2026-09-19 23:00). Rayleigh requires > 14.8 d to separate M2 from S2 and > 13.7 d for K1 from O1. **RESOLVED** — the constituent set is legitimate.
  - **Form factor** `F = (K1+O1)/(M2+S2) = 1.401` → mixed, diurnal-dominant, consistent with the Gulf of Thailand's known regime. This is a plausible result.

- **Proposed Solution:** Report `g` (not `360 − g`), add the epoch, compute and publish the calibration R² and residual, and add Doodson numbers. Then the amphidromic consistency check becomes possible.

---

### [F-13] The L3 confidence intervals ignore serial correlation

- **Location:** `analysis/goal6_l3_coastal_model.py:82-93`

  ```python
  for b in range(n_boot):
      idx = rng.integers(0, n, n)   # iid resample of hourly residuals
  ```

- **Empirical evidence** (recomputed by replaying the model's own feature construction):

  | Lead | n_test | Residual lag-1 autocorr | lag-6 h autocorr | IAT τ (h) | Improvement | iid bootstrap CI95 | **moving-block bootstrap CI95** |
  |---:|---:|---:|---:|---:|---:|---|---|
  | +6 h | 226 | +0.551 | −0.303 | 1.7 | +39.6 % | (32.4, 46.3) | (30.9, 47.8) |
  | +24 h | 226 | **+0.931** | +0.658 | **14.0** | +5.9 % | (−0.1, 12.3) | **(−3.4, 23.8)** |
  | +48 h | 226 | **+0.940** | +0.660 | **16.1** | +12.3 % | (6.4, 18.6) | (4.2, 26.5) |

- **Critique:** At +24 h the effective sample size is 226/14 ≈ **16**, not 226. The iid bootstrap is anti-conservative by roughly √16 ≈ 4×, and the block bootstrap confirms it: the published interval excludes zero by 0.1 percentage points, the correlation-aware interval comfortably includes it. The repo's `statistical_power_note` correctly warns "ช่วงควรคร่อมศูนย์ = 'ยังสรุปทิศทางไม่ได้'" but then ships an interval that only barely avoids that condition by an artefact of the resampling scheme.

- **Proposed Solution:** Block bootstrap with block length ≥ IAT. Report both intervals. Publish the IAT.

---

### [F-15] Hard-coded dam-storage literals contradict the source data

- **Location:** `report/goal6_build_report3_draft.py:676-677` → published at `report/ระลอกปลายกย2569.html:176`

  ```python
  "<b>ต่ำกว่าระดับกำกับทุกวัน</b> (15 ก.ย. เก็บ 8,004 vs ระดับกำกับ 10,788 ล้าน ลบ.ม. — ต่ำกว่า 2,800) "
  ```

- **Empirical evidence** — `analysis/goal6/dam_history_all.json → dams.ภูมิพล.years[2026].storage_sep_oct`:

  | Date | Storage (MCM) |
  |---|---:|
  | 2026-09-06 | 7,776.10 |
  | **2026-09-15** | **7,986.87** |
  | **2026-09-16** | **8,004.38** |
  | 2026-09-21 | 8,202.13 |

  8,004 is the **16 September** value; 15 September was 7,987. The neighbouring literals (7,293 for Sirikit on 15 Sep; 10,788 URC; 8,182 URC) are all correct — this is an isolated off-by-one date.

  Second literal at `report/ระลอกปลายกย2569.html:169`: "ภูมิพล 7,776 → 8,202 ล้าน ลบ.ม. **ใน 15 วัน**" — but 7,776 is 6 Sep and 8,202 is 21 Sep, a **16-day** window.

- **Critique:** These are hand-typed metrics that bypass canonical rendering, and they contradict the repository's own primary data in a reader-facing document. `tests/test_goal6_consistency.py` cannot catch them: its scanner is an 11-item deny-list (see F-17), and none of `8,004`, `10,788`, `7,293`, `8,182` appears in `analysis/goal6/canonical.json`.

- **Proposed Solution:** Render from `dam_history_all.json`; add a test that recomputes any inline dam-storage literal from source.

---

### [F-16] The Chao Phraya 2 public report contradicts itself and its own canonical table

- **Location:** `report/goal7_build_public.py:362,364`

  ```python
  :362  "พบว่าที่ระดับน้ำ +2.40 ม.รทก. ... น้ำขังค้างในลุ่มต่ำ 81.3 ตร.กม. (ปริมาตร 19.3 ล้าน ลบ.ม.)"
  :364  "ด้วยปริมาตรสะสมสูงถึง <b>126.22 ล้าน ลบ.ม.</b> ครอบคลุมพื้นที่ 257.2 ตร.กม. (ร้อยละ 50.1 ของอำเภอ)"
  ```

- **Empirical evidence:**
  - Canonical table (`ongkharak_2d_depression_summary.json`, stage 2.40 m): **36.84 km² / 19.03 MCM / 50.1 %**. The prose says **81.3 km²** — a **+120.7 %** area error — with the volume (19.3 vs 19.03) silently matching neither.
  - At +3.20 m the canonical table says **257.0 km²**. The prose says **257.2 km²**. I confirmed by grepping the shipped HTML that **both** `257.0` and `257.2` appear in `report/คลองเจ้าพระยา2_ประชาชน.html` — a visible internal contradiction in a published deliverable.
  - A third stale value at `analysis/goal7_ongkharak_2d_depression.py:90`: `observed_oct2026.description` says "ราว 41.5 ตร.กม. … ~17.8 ล้าน ลบ.ม." while the computed fields in the same object read 36.84 / 19.03.
  - `tests/test_goal7_report.py:169-179` already contains `test_builders_have_no_crest_range_literal`, written specifically to eliminate "a range re-typed as a literal in a builder, causing the two versions to diverge" (docstring: *"ต้นเหตุของ '2.5–4.8' ค้าง"*). It is scoped only to `eia_profile.nn_reach` and was not extended.

- **Proposed Solution:** Render all Ongkharak figures from canonical. Extend the existing literal test to the Ongkharak block.

---

### [F-17] The quality gates are deny-lists, not invariants

- **Location:** `tests/test_goal6_consistency.py:111-139`, `tests/test_reports12.py:54-78`, `tests/test_legal_compliance.py:45,120`

- **Empirical evidence:**
  - `test_builder_source_has_no_metric_literals` is a fixed list of 11 exact substrings. The list `banned_literals` declared at `:114-117` is **assigned and never referenced again** — dead code.
  - `tests/test_reports12.py:64-69` covers 5 render keys only.
  - `THAI_CITIZEN_ID` is defined at `tests/test_legal_compliance.py:45` as `(?<![\d])\b[1-8]\d{12}\b(?![\d])` but `grep -n "THAI_CITIZEN_ID" tests/*.py` returns **only the definition line**. The module docstring at `:11` claims the suite "สแกนหาเลขบัตรประชาชน 13 หลัก".
  - `tests/test_legal_compliance.py:120` skips files > 3 MB. Sizes: `report/น้ำท่วมนครนายก2569_ประชาชน.html` = **4,790,483 B** and `report/ระลอกปลายกย2569.html` = **3,869,394 B** — **both skipped** from the land-title / ID scan.
  - `tests/test_privacy.py:14` `PROFILE` regex is Facebook-only; no Instagram / t.me / LINE OA coverage.
  - `docs/LEGAL_REVIEW.md` §1.1 item 4 bans "เขื่อนเสี่ยงแตก" / "คันจะพังทลาย" — no test enforces either.

- **I confirmed the gates do pass**, so these are coverage gaps rather than active failures: `test_legal_compliance.py` + `test_privacy.py` = **7 passed**; `test_thai_language_lint.py` = **11 passed**.

- **Proposed Solution:** Replace the deny-list with a numeric-plus-Thai-unit regex over reader text (the linter already has a `_reader_text` helper). Wire up `THAI_CITIZEN_ID`. Replace the size gate with a streaming scan.

---

### [F-18] WCAG AA failures in the Chao Phraya 2 output, with zero test coverage

- **Empirical evidence** — I computed WCAG 2.x contrast ratios directly.

  **Text below 4.5:1:**

  | Foreground | Background | Ratio | Location |
  |---|---|---:|---|
  | `#d97706` | `#ffffff` | **3.19:1** | `report/สมุดปกขาว_เจ้าพระยา2.html:102` (`<span id="val_delay">`), source `goal7_build_policy_brief.py:45` |
  | `#0284c7` | `#ffffff` | **4.10:1** | `report/สมุดปกขาว_เจ้าพระยา2.html:90`, source `goal7_build_policy_brief.py:33` |
  | `#0284c7` | `#f6f9fb` | **3.87:1** | `<summary>` in even table rows, `goal7_blocks.py:458` |

  **Graphical marks below 3.0:1 on white (Goal 7 maps):**

  | Colour | Ratio | Role | Source |
  |---|---:|---|---|
  | `#9ccfe0` | **1.69:1** | reservoir/water fill | `goal7_common.py:97` |
  | `#d9bf86` | **1.79:1** | elevation band 10–20 m | `goal7_common.py:54` |
  | `#c1b6ac` | **1.99:1** | road line, secondary | `report_assets.py:227` |
  | `#c2a06a` | **2.46:1** | elevation band 20–50 m | `goal7_common.py:54` |
  | `#5fb3aa` | **2.47:1** | canal line | `report_assets.py:253` |
  | `#a89e94` | **2.63:1** | road line, tertiary **and the fallback for every unmapped class** | `goal7_common.py:107,109` |

  `tests/test_contrast.py:68-70` parses colour pairs only from `report/build_report_html.py`, `report/build_expert_report.py` and `report/goal6_reportlib.py`. **Every Goal 7 builder has zero coverage.** The test does compute real luminance ratios (it does not cheat with a token table) but performs no DOM/cascade resolution — it never reads the shipped HTML or walks ancestors for a background.

  **Verified passing** (for balance): the Goal 7 theme tokens all clear their floors — `--c-chart-bar #ffffff/#4d94c9` = 3.28, `--c-chart-accent #ffffff/#e74c3c` = 3.82, `--c-muted #5a6b7b/#ffffff` = 5.49, `--c-accent #ffffff/#1e6fb8` = 5.22.

- **Proposed Solution:** Extend `test_contrast.py`'s source list to the six Goal 7 builders; add a pass that resolves `background` through the ancestor chain in the rendered HTML.

---

### [F-22] Chao Phraya 2 storage figures are literals, and the dead storage contradicts the canal's own section

- **Location:** `analysis/goal7_operational_economics.py:344-358`

  ```python
  "canal_length_km": 135.9,
  "design_depth_m": 7.0,
  "bed_width_m": 48.0,
  "total_storage_mcm": 55.4,
  "dead_storage_depth_m": 2.0,
  "dead_storage_mcm": 21.0,
  "active_storage_mcm": 34.4,
  "buffer_duration_hours": 15.9,
  ```

- **Empirical evidence:**
  - Arithmetic is internally consistent: 55.4 − 21.0 = 34.4; 34.4e6 / 600 / 3600 = 15.93 h ✓.
  - `total_storage_mcm = 55.4` **is** geometrically coherent with the stated section: 55.4e6 / 135,900 m = 407.7 m², implying 48·7 + 49z = 407.7 → z ≈ 1.46 (1 V : 1.46 H). Plausible, though the side slope is stated nowhere.
  - **`dead_storage_mcm = 21.0` is inconsistent with that same section.** For a prismatic canal the water volume between bed and stage h is **A(h) × L** (the wetted area already contains the depth). Taking A(7.0) from the 55.4 MCM figure gives 407.5 m², so the trapezoid has mean width A/h = 48 + 1.46h, i.e. **50.9 m at h = 2.0 m**. The stated 21.0 MCM instead requires A(2.0) = 154.5 m², a mean width of **77.3 m** — larger than the 58.2 m implied at full depth. Since A(h)/h = b + zh *increases* with h for any trapezoid, a 2 m section wider than the full-depth section is impossible. The correct value is **A(2.0) × L = 101.84 × 135,900 = 13.84 MCM**, so 21.0 was **+52 % too high**.
    | Active slice, 5.0 m | 34.4 | 253.13 m² | 50.6 m |

    **The 2.0 m dead-storage slice requires a *wider* section (77.3 m) than the entire 7.0 m canal (58.2 m).** For any trapezoid the sub-depth area must be a strict subset of the full section. So 21.0 MCM cannot be a constant-area × depth deduction from the same geometry as 55.4 MCM. The two figures come from different, unreconciled sources.
  - Worse, `bed_width_m = 48.0` (line 347) is uncited and **contradicts the only sourced cross-section in the repo**. `analysis/goal7_analysis.py:307` records `EIA_SECTION = {"D_m": 7.0, "A_m2": 504.0, "z1": 3.0, "z2": 2.0, …}` sourced to *"รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-39 (รูปที่ 2.3.2-11 ตาราง กม.23-134)"*. That implies a **bed width of 54.5 m**, and 504 m² × 135.9 km = **68.5 MCM — not 55.4 MCM**. `goal7_analysis.py:510` records `"bed_m": None`, i.e. the main EIA module does not have a bed width at all.
  - None of the five values is computed from the section three lines above; all are bare literals. No source is cited for the 2.0 m.
  - **And the published text claims a computation that does not exist.** `report/goal7_blocks.py:540` reads *"**จากการคำนวณ**มิติคลองรูปตัดสี่เหลี่ยมคางหมูตลอดความยาว 135.9 กม. ความลึกน้ำออกแบบ 7.0 ม. ท้องคลองกว้าง 48.0 ม."* ("**computed from** the trapezoidal cross-section…"). No such computation exists in any code path — the builder only formats values read from JSON.

- **Resolution (added 18 ต.ค. 69, after the round-5 remediation):** triage item 4 replaced `21.0 / 34.4 / 15.9` with `dead_storage = 13.9`, `active_storage = 41.5`, `buffer_hours = 19.2`. **I verified this correction is numerically right** — A(2.0) × L = 101.84 × 135,900 = 13.84 MCM — and my original "implied mean width" arithmetic above was the sloppier statement of the same error. What survives from this finding is: the values are still literals rather than computed (derivation lives only in a comment), and `bed_width_m = 48.0` is still uncited and still contradicts the only sourced section (see F-33).

- **Critique:** The `assessment` string asserts the 2.0 m exists "เพื่อรักษาเสถียรภาพลาดตลิ่งดินเหนียวอ่อน" (to maintain slope stability in soft clay) as an established fact, and `report/goal7_blocks.py:543` publishes it as *"จำเป็นต้องคงไว้เพื่อสร้างแรงดันต้านทานการพังทลายของลาดตลิ่งดินเหนียวอ่อนกรุงเทพฯ และหลีกเลี่ยงการทรุดตัว"*. **I could not locate any slope-stability calculation, factor of safety, shear-strength parameter, borehole log, or page reference for this anywhere in the repository**, and it is not registered in `analysis/goal7/gaps.json`. **UNVERIFIED — I am not asserting it is wrong, only that the repo does not evidence it** — yet it drives the entire "34.4 MCM / 15.9 hours" headline, which is the policy brief's central "reality check" argument.

- **Proposed Solution:** Compute both volumes from a sourced trapezoidal section (bed width, side slope, invert profile). Cite the geotechnical basis for the 2.0 m, or reframe it as a scenario parameter with a sensitivity band — the buffer duration is directly proportional to it (1.0 m → 7.9 h; 3.0 m → 23.9 h).

---

### [F-26] The counterfactual simulation cannot represent the bottleneck it is asked to represent

- **Location:** `analysis/goal7_counterfactual_simulation.py:120-123`, `161-162`

  ```python
  tide_eff_54 = 0.92 + 0.08 * np.cos(np.linspace(0, 8 * math.pi, n_days_54))   # -> [0.84, 1.00]
  tide_eff_69 = 0.90 + 0.10 * np.cos(np.linspace(0, 2 * math.pi, n_days_69))   # -> [0.80, 1.00]
  ```

  ```python
  actual_canal_cap = canal_capacity_cms * eff
  ```

- **Empirical evidence:** The script's own `limitations[0]` states it verbatim:

  > "ไม่มีช่วงที่ประตูปลายคลองปิดเพราะน้ำทะเลสูงกว่าผิวน้ำในคลอง (tidal lockout) — **ประสิทธิภาพถูกจำกัดต่ำสุดที่ 0.80–0.84 ไม่เคยเป็น 0** ทั้งที่รายงานระบุว่าผิวน้ำในคลองจะนิ่งตอนน้ำขึ้นสูงสุด"

  ("There is no period in which the outlet gates close because sea level exceeds the canal water surface (tidal lockout) — efficiency is floored at 0.80–0.84 and never reaches 0, even though the report states the canal surface will stagnate at peak high water.")

  I confirmed both floors numerically: `0.92 − 0.08 = 0.84`, `0.90 − 0.10 = 0.80`. So the minimum outlet discharge the model will ever accept is **600 x 0.84 = 504 m³/s**.

  **The EIA contradicts that floor in the repo's own excerpt file.** `analysis/goal7/eia_excerpts.json:102` (PDF p.184, printed 2-79, verbatim):

  > "แบบจำลอง MIKE-11 · ทะเลสูงสุด +2.49 / ต่ำสุด -1.49 ม.รทก. (ปี 2554) · อัตราระบายเฉลี่ย ~597 ลบ.ม./วินาที · **ต่ำสุด ~107 เมื่อน้ำทะเลขึ้นสูงสุด** · สูงสุด ~891"

  The project EIA states the outlet falls to **~107 m³/s at high tide**. The model's floor of 504 m³/s is a **4.7x overstatement of the guaranteed minimum**. (`eia_excerpts.json:114` gives the p.185 range 121.27–853.05 m³/s, mean 591.90 — yet the 1,000 m³/s "expansion" case is still modelled at full availability.)

- **Critique:** This is the most consequential self-contradiction in the Goal 7 modelling, and it is *stated rather than concealed* — which deserves credit — but the consequence is not carried through. The headline 2026 result `days_over_safe_with_canal: 0` / `prevented_overbank_entirely: true` is "100 % prevention of overbank flow," which is **only** true because the model guarantees the canal can always discharge at >= 80 % of 600 m³/s. If the EIA is right that the outlet falls to ~107 m³/s — i.e. **82 % below** the model's assumed floor, at exactly the moment of peak high water — then the correct answer is the opposite of "100 % prevention". The two sources cannot both hold, and the resolution depends on the outlet gate/pump specification, which the repo has already requested as FOI (HANDOFF:279, still open: "เกณฑ์ตัวเลขรายประตูของป่าสัก–อ่าวไทย").

  With the EIA's own figure, one spring-neap cycle at low outlet capacity would cut the 2011 diversion by ~80 % (4,394.5 → ~880 MCM) and the absorption share from 38.8 % to ~8 %.

- **A second, independent self-contradiction: `dQ/dh = 1,100` is contradicted by the repo's own dedicated rating study.** `analysis/goal7_ayutthaya_dqdh_rating.py` / `ayutthaya_dqdh_rating_summary.json` computes dQ/dh for exactly this reach and event:

  | Regime (per that study) | dQ/dh | Stage reduction for 600 m³/s |
  |---|---:|---:|
  | 2011 critical, Q = 4,000 | 1,304.7 | 0.460 m |
  | 2011 peak, Q = 4,686 | **1,529.9** | **0.392 m** |

  Using the repo's own rating, 0.53 m should be **0.39–0.46 m (−16 % to −26 %)**. The counterfactual script's comment at line 87 already concedes the point — *"dh ต่อ dQ = (5/3)·v·B ≈ 1,825 ให้ ~0.33 ม. — ผล 0.53 ม. ที่รายงานคือปลายบนของช่วง ไม่ใช่ค่าฟันธง"* ("0.53 m is the **top of the range, not the anchor**") — yet 0.53 m is emitted as a single rounded figure. (`ayutthaya_dqdh_rating_summary.json` is itself inconsistent: its `conclusions.key_insight` claims dQ/dh = "1,750–2,100" and "30–35 ซม." while its own table maxes at 1,529.9 → 0.392 m.)

- **Proposed Solution:** Make the outlet boundary condition real — compare instantaneous downstream sea level to the canal invert at the outlet structure and set efficiency accordingly (0 below the invert, rising with head). Until the gate criteria are obtained, publish the counterfactual as an **upper bound** and state the floor explicitly next to every result.

---

### [F-27] The 2011 counterfactual rests on an unsourced safe capacity and a 4–6× over-broad synthetic flood

- **Location:** `analysis/goal7_counterfactual_simulation.py:113-118, 128`

  ```python
  t_54 = np.linspace(0, math.pi, n_days_54)
  inflow_2554 = 2200.0 + 2486.0 * (np.sin(t_54) ** 1.3)
  inflow_2554 += np.random.normal(0, 45.0, n_days_54)
  safe_cap_ayutthaya = 2600.0  # ค่า 2,600 ไม่มีเอกสารอ้างอิงใน repo (SB F-07)
  ```

- **Empirical evidence — I reproduced the run exactly:**

  | Quantity | Recomputed | Published |
  |---|---:|---:|
  | Peak inflow | 4,727 m³/s | (implicit 4,686 + noise) |
  | Mean inflow | 3,638 m³/s | — |
  | Days above 2,600 m³/s | **102 of 122** | `days_over_safe_no_canal: 102` ✔ |
  | Excess volume at 2,600 | **11,325.1 MCM** | `excess_mcm: 11325.1` ✔ |
  | 4,394.5 / 11,325.1 | **38.8 %** | `share_of_excess_flood_pct: 38.8` ✔ |
  | Peak Q reduction → stage (582.9 / 1,100) | 0.530 m | `peak_stage_reduction_m: 0.53` ✔ |

  **The arithmetic is fully reproducible.** The problem is the inputs:
  - The hydrograph is a half-sine raised to 1.3 over 122 days: **61-day rise, 61-day fall**, with essentially flat top. The real October 2011 event at Ayutthaya rose over roughly 10–15 days and receded over ~30 days, peaking near 6,200 m³/s. The synthetic under-peaks by ~24 % and over-dwells by roughly 3×.
  - `safe_cap_ayutthaya = 2,600` is annotated **"ไม่มีเอกสารอ้างอิงใน repo"** — no supporting document in the repository. Because the excess volume is `∫ max(Q − 2600, 0) dt`, this constant *is* the denominator of the headline absorption fraction:

  | safe cap (m³/s) | Excess (MCM) | 4,394.5 MCM as % of excess |
  |---:|---:|---:|
  | **2,600 (published)** | **11,325.1** | **38.8 %** |
  | 3,000 | 8,068.0 | 54.5 % |
  | 2,200 | 15,165.4 | 29.0 % |
  | 2,000 | 17,270.0 | 25.4 % |

  A ±400 m³/s change in an admittedly unsourced constant moves the headline by **±6 to +16 percentage points**.

  - The stage reduction uses `dh = dQ/1,100 m²/m`, and the code annotates it *"สมมติฐานที่เขียนไว้ ยังไม่สอบเทียบกับภาคตัดขวางที่อยุธยา"* (an assumption written down, not yet validated against the Ayutthaya cross-section). HANDOFF:39 records the plausible-value band 0.12–0.97 m and that the correct kinematic form (5/3·v·B ≈ 1,825) gives ~0.33 m — i.e. the published 0.53 m sits above the kinematic estimate. This is honestly disclosed.

- **Proposed Solution:** Obtain the Ayutthaya safe-capacity threshold (it is a rating-curve question, answerable from the repo's own C-series data) and drive the simulation from a published 2011 hydrograph. The `dQ/dh` band should be printed next to every stage-reduction figure.

---

### [F-28] The unit cost and the utilisation statistic are the same assumption twice

- **Location:** `analysis/goal7_operational_economics.py:61`

- **Empirical evidence:**

  | Quantity | Value |
  |---|---:|
  | `annual_diverted_mcm` | 1,970 MCM |
  | 1,970 MCM ÷ (600 m³/s × 86,400 s) | **38.0 days at full design capacity** |
  | Reported `days_average_year` | **38.3 days** |
  | 38.3 days × 600 m³/s | 1,985.5 MCM |

  The levelised unit cost denominator and the "10.5 % annual utilisation" headline are the same quantity. Presenting them as two independent lines of evidence in the policy brief overstates the support for the conclusion.

- **Also verified as sound:** `capex_mb = 160046.0` is annotated as the EIA 2569 financial envelope (Clarification Report 2nd edition) — a Tier-A citation, correctly applied. **However** the LUC is reported to two decimals while the alternatives are reported as *ranges* ("0.50–1.20", "1.10–1.80", "1.50–2.50 บาท/ลบ.ม."), while the project's own uncertainty from the discount rate alone is 6.81–10.35 THB/m³ (a 52 % band). Comparing a point estimate against a range of alternatives is not like-for-like.

- **Proposed Solution:** State the denominator assumption once, propagate the band, and compare ranges to ranges. Include land acquisition / compensation explicitly, even as a separately-flagged line, since it is the largest escalation risk for a 135.9 km alignment across four provinces (registered as the open gap `expropriation_commercial_use`, HANDOFF:278).

---

## 4. Verified Invariants (Passed Spot-Checks)

Every item below was independently recomputed from primary data or directly executed.

| # | Invariant | Verification method | Result |
|---|---|---|---|
| V-01 | Full verification suite passes | `python tools/verify_all.py` | **4/4 steps ✅** (catalog check, SHA-256 integrity, lint, pytest) |
| V-02 | Catalogue integrity | `python catalog.py check` / `audit` | **105/105** entries exist; **33/33** root+docs documents registered ✅ |
| V-03 | Full test suite (clean tree, before this file was written) | `python -m pytest tests/ -q` | **140 passed in 21.20 s** ✅ — *note: after writing this review, see §7.1 / F-36* |
| V-04 | Data integrity | via `verify_all` step 2 | **MISMATCH 0** ✅ |
| V-05 | Legal + PDPA gates | `pytest tests/test_legal_compliance.py tests/test_privacy.py -v` | **7 passed** ✅ |
| V-06 | Thai language lint | `pytest tests/test_thai_language_lint.py -v` | **11 passed** ✅ |
| V-07 | Observed H→H peak lag is 9.00 h | Read `data/20_multistation_levels/st61.csv`, `st62.csv`; Ny.1B peak 2026-09-27T01:00 → Ny.7 peak 2026-09-27T10:00 | **9.00 h exactly** ✅ |
| V-08 | Bankfull capacity arithmetic (composite Manning) | Recomputed from `Ny.1B_profile.csv`, `Ny.7_profile.csv` with n = 0.0437 | 666.3 / 617.4 / 486.9 m³/s reproduce the JSON exactly ✅ |
| V-09 | Composite Manning geometry | Recomputed A, P, R | Ny.1B@10.60: A = 471.8, P = 125.3, R = 3.77; Ny.7@8.213: A = 606.9, P = 165.7, R = 3.66 — matches JSON ✅ |
| V-10 | Stage inversion produces the reported RMSE decomposition | Recomputed h_sim from the running-max envelope | h_sim peak 8.17, bias **−80.1 cm**, RMSE **106.0 cm**, residual **69.4 cm** — all match `hydraulic_1d_routing_summary.json` ✅ |
| V-11 | Harmonic constituent periods are astronomically correct | `goal6_l3_coastal_harmonics.py:31-34` | M2 12.4206012 h, S2 12.0, K1 23.9344721, O1 25.8193417 — all correct ✅ |
| V-12 | M2/S2 and K1/O1 are Rayleigh-resolvable on the calibration record | Δf = 0.0677 / 0.0732 cpd → need > 14.8 / 13.7 d; record is **80.9 d** | **RESOLVED** ✅ |
| V-13 | Harmonic form factor is physically plausible | F = (K1+O1)/(M2+S2) = 1.401 | mixed, diurnal-dominant — consistent with the Gulf of Thailand ✅ |
| V-14 | Compound-flood benchmark arithmetic is self-consistent | Recomputed `calculate_c12_stage` for all 4 benchmarks | 3.15 / 2.36 / 2.85 / 2.73 m — match the JSON and the published table exactly ✅ |
| V-15 | Active-storage arithmetic | 55.4 − 21.0 = 34.4; 34.4e6/600/3600 = 15.93 h | Matches the literals ✅ (but see F-22 on their provenance) |
| V-16 | **Capital Recovery Factor is textbook-correct at all three discount rates** | Recomputed `CRF = r(1+r)ⁿ/((1+r)ⁿ−1)` with n = 30: r=7 % → **0.080586**; r=9 % → **0.097336**; r=12 % → **0.124144**. Annualised capital 12,897.5 / 15,578.3 / 19,868.7 MB; total 13,416.5 / 16,097.3 / 20,387.7 MB; LUC **6.81 / 8.17 / 10.35** THB/m³ | All reproduce `operational_economics_summary.json` to 6 decimal places ✅ |
| V-17 | Counterfactual internal arithmetic is fully reproducible | Re-ran the synthetic 2011 inflow with seed 42: peak 4,727; days > 2,600 = **102/122**; excess = **11,325.1 MCM**; 4,394.5/11,325.1 = **38.8 %**; 582.9/1,100 = **0.53 m** | All match the published summary exactly ✅ (inputs are the problem — see F-26/F-27) |
| V-18 | `capex_mb` is Tier-A sourced | `goal7_operational_economics.py:57` annotates 160,046 MB as the EIA 2569 financial envelope, Clarification Report 2nd edition | Correctly cited ✅ |
| V-19 | ONEP/คชก. round-1 rejection: the **primary letter exists in the repo and its number is confirmed verbatim** | `data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/EIA/1. แจ้งมติไม่เห็นชอบ EIA ทางระบายน้ำหลาก.pdf`, 350,650 B, SHA-256 `4d680b7990f147e08211581e77fb3d6f4e2480528cf41948d3c8aa5223fc3216`, registered at `data/manual/manifest.md:250`. Page 1 header reads **"ที่ ทส ๑๐๑๐.๖/๒๒๓๓"** = `ทส 1010.6/2233` ✔. Body confirms the committee resolution date **1 ก.พ. 2562**. | Letter number and resolution date verified against the primary scan ✅ (but see F-31 on the *letter* date, and F-30/F-32 on the objection record) |
| V-20 | Pasak "years exceeding" ambiguity is closed | `analysis/goal6/canonical.json → pasak_year_counts` + `definitions` | Four definitions separated across two year sets: 20/22, 16/22, 17/24, 8/24 ✅ |
| V-21 | Report 4 renders the correct Pasak count | `goal6_build_report4_draft.py:82` recomputes from JSON; comment records the old `17/22` hardcode bug | Now reads **20 of 22** ✅ |
| V-22 | Ongkharak JSON faithfully reflects its generating code | I recomputed all 36 hypsometric rows from `dem_30m.npy` | **0/36 mismatches**; 513.1296 km², median 3.1986 m, 126.22 MCM @ 3.20 m, 257.00 km², 50.1 % ✅ |
| V-23 | Model v1 event RMSE matches canonical | `analysis/goal4_model_v1_results.json` vs `START_HERE.md:169` | linear 30.03/117.56/163.70; persistence 30.65/101.77/170.37; GBDT 127.69/159.79/140.55 — all consistent ✅ |
| V-24 | No personally identifiable information in published reports | Manual grep for 13-digit `[1-8]\d{12}`, `0[689]\d[- ]?\d{3}[- ]?\d{4}`, and Thai personal names across `report/*.html` + `report/*.py` | **0 hits.** "เขานางบวช" is the Ny.1B gauging station; "รังสิตประยูรศักดิ์" is a canal name ✅ |
| V-25 | No individual-culpability language in published reports | Manual grep for `ละเลย`, `ประมาท`, `ขาดความรับผิดชอบ`, `โกง`, `ทุจริต` across all reports | **0 hits.** Criticism targets mechanisms (URC design, gate operation, project assumptions) and each is balanced with an explicit positive finding ✅ |
| V-26 | Working tree unmodified by this audit | `git status --short` at session start and end | **Clean** (only this review file added) ✅ |

---

## 5. Information Gaps & Required Field Data

Items that **cannot be audited** from this repository because the primary data is not released. Listed with the specific artefact each would unlock.

| # | Missing data | Blocks | Register entry |
|---|---|---|---|
| G-01 | **Route 305 / ถนนรังสิต–นครนายก road-crown elevation profile.** No measured value exists anywhere in the repo (exhaustive grep; the only geotagged point at km 41+800 records water *depth*, not crown level). | The entire +3.20 m tipping-point claim (F-01). | **ABSENT from `analysis/goal7/gaps.json`** — must be added; `docs/GOAL7_FOI_REQUESTS.md` holds the 11 live requests. |
| G-02 | **High-resolution DTM / Thai LiDAR (ONEMap ONWR).** Only 30 m Copernicus GLO-30 **DSM** is present, with an official vertical accuracy of ±2–4 m — larger than the entire 0.85 m interval between the 2.50 m bankfull threshold and the 3.20 m tipping point. | Any hypsometric conclusion finer than ±2 m of vertical bias. A ±0.50 m bias swings the headline area by −62 %/+47 %. | `gaps.json → ground_level_table` (adjacent, dam–canal profile); `docs/DATA_SOURCES.md:78` records onemap.go.th as unreachable. |
| G-03 | **Geoid / vertical-datum metadata for `dem_30m.npy`.** The label "ม.รทก./MSL" is author-assigned. `data/08_dem_topography/fabdem/manifest.md:7` records an unresolved ~1.2 m offset against the official hand-read profile ("ฐานอ้างอิงความสูงอาจต่างกัน — ยังไม่ได้ตรวจ"), and `fabdem_compare.json → summary_nn_reach.fabdem_minus_hand_m` has median **1.22 m**. | Whether any stated stage is MSL at all. | Not registered. |
| G-04 | **Hourly gate open/close logs for ปตร.ท่าช้าง and all regulators.** | Testing the gate-control hypothesis (F-21) rather than asserting it. | `docs/OFFLINE_DATA_BACKLOG.md` FOI item 1 (2,315 stations). |
| G-05 | **Confirmed vertical datum for Ny.1B.** `rid_cross_section_hydraulics.py:95-96`: 11.07 m MSL vs 11.0 m gauge = −0.07 m offset, contradicting the +1.59 m convention. The script explicitly refuses to fit `n` here. | Any Ny.1B rating or capacity figure, including the published 666.3 m³/s (F-06). | GL-08; FOI สช.9. |
| G-06 | **Longer C.12 / CPY015 / BKK001 record covering multiple events.** The L3 model trains on 2026-07-01…09-19 and tests on 20 Sep…02 Oct (47.1 % usable coverage, ending because BKK001 stops at 2026-10-02 15:00). | Any statement about generalisation. The repo's own `train_scope_note` and `statistical_power_note` say as much. | GLM F-08, SB F-16, SB F-17/F-18. |
| G-07 | **Multi-year Bang Sai (Chao Phraya–Pasak confluence) discharge to calibrate `c1` and the exponent.** The 2011 input (Q = 3,750 m³/s) and 2026 input (Q = 2,250 m³/s) are both recorded as estimates with no source in the repo. | Any absolute stage from the compound-flood model (F-08, F-09). | `compound_flood_risk.py:136-137`, `limitations[2-3]`. |
| G-08 | **Calibrated `dQ/dh` at Ayutthaya.** The 2011 counterfactual's 0.53 m stage reduction rests on `dQ/dh = 1,100 m²/m`, which HANDOFF:39 records as "ยังไม่สอบทดสอบเทียบ" with a plausible-value band of 0.12–0.97 m. | The headline counterfactual stage benefit. | `docs/GOAL7_FOI_REQUESTS.md`. |
| G-09 | **Geotechnical basis for the 2.0 m canal dead storage in soft Bangkok clay.** Not cited anywhere I could locate. | The 34.4 MCM active storage and the 15.9 h buffer (F-22). | Not registered. |
| G-10 | **Bridge-scour / bathymetry cross-sections below the water surface** for Nakhon Nayok, and the Dan S-non plan longitudinal profiles. | Replacing the 1D kinematic routing with a calibrated dynamic model (F-03). | `docs/OFFLINE_DATA_BACKLOG.md` (กช. / กรมเจ้าท่า). |
| G-11 | **Measured rating curves at C.2 / C.12 / Kgt.30 / NY stations** with a stated datum. | Separating gate/river/tide influences (F-05) and validating the compound model (F-08). | `docs/OFFLINE_DATA_BACKLOG.md`. |

---

## 6. Auditor's Note on the Commissioning Brief

Several figures in the commissioning brief do **not** match the repository's current canonical ledgers. This is recorded as F-24 so that external citations can be re-baselined before the next review round:

| Brief states | Canonical value | Source |
|---|---|---|
| "+6h linear RMSE falls 73.6 → 35.9 cm (51.2 %)" | **79.6 → 37.4 cm (53.0 %)** | `analysis/goal6/l3_coastal_summary.json` |
| "usable test coverage is 57.1 %" | **47.1 %** (cap if BKK001 complete: 63.3 %) | same |
| "Model v1: +6h RMSE 0.17 m" | **0.30 m** (30.03 cm); beats persistence by only **2.0 %** (30.65 cm) | `analysis/goal4_model_v1_results.json` |
| "Pasak exceeded URC in 17 of 22 years, median 107 %" | **20 of 22** (URC, full-year) or **16 of 22** (Aug–Sep); **17 of 24** is a *different metric on a different year set*; the **median is 110.93 %** (mean 107.86 %), and no median field exists in canonical at all | `analysis/goal6/canonical.json → pasak_year_counts`, `pasak_24y_baseline` |
| "ONEP EIA Rejection Order (Letter ทส 1010.6/2233, **18 Feb 2562**)" | Letter number **confirmed verbatim** (Thai numerals ๑๐๑๐.๖/๒๒๓๓) in the scan at `data/manual/…/EIA/1. แจ้งมติไม่เห็นชอบ….pdf`, SHA-256 `4d680b79…`. But the header reads **๑๔ กุมภาพันธ์ ๒๕๖๒ = 14 Feb**, matching four internal modules — while the **18 Feb** value is what reaches every published report (F-31). Also issued by **สผ.** (ONWR), not ONEP. | `data/manual/manifest.md:250`; `goal7_analysis.py:287` vs `goal7_operational_economics.py:146` |
| "EIRR 14.52 %" as a คชก. objection | 14.52 % is the **EIA report's own executive summary** figure (บทที่ 8 หน้า 784 / สรุปผู้บริหาร), not the committee's (F-32) | `analysis/goal7/canonical.json:1441` |
| "257.2 km²" | **257.0 km²** | `analysis/goal7/ongkharak_2d_depression_summary.json` |
| "median +3.19 m MSL" | **+3.1986 m → renders 3.20** | same; `3.19` exists only as an unused fallback at `report/goal7_blocks.py:525` |
| "harmonics across C.29, BKK001, GLF002, GLF003" | Harmonics are fitted to **CPY015 only** (Bangkok Bridge); C.29 / GLF002 / GLF003 appear in `estuary_tide`, not in the harmonic decomposition | `analysis/goal6_l3_coastal_harmonics.py:129-131` |
| "5 historical benchmark events (2011, 2021, 2022, 2024, 2026)" | **4** entries, of which **2 are explicitly labelled `กรณีสมมติ`** (hypothetical) | `analysis/compound_flood_risk.py:92-121` (F-23) |

---

## 7. Closing Assessment

### 7.1 An action item that needs your decision — I have broken one of your gates

Writing this review to the repo root, exactly as `HANDOFF.md:18` instructs (*"บันทึกผลลง root เป็น `REVIEW.<model_name>.md`"*), **necessarily fails one of your tests**:

```
$ python -m pytest tests/ -q
1 failed, 139 passed in 21.60s

FAILED tests/test_standards_integrity.py::test_all_top_level_docs_are_registered
AssertionError: พบเอกสารที่ยังไม่ลงทะเบียนใน catalog.py ...:
  REVIEW.Claude-Sonnet-5.5.md
  REVIEW.deepseek-v4.1-flash-free.md
  REVIEW.space-bunny-free.md
```

The test's own docstring says *"กฎนี้ไม่มี allowlist: ไฟล์ใหม่ต้องลงทะเบียนหรือย้ายออกจากพื้นที่"* ("this rule has no allowlist: new files must be registered or moved out of the area"). So the prescribed deliverable location and the prescribed quality gate are mutually exclusive. I note the two other `REVIEW.*.md` files were already present when I re-ran the suite — they came from other concurrent review sessions, not from me.

**I did not fix this**, because it requires either an edit to `catalog.py` / the test (outside my read-only mandate) or a policy decision that is yours:

- **Option A** — add an explicit allowlist to `test_all_top_level_docs_are_registered` for `REVIEW.*.md` and `TRIAGE.*.md` (matches what round 4 effectively did by archiving them to `archive/reviews/round4_2026-10-17/`).
- **Option B** — change `HANDOFF.md:18` to direct review deliverables into `docs/reviews/`, which is already a registered directory.

Until one of these is done, **any** external model review saved per the current instructions will leave `pytest` red. That is a process defect worth closing before the next round, not a one-off.

---

The repository passes every gate it has built for itself, and I verified those gates independently. That is a real and uncommon achievement, and the negative results in `analysis/thachang_leadtime.md` and the retired-value ledger demonstrate a team that deletes its own headline numbers when the evidence moves.

The problem is structural rather than cultural: **the gates test consistency, not identification.** The canonical-ledger machinery guarantees that a number appears identically in the JSON, the builder and the HTML — it cannot guarantee that the number was *derived* rather than typed. Consequently the most policy-consequential claims in the Chao Phraya 2 and compound-flood workstreams are the ones that escape verification: a hard-coded `3.20`, a subtraction of two inconsistent discharges, a coefficient set to `1.0` that the project's own telemetry rejects at 18σ, and a bootstrap that assumes independent hourly residuals where the autocorrelation is 0.94.

None of these findings requires new data to fix. Six of the highest-severity items (F-02, F-04, F-07, F-10, F-15, F-16) are pure accuracy defects with no modelling content and can be closed by extending tests and render paths that already exist in the codebase. The rest need either a cited source (F-22) or a decision to publish a range instead of a point (F-01, F-06, F-08).

Worth stating plainly, because it is unusual: **every arithmetic chain I tested was correct.** The CRF reproduces to six decimal places. The 4,394.5 / 11,325.1 = 38.8 % division is exact. The Ongkharak hypsometric JSON reproduces its DEM to 0/36 rows. The harmonic constituent periods are astronomically right. The routing geometry reproduces A, P, R to the decimal. Not one finding in this report is an arithmetic error. Every single one is an *identification* error — a number that is correctly computed from assumptions that are wrong, unmeasured, or unstated. That is a much easier class of problem to fix, and a much more dangerous one, because the arithmetic is what currently earns the numbers their credibility.

**Recommended sequence:** (1) correct the reader-facing provenance and internal contradictions (F-02, F-07, F-15, F-16) — these are pure accuracy defects with no modelling content; (2) relabel the Ongkharak +3.20 m, the compound-flood absolute risk classes, and the counterfactual results as assumptions or upper bounds (F-01, F-08, F-10, F-26); (3) replace the three broken statistical treatments (F-04, F-13, F-06) with methods that are identified; (4) harden the gates so the next literal cannot ship (F-17, F-18).

---

*Prepared by independent red-team review. Read-only; no repository file was modified. All command outputs quoted above were executed in this session. Items marked UNVERIFIED are explicitly not asserted as errors — only as items this repository cannot presently settle.*
