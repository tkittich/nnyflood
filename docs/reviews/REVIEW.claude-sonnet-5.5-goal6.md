# REVIEW — claude-sonnet-5.5 — Goal 6 (reports 3 & 4, drafts)

Reviewer: Claude Sonnet 5.5 · 12 Oct 2026 · repo state = working tree at review time (`main`, uncommitted changes present)

## Top line

**FIX-FIRST.** The data pipeline and the integrity discipline are sound (pytest green, integrity MISMATCH 0, the 67/199 → 32/99 de-duplication is already in the TLDR). But five headline statements in reports 3/4 are contradicted by the project's own JSON files or are not supported by any data in the repo: the pre-release scenario, the "peak flood area" ranking, the 2569 dam-storage column, the 2554-vs-2569 "operations are comparable" conclusion, and the "forecasts are accurate / gates all closed / pumping 100 %" claims. None needs new data to fix — they need to be re-worded, re-labelled or bounded.

> **Note on the request text itself.** Several numbers in the review request are *retired* in this repo's own ledger (`analysis/goal6/canonical.json → retired`): "1.7–7.4 m" (unit bug; current = 0.16–2.22 m), "Bangkok 1,200 km²" (current = 1,104), "+48 h models collapse equally in every basin" (retired as M9), "18 SUSPECT stations" (current = 19). `analysis/goal6/prerelease_scenario.json` (the deprecated bug output) is still sitting beside the live files, which is probably how it got quoted. Also `analysis/goal6/l3_model.json` does not exist — the files are per basin (`analysis/goal6/<basin>/l3_model.json`). I reviewed the *current* values.

---

## Findings

### HIGH

**H1 — The pre-release scenario contradicts the report's own 3 % result; the "1–2 m" headline has no physical basis.**
- Evidence: `analysis/goal6_c2_attribution.py` builds `q_new = q_peak − (extra − actual_avg)` (lines ~92–100), i.e. it subtracts the *whole extra daily release* (15–75 mcm/day) from the **1 Oct** C.2 flow. But the same file's chain shows the dams' release on 1 Oct is only **7.01 mcm/day (3.1 % of 225.5)** — I re-derived it from `data/22_goal6_network/raw/spike_ping_cp/c2_sources_volumes.json` (`released_total[1 Oct]=7.01`).
- Consequence: even *zero* dam release on 1 Oct could lower C.2 by `0.034241 × 7.01 = 0.24 m` using the report's own level–volume equation. The reported drops (0.85 / 1.53 / 2.22 m for 60/80/100 mcm/day) are 3.5–9× above that ceiling. Water released 11–15 Sep is not "subtracted" from the 1 Oct flow; the only mechanism by which pre-release helps the peak is that the dam then releases less at the peak, bounded by 7 mcm/day.
- `within_calib: true / usable: true` only tests that `q_new` is inside 49.9–225.5, not that the mechanism is valid. The Q&A sentence "ทุกกรณียังอยู่ในช่วงที่ข้อมูลจริงสอบเทียบไว้" gives that check a meaning it does not have; `builder:505` ("ลดระดับพีคที่ C.2 ได้ราว 2 ม.") and `:518` ("ราว 1–2 ม. ที่ C.2") then carry it into the policy conclusion.
- The R² = 0.996 is a level-vs-discharge rating fit on 39 autocorrelated daily points (it will always be high); it says nothing about the counterfactual.
- Fix: either (a) cap the scenario at `min(extra−actual, release_at_peak)` (→ ≤ 0.24 m), or (b) delete the quantitative scenario and keep only "bounded by the 3 % share". Remove "ราว 1–2 ม." from both Q&A and the policy bullet. Also move `prerelease_scenario.json` + `goal6_prerelease_scenario.py` to `analysis/archive/`.

**H2 — "Peak flood area per basin" is a single-frame, coverage-unnormalised lower bound; the cross-basin ranking (2,264 / 1,104 / 1,282 / 521 / 160 / 73) is not like-for-like, and "peak = 1 Oct" is an artefact of the satellite schedule.**
- Evidence (`analysis/goal6/s1_stage2_*.md`, column "ครอบกริด"): the max frame covers only **18 %** of the Ping grid (2,263.6 km²), **13 %** of Tha Chin (160.4), 53 % of Pasak (521.0), 42 % of Bang Pakong (1,281.6), 43 % of Mae Klong (73.0), 100 % of lower Chao Phraya (1,320.8). Pixels outside the footprint are NaN → comparisons give `False` → counted as "no water" (`goal6_s1_stage2_water.py:83–90`). "% ที่ราบ" divides by the *whole-basin* lowland (2,263.6 / 5.7 % ≈ 39,700 km²), so Ping's "5.7 %" is understated ~5×.
- Adjacent frames of the same pass are not merged: Ping 1 Oct 23:07:50 = 393.0 km² (14 %) and 23:08:15 = 2,263.6 km² (18 %) → ≥ 2,657 km² if non-overlapping; the report uses the larger one only.
- Date label: Mae Klong 73.0 km² is the **2 Oct 11:36** frame (`1SDV_20261002T113615`), but TLDR/Q&A/map captions say "1 ต.ค.".
- "Peak": the latest S1 scene for *every* basin is 1–2 Oct; gauge peaks in the same report are later (S.26 7 Oct, C.35 6 Oct, C.36 4 Oct, C.3/C.37 3 Oct). "1 ต.ค. จุดสูงสุด" is "last acquisition available", not the flood peak.
- "ล่างขอบ" (lower bound) for Bangkok (`builder:282, :350`): the rule has precision 0.67–0.78 (commission error 22–33 %) and recall 0.64–0.79, so the net sign of the bias is unknown; only the permanent-water subtraction is directionally conservative.
- Fix: (i) report per-basin "detected area in frames that cover X % of the basin", never one number across basins; (ii) union frames of the same pass; (iii) caption "1–2 ต.ค. (ฉากสุดท้ายที่มี)"; (iv) drop "ล่างขอบ" or justify it; (v) fix the Mae Klong date.

**H3 — The "2569 เก็บสูงสุด" column in the 24-dam table (reports 3 §3 and 4 §2) is the Jan–Oct calendar-year maximum for 12 of 24 dams, not the Sep–Oct event.**
- Evidence: `analysis/goal6/dam_history_all.json` → 2026 row has `n_days: 282` (1 Jan–9 Oct) and `max_storage` over all 282 days. Compared with `sep_oct_max_storage` in `goal6_screen_2026_summary.json`: Bhumibol **12,936 vs 9,291 (+39 %)**, Ubolratana 2,102 vs 1,424 (+48 %), Lam Pao 1,747 vs 1,229 (+42 %), Kra Siao 243 vs 155 (+57 %), Mae Kuang 258 vs 186 (+38 %), Bang Lang +29 %, Lam Chae +30 %, Nam Un +26 %, Sirikit +14 %, plus 3 smaller. Almost all are January carry-over from the 2568 season (`2025: days_over_urc=90`, `2026: days_over_urc=13` for Bhumibol).
- Consequences: "ภูมิพล 2554 100 % vs 2569 96 %" compares an event peak with a carry-over; the table simultaneously shows 0 days over URC for 2569 (Sep–Oct only) but `days_over_urc` = 13/198/71 for Bhumibol/Mae Ngat/Pasak for the same year; and Mae Ngat's "เกินเต็มหน้าต่าง 39 วัน" is not a late-September phenomenon (198 of 282 days over URC in 2026, 228 days in 2554 — see H4).
- Fix: use `sep_oct_max_storage` (event window) for 2569 and the same window for 2554, or label the column "สูงสุดในปีปฏิทิน (รวมน้ำยกยอดจากปีก่อน)". Compute "% of normal storage" from the same window as the days-over-URC columns.

**H4 — "Dam operation can be compared across years, rainfall events cannot" (report 4) is not supported, and report 4 §3 contradicts §4.**
- Days-over-URC is an *outcome* of inflow × operation; without inflow/release series for 2011 the two cannot be separated. The report itself says (§3) "2554 = ฝนมากเกินแผนทุกจุดพร้อมกัน" and (§4) lower basins' rain "ปกติ" (median rank 30–39 of 46) while ลำตะคอง/ลำแชะ (Mun basin, median rank 26) were over URC 219/122 days. Both cannot be true.
- The rain index is a 7/30-day *annual maximum at 0.5° gauge-location cells* (`goal6_rain_rarity_2554.py`). 2011 was a season-total / antecedent-moisture year; a 7-day maximum is the wrong statistic to say its rain was "ordinary" in a basin. No Jul–Oct total or Aug–Sep total was computed. Conclusion "event comparison is not valid" may be right, but "dam-operation comparison is valid" does not follow.
- "Irrigation dams exceeding the guide curve is normal system behaviour (ป่าสัก 20/22 ปี)": exceeding the *upper* rule curve in 20 of 22 years is evidence that the 2020-dated month-day template is not the operative constraint for that dam (or the curve was revised), not that the exceedance is "normal". Mae Ngat is above the curve 198 of 282 days in 2026 and 228 days in 2554 — same signature. The single cross-check (Khun Dan, 5,025 rows, diff 0.0) is for one dam in one year and cannot validate the 2011 curve of another dam.
- Report 3 states the cause as fact ("เพราะระบบของเขาผลิตไฟฟ้าได้ทุกระดับน้ำ จึงเผื่อพื้นที่ว่างไว้", `builder:335`), where report 4 softens the same sentence to "การตีความที่เป็นไปได้". No source for intent exists in the repo.
- Fix: replace "operations comparable" with "outcomes (days over the 2020 curve) are comparable only as descriptive counts; operation and inflow are confounded"; add a season-total rain column (Jul–Oct sum rank) for 2011/2026; mark every "because" about operator intent as interpretation.

