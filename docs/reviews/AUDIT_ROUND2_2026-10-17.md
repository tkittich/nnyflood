# Red-Team Audit — Round 2 (Delta Review)

**Commit reviewed:** `bc2a95d` — "audit: remediate red-team technical findings F-01 to F-10 across Pillars 1-3"
**Previous audit:** `.workbuddy-ai/audit/AUDIT_REDTEAM_2026-10-17.md` (2026-10-17)
**Method:** re-derived every claim from the new artifacts; re-ran the L3 model logic independently; diffed canonical ledgers against their source JSONs.
**Verification state:** `catalog.py check` 84/84 · `pytest tests/ -q` **120 passed** · `verify_data_integrity --quick` MISMATCH 0 (37 MISSING / 3 DELETED are the pre-existing disk-only raw files, unchanged by this commit).

---

## 1. Verdict

**Two findings are genuinely fixed. Three are partially fixed. Five of the ten claimed findings were not touched at all.**

The two real fixes are good work — the rainfall loader now reads the actual schema, and the CP2 figure titles are now rendered from JSON instead of typed. Both were the highest-value items in my report.

But the commit message overstates the outcome, and one change has left the canonical ledger **stale relative to its own artifact** while all 120 tests stay green. That is a new regression, and it is the more serious of the new findings because it silently breaks the project's core invariant.

| Status | Count | Findings |
|---|---|---|
| Fixed | 2 | F-02, F-08 |
| Partial | 3 | F-01, F-05, F-06 (+ F-11 outside the claimed range) |
| Untouched | 5 of 10 claimed | F-03, F-04, F-07, F-09, F-10 |
| Untouched (beyond F-10, not claimed) | 9 | F-12…F-20 |
| New | 4 | N-01…N-04 |

---

## 2. What Is Actually Fixed (verified)

### F-02 — Rainfall feature: FIXED

`analysis/goal6_l3_coastal_model.py:82-99` now resolves the nested schema. Re-executing the new loader:

```
keys loaded: 279
20260926 -> 147.03
```

Previously: 0 keys, feature identically 0.0. The dead feature is alive.

**The recomputed numbers are internally consistent.** I independently replicated the full feature pipeline and reproduced the published values exactly:

| Horizon | Published (new) | My replication |
|---|---|---|
| +6 h base / coastal | 72.3 / 36.7 | 72.3 / 36.7 |
| +24 h base / coastal | 18.3 / 18.6 | 18.3 / 18.6 |
| +48 h base / coastal | 32.9 / 32.3 | 32.9 / 32.3 |

`analysis/goal6/canonical.json` and `analysis/goal6/l3_coastal_summary.json` agree field-by-field at all three horizons (checked programmatically, zero diffs). `HANDOFF.md` was updated to 72.3 / 36.7 / 49.3%. That chain is clean.

**Bonus fix I had not flagged:** `:171-175` replaces hour-of-day with elapsed-hours for the tidal phase. The old `sin(2π·hour/12.42)` had a ~25° phase discontinuity at every midnight (24 h is not a multiple of 12.42 h). Genuine improvement.

### F-08 — CP2 figure titles: FIXED

`:199` and `:211` now use `f"{res_54_600['total_diverted_mcm']:,.0f}"` instead of the hardcoded 3,695 / 756. The PNG was regenerated. Verified: no remaining literal `3,695` or `756 ล้าน` anywhere in `analysis/`.

---

## 3. What Is Partially Fixed

### F-01 — Brief still carries the unsupported figures

`HANDOFF.md:39` was rewritten to scope the claim honestly:

> "ความเร็วคลื่นน้ำหลาก 1.62 ม./วินาที ในลำน้ำธรรมชาติ: ระยะทางรวมทั้งลุ่มน้ำ 43 กม. ใช้เวลาเคลื่อนตัว 7.37 ± 0.8 ชม. … และช่วงสถานีหลัก Ny.1B สู่ Ny.7 (18.3 กม.) … คำนวณเวลาเคลื่อนตัวของยอดคลื่นได้ 3.25 ชม."

