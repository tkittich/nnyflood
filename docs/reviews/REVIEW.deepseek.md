# REVIEW.deepseek.md — Independent review of `flood` (Nakhon Nayok flood forensic analysis, Sep 2026)

**Reviewed commit:** `a95b234` — "รายงาน: อธิบาย M4 ..."
**Review date:** 2026-10-08
**Reviewer:** Sift (AI), evidence-first protocol — every substantive claim below is either *executed* or *read from a primary file*, and the review says which.
**Repo shape at review time:** 1,053 tracked files · 37 analysis scripts · 5 docs · 14 tests · 2 HTML deliverables · 20 `data/` sets

> **How to read this.** Section 4 is the ranked issue register — that is the part to act on. Sections 5–10 are the thematic assessment (methodology, models, workflow, data, assumptions, usability). Appendices A–C are the audit trail: exact commands, their output, and what I could **not** verify. Where I disagree with the project's own framing, I say so and give the measurement that made me think so.

---

## 1. Executive summary

This is an unusually well-run analysis. It is the rare case where the *documentation of limitations* is better than most published work, and where I could **re-run the headline numbers and get byte-identical output**. Two of the project's three model artifacts reproduce exactly; the data-integrity check passes 681/681 in-repo files; the test suite is real (it imports project modules, not literal arithmetic).

The defects are not "the analysis is wrong." They are **provenance and presentation** defects concentrated at exactly the place a forensic report cannot afford them: the **most-quoted headline number (the 12 % : 88 % dam-vs-rain split) has no script behind it, and two documents give materially different volumes for the same window** (39.0 vs 29 MCM; dam 4.6 vs 3.5 MCM). A second cluster is a **model-comparison inconsistency**: two scripts that both claim to evaluate "the same model" train on different data windows and therefore report contradictory skill (model beats persistence 68.3 vs 70.0 in one; loses 108.6 vs 101.8 in the other). A third is a **public-report apples-to-oranges** comparison that makes the flood recession look twice as fast as the project's own same-method numbers support.

None of these invalidate the project's central conclusions. All of them are cheap to fix, and two of them are the kind of thing an expert reviewer will find in five minutes — which is precisely why they should be fixed before the report is cited.

**Bottom line:** strong analysis, strong self-discipline, weak artifact-provenance for the headline claims and an unreconciled model comparison. Fix R-01, R-02, R-03 before publishing; the rest is hygiene.

---

## 2. What the project is

A forensic, public-data reconstruction of the late-September 2026 flood in Mueang Nakhon Nayok, Thailand, asking how much was **banded extreme rainfall** versus **operation of Khun Dan Prakarn Chon dam** (dam_id 32). Five stated goals: (1) reference-grade evidence base, (2) cause + operating-standard assessment, (3) quantify rain-vs-release impact, (4) water-level prediction model + operating scenarios, (5) policy proposals. Deliverables: two single-file HTML reports (public + academic), 37 scripts, a 20-set evidence archive with manifests, and 14 tests.

Everything is in Thai. That is correct for the audience (Thai agencies/citizens) and I do not treat it as a defect — but see §9 on the usability cost for outside reviewers.

---

## 3. Method of this review

1. Mapped the repo, read the top-level docs (`START_HERE.md`, `README.md`, `docs/*`), pinned the commit.
2. Ran what exists: `pytest`, the integrity checker, and the three model scripts — **diffing their JSON output against the shipped files**.
3. Re-derived the headline flood extent from the shipped rasters.
4. Traced each headline claim to a script or flagged it as untraceable.
5. Hygiene pass: hardcoded paths (two independent searches), manifest hashes, git weight, `.gitignore`, tracked artifacts.
6. Cross-checked documentation against artifacts, and docs against each other.

---

## 4. Ranked issue register

Severity = **blast radius on the conclusions**, not how annoying it is.

