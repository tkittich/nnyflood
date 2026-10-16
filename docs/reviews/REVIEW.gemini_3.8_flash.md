# REVIEW — เป้าหมาย 7 (คลองเจ้าพระยา 2) · Independent Red-Team Review

> **Reviewer:** Gemini 3.8 Flash (Independent Red-Team Reviewer)  
> **Date:** 15 October 2026  
> **Mode:** Read-only review (No project code or data files modified/committed)  
> **Target Scope:** Goal 7 — Chao Phraya-2 Flood Diversion Canal (Chainat–Pasak–Gulf of Thailand), Nakhon Nayok reach analysis, engineering screening, and generated reports (`report/คลองเจ้าพระยา2_*.html`).  
> **Core Baselines Checked:** `python -m pytest -q` (85 passed), `python -I analysis/verify_data_integrity.py --quick` (2,885 OK, 0 MISMATCH).

---

## 1. Executive Summary (≤10 lines)

1. **Overall Trustworthiness:** Moderate to High on document transcription; **Low to Questionable on open-channel hydraulic screening (§3.13, §3.15)**.
2. Official EIA numbers, economic indicators, land/building counts, and the 99-structure table are transcribed with near 100% fidelity from primary PDFs.
3. Legal, defamation, and PDPA compliance is strictly maintained across all three reports (zero named individuals, zero personal data, system-focused framing).
4. **Fix 1 (Hydraulic Flaw):** Option 2 (§3.13) falsely assumes outlet pumping lowers water levels *uniformly* over 134 km; in subcritical flow, drawdown decays upstream, and lowering the bed by 1.5–3 m at km 134 causes basal heave in soft Bangkok clay and severe saline intrusion.
5. **Fix 2 (Double-Counting Drainage):** Local drainage screening (§3.15, Q18) sums 47 m³/s of siphons and 28 m³/s of connecting canal to balance overland runoff; these are dedicated natural stream conduits that will already be running full during a regional storm.
6. **Fix 3 (Stale Literal & Canonical Leak):** Academic §3.1 still states embankment height as `ราว 2.5–4.8 ม.` (obsolete DSM artifact superseded by 3.2–4.8 m in §21); Goal 7 builders contain over 50 hardcoded numeric literals not covered by automated consistency tests.
7. **Solid Point 1:** Longitudinal profile levels (`_profile_levels`) perfectly reproduce all printed elevations on EIA 2569 Fig. 2.3.2-9 and 2561 Fig. 2.3.2-5.
8. **Solid Point 2:** Structure Table 2.3.2-3 cross-version identity (0 differences across 2561, 2564, 2566, 2569) is confirmed across 20+ spot-checked rows.
9. **Solid Point 3:** GIS overlay finding that the canal crosses the Ban Na floodway for 16.8 km (47% of the Nakhon Nayok reach) is robust under ±300 m alignment perturbations (15.7–16.6 km / 45–48%).

---

## 2. Findings Table (Most severe first)

