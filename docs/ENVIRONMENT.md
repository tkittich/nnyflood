# สภาพแวดล้อมที่ใช้รัน (Environment record)

> บันทึกสภาพแวดล้อมที่ตัวเลขในรายงานทุกฉบับผลิตด้วยจริง — ทำซ้ำตัวเลขให้ตรงต้องใช้ชุดนี้

## อินเทอร์พรีเตอร์

| รายการ | ค่า |
|---|---|
| เวอร์ชัน | **CPython 3.14.5** (tags/v3.14.5:5607950, 10 May 2026, MSC v.1944 64-bit) |
| พาธที่ใช้จริง | `C:\Users\theera\AppData\Local\Python\pythoncore-3.14-64\python.exe` |
| OS | Windows (รันสคริปต์ผ่าน Git Bash) |
| ตัวจัดการ | ไม่มี venv — ติดตั้งที่ระดับผู้ใช้ (ระบบเป็น single-user workstation) |

## เวอร์ชันไลบรารีที่ "รันจริงและผ่านเทสต์"

ตัวเลขในรายงานทุกฉบับผลิตด้วยชุดนี้ — `requirements.txt` ปักหมุดไว้ตรงกัน

| แพ็กเกจ | เวอร์ชัน | ใช้ทำอะไร |
|---|---|---|
| numpy | 2.5.1 | คำนวณอนุกรมเวลา/Manning/พื้นที่ |
| scipy | 1.18.1 | สถิติเสริม |
| rasterio | 1.5.2 | อ่าน GeoTIFF/DEM + reproject Sentinel-1 |
| shapely | 2.1.2 | เรขาคณิตโซนน้ำท่วม |
| matplotlib | 3.11.2 | กราฟทั้งหมด (ต้องมีฟอนต์ไทย — ดูด้านล่าง) |
| pyshp | 3.1.6 | อ่าน shapefile GISTDA |
| scikit-learn | 1.9.1 | โมเดลทำนาย (LinearRegression, HistGradientBoosting) |
| openpyxl | 3.1.5 | อ่านไฟล์สำรวจรูปตัดขวาง .xlsx ของกรมชลประทาน |
| pytest | 9.1.1 | รันชุดทดสอบ |

## ติดตั้งใหม่ / ย้ายเครื่อง

```bash
pip install -r requirements.txt
python -m pytest tests/ -q          # ต้องได้ 31 passed
```

## กับดักสภาพแวดล้อมที่เจอจริงในโครงการนี้

1. **ฟอนต์ไทยใน matplotlib** — ค่าเริ่มต้น (DejaVu Sans) ไม่มีสระ/วรรณยุกต์ไทย ทำให้กราฟ
   ออกมาเป็นกล่องสี่เหลี่ยม ต้องตั้งในทุกสคริปต์ที่วาดกราฟ:
   ```python
   plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma"]
   ```
   (มีใน `report/report_assets.py`, `goal4_model_v1.py`, `goal4_counterfactual_model.py`,
   `rid_cross_section_plot.py`)

2. **บรรทัดขึ้นบรรทัดใหม่บน Windows** — `git checkout` เติม CRLF ให้ไฟล์ที่ commit เป็น LF
   ทำให้ **sha256 ของไฟล์ดิบไม่ตรง** กับตอนที่เขียนครั้งแรก แม้เนื้อหาจะเหมือนกันเป๊ะ
   · เวลาตรวจ "คืนไฟล์สำเร็จไหม" ให้เทียบ hash หลัง normalize `\r\n` → `\n` ก่อน
   ไม่งั้นจะอ่านผิดว่า restore ล้มเหลว

3. **UTF-8 BOM** — ไฟล์ CSV ไทยหลายไฟล์มี BOM · `encoding="utf-8-sig"` ตัด BOM **ตัวแรก**
   เท่านั้น การเขียนแบบ append ต้องกันไม่ให้ BOM ซ้ำ (ดู `analysis/album_append.py`)

4. **path ของ curl ใน Git Bash vs Python บน Windows** — `curl -o /tmp/x.json` เขียนลงพาธ
   ที่ Python ฝั่ง Windows อ่านไม่ได้ ให้เขียนลงไฟล์ในโครงการแทน (เช่น `.ov_tmp.json`)

5. **ชื่อแพ็กเกจ ≠ ชื่อโมดูล (`pyshp`)** — ติดตั้งด้วยชื่อ `pyshp` แต่ import ด้วย `import shapefile`
   · `import pyshp` **ล้มเหลว** (ตรวจแล้ว: `ModuleNotFoundError: No module named 'pyshp'`
   ขณะที่ `import shapefile` คืนเวอร์ชัน 3.1.6) — อย่าเขียน `import pyshp` ในสคริปต์ใหม่

## OCR ภาษาไทย (เป้าหมาย 7 — ติดตั้งแยก ไม่อยู่ใน requirements.txt)

> **อัปเดต 19 ต.ค. 69:** มี OCR ตัวใหม่ที่แม่นกว่า — **Typhoon-OCR 1.5 2B บน GPU** ใน `E:/theera/typhoon_env` (สภาพแวดล้อม `typhoon_env` ในทะเบียนด้านล่าง) ใช้เมื่อต้องยืนยันตัวเลขในตาราง/รูป EIA · RapidOCR ข้างล่างยังใช้คัดกรองหน้าได้เร็วกว่า แต่ถือเป็นตัวรอง (`superseded`) · เวอร์ชันและสถานะล่าสุดอ่านจากตารางที่สร้างอัตโนมัติ ไม่ต้องเชื่อข้อความมือในส่วนนี้

- เครื่องมือ: **RapidOCR** (รุ่นภาษาไทย PP-OCRv5 `th_PP-OCRv5_rec_mobile` + onnxruntime CPU) ใน venv **นอก repo** `E:/theera/ocr_env`
  (`python -m venv E:/theera/ocr_env` แล้ว `pip install rapidocr onnxruntime pymupdf pillow numpy`) · โมเดลดาวน์โหลดครั้งแรกจาก modelscope (~8 MB)
