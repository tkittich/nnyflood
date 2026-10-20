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

> **อัปเดต 19 ต.ค. 69:** มี OCR ตัวใหม่ที่แม่นกว่า — **Typhoon-OCR 1.5 2B บน GPU** ใน `E:/theera/typhoon_env` (สภาพแวดล้อม `typhoon_env` ในทะเบียนด้านล่าง) ใช้เมื่อต้องยืนยันตัวเลขในตาราง/รูป EIA · **RapidOCR และ OCR อื่นทั้งหมดเลิกใช้แล้ว (ผู้ใช้ตัดสิน 19 ต.ค. 69 — อ่านไทยไม่ดี) ใช้ Typhoon เท่านั้น** ข้อความ RapidOCR ข้างล่างเก็บเป็นประวัติ (`deprecated`) · เวอร์ชันและสถานะล่าสุดอ่านจากตารางที่สร้างอัตโนมัติ ไม่ต้องเชื่อข้อความมือในส่วนนี้

- เครื่องมือ: **RapidOCR** (รุ่นภาษาไทย PP-OCRv5 `th_PP-OCRv5_rec_mobile` + onnxruntime CPU) ใน venv **นอก repo** `E:/theera/ocr_env`
  (`python -m venv E:/theera/ocr_env` แล้ว `pip install rapidocr onnxruntime pymupdf pillow numpy`) · โมเดลดาวน์โหลดครั้งแรกจาก modelscope (~8 MB)
- ใช้กับ `analysis/goal7_ocr.py` (รันด้วย python ของ venv นั้น) · ความเร็วราว 1.4–1.7 วินาที/หน้า (200 dpi) · อ่านไทยพิมพ์ได้ดี
  (ผิดเล็กน้อย: วรรณยุกต์/สระบางตัว หัวคอลัมน์บางช่อง) → ค้นด้วยข้อความตัดวรรณยุกต์ (`analysis/goal7_ocr_scan.py`) แล้ว**ตรวจภาพหน้าก่อนอ้าง**
- **พฤติกรรมของ Typhoon-OCR ที่วัดได้ (19 ต.ค. 69)**: (1) หน้าสแกนข้อความไทยให้ผลดีและเร็ว (~6–30 วินาที/หน้า) (2) หน้าแบบวิศวกรรม/รูปมักสะท้อนแม่แบบคำสั่งกลับ (echo: 23% ใน `eia_clarify2_att1`) — แม่แบบคำสั่งทางการแก้ echo ได้แต่ **แต่งข้อความขึ้นเองและช้ามาก (~160 วินาที/หน้า)** จึงไม่ใช้เป็นค่าตั้งต้น (3) หน้าตารางหนาแน่นอาจวนซ้ำจนถึงเพดานโทเคน (184 วินาที/หน้า) — ตัวถอดความจึงมีเพดานเวลา 70/45 วินาที และทำเครื่องหมาย `truncated` · หน้าที่ถอดไม่ได้ทำเครื่องหมาย `needs_visual` ให้คนเปิดภาพ/ตัดตารางอ่าน · GPU รองรับ 2 งานอิสระพร้อมกัน (`--workers 2`)
- ทางเลือกที่ตรวจแล้ว: Windows OCR ในเครื่องไม่มีภาษาไทย (ต้องสิทธิ์ผู้ดูแลเพิ่มแพ็ก) · ไม่มี tesseract/torch ในเครื่อง · python 3.14 ไม่มี wheel ของ torch ในเวลาที่ทดสอบ
- ผลลัพธ์ OCR เก็บบนดิสก์ `data/32_goal7_chaophraya2/ocr/` (ไม่เข้า git) — ในไฟล์เก็บเฉพาะข้อเท็จจริงที่ตรวจภาพแล้ว (`analysis/goal7/ocr_findings.json` + `OCR_FACTS`)

<!-- BEGIN GENERATED: tool-registry (python tools/doctor.py --write-docs) -->

## ทะเบียนเครื่องมือและสภาพแวดล้อม (สร้างอัตโนมัติจาก `tools/registry.json`)

> อย่าแก้ส่วนนี้ด้วยมือ — แก้ `tools/registry.json` แล้วรัน `python tools/doctor.py --write-docs` · ตรวจด้วย `python tools/doctor.py`

### สภาพแวดล้อม

