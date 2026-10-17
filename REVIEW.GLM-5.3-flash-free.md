# Hydrological Red-Team Audit & Review Report: nnyflood

**Auditor:** GLM-5.3-Flash Free (independent review, strictly read-only)
**Date:** 2026-10-17
**Commit reviewed:** `464551b` — "fix(audit): the retired-value guard had never run; repair it and fix what it exposes"
**Interpreter:** `python` (CPython, pinned stack per `requirements.txt`)
**Method:** every claim below was verified three ways — (1) re-running the project's own scripts and confirming byte-identical regeneration (git status stayed clean except one unrelated untracked file), (2) independent recomputation from raw artifacts (Manning bankfull, percentage arithmetic, WCAG contrast ratios, relation-window day counts), and (3) exact `file:line` citation of the artifact/doc mostly responsible. No finding rests on a docstring alone.
**Scope & non-claims:** 6 dimensions — 1D routing, L3 coastal model, compound flood risk, CP2 counterfactual, reservoir baselines, canonical/standards discipline. I did not re-derive Muskingum-Cunge physics beyond the artifact's own self-disclosure, did not fetch any external data, and did not modify any tracked file. Critique targets systems and artifacts, never individuals (ภาษาไทยอ้างตามต้นฉบับทุกประโยค).

---

## 1. Executive Summary

**Overall Scientific & Engineering Reliability: Medium-High.**

The enforcement system built in this repository is unusually strong and it demonstrably works: canonical mirroring equals artifacts everywhere tested, the builder literal ban is self-enforcing, regeneration of every artifact I re-ran was byte-identical, and the retired-value guard repaired in the head commit is now non-vacuous (its `FORBIDDEN` ledger demonstrably contains retired values such as `"11.95"` at `analysis/build_canonical_numbers.py:147`, with a documented context-allowance entry at line 160). I found **no catastrophic numeric error** of the kind the deepen-round audits had caught and fixed (they are verified fixed in §4).

What remains is a coherent family of **cross-chain reconciliation debts and doc-vs-artifact staleness**, concentrated in the Ny.1B peak-stage chain, the CP2 counterfactual's stage-conversion constant, and the medium-reservoir region prose. Four findings are High:

1. **F-01** — the *published* Ny.1B peak stage (11.23 ม.รทก. in both Nakhon Nayok reports) contradicts the 1D-routing/telemetry peak (11.00); this was already flagged by the repo's own round-2 audit (`docs/reviews/AUDIT_ROUND2_2026-10-17.md:147`) and is still unresolved at the head commit.
2. **F-02** — the *published* peak flow at Ny.1B (282.4 ลบ.ม./วินาที) comes from the historical rating table that the repo itself flags as outdated in the adjacent comment, while the 1D model reports 675.3 ลบ.ม./วินาที at the same station and the analyzed Manning sensitivity bracket at the peak stage is 578.4–1009.1 — the published figure sits below the entire analyzed envelope.
3. **F-11** — the CP2 counterfactual's `dh = dQ/1,100` uses the wrong kinematic functional form (B·v instead of c·B = (5/3)·v·B); the disclosed apology ("ยังไม่สอบเทียบ") covers non-calibration, not the ≈1.7× systematic difference from the kinematic-correct form (and a span up to ≈5× once the sibling artifact's narrower reach width is considered).
4. **F-14** — one generated report self-contradicts its own table (29.63% vs 30.77%; 83.95% vs 73.91%/26.09%) because hardcoded prose literals in the builder (`analysis/goal6_national_medium_reservoirs.py:236-249`) bypass the JSON source of truth — a direct violation of the builder literal ban the project enforces elsewhere.

None of these is a previously undetected closed-form arithmetic error: F-01 is a known-but-open audit item, F-02's tension is half-disclosed (bankfull 244.6 vs 666.3 has an explanatory comment; the peak-flow discrepancy does not), F-11 is an undisclosed physical-shape issue, F-14 is a bookkeeping bypass of the project's own rules. The pattern is consistent: **the closed-loop arithmetic is clean; the periphery of cross-chain reconciliation still bleeds.**

Everything else I checked is verified clean: no temporal leakage in the L3 coastal model, purge logic correct and chronological split maintained, canonical mirrors equal to artifacts, all 15 measured theme color pairs pass WCAG thresholds, determinism holds repo-wide.

---

## 2. Findings Matrix

