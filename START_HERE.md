# START HERE — โครงการน้ำท่วมนครนายก 2569

> อ่านไฟล์นี้ **ก่อน** อย่างอื่น ถ้าเพิ่งเปิดโปรเจกต์นี้ครั้งแรก
> ตอบ 3 คำถาม: โปรเจกต์นี้คืออะไร · เริ่มอ่านตรงไหน · รันตัวเลขเองอย่างไร
>
> **สถานะล่าสุด + งานค้าง:** ดู `HANDOFF.md` (สถานะส่งมอบ 8 ต.ค. 69 — publish แล้ว: github.com/tkittich/nnyflood)

---

## 1. นี่คืออะไร (30 วินาที)

การสอบสวนเชิงหลักฐาน (forensic) ของน้ำท่วม **อ.เมือง นครนายก ปลาย ก.ย. 2569** —
บทบาทของ **ฝนตกหนักเป็นแถบ** เทียบกับ **การบริหารน้ำของเขื่อนขุนด่านปราการชล (สช.9, dam_id 32)**

5 เป้าหมาย: (1) คลังหลักฐานระดับอ้างอิง · (2) วิเคราะห์สาเหตุ+มาตรฐานการบริหาร ·
(3) ปริมาณผลกระทบ ฝน vs น้ำปล่อย · (4) โมเดลทำนายระดับน้ำ + สถานการณ์บริหาร ·
(5) ข้อเสนอแนะต่อภาครัฐ: ควรแก้ไข/เพิ่มเติมส่วนใดเพื่อให้การบริหารจัดการน้ำมีประสิทธิภาพขึ้น —
แยกสิ่งที่ทำได้เลยไม่ต้องใช้เงิน vs ต้องลงทุน (`analysis/goal5_policy_proposals.md`)

**จุดยืนบังคับ: เป็นกลางตามหลักฐาน** — ผลออกทางไหนก็ได้ · ทุกตัวเลขสำคัญมีแหล่งอ้างอิงกำกับ

---

## 2. ติดตั้ง / ตรวจสุขภาพ (2 นาที)

```bash
cd <โฟลเดอร์ repo>

# Python 3.11+ ที่มีในเครื่อง (เครื่องที่ใช้พัฒนา: CPython 3.14.5 — สภาพแวดล้อมเต็ม: docs/ENVIRONMENT.md)
PY=python

"$PY" -m pip install -r requirements.txt
"$PY" -m pytest tests/ -q                        # ต้องได้: 29 passed
"$PY" analysis/verify_data_integrity.py --quick # ต้องได้: MISMATCH 0 (MISSING = ไฟล์ใหญ่นอก git)
```

- สคริปต์ทั้งหมด derive path จาก `Path(__file__)` แล้ว → **รันจากโฟลเดอร์ไหนก็ได้**
  (ไม่ต้อง cd ไปที่รากโปรเจกต์ก่อน)
- ไลบรารีต้องปักหมุดตาม `requirements.txt` — ตัวเลข RMSE ของโมเดลขยับตามเวอร์ชัน
  ของ scikit-learn/numpy · อัปเกรดเมื่อไรให้รันเทสต์เทียบ `goal4_model_v1_results.json` ก่อน

---

## 3. ลำดับการอ่าน (canonical reading order)

| # | ไฟล์ | อ่านเพื่อ |
|---|---|---|
| 1 | `README.md` | ขอบเขตงาน (เริ่มที่นี่เสมอ) |
| 2 | `docs/METHODS.md` | มาตรฐานหลักฐาน (`[F]/[I]/[O]`, datum, rating curve) |
| 3 | `docs/DATA_DICTIONARY.md` | **ค่าที่เป็นทางการ** ของทุกตัวเลขที่โต้แย้ง (น้ำสูงสุด, ระยะเวลา, พื้นที่) |
| 4 | `docs/ANALYSIS_PLAN.md` | แผนวิเคราะห์ 5 เป้าหมาย + ช่องว่างที่เหลือ |
| 5 | `docs/DATA_SOURCES.md` | แหล่งข้อมูล + สถานะการเข้าถึง |
| 6 | `analysis/*_findings.md` | รายละเอียดเชิงลึกแต่ละหัวข้อ (ดูตาราง §4) |
| 7 | `report/*.html` | **ชิ้นงานส่งมอบ** — ฉบับประชาชน (หลัก) + ฉบับวิชาการ (ตรวจสอบได้) |