That resolves the 43 km vs 18.3 km confusion I raised. Good.

But the **review prompt itself is unchanged** — `docs/REVIEW_PROMPT_EN.md:18,63` still presents `1.62 m/s` and `7.37 ± 0.8 h` as properties of the 18.3 km reach. Anyone reusing that prompt will re-derive the same false premise. And neither 1.62 m/s nor the "6–8 ชม. lag histogram" now cited in `HANDOFF.md:39` is produced by any script — `grep -rln "1.62"` across `analysis/*.py` and `*.json` returns no celerity computation, and no lag-histogram artifact exists. The claim is better scoped but still unbacked.

### F-05 — Docstring exponent fixed, calibration comments still wrong

`:34` now reads `^1.28`, matching `:40`. But `:36-38` still asserts:

```
เมื่อ Q=2,500 และ Tide=+2.00 ม. -> H_C12 ≈ +2.42 ม.     (actual 2.5065)
เมื่อ Q=3,500 และ Tide=+2.30 ม. -> H_C12 ≈ +2.82 ม.     (actual 3.0361)
```

The second anchor is still 21.6 cm off. The comment was left behind again.

### F-06 — One status string fixed, the contradiction survives

`:105` was corrected from "2.84 ม." to a `critical` description — that row is now right. But the CP2 row at `:107-113` is untouched:

```
"c12_stage_msl_m": 2.7306
"status": "ลดระดับน้ำลงเหลือ 2.73 ม. ช่วยพ้นภาวะวิกฤตล้นคัน"
```

2.73 > 2.70 = `critical`. The row still claims to escape the band it is inside. The undamped tide term (∂H/∂tide ≡ 1.0) and the missing Q–tide interaction are also unchanged.

### F-11 — Better numerics, same estimator

The routing is now 12 sub-reaches (`n_sub=12`), which is the correct stability fix, and a stage-based lag was added. New output:

```
travel_time_hours_sim   3.25   (was 2.0)
travel_time_stage_obs   9.00   (new)
travel_time_hours_obs  24.25   (unchanged)
rmse_stage_cm         105.8    (was 106.9)
rmse_discharge_cms    128.78   (was 126.13 — slightly worse)
q_peak_sim_cms        613.0    (was 578.7, obs 648.3)
```

Subdividing improved the peak (578.7 → 613.0) but not the RMSE. `argmax` is still the estimator — cross-correlation (10.75 h, r = 0.94) was not adopted. The model still has no lateral inflow and no floodplain, and 105.8 cm RMSE against a ~0.8 m event range still means no stage skill.

**New evidence that all three travel times are unreliable (see N-03 below).**

---

## 4. What Was Not Touched

### F-03 — SWAN is still a constant (unchanged)

```
swan n 31  mean 0.0968 m  timestamps {'2026-10-16'}
```

Still a single post-event snapshot collapsed to one scalar appended to every row. Zero variance, cannot contribute. The model's "coastal wave coupling" remains nominal.

### F-04 — Compound model still over-predicts the event by 33 cm

`c1 = 0.132` and the exponent are unchanged. `analysis/compound_flood_risk_summary.json` still reports:

```
"ระลอกปลาย ก.ย. 2569 (เหตุการณ์จริง)"  →  2.57 m
canonical observed C.12 peak          →  2.24 m
```

Still +33 cm, still one risk band too high, and the status string still says "แตะระดับเฝ้าระวัง" (watch) while 2.57 sits in the `warning` band. The tide input is still 2.12 m against an observed CPY015 peak of 1.91 m.

### F-07 — Synthetic hydrographs still labelled "actual"

`:194` and `:207` still read `label="น้ำหลากจริงปี 2554"` / `"น้ำหลากจริงปี 2569"` on series built from `np.sin()` + `np.random.normal` at `:102,105,123,124`. Only the *titles* were fixed (F-08); the *legends* still assert the curves are observed.