**H5 — Forecast headline ("พยากรณ์ระยะสั้นทำได้จริง", "พิสูจน์ว่า ... แม่นยำสูง") is not what `l3_model.json` shows.**
Re-read all six `analysis/goal6/<basin>/l3_model.json`:

| basin | +6 h persistence / linear / GBDT (RMSE cm) | +24 h | +48 h |
|---|---|---|---|
| pasak S.26 | **20.8** / 44.0 / 30.9 | **68.6** / 83.2 / 74.6 | 125.9 / 126.3 / 125.9 |
| maeklong K.3A | **10.2** / 10.3 / 19.7 | 20.1 / **19.3** / 25.6 | 31.5 / **26.5** / 30.4 |
| thachin T.1 | **13.0** / 15.9 / 38.9 | 11.7 / **10.6** / 26.6 | 20.6 / **19.4** / 34.1 |
| bp_prach Kgt.3 | 10.0 / **6.3** / 17.5 | 37.8 / 32.8 / **32.4** | 77.9 / **68.7** / 71.1 |
| ping_cp C.2 | 10.5 / **4.4** / 6.4 | 39.0 / **24.9** / 31.3 | 66.8 / 61.0 / **60.6** |
| bkk_lower C.13 | 17.7 / **12.4** / 23.6 | 57.0 / **37.4** / 53.3 | 96.6 / **66.0** / 69.7 |

