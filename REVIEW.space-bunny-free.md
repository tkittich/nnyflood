# Hydrological Audit & Red-Team Report: `nnyflood`

**Auditor role:** Independent Senior Hydraulic Engineer / Lead Data Science Auditor (Red-Team)
**Model identifier:** `space-bunny-free`
**Date of audit:** 17 Oct 2026
**Repository:** `E:\theera\code\flood` (branch `main`)
**Mode:** Strictly read-only. No files modified, no commits, no destructive commands.

---

## 0. Scope, Method & Baseline Verification

### 0.1 Mandatory verification runner — **PASSED (4/4)**

```
$ python tools/verify_all.py
[1/4] catalog.py check .............................. ✅ ผ่าน (0.05 วินาที)
[2/4] verify_data_integrity.py --quick ............... ✅ ผ่าน (2.66 วินาที)
[3/4] pytest lint .................................... ✅ ผ่าน (0.97 วินาที)
[4/4] pytest tests/ .................................. ✅ ผ่าน (10.48 วินาที)
🎉 ระบบผ่านการตรวจสอบความสมบูรธุ์ 100%
```

Independent re-execution of the constituent steps:

| Command | Result |
|---|---|
| `python catalog.py check` | 97/97 catalog entries exist |
| `python -m pytest tests/ -q` | **129 passed** in 10.04 s |
| `python analysis/verify_data_integrity.py --quick` | OK 2892 · MISSING 37 · DELETED 3 · SKIPPED 458 · **MISMATCH 0** |

> **Audit note on the green baseline.** The 129 tests verify *internal consistency and drift detection*, not *external physical validity*. `tests/test_standards_integrity.py:170-197` (`test_canonical_mirrors_artifacts`) asserts only that `canonical_numbers.json[key] == artifact_json`. It never checks that a number is physically correct. A model can be internally consistent and physically wrong and still pass 129/129 — as demonstrated by F-01 through F-05 below, all of which are green.

> **Audit note on MISSING 37 / DELETED 3.** All 37 MISSING are `data/06_citizen_social/images/*.jpg` recorded under an absolute `D:/theera/...` path in a stale hash list; the 3 DELETED are `data/manual/manual-deleted/S2*.SAFE.zip` intentionally removed (HANDOFF:242 "R-13 ลบ PQR ซ้ำ"). Neither is a hash mismatch. Consistent with the project's stated policy. **However**, `HANDOFF.md:273` records two unexplained `data/22_goal6_network` items (`mask_sea.npy`, `2015_751_BKK006_annual.json`) as still "ยังไม่ได้สอบสวน" (not investigated) — these do **not** appear in the current MISSING list, so they were apparently resolved; the HANDOFF note is now stale and should be closed.

---

## 1. Executive Summary

### Overall Scientific & Engineering Reliability: **Medium — with Low reliability in the three most recently added advanced models**

The repository's *governance infrastructure* is genuinely strong — better than most published hydrological work. Canonical number ledgers, a retired-value ledger, SHA-256 provenance for 3,390 hashes, an explicit data-gap register, a legal/defamation framework, and a 129-test suite constitute real, working discipline. Pillar 1 (Goals 1–5) metrics are traceable, caveated, and reproducible.

The problem is concentrated in the **three "advanced modeling" deliverables added on 17 Oct 2026** (1D routing, L3 coastal coupling, CP2 counterfactual). Each is a *headline number generator* whose central parameter is uncalibrated or structurally degenerate, and each produces a number that is subsequently presented with more confidence than the formulation supports. In all three cases the analysis script's own docstring disclaims the result — and the disclaimer has not propagated to the handoff document.

**Encouraging finding that materially changes the exposure assessment:** none of the three defective results reached the published reports. Verified by exhaustive grep (§F-09, F-10). The published scientific claims are therefore *cleaner* than `HANDOFF.md` asserts. The exposure is confined to `HANDOFF.md`, the canonical ledgers, and the interactive portal.

### Key System Strengths (validated)

1. **Canonical-number contract is real and enforced.** Every headline metric audited (`666.3`, `617.4`, `486.9`, `3.25`, `4394.5`, `11325.1`, `38.8`, `0.53`, `73.6`, `35.9`, `51.2`, `0.132`, `2.70`, `1.28`, `1100`) is **absent** from all seven report-builder sources. They are read from canonical JSON. This is exactly the discipline AGENTS.md §"เป้าหมาย 6: สัญญา canonical แบบเดียวกัน" demands, and it held.
2. **Honest self-disqualification.** `hydraulic_1d_routing.py:356-357` states *"RMSE ไม่ลดลงเมื่อแบ่งช่วงย่อยละเอ็ยดขึ้น → ผลที่ n_sub=12 เป็นค่าที่ 'พอดี' ไม่ใช่ค่าที่ลู่เข้า · ห้ามอ้างว่าเป็นคำตอบเชิงกายภาพ"* ("does not converge … must not be claimed as a physical answer"). The author knew. So did the CP2 script (`:153-158`). This is a governance *propagation* failure, not an integrity failure.
3. **Phantom-figure retirement genuinely worked.** The 43 km basin-wide lag (7.37 h) and 1.62 m/s celerity are absent repo-wide (verified — only coincidental digit matches inside `dam_history_all.json`). This was the correct call.

### Critical Vulnerabilities & Limitations

1. **The Ny.1B rating curve is physically non-physical** (F-01): discharge *drops 22%* for a 25 cm rise in stage, because composite `R = A/P` collapses when the compound section spills onto the floodplain. The headline "bankfull capacity 666.3 m³/s" sits on a fold and the curve under-predicts the observed peak discharge by **14.4%**.
2. **The Muskingum–Cunge routing is run outside its validity domain** (F-02): the X parameter clamps to **exactly 0.000** for every reported resolution, degenerating the scheme to maximally-damped level-pool routing; numerical damping coefficients go **negative** at `n_sub=48`; grid convergence **diverges monotonically**.
3. **The L3 headline metric is a tidal-aliasing artifact** (F-03): persistence RMSE swings from 17.9 cm to 60.4 cm purely as a function of lead time, tracking the ~24 h recurrence of the tidal signal at C.12. The "+6 h improvement of 51.2%" is measured at the lead time of *maximum* tidal phase difference and the "−1.9% at +24 h" at the lead time of *minimum*. Cross-horizon comparison is invalid.

---

## 2. Findings Matrix