### F-09 — Tidal efficiency still 84–100%

`:108,126` unchanged. Still contradicts `report/goal7_build_public.py:576`, which states gravity diversion falls to 100 m³/s (17%) at peak tide. A 5× disagreement on the parameter that decides whether the canal works.

### F-10 — Ny.1B still has two canonical states

`analysis/build_canonical_numbers.py` was not touched:

```
:127  "bankfull_q_m3s": 244.6      ← vs r1d 666.3 at the same 10.60 m
:128  "peak_stage_msl": 11.23      ← vs telemetry 11.00
:129  "peak_q_m3s": 282.4          ← vs telemetry 675.3
:211  "r1d_ny1b_q_bankfull": ... 666.3
```

`analysis/canonical_numbers.json` still emits both `ny1b_q_bankfull = "244.6"` and `r1d_ny1b_q_bankfull = "666.3"`, and both are still in the `checks` lists at `:137,140`. The raw telemetry (675.3 m³/s @ 11.00 m) still contradicts the hand-typed block by 2.4–2.7×.

### F-12 … F-20 — unchanged

- **F-12** datum: `fetch_multistation_levels.py` still writes `level_msl_m` with no conversion; Ny.1B source still says `UseMSL: 0`.
- **F-13** Khun Dan: `goal2_khundan_22y_baseline.py:126` still hardcodes `"days_earlier_than_median": 40` (recomputed: 36.5); `:171` still claims an emergency spillway was opened, which the data schema cannot support.
- **F-14** capacity denominators: Pasak gained a `storage_definitions` block (good documentation), Khun Dan did not, and no number changed. The 9-vs-13-years sensitivity is still undocumented.
- **F-15** Pasak headline: still `days_over_normal: 86` / `max_outflow_mcm_day: 87.21` against computed `94` / `84.78`.
- **F-16** 22 null reservoirs still counted as "below 80%".
- **F-17** "East highest risk" still contradicts the composite column (North 73.9% vs East 40.7%); `q_info` units still unverified.
- **F-18** the three sub-4.5:1 palette tokens are still declared (still unused — still latent, not live).
- **F-19** metric literals still in `build_expert_report.py`.
- **F-20** no embargo before `test_start`.

---

## 5. New Findings Introduced by the Remediation

### [N-01] **High** — Canonical ledger is now stale relative to the routing artifact

**Location:** `analysis/canonical_numbers.json` → `values.routing_1d` vs `analysis/hydraulic_1d_routing_summary.json`

**Empirical Evidence.** `values.routing_1d` is a straight copy of the summary (`build_canonical_numbers.py:244`). The routing was re-run, the builder was not:

| Field | canonical_numbers.json | hydraulic_1d_routing_summary.json |
|---|---|---|
| `travel_time_hours_sim` | **2.0** | **3.25** |
| `rmse_discharge_cms` | **126.13** | **128.78** |
| `rmse_stage_cm` | **106.9** | **105.8** |
| `q_peak_sim_cms` | **578.7** | **613.0** |
| `metadata.n_subreaches` | absent | 12 |
| `travel_time_stage_obs` | absent | 9.0 |

**Critique.** This is a regression, not a pre-existing defect: the two files agreed before the commit. It is precisely the failure that `AGENTS.md` rule (4) forbids — "อัปเดตตัวเลขใด ๆ = รัน … จนจบ". The reason it slipped through is structural: **no test compares a canonical ledger against the artifact it copies.** `grep -rn "routing_1d\|travel_time" tests/*.py` returns nothing. All 120 tests are green while the ledger disagrees with its source in four fields.

This matters more than the individual numbers because `canonical_numbers.json` is what the report builders render from. Right now a report built from canonical would state 2.0 h while the model says 3.25 h.

**Proposed Solution.** Re-run `python analysis/build_canonical_numbers.py`, then add a generic invariant test:

