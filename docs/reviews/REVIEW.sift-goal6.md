# REVIEW — Goal 6 (national extension): reports 3 & 4

Reviewer: **Sift** (independent AI review, second-wave package `docs/reviews/GOAL6_REVIEW_BRIEF.md`)
Scope: drafts `report/ระลอกปลายกย2569_6ลุ่ม.html` (report 3) and `report/ชุดเทียบมาตรฐาน2554.html` (report 4),
the `analysis/goal6*` scripts and `analysis/goal6/*.json`, cross-checked against `HANDOFF.md`,
`START_HERE.md`, `docs/GOAL6_PLAN.md`.
Method: ran/derived from the committed JSON and HTML; re-computed every quantity I could.
Thai: **readable** — I reviewed language (section C) as well as A/B/D/E.

---

## Top line

**fix-first.** The canonical Nakhon Nayok work (reports 1–2) is not implicated, and the flood-area
pipeline is internally consistent — but reports 3 and 4 as drafted contain **two false headline
generalizations**, a **builder that hardcodes the central attribution numbers**, an **out-of-range
extrapolation presented as a policy finding**, and an **L3 forecast that re-introduces a look-ahead the
repo itself documents as a bug**. None of these require re-deriving reports 1–2; all are fixable in
the drafts. Do not publish 3/4 until H1–H7 are resolved.

Counts: 7 HIGH · 8 MED · 3 LOW.

---

## Findings

### H1 — HIGH — "EGAT dams never exceeded their guide curve" is false, and self-contradictory in the same paragraph

**Claim (report 3 TLDR, report 4 TLDR, report 3 §3):**
- report 3 TLDR: "(2) … **เขื่อนการไฟฟ้าฝ่ายผลิตฯ เก็บน้ำต่ำกว่าระดับกำกับเสมอ (2554 และ 2569 ไม่เคยเกิน)**"
- report 3 §3 table intro: "สิริกิติ์ 164 วัน · **ขณะที่เขื่อน กฟผ. ทุกแห่ง 0 วัน**"
- report 4 TLDR: "และเขื่อนการไฟฟ้าฝ่ายผลิตฯ **ไม่เคยเกินระดับกำกับเลยทั้งสองปี**"

**Evidence:** `analysis/goal6/dam_history_all.json`, 2011 `days_over_urc`:

| dam | operator | 2011 days over URC |
|---|---|---|
| ภูมิพล (Bhumibol) | **กฟผ./EGAT** | **127** |
| สิริกิติ์ (Sirikit) | **กฟผ./EGAT** | **164** |
| อุบลรัตน์ (Ubol Ratana) | **กฟผ./EGAT** | **99** |
| ศรีนครินทร์ | กฟผ. | 0 |
| วชิราลงกรณ | กฟผ. | 0 |
| รัชชประภา | กฟผ. | 0 |