**ไฟล์ findings ที่สำคัญ** (เรียงตามความสำคัญ):

- `analysis/khundan_tele_findings.md` — datum Ny.7, rating curve, สัดส่วนเขื่อน/ฝน
- `analysis/s1_flood_extent_findings.md` — แผนที่ช่วงสูงสุด 452 ตร.กม. + การสอบเทียบกับ GISTDA
- `analysis/goal4_model_v1_findings.md` — โมเดลทำนาย + วินิจฉัยฟีเจอร์ฝน (หน้าต่างรายวัน กันข้อมูลอนาคตรั่ว)
- `analysis/goal4_counterfactual_model_vs_nomodel.md` — สถานการณ์บริหาร R1/M1–M4
- `analysis/rid_cross_section_findings.md` — รูปตัดขวางจริง + ตรวจไขว้ BANKFULL
- `analysis/all_stations_goals.md` — **ขยายเป็นทุกจุดวัด**: ผลต่อ 4 วัตถุประสงค์ (เหมือนเดิม/ต่าง/ติดอะไร)
- `analysis/all_stations_network.md` — ความสามารถ + คุณภาพข้อมูลราย 19 จุด + ตาราง Δ แบบ 2 คอลัมน์
- `analysis/thachang_leadtime.md` — ทดสอบว่าท่าช้างทำนายได้ไหม (ช่วงเหตุการณ์เดียว)
- `analysis/goal4_thachang_model.md` — ทดสอบหลายฤดู → ท่าช้าง **ทำนายจาก Ny.7 ไม่ได้** (ΔNy.7 ยุบ 0.173→0.002)

---

## 4. ทำซ้ำตัวเลขหัวใจ

### 4.A — ทำซ้ำได้จาก clone เปล่า (อินพุตทั้งหมดอยู่ใน git)

รันทีเดียวจบ (pipeline ครบ — ขั้นที่ต้องมีข้อมูลดิบใหญ่จะ SKIP อัตโนมัติ):
```bash
"$PY" analysis/run_all.py        # หรือ --fast เพื่อข้าม backtest ยาว (~25 นาที)
```

หรือรันทีละขั้น:

```bash
"$PY" analysis/goal4_model_v1.py
#   -> analysis/goal4_model_v1_results.json  (ตาราง RMSE 11 ตัวแปร vs persistence/GBDT)
#   -> analysis/goal4_linear_coeffs_full.json, goal4_model_v1_ablation.json
#   -> analysis/goal4_model_v1_event.png, report/assets/m_simple24.png

"$PY" report/make_x_charts_thai.py
#   -> report/assets/x1_rating.png, x2_hydro3.png  (กราฟ rating/ไฮโดร 3 สถานี ภาษาไทย)

"$PY" analysis/goal4_counterfactual_model.py
#   -> analysis/goal4_counterfactual_summary.json  (R1/M1–M4 + envelope ความไม่แน่นอน ±18 %)
#   -> analysis/goal4_counterfactual_model.png

"$PY" analysis/qa5_rain_drainage_counterfactual.py     # พิมพ์อย่างเดียว ไม่เขียนไฟล์

"$PY" analysis/hecras_lite_channel.py
#   -> analysis/river_cross_sections.json   (ภาคตัดขวาง DEM 9 เส้น)

"$PY" analysis/rid_cross_section_extract.py            # ต้องมี .xlsx ดิบใน data/19 (อยู่ใน git)
"$PY" analysis/rid_cross_section_hydraulics.py
#   -> data/19_rid_cross_sections/derived/cross_section_hydraulics.json
"$PY" analysis/rid_cross_section_plot.py
#   -> analysis/rid_cross_section_ny7.png
```

### 4.B — ต้องมีข้อมูลดิบบนดิสก์ (ไม่เข้า git — ดู §6)

