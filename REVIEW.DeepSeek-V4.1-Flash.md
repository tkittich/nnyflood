# Hydrological Audit & Red-Team Report: nnyflood

**Auditor:** DeepSeek-V4.1-Flash (independent review, read-only)
**Date:** 2026-10-17
**Commit reviewed:** `43b38d9` — "audit: remediate Round 2 delta review findings (N-01 to N-04, F-04, F-06, F-07, F-13, F-15) and enforce canonical mirror invariants"
**Interpreter used:** `python3.14` (CPython 3.14.x) with the pinned stack `numpy 2.5.1 / scikit-learn 1.9.1` per `requirements.txt`
**Method:** every claim below was re-derived by executing the project's own code, re-reading its own inputs, or recomputing from the raw telemetry. No finding rests on reading a docstring alone.
**Revision 2 (2026-10-17, 15:20):** triaged against `REVIEW.gemini_3.8_flash.md` — full verdict table in §7. Two findings added (F-21, F-22), two materially strengthened (F-10, F-17), and one claim in that review rejected as stale. Total: **22 findings**.
**Revision 3 (2026-10-17):** remediation round — §8 records what was fixed in code, what was disclosed rather than changed, what remains open, and one new finding (**F-23**, documentation drift) that the fixes themselves exposed.
**Revision 4 (2026-10-17):** the three items left open in Revision 3 are closed — F-18 (metric literals now rendered from canonical, with a regression test), F-15 (the three "bankfull" numbers reconciled), F-04 (the invalid Q-based travel time removed). See §8.3.
**Revision 5 (2026-10-17):** three structural fixes so the F-18 / N-01 / N-04 failure *mechanisms* stop recurring — a two-way token contract, a reverse catalog check, and named (non-positional) counterfactual records. No reported number changed; both report HTMLs rebuild byte-identical. See §8.6.

---

## 1. Executive Summary

**Overall Scientific & Engineering Reliability: Medium.**

The evidence discipline of this repository is genuinely unusual and it works: the canonical-mirror invariant that was broken in the previous round is now fixed and enforced, all 124 tests pass, and the two prior "duplicated source of truth" regressions are gone. What remains is not bookkeeping. It is **hydraulics and model provenance**: three of the four physical models publish headline numbers whose sign or magnitude is set by an assumption the code does not test, and one model's training-set description is contradicted by its own loader.

**Key system strengths (validated, not assumed)**

1. **Canonical ledgers now mirror their artifacts exactly.** I diffed `values.routing_1d` against `analysis/hydraulic_1d_routing_summary.json` field-by-field (zero diffs), and confirmed `goal6/canonical.json → l3_coastal_coupled` and `goal7/canonical.json → counterfactual_simulation` are byte-equal to their source JSONs. The N-01 class of regression is closed.
2. **The telemetry-derived headline survives independent recomputation.** `65 h above 8.45 m gauge` re-derived from `st62.csv` gives **64.75 h** (2026-09-26 22:45 → 09-29 15:15). The Pasak 2011 block now reads 94 days / 84.78 MCM·d⁻¹ from the record instead of the old hand-typed 86 / 87.21.
3. **The reports do not overclaim the levee.** `build_expert_report.py:337` correctly states that peak 7.64 m MSL is **0.57 m below** the surveyed crest 8.213 and that flooding came from the low terrace (6.94–8.07), not overtopping. That is the right call and it is rarer than it should be.

**Critical vulnerabilities requiring mitigation**

1. **The 1D routing's rating curve is non-monotonic, and its "bankfull discharge" is a local maximum of that curve** (F-01). Conveyance at Ny.1B *falls* from 666.3 to 517.7 m³/s as stage rises 10.60 → 10.84 m, because a single composite hydraulic radius is used across a compound section. The published `overflow_q_cms = 9.0` is the difference between two incompatible curves.
2. **The coastal-ML model is described as trained on "2020–2026 wet seasons" and is in fact trained on 47 days of 2026** (F-05). `n_train = 1130 h`. This is stated in `goal6/canonical.json → definitions.l3_test_window` and rendered verbatim into Report 3.
3. **The CP2 counterfactual's headline stage benefit is `ΔQ / 1100` where the comment one line above says the denominator should be 375** (F-12), and its 2011 inflow is a synthetic half-sine, so "4,394.5 MCM diverted" is a property of the assumed hydrograph shape, not of the 2011 flood.
4. **The compound-risk figure and its own JSON place the 2026 event in different risk bands** (F-21): the shipped PNG draws it at 2.57 m (`warning`), the JSON says 2.36 m (`watch`). A half-applied fix from the previous round — the table was corrected, the plot marker was not, and both files were then rewritten in the same run from two different constants.

---

## 2. Findings Matrix

| Finding ID | Severity | Component / Target File | Root Cause Summary | Recommended Action |
|---|---|---|---|---|
| F-01 | **Critical** | `analysis/hydraulic_1d_routing.py:45-88, 156-162, 240` | Composite single-`R` conveyance across a compound section → rating curve is non-monotonic; `bankfull_q 666.3` is a local max; `overflow_q 9.0` is a difference of two incompatible curves | Divide conveyance per sub-section (or use `Q = Σ (1/n) Aᵢ Rᵢ^⅔ S^½`); recompute bankfull at the terrace level; delete `overflow_q_cms` until fixed |
| F-02 | High | `analysis/hydraulic_1d_routing.py:199-201` | `np.interp` inverts a **non-monotonic** `q_lookup` (7 folds, min Δ = −23.96 m³/s) | Build a strictly monotonic inverse by taking `max(Q)` per stage; assert `np.all(np.diff(q_lookup)>0)` |
| F-03 | High | `analysis/hydraulic_1d_routing.py:105-141` | Scheme not grid-convergent: RMSE **worsens** monotonically as `n_sub` 1→96 (126.1 → 131.8 cm) while peak climbs 578.7 → 649.1 | Report a convergence table; do not publish a single `n_sub=12` result as physical |
| F-04 | High | `HANDOFF.md:39`; `analysis/hydraulic_1d_routing.py:209-218` | `7.37 ± 0.8 h` / `1.62 m/s` produced by no script; the two "observed" travel times derive from Q and H series whose peaks are offset in **opposite** directions (+6.5 h, −8.75 h) | Either compute a lag histogram or delete the sentence; compute travel time from stage only |
| F-05 | High | `analysis/goal6_l3_coastal_model.py:113`; `analysis/goal6/canonical.json → definitions.l3_test_window`; `report/goal6_build_report3_draft.py:353` | Training window claim ("2020–2026") contradicts loader (`start_dt = 2026-07-01`); `n_train = 1130 h` | Change definition + rendered sentence to "ฝึก 47 วัน (1 ก.ค.–19 ก.ย. 2569)" |
| F-06 | High | `analysis/goal6/l3_coastal_summary.json` (`test_window`) | 178 h (37 %) of the stated 20 Sep–9 Oct window has **no target data**; usable 274/480 = 57.1 % | State effective test end (2 Oct 14:00) and coverage fraction |
| F-07 | Medium | `analysis/goal6_l3_coastal_model.py:128,181` | No purge/embargo: last training target falls up to `lead_h` hours inside the test window | Drop training rows with `t_lead >= test_start` |
| F-08 | Medium | `analysis/goal6/l3_coastal_summary.json` horizons 6/24/48 | 50.5 % headline measured against a baseline (72.7 cm) that is **worse than persistence** (61.8 cm); at +24 h the coastal model is 0.4 cm worse | Re-headline against persistence: 36.0 vs 61.8 = 41.7 %; disclose the −1.7 % at +24 h |
| F-09 | Medium | `analysis/goal6_l3_coastal_model.py:102-108` | SWAN feature = mean of 31 stations at **one post-event timestamp** (2026-10-16 19:00) → zero variance + look-ahead | Either ingest a real hourly series or drop the feature and say so |
| F-10 | High | `analysis/compound_flood_risk.py:36-40` | `c1 = 0.132` has no calibration artifact; docstring claims calibration on 2011/2021/2022/2026 telemetry that does not exist in the repo; exponent 1.28 is not derivable from any rating | Remove the provenance claim or add `analysis/compound_flood_risk_calibration.py` + artifact |
| F-11 | Medium | `analysis/goal7_counterfactual_simulation.py:150,159` | `share_of_excess_flood_pct = MCM / 11000` — hardcoded round denominator; model's own excess is 11,325.1 MCM → **38.8 %**, not 40.0 % | Divide by the computed excess; assert equality with the summary |
| F-12 | **Critical** | `analysis/goal7_counterfactual_simulation.py:74-77` | Comment says `B·v ≈ 375`; code divides by **1100**. Published 0.53 m depends entirely on the undocumented 1100 (at 375 it would be 1.55 m) | Resolve the discrepancy, cite the source of the rating slope, and re-derive |
| F-13 | High | `analysis/goal7_counterfactual_simulation.py:102-105, 111` | 2011 inflow is `2200 + 2486·sin(t)^1.3 + N(0,45)`; "102 of 122 days above safe capacity" and 4,394.5 MCM are properties of the assumed shape | Label every derived number "synthetic hydrograph"; or drive it from observed 2011 daily flows |
| F-14 | Medium | `analysis/goal7_counterfactual_simulation.py:108,126` | Tidal efficiency floored at 0.84 (2011) / 0.90 (2026); never 0. No lockout, no outlet backwater — contradicts `goal7_build_public.py:576` ("น้ำในคลองจะนิ่ง" at peak tide) | Add a gate-closure rule (`H_gulf > H_canal → eff = 0`) and report the volume lost |
| F-15 | Medium | `analysis/hydraulic_1d_routing.py:160-162` vs `docs/DATA_DICTIONARY.md:83,101` | Three numbers named "Ny.7 bankfull capacity": **420–425** (empirical rating), **487** (Manning @ 6.86), **617.4** (Manning @ 8.213) | Rename routing key to `levee_crest_capacity_q_cms`; state definition in the legend |
| F-16 | Medium | `analysis/goal6_national_medium_reservoirs.py:68-70, 111-113` | 22 of 461 dams have no data; `percent_rsv` defaults to 0 → classified **"below 80 %"** | Exclude nulls from the denominator and from `below_80_count` |
| F-17 | Medium | `analysis/build_canonical_numbers.py:125-134` | `ny1b_cross_section` still emits `peak_q 282.4` / `peak_stage 11.23` vs telemetry **675.3 / 11.00**; the added note covers only `bankfull_q` | Extend the note to the peak fields, or split the block into `historical_table_*` |
| F-18 | Low | `report/build_expert_report.py` | Metric literals remain: `9.23`×9, `306.9`×5, `7.64`×4, `11.89`, `65`×13 — violates AGENTS.md rule (2) for Reports 1–2 | Render from `canonical_numbers.json` |
| F-19 | Low | `report/build_expert_report.py:57`, `report/build_report_html.py:69` | `--c-sea-flood-fg #f5edda` on `#1d6fb8` = **4.48:1** (below 4.5 for text). Declared but never applied as `color:` — latent | Darken to ≥4.5 or document as graphics-only |
| F-20 | Low | `analysis/compound_flood_risk.py:94-99` | 2026 row predicts 2.36 vs observed 2.24 (+12 cm) and calls it "สอดคล้อง" | Say "+12 cm (+5 %), same band" instead of "consistent" |
| F-21 | **High** | `analysis/compound_flood_risk.py:160` vs `:96` | **Figure and table disagree on the same event.** PNG plots 2026 at tide 2.12 → 2.57 m (`warning`); JSON says tide 1.91 → 2.36 m (`watch`) | Set the marker to 1.91 from canonical, regenerate, and add a test that every marker equals its JSON row |
| F-22 | Low | `analysis/hydraulic_1d_routing.py:148, 152` | `Kgt.30` cross-section and `slope_reach3` are loaded/declared and **never used**; no downstream boundary condition exists despite the docstring claiming one | Delete the dead load, or implement stage-controlled downstream routing |

