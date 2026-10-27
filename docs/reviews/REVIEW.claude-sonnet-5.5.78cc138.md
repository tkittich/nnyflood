# Hydrological Audit & Red-Team Report: nnyflood

- **Auditor**: Claude Sonnet 5.5 (`claude-sonnet-5-5`), Claude Code, read-only
- **Commit audited**: `78cc138` (branch `main`, working tree clean at start)
- **Date**: 27 Oct 2026
- **Brief**: `docs/REVIEW_PROMPT_EN.md` (13 dimensions)
- **Scope honesty**: dimensions 1, 3, 5, 7, 8, 11, 13 got targeted checks; 2, 4, 6, 9, 10, 12 got no independent verification (see §6).

## 1. Executive Summary
- **Overall reliability: Medium–High, for the parts checked.**
- **Strengths**
  - Gates are green: `pytest` 321 passed, `tools/verify_all.py` 5/5 steps passed (exit 0), `catalog.py check` (124 entries) and `catalog.py audit` (47 docs) pass.
  - Pre-registration commit order holds for every rule traced (§5).
  - Round-7 defects re-tested no longer reproduce: ก1 `ชั้นหินแข็ง`, ก4 Ongkharak `3.2 ม.`, ก17 RapidOCR wording.
- **Vulnerabilities**
  - `README.md` still carries retired Sentinel-1 peaks because the retired-value test does not scan it (F-01).
  - The 24 Sep "pre-event" cut-off is four days after the project's own rain onset (F-02).
  - Some sensitivity percentages and a "within 20%" verdict are printed without the caveat that changes how they read (F-03, F-04).

## 2. Findings Matrix
| ID | Severity | Location | Root cause | Action |
|---|---|---|---|---|
| F-01 | Medium | `README.md:26`; `tests/test_goal6_consistency.py:18` | README prints retired goal-6 peaks; the retired-value test's `DOCS` list omits `README.md` | Render from canonical; add `README.md` to `DOCS` |
| F-02 | Low–Medium | `analysis/s1_orbit.py:13`; `analysis/goal6_s1_stage2_water.py:58-71` | "Pre-event" = before 24 Sep, but rain starts 20 Sep; references dated 19–22 Sep are not necessarily dry | Disclose; test a reference direction not yet tested |
| F-03 | Low | `analysis/goal7/reach_length.json`; `docs/REACH_LENGTH_PREREG.md` §3 | "Within 20%" verdict depends on denominator (17.4% of 18.3 km vs 21.1% of measured 15.11 km) | State denominator; note sensitivity |
| F-04 | Low | Report 3, reference-sensitivity paragraph | Pasak "-9% ถึง +600%" printed without base size; Bang Pakong "(-0%)" for a true −0.4% | Show absolute values / one decimal |
| F-05 | Low | `tools/write_verification.py`; `report/assets/verification.json` | Committed badge rev `c8fb0b1` ≠ HEAD `78cc138`; `verify_all` dirties a tracked file | Document the lag or stamp at release |
| F-06 | Low | `docs/REVIEW_PROMPT_EN.md` | Header says "8 Reports"; repo has reports 1, 2, 3, 4, 7, 8 + policy brief; prompt quotes figures it says to quote none of | Fix count; drop literals |

## 3. Deep-Dive Technical Findings

### [F-01] Retired Sentinel-1 peaks remain in README.md
- **Location**: `README.md:26`; `tests/test_goal6_consistency.py:18` (`DOCS = ["HANDOFF.md", "docs/GOAL6_PLAN.md", "START_HERE.md"]`), test at line 38.
- **Evidence**: A scan of tracked `.md/.html/.py/.json/.txt` files for every key in `analysis/goal6/canonical.json → retired.retired_values` found in `README.md`: `ป่าสัก 521`, `ท่าจีน 160`, `2,263.6`, `แม่กลอง 73 ตร.กม.`. The sentence reads "…ปิง-เจ้าพระยา 2,263.6 ตร.กม., บางปะกง-ปราจีนบุรี 1,281.6 ตร.กม., … ป่าสัก 521 ตร.กม., ท่าจีน 160.4 ตร.กม., แม่ก…". Current `canonical.json → flood_peak_km2`: pasak 1576.6, maeklong 380.3, bp_prach 1379.7, thachin 1667.2, ping_cp 2656.6, bkk_lower 1320.8. `README.md` was last touched in `3a71602` (27 Oct) without these being updated.
- **Critique**: These are the pre-27 Oct per-slice values with reference scenes acquired during the flood, which the project itself retired. README is the public landing page. The 1,281.6 Bang Pakong value also appears there while canonical now says 1,379.7.
- **Why it escaped**: `AGENTS.md` names reports 3/4, HANDOFF, GOAL6_PLAN, START_HERE as the canonical-contract scope. README is outside that list and `tests/test_data_consistency.py` only checks the goal-7 ledger patterns for README.
- **Proposed solution**: Generate the README sentence from canonical (or remove numbers). Add `README.md` to `DOCS`. Longer term, derive scan scope from `git ls-files` minus an explicit exempt list.
- **Also seen, probably acceptable**: `data/22_goal6_network/manifest.md` holds `2,263.6` (provenance record), and `docs/reviews/*` hold old values (review archives). `docs/READER_CHANGELOG.md` is exempt by design.