```python
def test_canonical_mirrors_artifacts():
    c = json.load(open("analysis/canonical_numbers.json"))["values"]
    for name, path in {"routing_1d": "analysis/hydraulic_1d_routing_summary.json"}.items():
        assert c[name] == json.load(open(path)), f"{name} ledger drifted from {path}"
```

Apply the same pattern to every `values.*` block that is a copy rather than a computation.

### [N-02] **Medium** — Q and stage peak at opposite offsets at the two stations

**Location:** `data/20_multistation_levels/st61.csv`, `st62.csv`

**Empirical Evidence.** Within a single station, the reported discharge peak and the reported stage peak should coincide (a rating is a monotone function of stage). They do not, and the sign flips:

| Station | Q peak | H peak | Offset |
|---|---|---|---|
| Ny.1B (st61) | 2026-09-26 18:30 (675.3) | 2026-09-27 01:00 (11.00) | **+6.5 h** |
| Ny.7 (st62) | 2026-09-27 18:45 (648.3) | 2026-09-27 10:00 (7.68) | **−8.75 h** |

I checked whether this is a flat-top `argmax` artifact: it is not. The 1 cm plateau spans 1.75 h at st61 and 0.75 h at st62, far short of a 6.5–8.75 h offset.

**Critique.** A rating-derived discharge cannot peak 8.75 h *before* its own stage. Either the `q_cms` column is not derived from the local stage (different source, different timestamp convention, or a routed/modelled value), or one of the two series is shifted. Combined with F-10's observation that Ny.1B's Q reaches 2.5× the station's `QMax`, the most likely explanation is that `q_cms` is **not a gauged quantity at either station**.

This directly undermines the newly added `travel_time_stage_obs = 9.0 h` (HANDOFF now headlines it): that number is the difference between two series that are internally inconsistent in opposite directions, so it is not a wave travel time. The same objection applies to the retained `travel_time_hours_obs = 24.25 h`.

**Proposed Solution.** Before publishing any travel time, plot Q against H at each station for the event window. If the loop is not physically explicable, treat `q_cms` as derived and say so; compute travel time from stage only (both stations), via cross-correlation, and report the intra-station Q–H offset as a data-quality metric.

### [N-03] **Low** — The rainfall fix activated a small look-ahead path (measured: ≤0.9 cm)

**Location:** `analysis/goal6_l3_coastal_model.py:147`

**Empirical Evidence.** `r24 = rain_data.get(d_curr, 0.0)` uses the **full calendar-day total**. At 06:00 the feature contains rainfall from the following 18 hours, and the target at +6 h depends on part of it. While the feature was dead (F-02) this path did not exist; fixing F-02 switched it on.

I measured the effect by rebuilding the design matrix with a strictly causal trailing-24 h rainfall sum and re-running the same regressions:

| Horizon | Published (same-day total) | Causal trailing 24 h | Δ |
|---|---|---|---|
| +6 h base | 72.3 | 71.4 | −0.9 |
| +6 h coastal | 36.7 | 36.3 | −0.4 |
| +24 h coastal | 18.6 | 19.5 | +0.9 |
| +48 h coastal | 32.3 | 33.1 | +0.8 |

**Critique.** The leak is real but immaterial — under 1 cm at every horizon, because the model is dominated by the persistence and tide terms. I am reporting it as Low precisely because I measured it rather than assumed it. It should still be fixed, because the *next* feature added to this pipeline will not necessarily be so forgiving.

**Proposed Solution.** `r24 = sum(daily[d] for d in last_24h)` using only hours ≤ `t_curr`.

### [N-04] **Low** — Audit report committed twice, unregistered in the catalogue

**Location:** `AUDIT_REDTEAM_2026-10-17.md` and `docs/reviews/AUDIT_REDTEAM_2026-10-17.md`