---

## 3. Deep-Dive Technical Findings

### [F-01] Critical — The Ny.1B rating curve is non-monotonic, so "bankfull 666.3 m³/s" is a local maximum, not a capacity

- **Location:** `analysis/hydraulic_1d_routing.py:45-88` (`compute_hydraulic_geometry`), `:87` (`radius = area/perimeter`), `:156-162`, `:240` (`overflow_q_cms`)
- **Empirical Evidence.** Executing the module's own functions on the surveyed section:

```
== Ny.1B zmin 2.23 zmax 10.84
  H= 10.00 A=  413.4 P=  95.9 R=4.31 B= 93.2 Q=  638.7
  H= 10.60 A=  471.8 P= 125.3 R=3.77 B=121.9 Q=  666.3   <- reported "bankfull"
  H= 10.84 A=  511.3 P= 223.6 R=2.29 B=220.0 Q=  517.7   <- conveyance FALLS 22 %
  H= 11.00 A=  546.5 P= 223.6 R=2.44 B=220.0 Q=  578.4
```

`zmax = 10.836`, so at the observed peak (11.00 m) the water is above the entire surveyed section, yet the model returns a **lower** discharge than at 10.60 m. The jump in wetted perimeter (125.3 → 223.6 m) when water crosses the left bank collapses `R = A/P` faster than `A` grows.

- **Hydraulic Critique.** This is the classic compound-section error: summing area and wetted perimeter across a main channel plus a shallow floodplain and using one `R` is only valid if the two sub-sections have the same roughness *and* the same velocity. They do not. The correct form is a divided-channel conveyance,

  `Q = Σᵢ (1/nᵢ) Aᵢ Rᵢ^(2/3) S^(1/2)`,

  which is monotonically increasing in stage by construction. Consequences that propagate into the reports:

  - `bankfull_q_cms = 666.3` is the **maximum of a non-monotonic curve**, i.e. the stage of maximum conveyance, not the stage at which the section stops carrying water.
  - `overflow_q_cms = 9.0` is `675.3 (telemetry) − 666.3 (model)` — a difference between a gauge-derived discharge and a Manning discharge from a different curve. At the *same* observed stage of 11.00 m, the model's own rating gives 578.4, i.e. **below** "capacity". The 9.0 m³/s overflow figure is not physically derived and should not be published.
  - The pair (`overflow_depth 0.40 m`, `overflow_q 9.0 m³/s`) implies a marginal conveyance of 22.5 m²/s per metre of rise in a 122-m-wide section, which is off by an order of magnitude.

- **Proposed Solution.** Replace `compute_hydraulic_geometry` + `stage_to_discharge` with a divided-conveyance routine that splits at the surveyed bank break (offset ≈ 0 for Ny.1B, where `z` jumps to 8.213), computes `A`, `P`, `R` per sub-section, and sums `Q`. Add a positive-control test:

```python
def test_rating_is_monotonic():
    stages = np.linspace(z.min()+0.2, z.max()+1.0, 300)
    q = [stage_to_discharge(compute_hydraulic_geometry(x, z, s), n, S) for s in stages]
    assert np.all(np.diff(q) > 0), "rating curve folded — compound section not split"
```

Then delete `overflow_q_cms` and `overflow_depth_m` from the summary, or recompute them from the terrace-onset level.

### [F-02] High — The inverse rating at Ny.7 is ill-posed; `np.interp` is fed a non-monotonic `xp`

- **Location:** `analysis/hydraulic_1d_routing.py:199-201`
- **Empirical Evidence.** Same geometry function, Ny.7:

```
non-monotonic at h = [-0.03  3.99  4.43  6.94  7.01  8.39  8.45]
corresponding Q:    [  6.7  158.7 181.2 499.1 495.8 665.7 641.7] -> [... 6.5 158.6 180.4 495.8 493.7 641.7 624.5]
q_lookup strictly increasing: False   min diff -23.964628629431445
```

`np.interp(q_sim, q_lookup, h_test_levels)` assumes `xp` is increasing. It is not, in seven places.

- **Critique, with the impact measured rather than assumed.** I counted how many simulated timesteps actually land inside a fold:

```
sim Q range 47.8..613.0
Q in ambiguous branch: 495.8 - 496.6
timesteps in ambiguous band: 7 of 576
interp at Q=495 -> 6.915   (forward h=6.94 -> Q 499.4)
interp at Q=640 -> 8.296   (forward h=8.43 -> Q 649.6)
```

So the bug is real but its effect on the published `rmse_stage_cm = 105.8` is small: 7 of 576 samples, ~0.1 m each. I am reporting it as High not because the number is wrong today but because the inverse is undefined: the same simulated discharge has two valid stages, and which one `np.interp` returns depends on array layout. The next change to `n_sub`, `b_avg`, or the stage grid can flip it. It should be fixed before the routing is reused.

- **Proposed Solution.** Build the inverse on the monotone envelope:

```python
order = np.argsort(hl)
q_env = np.maximum.accumulate(ql[order])
assert np.all(np.diff(q_env) >= 0)
h_sim = np.interp(q_sim, q_env, hl[order])
```

### [F-03] High — The routing is not grid-convergent, and the published numbers are resolution artifacts

- **Location:** `analysis/hydraulic_1d_routing.py:105-141`
- **Empirical Evidence.** Re-running the module's own `run_muskingum_cunge_reach` across sub-reach counts:

| `n_sub` | `travel_time` (h) | `q_peak` (m³/s) | `rmse_q` (m³/s) | `rmse_h` (cm) |
|---|---|---|---|---|
| 1 | 2.00 | 578.7 | 126.1 | 106.9 |
| 3 | 3.25 | 560.9 | 124.2 | 102.7 |
| 6 | 3.25 | 591.7 | 126.4 | 103.6 |
| **12 (published)** | **3.25** | **613.0** | **128.8** | **105.8** |
| 24 | 3.25 | 627.5 | 130.2 | 107.2 |
| 48 | 3.25 | 638.9 | 131.1 | 107.9 |
| 96 | 3.25 | 649.1 | 131.8 | 108.5 |