| ID | Severity | Component / Target | Root Cause Summary | Recommended Action |
|---|---|---|---|---|
| **F-01** | **Critical** | `analysis/hydraulic_1d_routing.py:46-120, 183-189`; `hydraulic_1d_routing_summary.json:19,32,64,76,82` | Composite conveyance `K = A·(A/P)^{2/3}` on a compound section makes Q(H) non-monotonic; Ny.1B Q falls 735.4→571.9 m³/s between H=10.50 and 10.75 m. Rating under-predicts observed peak Q by 14.4% | Adopt `divided` (vertical-slice) conveyance as default; recalibrate `n` per section against observed (Q, H) pairs; publish the fold count as a hard gate |
| **F-02** | **Critical** | `hydraulic_1d_routing.py:152-162`; summary `:86-108` | `x_param` raw value is negative over the whole operating range → `max(0.0, …)` clamps X ≡ 0 for `n_sub` ≥ 12. `c3` goes negative at `n_sub=48`. Grid RMSE diverges 126.4→131.1 | Reject the 3.25 h result; either implement a stable advective–diffusive scheme (Bates–Cunge with `d²`), or publish only the attenuation ratio with the non-convergence stated in the headline |
| **F-03** | **Critical** | `analysis/goal6_l3_coastal_model.py:129-235`; `goal6/l3_coastal_summary.json`; published in `report/ชุดเทียบมาตรฐาน2554.html` | RMSE of absolute stage is dominated by the semidiurnal tide; persistence baseline varies 3.4× (17.9–60.4 cm) with lead time alone | Switch to de-tided target or report RMSE of the flood component + peak-magnitude and timing error; never compare horizons on absolute-stage RMSE |
| **F-04** | **Critical** | `analysis/goal7_counterfactual_simulation.py:119, 137, 47-55`; `goal7/counterfactual_simulation_summary.json:11` | "Tidal efficiency" is a cosine with period **30.5 d (2554) / 31.0 d (2569)** — ~60× the M2 semidiurnal period — and floors at 0.80–0.84, never zero | Replace with a real semidiurnal gate schedule; allow zero efficiency at high water; treat current output as a screening envelope only |
| **F-05** | **Critical** | `analysis/goal2_khundan_22y_baseline.py:82-86`; `goal2_khundan_22y_summary.json` | Reported `sep_storage_gain_mcm` (= end-Sep storage − start-Sep storage) fails to reconcile with `sep_inflow − sep_outflow` in **22/22 years**, worst +7.76 MCM (2013). `float(x or 0)` silently converts missing flow to a real zero (2005 outflow = 0.00 MCM) | Close the mass balance or drop the storage-gain column; replace `or 0` with explicit null handling and report missing-day counts per year |
| **F-06** | High | `goal7_counterfactual_simulation.py:79-87` | `dq_dh_m2s = 1100.0` is a bare literal. The 0.53 m headline maps to 0.12–0.97 m over `dQ/dh` ∈ [5000, 600] — an **8× span** | Present 0.53 m as a range from an explicit `B_eff × v` bracket; register the Ayutthaya cross-section as a blocking gap |
| **F-07** | High | `goal7_counterfactual_simulation.py:122` | `safe_cap_ayutthaya = 2600.0` is an unsourced literal driving both numerator and denominator of the 38.8% headline. Over 2200–3100 m³/s the share ranges **33.7%–48.8%** | Source `safe_cap` from a RID rating curve or Ayutthaya cross-section; publish sensitivity as a required field, not an appendix |
| **F-08** | High | `analysis/compound_flood_risk.py` (whole file) | Entirely outside the canonical contract: registered in **none** of the three canonical ledgers, yet published on `index.html`. `c1=0.132`, exponent `1.28`, and thresholds `2.00/2.40/2.70/2.80` are hardcoded; zero test coverage | Register in `goal6/canonical.json` with a `definitions` block and explicit `calibration_status`; add a retired-ledger entry if any value changes |
| **F-09** | High | `HANDOFF.md:19` and `HANDOFF.md:46` | Both assert report integration that never occurred. `build_expert_report.py` / `build_report_html.py` contain **no** `routing_1d` reference; `666.3`/`617.4`/`3.25` absent from reports 1–2. `38.8` appears **0 times** in reports 7/8 despite `goal7_analysis.py:1377-1379` folding the counterfactual into canonical | Correct both HANDOFF claims to "canonical พร้อมแล้ว · ยังไม่เรนเดอร์ในรายงาน"; add a test asserting every canonical key is referenced by ≥1 builder |
| **F-10** | High | `report/assets/portal_map.js:86, 100` | `:100` still asserts *"เพิ่มความแม่นยำพยากรณ์ขึ้น 47.7%"* — a figure **retired** from canonical (matches no current value: 51.2 / 41.8 / −1.9 / +3.2). `:86` asserts C.12 peak **2.12 m**; raw series max = **2.24 m** and `compound_flood_risk.py:104` states 2.24 m | Render portal values from canonical; delete the 47.7% string; correct C.12 peak to 2.24 m |
| **F-11** | High | `analysis/compound_flood_risk.py:158-165` | Risk-band colours are the *sole* visual encoding of the 4 risk classes. Composited at α=0.85 over white: watch **1.63:1**, normal **2.06:1**, warning **2.77:1** — all below the project's own 3.0:1 rule (AGENTS.md §7) | Replace palette with ≥3.0:1 (e.g. `#1b7f3b` / `#8a6d00` / `#b34700` / `#a12020`), drop α to 1.0, add an automated contrast test |
| **F-12** | Medium | `tests/test_goal6_consistency.py:102-119` | Literal-ban is a **12-string blocklist** covering only 2 of 7 builders. `build_expert_report.py`, `build_report_html.py`, `goal7_build_public.py`, `goal7_build_academic.py`, `portal_map.js` are never scanned | Replace with a value-vs-canonical cross-check; extend coverage to all builders + portal JS |
| **F-13** | Medium | `HANDOFF.md:84` vs `goal6/national_medium_reservoirs_summary.json` | HANDOFF says **19.3%** (89/461); canonical says **20.27%** (89/439). The script's own `missing_data_note` records that the 461-denominator behaviour was a *bug* that understated the stress index | Update to 20.27%; the retired 19.3% should be added to `goal6/canonical.json → retired` |
| **F-14** | Medium | `hydraulic_1d_routing.py:309-315, 321-329`; summary `:16-19, 28-33` | Keys named `levee_crest_*` hold **bankfull/berm** values. `peak_above_levee_m = 0.40` is peak stage − bankfull, not "above levee". `ny7.note` contradicts its own key names | Rename to `bankfull_*` / `bankfull_capacity_q_cms`; reserve `levee_*` for surveyed embankment crests |
| **F-15** | Medium | `hydraulic_1d_routing.py:176-189` | `n = 0.0437` is annotated *"สอบเทียง Ny.7"* (calibrated at Ny.7) yet is applied to Ny.1B, which uses a **different slope** (0.00065 vs 0.00035). The two "bankfull capacities" are therefore not comparable | Calibrate `n` independently per section; report both with per-section provenance |
| **F-16** | Medium | `goal6_l3_coastal_model.py:101-102, 246-247` | Single-event training (1 season, `n_train` 1,125–1,467). Train = 20 Jul–19 Sep; test = 20 Sep–2 Oct of the **same event**. Within-event interpolation, not generalisation | Refit on 2020–2026 (`data/30_national_warehouse/`) with walk-forward CV; report per-season results |
| **F-17** | Medium | `goal6_l3_coastal_model.py:85, 155-156` | Rainfall is a **single point** ("กรุงเทพกลาง") for the lower Chao Phraya, and `r24` is the *previous calendar day* only (≤24 h stale, up to 20 h of recent rain discarded). `rain_data.get(..., 0.0)` turns gaps into zeros | Use `basin_rain` areal series; use a true trailing 24 h window; count imputed days |
| **F-18** | Medium | `goal6_l3_coastal_model.py:118-125` | 57.1% test coverage is caused by **BKK001 ending 2026-10-02 15:00** while C.12 and CPY015 both run to 10-09. Root cause is not stated anywhere | Name BKK001 in the metadata; extend its record before drawing +24/+48 h conclusions |
| **F-19** | Low | `compound_flood_risk.py:157` | `levels = [1.6, 2.0, 2.4, 2.7, 3.2]` is **dead code**; `contourf` at `:163` uses an inline literal `[1.4, …, 3.4]`. Bounds disagree | Delete line 157 or use it and remove the inline list |
| **F-20** | Low | `goal6_l3_coastal_model.py:6`; `compound_flood_risk.py:8` | Both module docstrings still claim SWAN wave heights are inputs; `:173-176` and `:134` state they are not | Update docstrings to "Tidal-Coupled only" |
| **F-21** | Low | `goal2_khundan_22y_summary.json` metadata; `goal6_national_medium_reservoirs.py` | Pasak 24 y has an explicit, correct `storage_definitions` block separating normal conservation / surcharge pool / emergency freeboard. Khun Dan 22 y and the 461-reservoir index have **no** equivalent, so "over 100%" is undefined there | Port Pasak's `storage_definitions` block to both scripts |
| **F-22** | Low | `goal2_khundan_22y_baseline.py:111-113` | `median_doy` **includes 2026**, the very event being compared → 36.5 d. Leave-one-out median gives **37.9 d** | Use leave-one-out; state the choice |
| **F-23** | Low | `goal2_khundan_22y_baseline.py:63` | `is_full = max_q >= CAPACITY` → 9/22 = 40.9%. `peak_pct ≥ 99%` → 12/22; `≥ 98%` → 13/22. Three defensible answers to "how often full" | Publish all three with labels, per AGENTS.md rule 7(6) |
| **F-24** | Low | `hydraulic_1d_routing_summary.json:45` | `rmse_stage_cm = 106.0` cm. Decomposed: **mean bias −80.1 cm (57.1% of MSE)**, residual 69.4 cm. The error is dominated by an uncalibrated rating curve, not by routing skill | Report bias and RMSE separately; a model with a constant −0.80 m offset is not a routing result |

---

## 3. Deep-Dive Technical Findings

### [F-01] Ny.1B rating curve is non-monotonic — the headline "bankfull capacity" is a fold artifact

