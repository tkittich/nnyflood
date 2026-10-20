# START HERE — โครงการน้ำท่วมนครนายก 2569 และการขยายผลระดับชาติ

> อ่านไฟล์นี้ **ก่อน** อย่างอื่น ถ้าเพิ่งเปิดโปรเจกต์นี้ครั้งแรก
> ตอบ 3 คำถาม: โปรเจกต์นี้คืออะไร · เริ่มอ่านตรงไหน · รันตัวเลขเองอย่างไร
>
> **แผนผังและแคตตาล็อกระบบฉบับเต็ม:** ดู [docs/PROJECT_MAP.md](docs/PROJECT_MAP.md) (ค้นหาทุกเรื่อง/โค้ด/ตัวเลข)
> **สถานะล่าสุด + งานค้าง:** ดู `HANDOFF.md` · publish เป้าหมาย 1–5: github.com/tkittich/nnyflood

---

## 1. นี่คืออะไร (30 วินาที)

คลังข้อมูลและการสืบสวนเชิงหลักฐาน (forensic investigation) ด้านอุทกวิทยาและการบริหารจัดการน้ำ ครอบคลุม **3 เสาหลัก 7 เป้าหมาย**:

1. **เสาที่ 1: ลุ่มน้ำนครนายก (เป้าหมาย 1–5)** — บทบาทของ **ฝนตกหนักเป็นแถบ** เทียบกับ **การบริหารน้ำของเขื่อนขุนด่านปราการชล** ในเหตุการณ์น้ำท่วม 26–29 ก.ย. 2569 พร้อมแบบจำลองทำนายระดับน้ำ (Model v1) และข้อเสนอนโยบาย
2. **เสาที่ 2: 6 ลุ่มน้ำทั่วประเทศ & เทียบปี 2554 (เป้าหมาย 6)** — ขยายระเบียบวิธีสู่ 6 ลุ่มน้ำทั่วประเทศ, พฤติกรรม 24 เขื่อนใหญ่ (กฟผ. vs ชลประทาน), สถิติฝนรอบ 46 ปี, และชุดเทียบมาตรฐานปี 2554 vs 2569
3. **เสาที่ 3: คลองระบายน้ำหลากเจ้าพระยา 2 (เป้าหมาย 7)** — การตรวจสอบโครงการคลองชัยนาท–ป่าสัก–อ่าวไทย (111 กม.), สาเหตุคันคลองสูง 3.2–4.8 ม., ท่อลอด/ไซฟอนตัดคลองเดิม 34 จุด, อาคารบังคับน้ำ 99 แห่ง, และการประเมินผลกระทบต่อ อ.องครักษ์

**จุดยืนบังคับ: เป็นกลางตามหลักฐาน** — ผลออกทางไหนก็ได้ · ทุกตัวเลขสำคัญมีแหล่งอ้างอิงกำกับ · ห้ามพิมพ์ตัวเลขเป็น literal

---

## 2. ติดตั้ง / ตรวจสุขภาพ (2 นาที)

```bash
cd <โฟลเดอร์ repo>

# Python 3.11+ ที่มีในเครื่อง (เครื่องที่ใช้พัฒนา: CPython 3.14.5 — สภาพแวดล้อมเต็ม: docs/ENVIRONMENT.md)
PY=python

"$PY" -m pip install -r requirements.txt
"$PY" tools/verify_all.py                        # ตรวจสอบระบบครบวงจร (catalog + SHA-256 + pytest 162 passed)
# หรือแยกรันรายคำสั่ง:
"$PY" catalog.py check                           # ตรวจสารบัญไฟล์ (111 รายการ)
"$PY" catalog.py audit                           # ตรวจย้อนกลับ: เอกสารที่ root/docs ลงทะเบียนครบไหม (33/33 ไฟล์)
"$PY" analysis/verify_data_integrity.py --quick  # ตรวจ SHA-256 (MISMATCH 0)
"$PY" -m pytest tests/ -q                        # ตรวจเทสต์ทั้งหมด (162 passed)
```

- สคริปต์ทั้งหมด derive path จาก `Path(__file__)` แล้ว → **รันจากโฟลเดอร์ไหนก็ได้**
- ไลบรารีต้องปักหมุดตาม `requirements.txt` — ตัวเลข RMSE ของโมเดลขยับตามเวอร์ชันของ scikit-learn/numpy
- **เครื่องมือสืบค้นเร็ว**: ใช้ `python catalog.py find <คำค้น>` หรือ `python catalog.py goal <1..7>` เพื่อค้นหาไฟล์และตัวเลขได้ทันที — ค้น 2 ชั้น: สารบัญ (ไฟล์/ฟังก์ชัน/เอกสาร) แล้วต่อด้วยดัชนีเนื้อหาเต็ม Mini-FTS (`tools/mini_fts.py --reindex` เมื่อมี OCR หรือเอกสารใหม่)
- **สถานะล่าสุด (20 ต.ค. 69)**: ดู `HANDOFF.md` ส่วนบนสุด — DEM 5 ม./ขอบน้ำเรดาร์/หนังสือ คชก./นำร่อง VLM