- "No change" (persistence) is the best or within 10 % of the best in 3 of 6 basins at +6 h and in 3–4 of 6 at +24 h. The TLDR's "แม่นสุด 4–21 ซม." mixes models with the persistence baseline (21 = persistence in Pasak) and is best-of-3 *chosen on the test set* (winner's curse). There is no skill score against persistence anywhere in report 3.
- "+48 h collapse equally" (the request's wording) is false in the data: Mae Klong/Tha Chin 19–26 cm vs Pasak 126 cm; Bang Pakong *event-window* RMSE 26.1 (linear) vs 59.8 (persistence) vs 76.3 (GBDT). The report text already says "โตตามลุ่ม" in TLDR but each basin's "สรุป" line still says "คลาดเคลื่อนทุกโมเดล" (`builder`, six times).
- Design limits that make the tables optimistic/fragile: one test event of 157–360 hours (≈ 7–15 days, highly autocorrelated, effective n of a handful); 7 training seasons; GBDT cannot extrapolate above the training maximum (GBDT is 1.3–3.0× worse than persistence at +6 h in 4 of 6 basins); training rows 18–19 Sep have +24/+48 h labels that fall inside the test window (`goal6_l3_model.py:~152`: `tr = ~te` on feature time only).
- Policy text `builder:578` "พิสูจน์ว่า ... ความแม่นยำสูง" for 6–24 h must go: +24 h best-model RMSE is 25–69 cm in 4 of 6 basins (C.2, Kgt.3, C.13, S.26).
- Fix: report skill vs persistence (1 − RMSE/RMSE_pers), keep persistence as a named baseline, drop "พิสูจน์", purge training labels whose horizon crosses the test start, state n_test as "≈ 1 event".

**H6 — Tide/gate claims in the Q&A are not supported by any data in the repo, and contradict limitation (2).**
- `builder:372–373, :387`: "ประตูระบายน้ำปากอ่าวและแนวคันกั้นน้ำทะเลทั้ง 38 แห่ง จำเป็นต้องปิดบาน ... พึ่งพาเครื่องสูบน้ำ 100 %", "น้ำไม่สามารถไหลลงอ่าวไทยด้วยแรงโน้มถ่วงได้เลยตลอด 72 ชั่วโมง". Limitation (2) of the same report says gate/pump logs are not in any API. Data support only: estuary stage 0.31–0.49 m (Krung Thep Bridge) and ≥ 1.15 m (Sam Sen) at low water on 26–28 Sep (`downstream_tide_summary.json`).
- Low-water level at the river mouth being +0.3–0.5 m instead of −0.8 to −1.2 m is *also* what a 226 mcm/day (≈ 2,600 m³/s) upstream discharge produces without any tidal blocking; the stated causal direction (tide → blocking) is not separated from discharge → stage. A gravity-flow statement needs the gradient between an upstream and a downstream gauge (C.22A/C.12 vs CPY015), which is not shown.
- "38" comes from `canonical.json → estuary_tide.coastal_gates_count`; I could not trace its source file in the repo.
- "14-year statistics" (2012–2025): `historical_estuary_summary.json` shows very uneven coverage (e.g. CPY015 2012 = 5,391 points, 2018 = 12,692, vs ≈ 52,000 in a full year; MKG006 2012 = 0; GLF003 2021 = 1,229) — not disclosed, and the "1.80–2.25 m spring range" is computed from these.
- Fix: say "ระดับน้ำต่ำสุดรายวันที่ปากแม่น้ำสูงกว่าปกติ 0.8–1.0 ม. ซึ่งสอดคล้องกับ ... ; สถานะบาน/เครื่องสูบไม่มีข้อมูล" and delete "100 %", "ทั้ง 38 แห่ง ... ปิดบาน" unless a source is added. Disclose coverage per year.

### MED

**M1 — Satellite rule: "ตรงกัน 72.7 %" is an in-sample F1, mis-described, and transferred unvalidated to 5 other basins.**
- `analysis/calibrate_s1_thresholds.py` picks thresholds from a 420-point grid by maximising F1 against GISTDA on **one scene (2 Oct, Nakhon Nayok)**; the same scene is then the "validation". On the out-of-sample 27 Sep peak scene the same rule scores F1 = **0.645** (`analysis/gistda_georef_findings.md` §7), and the post-8 Oct recomputation of the 2 Oct scene is 0.700 (P 0.778 / R 0.636), vs 0.727 (P 0.672 / R 0.792) in the header of `s1_change_detect.py`. Report 3 repeats "ตรงกัน 72.7 %" in every basin section; "F1" is not "% agreement", and the GISTDA reference is a composite of 28 Sep–2 Oct, not a pass-matched ground truth.
- Each basin section then says "ยังไม่ได้เทียบ GISTDA (ทำต่อใน v0.3)" — correct, but then the header sentence in the same section implies validation.
- Fragility ranking for basin scale (my assessment from the rule definition): (1) **tidal flats / aquaculture / canal-dense lowland** in the lower Chao Phraya, Tha Chin and Mae Klong grids — Sep 19 vs 1 Oct acquisitions are at different tidal states, ΔVH ≤ −0.5 dB is within radiometric stability, only VH ≤ −20 dB is selective; (2) **wet/harvest-bare rice fields** (smooth fallow also gives VH ≤ −20 dB); (3) **urban double-bounce** biases Bangkok low (flooded buildings brighten); (4) shadow is largely removed by the Δ criteria and same-track pairing — the least fragile. None of (1)–(3) is quantified for a non-Nakhon-Nayok basin.
- Fix: report F1 as "F1 = 0.73 ในสนามเทียบ (ฉากเดียวกับที่ใช้ตั้งค่า); 0.65 ในฉากอื่น", remove "ตรงกัน %", add a tide-state column per scene for the three coastal basins.

**M2 — "25 gauges exceeded critical level" is mostly an artefact; and three SUSPECT gauges carry usable evidence.**
- Re-ran the classifier logic on `goal6_screen_2026_summary.json`: of 25 "over critical" gauges, **18 are over critical for 100 % of the window's hours** (n = hours with data), 1 is classed on the "partial" rule only (B.10: 13 % of hours over crit but max < min_bank), and 6 are genuine exceedances. TLDR/§1 still say "พบว่า 25 จุด มีระดับน้ำที่เกินระดับวิกฤต ... 17 จุดมีระดับสูงสุดช่วง 23 ก.ย.–9 ต.ค." — 12 of the 17 are SUSPECT stations, and M.6A's "peak" is 9 Oct 23:00, the last hour of the window (censored).
- Misclassification risk: K.10 (max 47.15 m vs own lowest bank 40.7 → +6.45 m), K.37 (+0.42), P.17 (+0.14) are SUSPECT only because their `crit` is wrong, but `meta_min_bank` and the series are on the same scale — a datum-consistent "over bank" criterion exists for them and for every gauge with `crit = null`. For B.10 the "max < bank ⇒ datum mismatch" rule assumes a warning/critical level cannot be below bank; for Kgt.1 and Z.57 `crit` equals `min_bank` exactly, so the rule's premise is untested for stations whose crit is below bank.
- Fix: add a second, datum-independent screen (series vs `meta_min_bank` and vs the gauge's own 2020–2025 annual-maximum distribution) and report the count of gauges exceeding their own historical maximum; state "6 gauges with a usable threshold" in the TLDR instead of "25".

**M3 — Pre-registration claim ("กำหนดไว้ก่อนดูผล") is not demonstrable and the window was changed after results.**
- `git log`: `analysis/goal6/config.json` first appears 10 Oct 09:35 in the same commit (`8f9d340`) as the screening summary/findings, and again 13:29 with L2/L3 results. Basin choice follows the screen's own "ข้อเสนอลุ่มรอบแรก". `goal6_l3_model.py` carries the comment that the grid originally ended 4 Oct and was extended to 9 Oct because the S.26 peak (7 Oct) fell outside — a post-hoc change that is logged but contradicts "fixed window, changed only with reason before results". Report 3 §2 should say "ลุ่มถูกเลือกหลังคัดกรองระดับชาติ; หน้าต่างถูกขยายหนึ่งครั้งหลังเห็นผล (เหตุผล: …)".
- Fixed window Jul 1–Oct 9 for all basins (A4): fair for Pasak because S.3/S.33 peaks (20–22 Aug) are inside it and the report says so, but "ระลอกปลาย ก.ย." as an event label then covers a basin whose river peak was not in the wave; Pasak's Q&A should not be pooled into "wave" statistics.

**M4 — `rain_rarity_2554.md/.json` mislabels ranks as "/199" (they are ranks among 46 years), and three different "Nakhon Sawan 7-day rain" values coexist.**
- `analysis/goal6/rain_rarity_2554.md` prints "1/199 … 33/199"; `max(rank54)=45`, `max(rank26)=46` — they are year ranks (46 years); the MD footer even says "อันดับกลาง ... จาก 46 ปี". Report 4 prints the right basin medians, so only the MD (and any reader of it) is misled.
- Nakhon Sawan/C.2 7-day rain: **248 mm** (`builder:~70`, hard-wired window 23 Sep–1 Oct on `power_2795.json` — a window chosen after seeing the event, and a builder-side computation), **251.6 mm** (§4.5 table, Sep 1–Oct 9 on `power_ping_cp_นครสวรรค์_C.2.json`), **165.2 mm** (`rain_obs_2026.json`, older cache). Rain on the same point should come from one canonical field.
- 2026's window ends 9 Oct (POWER cache last date 6 Oct for the Ping points; report says 7 Oct) while other years run to 31 Oct — conservative for the rank, correctly disclosed as (3.1), but "ปีอื่นนับถึง 31 ต.ค." means 2026's 30-day value is a 28-day-effective lower bound; the TLDR 30-day figure (66/199) should carry that note.

**M5 — Cross-file stale numbers that the test-suite does not catch.**
- `HANDOFF.md:83` and `docs/GOAL6_PLAN.md:353` still carry the pre-H2 L3 numbers (C.2 5.3 · Bang Pakong 7.9 · Mae Klong 8.8 · Tha Chin 14.1 · Bangkok 14.2 · Pasak 24.6 @+6; +48 Tha Chin 22.8 · Mae Klong 28.1 · Pasak 148.7 · Bangkok 76.4) vs current JSON/canonical/report (4.4 · 6.3 · 10.2 · 13.0 · 12.4 · 20.8; 19.4 · 26.5 · 125.9 · 66.0). AGENTS.md rule (5) says status documents must carry current values.
- `docs/reviews/GOAL6_REVIEW_BRIEF.md` row "กฟผ. เดินเขื่อนใต้ URC (2554 และ 2569 = 0 วันเกิน)" was retired (H1 in the ledger) and contradicts the table in the same brief ("สิริกิติ์ 2554 เกิน URC 164 วัน"); "45/45 tests" vs the progress line I saw (46 dots, all passed); "18 SUSPECT" vs canonical 19.
- `builder:91`: "4 จาก 6 ลุ่มเกิดจากฝนเป็นหลัก" is a literal in the builder (AGENTS rule 6(2)) and has no JSON field or computation behind it; no formal attribution exists for 3 of the 4 basins (only C.2 has a chain table).

**M6 — Defamation framing (AGENTS.md / LEGAL_REVIEW) in reports 3 and 4.**
- Headings "ถาม: เขื่อนผิดหรือฝนผิด?" and "ถาม: เขื่อนไหนจัดการดีที่สุด?" are exactly the "ใครผิด / ใครดีสุด" framing the rule asks to avoid; they name agency groups (กฟผ. vs ชลประทานย่อ) in a ranked comparison.
- Unsourced motive attribution: `builder:335` ("เพราะระบบของเขาผลิตไฟฟ้าได้ทุกระดับน้ำ จึงเผื่อพื้นที่ว่างไว้"), `:529` ("เหตุผลจริง: ... พฤติกรรมมาตรฐาน"), report 4 ("เป็นเรื่องปกติของระบบ ... เพราะต้องเก็บไว้ใช้ชลประทาน").
- Flat "ใช่" at `builder:474` ("เขื่อนปล่อยน้ำเยอะผิดปกติใช่ไหม → ตอบ: ใช่") and the Q&A "การเก็บน้ำของเขื่อนบางแห่งทำให้พื้นที่รองรับน้ำฝนน้อยลงกว่าที่ควรจะเป็น" (no dam named, no quantity) are evaluative claims about agencies without a cited source in the sentence. The statement "เขื่อนเพิ่มการปล่อย ... ทำให้ระดับ C.2 โตจาก 50 เป็น 90" attributes a 40 mcm/day rise to an 8 mcm/day release increase.
- Positive: "ปฏิบัติหน้าที่ตามภารกิจของตนเองอย่างเต็มที่" and the EGAT/RID caveat paragraph are present; PDPA — I found no person names, handles or contact details in either report (only place names such as เขานางบวช).
- Fix: re-title as "ระบบเก็บน้ำของเขื่อนกลุ่มใดมีพื้นที่ว่างเหลือเมื่อฝนมา?"; mark every "เพราะ" about operations as "ข้อมูลไม่เพียงพอที่จะระบุเหตุผล"; compute the C.2 growth attribution (≈ 20 % at most) instead of "ทำให้".

### LOW

**L1 — C.2 correlation is trend-driven.** `corr(release, C.2) = −0.917` reproduces (n = 39 daily points), but correlation of first differences is **−0.45**; lag-2 inflow→C.2 is 0.44 (lag 0–5: 0.19–0.44). The report already flags it as supporting evidence; the sentence "ถ้าน้ำที่สูงขึ้นมาจากการปล่อยเขื่อน ระดับต้องลดตาม" in Q&A should be dropped (it is a non sequitur for a stock that is rising).

**L2 — Weibull return period.** `weibull_rp_yr = (n+1)/rank` with n = 46 caps at 47 yr; rank-1 stations show "~47 ปี" — it is a *lower bound on the plotting position*, not a return period (report 3 does not print it; `rain_rarity_*.md` does). Under stationarity the expected number of top-3 cells is 99 × 3/46 ≈ 6.5; observed 32 (≈ 5×). Spatial dependence widens the null variance, but not by that factor. **De-duplicated figure (my computation)**: grouping the 199 stations by identical (7-day value, end date, 30-day value) gives **99 cells; 32 cells in the top 3** — identical to `canonical.json → rain_national` and the TLDR. A plain 0.5° floor grid gives 105 cells / 33 with a top-3 gauge (approximation; POWER MERRA-2 cells are 0.5° × 0.625°).

**L3 — Report 4 is thin relative to what report 3 promises.** Report 3 defers the "pooled flow below Ayutthaya (C.22A)" and cross-year analysis to "รายงานที่ 4"; report 4 contains one table, one rain section, and ends with "⏳ รอข้อมูล — ... (รอผู้ใช้ยืนยันขอบเขต)". The self-contained rule is respected, but the promise is not kept.

**L4 — Readability / language.** Garbled or misspelt: "คอควด" (→ คอขวด, builder:397–398), "ล้วงหน้า" (:510), "ช่วงฝนฝนตกหนัก" (:652), "ทิศเอียง สวน ปี 2569" (:640), limitation numbering jumps "(3) … (3.1) … ใช้ได้เชิงคุณภาพเท่านั้น (5)" with (4) missing, "(ต.-ง.)". Jargon the checker cannot see: "R² 0.996", "POWER", "DEM", "ค่าเดิมคงที่/แบบจำลองต้นไม้" (acceptable but unexplained), "น้ำเทิน", "ช่องกริดอิสระ". Reports 1–2 are referred to as "ต้องดู" in two places (TLDR (2) "(รายงานที่ 4)", Q&A "รายงานที่ 4 บทฝนสองปี").

**L5 — TLDR coverage.** The 2-minute summary omits the C.2 chain finding (3 % at peak), the tide coincidence, and the S2 non-validation, all of which appear as headline Q&A answers.

**L6 — Duration maps.** `goal6_duration_maps.py` uses absolute VH ≤ −20 (not the Δ rule), per-pixel scene counts of 2–N (different per pixel), scenes 1–3 days apart — HANDOFF correctly says "ยังไม่ฝังในร่าง 3". Not in the draft, so no finding; if embedded, the caption must say "สัดส่วนฉากที่เห็นน้ำ ไม่ใช่จำนวนวัน" and show per-pixel scene count.

---

## What I checked and found OK

- `python -m pytest tests/ -q` → all tests pass (46 progress dots, 100 %); `python analysis/verify_data_integrity.py --quick` → OK 2,770, DELETED 3 (the three S2 zips under `manual-deleted/`, all listed in manifest), SKIPPED 354, **MISMATCH 0**.
- 67/199 stations top-3 for 7-day rain reproduces from `rain_rarity_national.json`; 66 for 30-day; de-duplication to 32/99 reproduces and is already in the TLDR, Q&A and limitation (3).
- `canonical.json → l3_best` matches the six `l3_model.json` files; per-basin L3 tables in the HTML match the JSON (spot-checked C.2, K.3A, S.26, T.1).
- L3 train/test split is time-ordered (no random shuffle); rain windows end "yesterday" (`rain_window.windows_for_grid`), so the H6 leak is genuinely fixed.
- C.2 chain numbers reproduce: release 7.01 of 225.5 mcm/day = 3.1 %; Bhumibol release 0 on 30 Sep; P.17 148.9 + N.67 95.2 vs C.2 225.5 (routing attenuation, plausible).
- Bangkok subtraction arithmetic: 1,320.8 − 216.8 = 1,104.0 ✓; permanent-water mask 1,435.1 km² reported.
- Report 4 table days-over-URC counts match `dam_history_all.json` (Sep–Oct count: 2569 = 9 dams; 2554 Sep–Oct = 14).
- Khun Dan 224.34 @ 27 Sep and release 31.66 reproduce from the screen JSON.
- PDPA: no personal names, handles, phone numbers in reports 3/4.
- Banned-term list: no occurrences of the listed words in either rendered text (my scan; the repo's own checker is authoritative).

## Limitations of this review

- I did **not** re-run the S1 pipeline (`goal6_s1_stage2_water.py`), `goal6_screen_basins.py`, or `goal6_l3_model.py` (needs the derived rasters / API caches); S1 and L3 statements rely on the committed `.md`/`.json` outputs and on reading the scripts. The 0.0 km² frames adjacent to non-zero frames (e.g. Tha Chin 23:08:40 = 0.0 at 87 % coverage next to 160.4 at 13 %) may be genuine; I could not rule out an alignment/no-data effect and flag it as "to check".
- I did not independently verify F1 against GISTDA; I used the repo's own documents (0.727 / 0.700 / 0.645).
- POWER PRECTOTCORR homogeneity (reanalysis vs near-real-time stream for the last months) was not tested; it could affect 2026's rank relative to 1981–2025.
- I could not trace the "38 coastal gates" figure or the Nakhon Sawan "248 mm" to an upstream observation file beyond `power_2795.json`.
- I read Thai text, but only the rendered text extracted from the two HTML drafts (images, maps and CSS contrast were not inspected). Reports 1–2 were not reviewed. WCAG colour checks and chart label legibility were not covered.
- The brief's pre-registration commit order was inferred from `git log` timestamps, which do not prove file contents at that moment.


---
---

# Addendum — other issues, suggestions, and whole-project review (12 Oct 2026)

Scope: everything outside the Goal-6 numbers reviewed above — repository, privacy, tests, process, reports 1–2, documentation, reproducibility. Same rule as before: each item cites what I actually ran or read. A separate **P-series** is used so the findings above keep their IDs.

## Whole-project scorecard

| Area | Rating | One-line reason |
|---|---|---|
| Data provenance & forensics | **Strong** | per-folder `manifest.md`, 3,127 recorded SHA-256, `verify_data_integrity.py` → OK 2,770 / MISMATCH 0; credentials file is gitignored (`git check-ignore -v` → `.gitignore:78`); a regex scan of tracked text files found no keys/tokens |
| Process discipline | **Strong, with one blind spot** | pre-registration language, retired-number ledger, review-by-running, "done" criteria. Blind spot: the rules police *consistency*, not *validity* (P5/P6) |
| Analysis validity (Goal 6) | **Mixed** | rain counting, dams-vs-URC counting and screening are sound; scenario, area ranking, 2569 storage column, forecast skill and tide/gate claims are not (H1–H6) |
| Reports 1–2 (Nakhon Nayok) | **Good, not re-audited** | pass tests and 5 reviews; language-rule and README-framing issues below (P7) |
| Legal / privacy | **Needs action now** | P1 is the single most urgent item in the whole project |
| Reproducibility | **Good locally, limited externally** | pinned `requirements.txt`, paths from `__file__`, `goal6_build_all.py`; but the 17 GB Sentinel and DEM inputs are disk-only, so a third party can verify numbers from JSON, not regenerate them |
| Maintainability | **Fair** | 14.9 k lines Python, 1,759 tracked files / 119 MB, flat `analysis/` of ~200 mixed files (P8) |

## P-series findings

### P1 — HIGH (privacy / legal): tracked raw social-media files contain private individuals' names and phone numbers, contradicting `docs/LEGAL_REVIEW.md`

- Evidence (tracked in git; `main` is in sync with `origin/main` — `git log origin/main..HEAD` = 0 commits):
  - `data/06_citizen_social/raw/tinyNakhonNayok_feed.json` — commenter display names of private individuals (not reproduced here), four personal mobile numbers placed next to requests for help at a specific household area (e.g. ม.4 ต.ศรีจุฬา). I do not reproduce the numbers here.
  - `data/01_rid_khun_dan/fb_page/raw/feed_loggedin_posts.json` and `instagram/raw/posts_data.json` — names of named civil servants plus a few `facebook.com` profile links (public-office holders, lower risk, but unnecessary).
  - Derived from the same source family: `analysis/flood_feed_evidence_posts.csv`, `analysis/flood_album_captions.csv`, `analysis/album_geotag_results.csv`, `analysis/villages_warning_zones.csv` (I did not open every row).
  - 10 PNG screenshots of Facebook pages under `data/01_rid_khun_dan/fb_page/screenshots/`, `data/10_mitrearth_gis/screenshots/`, `data/11_external_forecasters/tee_page/screenshots/` — I did **not** inspect image content for commenter names/avatars.
- Contradiction: `docs/LEGAL_REVIEW.md` (rows at lines ~40 and ~55) states the data has no personal names or profiles ("ไม่มีชื่อบุคคลที่สามในไฟล์ที่ track"). That is false for the files above. The AGENTS.md PDPA rule (no personal data of natural persons in published data) also applies — a public repo is publication.
- Why it outranks the analysis findings: phone numbers plus the home area of people asking for help are the most harmful class of leak; later deletion does not remove forks and caches; the project's own defence (research basis + identity masking) needs masking that is not there.
- Proposed fix (author's decision — AGENTS.md forbids history rewriting without discussion, so I propose rather than act): (1) `git rm` the raw feed files and screenshots from the tree now; keep SHA-256 + manifest, as is already done for 17 GB of imagery; (2) replace the analysis CSVs with per-tambon counts, which is all the analysis uses ("ต.องครักษ์ 6 โพสต์"); (3) decide on a history rewrite (`git filter-repo` + force-push + request GitHub to purge cached views) — for phone numbers it is the only complete remedy; (4) correct LEGAL_REVIEW.md; (5) add a pytest check that fails on `0[689]\d{8}` or `facebook.com/profile` in tracked text files outside an allow-list.
- Separately for counsel: `data/06_citizen_social/manifest.md` records collection by a user logged into Facebook scrolling the page — a platform-terms and lawful-basis question, distinct from masking.

### P2 — HIGH: drafts of reports 3 and 4 are already linked from the public landing page

- `index.html` lines 39–46 link `report/ระลอกปลายกย2569.html` and `report/ชุดเทียบมาตรฐาน2554.html` as "(ร่าง)"; commit `d81ec83` is on `origin/main`; README links `tkittich.github.io/nnyflood`. If Pages is enabled, H1–H6 are not pre-publication.
- The "(ร่าง)" label and the AI-authorship disclaimer are good practice, but the drafts carry quantitative policy statements (H1 "ราว 1–2 ม.", H5 "พิสูจน์ว่า … แม่นยำสูง", H6 "ทั้ง 38 แห่ง ปิดบาน") that readers will quote without the draft label.
- Fix: remove the two cards from `index.html` (or serve the drafts from an unlinked path) until H1, H2, H3, H5, H6 and P1 are closed. The drafts can stay in git.

### P3 — MED: report 3 mixes UTC (satellite scene names) with Thai local time (gauge data) without saying so

- Scene IDs (`1SDV_20261001T230815`) are UTC. The report prints orbit time "23:08" and the headline "1 ต.ค."; the local time of that acquisition is **2 Oct 06:08 ICT**, and the Mae Klong "2 Oct 11:36" frame is 18:36 ICT. Reports 1–2 use local time for the same satellite ("27 ก.ย. 18:28" = 11:28 UTC), so the two report families are inconsistent. A search of report 3's text for "UTC|เวลาสากล|เวลาไทย" returns 0 hits.
- Effect: every "peak flood area, 1 ต.ค." is one local day later than labelled, and the comparison with gauge peaks (C.13 2 Oct 03:00, C.3 3 Oct, S.26 7 Oct) is shifted in the reader's mind. It reinforces H2's "last acquisition, not the peak".
- Fix: convert scene times to ICT in the builder and print "(เวลาไทย)" in each table header.

### P4 — MED: the policy Q&A in report 3 is generic engineering prose rather than output of the analysis, with unsourced numbers

- `report/goal6_build_report3_draft.py` ≈ lines 570–620 (answers beginning "ตอบตามแนวทางวิศวกรรมชลศาสตร์…", "ตอบตามหลักการสื่อสารความเสี่ยง…"). Unsourced quantities: Tha Chin "รองรับน้ำได้เพียงราวหนึ่งในเจ็ดของเจ้าพระยา", plain slope "ต่ำกว่า 1 ต่อ 10,000", "ความละเอียด 1 ตารางกิโลเมตร", "~50 กิโลเมตร". It also recommends giving dams the "อำนาจ" to pre-drain and a unified command centre — normative policy that AGENTS.md's "ทุกตัวเลขมีแหล่ง" and "แยกข้อเท็จจริง/ตีความ/ประเมิน" rules require to be labelled as opinion.
- It contradicts the report's own findings: it recommends warnings "ล่วงหน้า 12–24 ชม." on a model it calls "ความแม่นยำสูง" (H5), and reuses pre-release as a tool while H1 bounds the C.2 benefit at ≈ 0.24 m.
- Fix: move to a separate "ข้อเสนอของผู้จัดทำ (ความเห็น)" box with sources, or cut. Keep in the main flow only what a JSON field supports.

### P5 — MED: the test suite ratifies current values instead of falsifying them; some tests pin the flawed numbers

- `tests/test_goal6_consistency.py` asserts `scenarios[-1]["drop_m"] == 2.22`, `(25, 17, 8)`, `n_usable_datum == 6`, `coastal_gates_count == 38`, `pasak_over_years == "20/22"`. These tests will *fail when H1/M2/H6 are fixed* and pass while the errors stand. The retired ledger works by substring (`"17/22"`), so a stale number never listed in it passes (HANDOFF.md:83 and GOAL6_PLAN.md:353 L3 values pass today).
- `test_canonical_exists_and_generated` re-runs `goal6_canonical.py` (rewriting a tracked file as a side effect) and compares only `rain_national`.
- No test checks reports 1–2 against the banned-term list (they fail it — P7), and no test checks a statistical invariant. Each of H1–H3 and H5 would have been caught by a one-line invariant.
- Suggested invariants: scenario `drop_m ≤ b × release_at_peak` (H1); the printed 2569 storage max equals the max over the same window as the days-over-URC column (H3); rank ≤ n_years and MD denominator = n_years (M4); every basin flood area printed with its footprint-coverage fraction, no cross-basin sort on un-normalised area (H2); `n_over_crit` reported alongside the count over-critical for the whole window (M2); skill vs persistence beside every RMSE (H5); no UTC scene date printed without ICT conversion (P3).

### P6 — MED (design): "single source of truth" guarantees agreement, not correctness

- `goal6/canonical.json` is produced from the same JSON files the builders read, so H1, H2, H3 and H5 propagated consistently into every document. The contract removed copy-paste drift (good — I found only the HANDOFF/PLAN L3 miss), but a wrong aggregate is then wrong everywhere at once.
- Two parallel canonical systems exist (`analysis/canonical_numbers.json` for reports 1–2, `analysis/goal6/canonical.json` for 3–4) with different generators and test files; numbers that cross (224.34, 452.1) are protected twice, others once.
- Suggestion: an "independent recomputation" tier — for each headline number a second small script derives it from raw files by a different route (flood area from the stage-1 rasters, dam storage straight from `raw/dam_history_all/`), compared with a tolerance. 6–8 numbers cover the headlines.

### P7 — MED: published reports 1–2 and README

- Language rule (AGENTS.md; list in `report/goal6_reportlib.py: BANNED_TERMS`): scanning the rendered text of the two published reports finds, in the academic edition, `model` ×15, `curve` ×13, `datum` ×7, `feature` ×3, `pipeline` ×2, `downstream` ×2, `rule curve` ×1; in the public edition `model` ×3, `curve` ×1. The rule is enforced only for reports 3–4 (`tests/test_report3_language.py`). HANDOFF records a single deferred batch fix — acknowledged, but the public edition is the one most readers meet first.
- README TL;DR quotes "RMSE 0.78 ม. ที่ 24 ชม." for the Ny.7 model. In `analysis/goal4_model_v1_results.json` that is the **linear** model; **persistence on the same window is 0.705 m**, i.e. better — and `analysis/goal4_model_v1_findings.md` (§1 and point 4) says exactly this and tells readers not to present persistence-level numbers as model skill. HANDOFF.md:29 "ชนะ persistence ทุกฤดู" refers to the long backtest, not this window; README should say which.
- The lesson was learned in reports 1–2 and then not carried into report 3 (H5).
- README's "เขื่อนทำตามมาตรฐานไหม? … ไม่มีกลไก URC" and "ถ้าบริหารดีที่สุด … −55 % / −93 %" are the most agency-sensitive lines in the project; each needs its source adjacent and the "positive side" sentence AGENTS.md requires. I did not re-derive the counterfactual.

### P8 — LOW: repository hygiene and maintainability

- 1,759 tracked files / 119 MB. `analysis/` is one flat folder of ~200 entries mixing scripts, results, plans, CSV/PNG and `*_findings.md`; Goal-6 files are split between `analysis/goal6_*.py` and `analysis/goal6/`.
- Dead or deprecated artefacts still live: `analysis/goal6_prerelease_scenario.py` + `analysis/goal6/prerelease_scenario.json` (marked DEPRECATED; its number was then quoted by a reviewer), three near-identical `fetch_khundan_training*.py`, `goal6_rain_rarity.py` vs `goal6_rain_rarity_national.py`. Move to `analysis/archive/`.
- Root has seven untracked `_tmp_*` files; they are gitignored (`.gitignore:62`) so the 09:15/21:15 `git add -A` cron skips them — fine, but delete them. The review itself ran on a **dirty tree** (24 modified/untracked files, including report HTML): commit or tag the reviewed baseline so "what was reviewed" is recoverable.
- `report/goal6_build_report3_draft.py` is a ~650-line script of f-string prose with computation inline (the `_rain_c2_7d` window at lines 62–70, the literal "4 จาก 6" at :91). Splitting content (templates + JSON fields) from logic would make the "no literals" rule enforceable by construction.
- `goal6_build_all.py` excludes the network/large-cache steps (national rain, 2554 ranks, screening, S1 stages, sea mask), so "run build_all → everything consistent" holds for the downstream half only; the docstring says so, README/START_HERE should too.

### P9 — LOW: licensing and third-party data

- `LICENSE` is CC BY 4.0 for the whole repo including code; CC licences are not designed for software (no patent/warranty terms). Consider MIT/Apache-2.0 for code and CC BY for text/data.
- `THIRD_PARTY_NOTICES.md` calls thaiwater "ข้อมูลเปิด"; the repo redistributes 199-gauge hourly series and the 2,315-gate list. I did not verify the portal's reuse terms — one sentence with the licence URL would settle it.

### P10 — process: who has reviewed this, and what is missing before publication

- The five earlier review files are from LLMs (GLM, Gemini, Qwen, DeepSeek, Sift), as is this one; the repo itself records that LLM reviews were wrong several times. No hydrologist, statistician or Thai media-law adviser has signed off, yet the drafts contain policy proposals and agency comparisons.
- Suggested minimum before announcing reports 3–4: (a) a human hydrologist reads §4.5 (C.2 chain), §6 (L3) and the dam table; (b) counsel reads the Q&A flagged in M6/H6/P4 and the P1 remedy; (c) right of reply — send the agency-specific pages (RID dams, EGAT dams) to the agencies' public contacts ≥ 7 days before posting, which AGENTS.md's "แสดงด้านบวกของหน่วยงาน" principle already points toward; (d) tag the release and archive it (e.g. Zenodo DOI) so the forensic timestamp is third-party.

## Additional suggestions (technical, ordered by value / effort)

1. **Flood area:** per basin, union same-pass frames and report `detected_km² / covered_lowland_km²` plus `covered_lowland_km²`; publish the range [detected, detected ÷ coverage] — ≈ 20 lines in `goal6_s1_stage2_water.py`, removes the H2 attack surface.
2. **Basin rain:** area-weighted mean of POWER cells inside each HydroBASINS polygon (lev08 is already in `data/22…/hydrobasins`) instead of one point per basin; add Jul–Oct total and 30-/60-day maxima beside the 7-day maximum so the 2011 comparison (H4) uses the statistic that mattered in 2011.
3. **Forecast table:** `skill = 1 − RMSE/RMSE_persistence` on rolling-origin folds over the 2020–2025 flood seasons rather than one 2026 window; drop the best-of-3 sentence.
4. **Headline rain count:** state "32/99 (expected ≈ 6.5 under stationarity; field significance by block bootstrap over years)" — cheap with the cached POWER series and answers the post-selection/spatial-dependence attack directly.
5. **Critical-level screen:** add the datum-independent "above `meta_min_bank`" and "above own 2020–2025 annual maximum" tests (M2); they also rescue K.10/K.37/P.17 as usable evidence.
6. **Tide:** compute the upstream–downstream gradient (C.12/C.22A minus CPY015) for 24–29 Sep against a same-discharge historical baseline — the evidence "gravity drainage was limited" actually needs, using data you already hold.
7. **UTC→ICT** in all satellite tables (P3).
8. **Privacy gate in CI** (P1 fix 5) and a `docs/PRIVACY_REDACTION.md` listing what was removed and why.

## What else I checked and found OK (project level)

- Secrets: regex scan of tracked text files for key/secret/token/password assignments → no hits; `data/22_goal6_network/.cdse_s3.json` is ignored.
- No tracked temporary files (`git ls-files | grep -E "^_tmp|\.log$"` → 0); `.gitignore` covers large binaries, SAFE folders and `archive/`.
- Colour contrast: every CSS rule in reports 3 and 4 that sets both `color` and `background` as hex has ratio ≥ 4.5; no low-contrast inline styles (limited — gradients, SVG fills and chart images not covered).
- Reports 3–4 carry AI-authorship and expert-review disclaimers, TLDR, context, definitions and Q&A, as AGENTS.md requires; self-containment is respected apart from the "(รายงานที่ 4)" forward references.
- `requirements.txt` pins versions and explains why (RMSE depends on scikit-learn/numpy versions); `goal6_build_all.py` fails fast with the failing step name.
- Folders sampled all had `manifest.md` with source, date and method (a full audit of all 21 folders was not done).

## Limitations added by this addendum

- I did not open image files (screenshots, maps): privacy and legibility of images are unverified.
- Phone/name detection used regexes over tracked text files; names without honorifics and Latin-script names beyond those seen were not enumerated, so P1 is a floor, not a full inventory.
- Reports 1–2 were checked only for language-rule terms and README consistency, not re-audited numerically.
- I did not run `goal6_build_all.py` end-to-end (it rewrites tracked files and needs caches).
- Legal statements are engineering-side observations, not legal advice.


---
---

# Addendum 2 — suggested additional data, information and analysis (12 Oct 2026)

Purpose: things that would make the project more useful or more defensible, beyond fixing the findings above. The FOI items already in `docs/OFFLINE_DATA_BACKLOG.md` (gate/pump logs, SOPs, bathymetry, rule-curve documents) are **not repeated**; this list is what the repo does not yet contain. I did not verify access, licence terms or API availability for the external sources; those are marked "check". Each entry gives: what, why it matters here, how, effort, and which finding it closes.

Effort scale: **S** ≤ 1 day · **M** 2–5 days · **L** > 1 week.

## A. Use data the project already holds (no new acquisition)

### A1. Flood area with coverage normalisation and frame union — effort S — closes H2
- **What:** per basin and pass, merge adjacent frames (same relative orbit, same date), then report `detected_km²`, `covered_lowland_km²`, `detected / covered_lowland` and the range [detected, detected ÷ coverage].
- **Why:** headline areas currently come from frames covering 13–100 % of a basin; the cross-basin ranking is not like-for-like.
- **How:** in `analysis/goal6_s1_stage2_water.py` the per-frame mask `w` and `lowland` already exist; take the union of `w` across same-pass frames on the shared basin grid, and divide by `(valid_mask & lowland).sum()` where `valid_mask = isfinite(post_vh) & isfinite(pre_vh)`. Print coverage in every table row and map caption.
- **Output:** `analysis/goal6/flood_area_normalised.json` consumed by `goal6_canonical.py`.

### A2. Basin-mean rain on HydroBASINS polygons plus season totals — effort M — closes H4, M4, and part of L2
- **What:** area-weighted mean of POWER cells inside each lev08 polygon (and each dam catchment if polygons are traceable), for 7/30/60-day maxima **and** Jul–Oct and Aug–Sep totals, 1981–2026.
- **Why:** 2011 was a season-total year; a 7-day maximum at one point is the wrong statistic to call its rain "ordinary" in a basin, and point values share cells.
- **How:** `data/22…/hydrobasins` is present; rasterise polygons on the 0.5° × 0.625° POWER grid, weight by intersected area; reuse `best_window` from `goal6_rain_rarity_national.py` (reuse-first rule) and add a `season_total()` helper. Use the rank among 46 years with the same-window rule for 2026 (Jul 1–Oct 9) and truncated windows for all other years too (apples-to-apples), reporting both.
- **Output:** `analysis/goal6/rain_basin_mean.json`; replaces the "basin median of gauge-point ranks" in report 4.

### A3. Travel time and warning lead time along the main stem — effort S–M — new content, supports H5/P4
- **What:** cross-correlation of detrended hourly stage between gauge pairs (P.17 → C.2 → C.13; S.28 → S.26; Kgt.3 → Ny.7 ...) in the 2019–2026 warehouse; for 2026 report the observed peak-to-peak delay.
- **Why:** gives the only honest "hours of warning upstream gauges gave" number, and checks the 2-day lag used in the C.2 chain (corr 0.44) against measured travel time.
- **How:** use first differences (removes the trend that inflates −0.92-type correlations — L1), restrict to flood-season hours, bootstrap by day blocks for the interval. Report median lag ± interval per pair.
- **Output:** `analysis/goal6/travel_times.json` and a single table in report 3 §4.

### A4. Return-period flows at gauges with discharge — effort M — adds a number agencies use
- **What:** GEV/Gumbel fit to annual maximum discharge (or stage → discharge through the gauge's own rating pairs) at stations with ≥ 7 seasons, with bootstrap confidence intervals; place the 2026 peak on the curve.
- **Why:** replaces "rank 1 of 46 years of rain" (and the Weibull cap at 47 years — L2) with "flow of about a T-year event (interval a–b)", and exposes how short the 2019–2026 hourly record really is.
- **How:** `scipy.stats.genextreme`; use L-moments or MLE with a shape-parameter prior to avoid wild fits on 7 points; for longer records use the daily discharge series if the API provides them (check `เขื่อนรายวัน` inflow for dams — 22 years, usable directly).
- **Caveat to state:** 7 annual maxima → intervals will be wide; show them, that is the point.

### A5. Reservoir mass balance for all 24 dams — effort S — closes part of H1/H3, new QA
- **What:** `ΔS(t) = I(t) − R(t) − residual(t)` daily; tabulate residual statistics per dam and year; then compute "spare capacity below URC on 19 Sep" per dam.
- **Why:** (1) residuals reveal bad series (the H3 carry-over problem would also have surfaced); (2) "spare capacity at the start of the wave" is what the pre-release question actually needs, not an assumed 100 mcm/day.
- **How:** inflow/release/storage already in `dam_history_all/` and `dam_screen_2026/`; evaporation is small relative to flood-season flows, treat it as residual.
- **Output:** `analysis/goal6/dam_balance.json`; one column in the dam table.

### A6. "Own-history" screen for all ~200 gauges — effort S — closes M2
- **What:** for every gauge in the warehouse compute percentile of the 2026 maximum against its 2020–2025 annual maxima, and exceedance of `meta_min_bank` when the metadata is consistent with the series scale (series max within ± few m of bank).
- **Why:** independent of the API critical level that was unusable for 19 of 25 gauges; gives a national map that does not depend on a threshold.
- **How:** warehouse JSON per station; record n_years so short-record gauges are flagged rather than ranked.
- **Output:** `analysis/goal6/own_history_screen.json` + one national figure.

### A7. Tide gradient and same-discharge baseline — effort S — closes H6
- **What:** `Δh = stage(C.12 or C.22A) − stage(CPY015)` and the low-water level at CPY015 as a function of upstream discharge (C.13/C.2), 2012–2025 vs 24–29 Sep 2026.
- **Why:** shows whether the +0.8–1.0 m rise of the low-water mark is explained by discharge alone (then "tide blocked drainage" is not supported) or exceeds the discharge-conditional expectation (then it is).
- **How:** regression of daily minimum at CPY015 on daily mean upstream discharge and tidal range, using historical years with coverage ≥ 80 % (many years in `historical_estuary_summary.json` are < 25 % — use only the good ones and say so).
- **Output:** one scatter + one sentence in the Q&A with an interval.

## B. External public data not yet in the repository (check access and licence)

| ID | Source | What it adds | Where it helps | Effort |
|---|---|---|---|---|
| B1 | **GPM IMERG Final / GSMaP** (≈ 0.1°, 30 min) | rain at ~10 km vs POWER ~55 km; storm structure and timing for 26–28 Sep | limitation (3); shared-cell inflation of 67/199; A2 | M |
| B2 | **TMD rain gauges / radar mosaics** (check API/FOI) | real station totals, the "gauge always higher than grid" correction | calibrates B1/POWER bias | M–L |
| B3 | **ERA5-Land soil moisture** (ERA5 already used for Khun Dan) | antecedent wetness before 19 Sep for all six basins | "basin was saturated" is asserted for Nakhon Nayok only; tests it elsewhere | S–M |
| B4 | **ESA WorldCover 10 m or Dynamic World** | stratify rule performance by paddy / aquaculture / urban / bare | M1: answers "wet rice fields / aquaculture / urban double-bounce" quantitatively | S |
| B5 | **JRC Global Surface Water (occurrence/seasonality)** | independent permanent/seasonal water mask | cross-check of the 1,435 km² Bangkok permanent-water mask | S |
| B6 | **Sentinel-1 coherence and time series** (same archive) | separates paddy cycle (backscatter ramp) from inundation; longer pre-event baseline than one date | M1; reduces dependence on the single 19/20 Sep reference | M |
| B7 | **Landsat 8/9, HLS, MODIS** after 3 Oct | optical confirmation when S2 is cloud-covered; extends the "last acquisition 2 Oct" limit | H2 date/peak question; item (6) | M |
| B8 | **GISTDA historical flood extents** (2554, 2560, 2565) | second and third events with an independent reference | out-of-sample test of the S1 rule (C5) and "is 2569 unusual" in area terms | M (needs human step per AGENTS.md) |
| B9 | **WorldPop / GHSL / Thai census at tambon** | people and assets inside detected flood area | the question readers ask; aggregate only, consistent with PDPA | S–M |
| B10 | **OSM roads/rail/canals** (already used for maps) | embankments as barriers (policy Q&A item 4); roads cut | adds evidence for statements currently made without data | S |
| B11 | **Rating-curve / discharge measurement tables** (RID/HII public pages) | stage → discharge for gauges used in L3 and C.2 | replaces the linear level–volume fit (H1) with the gauge's own curve | M |
| B12 | **Official URC/LRC PDF for each dam** (EGAT/RID public pages; FOI-03 for the rest) | removes the "single month-day template" caveat | H3/H4 | M–L |

## C. New analyses

### C1. Counterfactual routing instead of subtraction — effort M — replaces the pre-release scenario (H1)
- **What:** a lumped Muskingum (or two-reservoir) model for P.17 and N.67 → C.2 calibrated on 2020–2025 storms; run 2026 with (a) observed dam release, (b) alternative release schedules constrained by A5's spare capacity and by physical release limits.
- **Why:** the current scenario violates the report's own 3 % finding; a routed counterfactual yields an honest, bounded number (probably ≈ 0.1–0.3 m at the peak by the 3 % argument) that is still useful policy information.
- **How:** parameters K, X by least squares on observed inflow/outflow pairs; validate on a held-out season; report parameter uncertainty by bootstrap; always cap the alternative release by what the reservoir could hold (A5).
- **Output:** `analysis/goal6/c2_counterfactual.json` with median and interval, and a clear "what this cannot say" sentence.

### C2. Forecast skill and lead-time value — effort M — closes H5
- **What:** (1) skill vs persistence with rolling-origin evaluation across 2020–2025 flood seasons plus 2026 as final test; (2) lead time between model-predicted bank exceedance and the actual crossing, per basin, with false-alarm rate.
- **Why:** turns RMSE tables into the number a warning system needs and shows honestly where lead time is zero.
- **How:** reuse `goal6_l3_model.py` feature builder; add purge/embargo of `max(horizon)` hours at fold boundaries (fixes the leakage noted under H5); report `1 − RMSE/RMSE_pers` with block-bootstrap intervals by day.

### C3. Uncertainty propagation for the headline numbers — effort M
- **What:** Monte-Carlo over (S1 rule precision/recall as estimated, POWER grid bias, rating-curve error) to give ranges for flood area, "% of flow from dam", return period.
- **Why:** replaces point estimates with intervals; also prioritises which input to improve (sensitivity indices).
- **How:** simple parametric draws; 5,000 samples are plenty; store in canonical.json as `{value, lo, hi}` and have builders print ranges.

### C4. URC-template reliability study — effort S–M — closes part of H4
- **What:** for dams where an official curve is available (Khun Dan already cross-checked; add 2–3 more from B12), compare template-derived days-over-URC with official-curve days for years the curve differs; quantify the error rate.
- **Why:** the 24-dam table rests on one template dated 2020 applied back to 2005–2011; one measured error rate is worth more than a caveat.
- **Output:** "template agreement X % of days, Y dam-years differ by > Z days".

### C5. Out-of-sample test of the S1 water rule — effort M — closes M1
- **What:** apply the frozen thresholds (ΔVH ≤ −0.5, ΔVV ≤ −1.5, VH ≤ −20, 3×3 opening) to at least one other event with an independent reference (B8) and one **non-flood** control pair (same orbit, dry weeks) to measure false-positive area per 1,000 km².
- **Why:** the 0.727 F1 was tuned and scored on one scene; the control pair directly measures how much of 2,264 or 1,104 km² could be noise; the class-stratified accuracy (B4) shows where.
- **How:** reuse `s1_change_detect.detect/prf`; report F1 and area bias per land-cover class.

### C6. Exposure and impact layer — effort S–M
- **What:** overlay detected flood (with ranges from C3) on population (B9) and road/rail (B10) to give people and kilometres of road inside detected water per basin.
- **Why:** the most-requested public number; it also forces the coverage and bias caveats to be visible next to something people care about.
- **Constraint:** aggregate at tambon or 1 km grid, no household-level layers (PDPA).

### C7. Event comparison library (2554, 2560, 2565, 2569) — effort L
- **What:** run the same pipeline (rain basin-mean, dam balance, area if imagery exists, return-period flows) for each prior major flood.
- **Why:** converts the single-event "forensics" into a calibrated judgement of how unusual 2569 was on each axis; also tests whether the pipeline is stable across years (e.g. do the same SUSPECT gauges appear?).
- **Dependency:** B8/B12; the data-quality ledger (D1).

### C8. Public-information timeline — effort S–M
- **What:** per basin, merged timeline of public forecast products (Flood Hub, TMD warnings, RID bulletins if captured), gauge crossings, and S1 acquisitions with lead-time between first public signal and first bank exceedance.
- **Why:** README already points to a 4-day Flood Hub signal for Nakhon Nayok; extending it shows whether that was typical, in a way that supports system-level (not blame-level) conclusions.

## D. Information to add to the reports and repo

| ID | Item | Why | Effort |
|---|---|---|---|
| D1 | **Data-quality ledger** — per gauge/dam: % hours present, longest gap, datum status (OK / SUSPECT with reason), source URL, fetch date | one table reused in every report; makes limitations (1), (5), (6) checkable at a glance | S |
| D2 | **Agency/responsibility map** — who operates which dam, gate, gauge, with public contact | readers see where evidence stops; supports the right-of-reply step (P10) | S |
| D3 | **"What public data cannot answer"** page — 5–6 questions, each tied to the FOI item that would answer it | converts limitations into an actionable request list; avoids over-claiming | S |
| D4 | **Reproducibility card per headline number** — script, input hashes, one command, expected value ± tolerance | START_HERE §4 does this for reports 1–2; extend to Goal 6 | S |
| D5 | **Method-validity box** in each report — for each method: what it can/cannot show, validation evidence, known failure mode (e.g. rule: tuned on one scene) | puts M1/H5-style caveats in the reader's path instead of the limitations tail | S |
| D6 | **Versioned release notes** — what changed between report 3 drafts and why (the retired ledger already holds the data) | forensic traceability; shows corrections transparently | S |
| D7 | **Plain-language "how sure are we"** — three-level confidence label per headline (supported by independent data / by one data source / indicative) | supports the "easy for the public" requirement without hiding uncertainty | S |
| D8 | **PRIVACY_REDACTION.md** and a CI check | P1 | S |

## E. Suggested order of work

1. **Close the legal exposure first (P1, P2).** Remove/aggregate the social-media raw data; unlink drafts. Effort S.
2. **Fix what is wrong without new data:** H1 (cap scenario), H2/A1, H3 (window), H5/C2 wording and skill table, H6/A7, M2/A6, P3 (UTC→ICT). Roughly 3–5 days.
3. **Strengthen the evidence base cheaply:** A2 (basin rain with season totals), A5 (dam balance), B4 + C5 (land-cover and out-of-sample test of the S1 rule), D1 (data-quality ledger).
4. **Then add new content:** C1 (routing counterfactual), A3/A4 (travel times, return-period flows), C6 (exposure), C8 (information timeline).
5. **Before announcing:** human hydrologist and counsel review, right of reply to agencies, tagged and archived release (P10).

If only four additions are possible: **A1 (frame-union area), C1 (routing counterfactual), B4 + C5 (land-cover-stratified, out-of-sample S1 accuracy), A4 (return-period flows)** — together they turn the four largest attack surfaces (area ranking, pre-release number, area bias, rarity claim) into defensible ranges without waiting for any agency data.

---

# Resolution log (updated 12 Oct 2026, same day)

| ID | Status | Where |
|---|---|---|
| P1 privacy | **Done** — files removed from tree and rewritten out of history (local + remote force-push by author); `tests/test_privacy.py` | commit "PDPA: …" |
| H1 pre-release | **Done** — scenarios withdrawn; ceiling ≤ 0.24 m | `goal6_c2_attribution.py`, report 3 Q&A, tests |
| H6 tide/gates | **Done** — unsupported gate/pump claims removed; observed low-water rise stated with limits | report 3 |
| P4 policy Q&A | **Done (labelled)** — block labelled as the author's opinion; unsourced numbers removed | report 3 |
| H3 dam storage window | **Done** — window max (1 Sep–9 Oct) in both reports; daily window values stored; cross-checked vs screen within 1 % | `goal6_dam_history_all.py --refresh`, reports 3–4, test |
| H4 2554-vs-2569 wording | **Done (wording)** — "operations comparable" and "normal system behaviour" removed; season-total rain still not computed (open: suggestion A2) | report 4 |
| H5 forecast claims | **Done** — skill vs persistence in canonical; TLDR/summaries/policy text reworded; single-event caveat. Leakage/embargo fix and rolling-origin evaluation still open (C2) | report 3 |
| H2 + P3 area/dates | **Partly** — coverage % and same-pass sum printed; dates converted to Thai time; headline no longer says "1 ต.ค. จุดสูงสุด". Coverage-normalised estimate / frame union still open (A1) | report 3 |
| M4 `/199` label | **Done** | `goal6_rain_rarity_2554.py` |
| M5 stale numbers | **Done** for HANDOFF/PLAN L3 values | docs |
| P5 tests | **Done** — pins replaced by ceiling/invariants; 4 new invariant tests | `tests/test_goal6_consistency.py` |
| H2 maps | **Done** — maps now draw the frame footprint (grey = not inspected), the Thai-time stamp and coverage %; the Bangkok map shows parcel-shaped detections in the north-east (paddy/aquaculture pattern, supports M1 caution) | `goal6_flood_maps.py` |
| Report size | **Done** — report 3: 10.0 MB → 3.8 MB (128-colour palette PNG at embed time; originals untouched) | `goal6_reportlib.figure` |
| Open | M1 (S1 rule validation), M2 (25 over-critical headline / own-history screen), M3 (pre-registration wording), M6 residual wording, P2 (drafts still linked — author's choice), P6–P10, all suggestions A/B/C/D | — |


---

# Addendum 3 — reports 1–2 (Nakhon Nayok) now in scope (12 Oct 2026)

Scope change: the public and academic editions and the README are reviewed and fixed under the same rules as reports 3–4. Method: read the rendered text of both editions, re-derived the checkable claims from the repo's own CSV/JSON, then fixed the builders (`report/build_report_html.py`, `report/build_expert_report.py`) and re-ran `analysis/build_canonical_numbers.py`, the builders, `pytest`, and the integrity check.

| ID | Sev | Finding (evidence) | Status |
|---|---|---|---|
| R1 | HIGH | **"Rain higher than the 26-year maximum (ERA5)"** compares gauge totals (1,058–1,416 mm) with an ERA5 grid maximum (606 mm). Like for like, `analysis/era5_rain_18day_max_by_year.csv` gives 2026 = 430 mm, **rank 6 of 27** (≈ 1 year in 4) — the project's own `event_timeline_sep2026.md` item 6 says so. Appeared in the public TL;DR card, Q&A "ฝนผิดปกติจริงหรือ?" and "ใหญ่แค่ไหน". | **Fixed** — text now states both, with the ERA5 rank rendered from the CSV (`@@R:era5_rank@@`) |
| R2 | HIGH | **"36 days above the upper rule curve before the storm"** (README, public ×5, academic table): `dam_khun_dan_daily_2013_2026.csv` shows the run is **30 Aug–27 Sep = 29 days at the flood peak**; 36 days is the run to 4 Oct (after the event). | **Fixed** everywhere; test recomputes the streak from the CSV |
| R3 | MED | Over-claims: "พิสูจน์ว่า "ตัวกั้น" = อัตราการปล่อย" (release cut on 30 Sep coincided with rain stopping and tributaries receding); "ซึ่งไม่มีหน่วยงานใดเคยเผยแพร่" (absence claim); unsourced "ฝนเดือน ต.ค. กรุงเทพฯ ~200 มม." | **Fixed** (softened / removed) |
| R4 | MED | Language rule not enforced on reports 1–2: academic `model` ×15, `curve` ×13, `datum` ×7, `feature`, `pipeline`, `downstream`; transliterations "สปิลเวย์", "เกจ" (24×). `rating curve` must not become "rule curve", so replacement is context-ordered. | **Fixed** — `soften_terms()` + builder aborts if any remain; `tests/test_reports12.py` |
| R5 | MED | Framing: "การไม่ตามเส้นควบคุมมา 36 วัน" presupposes a duty that the same report says it could not find; "การบริหาร … คือจุดที่เลือกทางไว้จริง" attributes choice; heading "ผิดกฎหมายหรือไม่?". | **Fixed** — "เก็บอยู่เหนือเส้น", "สถานะอ่าง … กำหนดทางเลือก", "มีระเบียบสาธารณะบังคับหรือไม่?" |
| R6 | MED | README quoted RMSE 0.78 m at +24 h without saying persistence scored 0.71 m on the same window (`goal4_model_v1_results.json`). | **Fixed** |
| R7 | LOW | Size: public 6.7 → 4.8 MB, academic 3.3 → 2.2 MB (palette PNG, JPEG q78 at embed time; sources untouched). Images re-validated by test. | **Done** |
| R8 | MED | **Open (counsel):** "ผังน้ำลุ่มบางปะกงที่เป็นกฎหมายกำกับ" (legal status of the plan not verified in repo); named expert quotation (LEGAL_REVIEW accepts it, re-confirm source link); "ตามมาตรฐานหรือไม่" language. | Open |
| R9 | MED | **Open:** the 452.1 km² peak depends on the same S1 rule whose F1 on that very scene is 0.645 (`gistda_georef_findings.md` §7); the report calls it a lower bound (optical 5.3× larger in clear patches) but the counterfactual "area × days" table inherits ±30 % commission/omission. Needs the M1/B4 validation. | Open |
| R10 | LOW | **Open:** peak discharge "610–630 m³/s ≈ 2× previous maxima 323/212" compares against only three seasons of gauge data; stated, but "ใหญ่กว่าปกติมาก" is stronger than a 3-year record supports. | Open |

Re-verified and **found OK** in reports 1–2: 452.1 / 363.6 / 306.9 km² match `canonical_numbers.json`; release 31.66 mcm/day = 366 m³/s; storage 224.34 mcm at 27 Sep; 9.23 m / 8.45 m stage values and 65 h over bank agree with the canonical checks; scene times are already in Thai local time (18:28 = 11:28 UTC); uncertainty ranges (±18 %, ±6 h, ±0.85 m) are disclosed next to the counterfactual table; the "ช่องโหว่อยู่ตรงไหน" Q&A frames systems, not persons.


---

# Addendum 4 — S1 water-rule validation (M1 / R9), 12 Oct 2026

Script: `analysis/goal6_s1_rule_validation.py` → `analysis/goal6/s1_rule_validation.json/.md` (frozen rule, no new data, no threshold change). What the data in the repo can and cannot say:

| Test | Result | Reading |
|---|---|---|
| In-sample F1 (2 Oct, vs GISTDA pass) | **0.727**, 95 % block-bootstrap 0.683–0.765 (P 0.672, R 0.792) | reproduces the calibration value; the interval is ±0.04 |
| Out-of-sample F1 (27 Sep peak, vs the same GISTDA composite) | **0.601**, 0.535–0.654 (P 0.505) | the composite (28 Sep–2 Oct) is not time-matched, so this is a pessimistic bound, but 0.73 does not transfer unchanged |
| Pre-flood control pair (S1D 15 Sep → S1C 21 Sep, ~19 % of lowland) | 4.1 km² "water" in 293 km² covered ≈ **14 per 1,000 km²** | specificity under moderate rain is good; only **one** control covers the lowland (the 18:20 pairs cover mountains only), so this is not a basin-wide false-positive rate |
| Threshold sensitivity (VH threshold −18/−20/−22 dB at calibrated Δ) | peak scene 578 / 452 / 288 km²; 2 Oct 471 / 364 / 226 km²; F1 moves only ±0.04 | **the calibration cannot pin area**: ±2 dB moves area ±25–36 % with almost no change in F1. The full 45-setting grid spans 196–683 (peak) and 174–536 km² (2 Oct) |
| Share of detected "new" water that was already dark (VH ≤ −20 dB) in the reference | NN 22–28 %; Pasak 14 %, Bang Pakong 20 %, Tha Chin 13 %, Ping 16 %, Bangkok 19 %, **Mae Klong 90 %** | permanent water/ponds with a ≥0.5 dB change pass the Δ test. Net-new area: Pasak ~450, Bang Pakong ~1,023, Tha Chin ~140, Ping ~1,908, Bangkok ~1,071 (before the sea mask), **Mae Klong ~7 km²** |
| Same-orbit no-flood controls for the five other basins | none (24 Sep frames are their own references; 20 Sep frames cover 0–3 %) | not testable with the repo's imagery |

Consequences applied: report 3 limitation (7) carries these numbers (rendered from canonical); each basin note prints the already-dark share and the net-new area; the TLDR adds one clause; "ตรงกัน 72.7 %" is retired; reports 1–2 no longer call 452 km² a "lower bound" and state the 288–578 km² range with F1/CI. Canonical headline areas (521/73/1,282/160/2,264/1,104) are **unchanged** — impact was computed above rather than applied, because changing the definition to "net-new" would alter published report-3 figures and needs the author's decision.

Still open: land-cover stratification (needs WorldCover), a time-matched reference for the peak, any independent reference outside Nakhon Nayok.


---

# Addendum 5 — basin-mean rain and season totals (A2), 12 Oct 2026

Script `analysis/goal6_basin_rain.py` → `analysis/goal6/basin_rain.json/.md`. Catchments = all HydroBASINS lev08 polygons upstream (NEXT_DOWN) of the polygon containing each reference gauge; weights = area overlap with NASA POWER 0.5° × 0.625° cells; 38 new cells fetched (45 reused from the earlier gauge cache); one common window 1 Jul–7 Oct for **all 46 years including 2026** (removes the one-sided truncation noted in M4).

| Catchment above | cells | season total 2554 (rank/46) | 2569 (rank) | 7-day max rank 2554 / 2569 | median (mm) |
|---|---|---|---|---|---|
| Ping–Wang–Yom–Nan at C.2 | 49 | 888 mm (**3**) | 806 (8) | 10 / 3 | 624 |
| Whole basin above C.13 | 52 | 890 (**3**) | 824 (7) | 8 / 2 | 633 |
| Pasak at S.26 | 13 | 827 (5) | 846 (4) | 9 / 5 | 616 |
| Mae Klong at K.3A | 16 | 920 (15) | 1,538 (**1**) | 18 / 1 | 800 |
| Bang Pakong at Kgt.3 | 10 | 1,087 (5) | 1,288 (2) | 29 / 1 | 828 |
| Tha Chin at T.1 | 11 | 707 (16) | 972 (**1**) | 18 / 1 | 655 |
| Nakhon Nayok at Ny.7 | 2 | 1,039 (5) | 1,188 (2) | 18 / 1 | 783 |

What changed in the conclusions:
- **H4 sharpened:** the 2011 rain was a *season-long, upper-basin* event (season total rank 3 of 46, 888 mm — above the 2026 value of 806 mm), which the old 7-day-maximum statistic put at rank 10 and the old gauge-median table called "ordinary". Report 4 now says so and states that cross-year days-over-curve are descriptive only.
- **"2554 west was dry" retracted:** Mae Klong 2554 season total is rank 15/46 (above median), not "median rank 39". Report 3's dam-table note and the "best dam" Q&A now carry the computed rank and still say operation and inflow cannot be separated.
- **2569:** a late-September burst on the middle/lower basins (7-day max rank 1 in Mae Klong, Tha Chin, Nakhon Nayok; Bang Pakong season total rank 2), while the upper basin's season total was only rank 8.
- Weibull/ranks at gauge points (67/199 → 32/99 cells) remain valid as a *station-density* count; the basin-mean table is the preferred statement for basin-level claims.

Limits: POWER MERRA-2 is ~55 km (cells span 0.5° × 0.625°); the 2-cell Nakhon Nayok catchment is crude; reanalysis rain is smoothed (gauges higher); season totals are not inflow (reservoir inflow for 2011 is still not in the report).