- **Critique.** A convergent scheme improves (or stabilises) as `Δx → 0`. Here error **increases monotonically** with refinement, and the simulated peak keeps climbing toward the observed 648.3 by coincidence, not by calibration. That is the signature of numerical diffusion doing the work that physical dispersion should do: at `n_sub = 1` the single reservoir smears the wave enough to accidentally fit better. The docstring at `:109-110` justifies `n_sub = 12` by a Courant criterion, but the Courant number at peak flow is ≈ 1.8 (`dx_sub = 1525 m`, `c ≈ 3.05 m/s`, `dt = 900 s`), which is exactly where the scheme is *not* stable; `x_param` is then clamped from −4.49 to 0.0 at `:129`, silently deleting the diffusive term entirely and reducing the model to a cascade of linear reservoirs. So the "Muskingum-Cunge" label overstates what is being solved.

- **Proposed Solution.** Report the table above in `docs/METHODS.md`, state that `n_sub = 12` is chosen for best fit rather than convergence, and either (a) move to an implicit Preissmann/θ-scheme with a proper Courant limit, or (b) rename the method to "cascade of linear reservoirs (Muskingum K, X→0)" and drop the Cunge attribution. Also add the missing physics: lateral inflow between Ny.1B and Ny.7 and a floodplain storage area — without them a 105.8 cm RMSE against a ~0.8 m event range is expected, not fixable by tuning.

### [F-04] High — The `7.37 ± 0.8 h` / `1.62 m/s` headline is produced by nothing, and the two observed travel times are mutually inconsistent

- **Location:** `HANDOFF.md:39`; `analysis/hydraulic_1d_routing.py:209-218`
- **Empirical Evidence.**
  1. `grep -rln "7\.37"` across `analysis/*.py` returns **no script** that computes it; the only hits are data CSVs, `goal7/canonical.json` (an unrelated `0.53` entry at line 5370), and the review prompts themselves (`docs/REVIEW_PROMPT_EN.md:18,63`). `1.62 m/s` likewise appears only as a *Mae Klong water level* at `analysis/goal6_downstream_tide.py:161`. The celerity is the quotient `43 km / 7.37 h` — circular.
  2. The two "observed" travel times rest on series whose own peaks disagree:

| Station | Q peak | H peak | Offset |
|---|---|---|---|
| Ny.1B (`st61.csv`) | 2026-09-26 18:30 (675.3) | 2026-09-27 01:00 (11.00) | **+6.5 h** |
| Ny.7 (`st62.csv`) | 2026-09-27 18:45 (648.3) | 2026-09-27 10:00 (7.68) | **−8.75 h** |

  A rating-derived discharge cannot peak 8.75 h *before* its own stage at one station while peaking 6.5 h *after* it at another. So `travel_time_hours_obs = 24.25 h` and `travel_time_stage_obs = 9.0 h` are differences between two series that are internally inconsistent in opposite directions — neither is a wave travel time.
  3. The same inconsistency is visible in the rating itself: at the observed peak stage 7.68 m, the project's rating gives **548.5 m³/s**, while telemetry reports **648.3** — an 18 % gap at a single station at a single instant.

- **Proposed Solution.** Delete the `7.37 ± 0.8 h` / `1.62 m/s` sentence from `HANDOFF.md:39` and `docs/REVIEW_PROMPT_EN.md` until a script produces it. Compute travel time from **stage only** at both stations via cross-correlation, report the intra-station Q–H offset as a data-quality metric, and mark Ny.1B/Ny.7 `q_cms` as *derived* rather than gauged until the source is confirmed.

### [F-05] High — The coastal model is described as trained on 2020–2026 and is trained on 47 days of 2026

- **Location:** `analysis/goal6_l3_coastal_model.py:113`; `analysis/goal6/canonical.json → definitions.l3_test_window`; `report/goal6_build_report3_draft.py:353`
- **Empirical Evidence.**
  - Code: `start_dt = dt.datetime(2026, 7, 1, 0, 0)`; all inputs are `*_2026_hourly.json`.
  - Artifact: `n_train = 1130` (+6 h), `1467` (+24 h), `1462` (+48 h) — i.e. 47–61 days.
  - Canonical definition: `"ฝึก = ฤดูฝน 2020–2026 ก่อน 20 ก.ย."`
  - Rendered sentence: `f"ฝึก {l3['train_hours']:,} ชม. (2020–2026 ฤดูฝน)"`
- **Critique.** The rendered sentence is self-refuting: 1,130 hours is 47 days, not six wet seasons. A reader who checks the number against the parenthesis sees the contradiction immediately. This matters more than a typo because the model's claimed generality ("trained on six years, tested on one event") is the main reason a reader would trust its +6 h RMSE.
- **Proposed Solution.** Change both the canonical definition and the f-string to `"ฝึก 47 วัน (1 ก.ค.–19 ก.ย. 2569)"`, and add a test that `train_hours / 24 < 90` implies the text must not contain "2020".

### [F-06] High — 37 % of the declared test window has no target data

- **Location:** `analysis/goal6/l3_coastal_summary.json → metadata.test_window`
- **Empirical Evidence.** Joining the three input series over 2026-09-20 → 2026-10-09:

```
test window 480 h, usable 274 h (57.1 %)
missing blocks: 2026-10-02 14:00 -> 2026-10-09 23:00  (178 h)
                plus 12 isolated 00:00 holes and 2026-09-27 22:00->09-28 05:00 (8 h)
C.12 peak in window: 2.24 m at 2026-09-27 19:00  (covered — good)
```

- **Critique.** The test period ends in practice on **2 Oct 14:00**, not 9 Oct. The RMSE is computed on 57 % of the advertised window. Two mitigating facts I verified rather than assumed: the event peak *is* inside the covered portion, so the metric is not peak-blind; and the recurring 00:00 holes are a systematic property of the source pages, not random loss. But `metadata.test_window` and the report caption still assert a 20-day window. The isolated midnight holes also interact with the lag features: `h1 = target_data.get(all_hours[i-1], h0)` silently substitutes `h0`, so `h0 - h1` is forced to exactly 0 for every sample whose previous hour is missing.
- **Proposed Solution.** Set `test_window` from the data (`min/max` of `test_flags`), add `test_coverage_pct` to the summary, and have the report render it. For the lag features, drop rows with missing `t-1` rather than substituting `h0`.

### [F-07] Medium — No purge between train and test

- **Location:** `analysis/goal6_l3_coastal_model.py:128, 181`
- **Empirical Evidence.** `test_flags` is assigned from `t_curr >= test_start`, but the target is `t_lead = t_curr + lead_h`. The last training sample is `t_curr = 2026-09-19 23:00`, whose target is `2026-09-20 05:00` (+6 h) … `2026-09-21 23:00` (+48 h). Up to `lead_h` hours of test-window labels therefore sit in the training set.
- **Critique.** Small in magnitude (48 of 1,462 labels) but it is a protocol violation of exactly the kind the prompt asks about, and it is the one item from the previous round that survived. With an autoregressive `h0` feature and hourly sampling, adjacent samples are near-duplicates, so the boundary is the only place where leakage can enter — and it is open.
- **Proposed Solution.** `train_mask = (t_curr < test_start) & (t_lead < test_start)`.

### [F-08] Medium — The 50.5 % headline is measured against a baseline worse than doing nothing

- **Location:** `analysis/goal6/l3_coastal_summary.json`, horizon `6`
- **Empirical Evidence.**

| Horizon | Persistence | Linear base | Linear coastal | Coastal vs persistence |
|---|---|---|---|---|
| +6 h | 61.8 | **72.7** | 36.0 | −41.7 % |
| +24 h | 21.2 | 20.1 | 20.5 | −3.3 % |
| +48 h | 37.6 | 34.5 | 33.5 | +10.9 % |

- **Critique.** At +6 h the uncoupled linear model is **17 % worse than persistence**, so `(72.7 − 36.0)/72.7 = 50.5 %` measures the coastal features against a mis-specified baseline. Against persistence the honest improvement is 41.7 %. And the coastal coupling is not a general win: at +24 h it is 0.4 cm *worse* than the uncoupled model (`−1.7 %`), and at +48 h it adds 2.7 %. The defensible claim is "coastal boundary conditions cut +6 h error by 42 % relative to persistence; at 24–48 h the benefit is within noise." The current framing implies a uniform halving.
- **Proposed Solution.** Headline `linear_coastal` vs `persistence` (a skill score, as `canonical.json → l3_best` already does with `skill_vs_persistence`), and render the negative +24 h number in the report rather than only the +6 h one.

### [F-09] Medium — The "wave coupling" feature is one post-event scalar

- **Location:** `analysis/goal6_l3_coastal_model.py:102-108`
- **Empirical Evidence.** `data/25_gulf_marine_tides/raw/gulf_wave_summary.json` is a list of 31 stations, each with a single `latest_datetime` of `2026-10-16T19:00:00+07:00` and one `wave_height_sig_m`. `np.mean(waves)` ≈ 0.0968 m, appended identically to every row from 1 Jul to 9 Oct.

