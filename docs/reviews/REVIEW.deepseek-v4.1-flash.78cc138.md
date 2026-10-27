# Hydrological Audit & Red-Team Report: nnyflood

- **Auditor**: DeepSeek-V4.1-Flash, read-only session
- **Commit audited**: `78cc138` (working tree clean apart from the untracked `REVIEW.*.md` deliverables — four
  at repo root, plus one copy under `docs/reviews/`)
- **Date**: 27 Oct 2026
- **Brief**: `docs/REVIEW_PROMPT_EN.md` (13 dimensions)
- **Access constraint (state first, because it bounds everything below)**: a Security Center rule in this
  session denies read access to all seven `report/*.html` files. Consequences, which I did not work around:
  (a) `pytest` cannot collect — 11 modules name a report by literal path and several more glob
  `report/*.html`, and the four verification gates are drawn from exactly those modules; (b) Dimension 8
  (intra-/cross-report consistency) could only be audited at
  *builder* level, never against the rendered HTML. I ran 144 report-independent tests and they pass; I
  did **not** verify the reports themselves. Everything I report is reproducible from source, canonical
  JSON, PDFs, or the test subset I could run.

---

## 1. Executive Summary

- **Overall Scientific & Engineering Reliability: Medium–High.** The governance machinery (pre-registration,
  canonical ledgers, retired-value ledgers, gap register, two-layer literal gate) is real and mostly
  functioning — I re-verified commit order for eight pre-registration pairs and found no violation. The
  weak points are not the *process*, they are a small number of places where a number's definition has
  quietly drifted out of the ledger, and two places where the gates are weaker than they look.
- **Key System Strengths**
  1. Pre-registration discipline holds: every rule commit precedes its result commit (eight pairs traced,
     §5). The reference-scene audit was diagnostic-only before an owner decision changed published numbers.
  2. Provenance for the goal-7 source constants is verifiable: I re-read three `source_quote_verified`
     constants against the cited PDF text-layer pages and all three reproduce exactly (§5).
  3. The relative-orbit re-pairing of goal-6 Sentinel-1 scenes is internally coherent: no
     (basin, orbit) group mixes acquisition times, so the new pairing is not silently merging tracks (§5).
- **Critical Vulnerabilities**
  1. **The 88:12 attribution is a typed literal in the report and a ratcheted constant in the ledger, and
     the lag behind it is stored nowhere as data** (F-01). The report *does* print the 10–21 % band, so the
     reader is not misled — an earlier draft of this finding said otherwise and was wrong. What remains: no
     builder reads `dam_share`; the ledger asserts `round(p1_pct) == 12` in two separate files; the sustained
     window (60:40) is printed nowhere; and five documents disagree on whether the ratio is 88:12 or 12:88.
  2. **The two-layer literal gate is blind to negative numbers** (F-02). `-1.25 ม.` never matches; only the
     Unicode minus does. 35 signed-format placeholders in the builders can emit exactly that form.
  3. **`verify_all.py` records "could not run" as "fail" and writes it into a tracked file** (F-03). A run in
     an environment without dev dependencies stamped all four gates `fail` at HEAD.

---

## 2. Findings Matrix

| ID | Severity | Component / Target File | Root Cause Summary | Recommended Action |
|---|---|---|---|---|
| F-01 | **High** | `analysis/canonical_numbers.json` → `values.dam_share`; `analysis/build_canonical_numbers.py:305-308`; `tests/test_data_consistency.py:151-154`; `report/build_report_html.py:197` | 88:12 is a typed literal in the builders and an equality-asserted constant in the ledger; the 12 h lag behind it exists only as free text, P2 (60:40) is printed nowhere, and three docs write the ratio as 12:88 | Store `window`/`lag_h`/`lag_band` and rename to `dam_pct`/`rain_pct`; make builders read them; relax the ratchet to a band check; print the P2 split |
| F-02 | **Medium** | `tools/number_inventory.py:44,110` | `NUM_RE` lookbehind excludes a preceding `-`, so every ASCII-negative number with a unit is invisible to both layers | Handle an optional sign inside the pattern instead of excluding it |
| F-03 | **Medium** | `tools/write_verification.py:32-34,41` | `run_gate` maps any non-zero exit (including `No module named pytest`) to `fail`, then overwrites a tracked file | Distinguish `not_run` from `fail`; never write a `fail` that came from an environment error |
| F-04 | **Medium** | `analysis/goal7_ongkharak_2d_depression.py:55-56,62,73`; `analysis/goal7/dem_bias_correction.py:121-131` | The continuous correction compresses low-plain relief (0.13 m per 1 m of FABDEM below 1.6 m), so "95.6 % of the district" is an axis relabelling, not an independent result; the −3 m clip drops a different area per surface | State the relief compression explicitly; report each surface's own district area; note that the two corrected surfaces agree by construction |
| F-05 | Low | `analysis/goal7_analysis.py:270`; `analysis/goal7/canonical.json` → `extra_q.travel` | `canonical_value_km` 135.655 is written and never read; travel time uses 135.9, corridor uses 135.7 | Make the travel-time consumer read the reconciled value, or record why it uses the design length |
| F-06 | Low | `tests/test_tool_registry.py:49`; `catalog.py audit` | The audit deliverable at repo root fails the registry test, while `catalog.py audit` reports "all registered" for the same files | Register review files or move them to `docs/reviews/`; make the two registries share one file list |
| F-07 | Low | `docs/REVIEW_PROMPT_EN.md:20` | The brief quotes `36.5 days`, a value the repo lists in `canonical_numbers.json → forbidden` | Remove the value; cite the field name instead |
| F-08 | Low | `analysis/goal7_ongkharak_hydraulic_2d.py:236,253,215`; `report/goal6_build_report4_draft.py:389` | Hard-coded 0.367/0.321 bucket baseline with no computation behind it; dead `if True:`; static conclusion appended regardless of counts | Compute the baseline or label it; delete the dead branch; derive the sentence from `band_counts` |