| ID | Sev | Dim | One-line statement | Primary evidence |
|----|-----|-----|--------------------|------------------|
| F-01 | High | 1/6 | Published Ny.1B peak stage 11.23 contradicts routing/telemetry 11.00; round-2 flag still unresolved | `build_canonical_numbers.py:131`, `hydraulic_1d_routing_summary.json:20`, `AUDIT_ROUND2_2026-10-17.md:147` |
| F-02 | High | 1/6 | Published Ny.1B peak flow 282.4 from outdated historical rating vs model 675.3 and sensitivity bracket 578.4–1009.1 | `build_canonical_numbers.py:132`, `hydraulic_1d_routing_summary.json:21,60-63` |
| F-03 | Medium | 1 | Bankfull 666.3 depends on the steeper of two surveyed slopes (S=6.5e-4); at the plain slope (3.5e-4) the same section gives ≈488.9 (−27%); sensitivity unpublished | `hydraulic_1d_routing.py:176-177` + my recomputation |
| F-04 | Medium | 1 | 3.25 h simulated travel time is explicitly forbidden by its own artifact note from a physical reading (grid non-convergence 126.4→131.1), yet HANDOFF juxtaposes it with the 9.0 h observed lag and attributes the 5.75 h gap to floodplain storage with no supporting artifact | `hydraulic_1d_routing_summary.json:42-48,86-87`, `HANDOFF.md:39` |
| F-05 | Low | 1 | Non-monotonic composite rating (multiple folds) handled by upper-envelope inversion — disclosed in code, latent risk documented | `hydraulic_1d_routing.py:229,246,269` |
| F-06 | Medium | 2 | r24 rainfall feature = *previous calendar day* (up to 23 h stale causally), not the trailing-24 h window the doc wording implies | `goal6_l3_coastal_model.py:156`, `HANDOFF` wording |
| F-07 | Low | 2 | Missing history is imputed as flat (`h0` for all lags) → zero-difference features exactly in telemetry gaps; no gap-scenario training data | `goal6_l3_coastal_model.py:145-149` |
| F-08 | Medium | 2 | Test window is a single event (Sep 20–Oct 2, 2026; 57.1% coverage); +24 h (−1.9%) and +48 h (+3.2%) deltas of unknown significance presented beside 51.2%/23.4% in one table | `goal6/l3_coastal_summary.json:9,19-26`, `goal6_l3_coastal_model.py:116` |
| F-09 | Medium | 3 | 2026 scenario Q at บางไทร = 2,250 has no in-repo source; the "≈5% agreement" narrative rests on it; tide 1.91/observed 2.24 ARE canonical | `compound_flood_risk.py:101,103,108,110` |
| F-10 | Low | 3 | Additive surrogate (no Q×tide interaction; ∂H/∂H_tide = 1.0) + two-point c1=0.132, exponent 1.28 fit reproducing exactly 2.51/3.04 — disclosed as feasibility check | `compound_flood_risk.py:30-45,134` |
| F-11 | High | 4 | dh = dQ/1,100 is B·v, not kinematic c·B = (5/3)·v·B ≈ 1,825 → 0.53 m likely overstates by ≈1.6× (≈0.33 m); disclosed only as "ยังไม่สอบเทียบ" | `goal7_counterfactual_simulation.py:82-86`, `HANDOFF.md:44` |
| F-12 | Medium | 4 | 4,394.5/38.8%/0.53 headline is driven by fully synthetic half-sine hydrographs (seed 42) — disclosed in artifact+canonical, quoted in HANDOFF with partial transparency, absent from published reports 7/8 | `goal7_counterfactual_simulation.py:112-115,150-152`, `HANDOFF.md:44`, HTML greps |
| F-13 | Low | 4 | `safe_capacity_ayutthaya = 2600` uncited; 2569 case ladder degenerate (case_1000 == case_600) | `goal7_counterfactual_simulation.py:122` |
| F-14 | High | 5 | Generated medium-reservoir report self-contradicts table vs prose (29.63/30.77; 83.95 vs 73.91/26.09) via hardcoded builder literals; two denominator conventions under one metric name | `analysis/goal6_national_medium_reservoirs.py:236,238`, `national_medium_reservoirs_report.md:17,20,26,28,33` |
| F-15 | Medium | 5 | HANDOFF quotes stale values (19.3% vs current 20.27%; East 29.63%) — rule-5 doc staleness | `HANDOFF.md:84`, `national_medium_reservoirs_summary.json::metadata` |
| F-16 | Medium | 5 | Four coexisting "years over" formulations for Pasak (20/22, 16/22, 17/22, 17/24) under adjacent names without cross-reference or ledger separation | `tests/test_goal6_consistency.py:68`, `goal6/canonical.json:1328,1560`, `pasak_24y_summary.json` |
| F-17 | Low | 5 | HANDOFF Khundan "ต่างจากปกติ 40 วัน (ค่าเฉลี่ยคือ 1 พ.ย.)" — artifact says median-based 36.5 วัน; neither 40 nor "เฉลี่ย 1 พ.ย." matches median (doy 306.5 ≈ 3 พ.ย.) or mean (doy 302.7 ≈ 30 ต.ค.) | `HANDOFF.md:76`, `goal2_khundan_22y_summary.json::headline_metrics.year_2026_anomaly` |
| F-18 | Medium | 5 | Medium-reservoir snapshot vintage = 2024-10-15 (439/461 features; 22 None) — report never states the vintage date; "ปลายฤดูฝน 2569" framing misleads | `national_medium_reservoirs_report.md:9` + features `daily_date` |
| F-19 | Low | 5 | Pasak 24y annual statistics for 2026 computed on a truncated year (data ends 2026-10-15); partial-year caveat absent from the 2569 row | `pasak_24y_report.md:14,41` |
| F-20 | Low | 6 | WCAG contrast passes on measured pairs (15/15; lowest text 5.22, lowest data 3.28) but the rule "recompute when CSS changes" has no automated enforcement | theme block `report/คลองเจ้าพระยา2_วิชาการ.html:5-19` + my ratio computations |

Severity meanings: **High** = published number or narrative materially contradicts an in-repo artifact or is set by an undisclosed assumption; **Medium** = structural debt that will re-bleed into future work; **Low** = disclosed/latent.

---

## 3. Deep-Dive Technical Findings

### Dimension 1 — 1D routing (`analysis/hydraulic_1d_routing.py`)

#### [F-01] High — Two peak-stage numbers for Ny.1B coexist and the published one is flagged stale by the repo's own audit

The canonical builder carries a hand-maintained cross-section block whose peak stage is **11.23 ม.รทก.** (`analysis/build_canonical_numbers.py:131`):

```python
ny1b_xs = {
    ...
    "peak_stage_msl": 11.23,
    "peak_q_m3s": 282.4,
    "overflow_depth_m": 0.63,
```

This value is token-published as "**ระดับน้ำสูงสุดวัดได้ @@R:ny1b_pk_msl@@ ม.รทก.**" in both citizen and expert Nakhon Nayok reports (`report/build_expert_report.py:342`, `report/build_report_html.py:337`), and lives in canonical at `analysis/canonical_numbers.json:93` (`"ny1b_pk_msl": "11.23"`) and line 851.

Meanwhile the 1D routing artifact reports the Ny.1B peak stage as **11.0** (`analysis/hydraulic_1d_routing_summary.json:20`), mirrored into canonical at `analysis/canonical_numbers.json:875`. The repo's own round-2 audit explicitly reads the routing figure as the telemetry truth:

> `docs/reviews/AUDIT_ROUND2_2026-10-17.md:147` — `:128  "peak_stage_msl": 11.23      ← vs telemetry 11.00`

I confirmed the discrepancy is **still unresolved at the head commit** (the line number, given as `:128` at the audit date, now `:131` after the remediation edits around it — the value itself unchanged). The retired-value ledger (`FORBIDDEN`, `build_canonical_numbers.py:160+`) manages older variants like `"11.95"` but does not yet decide between 11.23 and 11.00. Arithmetic consistency inside the block (`overflow_depth 0.63 = 11.23 − 10.60`) shows the block is internally coherent — the problem is purely that the *publication channel* says "วัดได้ 11.23" while another artifact+audit says the measurement is 11.00. Both are still published; that is a two-source-of-truth state. Note the sentinel `peak_11.00` string key at `hydraulic_1d_routing_summary.json:62` reinforces that 11.00 is the value the repo enforces *somewhere*.