---

## 3. ทางด่วนการอ่านตามกลุ่มผู้ใช้ (3 Persona Tracks)

เลือกเส้นทางการอ่านที่ตรงกับเป้าหมายของท่าน:

### 👤 ลู่ที่ 1: ผู้อ่านทั่วไป / สื่อมวลชน (Reader & Media Track)
- เริ่มต้นที่ **[index.html](index.html)** (หน้ารวมรายงานทั้ง 7 ฉบับ + สมุดปกขาว พร้อมป้ายบอกระดับความยากและพื้นที่)
- **ฉบับประชาชน (อ่านง่าย สรุป 2 นาที จบในเล่ม)**:
  - นครนายก: `report/น้ำท่วมนครนายก2569_ประชาชน.html` (สไลเดอร์ดาวเทียม + ถาม–ตอบ 15 ข้อ)
  - ทั่วประเทศ: `report/ระลอกปลายกย2569.html` (สถิติ 6 ลุ่มน้ำ + น้ำท่วมใหญ่)
  - คลองเจ้าพระยา 2: `report/คลองเจ้าพระยา2_ประชาชน.html` (ทำไมคันสูง + ถาม–ตอบ 23 ข้อ + สัดส่วนเทียบคนและบ้าน 2 ชั้น)
  - เชิงนโยบาย: `report/สมุดปกขาว_เจ้าพระยา2.html` (ถอดบทเรียนความเสี่ยง + แบบจำลองการเงินสดแบบโต้ตอบ)

### 🔬 ลู่ที่ 2: นักวิจัย / วิศวกร / นโยบาย (Researcher & Engineer Track)
- เริ่มต้นที่ **[docs/PROJECT_MAP.md](docs/PROJECT_MAP.md)** (ตาราง Matrix เชื่อมโยงประเด็น $\leftrightarrow$ ตัวเลข $\leftrightarrow$ สเปก)
- **ฉบับวิชาการ (ตรวจสอบย้อนกลับได้ทุกตัวเลข & สมการ)**:
  - นครนายก: `report/น้ำท่วมนครนายก2569_วิชาการ.html` + `docs/METHODS.md` + `docs/DATA_DICTIONARY.md`
  - ทั่วประเทศ: `docs/GOAL6_PLAN.md` + `report/ชุดเทียบมาตรฐาน2554.html`
  - คลองเจ้าพระยา 2: `report/คลองเจ้าพระยา2_วิชาการ.html` + `docs/GOAL7_PLAN.md` + `docs/GOAL7_FOI_REQUESTS.md`
- **ไฟล์ตัวเลขทางการ (Canonical JSON)**:
  - `analysis/canonical_numbers.json` (เป้าหมาย 1–5)
  - `analysis/goal6/canonical.json` (เป้าหมาย 6)
  - `analysis/goal7/canonical.json` (เป้าหมาย 7) + `analysis/goal7/gaps.json` (ทะเบียนช่องว่างข้อมูล)

### 💻 ลู่ที่ 3: นักพัฒนา / AI Pair-Programmer (Developer & Agent Track)
1. **[AGENTS.md](AGENTS.md)** — **กติกาบังคับ** (ละเมิดแล้วเสียหลักฐาน/ตัวเลข, PDPA, ห้าม commit ไฟล์ใหญ่, ห้าม push เอง)
2. **[docs/REPORT_CONVENTIONS.md](docs/REPORT_CONVENTIONS.md)** — ข้อตกลงการทำรายงาน (เอ็นจิน key+โทเคน, ชิ้นส่วนร่วม, ธีม WCAG, สรีรศาสตร์สายตา, และ Linter ภาษาไทย)
3. **[docs/PROJECT_MAP.md](docs/PROJECT_MAP.md)** — แผนที่นำทางและสารบัญสคริปต์ 199 ไฟล์ใน `analysis/`
4. **`catalog.py`** — สคริปต์สืบค้นเร็วใน Terminal (`python catalog.py`)
5. **[docs/LEGAL_REVIEW.md](docs/LEGAL_REVIEW.md)** — กรอบวิจารณ์เชิงระบบและแนวปฏิบัติหมิ่นประมาท

