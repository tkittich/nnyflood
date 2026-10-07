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
python -m pytest tests/ -q          # ต้องได้ 19 passed
```

## กับดักสภาพแวดล้อมที่เจอจริงในโปรเจคนี้

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
   ที่ Python ฝั่ง Windows อ่านไม่ได้ ให้เขียนลงไฟล์ในโปรเจคแทน (เช่น `.ov_tmp.json`)

5. **ชื่อแพ็กเกจ ≠ ชื่อโมดูล (`pyshp`)** — ติดตั้งด้วยชื่อ `pyshp` แต่ import ด้วย `import shapefile`
   · `import pyshp` **ล้มเหลว** (ตรวจแล้ว: `ModuleNotFoundError: No module named 'pyshp'`
   ขณะที่ `import shapefile` คืนเวอร์ชัน 3.1.6) — อย่าเขียน `import pyshp` ในสคริปต์ใหม่

## สิ่งที่ *ไม่* ต้องติดตั้ง

- ไม่ต้องมี API key สำหรับ NASA POWER และ Open-Meteo (Historical Forecast)
- `khundan-tele.rid.go.th` และ `api-v3.thaiwater.net` เปิดให้ GET/POST โดยไม่ต้องยืนยันตัว
- Flood Hub API และตารางเปิดบานรายชั่วโมง สช.9 ยัง**ไม่มี** — เป็นช่องว่างของข้อมูลภายนอก
  ไม่ใช่ปัญหาสภาพแวดล้อม (รายการ FOI อยู่ใน START_HERE.md §8)