---

## 3. Deep-Dive Technical Findings

### [F-01] The 88:12 headline is a typed literal in the report and a ratcheted constant in the ledger, and the lag behind it is not data

- **Location**: `analysis/canonical_numbers.json` → `values.dam_share`; `analysis/attribution_share.json`
  (`windows`, `lag_sensitivity`); `analysis/build_canonical_numbers.py:302-308`; `tests/test_data_consistency.py:150-154`;
  `report/build_report_html.py:197`; `report/build_expert_report.py:190`;
  `analysis/hydraulic_1d_routing_summary.json` → `routing_performance`.
- **Empirical evidence**
  - `canonical_numbers.json` holds exactly five fields:
    `{"p1_pct": 11.9, "p2_pct": 60.1, "p1_total_mcm": 38.8, "p2_total_mcm": 68.9, "p2_dam_mcm": 41.4}`.
    Nothing in the file says what P1/P2 are, what window they cover, or what lag was applied. The file has
    no `definitions` block at all (top-level keys are `forbidden, forbidden_exceptions, render, meta, values,
    checks`), while `analysis/goal6/canonical.json` does have one with 20 entries. `AGENTS.md` rule (6)
    requires exactly this ("ตัวเลขที่มีหลายนิยามต้องแยก field + จดนิยาม").
  - `attribution_share.json` supplies the missing context and shows why it matters:
    - P1 = 26 Sep 12:00–27 Sep 12:00, dam share 11.9 % (measured Q) / 12.6 % (rating curve);
    - P2 = 27 Sep 12:00–29 Sep 00:00, dam share **60.1 %** / 65.6 %;
    - `lag_sensitivity.pct_by_lag_h` for P1: 6 h → **29.3 %**, 9 h → **20.6 %**, 12 h → **11.9 %**,
      18 h → **10.3 %**. The file's own note reads "lag วัดจริง 9–18 ชม."
  - The routing summary reports the observed H→H lag at Ny.7 as 9.0 h
    (`routing_performance.travel_time_stage_obs: 9.0`).
  - **The report already carries the caveat, correctly.** `report/build_report_html.py:197` prints "มาจากเขื่อน
    เพียง ~12% (แกว่ง 10–21% ตามช่วงเวลาเดินทาง 9–18 ชม. ที่วัดได้)"; `report/build_expert_report.py:190`
    repeats the band and points the reader at `lag_sensitivity`; `OFFLINE_DATA_BACKLOG.md:128` (R6-17) records
    this as done. The band is **not** hidden from readers. An earlier draft of this finding claimed it was;
    that claim was wrong and is retracted here.
  - **What the report does not do is read the number.** A grep for `dam_share` finds consumers only in
    `analysis/build_canonical_numbers.py` (`:302`, `:368`) and `tests/test_data_consistency.py:150`. No report
    builder reads it. The "~12%", "10–21" and "9–18" in the two builders are typed literals. The ledger and the
    report are two independent statements of the same claim, and only one of them is checked.
  - **The ledger is ratcheted, without recording why.** `analysis/build_canonical_numbers.py:305-308` asserts
    `round(p1_pct) == 12`, `round(100 − p1_pct) == 88`, `round(p2_pct) == 60`, `round(100 − p2_pct) == 40`,
    under a docstring that calls them "inward data contracts"; `tests/test_data_consistency.py:151-154`
    repeats all four. If the lag basis were revised to the *measured* 9 h (20.6 %), both would fail with
    "สัดส่วนเขื่อน P1 ต้องปัดเศษได้ 12%" — a legitimate methodological revision would surface as a regression,
    because the assumption behind the constant is not in the file.
  - **P2 is printed nowhere.** Grepping `report/*.py` for `60.1` returns nothing: the sustained window, in
    which the dam supplies 60 % of the water, appears in no reader-facing text. `docs/REVIEW_PROMPT_EN.md:16`
    presents "88:12" as *the* attribution, so an external auditor has no way to learn that a second window
    exists and reverses the conclusion.
  - **The ratio's orientation is not stable.** `docs/REVIEW_PROMPT_EN.md:16` and `docs/PROJECT_MAP.md:214`
    write **88:12** (rain:dam — confirmed by `build_canonical_numbers.py:306`, which labels `100 − p1` as
    "สัดส่วนฝนตกหนัก"), while `docs/ANALYSIS_PLAN.md:107`, `docs/OFFLINE_DATA_BACKLOG.md:128` (R6-17) and
    `docs/reviews/TRIAGE_ROUND5_2026-10-18.md:177` write **12:88** (dam:rain). Five documents, two orders, no
    key that says which is which — because the fields are named `p1_pct`/`p2_pct`, not `dam_pct`/`rain_pct`.
