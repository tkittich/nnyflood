# Hydrological Audit & Red-Team Report: nnyflood (round 9, Claude Sonnet 5.5, commit c8bf9c4)

> Scope: a focused pass against the 28 Oct prompt (`docs/REVIEW_PROMPT_EN.md`), concentrating on Dimensions 13 and 14, the literal gate (Dimension 7) and cross-report numbers (Dimension 8). The reviewer also wrote the code under review (Claude Sonnet 5.5 made the 27–28 Oct commits), so independence is limited; the other dimensions were **not** re-audited this round.
> Method: read-only. Commands run: `pytest` (330 passed), `python catalog.py audit` (all 48 documents registered), scratch scripts under the session scratchpad that read the JSON/HTML files and call `tools/number_inventory.py` functions on a scratch file outside the repo. `tools/verify_all.py` was **not** run (it rewrites `report/assets/verification.json`).

## 1. Executive Summary
- **Overall reliability**: Medium-High for the parts checked. Every sensitivity summary recomputes from its pass list; no number drift found in the cross-report census.
- **Strengths**: (1) pre-registration order holds (`8c728a5`, rule, 27 Oct 21:40 → results `c71939b`, 28 Oct 03:49); (2) all five new summaries recompute exactly from `passes` and match what Report 3 prints; (3) the Dimension 14 scan found no canonical value that fails to reach the HTML.
- **Vulnerabilities**: (1) Report 3's single 'sensitive' label (Maeklong) rests on a change of which pass sets the peak, undisclosed; (2) pre-event controls are not expressed against the peak, and 'seasonal' is an untested reading; (3) the literal gate has structural blind spots, one of them a plain bug.

## 2. Findings Matrix
| ID | Severity | Target | Root cause | Action |
|---|---|---|---|---|
| F-01 | Medium | `report/goal6_build_report3_draft.py` (Maeklong sensitivity sentence), `analysis/goal6/s1_ref_sensitivity_maeklong.json` | The basin 'peak' change (+10.4%) compares the largest primary pass (orbit 31, 380.3 km²) with the largest alternative pass (orbit 141, 419.9 km²). The same pass moves only +3.9%. | Print the orbit that sets each peak; keep the label but say it comes from a switch of passes. |
| F-02 | Medium | Report 3 reference-date sentences; `canonical.s1_ref_dates` | Controls are printed as ranges but never as a share of the peak. 'Seasonal change' is asserted, not tested. | Add control ÷ peak per basin (descriptive); say the cause of a control is unknown. |
| F-03 | Medium-Low | `tools/number_inventory.py:100-107` (`builder_literals`) | Year exemption `2400 <= val <= 2600` applies to every unit; the ≥3-digit rule skips values like `ร้อยละ 60` and `9.2%`; string concatenation and spelled-out units pass. | Limit the year exemption to unit `year`; decide and document the two-digit policy. |
| F-04 | Low | Report 3 reference-date line | Label '(วันที่ฝนเริ่มหรือหลังจากนั้น)' is by calendar day. The orbit 31 scene was taken 20 Sep 06:07 Thai time, on the day with the smallest daily mean rain in the table. | Say 'taken on or after the calendar day rain began' and state the rain before 20 Sep is not in the table. |
| F-05 | Low | `analysis/goal7_ongkharak_hydraulics.py:233-238` | Marked deprecated in the registry and docstring only; running it still writes `ongkharak_hydraulics` into `analysis/goal7/canonical.json`. | Exit at the top of `main()` or delete the write. |

## 3. Deep-Dive Findings

