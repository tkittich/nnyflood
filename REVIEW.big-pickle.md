# Red-Team Audit — `nnyflood` (flood investigation repo)

- **Model / author:** big-pickle (`opencode/big-pickle`)
- **Date:** 2026-10-17
- **Commit audited:** `464551b` — *fix(audit): the retired-value guard had never run; repair it and fix what it exposes*
- **Scope:** independent, evidence-based review across 6 dimensions — (1) 1-D hydraulic routing, (2) coastal-coupled ML, (3) compound flood risk, (4) counterfactual simulation, (5) reservoir baselines, (6) canonical/code standards.
- **Method:** read-only inspection + numeric reproduction in a scratch dir (`C:\Users\theera\AppData\Local\Temp\opencode`); no repo files were written except this review. Commands run: `python tools/verify_all.py`, `python -m pytest -q`, `python catalog.py`-helpers, targeted `grep`/`python -c` against the three canonical files and the raw SWOC data.
- **Evidence discipline:** every claim cites a verified `file:line`, a canonical JSON field, or exact command output. Thai text is quoted verbatim.

> This review is written to be read on its own. It does **not** repeat prior audits; where a prior finding was checked, the result is stated. Two of my own intermediate hypotheses were **falsified during verification** and are noted as such (see `F-11` and the coastal persistence item) — they are recorded so the next auditor does not re-chase them.

---

## Executive Summary

**Overall.** The core numbers that reach the public reports are, for the most part, traceable to the three canonical files, and the repo's own guard-rails (SHA-256 integrity, Thai-language lint, canonical-anchor tests) are unusually strong for a project of this size. The headline hydrological narratives are defensible in direction.

**The single blocking fact.** The working tree **does not currently pass its own test suite**:

```
FAILED tests/test_standards_integrity.py::test_all_top_level_docs_are_registered
1 failed, 128 passed in 10.27s
```

`catalog.unregistered_docs()` returns two root Markdown files left behind by **other audit sessions**: `REVIEW.GLM-5.3-flash-free.md` and `REVIEW.space-bunny-free.md`. The repo's contract is *"ไฟล์ใหม่ต้องลงทะเบียนหรือย้ายออกจากพื้นที่"* (no allowlist) — so any audit that drops a `REVIEW.*.md` at root and does not register it in `catalog.py` **breaks the build**. This review file (`REVIEW.big-pickle.md`) has the same obligation and I could not register it without violating the read-only mandate; see `F-01` and *Information Gaps*.

**Highest-risk substantive findings (ranked):**

1. **`F-02` (High):** the inland L3 model that feeds Report 3 (`analysis/goal6_l3_model.py`) has **no label purge** and **selects the model on the test set** — the coastal sibling does both correctly. The favourable Report-3 skill figures are therefore optimistic in a way the coastal model is not.
2. **`F-03`/`F-04` (Medium-High):** the coastal-coupled model carries a **perfectly collinear feature** (rank deficiency 1) and reports a `+6h` gain (`+51.2%`) against a **persistence baseline that is anomalously weak at that horizon** — the gain disappears at `+24h` (`−1.9%`) and `+48h` (`+3.2%`).
3. **`F-08` (Medium):** `analysis/compound_flood_risk.py` is **orphaned and uncalibrated** — nothing in the repo reads its output, it is in no canonical file, yet `docs/PROJECT_MAP.md` advertises it as the canonical source for a Report-3 analysis.

**What is solid.** Canonical values sampled agreed with their builders; the 1-D routing output **is** in `canonical_numbers.json` and **is** rendered (contrary to my initial hypothesis); the coastal and counterfactual results **are** in their canonical files. Legal/PDPA posture is clean (no private-individual data; the one named person is a public academic, cited).

---

## Findings Matrix