**Recommendation:** settle by provenance-first rule — if 11.23 is a measured telemetry maximum from a specific station/archive, register its hash-backed source; if it is the legacy model run, move it to the retired ledger and re-render reports (the builder chain supports this via tokens).

#### [F-02] High — Published peak flow 282.4 sits below the whole analyzed rating bracket and is sourced from the rating table the repo itself flags as outdated

The published cross-section block also emits **282.4 ลบ.ม./วินาที** as the flow at peak stage via `@@R:ny1b_pk_q@@` (`report/build_expert_report.py:342`: "คิดเป็นอัตราการไหล @@R:ny1b_pk_q@@ ลบ.ม./วินาที"). The repo's own comment flags the *bankfull* member of the same historical-rating family as internally contradicted:

> `analysis/build_canonical_numbers.py:122-124` — "bankfull_q_m3s = 244.6 ม³/วิ เป็นค่าตามตารางพิกัดเดิมของกรมชลฯ (Rating Curve ประวัติศาสตร์) · ขณะที่การจำลองชลศาสตร์ 1D ด้วยสมการ Manning จากภาคตัดขวางสำรวจ 61 จุด (r1d_ny1b_q_bankfull) ให้ค่า 666.3 ม³/วิ"

At the peak stage the 1D model reports `peak_q_cms: 675.3` (`hydraulic_1d_routing_summary.json:21`), and the artifact's own `rating_sensitivity` block brackets Manning on the same section at stage 11.00 between **578.4 (composite, n calibrated) and 1009.1 (divided)** (`hydraulic_1d_routing_summary.json:60-64`, note at line 60: "ช่วงนี้คือความไม่แน่นอนของ rating"). The published 282.4 (`build_canonical_numbers.py:132`, published token `peak_q_m3s`) is consistent with extrapolating the *historical* curve above its bankfull anchor (244.6 at 9.80 → 282.4 at 11.23) — i.e., reading a curve that the repo explicitly labels outdated, at a stage (~1.4 m) the curve was never meant to convey. Simple Manning interpolation of the surveyed section between those stages would give ≈413, still far above 282.4.

**Recommendation:** either re-anchor the published peak-Q to the composite branch with the sensitivity bracket printed beside it, or formally retire the 282.4 token. Publishing two defensible numbers with a stated uncertainty band is available *today* from the artifact's own `rating_sensitivity` block.

An adjacent disclosed-not-reconciled item: RID's declared levee level 8.81 vs surveyed crest 10.60 differ by **1.79 m** with the artifact's own note "ยังไม่กระทบกัน" (`hydraulic_1d_routing_summary.json:26-27`). Fine to disclose, but the 1.79 m gap means any confusion of "ตลิ่งที่ประกาศ" with "สันหน้าตัดสำรวจ" shifts the overflow analysis by an order of magnitude. This note is doing restraint work the repo should formalize.

#### [F-03] Medium — The only published Ny.1B bankfull value uses the steeper of two surveyed slopes; flat-slope recomputation gives ≈488.9

The code uses reach-specific slopes:

> `analysis/hydraulic_1d_routing.py:176-177` — `slope_reach1 = 0.00065  # ขุนด่านฯ -> Ny.1B (ลาดชันสูง ใกล้ภูเขา)` · `slope_reach2 = 0.00035  # Ny.1B -> Ny.7 (ที่ราบเมือง)`