### [F-01] Maeklong 'sensitive to reference' label comes from a change of peak-setting pass
- **Location**: `analysis/goal6/s1_ref_sensitivity_maeklong.json` (`summary`, `passes`); Report 3 sentence beginning 'ความไวต่อวันของฉากอ้างอิง (ลุ่มแม่กลอง…'.
- **Evidence** (script over `passes`, role `event_or_after`): primary peak 380.3 km² on orbit 31 (1 Oct), alternative peak 419.9 km² on orbit 141 (27 Sep, primary value there 332.2). Peak-setting pass differs → summary +10.4%. Orbit 31 alone: 380.3 → 395.0 = +3.9%. For Pasak, Thachin, Ping–CP and Bangkok lower the same pass sets both peaks (−9.2%, −2.4%, +9.4%, +3.2%).
- **Critique**: the pre-registered label is a table label only, so nothing is mis-stated, but a reader will take '+10.4% of the basin peak' as one pass moving by that much. It is a 26% move on a different, lower-coverage pass (coverage 0.39) taking over.
- **Proposed solution**: add orbit and date of each peak to the sentence; this is a wording change, no recomputation.

### [F-02] Controls against the peak, and the word 'seasonal'
- **Evidence** (largest control ÷ primary peak, from the five JSON files): Maeklong 189.2 / 380.3 = 0.50; Ping–CP 1,070.7 / 2,656.6 = 0.40; Thachin 327.8 / 1,667.2 = 0.20; Bangkok lower 176.6 / 1,320.8 = 0.13; Pasak 195.0 / 1,576.6 = 0.12. In Ping–CP the control pass and the peak pass are the same orbit (31) with the same coverage (0.32). The alternative-minus-primary peak difference there is +250.6 km², far below the 1,070.7 km² control, so most of the dark area seen on 20 Sep against 7 Sep was not dark again on 1 Oct.
- **Critique**: Report 3 says the control 'tells the size of seasonal change before the event'. The data cannot separate seasonal paddy water, early rain, wet-soil or roughness effects, or short-lived inundation. Read as a false-alarm proxy, the quiet-pair change is a large fraction of the peak in two basins. The text does say to read the peak as a range by orbit, which is the right direction; the ratio would let the reader see how wide.
- **Proposed solution**: descriptive column 'largest control ÷ peak'; replace 'seasonal' with 'cause not separated'. Stays inside the prereg (§ descriptive only).

### [F-03] Literal gate blind spots (reproduced on a scratch file, not in the repo)
- **Evidence** (`builder_literals` on a scratch builder; MISSED = no row returned): `"2,512 ตร.กม."` MISSED; `"ร้อยละ 60"` MISSED; `"9.2 ม."` MISSED; `"9.2%"` MISSED; `"1,576 " + ".6 ตร.กม."` MISSED; `"1576.6 ตารางกิโลเมตร"` MISSED; `"1,576.6 sq.km"` MISSED; `"1,576.6 ตร.กม."` and the Thai-digit form CAUGHT.
- **Cause**: line 100-101 `digits >= 3 and unit not in ("year",) and not (2400 <= val <= 2600)`. The band is meant for Buddhist-era years but is applied to every unit. Real printed metrics sit in it: `2,566 ลบ.ม./วินาที` (Report 7), `2,541 ล้าน ลบ.ม.` (Report 3), `2,600 หลัง` (Report 7). I did not trace whether those come from JSON; the point is that the gate cannot see them either way.
- **Critique**: the two-digit skip is by design (docstring says ≥3 digits) but the prompt asks reviewers to try a `ร้อยละ N` phrase and the project's own headline shares are two-digit. Concatenation and long-form units are adversarial cases; the gate is a ratchet against accident, not an adversary.
- **Proposed solution**: apply the 2,400–2,600 exemption only when the unit is `year`; either count two-digit percentages or state the policy in the docstring and `docs/REPORT_CONVENTIONS.md`. Adding cases will change the allowlists, so use `--write-allowlist` and review the diff.