- ใช้กับ `analysis/goal7_ocr.py` (รันด้วย python ของ venv นั้น) · ความเร็วราว 1.4–1.7 วินาที/หน้า (200 dpi) · อ่านไทยพิมพ์ได้ดี
  (ผิดเล็กน้อย: วรรณยุกต์/สระบางตัว หัวคอลัมน์บางช่อง) → ค้นด้วยข้อความตัดวรรณยุกต์ (`analysis/goal7_ocr_scan.py`) แล้ว**ตรวจภาพหน้าก่อนอ้าง**
- ทางเลือกที่ตรวจแล้ว: Windows OCR ในเครื่องไม่มีภาษาไทย (ต้องสิทธิ์ผู้ดูแลเพิ่มแพ็ก) · ไม่มี tesseract/torch ในเครื่อง · python 3.14 ไม่มี wheel ของ torch ในเวลาที่ทดสอบ
- ผลลัพธ์ OCR เก็บบนดิสก์ `data/32_goal7_chaophraya2/ocr/` (ไม่เข้า git) — ในไฟล์เก็บเฉพาะข้อเท็จจริงที่ตรวจภาพแล้ว (`analysis/goal7/ocr_findings.json` + `OCR_FACTS`)

<!-- BEGIN GENERATED: tool-registry (python tools/doctor.py --write-docs) -->

## ทะเบียนเครื่องมือและสภาพแวดล้อม (สร้างอัตโนมัติจาก `tools/registry.json`)

> อย่าแก้ส่วนนี้ด้วยมือ — แก้ `tools/registry.json` แล้วรัน `python tools/doctor.py --write-docs` · ตรวจด้วย `python tools/doctor.py`

### สภาพแวดล้อม

| id | ชื่อ | สถานะ | ตัวแปลภาษา | ใช้ทำอะไร | เวอร์ชันที่ตรวจล่าสุด |
|---|---|---|---|---|---|
| `main` | Python หลักของโครงการ | active | `$MAIN` (python ที่รัน doctor) | รันสคริปต์วิเคราะห์ รายงาน และชุดทดสอบทั้งหมด (ปักเวอร์ชันตาม requirements.txt) | Python 3.14.5 · matplotlib 3.11.2, numpy 2.5.1, pytest 9.1.1, scikit-learn 1.9.1, scipy 1.18.1 |
| `ocr_env` | RapidOCR (ภาษาไทย · CPU) | superseded → typhoon_env | `E:/theera/ocr_env/Scripts/python.exe` | OCR ไทยเร็ว ๆ บน CPU (PP-OCRv5 th rec mobile) — ใช้คัดกรองหน้า/ค้นข้อความ ไม่เหมาะกับตารางและวรรณยุกต์ที่ต้องแม่นตัวเลข · ยังใช้ได้และเร็วกว่าบนหน้าเดี่ยว แต่ค่าตัวเลขสำคัญต้องยืนยันด้วย typhoon_env หรือเปิดภาพตรวจ | Python 3.14.5 · PyMuPDF 1.28.2, numpy 2.5.4, onnxruntime 1.31.0, pillow 12.3.0, rapidocr 3.10.0 |
| `typhoon_env` | Typhoon-OCR 1.5 2B (แบบจำลองภาพ–ภาษา · GPU) | active | `E:/theera/typhoon_env/Scripts/python.exe` | OCR ไทยที่คงรูปตารางเป็น Markdown และอ่านวรรณยุกต์/สระได้ดีกว่า — ใช้อ่านรูปและตารางใน EIA เมื่อต้องยืนยันตัวเลข | Python 3.12.9 · torch 2.6.0+cu124, transformers 5.20.1 |

### เครื่องมือ/สคริปต์ที่ทบทวนแล้ว