The report's own §3 sentence lists "สิริกิติ์ 164 วัน" and then, in the same breath, asserts all EGAT
dams were at 0 — a direct self-contradiction. The project's own text labels ภูมิพล as กฟผ.
(`analysis/goal6_screen_2026_findings.md` §5 row 3: "ภูมิพล 13,462 (กฟผ.)"), so the taxonomy is not
in dispute. The Q&A section does scope the claim correctly ("ศรีนครินทร์ · วชิราลงกรณ์ · รัชชประภา"),
but the TLDRs — the most-read lines — do not, and the causal explanation offered ("เพราะระบบของเขา
ผลิตไฟฟ้าได้ทุกระดับน้ำ") applies equally to ภูมิพล/สิริกิติ์, which did exceed.

**Fix:** scope every TLDR statement to the three dams actually observed, or state the true pattern
(e.g. "of the six EGAT dams, the three Mae Klong/Prachuap ones never exceeded; ภูมิพล/สิริกิติ์/อุบลรัตน์
did in 2554"). Drop the "because they can generate at any level" explanation or apply it only to the
dams where it holds.

---

### H2 — HIGH — "all 25 gauges peaked 23 Sep–9 Oct" is false for 8 of 25 (the August peaks are silently folded into the late-Sept narrative)

**Claim (report 3 intro; `goal6_screen_2026_findings.md` §1):**
- report 3: "การสำรวจจุดวัดระดับน้ำ 200 จุด … ช่วง 1 ก.ค.–9 ต.ค. 2569 พบว่า **25 จุด ระดับน้ำสูงสุดช่วง 23 ก.ย.–9 ต.ค.**"
- findings MD §1: "**จุดเกินวิกฤตทุกจุดมีพีคช่วง 23 ก.ย.–9 ต.ค. 69** → ระลอกปลาย ก.ย. เป็นเหตุการณ์ระดับชาติ"

**Evidence:** `analysis/goal6_screen_2026_summary.json`. Of the 25 stations with `hours_over_crit > 0`,
**8 peak before 23 Sep**:

```
Y.4    2026-08-23   X.119A 2026-08-27   P.1   2026-08-11   N.5A  2026-09-22
N.2B   2026-08-02   W.1C   2026-08-14   Gt.9  2026-09-20   Sw.5A 2026-08-10
```
(five of them in **August**: N.2B, W.1C, Sw.5A, P.1, Y.4 — all in northern basins.)

The screening window (1 Jul–9 Oct) deliberately captures the whole monsoon; the write-up then
attributes every one of those peaks to the late-Sept wave. The fixed-window design is fine; the
**narrative that the window's stations all peaked in the late-Sept wave is not**. `analysis/goal6/ping_cp/l1_summary.json`
independently shows upper-Ping stations (P.4A, P.75, P.67, P.1) peaking 8–11 Aug, so this is not a
one-off gauge artefact.

**Fix:** change "ทุกจุด" to a count, e.g. "17 of 25 peaked 23 Sep–9 Oct; the remaining 8 are separate
August/early-Sept events in the north and are not part of the late-Sept wave", and add a line to the
limitations section about the fixed window swallowing earlier-season peaks.

---

### H3 — HIGH — the C.2 attribution correlations (−0.92, 0.44) are hardcoded; no committed script computes them

**Claim (report 3, Q&A):** "ความสัมพันธ์ระหว่างการปล่อยเขื่อนกับน้ำที่ C.2 เป็นค่าติดลบสูง (**−0.92**) …
ขณะที่น้ำไหลเข้าเขื่อน … สัมพันธ์บวกกับน้ำที่ C.2 ที่ช่วงหน่วง 2 วัน (**0.44**)".

**Evidence:** `grep -rn "corrcoef\|pearsonr" analysis/ report/` → only `goal4_*` files. The values appear
**only as literal strings** at `report/goal6_build_report3_draft.py:306` and `:308`; the builder never
loads the C.2 series, and no script writes these numbers to any JSON. Repo rule (AGENTS.md) and the
review brief both require every reader-facing number to originate in a script-generated JSON.

**Fair note:** I *could* reproduce the values by hand from `data/22_goal6_network/raw/spike_ping_cp/`:

```
corr(release, C2)      = -0.917   (report: -0.92)
corr(inflow_lag2, C2)  = +0.438   (report:  0.44)
```

So the numbers are **not fabricated** — but they are unreproducible *by the repository*, which is
exactly the guarantee the project claims ("ทุกตัวเลขมาจาก JSON ที่สคริปต์สร้าง · builder ห้ามพิมพ์ตัวเลข").

**Fix:** add a small `goal6_c2_attribution.py` that emits these correlations (plus the release/inflow
series) to `analysis/goal6/ping_cp/l1_summary.json` (or a new JSON), and have the builder read them.

---

### H4 — HIGH — the entire C.2 "dam or rain?" chain table is hardcoded in the builder

**Evidence:** `report/goal6_build_report3_draft.py:311-316` — the table "การปล่อยน้ำเขื่อนรวม 20 → 7",
"P.17 … 166 (โต 20 เท่า)", "N.67 … 94–95", "รวมที่ C.2 … 224–226", "การปล่อยเขื่อนเหลือ 3%", and the
prose at `:304-309` ("226", "3%", "30%") are **plain string literals**. The builder's own docstring
(`:3`) says "อ่านข้อมูลจาก JSON ที่สคริปต์วิเคราะห์สร้างทั้งหมด (ห้ามพิมพ์ตัวเลขในโค้ด)". The builder
loads `goal6_spike_pasak.json` and `goal6_spike_maeklong.json` — it never loads the `spike_ping_cp`
raw files that hold these series.

This is the single most important analytical passage in report 3 (the answer to the headline question
"เขื่อนผิดหรือฝนผิด?"), and none of its numbers are machine-checkable.

**Fix:** move the C.2 chain (release, inflow, P.17/N.67/C.2 daily volumes) into a JSON emitted by a
script and render the table from it. Same for the TLDR flood-area literals at `:73` and the "2,264"
repeat at `:271` (those values happen to be correct — see "Checked OK" — but they are still literals).

---

### H5 — HIGH — the pre-release scenario is a linear extrapolation of a stage–volume curve to zero flow; "1.7–7.4 m" is an artefact of that extrapolation

**Claim (report 3 Q&A):** "ถ้าเพิ่มการปล่อยเป็น 40 … ลด ~1.7 ม. · 60 → ~4.5 ม. · 80 → ลด ~7 ม."
(and `HANDOFF.md`: "ปล่อยล่วงหน้า M2/M3 ลด C.2 1.7–7.4 ม. (40–100 ลลบ.ม./วัน × 4 วัน · R² 0.996)").

**Evidence:** `analysis/goal6_prerelease_scenario.py:39-43` fits `level = a + b·Q` on 39 September days.
The calibration range of `Q` (daily volume at C.2) is **49.9 – 225.5 ลลบ.ม./วัน** (source:
`data/22_goal6_network/raw/spike_ping_cp/c2_discharge_daily_sep2026.json`). The scenario `q_new` values are:

| scenario | peak_q_new | inside calibration range (49.9–225.5)? | drop_m |
|---|---|---|---|
| 40 | 165 | yes | 1.71 |
| 60 | 85 | **no** | 4.45 |
| 80 | 5 | **no** (10× below range) | 7.19 |
| 100 | **0** | **no** (no flow at all) | 7.37 |

Three of four scenarios are extrapolations below the fitted range; the 7.4 m headline comes from `Q = 0`,
which is not a physical state for a river (the intercept 16.73 m is the "level when no water flows").
A stage–volume rating curve is physically non-linear (stage rises steeply at high flow, flattens at low
flow), so a straight line fitted over a *narrow high-flow window* is the worst possible instrument for
extrapolating downward. `R² = 0.996` is a **within-range** fit statistic and provides no support for the
extrapolation. Compounding assumptions: all the "moved" water is assumed to reach C.2 1:1 (no routing,
no tributary dilution — but C.2 sits at the Ping/Wang/Yom/Nan confluence, so the dams are only part of
the flow) and none of it returns.

**Fix:** either restrict the scenario to the interpolated case (40 ลลบ.ม./วัน → 1.7 ม.), or replace the
linear fit with a monotone stage–volume relation over the full observed range, or clearly relabel the
4.5–7.4 m figures as "extrapolated beyond the data, not a prediction". Do not carry "1.7–7.4 ม." into
the policy sentence as if the endpoints were equally supported.

---

### H6 — HIGH — the L3 forecast re-introduces the exact look-ahead bug the repo documents, so the "+6/+24 h = 5–15 cm" skill claim is inflated

**Claim (report 3 TLDR / §basins):** "แบบจำลองทำนายระดับน้ำแม่นสุด **5–15 ซม. ที่ระยะ 6–24 ชม.** ใน 5 จาก 6 ลุ่ม".

**Evidence:** `analysis/goal6_l3_model.py:92-103`:

```python
def rain_at(daily, t):
    """R24/R72/R168 สะสมจบที่ t (ฝนวันนี้รวมชั่วโมง t ถือวัน t) ..."""
    days = [(t - timedelta(days=k)) ... for k in range(7)]
    r24  = days[0]          # <-- day OF t  (today), not yesterday
    r72  = nansum(days[:3]) # today + 2 previous
    r168 = nansum(days[:7]) # today + 6 previous
```

`days[0]` is the **current** day, so `r24` is the whole day's rainfall total — assigned to every hour of
that day. At 00:00 the model already knows the day's total rain, i.e. up to **~23 h of look-ahead**.

The repo already knows this is a bug and says so explicitly — `analysis/rain_window.py` (the shared
helper used by the canonical `goal4_model_v1.py`) documents it verbatim:

> "ถ้าคำนวณบนกริด 'รายชั่วโมง' ที่ฝนรายวันถูกทำซ้ำ 24 ช่อง → ช่อง 'เมื่อวาน' (t-24) มีฝนของ 'วันนี้'
> ปนอยู่ 23/24 ชั่วโมง → **ข้อมูลอนาคตรั่วเข้าโมเดลที่อ้างว่าเป็น forecast**"
> … "วิธีที่ถูก: รวมบนอนุกรม 'รายวัน' และรวมเฉพาะวันก่อนหน้าวันปัจจุบัน (D-n .. D-1)"

`goal4_model_v1.py` imports `windows_for_grid` and is leak-free. **`goal6_l3_model.py` bypasses it** and
hand-rolls the leaky version. Because the event is rain-driven and the test window is the rain event
itself, the leak flatters precisely the short horizons the report highlights. The reported ordering
(e.g. `ping_cp` +6 h: persistence 11.9 vs linear 4.7) is consistent with the linear model exploiting
future rain.

**Fix:** replace `rain_at` with `rain_window.day_window` / `windows_for_grid` (end windows at *yesterday*),
re-run all six basins, and re-state the accuracy claim from the corrected numbers. Flag this explicitly
if the numbers move.

---

### H7 — HIGH — report 4 says ป่าสัก exceeded its guide curve "17 of 22 years"; the JSON says 20

**Evidence:** HTML `report/ชุดเทียบมาตรฐาน2554.html` line 63: "ป่าสักเกิน **17 จาก 22 ปี**".
`analysis/goal6/dam_history_all.json` → ป่าสักชลสิทธิ์ `years` with `days_over_urc > 0` = **20 of 22**.
(Compare the matching sentence in `analysis/goal6_l1_followups.py:150-151`, which still says
"เกินกลางหน้าฝน 17/22 ปี".)

This is a builder-hardcoded number that disagrees with the source JSON — the brief's own rule ("mismatch = HIGH").

**Fix:** render the count from `dam_history_all.json` (`sum(1 for y in years if y['days_over_urc']>0)`)
instead of typing it, and correct the `l1_followups.py` verdict string too.

---

### M8 — MED — report 4's per-basin rain table is hardcoded and its ป่าสัก row is wrong

**Evidence:** `report/goal6_build_report4_draft.py:116-124` hardcodes the table
(`["ป่าสัก", "20", "15"]` etc.). Computed medians from `analysis/goal6/rain_rarity_2554.json`
(`best7.rank54` / `best7.rank26`, per basin):

| basin | report | computed median |
|---|---|---|
| ปิง / วัง / ยม | 6 / 5–10 | 6 / 3.5–10 ✓ |
| เจ้าพระยา | 13 / 1 | 13 / 1 ✓ |
| **ป่าสัก** | **20 / 15** | **16.5 / 13.5** ✗ |
| ชายฝั่งทะเลตะวันออก | 3 / 1 | 3 / 1 ✓ |
| บางปะกง | 30 / 1 | 30 / 1 ✓ |
| แม่กลอง | 39 / 1 | 39 / 1 ✓ |
| ท่าจีน | 37 / 1 | 37 / 1 ✓ |
| ใต้ฝั่งออก/ตก | 11–24 / 19–44 | 11–24 / 19–44 ✓ |

Every other row matches, so the table was clearly *derived* — but it is typed in, and the ป่าสัก row
disagrees with its own caption ("อันดับกลาง" = median). **Fix:** emit the table from the JSON (median
per basin), or correct ป่าสัก to 16.5 / 13.5.

---

### M9 — MED — "+48 h all models collapse equally, in every basin" is not what the data show

**Claim:** `HANDOFF.md` and `docs/GOAL6_PLAN.md`: "**+48 ชม. พังพอกันทุกลุ่ม** = ข้อค้นพบนครนายกถือข้ามลุ่ม";
report 3: "ระยะเกิน 48 ชม. แม่นยำไม่ได้ทุกลุ่ม".

**Evidence:** the six `analysis/goal6/<basin>/l3_model.json` files, RMSE at +48 h:

| basin | persistence | linear | GBDT |
|---|---|---|---|
| pasak | 148.7 | 150.9 | 158.9 |
| maeklong | 35.2 | 31.1 | 33.6 |
| bp_prach | 95.5 | 91.8 | **67.0** |
| thachin | **23.8** | 25.9 | 38.9 |
| ping_cp | 75.7 | 70.1 | **58.3** |
| bkk_lower | 112.6 | **77.9** | 94.2 |

The models do **not** collapse equally: in bp_prach, ping_cp and bkk_lower one model clearly beats the
others by 25–35 cm; in maeklong (31–35 cm) and thachin (24–39 cm) the errors are moderate, not a
"collapse". Only pasak looks like a genuine +48 h breakdown. **Fix:** state the actual pattern
("accuracy degrades sharply with lead time; at +48 h it is unusable in pasak/bkk_lower, still
moderate in maeklong/thachin") rather than a blanket "all fail together".

---

### M10 — MED — EVENT/SUSPECT: the criterion only catches *whole-record* mismatches, and one EVENT station carries the SUSPECT signature; the stated justification is wrong for 3 of 18

**Criterion (code, `goal6_screen_findings.py:25`):** `SUSPECT if hours_over_crit == n_values and longest_run == n_values`
— i.e. the level is above the threshold for the **entire** record. That is a sound *sufficient* test,
but not a necessary one.

**Evidence A — likely misclassification:** B.10 (ตลาดท่ายาง, เพชรบุรี-ประจวบคีรีขันธ์) is classed **EVENT**,
but its raw series (`data/22_goal6_network/raw/wl_screen_2026/2671_B.10.json`) runs 5.68–9.44 m while
its `meta.min_bank = 13.90` → `max_vs_minbank = −4.46`. That is the *same* datum-mismatch signature the
report uses to justify SUSPECT (max below the station's own lowest bank); B.10 escapes only because the
mismatch is partial (291 h of 2230), not total. So the headline "25 over critical → only 7 usable" is
probably "6 usable".

**Evidence B — the stated justification is inaccurate:** report 3 / findings §1 say the SUSPECT group
"ระดับสูงสุดต่ำกว่าตลิ่งต่ำสุดของจุดตัวเอง (max − min_bank เป็นลบเกือบทั้งหมด)". Computed from
`goal6_screen_2026_summary.json`, **3 of the 18** SUSPECT stations have a *positive* gap:
K.10 +6.45, K.37 +0.42, P.17 +0.14 (15 negative, 3 positive). The word "เกือบทั้งหมด" is doing a lot of
work; the classification is still right for those three (their series sits entirely above the threshold),
but the sentence as written is false for them.

**Fix:** (a) add a second SUSPECT test for partial datum mismatch (e.g. `max_val < meta_min_bank` when
`meta_min_bank` is present) and re-check B.10; (b) rewrite the justification to "the criterion is
'series above threshold for the whole record'; 15 of 18 also have max below their own lowest bank".

---

### M11 — MED — the automated banned-word checker `thai()` is dead code; the deployed test checks 15 of ~37 terms, and a live violation survives

**Claim (brief §5, `goal6_reportlib.py:7`):** "เนื้อหาผ่าน `thai()` ตรวจคำต้องห้ามอัตโนมัติทุกครั้งที่สร้างรายงาน …
สร้างรายงานไม่ผ่าน = หยุด".

**Evidence:** `grep -rn "thai(" report/ tests/` returns **only** the definition and comments — `thai()`
is never imported or called by any builder, and `page()` does not invoke it. The real enforcement is
`tests/test_report3_language.py`, whose local `BANNED` list has 15 entries vs the 37 in `BANNED_TERMS`.

Scanning both drafts against the **full** `BANNED_TERMS` list (reader text, `<style>`/`<code>`/tags
stripped) finds a live violation the test misses:

```
report/ระลอกปลายกย2569_6ลุ่ม.html  →  'การแยกส่วนสาเหตุ': 3   (should be "การแยกส่วนของสาเหตุ")
```

**Fix:** call `thai()` on the assembled body in `page()` (or in each builder) so the build actually
fails, and replace the three occurrences.

---

### M12 — MED — report 3 generalizes a single-dam URC cross-check to all 24 dams, and drops the template caveat the findings file carries

**Evidence:** report 3 §dams says the guide curves are "ยืนยันแล้วว่าเป็นเส้นจริงด้วยการไขว้ **5,025 แถว**
ต่าง 0.0" — presented as validation of the whole table. That cross-check (`goal6_l1_followups.py:51-69`,
`khundan_template_vs_csv`) covers **ขุนด่าน only** (the 5,025 rows are the ขุนด่าน CSV). Meanwhile
`goal6_screen_2026_findings.md:9` warns that the API guide curve is "เทมเพลตแหล่งเดียว (ลงวันที่ปี 2020
แบบรายเดือน-วัน)" and that the EGAT "0 days" conclusions still need the official กฟผ. curves — but the
word "เทมเพลต" appears **0 times** in report 3, so that caveat never reaches the reader. Given H1, this
caveat matters.

**Fix:** narrow the sentence to "ยืนยันกับเขื่อนขุนด่านปราการชล (ไขว้ 5,025 แถว)" and carry the
template/single-source caveat into report 3's limitations.

---

### M13 — MED — the Bangkok 1,200 km² sea mask uses OR where the docstring says AND, and DEM<1.2 m is not a coastline

**Evidence:** `analysis/goal6_bkk_sea_mask.py:43` → `sea_mask = (permanent_water | low_dem) & lowland`
(OR), while the module docstring (`:5-7`) says "ผสมสองเกณฑ์: (น้ำถาวรสถิติ) **AND** (พิกัดต่ำกว่าแนวชายฝั่ง
จาก DEM < 1.2 ม.รทก.)". The OR is far more aggressive: `dem < 1.2` deletes *all* low-lying land, not sea.
Result: 1320.8 → 1199.8 km² (`analysis/goal6/bkk_lower/l2_sea_adjust.json`). This also sits awkwardly
with the declared limitation that "DEM กทม. ใช้เชิงคุณภาพเท่านั้น" — a quantitative 1.2 m cut is not a
qualitative use. Attackers will say 1,200 under-counts flood (it deletes inhabited low ground) or that
the number is unfalsifiable.

**Fix:** pick one criterion (permanent-water is the defensible one), fix the docstring/code mismatch,
and report the number as "flood area excluding permanent water and land below 1.2 m (lower bound)".

---

### M14 — MED — "67 of 199 stations" is 32 of 99 grid cells; the declared limitation is honest but the headline stays undeduped

**Computed as requested (brief §A1).** NASA POWER is MERRA-2 on a **0.5° × 0.625°** grid (the 0.625° lon
step is confirmed: grouping the 199 stations at 0.5°×0.625° gives 99 cells with **0** cells containing
differing values; 0.5°×0.5° gives 15 non-identical cells):

```
199 stations → 99 unique grid cells
67 stations ranking top-3 (7-day) → 32 unique cells     (≈32/99 = 32%)
66 stations ranking top-3 (30-day) → 36 unique cells
```

So the *proportion* is roughly right (~34% of stations, ~32% of cells) but the **count is inflated ~2.1×**:
"67 จุด" is not 67 independent locations. This **is** declared in report 3's limitations ("ตัวเลข '67 จาก 199 จุด'
จึงนับจุดวัด ไม่ใช่นับช่องกริด"), so I am not treating it as a new error — but the declared limitation
gives no dedup figure, and the TLDR still leads with "67 จาก 199". **Fix:** add "= 32 จาก 99 ช่องกริด"
to the headline or the limitation.

---

### M15 — MED — the flood-duration maps are absent from report 3, and use a different water definition than the flood-area numbers

**Evidence:** `HANDOFF.md:90` lists "**แผนที่ระยะเวลาน้ำค้าง 6 ลุ่ม** (duration_maps …)" among report 3's
deliverables, but `grep -c "น้ำค้าง\|duration" report/ระลอกปลายกย2569_6ลุ่ม.html` = **0**, and the
builder has no `figure()` call for them. Separately, `goal6_duration_maps.py:19` defines water as
**absolute** `VH ≤ −20 dB`, whereas the flood-area numbers use the **Δ** rule — so the two artifacts
measure different things and must not be read together without a note. (The script's own header
acknowledges this.)

**Fix:** either add the duration maps with an explicit "หยาบ — ฉากห่าง 1–3 วัน · ใช้เกณฑ์น้ำรวมคนละชุดกับ
พื้นที่น้ำท่วม" caption, or remove them from HANDOFF's report-3 deliverable list.

---

### L16 — LOW — un-glossed acronyms in reader-facing tables

`URC` (7×), `RMSE` (12×), `MAE` (6×) appear in report 3 tables with no gloss, and none is in the
definitions table (§0). `URC` is explicitly on the repo's replace-list ("เส้นกำกับระดับน้ำบน"). The
rest of the loanword substitution is genuinely well done (GBDT → แบบจำลองต้นไม้, persistence →
ค่าเดิมคงที่, linear → สูตรเส้นตรง — all 0 Latin occurrences). **Fix:** replace URC in table headers,
and add a one-line gloss for RMSE/MAE.

### L17 — LOW — report 4 shows the EGAT positive but not the RID positive

The legal rule (`AGENTS.md`) requires an agency's positive side to be shown alongside criticism. Report 4
criticises irrigation dams (ป่าสัก 241 วัน, ภูมิพล 127 วัน) but the only "positive" shown belongs to
EGAT. The irrigation mitigation ("เพราะต้องเก็บไว้ใช้ชลประทาน") is a justification, not a positive.
**Fix:** add one sentence on the RID dams' flood-mitigation role.

### L18 — LOW — the −0.92 correlation does not support "releases were NOT the cause"

Even when reproduced (H3), this is a period correlation between two rainfall-driven series where the
dam's operational pattern (hold during peak inflow, release afterwards) mechanically produces the
negative sign — a confounded statistic, not evidence of non-causation. The report's *physical* argument
(release fell while inflow and C.2 rose) is the sound one. **Fix:** demote the correlation to a
supporting observation or drop it.

---

## What I checked and found OK

- **`python -m pytest tests/ -q` → 39 passed** (brief §2 claim of 39/39 holds).
- **Flood areas match their source JSON.** `data/22_goal6_network/derived/s1_stage2/summary.json`:
  ping_cp 2263.6, bp_prach 1281.6, pasak 521.0, thachin 160.4, maeklong 73.0 → reports 3/4 TLDRs
  (2,264 / 1,282 / 521 / 160 / 73) are correct; bkk_lower 1320.8 → 1,199.8 after sea mask → 1,200 correct.
- **Cross-file anchors are consistent** across `HANDOFF.md`, `START_HERE.md`, `docs/GOAL6_PLAN.md`
  for 67/199, 2,264, 1,200, 521, 73, 224.34. 452.1 correctly stays out of reports 3/4 (it belongs to
  reports 1–2). GOAL6_PLAN's "30 วัน = 66/199" checks out.
- **Per-basin "all stations top-3" claims verified**: บางปะกง 11/11 · แม่กลอง 11/11 · เจ้าพระยา 9/9 ·
  ท่าจีน 4/4 · สะแกกรัง 4/4 (from `rain_rarity_national.json`).
- **L3 best-model numbers in GOAL6_PLAN match** the six `l3_model.json` files (4.7 / 8.6 / 7.6 / 14.9 /
  14.1 / 24.6 at +6 h) — the numbers are right even though the rain features are leaky (H6).
- **2569 dam over-URC counts consistent**: findings §4 lists 9 dams over, four at 39 days — matches
  `dam_history_all.json` and report 4's TLDR.
- **Pre-release inputs are real data** (`c2_vs_dam_releases_sep2026.json`, `c2_discharge_daily_sep2026.json`
  exist and match the builder's narrative); the problem is the extrapolation (H5), not the inputs.
- **Report 3 self-sufficiency / structure**: TLDR ("สรุปสั้น (อ่าน 2 นาที)"), context block, definitions
  table, TOC, and Q&A section are all present and match the AGENTS.md report contract.
- **PDPA**: no phone numbers, emails, `นาย/นาง/คุณ <name>`, or social handles in reports 3/4.
- **Defamation framing**: report 3 criticises systems ("ระบบบริหารเขื่อนต่างกันจริง"), names no
  individuals, cites the data source for each dam claim, and praises the EGAT dams that performed well.
  (Report 4's gap is L17, not a framing failure.)
- **Water-rule design is sound in principle**: change detection on same-orbit pairs cancels static
  radar shadow (Δ≈0), which is the right choice for the shadow concern; the calibration itself is
  documented and versioned in `s1_change_detect.py`.

---

## My review's own limitations

- **I did not re-run the network-dependent pipelines** (`goal6_screen_basins.py`, `goal6_rain_rarity_*.py`,
  `goal6_s1_*`, `goal6_l3_model.py`) — they call the live thaiwater API / NASA POWER and need the 42.8 GB
  S1 COG cache plus rasterio/geopandas/scikit-learn. All my checks are re-derivations from the committed
  JSON/HTML/raw files, which is why H1/H2/H5/H7/M8/M9/M10/M14 are stated as exact recomputations rather
  than re-runs.
- **The satellite flood areas (2,264 / 1,282 / 1,200 / 521 / 160 / 73) are therefore NOT independently
  reproduced.** I verified only that they match `summary.json`; I did not re-run stage-1/2 or inspect the
  rasters, so I cannot speak to the per-basin water masks beyond the design issues in section B.
- I did **not** open the GISTDA shapefile or re-verify the F1=0.727 calibration; I take that from
  `s1_change_detect.py`'s docstring.
- I did **not** audit reports 1–2 (published) except where 3/4 inherit from them; H6 in particular is
  scoped to `goal6_l3_model.py` — the canonical `goal4_model_v1.py` uses the correct helper and is not
  implicated.
- I read Thai and reviewed language, but my banned-term scan is regex-based (it can miss inflected or
  split forms) and I did not proof-read every sentence of the two drafts.
- For H3 I reproduced the correlations by hand; I did **not** establish that the builder's *intended*
  series was exactly mine (e.g. which date alignment the author used), only that the values are
  obtainable from the committed raw files.
- I did not verify the `dam_history_all.json` values against the thaiwater API directly — I take the
  JSON as the source of truth, consistent with the repo's own rule.