### [F-04] 'On or after the day rain began'
- **Evidence**: `canonical.s1_ref_dates.rain_days` starts 20 Sep (11.9 mm mean, smallest of the 15 listed days); orbit 31 primary reference 20 Sep 06:07–06:08 Thai time; orbit 91 on 21 Sep 06:00; orbit 68 on 22 Sep 18:20. The table has no rain before 20 Sep, yet the controls compare passes taken 13 days earlier.
- **Critique**: the label is correct by calendar day but suggests rain had fallen before the scene. For orbit 31 it had not (same-day morning). The 7–19 Sep rain is not shown, so an early-rain explanation of the Ping–CP control cannot be checked from the report.
- **Proposed solution**: wording as in the matrix; optionally add the 7–19 Sep daily rain to the table, reading the same rain source.

### [F-05] Deprecated script can still write to canonical
- **Location**: `analysis/goal7_ongkharak_hydraulics.py:233-238`. Registry status `deprecated`; round-8 triage §7 ก2 says the tables were removed.
- **Critique**: nothing reads the key now, but a rerun by habit would add an unreviewed, hand-typed block to the ledger that other tests treat as data.
- **Proposed solution**: raise at the top of `main()` with the reason.

## 4. Intra-Report & Cross-Report Consistency
- **Census (HTML text, all seven files)**: retired values 55.4, 41.6, 54.5 and 36.5 appear in none; the strings 88:12 and 12:88 appear in none (I did not check in which form the ratio is printed). 68.5 / 53.0 / 24.5 appear in Reports 7–8 and the policy brief; 68.5 and 53.0 also appear once in Report 3, which I did not read in context. 15.5 and 10.5 appear in Reports 1–3 as well, probably other quantities (not checked). 1,970 and 1,988 appear together in Report 8 and the policy brief; round-8 ก7 made the 1,970 an assumption. Every report has one 'อ่านจบในตัวเอง' statement and a TLDR block.
- **Dimension 14**: 35 goal-6 and 69 goal-7 canonical keys. Eight are not named in any `report/*.py` (`rain_2554_vs_2569`, `dams_2554_over_urc_days`, `pasak_year_counts`, `design_2565_structs`, `ayutthaya_dqdh_rating`, `legal_and_nuclear_assessment`, `acid_sulfate_soil_assessment`, `interbasin_transfer_vectors`). Sampled values from each (acid-soil rai and share, the 241-day Pa Sak count, 20/22 and 17/24) are in the built HTML. I did not trace the access path, so these are rendered through a path the name search does not see; a test that builds each table and fails on an empty one would be safer than a name search. Anchored matrix (8.1) and the learned-model table (7b) are present in Report 4.
- **Heading scan**: near-empty headings found are parent headings followed directly by a subheading; no empty section found.

## 5. Verified Invariants
- `pytest`: 330 passed (81 s). `catalog.py audit`: all registered.
- Each of the five new sensitivity files: `peak_primary_km2` and `peak_alt_ref_km2` equal the maximum over `event_or_after` passes; `peak_change_pct` matches.
- Commit order for the 28 Oct run: rule `8c728a5` (27 Oct 21:40) before results `c71939b` (28 Oct 03:49).
- Thai-time conversion on two scenes: `1SDV_20260919T230750` (UTC) → 20 Sep 06:07 Thai time, as Report 3 prints for orbit 31; `…T230815` → 06:08.
- Canal storage: 504 m² × 135.9 km = 68.49 MCM; 68.5 − 15.5 = 53.0; 53.0 MCM ÷ 600 m³/s = 24.54 h.
- No key material matched `api_key=`-style patterns in tracked files outside `docs/reviews` and `archive`; tracked `data/12_gistda_flood/cdse_*` files are scene lists.

## 6. Information Gaps
- Rain between 7 and 19 Sep (needed for F-02/F-04).
- Whether the three in-band literals in F-03 come from JSON.
- Not re-audited this round: Dimensions 1–6, 9–12; routing, tidal, 2-D model and OCR findings stand as in the round-8 triage.

## 7. Recommendations
- **Methodological**: report each control as a share of the same-orbit peak; treat peak-setting-pass changes as their own line.
- **Governance**: replace name-based coverage of canonical keys with a test that renders each block and fails on an empty table; close the 2,400–2,600 band hole in the gate before the next allowlist review.