| id | ไฟล์ | สภาพแวดล้อม | สถานะ | ทำอะไร | รันอย่างไร | ผลิต |
|---|---|---|---|---|---|---|
| `verify_all` | `tools/verify_all.py` | `main` | active | ตรวจครบวงจร: สารบัญ · แฮชข้อมูลดิบ · ภาษา/มาตรฐาน · ทะเบียนเครื่องมือ · pytest ทั้งชุด | `python tools/verify_all.py` | — |
| `doctor` | `tools/doctor.py` | `main` | active | ตรวจทะเบียนนี้: สภาพแวดล้อมพร้อมใช้ · ไฟล์มีจริง · เอกสารตรงกับทะเบียน · สคริปต์ที่ยังไม่ลงทะเบียน | `python tools/doctor.py [--deep] [--write-docs] [--list-unregistered]` | `docs/ENVIRONMENT.md (ส่วนเครื่องมือ)` |
| `number_inventory` | `tools/number_inventory.py` | `main` | active | บัญชีตัวเลขทั้งคลัง: ปริมาณเดียวกันค่าต่างกัน · ตัวเลขกำพร้า · คีย์ JSON ขัด · literal ใน builder · เอกสารล้าสมัย | `python tools/number_inventory.py --out docs/reviews/INVENTORY_<วันที่>.md` | `docs/reviews/INVENTORY_*.md` |
| `mini_fts` | `tools/mini_fts.py` | `main` | active | ดัชนีค้นข้อความเต็ม (SQLite FTS) ของเอกสารและผล OCR | `python tools/mini_fts.py` | `data/search_index.db` |
| `install_hooks` | `tools/install_hooks.py` | `main` | active | ติดตั้ง Git pre-commit hook (สารบัญ + ภาษา + ความสอดคล้องข้อมูล) | `python tools/install_hooks.py` | `.git/hooks/pre-commit` |
| `round5_disposition` | `tools/round5_disposition.py` | `main` | deprecated | สร้างทะเบียนการตัดสินรายข้อของรีวิวรอบ 5 (ใช้ครั้งเดียว) | `python tools/round5_disposition.py` | — |
| `goal7_ocr` | `analysis/goal7_ocr.py` | `ocr_env` | superseded → goal7_typhoon_ocr | RapidOCR ไทยกับ PDF/ภาพสแกน → ผลต่อหน้า (pages.jsonl) | `E:/theera/ocr_env/Scripts/python.exe analysis/goal7_ocr.py spec.json` | `data/32_goal7_chaophraya2/ocr/<label>/pages.jsonl` |
| `goal7_ocr_scan` | `analysis/goal7_ocr_scan.py` | `main` | active | ค้นตัวเลข/ข้อความ (ตัดวรรณยุกต์) ในผล OCR | `python analysis/goal7_ocr_scan.py <คำค้น>` | — |
| `goal7_batch_ocr_queue` | `analysis/goal7_batch_ocr_queue.py` | `typhoon_env` | active | ตัวขับคิว OCR เอกสารสแกน EIA ด้วย Typhoon หลายงานพร้อมกัน | `E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_batch_ocr_queue.py --workers 2` | `data/32_goal7_chaophraya2/typhoon_ocr/` |
| `goal7_typhoon_ocr` | `analysis/goal7_typhoon_ocr.py` | `typhoon_env` | active | Typhoon-OCR บนหน้า/ช่วงหน้าที่ระบุ → Markdown คงตาราง | `E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_typhoon_ocr.py [args]` | `data/32_goal7_chaophraya2/typhoon_ocr/` |
| `build_canonical_numbers` | `analysis/build_canonical_numbers.py` | `main` | active | รวมตัวเลขรายงาน 1–2 เป็น canonical_numbers.json (โทเคน @@R:…@@) | `python analysis/build_canonical_numbers.py` | `analysis/canonical_numbers.json` |
| `hydraulic_1d_routing` | `analysis/hydraulic_1d_routing.py` | `main` | active | Manning บนหน้าตัดสำรวจ + การเดินน้ำ Muskingum–Cunge (X=0) Ny.1B→Ny.7 | `python analysis/hydraulic_1d_routing.py` | `analysis/hydraulic_1d_routing_summary.json`<br>`report/assets/hydraulic_1d_nakhonnayok_profiles.png` |
| `goal6_l3_coastal_model` | `analysis/goal6_l3_coastal_model.py` | `main` | active | โมเดลพยากรณ์ระดับน้ำ C.12 ผสานน้ำหนุน (block bootstrap) | `python analysis/goal6_l3_coastal_model.py` | `analysis/goal6/l3_coastal_summary.json` |
| `goal6_tide_gain_regression` | `analysis/goal6_tide_gain_regression.py` | `main` | active | ถดถอยอัตราส่งผ่านน้ำหนุนสู่ C.12 (Newey–West) | `python analysis/goal6_tide_gain_regression.py` | `analysis/goal6/tide_gain_regression.json` |
| `compound_flood_risk` | `analysis/compound_flood_risk.py` | `main` | experimental | เมทริกซ์น้ำเหนือหลากปะทะน้ำหนุน (ต้นแบบเชิงสำรวจ ยังไม่สอบเทียบหลายปี) | `python analysis/compound_flood_risk.py` | `analysis/compound_flood_risk_summary.json`<br>`report/assets/compound_flood_risk_matrix.png` |
| `goal6_canonical` | `analysis/goal6_canonical.py` | `main` | active | รวมตัวเลขเป้าหมาย 6 → goal6/canonical.json + ทะเบียนค่าที่ปลดประจำการ | `python analysis/goal6_canonical.py` | `analysis/goal6/canonical.json` |
| `goal6_build_all` | `analysis/goal6_build_all.py` | `main` | active | สายเดียวจบ: วิเคราะห์ → canonical → รายงาน 3–4 → pytest | `python analysis/goal6_build_all.py [--skip-l3]` | `report/ระลอกปลายกย2569.html`<br>`report/ชุดเทียบมาตรฐาน2554.html` |
| `goal7_ongkharak_2d_depression` | `analysis/goal7_ongkharak_2d_depression.py` | `main` | active | เส้นระดับ–พื้นที่–ปริมาตรแอ่งองครักษ์ (ถังเติมน้ำ) + ปรับเทียบกับดาวเทียม | `python analysis/goal7_ongkharak_2d_depression.py` | `analysis/goal7/ongkharak_2d_depression_summary.json` |
| `goal7_operational_economics` | `analysis/goal7_operational_economics.py` | `main` | active | วันเทียบเท่าเต็มกำลัง S.26 · ต้นทุนวงจรชีวิต · ความจุกักเก็บคลอง | `python analysis/goal7_operational_economics.py` | `analysis/goal7/operational_economics_summary.json` |
| `goal7_counterfactual_simulation` | `analysis/goal7_counterfactual_simulation.py` | `main` | experimental | การจำลองคู่ขนาน 2554/2569 จากรูปคลื่นสังเคราะห์ — อธิบายเท่านั้น (illustrative_only) | `python analysis/goal7_counterfactual_simulation.py` | `analysis/goal7/counterfactual_simulation_summary.json` |
| `goal7_analysis` | `analysis/goal7_analysis.py` | `main` | active | รวมตัวเลขเป้าหมาย 7 → goal7/canonical.json (reconciled_parameters, design_segments ฯลฯ) | `python analysis/goal7_analysis.py` | `analysis/goal7/canonical.json` |
| `goal7_build_all` | `report/goal7_build_all.py` | `main` | active | สร้างรายงาน 7–8 ให้ตรงกันจนผังหัวข้อนิ่ง (สมุดปกขาวสร้างแยกด้วย goal7_build_policy_brief.py) | `python report/goal7_build_all.py` | `report/คลองเจ้าพระยา2_ประชาชน.html`<br>`report/คลองเจ้าพระยา2_วิชาการ.html` |
| `goal7_build_policy_brief` | `report/goal7_build_policy_brief.py` | `main` | active | สมุดปกขาวนโยบาย | `python report/goal7_build_policy_brief.py` | `report/สมุดปกขาว_เจ้าพระยา2.html` |
| `build_expert_report` | `report/build_expert_report.py` | `main` | active | รายงาน 2 (วิชาการ นครนายก) | `python report/build_expert_report.py` | `report/น้ำท่วมนครนายก2569_วิชาการ.html` |
| `build_report_html` | `report/build_report_html.py` | `main` | active | รายงาน 1 (ประชาชน นครนายก) | `python report/build_report_html.py` | `report/น้ำท่วมนครนายก2569_ประชาชน.html` |
| `verify_data_integrity` | `analysis/verify_data_integrity.py` | `main` | active | ตรวจ SHA-256 ของข้อมูลดิบเทียบทะเบียนแฮช (MISSING = ไฟล์ใหญ่นอก git) | `python analysis/verify_data_integrity.py [--quick]` | — |
| `goal7_gaps_check` | `analysis/goal7_gaps_check.py` | `main` | active | ทบทวนช่องว่างข้อมูลที่เปิดอยู่เมื่อมีแหล่งใหม่ในทะเบียนแฮช (--ack) | `python analysis/goal7_gaps_check.py [--ack]` | `analysis/goal7/gaps.json` |