**Location**
`analysis/hydraulic_1d_routing.py:46-108` (`compute_hydraulic_geometry`), `:183-189` (call sites); manifest at `analysis/hydraulic_1d_routing_summary.json:19, 32, 64, 76, 82`.

**Empirical evidence** — recomputed from the surveyed profiles `data/19_rid_cross_sections/derived/Ny.{1B,7}_profile.csv` with `n = 0.0437`:

```
Ny.1B  (S0 = 0.00065), composite method
  H=10.25  A=436.8  P= 96.8  R=4.51  B= 93.8   Q = 695.8
  H=10.50  A=460.7  P=101.8  R=4.53  B= 98.5   Q = 735.4   <-- local maximum
  H=10.75  A=493.3  P=176.1  R=2.80  B=172.5   Q = 571.9   <-- -22.2 % for +0.25 m
  H=11.00  A=546.5  P=223.6  R=2.44  B=220.0   Q = 578.4   <-- OBSERVED PEAK STAGE
  H=11.25  A=601.5  P=223.6  R=2.69  B=220.0   Q = 678.7

Observed at Ny.1B (st61.csv): peak Q = 675.3 m³/s at H = 11.00 m
Rating curve at H = 11.00 m            : Q = 578.4  →  -14.4 % bias
Ny.7 at observed peak H = 7.68 m       : Q = 548.5  vs observed 648.3  →  -15.4 % bias
```

**Hydraulic & Data Science critique**

The root cause is documented in the function's own docstring (`:50-53`) but its consequence is not carried into the results. Manning's form `Q = (1/n)·A·R^{2/3}·S^{1/2}` with a **single composite** `R = A/P` assumes one uniform flow region. When the flow spills onto a 220 m-wide floodplain, `P` jumps 101.8 → 223.6 m while `A` grows only 460.7 → 546.5 m², so `R` collapses 4.53 → 2.44 m and `R^{2/3}` falls by 28 %. A rating curve whose discharge *decreases* as stage rises has no hydraulic meaning.

Consequences, in order of severity:

1. **The headline is a fold.** `666.3 m³/s` at Ny.1B is quoted at `bank_ny1b = 10.60`, but `Q(10.50) = 735.4 > Q(10.60) = 666.3`. The reported "capacity" is *below* the local maximum immediately beneath it. Any reader — including downstream report authors — is entitled to treat 666.3 as "the flow the channel can carry before spilling", which the model itself contradicts.
2. **The rating curve cannot reproduce the event it is used to invert.** Both stations under-predict observed peak discharge by 14–15 % at the observed peak stage. The implied roughness to match Ny.7 is `n ≈ 0.0437/1.154 = 0.0379`. So `n = 0.0437` is mis-assigned for this channel, and the `manning_n_note` (":300") only warns about the *method*, not the *station*.
3. **`666.3` vs `617.4` is not a like-for-like comparison** (also F-15): the two use different slopes (0.00065 / 0.00035) and different sections. The Ny.1B number carries √(0.00065/0.00035) = 1.36× the slope leverage of the Ny.7 number — 36 % of the apparent "downstream capacity loss" is a slope-assumption artifact.
4. **Method spread dominates.** The script's own sensitivity table gives 578.4 (composite) vs 1009.1 (divided) at Ny.1B H=11.00 — a **74 % spread**. The reported single figure `666.3` sits inside this band and therefore carries an unstated ±35 % method uncertainty. This is honestly disclosed in `rating_sensitivity`, which is to the author's credit — but the headline table does not carry the caveat.
5. **The inversion is safe.** I specifically tested the upper-envelope inversion (`:236-246`) that the code uses to handle the 7 folds in the Ny.7 curve. The induced bias is **negligible** (max −1.6 cm at Q = 500 m³/s; 0.0 cm elsewhere). **This mechanism is not a defect** and should be recorded as such.

**Proposed solution**

```python
# 1. Default to the divided (vertical-slice) conveyance — monotonic by construction
def stage_to_discharge(geom, n, slope, method="divided"):
    ...  # default changed

# 2. Hard gate: refuse to report a capacity on a folded curve
q_raw = np.array([stage_to_discharge(compute_hydraulic_geometry(x,z,l), n, S, "divided")
                  for l in levels])
if np.any(np.diff(q_raw) < 0):
    raise ValueError("divided conveyance must be monotonic — check section orientation")

# 3. Calibrate n per station against observed (Q, H) pairs
#    Ny.7: target Q=648.3 @ H=7.68 -> n = 0.0379 (not 0.0437)
#    Ny.1B: target Q=675.3 @ H=11.00 -> n to be solved; do NOT reuse Ny.7's n
```

Separately, rename `levee_crest_*` → `bankfull_*` (F-14) and report the capacity as a band `[Q_composite, Q_divided]` in the headline table, never as a point value.

---

### [F-02] Muskingum–Cunge X parameter is clamped to zero — the scheme is run outside its validity domain

**Location** `analysis/hydraulic_1d_routing.py:145-162`; convergence evidence at `hydraulic_1d_routing_summary.json:86-108`.

**Empirical evidence** — evaluated the scheme's own coefficient expressions across the operating envelope:

```
n_sub=12  dx_sub=1525 m        n_sub=48  dx_sub=381 m
  Q=100 b=122  c=0.93  X_raw= -0.330  -> X_used = 0.000
  Q=100 b=141  c=0.87  X_raw= -0.261  -> X_used = 0.000
  Q=100 b=160  c=0.83  X_raw= -0.205  -> X_used = 0.000
  Q=100 b=122  c=0.93  X_raw= -2.820  -> X_used = 0.000   c3 = -0.044  (NEGATIVE)
  Q=100 b=141  c=0.87  X_raw= -2.544  -> X_used = 0.000   c3 = -0.015  (NEGATIVE)

Grid convergence actually observed (summary :88-107):
  n_sub= 6  rmse_q=126.4  rmse_h=103.8  q_peak=591.7
  n_sub=12  rmse_q=128.8  rmse_h=106.0  q_peak=613.0   <-- the reported configuration
  n_sub=24  rmse_q=130.2  rmse_h=107.3  q_peak=627.5
  n_sub=48  rmse_q=131.1  rmse_h=108.0  q_peak=638.9
```

**Hydraulic & Data Science critique**

`x_param = 0.5·(1 − Q/(b·S₀·c·Δx))` (`:153`) reduces analytically to `0.5·(1 − 3y/(5·S₀·Δx))`. With `S₀ = 3.5e-4` and `Δx = 1525 m`, the term `5·S₀·Δx = 2.67`, so any depth exceeding ~0.45 m drives `X_raw` negative. The clamp at `:154` (`max(0.0, min(0.45, …))`) then converts a *destabilised* configuration into `X ≡ 0`.

Three distinct failures follow:

1. **`X = 0` is level-pool routing, not diffusive-wave routing.** At `X = 0` the Muskingum coefficients reduce to pure storage routing with maximum attenuation and no momentum diffusion. The model's stated purpose — "แบบจำลอง… คลื่นลมทะเล" (diffusive-wave propagation, `:5`) — is not achieved.
2. **The negative `c3` at `n_sub = 48` proves the scheme is outside its stability domain.** `c3 = 2K(1−X)/(2K(1−X)+Δt) < 0` requires `2K(1−X) < Δt`, i.e. the reach is over-resolved relative to the time step. This is a numerical-oscillation regime.
3. **The solution diverges rather than converges.** RMSE increases monotonically 126.4 → 131.1 and peak Q rises 591.7 → 638.9 with refinement. Grid convergence is the *minimum* standard for a discretised PDE solution; failing it means `n_sub = 12` is a fitted value, not a computed one.

**The travel-time number.** The 3.25 h figure is, however, *physically coherent as a channel-translation estimate*. Independent hand calculation at Ny.7 bankfull: `R = 606.9/160.0 = 3.79 m`, `v = (1/0.0437)·3.79^{2/3}·0.00035^{0.5} = 1.04 m/s`, `c = (5/3)v = 1.74 m/s` → 18,300 / 1.74 = 10,517 s = **2.92 h** pure translation, plus Muskingum storage delay → ≈ 3.25 h. So the magnitude is right; the claim is wrong.

