# Independent Red-Team Audit — `nnyflood` Hydrological Investigation Repo

- **Auditor model:** DeepSeek V4.1 Flash Free (independent audit, Round 5)
- **Date:** 18 Oct 2026
- **Repo HEAD audited:** `02ba87c` ("docs(handoff): prepare status, catalog metrics, and next session tasks"; working tree clean at audit start)
- **Scope:** 3 pillars / 7 goals; dimensions (1) 1D hydraulic routing, (2) L3 coastal ML + tidal harmonics, (3) compound flood-risk matrix, (4) Ongkharak 2D hypsometry / Route 305, (5) canal active storage + counterfactual, (6) operational economics / dam governance, (7) canonical invariants / legal / PDPA / WCAG.
- **Method:** every claim below was re-derived from raw data with fresh Python runs, or verified by reading the cited code verbatim; numbers were cross-checked against `analysis/canonical_numbers.json`, `analysis/goal6/canonical.json`, `analysis/goal7/canonical.json`; published HTML was inspected for what actually renders. Findings target **systems, methods, and documentation only** — no individuals are named; no personal data is used (PDPA-safe).
- **Read-only compliance:** no project file was modified; the only file created is this review. No commits or pushes were made.

---

## 1. Executive Summary

The mandatory gates all pass on the audited HEAD — but that is precisely why this audit had to go past the gates, and it found real defects the gates cannot see:

- **All gates green** (see §4): `tools/verify_all.py` 4/4 steps pass (catalog, SHA-256 MISMATCH 0, Thai lint, pytest); `catalog.py check` 105 items; `catalog.py audit` 33/33 docs. Round-4 remediations (W-1…W-8) were re-verified as present: L3 purge in the main coastal model, retired-value ledger, Pasak four-definition split, two-baseline bootstrap disclosure.
- **Two high-severity misstatements in published reports** (F1, F2): a DEM provenance caption that describes the Ongkharak hypsometry as "1 m LiDAR fused with FABDEM and Copernicus 30 m" while the computation is a pure Copernicus 30 m run (no LiDAR exists in the repo; FABDEM manifest itself says "not survey data"); and the Route 305 "critical tipping point at +3.20 m MSL" — presented as a headline critical threshold — is a hard-coded stage label with no terrain derivation or source anywhere in the repo.
- **Three high/medium computation-integrity defects** (F3–F5): negative DEM artifacts (down to −14.5 m, impossible in this terrain) contribute 30.1% of the "observed-stage" storage volume and produce 15–18 m "max depth" values; the observed-stage row is mislabeled (2.4 m rendered for a 2.35 m observation) and the machine-readable description contradicts its own fields; and the canal active-storage block is geometrically impossible as published (dead-storage fraction 37.9% exceeds the 28.6% theoretical cap for any bed-48 m/depth-7 m trapezoid; consistent values give ~19 h buffer, not 15.9 h), with unsourced hard-coded economic inputs despite a caption claiming geometric derivation.
- **Tidal-harmonics script carries the exact purge bug that the sibling L3 model already fixed** (F6), plus an auto-generated conclusion that contradicts its own table (it claims "outstanding skill at +12 h/+24 h" while skill is −3.0%/−2.7%), and the audit brief itself (`docs/REVIEW_PROMPT_EN.md`) is stale relative to canonical (F7).
- **Literal-number discipline is enforced by a fixed keyword list, not systematically** (F8) — canonical metric values still appear as hand-typed literals in builders (`8.21`, `6.86`, `486.9`, `126`, fallback `3.19`), demonstrating the exact drift mechanism that produced the stale audit prompt.

Overall verdict: the analysis pipeline's numeric *arithmetic* is largely sound and increasingly well-disclosed, but **claim-to-evidence traceability at the publication boundary still leaks** — captions and narrative text assert derivations that the code does not perform. F1/F2/F5 are the three items that should be fixed before the involved reports are further circulated.

---

## 2. Findings Matrix