- **Hydraulic & data-science critique**: the number itself is not wrong. 12 h sits inside the measured 9–18 h
  band, the report prints that band, and within it the dam share for the onset window is 10.3–20.6 %
  (79:21 to 90:10, same rain:dam order as the headline) — a factor of two, but a factor of two the reader is
  told about. What is wrong is the
  *representation*. One claim exists simultaneously as a free-text note in a JSON, as typed literals in two
  builders, as four equality assertions in two files, and in two opposite orderings across six documents —
  and in none of those places is the lag stored as data. In a project whose stated discipline is to write the
  analysis choice down before the result is seen, the choice that fixes the headline is the one thing absent
  from the ledger. The ratchet makes it worse rather than better: it converts a defensible assumption into a
  hard constraint that fails the build if anyone revises it, which is the opposite of what a pre-registration
  is for.
- **Proposed solution**: store the definition, not just the value —
  `dam_share = {"window": "P1_onset", "lag_h": 12, "lag_basis": "<why 12 h — e.g. midpoint of the measured 9–18 h band>", "dam_pct": 11.9, "rain_pct": 88.1, "lag_band_pct": {"6": 29.3, "9": 20.6, "12": 11.9, "18": 10.3}, "p2": {"window": "P2_sustained", "dam_pct": 60.1, "rain_pct": 39.9}}`.
  Rename the keys so the order is unambiguous; have both builders read `dam_pct` and `lag_band_pct` instead of
  typing them; replace the four equality assertions with a band check
  (`min(lag_band_pct.values()) <= dam_pct <= max(...)`) so revising the lag is a data change rather than a test
  failure; print the P2 split in Reports 1–2; and fix the three documents that write 12:88.

### [F-02] The two-layer literal gate cannot see negative numbers

- **Location**: `tools/number_inventory.py:44` (`NUM_RE`), `:110` (`extract`), `:114` (`RATIO_RE`).
- **Empirical evidence**: the pattern's lookbehind is `(?<![\w.,/\-:])`. A `-` immediately before the digits
  therefore suppresses the match. Run against the project's own regex:

  ```
  'ระดับต่ำกว่าเกจ 1.25 ม.'   -> ['1.25 ม.']
  'ระดับต่ำกว่าเกจ -1.25 ม.'  -> []            <-- ASCII hyphen: invisible
  'ระดับต่ำกว่าเกจ −1.25 ม.'  -> ['1.25 ม.']   <-- Unicode minus: caught
  'ลดลง 9.2%'                 -> ['9.2%']
  'ลดลง -9.2%'                -> []            <-- invisible
  ```

  `extract()` is the single entry point for layer A (same-quantity-different-value over reports and docs)
  and layer B (orphan numbers in reader text), so both layers inherit the hole. The reports render signed
  metrics through signed f-string fields (`f"{v:+.2f} ม."`) — I count **35** of them across the builders
  (`goal7_blocks.py` 27, `goal6_build_report4_draft.py` 4, `goal6_build_report3_draft.py` 3,
  `goal6_bp_downstream.py` 1), and the most sensitive published numbers are signed: `offset_vs_gauge_m`,
  `stage_diff_vs_original_m`, per-pass change percentages, DEM bias.
- **Critique**: the gate's stated purpose is "catch a number that does not match the JSON". A wrong *negative*
  number is precisely the failure mode the project has already suffered (the DEM offsets and the tide-gain
  sign flip in round 7), and it is the one class the gate cannot see. The round-7 addition of `ร้อยละ N`
  scanning closed the unsigned variant of the same hole; the signed variant remains.
- **Proposed solution**: replace the lookbehind exclusion of `-` with an explicit optional sign, e.g.
  `NUM_RE = re.compile(r"(?<![\w.,/:])([-−]?)(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?\s{0,2}(UNITS)…")` and
  carry the sign into `val`. Add a gate test asserting that `-1.25 ม.` and `−1.25 ม.` both produce a hit.

### [F-03] A verification badge that cannot distinguish "failed" from "could not run"