### [F-02] "Pre-event" reference scenes post-date the rain onset
- **Location**: `analysis/s1_orbit.py:13` (`EVENT_START = "2026-09-24T00:00:00"`); `analysis/goal6_s1_stage2_water.py:58-71`; `analysis/goal7/event_rain_summary.json`; `analysis/goal6_tide_gain_regression.py:32` (`EVENT_START = "2026-09-20 00:00"`).
- **Evidence**:
  - `data/22_goal6_network/derived/s1_stage2/summary.json` references: Pasak/Bang Pakong orbit 68 → 22 Sep, orbit 91 → 20 Sep, orbit 31 → 19 Sep; Maeklong/Thachin/Ping orbit 39 → 20 Sep.
  - Domain-mean rain (mm/day): 20 Sep 11.9, 21 Sep 35.7, 22 Sep 48.4, 23 Sep 35.6, then 46.5, 97.5, 158.1, 148.7.
  - The tide regression uses 20 Sep as event start; the radar uses 24 Sep.
- **Critique**: A reference taken after 70–130 mm of rain can already contain new water, which would make the "new water" of later passes a lower bound. The control passes bound the effect only for the passes tested: Pasak orbit 68 control 0.2 km², Pasak orbit 91 0.3, Bang Pakong orbit 68 51.1, orbit 91 120.5 (`analysis/goal6/s1_ref_sensitivity*.md`). The sensitivity test moves the reference about 12 days earlier; it never tests a wetter (later) reference, so the direction of the risk is untested. Only Bang Pakong and Pasak were tested; four basins were not.
- **Proposed solution**: Add a sentence tying the 24 Sep choice to its rationale and to the rain series; list reference dates beside each per-pass figure; if desired, a pre-registered sensitivity with a reference dated before 21 Sep for the orbits that have one.

### [F-03] Reach-length "consistent within 20%" depends on the denominator
- **Location**: `analysis/goal7/reach_length.json` (`diff_vs_used_pct: -17.4`, `consistent_within_20pct: true`, `central_km: 15.11`, `straight_km: 7.77`, `sinuosity: 1.94`); `docs/REACH_LENGTH_PREREG.md` §3.
- **Evidence**: |15.11 − 18.3| / 18.3 = 17.4%; |15.11 − 18.3| / 15.11 = 21.1%. The six cases (tolerance 10/30/100 m, all lines vs `hy_use` = 1) all give 15.11 km, so the "range" has no spread.
- **Critique**: The prereg says "differs from 18.3 km by no more than 20%", which is literally the first reading, and the rule was followed. But the independent estimate is the measured value, and against it the band is exceeded, which would have triggered an extra model run. Travel time scales with modelled length; my own rough estimate is about 2.7 h at 15.11 km against 3.25 h at 18.3 km. The measured length is a generalised mitrearth line, probably short, so neither number is a surveyed chainage.
- **Proposed solution**: State the denominator wherever "consistent" is used, and add the 21.1% reading. No model change is required by the rule.

### [F-04] Sensitivity percentages printed without base size
- **Location**: `report/ระลอกปลายกย2569.html`, reference-sensitivity paragraph (Bang Pakong and Pasak).
- **Evidence**: "ค่าสูงสุดของลุ่มเปลี่ยนจาก 1,380 เป็น 1,374 ตร.กม. (-0%)"; Pasak "รายรอบถ่ายเปลี่ยน -9% ถึง +600%". From `analysis/goal6/s1_ref_sensitivity_pasak.md` the +600% is 0.1 → 0.7 km² (orbit 26); the −9.2% is 1576.6 → 1431.2.
- **Critique**: The brief asks that percentages from tiny bases are not over-read; the sentence does not say the +600% base is below 1 km². "(-0%)" hides the −0.4% in `canonical.s1_ref_sensitivity.peak_change_pct`.
- **Proposed solution**: Print one decimal and the absolute range, or restrict the per-pass range to passes above a stated area.
- **Verified fine in the same paragraph**: Bang Pakong numbers equal canonical (1379.7 → 1373.8, −0.4%, per-pass −4.1% to +7.2%, controls 51.1–175.4); the union 2,035.4 (Pasak) is labelled "ไม่ใช่น้ำท่วมพร้อมกัน"; only two basins are named as tested.

### [F-05] Verification badge revision and side effect
- **Location**: `report/assets/verification.json`; `tools/write_verification.py`.
- **Evidence**: committed file had `git_rev: c8fb0b1`, `checked_at: 2026-10-27T13:45`, while HEAD was `78cc138`. Running `verify_all.py` rewrote only these two fields (all four gates `pass`) and left the tree dirty; I ran `git checkout -- report/assets/verification.json` to restore it.
- **Critique**: The badge logic itself is sound: `run_gate` returns `pass` only on pytest exit 0, and `main` returns nonzero if any gate fails. The badge necessarily describes the previous commit. I did not break a gate in a scratch copy, so "tick disappears on failure" is read from code, not demonstrated.
- **Proposed solution**: Document the one-commit lag, or stamp at release time.