| id | severity | claim in the report (file:line or section) | contradicting evidence (file:line, PDF page, or command output) | how to reproduce | suggested fix (do not apply it) |
|---|---|---|---|---|---|
| **F1** | **goes beyond evidence / hydraulic flaw** | Academic report §3.13 (Option 2): Lowering the outlet water level by 1.5–3.0 m via pumping lowers the entire water profile uniformly over 134 km, reducing crest height in Nakhon Nayok ("ระดับน้ำทั้งแนวลดลงเท่ากัน ท้องคลองปลายทางลึกลงตามกัน"). | Open-channel subcritical flow hydraulics ($Q=600\text{ m}^3/\text{s}, y=7\text{ m}, b=51\text{ m}, Fr \approx 0.15$). An outlet drawdown produces an $M_2$ backwater curve that decays upstream. At km 40 (94 km upstream), outlet drawdown has virtually zero effect unless the entire 94 km canal bed is excavated deeper. Furthermore, deepening the coastal bed from -5.50 to -8.50 m MSL in soft Bangkok marine clay causes severe basal heave, slope failure, and saltwater intrusion into coastal aquifers. | Run open-channel standard step backwater integration for $S_0=1/25000, n=0.016, Q=600$ with $y(134)=5.5\text{ m}$; observe $y(x)$ upstream. | Remove the claim that outlet pumping lowers water levels uniformly over 134 km. Explicitly state that lowering water surface at km 40 requires deepening the canal bed along the entire upstream reach, and state the geotechnical/salinity risks. |
| **F2** | **goes beyond evidence / engineering flaw** | Academic report §3.15 & Q&A Q18: Local runoff from the 5–10 km strip upstream of the embankment (40–128 m³/s) is safely absorbed by local drainage capacity of 76–79 m³/s (sum of 8 small siphons 47 m³/s + connecting canal 28 m³/s + side ditches 1.4–4.4 m³/s). | This double-counts dedicated stream capacities. The 8 siphons carry existing natural rivers and irrigation canals (Khlong 28, Khlong 29, Khlong Bang Pla Kot, Khlong Ban Na). During a regional flood storm, their upstream sub-basins are already generating peak discharge. The siphons cannot simultaneously drain their natural catchments AND take 47 m³/s of overland field runoff. The connecting canal is likewise dedicated to PK-AT-4 (Mae Nam Nai, 28.05 m³/s). | Open Table 2.3.2-1 and Table 2.3.2-3 in `1. รายงานหลัก EIA.pdf` (pp. 122–133) and inspect catchment assignments. | Clarify that siphons and connecting canals are dedicated crossings for existing river channels running at capacity during storms, not available surplus capacity for local overland sheetflow. |
| **F3** | **inconsistent / stale text** | Academic report §3.1 "สิ่งที่รู้แล้ว" item (3): "สันคันสูงกว่าพื้นเดิมราว **2.5–4.8 ม.**" (`report/goal7_build_academic.py:71`). | Everywhere else in the academic report (§3.3b, §3.11), the public report, and Q&A, the figure used is **3.2–4.8 ม.** (or 3.5–4.8 m for km 40–70). `GOAL7_PLAN.md` §21 explicitly superseded the 2.5 m figure (which was an artifact of rough DSM sampling). | `grep -n "2.5–4.8" report/goal7_build_academic.py` | Change `2.5–4.8 ม.` to `3.2–4.8 ม.` and render it directly from `canonical.json -> eia_profile.nn_reach.crest_above_ground`. |
| **F4** | **legal risk / goes beyond evidence** | Academic report §3.11 c: Embankment breach instantaneous peak discharge is calculated as 1,019 to 10,197 m³/s using broad-crested weir formula ($Q = 1.7 B H^{1.5}$), framing it as comparable to or larger than the 2011 Chao Phraya flood peak. | The formula assumes an instantaneous full-depth breach with infinite reservoir storage and zero tailwater resistance. In reality, the entire reach holds only 11.1 MCM above ground; draining at 1,000–3,000 m³/s would empty the reach in 1–3 hours. Stating peak numbers without emphasizing finite volume, tailwater backpressure, and breach formation time risks public alarm and defamation scrutiny under Thai law. | Review `docs/LEGAL_REVIEW.md` §4 and recompute $V_{storage} / Q_{breach}$. | Add clear qualifying language: emphasize that this is a theoretical maximum instantaneous weir capacity without tailwater, that storage is limited to 11.1 MCM (emptying within hours), and compare total volume rather than instantaneous peak. |
| **F5** | **inconsistent / calculation error** | Academic report §3.11 c: "ปริมาตรน้ำเหนือผิวดินระหว่าง ปตร. กม.23–74 ... ราว 14.0 ล้าน ลบ.ม. (บนสมมติฐานว่าระดับน้ำสูงสุดสูงกว่าผิวดินเฉลี่ย 3.3 ม. ตลอด 51 กม.)". | Exact trapezoidal integration of the digitized ground line and design water level from `PROFILE_FIG` between km 23.0 and km 74.0 yields **11.10 ล้าน ลบ.ม.** (not 14.0 MCM, a 26% discrepancy). | Run trapezoidal integration: $\sum 0.5 \times (h_i + h_{i+1}) \times \bar{B} \times \Delta x$ where $\bar{B} \approx 65\text{ m}$. | Update 14.0 MCM to 11.1 MCM based on the integrated profile, and explain the difference between uniform approximation and actual profile geometry. |
| **F6** | **inconsistent / canonical rule violation** | `AGENTS.md` Rule: "builder ห้ามพิมพ์ตัวเลข metric เป็น literal — TLDR/บท/ตารางเรนเดอร์จาก JSON เท่านั้น". | While Goal 6 enforces this with `tests/test_goal6_consistency.py:test_builder_source_has_no_metric_literals`, Goal 7 builders contain over 50 hardcoded literals (e.g. `176.9 ลบ.ม./วินาที`, `120 ลบ.ม./วินาที`, `74.0 ลบ.ม./วินาที`, `36 ลบ.ม./วินาที`, `600 ลบ.ม./วินาที`, `2.5–4.8 ม.`). | Run a regex literal scan across `report/goal7_build_*.py` matching canonical values. | Port `test_builder_source_has_no_metric_literals` to `tests/test_goal7_report.py` and replace hardcoded literals in builders with references to `canonical.json`. |
| **F7** | **factually wrong / overclaim** | `canonical.json -> eia_structs.src` & `GOAL7_PLAN.md` §21: "ตาราง 2.3.2-3 คอลัมน์ Q แรก (คลองเดิม) ... ตรงกับน้ำหลากรอบ 10 ปี 5 วัน **เฉพาะแม่น้ำใน (28.05 ลบ.ม./วินาที)**". | Table 2.3.2-3 Row 23 (km 20.233, Khlong Nong Khae) lists $Q_1 = 18.05\text{ m}^3/\text{s}$. Table 2.3.2-1 (EIA 2569 p. 149 / 2561 p. 122) lists sub-basin PK-AT-3 (Khlong Nong Khae) 10-year flood as **18.080 m³/s** (difference of only 0.17%). Thus, at least TWO major streams match the 10-year catchment flood. | Inspect Row 23 of `analysis/goal7/eia_structs.json` and compare with `canonical.basins_2569[2]`. | Revise "เฉพาะแม่น้ำใน" to state that at least two crossings (Mae Nam Nai 28.05 and Khlong Nong Khae 18.05) match their sub-basin 10-year flood peaks. |
| **F8** | **goes beyond evidence / hydraulic limit** | Academic report §3.13 (Option 1 - Wide Canal): Proposes widening canal bed to $b=157\text{ m}$ to maintain water at natural ground level ($h_t = 0\text{ m}$), yielding required slope $S = 1:192,557$ (0.5 cm/km). | Under Gulf of Thailand tidal cycles, spring high tides and storm surges reach +2.00 to +2.50 m MSL. Natural ground at km 40–60 is only +2.0 to +3.5 m MSL. Maintaining water level at ground elevation means high tide exceeds canal water level, creating a adverse/reverse hydraulic gradient and tidal drowning unless continuous 600 m³/s pumping is maintained against positive head. | Compare Gulf of Thailand tidal peaks (+2.00 m MSL in EIA 2569 p. 143) with natural ground elevation at km 40 (+2.60 m MSL). | Add a discussion of tidal lock and gravity discharge limitations under flat slopes in the lower reach. |
| **F9** | **inconsistent / profile drawing label** | `_profile_levels(134)` in `analysis/goal7_analysis.py:333` computes crest elevation as +4.000 m MSL at the outlet. | EIA 2569 Fig. 2.3.2-9 explicitly prints "สันคันหลังน้ำอัด **+3.000**", "ระดับน้ำระบายสูงสุดหน้า ปตร. **+1.498**", and "ระดับธรณี ปตร. **-5.504**". The formula omits the 1.0 m lower crest designation for the coastal backwater reach. | Inspect Fig. 2.3.2-9 at km 134 (`data/manual/EIA ทางระบายน้ำหลาก_สมบูรณ์ เล่ม 1-17907513091.jpg`). | Add an explicit condition for the tidal backwater reach (สันคันหลังน้ำอัด = +3.000 m MSL) in `_profile_levels()`. |
| **F10** | **goes beyond evidence / dismissal of ~6 m** | Reports repeatedly state that civil society's claim of a "~6 m embankment" has "no source in official documents" ("ไม่มีที่มาในเอกสารราชการ"). | Multiple official dimensions approximate 6 m: (1) Total height from canal bed to crest is $7.45 - (-1.05) = 8.50\text{ m}$; (2) Canal water depth is 6.0 m (EIA 2561 p. 135); (3) Crest above side-ditch bottom is $4.85 + 1.0 = 5.85\text{ m} \approx 6\text{ m}$; (4) At km 23.5, crest (+7.45) above low ground (+1.50) is 5.95 m $\approx 6\text{ m}$. Dismissing the claim as baseless ignores legitimate physical dimensions visible to local residents. | Calculate bed-to-crest and ditch-to-crest heights from Fig. 2.3.2-9 and Section 2.3.2.4. | Reframe: explain *where* the ~6 m perception likely originates (depth of excavation, height above ditch invert, or low-spot relief) rather than asserting it has "no source". |
| **F11** | **inconsistent / GIS metric mismatch** | `analysis/goal7/waterchart_overlay.json`: `cross_km = 16.82` km, but `km_intervals = [[41.4, 57.6]]` (span = 16.20 km). Academic report prints "16.8 กม. \| 47 % \| กม.41.4–57.6". | `goal7_waterchart_overlay.py:161` computes `cross_km` by intersecting the full line with the polygon, including fragments <50 m. Line 114 filters out intervals <50 m when creating `km_intervals`. The 0.62 km difference represents fragmented crossings. | Inspect lines 114 and 161 in `analysis/goal7_waterchart_overlay.py`. | State that 16.8 km includes short fringe segments, while the continuous main crossing corridor spans km 41.4–57.6 (16.2 km). |
| **F12** | **inconsistent / source date and citation** | `canonical.facts.eirr_2565` = "14.52 %" cited as "เอกสารกรมชลประทาน มี.ค. 2565 (ระยะที่ 1)". | In `data/manual/ป่าสัก-อ่าวไทย-ระยะที่1/`, the presentation mentioning EIRR 14.52% is from the 3rd sub-group meeting on **20–23 มี.ค. 2566** (file footer `04/04/66`). Furthermore, 14.52% is identical to the executive summary of EIA 2561 (p. 82). | Run text search across `data/manual/ป่าสัก-อ่าวไทย-ระยะที่1/*.pdf` for `14.52`. | Correct the date from March 2565 to March 2566, and note the identity with EIA 2561 executive summary. |
| **F13** | **inconsistent / missing file in hash manifest** | `data/32_goal7_chaophraya2/official_dwr/hashes.sha256` registers 2 files, including `รายงานการจัดทำผังน้ำลุ่มน้ำบางปะกง ฉบับสมบูรณ์.pdf` (161,640,156 bytes). | The file does not exist on disk in that folder (only `10-flood-ChaoPhraya.pdf` is present). | Run `Get-ChildItem data/32_goal7_chaophraya2/official_dwr/`. | Mark the file as pending download in `manifest.md` and comment out the hash until downloaded. |
| **F14** | **inconsistent / superseded plan text** | `docs/GOAL7_PLAN.md:288` (§19) retains obsolete text: "ส่วนล้นไซฟอนรอบ 10 ปี 77 ลบ.ม./วินาที = 33 ล้าน ลบ.ม./5 วัน = น้ำสูงเพิ่ม ~19–39 ซม." without an immediate forward pointer. | Section 21 (`:313`) explicitly cancels this calculation, but readers studying §19 can easily be misled. | Read `docs/GOAL7_PLAN.md` lines 288 and 313. | Add an explicit warning box at the top of §19: `> ⚠️ ข้อสรุปและตัวเลขในข้อนี้ถูกยกเลิกโดย §21`. |