### ลงทะเบียนอัตโนมัติ รอทบทวน (120 รายการ · สถานะ `unreviewed`)

> คำอธิบายมาจาก docstring บรรทัดแรกโดยอัตโนมัติ ยังไม่มีคนยืนยันสถานะ/ผลลัพธ์ — เปลี่ยนสถานะเป็น `active`/`deprecated` เมื่อทบทวนแล้ว

| id | ไฟล์ | env | ชนิด | คำอธิบาย (จาก docstring) |
|---|---|---|---|---|
| `album_append` | `analysis/album_append.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `album_geotag_map` | `analysis/album_geotag_map.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `album_scan_batch` | `analysis/album_scan_batch.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `all_stations_network` | `analysis/all_stations_network.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `archive_forecasts_daily` | `analysis/archive_forecasts_daily.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `attribution_share` | `analysis/attribution_share.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `calibrate_s1_thresholds` | `analysis/calibrate_s1_thresholds.py` | `main` | script | ค้น threshold ของกฎ 3 เงื่อนไข โดย maximize F1 เทียบ GISTDA บนฉาก 2 ต.ค. (producer ของ METHODS §6) |
| `common` | `analysis/common.py` | `main` | module | ค่าคงที่กายภาพ + สูตรกลางของโปรเจกต์ — แหล่งเดียว ห้ามพิมพ์ literal ซ้ำในสคริปต์อื่น |
| `common_datum_shift_correction` | `analysis/common_datum_shift_correction.py` | `main` | script | การปรับแก้ค่าระดับอ้างอิงและจุดกระโดดของสถานีโทรมาตร 9 แห่ง (September Datum Shifts) |
| `common_fetch_gulf_marine` | `analysis/common_fetch_gulf_marine.py` | `main` | script | ดึงข้อมูลคลื่น ความลึก และพยากรณ์น้ำทะเลอ่าวไทย (Gulf Marine & Wave Forecast) |
| `common_fetch_rain_stations` | `analysis/common_fetch_rain_stations.py` | `main` | script | ดึงข้อมูลฝนสถานีโทรมาตรอัตโนมัติทั่วประเทศ 4,593 จุด (National Rainfall Telemetry) |
| `common_fetch_rid_swoc` | `analysis/common_fetch_rid_swoc.py` | `main` | script | เครื่องมือดึงข้อมูลอ่างเก็บน้ำและโทรมาตรจากระบบ SWOC / RID |
| `common_fetch_water_quality` | `analysis/common_fetch_water_quality.py` | `main` | script | ดึงข้อมูลคุณภาพน้ำและความเค็มปากแม่น้ำ (Estuary Salinity) |
| `common_fetch_weather_forecasts` | `analysis/common_fetch_weather_forecasts.py` | `main` | script | ดึงข้อมูลพยากรณ์อากาศและน้ำท่า ECMWF IFS และ GloFAS |
| `fetch_gistda_flood` | `analysis/fetch_gistda_flood.py` | `main` | script | สคริปต์ดึงชั้นข้อมูลน้ำท่วมจาก GISTDA Disaster Platform API (2026) — ตัวเชื่อมโยงไปยัง goal6_fetch_gistda_flood.py |
| `fetch_khundan_fullyears` | `analysis/fetch_khundan_fullyears.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `fetch_khundan_training` | `analysis/fetch_khundan_training.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `fetch_khundan_training_2021_2022` | `analysis/fetch_khundan_training_2021_2022.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `fetch_khundan_training_2024_2025` | `analysis/fetch_khundan_training_2024_2025.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `fetch_multistation_levels` | `analysis/fetch_multistation_levels.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `georef_corner_match` | `analysis/georef_corner_match.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `georef_fit` | `analysis/georef_fit.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `georef_gistda` | `analysis/georef_gistda.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `gistda_georef_compare` | `analysis/gistda_georef_compare.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `gistda_pass_areas` | `analysis/gistda_pass_areas.py` | `main` | script | สรุปพื้นที่น้ำท่วมจาก attribute ของ shapefile GISTDA ราย pass → analysis/gistda_pass_areas_nn.json |
| `goal2_khundan_22y_baseline` | `analysis/goal2_khundan_22y_baseline.py` | `main` | script | การวิเคราะห์พฤติกรรมการกักเก็บน้ำของเขื่อนขุนด่านปราการชล 22 ปี (2548–2569) |
| `goal2_khundan_22y_mass_balance` | `analysis/goal2_khundan_22y_mass_balance.py` | `main` | script | การปิดสมดุลมวลน้ำรายวัน 22 ปี เขื่อนขุนด่านปราการชล (2548–2569) |
| `goal2_nny_medium_dams` | `analysis/goal2_nny_medium_dams.py` | `main` | script | วิเคราะห์บทบาทอ่างเก็บน้ำขนาดกลาง 6 แห่งใน จ.นครนายก ช่วงน้ำท่วม 2569 |
| `goal4_counterfactual_model` | `analysis/goal4_counterfactual_model.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `goal4_feature_diagnostics` | `analysis/goal4_feature_diagnostics.py` | `main` | module | วินิจฉัยฟีเจอร์ของโมเดลทำนายระดับน้ำ Ny.7 — ตอบคำถามว่า "ablation วัดสัญญาณจริงหรือวัดความไม่เสถียร" |
| `goal4_model_backtest_long` | `analysis/goal4_model_backtest_long.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `goal4_model_moisture_test` | `analysis/goal4_model_moisture_test.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `goal4_model_multistation` | `analysis/goal4_model_multistation.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `goal4_model_rainfcst_test` | `analysis/goal4_model_rainfcst_test.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `goal4_model_v1` | `analysis/goal4_model_v1.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `goal4_thachang_model` | `analysis/goal4_thachang_model.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `goal6_basin_rain` | `analysis/goal6_basin_rain.py` | `main` | script | ฝนเฉลี่ยทั้งลุ่ม (ถ่วงน้ำหนักตามพื้นที่) + ฝนรวมฤดู — รีวิว Sonnet A2 (12 ต.ค. 69) |
| `goal6_basin_readiness` | `analysis/goal6_basin_readiness.py` | `main` | script | เป้าหมาย 6 — sweep ความพร้อมข้อมูล 5 ลุ่มรอบแรก (ผู้ใช้ยืนยัน 10 ต.ค. 2569) |
| `goal6_bkk_sea_mask` | `analysis/goal6_bkk_sea_mask.py` | `main` | module | เป้าหมาย 6 — mask ทะเลบท กทม.: ตัดนอกตลิ่งน้ำขึ้นลงออกจากมาสก์น้ำ S1 ของ bkk_lower |
| `goal6_c2_attribution` | `analysis/goal6_c2_attribution.py` | `main` | script | C.2 attribution — ผลิตตัวเลขทั้งชุด "เขื่อนผิดหรือฝนผิด" ลง JSON (แทน literal ใน builder) |
| `goal6_dam_candidates` | `analysis/goal6_dam_candidates.py` | `main` | script | เป้าหมาย 6 — รายชื่อเขื่อนผู้สมัครทั่วประเทศ (ขนาดใกล้เคียง/ใหญ่กว่าเขื่อนขุนด่านปราการชล) |
| `goal6_dam_history_all` | `analysis/goal6_dam_history_all.py` | `main` | script | เป้าหมาย 6 — H1: ประวัติเขื่อนผู้สมัครที่ยังไม่ได้ดึง (เติมให้ครบ 24 แห่ง) → benchmark 2554 |
| `goal6_dam_inflow` | `analysis/goal6_dam_inflow.py` | `main` | script | น้ำเข้า–ปล่อย–เก็บ รายเขื่อน 2554 vs 2569 เทียบประวัติ 22 ปี — แยก "ฝน/น้ำเข้า" ออกจาก "สถานะ/การเดินเขื่อน" |
| `goal6_downstream_tide` | `analysis/goal6_downstream_tide.py` | `main` | script | วิเคราะห์ระดับน้ำทะเลและน้ำหนุนปากแม่น้ำสายหลัก (Downstream Sea Levels & Tidal Dynamics) |
| `goal6_duration_maps` | `analysis/goal6_duration_maps.py` | `main` | module | แผนที่ระยะเวลาน้ำค้าง (หยาบ) — นับสัดส่วนฉากที่พิกัดมีน้ำ (น้ำรวม VH≤−20 ในที่ราบ) |
| `goal6_exposure` | `analysis/goal6_exposure.py` | `main` | script | ชั้นผลกระทบ: ประชากรและถนน/ทางรถไฟในพื้นที่ที่ตรวจพบ (รวม = ขอบบน · เข้มงวด = ขอบล่างของ "น้ำใหม่ในฉาก") |
| `goal6_fetch_gistda_flood` | `analysis/goal6_fetch_gistda_flood.py` | `main` | script | สคริปต์ดึงชั้นข้อมูลน้ำท่วมจาก GISTDA Disaster Platform API (2026) |
| `goal6_flood_maps` | `analysis/goal6_flood_maps.py` | `main` | script | แผนที่น้ำท่วมจากดาวเทียม 6 ลุ่ม — จากมาสก์น้ำ S1 ที่ประมวลผลแล้ว (stage-2 พีค) |
| `goal6_l1_expand` | `analysis/goal6_l1_expand.py` | `main` | script | เป้าหมาย 6 — runner ขยาย L1 ทุกลุ่มตาม analysis/goal6/config.json (template จาก spike ป่าสัก/แม่กลอง) |
| `goal6_l1_followups` | `analysis/goal6_l1_followups.py` | `main` | script | เป้าหมาย 6 — ตามข้อเสนอที่ผู้ใช้เห็นด้วย (10 ต.ค. 69): (ก) ไขความหมาย URC เทมเพลตใน API |
| `goal6_l3_coastal_harmonics` | `analysis/goal6_l3_coastal_harmonics.py` | `main` | script | แบบจำลองพยากรณ์ระดับน้ำเจ้าพระยาตอนล่างผสานฮาร์มอนิกน้ำขึ้น-น้ำลงดาราศาสตร์ (Astronomical Tidal Harmonics Model) |
| `goal6_l3_model` | `analysis/goal6_l3_model.py` | `main` | script | เป้าหมาย 6 — L3: โมเดลทำนายระดับน้ำรายลุ่ม (วิธีเดียวกับ goal4_model_v1) |
| `goal6_make_config` | `analysis/goal6_make_config.py` | `main` | script | เป้าหมาย 6 — สร้าง analysis/goal6/config.json (ข้อตกลง pre-register ต่อลุ่ม) |
| `goal6_national_medium_reservoirs` | `analysis/goal6_national_medium_reservoirs.py` | `main` | script | การวิเคราะห์โครงข่ายอ่างเก็บน้ำขนาดกลาง 461 แห่งทั่วประเทศ |
| `goal6_network_base` | `analysis/goal6_network_base.py` | `main` | script | เป้าหมาย 6 — ขั้น 5: ชั้นเครือข่ายฐานระดับชาติ — HydroBASINS + ESA WorldCover |
| `goal6_network_nodes` | `analysis/goal6_network_nodes.py` | `main` | script | เป้าหมาย 6 — N1/N2 ฐาน: ผูก node ทั้งประเทศ (จุดวัด 199 + ปตร. 2,315) เข้าลุ่มย่อย HydroBASINS |
| `goal6_pasak_24y_baseline` | `analysis/goal6_pasak_24y_baseline.py` | `main` | script | การวิเคราะห์พฤติกรรมการเดินเขื่อนป่าสักชลสิทธิ์ 24 ปี (2546–2569) |
| `goal6_prerelease_scenario` | `analysis/goal6_prerelease_scenario.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `goal6_pull_historical_estuary` | `analysis/goal6_pull_historical_estuary.py` | `main` | script | ดึงข้อมูลระดับน้ำและน้ำหนุนปากแม่น้ำย้อนหลังลึกที่สุดเท่าที่ระบบออนไลน์มี (Historical Estuary Data Ingestion) |
| `goal6_rain_obs_2026` | `analysis/goal6_rain_obs_2026.py` | `main` | script | เป้าหมาย 6 — พยากรณ์ฝนย้อนหลัง (previous runs) ช่วงเหตุการณ์ 2569 ต่อจุดฝนลุ่ม |
| `goal6_rain_rarity` | `analysis/goal6_rain_rarity.py` | `main` | script | เป้าหมาย 6 — Q1: ฝนเหตุการณ์ 2569 หายากแค่ไหน (คาบคืนเชิงหยาบจาก POWER 1981–2026) |
| `goal6_rain_rarity_2554` | `analysis/goal6_rain_rarity_2554.py` | `main` | script | เป้าหมาย 6 — อันดับฝน 2554 จากแคช POWER เดียวกับ 2569 (ไม่ดาวน์โหลดใหม่) |
| `goal6_rain_rarity_national` | `analysis/goal6_rain_rarity_national.py` | `main` | script | เป้าหมาย 6 — ฝน POWER ระดับชาติ: ความหายากฝน 7/30 วัน ครบ 199 จุดวัดในคลังระดับชาติ |
| `goal6_report_charts` | `analysis/goal6_report_charts.py` | `main` | script | กราฟหัวใจรายงาน 3+4 — ระดับน้ำเก็บเขื่อนเทียบเส้นกำกับ (rule curve) ปี 2554 และ 2569 |
| `goal6_s1_dem` | `analysis/goal6_s1_dem.py` | `main` | script | เป้าหมาย 6 — L2 ประกอบ: DEM GLO-30 ต่อลุ่ม → mask ที่ราบ <60 ม. (แบบนครนายก) |
| `goal6_s1_download` | `analysis/goal6_s1_download.py` | `main` | script | เป้าหมาย 6 — ดาวน์โหลดคิว S1 GRDH-COG จาก CDSE ผ่าน S3 (credential ของผู้ใช้ในไฟล์ gitignored) |
| `goal6_s1_landcover` | `analysis/goal6_s1_landcover.py` | `main` | script | แยกผลตรวจน้ำ Sentinel-1 ตามชนิดผิวดิน (ESA WorldCover 2021 10 ม.) + น้ำถาวร (JRC Global Surface Water) |
| `goal6_s1_queue` | `analysis/goal6_s1_queue.py` | `main` | script | เป้าหมาย 6 — คิวดาวน์โหลด Sentinel-1 GRDH ช่วงเหตุการณ์ 23 ก.ย.–2 ต.ค. 69 ครบ 5 ลุ่มรอบแรก |
| `goal6_s1_rule_validation` | `analysis/goal6_s1_rule_validation.py` | `main` | script | ตรวจความถูกต้องของกฎตัดน้ำ Sentinel-1 (รีวิว Sonnet 12 ต.ค. 69 · M1/R9) — ไม่ใช้ข้อมูลใหม่ |
| `goal6_s1_stage1` | `analysis/goal6_s1_stage1.py` | `main` | script | เป้าหมาย 6 — L2 ขั้นที่ 1: geocode + calibrate ฉาก S1 ทุกฉากบนกริด 30 ม.ต่อลุ่ม (ขนาน) |
| `goal6_s1_stage2_water` | `analysis/goal6_s1_stage2_water.py` | `main` | script | เป้าหมาย 6 — L2 ขั้นที่ 2: ตัดน้ำด้วยกฎ canonical (เทียบฉากก่อนเหตุการณ์ วงโคจรเดียวกัน) |
| `goal6_s2_queue` | `analysis/goal6_s2_queue.py` | `main` | script | เป้าหมาย 6 — คิว Sentinel-2 L2A (ตรวจยืนยนอิสระ + ภาพสีจริง) ต่อลุ่ม — ค้นจาก CDSE OData |
| `goal6_s2_validate` | `analysis/goal6_s2_validate.py` | `main` | script | เป้าหมาย 6 — L2 ตรวจยืนยันอิสระ: S2 MNDWI เทียบมาสก์น้ำ S1 บนกริดเดียวกัน |
| `goal6_scan_banned_terms` | `analysis/goal6_scan_banned_terms.py` | `main` | script | สแกนรายงานที่ 3 — หาคำทับศัพท์/ศัพท์เทคนิคที่ยังไม่อนุมัติคำไทยแทน |
| `goal6_screen_basins` | `analysis/goal6_screen_basins.py` | `main` | script | เป้าหมาย 6 — screen เหตุการณ์ท่วมจริงหน้าฝน 2569 ต่อลุ่ม (เกณฑ์ pre-register) |
| `goal6_screen_findings` | `analysis/goal6_screen_findings.py` | `main` | script | เป้าหมาย 6 — สรุปผล screen หน้าฝน 2569 ต่อลุ่ม -> analysis/goal6_screen_2026_findings.md |
| `goal6_spike_maeklong_l1` | `analysis/goal6_spike_maeklong_l1.py` | `main` | script | เป้าหมาย 6 — spike ลุ่มที่สอง L1: แม่กลอง (ผู้ใช้ยืนยันรอบแรก 10 ต.ค. 69) |
| `goal6_spike_pasak_l1` | `analysis/goal6_spike_pasak_l1.py` | `main` | script | เป้าหมาย 6 — spike ลุ่มแรก L1: ป่าสัก (ผู้ใช้ยืนยันรอบแรก 5 ลุ่ม 10 ต.ค. 69) |
| `goal7_acid_sulfate_soil_analysis` | `analysis/goal7_acid_sulfate_soil_analysis.py` | `main` | script | การประเมินปริมาณดินกรดกำมะถันและไพไรต์ตามแนวขุดคลองเจ้าพระยา 2 |
| `goal7_ayutthaya_dqdh_rating` | `analysis/goal7_ayutthaya_dqdh_rating.py` | `main` | script | การสอบเทียบความสัมพันธ์ระดับ–ปริมาณน้ำ (dQ/dh) ลุ่มเจ้าพระยาตอนล่าง (อยุธยา–บางไทร) |
| `goal7_bangban_bangsai_comparison` | `analysis/goal7_bangban_bangsai_comparison.py` | `main` | script | เป้าหมาย 7 — การวิเคราะห์เปรียบเทียบเชิงวิศวกรรมและเศรษฐศาสตร์การก่อสร้าง: |
| `goal7_basin_containment` | `analysis/goal7_basin_containment.py` | `main` | script | เป้าหมาย 7 — ตรวจว่าแนวคลอง (แนวไม่เป็นทางการ) อยู่ในลุ่มน้ำใดบ้าง ตามขอบเขต 22 ลุ่มน้ำของ สทนช. |
| `goal7_clean_alignment` | `analysis/goal7_clean_alignment.py` | `main` | script | เป้าหมาย 7 — ทำความสะอาดแนวคลองเจ้าพระยา2 จาก My Maps (ผู้ใช้สร้าง) |
| `goal7_dam_to_gulf_hydraulics` | `analysis/goal7_dam_to_gulf_hydraulics.py` | `main` | script | เป้าหมาย 7 — การวิเคราะห์เส้นทางชลศาสตร์ เวกเตอร์การไหล และเวลาเดินทางจากเขื่อนสู่ปากอ่าวไทย (Dam-to-Gulf Hydraulic Corridors) |
| `goal7_eia_structs` | `analysis/goal7_eia_structs.py` | `ocr_env` | script | เป้าหมาย 7 — ดึงตาราง "บัญชีอาคารประกอบของคลองระบายน้ำหลาก" (ตาราง 2.3.2-3) จากรายงานผลกระทบสิ่งแวดล้อม 3 ฉบับ |
| `goal7_fabdem_compare` | `analysis/goal7_fabdem_compare.py` | `main` | script | เป้าหมาย 7 — เทียบความสูงพื้นดินตามแนวคลอง: FABDEM (ดินเปล่า) vs Copernicus GLO-30 (ผิวสูงสุด) vs ค่าอ่านจากรูปตัดตามยาว |
| `goal7_interbasin_transfer_vectors` | `analysis/goal7_interbasin_transfer_vectors.py` | `main` | script | การวิเคราะห์เวกเตอร์การผันน้ำข้ามลุ่มรายคลองเชื่อมโยง (Inter-basin Transfer Vectors) |
| `goal7_legal_and_nuclear_assessment` | `analysis/goal7_legal_and_nuclear_assessment.py` | `main` | script | การวิเคราะห์ข้อกฎหมายเวนคืนที่ดินเพื่อพาณิชย์ และการประเมินความปลอดภัยศูนย์วิจัยนิวเคลียร์องครักษ์ |
| `goal7_ongkharak_hydraulics` | `analysis/goal7_ongkharak_hydraulics.py` | `main` | script | เป้าหมาย 7 — การวิเคราะห์ชลศาสตร์ สมดุลมวลน้ำ และเวกเตอร์การไหลสุทธิทุ่งองครักษ์ (ตุลาคม 2569) |
| `goal7_scan_eia2569` | `analysis/goal7_scan_eia2569.py` | `ocr_env` | module | เป้าหมาย 7 — แผนที่การอ่านรายงานผลกระทบสิ่งแวดล้อม ฉบับ 2569 (4 เล่ม): นับหน้าที่พบคำสำคัญ ใช้บอกว่าส่วนสำคัญอยู่หน้าใดและยังไม่ได้อ่าน |
| `goal7_waterchart_overlay` | `analysis/goal7_waterchart_overlay.py` | `main` | script | เป้าหมาย 7 — ซ้อนแนวคลองเจ้าพระยา2 กับ "ผังน้ำ" และขอบเขตน้ำท่วมของ สทนช. (3 ลุ่มน้ำ: บางปะกง · เจ้าพระยา · ป่าสัก) |
| `hecras_lite_channel` | `analysis/hecras_lite_channel.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `landsat_water` | `analysis/landsat_water.py` | `main` | module | ตรวจน้ำท่วมด้วย Landsat optical 30 ม. (MNDWI) เทียบกับ S1 ของเรา + GISTDA บนกริดเดียวกัน |
| `national_pull_waterlevels` | `analysis/national_pull_waterlevels.py` | `main` | script | คลังข้อมูลระดับชาติ — ระดับน้ำรายชั่วโมงทุกจุดวัดสำคัญ (199 จุด) × 2020–2026 |
| `qa5_rain_drainage_counterfactual` | `analysis/qa5_rain_drainage_counterfactual.py` | `main` | module | QA5: 18-day rain (12-29 Sep 2026) -> river level/drainage analysis |
| `rain_window` | `analysis/rain_window.py` | `main` | module | หน้าต่างฝนสะสม n วัน สำหรับโมเดลทำนายระดับน้ำ Ny.7 — รวมตรรกะไว้ไฟล์เดียว |
| `rid_cross_section_extract` | `analysis/rid_cross_section_extract.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `rid_cross_section_hydraulics` | `analysis/rid_cross_section_hydraulics.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `rid_cross_section_plot` | `analysis/rid_cross_section_plot.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `rid_cross_section_stage_rating` | `analysis/rid_cross_section_stage_rating.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `run_all` | `analysis/run_all.py` | `main` | script | run_all — รัน pipeline ทั้งระบบตามลำดับมาตรฐาน จบในคำสั่งเดียว |
| `s1_change_detect` | `analysis/s1_change_detect.py` | `main` | script | Change-detection flood mapping — กฎที่ตีพิมพ์ในรายงาน (3 เงื่อนไข + opening 3×3) |
| `s1_masks` | `analysis/s1_masks.py` | `main` | module | Build common masks (province, districts, lowland DEM) on the S1 30 m grid. |
| `s1_merge_scenes` | `analysis/s1_merge_scenes.py` | `main` | script | โมเสก 2 slice ของฉาก S1 ที่ทับกัน → ไฟล์ `*_full_*` ที่ s1_change_detect.py ใช้ |
| `s1_pairs_animation` | `analysis/s1_pairs_animation.py` | `main` | module | Paired same-orbit change detection for the 3 new dates + stats + frame npys. |
| `s1_peak_flood_map` | `analysis/s1_peak_flood_map.py` | `main` | module | Peak flood map: 27 Sep 2026 18:28 change-detection extent on DEM hillshade. |
| `s1_process` | `analysis/s1_process.py` | `main` | script | Sentinel-1 GRDH COG processing for Nakhon Nayok flood mapping. |
| `s2_truecolor_process` | `analysis/s2_truecolor_process.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `s2_water` | `analysis/s2_water.py` | `main` | module | ตรวจน้ำท่วมด้วย Sentinel-2 optical (MNDWI) เทียบกับ S1 ของเรา บนกริดเดียวกัน — 2 ต.ค. 69 |
| `thachang_leadtime` | `analysis/thachang_leadtime.py` | `main` | script | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `goal6_build_report3_draft` | `report/goal6_build_report3_draft.py` | `main` | module | เป้าหมาย 6 — สร้างร่างรายงานที่ 3 v0.1 (L1 ครบ · L2/L3 เป็น placeholder) |
| `goal6_build_report4_draft` | `report/goal6_build_report4_draft.py` | `main` | module | สร้างร่างรายงานที่ 4 — benchmark 2554 vs 2569 (ระบบเดียว × หลายปี) |
| `goal6_reportlib` | `report/goal6_reportlib.py` | `main` | module | reportlib (เป้าหมาย 6) — builder บาง ๆ ใช้ร่วมทุกรายงาน (เสนอ §11 · เห็นด้วย 10 ต.ค. 69) |
| `goal7_blocks` | `report/goal7_blocks.py` | `main` | module | ชิ้นส่วนร่วมของรายงาน 7 (ประชาชน) และรายงาน 8 (วิชาการ) — ตารางที่สองฉบับต้องตรงกันเสมอ |
| `goal7_build_academic` | `report/goal7_build_academic.py` | `main` | module | สร้างรายงานที่ 8 ฉบับวิชาการ — คลองเจ้าพระยา2 (ข้อมูล วิธี ผล ข้อจำกัด ตรวจสอบย้อนกลับ) |
| `goal7_build_public` | `report/goal7_build_public.py` | `main` | module | สร้างรายงานที่ 7 ฉบับประชาชน — คลองเจ้าพระยา2 (คลองระบายน้ำหลากชัยนาท–ป่าสัก–อ่าวไทย) กับนครนายก |
| `goal7_common` | `report/goal7_common.py` | `main` | module | ส่วนกลางของรายงานเจ้าพระยา2 (ฉบับประชาชน/ฉบับวิชาการ): ข้อมูลจาก canonical + กราฟ |
| `goal7_engine` | `report/goal7_engine.py` | `main` | module | เอ็นจินรายงานเป้าหมาย 7 — ทะเบียนหัวข้อ/คำถามด้วยรหัสคงที่ (key) · เลขอัตโนมัติ · อ้างอิงข้ามฉบับ |
| `make_x_charts_thai` | `report/make_x_charts_thai.py` | `main` | module | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) |
| `report_assets` | `report/report_assets.py` | `main` | module | Generate all chart/frame PNGs for the public HTML report. |

รวม 3 สภาพแวดล้อม · 147 เครื่องมือที่ลงทะเบียน (สคริปต์อื่นที่ยังไม่ลงทะเบียนดูด้วย `python tools/doctor.py --list-unregistered`)

<!-- END GENERATED: tool-registry -->

## สิ่งที่ *ไม่* ต้องติดตั้ง

- ไม่ต้องมี API key สำหรับ NASA POWER และ Open-Meteo (Historical Forecast)
- `khundan-tele.rid.go.th` และ `api-v3.thaiwater.net` เปิดให้ GET/POST โดยไม่ต้องยืนยันตัว
- Flood Hub API และตารางเปิดบานรายชั่วโมง สช.9 ยัง**ไม่มี** — เป็นช่องว่างของข้อมูลภายนอก
  ไม่ใช่ปัญหาสภาพแวดล้อม (รายการ FOI อยู่ใน START_HERE.md §8)