```bash
"$PY" analysis/s1_process.py          # geocode + calibrate ฉาก S1 ดิบ -> derived/*.npy/.tif
"$PY" analysis/s1_change_detect.py    # -> derived/flood_peak_27sep1828.npy, flood_2oct_validated.npy
"$PY" analysis/s1_peak_flood_map.py   # -> analysis/s1_peak_flood_map_27sep1828.png  (น้ำสูงสุด 452 ตร.กม.)
```

> ⚠️ `data/13_sentinel1_copernicus/` เก็บเฉพาะ `manifest.md` ใน git — ฉากดิบ 17 ฉาก (~21 GB)
> และกริด `derived/` อยู่บนดิสก์เท่านั้น · **clone เปล่าทำซ้ำ §4.B ไม่ได้** จนกว่าจะมีฉากดิบ
> (มี SHA-256 ครบใน manifest ให้ตรวจ)

### 4.C — สร้างรายงานทั้งสองฉบับใหม่

```bash
"$PY" report/report_assets.py           # สร้าง/คัดลอกภาพทั้งหมดลง report/assets/
"$PY" report/build_expert_report.py     # -> report/น้ำท่วมนครนายก2569_วิชาการ.html
"$PY" report/build_report_html.py       # -> report/น้ำท่วมนครนายก2569_ประชาชน.html
```

> ลำดับสำคัญ: `report_assets.py` ต้องรันก่อน · `build_*_report.py` อ่านรูปจาก `report/assets/`
> เท่านั้น และจะเตือน (`!! ขาด ...`) ถ้าภาพที่ analysis เป็นเจ้าของยังไม่ถูกคัดลอก

---

## 5. ตัวเลขที่ควรได้ (sanity check)

รัน §4.A แล้วเทียบกับค่าที่บันทึกใน `docs/DATA_DICTIONARY.md`:

| ปริมาณ | ค่าที่เป็นทางการ | ที่มา |
|---|---|---|
| น้ำสูงสุดระดับน้ำ Ny.7 | **9.23 ม. เกจ = 7.64 ม.รทก. ±0.05** | thaiwater (9.23) · khundan-tele (7.68 รทก.) — ต่างกัน ≤5 ซม. |
| ระยะเวลาเหนือตลิ่ง | **65 ชม.** | thaiwater ขาด 3 แถวเที่ยงคืน · khundan ยืนยัน |
| พื้นที่น้ำท่วมน้ำสูงสุด 27 ก.ย. 18:28 | **452 ตร.กม.** | ประมวลผล S1 เอง (GISTDA ไม่ได้ทำ pass นี้) |
| BANKFULL | **6.86 ม.รทก. = เกจ 8.45 ≈ Q 420–425** | ตรวจไขว้กับหน้าตัดจริงแล้ว |
| สัดส่วนเขื่อน : ฝน (ช่วงเริ่มท่วม) | **12 % : 88 %** | `khundan_tele_findings.md` |
| โมเดล Ny.7 RMSE เหตุการณ์ (+6/+24/+48 ชม.) | **สูตร 30.0/117.6/163.7 · persistence 30.6/101.8/170.4 · GBDT 127.7/159.8/140.6 ซม.** | `goal4_model_v1_results.json` (สร้างใหม่ด้วยสคริปต์ — มีเทสตรงค่าใน tests/) |
| M4 ระบายล่วงหน้า 5.2 ลลบ.ม. | **ระดับสูงสุดลด ~1 ซม.** (บนที่ราบ 452 ตร.กม.) | `goal4_counterfactual_model.py` |
| Manning n ที่สอดคล้อง rating curve | **0.0437** (ปกติที่ราบลุ่ม) | `rid_cross_section_stage_rating.md` |

---

## 6. แผนผัง: อะไรอยู่ใน git อะไรอยู่บนดิสก์

**อยู่ใน git** (ตรวจสอบย้อนได้): สคริปต์ · ผลวิเคราะห์ JSON/CSV/PNG · รายงาน HTML ·
`manifest.md` ทุกโฟลเดอร์ · ข้อมูลโทรมาตรที่จัดระเบียบแล้ว (`data/01`, `02`, `16`, `19` ฯลฯ)