---

## 3. Verified Correct (Spot-checked against primary sources)

The following items were checked against original PDFs and data sources and confirmed strictly correct:

1. **Longitudinal Profile Control Points (EIA 2569 Fig. 2.3.2-9 & EIA 2561 Fig. 2.3.2-5):**
   - *km 0.000 (Inlet):* Bed +1.750 m MSL, Normal WL +8.750 m MSL, Crest +10.250 m MSL. (100% match)
   - *km 22.900 (Gate 1):* Upstream Bed -0.550, Crest +7.950; Downstream Bed -1.050, Crest +7.450. (100% match)
   - *km 74.000 / 75.000 (Gate 2):* Bed -3.130 m MSL, Normal WL +3.860 m MSL, Crest +5.360 m MSL. (100% match)
   - *km 109.000 (Gate 3):* Normal WL +2.500 m MSL, Crest +4.000 m MSL. (100% match)
   - *km 134.000 (Outlet):* Design WL +1.498 m MSL, Bed -5.504 m MSL. (100% match)
   - *Connecting Canal (km 39.8–51.5):* Upstream Bed -1.000, Crest +3.200; Downstream Bed -1.592, Crest +2.808. (100% match)
2. **Structure Table 2.3.2-3 (99 Structures across 4 EIA versions):**
   - Parsed by `analysis/goal7_eia_structs.py`. Verified that across all 4 versions (2561, 2564, 2566, 2569), structure names, types, chainages, and dimensions are **100% identical (0 differences)**.
   - Spot-checked 20 individual rows against PDF text (Row 1 inlet, Row 24 Khlong 28 siphon, Row 25 Khlong 29 siphon, Row 38 Khlong Ban Na siphon, Row 44 Bang Pla Kot siphon, Row 53 Khlong 14 siphon, Row 75 Gate 2, Row 99 Outlet gate). All coordinates, spans, and discharges match PDF text exactly.