**Empirical Evidence.** Byte-identical (`md5 9f865b88305f1c912ed12c4f47388d6c` both). `grep -c "AUDIT_REDTEAM" catalog.py` → **0**. `docs/PROJECT_MAP.md` was updated (+1 line), so registration was done in one of the three required places but not the others.

**Critique.** `catalog.py check` still passes 84/84 because it only verifies that *listed* entries exist — it does not detect unlisted files. So the project's "new reports must be registered in catalog.py, PROJECT_MAP.md and index.html" rule is only half-enforced. The repo-root copy is also an odd location for a document and will drift from the `docs/reviews/` copy the first time either is edited.

**Proposed Solution.** Keep one copy under `docs/reviews/`, delete the root duplicate, register it in `catalog.py`, and add a reverse check to `test_standards_integrity` (every `docs/**/*.md` must appear in the catalogue).

---

## 6. Updated Findings Matrix

| ID | Severity | Status | Note |
|---|---|---|---|
| F-01 | High | **Partial** | HANDOFF scoped correctly; `docs/REVIEW_PROMPT_EN.md` still wrong; 1.62 m/s and 6–8 h histogram still unbacked |
| F-02 | Critical | **Fixed** | Verified 279 keys; independently reproduced 72.3 / 36.7 |
| F-03 | High | **Open** | SWAN still one post-event scalar |
| F-04 | High | **Open** | Still 2.57 vs observed 2.24 |
| F-05 | High | **Partial** | Exponent fixed; both calibration anchors still wrong |
| F-06 | High | **Partial** | One row fixed; CP2 row still 2.73 > 2.70; physics unchanged |
| F-07 | Critical | **Open** | Legends still say `น้ำหลากจริง` on synthetic curves |
| F-08 | High | **Fixed** | Titles now f-string from JSON |
| F-09 | High | **Open** | Efficiency still 84–100% vs report's 17% |
| F-10 | Critical | **Open** | 244.6 vs 666.3 both still canonical |
| F-11 | High | **Partial** | 12 sub-reaches added; argmax retained; RMSE 105.8 cm |
| F-12 | Medium | Open | datum |
| F-13 | High | Open | 40 days; spillway claim |
| F-14 | Medium | Partial | Pasak documented; Khun Dan not; no numeric change |
| F-15 | High | Open | 86 vs 94; 87.21 vs 84.78 |
| F-16 | Medium | Open | 22 nulls as healthy |
| F-17 | Medium | Open | ranking + units |
| F-18 | Low | Open | latent WCAG |
| F-19 | Low | Open | builder literals |
| F-20 | Low | Open | no embargo |
| **N-01** | **High** | **New** | canonical ledger stale vs routing artifact (4 fields) |
| **N-02** | **Medium** | **New** | Q/H peaks inconsistent in opposite directions |
| **N-03** | **Low** | **New** | intra-day rain look-ahead, measured ≤0.9 cm |
| **N-04** | **Low** | **New** | duplicate audit file, unregistered |

---

## 7. What I Would Do Next, In Order

1. **N-01** — re-run the canonical builder and add the mirror test. This is a five-minute fix that closes the only *new* regression, and the test prevents the whole class.
2. **F-07** — change two legend strings. The numbers can stay synthetic; the word `จริง` cannot.
3. **F-10 / N-02** — settle the Ny.1B datum and the Q-vs-H question together; they are almost certainly the same root cause. Until then, mark Ny.1B discharge as derived.
4. **F-04 / F-06** — recalibrate the compound matrix on the two observed C.12 peaks and generate the band text from the classifier.
5. **F-13 / F-15** — delete the two hardcoded headline blocks.
6. **F-03 / F-09** — either source real time series or remove the features and say so.

**The systemic point, restated.** Round 1 found that every defect was a duplicated source of truth. Round 2 confirms it from the other direction: the one place where duplication was *introduced* (canonical vs artifact) is the one place no test looks. The project's canonical discipline is enforced for report prose but not for the ledger's own inputs — and that is where N-01 landed.
