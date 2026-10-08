# Full Project Review — nnyflood (น้ำท่วมนครนายก 2569)

**Date:** 8 October 2026
**Repository:** `D:\theera\Documents\code\flood` (tkittich/nnyflood, published on GitHub Pages) · Git head reviewed: `7249dcc` ("terminology: กวาด เบิก/พีค ...")
**Review type:** Independent full-project review (AI-produced — see the note in §8 before acting on any recommendation)

## 1. Scope & method

This review covers all Python code under `analysis/` and `report/`, the test suite (`tests/`), CI configuration (`.github/workflows/ci.yml`), packaging/hygiene files (`requirements.txt`, `pyproject.toml`, `.gitignore`, `.gitattributes`), methodology & documentation (`docs/METHODS`, `ANALYSIS_PLAN`, `DATA_DICTIONARY`, `DATA_SOURCES`, `LEGAL_REVIEW`, `ENVIRONMENT`; README, START_HERE, HANDOFF; the findings docs under `analysis/*_findings*.md`; data manifests), and the built Thai HTML reports themselves (scanned for leftover placeholders, external resource loads, MIME correctness). It is an independent pass conducted alongside — not derived from — the existing prior reviews (`REVIEW.md`, `REVIEW.gemini.md`, `docs/reviews/REVIEW.deepseek.md` R-01…R-13); those were consulted to avoid blind duplication, but every finding below was re-derived directly from code and data during this review.

**How this review was conducted.** Five parallel specialized subagent passes — **A:** core analysis pipeline, **B:** satellite + hydraulic code, **C:** report builders & output quality, **D:** methodology & documentation consistency, **E:** tests/CI/repo hygiene — each reading its assigned files fully and empirically verifying claims: a live `pytest` run (26 passed), `verify_data_integrity.py --quick` (681 OK / 42 SKIPPED / 0 mismatch), `py_compile` across all audited scripts, rasterio header inspection of the Copernicus DEM tiles, JSON artifact field checks, and grep-level cross-checks of every headline number across code, docs, tests and both built HTML reports. The five parts were then merged with deduplication: where two parts reported the same underlying issue (stale M4 corridor numbers in B & D; dataset-count drift and the duplicate review doc in D & E) it appears **once** in §4 with both source areas listed, and is cross-referenced from both detail sections.

## 2. Executive summary

**Overall verdict.** This is an unusually well-engineered, self-auditing project: no CRITICAL findings, and every published headline *value* reconciles to its committed artifact (frozen `canonical_numbers.json`, integrity gate at 681 OK / 0 mismatch, and the documented "26 passed" test claim verified true in this session). The risk clusters are elsewhere: **(a)** the methodology both reports describe for S1 flood detection is not the rule the code that produced the headline peak map actually ran (§5.2, F-01); **(b)** the master report contradicts itself on the 62 h vs 65 ชม. above-bankfull baseline (F-04); **(c)** a recurring *propagation lag after corrections* leaves pre-fix numbers in primary source docs while canonical/secondary artifacts moved (the M4 corridor ~12 ตร.กม./~44 ซม. case, F-14; the stale DATA_SOURCES status snapshot, F-21); and **(d)** guard coverage stops at headline strings — rating-curve coefficients, chart annotations, dam-release tables, large tracked data files and the CI interpreter all sit outside what is checked (F-02/F-03, F-25, F-23). Nothing requires re-doing an analysis: every P0 item in §7 is a one-line-to-small-doc fix except the S1 rule decision, which optionally triggers a peak-map re-derivation.

**Key stats.**

| Metric | Value |
|---|---|
| Files reviewed (full or by section) | ≈90 — all 50 .py under `analysis/` + `report/` + `tests/`, the CI workflow, packaging & ignore files, ~30 methodology/findings docs; both built HTML outputs plus committed JSON/NPY/CSV/TIF artifacts spot-verified |
| Tests run (this session) | `pytest tests/ -q` → **26 passed in 0.37s** — matches the documented "26 tests" claim exactly (README :41,77,82 · START_HERE :33 · ENVIRONMENT :34) |
| Integrity gate (this session) | `verify_data_integrity.py --quick` → **681 OK · 42 SKIPPED (>5 MB) · 0 MISSING · 0 MISMATCH · 0 AMBIGUOUS** |
| Compilation check | `py_compile` clean on all audited scripts (Part A ×12, Part B ×21) |
| Findings by part (raw) | A: 20 · B: 13 · C: 9 · D: 12 · E: 10 = **64** |
| Consolidated unique findings (§4) | **61** (three cross-part pairs merged: F-14, F-22, F-26) |

| Severity | Raw across parts A–E | Consolidated (§4 table) |
|---|--:|--:|
| CRITICAL | 0 | 0 |
| HIGH | 4 | 4 |
| MEDIUM | 23 | 22 |
| LOW | 25 | 23 |
| NITPICK | 12 | 12 |
| **Total** | **64** | **61** |

**Top-10 most important issues.**

1. [B] The published S1 flood rule ("ΔVH≤−1 dB & ΔVV≤−2 dB & VHหลัง≤−18 dB") is not what generated the headline peak map — the code runs a VH-only grid-search rule, so both reports' methodology description diverges from the code behind 509.3 ตร.กม. (F-01)
2. [D] The master report's §4 quotes the known-wrong 62 h above-bankfull baseline its own source doc flags as a data artifact, contradicting canonical and its own §2 (both say 65 ชม.) — a self-contradiction in the published headline scenario sentence. (F-04)
3. [B-D] M4 corridor numbers are stale in five documents after the G-03 correction: still ~12 ตร.กม./~44 ซม. where JSON, code, tests and both reports all say 9.94/~52 ซม. — the correction propagated backwards, into secondary docs only. (F-14)
4. [C] Headline numbers are hand-maintained in 4+ places per number and the canonical guard is presence-only: any single data correction means manual edits across both templates, chart annotations and test expectations, with no tooling to list affected sites. (F-02)
5. [C] The rating curve Q=242·(h−4.55)^0.66 is duplicated across 3 scripts + both HTML appendices with zero canonical check — the formula most likely to change next (a survey-based Ny.1B rating is planned in §6.9). (F-03)
6. [B] F1=0.70 threshold calibration is a single-pair, in-sample grid search with no holdout, and the headline 27 Sep scene has no independent validation at all — "509.3" carries an unvalidated ±~20% envelope; the defensible number is the existing ≈360–510 range. (F-10)
7. [E] The CI integrity gate (`--quick`) skips every file >5 MB by size, so ~70 MB of *version-controlled* evidence data escapes hashing entirely — a corrupted canonical tracked file would pass every gate. (F-25)
8. [B] The five Khundan fetchers share no validation: no row-count/gap checks, and failed chunks degrade to silent empty rows — the CSVs they produce feed the published backtest, so a silent gap would bias RMSE with no artifact flagging it. (F-12)
9. [E] CI validates Python 3.13 while shipped claims are pinned to CPython 3.14.5 ("versions move RMSE numbers" is the stated pinning rationale) — a silent gap between what CI certifies and what the docs promise readers. (F-23)
10. [C] `make_x_charts_thai.py` is missing from every documented build chain, and no freshness coupling exists anywhere between analysis outputs and embedded charts — x1/x2 PNGs can go stale with zero guard while the build stays green. (F-16/F-17)

## 3. Table of contents

- **§1** Scope & method
- **§2** Executive summary — overall verdict · key stats · top-10 issues
- **§4** Consolidated findings table (F-01 … F-61, deduped across all parts)
- **§5** Detailed findings per area (parts reproduced verbatim; finding titles carry consolidated IDs)
  - §5.1 Part A — Core analysis code (`analysis/` pipeline) · 20 findings: 5 M / 9 L / 6 N
  - §5.2 Part B — Satellite processing + hydraulic code · 13 findings: 1 H / 5 M / 4 L / 3 N
  - §5.3 Part C — Report builders & HTML output quality · 9 findings: 2 H / 3 M / 3 L / 1 N
  - §5.4 Part D — Methodology, documentation & internal consistency · 12 findings: 2 H / 5 M / 5 L (in the consolidated table F-14 is attributed B+D and F-26 takes MEDIUM via its E merge)
  - §5.5 Part E — Tests, CI & repo hygiene · 10 findings: 4 M / 4 L / 2 N
- **§6** Consolidated strengths (thematic)
- **§7** Prioritized roadmap — P0 correctness/credibility · P1 regression guardrails · P2 docs consistency & terminology · P3 hygiene/maintenance
- **§8** Open questions needing owner decision + review note