---

## 4. ทำซ้ำตัวเลขหัวใจ (Reproducibility Guide)

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

### 4.D — สร้างชุดเป้าหมาย 6 (รายงาน 3–4) ใหม่ทั้งชุด

```bash
bash data/31_external_landcover/fetch.sh          # ครั้งแรกเท่านั้น (~750 MB: WorldCover/JRC/WorldPop/OSM)
"$PY" analysis/goal6_build_all.py --with-analysis  # วิเคราะห์ → canonical → รายงาน 3–4 → pytest
```

> ไม่ใช้ `--skip-l3` ถ้าต้องการคำนวณโมเดล L3 ใหม่ (ต้องมีแคชรายชั่วโมงใน `data/22_goal6_network/raw/`) ·
> รอบเต็มวันที่ 12 ต.ค. 69 ผ่าน: pytest 60/60 · MISMATCH 0 · ไฟล์ที่ track ไม่เปลี่ยนเลย (ทำซ้ำได้ตรง)

### 4.E — สร้างชุดเป้าหมาย 7 (รายงาน 7–8: คลองเจ้าพระยา 2)

```bash
"$PY" report/goal7_build_all.py    # สร้างรายงาน 7 (ประชาชน) และ รายงาน 8 (วิชาการ)
```

> เอ็นจินรายงาน (`report/goal7_engine.py`) จะสร้างผังหัวข้อ ตรวจสอบโทเคนข้ามฉบับ (`⟦key⟧`)
> และเรนเดอร์ HTML ออกมา 2 ไฟล์ (`report/คลองเจ้าพระยา2_ประชาชน.html` และ `report/คลองเจ้าพระยา2_วิชาการ.html`)

---

## 5. ตัวเลขที่ควรได้ (sanity check)

รัน §4.A แล้วเทียบกับค่าที่บันทึกใน `docs/DATA_DICTIONARY.md`:

| ปริมาณ | ค่าที่เป็นทางการ | ที่มา |
|---|---|---|
| น้ำสูงสุดระดับน้ำ Ny.7 | **9.23 ม. เกจ = 7.64 ม.รทก. ±0.05** | thaiwater (9.23) · khundan-tele (7.68 รทก.) — ต่างกัน ≤5 ซม. |
| ระยะเวลาเหนือตลิ่ง | **65 ชม.** | thaiwater ขาด 3 แถวเที่ยงคืน · khundan ยืนยัน |
| พื้นที่น้ำท่วมสูงสุด 27 ก.ย. 18:28 | **452 ตร.กม.** | ประมวลผล S1 เอง (GISTDA ไม่ได้ทำ pass นี้) |
| BANKFULL | **6.86 ม.รทก. = เกจ 8.45 ≈ Q 487 (Manning หน้าตัดประกอบ จาก `analysis/hydraulic_1d_routing_summary.json`)** | ตรวจไขว้กับหน้าตัดจริงแล้ว |
| สัดส่วนเขื่อน : ฝน (ช่วงเริ่มท่วม) | **12 % : 88 %** | `khundan_tele_findings.md` |
| โมเดล Ny.7 RMSE เหตุการณ์ (+6/+24/+48 ชม.) | **สูตร 30.0/117.6/163.7 · persistence 30.6/101.8/170.4 · GBDT 127.7/159.8/140.6 ซม.** | `goal4_model_v1_results.json` (สร้างใหม่ด้วยสคริปต์ — มีเทสตรงค่าใน tests/) |
| M4 ระบายล่วงหน้า 5.2 ลลบ.ม. | **ระดับสูงสุดลด ~1 ซม.** (บนที่ราบ 452 ตร.กม.) | `goal4_counterfactual_model.py` |
| Manning n ที่สอดคล้อง rating curve | **0.0437** (ปกติที่ราบลุ่ม) | `rid_cross_section_stage_rating.md` |

---

---

## 6. แผนผัง: อะไรอยู่ใน git อะไรอยู่บนดิสก์

**อยู่ใน git** (ตรวจสอบย้อนได้): สคริปต์ · ผลวิเคราะห์ JSON/CSV/PNG · รายงาน HTML ·
`manifest.md` ทุกโฟลเดอร์ · ข้อมูลโทรมาตรที่จัดระเบียบแล้ว (`data/01`, `02`, `16`, `19` ฯลฯ)

**อยู่บนดิสก์เท่านั้น** (มี SHA-256 ใน manifest): ข้อมูลภายนอก `data/31_external_landcover/raw` (WorldCover/JRC/WorldPop/OSM) ·
ฝนรายเซลล์ `data/22.../raw/basin_rain` · น้ำเข้าอ่าง `data/22.../raw/dam_flows` · ฉากดาวเทียมดิบ (`*.zip/*.kmz`),
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