**อยู่บนดิสก์เท่านั้น** (มี SHA-256 ใน manifest): ฉากดาวเทียมดิบ (`*.zip/*.kmz`),
DEM ต้นฉบับ, PDF/ภาพสแกน, อัลบั้มภาพ, กริด `derived/` ของ S1, SAFE ที่แตกแล้วของ S2

> เหตุผล: git ไม่ใช่ backup ของไฟล์หลาย GB — นโยบายอยู่ใน `.gitignore` (หัวไฟล์)

---

## 7. กับดักที่เจอจริง (อย่าเสียเวลาซ้ำ)

1. **ฟอนต์ไทยใน matplotlib** — ต้องตั้งทุกสคริปต์ที่วาดกราฟ ไม่งั้นได้กล่องสี่เหลี่ยม:
   `plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma"]`
2. **CRLF ของ Windows** ทำ SHA-256 ของไฟล์ดิบเพี้ยน แม้เนื้อหาเหมือนเป๊ะ —
   เทียบ hash หลัง normalize `\r\n`→`\n` ก่อนสรุปว่า restore ล้มเหลว
3. **`import pyshp` ล้มเหลว** — แพ็กเกจชื่อ `pyshp` แต่ import ด้วย `import shapefile`
4. **Sentinel-2 tile** — ที่ราบนครนายกคือ **47PQR** · `47PPS` = สระบุรี (ผิดไทล์) —
   ยืนยันด้วย point-query CDSE ที่ 101.22/14.20 อย่าเชื่อชื่อ tile จากการเดา
5. **`git checkout` ไม่ re-include ไฟล์ที่โฟลเดอร์แม่ถูกตัด** — ต้องเขียน `data/manual/*`
   ไม่ใช่ `data/manual/` แล้วค่อย `!data/manual/manifest.md`
6. **`georef_corner_match.py`/`georef_fit.py` ต้องมี `opencv`** (ไม่อยู่ใน `requirements.txt`) —
   เป็นการทดลองที่**ล้มเหลว** (median 55.7 px) · **georeference สำเร็จทางอื่น**: `georef_gistda.py`
   อ่าน graticule ตรง ๆ → **median 0–1 px** — ผลลัพธ์ที่ใช้ได้อยู่ใน
   `analysis/gistda_georef_findings.md` + `analysis/gistda_georef_compare.py`

---

## 8. งานที่ยังเปิดอยู่

- **FOI / ต้องมีมนุษย์:** ระเบียบ กช. การระบายน้ำ · ตารางเปิดบานรายชั่วโมง สช.9 ·
  นิยาม Outflow กราฟโครงการ (+37 ลลบ.ม.) · benchmark datum Ny.1B/Ny.7 · Flood Hub API key
- **วิเคราะห์:** HEC-RAS 1D (แทน lumped model) · ขยายภาคตัดขวาง Ny.7 ด้วย Copernicus DEM ·
  ใส่ error bar ให้สัดส่วน 12 % : 88 % · ไขปริศนา Ny.1B Q = 668.6 ม³/วิ
- **ทุกจุดวัด (ครบแล้ว):** raw+แฮชครบ (`data/20_multistation_levels/`) · เครือข่ายรายจุด ·
  ผลต่อ 4 วัตถุประสงค์ · ทดสอบทำนายท่าช้าง (หลายฤดู — **ทำนายไม่ได้**) ·
  เหลือ: **rating curve คลอง** (วต.2) + **routing** (วต.4) + **FOI ตารางบาน** (ก้าวถัดไปที่แท้จริง)
  ดู `analysis/ALL_STATIONS_IMPLEMENTATION_PLAN.md`
- **ข้อมูล:** ⚠️ **datum 9 จุดเปลี่ยนกลางเดือน** (16–21, 26, 30, 84) — ต้องจัดการก่อนดึง 5 ปี
- **ข้อมูล:** PQR ซ้ำกับ SAFE ที่แตกแล้ว (~2.9 GB) เสนอลบไว้ใน `data/manual/manifest.md` (ยังไม่ลบ)

---