| # | Severity | Dimension | Finding | Key references |
|---|----------|-----------|---------|----------------|
| F1 | **High** | 4 (Ongkharak) | Published caption claims hypsometry from "1 m LiDAR fused FABDEM + Copernicus 30 m"; computation is pure Copernicus GLO-30 (30 m); no LiDAR data exists in repo; FABDEM is not an input to this computation | `report/goal7_blocks.py:523-526`; `analysis/goal7_ongkharak_2d_depression.py:2,10,20-21`; `data/08_dem_topography/fabdem/manifest.md`; rendered in `report/คลองเจ้าพระยา2_ประชาชน.html`, `report/คลองเจ้าพระยา2_วิชาการ.html` |
| F2 | **High** | 4 (Ongkharak) | "Critical tipping point +3.20 m MSL" (Route 305 overtopping) is a hard-coded stage label; no crown elevation or derivation/source in repo; published as a headline critical threshold | `analysis/goal7_ongkharak_2d_depression.py:71-72`; `report/goal7_blocks.py:511-512`; no source found via repo-wide search (self-references only) |
| F3 | Medium | 4 (Ongkharak) | 816 DEM cells < 0 m (min −14.5 m; 177 cells < −10 m; 0.734 km²) are counted as real topography: 30.1% of the 19.03 MCM "observed" storage and 5.0% at +3.2 m; max "depth" columns show 15.5–17.7 m | `analysis/goal7/ongkharak_2d_depression_summary.json:5-9,13-15`; recomputed from `dem_30m.npy` + district mask |
| F4 | Medium | 4 (Ongkharak) | Observed row mislabeled: 2.4 m row rendered as "ระดับน้ำจริงในคลอง (ต.ค. 2569)" against a stated +2.35 m observation; row selection relies on float tolerance; JSON description (41.5 km²/17.8 MCM) contradicts computed fields (36.84/19.03) | `analysis/goal7_ongkharak_2d_depression.py:67-68`; summary JSON `:12-17`; `report/goal7_blocks.py:507-508` |
| F5 | **High** | 5 (Economics) | Canal active-storage triplet is geometrically impossible (dead fraction 37.9% > 28.6% cap; implied side slopes from the three values are mutually irreconcilable); "derived from geometry" caption is false (dict of literals, no computation); capex/opex/diverted volume are unsourced hard-codes whose source file is admitted absent | `analysis/goal7_operational_economics.py:343-361` (and `:58-61`); `report/goal7_blocks.py:538-544`; `report/goal7_build_academic.py:611` |
| F6 | Medium | 2 (Harmonics) | Harmonics script: (a) auto-generated conclusion contradicts its own computed skill (claims "outstanding at +12/+24 h" where skill vs persistence is −3.0%/−2.7%; worse than astro baseline at all leads); (b) no purge — 5/11/18/41 train rows have test-window targets; (c) per-lead train sets differ (n_train 1150/1078/1499/1493) due to raw evening gaps, undisclosed | `analysis/goal6_l3_coastal_harmonics.py:170-171,183-191,266,269-275`; `analysis/goal6/l3_coastal_harmonics_summary.json`; recomputed counts |
| F7 | Medium-Low | 7 (Canonical) | `docs/REVIEW_PROMPT_EN.md` (the audit brief) carries retired/stale values: 73.6→35.9 cm (51.2%), 57.1% coverage, "17 of 22" Pasak, "1 m LiDAR/FABDEM", median 3.19 | `docs/REVIEW_PROMPT_EN.md:23,26,32,85-86,102` vs `analysis/goal6/canonical.json:1489-1505,1515,1560-1562` |
| F8 | Low-Medium | 7 (Canonical) | Literal-number enforcement gap: guard scans a fixed string list only; canonical values remain hand-typed in builders (`8.21`, `6.86`, `486.9`, `126`, fallback `513.1`/`3.19`) — the `3.19` default equals the stale prompt value while data renders `3.20` | `tests/test_goal6_consistency.py:111-139`; `report/build_expert_report.py:367`; `report/goal7_blocks.py:512,524-525`; `analysis/goal6_pasak_24y_baseline.py:185` |

Prior round status: none of F1–F8 appears in `archive/reviews/round4_2026-10-17/TRIAGE.round4_2026-10-17.md` (keyword-level cross-check performed; see §3 notes where round-4 open items are adjacent but distinct).