- **Location**: `tools/write_verification.py:32-34` (`run_gate`), `:41` (writes `report/assets/verification.json`).
- **Empirical evidence**: `run_gate` returns `"pass" if r.returncode == 0 else "fail"`. Running
  `python tools/verify_all.py` in an interpreter without the project's dependencies produced:

  ```
  ประทับผลตรวจ: {'thai': 'fail', 'contrast': 'fail', 'legal_privacy': 'fail', 'canonical': 'fail'} รุ่น 78cc138
  ```

  with the underlying cause being `No module named pytest` for each gate — no test ever executed. The file
  was rewritten (it is tracked) and the tree became dirty. I restored it with
  `git checkout -- report/assets/verification.json`. Separately, the committed badge still reads
  `git_rev: c8fb0b1, checked_at: 2026-10-27T13:45` while HEAD is `78cc138` (this reproduces F-05 of the
  Sonnet review; it is not new).
- **Critique**: the badge's contract, per the docstring, is "a gate with no result / not passing shows no
  tick". A reader of the HTML cannot distinguish "the Thai lint failed" from "the machine that stamped this
  had no pytest" — both render as a missing tick, and both are written to a file that is committed. Because
  `verify_all.py` is the project's own "definition of done" runner (`AGENTS.md`), a fresh clone without dev
  extras will stamp a red badge over a green one. The round-7 fix (ก6) correctly moved the badge from a
  constant to a computed value; it did not add a third state.
- **Proposed solution**: three-valued gate (`pass` / `fail` / `not_run`), where a non-zero exit whose stderr
  matches an import/collection error is `not_run`; render `not_run` as "ยังไม่ได้ตรวจในสภาพแวดล้อมนี้";
  refuse to overwrite a `pass` with `not_run` unless `--force`; and stamp the release commit at build time
  rather than at verify time.

### [F-04] Ongkharak: the continuous correction compresses the plain's relief, so "95.6 % at the observed stage" is an axis relabelling

- **Location**: `analysis/goal7_dem_bias_correction.py:109-131` (`monotone_knots`, `correct_monotone`);
  `analysis/goal7_ongkharak_2d_depression.py:55-56` (surface construction), `:62` (`dem >= -3.0` clip),
  `:73` (`median`), `:111-113` (`dem_sensitivity`); `analysis/goal7/dem_bias_correction.json` → `knots`.
- **Empirical evidence**
  - Knots: `x = [0.0, 1.64, 2.46, 3.68, 6.12, 10.37]`, `y = [0.1, 0.314, 0.776, 1.694, 4.292, 8.479]`.
    Segment slopes are 0.13, 0.56, 0.75, 1.07, 0.99 — the mapping is strongly compressive below 3.7 m:
    **a 1.64 m span of FABDEM (0 → 1.64) becomes 0.21 m of corrected height**.
  - Consequence at the observed gauge stage (2.35 m MSL): area flooded is 19.6 km² on raw FABDEM and
    490.1 km² on the corrected surface — a factor of 25 — while the median district height moves only
    3.09 → 1.25 m.
  - The two corrected surfaces agree almost exactly on every published figure: median 1.22 vs 1.25 m,
    area at gauge 492.2 vs 490.1 km², IoU 0.31 vs 0.33. `range_across_dems` (median 1.22–3.20 m,
    area 19.6–492.2 km², IoU 0.31–0.36) is therefore **two clusters, not four independent draws**: the
    stepped and continuous corrections both subtract ≈1.7–2.0 m in the 2–5 m band, so their agreement is
    a property of the construction, not corroboration.
  - The `dem >= -3.0` clip is binding and surface-dependent: implied district areas are 512.6 km²
    (corrected), 512.7 (stepped), 514.5 (Copernicus raw), 515.8 (FABDEM raw). The shares printed in
    `dem_sensitivity[*].area_at_gauge_share_pct` are computed against four different denominators.
- **Critique**: for a threshold-defined flood, a monotone height mapping leaves the *extent* invariant and
  only relabels the stage axis — the project says this correctly in Dimension 4's brief, and the IoU
  invariance (0.31–0.36 across all four surfaces) confirms it. But the headline number is not the IoU, it is
  "at the observed stage 95.6 % of the district is inundated". That number is *not* invariant: it is the
  direct arithmetic consequence of compressing 1.64 m of terrain relief into 0.21 m. Two things are missing
  from the text: (i) the correction's own residual uncertainty (EIA ground check MAE 0.64 m; leave-one-out
  corrected MAE 0.54–1.06 m, SD up to 3.08 m) is **larger than the compressed relief it produces**, so the
  hypsometric curve's 0.5 m rows are finer than the error they carry; (ii) because Ongkharak lies outside
  every DEMPro window, the compression factor itself is transferred, not measured. Reporting a four-surface
  range is honest, but it over-states the number of independent estimates and under-states why they differ.