3. **Sub-Basin Hydrology Table 2.3.2-1:**
   - Spot-checked all 13 sub-basins (PK-AT-1 to PK-AT-13) in EIA 2569 Vol 1 (p. 149) and EIA 2561 (pp. 122–124). Catchment areas, 10-year 5-day flood peaks, and runoff yields match `canonical.basins_2569` to 3 decimal places (e.g. PK-AT-4 Mae Nam Nai: 206,224 rai, 28.046 m³/s, 12.115 MCM).
4. **EIA Versions History & Expropriation/Building Counts:**
   - *EIA 2561:* Land 14,609 rai, 1,625 buildings (Chapter 4, p. 613). B/C at 12% = 1.35 (Chapter 8, p. 784). Exec summary: EIRR 14.52%, B/C 1.22 (p. 82). Construction 5 years (p. 142).
   - *EIA 2564:* B/C at 12% = 1.12 (Chapter 8, pp. 827–828). Construction period 7–8 years.
   - *EIA 2566:* Land 16,288 rai, 1,378 buildings (Section 8, pp. 42, 248, 275). B/C at 12% = 0.99, EIRR 11.96% (Chapter 3, p. 121). ONEP letter dated 14 Feb 2019 / Nov 2021 / Mar 2024.
5. **GIS Floodway Overlay & Alignment Perturbation:**
   - Ran `_tmp_perturb.py` shifting the unofficial alignment laterally by ±100 m, ±200 m, ±300 m, and ±700 m. The crossing length in the Nakhon Nayok reach varies within 15.0–16.9 km (corridor share 44.2%–48.6%), confirming that the core finding ("crosses floodway for ~16.8 km = 47%") is hydraulically and spatially robust.