```
swan n 31  mean 0.0968 m  timestamps {'2026-10-16'}
```

- **Critique.** Two defects in one line. (a) Zero variance: a constant column is absorbed into the intercept by `LinearRegression` and ignored by `HistGradientBoostingRegressor`, so the feature cannot contribute — the "coastal wave coupling" is nominal. (b) The timestamp is **after** the test window, so the value is a future observation used as a covariate. The leakage is harmless *only because* the feature is dead; fixing (a) without fixing (b) would introduce real look-ahead.
- **Proposed Solution.** Either ingest an hourly Gulf series aligned to the event, or drop `swan_hs` from `feat_coastal` and remove "และคลื่นลมทะเลอ่าวไทย" from the model title and `definitions.l3_coastal_coupled`.

### [F-10] High — The compound-risk coefficient has no calibration behind it, and its exponent is steeper than any rating curve

- **Location:** `analysis/compound_flood_risk.py:36-40`
- **Empirical Evidence.** `c1 = 0.132` is a bare literal. `grep -rn "0\.132" analysis/*.py` returns only its own definition. There is no `compound_flood_risk_calibration.py`, no fitted artifact, and no intermediate output. The comment above it claims "ค่าสัมประสิทธิ์สอบเทียบจากอนุกรมเวลาโทรมาตรปี 2554, 2564, 2565, และ 2569" — four years of telemetry that the repository does not contain. The two calibration anchors in the comment are now numerically correct (`2.51`, `3.04`), but correct arithmetic is not calibration.

- **Hydraulic Critique.** `H = H_tide + Δh_wave + c₁(Q/1000)^1.28`. Manning normal depth in a wide channel gives `h ∝ Q^0.6`; a downstream-controlled tidal reach is *less* sensitive, not more. An exponent of 1.28 means the stage response to a doubling of discharge is `2^1.28 = 2.43`, against `2^0.60 = 1.52` for normal depth — 4.5× the physical sensitivity per unit `Q`. The exponent also has no dimensionally consistent interpretation: `c₁` carries units of metres only if the exponent is fixed, so `1.28` is a free shape parameter that was tuned to two points and then extrapolated to `Q = 4,250` and to the 2011 benchmark at `Q = 3,750`, 67 % beyond the top of the matrix range it was fitted on.

  **The tidal term is worse than the discharge term.** Because `H_tide` enters additively with coefficient 1, `∂H_C12/∂H_tide ≡ 1.0` at every `Q` and every stage: a 10 cm rise at the river mouth transmits 100 % undamped to Samsen, 40+ km inland, regardless of whether the river is at 1,500 or 4,000 m³/s. Real backwater is a function of both heads — the same 10 cm tide increment produces a different stage response at high flow than at low, because the tidal signal propagates against a different downstream velocity. The model has **no `Q × tide` interaction term at all**, so the matrix's entire value as a compound-risk tool — the claim that river flood and storm surge interact non-linearly — is not represented in the equation. Two independent drivers are added; that is superposition, not compounding. I stop short of asserting that the gain must be *below* 1: in the Chao Phraya the tidal range is known to amplify upstream through funneling, so the correct statement is that the gain is untested and assumed constant, not that it is over-stated.

- **Proposed Solution.** Fit `(H − H_tide − Δh)` against `Q` on the actual C.12/CPY015 hourly series with a free exponent, store the fit and its confidence interval in an artifact, and constrain the exponent to `[0.4, 0.8]` unless a physical argument for higher is written down. Until then, the 2011 row (`Q = 3,750`, `tide = 2.35` → 3.15 m) is an extrapolation, not a hindcast — and `q_bangsai = 3750` appears nowhere else in the repo, so the input itself is unsourced.

### [F-11] Medium — `share_of_excess_flood_pct` divides by a hardcoded 11,000, not by the model's own excess

- **Location:** `analysis/goal7_counterfactual_simulation.py:150,159`
- **Empirical Evidence.** `round(res_54_600["total_diverted_mcm"] / 11000.0 * 100.0, 1)` → 40.0 %. Reconstructing the model's own hydrograph:

```
peak 4727.4   mean 3638.4
total volume 38351.6 MCM
excess over 2600 MCM 11325.1
diverted 4394.5 as % of TOTAL volume: 11.5
diverted as % of EXCESS: 38.8
```

- **Critique.** The field name says "excess" and the denominator is a round constant that is neither the total (38,351.6) nor the computed excess (11,325.1). It happens to sit within 3 % of the excess, so the published 40.0 % is roughly right by luck. A metric labelled as a model output should be `diverted / Σ max(Q−2600, 0)`. The 1.2 pp gap is small; the fact that it is not derived is the finding.
- **Proposed Solution.** Compute `excess_mcm` inside `simulate_event` and divide by it; add `excess_mcm` to the summary so the reader can check the ratio.

### [F-12] Critical — The CP2 stage benefit divides by 1100 while its own comment says 375

- **Location:** `analysis/goal7_counterfactual_simulation.py:74-77`
- **Empirical Evidence.**

```python
# ประเมินระดับน้ำลดลงที่อยุธยา (สมการ Stage-Discharge: dh ≈ dQ / (B * v))
# ที่อยุธยา แม่น้ำกว้าง ~250 ม. v ~ 1.5 ม./วิ -> B*v ≈ 375 ม²/วิ -> ลดได้ ~dQ / 375
peak_stage_reduction_m = peak_q_reduction / 1100.0
```

- **Critique.** The comment derives `B·v ≈ 375 m²/s`; the code uses 1100, a factor of **2.93**. The published `0.53 m` at `ΔQ = 582.9` becomes `1.55 m` with the stated coefficient. This is not a rounding choice: it is the difference between "the canal lowers Ayutthaya by half a metre" and "by a metre and a half", and it is the single most consequential number in Pillar 3. The `# ปรับเทียบ rating curve ช่วงน้ำหลากทุ่ง` ("calibrated to the floodplain rating curve") note asserts a calibration that leaves no artifact — the same pattern as F-10.
- **Proposed Solution.** Replace the divisor with a real rating slope `dQ/dh` computed from the Ayutthaya cross-section at the event stage, cite the section and stage, and store `dq_dh_m2s` in the summary. If 1100 is retained, document where it came from and reconcile the comment.

### [F-13] High — The 2011 counterfactual is driven by a synthetic half-sine, so its volumes describe the assumption, not the flood

- **Location:** `analysis/goal7_counterfactual_simulation.py:102-105, 111`
- **Empirical Evidence.**

```python
inflow_2554 = 2200.0 + 2486.0 * (np.sin(t_54) ** 1.3)   # t = linspace(0, pi, 122)
inflow_2554 += np.random.normal(0, 45.0, n_days_54)     # seed 42
safe_cap_ayutthaya = 2600.0
```

- **Critique.** A single half-sine rising from 2,200 to 4,686 and back has no recession limb, no second pulse (the 2011 flood had several), and a mean of 3,638 m³/s that sits 40 % above the stated safe capacity for 102 of 122 days. Every downstream number — `4,394.5 MCM`, `19 days saved`, `40.0 %` — is an integral of that shape. To the project's credit, the *figure* legend says `น้ำหลากจำลองปี 2554` ("simulated 2011 inflow"); the problem is that the JSON fields and the prompt's headline sentence do not carry that qualifier. A reader sees "CP2 would have diverted 4,394.5 MCM" and reasonably infers a hindcast.
- **Proposed Solution.** Drive the 2011 case from the observed daily Chao Phraya + Pasak flows already in `data/23_rid_swoc/` if they exist; if they do not, rename every field to `*_synthetic_*` and add a `"hydrograph": "synthetic half-sine, seed 42"` key to `metadata`. Do not report `days_over_safe` as a finding from a shape assumption.

### [F-14] Medium — The canal has no tidal lockout, and the efficiency floor contradicts the report

- **Location:** `analysis/goal7_counterfactual_simulation.py:108,126`
- **Empirical Evidence.** `tide_eff_54 = 0.92 + 0.08·cos(…)` → range **0.84–1.00**; `tide_eff_69 = 0.90 + 0.10·cos(…)` → **0.80–1.00**. Capacity is never zero. Meanwhile `report/goal7_build_public.py:576` states, verbatim:

  > "ตอนผันน้ำน้อย (100 ลบ.ม./วินาที) น้ำปกติลึกเพียง … ม. เมื่อทะเลหนุนสูงสุด **น้ำในคลองจะนิ่ง**ที่ราว +2.5 ม.รทก."

  — at peak tide the canal surface goes **still**, i.e. the gradient is zero and diversion is zero.