> Note on §5: each part is reproduced verbatim as produced by its subagent. Original section headings are demoted one level for nesting, and finding titles carry the consolidated "F-xx" ID in parentheses (original per-part IDs such as A-MED-1 / B-03 / D-02 / E's numbered findings are retained where parts cross-reference them). All file:line citations are preserved exactly as given.

## 4. Consolidated findings (all parts, deduped)

Merged rows: **F-14** = Part B "B-03" + Part D "D-02"; **F-22** = Part D "D-07" + Part E dataset-count finding; **F-26** = Part D "D-09" + Part E duplicate-review finding (consolidated severity takes the higher of the two). Related-but-distinct items are cross-referenced in the essence column.

| ID | Sev | Short title | Area(s) | Location | One-line essence |
|---|---|---|---|---|---|
| F-01 | HIGH | S1 detection rule in docs ≠ code that produced peak map | B | `analysis/s1_change_detect.py:59,67-73` vs `s1_flood_extent_findings.md:41`, `s1_pairs_animation.py:3,48`, `s1_peak_flood_map.py:135-136` | Headline 509.3 ตร.กม. map comes from a VH-only grid-search rule; the documented ΔVH/ΔVV triple rule has no code path for this figure (see §5.2). |
| F-02 | HIGH | Headline numbers hand-maintained in 4+ places; canonical check presence-only | C | `report/build_report_html.py` · `build_expert_report.py` · `report_assets.py`; `tests/test_artifacts.py:16` | Guard checks string *presence* only; any correction needs manual edits across templates, chart annotations and test expectations — same drift class as F-18/F-32 (see §5.3). |
| F-03 | HIGH | Rating-curve formula duplicated in 3 scripts + both appendices, unchecked | C | `report/report_assets.py:63-69` · `make_x_charts_thai.py` · public appendix ข · expert §3.2 | Q=242·(h−4.55)^0.66 is outside the canonical checks list — silent drift on the formula most likely to change next (see §5.3). |
| F-04 | HIGH | Master report uses known-wrong 62 h baseline in §4 | D | `report/รายงาน.md:104` vs `analysis/qa5_18day_rain_drainage_counterfactual.md:74`, canonical `hours_above_bankfull=65`, `รายงาน.md:54` | "62→12 ชม." contradicts the source doc's own correction, canonical and §2 — published self-contradiction (see §5.4). |
| F-05 | MEDIUM | Backtest "เหมือน v1 ทุกประการ" claims false; preprocessing diverges both ways | A | `analysis/goal4_model_backtest_long.py:62,117,122,147` | Feature set + 2026-fold + historical-fold preprocessing all differ from v1; comment and JSON method string are both false (numbers unaffected on committed data). |
| F-06 | MEDIUM | Ensemble mean divides by model count, not available count | A | `analysis/goal4_model_rainfcst_test.py:89-90` | Missing model day silently biases "ensemble" rainfall downward; dormant only because the committed forecast archive has full coverage. |
| F-07 | MEDIUM | Lag L selected on pooled train+test correlation | A | `analysis/thachang_leadtime.py:99-140` | Test-period information leaks into lag selection; reported lead-time skill is mildly optimistic and L=13 not provably the train-only optimum. |
| F-08 | MEDIUM | POWER rainfall −999 sentinel accepted as a valid value | A | `goal4_model_v1.py:~103` / `goal4_model_backtest_long.py:102` → `analysis/rain_window.py` | 2026-10-03/04 carry NASA −999; extending the grid/horizon by one day corrupts R72/R168 features with no validation in the chain. |
| F-09 | MEDIUM | Generated MD embeds hardcoded narrative numbers | A | `analysis/thachang_leadtime.py:286-287` | Tables update from data but the interpretive paragraph ("ขึ้น 0.96 ที่ +13…") is static — silent lie if inputs move. |
| F-10 | MEDIUM | F1=0.70 single-pair in-sample calibration; no independent validation of peak scene | B | `analysis/s1_change_detect.py:59-76`; context `s1_flood_extent_findings.md:41,48` | Thresholds from one quantized 6×5 grid search on the 2 Oct pair (06:09 leg); headline 18:28 pass never compared to any independent product (see §5.2). |
| F-11 | MEDIUM | Stage-storage & corridor width referenced to DSM surface, not ground | B | `analysis/hecras_lite_channel.py` (sampling from `dem_30m.npy`); caveats in `hecras_lite_channel.md:21-23,40` | Canopy-referenced bias on widths/volumes used in M4 is directionally documented but never quantified. |
| F-12 | MEDIUM | Khundan fetchers duplicate parsing/retry logic; no row-count or gap validation | B | `fetch_khundan_fullyears.py` · `fetch_multistation_levels.py:81-91` + siblings | Failed chunks degrade to silent empty rows and shorter CSVs feed the published backtest with only manual ("median gap 15 นาที") checks. |
| F-13 | MEDIUM | RID stage-rating year columns hardcoded by index; Ny.7 bankfull default for all stations | B | `analysis/rid_cross_section_stage_rating.py:34,93-102` | Template reordering silently relabels years; compound-n runs use a bankfull (6.86) that isn't the station's own. |
| F-14 | MEDIUM | M4 corridor numbers stale in 5 documents after G-03 correction (~12 ตร.กม./~44 ซม.) | **B + D** | `analysis/hecras_lite_channel.md:19,30` · `goal4_counterfactual_model_vs_nomodel.md:25,64` · `docs/ANALYSIS_PLAN.md:76` · `firo_dynamic_rulecurve_proposal.md:10,22` | Primary M4 docs carry pre-fix values while JSON/code/tests/reports all say 9.94/~52 ซม.; the ~17% area shift's mechanism is asserted, not explained (see §detail 5.2 + 5.4). |
| F-15 | MEDIUM | Dam release series triplicated: CSV + hard-coded dict + appendix table | C | `report/report_assets.py:60-62` · `build_expert_report.py:401-407` | The dataset the report documents as discrepant (+37.4 ลลบ.ม.) exists in three hand-maintained copies with no check (see §5.3). |
| F-16 | MEDIUM | `make_x_charts_thai.py` missing from every documented build chain | C | `build_expert_report.py:367` (§8); absent from README/START_HERE/HANDOFF/docs | Fresh clones never regenerate x1/x2 PNGs; if inputs update those charts go stale with no guard (see §5.3). |
| F-17 | MEDIUM | No freshness coupling between analysis outputs and embedded charts | C | builders embed bytes unconditionally; `report_assets.py` warn-only copy block | A stale chart beside canonically-checked new text passes the build green (see §5.3). |
| F-18 | MEDIUM | Headline rain range exists in two variants, neither canonicalized | D | exact 1,058–1,416 มม.: `README.md:12,14,26,47`, `รายงาน.md:104`; rounded 1,050–1,420: `รายงาน.md:11,48` + qa3/scenario/timeline/manifests | The headline trigger figure has no canonical form (same drift class as F-02) despite the "ทุกตัวเลขหัวใจอยู่ใน canonical" policy (see §5.4). |
| F-19 | MEDIUM | Three release rates + two scenario number-pairs, weak labeling | D | `scenario_analysis.md` · `goal4_counterfactual_model_vs_nomodel.md:21,32` · `ANALYSIS_PLAN.md:61,76` · `รายงาน.md:17,89` | 31.66 / 12.1 / 13.9 and −78%/−55% outcomes sit adjacent without shared scenario names; the qa5-vs-R1 caveat lives only in a footnote (see §5.4). |
| F-20 | MEDIUM | Rating uncertainty quoted as both ±18% and ±20%, no bridge | D | `khundan_tele_findings.md:53` · counterfactual `:30,92` · `firo:42` · `รายงาน.md:55` · `ny7_flow_stats:3` | Two defensible uncertainties for the same quantity with no doc stating "bias ≈18% → quote as ±20%" (see §5.4). |
| F-21 | MEDIUM | DATA_SOURCES.md is a stale phase-1 snapshot | D | `docs/DATA_SOURCES.md` §3–§5 | Status markers contradict current state everywhere (TMD/DEM/cross-sections/GISTDA/Sentinel all "ยังไม่เริ่ม" while done); duplicated section numbering 4–7. |
| F-22 | MEDIUM | Dataset count drift ("20 ชุด" vs 21 dirs) + no manifest-coverage test | **D + E** | `README.md:40,118` · `data/01_…`–`data/21_landsat_optical` | No authoritative enumeration (orphaned `data/manifest.md`); per-dir manifest invariant enforced by discipline, not a gate (see §detail 5.4 + 5.5). |
| F-23 | MEDIUM | CI validates Python 3.13 vs documented production CPython 3.14.5 | E | `.github/workflows/ci.yml:14` · `requirements.txt:3` · `docs/ENVIRONMENT.md:9` | The pinning rationale (versions move RMSE) is exactly why the interpreter gap matters; no matrix covers 3.14. |
| F-24 | MEDIUM | Temp artifact `_v1_out.txt` committed to git | E | repo root (tracked, 4,353 B; matches no ignore rule) | Scratch output against the repo's own temp-file policy; shows strays aren't caught by any gate. |
| F-25 | MEDIUM | CI integrity `--quick` never hashes tracked files >5 MB (~70 MB escape) | E | `.github/workflows/ci.yml:19-24` · `analysis/verify_data_integrity.py:234,262` | Size-based skip can't distinguish tracked from untracked; a corrupted canonical evidence file passes every gate. |
| F-26 | MEDIUM | Byte-identical duplicate review tracked twice; publish policy inconsistent | **D + E** | root `REVIEW.gemini.md` + `docs/reviews/REVIEW.gemini.md` (same SHA-256) · `.gitignore:68-69` | "Internal reviews unpublished" policy violated by a committed+published copy, duplicated in git with drift risk (see §detail 5.4 + 5.5). |
| F-27 | LOW | v1 test-window label vs actually evaluated rows | A | `goal4_model_v1.py:~167,232` | Docs/JSON say Sep 20–Oct 4 but the `i+48<e` constraint truncates evaluated rows at Oct 2 23:00 (n=312) unannounced. |
| F-28 | LOW | Hourly decimation keeps ≈1 of 4 samples, unreported | A | `thachang_leadtime.py` `hourly()` | train_n ≈ 122 → RMSE differences not statistically resolvable; pooling convention differs from v1 mean-pooling. |
| F-29 | LOW | Multistation: ThaChang 2021/2022 folds skipped without recorded reason | A | `goal4_model_multistation.py` (`te.sum() < 100`) | Zero Jun–Oct rows in source CSVs (station offline); the reason is absent from the JSON output. |
| F-30 | LOW | Inconsistent "event window" across model scripts | A | v1/moisture/rainfcst Sep 25–30 vs multistation Sep 23–Oct 3 | "Event RMSE" not comparable between files; no shared constant in `common.py`. |
| F-31 | LOW | Counterfactual `AREA_FLOOD=509.0` hardcoded vs canonical peak 509.3 | A | `goal4_counterfactual_model.py:183` · `canonical_numbers.json` (from `flood_peak_27sep1828.npy`) | M4 "peak drop" line carries a stale mask-derived constant (0.06% off). |
| F-32 | LOW | `build_canonical_numbers.py`: small self-consistency gaps | A | `analysis/build_canonical_numbers.py:42,78,87-89` | Re-inlined cell-area formula; MAE mislabeled "RMSE wet"; `None` fold would TypeError; hardcoded timestamps crash on reprocessing. |
| F-33 | LOW | `verify_data_integrity.py`: heuristic misattribution is latent, not active | A | `analysis/verify_data_integrity.py` (`looks_like_path`, collision resolver) | Wrong-file OK possible in principle (backticked-token + basename-collision paths); empirically dormant this session. |
| F-34 | LOW | `run_all.py`: counterfactual runs before hecras can refresh its input | A | `analysis/run_all.py` step order | Mixed vintages in one commit on any pass where DEM/section inputs changed (fresh clones safe). |
| F-35 | LOW | v1 header mislabels rainfall source ("ฝนรายวัน TMD" vs NASA POWER) | A | `goal4_model_v1.py` header comment | Wrong agency name in the script that defines the canonical model. |
| F-36 | LOW | Gauge datum (+1.59 m) printed for stations that don't use it | B | `rid_cross_section_hydraulics.py:73,83` · `rid_cross_section_extract.py:88` | Console-only ~1.7 m gauge error for 8 of 9 stations; shipped JSON is clean. |
| F-37 | LOW | `s2_water.py` writes output CWD-relative while inputs are repo-anchored | B | `analysis/s2_water.py:101` vs :24 | Stray folder + stale canonical artifact when run outside repo root. |
| F-38 | LOW | `gistda_georef_compare.py`: out-of-frame cells clamped; cell-area formula off ~0.7% | B | `analysis/gistda_georef_compare.py:38-39,63` vs `common.py:28-31` | Edge-pixel aliasing latent; absolute area comparisons carry an undocumented constant offset (110574 vs 111320). |
| F-39 | LOW | Two georef experiment scripts orphaned without in-code status marker | B | `analysis/georef_fit.py` · `georef_corner_match.py:60,82` | Superseded dead ends discoverable by code search carry no "experimental" header; the MERC gate is a no-op filter. |
| F-40 | LOW | `c5_floodhub.png` has no producer and isn't documented as manual | C | `build_expert_report.py:25`; §8 "browser steps" note :371 covers FB/CDSE only | Silent-staleness path specific to one image; no documented refresh procedure. |
| F-41 | LOW | Expert builder hard-codes `image/png` MIME; `__MAP__` is actually a JPEG | C | `build_expert_report.py` `b64()` / `imgs["MAP"]`:23 | Exactly 1 occurrence of `data:image/png;base64,/9j/` in expert HTML; browsers render fine, strict validators don't. |
| F-42 | LOW | Dead code / unused entries in the report pipeline | C | `build_report_html.py:31` · `report_assets.py:70`, ~258-261 | Unused G5 asset (~270 KB read+encode per build), `QBANK`, dead label branch, redundant imports. |
| F-43 | LOW | `album_geotag_summary.md` stuck at 666 photos (elsewhere 668) | D | `analysis/album_geotag_summary.md` title/:7/:75 | One collection-batch stale; every other doc uses 668. |
| F-44 | LOW | Typos / mojibake in public-facing text (all verified at cited lines) | D | `รายงาน.md:11,12,53,78` · `ANALYSIS_PLAN.md:60` · `goal4_counterfactual_model_vs_nomodel.md:56` · `khundan_tele_findings.md:53` | Verified mojibake in the published report and findings docs (e.g. "แบมป์รอง", "คาบอบัติ"). |
| F-45 | LOW | Evidence protocol [F]/[I]/[O] applied unevenly; [O] effectively unused | D | METHODS/README vs most `analysis/*_findings.md`; only `ny1b_q668_investigation.md:5` uses [O] | Advertised project standard not consistently applied. |
| F-46 | LOW | Ny.1B peak level quoted from two feeds, 7 cm apart (11.07 vs 11.00) | D | `รายงาน.md:51` · `khundan_tele_findings.md` K2 table & :16 | Gap hand-waved with "≈" while Ny.7's analogous gap got an explicit DATA_DICTIONARY note. |
| F-47 | LOW | No scheduled full-integrity run; README's "681 files verified" not reproducible from CI | E | `verify_data_integrity.py:5-8` · `.github/workflows/ci.yml` (no `schedule:`) | Strongest README integrity claim is a one-time local result with no standing mechanism. |
| F-48 | LOW | Report HTML build/determinism not verified by CI | E | `.github/workflows/ci.yml` (no build step) · `tests/test_artifacts.py:51-61` | Only committed-HTML string presence checked; builder regressions on charts/assets would ship unnoticed. |
| F-49 | LOW | No pip caching in CI; full install on every push to any branch | E | `.github/workflows/ci.yml:12-16` | Wasted minutes + PyPI load per push; no functional risk (pins). |
| F-50 | NITPICK | `ols()` returns None on singular design; predict path unguarded | A | `thachang_leadtime.py` | Latent crash if a future lag choice makes the matrix rank-deficient. |
| F-51 | NITPICK | Counterfactual: M1 rule now identical to R1 (dead `shape_storm` param) | A | `goal4_counterfactual_model.py:111-130` | Committed summary carries two rows with identical numbers; drop M1 or state the identity. |
| F-52 | NITPICK | `Ny7_peak` + `Ny7_rec` merged without overlap check | A | `goal4_counterfactual_model.py` | Zero duplicate timestamps today; a future khundan export overlap would silently overwrite observed peaks. |
| F-53 | NITPICK | Storage-capacity clamp applied to `rule_actual` too | A | `goal4_counterfactual_model.py` `rel_daily` | "Actual" could deviate from observed history if data ever violated capacity (never fires: 224.34 < 225.4). |
| F-54 | NITPICK | v1: TRAIN_END magic boundary; GBDT table pre-G-04 vintage; moisture TW pinned | A | `goal4_model_v1_findings.md` · `goal4_model_moisture_test.py` (`TW=2.0`) | Mixed vintages in one findings doc; the "base" row is not bit-identical to v1's. |
| F-55 | NITPICK | `rain_window.py` docstring omits backtest consumer; Oct 2 scene prefix hardcoded | A | `rain_window.py` · `goal4_model_backtest_long.py:101` · `s2_water.py:28` | Completeness nits on a single-event forensics repo (acceptable, noted). |
| F-56 | NITPICK | `s1_masks.py` merge/reproject assumes DEM nodata=−32767; tiles are float32 with no header nodata | B | `analysis/s1_masks.py:67-82` (verified tile metadata) | Inert today (no cell equals the sentinel); one comment or a `ds.nodata` read would close it. |
| F-57 | NITPICK | Peak-map figure bakes district areas/labels into text instead of tracked data | B | `analysis/s1_peak_flood_map.py` :135-136 / :22 | Re-run after any data change yields labels that may not match pixels; no test reads PNG text. |
| F-58 | NITPICK | Georef "GCP residual = 0.0 px" is structurally zero, reads like an independent check it isn't | B | `analysis/georef_gistda.py` (residual computation) · `gistda_georef_findings.md:42` | Tautology of a 4-parameter fit through 4 points; one doc clause prevents miscounting validations. |
| F-59 | NITPICK | `CANON["values"]` payload has zero consumers | C | `build_canonical_numbers.py` · `build_expert_report.py:477` (checks lists only) | Implies a wiring path that doesn't exist; wire one consumer or drop "values" (see §5.3). |
| F-60 | NITPICK | opencv documented as optional only in a requirements.txt comment | E | `requirements.txt:20-23` · `pyproject.toml:26-27` | Tooling can't see the optional extra; add `[project.optional-dependencies]`. |
| F-61 | NITPICK | Local object store is bloated (informational) | E | local `.git` (442 loose / 82.54 MiB + 65.72 MiB pack) | No effect on clones; `git gc --aggressive` locally at leisure, no repo change needed. |

## 5. Detailed findings per area
### 5.1 Part A — Core analysis code (`analysis/` pipeline)

*Synthesis.* The core modeling pipeline is the most conservative area of the repo: no CRITICAL/HIGH findings, and nothing changes a published headline number — every MEDIUM is either a false/stale *method claim* in committed artifacts or a latent time bomb that is currently dormant on exactly the data that is committed. Empirical re-checks (integrity run 681 OK / 42 SKIPPED, spike/range quantification on raw telemetry, py_compile ×12) confirmed the numbers hold; the risk concentrates in what the docs and comments *say* about method versus what the code actually does.

**Audit Date:** October 8, 2026
**Auditor:** opencode (local session)
**Git Head Commit:** `7249dcc` ("terminology: กวาด เบิก/พีค ...")
**Scope (Part A):** `analysis/*.py` model + forensics scripts and their data path — `goal4_model_v1.py`, `goal4_model_backtest_long.py`, `goal4_model_moisture_test.py`, `goal4_model_rainfcst_test.py`, `thachang_leadtime.py`, multistation scripts, `goal4_counterfactual_model.py`, `build_canonical_numbers.py`, `verify_data_integrity.py`, `common.py`, `rain_window.py`, `run_all.py`

**Method:** full or section reads of every script above; all cited claims below were empirically re-checked against the committed data/JSON, not taken from docstrings. Empirical checks performed this session:
- `verify_data_integrity.py --quick` → **681 OK · 42 SKIPPED (>5 MB) · 0 MISSING · 0 MISMATCH · 0 AMBIGUOUS**
- spike/range quantification on raw telemetry (see A-MED-1)
- POWER rainfall sentinel scan, backtest/v1 preprocessing diff, JSON artifact field inspection, `py_compile` × 12 scripts (all pass)

#### Defect summary

| Severity | Count | IDs |
|---|:---:|---|
| CRITICAL | 0 | — |
| HIGH | 0 | — |
| MEDIUM | 5 | A-MED-1 … A-MED-5 |
| LOW | 9 | A-LOW-1 … A-LOW-9 |
| NITPICK | 6 | A-NIT-1 … A-NIT-6 |

No finding changes any published headline number. All MEDIUM items are either (a) false/stale method claims in committed artifacts, or (b) latent time bombs currently dormant on the exact data that is committed.

#### MEDIUM

##### A-MED-1 (F-05) — `goal4_model_backtest_long.py`: "same as v1" claims are false since G-04; preprocessing diverges both ways
**Location:** `analysis/goal4_model_backtest_long.py:62`, `:122` (X row), `:117` comment, `:147` method string.

Three distinct asymmetries vs `goal4_model_v1.py`, all verified by re-reading both pipelines and scanning the raw CSVs:

1. **Feature set.** Backtest still includes `dH1B_6h` (`H1[i] - at(H1, i, 6)`, 8th column of X). v1 dropped it in commit `8b32689` (G-04, rank-deficient → unique coefficients). The comment "ฟีเจอร์ 12 ตัว เหมือน v1 ทุกประการ" and the method string in `goal4_model_backtest_long.json` — `"โมเดลเส้นตรง 12 ตัวแปร (ฟีเจอร์ชุดเดียวกับ v1)"` — are both false: v1 now has **11** features. Predictions are numerically unaffected only because the column is an exact linear combination of other columns on this data (the same property G-04 relied on); coefficients remain non-unique in the backtest artifact.
2. **2026 fold preprocessing.** Backtest loads 2026 raw (`series[st][2026] = load_file(fn26)`) — no despike, no range filter — while v1 despikes **all** years including 2026 (its `for yr in ny7s:` loop has no year exception). The code comment justifies the raw load with "(v1 ไม่ despike ปี 69 — คงเดิม)" which is factually wrong.
3. **Historical-year preprocessing.** Backtest applies per-station RANGE filters + a plausibility filter on X/Y (`:52`, `:137-141`) that v1 does not have at all, so backtest *training* rows also differ from v1's.

**Quantified impact (this audit):** raw Ny7 Jun–Oct 2026 contains exactly **3 spike points** despike would alter and **0 out-of-range values**; scanning all FULLYEAR files, the only in-window sensor garbage is **Ny1B 2024-08-08 ≈19:30–20:30, 33 zero rows**, which enter *v1-only* training (backtest filters them). Effect on any committed RMSE: negligible. The defect is the *claim*, not the numbers.

**Fix:** either align preprocessing (recommended: extract one shared loader) or rewrite the comment at `:62` and the JSON method string to state exactly what differs; drop or re-derive `dH1B_6h` so "ชุดเดียวกับ v1" is true again.

##### A-MED-2 (F-06) — `goal4_model_rainfcst_test.py`: ensemble mean divides by model count, not available count
**Location:** `analysis/goal4_model_rainfcst_test.py:89-90`.

```python
vals = [fc_rain(m).get(k) for m in MODELS]
ens[k] = sum(v for v in vals if v is not None) / len(MODELS)
```

If any of the 5 forecast models lacks coverage on a day, the ensemble mean is divided by 5 regardless → silent downward bias. Related: keys are taken only from `fc_rain("gfs_seamless")` so other models' extra days are silently dropped, and `(a.get(k) or 0)` treats a missing station value as 0 mm (downward bias for that station's half-weight). **Dormant today** — the committed forecast archive has full coverage for all 5 models in the window — but any future re-run with an updated `data/17_forecast_archive` file silently changes every "ensemble" number.