**The 9.0 h gap.** `travel_time_stage_obs = 9.0 h` (H→H) versus `travel_time_hours_sim = 3.25 h` (Q→Q). Ratio **2.77×**. The model uses **only the bankfull channel** (widths 121.9 / 160.0 m). It contains **no floodplain storage term**, so the 5.75 h shortfall is not model error — it is *structurally absent physics*. Note the code correctly states at `:336-343` that these two numbers are not directly comparable (one is H→H, the other Q→Q). **The code is right; `HANDOFF.md:39` juxtaposes them anyway** as if they were the same quantity.

**Proposed solution**

1. **Withdraw 3.25 h as a travel-time result.** Report instead: *channel-translation time 2.9 h (hand-calculated), attenuation factor 3.25/2.92 = 1.11 (grid-divergent, not reported), observed stage lag 9.0 h ⇒ floodplain storage accounts for ~6 h — magnitude only, from a 2-section model that contains no floodplain geometry.*
2. Replace with a Bates–Cunge advective–diffusive form, or run HEC-RAS 1D — which HANDOFF:238 already lists as available and unexploited ("วัตถุดิบครบ: หน้าตัดจริง 5 สถานี data/19").
3. Add a convergence assertion: refuse to publish if `rmse(n_sub_max) > rmse(n_sub_min)`.
4. If `X_raw < 0` is to be clamped, at minimum **log the clamp rate**; 100 % clamping is the diagnostic.

---

### [F-03] The L3 headline is a tidal-aliasing artifact, and it is published

**Location** `analysis/goal6_l3_coastal_model.py:129-235`; `analysis/goal6/l3_coastal_summary.json`; **rendered in** `report/ชุดเทียบมาตรฐาน2554.html` (verified: `73.6`, `35.9`, `51.2` all present).

**Empirical evidence** — RMSE of the persistence baseline `H(t) − H(t+lag)` on the C.12 usable test window, computed directly from `data/22_goal6_network/raw/l1_bkk_lower/2599_C.12_2026_hourly.json`:

```
lag=  6 h  n=454  RMSE= 58.6 cm    lag/24h = 0.25 cycle
lag= 12 h  n=448  RMSE= 58.2 cm    lag/24h = 0.50 cycle   (max tidal difference)
lag= 24 h  n=436  RMSE= 17.9 cm    lag/24h = 1.00 cycle   (tide returns to phase)
lag= 36 h  n=424  RMSE= 60.4 cm    lag/24h = 1.50 cycle
lag= 48 h  n=412  RMSE= 31.8 cm    lag/24h = 2.00 cycle
                                              — swing factor 3.4× —
```

**Hydraulic & Data Science critique**

**On look-ahead leakage — I found none, and I want to be explicit about that.** The audit brief asks whether the trailing-24 h rainfall feature leaks into the target. It does not:

- `train_mask = (~test_flags) & (~leak_flags)` (`:192`) with `leak_flags = (t_lead >= test_start)` (`:184`) correctly purges any training sample whose *target* falls inside the test window. A sample at `t_curr = 19 Sep 12:00` with lead 6 h has `t_lead = 19 Sep 18:00 < 20 Sep 00:00` and is legitimately retained. **Correct.**
- Every feature is causal: `h0/h1/h3/h6`, `u0/u6/u12` at or before `t_curr`; `r24` is the *previous* calendar day; `tide0/tide_diff/tide_head` at `t_curr`; `tide_phase_*` is a closed-form function of calendar time (`:170-171`).
- Chronological split is strict, and the purge is *more* conservative than a naive split would be.

**The actual defect is the choice of metric.** RMSE of *absolute stage* is dominated by the gauge's tidal oscillation (range in test window: 0.13–2.24 m = 2.11 m). Because the lead times 6/24/48 h alias against the tide's ~24 h recurrence, the difficulty of the prediction task varies by 3.4× purely as a function of horizon. Therefore:

| Horizon | Reported linear improvement | True interpretation |
|---|---|---|
| +6 h | **+51.2 %** | Lead time of **maximum** tidal phase mismatch. Hardest task, biggest apparent win. |
| +24 h | **−1.9 %** | Lead time of **near-total** tidal cancellation (persistence RMSE already 17.9 cm). The target is nearly trivial; "no improvement" carries no information about the tide's usefulness. |
| +48 h | +3.2 % | Partial cancellation returns. |

The published conclusion *"ข้อสรุปใช้ได้เฉพาะการพยากรณ์ระยะสั้น (≤6 ชม.)"* ("usable only for short-range ≤6 h") is **not supported** — it is an artifact of horizon-to-tide aliasing. Equally, the +51.2 % is not evidence of forecast skill.

**Secondary findings in this component**

- **The base model is worse than doing nothing.** At +6 h, `linear_base_rmse = 73.6` cm vs `persistence_rmse = 61.8` cm — the 8-feature model is **19 % worse than predicting no change**. Measuring the headline against that baseline inflates the result. The project *does* disclose the fairer figure (`linear_improvement_vs_persistence_pct = 41.8`, `l3_coastal_summary.json:22`), which is creditable, but the headline uses 51.2 %.
- **Different test samples per horizon.** `n_test` = 262 (+6 h) vs 274 (+24 h, +48 h); `n_train` = 1,125 / 1,449 / 1,421. The three horizons are **not evaluated on a common sample set**, so the RMSEs are not mutually comparable even before the aliasing problem.
- **Single-event training** (F-16): train 20 Jul–19 Sep, test 20 Sep–2 Oct of the *same* flood. This is within-event interpolation.
- **Silent imputation** (F-17): `h1,h3,h6 = target_data.get(…, h0)` and `r24 = rain_data.get(…, 0.0)` inject synthetic zeros with no count of how often.
- **Coverage root cause unstated** (F-18): BKK001 ends `2026-10-02 15:00`; C.12 and CPY015 both run to `10-09`. The metadata says only "ข้อมูลเป้าหมายขาดช่วง 2–9 ต.ค." (":118") which is **wrong** — it is the *upstream* series that truncates.

**Proposed solution**

```python
# De-tide the target, then score on the flood signal
tide_pred = fit_semidiurnal(tide0, tide_phase_sin, tide_phase_cos)   # M2+K1+O1
y_flood   = y - tide_pred[t_lead]
# Score: RMSE of the flood component + peak-magnitude error + timing error (days to peak)
# Keep a common sample set across horizons (purge on the union of target windows)
```

Add to the metadata: `test_samples_common`, `imputed_feature_counts`, and the aliasing table above so the reader can see the metric's horizon dependence.

---

### [F-04] The CP2 "tidal efficiency" is a monthly cosine, ~60× the tidal period

**Location** `analysis/goal7_counterfactual_simulation.py:119, 137`, applied at `:46-47`.

**Empirical evidence**

```
2554: tide_eff_54 = 0.92 + 0.08·cos(linspace(0, 8π, 122))
      → 4 full cycles over 122 days → PERIOD = 30.5 days = 732 h
      → range 0.840 .. 1.000, floor never below 0.84

2569: tide_eff_69 = 0.90 + 0.10·cos(linspace(0, 2π, 31))
      → 1 full cycle over 31 days  → PERIOD = 31.0 days = 744 h
      → range 0.800 .. 1.000, floor never below 0.80

Reference: M2 semidiurnal tide = 12.4206 h = 0.518 days
Ratio: 732 / 12.42 = 59×  (2554)   744 / 12.42 = 60×  (2569)
```

**Hydraulic & Data Science critique**

The Pasak–Gulf of Thailand outlet is a **tidal gate**. It closes when the Gulf level exceeds the canal invert — roughly **twice daily**. The code models this with a smooth cosine whose period is a lunar month. It therefore:

1. **Cannot represent gate closure at all.** Efficiency floors at 0.80. The repository's own EIA evidence (`report/คลองเจ้าพระยา2_วิชาการ.html`, table row *"การระบายตามแรงโน้มถ่วงช่วงน้ำลง–น้ำขึ้นสูงสุด"*, citing EIA 2569 vol. 1 p.2-82, source class **A**) records net gravity-driven drainage falling from **891 to 107 m³/s** during peak high water — an **88 % reduction**. The model applies at most **20 %**.
2. **Misrepresents a physical gate as a smooth seasonal modulation.** Any reader would take `tide_eff` to be a tidal signal. It is not one.
3. **The author knew** — `:154-155`: *"ประสิทธิภาพถูกจำกัดต่ำสุดที่ 0.80–0.84 ไม่เคยเป็น 0 ทั้งที่รายงานระบุว่าผิวน้ำในคลองจะนิ่งตอนน้ำขึ้นสูงสุด"* ("efficiency floors at 0.80–0.84, never 0, although reports state the canal surface goes still at high water").