- **Proposed solution**: (1) print the compression factor beside the curve caption ("ต่ำกว่า 1.6 ม. ค่าแก้
  บีบความต่างระดับเหลือ ~13 % — พื้นที่ที่ระดับหนึ่งจึงไวต่อค่าแก้มากกว่าความสูงจริง"); (2) report each
  surface's own district area next to its share so the denominators are visible; (3) replace "4 ชุด" with
  "2 กลุ่ม (ดิบ / ปรับแล้ว) × 2 วิธีปรับ"; (4) state that the two corrected surfaces agreeing is expected by
  construction. No model re-run is needed — this is a caption and prose change, so it does not collide with
  the pre-registration rules.

### [F-05] The reconciled canal length is written and never read

- **Location**: `analysis/goal7_analysis.py:270` (`"canonical_value_km": 135.655`);
  `analysis/goal7/canonical.json` → `extra_q.travel.length_km` (135.9), `corridor_area.length_km` (135.7),
  `provinces_km` (ends at 135.7).
- **Empirical evidence**: a repository-wide grep for `canonical_value_km` returns only the producer
  (`goal7_analysis.py:270`) — no builder, test or consumer reads it. `reconciled_parameters.canal_length`
  declares 135.655 canonical, explains that 135.7 is its rounding, and explains that 135.9 is the March-2565
  design length used for volume. That resolution does **not** cover the travel-time consumer, which silently
  uses 135.9 to produce "31–47 ชั่วโมง" (`extra_q.travel`).
- **Critique**: numerically this is 0.2 % and changes nothing at the printed precision. As governance it is
  the failure mode the reconciliation block exists to prevent: a canonical value that is displayed but not
  used, and a consumer that picks a variant without saying so. The reconciliation box
  (`report/goal7_blocks.py:1016-1052`) shows the reader "135.655 · 135.7 · 135.9 · 135.963" and a
  resolution that mentions 135.9 only in the volume context; a reader who then meets "31–47 ชั่วโมง" has no
  way to know which length it used.
- **Proposed solution**: either point `travel` at the reconciled value (and let the resolution say so), or
  add the length to the travel row's caption. Cheap test: assert that every `*_km` consumer's length equals
  one of the registered variants **and** names it.

### [F-06] The audit deliverable breaks the registry gate; two registries disagree

- **Location**: `tests/test_tool_registry.py:49`; `tools/doctor.py`; `catalog.py audit`.
- **Empirical evidence**: with the three round-8 reviews sitting at repo root, the one non-environmental test
  failure in my run was:

  ```
  AssertionError: เอกสารยังไม่ลงทะเบียนใน tools/registry.json:
  ['REVIEW.claude-sonnet-5.5.78cc138.md', 'REVIEW.gemini-3.8-flash.78cc138.md', 'REVIEW.glm-5.3-flash.78cc138.md']
  ```

  In the same tree, `python catalog.py audit` prints "✅ เอกสารทุกไฟล์ลงทะเบียนครบ (50 ไฟล์จาก *.md +
  docs/*.md)" and `python catalog.py check` passes 124/124. So one registry calls the tree clean and the
  other fails it, on the same files.
- **Critique**: `docs/REVIEW_PROMPT_EN.md` instructs auditors to write `REVIEW.<model>.<commit>.md` at repo
  root; `AGENTS.md` and `TRIAGE_ROUND7` §R7-33 record that reviews must live under `docs/reviews/` precisely
  because the registry test counts root `*.md`. The brief and the gate therefore contradict each other, and
  the contradiction lands on whoever follows the brief — including this file, which will make the count four.
  The deeper issue is that "registered" has two definitions in two tools with different scopes.
- **Proposed solution**: pick one registry (`tools/registry.json` is declared the single source of truth in
  `AGENTS.md`), make `catalog.py audit` read it, and either auto-register `REVIEW.*.md` or move the
  deliverable to `docs/reviews/` and update the brief.

### [F-07] The audit brief quotes a value the repository forbids

- **Location**: `docs/REVIEW_PROMPT_EN.md:20` ("Khun Dan 22-year operational baseline (36.5 days premature
  filling ahead of median)"); `analysis/canonical_numbers.json` → `forbidden` (contains `'36.5 วัน'`) and
  `values.khundan_22y.headline_metrics.year_2026_anomaly` (`days_earlier_than_median: 38.0`,
  `days_earlier_than_median_all22: 36.5`).
- **Empirical evidence**: the current headline is 38.0 (leave-one-out, SB F-22); 36.5 is retained only as
  `..._all22` for audit and is on the forbidden list. The brief prints it as the project's figure.
- **Critique**: the brief is the one document every external auditor reads first. Handing them a forbidden
  number means the next review will either report a "discrepancy" that is actually correct retirement, or
  (worse) validate the stale value. This is the same class as the round-7 finding ก12, which removed several
  literals from the brief; one survived.
- **Proposed solution**: delete the parenthetical and cite
  `canonical_numbers.json → values.khundan_22y.headline_metrics.year_2026_anomaly.days_earlier_than_median`.

### [F-08] Hard-coded baseline, dead branch, and a static conclusion in the compound section

- **Location**: `analysis/goal7_ongkharak_hydraulic_2d.py:253`; `:236`; `:215`;
  `report/goal6_build_report4_draft.py:389`.
- **Empirical evidence**
  - `:253` — `res["bucket_baseline"]["connected_fill_copernicus_s0"] = {"peak_27sep": 0.367, "oct2_validated": 0.321}`.
    No computation produces these two numbers in the run; they are typed into the analysis script and are
    then rendered in `tbl_hydraulic_2d`'s caption as "การเติมแบบต่อเนื่อง 0.37 / 0.32".
  - `:236` — `if True:` wrapping the whole run loop (leftover from the parallel-per-DEM refactor).
  - `:215` — `def iou(..., cell_km2=0.0081)`: the default still carries the 2.3 % understatement that
    round 7 fixed at the call sites (`run()` passes `dx*dy/1e6`). It is currently harmless but is a trap for
    the next caller.
  - `report/goal6_build_report4_draft.py:389` appends "จึงพื้นที่เสี่ยงล้นคันที่สมการเดิมประเมินสูงกว่าเมื่อ
    ยึดค่าที่วัด" unconditionally. It happens to be true now (critical cells 48 → 24, band 23–25), but the
    sentence is not derived from `band_counts`, so a future re-anchor could silently falsify it.
- **Critique**: `AGENTS.md` requires every number in a report to trace to a ledger and every conclusion to be
  computed. Three of these four are cosmetic; the hard-coded 0.367/0.321 is not — it is a comparison
  baseline that a reader will treat as a result.
- **Proposed solution**: compute the connected-fill baseline inside the run (or move it to a JSON with a
  `source` field); delete `if True:`; drop the `cell_km2` default (make it required); derive the sentence
  from `band_counts["original"]["critical"] > max(band_counts[k]["critical"] for k in …)`.

---

## 4. Intra-Report & Cross-Report Consistency Audit

**Scope caveat**: as stated at the top of this file, the rendered HTML was not readable in this session. The
checks below are against builders, canonical ledgers and the JSON that feeds them; they catch drift in the
*source of truth*, not rendering bugs.

- **Intra-report (builder level)**
  - Report 4 §8.1: the anchored matrix and the four benchmark rows are mutually consistent in the JSON
    (`matrix_anchored.anchor = {2.24, 1.91, 2250}` matches `historical_benchmarks[1]`), and the prereg's §3
    limitations are all printed at `goal6_build_report4_draft.py:390` and `:396-398`, including the
    "ค่าสูงสุดสองค่าคนละเวลา" caveat. No contradiction found.
  - Report 7 public §hypsometry: `_r305` is correctly labelled "ระดับมัธยฐานของภูมิประเทศ ไม่ใช่ระดับสัน
    ทางหลวง 305" and carries the `# gap: route305_crown_elevation` tag (`goal7_build_public.py:392-395`), and
    the hypsometric table's caption carries the same caveat twice (`goal7_blocks.py:543-544, 561`). The
    Route 305 overtopping level is nowhere presented as fact. **Passed.**
  - Report 7 public, storage paragraph: `ratio_to_sar` is read from canonical (2.9) and the raw-vs-corrected
    area range is read from `dem_sensitivity` (20–32 km²), both computed, no literals. **Passed** — except
    that the two-surface min/max is presented as "ชุดดิบ" without saying which two (F-04).
- **Cross-report (ledger level)**
  - Canal length appears as 135.655 / 135.7 / 135.9 / 135.963 in four places; the reconciliation documents
    all four and names the consumer for three of them. The travel-time consumer is the exception (F-05).
  - Storage: 68.5 (flat 504 m² × 135.9) vs 68.59 (three-reach table) vs 74.0 (author-assumed sections).
    All three are registered variants with reasons; the box prints them and says which one the report uses.
    **This is the model the rest of the project should follow.** One arithmetic consequence is *not*
    registered: 504 m² × the canonical 135.655 km gives 68.37 MCM (active ≈52.9, fill ≈24.5 h), a fourth value
    that no variant records (F-05).
  - Structure count: 87 (analyst compilation, tier C, marked `status: "disputed"` in
    `analysis/goal7/quantities.json` with `disputed_by` stating that 87 cannot be reproduced from the
    130-row catalogue) vs 99 (EIA component buildings, tier A) vs 130 (project catalogue). The registry
    handles this correctly. Note for the reader: the *canonical* value is the tier-C one; the tier-A figure
    is demoted to a variant. That is defensible on scope grounds (canal crossings ≠ component buildings) but
    should be stated as a scope choice wherever 87 appears.
- **Retired ledger**: I scanned every tracked `.md/.py/.json/.txt` outside `archive/`, `docs/reviews/` and
  `data/` for all 47 keys in `goal6/canonical.json → retired.retired_values`. Hits are confined to the
  producer (`goal6_canonical.py`), the ledger itself, the review archives, and **`README.md`**, which still
  carries `ป่าสัก 521`, `ท่าจีน 160`, `2,263.6` and `แม่กลอง 73 ตร.กม.` — the same miss reported as F-01 by
  the Sonnet review at this commit; **still reproducible**, because `README.md` is not in the retired-value
  test's `DOCS` list.
- **Gap register**: `route305_crown_elevation` is open and every builder reference carries the tag;
  `test_mitrearth_road_valley.py:22` asserts the open status. No stale "does not exist" phrasing found in the
  builders.

---

## 5. Verified Invariants (Passed Spot-Checks)

| Check | Method | Result |
|---|---|---|
| Test suite, report-independent subset | `pytest --ignore` × 15 report-reading modules, stdin detached | **144 passed, 0 failed** (the run was cut off by a temp-cleanup guard after the last dot; no `F`) |
| Report-reading subset | same run, `--continue-on-collection-errors` | 77 failed / 1 error, **all** `PermissionError` on `report/*.html`; the single non-environmental failure was `test_tool_registry` (F-06) |
| Catalog | `catalog.py check` / `catalog.py audit` | 124/124 exist; audit reports all 50 scanned docs registered (see F-06 for why this disagrees with the registry test) |
| Source-quote provenance | PyMuPDF text layer, `main1.pdf` pages 146 / 191 / 196 | `600 ลูกบาศก์เมตร/วินาที` ✔ p.146; `723 ล้านบาท` ✔ p.191; `ไม่เกิน 650 ลบ.ม./วินาที` ✔ p.196 — all three `source_quote_verified` constants reproduce exactly |
| Pre-registration commit order | `git log --date=format` | audit `7841e10` 22:15 → run `8c2c1d0` 03:37 → owner decision `182fb83` 05:49 → code `d3c7e11` 06:21; pass-mosaic `769d4d5` 08:13 → `3a71602` 10:02; Pasak sensitivity `c8fb0b1` 11:48 → `78cc138` 13:48; cross-check `933e13b` 07:57 → `fbbb02c` 08:09; reach length `c2aabd3` 11:06 → `16cf7c6` 11:12; anchored matrix `ee73fe9` 00:06 → `85a7ae5` 00:13; Chachoengsao `7ebde3f` 11:14 → `f3fc89d` 12:31. **Eight pairs, no inversion** |
| S1 relative-orbit pairing | enumerate all 127 stage-1 scenes, group by `(basin, rel_orbit)`, collect acquisition HH:MM | 6 groups contain two times, all differing by ≤1 minute (12-day repeat drift). **No group merges two different tracks** — the `OFFSET` table is internally consistent |
| HH:MM proxy removal | grep | `hhmm()` exists only as a display label (`goal6_s1_stage2_water.py:143`), never as a grouping key; `reference == scene` exclusion at `:131-134`; unpaired scenes collected at `:118` |
| Harmonics | `l3_coastal_harmonics_summary.json` | fit ends 2026-09-19 23:00 (before the 20 Sep test start); common sample n_test = 232 for all four leads; amplitudes K1 0.543 > M2 0.484 > O1 0.334 > S2 0.238, form factor (K1+O1)/(M2+S2) = 1.22 → mixed, diurnal-dominant, physically plausible for the Gulf; tide predictor on CPY015 in the test window RMSE 0.333 m (multiyear) vs 0.617 m (4-constituent) |
| L3 leakage | code read `goal6_l3_coastal_model.py:235,263` | `leak[:,k]` purge of training rows whose target falls in the test window is present; `n_test` identical across leads by construction; tide features are `tide0`, `tide0−tide1` and a deterministic M2 phase — no future tide value enters the feature set |
| 2D water budget | `canonical.ongkharak_hydraulic_2d.rain_best[*].budget` | closure error ≤ 0.004 MCM (0.000 % of input) on all four surfaces; edge outflow 53 % of input (448 of 851 MCM) is disclosed in prose and in a dedicated table |
| 2D post-hoc disclosures | `report/goal7_blocks.py:963-979` | grid-edge optimum (f = 1.0, k = 0.05, both at the extended grid's minimum) is stated; the depth-grid change after seeing the result is stated; over-prediction 1.7–2.0× is stated; "parameters not identifiable" is stated |
| Canal volume chain | 504 m² × 135.9 km; (51×2 + 3×2²) m² × 135.9 km | 68.49 → 68.5 MCM; dead 15.49 → 15.5; active 53.0; 53.0e6/600/3600 = 24.53 h. **Reproduces** |
| CRF / unit cost | `goal7_operational_economics.py:64-83` | `r(1+r)^n / ((1+r)^n − 1)` — standard; 7/9/12 % scenarios share one lifespan, and the 50-year sensitivity is a labelled analyst variant |
| Utilisation | 1,985.5 MCM / 51.84 MCM/day = 38.3 d; /365 = 10.49 % | reproduces, and the summary explicitly says the figure is an equivalence, not idle days |
| Compound anchored arithmetic | recomputed `0.132 × ((Q/1000)^1.28 − (2250/1000)^1.28)` and the gain term | `stage_diff_vs_original` min −0.26 / max 0.00 reproduced exactly; critical cells 48 → 24 (band 23–25); 44 of 132 cells change band |
| Ny.1B/Ny.7 bankfull | `hydraulic_1d_routing_summary.json` | 666.3 / 617.4 m³/s, travel 3.25 h sim vs 9.0 h observed — matches the brief's figures |

---

## 6. Information Gaps & Required Field Data

**Gaps in this audit (not in the project)**

1. `report/*.html` unreadable in this session → Dimension 8 could not be executed against rendered text, and
   the four badge gates could not be exercised. Re-run the brief's §3a in an environment with access.
2. I did not defeat the literal gate by injection (that needs a write to a builder); F-02 is an analytical
   defeat of the same gate, which is stronger evidence than an injection would be, but the injected test
   remains unrun.
3. I did not re-run the 2-D solver or the L3 model (CUDA + write access). The determinism claim
   (re-running old surfaces reproduces old scores to 3 decimals) is therefore read from code, not verified.

**Gaps in the project (still open, per its own registers)**

| Gap | Consequence |
|---|---|
| `route305_crown_elevation` | No overtopping level for Highway 305; the tipping-point section can only report the terrain median |
| Surveyed Ny.1B–Ny.7 chainage | 18.3 km is unsourced; the mitrearth line gives 15.11 km — 17 % short of 18.3, inside the pre-registered ±20 % band (Sonnet F-03 covers which denominator the published percentage uses) |
| S.26 daily series | The 1,970 MCM/yr denominator of the unit cost has no traceable source (R7-02) |
| Gate discharge logs | The Gate-Control vs Routing Trap case study separates gate operation from routing by argument, not by record |
| C.12 multi-year record | The compound matrix's `c1` and exponent remain uncalibrated; the anchored variant rests on one season |
| DEMPro coverage outside 18 windows | Ongkharak's ground level is a transferred correction, not a measurement (F-04) |
| A "measured lag" for the dam→Ny.7 travel time | The 9–18 h band is stated in the report caption, but the basis for choosing 12 h inside it is recorded nowhere (F-01) |

---

## 7. Overall System Suggestions & Consistency Recommendations

**Hydraulic & methodological**

1. **Record the lag, not just the ratio.** F-01 is the highest-value fix here and costs no computation: the
   report already prints "แกว่ง 10–21 % ตามช่วงเวลาเดินทาง 9–18 ชม.", so what is missing is not a caveat but a
   *source*. Put `lag_h`, `window` and the band into `dam_share`, let the builders read them, and turn the
   `== 12` assertions into a band check — then revising the lag is a data edit, not a build failure.
2. **Separate "relabelled" from "estimated".** For any threshold-defined flood on a corrected DEM, the
   extent is invariant under a monotone correction and only the stage axis moves. Say that explicitly in the
   Ongkharak section and quote the compression factor (F-04); it pre-empts the objection that 95.6 % and
   3.8 % are two estimates of one thing.
3. **Give the compound matrix a two-parameter anchor.** The anchored variant currently anchors a *measured
   stage* to an *estimated co-timed tide* (prereg §3 admits this). If the CPY015 record exists at 10-minute
   resolution for the peak-stage hour, anchoring to the measured tide at that hour removes the caveat
   entirely and is a one-line change in `goal6_tide_gain_regression.py`.
4. **Test the reference-date sensitivity in the direction that matters.** Both tested basins moved the
   reference *earlier*; the risk identified in the Sonnet review (a reference dated 19–22 Sep already
   contains new water) is untested. One basin, one orbit, one pre-21-Sep reference would bound it.

**Data-consistency & governance**

5. **One registry, one definition of "registered".** F-06 exists because `catalog.py` and
   `tools/registry.json` answer the same question differently. `AGENTS.md` already names the registry as the
   single source of truth; make the catalog read it, and make the review deliverable path match whatever the
   gate accepts.
6. **A three-state gate.** "Not run" must not render as "failed" (F-03). The badge is the project's most
   visible claim of rigour; a false red is as damaging as a false green.
7. **Fix the sign in the literal gate and add a regression test.** One character (F-02). The project's most
   sensitive published numbers are signed offsets; leaving them unscanned undermines the whole two-layer
   design.
8. **Give `canonical_numbers.json` the `definitions` block that `goal6/canonical.json` already has.** The
   `dam_share` case (F-01) is not an outlier: `s1`, `levels` and `model_v1` all carry several windows'
   worth of numbers under short keys. Rule (6) in `AGENTS.md` should apply to all three ledgers, and a test
   should assert that any key whose name ends in `_pct` and whose sibling has `_mcm` has a definition.
9. **Retire the review-prompt literals.** F-07 is the second round in which the brief itself carried a
   value the repo had retired (round 7 ก12 removed several). Add the brief to the retired-value test's
   `DOCS` list so the next stale literal fails a test instead of reaching an auditor.

---

*Prepared read-only against `78cc138`. No file in the repository was modified except
`report/assets/verification.json`, which `tools/verify_all.py` rewrote as a side effect and which was
restored with `git checkout --`. The four untracked `REVIEW.*.md` files at repo root (three pre-existing,
plus this one) are what F-06 documents.*