**Fix:** divide by `sum(v is not None for v in vals)`; take keys as the union of model days (or document gfs-as-reference); decide explicitly whether missing station = 0 or NaN-propagate, and record per-model coverage counts in the output JSON.

##### A-MED-3 (F-07) — `thachang_leadtime.py`: lag L selected on pooled train+test correlation
**Location:** `analysis/thachang_leadtime.py:99-140`.

The lag scan computes raw/diff/detrend correlations over the **full period**, then `L = best_raw["lag_h"]` (`:140`) before any time-based split is applied to model training. Test-period information therefore leaks into model selection; reported lead-time skill (e.g. Model C RMSE −27% vs A) is mildly optimistic and the chosen L=13 is not provably the train-only optimum.

**Fix:** re-run the scan on train rows only, report both `L_train` and `L_pooled`, and keep whichever generalizes; with `train_n ≈ 122` (see A-LOW-2) also widen the reported uncertainty band or say so in the MD.

##### A-MED-4 (F-08) — POWER rainfall `-999` sentinel accepted as a valid value
**Location:** loader at `goal4_model_v1.py:~103` / `goal4_model_backtest_long.py:102` (`rain_pw[r[0]] = (float(r[1]) + float(r[3])) / 2`) feeding `analysis/rain_window.py`.

`data/16_training_data/power_rain_daily_3pts_2021_2026.csv` carries NASA's `-999` missing sentinel on **2026-10-03 and 2026-10-04**. It is parsed as a real float, so `R72/R168` for rows dated ≥ Oct 4 become large *negative* rainfall. Dormant today only because the last evaluated row is Oct 2 23:00 (the `i + 48 < e` target constraint); extending the grid or horizon by a single day corrupts features with no validation anywhere in the chain.

**Fix:** map `-999 → NaN` at CSV load, and add one cheap invariant (`assert (R24 >= 0).all()` etc.) in each model script — this class of sentinel is common in WMO/NASA products.

##### A-MED-5 (F-09) — `thachang_leadtime.py`: generated MD embeds hardcoded narrative numbers
**Location:** `analysis/thachang_leadtime.py:286-287`.

The script *generates* `analysis/thachang_leadtime.md`, but the interpretive paragraph is a static string ("ขึ้น 0.96 ที่ +13, ตก 0.78 ที่ +21 กลับขึ้น 0.96 ที่ +35"). If data or the lag scan changes, the tables in the same file update while the narrative silently lies — the worst failure mode for a generated artifact.

**Fix:** interpolate the cited r-values from the computed correlation table (or delete the specific numbers and keep only the qualitative "signature of shared trend" sentence).
#### LOW

##### A-LOW-1 (F-27) — v1 test-window label vs actually evaluated rows
`goal4_model_v1.py:~167,232`: docs/JSON speak of a Sep 20–Oct 4 test window, but the `i + 48 < e` constraint truncates evaluated rows at **Oct 2 23:00 (n = 312)**. The final ~1.5 days are excluded from all-period metrics without being named anywhere. Fix: compute and emit the actual first/last evaluated timestamp into the results JSON.

##### A-LOW-2 (F-28) — `thachang_leadtime.py`: hourly decimation keeps ≈1 of 4 samples, unreported
`hourly()` (nearest within ±25 min) applied to 15-min data retains at most one reading per hour and discards the rest without reporting coverage/retention. st63 yields only `common_hours = 521`, giving **train_n ≈ 122** for every model — small enough that RMSE differences between models are not statistically resolvable, yet the MD presents point estimates. The convention also differs from v1/backtest mean-pooling (`np.mean` over all readings in the hour), so "hourly" series across scripts are not directly comparable. Fix: report retention % per station; prefer mean-pooling for consistency with `goal4_model_v1.py`.

##### A-LOW-3 (F-29) — multistation: ThaChang 2021/2022 folds skipped without recorded reason
The skip (`te.sum() < 100`) is silent in the JSON output. Root cause identified this audit: `khundan_15min_ThaChang_tail_FULLYEAR{2021,2022}.csv` contain **zero Jun–Oct rows** (station offline), so there was never data to fold on. Fix: emit `"skipped_folds": {"2021": "no Jun-Oct rows in source"}` into the JSON so readers don't infer a methodological choice.

##### A-LOW-4 (F-30) — inconsistent "event window" across model scripts
v1 / moisture_test / rainfcst_test define event = **Sep 25–30**; multistation uses **Sep 23–Oct 3**. "Event RMSE" is therefore not comparable between files, and each JSON embeds its own definition only implicitly. Fix: one shared `EVENT_START/EVENT_END` in `common.py`.

##### A-LOW-5 (F-31) — counterfactual `AREA_FLOOD = 509.0` vs canonical peak 509.3
`goal4_counterfactual_model.py:183` hardcodes the mask-derived area; `canonical_numbers.json` says **509.3** (recomputed from `flood_peak_27sep1828.npy`). The M4 "peak drop" line therefore carries a 0.06% stale constant. Fix: read the value from `s1_flood_series.json`/mask, or recompute like `build_canonical_numbers.py:44`.

##### A-LOW-6 (F-32) — `build_canonical_numbers.py`: small self-consistency gaps
(i) `:42` re-inlines the cell-area formula (`res*111.32**2*cos(14.2°)`) instead of importing `cell_km2()` from `common.py`, whose docstring explicitly exists to forbid this duplication — values agree today, but that is coincidence-by-copy; (ii) `:78` comment mislabels row position 2 as "RMSE wet" — it is **MAE** (`row[1]`=RMSE-all, `row[3]`=RMSE-event are the fields actually read); (iii) `:87-89` `all(f["rmse24_wet"] < f["rmse24_persistence_wet"])` would raise `TypeError` if any fold carried `None`; (iv) hardcoded keys `"2026-09-27 06:00"` and the three GISTDA pass IDs crash with bare `KeyError` if S1/GISTDA reprocessing shifts timestamps.

##### A-LOW-7 (F-33) — `verify_data_integrity.py`: heuristic misattribution is latent, not active
Two soft spots: `looks_like_path()` accepts *any* backticked token containing a dot (a line mentioning `` `some_script.py` v2 `` plus a hash would attribute the hash to the script name), and on basename collision the resolver hashes the first candidate while only warning to stderr — exit code stays 0, so a wrong-file OK is possible in principle. Empirically dormant: this session's run produced **681 OK / 42 SKIPPED / zero MISSING/MISMATCH/AMBIGUOUS**. Also `DATA.iterdir()` (`:260`) raises an unhandled `FileNotFoundError` if `data/` is absent. Fix ideas: require resolved paths to live under the manifest's directory; make AMBIGUOUS count toward exit code 3; wrap the iterdir in a friendly error.

##### A-LOW-8 (F-34) — `run_all.py`: counterfactual runs before its input can be refreshed
Step order places `goal4_counterfactual_model.py` (reads `river_cross_sections.json`) **before** `hecras_lite_channel.py` rewrites that JSON. In any single pass where DEM/section inputs changed, canonical numbers + reports would publish new S1 areas alongside a stale M4 corridor volume — mixed vintages in one commit. Fresh clones are safe (the JSON is committed). Fix: move the hecras step ahead of counterfactual, or have run_all re-run counterfactual after it when the sections file changed.

##### A-LOW-9 (F-35) — v1 header mislabels rainfall source
`goal4_model_v1.py` header comment says "ฝนรายวัน TMD" while the code loads NASA POWER (`power_rain_daily_3pts_...csv`). In a project whose value proposition is traceable provenance, the wrong agency name in the script that defines the canonical model is worth one line of correction.

#### NITPICK

- **A-NIT-1 (F-50)** `thachang_leadtime.py`: `ols()` returns `None` on a singular design; the predict path unpacks coefficients without a guard → latent crash if a future lag choice makes the matrix rank-deficient.
- **A-NIT-2 (F-51)** `goal4_counterfactual_model.py:111-130`: `rel_hourly(traj, shape_storm=None)` — parameter is dead (body always distributes flat 1/24) and the "M1 ช่วงพายุ 30/70" comment describes an abandoned experiment. Consequence in data: M1's rule now equals R1's, so the committed summary carries two rows with identical numbers; either drop M1 or state the identity explicitly.
- **A-NIT-3 (F-52)** `goal4_counterfactual_model.py`: `Ny7_peak` + `Ny7_rec` are merged into one dict without an overlap check — verified zero duplicate timestamps today, but if a future khundan export overlaps, `_rec` values silently overwrite observed peaks.
- **A-NIT-4 (F-53)** counterfactual: the storage-capacity clamp (`rel = S + infl − CAP`) is applied inside `rel_daily` for *all* rules including `rule_actual`, so "actual" could deviate from observed history if the data ever violated capacity (never fires today: max storage 224.34 < 225.4).
- **A-NIT-5 (F-54)** v1: `TRAIN_END = Sep 20 23:59` magic boundary; the GBDT table in `goal4_model_v1_findings.md` is from the pre-G-04 run (linear/persistence rows are unaffected by design, but a reader comparing all three models sees mixed vintages); `moisture_test.py` pins `TW = 2.0` constant where v1 uses real TW with default-fill, so its "base" row is not bit-identical to v1's.
- **A-NIT-6 (F-55)** `rain_window.py` docstring lists three consumer scripts but `goal4_model_backtest_long.py:101` also imports it; `s2_water.py:28` + run_all hardcode the Oct 2 scene prefix (acceptable for a single-event forensics repo, noted for completeness).

#### Verified clean (no finding)

- G-04 feature removal correctly applied in v1: `FEATS` = 11 names, X rows have 11 columns, ablation arm labels updated ("เต็ม 11 ตัว / ตัดฝน (8) / ตัด Ny.1B+ฝน (4)").
- All model JSONs: no `None` in required metric fields; backtest folds all finite; `backtest_beats_persistence_every_season` recomputes to true on committed data.
- Rain-window logic is shared (`rain_window.py`) and backward-looking only — no future leakage into R24/R72/R168 in any model script (verified identical import path in v1, backtest, rainfcst, moisture).
- thachang st62 series: clean 15-min Sep 1–30; `common_hours = 521` after intersection with st63.
- `river_cross_sections.json` committed and consistent (`corridor_area_km2_at_1p5m = 9.94`) with the counterfactual's post-`d926f43` read path.
- All 12 audited scripts pass `py_compile`.

#### Strengths worth keeping