- **Critique.** A 111-km canal discharging into the Gulf through control structures cannot divert while the sea surface is above the canal water level: the gates close and the flow is zero, not 84 %. The report already states the correct physics ("น้ำในคลองจะนิ่ง"); the simulation contradicts it. The two models disagree on the parameter that decides whether the canal works at all, and the omission is one-directional: it can only *increase* the diverted volume.
- **Proposed Solution.** Add an explicit gate rule — `eff = 0` when `H_gulf ≥ H_canal`, with the canal stage from a simple backwater — and report `volume_lost_to_lockout_mcm` alongside `total_diverted_mcm`. Reconcile with the 17 % figure in the report or change the report.

### [F-15] Medium — "Ny.7 bankfull capacity" carries three different numbers

- **Location:** `analysis/hydraulic_1d_routing.py:160-162` vs `docs/DATA_DICTIONARY.md:83,101` vs `START_HERE.md:165`
- **Empirical Evidence.** All three are internally sourced, which is what makes the collision worth fixing:

| Value | Definition | Source |
|---|---|---|
| **420–425 m³/s** | project empirical rating `242(h−4.55)^0.66` at h = 6.86 | `rid_cross_section_hydraulics.py:66`, `DATA_DICTIONARY.md:83` |
| **486.9 m³/s** | Manning at h = 6.86, n = 0.0437, S = 0.00035 | recomputed from the surveyed section |
| **617.4 m³/s** | Manning at h = 8.213 (left pier crest) | `hydraulic_1d_routing.py:162` |

- **Critique.** The routing figure's legend calls 617.4 "ความจุลำน้ำ Ny.7 ก่อนล้นตลิ่ง" ("channel capacity before overtopping"), while `START_HERE.md:165` calls 420–425 the bankfull discharge. A reader comparing the two documents sees a 47 % contradiction with no way to resolve it. This is precisely the failure mode AGENTS.md rule (6) was written to prevent ("ห้ามใช้ชื่อเดียวครอบหลายนิยาม"). The 8.213 value is a genuine surveyed point (offset 0.0, `Ny.7_profile.csv`), so the number is not invented — only the name is overloaded.
- **Proposed Solution.** Rename the routing key to `levee_crest_capacity_q_cms` and `levee_crest_msl_m`, add `terrace_onset_capacity_q_cms` computed at 6.86, and make the figure legend say which definition it plots.

### [F-16] Medium — 22 dams with no data are counted as "below 80 %"

- **Location:** `analysis/goal6_national_medium_reservoirs.py:68-70, 111-113`
- **Empirical Evidence.**

```python
pct = float(p.get("percent_rsv") or 0)      # missing -> 0.0
...
else:
    reg_stat["below_80_count"] += 1         # pct == 0 lands here
```

In `data/23_rid_swoc/raw/dams_medium_snapshot_461.json`: 461 features, **22 with `percent_rsv`, `cap_resv` and `qdisc` all null**. They are still counted in `reg_stat["count"]`, so they enter every regional denominator.

- **Critique.** Missing data is silently converted into the *safest possible* category. The published `dams_stress_total_pct = 57.92 %` is therefore diluted by 22 non-observations. Excluding them: `267 / 439 = 60.8 %` (+2.9 pp). The direction of the bias is conservative (it understates stress), which is the less dangerous direction, but it is still an unstated assumption inside a headline index. The same `or 0` pattern applies to `q_info`/`q_outfo`, which feed `total_inflow_mcm_day = 39.25`.
- **Proposed Solution.** `if not p.get("percent_rsv"): n_missing += 1; continue`, report `n_missing` and `n_assessed`, and compute percentages over `n_assessed`.

### [F-17] Medium — Ny.1B still carries two contradictory states

- **Location:** `analysis/build_canonical_numbers.py:125-134`
- **Empirical Evidence.** The block now carries a `historical_rating_note`, which is an improvement, but the fields it does not explain remain:

```
"bankfull_q_m3s": 244.6     (explained: historical RID table)
"peak_stage_msl": 11.23     (vs telemetry 11.00)
"peak_q_m3s": 282.4         (vs telemetry 675.3 — 2.4x)
```

and `checks["public"]` / `checks["expert"]` still require the strings `"244.6"` and `"10.60"` in the built HTML. The observed peak discharge in the same canonical file's `routing_1d.ny1b_hydraulics.peak_q_cms` is **675.3**.

**Additional evidence (from the Gemini cross-review, verified).** `data/23_rid_swoc/raw/rid_telemetry_cross_sections.json → stations.Ny.1B.station_info` declares:

```
braelevel = 8.8100004196167    <- RID's own bank elevation
QMax      = 266.8999938964844  <- station's declared maximum discharge
UseMSL    = 0                  <- station datum, not MSL
```

Two things follow. First, **RID's declared bank elevation (8.81 m) does not match the 10.60 m the routing model uses** — a 1.79 m gap that no document reconciles. Second, `QMax = 266.9` is consistent with `244.6` (both are sub-300) and **inconsistent with the observed event peak of 675.3**, which is 2.5× the station's declared maximum. That is independent corroboration of the `q_cms` provenance problem in F-04.

I checked the most attractive explanation — that 244.6 is simply Manning at the 8.81 m bank — and it does not hold:

```
H= 8.81 A=304.9 P=90.6 B=88.6 Q(n=.0437,S=.00065)= 399.5
n that gives 244.6 at 8.81  = 0.0714
n that gives 244.6 at 10.60 = 0.1190
```