**Direction of the bias.** Since real gate closure is more severe than modelled, true diversion is **lower** than 4,394.5 MCM. Combined with F-06/F-07, the CP2 headline is **optimistically biased on every axis simultaneously**.

**Additional structural defect: no intake hydraulics.** The audit brief asks about submergence at the +10.25 m diversion weir crest. The code contains **no** check. Further, the inflow series is documented as *"จุดรวมน้ำเข้าอยุธยา"* (combined inflow at Ayutthaya, `:108`) while the CP2 intake is at **Chainat**, upstream of where the Pasak (S.26) joins. The model therefore assumes the entire Ayutthaya inflow is available ~50 km upstream at the intake, with no accounting for the Pasak's separate path. There is no backwater effect of the canal intake on the main river, and no submergence or weir-crest constraint on `q_div`.

**Proposed solution**

```python
# Real semidiurnal gate schedule, tied to the Gulf level and the canal invert
phase   = 2*np.pi * hours_since_epoch / 12.4206       # M2
gulf    = MSL + amp*sin(phase + lag)                   # from CPY015-equivalent record
efficiency = np.where(gulf > canal_invert_level, 0.0, np.clip(1 - 0.88*closure, 0, 1))
# and add an intake constraint:
q_div = min(q_div, weir_q(h_river - crest, gate_opening))   # crest = +10.25 m MSL
```

Until then, relabel all CP2 outputs **"upper bound, assuming no gate closure"** in the title, not only in a limitations array.

---

### [F-05] Khun Dan 22-year mass balance fails to close in every year

**Location** `analysis/goal2_khundan_22y_baseline.py:82-86`, `:99-101`; manifest `analysis/goal2_khundan_22y_summary.json`.

**Empirical evidence** — recomputed for all 22 annual records (2005–2026, 7,811 days):

```
years where (sep_inflow − sep_outflow) ≠ sep_storage_gain : 22 / 22
worst residual: +7.76 MCM (2013)

2005: in  99.32 − out  0.00 =  99.32 | reported storage_gain  98.86  (Δ −0.46)
2006: in  55.63 − out 34.47 =  21.16 | reported storage_gain  17.25  (Δ −3.91)
2007: in 104.02 − out 17.30 =  86.72 | reported storage_gain  83.46  (Δ −3.26)
2008: in  88.93 − out 61.21 =  27.72 | reported storage_gain  25.68  (Δ −2.04)
2009: in  64.44 − out  4.64 =  59.80 | reported storage_gain  58.92  (Δ −0.88)
```

Source of the mismatch — `:84-86`:
```python
sep_start_q = float(sep_rows[0].get("DMD_QUse_curr") or 0)
sep_end_q   = float(sep_rows[-1].get("DMD_QUse_curr") or 0)
sep_gain    = sep_end_q - sep_start_q        # <-- storage DIFFERENCE, not a flow balance
```
The column is labelled `sep_storage_gain_mcm` and rendered in the report table (`goal2_khundan_22y_baseline.py:167`) as "+98.86" etc., i.e. presented as a *flow-derived* quantity.

**Hydraulic & Data Science critique**

1. **`DMD_QUse_curr` does not close against the flow records.** Either it is not the storage volume, or there is unrecorded loss (evaporation, seepage, gauging error) of 2–8 % of September throughput. Either way the column is not what its name and its table presentation imply.
2. **`float(x or 0)` silently converts missing data into real zeros.** `:82-83` uses `float(r.get("DMD_Inflow_curr") or 0)`. The 2005 record shows `sep_outflow_mcm = 0.00` — for a reservoir at 97 % of capacity that filled from 99.32 MCM of September inflow with zero recorded release. That is almost certainly a **data gap**, not a physical zero. Nothing in the artifact records how many days were imputed.
3. **Compounding effect on the headline.** `HANDOFF.md:76` reports *"น้ำเกิน 100% เพียง 9 ใน 22 ปี (40.9%)"* and the 36.5-day anomaly — both derived from the same unreconciled series.

**Proposed solution**

- Either (a) close the balance and report the residual per year as a data-quality column, or (b) drop `sep_storage_gain_mcm` from the report table entirely until reconciled.
- Replace `or 0` with an explicit count:
```python
def _sum_field(rows, key):
    vals = [r.get(key) for r in rows if r.get(key) not in (None, "")]
    return sum(map(float, vals)), len(rows) - len(vals)   # sum, n_missing
```
and surface `n_missing` per year in the artifact.

---

### [F-06] / [F-07] CP2 headline sensitivities — both drivers are unsourced literals

**Location** `analysis/goal7_counterfactual_simulation.py:79-87` (`dq_dh_m2s = 1100.0`), `:122` (`safe_cap_ayutthaya = 2600.0`).

**Empirical evidence — stage reduction vs. `dQ/dh`** (ΔQ = 582.9 m³/s, the 2011 peak reduction):

| `dQ/dh` (m²/s) | implied `dH` | basis |
|---|---|---|
| 600 | **0.971 m** | channel-only (≈375 m × 1.6 m/s) |
| **1,100** | **0.530 m** | **the assumed value** |
| 2,200 | 0.265 m | — |
| 3,300 | 0.177 m | — |
| 5,000 | 0.117 m | wide-plain B_eff ≈ 3,300 m × 1.5 m/s |

**Span: 0.12 m – 0.97 m, i.e. 8×.** The 0.53 m figure is the least-constrained choice in the range, not a calibrated one. The code's own comment (`:85`) says *"ค่า 1,100 เป็น 'สมมติฐานที่เขียนไว้' ไม่ใช่ค่าสอบเทียบ"* ("1,100 is a written assumption, not a calibrated value") — correct, and not reflected in any headline.

**Empirical evidence — share-of-excess vs. `safe_capacity`** (full re-run of `simulate_event`):

| `safe_cap` (m³/s) | diverted (MCM) | excess (MCM) | **share** | `dH` (m) |
|---|---|---|---|---|
| 2,200 | 5,109.9 | 15,165.4 | 33.7 % | 0.53 |
| 2,400 | 4,732.6 | 13,169.7 | 35.9 % | 0.53 |
| **2,600** | **4,394.5** | **11,325.1** | **38.8 %** | **0.53** |
| 2,800 | 4,092.6 | 9,643.2 | 42.4 % | 0.53 |
| 3,000 | 3,742.6 | 8,068.0 | 46.4 % | 0.53 |
| 3,100 | 3,579.6 | 7,332.2 | 48.8 % | 0.53 |

`safe_capacity_ayutthaya_cms = 2600.0` drives **both** the diversion trigger (`:50-56`) and the `excess_mcm` denominator (`:67-68`), with no source in the repository. **Share spans 33.7 %–48.8 %: the headline carries ±5–10 pp of undocumented uncertainty.** Note the stage reduction is *insensitive* to `safe_cap` (0.53 m throughout) because the peak always saturates the canal — that one is robust, and is the only CP2 number that is.

**Proposed solution**

Publish all CP2 results as a 2-D envelope — `dQ/dh` ∈ [600, 5000] × `safe_cap` ∈ [2200, 3100] — with the point estimate marked. Register the Ayutthaya cross-section in `analysis/goal7/gaps.json` as **blocking** for any stage-reduction claim.

---

### [F-08] The compound flood risk matrix is outside the canonical contract entirely

**Location** `analysis/compound_flood_risk.py` (whole file); publication at `index.html:199, 233`.

**Empirical evidence**

```
$ grep -c "compound" analysis/canonical_numbers.json analysis/goal6/canonical.json analysis/goal7/canonical.json
analysis/canonical_numbers.json:0
analysis/goal6/canonical.json:0
analysis/goal7/canonical.json:0

tests/ coverage: only tests/test_naming_convention.py:37 (a filename allowlist entry)
```