### [F-06] Review prompt drift
- **Location**: `docs/REVIEW_PROMPT_EN.md` lines 4 and 14–45.
- **Evidence**: "8 Reports + Policy Brief" against seven HTML files in `report/` (reports 1, 2, 3, 4, 7, 8 and the brief); `index.html` lists reports 1, 2, 3, 4, 7, 8. The prompt still quotes 88:12, 36.5 days, 666.3 / 617.4, 3.25 h, 9.0 h, 53.0 MCM, 18.3 km, despite stating that it quotes none. I did not check each against canonical.
- **Proposed solution**: Correct the count; reference canonical keys instead of values.

## 4. Intra-Report & Cross-Report Consistency Audit
- **Intra-report**: Report 3's S1 paragraph, tables and canonical agree for the numbers listed in F-04. No other intra-report comparison was done.
- **Cross-report**: no pairwise comparison across reports 1/2, 7/8/brief was done.
- **Retired ledger**: none of the goal-6 retired values appears in any `report/*.html`; the misses are in `README.md` only (F-01).
- **Gap register**: not re-audited.

## 5. Verified Invariants (Passed Spot-Checks)
| Check | Method | Result |
|---|---|---|
| Test suite | `python -m pytest -q` with stdin detached | 321 passed (118 s) |
| Unified runner | `python tools/verify_all.py` | 5/5 passed, exit 0 (integrity step is `--quick`) |
| Catalog | `catalog.py check` / `audit` | 124 entries exist; 47 docs registered |
| Canal volume | 504 m² × 135.9 km | 68.5 MCM |
| Dead pool | (51×2 + 3×2²) = 114 m² × 135.9 km | 15.49 MCM |
| Active volume / fill time | 68.5 − 15.5; 53.0e6 / 600 / 3600 | 53.0 MCM; 24.5 h |
| Utilisation | 38.3 d / 365 | 10.5% |
| Straight line Ny.1B–Ny.7 | haversine on `network_nodes.json` coordinates | 7.78 km; reach file says 7.77 |
| Implied wave speed | 18,300 m / (3.25 × 3600 s) | 1.56 m/s |
| Compound term | 0.132 × 3.75^1.28 | 0.717 m |
| Stage-2 pairing | code read `goal6_s1_stage2_water.py:41-166` | pairing by `rel_orbit`; `hhmm()` is a label only; reference pass forced to zero; unpaired scenes listed (0 in current summary); pass = orbit × day, slices mosaicked, coverage stored |
| Retired values in reports | tracked-file scan | absent from `report/*.html` |
| Credentials | `git grep` for key-like strings; `git check-ignore` | none in tracked files; `.gistda_api.json` and `.cdse_s3.json` are ignored |
| Round-7 re-tests | grep | `ชั้นหินแข็ง`, Ongkharak `3.2 ม.`, RapidOCR present only as retired/historical wording |

**Commit order (prereg before run)**
- S1 reference audit prereg `7841e10` (26 Oct 22:15) → audit run `8c2c1d0` (27 Oct 03:37) → owner decision `182fb83` (05:49) → code change `d3c7e11` (06:21). The audit did not change published numbers on its own.
- Pass-mosaic prereg `769d4d5` (08:13) → code `3a71602` (10:02).
- Pasak sensitivity prereg `c8fb0b1` (11:48) → results `78cc138` (13:48).
- Reach-length prereg `c2aabd3` (11:06) → run `16cf7c6` (11:12).
- Chachoengsao prereg `7ebde3f` (11:14) → run `f3fc89d` (12:31).
- GISTDA cross-check prereg `933e13b` (07:57) → `fbbb02c` (08:09). The boundary-file fix and the results are in one commit, so git cannot show the error was caught before results were read; the prereg §5 says it was.

## 6. Information Gaps & What Was Not Done
- **Not exercised** (needs writing in a scratch copy): defeating the two-layer literal gate; breaking a gate to see the badge tick vanish.
- **No independent verification**: Dimension 2 (leakage, tidal harmonics), 4 (hypsometric curve, Route 305), 6 (economics, ONEP rows), 9 (DEM correction), 10 (2-D model), 12 (OCR provenance). Not opened: PDFs, OCR outputs, DEM rasters. Not re-derived: model skill figures, 2-D overlap scores.
- **Not compared**: reports 1/2 and 7/8/brief pairwise.
- **Outside data still missing** (per the repo's own registers): Route 305 crown level, surveyed Ny.1B–Ny.7 chainage, S.26 daily series for the 1,970 MCM/yr denominator, gate discharge logs.

## 7. Suggestions
- **Methods**: test reference sensitivity in both directions, including a reference dated before the rain onset; report absolute ranges beside percentages; state denominators for any band test.
- **Governance**: derive retired-value scan scope from `git ls-files` minus an explicit exempt list instead of hand-kept `DOCS` lists (would have caught F-01); keep the badge revision visible so readers can see it describes the previous commit.