So 244.6 is **not** a Manning value at any surveyed bank elevation with channel roughness; reproducing it needs `n = 0.0714` at 8.81 m or an absurd `n = 0.119` at 10.60 m. It is a station-table figure. The consequence is that "Ny.1B bankfull capacity" now has **four** candidate values — 244.6 (station table), 266.9 (declared `QMax`), 399.5 (Manning at RID's 8.81 m bank), 666.3 (Manning at the surveyed 10.60 m edge) — and the project publishes two of them as canonical.

- **Critique.** A reader who sees "Ny.1B bankfull 244.6 m³/s" next to "Ny.1B peak 675.3 m³/s" concludes the station ran at 2.8× capacity for the whole event. That may be the intended message, but it is produced by mixing a 1990s rating table with 2026 Manning geometry in one table without a column saying which is which. The note covers `bankfull_q` only.
- **Proposed Solution.** Split the block into `historical_rating_table: {bankfull_q: 244.6, qmax: 266.9, peak_q, peak_stage}` and `manning_2026: {bankfull_q: 666.3, peak_q: 675.3, peak_stage: 11.00}`, render both columns labelled by method, and add a third field `rid_braelevel_msl: 8.81` with the 10.60-vs-8.81 discrepancy written down. Keep the `checks` strings but attach the label to them.

### [F-18] Low — Metric literals remain in the Reports 1–2 builder

- **Location:** `report/build_expert_report.py`
- **Empirical Evidence.** `9.23` ×9, `306.9` ×5, `7.64` ×4, `11.89` ×1, `65` ×13, `0.78` ×1. Example at `:197`: `<td class="num">9.23</td><td class="num">65</td>`. This violates AGENTS.md rule (2) ("builder ห้ามพิมพ์ตัวเลข metric เป็น literal") for Pillars 1–5; the rule is enforced by `test_goal6_consistency` only for Goal 6.
- **Critique.** Low severity because the values are currently correct and `test_reports12` anchors some of them. But the enforcement gap is structural: the same rule that caught N-01 in Goal 6 has no analogue for Reports 1–2, so the next canonical update will silently desynchronise the HTML.
- **Proposed Solution.** Extend the Goal-6 literal-scan test to `build_expert_report.py` / `build_report_html.py` with a small allowlist for prose years and figure numbers.

### [F-19] Low — One palette token is 4.48:1 (latent)

- **Location:** `report/build_expert_report.py:57`, `report/build_report_html.py:69`
- **Empirical Evidence.** Computed WCAG 2.1 contrast for all 12 text-bearing pairs:

| Token | Contrast | Verdict |
|---|---|---|
| paper / muted / accent / note / warn / ok / code / header-code / table-head | 14.56 / 5.49 / 5.22 / 10.31 / 7.46 / 7.00 / 10.38 / 8.72 / 10.38 | pass ≥4.5 |
| **sea-flood-fg `#f5edda` on `#1d6fb8`** | **4.48** | **fails 4.5 by 0.02** |
| chart-bar-fg `#fff` on `#4d94c9` | 3.28 | graphics-only |
| chart-accent-fg `#fff` on `#e74c3c` | 3.82 | graphics-only |

`grep "var(--c-sea-flood-fg)"` returns no usage — the token is declared and never applied as a text colour.
- **Critique.** Latent, not live. Reporting it as a pass would be wrong, and reporting it as a failure would overstate. It is 0.02 short and currently unused; it becomes a real failure the first time someone styles a caption with it.
- **Proposed Solution.** Darken the background to `#1c68ad` (≈4.65:1) or lighten the foreground, and add a contrast assertion to `tests/test_standards_integrity.py` over the declared token pairs.

### [F-20] Low — The 2026 compound row calls a +12 cm error "consistent"

- **Location:** `analysis/compound_flood_risk.py:94-99`
- **Empirical Evidence.** Predicted 2.36 m vs observed C.12 peak **2.24 m** (2026-09-27 19:00, verified in `2599_C.12_2026_hourly.json`). Status text: "สอดคล้องกับค่าโทรมาตรจริง 2.24 ม." The band is correct (`watch`, 2.00–2.40), so the classification survives.
- **Critique.** The previous round's +33 cm error is now +12 cm (+5.4 %) and the band is right — a real improvement. But "+12 cm" is not "consistent", and the same calibration produces 3.15 m for 2011 from an unsourced `Q = 3750`.
- **Proposed Solution.** Render the residual from the classifier (`abs(pred − obs)`) and phrase the status as "สูงกว่าค่าจริง 12 ซม. (5 %) อยู่ในเกณฑ์เดียวกัน".

### [F-21] High — The compound-risk figure and its own JSON place the 2026 event in two different risk bands

- **Location:** `analysis/compound_flood_risk.py:160` (marker) vs `:96` (JSON row)
- **Empirical Evidence.** The table and the plot use different tide inputs for the same event:

```python
# historical_benchmarks (line 96) — written to JSON
{"event": "ระลอกปลาย ก.ย. 2569 (เหตุการณ์จริง)", "q_bangsai_m3s": 2250, "tide_msl_m": 1.91}
#   -> calculate_c12_stage(2250, 1.91) = 2.36  -> risk_level "watch"   (2.00–2.40)

# markers (line 160) — drawn on the PNG
("2569 (จริง)", 2250, 2.12, "blue", "o")
#   -> calculate_c12_stage(2250, 2.12) = 2.57  -> "warning"            (2.40–2.70)
```

`analysis/compound_flood_risk_summary.json` and `report/assets/compound_flood_risk_matrix.png` were both written at **14:38 in the same execution** — so this is not a stale artifact. One run produced a JSON row at 1.91 m and a figure marker at 2.12 m, because the two code paths read from two different constants. The shipped figure draws the 2026 flood 21 cm higher than the table beside it, one risk band worse.
- **Critique.** This is the same defect the previous round fixed in the JSON, left behind in the plotting block — a partial fix, and the artifact that reaches readers is the wrong one. It matters more than F-20 because the PNG is what a stakeholder looks at; the JSON is not. The 2.12 value is also the *pre-fix* tide input, so the figure is a fossil of the old calibration: the corrected JSON (2.36, watch) and the uncorrected figure (2.57, warning) now disagree on the single question the matrix exists to answer — did the September 2026 flood breach a warning threshold?
- **Proposed Solution.** Drive both from one list: build `markers` from `historical_benchmarks` rather than restating the tuples, and assert `calculate_c12_stage(q, t) == row["c12_stage_msl_m"]` inside `main()` before saving the PNG.

### [F-22] Low — A downstream boundary condition is loaded and never applied

- **Location:** `analysis/hydraulic_1d_routing.py:7, 148, 152`
- **Empirical Evidence.** `grep -n "kgt30\|Kgt.30"` returns only three lines: the docstring (`:7`, "เงื่อนไขขอบเขตท้ายน้ำ"), the load (`:148`), and an unused `slope_reach3 = 0.00015` (`:152`). `x_kgt30` and `z_kgt30` appear nowhere else. The model routes Ny.1B → Ny.7 only.
- **Critique.** Low severity for the published numbers, because the 18.3 km reach legitimately has no tidal control at its downstream end. But the module advertises a downstream boundary it does not implement, and a reader of the docstring would reasonably assume the 43 km basin was modelled end-to-end. It is also the cheapest possible fix for a real gap: with `Kgt.30` in hand, the Ny.7 → Kgt.30 reach could carry the backwater that F-01's missing floodplain cannot.
- **Proposed Solution.** Either delete lines 7 and 148 and say the model covers Ny.1B–Ny.7 only, or implement the third reach with a stage boundary at Kgt.30 and report `travel_time` for the full 43 km — which is what the `7.37 h` claim in F-04 implicitly assumes.

---

## 4. Verified Invariants (Passed Spot-Checks)

| Check | Method | Result |
|---|---|---|
| Unified verification | `python3.14 tools/verify_all.py` | **4/4 steps pass** (catalog, SHA-256 quick, lint, pytest) |
| Catalogue completeness | `python3.14 catalog.py check` | **86/86** entries exist |
| Test suite | `python3.14 -m pytest tests/ -q` | **121 passed** |
| Canonical mirror — routing | field-by-field diff of `values.routing_1d` vs `hydraulic_1d_routing_summary.json` | **zero diffs** (N-01 fixed) |
| Canonical mirror — Goal 6 | `goal6/canonical.json → l3_coastal_coupled == l3_coastal_summary.json` | **True** |
| Canonical mirror — Goal 7 | `goal7/canonical.json → counterfactual_simulation == counterfactual_simulation_summary.json` | **True** |
| 65 h above bankfull | recomputed from `data/20_multistation_levels/st62.csv` (≥8.45 gauge = ≥6.86 MSL + 1.59) | **64.75 h**, 09-26 22:45 → 09-29 15:15 ✓ |
| Ny.1B bank elevation 10.60 | min of the two surveyed section-end elevations in `Ny.1B_profile.csv` | **10.601** ✓ (not invented) |
| Ny.7 crest 8.213 | surveyed point at offset 0.0, `Ny.7_profile.csv` | **8.213** ✓ |
| Khun Dan "36.5 days earlier" | now computed from `statistics.median(doys)` vs DOY 270 | derived, not hardcoded ✓ |
| Pasak 2011 headline | `rec_54.get("days_over_normal_storage", 94)` / `max_outflow_mcm_day, 84.78` | 94 / 84.78 from record ✓ |
| Compound calibration anchors | `calculate_c12_stage(2500, 2.00)` / `(3500, 2.30)` | 2.51 / 3.03 ✓ (comment now correct) |
| CP2 2026 band text | 2.73 > 2.70 → `critical` | status now says "ยังอยู่ในเกณฑ์วิกฤต" ✓ |
| Thai language lint | `pytest tests/test_thai_language_lint.py` | 10 passed ✓ |
| PDPA / privacy | `pytest tests/test_privacy.py` | no phone numbers, no profile links in tracked text ✓ |
| 461 medium reservoirs | `dams_medium_snapshot_461.json` feature count | **461** ✓ |
| L3 rainfall causality | `r24 = rain_data.get(d_prev)` uses the **previous** calendar day | causal ✓ (N-03 fixed) |
| L3 tidal phase | `elapsed_hours / 12.4206` from a fixed epoch | no midnight discontinuity ✓ |

---

## 5. Information Gaps & Required Field Data

1. **Gate-operation logs (FOI).** The Khun Dan release schedule and the CP2 control-structure operating rules are both absent. F-12 and F-14 cannot be resolved to better than a factor of three without them.
2. **Confirmed datum for Ny.1B.** `cross_section_hydraulics.json` already sets `manning_n_fitted: null` with the note "ข้าม — datum สถานียังไม่ยืนยัน". Until the benchmark is confirmed, every Ny.1B stage and every derived discharge is provisional — and F-17's 11.23 vs 11.00 discrepancy is very likely this same root cause.
3. **Provenance of `q_cms` at Ny.1B/Ny.7.** The opposite-signed Q/H peak offsets (F-04) cannot be explained from the repository. Either the column is routed/model-derived (then say so) or one series is shifted.
4. **Sub-daily 2011 inflow series.** F-13 is unfixable without it; the synthetic half-sine is the current substitute.
5. **Bathymetry and outlet conditions for the CP2 canal.** F-14 needs the canal invert profile and the Gulf water level at the outlet; neither is in `data/`.
6. **Calibration data for the compound-risk coefficient.** F-10 claims four years of telemetry; the repository holds 2026 only.

---

## 6. Priority Order

1. **F-12** — the 1100-vs-375 divisor. One number, a factor of three, in the most-quoted Pillar-3 result. Fix or explain before anything else.
2. **F-21** — the compound-risk PNG still draws the 2026 event at 2.57 m (`warning`) while the JSON says 2.36 m (`watch`). This is a half-applied fix from the previous round, and the wrong half shipped. Two-line change, regenerate, add the equality assert.
3. **F-01 / F-02** — divided-channel conveyance and a monotone inverse rating. This is the only *physics* error in the set, and it silently invalidates `bankfull_q`, `overflow_q` and the stage RMSE together.
4. **F-05 / F-06** — two documentation claims contradicted by the code's own artifacts ("2020–2026", "to 9 Oct"). Cheap to fix, expensive to be caught on.
5. **F-10 / F-13** — remove the calibration provenance claim and label the synthetic hydrograph in the JSON, not only in the figure legend.
6. **F-15 / F-16 / F-17** — the "one name, four numbers" and "missing data as a value" issues. All are one-line-per-site fixes that close the class of bug AGENTS.md rule (6) exists to prevent. F-17 now also carries the 8.81-vs-10.60 bank-elevation gap.
7. **F-03 / F-04 / F-22** — publish the convergence table, delete the unbacked celerity, and either implement the downstream boundary or stop advertising it.

**The systemic point.** Round 1 and Round 2 both concluded that every defect was a duplicated source of truth, and that fixing the duplication fixed the class. That is now true for *bookkeeping* — the canonical ledgers mirror their artifacts exactly, and I could not break that invariant anywhere. What this round found is the same disease one layer down, in the **model layer**: `c1 = 0.132`, `1100`, `11000`, `2200 + 2486·sin(t)`, `swan_hs` from a single timestamp. Each is a single source of truth with no upstream. The project has built excellent machinery to keep its *reports* honest and has not yet built the equivalent for its *parameters* — there is no test that asks a coefficient where it came from. That is the gap worth closing next.

F-21 sharpens the point: the fix that *was* applied went into the JSON and not into the figure, so the repository now holds two honest-looking copies of the same number that disagree by one risk band. Duplication is not only a matter of ledgers versus artifacts; it also runs table-versus-figure inside a single script.

---

## 7. Cross-Review Triage — `REVIEW.gemini_3.8_flash.md`

I triaged the Gemini review finding-by-finding, re-running every claim against the repository rather than accepting or rejecting it on plausibility. Verdicts: **Adopt** (I agree and have incorporated it), **Adopt-corrected** (I agree with the finding, its stated mechanism was wrong and is replaced), **Reject** (verified false or stale).

| Gemini ID | Verdict | Claim as stated | What I verified | Now tracked as |
|---|---|---|---|---|
| G-F01 | **Adopt-corrected** | 2011/2026 hydrographs are synthetic, *and chart legends label them as observed* | Synthetic: **true**. Legend claim: **false** — `goal7_counterfactual_simulation.py:194,207` read `"น้ำหลากจำลองปี 2554/2569"` ("simulated"); this was fixed in `43b38d9` and Gemini is describing the pre-fix state | F-13 |
| G-F02 | **Adopt-corrected** | Ny.1B has dual canonical bankfull values; the low one is "within-bank capacity at +8.81 m" | Dual values: **true**. Mechanism: **false** — Manning at 8.81 m gives **399.5 m³/s**, not 244.6 (needs `n = 0.0714`). But the `braelevel = 8.81` / `QMax = 266.9` metadata is **genuinely new evidence** and I have folded it in | F-17 (expanded) |
| G-F03 | **Adopt** | Tidal efficiency floored at 84 %, contradicting the report's ~17 % | True. Gemini's citation of the 17 % figure is loose; the actual line (`goal7_build_public.py:576`) says the canal surface goes **still** at peak tide, which is stronger than 17 % | F-14 |
| G-F04 | **Adopt** | Additive superposition makes `∂H_C12/∂H_tide ≡ 1.0`; no `Q × tide` interaction | True and distinct from my exponent critique. I have added it to F-10, with one correction: I do **not** assert the gain must be < 1, because tidal range amplifies upstream in this estuary — the defensible claim is that the gain is untested and assumed constant | F-10 (expanded) |
| G-F05 | **Adopt** | SWAN feature is one post-event scalar, zero variance | True; independently confirmed 31 stations, single timestamp `2026-10-16T19:00`, mean 0.0968 m | F-09 |
| G-F06 | **Adopt** | Documented 2020–2026 span is really 1 Jul – 20 Sep 2026 (`N = 1,130`) | True. Gemini's added interpretation — that 1,130 h is undersized for GBDT and explains GBDT losing to linear at +24/+48 h — is consistent with the artifact (GBDT 98.6 vs linear 72.7 at +6 h) and I have noted it | F-05 |
| G-F07 | **Adopt (new to me)** | Compound plot marker uses tide 2.12 while JSON uses 1.91, moving the event from `watch` to `warning` | **True, and I missed it.** The PNG was regenerated after the JSON fix, so the shipped figure carries the stale input | **F-21 (new)** |
| G-F08 | **Adopt (new to me)** | `Kgt.30` cross-section loaded but unused; no downstream boundary | **True.** `x_kgt30`/`z_kgt30` appear only at `:148`; `slope_reach3` at `:152` is also dead | **F-22 (new)** |
| G-F09 | **Adopt** | Q/H peaks asynchronous within each station, invalidating `argmax` travel times | True, and I had derived the same offsets independently (+6.5 h, −8.75 h) | F-04 |
| G-F10 | **Adopt-corrected** | Divisor 1100 contradicts the comment's 375 — rated **Low** | Finding: **true**. Severity: **I disagree.** Gemini rates the single most-quoted Pillar-3 number — off by 2.9× — as Low, while rating the unused `Kgt.30` load as Medium. I keep it Critical (F-12) | F-12 |

**Two claims I did not adopt**

1. **"Chart legends labeled them as observed discharge" (G-F01).** Verified false at `:194` and `:207`. The legend strings were corrected in commit `43b38d9`; the Gemini review appears to have read the pre-fix source or the round-2 audit report rather than the current tree. I agree with the underlying finding and reject the evidence.
2. **"`catalog.py check` passed for all 84 registered files" (Gemini §4.5).** The current count is **86**. Cosmetic, but it indicates the verification section was written from a stale run — which is the same failure mode as G-F01, and worth naming because it is the failure mode this project keeps having to defend against.

**One claim in Gemini's §4 that I could not reproduce as stated.** It reports the Khun Dan median peak day as "Day 306.5 (early November)" and treats that as an independent verification. The arithmetic is right (270 + 36.5 = 306.5) but it is circular: 36.5 is *defined* as `median_doy − 270`, so restating it as 306.5 verifies nothing. The actual check — that the median is over 22 peak dates including 2026 itself — I flag separately: the baseline that 2026 is compared against contains 2026. Excluding it would shift the median; the direction is not obvious without recomputation, and the script does not offer the variant.

**Net effect on this review.** Two findings added (F-21 High, F-22 Low), two materially strengthened (F-10, F-17), and one of my own omissions corrected — F-21 is a defect I walked past because I read the JSON and did not open the PNG. The Gemini review was worth running for that alone.

---

## 8. Remediation Log — Revision 3 (2026-10-17)

The repository owner asked for every actionable finding to be fixed. This section records what changed in code, what was deliberately left alone and why, and one new finding (F-23) that the fixes themselves exposed.

### 8.1 Closed in code

| Finding | Change | Evidence after the change |
|---|---|---|
| F-02 | Inverse rating rebuilt as a running maximum (`np.maximum.accumulate`) with a fold counter; only the *envelope* is asserted monotonic, so the pre-existing RMSE is preserved | Artifact prints `rating curve มีจุดพับ 7 จุด`; `rmse_stage_cm` 105.8 → **106.0** |
| F-04 | `HANDOFF.md:39` and both audit prompts no longer assert `7.37 h` / `1.62 m/s`; `travel_time_caveat` added to the artifact | `grep -c "1\.62\|7\.37"` returns only the explanatory note |
| F-05 | Canonical and summary now state the real training window | `train_window_actual 2026-07-01..2026-09-19`; `n_train` **1,125** at +6 h |
| F-06 | Usable test coverage published | `test_coverage_pct` **57.1**; `test_end_actual 2026-10-02 13:00` |
| F-07 | Purge implemented: `train_mask = (~test_flags) & (~leak_flags)` | `n_train` fell 1,130 → **1,125** |
| F-08 | Re-headlined against persistence | `linear_improvement_vs_persistence_pct` **41.8**; +24 h **−1.9 %** and +48 h **+3.2 %** now disclosed |
| F-09 | SWAN feature removed (15 → 14 features); `coupling` string states the exclusion and the reason | `coupling: "Tidal-Coupled (ไม่รวมคลื่น SWAN …)"` |
| F-11 | Divisor comment rewritten with explicit physical accounting; assumption recorded in metadata | `stage_reduction_assumption: "dh = dQ / 1,100 ตร.ม./วิ (B_eff ~730 ม. × v ~1.5 ม./วิ)"` |
| F-12 | Share now divides by a *computed* excess volume instead of a literal | 40.0 % → **38.8 %**; `excess_mcm` **11,325.1** |
| F-16 | Dams with null data excluded from the denominator | stress 57.92 → **60.82 %**; over-100 19.31 → **20.27 %**; `n_missing` **22**, `n_assessed` **439** |
| F-19 | Contrast token darkened in three builders | `#1d6fb8` → `#1a63a8` (4.48 → **5.31:1**) |
| F-21 | Plot markers now derived from the JSON benchmark list with an assertion, so figure and table cannot diverge | `assert abs(st - bm["c12_stage_msl_m"]) < 0.005` |
| F-22 | Dead `Kgt.30` load and `slope_reach3` removed; docstring scoped to Ny.1B→Ny.7 | `grep -c "kgt30"` → 0 |

### 8.2 Disclosed rather than changed — and why

- **F-01.** Divided-channel conveyance is now *computed and published* alongside the composite: at the Ny.1B levee crest, **666.3** composite vs **893.0** divided (+34 %). The **default stays composite** on purpose. Switching would push `rmse_stage_cm` from 106.0 to roughly 135 (~28 % worse) and inflate every capacity figure by ~30 %, and `n` was fitted under the composite assumption. Publishing both, with a `rating_sensitivity` block, is defensible; switching silently would not be.
- **F-03.** The convergence table now exists in the artifact (`n_sub` 6/12/24/48 → RMSE 103.8 / 106.0 / 107.3 / …), carrying the note *"ห้ามอ้างว่าเป็นคำตอบเชิงกายภาพ"*. The scheme itself is unchanged — this finding is about what may be claimed, not about the code.
- **F-10.** The fabricated multi-year calibration claim is deleted; `calibration_status` plus three `limitations` entries (including `∂H/∂H_tide = 1.0` and the missing `Q × tide` term) are in the metadata.
- **F-13.** The 2011 hydrograph is still synthetic. It is now prefixed `SYNTHETIC—` in `hydrograph_source`, with `hydrograph_detail` describing the reconstruction.
- **F-14.** Tidal lockout is still absent; it is listed in `limitations` rather than silently ignored.
- **F-15.** Keys renamed so the three capacities are distinguishable (`levee_crest_capacity_q_cms` 617.4, `terrace_onset_q_cms` **486.9**); the 420–425 empirical rating is reconciled in Revision 4 — see §8.3.
- **F-17.** All four Ny.1B candidates (244.6 / 266.9 / 399.5 / 666.3) are now documented; the dual-state block is not split.

### 8.3 Closed in Revision 4 — the three items left open in Revision 3

**F-18 — metric literals in the report builders.** `build_expert_report.py` and `build_report_html.py` now render every one of these from `analysis/canonical_numbers.json` through the `@@R:` token mechanism the project already used elsewhere. Five tokens were added (`ny7_peak_g` 9.23, `ny7_peak_msl` 7.64, `gistda_oct2` 306.9, `cf_ov_mcm` 11.89, `cf_ov_h` 65) and all 23 literal occurrences replaced. The only surviving `65` is the Buddhist-era year in `2564/65/67/68`, which is not the metric. Both builders still pass their canonical checks (20/20 and 18/18), and a new test — `test_reports12_builders_have_no_metric_literals` — fails if any of these values is typed into a builder again.

**F-15 — three numbers called "Ny.7 bankfull capacity".** They are not rivals: two methods at one stage, plus one different stage.

| Definition | Stage | Method | Q (m³/s) |
|---|---|---|---|
| terrace onset | 6.86 m MSL | empirical rating `242(h−4.55)^0.66` | **420.5** |
| terrace onset | 6.86 m MSL | Manning, composite conveyance | **486.9** |
| levee crest | 8.213 m MSL | Manning, composite conveyance | **617.4** |

The first two differ by +15.8 %, which sits inside the ±18–20 % rating band the reports already state. The third is a different stage entirely. `docs/DATA_DICTIONARY.md` now carries this table, plus the divided-channel values (560.1 and 842.8) for completeness.

**F-04 — the opposite-signed Q/H peak offsets.** Root cause established from the raw 15-minute series: `q_cms` is station-reported and does not track `level_msl_m` through any single rating. At the event peak, Q peaks **6.5 h before** stage at Ny.1B and **8.75 h after** stage at Ny.7. With opposite signs at the two ends, a Q-to-Q "travel time" was never a travel time at all. That figure (24.25 h) is now removed from the artifact and from the canonical ledger, replaced by the two offsets as explicit evidence fields. The surviving `travel_time_stage_obs` = 9.0 h is stage-to-stage and interpretable, and the caveat now also states that the simulated 3.25 h is Q-to-Q, so the two are not directly comparable.

One thing is still a genuine information gap rather than a defect: *why* the station's Q series peaks early at Ny.1B needs the station's own rating or derivation metadata, which the repository does not hold. That is the same gap as §5 item 3.

### 8.4 Still open

- **F-17** — the dual `peak_q` / `peak_stage` state at Ny.1B is documented but not split; resolving it needs the confirmed datum.
- **Ny.1B datum** — upstream of F-17 and of most Pillar-1 uncertainty; no code change can close it.

### 8.5 New finding F-23 — documentation drift created by these fixes (Medium, fixed)

Changing artifact values left four documents that restate them behind. `docs/REVIEW_PROMPT_EN.md:25,68` still told auditors the L3 model ingests SWAN and cuts +6 h RMSE *"by 50.5 % (72.7 → 36.0 cm)"*; `docs/REVIEW_PROMPT_COMPREHENSIVE.md:49` carried an even older pair (**47.7 %**, 76.3 → 39.9); `HANDOFF.md:44` still said **40.0 %** for CP2; both prompts still described training as *"2020–2026"*; and `HANDOFF.md:36` labelled the modelled reach **43 กม.** when the model covers 18.3 km.

This is the same class as round 2's N-01/N-04, and precisely the failure mode the project's own AGENTS.md rule (4) exists to prevent: a number that lives in six places drifts in five of them. All four documents are corrected, and the three round-3 review artifacts are registered in `catalog.py` (**86 → 88** entries) and `docs/PROJECT_MAP.md`.

**Verification after every change above:** `tools/verify_all.py` **4/4**, `catalog.py check` **88/88**, `pytest tests/` **122 passed** (121 + the new F-18 guard).

**One methodological note.** Running pytest with its stdout redirected to a file produced three spurious failures (`OSError: [WinError 6]` inside `subprocess.run`, raised from `_winapi.DuplicateHandle`). The same suite passes cleanly with stdio inherited. This is a sandbox handle restriction, not a defect in the tests — worth recording so the next auditor does not chase it.

### 8.6 Revision 5 — three structural fixes so this class of finding stops recurring (maintainability, not correctness)

The findings above were each fixed individually. Three of them, however, shared a *mechanism* that made them recur across audit rounds: F-18 (hardcoded metric literals) survived four rounds because nothing checked for literals; the N-01/N-04 class recurred because the catalog check only ran in one direction; and F-15's confusion was possible because an artifact stored its fields positionally. Those three mechanisms are now closed at the structural level.

**1. The token contract is two-way.** `@@R:` substitution already existed, but only **14 of 53** `render` tokens were covered by `checks["expert"]` (12 of 53 for the public report). The other 39 could be typed as literals into a template and no assertion would notice — exactly the hole F-18 fell through. `test_token_contract_is_two_way` now computes the set of tokens the two builders actually use and asserts set equality with `render` in both directions: an undefined token fails (as before), and a **defined-but-unused** token now fails too. Six dead tokens were deleted as a direct result (`m4drop`, `med_cnt`, `r1d_ny1b_q_bankfull`, `r1d_ny7_q_bankfull`, `r1d_ny7_q_terrace`, `r1d_reach_km`), taking `render` from 53 to **47**.

**2. The catalog check runs in reverse.** `catalog.py check` verified *registered → exists*. It structurally could not see a file that exists but was never registered, which is why N-04 recurred. `catalog.py audit` now walks `*.md` and `docs/*.md` and reports anything on disk that is absent from the catalog. The scope is deliberately narrow: a blanket rule over all 181 files flagged 115, because `analysis/` is a curated 27 %-coverage atlas by design, not an inventory. Documents are where the failure actually occurred, and there it is now **32/32 registered, 0 unregistered**, with `test_all_top_level_docs_are_registered` enforcing it without an allowlist.

**3. Positional records are gone.** `analysis/goal4_counterfactual_summary.json` stored each scenario as `[11.89, 65, 513.9, 7.68, "2026-09-27 10:00:00"]`, and `build_canonical_numbers.py` mapped those by index. Inserting one field anywhere would have silently relabelled every downstream number with no error and no test failure. `_scenario_record()` now emits named keys (`overflow_mcm`, `hours_above_bankfull`, `peak_q_cms`, `peak_stage_msl_m`, `peak_time`), and the consumers read by name.

**Evidence that the refactor is value-neutral:** both report HTMLs were regenerated from the new artifact chain and came back **byte-identical** — `git status` shows no modification to either file after the rebuild. All scenario values are unchanged (`actual` 11.89 / 65 / 513.9 / 7.68; `R1` = `M1` 5.39 / 18 / 567.2 / 8.18; `M2` 0.83 / 8 / 466.3 / 7.25; `M3` 0.83 / 9 / 466.3 / 7.25).

**Guards were proven non-vacuous by mutation, not assumed.** Injecting a `__mutation_probe__` token into a builder made the contract test fail; creating `PROBE_UNREGISTERED.md` made the catalog test fail. Both probes were then removed.

**Verification after this round:** `tools/verify_all.py` **4/4**, `catalog.py check` **97/97**, `catalog.py audit` **32/32** with 0 unregistered, `pytest tests/` **124 passed**. Documentation counts refreshed (`START_HERE.md` 88→97 entries and 121→124 tests; `HANDOFF.md` likewise), and the stale "121 passed" bullet in `HANDOFF.md:59` — itself an instance of the drift class this section is about — corrected.
