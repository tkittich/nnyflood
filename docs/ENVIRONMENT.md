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

### เครื่องมือ/สคริปต์ที่ลงทะเบียน

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

รวม 3 สภาพแวดล้อม · 27 เครื่องมือที่ลงทะเบียน (สคริปต์อื่นที่ยังไม่ลงทะเบียนดูด้วย `python tools/doctor.py --list-unregistered`)

<!-- END GENERATED: tool-registry -->

## สิ่งที่ *ไม่* ต้องติดตั้ง

- ไม่ต้องมี API key สำหรับ NASA POWER และ Open-Meteo (Historical Forecast)
- `khundan-tele.rid.go.th` และ `api-v3.thaiwater.net` เปิดให้ GET/POST โดยไม่ต้องยืนยันตัว
- Flood Hub API และตารางเปิดบานรายชั่วโมง สช.9 ยัง**ไม่มี** — เป็นช่องว่างของข้อมูลภายนอก
  ไม่ใช่ปัญหาสภาพแวดล้อม (รายการ FOI อยู่ใน START_HERE.md §8)