- **FOI / ต้องมีมนุษย์ (คลังเต็ม docs/OFFLINE_DATA_BACKLOG.md):** FOI 7 เรื่อง (ตารางเปิดบานรายชั่วโมง 2,315 ปตร. · ประวัติเดินเครื่องสูบน้ำ · ระเบียบ กช. · รูปตัดขวางใต้น้ำ · datum benchmark · สถิติผันน้ำข้ามลุ่ม · นิยาม Outflow) + ขอวิชาการ (LiDAR 1–5 ม. · ฝน TMD รายชั่วโมง · เรดาร์ QPE · คุณภาพน้ำ/ความเค็ม) · Flood Hub API key
- **วิเคราะห์:** HEC-RAS 1D (แทน lumped model) · ขยายภาคตัดขวาง Ny.7 ด้วย Copernicus DEM ·
  ใส่ error bar ให้สัดส่วน 12 % : 88 % · ไขปริศนา Ny.1B Q = 668.6 ม³/วิ
- **ทุกจุดวัด (ครบแล้ว):** raw+แฮชครบ (`data/20_multistation_levels/`) · เครือข่ายรายจุด ·
  ผลต่อ 4 วัตถุประสงค์ · ทดสอบทำนายท่าช้าง (หลายฤดู — **ทำนายไม่ได้**) ·
  เหลือ: **เส้นความสัมพันธ์ระดับน้ำ–อัตราการไหล (rating curve) ของคลอง** (วต.2) + **การเคลื่อนตัวของน้ำหลาก (routing)** (วต.4) + **FOI ตารางเปิด-ปิดบานระบายน้ำ** (ก้าวถัดไปที่แท้จริง)
  ดู `analysis/ALL_STATIONS_IMPLEMENTATION_PLAN.md`
- **ข้อมูล:** ⚠️ **ค่าอ้างอิงความสูง (datum) 9 จุดเปลี่ยนกลางเดือน** (16–21, 26, 30, 84) — ต้องจัดการก่อนดึง 5 ปี
- **ข้อมูล:** PQR ซ้ำกับ SAFE ที่แตกแล้ว (~2.9 GB) เสนอลบไว้ใน `data/manual/manifest.md` (ยังไม่ลบ)
- **เป้าหมาย 6 (ตั้ง 9–10 ต.ค. 69 — สถานะ 12 ต.ค.):** ครบแล้ว: ผู้สมัคร 24 เขื่อน · screen 200 จุด ·
  L1 6 ลุ่ม (config pre-register) · L2 (S1 35 ฉาก + DEM → **น้ำท่วมสูงสุด 1 ต.ค. ทั้งประเทศ**) ·
  L3 โมเดล 6 ลุ่ม · H1 benchmark 2554 ครบ 24 เขื่อน · Q1 ฝนคาบคืน (ครบ 199 จุด: อันดับ 1–3 ที่ 67/199) ·
  ฐานเครือข่าย HydroBASINS+WorldCover+ผูก node (10 ต.ค.) ·
  **ร่างรายงานที่ 3 ออกแล้ว (ตรวจภาษา+ตัวเลขผ่านเทสต์)** — เหลือ: mask ทะเล กทม. · GISTDA ราย pass (มนุษย์) ·
  รีวิวครบชุด AI หลายตัว · ดู `docs/GOAL6_PLAN.md` §10 + `HANDOFF.md`
- **เป้าหมาย 7 (ตั้ง 14–16 ต.ค. 69 — สถานะ 16 ต.ค.):** เสร็จสมบูรณ์แล้ว: สกัดและสอบทาน EIA 4 ฉบับ (2561–2569) ·
  ถอดตารางอาคารประกอบ 99 แห่ง และไซฟอนตัดคลองเดิม 34 จุด · ซ้อนทับแนวคลองกับผังน้ำ สทนช. ·
  สร้างเอ็นจินรายงาน key+โทเคน (`report/goal7_engine.py`) · **รายงานที่ 7 และ 8 ออกสมบูรณ์แล้ว**
  (ถาม–ตอบ 23 ข้อ + ภาพหน้าตัดสเกลจริงเทียบกับบ้าน 2 ชั้น) · ทะเบียนช่องว่างข้อมูลอยู่ใน `analysis/goal7/gaps.json`
  และประเด็นขอข้อมูลทางการอยู่ใน `docs/GOAL7_FOI_REQUESTS.md`

---