Every threshold is a literal: `:73-80` (2.00 / 2.40 / 2.70), `:126-129` (metadata `floodwall_crest_msl_m: 2.80`). Every coefficient is a literal: `:45-46` (`c1 = 0.132`, exponent `1.28`). The module is linked from the public portal but has **no canonical home, no retired-ledger entry, and no numeric test**.

**Hydraulic & Data Science critique — the matrix is structurally near-degenerate**

With `H = tide + 0.08 + 0.132·(Q/1000)^{1.28}` over the declared grid (`q_range` 1500–4000, `tide_range` 1.40–2.50):

| Contribution to total H spread | Range | Share |
|---|---|---|
| Tide | 1.10 m | **67 %** |
| Discharge term | 0.222 → 0.764 m = 0.54 m | 33 % |
| **Total** | **1.64 m** | |

Consequence: **the risk classification is essentially a tide ladder.** At the grid minimum Q = 1,500 m³/s the stage already sweeps 1.70 → 2.80 m — i.e. all four risk classes are reachable at *zero* change in river discharge. The "compound" claim is not supported by the formulation; the model cannot express genuine compound interaction because it is additive by construction.

**Dimensional / physical critique of the exponent**

`c1·(Q/1000)^{1.28}` is dimensionally unsound as a *backwater head*: it has units of metres only because `c1` carries them, and it is anchored at an arbitrary reference `Q = 1000 m³/s` that has no hydraulic meaning. An exponent of **1.28 > 1** means stage grows *faster* than discharge. For a natural alluvial channel the stage–discharge exponent is typically **0.3–0.5** (strongly sublinear); values approaching or exceeding 1 arise only in flat, floodplain-dominated delta reaches. No cross-section, no rating curve, and no multi-year fit supports 1.28 here. The docstring (`:36-40`) is admirably honest — *"ไม่มีสคริปต์สอบเทียบและไม่มี artifact ของการ fit ใน repo"* ("no calibration script and no fitting artifact in the repo") — and names the exact file that would be needed: `analysis/compound_flood_risk_calibration.py`.

**Calibration is circular.** The one available observation (2026: Q = 2,250, tide = +1.91, observed 2.24 m) yields a computed 2.36 m — **+12 cm bias**, disclosed at `:104`. The 2011 case (Q = 3,750, tide = +2.35 → 3.15 m) uses an input the limitations array itself flags as *"เป็นค่าประมาณ ไม่มีแหล่งอ้างอิงใน repo"* ("an estimate with no source in the repository"). Then a CP2 counterfactual is presented (`:113-119`) as evidence **for** CP2 — advocacy generated by an uncalibrated model, on a synthetic discharge decrement of −600 m³/s.

**Threshold alignment (audit brief item 2).** `critical_threshold = 2.70` against `floodwall_crest_msl_m = 2.80` leaves **10 cm of freeboard**; the narrative at `:143` says crest is "2.80–3.00 m" while `:126` stores a single `2.80`. Two further problems:

- **Category error.** C.12 Samsen is a *river gauge inside the channel*. Assigning a "Bangkok floodwall overtopping" class from an interior river stage requires a rating curve from the gauge to the relevant floodwall reach. None is supplied. The same error recurs in `report/assets/portal_map.js:85`, which labels C.12's `bankfull` as *"2.80 ม.รทก. (สันคันกั้นน้ำ กทม.)"* — a floodwall crest is not a river bankfull stage.
- **Wave setup is a constant.** `wave_setup_m = 0.08` for every cell and every hour (`:30`), while the project's own EIA-cited figure (source class A) gives upper Gulf of Thailand wave heights of **0.4–1.2 m** — 5–15× the assumed setup.

**Proposed solution**
1. Register in `goal6/canonical.json` with a `definitions` block and `calibration_status: "uncalibrated"`; add a numeric test.
2. Replace the dead `levels` at `:157` (see F-19).
3. Refit `c1` and the exponent against the multi-year C.12 + Bang Tai record the project already holds (`data/30_national_warehouse/`, 199 stations × 2020–2026) — this gap is closeable and would remove the single largest weakness.
4. Until refitted, remove the 2011 and CP2 counterfactual rows from the published matrix; an uncalibrated model must not be used to advocate for or against a capital project.

---

### [F-09] HANDOFF.md asserts two completions that did not occur

**Location** `HANDOFF.md:19` and `HANDOFF.md:46`.

**Empirical evidence**

```
Claim 1 (HANDOFF:19): "อัปเดต analysis/build_canonical_numbers.py เชื่อมโยงผล 1D Routing
                       (Bankfull 666.3 และ 617.4 cms) · Rebuild รายงานที่ 1 (ประชาชน)
                       และ รายงานที่ 2 (วิชาการ) ผ่านการตรวจสอบ canonical 100%"

  $ grep -n "routing_1d" report/build_expert_report.py report/build_report_html.py
    -> no matches (only the word "routing" in unrelated prose about the lumped model)
  $ grep -c "666.3\|617.4\|3\.25" report/น้ำท่วมนครนายก2569_{วิชาการ,ประชาชน}.html
    -> 0 / 0
  BUT: analysis/canonical_numbers.json → values.routing_1d EXISTS (6 keys)

Claim 2 (HANDOFF:46): "บูรณาการ: ผสานเข้า analysis/goal7_analysis.py, analysis/goal7/canonical.json,
                       และเรนเดอร์ในรายงานฉบับประชาชนและวิชาการเรียบร้อยแล้ว"

  $ grep -n "counterfactual" analysis/goal7_analysis.py   -> :1377-1379 (canonical folded in) ✅
  $ grep -rn "counterfactual_simulation" report/          -> no matches                    ❌
  $ grep -c "38\.8" report/คลองเจ้าพระยา2_{ประชาชน,วิชาการ}.html -> 0 / 0
```

**Hydraulic & Data Science critique**

Both claims follow the pattern *"canonical wired up ✅ + rebuild reports ✅"* when only the first half was done. The cause is almost certainly the reports-1–2 hold (`AGENTS.md`: *"รายงาน 1–2: hold ยกเลิกแล้ว"*) — but the goal7 reports are **not** on hold, so claim 2 is simply unexecuted.

Why this matters despite the favourable exposure outcome:

1. **HANDOFF.md is the entry point for the next session** and is explicitly a tested document. An auditor (or agent) reading it will believe three unvalidated models are embedded in the published reports and will waste effort re-deriving them, or worse, cite them as published.
2. **No test bridges canonical → published artifact.** `test_docs_carry_current_anchor_values` (`:122-142`) checks **6 anchors** in `HANDOFF.md` and `docs/GOAL6_PLAN.md`, covering `rain_national`, `flood_peak_km2`, and `c2_attribution` only. Nothing anchors the routing, L3, or counterfactual values anywhere.
3. **The canonical ledgers now hold numbers that no published document and no builder references** — canonical keys that are simultaneously "official" and inert.

**Proposed solution**

```python
# tests/test_canonical_is_rendered.py
CANON = {"analysis/canonical_numbers.json": [...],
         "analysis/goal6/canonical.json":    ["l3_coastal_coupled", ...],
         "analysis/goal7/canonical.json":    ["counterfactual_simulation", ...]}
BUILDER_SRC = [*glob("report/build_*.py"), *glob("report/goal6_build_*.py"),
               *glob("report/goal7_build_*.py"), "report/assets/portal_map.js"]
for key in CANON: assert key appears in at least one builder source
```

Then correct HANDOFF:19 and :46 to state "canonical พร้อมแล้ว · ยังไม่เรนเดอร์ในรายงาน" until the render exists.

---

### [F-10] The public interactive portal carries a retired figure and a contradicted observation

**Location** `report/assets/portal_map.js:86` and `:100`.

**Empirical evidence**

```javascript
// portal_map.js:86
peak: "2.12 ม.รทก. (ปลาย ก.ย. 69)",          // C.12 Samsen

// portal_map.js:100
desc: "ขอบเขตทะเลหนุนที่ใช้ในโมเดล L3 Coastal Model เพิ่มความแม่นยำพยากรณ์ขึ้น 47.7%",
```

Cross-checks:
- C.12 observed peak, recomputed from the raw hourly series: **`max = 2.24 m`**. Corroborated by `compound_flood_risk.py:104` (*"สูงกว่าค่าโทรมาตรจริง 2.24 ม."*). **`2.12` is a 12 cm understatement of the project's own headline gauge.**
- `47.7 %` matches **no** current value. Canonical L3 values are 51.2 / 41.8 / −1.9 / +3.2. The prior review at `docs/reviews/AUDIT_REDTEAM_2026-10-17.md:24` records 47.7 % as superseded (*"76.3→39.9"*). **`portal_map.js` was never updated.**