6. **Manning Hydraulic Capacity:**
   - Trapezoidal section: $b=51\text{ m}, y=7.0\text{ m}, z=3, n=0.016, S=1/25,000$.
   - $A = (51 + 3 \times 7) \times 7 = 504.0\text{ m}^2$.
   - $P = 51 + 2 \times 7 \times \sqrt{1 + 9} = 51 + 44.27 = 95.27\text{ m}$.
   - $R = 504.0 / 95.27 = 5.290\text{ m}$.
   - $V = \frac{1}{0.016} \times (5.290)^{2/3} \times (1/25000)^{1/2} = 62.5 \times 3.036 \times 0.006324 = 1.1999\text{ m/s}$.
   - $Q = 504.0 \times 1.200 = 604.8\text{ m}^3/\text{s} \approx 600\text{ m}^3/\text{s}$. (100% verified).
7. **Legal & Defamation Review:**
   - Full text search across `report/คลองเจ้าพระยา2_*.html` and `analysis/goal7/canonical.json`: zero private names, zero personal email addresses/phone numbers, zero allegations of corrupt intent. Critiques focus strictly on administrative procedure, environmental documentation gaps, and engineering trade-offs.

---

## 4. Could Not Verify (Missing data/files & FOI needs)

1. **`รายงานการจัดทำผังน้ำลุ่มน้ำบางปะกง ฉบับสมบูรณ์.pdf` (161.6 MB):**
   - Listed in `data/32_goal7_chaophraya2/official_dwr/hashes.sha256`, but missing from the disk. Only the Chao Phraya floodway volume is present. Must be obtained to verify Bang Pakong basin floodway layer boundaries.