---

## 3. Deep-Dive Findings

### F1 (High) — Published DEM-provenance caption materially misstates the Ongkharak hypsometry

**Claim rendered to readers:**

> "เส้นความสัมพันธ์ระดับ–พื้นที่–ปริมาตร 2 มิติ (2D Hypsometric) ของแอ่งก้นกระทะ อ.องครักษ์ … วิเคราะห์จาก**แบบจำลองระดับความสูงภูมิประเทศ 1 ม.** (LiDAR ผสาน FABDEM และ Copernicus 30 ม.) — ชี้ชัดจุดเปลี่ยนวิกฤตที่ระดับ +3.20 ม.รทก."
> — `report/goal7_blocks.py:523-526` (captions are constructed here and embedded by `goal7_build_public.py:359` / `goal7_build_academic.py:822`)

**What the code actually does:**

- `analysis/goal7_ongkharak_2d_depression.py:2` — title: "…องครักษ์**บน DEM 30m**"; `:10` — source comment: `data/13_sentinel1_copernicus/derived/dem_30m.npy (Copernicus DEM 30m)`; `:20-21` — the script loads exactly two arrays: `dem_30m.npy` and `mask_district_อำเภอองครักษ์.npy`; `:35` — area computed as `len(cells) × 30×30 m²`. Verified by direct load: 570,144 valid pixels → 513.13 km².
- No LiDAR dataset is used or even present in the data flow (the project's LiDAR item ACAD-01 is unobtained).
- FABDEM is *not an input to this computation at all*; the repo uses FABDEM only in a different cross-check script (`analysis/goal7_fabdem_compare.py` → `analysis/goal7/fabdem_compare.json`), and its own manifest states: "**ไม่ใช่ข้อมูลสำรวจ** ใช้ดูความสมเหตุสมผลเท่านั้น" with "ความละเอียด 1 อาร์ควินาที (~30 ม.)" (`data/08_dem_topography/fabdem/manifest.md`).
- The scholarly report on the same project even states the correct fact elsewhere — "แบบจำลองความสูงผิวดินเปล่าอีกชุด (FABDEM ความละเอียดราว 30 ม. ไม่ใช่ข้อมูลสำรวจ)" — so the repo **contradicts itself** between two rendered sections of the same publication set.

**Rendered where:** the false caption appears in `report/คลองเจ้าพระยา2_ประชาชน.html` and `report/คลองเจ้าพระยา2_วิชาการ.html` (verified by extraction from the files). It also propagated into the audit prompt (`docs/REVIEW_PROMPT_EN.md:32,102`), showing the caption is being treated as ground truth by tooling.

**Impact:** the caption overstates the horizontal resolution by 10× (it is a 30 m DEM, not 1 m) and names two provenance elements that do not exist in the computation. Readers/policy users may treat stage–area–volume curves and the +3.20 m tipping analysis as survey-grade when they are 30 m bathtub-model geometry.

**Recommendation (one-shot):** replace the caption text in `goal7_blocks.py:525-526` with the true provenance ("Copernicus GLO-30 (30 m), no LiDAR; FABDEM not an input — used only for a separate plausibility cross-check"), add a regression assert that the caption contains "30 ม." and does not contain "LiDAR", and re-run the goal7 builders once (per canonical discipline).

---

### F2 (High) — The Route 305 "critical tipping point (+3.20 m MSL)" has no derivation in the repo

**Claim rendered to readers:** the Ongkharak table labels the +3.2 m row as "🚨 จุดเปลี่ยนวิกฤต (Tipping Point) — คันทางหลวง 305 ถูกน้ำบ่าข้าม …" (`report/goal7_blocks.py:511-512`) and both published canal reports carry it.

**Verification performed:**

- The script itself sets the value as a constant stage label whose row is then fetched from the curve: `analysis/goal7_ongkharak_2d_depression.py:71-72` — comment "จุดเริ่มบ่าล้นคันทางหลวง 305 (+3.20 ม.รทก.)" and `next(c for c in curve if abs(c["stage_msl_m"] - 3.20) < 0.05)`. There is **no computation of the road crown elevation from any dataset** and no citation.
- Repo-wide search for Route 305 elevation sources: the only occurrences are the script comment, its own downstream copies (`analysis/goal7/canonical.json:6200-6205`, `analysis/goal7/ongkharak_2d_depression_summary.json:26-31`), a generic import note in `goal7_dam_to_gulf_hydraulics.py:370`, and event-reporting notes (`analysis/album_geotag_summary.md:45,50` — road flooded 10–35 cm at Km 41+800 on 4 Oct 2026). **No highway design/crown elevation document or measurement exists in the repo.**
- The chain is self-referential: the audit-prompt formulation ("where floodwater overtops Route 305 … spilling directly into the Rangsit canal network", `docs/REVIEW_PROMPT_EN.md:32`) derives from the same caption.

**Impact:** the +3.20 m level is one of the project's headline "critical thresholds" (it defines when the depression is claimed to spill toward the Rangsit canal network — a qualitatively different hazard). As published, it is an assumption presented as a terrain result. The 2D stage–volume numbers at 3.2 m inherit its uncertainty.

**Recommendation:** either (a) source a crown elevation from the highway authority (FOI — แขวงทางหลวงนครนายก / ทล.305 design file) and document it, or (b) relabel everywhere as a **scenario assumption** ("สมมติระดับบ่าล้นที่ +3.20 ม.รทก. — ยังไม่มีข้อมูลระดับคันทาง") and add it to `analysis/goal7/gaps.json` with a `# gap:` linkage so no narrative asserts it as measured.

---

### F3 (Medium) — Negative DEM cells contaminate the Ongkharak hypsometry (30% of observed-stage volume)

**Recomputation (fresh run on `dem_30m.npy` + district mask):**

```
pixels: 570,144 → area 513.13 km²
cells < 0 m : 816 (0.734 km²)   min = −14.5 m   cells < −10 m : 177   cells < −1 m : 646
stage 2.4 m : negative-cell volume = 5.73 MCM of 19.03 MCM total = 30.1%
stage 2.5 m : 5.80 / 23.27 = 24.9%
stage 3.2 m : 6.31 / 126.22 = 5.0%
max "depth" column: 15.5 m (stage 1.0), 16.9 m (2.4), 17.7 m (3.2)
```

The area is a flat lower-delta district (median elevation 3.2 m; `ongkharak_2d_depression_summary.json:5-9`). Elevations of −14.5 m are physically impossible as terrain and are Copernicus GLO-30 water-body/void artifacts. The script never masks them (`analysis/goal7_ongkharak_2d_depression.py:30-51` sums `h − z` over all cells ≤ h), so the low-stage half of the published curve is dominated by artifact pits: at stage 1.0 m the mean depth is 2.61 m with 15.5 m "max depth", and the first ~5.2 MCM of the curve is essentially pit volume.

**Impact:** published stage–area–volume rows at 1.0–2.5 m (and the "observed" row at 2.4 m) are materially inflated; the "max depth" fields (not rendered, but machine-readable) are absurd. The tipping-point volume "> 125 MCM" is barely affected (5.0% at 3.2 m), but the observed-stage storage claims are.

**Recommendation:** mask or clamp `z < 0` (and document the choice), recompute the curve, and update the JSON + reports via the standard chain. Add a data-quality note in the JSON metadata.

---

### F4 (Medium) — Observed-stage row is mislabeled and its description contradicts its own fields

- The script calls the observed level "+2.35 ม.รทก. ณ สถานี TNy10" (`analysis/goal7_ongkharak_2d_depression.py:67`) but then selects a row by float tolerance on a 0.1-m grid: `abs(stage − 2.35) < 0.05` (`:68`). Floating-point evaluation selects the **2.4 m** row, and the JSON then states `"stage_msl_m": 2.4` (`analysis/goal7/ongkharak_2d_depression_summary.json:13`).
- The same JSON's `description` for this row says "ราว **41.5 ตร.กม.** ปริมาตรน้ำค้างทุ่ง **~17.8 ล้าน ลบ.ม.**" (`:17`) while the computed fields in the same object are **36.84 km² / 19.03 MCM** (`:14-15`). The description's figures are stale from an earlier run and contradict the machine-readable fields.
- The builder labels the 2.4 m table row "**ระดับน้ำจริงในคลอง (ต.ค. 2569)**" (`report/goal7_blocks.py:507-508`), i.e., the published "observed" row displays a 0.05 m upward rounding as if it were the observation.
- (The `critical_thresholds` descriptions are not rendered into any report — verified by grep — so the user-visible defect is the mislabeled row; the JSON inconsistency is an integrity issue for downstream consumers.)

**Recommendation:** snap explicitly to a named nearest grid stage with the quantization disclosed (or add 2.35 m to the sweep), regenerate description strings from computed values (never hand-text numbers into JSON), and label the row "≈ +2.4 ม. (สังเกต +2.35 ม., ปัดตามขั้น 0.1 ม.)".

---

### F5 (High) — Canal active-storage triplet is geometrically impossible; "computed from geometry" caption is false; economic inputs are unsourced

**What is published:** `analysis/goal7_operational_economics.py:343-361` hard-codes a literal dict:

```
canal_length_km 135.9 · design_depth_m 7.0 · bed_width_m 48.0
total_storage_mcm 55.4 · dead_storage_depth_m 2.0 · dead_storage_mcm 21.0
active_storage_mcm 34.4 · design_discharge_m3s 600 → buffer_duration_hours 15.9
```

and the builder renders it with the sentence "**จากการคำนวณมิติคลอง**รูปตัดสี่เหลี่ยมคางหมูตลอดความยาว 135.9 กม. …" (`report/goal7_blocks.py:540`) — i.e., it claims a geometric derivation. **No geometry computation exists anywhere in the script** (verified: the dict is written directly to the output JSON at `:344-361,363-373`).

**Geometric impossibility (recomputed):** for any trapezoid with bed B=48 m, depth 7 m, side slope m (H:V), the bottom-2 m slice fraction is
`(96+4m)/(336+49m)`, which is **maximized at m=0 → 2/7 = 28.57%** and decreases for wider sections. The published dead fraction is `21.0/55.4 = 37.9%` — **exceeds the theoretical cap by ~9 points**. Equivalently:

- Implied side slope from the published total: `55.4 MCM @ L=135.9 km` → cross-section 407.7 m² → m = (407.7−336)/49 = **1.46** → dead = 96+4(1.46) = 101.9 m² → **13.84 MCM** (published: 21.0).
- Implied side slope from the published dead value: 154.5 m² → m = **14.6** (absurd for a canal).
- The EIA-based section used elsewhere in this repo — "ท้อง 51 ม. ลาด 1:3 น้ำลึก 7 ม." (`report/goal7_build_academic.py:711`) — gives total 68.5 MCM ≠ 55.4.
  No single admissible geometry reproduces the published (55.4, 21.0, 34.4) triple.
- Consistent recomputation: dead ≤ 15.83 MCM → **active ≥ 39.6 MCM → buffer ≥ 18.3 h** (with m=1.46: active 41.56 MCM → 19.2 h). Published: 34.4 MCM / 15.9 h — underestimates by 15–21%.

**Unsourced economics:** `capex_mb = 160046.0`, `opex_annual_mb = 519.0`, `diverted_volume_mcm = 1970.0` are literal constants (`:58-61`) commented as coming from "กรอบวงเงิน EIA 2569 (รายงานชี้แจงครั้งที่ 2)" and an annual-average diversion; the repo's own academic report admits the cited source file is absent: "ฉบับย่อ ก.พ. 2569 ที่สมาคมอ้าง (160,046 ล้านบาท · 7 ปี) — **ไม่มีไฟล์** … ขอจาก สผ." (`report/goal7_build_academic.py:611`). The levelized-cost outputs (6.81/8.17/10.35 THB/m³ at 7/9/12%) recompute correctly **from these inputs** — the discounting math itself is fine; the inputs are what cannot be traced in-repo.

**Rendered where:** the storage block appears in `report/คลองเจ้าพระยา2_วิชาการ.html` and `report/สมุดปกขาว_เจ้าพระยา2.html` (verified by extraction; not in the public summary version).

**Impact:** the white paper's "the canal is not storage — it fills in <1 day" argument understates the true consistent buffer (≥18 h) and cites unsourceable cost figures; if the geometry were audited externally, the same caption ("จากการคำนวณมิติคลอง") is directly falsifiable.

**Recommendation:** (a) implement the actual trapezoid computation in the script (bed 48 vs EIA 51 m must be reconciled first — pick the citable design section), (b) recompute dead/active/buffer from geometry, (c) either attach the capex/opex/diverted sources (FOI for ฉบับย่อ) or clearly print "ตัวเลขจากแหล่งที่ยังไม่เปิดเผย — ประมาณการ" in the rendered block, and (d) fix or delete the "จากการคำนวณ" wording until (a) is true.

---

### F6 (Medium) — Tidal-harmonics script: false auto-conclusion, missing purge, unstable train sets

**(a) Auto-generated conclusion contradicts computed numbers.** The script rewrites `analysis/goal6/l3_coastal_harmonics_findings.md` on every run with a hard-coded bullet (`analysis/goal6_l3_coastal_harmonics.py:269-275`): "ทักษะการพยากรณ์โดดเด่นที่ระยะ +12 ชม. และ +24 ชม. … โมเดลให้ค่าความคลาดเคลื่อนต่ำกว่าฐานเทียบเดิมอย่างมีนัยสำคัญ". The table above it (generated from the summary JSON) shows the opposite: skill vs persistence = **+2.9% / −3.0% / −2.7% / −4.2%** for +6/+12/+24/+48 h, and vs the astro baseline the model is worse at **every** lead (−6.6/−10.9/−6.3/−8.6%). Only at +6 h vs the weak persistence baseline is it marginally ahead. (Also a formatting bug: negatives render as `**+-3.0%**`, from the `**+{value}%**` template at `:266`.)
Report impact is contained — the false text is not rendered into any report HTML (verified: no "โดดเด่น"/"ทักษะการพยากรณ์" in `report/ชุดเทียบมาตรฐาน2554.html`; the Report-4 caption quotes only R²/RMSE at +24 h, `report/goal6_build_report4_draft.py:307`) — but the artifact is committed and rewritten each run, and is exactly the kind of hard-coded narrative the repo's own rules prohibit.

**(b) No purge — train rows with targets inside the test window.** The split is by timestamp only (`d < TEST_START`, `:183-191`), so for leads 6/12/24/48 h there are **5 / 11 / 18 / 41 train rows whose targets fall in the test window** (recomputed from the same raw files). The sibling model already implements the fix — `analysis/goal6_l3_coastal_model.py:217` (leak mask) and `:245` (`train_mask = (~test_mask) & (~leak[:, k])`, with per-lead `n_train` variation documented at `:333-334`). The harmonics script does not.

**(c) Per-lead train/test sets differ substantially, and it is undisclosed.** n_train in the summary JSON is **1150 / 1078 / 1499 / 1493** (`analysis/goal6/l3_coastal_harmonics_summary.json:47,59,71,83`) — note it *increases* with lead. Root cause (verified on the raw files): the C.12 raw hourly feed has systematic daily evening gaps — July: missing ~15:00/16:00→01:00 every day; Aug: 18:00→01:00; later single hours. The check `if target_str not in c12_data: continue` (`:170-171`) therefore excludes different *hours-of-day* per lead, so each lead is trained/evaluated on a different dataset; claims like "+24 h is more accurate than +6 h" are confounded by composition, not skill. (The raw-file gap pattern is itself a data-quality item worth documenting.)

**Recommendation:** add the same purge filter as the L3 model; regenerate the findings MD from values (no recommendation sentences with attached numbers); fix the `+-` formatting; disclose the per-lead n and the evening-gap cause; state plainly that no skill vs the astro baseline was achieved at any lead.

---

### F7 (Medium-Low) — The unified audit prompt is stale relative to canonical (and repeats the F1 caption error)

`docs/REVIEW_PROMPT_EN.md` was designated the primary audit brief at `e0b9cdf` but was not synchronized with the Round-4/5 canonical state. Verified stale pairs (prompt → current):

| Prompt (stale) | Current artifact |
|---|---|
| `:26,:85` "+6 h linear RMSE falls from **73.6 cm to 35.9 cm (51.2%)**" | `canonical.json:1560-1562` — **79.6 → 37.4 cm (53.0%)** |
| `:86` "usable coverage … **57.1%**" | `canonical.json:1515` — **`test_coverage_pct: 47.1`** |
| `:23` Pasak "**17 of 22** years" | `canonical.json:1489-1505` — `pasak_year_counts` (20/22; 16/22; 17/24); "17/22" is in the **retired ledger** (`:2630`) |
| `:32,:102` "**1 m LiDAR/FABDEM**"; median "**+3.19 m**" | actual: Copernicus 30 m (F1); median **3.20 m** (summary JSON `:7`) |

**Impact:** any follow-up audit that anchors on this prompt will (i) test the wrong numbers, (ii) propagate the disproven LiDAR provenance claim, and (iii) re-flag already-resolved items. This audit had to re-derive everything from canonical/precise files for exactly this reason.

**Recommendation:** regenerate the prompt's numbers from canonical (or replace numbers with file pointers), add the prompt to the anchor test pattern used for HANDOFF/GOAL6_PLAN (`tests/test_goal6_consistency.py:142-162`), and re-verify after the next `goal6_build_all.py` run.

---

### F8 (Low-Medium) — Literal-number guard is keyword-based; canonical values still hand-typed in builders

The rule " builders must not print metric literals; render from canonical JSON" is enforced by `tests/test_goal6_consistency.py::test_builder_source_has_no_metric_literals` — but only against a **fixed list of strings** (`:114-126`: 13 specific literals; the "all builders" extension checks 5 more). Decimal literals that are not on the list pass. Verified instances (values currently match canonical — the issue is discipline/drift risk, and F7/the `3.19` default shows drift already happens):

- `report/build_expert_report.py:367` — "ที่ระดับสันตลิ่งจริง **8.21** ม.รทก. … เริ่มท่วมชานพักที่ **6.86** ม.รทก. รองรับได้ **486.9** ลบ.ม./วินาที" — hand-typed in the same sentence that uses `@@R:` tokens for its neighbors; all three values exist in `analysis/canonical_numbers.json:926-931`.
- `report/goal7_blocks.py:512` — "ปริมาตรน้ำสะสมเกิน **126** ล้าน ลบ.ม."; `:524-525` — fallback defaults `513.1` and `**3.19**` (the rendered value is 3.20 because data is present, but the default is stale — the *same* 3.19 that persists in the audit prompt).
- `analysis/goal6_pasak_24y_baseline.py:185` — hand-typed comparison row "40.9% (9 ใน 22 ปี)" in an auto-generated findings MD (value traces to `canonical_numbers.json:94,516`, but is not computed or imported by this script).

**Recommendation:** extend the guard from a keyword list to a positional scan — e.g., fail on any `\d+\.\d+` inside rendered string literals in `report/*.py` unless preceded by a token/substitution marker, with an explicit allowlist regenerated from canonical. This is cheap and would have caught all four instances above (and would have caught F1's caption provenance words, if the guard also scanned for "1 ม." near "LiDAR").

---

## 4. Verified Invariants (what passed and why it can be trusted)

**Mandatory gates (run on HEAD `02ba87c`):**

- `python tools/verify_all.py` → all 4 steps pass: catalog check (105 items registered), SHA-256 **MISMATCH 0** across manifest hashes, Thai-language lint, full pytest suite.
- `python catalog.py check` (105 items) and `python catalog.py audit` (33/33 documents) pass.
- Targeted compliance pytest: `tests/test_legal_compliance.py`, `tests/test_privacy.py`, `tests/test_thai_language_lint.py`, `tests/test_contrast.py` → **21 passed**.

**Spot-verifications of critical claims (independent recomputation):**

- **1D routing (Dim 1):** Muskingum–Cunge weights verified to sum to 1; the X-parameter clamp is disclosed with the raw probe (96.7% negative raw values, `hydraulic_1d_routing_summary.json:9-17`); grid non-convergence is disclosed and quantified (RMSE 103.8 → 108.0 cm as n_sub 6→48, `:111-132`); the model scope (no Kgt.30 downstream boundary) and the Q→Q vs H→H incomparability caveat are explicit (`:5,:53`); negative bias (−80.1 cm) is published separately from residual (69.4 cm), per Round-4 decision W-4.
- **L3 coastal ML (Dim 2):** purge of test-window targets implemented in the main model (`goal6_l3_coastal_model.py:217,245`; per-lead n_train 1087/1078/1066 in canonical `:1576,1599…`); all features causal at time t; the fact that the linear model is *worse* than the tide-aware persistence at +24 h is disclosed with bootstrap CIs (`canonical.json:1591-1595`, −41.3% [−66.5, −19.5]); coverage 47.1% disclosed with cause (BKK001 feed end).
- **Tidal harmonics physics (Dim 2):** the extracted amplitudes (K1 0.603 m > M2 0.430 m, `l3_coastal_harmonics_summary.json:13,29`) are consistent with the diurnal-dominant tidal regime of the upper Gulf of Thailand — unusual-looking but plausible; **not flagged**.
- **Compound flood matrix (Dim 3):** now registered in `analysis/goal6/canonical.json` (block + description; thresholds 2.00/2.40/2.70 m vs floodwall 2.80 m consistent across canonical and report); uncalibrated status and the two-point plausibility provenance are disclosed in both the script docstring (`compound_flood_risk.py:31-46`) and canonical `calibration_status`/`limitations`; the Round-4 open item "register the matrix into canonical" is thereby **resolved**.
- **Counterfactual (Dim 5):** `share_of_excess` is computed against the recomputed excess (38.8% of 11,325.1 MCM); synthetic-hydrograph and dq/dh limitations are disclosed; the 2026 case-equality is documented; naming duplication resolved (goal7 key is `cp2_bypass_counterfactual`).
- **Governance (Dim 6):** Pasak four-definition split present (`canonical.json:1489-1505` with definitions text; retired "17/22"/"17 จาก 22" entries in the ledger `:2628-2631`); Khun Dan medians and capacity-threshold definitions labeled (W-3/W-5 remediations); main L3 model selection moved to a validation window (W-5).
- **Canonical/test discipline:** the report builders for reports 3/4 render flood/rain/reservoir numbers from canonical and the anchor tests (`:142-162`) pass; retired-value tests pass (`:38`); contrast tests enforce ≥4.5:1 text / ≥3.0:1 data pairs across ≥40 pairs + compound palette solidity + banned color/jargon lists; legal test enforces model-uncertainty disclaimers and a defamation blocklist across 7 published reports; privacy test scans git-tracked text for phones/profile links.
- **Stale-number sweep:** no rounded L3 legacy figures (73.6/35.9/51.2/57.1) appear in any published HTML (word-boundary scan; earlier substring hits were "135.9 กม." artifacts).

---

## 5. Information Gaps (to close outside the code)

1. **Route 305 crown elevation / design level** — required to justify or replace the +3.20 m tipping label (F2). FOI: แขวงทางหลวงนครนายก (ทล.305 data).
2. **LiDAR survey (ACAD-01)** — not obtained; until then the Ongkharak caption must state Copernicus 30 m (F1).
3. **Canal design section reconciliation** — bed 48 m (storage block) vs 51 m / 1:3 (EIA-based section used in the hydraulic model, `goal7_build_academic.py:711`); needed for F5 fix.
4. **EIA cost annexes** — "ฉบับย่อ ก.พ. 2569 (160,046 ลบ. · 7 ปี)", opex and annual diverted-volume sources (self-admitted absent, `goal7_build_academic.py:611`).
5. **C.12 raw feed quality** — systematic evening gaps in the stored hourly series (F6c); decide an imputation/documentation policy for any hourly model that consumes it.
6. **Known-open Round-4 items (unchanged, not re-reported):** Khun Dan mass-balance closure (Wave D, awaiting agency release/pumping data) and BKK001 station name/scope confirmation with the agency (`TRIAGE.round4_2026-10-17.md:85`).

---

*End of review. All file:line references and numeric recomputations were verified against the repo at HEAD `02ba87c`; no project file was modified.*