| ID | Dimension | Finding (short) | Evidence | Severity | Confidence |
|----|-----------|-----------------|----------|----------|------------|
| F-01 | standards | Working tree **fails pytest**: 2 unregistered root docs left by other audits | `catalog.unregistered_docs()` → `['REVIEW.GLM-5.3-flash-free.md','REVIEW.space-bunny-free.md']`; `tests/test_standards_integrity.py:64-75`; command output `1 failed, 128 passed` | **High** | Certain |
| F-02 | coastal/inland ML | `goal6_l3_model.py` has **no purge** and picks the model by **test RMSE** → Report-3 optimism | `analysis/goal6_l3_model.py:185` `best = min(rows, key=lambda r: r["rmse_cm"])`; no leak/purge logic (contrast `goal6_l3_coastal_model.py:183-192`) | **High** | High |
| F-03 | coastal ML | Perfect multicollinearity: `tide_head = tide0 − h0` is a linear combination of features already present | `analysis/goal6_l3_coastal_model.py:166` + feature list `:177` (`tide0`) + `:159` (`h0`) → rank deficiency 1 | Medium-High | High |
| F-04 | coastal ML | `+6h` improvement (`+51.2%`) is inflated by a tide-aliased persistence baseline; skill ~0 at 24/48h | `analysis/goal6/canonical.json → l3_coastal_coupled.horizons`: 6h persistence 61.8 cm vs 24h 21.2 vs 48h 37.6; improvements +51.2 / −1.9 / +3.2 % | Medium-High | High (numbers) / Medium (interp.) |
| F-05 | coastal ML | Single-season training; test window truncated; declared ≠ actual | canonical `l3_coastal_coupled.metadata`: `test_coverage_pct: 57.1`, `train_window_actual: 2026-07-01..2026-09-19`, `test_window_actual: 2026-09-20..2026-10-02 13:00` | Medium | High |
| F-06 | 1D routing | Grid **non-convergence** — RMSE worsens with refinement; result is not the physical answer | canonical `routing_1d.grid_convergence`: `n_sub_6` RMSE_q 126.4 → `n_sub_12` 128.8; note `"ไม่ลู่เข้า"` | Medium (disclosed) | High |
| F-07 | 1D routing | Simulated travel time **3.25 h** vs observed stage lag **9.0 h** (≈2.8×) | canonical `routing_1d.routing_performance`: `travel_time_hours_sim: 3.25`, `travel_time_stage_obs: 9.0` | Medium | High |
| F-08 | compound risk | `compound_flood_risk.py` **orphaned + uncalibrated**; PROJECT_MAP claims canonical status | no reader anywhere (`grep` — only self, `tests/test_naming_convention.py:37`, docs); absent from all 3 canonical files; `compound_flood_risk_summary.json.metadata.calibration_status = "ยังไม่สอบเทียบหลายปี..."`; `docs/PROJECT_MAP.md:62` | Medium | High |
| F-09 | counterfactual | Synthetic hydrographs, **no tidal lockout**, spring–neap comment wrong, and result **canonicalised but unpublished** | `analysis/goal7_counterfactual_simulation.py:116,118-119`; `counterfactual_simulation_summary.json.metadata.limitations[0]`; `analysis/goal7_analysis.py:1377-1379`; no report builder references it | Medium | High |
| F-10 | reservoir | Pasak: stated max capacity `1,036.16` MCM is **exceeded** by the record peak `1,177.22` MCM | `analysis/goal6_pasak_24y_baseline.py:26` vs `:120` (and canonical `pasak_24y_baseline.record_peak_mcm: 1177.22`) | Medium | High |
| F-11 | reservoir | Medium-reservoir md says **`10–15%` of large dams**; canonical metric is **7.05%** (and the md's other percentages do match) | `analysis/goal6/national_medium_reservoirs_report.md:58` vs `analysis/goal6_canonical.py:359` → `national_medium_reservoirs.ratio_to_large_dams_cap_pct: 7.05` | Medium | Medium |
| F-12 | standards | Metric **literals hard-printed in the Report-3 builder**; the guard only bans a tiny whitelist | `report/goal6_build_report3_draft.py:380,402,765` (`67/199`, `32/99`, `151/199`, `2,264`); guard `tests/test_goal6_consistency.py:102-119` | Medium | High |
| F-13 | standards | Text colour `#78909c` ≈ **3.35:1** on light backgrounds (< 4.5 AA); **no automated contrast test** exists, yet two reports display an AA badge | `report/build_report_html.py:265,293`; `report/report_assets.py:432`; shipped `report/น้ำท่วมนครนายก2569_ประชาชน.html:216,244`; badges at `report/คลองเจ้าพระยา2_วิชาการ.html:247`, `report/ชุดเทียบมาตรฐาน2554.html:90`; `ls tests/ | grep contrast` → ∅ | Low-Medium | High |
| F-14 | standards | Builder ↔ shipped-HTML **terminology drift**; chart/asset scripts are outside every literal test | `report/build_report_html.py:265` says `ม.เกจ` but shipped `report/น้ำท่วมนครนายก2569_ประชาชน.html:216` says `ม.ตามมาตรวัด`; `report/report_assets.py`, `report/make_x_charts_thai.py` unscanned | Low | High |
| F-15 | standards | Name collision: `counterfactual` means two different things in two canonical files | `analysis/canonical_numbers.json → values.counterfactual` (Nakhon Nayok spillway measures) vs `analysis/goal7/canonical.json → counterfactual_simulation` (Chao Phraya-2 canal) | Low | High |
| F-16 | 1D routing | Two coexisting Ny.1B "bankfull capacity" definitions (666.3 vs 244.6) | canonical `routing_1d.ny1b_hydraulics.levee_crest_capacity_q_cms: 666.3`; historical rating 244.6 documented in `analysis/build_canonical_numbers.py` | Low-Medium | High |

---

## Deep-Dive Technical Findings

### D1 — Coastal-coupled model: collinearity and a fragile headline (`goal6_l3_coastal_model.py`)

The model targets `C.12` (สามเสน) with tide input from `CPY015`. Feature construction:

```
145:            h0 = target_data[t_curr]
159:            feat_base = [h0, h0 - h1, h0 - h3, h0 - h6, u0, u0 - u6, u0 - u12, r24]
162:            tide0 = tide_data[t_curr]
166:            tide_head = tide0 - h0  # ความชันระดับน้ำปากอ่าวเทียบระดับน้ำในแม่น้ำ (ตรวจ Backwater)
177:            feat_coastal = feat_base + [tide0, tide_diff, tide_head, tide_phase_sin, tide_phase_cos]
```

Because `tide0` and `h0` are already columns, `tide_head = tide0 − h0` is an **exact linear combination** of existing features → the design matrix has **rank deficiency 1**. For an ordinary-least-squares linear model this does not change fitted predictions, but it makes the `tide_head` coefficient unidentifiable and its standard error infinite; any narrative that reads a "backwater" coefficient off this model would be reading noise. The check should either drop one of `{h0, tide0, tide_head}` or use a ridge/regularised fit and say so.

Second, the reported skill is fragile:

| lead | persistence RMSE | linear base | linear coastal | Δ |
|------|------------------|-------------|----------------|---|
| +6 h | **61.8 cm** | 73.6 | 35.9 | **+51.2 %** |
| +24 h | **21.2 cm** | 20.3 | 20.6 | −1.9 % |
| +48 h | **37.6 cm** | 34.9 | 33.8 | +3.2 % |

(all from `analysis/goal6/canonical.json → l3_coastal_coupled.horizons`)

The persistence baseline is **non-monotonic** (61.8 → 21.2 → 37.6 cm) because the tidal signal is semi-diurnal (≈12.42 h): a 6-hour-ahead "hold the last value" guess is nearly anti-phase, while a 24-hour guess is nearly the same phase again. So the `+51.2 %` improvement at `+6h` largely reflects a *deliberately weak* baseline, not strong coastal skill. At the horizons where persistence is fair, coastal coupling is worth ~0 (and slightly negative at 24 h). **Recommendation:** report a **tide-aware persistence** baseline (`ĥ(t+lead) = h(t) + tidal_component(t+lead) − tidal_component(t)`), or report all three horizons side by side and state that the benefit is confined to short leads.

Governance context (not an error): the builder **does** purge training rows whose label falls in the test window — `:183` comment and `:192 train_mask = (~test_flags) & (~leak_flags)` — and the metadata declares the narrow window honestly (`l3_coastal_coupled.metadata.purge_note`, `train_scope_note`). The model is fine as an exploratory result; it should not be used as evidence of general coastal predictability.

### D2 — Inland L3 model feeds Report 3 with leakage-class optimism (`goal6_l3_model.py`)

This is the most consequential finding because its output (`l3_best`) is published.

- **No purge.** The file contains no `leak`/`purge` logic at all (grep for `purge` in `analysis/goal6_l3_model.py` → ∅), unlike its coastal sibling which explicitly guards label leakage. Any training row whose target `t+lead` lands inside the evaluation window is used for training.
- **Model selection on the test set:**

```
185:        best = min(rows, key=lambda r: r["rmse_cm"])
186:        print(f"  {bid} +{h}ชม.: ดีสุด {best['model']} RMSE {best['rmse_cm']} ซม. ...")
```

`rows` are scored on the test split, and the minimum is then reported as the result (`canonical.json → l3_best`). Selecting the model that minimises test error and reporting that same test error is a well-known optimistic bias.

- **Target/period:** `:40 "bkk_lower": ("C.13", "ท้ายเขื่อนเจ้าพระยา", "C.22A")`; the model trains 2020–2026.

Held against `F-04` (where the sister model purges and discloses), Report 3's forecast-skill claims are the weakest link. Note also the same "fine at short lead, ~0 later" pattern in `l3_best` (e.g. `bkk_lower.h6` skill 0.299, `h24` 0.344, `h48` 0.317 vs persistence — but with a purged, tuned baseline these should be recomputed).

### D3 — 1-D routing: honest but non-answer (`hydraulic_1d_routing.py`)

Three independent issues, all already partly disclosed by the author:

1. **Grid non-convergence (`F-06`).** `routing_1d.grid_convergence` shows `rmse_q_cms` rising from 126.4 (n_sub=6) to 128.8 (n_sub=12); the canonical note is explicit: *"RMSE ไม่ลดลงเมื่อแบ่งช่วงย่อยละเอียดขึ้น → ผลที่ n_sub=12 เป็นค่าที่ 'พอดี' ไม่ใช่ค่าที่ลู่เข้า · ห้ามอ้างว่าเป็นคำตอบเชิงกายภาพ"*. Good disclosure; the risk is any downstream text that quotes a routing number as if it were converged.
2. **Travel-time gap (`F-07`).** `routing_performance.travel_time_hours_sim = 3.25` vs `travel_time_stage_obs = 9.0`. The build acknowledges the caveat (`travel_time_caveat`: *"ใช้ยอด *ระดับน้ำ* เป็นหลักเท่านั้น · q_cms ... ยอด Q เหลื่อมจากยอด H"*). The near-3× gap means the model under-represents floodplain storage/attenuation on the Ny.1B→Ny.7 reach.
3. **Non-monotonic rating (`F-16`).** The composite conveyance `A_total·(A/P)^(2/3)` folds as stage rises (documented at `:52-57`), so "bankfull capacity" is a **local maximum**, not a monotone limit; the code handles this with an upper envelope (`:230`, `:241`) and publishes *both* composite and divided methods as an uncertainty range (`:248`, `:350`). The canonical `ny1b_hydraulics.levee_crest_capacity_q_cms = 666.3` accordingly coexists with a historical-rating value `244.6` captured in `analysis/build_canonical_numbers.py`. Two different physical definitions share one concept name — acceptable only because both are documented; keep them from being quoted interchangeably.

**Good news (falsified hypothesis):** I initially suspected the routing results were orphaned. They are **not** — they are in `analysis/canonical_numbers.json → values.routing_1d` and rendered via tokens (`ny1b_*`, `ny7_peak_*`, `cf_ov_*`) in `report/build_report_html.py` and `report/build_expert_report.py`.

### D4 — Compound flood risk is orphaned and uncalibrated (`compound_flood_risk.py`)

`analysis/compound_flood_risk.py:34` defines:

```
H_C12 = H_tide + wave_setup + c1 * (Q / 1000)^1.28      # c1 = 0.132, wave_setup = 0.08
```

The file's own summary is candid:

- `metadata.calibration_status = "ยังไม่สอบเทียบหลายปี — ค่าสัมประสิทธิ์เป็นการตรวจความเป็นไปได้จาก 2 จุด"`
- `limitations[0] = "สมการบวกกันตรง ๆ: ∂H_C12/∂H_tide = 1.0 ทุกสภาวะ และไม่มีพจน์ปฏิสัมพันธ์ Q×tide ..."` — i.e. **no Q×tide interaction**, so the "compound" effect is additive by construction, not modelled.
- `limitations[2]` flags the 2554 inputs (`Q=3,750`, `Tide=+2.35`) as unsourced.

The decisive problem is **consumption**. A repo-wide search finds **no reader**: no report builder, no test, no canonical file. It appears only in `catalog.py`, `index.html`, docs, and the naming test's core list. Yet `docs/PROJECT_MAP.md:62` lists its canonical source as *"`analysis/compound_flood_risk_summary.json`"* and names *"รายงาน 3"* as an output. **That documentation claim is false as of this commit.** Either wire it in (and add the Q×tide term + calibration) or mark it clearly as a non-published exploratory module.

### D5 — Counterfactual simulation: synthetic, no lockout, canonical-but-unpublished (`goal7_counterfactual_simulation.py`)

- **Synthetic by declaration.** `metadata.hydrograph_source = "SYNTHETIC — ... สร้างจากฟังก์ชันไซน์ + สุ่มปรกติ (seed 42) ไม่ใช่ข้อมูลวัดจริง"`, with `limitations[2] = "... ห้ามอ่านเป็น hindcast ของปี 2554"`. Honest, but it means the `4,394.5` MCM / `38.8 %` / `0.53 m` figures are outputs of an assumed wave, not evidence.
- **No tidal lockout.** `limitations[0]`: *"ไม่มีช่วงที่ประตูปลายคลองปิดเพราะน้ำทะเลสูงกว่าผิวน้ำในคลอง (tidal lockout) — ประสิทธิภาพถูกจำกัดต่ำสุดที่ 0.80–0.84 ไม่เคยเป็น 0"*. So the gate is never shut — the optimistic case for a diversion canal.
- **Comment/period error (`F-09`).** `:118` comment says *"น้ำเกิดรอบ 15 วัน"*, but `:119 tide_eff_54 = 0.92 + 0.08*np.cos(np.linspace(0, 8*np.pi, n_days_54))` makes **8π over 122 days = 4 cycles ≈ 30.5-day period** (the spring–neap cycle), not 15 days. The 2569 block (`:137`, `2π over 31 days`) is a 1-month cycle. A code comment that mis-states the modelled period is a trap for a future editor.
- **Canonical but unpublished.** `analysis/goal7_analysis.py:1377-1379` attaches the summary to `canonical.json → counterfactual_simulation`, yet **no** builder in `report/goal7_*.py` references it (grep → ∅). So it is "blessed" as canonical while reaching no reader. Combined with `F-15` (name collision with `canonical_numbers.json → counterfactual`), the label "counterfactual" is currently ambiguous and half-wired.

### D6 — Reservoir baselines: partial-year bias and a capacity contradiction

- **Khun Dan 22-year baseline (`goal2_khundan_22y_baseline.py`).** `CAPACITY = 224.0` (`:25`). The canonical record shows 2026 contributes only **288 of 365 days** (`annual_records[2026].total_days = 288`, peak `2026-09-27`), and earlier years also have gaps (2017: 90 missing days; 2016: 33; 2015: 17 — derived from `annual_records[*].total_days`). The claim at `:156`, *"... เป็นปรากฏการณ์ที่ **เกิดขึ้นเพียง 2 ครั้งในรอบ 22 ปี**"*, mixes a truncated-observation year with full years; the September-peak month distribution is the metric most exposed to this asymmetry because a truncated 2026 cannot contribute an Oct/Nov peak. Cite the per-year `total_days` whenever the "N in 22 years" style claim is made.
- **Pasak contradiction (`F-10`).** `:26 MAX_CAP = 1036.16` is described (`:109`) as *"ช่องความจุหน่วงน้ำหลากวิกฤต (Surcharge Storage) 871.5–1,036.16"*, i.e. the top of the design range — but the same file reports a historical peak of **1,177.22 MCM** (`:120`, `:153`, and canonical `pasak_24y_baseline.record_peak_mcm`). A "maximum" that is exceeded by 141 MCM is an internal inconsistency, most likely because `MAX_CAP` is the *surveyed/declared* surcharge ceiling while the historical reading is a different datum. State the distinction explicitly.
- **Medium reservoirs (`F-11`).** `national_medium_reservoirs_report.md:58` says the 461 medium dams total *"10–15% ของเขื่อนใหญ่"*, while the machine-produced metric is `ratio_to_large_dams_cap_pct = 7.05` (`goal6_canonical.py:359`). **Note the falsified hypothesis:** the same md's `106–108%`/`101%` for ทรายทอง/คลองวังบอน (`:29`) are **correct** — canonical gives peak_pct 107.7 and 101.6 respectively — so the md is not uniformly stale; only the `10–15%` figure is unreconciled.

### D7 — Canonical & code standards

- **`F-01` — failing build.** `tests/test_standards_integrity.py::test_all_top_level_docs_are_registered` asserts `catalog.unregistered_docs()` is empty; it currently returns `['REVIEW.GLM-5.3-flash-free.md', 'REVIEW.space-bunny-free.md']`. `catalog.py` already registers the *earlier* review files (`:179-180`), so the mechanism works — the two newer files simply were not added. **Any audit file written to root must be registered or moved.**
- **`F-12` — metric literals in a builder.** `report/goal6_build_report3_draft.py` prints raw metrics inside prose strings: `:380 "...67 จาก 199 จุดวัด (= 32 จาก 99 ช่อง...)"; :402 "...(2,264 ตร.กม.)"; :765 "...151 จาก 199 จุด..."`. The guard `tests/test_goal6_consistency.py:102-119` bans only a fixed whitelist (`1.7`, `224.34`, `241`, `164 วัน`, `127 วัน`, `−0.92`, …) and scans only `goal6_build_report3_draft.py` / `goal6_build_report4_draft.py`. So the AGENTS rule *"builder ห้ามพิมพ์ตัวเลข metric เป็น literal"* is enforced only against previously-regressed values, not in general.
- **`F-13` — contrast.** `#78909c` = rgb(120,144,156) → relative luminance ≈ 0.263 → contrast vs white ≈ **3.35:1** (below the WCAG AA 4.5:1 for normal-sized text). It is used for reader-facing text in `build_report_html.py:265,293`, `report_assets.py:432`, and ships in `น้ำท่วมนครนายก2569_ประชาชน.html:216,244`. There is **no** automated contrast test (`ls tests/ | grep -Ei 'contrast|access|wcag'` → empty), even though `คลองเจ้าพระยา2_วิชาการ.html:247` and `ชุดเทียบมาตรฐาน2554.html:90` display *"✓ ความเปรียบต่างสีผ่านเกณฑ์ WCAG AA"*. Recommend a unit test that computes contrast for every `color:`/`background:` pair against the AGENTS threshold.
- **`F-14` — drift & untested assets.** `build_report_html.py:265` says `ม.เกจ`; the shipped `ประชาชน.html:216` says `ม.ตามมาตรวัด`. Same sentence otherwise — so the shipped HTML is not regenerated by the current builder (or is produced by another pipeline). Meanwhile `report/report_assets.py` and `report/make_x_charts_thai.py` are scanned by **no** consistency test.
- **`F-15` — name collision.** "Counterfactual" denotes two unrelated analyses across two canonical files (see `D5`); a cross-file test that keys on the bare word would be ambiguous.

---

## Verified Invariants (things I checked and that hold)

- **Integrity.** `tools/verify_all.py`: catalog check OK; **SHA-256 MISMATCH 0**; integrity tests pass. (The only failing test is `F-01`, unrelated to data integrity.)
- **Routing output is canonical and rendered.** `canonical_numbers.json → routing_1d` exists and `ny1b_*`/`ny7_peak_*`/`cf_ov_*` render tokens are consumed by `report/build_report_html.py` and `report/build_expert_report.py`. *(This falsifies the "routing is orphaned" hypothesis.)*
- **Coastal and counterfactual are canonicalised.** `goal6/canonical.json → l3_coastal_coupled` and `goal7/canonical.json → counterfactual_simulation` both exist and match their builders' outputs.
- **Coastal model purges correctly.** `goal6_l3_coastal_model.py:183-192` implements label-window purging and declares the narrow training scope.
- **Medium-reservoir percentages (ทรายทอง/คลองวังบอน) match canonical** (107.7 / 101.6 vs md "106–108%" / "101%"). *(Falsifies a checkpoint hypothesis; recorded here to prevent re-reporting.)*
- **Thai-language lint suite passes** (`tests/test_thai_language_lint.py`, part of the 128 passing).
- **Privacy/legal posture clean on inspection:** `tests/test_privacy.py` passes; no private-individual personal data found; the only named person is a public academic cited to a public source; a juristic entity is named per official record.

---

## Information Gaps (open / unverifiable from the repo)

1. **No tide-aware baseline** exists for the coastal model, so the true, fair skill of coastal coupling (beyond `+6h`) is unknown. Provide or the `+51.2%` claim should be withdrawn.
2. **`compound_flood_risk` inputs are unsourced** (`limitations[2]`: 2554 `Q=3,750`, `Tide=+2.35`), and the model has **no Q×tide interaction** — the "compound" claim is not yet demonstrated.
3. **Gate-operation / dam despatch history** (บาน/เดินเครื่อง) is absent from every API (`report/goal6_build_report3_draft.py` states attribution can only be daily). This caps the achievable causal resolution.
4. **Missing reservoir-days** (Khun Dan 2017: 90; Pasak 2017: 93, etc.) were not re-derived here; the `N in 22/24 years` statistics depend on how those gaps are treated.
5. **Counterfactual simulation reaches no report** (canonical but unpublished) — its `4,394.5` MCM figure cannot be cross-checked against any published narrative.
6. **`REVIEW.big-pickle.md` (this file) is unregistered** and, per the read-only mandate, I did not edit `catalog.py`. Left as-is it will add a third entry to `F-01`'s failing set. **Follow-up:** add `REVIEW.GLM-5.3-flash-free.md`, `REVIEW.space-bunny-free.md`, and this file to `catalog.CORE_GOVERNANCE`, or move all root `REVIEW.*.md` under `docs/reviews/`.

---

*End of review. No repository files were modified other than adding this file; no commit, push, or destructive command was executed.*