**Hydraulic & Data Science critique**

`report/assets/portal_map.js` is a **published, client-side artifact** — it is exactly the file the project's own canonical contract should govern hardest, because it is not generated by a builder and so has no drift test. It is the single place in the repository where (a) a retired figure and (b) a value contradicted by primary data are both publicly visible, and it does so on the C.12 and CPY015 cards — the two stations a reader would use to judge Bangkok flood risk.

**Proposed solution**

Add `report/assets/portal_map.js` to the builder-scan set in F-12; source `peak` from `goal6/canonical.json → event_stations`; delete the `47.7%` string.

---

### [F-11] Risk-band colours fail the project's own WCAG rule

**Location** `analysis/compound_flood_risk.py:158, 161-165`; also `goal7_counterfactual_simulation.py:220, 232`.

**Empirical evidence** — WCAG 2.1 contrast ratios, computed from the sRGB values actually rendered (fills composited at the α specified in code over white):

```
compound_flood_risk.py risk bands (contourf alpha = 0.85), threshold ≥ 3.0 for data marks
  #2ecc71  normal/safe     raw 2.31:1   composited 2.06:1   FAIL
  #f1c40f  watch           raw 1.77:1   composited 1.63:1   FAIL  (worst)
  #e67e22  warning         raw 3.35:1   composited 2.77:1   FAIL
  #e74c3c  critical        raw 4.78:1   composited 3.83:1   pass

goal7_counterfactual_simulation.py diverted-volume fill (alpha = 0.30)
  #2ecc71  composited rgb(192,240,212)   contrast 1.30:1    FAIL — effectively invisible
```

For contrast, the CP2 panel's line colours all pass (`#27ae60` 3.39, `#c0392b` 7.80, `#2980b9` 5.78, `#d35400` 5.41). And `hydraulic_1d_routing.py`'s `#e67e22` bank-level dash at **2.85:1** and `#3498db` fill at 3.15:1 are borderline/marginal.

**Hydraulic & Data Science critique**

AGENTS.md §7 states the rule plainly: *"องค์ประกอบข้อมูล (แท่งกราฟ/เส้น/พื้นที่) ≥ 3.0"*. **Three of the four risk bands fail**, and critically the two that fail worst are **"normal/safe" (2.06:1)** and **"watch" (1.63:1)** — precisely the distinction a reader must make to decide whether protective action is needed. A colour-blind or low-vision reader, or anyone viewing a projected screen or a printed grayscale copy, cannot separate "safe" from "watch".

The CP2 case is worse in kind: the green fill is the **only** visual encoding of the 4,394.5 MCM diversion — the component's single headline — and at 1.30:1 it is effectively invisible on white. (The number does survive in the legend text, which limits but does not eliminate the problem.)

**Proposed solution**

```python
colors = ["#1b7f3b", "#8a6d00", "#b34700", "#a12020"]   # all ≥ 4.5:1 on white
ax.contourf(..., levels=[...], colors=colors, alpha=1.0)  # no alpha wash
```
Add an automated assertion to the test suite computing contrast from the source palette, so this cannot regress.

---

## 4. Verified Invariants (Passed Spot-Checks)

Each item below was verified by direct execution or exhaustive search, not by reading documentation.

| # | Invariant | Verification method | Result |
|---|---|---|---|
| V-01 | Unified verification runner passes | `python tools/verify_all.py` | 4/4 steps green |
| V-02 | Test suite passes | `python -m pytest tests/ -q` | 129 passed / 10.04 s |
| V-03 | Catalog completeness | `python catalog.py check` | 97/97 entries exist |
| V-04 | Raw-data integrity | `verify_data_integrity.py --quick` | OK 2892 · **MISMATCH 0** |
| V-05 | Thai language lint (typo registry, collision patterns, cross-doc consistency) | `pytest tests/test_thai_language_lint.py -q` | 10/10 passed |
| V-06 | PDPA compliance | `pytest tests/test_privacy.py -q` + regex scan of `report/*.html`, `portal_map.js`, `index.html` for phone/ID patterns | 2/2 passed; **zero** phone-like strings found |
| V-07 | **No look-ahead leakage in the L3 model** | Line-by-line trace of `goal6_l3_coastal_model.py:136-192`; confirmed `leak_flags = (t_lead >= test_start)` and `train_mask = (~test_flags) & (~leak_flags)`; all 13 features are at or before `t_curr` | **No leakage found.** Purge logic is correct and conservative |
| V-08 | Key metrics are **not** hardcoded in report builders | Exhaustive regex search of 7 builder sources for `666.3 · 617.4 · 486.9 · 3.25 · 4394.5 · 11325.1 · 38.8 · 0.53 · 0.35 · 73.6 · 35.9 · 51.2 · 0.132 · 1.28 · 1100` | **Zero matches.** All sourced from canonical JSON |
| V-09 | Phantom basin-wide figures genuinely retired | Repo-wide search for `7.37`, `1.62 ม`, `43 กม` across `analysis/ report/ docs/ HANDOFF.md START_HERE.md` | Absent (only coincidental digits inside `dam_history_all.json`) |
| V-10 | Rating-curve envelope inversion is sound | Recomputed naive vs upper-envelope branch across Q ∈ [300, 750] | Bias ≤ **1.6 cm** — negligible. **Mechanism accepted** |
| V-11 | Canonical↔artifact mirroring holds | `test_standards_integrity.py:170-197` | Passes (drift detection working) |
| V-12 | Waterchart overlay methodology | Read `goal7_waterchart_overlay.py:105-186` | Strong: distinguishes `cross_km` (16.82, all fragments) from `interval_sum_km` (16.2, ≥50 m only); 100–300 m **shift sensitivity**; 5 km buffer share; two different scope measures (`nn` 35.7 km / `all` 144.2 km) |
| V-13 | Pasak 24 y storage definitions | `analysis/goal6/pasak_24y_summary.json → metadata.storage_definitions` | **Exemplary.** Separates normal conservation (871.5 MCM, +42.0 m) / surcharge pool (→1,036.16 MCM, +43.0 m) / emergency freeboard (>1,036.16, +44.5 m) with the explicit caveat *"ไม่ใช่การล้นข้ามสันเขื่อน"* ("not dam overtopping"). Directly satisfies audit Dimension 5 item 1 |
| V-14 | National reservoir index denominator hygiene | `goal6_national_medium_reservoirs_summary.json → metadata.missing_data_note` | Correct: 22 dams with no data excluded from **every** denominator (n_assessed = 439), with the prior bug documented |
| V-15 | Legal/defamation framework is correctly scoped | `docs/LEGAL_REVIEW.md:9-11, 20, 53-56, 79` | Critique is directed at systems/procedures, not individuals; the one named individual (`:20`) is a public academic quoted with a public source (Thai PBS, 28 Sep) — compliant with AGENTS.md §PDPA; `data/manual/*` participant names correctly excluded from git |
| V-16 | CP2 2026 "real data" claim is **not** made in the artifact | `goal7/counterfactual_simulation_summary.json:7` | Metadata correctly states `"SYNTHETIC — ทั้งสองเหตุการณ์"`. ⚠️ But the **code comment** at `:128-129` still says *"ข้อมูลจริง ปี 2569"* and cites C.2 peak 2,610 + Pasak 500 m³/s — while the code actually generates peak **2,980** m³/s from `1600 + 1380·sin(t)^2.2`. **The comment contradicts the code** |

---

## 5. Information Gaps & Required Field Data

These are parameters that **cannot currently be audited** because the primary data are not in the repository. Each is listed with the specific finding it blocks.

### 5.1 Blocking gaps (a finding cannot be closed without these)