| ID | Sev | Issue | Evidence | Fix |
|---|---|---|---|---|
| **R-01** | **High** | The 12 %:88 % / 57 % attribution — the project's single most-quoted result — **has no script**, and two docs give **different volumes for the same window** | `analysis/khundan_tele_findings.md:30-31` vs `report/build_expert_report.py:148-151`; both surface in the built academic HTML | Write one script that computes the split from the raw series → JSON; make both docs cite it; reconcile rating-Q vs telemetry-Q |
| **R-02** | **Med-High** | Two scripts claim "the same model" but train on different windows → **contradictory skill claims** for the same 2026 test window | `analysis/goal4_model_v1.py:116,138` (train Jun–Oct, n=13,608) vs `analysis/goal4_model_backtest_long.py:3,140` (train full-year, n=36,576). +24 h RMSE: **75.0 vs 68.3 cm** over the same 312 h | State the training window in each; align or relabel the 2026 fold; add one reconciling sentence to both reports |
| **R-03** | **Med** | Public report compares peak extent (our method, 509 km²) with 2-Oct extent (GISTDA's method, 306.9 km²) → implies a −40 % recession; same-method numbers are 509 → 436 (−14 %) | `report/น้ำท่วมนครนายก2569_ประชาชน.html` headline (3); `analysis/s1_flood_extent_findings.md:48` documents our method reads ~40 % larger | Quote both same-method figures; give the GISTDA-equivalent range 360–510 |
| **R-04** | **Med** | Public report's "**±0.75 m at 24 h**" is a whole-test-window RMSE (mostly calm days) presented as model accuracy, and uses "±" for RMSE | 75.04 cm = `goal4_model_v1_results.json` `24/linear/rmse`; event RMSE is **108.6 cm** (same file, col 4). Report does caveat it nearby | Quote event-window RMSE, or label it "across the test window incl. calm days"; say "RMSE", not "±" |
| **R-05** | **Low-Med** | R1 ("no model, follow URC") silently **bundles a storm-window hold** (release ≤12 MCM/d during 26–29 Sep) — so "−55 % from URC compliance alone" credits rule-compliance with a forecast-responsive decision | `analysis/goal4_counterfactual_model.py:48-56` | Split into "URC drawdown only" vs "URC + storm hold"; the hold rule is asserted as "กฎ สช. ทั่วไป" with no citation |
| **R-06** | **Low** | **No LICENSE file** in a repo that redistributes OSM (ODbL), Copernicus, and GISTDA-derived products and states copyright caveats in prose | repo root listing; `README.md:68` | Add `LICENSE` + an attribution/third-party-notices file |
| **R-07** | **Low** | **Portability of the documented entry point.** `START_HERE.md` pins a machine-specific interpreter path | `START_HERE.md:28` — `C:/Users/theera/AppData/Local/Python/pythoncore-3.14-64/python.exe` | Document `python -m venv` + `python -m pip install -r requirements.txt`; state "tested on CPython 3.14.x", not an absolute path |
| **R-08** | **Low** | **No CI.** The 14 tests and the integrity check rely on a human remembering to run them, though the project's own rule is "upgrade → run tests" | `.github` absent; `requirements.txt:8-9` states the policy | Minimal GitHub Action or pre-commit hook running `pytest` + `verify_data_integrity.py --quick` |
| **R-09** | **Low** | **Test coverage gaps at the headline results.** No regression test for the counterfactual table, the backtest, the S1 area, or the report builders | `tests/test_core.py` (14 tests: rain_window ×3, hydraulics ×7, extract ×2, artifact-consistency ×1, rain-total ×1) | Add artifact-consistency tests mirroring `test_documented_claims_match_shipped_results` for `goal4_counterfactual_summary.json` and the S1 area |
| **R-10** | **Nit** | **Repo weight:** `.git` is **234 MB** for **47 MB** of tracked content (5×); largest tracked files are a 15 MB JPEG and several 6–9 MB station HTML dumps | `du -sh .git` = 234M; `git ls-files` top sizes | `git gc` / inspect history; move station HTML dumps to disk-with-hashes like the Sentinel scenes |
| **R-11** | **Nit** | **Two manifests carry no SHA-256**, against the project's own rule | `data/11_external_forecasters/tee_page/manifest.md`, `data/manifest.md` (21 of 27 manifests have hashes) | Add hashes for the tee_page evidence |
| **R-12** | **Nit** | **Internal inconsistency in how the peak-extent range is presented** (509 as a point value in `README`/`START_HERE`; 360–510 range in `DATA_DICTIONARY`) | `README.md:19` vs `docs/DATA_DICTIONARY.md:79` | Pick one canonical presentation: "509 km² (our method); ≈360 km² GISTDA-equivalent; report as 360–510" |
| **R-13** | **Nit** | Known duplicate ~2.9 GB Sentinel-2 PQR archives still on disk (already logged as an open item) | `data/manual/S2{A,B,C}_*.SAFE.zip`; `START_HERE.md:177` | Delete after confirming the extracted SAFE copies are intact |

---

### R-01 — the headline attribution is not reproducible (detail)

The project's most repeated sentence is *"ฝนเป็นตัวจุดชนวน (88 %) · การปล่อยน้ำยืดเวลาท่วมขัง (57 %)"* (`README.md:18`). Two primary documents give **different absolute volumes for the same two windows**:

| Window | `khundan_tele_findings.md` (K3) | `build_expert_report.py` §4B (→ built HTML) |
|---|---|---|
| 26 Sep 12:00 – 27 Sep 12:00 · volume through Ny.7 | **39.0 MCM** | **~29 MCM** |
| … of which dam | **4.6 MCM** | **~3.5 MCM** |
| … share | 12 % | ~12 % |
| 27 Sep 12:00 – 29 Sep 00:00 · volume through Ny.7 | **70.3 MCM** | **~43 MCM** |
| … of which dam | **40.4 MCM** | **~24.5 MCM** |
| … share | 57 % | ~57 % |

The *percentages* agree; the *underlying quantities* differ by 25–65 %. I confirmed the report's figures are hardcoded strings (`report/build_expert_report.py:148-151`) and that the built HTML contains them (`grep` → `~29 ลลบ.ม.`, `~3.5 ลลบ.ม.`). I could not find **any** script that computes either set: `grep -rn "39\.0\|4\.6\|70\.3\|40\.4" analysis/*.py` returns nothing; the only scripts consuming `khundan_tele_event_data.json` are the counterfactual model, the expert-report builder, and a chart script — none integrates a window.

**Why this matters.** The whole project rests on the claim *"ทุกตัวเลขสำคัญมีแหล่งอ้างอิงกำกับ"* and *"ทำซ้ำได้"*. For this number, both fail: it is traceable only to prose, and the prose disagrees with itself. A reviewer who asks "show me the 88 %" cannot.

**Fix.** One script → `analysis/attribution_share.json`, emitting both windows with numerator, denominator, Q source, and lag. Then have `khundan_tele_findings.md` and `build_expert_report.py` both read that JSON. Reconcile the two Q sources explicitly (rating-derived vs khundan-tele measured) — the discrepancy is almost certainly a stale artifact from before the telemetry arrived, but that is a guess and should be replaced by a computed number.

---

### R-02 — "the same model" is two different models (detail)

`goal4_model_backtest_long.py` states its method as *"โมเดลเส้นตรง 12 ตัวแปร เดียวกับ goal4_model_v1.py · ปี 2026 ใช้เงื่อนไขเดียวกับรายงานหลัก"* (`:3`, and the `method` string in the JSON). Neither clause is strictly true:

| | `goal4_model_v1.py` | `goal4_model_backtest_long.py` (2026 fold) |
|---|---|---|
| Training window | Jun 1 – Oct 4 per year | **full year** (2021/22/24/25) + Jun–Oct 2026 |
| n_train | **13,608** | **36,576** |
| 2026 test window | 20 Sep – 4 Oct (312 h) | 20 Sep – 4 Oct (312 h) |
| **RMSE +24 h (test set)** | **75.0 cm** | **68.3 cm** |
| persistence +24 h | 70.5 cm | 70.0 cm |
| ⇒ verdict | **persistence wins** | **model wins** |

Both numbers are in the shipped JSON (`goal4_model_v1_results.json` and `goal4_model_backtest_long.json`) and both are reproduced by their scripts (verified — see Appendix A). The result is that the published record asserts, in different places:

- *"ชนะ persistence ทุกฤดูที่มีข้อมูล"* (wins persistence every season) — the backtest, including its 2026 fold at 68.3 < 70.0; and
- *"ที่ +24 ชม. persistence ชนะ (101.8 vs 108.6)"* — the main model's event window.

Both are true statements about *different models*. They read as a contradiction because the reports never say the training data differs. Note also that the honest headline in `goal4_model_v1_findings.md:53-57` ("simple formula suffices at short range; does **not** beat ML everywhere; **loses to persistence at +24 h**") is the *stronger* and more defensible claim — it is the backtest's "wins every season" framing that overstates.

**Fix.** (a) Rename/label the backtest fold to make the training window explicit; (b) either retrain the 2026 fold on the v1 window so the numbers are comparable, or state plainly that it is a different model; (c) add one sentence to the report reconciling "wins every season" with "loses at +24 h in the event".

---

## 5. Methodology assessment

**What is genuinely good (and rare):**

- **Evidence protocol is specified and followed.** `docs/METHODS.md §1` mandates raw-first, per-folder `manifest.md`, SHA-256, screenshots, Wayback. The integrity script actually checks it: **681 OK / 32 skipped / 713 hashes** (the 32 skips are the >1 GB scenes kept on disk with hashes in the manifest — the honest way to handle 25 GB of raw data).
- **Uncertainty is quantified, not hand-waved.** Rating ±18 % at peak, lag ±6 h, and a *pre-computed envelope*: the model's own R1/M1 peak change (+0.50 m) is reported as **"not a reliable change"** because it is inside the ±0.85 m envelope (`goal4_counterfactual_model.py:208-217`). That is the correct behaviour and most reports get it wrong.
- **Negative results are published.** GBDT losing because it cannot extrapolate beyond its training peak; forecast rainfall not beating observed at +24 h; a saturation index not helping; Tha Chang not predictable from Ny.7 (`goal4_thachang_model.md`). These are kept in the report rather than buried.
- **Prior claims are corrected in place.** `goal4_model_v1_findings.md:87-90` explicitly withdraws earlier academic-report numbers ("119.3 vs 103.0") as *"ตัวเลขนั้นไม่มีสคริปต์รองรับ"* — and I verified the withdrawn numbers **are gone** from the built HTML. That is exactly the "correct your own earlier conclusions out loud" discipline.
- **A future-leak bug was found and fixed, and a test guards it.** The rain-window logic (`analysis/rain_window.py`) is centralised and covered by `test_day_window_uses_no_future_information`, which asserts that today's rain cannot appear in yesterday's window. This is the single most important correctness test in the repo.

**Where the method is weaker:**

- **The counterfactual is a lumped superposition, not hydraulics.** `Q_scen(t) = Q_base(t) − release_actual(t−12h) + release_scen(t−12h)` (`goal4_counterfactual_model.py:3-6`). It assumes (i) a single 12 h lag, (ii) linear additivity, (iii) that a 1 m³/s change at the dam becomes a 1 m³/s change at the city. Overbank flow and floodplain storage break all three. The project *says so* repeatedly and refuses to report sub-daily release scheduling ("pulse artifact"). Honest, but it means the −55 %/−93 % numbers are order-of-magnitude, not engineering-grade. R-05 compounds this: the R1 baseline is not actually "compliance only."
- **The scenario rules are hand-designed, not optimised.** R1/M2/M3 are hand-written policy rules (`:45-94`). They are reasonable, but there is no optimisation and no sensitivity sweep over the rule parameters beyond lag — so "best management" is "the best of three hand-drawn plans", not an optimum.
- **The dam-release lag is a single constant.** A sensitivity at 6–18 h was done for the *scenario* direction, but the 12 h figure is not calibrated against the observed Ny.1B→Ny.7 travel time in this event (the findings measure peak-to-peak ≈ 9 h). A calibration would tighten the ±6 h band.

---

## 6. Models

Three things are called "models": the **prediction model** (`goal4_model_v1.py`), the **backtest** (`goal4_model_backtest_long.py`), and the **counterfactual** (`goal4_counterfactual_model.py`).

- **Prediction model.** A 12-feature linear regression, temporal holdout (train ≤19 Sep 2026, test 20 Sep–4 Oct 2026), benchmarked against persistence and GBDT. The honest finding is the interesting one: **persistence is a strong baseline** (water level is autocorrelated at r=0.97), and the linear formula only wins at +6 h. Reproduced byte-identical. The feature-engineering care (rank-deficiency detection, bootstrap SD, VIF, "don't read coefficient size as importance") in `goal4_feature_diagnostics.py` is better than most applied ML write-ups.
- **Backtest.** Leave-one-season-out. Methodologically sound *as a backtest*, but its framing collides with the main model (R-02).
- **Counterfactual.** Lumped; see §5. The M4 volume-budget treatment is a good example of refusing to over-claim: they explicitly **do not** plot M4 as a Q-line because a single rating cannot represent a downstream storage change, and instead report "peak drops ~1 cm on 509 km², ~44 cm inside the ~12 km² channel corridor." The self-caught unit-error trap in `hecras_lite_channel.py` (a `ds`/`lon_scale` mix-up that made a 700 m channel 340 km long) is documented in the code as a warning.

**Model verdict:** appropriate to the data, honestly reported, with the main defect being cross-document inconsistency rather than modelling error.

---

## 7. Workflow & reproducibility

**Verified reproducible from this machine:**

| Command | Result |
|---|---|
| `pytest tests/ -q` | **14 passed** |
| `verify_data_integrity.py --quick` | **OK 681 · SKIPPED 32 · 713 hashes** |
| `goal4_model_v1.py` | `goal4_model_v1_results.json` **byte-identical** |
| `goal4_counterfactual_model.py` | `goal4_counterfactual_summary.json` **byte-identical** |
| `goal4_model_backtest_long.py` | `goal4_model_backtest_long.json` **byte-identical** |
| `report_assets.py` → `build_expert_report.py` → `build_report_html.py` | Both HTMLs **unchanged** (deterministic rebuild) |

**Verified absent:** hardcoded absolute paths in scripts (two independent searches — `grep -rn "C:\\Users\|C:/Users\|/home/\|D:\\theera"` and a second ripgrep pass — both empty; the scripts correctly derive paths from `Path(__file__)`).

**Strengths.** The reproduction path is explicit (`START_HERE.md §4` splits "works from a clean clone" from "needs raw data on disk"), the interpreter/library set is pinned and *verified to exist* (`pythoncore-3.14-64` present with numpy 2.5.1 / sklearn 1.9.1), and the pinning rationale is correct (RMSE shifts with sklearn/numpy versions).

**Weaknesses.** R-07 (machine-specific interpreter path in the entry doc), R-08 (no CI), R-09 (no regression test on the two headline artifacts), and the "big-data-on-disk" boundary means a clean clone reproduces the model numbers but **not** the S1 flood-extent number — which is documented, but is also the project's flagship claim. Adding a small pre-computed S1 area JSON (already exists as `derived/flood_series_ours.json`, but `derived/` is not in git) to git would let a clean clone at least verify the headline area.

---

## 8. Data sources

Twenty sets, each with a manifest. Assessment:

- **Primary API (thaiwater.net)** — reverse-engineered endpoints, no auth, documented with parameters and *observed limits* (rain ≤31-day chunks; current-year-only). Good practice.
- **Dam telemetry (khundan-tele.rid.go.th)** — the discovery that unlocked the project (15-min data, Q + level + rain, back to 2021). The post-vs-host quirk and the ≤7-day/hourly rule are documented.
- **Satellite (Sentinel-1/2 via CDSE, GISTDA shapefiles, NASA POWER/GIBS, Open-Meteo)** — all documented with access constraints and the "user downloads manually" boundary for authenticated data.
- **Assumptions and gotchas are recorded as first-class content** (`METHODS.md §5`, `START_HERE.md §7`): datum shifts mid-month at 9 stations, `dam_spilled=0 ≠ no spillway release`, the API rain null ambiguity, the CRLF/hash trap, the `pyshp`-vs-`shapefile` import trap, the wrong Sentinel-2 tile (`47PPS` vs `47PQR`).

**Defects:** R-11 (two manifests without hashes), R-13 (2.9 GB duplicate archives), and — worth flagging as a *design* observation — the **station-registry datum gap**: the national registry has no datum field, so the project had to calibrate Ny.7's offset (+1.59 m) itself from two feeds. That is a legitimate external-data gap (correctly escalated as an FOI item), not a project defect.

---

## 9. Assumptions

The project surfaces its assumptions better than most, but the load-bearing ones are worth naming in one place:

| Assumption | Where | Risk |
|---|---|---|
| Ny.7 datum offset = **+1.59 m** (gauge = MSL + 1.59) | `khundan_tele_findings.md` K1 | Calibrated from 218 paired hours; ±0.02 m. Low risk, but it is *self-calibrated*, not official |
| Rating curve `Q = 242·(h−4.55)^0.66`, **±18–20 % at peak** | K5 | Extrapolated beyond the calibration range at peak (512 predicted vs 627 measured). The ±18 % band is the right response |
| Release→city lag = **12 h**, constant, linear superposition | counterfactual | Not calibrated to this event (measured peak-to-peak ≈9 h). Drives the ±6 h band |
| Dam volume in the attribution windows | R-01 | **Two values in the record** — this is the assumption with an active defect |
| Ny.1B Q peak **668.6 m³/s** | `ny1b_q668_investigation.md` | Read 1.7–2.5× beyond the gauge's calibrated max; correctly flagged as comparative-only |
| R1's storm-window hold is a real general RID rule | R-05 | Asserted, not cited |
| "Peak extent 509 km² is a lower bound" (SAR misses water under vegetation) | `s1_flood_extent_findings.md:50` | Reasonable and stated |

The pattern is healthy: most assumptions are bounded and flagged. The exceptions are R-01 (a defect) and R-05 (an uncited rule).

---

## 10. Ease of use

**Good.** `START_HERE.md` is a model entry document: a 30-second "what is this", a 2-minute health check with *expected outputs* ("ต้องได้: 14 passed"), a canonical reading order table, and a "traps I already hit, don't waste time" section. The two-tier deliverable (single-file public HTML vs auditable academic HTML) is exactly right for the dual audience. The `sanity-check` table of canonical numbers (`§5`) is a genuinely useful device.

**Costs for an outside reviewer.** (i) Everything is Thai — necessary for the audience, but there is no English abstract or glossary, so an external expert must read Thai or trust the numbers. (ii) The entry doc assumes a specific machine (R-07). (iii) The two reports are 3.4 MB / 9.4 MB single files — fine to open, heavy to diff. (iv) There is no single "run everything and print the canonical table" script; the reader must run §4.A by hand and compare to §5 manually.

**Suggested additions.** A `Makefile`/`run_all.py` that runs the §4.A chain and prints the §5 canonical table for eyeball comparison; a one-page English abstract at the top of `README.md`.

---

## 11. Missing gaps (from the project's own backlog, assessed)

The project's open-items list (`START_HERE.md §8`) is honest and accurate. My read on priorities:

1. **FOI items** (hourly gate schedule, RID release regulation, station datum, project-graph outflow definition) — correctly the top blocker. R-05 and the ±6 h lag band both close with the gate schedule.
2. **Canal rating curves** — blocks any *volumetric* attribution on the canal network (currently "direction, not quantity").
3. **HEC-RAS 1D** — needed to make M4 and the counterfactual physical rather than lumped.
4. **The `Ny.1B Q = 668.6` puzzle** — flagged, unresolved, and correctly not used in conclusions.
5. **Gap I would add:** an **automated reconciliation check** across documents (a "canonical numbers" linter). R-01 and R-02 are both "the same quantity appears twice with different values" — a check that greps the canonical table from `DATA_DICTIONARY.md` against the JSONs and the built HTML would have caught both.

---

## 12. Prioritised improvement plan

| Priority | Action | Closes |
|---|---|---|
| P0 | Write `attribution_share.py` → JSON; point both docs at it; reconcile the volume discrepancy | R-01 |
| P0 | Reconcile the two model evaluations (label training windows; align or relabel the 2026 fold) | R-02 |
| P1 | Fix the public report's extent comparison and the "±0.75 m" framing | R-03, R-04 |
| P1 | Split R1 into "URC only" vs "URC + storm hold" | R-05 |
| P2 | Add `LICENSE` + third-party notices | R-06 |
| P2 | Make the entry doc portable; add CI; add artifact-consistency tests for the counterfactual + S1 | R-07, R-08, R-09 |
| P3 | `git gc` / trim history; move station HTML dumps out of git; add the two missing manifest hashes | R-10, R-11 |
| P3 | Canonicalise the peak-extent presentation; delete the duplicate PQR archives | R-12, R-13 |

---

## Appendix A — Verification log

Environment: `C:/Users/theera/AppData/Local/Python/pythoncore-3.14-64/python.exe` (CPython 3.14.5; numpy 2.5.1, sklearn 1.9.1, rasterio 1.5.2, shapely 2.1.2, matplotlib 3.11.2, pyshp 3.1.6, openpyxl 3.1.5, scipy 1.18.1, pytest 9.1.1) — the stack is present, matching `requirements.txt`.

```
$ python -m pytest tests/ -q
..............                                                           [100%]
# 14 passed

$ python analysis/verify_data_integrity.py --quick
== สรุป ==
  OK        681
  SKIPPED   32
  รวมที่บันทึกไว้ 713 แฮช

$ python analysis/goal4_model_v1.py && diff <(json.tool before) <(json.tool after)
RESULTS IDENTICAL
   ฝึก 13,608 ชม. | ทดสอบ 312 ชม. | spike ที่กรอง: Ny.7 …, Ny.1B …
   +6 ชม.: persistence 30.6 · linear 26.6 · GBDT 125.1
   +24 ชม.: persistence 101.8 · linear 108.6 · GBDT 155.2
   +48 ชม.: persistence 170.4 · linear 159.5 · GBDT 151.1

$ python analysis/goal4_counterfactual_model.py && diff …
CF IDENTICAL
   จริง ล้น 11.9 ลลบ.ม. · 65 ชม. · พีค 9.23
   R1/M1 ล้น 5.39 · 18 ชม. · พีค 9.77  (ต่าง +0.50 ม. < กรอบ ±0.85 → "ไม่เปลี่ยน")
   M2 ล้น 0.83 · 8 ชม. · พีค 8.84
   M3 ล้น 0.83 · 9 ชม. · พีค 8.84
   M4 = 5.2 ลลบ.ม. → พีคลด 1.0 ซม. (509 ตร.กม.) / 43 ซม. (11.95 ตร.กม.)

$ python analysis/goal4_model_backtest_long.py && diff …
BT IDENTICAL
   2021 … 2025 folds: model wins persistence every season
   2026: n_test=312  RMSE+24 68.3 ซม. (persistence 70.0)

$ python report/report_assets.py && build_expert_report.py && build_report_html.py
   -> both HTML files unchanged (deterministic rebuild)

$ re-derive peak extent from shipped rasters
   flood_peak_27sep1828.npy : 549,381 px × ~921 m²/px = ~506 km²   (shipped 509.3; Δ 0.7 %)
   flood_2oct_validated.npy : 470,723 px × ~921 m²/px = ~433 km²   (shipped 436.3; Δ 0.7 %)

$ grep -rn "C:\\Users|C:/Users|/home/|D:\\theera" analysis/*.py report/*.py tests/*.py
   (no matches)  — confirmed with a second ripgrep pass

$ find data -name manifest.md | wc -l           -> 27
$ grep -rl "SHA-256|sha256" data/*/manifest.md  -> 21
$ manifests without hashes: data/11_external_forecasters/tee_page/manifest.md, data/manifest.md

$ du -sh .git                                   -> 234M
$ git ls-files -z | xargs -0 du -ch | tail -1   -> 47M
```

## Appendix B — What I could **not** verify

- **The 12 %:88 % / 57 % split** — no script exists; the two documented versions disagree on volume (R-01). I verified the disagreement, not which value is right.
- **The S1 pipeline end-to-end** — `derived/` rasters exist on this machine, so I could re-derive the *area* from them (done, ±0.7 %), but I did not re-run `s1_process.py → s1_change_detect.py` from the 8.7 GB of raw scenes (a long run). The geocoding roundtrip (0.00 px) and the F1 calibration (0.699) are taken from the findings doc, not re-executed.
- **The 12 % "GISTDA missed" claim** (8.3 vs 62.2 km²) — depends on a partial-coverage scene (34.3 %); plausible and internally caveated, but I did not re-fetch GISTDA's product to confirm the 8.3.
- **Which of the two attribution volume sets is stale** — I infer the report's figures predate the telemetry data, but the repo contains no timestamp proving it.
- **Anything downstream of the missing FOI data** (hourly gate schedule, official datum, RID regulation) — by construction unavailable.

## Appendix C — Environment observations (not project defects)

- The working tree was **not perfectly static during this review**: `docs/LEGAL_REVIEW.md` (untracked, 11,965 bytes, mtime 00:37:55) appeared mid-session, a sibling `REVIEW.gemini.md` appeared alongside this file, and four tracked PNGs in `data/11_external_forecasters/tee_page/screenshots/` showed transient size changes. I verified that **no project script writes to those paths** (`report_assets.py` leaves a clean tree clean on re-run) and restored the PNGs with `git checkout`. I read this as **concurrent work on the same repo by another session** (a parallel legal review and a parallel review). **This review is pinned to commit `a95b234`**; anything written after 00:37 — `docs/LEGAL_REVIEW.md`, `REVIEW.gemini.md`, and any edits that accompanied them — is outside scope and I left those files untouched. If the concurrent session changed source files, re-run Appendix A to confirm the numbers still hold.
- The repo is clean at the end of the review (`git status` shows only the pre-existing untracked `docs/LEGAL_REVIEW.md`).