2. **`wcmis/json/miswc22.json`:**
   - Cited in `manifest.md` and `docs/GOAL7_PLAN.md` §16.1 for verifying 22-basin boundary containment. Missing on disk.
3. **Official CAD/GIS Shapefile for the Canal Alignment:**
   - The analysis relies entirely on an unofficial user-digitized My Maps KML. The official engineering centerline shapefile must be requested from the Royal Irrigation Department (RID) or ONEP via Freedom of Information (FOI / พ.ร.บ. ข้อมูลข่าวสารฯ).
4. **Regulator Gate Operation Rules (คู่มือการปฏิบัติการเปิด-ปิดบานระบายน้ำ):**
   - None of the four 2569 volumes contain operation curves or water level triggers for the 4 cross-regulators (km 0, km 22.9, km 74.0, km 134.0). Cannot verify how gates will be managed during concurrent regional floods.
5. **Geotechnical Borehole Logs (km 20 to km 75):**
   - Soft Bangkok clay thickness and shear strength parameters ($c_u$, SPT-N) in the Nakhon Nayok reach are not provided in the EIA main report. FOI request required to verify embankment slope stability and long-term consolidation settlement.

---

## 5. Questions for the Authors (≤10)

1. **Hydraulic Backwater:** How can outlet pumping at km 134 lower the water profile 94 km upstream at km 40 by 1.5–3.0 m in a subcritical canal without deepening the canal bed over the entire intervening reach?
2. **Geotechnical Feasibility:** If the canal bed at km 134 is lowered from -5.5 m to -8.5 m MSL in coastal Bangkok marine clay, how will basal heave, circular slip failures, and saline water intrusion into agricultural aquifers be mitigated?
3. **Siphon Capacity Double-Counting:** Siphons at Khlong 28, 29, and Ban Na are designed to pass existing river flows. During a regional storm, when those rivers run full, where will the 40–128 m³/s of local overland sheetflow go?
4. **Tidal Lock in Flat Slopes:** If Option 1 widens the canal to lower the water surface to natural ground elevation (+2.0 m MSL at km 40), how will the canal discharge into the Gulf of Thailand during spring high tides (+2.0 to +2.5 m MSL) without massive pumping?
5. **Breach Volume Clarification:** Why present an instantaneous breach peak of 1,000–10,000 m³/s (which alarms the public) without clarifying that the above-ground storage in that reach is only 11.1 MCM and would empty within 1–3 hours?
6. **Lumped Volume Discrepancy:** Why does §3.11 c use 14.0 MCM (based on an assumed uniform 3.3 m depth) when trapezoidal integration of your own digitized profile yields 11.1 MCM?
7. **Canonical Literal Enforcement:** Why does Goal 7 lack the automated `test_builder_source_has_no_metric_literals` test that protects Goal 6, allowing stale literals like "2.5–4.8 ม." to persist in `goal7_build_academic.py:71`?
8. **Dismissal of ~6 m Embankment:** Why dismiss the civil society claim of a "~6 m embankment" as having "no source," when canal depth is 6.0 m, bed-to-crest is 8.5 m, and crest above side ditch invert is 5.85 m?
9. **Connecting Canal Flow Direction:** Does the Mae Nam Nai connecting canal (km 39.8–51.5) operate under gravity at all river stages, or does high stage in Bang Pla Kot cause backflow into Mae Nam Nai?
10. **Unofficial Alignment Sensitivity:** Given that the alignment is unofficial and markers deviate up to 3.6 km from the actual centerline, why are floodway crossing lengths presented as single exact numbers (16.8 km / 47%) rather than sensitivity ranges (15–17 km / 44–49%)?