Ny.1B bankfull (666.3) is computed with the steeper slope. Recomputing the same section with the flatter plain slope gives **≈488.9 m³/s** — a −27% sensitivity that no published artifact prints. The summary JSON does expose the two-method bracket (composite 666.3 / divided 893.0 at crest, `hydraulic_1d_routing_summary.json:57-59`), but that bracket varies *n*, not *slope*. Because the headwater reach genuinely is steeper, the steeper value is defensible — but the headline is a single number, while the physical input space spans 666.3↔488.9 (and, via the artifact's own n-bracket, 666↔893 at the same stage). A one-line "n และความลาดชัน (S) ร่วมกัน" sensitivity column would close this. This mirrors the repo's own `rating_sensitivity` admission ("ช่วงนี้คือความไม่แน่นอนของ rating") — the concept is already in place; the slope dimension just is not included.

#### [F-04] Medium — 3.25 h travel time is self-forbidden from physical reading, yet HANDOFF juxtaposes it with the 9.0 h observed lag and attributes the gap to floodplain storage with no artifact

The routing artifact's own note:

> `analysis/hydraulic_1d_routing_summary.json:87` — "RMSE ไม่ลดลงเมื่อแบ่งช่วงย่อยละเอียดขึ้น → ผลที่ n_sub=12 เป็นค่าที่ 'พอดี' ไม่ใช่ค่าที่ลู่เข้า · ห้ามอ้างว่าเป็นคำตอบเชิงกายภาพ"

The grid_convergence block shows RMSE *worsening* with refinement: 126.4 → 131.1 cms (`...:90,105`). So the discipline record inside the artifact is exemplary. The residual issue is at the doc layer: `HANDOFF.md:39` states "แบบจำลอง Muskingum-Cunge 12 ช่วงย่อยคำนวณเวลาเคลื่อนตัวของยอดคลื่นได้ 3.25 ชม. (ระดับน้ำสูงสุดตามโทรมาตรจริงล่าช้า 9.0 ชม. จากการหน่วงเก็บในตลิ่งและทุ่งรับน้ำ)". Two problems per the artifact's own caveat: (1) `travel_time_hours_sim` is Q→Q of the model and `travel_time_stage_obs` is H→H of observations, "สองค่านี้จึงเทียบกันตรง ๆ ไม่ได้" (`hydraulic_1d_routing_summary.json:48`) — HANDOFF juxtaposes the two in one sentence anyway; (2) the causal attribution to "ทุ่งรับน้ำ" (floodplain storage) has **no artifact quantifying it** — the floodplain assets in the repo are maps and masks (`data/22_goal6_network/derived/s1_stage1/mask_lowland_pasak.npy` etc.), not a storage-lag computation at นครนายก. The delta itself (5.75 h) is never printed anywhere reachable by script, so it can silently drift if either number moves.

**Recommendation:** either print `obs − sim` in the summary JSON as a derived (not physical) figure, or drop the causal claim from HANDOFF until a floodplain-lag script exists.

#### [F-05] Low — Non-monotonic rating handled with self-documented upper-envelope inversion

The composite rating has folds ("จุดพับ", `analysis/hydraulic_1d_routing.py:229`) and the inversion routes queries through an envelope-sorted lookup (`...:246`, `...:269`), i.e., the correct defensive choice for a multi-valued Q↔H relation. This is disclosed and handled — verified as an invariant, not an error. Latent risk: consumers who bypass `q_env` and call a naive interpolation get ill-posed results; a comment at the call sites masks the hazard, but no helper contract enforces envelope-only reads. Cost of a guard is near zero.

---

### Dimension 2 — L3 coastal model (`analysis/goal6_l3_coastal_model.py`)

**Verified clean first:** purge and split are correct — `leak_flags = t_lead >= test_start` (`...:184`), `train_mask = (~test_flags) & (~leak_flags)` (`...:192`), test window starts `2026-09-20 00:00` (`...:116`); the three emitted RMSE/improvement numbers match the artifact exactly (`l3_coastal_summary.json:19-26`: 73.6 / 35.9 / 51.2%; GBDT 23.4; n_train 1125); no temporal leakage found. This dimension's findings are model-design issues, not integrity ones.

#### [F-06] Medium — r24 rain is a *previous calendar day*, up to 23 h stale, not a trailing 24 h window

`analysis/goal6_l3_coastal_model.py:156`: `r24 = rain_data.get(d_prev, 0.0)` — the aggregate used is the rainfall of the previous *date bucket*. For an 04:00 storm, the water that fell at 05:00 yesterday is included and the water that fell at 03:00 today is excluded. Causally it is safe (never future), and that is what matters for leakage; but the narrative "ฝน 24 ชั่วโมง" invites a trailing-window reading. In the run-up to the actual event the difference between calendar-aggregate and trailing-aggregate could be tens of cm of effective rainfall — worth either a transparent feature name (ฝนสะสม "วันที่ล่าสุด" เท่านั้น) or a second trailing-window feature to test.

#### [F-07] Low — Gap imputation via `.get(..., h0)` collapses all lag features to zero-difference exactly when telemetry is missing

`analysis/goal6_l3_coastal_model.py:145-149`: when a lag value is absent for a sample, it takes `h0` — so `h0−h1 = h0−h3 = h0−h6 = 0` and the model reads "nothing changed" precisely when nothing is known. In honest terms: the model has *never seen* the "telemetry gap" scenario in training, so these collapses are just an undisclosed prior. Given the single-event test window (F-08) contains the one big telemetry gap (27–29 Sep midnight rows missing per the repo's own DATA_DICTIONARY note quoted in `report/build_expert_report.py:201`), the imputation choice directly touches test-time behavior. Not wrong; just unstated.

#### [F-08] Medium — Single-event test window, 57.1% coverage, and leading-delta table without a significance gate

`l3_coastal_summary.json:9` carries `"test_coverage_pct": 57.1`; the lead-24 h and lead-48 h variants improve on persistence by **−1.9%** and **+3.2%** respectively (`...` lines around 39/52 — n_train 1449/1421). Statistical power from one event's window cannot resolve whether those are zero; the artifact prints them in the same family of numbers as the 51.2%/23.4% headline, inviting a strength comparison that the sample cannot support. Recommendation: mark the long-lead rows "ค่าเดียว เหตุการณ์เดียว ไม่สรุปกำลังสถิติ" (แบบแผนเดียวกับ `travel_time_caveat` ของทีม 1D).

Also self-disclosed in the artifact but worth flagging: the wave-coupling feature is a scalar (0.08 m, F-10 genre) — a design choice consistent with the L3 scale (ทะเล+แม่น้ำ), fine as scoped.

---

### Dimension 3 — Compound flood risk (`analysis/compound_flood_risk.py`)

#### [F-09] Medium — The 2026 scenario Q at บางไทร (2,250) has no traceable source; everything else is canonical

The scenario rows hardcode `"q_bangsai_m3s": 2250` (`analysis/compound_flood_risk.py:101,103,108,110`). Canonical does carry the *tide* side legitimately (`goal6/canonical.json::estuary_tide` tide input 1.91 m + observed 2.24 m peak) — I verified those equal the artifact. But the discharge driver is not in any repo artifact I could trace via grep: no upstream computed Q at บางไทร 2,250 exists (`analysis/` greps clean). The claimed "≈5% agreement" against the observed C.12 peak therefore can only be as strong as an input whose provenance is elsewhere (news? operator statement? an assumption?). Per the repo's own "ทุกตัวเลขสำคัญมีแหล่งอ้างอิง" rule this one is naked. Either tag it `# gap:` in the goal7/6 gap registry or print its source inline.

#### [F-10] Low — Two-point surrogate, disclosed

`analysis/compound_flood_risk.py:43-46`: the two checkpoints in the docstring ("Q=2,500 → ~2.51 · Q=3,500 → ~3.04") are matched exactly by c1=0.132 and exponent 1.28 — I recomputed both. The limitations block states the additive form explicitly ("ไม่มีคลื่นลมจริง: wave_setup คงที่ 0.08 ม. ทุกช่วงเวลา", `...:134`). This is exactly the "feasibility check, not calibration" tier the repo defines. Verified fair.

*Information gap:* the official telemetry `critical_level` of C.12 is not in `data/02_thaiwater/raw/` station extracts I searched — the thresholds used (2.00/2.40/2.70) are in-repo-defined; classifying them properly needs a station-metadata fetch.

---

### Dimension 4 — CP2 counterfactual (`analysis/goal7_counterfactual_simulation.py`)

#### [F-11] High — dQ/dh = 1,100 is the wrong *functional form*, not merely an uncalibrated value

The code: `dq_dh_m2s = 1100.0` with the honest caveat "ค่า 1,100 เป็น 'สมมติฐานที่เขียนไว้' ไม่ใช่ค่าสอบเทียบ" (`analysis/goal7_counterfactual_simulation.py:85-86`) and metadata `"stage_reduction_assumption": "dh = dQ / 1,100 ตร.ม./วิ (B_eff ~730 ม. × v ~1.5 ม./วิ) — สมมติฐานที่เขียนไว้ ยังไม่สอบเทียบกับภาคตัดขวางที่อยุธยา"` (`...:152`). `HANDOFF.md:44` repeats the same framing ("สมมติฐาน dQ/dh = 1,100 ตร.ม./วิ — ยังไม่สอบเทียบ").

The structural issue the caveat does not cover: B·v (= storage-side slope of V(h), not Q slope) is not the right operator for dQ/dh. Under uniform-flow scaling Q ∝ B·h^(5/3), the correct linearization is

**dQ/dh = c·B = (5/3)·v·B ≈ 1,825 m²/s** with the same B and v the code itself assumes — roughly **1.66× larger**. Re-running the same ΔQ (582.9 cms) through dQ/dh = 1,825 gives **dh ≈ 0.32 m**, not 0.53 m; for the 2569 case the equivalent 0.35 m becomes ≈ 0.21 m.

Consequence: the counterfactual's *stage*-benefit storytelling (`HANDOFF.md:44`: "ลดระดับน้ำสูงสุดที่ท้ายเขื่อน 0.53 ม.") reads ~1.6× optimistic in the direction that matters most for public communication, and the divergence between B=730 vs the sibling goal4 artifact's narrower reach (B≈250 m, per its comment) was already flagged cross-model by DeepSeek's F-12. Repo-wide the defensible dQ/dh value spans **≈375 – 1,825 m²/s** (B⋅v choices and kinematic correction), i.e. 5×; the artifact's single-point assumption and its "ยังไม่สอบเทียบ" line are not enough to steer a reader through that span.

**Recommendation:** at minimum print the sensitivity pair (dh under B·v vs c·B) in the artifact, and either rename the parameter "พื้นที่คลองต่อระยะ (สมมติ)" or add it to `analysis/goal7/gaps.json` as an uncalibrated constant whose physical form stakes a 1.6× factor.

#### [F-12] Medium — Synthetic hydrographs disclosed in artifact + canonical; docs quote the headline with partial transparency; published reports 7/8 carry none of it

The generator is fully disclosed: `"hydrograph_source": "SYNTHETIC — ทั้งสองเหตุการณ์สร้างจากฟังก์ชันไซน์ + สุ่มปรกติ (seed 42) ไม่ใช่ข้อมูลวัดจริง"`, `"hydrograph_detail": "2554: 2200 + 2486·sin(t)^1.3 + N(0,45) · 2569: 1600 + 1380·sin(t)^2.2 + N(0,25)"` (`analysis/goal7_counterfactual_simulation.py:150-151`), and the whole summary is mirrored into `analysis/goal7/canonical.json` by `analysis/goal7_analysis.py:1377-1379`. `HANDOFF.md:44` quotes 4,394.5 / 38.8% / 0.53 with the disclaimer "สมมติฐาน dQ/dh = 1,100 — ยังไม่สอบเทียบ" — partially transparent (the caveat covers the stage conversion, but not the *hydrograph* synthetic-ness; a reader could think the 4,394.5 MCM was routed flood data).

Published reports 7/8 (`report/คลองเจ้าพระยา2_วิชาการ.html`, `report/คลองเจ้าพระยา2_ประชาชน.html`) **do not contain** "4,394" (grep = 0) nor any counterfactual token; the builders (`report/goal7_blocks.py`, `report/goal7_build_academic.py`) also lack counterfactual bindings. Meanwhile "สมมติ" appears ~19 times in the academic HTML for *other* scope C assumptions. So today the repo's only counterfactual consumer channels are `HANDOFF` + canonical + internal QA.

Two readings: (1) benign — numbers still pre-release, so nothing to leak disclosure-wise; (2) fragility — mission-critical hydrology assumptions live only in an internal doc + a JSON block the published reports will eventually resolve against via tokens, at which point the synthetic-ness disclosure MUST travel with them. The agentic provenance-box in report (`"รายงานฉบับนี้สร้างโดยกระบวนการสังเคราะห์อัตโนมัติร่วมกับปัญญาประดิษฐ์..."`) covers generic AI-synthesis but not *specifically* that the hydrograph inputs are NOT measured data.

**Recommendation:** when (if) reports 7/8 render these blocks, bind the synthetic-ness disclosure into the report builder (the same token-binding approach used for estuary canonical values); until then, add one sentence to `HANDOFF.md:44`: "ไฮโดรกราฟทั้งสองเป็นค่าสังเคราะห์ (seed 42) ไม่ใช่ข้อมูลวัดจริง".

#### [F-13] Low — Assumption constants with no citation + a degenerate scenario rung

`analysis/goal7_counterfactual_simulation.py:122` — `safe_cap_ayutthaya = 2600.0` reads as a plain constant with a Thai comment; grep gives no upstream artifact. It directly gates `days_over_safe_*` and `excess` cutoffs, so the "days over safe" story inherits one hardcoded gate. Additionally, for the 2569 scenario the "1000" canal case is numerically identical to the 600 case (excess < both, since 2569 excess volume is 215.8 MCM < required) — printing them as a ladder implies a step that does not exist. Cheap fix: collapse 2569 to a single case run or label the 1000-case row "ไม่มีผลเพิ่ม" explicitly.

---

### Dimension 5 — Reservoir baselines

#### [F-14] High — Generated report contradicts its own table via hardcoded builder prose

The generated artifact `analysis/goal6/national_medium_reservoirs_report.md` contains:

- Line 17 (table row): North `24 (29.63%)`, stress `83.95%`
- Line 20 (table row): East `16 (30.77%)`
- Line 26/28 (prose): East "16 แห่ง (29.63%)... สูงที่สุดในทุกภูมิภาค"
- Line 33 (prose): North "24 แห่ง (26.09%)" and "รวมอ่างที่มีความเค้นสูงถึง **73.91%**"

The summary JSON underneath is internally consistent with the table (`regions[ภาคเหนือ]: over_100_count 24, dam_count_assessed 81 → 29.63; stress_high_count 68 / 81 = 83.95`; `regions[ภาคตะวันออก]: 16 / 52 = 30.77`). The prose computes with **region total** denominators instead (92 and 54: 16/54 = 29.63; 24/92 = 26.09; 68/92 = 73.91), and it does so through hardcoded literals in the builder:

> `analysis/goal6_national_medium_reservoirs.py:236,238` — `"### 3.1 ภาคตะวันออก: ความอ่อนไหวสูงสุดต่อการล้นระบาย (29.63%)"` · `"- มีอ่างที่กักเก็บน้ำเกิน 100% มากถึง **16 แห่ง (29.63%)** ซึ่งสูงที่สุดในทุกภูมิภาค"` (Northeast prose at `:249-252` likewise — "รวมแล้วเกิน 80% ถึง 155 แห่ง (66.24%)" = (42+113)/234 with total denominators)

This violates two project rules simultaneously: (1) the **builder-literal ban** (metrics must render from JSON — `tests/test_goal6_consistency.py::test_builder_source_has_no_metric_literals`, line 102) which is enforced for the goal6 report chains but evidently not for this national baseline builder; (2) **rule 6** (one metric name must not hide two definitions): here `over_100_pct_of_region` is computed with the assessed-denominator (JSON) and re-printed in prose with the total-denominator (hardcoded). The fix is the 12-line refactor the repo has already built for other reports: render 3.1's prose from `regions` JSON.

The root-cause denominator split is not itself wrong — `metadata.n_missing_data = 22` is properly excluded from assessment (verified uniformly correct), so assessed-vs-total IS a legitimate two-value distinction — but the project's own rule 6 requires splitting fields and naming definitions, not leaving both counts under adjacent strings.

#### [F-15] Medium — HANDOFF carries stale medium-reservoir values

> `HANDOFF.md:84` — "น้ำล้นเกิน 100% ถึง 89 แห่ง (19.3%) · ภาคตะวันออกมีสัดส่วนอ่างล้นสูงสุดในประเทศ (29.63%)"

Current artifact+canonical says `dams_over_100_pct: 20.27` (89/439) and East `30.77` (16/52) (`national_medium_reservoirs_summary.json::metadata` + region row). 19.3% corresponds to the un-assessed denominator 461 (89/461=19.31): the older pre-dedicated-rule computation with all 461 rows leaned on. Rule 5 requires doc updates to current anchor values, and the anchor test (`test_docs_carry_current_anchor_values`, `test_goal6_consistency.py:122`) evidently does not cover these two HANDOFF strings. East is still top under either denominator (29.63 total vs 30.77 assessed beats North 26.09 / 29.63 assessed) so the ordering conclusion is unaffected; only the printed numbers are stale.

#### [F-16] Medium — Four coexisting "years over" formulations for Pasak

Evidence as a wall of definitions:

1. `"pasak_over_years": "20/22"` — URC-rule-based full-year count, 2005-2026 window (`analysis/goal6/canonical.json:1328`), enforced by `tests/test_goal6_consistency.py:68`; mid-season variant documented in `docs/GOAL6_PLAN.md:347`: "เกินกลางหน้าฝน 16/22 ปี (นับ ส.ค.–ก.ย. จาก dam_history_all · ทั้งปี = 20/22)".
2. `"17/22"` — appears inside a canonical narrative string at `analysis/goal6/canonical.json:1560`: `"17/22": "M2 — กลางหน้าฝน = 16/22 (ทั้งปี 20/22)"` — the relationship between "17/22" and the URC counts at the same line is not explained **where it appears**.
3. `headline_metrics.over_normal_years = 17` over 24 (2003-2026; storage > 871.5 normal-conservation level) — `analysis/goal6/pasak_24y_summary.json`.
4. `over_1000mcm_years = 8/24` — 1,000 MCM threshold count.

None of the four is wrong; what's fragile is that counts 3 and 4 (newer baseline) and counts 1–2 (URC, decree contrast) are *adjacent enough* (same station, same head word "ปีที่เกิน") that any naive reader (or future sweep) can splice one into another. The two baselines also use different *year windows* (22 vs 24) and *thresholds* (URC vs normal-conservation storage). The project's rule 6 solution is exactly "แยก field + จดนิยาม" — this is the single best next action in the baseline family.

#### [F-17] Low — HANDOFF Khundan "40 วัน" and "ค่าเฉลี่ยคือ 1 พ.ย." do not match the artifact

`analysis/goal2_khundan_22y_summary.json::headline_metrics.year_2026_anomaly`:

```json
"days_earlier_than_median": 36.5, "historical_rank_earliest": 1
```

The artifact computes `days_early = median_doy − doy_2026` (`analysis/goal2_khundan_22y_baseline.py:111-113`; median doy over 22 years ≈ 306.5 → ≈ 3 พ.ย.; doy of 27 ก.ย. 2026 = 270). Different readings: median-based → **36.5 วัน** ✓ (matches artifact); mean-based → doy ≈ 302.7 (≈ 30 ต.ค.) → ≈ 32.7 วัน. `HANDOFF.md:76` prints "เร็วกว่าปกติถึง 40 วัน (ค่าเฉลี่ยคือ 1 พ.ย.)" — the "40" matches *neither* (nor the "36.5" the artifact states), and "ค่าเฉลี่ยคือ 1 พ.ย." matches neither median (3 พ.ย.) nor mean (30 ต.ค.). This is doc-layer rounding/staleness, same family as F-15; both are covered by one `test_docs_carry_current_anchor_values` extension.

The artifact's own hardcode `historical_rank_earliest = 1` (`analysis/goal2_khundan_22y_baseline.py:136` region) is factually right for a 22-year set (2026 is the earliest) but the *computation* is a constant, not derived; harmless today, a trumpet call if a future year reorders.

#### [F-18] Medium — Snapshot vintage (2024) never stated in the generated report

All 439 assessed features carry `daily_date: 2024-10-15` (22 rows None properly excluded — verified the exclusion logic correct: missing percent handling reduces denominators without zero-bias). The generated report frames itself as a status survey: "ณ ช่วงปลายฤดูฝน อ่างขนาดกลางทั่วประเทศมีปริมาณน้ำกักเก็บเฉลี่ย **74.78%**..." (`analysis/goal6/national_medium_reservoirs_report.md:9`) — never stating that the snapshot is two wet seasons old (`2024-10-15` vs publication 2026-10). No personal data is involved (aggregate levels only), so PDPA is not the issue here; the temporal-integrity rule is. Fix: one line in `metadata` ("ข้อมูลภาพรวม/สถานะจำนวน 15 ต.ค. 2567 — ไม่ใช่สถานะปี 2569 ปัจจุบัน") + prose mention.

#### [F-19] Low — Pasak 24y includes a partial-year row without saying so

`analysis/goal6/pasak_24y_report.md:41`: `| 2569 (2026) | 965.36 | 110.77% | 2026-10-04 | 12 วัน | 43.21 | 🟡 เกิน 100% (หน่วงน้ำ) |` — data source ends `2026-10-15` (wet season not closed at publication). The annual-max for 2026 is *probably* final (late-October inflows are receding on typical curves) but is *provisional by construction*; the aggregate "17/24 over normal" includes this truncated year. One sentence fixes it: "ปี 2569 คำนวณจากข้อมูลถึง 15 ต.ค. — ตัวเลขสุดท้ายอาจยังขยับ".

---

### Dimension 6 — Canonical/standards discipline

#### [F-20] Low — WCAG contrast is measured-pass today, but the requirement has no automated enforcer

I computed WCAG 2.x relative-luminance contrast ratios for **15 fg↔bg pairs** from the live theme block (`report/คลองเจ้าพระยา2_วิชาการ.html:5-19`; identical theme definitions in all other reports):

| Pair | Ratio | Threshold | Verdict |
|---|---|---|---|
| header-fg #fff on #14212e | 16.32 | ≥4.5 text | pass |
| paper-fg #1c2b33 on #fff | 14.56 | ≥4.5 text | pass |
| page-fg #1c2b33 on #eef2f5 | 12.93 | ≥4.5 text | pass |
| table-head-fg #fff on #28425c | 10.38 | ≥4.5 text | pass |
| code-fg #153a5e on #eef2f6 | 10.38 | ≥4.5 text | pass |
| note-fg #4a3b00 on #fff8e1 | 10.31 | ≥4.5 text | pass |
| header-code-fg #fff on #2a4d73 | 8.72 | ≥4.5 text | pass |
| warn-fg #8a2b2b on #fdecea | 7.46 | ≥4.5 text | pass |
| ok-fg #1b5e20 on #e8f5e9 | 7.00 | ≥4.5 text | pass |
| muted-fg #5a6b7b on #fff | 5.49 | ≥4.5 text | pass |
| sea-flood-fg #f5edda on #1a63a8 | 5.31 | ≥4.5 text | pass |
| accent-fg-on-accent #fff on #1e6fb8 | 5.22 | ≥4.5 text | pass |
| chart-accent-fg #fff on #e74c3c | 3.82 | ≥3.0 data | pass |
| chart-bar-fg #fff on #4d94c9 | 3.28 | ≥3.0 data | pass |

(key: `report/คลองเจ้าพระยา2_วิชาการ.html:5-19` — `--c-header: #14212e` etc.)

All pass — the fixed palettes are clean. The remaining debt is procedural: `docs/REPORT_CONVENTIONS.md` mandates computing every pair when CSS changes ("ตรวจทุกคู่สีเมื่อแก้ CSS/กราฟ"), and no `tests/` file enforces it (grep for "contrast" hits only the docs). Given that the previous review's F-19 caught exactly one borderline palette token and it was fixed, the enforcement the repo already built elsewhere (FORBIDDEN ledger, mirror tests) suggests a contrast test fits one file. This is the same "manual rule with automatic neighbors" pattern the repo has systematically eliminated elsewhere.

---

## 4. Verified Invariants (things that held under re-derivation)

1. **Determinism repo-wide.** Re-running `analysis/hydraulic_1d_routing.py`, `analysis/goal6_l3_coastal_model.py`, `analysis/goal7_counterfactual_simulation.py`, `analysis/goal2_khundan_22y_baseline.py`, `analysis/goal6_pasak_24y_baseline.py`, `analysis/goal6_national_medium_reservoirs.py` changed nothing (git status only flagged the unrelated untracked `REVIEW.space-bunny-free.md`).
2. **Integrity harness.** `python tools/verify_all.py` → 4/4 (catalog check OK, SHA-256 MISMATCH=0, thai lint OK, pytest OK) at session start; `python catalog.py check` → 97/97 OK. Its pytest component showed 128 pass / 1 fail *after* an unrelated untracked file appeared mid-session (see §6).
3. **Canonical mirror equality.** `tests/test_goal6_consistency.py` green: `routing_1d`/`khundan_22y`/`medium_dams`/`l3_coastal_coupled` mirrors equal artifacts byte-wise; builder literal ban self-enforces (`test_goal6_consistency.py:102`).
4. **L3 purge/split correctness.** `leak_flags`/`train_mask` math verified by reading derivation (`goal6_l3_coastal_model.py:184,192`); chronological test split honest; all emitted numbers match HANDOFF's citations exactly.
5. **Compound risk constitution.** Two-point surrogate reproduces both docstring checkpoints by hand (2.51/3.04); additive form + tie-break set disclosed in limitations (`compound_flood_risk.py:43-46,134`); canonical tide/peak pair matches estuary artifacts.
6. **Counterfactual arithmetic.** 4,394.5/11,325.1 = 38.8% recomputed ✓; 582.9/1100 = 0.5298 ≈ 0.53 ✓; 215.8 MCM for 2569 ✓; synthetic inputs marked in artifact + canonical + (partially) HANDOFF.
7. **Khundan 22y aggregates.** Full-capacity years 9/22 (40.9% — matches `HANDOFF.md:76`); median-doy basis math matches artifact's output ("เดือนกันยายน 2 ครั้งใน 22 ปี" note ✓); the 2026 anomaly's own figure is 36.5 วัน (`goal2_khundan_22y_summary.json`) — the finding is only against HANDOFF's rendering of it (F-17).
8. **Pasak 24y definition block.** Three storage tiers separated properly, "ไม่ใช่การล้นข้ามสันเขื่อน" honesty line present; definitions live at `pasak_24y_summary.json::metadata.storage_definitions` — the 2554-over-normal/additive-channel distinction holds.
9. **Medium-reservoir data hygiene.** `qdisc` semantics verified = current storage (spot-sampled ~50 rows: `qdisc ≈ cap_resv·percent_rsv/100`); 22 missing-feature rows excluded from denominators, not zero-filled — the correct move, keeping the stress index honest.
10. **Retired-value guard is no longer vacuous** (head commit fix verified): the `FORBIDDEN` list at `build_canonical_numbers.py:147` is consumed by absence checks, with a documented context-allowance table at `:155-160`. The two-round regression that F-01 embodies is precisely the shape of value this guard was built to catch — the Ny.1B peak stage has simply not been routed through it yet.
11. **Thai-language lint enforced repo-wide.** `tools/verify_all.py` includes the lint stage and it passed (4/4 at session start); the linguistic rules (คำซ้อน/คำกลืน, ห้ามคำทับศัพท์) are being followed in the new baseline modules I read.
12. **Review-prompt hygiene inside the repo.** `docs/REVIEW_PROMPT_EN.md:18,63` now states exactly what artifacts establish and delegitimizes the unsupported claims ("No basin-wide (43 km) lag and no wave celerity are computed anywhere in the repository — any such figure is unsupported and should be rejected on sight"); the stale "1.62 m/s / 7.37 h" numbers are absent from this file (verified by grep).

---

## 5. Information Gaps & Unresolved Lookups

These are items I could not resolve *from within the repo* within read-only constraints; they are not findings, and they need human/FOI follow-up:

1. **C.12 official threshold level** — no `critical_level` for station C.12 in the `data/02_thaiwater/raw/` extracts; the 2.00/2.40/2.70 thresholds used by the compound-risk artifact are in-repo definitions. Needs a station-metadata fetch (or official statement) to compare.
2. **2554 Pasak mass-balance cross-check** — in-repo data does not cover 2011 (thaiwater `dam_yearly` series starts 2013). A genuine inflow-vs-storage+outflow audit of the CP2 counterfactual's driving year needs RID/historical records (FOI class; already flagged in START_HERE §8).
3. **Provenance of 11.23 ม.รทก.** — either the survey-extraction source (a specific manual reading of a station table) is documented nowhere I searched, or it is a legacy model output. Needs an explicit ledger decision (see F-01).
4. **Source of the 2,600 cms "safe passage at Ayutthaya"** — a named official gate value would let `safe_capacity_ayutthaya` gradate from "assumed" to "cited".
5. **What "17/22" means in `analysis/goal6/canonical.json:1560`** — the narrative string at that line references URC counts (16/22 · 20/22) but not the meaning of its own "17/22"; should be annotated or deleted to rule-6 form.
6. **Medium-reservoir vintage communication** — whether the 2024-10-15 snapshot date is communicated in any in-repo produced *reader-facing* channel (I found no statement in the report MD/HANDOFF; START_HERE may mention the vintage in the data-collection section).
7. **`mask_lowland_*` geo artifacts** — the binary masks under `data/22_goal6_network/derived/` are not bound by any script to the floodplain-lag narrative in `HANDOFF.md:39`; whether a floodplain-lag script should exist (and what it needs) is a maintainer call left open here (see F-04).

---

## 6. Test-Registration Impact of This Report (meta-compliance)

Per the project's "all top-level docs must be registered" rule (no allowlist; `tests/test_standards_integrity.py:64-75`, implemented via `catalog.unregistered_docs()` scanning `DOC_SURFACES = ("*.md", "docs/*.md")` at `catalog.py:381`):

- Placing this file at root **will itself trip** `test_all_top_level_docs_are_registered` — the same deterministic behavior caused by the unrelated `REVIEW.space-bunny-free.md` (634 lines, untracked, not deletable by me under read-only scope).
- **Session pytest state I observed: 128 passed / 1 failed** — the failure being exactly that registration test, caused solely by the foreign file. After this file lands, the same call will report **2 failed** until the user registers one or both reports.
- Recommended resolution, mirroring `catalog.py:179-180` precedent:
  ```python
  ("REVIEW.space-bunny-free.md", "ผลการตรวจสอบอิสระ (space-bunny-free) — รายงานตรวจสอบอิสระจากโมเดลภายนอกที่ผู้ใช้เก็บไว้เป็นหลักฐานของกระบวนการรีวิว"),
  ("REVIEW.GLM-5.3-flash-free.md", "ผลการตรวจสอบอิสระ (GLM-5.3-Flash Free) — รายงานเรื่อง 6 มิติ: 1D routing, L3 coastal, compound risk, CP2 counterfactual, baselines, canonical discipline"),
  ```
  Alternatively, move both to `docs/reviews/` and register there (precedent: `docs/reviews/AUDIT_ROUND2_2026-10-17.md` is registered at `catalog.py:177`).

---

## 7. Review-Prompt vs In-Repo Truth (external drift note, not a repo finding)

Two claims circulating in the *external* audit-prompt materials I received are inconsistent with the in-repo data as of the head commit:

| Prompt claim | In-repo truth | Evidence |
|---|---|---|
| "Ridge regression, +6h RMSE 0.17 m" | `LinearRegression` (not Ridge); +6h event RMSE = 30.03 cm (0.30 m); persistence 30.65 cm. "0.17 m" does not appear in any artifact (grep = 0) | `analysis/goal4_model_v1.py:8`, `analysis/canonical_numbers.json::model_v1`, goal4_model_multistation.json (leave-one-season-out folds) |
| framing of the counterfactual pair as "not calibrated" | accurate to the artifact's own disclosure; no conflict | `compound_flood_risk.py:38-46` |

This is consistent with the earlier drift pattern fixed inside the repo (`docs/REVIEW_PROMPT_EN.md` no longer carries the retired 1.62 m/s / 7.37 h claims, verified by grep at lines 18, 63 of the current file). Recommend updating any external prompt workouts that still cite "Ridge / 0.17 m" so future auditors don't waste cycles chasing nonexistent artifacts (this one cost me half an exploratory round at audit start).

---

*End of report. Audited files untouched; only this report file was created, at the project root, following the `REVIEW.*.md` naming precedent. Regeneration of every artifact whose SHA-256 the integrity pipeline tracks matched the recorded hashes (MISMATCH = 0 via `tools/verify_all.py`).*