| id | ชื่อ | สถานะ | ตัวแปลภาษา | ใช้ทำอะไร | เวอร์ชันที่ตรวจล่าสุด |
|---|---|---|---|---|---|
| `main` | Python หลักของโครงการ | active | `$MAIN` (python ที่รัน doctor) | รันสคริปต์วิเคราะห์ รายงาน และชุดทดสอบทั้งหมด (ปักเวอร์ชันตาม requirements.txt) | Python 3.14.5 · PyMuPDF 1.28.0, matplotlib 3.11.2, numpy 2.5.1, pytest 9.1.1, scikit-learn 1.9.1, scipy 1.18.1 |
| `ocr_env` | RapidOCR (ภาษาไทย · CPU) | deprecated | `E:/theera/ocr_env/Scripts/python.exe` | RapidOCR ไทย (CPU) — เลิกใช้แล้ว · เลิกใช้ (ผู้ใช้ 19 ต.ค. 69): อ่านไทยไม่ดี — OCR ทั้งหมดใช้ Typhoon (typhoon_env) · เก็บไว้เป็นประวัติ ไม่ใช้กับงานใหม่ | Python 3.14.5 · PyMuPDF 1.28.2, numpy 2.5.4, onnxruntime 1.31.0, pillow 12.3.0, rapidocr 3.10.0 |
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
| `goal7_ocr` | `analysis/goal7_ocr.py` | `ocr_env` | deprecated | RapidOCR ไทยกับ PDF/ภาพสแกน — เลิกใช้ (ใช้ goal7_typhoon_ocr / goal7_typhoon_queue_eia) | `E:/theera/ocr_env/Scripts/python.exe analysis/goal7_ocr.py spec.json` | `data/32_goal7_chaophraya2/ocr/<label>/pages.jsonl` |
| `goal7_ocr_scan` | `analysis/goal7_ocr_scan.py` | `main` | active | ค้นตัวเลข/ข้อความ (ตัดวรรณยุกต์) ในผล Typhoon-OCR รายหน้าและชั้นข้อความของ EIA | `python analysis/goal7_ocr_scan.py <คำค้น>` | — |
| `goal7_batch_ocr_queue` | `analysis/goal7_batch_ocr_queue.py` | `typhoon_env` | active | รายการงานเอกสารค้าง (BACKLOG_JOBS) สำหรับคิว Typhoon — รันผ่าน goal7_typhoon_queue_eia (คิวรวม worker อิสระ) | `E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_batch_ocr_queue.py --workers 2` | `data/32_goal7_chaophraya2/typhoon_ocr/` |
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
| `album_append` | `analysis/album_append.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/album_append.py` | — |
| `album_geotag_map` | `analysis/album_geotag_map.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | `analysis/album_geotag_map.png` |
| `album_scan_batch` | `analysis/album_scan_batch.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/album_scan_batch.py` | — |
| `all_stations_network` | `analysis/all_stations_network.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/all_stations_network.py` | — |
| `archive_forecasts_daily` | `analysis/archive_forecasts_daily.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `attribution_share` | `analysis/attribution_share.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/attribution_share.py` | — |
| `calibrate_s1_thresholds` | `analysis/calibrate_s1_thresholds.py` | `main` | active | ค้น threshold ของกฎ 3 เงื่อนไข โดย maximize F1 เทียบ GISTDA บนฉาก 2 ต.ค. (producer ของ METHODS §6) | ``python analysis/calibrate_s1_thresholds.py`   # ~1 นาที (504 คู่ threshold × 5.1 ล้าน px)` | — |
| `common` | `analysis/common.py` | `main` | active | ค่าคงที่กายภาพ + สูตรกลางของโปรเจกต์ — แหล่งเดียว ห้ามพิมพ์ literal ซ้ำในสคริปต์อื่น | `(โมดูล — import ไม่รันตรง)` | — |
| `common_datum_shift_correction` | `analysis/common_datum_shift_correction.py` | `main` | active | การปรับแก้ค่าระดับอ้างอิงและจุดกระโดดของสถานีโทรมาตร 9 แห่ง (September Datum Shifts) | `python analysis/common_datum_shift_correction.py` | `analysis/common_datum_shift_findings.md`<br>`analysis/common_datum_shift_summary.json` |
| `common_fetch_gulf_marine` | `analysis/common_fetch_gulf_marine.py` | `main` | active | ดึงข้อมูลคลื่น ความลึก และพยากรณ์น้ำทะเลอ่าวไทย (Gulf Marine & Wave Forecast) | `python analysis/common_fetch_gulf_marine.py` | — |
| `common_fetch_rain_stations` | `analysis/common_fetch_rain_stations.py` | `main` | active | ดึงข้อมูลฝนสถานีโทรมาตรอัตโนมัติทั่วประเทศ 4,593 จุด (National Rainfall Telemetry) | `python analysis/common_fetch_rain_stations.py` | — |
| `common_fetch_rid_swoc` | `analysis/common_fetch_rid_swoc.py` | `main` | active | เครื่องมือดึงข้อมูลอ่างเก็บน้ำและโทรมาตรจากระบบ SWOC / RID | `python analysis/common_fetch_rid_swoc.py` | — |
| `common_fetch_water_quality` | `analysis/common_fetch_water_quality.py` | `main` | active | ดึงข้อมูลคุณภาพน้ำและความเค็มปากแม่น้ำ (Estuary Salinity) | `python analysis/common_fetch_water_quality.py` | — |
| `common_fetch_weather_forecasts` | `analysis/common_fetch_weather_forecasts.py` | `main` | active | ดึงข้อมูลพยากรณ์อากาศและน้ำท่า ECMWF IFS และ GloFAS | `python analysis/common_fetch_weather_forecasts.py` | — |
| `fetch_gistda_flood` | `analysis/fetch_gistda_flood.py` | `main` | active | สคริปต์ดึงชั้นข้อมูลน้ำท่วมจาก GISTDA Disaster Platform API (2026) — ตัวเชื่อมโยงไปยัง goal6_fetch_gistda_flood.py | `python analysis/fetch_gistda_flood.py` | — |
| `fetch_khundan_fullyears` | `analysis/fetch_khundan_fullyears.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `fetch_khundan_training` | `analysis/fetch_khundan_training.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/fetch_khundan_training.py` | — |
| `fetch_khundan_training_2021_2022` | `analysis/fetch_khundan_training_2021_2022.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `fetch_khundan_training_2024_2025` | `analysis/fetch_khundan_training_2024_2025.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `fetch_multistation_levels` | `analysis/fetch_multistation_levels.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/fetch_multistation_levels.py` | — |
| `georef_corner_match` | `analysis/georef_corner_match.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `georef_fit` | `analysis/georef_fit.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `georef_gistda` | `analysis/georef_gistda.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/georef_gistda.py` | — |
| `gistda_georef_compare` | `analysis/gistda_georef_compare.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/gistda_georef_compare.py` | — |
| `gistda_pass_areas` | `analysis/gistda_pass_areas.py` | `main` | active | สรุปพื้นที่น้ำท่วมจาก attribute ของ shapefile GISTDA ราย pass → analysis/gistda_pass_areas_nn.json | `python analysis/gistda_pass_areas.py` | — |
| `goal2_khundan_22y_baseline` | `analysis/goal2_khundan_22y_baseline.py` | `main` | active | การวิเคราะห์พฤติกรรมการกักเก็บน้ำของเขื่อนขุนด่านปราการชล 22 ปี (2548–2569) | `python analysis/goal2_khundan_22y_baseline.py` | — |
| `goal2_khundan_22y_mass_balance` | `analysis/goal2_khundan_22y_mass_balance.py` | `main` | active | การปิดสมดุลมวลน้ำรายวัน 22 ปี เขื่อนขุนด่านปราการชล (2548–2569) | `python analysis/goal2_khundan_22y_mass_balance.py` | — |
| `goal2_nny_medium_dams` | `analysis/goal2_nny_medium_dams.py` | `main` | active | วิเคราะห์บทบาทอ่างเก็บน้ำขนาดกลาง 6 แห่งใน จ.นครนายก ช่วงน้ำท่วม 2569 | `python analysis/goal2_nny_medium_dams.py` | — |
| `goal4_counterfactual_model` | `analysis/goal4_counterfactual_model.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `goal4_feature_diagnostics` | `analysis/goal4_feature_diagnostics.py` | `main` | active | วินิจฉัยฟีเจอร์ของโมเดลทำนายระดับน้ำ Ny.7 — ตอบคำถามว่า "ablation วัดสัญญาณจริงหรือวัดความไม่เสถียร" | `(โมดูล — import ไม่รันตรง)` | — |
| `goal4_model_backtest_long` | `analysis/goal4_model_backtest_long.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `goal4_model_moisture_test` | `analysis/goal4_model_moisture_test.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `goal4_model_multistation` | `analysis/goal4_model_multistation.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `goal4_model_rainfcst_test` | `analysis/goal4_model_rainfcst_test.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `goal4_model_v1` | `analysis/goal4_model_v1.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `goal4_thachang_model` | `analysis/goal4_thachang_model.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/goal4_thachang_model.py` | — |
| `goal6_basin_rain` | `analysis/goal6_basin_rain.py` | `main` | active | ฝนเฉลี่ยทั้งลุ่ม (ถ่วงน้ำหนักตามพื้นที่) + ฝนรวมฤดู — รีวิว Sonnet A2 (12 ต.ค. 69) | `python -I analysis/goal6_basin_rain.py [--workers N]   (-I: ไม่โหลดโมดูลจากโฟลเดอร์ปัจจุบัน)` | `analysis/goal6/basin_rain.json`<br>`analysis/goal6/basin_rain.md` |
| `goal6_basin_readiness` | `analysis/goal6_basin_readiness.py` | `main` | active | เป้าหมาย 6 — sweep ความพร้อมข้อมูล 5 ลุ่มรอบแรก (ผู้ใช้ยืนยัน 10 ต.ค. 2569) | `python analysis/goal6_basin_readiness.py (ทำซ้ำได้ — จุดที่ตรวจแล้วข้าม)` | `analysis/goal6_basin_readiness.json`<br>`analysis/goal6_basin_readiness.md` |
| `goal6_bkk_sea_mask` | `analysis/goal6_bkk_sea_mask.py` | `main` | active | เป้าหมาย 6 — mask ทะเลบท กทม.: ตัดนอกตลิ่งน้ำขึ้นลงออกจากมาสก์น้ำ S1 ของ bkk_lower | `python analysis/goal6_bkk_sea_mask.py` | `analysis/goal6/bkk_lower/l2_sea_adjust.json`<br>`analysis/goal6/bkk_lower/l2_sea_adjust.md` |
| `goal6_c2_attribution` | `analysis/goal6_c2_attribution.py` | `main` | active | C.2 attribution — ผลิตตัวเลขทั้งชุด "เขื่อนผิดหรือฝนผิด" ลง JSON (แทน literal ใน builder) | `python analysis/goal6_c2_attribution.py` | `analysis/goal6/c2_attribution.json` |
| `goal6_dam_candidates` | `analysis/goal6_dam_candidates.py` | `main` | active | เป้าหมาย 6 — รายชื่อเขื่อนผู้สมัครทั่วประเทศ (ขนาดใกล้เคียง/ใหญ่กว่าเขื่อนขุนด่านปราการชล) | `python analysis/goal6_dam_candidates.py [--min-storage 200]` | `analysis/goal6_dam_candidates.json` |
| `goal6_dam_history_all` | `analysis/goal6_dam_history_all.py` | `main` | active | เป้าหมาย 6 — H1: ประวัติเขื่อนผู้สมัครที่ยังไม่ได้ดึง (เติมให้ครบ 24 แห่ง) → benchmark 2554 | `python analysis/goal6_dam_history_all.py` | `analysis/goal6/dam_history_all.json`<br>`analysis/goal6/dam_history_all.md`<br>`analysis/goal6_dam_candidates.json` |
| `goal6_dam_inflow` | `analysis/goal6_dam_inflow.py` | `main` | active | น้ำเข้า–ปล่อย–เก็บ รายเขื่อน 2554 vs 2569 เทียบประวัติ 22 ปี — แยก "ฝน/น้ำเข้า" ออกจาก "สถานะ/การเดินเขื่อน" | `python analysis/goal6_dam_inflow.py [--refresh] [--workers N]` | `analysis/goal6/dam_inflow.json`<br>`analysis/goal6/dam_inflow.md` |
| `goal6_downstream_tide` | `analysis/goal6_downstream_tide.py` | `main` | active | วิเคราะห์ระดับน้ำทะเลและน้ำหนุนปากแม่น้ำสายหลัก (Downstream Sea Levels & Tidal Dynamics) | `python analysis/goal6_downstream_tide.py` | `analysis/goal6/downstream_tide_findings.md`<br>`analysis/goal6/downstream_tide_summary.json` |
| `goal6_duration_maps` | `analysis/goal6_duration_maps.py` | `main` | active | แผนที่ระยะเวลาน้ำค้าง (หยาบ) — นับสัดส่วนฉากที่พิกัดมีน้ำ (น้ำรวม VH≤−20 ในที่ราบ) | `python analysis/goal6_duration_maps.py` | — |
| `goal6_exposure` | `analysis/goal6_exposure.py` | `main` | active | ชั้นผลกระทบ: ประชากรและถนน/ทางรถไฟในพื้นที่ที่ตรวจพบ (รวม = ขอบบน · เข้มงวด = ขอบล่างของ "น้ำใหม่ในฉาก") | `python analysis/goal6_exposure.py` | `analysis/goal6/exposure.json`<br>`analysis/goal6/exposure.md` |
| `goal6_fetch_gistda_flood` | `analysis/goal6_fetch_gistda_flood.py` | `main` | active | สคริปต์ดึงชั้นข้อมูลน้ำท่วมจาก GISTDA Disaster Platform API (2026) | `python analysis/goal6_fetch_gistda_flood.py` | `data/12_gistda_flood/.gistda_api.json` |
| `goal6_flood_maps` | `analysis/goal6_flood_maps.py` | `main` | active | แผนที่น้ำท่วมจากดาวเทียม 6 ลุ่ม — จากมาสก์น้ำ S1 ที่ประมวลผลแล้ว (stage-2 พีค) | `python analysis/goal6_flood_maps.py` | — |
| `goal6_l1_expand` | `analysis/goal6_l1_expand.py` | `main` | active | เป้าหมาย 6 — runner ขยาย L1 ทุกลุ่มตาม analysis/goal6/config.json (template จาก spike ป่าสัก/แม่กลอง) | `python analysis/goal6_l1_expand.py [--basin id,...]` | `analysis/goal6/config.json`<br>`data/02_thaiwater/raw/2026-10-09_canal_waterlevel.json`<br>`data/02_thaiwater/raw/2026-10-09_watergate_load.json` |
| `goal6_l1_followups` | `analysis/goal6_l1_followups.py` | `main` | active | เป้าหมาย 6 — ตามข้อเสนอที่ผู้ใช้เห็นด้วย (10 ต.ค. 69): (ก) ไขความหมาย URC เทมเพลตใน API | `python analysis/goal6_l1_followups.py` | `analysis/dam_khun_dan_daily_2013_2026.csv`<br>`analysis/goal6_l1_followups.json`<br>`analysis/goal6_l1_followups.md`<br>`data/22_goal6_network/raw/urc_template_check_2026.json` |
| `goal6_l3_coastal_harmonics` | `analysis/goal6_l3_coastal_harmonics.py` | `main` | active | แบบจำลองพยากรณ์ระดับน้ำเจ้าพระยาตอนล่างผสานฮาร์มอนิกน้ำขึ้น-น้ำลงดาราศาสตร์ (Astronomical Tidal Harmonics Model) | `python analysis/goal6_l3_coastal_harmonics.py` | `analysis/goal6/l3_coastal_harmonics_findings.md`<br>`analysis/goal6/l3_coastal_harmonics_summary.json` |
| `goal6_l3_model` | `analysis/goal6_l3_model.py` | `main` | active | เป้าหมาย 6 — L3: โมเดลทำนายระดับน้ำรายลุ่ม (วิธีเดียวกับ goal4_model_v1) | `python analysis/goal6_l3_model.py [--basin id,...]` | `analysis/goal6/config.json`<br>`analysis/goal6_basin_readiness.json` |
| `goal6_make_config` | `analysis/goal6_make_config.py` | `main` | active | เป้าหมาย 6 — สร้าง analysis/goal6/config.json (ข้อตกลง pre-register ต่อลุ่ม) | `python analysis/goal6_make_config.py` | `analysis/goal6/config.json`<br>`analysis/goal6_basin_readiness.json`<br>`analysis/goal6_dam_candidates.json`<br>`analysis/goal6_spike_maeklong_findings.md`<br>`analysis/goal6_spike_pasak_findings.md` |
| `goal6_national_medium_reservoirs` | `analysis/goal6_national_medium_reservoirs.py` | `main` | active | การวิเคราะห์โครงข่ายอ่างเก็บน้ำขนาดกลาง 461 แห่งทั่วประเทศ | `python analysis/goal6_national_medium_reservoirs.py` | — |
| `goal6_network_base` | `analysis/goal6_network_base.py` | `main` | active | เป้าหมาย 6 — ขั้น 5: ชั้นเครือข่ายฐานระดับชาติ — HydroBASINS + ESA WorldCover | `python analysis/goal6_network_base.py` | — |
| `goal6_network_nodes` | `analysis/goal6_network_nodes.py` | `main` | active | เป้าหมาย 6 — N1/N2 ฐาน: ผูก node ทั้งประเทศ (จุดวัด 199 + ปตร. 2,315) เข้าลุ่มย่อย HydroBASINS | `python analysis/goal6_network_nodes.py` | `analysis/goal6/network_nodes.json`<br>`analysis/goal6/network_nodes.md` |
| `goal6_pasak_24y_baseline` | `analysis/goal6_pasak_24y_baseline.py` | `main` | active | การวิเคราะห์พฤติกรรมการเดินเขื่อนป่าสักชลสิทธิ์ 24 ปี (2546–2569) | `python analysis/goal6_pasak_24y_baseline.py` | — |
| `goal6_prerelease_scenario` | `analysis/goal6_prerelease_scenario.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `goal6_pull_historical_estuary` | `analysis/goal6_pull_historical_estuary.py` | `main` | active | ดึงข้อมูลระดับน้ำและน้ำหนุนปากแม่น้ำย้อนหลังลึกที่สุดเท่าที่ระบบออนไลน์มี (Historical Estuary Data Ingestion) | `python analysis/goal6_pull_historical_estuary.py` | `analysis/goal6/historical_estuary_summary.json`<br>`data/22_goal6_network/_hashes.txt` |
| `goal6_rain_obs_2026` | `analysis/goal6_rain_obs_2026.py` | `main` | active | เป้าหมาย 6 — พยากรณ์ฝนย้อนหลัง (previous runs) ช่วงเหตุการณ์ 2569 ต่อจุดฝนลุ่ม | `python analysis/goal6_rain_obs_2026.py` | `analysis/goal6/config.json`<br>`analysis/goal6/rain_obs_2026.json`<br>`analysis/goal6/rain_obs_2026.md` |
| `goal6_rain_rarity` | `analysis/goal6_rain_rarity.py` | `main` | active | เป้าหมาย 6 — Q1: ฝนเหตุการณ์ 2569 หายากแค่ไหน (คาบคืนเชิงหยาบจาก POWER 1981–2026) | `python analysis/goal6_rain_rarity.py` | `analysis/goal6/rain_rarity.json`<br>`analysis/goal6/rain_rarity.md` |
| `goal6_rain_rarity_2554` | `analysis/goal6_rain_rarity_2554.py` | `main` | active | เป้าหมาย 6 — อันดับฝน 2554 จากแคช POWER เดียวกับ 2569 (ไม่ดาวน์โหลดใหม่) | `python analysis/goal6_rain_rarity_2554.py` | `analysis/goal6/rain_rarity_2554.json`<br>`analysis/goal6/rain_rarity_2554.md` |
| `goal6_rain_rarity_national` | `analysis/goal6_rain_rarity_national.py` | `main` | active | เป้าหมาย 6 — ฝน POWER ระดับชาติ: ความหายากฝน 7/30 วัน ครบ 199 จุดวัดในคลังระดับชาติ | `python analysis/goal6_rain_rarity_national.py` | `analysis/goal6/rain_rarity_national.json`<br>`analysis/goal6/rain_rarity_national.md` |
| `goal6_report_charts` | `analysis/goal6_report_charts.py` | `main` | active | กราฟหัวใจรายงาน 3+4 — ระดับน้ำเก็บเขื่อนเทียบเส้นกำกับ (rule curve) ปี 2554 และ 2569 | `python analysis/goal6_report_charts.py` | `analysis/goal6/dam_history_all.json`<br>`analysis/goal6/rain_rarity.json`<br>`data/22_goal6_network/raw/spike_ping_cp/c2_discharge_daily_sep2026.json`<br>`data/22_goal6_network/raw/spike_ping_cp/c2_sources_volumes.json`<br>`data/22_goal6_network/raw/spike_ping_cp/c2_vs_dam_releases_sep2026.json` |
| `goal6_s1_dem` | `analysis/goal6_s1_dem.py` | `main` | active | เป้าหมาย 6 — L2 ประกอบ: DEM GLO-30 ต่อลุ่ม → mask ที่ราบ <60 ม. (แบบนครนายก) | `python analysis/goal6_s1_dem.py` | `analysis/goal6/config.json` |
| `goal6_s1_download` | `analysis/goal6_s1_download.py` | `main` | active | เป้าหมาย 6 — ดาวน์โหลดคิว S1 GRDH-COG จาก CDSE ผ่าน S3 (credential ของผู้ใช้ในไฟล์ gitignored) | `python analysis/goal6_s1_download.py [--limit N] [--test-one]` | `data/22_goal6_network/.cdse_s3.json`<br>`data/22_goal6_network/raw/s1_queue/s1_queue.json` |
| `goal6_s1_landcover` | `analysis/goal6_s1_landcover.py` | `main` | active | แยกผลตรวจน้ำ Sentinel-1 ตามชนิดผิวดิน (ESA WorldCover 2021 10 ม.) + น้ำถาวร (JRC Global Surface Water) | `python analysis/goal6_s1_landcover.py` | `analysis/goal6/s1_landcover.json`<br>`analysis/goal6/s1_landcover.md` |
| `goal6_s1_queue` | `analysis/goal6_s1_queue.py` | `main` | active | เป้าหมาย 6 — คิวดาวน์โหลด Sentinel-1 GRDH ช่วงเหตุการณ์ 23 ก.ย.–2 ต.ค. 69 ครบ 5 ลุ่มรอบแรก | `python analysis/goal6_s1_queue.py` | `analysis/goal6_s1_queue.md`<br>`data/22_goal6_network/raw/s1_queue/s1_queue.json` |
| `goal6_s1_rule_validation` | `analysis/goal6_s1_rule_validation.py` | `main` | active | ตรวจความถูกต้องของกฎตัดน้ำ Sentinel-1 (รีวิว Sonnet 12 ต.ค. 69 · M1/R9) — ไม่ใช้ข้อมูลใหม่ | `python analysis/goal6_s1_rule_validation.py` | `analysis/goal6/s1_rule_validation.json`<br>`analysis/goal6/s1_rule_validation.md` |
| `goal6_s1_stage1` | `analysis/goal6_s1_stage1.py` | `main` | active | เป้าหมาย 6 — L2 ขั้นที่ 1: geocode + calibrate ฉาก S1 ทุกฉากบนกริด 30 ม.ต่อลุ่ม (ขนาน) | `python analysis/goal6_s1_stage1.py [--basin id] [--limit N] [--workers 8] [--job basin:scene]` | `data/22_goal6_network/derived/s1_stage1/grid_<basin>.json` |
| `goal6_s1_stage2_water` | `analysis/goal6_s1_stage2_water.py` | `main` | active | เป้าหมาย 6 — L2 ขั้นที่ 2: ตัดน้ำด้วยกฎ canonical (เทียบฉากก่อนเหตุการณ์ วงโคจรเดียวกัน) | `python analysis/goal6_s1_stage2_water.py [--basin id]` | `analysis/goal6/config.json` |
| `goal6_s2_queue` | `analysis/goal6_s2_queue.py` | `main` | active | เป้าหมาย 6 — คิว Sentinel-2 L2A (ตรวจยืนยนอิสระ + ภาพสีจริง) ต่อลุ่ม — ค้นจาก CDSE OData | `python analysis/goal6_s2_queue.py` | `analysis/goal6_s2_queue.md`<br>`data/22_goal6_network/raw/s2_queue/s2_queue.json` |
| `goal6_s2_validate` | `analysis/goal6_s2_validate.py` | `main` | active | เป้าหมาย 6 — L2 ตรวจยืนยันอิสระ: S2 MNDWI เทียบมาสก์น้ำ S1 บนกริดเดียวกัน | `python analysis/goal6_s2_validate.py` | `analysis/goal6/s2_validation.json`<br>`analysis/goal6/s2_validation.md` |
| `goal6_scan_banned_terms` | `analysis/goal6_scan_banned_terms.py` | `main` | active | สแกนรายงานที่ 3 — หาคำทับศัพท์/ศัพท์เทคนิคที่ยังไม่อนุมัติคำไทยแทน | `python analysis/goal6_scan_banned_terms.py` | `report/goal6_banned_terms_candidates.json`<br>`report/ระลอกปลายกย2569.html` |
| `goal6_screen_basins` | `analysis/goal6_screen_basins.py` | `main` | active | เป้าหมาย 6 — screen เหตุการณ์ท่วมจริงหน้าฝน 2569 ต่อลุ่ม (เกณฑ์ pre-register) | `python analysis/goal6_screen_basins.py` | `analysis/goal6_dam_candidates.json`<br>`analysis/goal6_screen_2026_findings.md`<br>`analysis/goal6_screen_2026_summary.json`<br>`data/02_thaiwater/raw/2026-10-10_waterlevel_load.json` |
| `goal6_screen_findings` | `analysis/goal6_screen_findings.py` | `main` | active | เป้าหมาย 6 — สรุปผล screen หน้าฝน 2569 ต่อลุ่ม -> analysis/goal6_screen_2026_findings.md | `python analysis/goal6_screen_findings.py` | `analysis/goal6_screen_2026_findings.md`<br>`analysis/goal6_screen_2026_summary.json` |
| `goal6_spike_maeklong_l1` | `analysis/goal6_spike_maeklong_l1.py` | `main` | active | เป้าหมาย 6 — spike ลุ่มที่สอง L1: แม่กลอง (ผู้ใช้ยืนยันรอบแรก 10 ต.ค. 69) | `python analysis/goal6_spike_maeklong_l1.py` | `analysis/goal6_screen_2026_summary.json`<br>`analysis/goal6_spike_maeklong.json`<br>`analysis/goal6_spike_maeklong_findings.md` |
| `goal6_spike_pasak_l1` | `analysis/goal6_spike_pasak_l1.py` | `main` | active | เป้าหมาย 6 — spike ลุ่มแรก L1: ป่าสัก (ผู้ใช้ยืนยันรอบแรก 5 ลุ่ม 10 ต.ค. 69) | `python analysis/goal6_spike_pasak_l1.py` | `analysis/dam_khun_dan_daily_2013_2026.csv`<br>`analysis/goal6_basin_readiness.json`<br>`analysis/goal6_screen_2026_summary.json`<br>`analysis/goal6_spike_pasak.json`<br>`analysis/goal6_spike_pasak_findings.md` |
| `goal7_acid_sulfate_soil_analysis` | `analysis/goal7_acid_sulfate_soil_analysis.py` | `main` | active | การประเมินปริมาณดินกรดกำมะถันและไพไรต์ตามแนวขุดคลองเจ้าพระยา 2 | `python analysis/goal7_acid_sulfate_soil_analysis.py` | `analysis/goal7/acid_sulfate_soil_summary.json` |
| `goal7_ayutthaya_dqdh_rating` | `analysis/goal7_ayutthaya_dqdh_rating.py` | `main` | active | การสอบเทียบความสัมพันธ์ระดับ–ปริมาณน้ำ (dQ/dh) ลุ่มเจ้าพระยาตอนล่าง (อยุธยา–บางไทร) | `python analysis/goal7_ayutthaya_dqdh_rating.py` | `analysis/goal7/ayutthaya_dqdh_rating_summary.json` |
| `goal7_bangban_bangsai_comparison` | `analysis/goal7_bangban_bangsai_comparison.py` | `main` | active | เป้าหมาย 7 — การวิเคราะห์เปรียบเทียบเชิงวิศวกรรมและเศรษฐศาสตร์การก่อสร้าง: | `python analysis/goal7_bangban_bangsai_comparison.py` | `analysis/goal7/bangban_bangsai_comparison.json` |
| `goal7_basin_containment` | `analysis/goal7_basin_containment.py` | `main` | active | เป้าหมาย 7 — ตรวจว่าแนวคลอง (แนวไม่เป็นทางการ) อยู่ในลุ่มน้ำใดบ้าง ตามขอบเขต 22 ลุ่มน้ำของ สทนช. | `python analysis/goal7_basin_containment.py` | `analysis/goal7/basin_containment.json`<br>`data/32_goal7_chaophraya2/derived/centerline.geojson`<br>`data/32_goal7_chaophraya2/official_onwr_waterchart/miswc22.json` |
| `goal7_clean_alignment` | `analysis/goal7_clean_alignment.py` | `main` | active | เป้าหมาย 7 — ทำความสะอาดแนวคลองเจ้าพระยา2 จาก My Maps (ผู้ใช้สร้าง) | `python analysis/goal7_clean_alignment.py` | — |
| `goal7_dam_to_gulf_hydraulics` | `analysis/goal7_dam_to_gulf_hydraulics.py` | `main` | active | เป้าหมาย 7 — การวิเคราะห์เส้นทางชลศาสตร์ เวกเตอร์การไหล และเวลาเดินทางจากเขื่อนสู่ปากอ่าวไทย (Dam-to-Gulf Hydraulic Corridors) | `python analysis/goal7_dam_to_gulf_hydraulics.py` | `analysis/goal7/dam_to_gulf_summary.json` |
| `goal7_eia_structs` | `analysis/goal7_eia_structs.py` | `main` | active | เป้าหมาย 7 — ดึงตาราง "บัญชีอาคารประกอบของคลองระบายน้ำหลาก" (ตาราง 2.3.2-3) จากรายงานผลกระทบสิ่งแวดล้อม 3 ฉบับ | `python analysis/goal7_eia_structs.py` | `analysis/goal7/eia_structs.json`<br>`analysis/goal7/structures_all.csv` |
| `goal7_fabdem_compare` | `analysis/goal7_fabdem_compare.py` | `main` | active | เป้าหมาย 7 — เทียบความสูงพื้นดินตามแนวคลอง: FABDEM (ดินเปล่า) vs Copernicus GLO-30 (ผิวสูงสุด) vs ค่าอ่านจากรูปตัดตามยาว | `python analysis/goal7_fabdem_compare.py` | `analysis/goal7/fabdem_compare.json` |
| `goal7_mitrearth_layers` | `analysis/goal7_mitrearth_layers.py` | `main` | active | เป้าหมาย 7 — ชั้นข้อมูลมิตรเอิร์ธ: ขอบเขตน้ำท่วม GISTDA 2548–2554 เทียบ 2569 · ลุ่มน้ำย่อยเทียบ PK-AT-4 · เส้นชั้น 1 ม. เทียบ FABDEM/Copernicus | `python analysis/goal7_mitrearth_layers.py` | `analysis/goal7/mitrearth_layers_summary.json` |
| `goal7_interbasin_transfer_vectors` | `analysis/goal7_interbasin_transfer_vectors.py` | `main` | active | การวิเคราะห์เวกเตอร์การผันน้ำข้ามลุ่มรายคลองเชื่อมโยง (Inter-basin Transfer Vectors) | `python analysis/goal7_interbasin_transfer_vectors.py` | `analysis/goal7/interbasin_transfer_findings.md`<br>`analysis/goal7/interbasin_transfer_summary.json`<br>`data/02_thaiwater/raw/2026-10-09_canal_waterlevel.json`<br>`data/02_thaiwater/raw/2026-10-09_watergate_load.json` |
| `goal7_legal_and_nuclear_assessment` | `analysis/goal7_legal_and_nuclear_assessment.py` | `main` | active | การวิเคราะห์ข้อกฎหมายเวนคืนที่ดินเพื่อพาณิชย์ และการประเมินความปลอดภัยศูนย์วิจัยนิวเคลียร์องครักษ์ | `python analysis/goal7_legal_and_nuclear_assessment.py` | `analysis/goal7/legal_and_nuclear_summary.json` |
| `goal7_ongkharak_hydraulics` | `analysis/goal7_ongkharak_hydraulics.py` | `main` | active | เป้าหมาย 7 — การวิเคราะห์ชลศาสตร์ สมดุลมวลน้ำ และเวกเตอร์การไหลสุทธิทุ่งองครักษ์ (ตุลาคม 2569) | `python analysis/goal7_ongkharak_hydraulics.py` | `data/02_thaiwater/raw/2026-10-09_watergate_load.json` |
| `goal7_scan_eia2569` | `analysis/goal7_scan_eia2569.py` | `main` | active | เป้าหมาย 7 — แผนที่การอ่านรายงานผลกระทบสิ่งแวดล้อม ฉบับ 2569 (4 เล่ม): นับหน้าที่พบคำสำคัญ ใช้บอกว่าส่วนสำคัญอยู่หน้าใดและยังไม่ได้อ่าน | `(โมดูล — import ไม่รันตรง)` | `analysis/goal7/eia2569_scan.json` |
| `goal7_waterchart_overlay` | `analysis/goal7_waterchart_overlay.py` | `main` | active | เป้าหมาย 7 — ซ้อนแนวคลองเจ้าพระยา2 กับ "ผังน้ำ" และขอบเขตน้ำท่วมของ สทนช. (3 ลุ่มน้ำ: บางปะกง · เจ้าพระยา · ป่าสัก) | `python analysis/goal7_waterchart_overlay.py` | `analysis/goal7/waterchart_overlay.json` |
| `hecras_lite_channel` | `analysis/hecras_lite_channel.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `landsat_water` | `analysis/landsat_water.py` | `main` | active | ตรวจน้ำท่วมด้วย Landsat optical 30 ม. (MNDWI) เทียบกับ S1 ของเรา + GISTDA บนกริดเดียวกัน | `python analysis/landsat_water.py   (ต้องมี data/manual/LC0* + data/13/derived/*)` | — |
| `national_pull_waterlevels` | `analysis/national_pull_waterlevels.py` | `main` | active | คลังข้อมูลระดับชาติ — ระดับน้ำรายชั่วโมงทุกจุดวัดสำคัญ (199 จุด) × 2020–2026 | `python analysis/national_pull_waterlevels.py [--workers 6]` | `data/02_thaiwater/raw/2026-10-10_waterlevel_load.json` |
| `qa5_rain_drainage_counterfactual` | `analysis/qa5_rain_drainage_counterfactual.py` | `main` | active | QA5: 18-day rain (12-29 Sep 2026) -> river level/drainage analysis | `(โมดูล — import ไม่รันตรง)` | — |
| `rain_window` | `analysis/rain_window.py` | `main` | active | หน้าต่างฝนสะสม n วัน สำหรับโมเดลทำนายระดับน้ำ Ny.7 — รวมตรรกะไว้ไฟล์เดียว | `(โมดูล — import ไม่รันตรง)` | — |
| `rid_cross_section_extract` | `analysis/rid_cross_section_extract.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/rid_cross_section_extract.py` | — |
| `rid_cross_section_hydraulics` | `analysis/rid_cross_section_hydraulics.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/rid_cross_section_hydraulics.py` | — |
| `rid_cross_section_plot` | `analysis/rid_cross_section_plot.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `rid_cross_section_stage_rating` | `analysis/rid_cross_section_stage_rating.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/rid_cross_section_stage_rating.py` | — |
| `run_all` | `analysis/run_all.py` | `main` | active | run_all — รัน pipeline ทั้งระบบตามลำดับมาตรฐาน จบในคำสั่งเดียว | `python analysis/run_all.py [--fast] [--with-backtest]   (--fast = ข้าม backtest ยาว)` | `analysis/attribution_share.json`<br>`analysis/gistda_pass_areas_nn.json`<br>`analysis/goal4_counterfactual_summary.json`<br>`analysis/goal4_model_backtest_long.json`<br>`analysis/goal4_model_v1_results.json`<br>`analysis/river_cross_sections.json` |
| `s1_change_detect` | `analysis/s1_change_detect.py` | `main` | active | Change-detection flood mapping — กฎที่ตีพิมพ์ในรายงาน (3 เงื่อนไข + opening 3×3) | `python analysis/s1_change_detect.py` | — |
| `s1_masks` | `analysis/s1_masks.py` | `main` | active | Build common masks (province, districts, lowland DEM) on the S1 30 m grid. | `(โมดูล — import ไม่รันตรง)` | — |
| `s1_merge_scenes` | `analysis/s1_merge_scenes.py` | `main` | active | โมเสก 2 slice ของฉาก S1 ที่ทับกัน → ไฟล์ `*_full_*` ที่ s1_change_detect.py ใช้ | ``python analysis/s1_merge_scenes.py`          # สร้าง/ทับ *_full_* ทั้ง 2 วัน` | — |
| `s1_pairs_animation` | `analysis/s1_pairs_animation.py` | `main` | active | Paired same-orbit change detection for the 3 new dates + stats + frame npys. | `(โมดูล — import ไม่รันตรง)` | — |
| `s1_peak_flood_map` | `analysis/s1_peak_flood_map.py` | `main` | active | Peak flood map: 27 Sep 2026 18:28 change-detection extent on DEM hillshade. | `(โมดูล — import ไม่รันตรง)` | — |
| `s1_process` | `analysis/s1_process.py` | `main` | active | Sentinel-1 GRDH COG processing for Nakhon Nayok flood mapping. | `python analysis/s1_process.py` | — |
| `s2_truecolor_process` | `analysis/s2_truecolor_process.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `s2_water` | `analysis/s2_water.py` | `main` | active | ตรวจน้ำท่วมด้วย Sentinel-2 optical (MNDWI) เทียบกับ S1 ของเรา บนกริดเดียวกัน — 2 ต.ค. 69 | `(โมดูล — import ไม่รันตรง)` | — |
| `thachang_leadtime` | `analysis/thachang_leadtime.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `python analysis/thachang_leadtime.py` | — |
| `goal6_build_report3_draft` | `report/goal6_build_report3_draft.py` | `main` | active | เป้าหมาย 6 — สร้างร่างรายงานที่ 3 v0.1 (L1 ครบ · L2/L3 เป็น placeholder) | `python report/goal6_build_report3_draft.py` | `report/ระลอกปลายกย2569.html` |
| `goal6_build_report4_draft` | `report/goal6_build_report4_draft.py` | `main` | active | สร้างร่างรายงานที่ 4 — benchmark 2554 vs 2569 (ระบบเดียว × หลายปี) | `python report/goal6_build_report4_draft.py` | `report/ชุดเทียบมาตรฐาน2554.html` |
| `goal6_reportlib` | `report/goal6_reportlib.py` | `main` | active | reportlib (เป้าหมาย 6) — builder บาง ๆ ใช้ร่วมทุกรายงาน (เสนอ §11 · เห็นด้วย 10 ต.ค. 69) | `(โมดูล — import ไม่รันตรง)` | — |
| `goal7_blocks` | `report/goal7_blocks.py` | `main` | active | ชิ้นส่วนร่วมของรายงาน 7 (ประชาชน) และรายงาน 8 (วิชาการ) — ตารางที่สองฉบับต้องตรงกันเสมอ | `(โมดูล — import ไม่รันตรง)` | — |
| `goal7_build_academic` | `report/goal7_build_academic.py` | `main` | active | สร้างรายงานที่ 8 ฉบับวิชาการ — คลองเจ้าพระยา2 (ข้อมูล วิธี ผล ข้อจำกัด ตรวจสอบย้อนกลับ) | `python analysis/goal7_analysis.py && python report/goal7_build_academic.py` | `report/คลองเจ้าพระยา2_วิชาการ.html` |
| `goal7_build_public` | `report/goal7_build_public.py` | `main` | active | สร้างรายงานที่ 7 ฉบับประชาชน — คลองเจ้าพระยา2 (คลองระบายน้ำหลากชัยนาท–ป่าสัก–อ่าวไทย) กับนครนายก | `python analysis/goal7_analysis.py && python report/goal7_build_public.py` | `report/คลองเจ้าพระยา2_ประชาชน.html` |
| `goal7_common` | `report/goal7_common.py` | `main` | active | ส่วนกลางของรายงานเจ้าพระยา2 (ฉบับประชาชน/ฉบับวิชาการ): ข้อมูลจาก canonical + กราฟ | `(โมดูล — import ไม่รันตรง)` | `analysis/goal7/waterchart_clip.geojson`<br>`analysis/goal7/waterchart_overlay.json` |
| `goal7_engine` | `report/goal7_engine.py` | `main` | active | เอ็นจินรายงานเป้าหมาย 7 — ทะเบียนหัวข้อ/คำถามด้วยรหัสคงที่ (key) · เลขอัตโนมัติ · อ้างอิงข้ามฉบับ | `(โมดูล — import ไม่รันตรง)` | — |
| `make_x_charts_thai` | `report/make_x_charts_thai.py` | `main` | active | (ไม่มีคำอธิบายในหัวไฟล์ — ต้องเติม) | `(โมดูล — import ไม่รันตรง)` | — |
| `report_assets` | `report/report_assets.py` | `main` | active | Generate all chart/frame PNGs for the public HTML report. | `(โมดูล — import ไม่รันตรง)` | — |
| `goal7_source_constants` | `analysis/goal7_source_constants.py` | `main` | active | ตัวโหลดค่าคงที่นำเข้าที่มีแหล่งอ้างอิง (source_constants.json) — สคริปต์เรียก value('<id>') แทนพิมพ์ตัวเลข | `(โมดูล — import)` | — |
| `goal7_verify_constants` | `analysis/goal7_verify_constants.py` | `main` | active | ตรวจค่าคงที่กับชั้นข้อความ PDF EIA และภาพหลักฐาน (แฮช) → verified/failed/assumption/conflict | `python analysis/goal7_verify_constants.py` | `analysis/goal7/source_constants_verification.json` |
| `goal7_ocr_coverage` | `analysis/goal7_ocr_coverage.py` | `main` | active | วัดความครอบคลุม OCR ของเล่ม EIA 2569 (หน้าสแกน/หน้ารูปเทียบผล Typhoon ที่ใช้ได้) และสร้างรายการหน้าค้าง | `python analysis/goal7_ocr_coverage.py` | `analysis/goal7/ocr_coverage.json` |
| `goal7_typhoon_queue_eia` | `analysis/goal7_typhoon_queue_eia.py` | `typhoon_env` | active | คิว Typhoon-OCR ของเล่ม EIA 2569 ตามรายการหน้าค้าง (หน้าสแกนก่อน แล้วหน้ารูป) 2 worker บน GPU | `E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_typhoon_queue_eia.py --workers 2` | `data/32_goal7_chaophraya2/typhoon_ocr/eia2569_<เล่ม>/pages.jsonl` |
| `quantity_registry` | `tools/quantity_registry.py` | `main` | active | ตรวจทะเบียนตัวตนของปริมาณ (ชื่อ·ขอบเขต·นิยาม·หน่วย·ชนิดที่มา) กับ canonical และค่าคงที่ต้นทาง · ส่งต่อสถานะถูกโต้แย้ง | `python tools/quantity_registry.py` | — |
| `goal7_ongkharak_connected_fill` | `analysis/goal7_ongkharak_connected_fill.py` | `main` | active | เป้าหมาย 7 (R7-04) — น้ำท่วมแอ่งองครักษ์แบบเชื่อมต่อลำน้ำ + ผิวน้ำลาดตามระยะ เทียบถังเติมน้ำเดิมกับมาสก์ดาวเทียม (Copernicus/FABDEM) | `python analysis/goal7_ongkharak_connected_fill.py` | `analysis/goal7/ongkharak_connected_fill_summary.json` |
| `goal7_official_geometry` | `analysis/goal7_official_geometry.py` | `main` | active | รวมมิติทางการของคลองเจ้าพระยา 2 (รูปตัด 3 ช่วง · ระดับตามยาว · อาคาร 99 แถว · แนวจากหมุด กม.) เป็นไฟล์เดียวสำหรับแบบจำลอง 3 มิติ | `python analysis/goal7_official_geometry.py` | `analysis/goal7/official_geometry.json` |
| `goal7_build_3d_model` | `analysis/goal7_build_3d_model.py` | `main` | active | สร้างแบบจำลอง 3 มิติคลองเจ้าพระยา 2 (สคริปต์ SketchUp .rb + OBJ + ตัวดูเบราว์เซอร์) จากมิติทางการ | `python analysis/goal7_build_3d_model.py` | `report/models/chaophraya2_sketchup.rb`<br>`report/models/chaophraya2.obj`<br>`report/models/chaophraya2_viewer.html` |
| `goal7_rejection_letter_items` | `analysis/goal7_rejection_letter_items.py` | `main` | active | ถอดโครงหนังสือ สผ. ทส 1010.6/2233 (วันที่ · 21 หัวข้อ · ข้อย่อย) จากผล Typhoon-OCR ใช้ตรวจเลขข้ออ้างอิงในรายงาน | `python analysis/goal7_rejection_letter_items.py` | `analysis/goal7/rejection_letter_items.json` |
| `goal7_mitrearth_provinces` | `analysis/goal7_mitrearth_provinces.py` | `main` | active | ชั้นมิตรเอิร์ธรายจังหวัดลุ่มเจ้าพระยาตอนล่าง 11 จังหวัด: น้ำท่วม GISTDA 2548–2554 รายปี · ลุ่มน้ำย่อย · เทียบน้ำท่วม 2569 | `python analysis/goal7_mitrearth_provinces.py` | `analysis/goal7/mitrearth_provinces_summary.json` |
| `goal7_mitrearth_dempro` | `analysis/goal7_mitrearth_dempro.py` | `main` | active | DEM 5 ม. (DEMPro) ของมิตรเอิร์ธนครนายก: ขอบเขต · ส่วนต่างเทียบ FABDEM/Copernicus · ทดสอบถังเติมน้ำเทียบเรดาร์ 2569 | `python analysis/goal7_mitrearth_dempro.py` | `analysis/goal7/mitrearth_dempro_summary.json` |
| `goal7_mitrearth_thailand` | `analysis/goal7_mitrearth_thailand.py` | `main` | active | ชุดมิตรเอิร์ธระดับประเทศ: ตรวจความครบ · สถานีอุทกวิทยา กช. · จุดร่องน้ำตัดถนน · หมู่บ้านพร้อมระดับพื้น ใกล้แนวคลอง | `python analysis/goal7_mitrearth_thailand.py` | `analysis/goal7/mitrearth_thailand_summary.json`<br>`analysis/goal7/rid_hydro_stations_study_area.csv`<br>`analysis/goal7/stream_road_crossings_corridor.csv` |
| `goal7_mitrearth_national` | `analysis/goal7_mitrearth_national.py` | `main` | active | ชุดมิตรเอิร์ธฉบับสมบูรณ์: น้ำท่วม GISTDA 15 ปีตลอดแนวคลอง · เทียบ 2569 · ระดับน้ำทะเลสูงขึ้น · DEMPro 5 ม. เทียบเส้นดิน EIA · บัญชีชั้นข้อมูล 77 จังหวัด | `python analysis/goal7_mitrearth_national.py` | `analysis/goal7/mitrearth_national_summary.json` |
| `goal7_dem_bias_correction` | `analysis/goal7_dem_bias_correction.py` | `main` | active | ปรับ FABDEM ให้ใกล้ DEM 5 ม. (DEMPro) ในที่ราบต่ำ ตรวจนอกตัวอย่างและกับเส้นดิน EIA ตลอดแนวคลอง · ทดสอบถังเติมน้ำองครักษ์ | `python analysis/goal7_dem_bias_correction.py` | `analysis/goal7/dem_bias_correction.json` |
| `goal7_dem_waterline_test` | `analysis/goal7_dem_waterline_test.py` | `main` | active | ทดสอบ DEM 3 ชุดด้วยขอบน้ำท่วมเรดาร์ (ความสูงตามขอบควรรวมกลุ่มแคบ) · หลักฐานอิสระเสริมเส้นดิน EIA | `python analysis/goal7_dem_waterline_test.py` | `analysis/goal7/dem_waterline_test.json` |

### ลงทะเบียนอัตโนมัติ รอทบทวน (0 รายการ · สถานะ `unreviewed`)

> คำอธิบายมาจาก docstring บรรทัดแรกโดยอัตโนมัติ ยังไม่มีคนยืนยันสถานะ/ผลลัพธ์ — เปลี่ยนสถานะเป็น `active`/`deprecated` เมื่อทบทวนแล้ว

| id | ไฟล์ | env | ชนิด | คำอธิบาย (จาก docstring) |
|---|---|---|---|---|

รวม 3 สภาพแวดล้อม · 163 เครื่องมือที่ลงทะเบียน (สคริปต์อื่นที่ยังไม่ลงทะเบียนดูด้วย `python tools/doctor.py --list-unregistered`)

<!-- END GENERATED: tool-registry -->

## สิ่งที่ *ไม่* ต้องติดตั้ง

- ไม่ต้องมี API key สำหรับ NASA POWER และ Open-Meteo (Historical Forecast)
- `khundan-tele.rid.go.th` และ `api-v3.thaiwater.net` เปิดให้ GET/POST โดยไม่ต้องยืนยันตัว
- Flood Hub API และตารางเปิดบานรายชั่วโมง สช.9 ยัง**ไม่มี** — เป็นช่องว่างของข้อมูลภายนอก
  ไม่ใช่ปัญหาสภาพแวดล้อม (รายการ FOI อยู่ใน START_HERE.md §8)