1. **Canonical-numbers gate** (`build_canonical_numbers.py` + both HTML builders' compile-time substring assertions + pytest mirror): fail-loud by design — a stale report cannot be built silently.
2. **`common.py` as single source for constants**, with its docstring recording the historical unit bug it was created to prevent (only one re-inlined literal found: A-LOW-6i).
3. **Honest baselines everywhere**: persistence included in every model comparison; thachang includes a 3-model head-to-head; backtest carries an explicit non-generalization caveat banner.
4. **Counterfactual discipline**: capacity asserted (`:133`), uncertainty envelope + `peak_reliable` flag, and a docstring that self-documents the earlier unit bug and why volume-based (not single-gauge-subtraction) evaluation is used.
5. **Integrity checker** with four manifest formats, documented exit codes, deterministic ordering fix (`4e64605`) and ambiguity warnings — clean run this session.

*Part A ends here. Parts B (tests/CI) and C (reports/docs cross-consistency) to follow in the same file.*
### 5.2 Part B — Satellite processing + hydraulic code

*Synthesis.* The satellite and hydraulic chains are scientifically strong — genuinely rigorous GISTDA georeferencing validation with negative controls, a live (not hardcoded) M4 number chain from JSON through code to test to report, and negative results honestly framed as results — but this area carries the review's single most serious finding: the published S1 detection rule does not match the code that produced the headline peak map (F-01), compounded by a single-pair in-sample F1 calibration with no independent validation of the peak scene (F-10).

#### Scope reviewed

Files read in full (21 scripts, `analysis/`):
- S1 chain: `s1_process.py` (218), `s1_masks.py` (94), `s1_change_detect.py` (102), `s1_peak_flood_map.py` (141), `s1_pairs_animation.py` (64)
- Optical: `s2_water.py`, `landsat_water.py`
- Georef: `georef_gistda.py`, `georef_fit.py`, `georef_corner_match.py`, `gistda_georef_compare.py`
- Hydraulic/RID: `hecras_lite_channel.py`, `rid_cross_section_hydraulics.py` (123), `rid_cross_section_stage_rating.py`, `rid_cross_section_extract.py` (95), `rid_cross_section_plot.py`
- Fetchers: `fetch_khundan_training.py`, `fetch_khundan_training_2021_2022.py`, `fetch_khundan_fullyears.py` (45), `fetch_khundan_training_2024_2025.py`, `fetch_multistation_levels.py` (189)
- Shared: `common.py` (31)

Cross-referenced (not in script scope but used to verify claims): `analysis/s1_flood_extent_findings.md` (52), `analysis/gistda_georef_findings.md` (115), `analysis/hecras_lite_channel.md` (47), `analysis/rid_cross_section_stage_rating.md` (145), `data/08_dem_topography/satellite_gistda_28sep02oct/georef_progress.md` (42), `analysis/s1_flood_series.json`, `analysis/river_cross_sections.json`, `tests/test_core.py` + `test_artifacts.py` (names only), git log (`git log --oneline` on each suspect file).

Commands run (key outputs):
1. `python -m py_compile <all 21 scripts>` → **COMPILE_OK** (no syntax errors anywhere in scope)
2. `rasterio.open('data/08_dem_topography/raw/Copernicus_DSM_COG_10_N14_00_E101_00_DEM.tif')` → header `nodata=None`, dtype **float32**, shape 3600×3600; sampled window over the NN plain: min −1.12 m, max 45.64 m, **zero** cells equal to −9999/−32768/−32767/0 (see finding B-11)
3. `python -c json.load river_cross_sections.json` → `corridor_area_km2_at_1p5m = 9.94`, 11 sections, widths @+1.5 m ≈ 82–350 m per section
4. Grep for `9.94|11.95|corridor_area_km2_at_1p5m` across repo → JSON + `goal4_counterfactual_model.py:184` (reads from JSON, comment records 11.95 history) + `tests/test_artifacts.py:24` (~52 cm assertion) + both report builders use 9.94/52 cm — but **not** `hecras_lite_channel.md` (still 11.95/44 cm, see B-03)
5. Grep for `FULLYEAR` consumers → `goal4_model_backtest_long.py`, `goal4_model_multistation.py:44`, `goal4_thachang_model.py:32` all read the CSVs produced by the fetchers (B-05 blast radius confirmed)
6. Git history of `s1_change_detect.py` / findings doc: only touched at initial release + terminology sweep — the B-01 mismatch shipped in commit 207e8a7, not a later regression

#### Strengths

- **Single-source constants that demonstrably earned their keep.** `common.py` exists because rating/datum/bankfull/cell-area literals were duplicated 5–7× and caused a real unit bug (documented in its header); it re-exports the *tested* definitions from `rid_cross_section_hydraulics.py` instead of re-typing them, and `cell_km2`'s docstring explicitly pins "ห้ามเปลี่ยนเพราะพื้นที่ 509.3/436.3 ผูกกับค่านี้" — reproducibility is treated as a first-class constraint (common.py:1-31).
- **The S1 speckle-filter edge bug was found, fixed, and the fix matches the doc.** `s1_process.py:160-172` fills invalid/edge pixels with the interior median *before* `uniform_filter`, then restores them — exactly what `s1_flood_extent_findings.md:32` describes ("ช่อง DN=0 แพร่ผ่าน speckle filter จนภาพว่าง — แก้โดยเติมค่าก่อนกรอง"). The GCP grid is asserted fully populated (`assert not np.isnan(lon_g).any()`, s1_process.py:55) and per-scene coverage % of the province is printed (:180-181), so partial-swath scenes (the 9%/34% ones) are visible, not silent.
- **The wetted-perimeter bug was caught with a wrong-vs-right table.** `rid_cross_section_stage_rating.md:§1` shows counting the free surface double gives P=299 m / n=0.0268 (wrong conclusion: "n abnormally low") vs correct P=144 m / **n=0.0437** — and both `hecras_lite_channel.md:35-36` and the stage-rating doc cross-reference it, so the corrected value is consistent across all three documents. That conclusion (project rating curve Q=242(h−4.55)^0.66 is geometrically plausible) is sound and properly caveated (single-n Manning penalizes wide shallow floodplain; §2 note on divided-channel).
- **M4 number chain is live, not hardcoded.** `hecras_lite_channel.py:109` writes `corridor_area_km2_at_1p5m` into JSON → `goal4_counterfactual_model.py:184` reads it (with a comment documenting the old 11.95 hardcode) → `tests/test_artifacts.py:24` pins ~52 cm on corridor 9.94 km² → both reports say 9.94/52 ซม. One rerun of hecras_lite propagates everywhere; the test would catch a drift. (The one stale consumer is the findings .md — B-03.)
- **GISTDA georeferencing validation is genuinely rigorous for this class of problem.** Graticule-based affine with 4 pixel-verified GCPs, then *external* checks: chamfer vs OSM province boundary (median 0–1 px), independent area check (2,144 vs 2,151 km²), best-offset search ≈ 0, and a **negative control** showing the metric fails under deliberate shifts (findings §4). The F1=0.70 result was explicitly shown not to be a co-registration artifact (offset search → only 0.730; native-resolution comparison unchanged; eroding both sides *lowers* F1, ruling out edge effects — findings §7), and the composite-vs-single-pass comparability caveat is stated (§7 note).
- **Negative results are framed as results.** The DEM end-extension experiment enforces an RMS<1 m gate on the overlapping (known) portion before trusting the unknown part, failed at 3.23 m RMS, and is documented as "ทดลองแล้ว ปฏิเสธ … ไม่ต้องลองซ้ำ" with a stated lesson (`rid_cross_section_stage_rating.md:§3`) — this is better scientific hygiene than most positive results in the repo get.
- **Fetcher engineering basics are present where it matters:** retries (3×), chunking to ≤6 days, politeness sleeps, ASCII filenames with Thai names kept in registry/JSON, SHA-256 manifest covering *all* `st*.csv` so partial-station runs don't erase others' hashes (`fetch_multistation_levels.py:157-166`).

#### Findings
##### [HIGH] (B-01 / F-01) The published S1 flood-detection rule does not match the code that produced the headline peak map
- **Location:** `analysis/s1_change_detect.py:59,67-73` vs `analysis/s1_flood_extent_findings.md:41`, `analysis/s1_pairs_animation.py:3,48`, `analysis/s1_peak_flood_map.py:135-136`
- **Evidence:** The rule as documented everywhere is "น้ำท่วม = ΔVH≤−1 dB & ΔVV≤−2 dB & VHหลัง≤−18 dB + กลั่นหย่อม 3×3 (ตั้งค่าโดย maximize F1 กับ GISTDA บนฉาก 2 ต.ค.: F1=0.699, P=0.597, R=0.843)". The code that actually produces `flood_peak_27sep1828.npy` (which `s1_peak_flood_map.py:22` loads for the headline 509.3 km² figure) is:
  ```python
  def f1_for(drop, absv):
      w = (d <= -drop) & (post <= absv) & valid          # s1_change_detect.py:59-60 — VH only, no VV term
  for drop in (2.0, 2.5, 3.0, 3.5, 4.0, 5.0):            # :67
      for absv in (-18, -17, -16, -15, -14):             # :69
  ```
  i.e., a **VH-only** rule with thresholds selected by grid search over DROP∈[2.0…5.0] and ABS∈[−18…−14]. ΔDROP=1 is not even on the grid, VV never enters, so the documented triple rule *cannot* be what generated the peak map. The triple rule exists only in `s1_pairs_animation.py:48` (the three animation frames). The figure caption (`s1_peak_flood_map.py:135-136`) prints the triple-rule text together with P=0.60/R=0.84 — metrics that come from the change-detect grid search, not from a triple rule.
- **Why it matters:** Both published reports rest on 509.3 km² and describe a methodology that is not what was run; an external reviewer reproducing "ΔVH≤−1 & ΔVV≤−2 & VH≤−18" gets different pixels, and the stated P/R have no corresponding code path for this figure. Git history shows this shipped in the initial release (207e8a7), so it is not a later drift — the doc was written around an intended rule while the executed script implemented a calibrated variant.
- **Suggested fix:** Pick one canonical rule and make all four artifacts agree: either (a) implement the triple rule in `s1_change_detect.py` (VV arrays already exist from `s1_process`) and re-derive the peak map + F1, or (b) rewrite findings:41 / figure caption to state the actual VH-only calibrated rule with its selected DROP/ABS values and note VV was used only for the animation frames. Option (b) is cheaper; option (a) matches what readers are told.

##### [MEDIUM] (B-02 / F-10) F1=0.70 threshold calibration is a single-pair, in-sample grid search with no holdout — and the peak scene has no independent validation at all
- **Location:** `analysis/s1_change_detect.py:59-76`; context `s1_flood_extent_findings.md:41,48`
- **Evidence:** Thresholds are chosen by maximizing F1 against the GISTDA polygon on exactly one pair (2 Oct 06:09 vs 20 Sep 06:09), quantized to a 6×5 grid; there is no second test pair and no report of F1 sensitivity across the grid. The *headline* scene (27 Sep 18:28) was never compared against any independent product — GISTDA has no product for that pass (findings table, line 9). Additionally, calibration happened on the **06:09 orbit leg** while the headline map uses the **18:28 leg**: ascending/descending passes have different incidence-geometry distributions across the same scene, so ΔVH statistics shift between legs and a dB threshold calibrated on one leg transfers with unquantified bias.
- **Why it matters:** The 0.699/0.597/0.843 numbers are training-set metrics; the only real check on 509.3 km² is physical (volume-balance consistency, findings:49) plus a ratio-scaled range "≈360–510 ตร.กม." (findings:48). That mitigation is honestly stated in the doc — but it means the single precise number in both reports carries an unvalidated ±~20% envelope that the code itself could have reported (it has all the data to run a leave-one-pair-out or drop-sensitivity sweep).
- **Suggested fix:** In `s1_change_detect.py`, print/save the full F1 surface over the grid (drop × absv) and, if another same-pass pre-flood/other-scene pair is available, report threshold stability across pairs; add one sentence to findings documenting the leg-mismatch caveat. Cheap, no new data needed for the sensitivity table.
##### [MEDIUM] (B-03 / F-14) `hecras_lite_channel.md` still carries the pre-fix corridor number (11.95 km² / ~44 ซม.) while everything shipped says 9.94 km² / ~52 ซม.
- **Location:** `analysis/hecras_lite_channel.md:19,30` vs `analysis/river_cross_sections.json`, `goal4_counterfactual_model.py:184`, `tests/test_artifacts.py:24`, both report builders
- **Evidence:** md line 19: "ผิวน้ำกรอบลำน้ำ ≈ **11.95 ตร.กม.** (กว้างเฉลี่ย @+1.5 ม. = 393 ม.)"; line 30: "ระดับลด ~44 ซม.". Current JSON: `corridor_area_km2_at_1p5m = 9.94` (verified locally); the test asserts "~52 ซม. ในกรอบลำน้ำ (corridor 9.94 ตร.กม. จาก hecras_lite หลังแก้ lon-scale)"; goal4's comment records "เดิม hardcode 11.95 จากสูตรผิด". Commit d926f43 switched goal4 to read the JSON and updated reports/tests but did not regenerate this findings doc.
- **Trace of the 44→52 ซม. change (requested check):** after the lon-scale formula fix (commit 8b32689, G-03: "สูตร lon-scale กลับด้าน"), hecras_lite was rerun and wrote 9.94 km² into JSON; M4 drop = min(5.2, V₂₀₀)×10⁶ / A ×100 cm → 5.2/11.95 ≈ 43.5→**44 ซม.** old vs 5.2/9.94 ≈ 52.3→**52 ซม.** new. The mechanism is arithmetically consistent end-to-end (smaller wetted area ⇒ same volume raises/lower stage more). One gap: the goal4 comment attributes the old value to a "+6.1%" formula error, but 11.95/9.94 = +20% — neither doc explains *why* the area itself moved ~17% (plausibly transect sampling changed with the scale fix), so the magnitude of the correction is asserted, not explained.
- **Why it matters:** A reader of the findings doc for the script that produces the number gets a 20%-off value and a stale M4 conclusion; this is exactly the drift the JSON+test chain exists to prevent — except docs are outside its reach. *(Also consolidated with Part D's D-02: the same stale values appear in four more documents — see §5.4.)*
- **Suggested fix:** Regenerate hecras_lite_channel.md §ผล/§M4 from the current JSON (or have `hecras_lite_channel.py` write those two numbers into the md), and add one line explaining what changed between 11.95 and 9.94.

##### [MEDIUM] (B-04 / F-11) HEC-RAS-lite stage-storage and corridor width are referenced to DSM surface (canopy/water at acquisition), not ground — bias partially documented, never quantified
- **Location:** `analysis/hecras_lite_channel.py` (cross-section sampling from `dem_30m.npy`), caveats in `hecras_lite_channel.md:21-23,40`
- **Evidence:** Transects sample the GLO-30 DSM; "stage +0.5…+3 ม." is measured above the local *DSM* thalweg. On rice canopy (~1–3 m) and forest (higher), a level of "+1.5 m above DSM minimum" corresponds to a spatially variable height above true ground, so widths @+1.5 m (9.94 km² corridor, per-section 82–350 m verified in JSON) and the MCM stage-storage table (3.0/9.1/19.7/31.6/60.1) are canopy-referenced approximations. The md correctly says "DEM เป็น DSM … ห้ามใช้เป็น 'ความจุร่องน้ำ' ตรง ๆ" — but the systematic direction/magnitude of bias on the *widths and volumes* (the numbers actually used in M4) is not stated, and the `z_bank p90 > 30 m` filter that keeps only 11/~35 sections also silently drops valid lowland reaches whose banks sit just above 30 m.
- **Why it matters:** The corridor drop (52 ซม.) inherits this bias: if canopy makes the DSM surface locally *higher* than ground, true floodplain area at a given ground-level stage is larger ⇒ real stage drop smaller. M4's "ลดเวลาท่วมริมน้ำ" conclusion is directionally safe (it's an upper bound on storage in-channel), but the doc doesn't say that explicitly.
- **Suggested fix:** One paragraph + one number: estimate canopy-height range over the corridor from land cover (or from S2/SAR-derived water extent vs DEM mismatch already computed elsewhere in the repo) and state the stage-storage table as "DSM-referenced, true-ground values within ±X". Also record how many sections were dropped by the 30 m bank filter.

##### [MEDIUM] (B-05 / F-12) The five Khundan fetchers duplicate parsing/retry logic with inconsistent safety: no row-count or gap validation anywhere, failed chunks degrade to silent empty rows
- **Location:** `fetch_khundan_fullyears.py` (whole file), `fetch_multistation_levels.py:81-91`, siblings `fetch_khundan_training*.py`
- **Evidence:** All five scripts independently implement the same POST + `<tr>` regex parse with `decode("utf-8", errors="ignore")`. None validates output against expectation (~96 rows/station/day ⇒ ~35 k/year): a server layout change, an outage mid-year, or an HTML edit yields shorter CSVs that are written and (for multistation) *hashed as if canonical* — the only signal is row counts in `fetch_info.json`. Persistent chunk failure appends `[]` and continues (`fetch_multistation_levels.py:86-88`, same pattern in fullyears:26-34), with no exit code, no per-chunk failure marker. Behavior also diverges between siblings producing the *same* format: multistation sorts + dedupes + hashes (write_csv :99-109); `fetch_khundan_fullyears.py` writes rows in **server order (new→old within each 6-day block)**, has no `OUT.mkdir` (crashes if `data/16_training_data` is absent — it exists only because the CSVs are committed), and emits no hash file.
- **Why it matters:** These files feed the published backtest (`goal4_model_backtest_long.py`, `goal4_model_multistation.py:44`, `goal4_thachang_model.py:32`); a silent gap in a FULLYEAR CSV would bias RMSE with no repo artifact flagging it. The docstrings show gaps were checked *manually* ("median gap 15 นาที" verified by hand) — the check should be code.
- **Suggested fix:** Extract one shared fetch module (request/retry/chunk/parse + `expected_rows(min_gap=14 min, max_gap=90 min)` validation that exits non-zero on violation), and make every writer sort+dedupe+hash uniformly. If the historical scripts are meant to be frozen provenance artifacts instead, say so in a header comment — currently they read as interchangeable utilities.

##### [MEDIUM] (B-06 / F-13) `rid_cross_section_stage_rating.py`: survey-year columns hardcoded by index with no header check; Ny.7 bankfull (6.86) is the default for all stations
- **Location:** `analysis/rid_cross_section_stage_rating.py:34,93-102`
- **Evidence:** `YEAR_COLS = [(2568, 18, 19), (2567, 20, 21), (2565, 22, 23), (2566, 26, 27)]` — openpyxl column pairs assumed stable; nothing reads the header row to confirm which year sits where. `manning_compound(..., bank_stage=6.86)` defaults to `BANKFULL_MSL`, i.e., Ny.7's bankfull elevation (common.py:25 "ระดับล้นตลิ่ง … เกจ 8.45 − datum 1.59"), applied whenever other stations are evaluated with the divided-channel method.
- **Why it matters:** If RID reorders columns in next year's template, every "multi-year" claim (thalweg deepening 0.42 m, wide-vs-narrow Q comparison — stage_rating.md §4) is silently recomputed on mislabeled years; and compound-n results for non-Ny.7 stations use a bankfull that isn't theirs (Ny.1B's water at peak sits above *both* crests per its own findings doc). Mitigations exist: the raw xlsx is committed with hashes, and stage_rating.md explicitly scopes the divided-channel result to Ny.7 and flags Ny.1B as lower-confidence (§2) — so this is latent robustness, not an active error in shipped numbers.
- **Suggested fix:** Read year labels from the header cells next to each column pair and assert they match; pass `bank_stage` per station (from crest elevations already extracted by `rid_cross_section_extract.py`) instead of a Ny.7 default.
##### [LOW] (B-07 / F-36) Gauge-datum (+1.59 m) printed for stations that don't use it — console output only, shipped JSON is clean
- **Location:** `analysis/rid_cross_section_hydraulics.py:73,83`; `analysis/rid_cross_section_extract.py:88`
- **Evidence:** The hydraulics loop covers both Ny.7 and Ny.1B (`("Ny.1B", 11.07, 11.0)` at :73 — note its true gauge offset ≈ −0.07 m), yet every per-stage line prints `เกจ {stage + GAUGE_OFFSET}` with the Ny.7-only 1.59 (:83). Extract prints `lower crest -> gauge (crest+1.59)` for **all nine** stations including Kgt.30 (:88). Shipped artifacts are unaffected: the hydraulics JSON stores per-station peak gauge from the hardcoded tuple (:107-108) and extract's JSON stores MSL only (:60-65,90).
- **Why it matters:** Anyone transcribing console output (or a future script reusing these prints as data source) propagates a ~1.7 m gauge error for 8 of 9 stations.
- **Suggested fix:** Make the offset per-station in both loops (a small `{stem: offset}` dict, Ny.7=1.59, others from their registry), or label the column "เกจ(Ny.7 datum)" to remove ambiguity.

##### [LOW] (B-08 / F-37) `s2_water.py` writes its output with a CWD-relative path while everything else in the script is repo-anchored
- **Location:** `analysis/s2_water.py:101` vs :24
- **Evidence:** Line 101: `Path("analysis/s2_water.json").write_text(...)`; line 24 defines `PROJ = Path(__file__).resolve().parent.parent` and all inputs use it. From any CWD other than the repo root, running the script creates a stray `analysis/` folder next to the caller and silently leaves the canonical artifact stale.
- **Why it matters:** Inconsistent with every sibling script; breaks scripted invocation from subdirectories or CI working dirs; the pipeline runner (`run_all`) happens to work only because it runs from root.
- **Suggested fix:** `Path(PROJ / "analysis/s2_water.json")`.

##### [LOW] (B-09 / F-38) `gistda_georef_compare.py`: out-of-frame grid cells are clamped to map edges without a containment check, and its cell-area formula disagrees with the canonical one by ~0.7%
- **Location:** `analysis/gistda_georef_compare.py:38-39,63` vs `common.py:28-31`
- **Evidence:** `px = np.clip(np.rint(...), 0, W-1)` / same for py — any grid cell outside the GISTDA map frame (lon 100.754–101.665°, lat 13.934–14.541° per findings §3) is silently mapped to an *edge pixel* of the flood mask rather than "outside". Currently harmless because the NN province bbox sits inside the frame, but nothing enforces that. Separately, line 63 computes cell area as `res·(111320·cos φ̄) × res·110574` while canonical `common.cell_km2` uses `res²·111.32²·cos(14.2°)` — a ~0.68% constant-factor difference (110574 vs 111320), so GISTDA-side areas in findings §7 (e.g., 442.7 km²) are on a slightly different area basis than our side (433.3 km²).
- **Why it matters:** F1/IoU are ratio-based so the bias is negligible for them, but absolute-area comparisons between the two layers in that doc carry an undocumented ~0.7% systematic offset, and the clip would become a real edge-leak bug if the province mask or map frame ever changed.
- **Suggested fix:** Mask cells outside `[x0,x1]×[y0,y1]` before/after the affine instead of clipping; import `cell_km2` from `common.py` for both sides (or document why this script deliberately differs).

##### [LOW] (B-10 / F-39) Two georef experiment scripts are orphaned without any in-code status marker, and one contains a misleading constant
- **Location:** `analysis/georef_fit.py`, `analysis/georef_corner_match.py:60,82`; artifacts `_georef_fit.json` (and per findings §1 also corner-match outputs) under `data/08_dem_topography/satellite_gistda_28sep02oct/`
- **Evidence:** Neither script's header says "experimental / superseded by georef_gistda.py". The outcomes *are* documented at data level — `georef_progress.md:37-42` marks the corner-matching round "ยังไม่ถึงระดับใช้งาน · ถูกแทนที่แล้ว" (median 55.7 px, <20 px only 28%) and ❌-marks SIFT/ORB — but a reader discovering these scripts via code search gets no signal that they are dead ends; their output files sit next to the *accepted* `_georef_gistda.json`. In `georef_corner_match.py:60`, `MERC = 1/cos(14.24°)` is used as an aspect-ratio gate with ±6% tolerance (:82): at this latitude plate carrée (ratio ≈ 1.0005) and UTM-style anisotropy both pass, so the filter discriminates nothing — a misleading name for a no-op check in a script whose whole purpose was to tell projections apart.
- **Why it matters:** Future maintainers may "fix" or re-run a superseded experiment, or trust its params file; the repo's own lesson (wrong method, documented) lives only in prose outside the code.
- **Suggested fix:** Add a 2-line header to each: "EXPERIMENTAL — replaced by georef_gistda.py on 6 Oct 2026 (see data/…/georef_progress.md); keep for provenance". Optionally rename the MERC gate or delete it with a comment.

##### [NITPICK] (B-11 / F-56) `s1_masks.py` merge/reproject assumes DEM nodata=−32767, but the raw tiles are float32 with no header nodata
- **Location:** `analysis/s1_masks.py:67-82` vs verified tile metadata (`Copernicus_DSM_COG_10_N14_00_E101_00_DEM.tif`: `nodata=None`, dtype float32; sampled window over the plain min −1.12 m, no sentinel values present)
- **Evidence:** `merge(..., nodata=-32767.0)` + `reproject(src_nodata=-32767, dst_nodata=nan)`. No cell in the data equals that value (it's an int16 sentinel; terrain here is float down to −1.12 m), so the assumption is currently inert — uncovered regions still correctly become NaN via merge's fill → reproject mapping. Negative terrain (<0 MSL) passes through fine (`lowland = dst < 60`).
- **Why it matters:** Purely latent: if a future tile generation or different DEM source starts using a real sentinel, the mask silently eats those cells (or keeps garbage). One comment line would record that this value was checked against the actual tiles.
- **Suggested fix:** Read `ds.nodata` from one tile at load time and pass it through; if None, use 0 or skip the nodata path — with a comment citing the verified metadata.

##### [NITPICK] (B-12 / F-57) Peak-map figure bakes district areas/labels into text instead of reading them from tracked data
- **Location:** `analysis/s1_peak_flood_map.py` (caption/legend assembly; loads `flood_peak_27sep1828.npy` at :22)
- **Evidence:** The published PNG's per-district numbers and the rule caption (:135-136, see B-01) are assembled as figure text rather than derived from `s1_flood_series.json`/the npy itself. Re-running the script after any data change produces a figure whose embedded labels may no longer match its own pixels — with nothing to catch it (no test reads PNG text).
- **Suggested fix:** Compute displayed areas from the loaded arrays at render time; keep only units/station names as literals.

##### [NITPICK] (B-13 / F-58) Georef "GCP residual = 0.0 px" is structurally zero and reads like an independent check it isn't
- **Location:** `analysis/georef_gistda.py` (residual computation), reported at `gistda_georef_findings.md:42` ("residual ที่ GCP = 0.0 px ทั้ง 4 จุด")
- **Evidence:** A 4-parameter affine fit through 4 points interpolates them exactly; the residual is a tautology of least-squares-with-equal-dof, not evidence of accuracy. The *informative* validation (chamfer vs OSM boundary, area cross-check, offset search, negative controls — findings §4) was properly done, so no number is in doubt.
- **Suggested fix:** One clause in the doc: "residual ที่จุด fit เป็น 0 โดยโครงสร้าง (พารามิเตอร์เท่ากับจำนวน GCP) — การยืนยันจริงคือข้อ 4". Prevents a future reader from counting it as one of three validations.

#### Review questions answered (explicit checks requested for this part)

1. **Is F1=0.70 rigorous?** Partially. It is *stable* with respect to co-registration (three explicit tests, findings §7) and honestly caveated (composite vs single-pass; 40% area gap attributed to paddy-water/wetland definitions with a ratio-scaled range). What it is not: out-of-sample — one calibration pair, quantized grid, no holdout, cross-leg transfer (B-02), and the headline scene itself has zero independent validation. The published range 360–510 km² is the defensible number; "509.3" as a point estimate overstates precision by ~one order of magnitude relative to what was actually validated.
2. **The 62.2 vs 8.3 km² discrepancy (27 Sep 06:00 scene):** No internal contradiction found — it is one deliberate argument, stated consistently in `s1_flood_extent_findings.md:29` and `s1_flood_series.json` (tracked copy of the pairs-animation output: 62.2 = ours, Pakchong 51.6 + Mueang 10.6, within a 34%-coverage band; 8.3 = GISTDA's product from the same source scene). The logic — gauge Ny.7 ≈ 9.13 m at acquisition ⇒ flood extent should be near-peak ⇒ GISTDA's 8.3 must be an under-detection (heavy rain / rough water surface defeats their auto-detect) — is sound but *inferential*; it rests on the gauge reading, not on a second independent observation. Note the doc uses GISTDA asymmetrically across dates (Oct 2: scale *us down* by their ratio; Sep 27: declare *them* wrong) and addresses this explicitly in §48 — a reviewer should still be aware both directions are judgment calls.
3. **Corridor area / M4 drop change (11.95→9.94 km², 44→52 ซม.):** Fully traced (B-03): lon-scale formula fix → rerun wrote 9.94 to JSON → goal4 switched from hardcoded 11.95 to reading the JSON in d926f43 with tests+reports updated same commit; arithmetic checks out exactly (V/A scaling). Only gap: the *mechanism* behind the 17% area shift is asserted ("สูตรผิด") but never explained, and the "+6.1%" comment doesn't match the observed magnitude.
4. **Georef experiments marked inconclusive in code?** No — only in `georef_progress.md` (data folder) and findings §1 prose. The two dead-end scripts carry no header status (B-10).

#### Open questions / needs-owner-decision

- **Which S1 rule is canonical for publication** (fixed triple VH+VV vs calibrated single-VH)? This decides whether B-01 is a doc fix or a re-run of the peak map — and if it's a re-run, 509.3 km² and every downstream number citing it (reports, tests) move.
- **DSM-referenced stage-storage:** accept with an explicit ± band (B-04), or invest in a ground-surface proxy before M4 numbers are quoted with more precision than they currently carry?
- **Fetcher scripts:** consolidate into one shared module now (recommended; B-05 blast radius reaches the published backtest), or freeze them as provenance artifacts with explicit headers — but pick one, since today's ambiguity is the risk.
### 5.3 Part C — Report builders & HTML output quality

*Synthesis.* The report pipeline is the most disciplined part of the repo on build mechanics — fail-loud asset embedding, canonical presence guards regenerated from source data, deterministic and fully self-contained HTML — but that discipline has a structural blind spot: the guard only checks string *presence* in hand-written templates, so any single number correction requires manual edits across 4+ sites (F-02), and the rating-curve coefficients — the formula most likely to change next per the report's own §6.9 plan — sit outside the check list entirely, duplicated in three scripts plus both appendices (F-03).

#### Scope reviewed (files actually read)
- `report/build_report_html.py` — 426 lines, full
- `report/build_expert_report.py` — 487 lines, full
- `report/report_assets.py` — 448 lines, full
- `report/make_x_charts_thai.py` — 85 lines, full
- `analysis/build_canonical_numbers.py` — 140 lines, full
- `tests/test_artifacts.py` — read (asserts e.g. `j["actual"][1] == 65`)
- Both built outputs scanned: `report/น้ำท่วมนครนายก2569_ประชาชน.html`, `report/น้ำท่วมนครนายก2569_วิชาการ.html` (MIME magic bytes, external URL scan, leftover-placeholder pattern)
- `report/assets/` directory listing (35 files + mtimes), cross-referenced against both builders' `imgs` dicts

#### Strengths
1. **Fail-loud builds.** `b64()` raises `FileNotFoundError` on any missing asset; after substitution each builder scans the final HTML for residual `__KEY__` tokens and exits with the offending keys (`build_expert_report.py:473-475`, same pattern in public builder). A dropped image cannot ship silently.
2. **Canonical presence guard.** Both builders require every string in `CANON["checks"]["public"/"expert"]` to appear verbatim in the final HTML or exit with a pointer at `analysis/canonical_numbers.json` (`build_expert_report.py:477-483`). The checks list is *regenerated from source data* by `build_canonical_numbers.py`, so if analysis results move without template edits, the build breaks instead of publishing stale numbers. This is a genuinely good pattern for this project's risk profile (numbers already revised at least once: 65 ชม. ± uncertainty framing).
3. **Deterministic output.** No wall-clock timestamps in any builder (rg for `time.`/`now()` in `report/*.py` → zero hits outside data parsing); identical inputs give byte-identical HTML; saved size is printed.
4. **Self-contained, offline-capable HTML.** Public `b64()` is MIME-correct (`build_report_html.py:15`: `.jpg→image/jpeg`). Zero external http(s) resource loads in the public report; the expert report's only URL is a `curl` example inside a `<pre>` reproduction block (`build_expert_report.py:341`) — not a fetch.
5. **Chart generation separated from composition.** `report_assets.py` produces PNGs; builders only embed them, so charts can be regenerated without touching 100KB+ templates.

#### Findings

##### [HIGH] (C-01 / F-02) Headline numbers hand-maintained in 4+ places per number; canonical check is presence-only
- `rg -c` over key literals (`8.45`, `9.23`, `509`, `1,058`, `65 ชม.`): hits concentrated in `build_report_html.py` (31), `build_expert_report.py` (36), `report_assets.py` (15 — chart axis annotations/titles), plus `tests/test_artifacts.py:16` (`== 65`).
- The guard only checks that the *string* appears in HTML. The string comes from hand-written template text, so any single data correction means manual edits in both templates **and** every hard-coded annotation inside chart scripts **and** test expectations — with no tooling to list the affected sites.
- Why it matters: this is a recurring cost (the project has already revised numbers) and the exact location of "published report disagrees with analysis" risk. *(Same drift class as F-18 / D-03's two rain-range variants, §5.4.)*
- Suggested fix: have `build_canonical_numbers.py` also emit check strings for values that currently live only in chart code (annotations, rating coefficients — see next finding), so drift anywhere in the pipeline breaks the build; longer term, inject numbers into templates from `canonical_numbers.json`.

##### [HIGH] (C-02 / F-03) Rating-curve formula duplicated across 3 scripts and both HTML appendices
- `Q = 242·(h−4.55)^0.66` (and its inverse) appears in: `report/report_assets.py:63-69` (`q_of`/`stage_of`), `report/make_x_charts_thai.py`, the public template appendix ข, and expert §3.2 — all four files matched `rg "242.*0.66"`.
- Why it matters: these coefficients are **not** in the canonical checks list, so drift here is silent (unlike headline numbers). The report itself flags rating uncertainty (−18% at peak, hysteresis) and plans a survey-based Ny.1B rating (§6.9) — i.e., this formula is the one most likely to change next.
- Suggested fix: single shared module (e.g. `analysis/rating.py`) imported by both chart scripts; `build_canonical_numbers.py` consumes it too and emits its coefficients into the checks lists.
##### [MEDIUM] (C-03 / F-15) Dam release series triplicated: CSV + hard-coded dict + expert appendix table
- `report_assets.py:60` loads `dam_khun_dan_daily_2013_2026.csv` into `dam` (used only for chart C3); lines 61-62 then hard-code the same days in a second structure:
  ```python
  rel_daily = {"2026-09-24": 1.50, ..., "2026-09-27": 31.66, ...}   # used for chart C2
  ```
  and the identical values are hand-transcribed again in expert appendix table 10.1 (`build_expert_report.py:401-407`, e.g. `<b>31.66</b>`).
- Why it matters: this is precisely the dataset the report itself documents as discrepant (+37.4 ลลบ.ม. between API and project-web cumulative outflow, §7 item 2). If the CSV is corrected, chart C2 and table 10.1 silently diverge; no check covers these values.
- Suggested fix: derive `rel_daily` from the already-loaded `dam` dict filtered to 24 ก.ย.–2 ต.ค.; keep the appendix as the only manual copy (or add its cells to canonical checks).

##### [MEDIUM] (C-04 / F-16) `make_x_charts_thai.py` missing from every documented build chain
- The expert report's own reproduction guide §8 (`build_expert_report.py:367`) says:
  ```
  python report/report_assets.py && python report/build_report_html.py && python report/build_expert_report.py
  ```
  — it omits `make_x_charts_thai.py`, the sole producer of `x1_rating.png`/`x2_hydro3.png`. rg finds no mention in README.md / START_HERE.md / HANDOFF.md / docs/. The PNGs exist only because they are committed (mtime Oct 8).
- Why it matters: a fresh clone following documented steps never regenerates x1/x2; if `khundan_tele_event_data.json` is updated, those charts go stale with **no** guard at all (unlike the goal4 PNGs, which at least warn-if-missing in `report_assets.py`).
- Suggested fix: insert `python report/make_x_charts_thai.py` into §8 before `report_assets.py`; mirror in START_HERE.md build order.

##### [MEDIUM] (C-05 / F-17) No freshness coupling between analysis outputs and embedded charts
- Builders embed bytes unconditionally; the only guard anywhere is a copy block in `report_assets.py` that **warns (does not fail)** when `goal4_model_v1_event.png` / `goal4_counterfactual_model.png` are absent from their `analysis/` source locations. No mtime/hash comparison exists in any builder.
- Why it matters: re-running an analysis script with different parameters — or one that fails before its final `savefig` — leaves a stale chart beside canonically-checked new text, and the build still passes green.
- Suggested fix (cheap): builders compare each asset mtime against its declared producer output and warn; (stronger): producers write a small `.meta.json` (input hashes + key numbers) that builders cross-check before embedding.

##### [LOW] (C-06 / F-40) `c5_floodhub.png` has no producer and is not documented as manual
- Only reference in the whole repo: `build_expert_report.py:25`. File mtime Oct 5; no script writes it; §8's "browser steps" note (line 371) covers FB/CDSE but not this screenshot.
- Why it matters: if the FloodHub dashboard state changes, there is no documented way to refresh this figure — a silent-staleness path specific to one image.
- Suggested fix: document provenance/capture steps + date in §8 or `docs/DATA_SOURCES.md`, or remove from the expert report if it's not load-bearing.

##### [LOW] (C-07 / F-41) Expert builder hard-codes `image/png` MIME; `__MAP__` is actually a JPEG
- `build_expert_report.py`'s `b64()` declares `image/png` for every key, yet `imgs["MAP"] = frame_PEAK_OURS.jpg` (line 23). Output scan: exactly **1** occurrence of `data:image/png;base64,/9j/` (JPEG magic under PNG MIME) in the expert HTML; public builder handles this correctly (`build_report_html.py:15`).
- Why it matters: cosmetic — browsers sniff and render fine — but inconsistent with the public builder and technically invalid for strict validators/proxies.
- Suggested fix: reuse the MIME-aware `b64` from the public builder (it's 3 lines).

##### [LOW] (C-08 / F-42) Dead code / unused entries in the report pipeline
- `build_report_html.py:31`: `"G5": b64(ASSETS / "frame_20260928_1819.jpg")` — `__G5__` appears nowhere in the template (rg count = 1, the dict entry itself). Wasted ~270 KB read+encode per build and a misleading signal about report contents.
- `report_assets.py:70`: `QBANK = q_of(8.45)` — computed, never used.
- `report_assets.py` (~lines 258-261): reservoir-label block computes `cx`, `cy` then draws nothing (dead branch).
- Redundant imports in `report_assets.py`: `matplotlib.colors as mcolors` re-imported mid-file; local `from datetime import datetime` shadows the module-level `import datetime`.
- Suggested fix: delete all four; add a lint pass (`pyflakes`) to CI if not already present.

##### [NITPICK] (C-09 / F-59) `CANON["values"]` payload has zero consumers
- `build_canonical_numbers.py` writes both `"values"` and `"checks"`; rg across all `*.py` finds **no** read of `["values"]` — only the checks lists are used (`build_expert_report.py:477`, public twin).
- Why it matters: implies a wiring path that doesn't exist; future readers may assume templates already read values from JSON.
- Suggested fix: either wire one consumer (e.g. generate chart-annotation check strings from `values`) or drop `"values"` and document `checks` as the sole interface.

#### Open questions / needs-owner-decision
1. One-off event report vs. living artifact: is manual number sync + presence checks acceptable, or should templates be generated from `canonical_numbers.json` (larger refactor)?
2. Is `c5_floodhub.png` still needed in the expert report, and what is its update policy?
3. §8 currently sits in a mixed state for derived PNGs: goal4 charts have warn-if-missing copies, x1/x2 have nothing, m_*.png (from `analysis/goal4_*` scripts) are neither copied nor listed. Decide one rule: "analysis scripts own their PNGs, §8 lists them" vs. "report_assets.py owns all chart assets".
### 5.4 Part D — Methodology, documentation & internal consistency

*Synthesis.* The documentation architecture is genuinely strong — a frozen `canonical_numbers.json` generated by script and enforced into both HTML builds, uncertainty bands carried through every scenario, and known-wrong intermediates published *with* their correction path — but its failure mode is **propagation lag after corrections**: fixes land in canonical/secondary docs (JSON, DATA_DICTIONARY, reports) while the primary source findings docs keep superseded numbers (F-14), stale status snapshots survive (DATA_SOURCES, geotag counts), and scenario vocabulary drifts across the doc set. No underlying number is wrong — everything reconciles to its artifact; this is a documentation-loop problem, not a methodology error.

**Scope:** `docs/` (METHODS, ANALYSIS_PLAN, DATA_DICTIONARY, DATA_SOURCES, LEGAL_REVIEW, ENVIRONMENT), `START_HERE.md`, `HANDOFF.md`, `README.md`, `THIRD_PARTY_NOTICES.md`, `report/รายงาน.md`, `analysis/canonical_numbers.json` + core findings docs (goal4_counterfactual_model_vs_nomodel, goal4_model_v1_findings, qa3, qa5_18day, scenario_analysis, khundan_tele_findings, rid_cross_section_findings, album_geotag_summary), `data/` manifests. Verified by cross-grep of every headline number and git history (`log -25`).

#### HIGH

##### D-01 (F-04) · Master report uses the *known-wrong* 62 h baseline in §4
`report/รายงาน.md:104` — QA5 summary says "เวลาเหนือตลิ่ง **62**→12 ชม." but its own source doc explicitly flags 62 as a data artifact: `analysis/qa5_18day_rain_drainage_counterfactual.md:74` — "(ระวัง: ถ้าคำนวณจากฟีด thaiwater ตรง ๆ จะได้ 62 ชม. เพราะฟีดขาดแถวเที่ยงคืน 3 แถว — **ค่าที่ถูกคือ 65 ชม.**)". Canonical (`canonical_numbers.json: counterfactual.actual.hours_above_bankfull = 65`) and the report's own §2 (`รายงาน.md:54` "≥8.45 ม. นาน 65 ชม.") both say 65 h. The report contradicts itself (line 54 vs line 104) by quoting the corrected-away value in its headline scenario sentence.

##### D-02 (F-14, with B-03) · M4 corridor numbers stale in 5 documents after the G-03 correction
Commit `d926f43` fixed the lon-scale bug: corridor area 11.95 → **9.94 km²**, drop 44 → **~52 ซม.** (`goal4_counterfactual_summary.json: M4_volume_budget {area_corridor_km2: 9.94, corridor_drop_m: 0.522}`; `DATA_DICTIONARY.md:100`). But the *primary* M4 document and three others still carry the pre-correction "~12 ตร.กม. / ~44 ซม.":
- `analysis/goal4_counterfactual_model_vs_nomodel.md:25` and `:64` (the origin doc for M4)
- `docs/ANALYSIS_PLAN.md:76` (D2)
- `analysis/firo_dynamic_rulecurve_proposal.md:10` and `:22`
- `analysis/hecras_lite_channel.md:30`

The correction propagated to DATA_DICTIONARY/report/tests but not to the source docs — exactly backwards. A reader of the M4 doc gets the superseded numbers with no pointer to the fix. *(Consolidated here with Part B's B-03, which traces the 11.95→9.94 / 44→52 ซม. mechanism end-to-end; see §5.2.)*

#### MEDIUM

##### D-03 (F-18) · Headline rain range exists in two variants, neither canonicalized
Exact per-station min–max **1,058–1,416 มม.** (qa5 table `:11`: นางรอง 1,416 … ท่ามะปราง 1,058) is used by README ×4 (`README.md:12,14,26,47`) and report §4 (`รายงาน.md:104`). The rounded **1,050–1,420 มม.** is used in the *same report's* exec summary + §2 (`รายงาน.md:11,48`), plus qa3 (`:16,81`), scenario_analysis (`:51`), event_timeline_sep2026 (`:43`), khundan_tele_findings K6 (`:61`), qa4_forecast_crosscheck_tee (`:27,53`) and data/04 + data/11 manifests. Both refer to the same 6-station set; rounding was applied outward in some places only. Neither variant appears in `canonical_numbers.json` or `DATA_DICTIONARY`, despite being *the* headline trigger figure — a gap against the project's own "ทุกตัวเลขหัวใจอยู่ใน canonical" policy (`build_canonical_numbers.py`).

##### D-04 (F-19) · Three release rates + two scenario number-pairs, weak labeling
All documented in source docs but easy to misread when adjacent:
- 31.66/วัน = actual; **12.1** = F-SC1 "ไล่น้ำเก็บลง URC ตั้งแต่ 30 ส.ค." (`scenario_analysis.md`, `รายงาน.md:17,89`); **13.9** = goal4 R1 strict daily-URC table (`goal4_counterfactual_model_vs_nomodel.md:21`, qa5 `:66`).
- Outcomes: B2 row of the same status table cites qa5 sims (−78%/−94%, 65→8–12 ชม. — `ANALYSIS_PLAN.md:61`) while D2 two lines below cites goal4 R1/M2 (−55%/−93%, 18/8 ชม. — `:76`); the reason qa5-S1 ≠ R1 lives only in a footnote (`goal4_counterfactual_model_vs_nomodel.md:32`: "ต่างจากตารางนี้เพราะไม่ได้บังคับความจุอ่างวันที่ 26–27").
Recommendation: name scenarios (S-URC / S-plan / M2/M3) once and cross-reference at every use; add the capacity-constraint caveat inline in ANALYSIS_PLAN B2.

##### D-05 (F-20) · Rating uncertainty quoted as both ±18% and ±20% with no bridge
±18% is the systematic under-prediction (khundan_tele K5 `:53` "ช่วงน้ำสูงสุดต่ำกว่าจริง ~18%") and drives scenario error bars (counterfactual `:30,92`, firo `:42`, ANALYSIS_PLAN D2 — incl. the ±0.85 ม. peak band). ±20% is the quoted use-band (report `รายงาน.md:55`, K5 "กำกับ ±20%", ny7_flow_stats `:3`). Both are defensible, but no doc states the relationship ("bias ≈18% → quote as ±20%"), so a reader sees two different uncertainties for "rating ช่วงน้ำสูงสุด".
##### D-06 (F-21) · DATA_SOURCES.md is a stale phase-1 snapshot
Status markers contradict current state everywhere: §3 TMD "**เฟสถัดไป**" / token "ยังไม่มี" (yet `data/04_tmd_rainfall` exists and 12-station rain drives the analysis); §5 table — DEM "🔄 กำลังดาวน์โหลด", cross-sections "⏳ ยังไม่เริ่ม" (`data/19` + hecras_lite exist), ผังน้ำบางปะกง "⏳" (full 291-pg report in `data/09`, used in report §3.2(ค)), GISTDA "⏳ น่าลอง" (`data/12` done), Sentinel-1/2 "⏳ ยังไม่เริ่ม" (`data/13`,`18` done); §4 tiny.NN album "รอเก็บทั้งอัลบั้ม" (668/732 collected, `รายงาน.md:30`). Also duplicated section numbering — two series of 4–7 (main vs ภาคสนาม supplement). This is the doc README advertises as "แหล่งข้อมูล 20 ชุด + สถานะการเข้าถึง".

##### D-07 (F-22, with Part E) · No authoritative dataset enumeration; count mismatch
README says "หลักฐานต้นฉบับ **20 ชุด**" (`README.md:40,118`) but `data/` holds **21** numbered folders (01–21) plus `manual`. There is no central index table of all 21 sets with status — and `data/manifest.md`, the natural place for it, is an orphaned GISTDA-pass note (7 lines, no title), not an index. Per-folder manifests are excellent; only the rollup is missing/stale. *(Consolidated with Part E's finding that the per-dir manifest invariant has no test gate — §5.5.)*

#### LOW

##### D-08 (F-43) · album_geotag_summary.md stuck at 666 photos
Title + `:7` + `:75` say "จาก 666"; every other doc uses **668** (report `:30,98`, qa3 `:28,35,86`, flood_locations_summary, data/06 manifest, terrain_mueang). Report's gap line "อัลบั้มอีก 64 ภาพ" implies 732 total ✓ — so the summary doc is one collection-batch stale.

##### D-09 (F-26, with Part E) · Duplicate internal review at repo root
Root `REVIEW.gemini.md` is **git-tracked** and byte-for-byte the same document as `docs/reviews/REVIEW.gemini.md`; `.gitignore` excludes only root `REVIEW.md`. So one internal review (deepseek's twin) is hidden while its gemini twin is published twice. README points at `docs/reviews/`. Suggest: untrack root copy or ignore both roots consistently. *(Consolidated here with Part E's publish-policy finding; consolidated severity MEDIUM — §5.5.)*

##### D-10 (F-44) · Typos / mojibake in public-facing text (all verified at cited lines)
- report: "น้ำสูงสุด**สูงสุด**ที่ตัวเมือง" (`รายงาน.md:11`), "แต่การปล่อยน้**้ำหนักสุด** 31.66 ล้าน ลบ.ม./วัน" (`:12`, → น้ำสูงสุด), "**แบมป์รอง**" (`:53`), "คาบ**อบัติ** 100 ปี" (`:78`, should be คาบกลับ).
- `ANALYSIS_PLAN.md:60` — C2 checklist row reads "แยกส่วนฝน/เขื่**่อง**ต่อระดับน้ำ" (→ เขื่อน).
- `goal4_counterfactual_model_vs_nomodel.md:56` — garbled "หน่วยงาน**ตะขิบตะของ**จะทำจริง".
- `khundan_tele_findings.md:53` — "ความแม่", "ช่วงน้ำสูงสุดสุด".

##### D-11 (F-45) · Evidence protocol applied unevenly
[F]/[I] markers are used consistently in the master report and a few findings (ny1b_q668, rid_cross_section) but absent from most `analysis/*_findings.md`; **[O] is effectively unused anywhere** except one file (`ny1b_q668_investigation.md:5`), although METHODS/README advertise `[F]/[I]/[O]` as the project standard. Either apply [O] to social/citizen evidence or drop it from the advertised protocol.

##### D-12 (F-46) · Ny.1B peak level quoted from two feeds, 7 cm apart
Report §2 (`รายงาน.md:51`) uses **11.07 ม.** (gauge feed) at 27 ก.ย. 01:00; khundan_tele K2 table shows **11.00 ม.รทก.** same time, and K1 asserts Ny.1B "gauge ≈ รทก. โดยตรง" — the 7 cm gap is hand-waved with "≈" (`khundan_tele_findings.md:16`) while Ny.7's analogous gap (7.64 vs 7.68) got an explicit DATA_DICTIONARY note. Minor, but worth a one-line caveat at the report citation.

*Also noted in this part (not counted as findings): `รายงาน.md:99` "≥307–500 ตร.กม." and `:101` "พิสัย ~360–510" are two different claims for peak extent in adjacent bullets without a pointer; `:97` "สอดคล้อง ±คูณ 2" is unparseable phrasing.*

#### Verified consistent (checked, no issue)
- **Test count 26** identical in README (`:41,77,82`), START_HERE `:33`, HANDOFF `:9` (breakdown 14+5+7 ✓), ENVIRONMENT `:34`.
- **SHA-256 681 OK / 0 mismatch** consistent (README `:83`, HANDOFF `:10`); "723 artifacts" in reviews = 681 + 42 skipped >5 MB — arithmetic reconciles.
- Canonical cross-checks: overflow 11.89→"~12 ลลบ.ม.", R1 −55% (5.39/11.89 ✓), M2/M3 −93%, hours 65/18/8/9; S1 peak 509.3↔"509 ตร.กม."; dam share 11.8→12% / 58.9→59%; datum +1.59±0.02 → 7.64 ม.รทก.; bankfull 8.45 เกจ / 8.21 รทก. — all agree across METHODS, DATA_DICTIONARY, report, khundan_tele, qa4.
- **7.64 vs 7.68** (offset-derived vs direct feed) is explicitly documented (counterfactual table note + DATA_DICTIONARY).
- Time windows arithmetic: ≥8 ม. = 79 ชม. (26/18→30/01 ✓), ≥8.45 = 65 ชม. (26/23→29/16 ✓); Ny.7 Q peak 626.6 @ 14:00 vs level peak 10:00 consistently separated everywhere; lag "~9 ชม." matches 01:00→10:00.
- Evidence counts: FB 129 โพสต์/209 ภาพ (report `:26` = fb_page manifest ✓), รายงานโครงการ 231 ไฟล์ ✓, album 668+64=732 ✓, URC scenario table arithmetic (−62%, −17.6 ลลบ.ม.) ✓, "สูงสุด ~1.9 เท่า" = 626.6/323 ✓.
- mitrearth villages **400 vs 486** is explained, not contradictory: original FLOOD.rar 400 = labeled-risk subset of the full 486-point registry (`mitrearth_full_set_assessment.md:9,25`); report uses each number for its own dataset correctly.
- GISTDA series (11.8 → 306.9) and our S1 cross-check (P=0.60/R=0.84, 436 vs 306.9) consistent between report §4, canonical and `data/manifest.md` note.

#### Methodology assessment
**Strengths.** The project's documentation architecture is genuinely strong: a frozen `canonical_numbers.json` generated by script, with `checks.public/expert` strings enforced into both HTML builds by tests; explicit uncertainty bands carried through every scenario (±6 ชม., rating ±18/20%); datum solved and cross-validated from two independent feeds; the report separates [F]/[I] per claim; known-wrong intermediates are *published* with their correction path (the 62 h case, M4's 3 ซม. trap at counterfactual `:64`, the 566658 outflow base mismatch); reviews retained in-repo with fix-status tracking (G-01…G-07).

**Weaknesses.** The failure mode is *propagation lag after corrections*: fixes land in canonical/secondary docs but not primary source docs (D-02), stale status snapshots survive (D-06, D-08), and scenario vocabulary drifts across the doc set (D-04). None of these are methodological errors — the underlying numbers all reconcile to their artifacts — but for a project whose selling point is "ทุกตัวเลขทำซ้ำได้", the docs should close the loop: add the rain range + M4 corridor values to canonical_numbers.json, refresh DATA_SOURCES as a live 21-row table (or move status into per-folder manifests only and drop it from README), unify scenario names, and fix the D-01/D-10 line-level typos in the public report.
### 5.5 Part E — Tests, CI & repo hygiene

*Synthesis.* The test/CI/hygiene layer is small but honest: the "26 tests" claim is true and fast (verified `26 passed in 0.37s`), artifact-anchored drift guards genuinely re-derive published numbers from committed JSON/HTML, and the raw-first policy — manifests with SHA-256 in every data dir, big binaries kept out of git — matches reality. The gaps are all about *enforcement*: CI certifies a different interpreter than the documented production environment (F-23), the size-based `--quick` skip lets ~70 MB of tracked canonical evidence escape hashing entirely (F-25), and several strong claims ("681 files verified", dataset count, manifest invariant) rest on one-time local runs or developer discipline rather than any gate.

#### Scope reviewed
Files read in full:
- `tests/test_core.py` (175 lines) — 14 tests; artifact-anchored by design (docstrings forbid self-contained arithmetic tests)
- `tests/test_artifacts.py` (61 lines) — 5 tests pinning headline numbers from committed JSON/HTML artifacts
- `tests/test_integrity.py` (101 lines) — 7 tests for `verify_data_integrity.py` (3 manifest formats, OK/MISMATCH/MISSING/DELETED exit codes, ambiguous-basename warning)
- `.github/workflows/ci.yml` (24 lines) — single `test` job: checkout → setup-python "3.13" → `pip install -r requirements.txt` → `pytest tests/ -q` → `verify_data_integrity.py --quick` with exit-code mapping (1=fail, 2=pass, >2=fail)
- `analysis/verify_data_integrity.py` (305 lines) — coverage/policy angle: 4 manifest formats, `--quick` = skip files >5 MB by on-disk size (`max_bytes = 5 << 20`, line 262; check at line 234), exit codes 0/1/2, exceptions file optional
- `.gitignore` (72 lines) — raw-first policy: large binaries ignored everywhere; deliberate negations for small evidence images and report HTML
- `requirements.txt`, `pyproject.toml`, `docs/ENVIRONMENT.md`
- `index.html` (link targets verified), README.md / START_HERE.md (file references extracted and existence-checked)

Commands run (key outputs):
1. `python -m pytest tests/ -q` → **`26 passed in 0.37s`** (local CPython 3.14.5, pytest 9.1.1). Exit 0. Matches the documented "26 tests" claim exactly (README.md:41,77,82 · START_HERE.md:33 · ENVIRONMENT.md:34). Test-function count: 14 + 5 + 7 = 26 ✓
2. `git ls-files | wc -l` → **1082 tracked files**. `git count-objects -vH` → loose 442 / 82.54 MiB, pack 65.72 MiB. `.gitattributes` = only `* -text` (no LFS patterns); git-lfs 3.7.1 is installed locally but **Git LFS is NOT used**
3. Tracked files >10 MB: exactly one — `data/08_dem_topography/satellite_gistda_28sep02oct/S__5980182_gistda_28sep02oct.jpg` (15,332,518 B), deliberately whitelisted via `.gitignore:51`. The 56/135/137 MB PDFs in `data/09_plans_standards/` are on disk only (dir total 327 MB) and **not** tracked (`git ls-files data/09_plans_standards` → only `manifest.md` + one extracted .txt); ignored by global `*.pdf`
4. Strays: `_tmp_tiles/` (412 KB) and `.workbuddy-ai/` (52 KB) exist untracked but **are** ignored ✓; no tracked `__pycache__`/`.pytest_cache` files (`git ls-files | grep -icE pycache` → 0) ✓; `report/__pycache__/` exists on disk, ignored by pattern ✓. But **`_v1_out.txt` (4,353 B) is tracked in git** and matches no ignore rule — a temp artifact committed against the repo's own `_tmp_*` policy
5. Duplicates: root `REVIEW.gemini.md` (33,449 B) and `docs/reviews/REVIEW.gemini.md` have **identical SHA-256** (`0fb6d0…`) — both tracked → byte-for-byte duplicate in git. Top-level `REVIEW.md` (28,730 B) is untracked + ignored ✓ per policy. `archive/reviews/REVIEW.gemini.md` differs (84,573 B) but `archive/` is intentionally untracked ("ดึงมาจากประวัติ git ก่อนลบ .git"). `HANDOFF.md` (9,586 B, mtime 10-08 13:16) vs `archive/HANDOFF.md` (26,300 B, older snapshot) — different by design; top-level is the current one
6. Index/README references: all targets of `index.html` exist (`report/น้ำท่วมนครนายก2569_ประชาชน.html`, `..._วิชาการ.html`, `START_HERE.md`). 36 backticked file refs extracted from README.md + START_HERE.md — every concrete path exists (unprefixed ones resolve under `analysis/` or `report/`; the only "misses" were glob patterns like `analysis/*_findings.md`)
7. Manifests: **all 21 numbered dirs `data/01..21` have `manifest.md`** ✓; extras `_hashes.txt`: 01(3), 10, 12(2), 15, 16(4), 20 + top-level `data/18_sentinel2_hashes.txt`. `data/INTEGRITY_EXCEPTIONS.md` does not exist (tool handles absence gracefully — returns {})
8. CI: single job, python "3.13" only, **no pip cache**, triggers on all pushes + PRs, no secrets used, no report-build/determinism step

#### Strengths
- The published test claim is true and fast: `26 passed in 0.37s`, matching README/START_HERE/ENVIRONMENT.md verbatim ("ต้องได้ 26 passed").
- Tests are deliberately artifact-anchored: test_core.py's header explicitly bans self-contained arithmetic tests; several tests re-derive published numbers from real committed artifacts (`goal4_model_v1_results.json`, the actual rain CSV, canonical HTML) so a re-run with shifted results fails CI — a genuine drift guard.
- "ทุกชุดมี manifest + SHA-256" verified: all 21 numbered data dirs carry `manifest.md`; large raw binaries (17 GB Sentinel-1, 327 MB PDF scans, DEM raw) are consistently kept out of git with hashes in manifests — policy and reality agree.
- No LFS complexity needed: only one tracked file >10 MB (a whitelisted evidence photo); `.gitattributes` `* -text` deliberately freezes line endings so manifest SHA-256s stay stable cross-platform, matching the CRLF pitfall documented in ENVIRONMENT.md.
- Dependency docs are internally consistent: requirements.txt pins match the ENVIRONMENT.md table exactly (numpy 2.5.1 … pytest 9.1.1), pyproject.toml carries compatible lower bounds and documents why it has no build-system; opencv is explicitly documented as optional for three experimental scripts only.
- CI's integrity gate maps exit codes with intent: MISMATCH(1) fails, MISSING(2) passes because big files live outside git by design — the comment says exactly that, and test_integrity.py locks each code down.
- Repo hygiene baseline is clean: 0 tracked cache/temp paths (except one stray, see findings), `.nojekyll` present for Pages, every link in index.html and every concrete file reference in README/START_HERE resolves.

#### Findings
##### [MEDIUM] (E-01 / F-23) CI validates a different interpreter than the documented production environment
- **Location:** `.github/workflows/ci.yml:14` vs `requirements.txt:3`, `docs/ENVIRONMENT.md:9`
- **Evidence:** ci.yml pins `python-version: "3.13"`; requirements.txt header says versions were pinned because they were "รันจริงและผ่านเทสต์ บน Windows + CPython 3.14.5"; ENVIRONMENT.md records the report numbers as produced on CPython 3.14.5 and states re-running requires that exact set. No job covers 3.14, and no matrix exists.
- **Why it matters:** The project's own stated reason for pinning is that sklearn/numpy versions move RMSE numbers. CI therefore certifies "tests pass on 3.13" while the shipped claims rest on 3.14.5 — a silent gap between what CI guarantees and what the docs promise readers.
- **Suggested fix:** Add a matrix (`python-version: ["3.13", "3.14"]`) or run the main job on "3.14" with 3.13 as a minimum-supported check, and note in ENVIRONMENT.md which version CI certifies.

##### [MEDIUM] (E-02 / F-24) Temp artifact `_v1_out.txt` is committed to git
- **Location:** repo root; tracked (appears in `git ls-files`)
- **Evidence:** `ls -la _v1_out.txt` → 4,353 B, mtime Oct 8 12:44. `git check-ignore --no-index _v1_out.txt` → not ignored (exit 1). `.gitignore` deliberately ignores temp files (`_tmp_*`, `.ov_*`) but this file predates/matches no pattern and was committed anyway.
- **Why it matters:** It is a scratch output of an analysis run, sitting in the published repo against the project's own ignore policy; readers cloning get meaningless cruft at the top level, and it shows the temp-file convention isn't enforced (nothing catches newly-created strays).
- **Suggested fix:** `git rm --cached _v1_out.txt`, add `_*_out.txt` (or the specific name) to `.gitignore`. Consider a CI lint step that fails if new untracked-pattern files appear in commits.

##### [MEDIUM] (E-03 / F-26, with D-09) Byte-identical duplicate review tracked twice; publish policy applied inconsistently
- **Location:** root `REVIEW.gemini.md` + `docs/reviews/REVIEW.gemini.md` (both in `git ls-files`)
- **Evidence:** SHA-256 of both files is identical (`0fb6d007…4fba4923`, 33,449 B each). Meanwhile `.gitignore:68-69` says "รีวิวภายใน (ไม่ publish — เก็บไว้ในเครื่อง)" and ignores `REVIEW.md` — yet the gemini review *is* committed and therefore served on GitHub Pages.
- **Why it matters:** Two copies of a 33 KB doc in git will drift on next edit (one updated, the other stale) with no test to catch it; more importantly, the repo simultaneously claims internal reviews are unpublished while publishing one — readers can't tell which review docs are official. *(Same finding as D-09 from the documentation side; consolidated severity MEDIUM.)*
- **Suggested fix:** Decide policy explicitly: either `git rm --cached REVIEW.gemini.md` at root and ignore it (keep only `docs/reviews/` as the published set), or rename/relocate so exactly one canonical copy is tracked; add a one-line note in README about what's internal vs public.

##### [MEDIUM] (E-04 / F-25) CI integrity gate (`--quick`) never hashes any tracked file >5 MB
- **Location:** `.github/workflows/ci.yml:19-24`, `analysis/verify_data_integrity.py:234,262`
- **Evidence:** `--quick` sets `max_bytes = 5 << 20`; files with on-disk size >5 MB become `SKIPPED` and are not hashed. Yet tracked data files exceed that threshold: `data/01_rid_khun_dan/khundan_site/stations/kh_y2025.html` (9,493,268 B), `kh_y2024.html` (6.99 MB), `st_61_year.html`, `kh_y2026.html`, `st_62_year.html`, `kh_y2023.html` (~5–9.5 MB each) and `data/02_thaiwater/raw/station_all.json` (5,985,103 B) — roughly 70 MB of **version-controlled** data escapes the CI hash check entirely.
- **Why it matters:** These files are in git precisely because they're canonical evidence; a corrupted or tampered large tracked file would pass every CI gate (SKIPPED is not MISMATCH). The "quick" trade-off was designed for *untracked* big files, but size-based skipping can't distinguish tracked from untracked.
- **Suggested fix:** In `--quick`, skip by "manifest entry whose file is expected to be outside git" instead of raw size — or add a CI-only mode that hashes everything resolvable in the checkout regardless of size (hashing ~70 MB is seconds), keeping true big-file skipping for genuinely absent paths.
##### [LOW] (E-05 / F-47) No scheduled full-integrity run; README's "681 files verified" claim isn't reproducible from CI
- **Location:** `analysis/verify_data_integrity.py:5-8` (docstring names the gap: "A nightly job… would catch silent drift"), `.github/workflows/ci.yml` (no `schedule:` trigger)
- **Evidence:** README.md:83 claims "ตรวจความครบถ้วนข้อมูลต้นฉบับ 681 ไฟล์ด้วย SHA-256 ผ่านทั้งหมด"; only `--quick` ever runs, on push. A full run needs the ~6–12 GB of raw files that are *deliberately not in git*, so no GitHub-hosted runner could execute it at all.
- **Why it matters:** The strongest integrity statement in the README is a one-time local result with no standing mechanism to re-prove it; drift on disk (the exact scenario the tool was built for) goes unnoticed until someone manually runs the full check.
- **Suggested fix:** Document that full verification is a local/manual duty (with the command + expected counts in START_HERE.md), and/or add a schedule job if a self-hosted runner with the data ever exists; consider committing the last full-run summary (counts + timestamp) as an artifact so readers see when it was last true.

##### [LOW] (E-06 / F-48) Report HTML build/determinism not verified by CI
- **Location:** `.github/workflows/ci.yml` (no build step), `tests/test_artifacts.py:51-61`, `report/build_report_html.py` / `build_expert_report.py`
- **Evidence:** The only report check in CI is that the *committed* HTML files contain strings from `analysis/canonical_numbers.json`. The ~240 KB of builder code runs manually; nothing rebuilds, diffs, or asserts determinism (fonts, image embedding order) — test_artifacts' own docstring calls its check "ชั้นที่ 2" with layer 1 happening only at manual build time.
- **Why it matters:** A builder regression could ship a report whose numbers are right but whose charts/assets silently changed; no gate would notice between builds. (Mitigating: ubuntu-latest lacks the Thai font `Leelawadee UI`, so a naive CI rebuild would produce box-glyph charts — that's likely why no build job exists.)
- **Suggested fix:** Add an optional job that installs a Noto Thai font, runs both builders into temp dirs, and asserts canonical numbers + stable asset list (hash manifest of embedded images) without committing output.

##### [LOW] (E-07 / F-49) No pip caching in CI; full install on every push to any branch
- **Location:** `.github/workflows/ci.yml:12-16`
- **Evidence:** `actions/setup-python@v5` used without `cache: 'pip'`; triggers are unconditional `push:` + `pull_request:` (all branches). 9 pinned packages installed from scratch each run.
- **Why it matters:** Wasted minutes per push and extra load on PyPI for a repo that pushes frequently; no functional risk since pins make installs reproducible.
- **Suggested fix:** Add `cache: 'pip'` under setup-python (or use the built-in pip cache key); optionally restrict triggers to the default branch + PRs if branch noise is an issue.

##### [LOW] (E-08 / F-22, with D-07) Doc drift on dataset count; no test enforces "every data dir has a manifest"
- **Location:** `README.md:40` vs `data/` contents
- **Evidence:** README says "หลักฐานต้นฉบับ 20 ชุด (ทุกชุดมี manifest + SHA-256)" but the repo contains **21** numbered datasets (`data/01_…` through `data/21_landsat_optical`). All 21 currently have `manifest.md` ✓, yet no test asserts that invariant — nothing fails if a future dataset is added without one.
- **Why it matters:** The manifest claim is central to the raw-first protocol; right now its longevity depends on developer discipline rather than any gate. *(Consolidated with D-07's documentation-side view of the same 20-vs-21 mismatch — §5.4.)*
- **Suggested fix:** Fix "20" → "21"; add a small test that every `data/[0-9]*` directory contains a parseable `manifest.md` (cheap, no hashing) and that `collect()` finds ≥1 hash per dir.

##### [NITPICK] (E-09 / F-60) opencv documented as optional only in a requirements.txt comment
- **Location:** `requirements.txt:20-23`, `pyproject.toml:26-27`
- **Evidence:** The three experimental georef scripts do `import cv2`; the optionality is explained in a comment block, but `[project.optional-dependencies]` lists only `dev`.
- **Why it matters:** Tooling (pip-tools, dependabot, env generators) can't see the optional extra; low practical impact since the scripts are explicitly non-pipeline.
- **Suggested fix:** Add e.g. `geo = ["opencv-python"]` under `[project.optional-dependencies]`.

##### [NITPICK] (E-10 / F-61) Local object store is bloated (informational)
- **Location:** local `.git`
- **Evidence:** `git count-objects -vH` → 442 loose objects / 82.54 MiB loose + 65.72 MiB pack, no garbage pruned.
- **Why it matters:** No effect on clones (loose objects aren't pushed un-packed) and nothing to fix in the published repo; `git gc` would shrink the local copy only.
- **Suggested fix:** Run `git gc --aggressive` locally at leisure; no repo change needed.

#### Open questions / needs-owner-decision
1. **Publish policy for AI reviews:** `.gitignore` treats `REVIEW.md` as internal-only, but `docs/reviews/REVIEW.gemini.md` (and its root duplicate) are committed and published on Pages. Which review docs are meant to be public? Decide, then align ignore rules + dedupe.
2. **CI interpreter:** Is 3.13 "minimum supported" or drift from the documented 3.14.5 production env? Owner should pick the matrix (see E-01).
3. **Where does full-hash verification live?** Raw data is intentionally outside git, so a hosted scheduled job can never run the full check. Accept manual-local-only (and document it), or provision a self-hosted runner with the data? This determines whether README's "681 ไฟล์ผ่าน" claim gets any standing enforcement.
4. **HANDOFF.md canonicality:** top-level `HANDOFF.md` (9,586 B) supersedes `archive/HANDOFF.md` (26,300 B) by mtime and the archive's stated purpose — confirm no reader is expected to use the archived 26 KB version.
5. **Is the >10 MB tracked JPG intended long-term?** It's whitelisted and within GitHub limits, but it's the only binary that large in git; if more evidence photos are planned, decide now between the whitelist approach and LFS (LFS client is already installed locally).

## 6. Consolidated strengths (thematic)

1. **Fail-loud, canonical-number-driven publishing.** A script-generated `canonical_numbers.json` whose check strings are enforced verbatim into both HTML builds (and mirrored in pytest); a stale report cannot be built silently. The strongest single design decision in the repo (F-02/F-03 show its blind spots, not its absence).
2. **Reproducibility treated as first-class constraint.** `common.py` centralizes constants with docstrings recording the real unit bug it prevents; `.gitattributes * -text` freezes line endings so SHA-256 manifests stay stable cross-platform; dependencies pinned to the exact interpreter that produced the numbers, documented in ENVIRONMENT.md.
3. **Artifact-anchored testing.** Tests ban self-contained arithmetic and instead re-derive published figures from committed JSON/CSV/HTML — a genuine drift guard (`26 passed` verified this review).
4. **Raw-first data protocol with real coverage.** All 21 numbered datasets carry `manifest.md` + SHA-256; ~6–12 GB of raw binaries stay out of git by design, with one deliberately whitelisted 15 MB evidence photo and no LFS complexity; integrity tool has documented exit codes locked down by its own tests.
5. **Honest science throughout.** Negative results framed as results (rejected DEM extension experiment), wrong-vs-right tables for the wetted-perimeter bug, known-wrong intermediates published *with* their correction path (62 h case, 11.95→9.94 corridor, +37.4 ลลบ.ม. outflow discrepancy), persistence baselines in every model comparison, uncertainty bands carried through all scenarios.
6. **Rigorous validation where it counts.** GISTDA georeferencing with external checks and negative controls; S1 speckle-filter edge bug found and fixed with the doc matching the fix; datum solved from two independent feeds.

## 7. Prioritized roadmap

**P0 — correctness & credibility (fix before any further publication)**
1. **F-01 / B-01:** Decide the canonical S1 rule (triple VH+VV vs calibrated VH-only); align `s1_change_detect.py`, findings doc, figure caption, and animation frames — or re-run the peak map and cascade 509.3 km² through reports/tests.
2. **F-04 / D-01:** Fix `รายงาน.md:104` "62→12 ชม." → "65→…" (contradicts the report's own §2 and its source doc).
3. **F-14 / B-03+D-02:** Regenerate/patch the 5 stale M4 documents to 9.94 km²/~52 ซม.; add one line explaining the 17% area-shift mechanism; consider having `hecras_lite_channel.py` write the two numbers into its own md.
4. **F-03 / C-02:** Extract the rating curve into a shared module; add its coefficients to canonical checks so drift can't be silent again (the formula most likely to change next).
5. **F-44 / D-10:** Fix verified mojibake/typos in public-facing text (`รายงาน.md:11,12,53,78`, ANALYSIS_PLAN:60, etc.).

**P1 — regression guardrails (close the enforcement gaps)**
6. **F-02 / C-01:** Extend `build_canonical_numbers.py` check strings to chart annotations; longer term inject numbers into templates from JSON.
7. **F-25 / E-04 + F-23 / E-01:** Make CI hash all tracked files regardless of size in `--quick`; add a 3.13/3.14 matrix matching the documented production interpreter.
8. **F-15 / C-03:** Derive `rel_daily` from the dam CSV; drop or canonical-check the hand-transcribed appendix copy.
9. **F-22 / D-07+E-08:** Fix "20 ชุด" → 21 (or renumber); add a test that every `data/[0-9]*` dir has a parseable manifest; replace orphaned `data/manifest.md` with a real index table.
10. **F-16 / C-04 + F-17 / C-05:** Put `make_x_charts_thai.py` into the documented build chain; add mtime/hash freshness coupling between analysis outputs and embedded charts (at minimum warn-loud in both builders).
11. **F-12 / B-05:** Consolidate the five Khundan fetchers into one shared module with row-count/gap validation that exits non-zero (blast radius reaches the published backtest).
12. **F-08 / A-MED-4 + F-06 / A-MED-2:** Map NASA `-999 → NaN` at load; divide ensemble by available-model count — both dormant today, one data update away from corrupting features/metrics.

**P2 — documentation consistency & terminology**
13. **F-18 / D-03:** Pick one canonical rain range (recommend exact 1,058–1,416) and add it to `canonical_numbers.json`; sweep all rounded variants.
14. **F-19 / D-04 + F-20 / D-05:** Name scenarios once (S-URC/S-plan/M2/M3), cross-reference everywhere; state the "bias ≈18% → quote ±20%" bridge in one doc.
15. **F-21 / D-06:** Refresh DATA_SOURCES.md as a live 21-row status table (or move all status into per-folder manifests and drop it from README).
16. **F-10 / B-02 + F-11 / B-04:** Publish the F1 sensitivity surface + leg-mismatch caveat; quantify the DSM-referenced stage-storage band for M4.
17. **F-13 / B-06 + F-05 / A-MED-1:** Header-check RID year columns, per-station bankfull; align backtest preprocessing with v1 (or state exactly what differs) so "เหมือน v1" claims are true again.

**P3 — hygiene & maintenance**
18. **F-26 / D-09+E-03:** Decide review publish policy; dedupe the byte-identical `REVIEW.gemini.md` copies; align `.gitignore`.
19. **F-24 / E-02 + F-39 / B-10 + F-37 / B-08:** `git rm --cached _v1_out.txt`; header-mark superseded georef experiments as EXPERIMENTAL; repo-anchor `s2_water.py` output path.
20. **F-40…F-42, F-59:** Delete dead code/unused assets in the report pipeline; fix JPEG-under-PNG-MIME; wire or drop `CANON["values"]`.
21. **F-36, F-38, F-50…F-58 (LOW/NITPICK long tail):** per-station gauge offsets in prints, georef containment mask + shared `cell_km2`, figure labels computed at render time, etc. — batch into a single cleanup PR with the P1 fixes where they touch the same files.
22. **F-47…F-49 / E:** Document full-integrity verification as a local manual duty (command + expected counts); optional Thai-font CI build job; add pip cache to CI.

## 8. Open questions needing owner decision + review note

**Owner decisions collected across parts (deduped):**
1. Which S1 detection rule is canonical for publication — doc fix or peak-map re-run? (B-01/F-01)
2. Accept DSM-referenced stage-storage with an explicit ± band, or invest in a ground-surface proxy before M4 numbers are quoted further? (B-04/F-11)
3. Consolidate the Khundan fetchers now, or freeze them as provenance artifacts — pick one; today's ambiguity is the risk. (B-05/F-12)
4. One-off event report vs living artifact: keep manual number sync + presence checks, or generate templates from `canonical_numbers.json`? (C-09 open Q1 / F-02)
5. Is `c5_floodhub.png` still load-bearing in the expert report; what's its update policy? (C-06/F-40)
6. Decide one ownership rule for derived PNGs: "analysis scripts own their PNGs, §8 lists them" vs "report_assets.py owns all chart assets". (C open Q3 / F-17)
7. Which AI-review docs are meant to be public? Align ignore rules + dedupe after deciding. (E-03/F-26)
8. CI interpreter: 3.13 as minimum-supported or drift from the documented 3.14.5 production env — pick the matrix. (E-01/F-23)
9. Where does full-hash verification live: manual-local-only (document it) or a self-hosted runner with the raw data? Determines whether "681 ไฟล์ผ่าน" gets standing enforcement. (E-05/F-47)
10. Confirm top-level `HANDOFF.md` is canonical and no reader expects the archived 26 KB version; decide whitelist-vs-LFS for future >10 MB evidence photos. (E open Q4–Q5)

**Review note.** This document consolidates five independent subagent reviews (parts A–E, reproduced verbatim in §5 with consolidated finding IDs F-01…F-61 assigned by the assembler). Findings were deduped across parts (merges noted per row); severity takes the higher value of any merged pair. All file:line citations are as reported by the subagents and were spot-checked during assembly; no repo files were modified by this review. *Produced with AI assistance — verify before citing externally.*