| Gap | Blocks | Source required |
|---|---|---|
| **Ayutthaya cross-section (stage–discharge geometry)** | F-06 — the 0.53 m headline spans 0.12–0.97 m on `dQ/dh` alone | RID/กช. surveyed section or a calibrated rating curve at C.2 / S.4 |
| **Independent `n` for the Ny.1B section** | F-01, F-15 — `n = 0.0437` is annotated as Ny.7-calibrated but applied to Ny.1B with a different slope | Recalibration against observed (Q, H) pairs at both stations |
| **Intermediate cross-sections between Ny.1B (km 9.2) and Ny.7 (km 27.5)** | F-02 — the 12 "sub-reaches" are 12 copies of one averaged trapezoid; no intermediate geometry exists | `data/19_rid_cross_sections/` currently holds only the two end sections |
| **Multi-year C.12 stage + Bang Tai (C.29A) tide record** | F-08 — `c1` and the 1.28 exponent are unfitted; refitting would remove the model's largest weakness | **Already partially available**: `data/30_national_warehouse/` holds 199 stations × 2020–2026 |
| **Real 2011 Ayutthaya inflow hydrograph (C.13 + S.26)** | F-04, F-07 — the 2011 case runs on a half-sine reconstruction; `Q = 3,750` and `tide = +2.35` are flagged in the artifact as unsourced | RID historical discharge records |
| **CP2 gate opening/closure log + invert elevations** | F-04 — gate closure is unrepresentable (efficiency floor 0.80 vs EIA-cited 88 % reduction) | Project operating records; `docs/GOAL7_FOI_REQUESTS.md` |
| **Gate-criteria numeric values at the Pasak–Gulf outlet** | F-04 — HANDOFF:288 records the *existence* of the criterion (elev. > +17.00) but not the numbers | EIA 2569 appendices; still open per HANDOFF:288 |

### 5.2 Non-blocking but material gaps

| Gap | Consequence |
|---|---|
| **Hourly SWAN wave series** for the test window | Model is Tidal-Coupled only; `:173-176` and `:249` are correct to say so, but `:6` and `compound_flood_risk.py:8` still claim SWAN is an input (F-20) |
| **Upstream station BKK001 record past 2026-10-02 15:00** | Cause of the 57.1% test coverage (F-18); blocks any +24/+48 h conclusion |
| **BKK006 annual file and `mask_sea.npy`** | Recorded as unexplained at HANDOFF:273; **not** in the current MISSING list — appears resolved. Close the HANDOFF note |
| **Siphon/culvert invert levels (34 crossings)** | HANDOFF:288 records these as still open; affects whether the canal can actually pass 600 m³/s |
| **Ground slope slips (5 surveyed points)** | HANDOFF:288 open; bears on the 3.2–4.8 m embankment finding |
| **Flood-levee-freeboard geometry at Bangkok** | F-08 — the 2.80 m crest and the 10 cm critical-threshold margin cannot be assessed without per-reach crest elevations |

### 5.3 Items I could not verify

- `review_coverage` / whether EIA 2569 appendices contain a dam-overtopping plan. HANDOFF:288 records concern #11 (no overtopping/embankment-breach plan found) as checked against volumes 1–2 and appendices — I did not re-verify this, as it depends on OCR output (`analysis/goal7_ocr_scan.py`) I did not re-run.
- Reproducibility of the full Goal 6 pipeline. `python analysis/goal6_build_all.py --with-analysis` requires ~42.8 GB of Sentinel-1 COG scenes on disk; I verified the *outputs* and the canonical mirroring, not a full end-to-end re-run. Within audit scope (read-only), I did not regenerate any artifact.

---

## 6. Priority Remediation Sequence

Ordered by (severity × tractability). Items 1–4 require no new data and can be completed immediately.

| # | Action | Effort | Addresses |
|---|---|---|---|
| 1 | Fix `HANDOFF.md:19` and `:46` to state "canonical พร้อมแล้ว · ยังไม่เรนเดอร์" | 5 min | F-09 |
| 2 | Delete the retired `47.7%` string; correct C.12 peak `2.12 → 2.24 m` in `portal_map.js` | 10 min | F-10 |
| 3 | Update `HANDOFF.md:84` to 20.27% and add `19.3%` to `goal6/canonical.json → retired` | 10 min | F-13 |
| 4 | Replace the compound-flood and CP2 palettes; add a contrast test | 1 h | F-11 |
| 5 | Withdraw `3.25 h`, `666.3`, `617.4` from all prose; publish the 2.92 h hand-check and the 9.0 h storage interpretation | 2 h | F-01, F-02 |
| 6 | Switch `stage_to_discharge` default to `divided`; add a monotonicity gate; recalibrate `n` per section against observed pairs | 4 h | F-01, F-15 |
| 7 | Add the "canonical key must be referenced by ≥1 builder" test; extend literal scanning to all 7 builders + `portal_map.js` | 3 h | F-12 |
| 8 | Replace the de-tided metric in the L3 model; publish the aliasing table; add `test_samples_common` and imputation counts | 4 h | F-03 |
| 9 | Register `compound_flood_risk` in `goal6/canonical.json` with a `definitions` block; remove the uncalibrated 2011/CP2 rows from the published matrix | 2 h | F-08 |
| 10 | Fix the Khun Dan mass balance or drop the column; replace `or 0` with explicit missing-day counts | 3 h | F-05 |
| 11 | Replace the monthly cosine with a real semidiurnal gate schedule + intake submergence constraint | 6 h | F-04 |
| 12 | Submit the FOI requests that unblock 5.1; register the Ayutthaya cross-section as a blocking gap | — | F-04, F-06, F-07 |
| 13 | Move to HEC-RAS 1D (material already available per HANDOFF:238) | 2 d | F-02 |

---

## 7. Closing Assessment

The repository's **verification infrastructure is sound and honestly maintained**; its **science in the three newest components is not yet sound**. The central governance risk is not fabrication — it is **promotion without propagation**. In all three cases the analysis author recorded the disqualifying caveat in the script, and the caveat stopped there. `hydraulic_1d_routing.py:356-357` forbids citing the travel time; `goal7_counterfactual_simulation.py:154-155` admits the gate model is wrong; `compound_flood_risk.py:36-40` admits there is no calibration. The scripts then wrote those results into canonical ledgers, and `HANDOFF.md` presented them as delivered and integrated into the reports.

The highest-leverage structural fix is **#7 in the remediation sequence**: a test asserting that every canonical key is consumed by a builder, and that no builder or portal asset contains a value absent from canonical. That single test would have caught three of the four High-severity findings (F-09, F-10, F-12) and would have prevented a retired figure from reaching a published page.

Two findings deserve emphasis because they cut against the audit brief's framing, and I want them on the record:

- **There is no temporal data leakage in the L3 model.** The purge logic at `:184`/`:192` is correct. The defect is the *metric*, not the *split*.
- **The phantom 43 km / 7.37 h / 1.62 m-s figures really are gone**, and the `levee_crest_*` vs `terrace_onset_*` split the project added is the right instinct — it simply was not carried into the key names.

And one finding cuts in the project's favour, against the brief's implicit assumption: **none of the three defective results reached the published reports.** `666.3`, `617.4`, `3.25`, `4,394.5`, `11,325.1` and `38.8` are absent from all six published HTML reports. The scientific claims a general reader actually consumes are considerably better supported than `HANDOFF.md` implies.

---

**Audit scope:** `analysis/hydraulic_1d_routing.py` · `analysis/goal6_l3_coastal_model.py` · `analysis/compound_flood_risk.py` · `analysis/goal7_counterfactual_simulation.py` · `analysis/goal6_pasak_24y_baseline.py` · `analysis/goal6_national_medium_reservoirs.py` · `analysis/goal2_khundan_22y_baseline.py` · `analysis/goal7_waterchart_overlay.py` · three canonical ledgers · seven report builders · `report/assets/portal_map.js` · `tests/` (129 cases) · `tools/verify_all.py`.

**Compliance:** All findings are directed at water-management systems, operational rules, design assumptions, and physical infrastructure. No individual public servant is criticised; no personally identifiable information appears in this report. Read-only throughout: no file was modified, no commit made, no destructive command executed.

**Confidence:** High for all findings backed by an executed command shown above (F-01, F-02, F-03, F-04, F-05, F-06, F-07, F-09, F-10, F-11, F-13, V-01…V-16). Medium for F-08 (formulation critique is sound; the underlying intent of the 1.28 exponent cannot be determined without the author). Low for F-21 (needs the national-reservoir capacity definition to confirm whether "over 100%" is surcharge or overtopping — the defect is the *absence* of a documented definition, which is verified regardless).