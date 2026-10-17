# แผนงานการพัฒนาและยกระดับระบบฉบับสมบูรณ์ (Implementation Plan)
## การบูรณาการรายงาน 1–2, แผนที่เชิงโต้ตอบบน GitHub Pages, เมทริกซ์ความเสี่ยงน้ำหลากปะทะน้ำหนุน, และ GitHub Actions CI

> วันที่: 17 ตุลาคม 2569  
> สถานะ: กำลังดำเนินการ (In Progress)  
> เป้าหมาย: ยกระดับคลังข้อมูลสู่ระดับ Production Ready รองรับการเผยแพร่สาธารณะบน GitHub Pages พร้อมระบบตรวจสอบอัตโนมัติ

---

## 1. วัตถุประสงค์และขอบเขตงาน (Objectives & Scope)

ดำเนินงาน 4 ด้านหลักเพื่อยกระดับระบบให้เป็นเอกภาพและครอบคลุมทุกมิติ:

1. **ส่วนที่ 1: ระบบตรวจสอบอัตโนมัติบนคลาวด์ (GitHub Actions CI Workflow)**
   - สร้าง `.github/workflows/ci.yml` รัน `tools/verify_all.py` (สารบัญ, SHA-256 ข้อมูลดิบ, ภาษาไทย/Typo Registry, pytest ครบ 100%) อัตโนมัติทุก push/PR บน GitHub
2. **ส่วนที่ 2: การอัปเกรดรายงานที่ 1 และ 2 (ลุ่มน้ำนครนายก)**
   - บูรณาการผลวิเคราะห์ชลศาสตร์ 1D Hydrodynamic Routing (อัตราน้ำล้นตลิ่งแท้จริง $666.3\ m^3/s$ ที่ Ny.1B และ $617.4\ m^3/s$ ที่ Ny.7, เวลาเดินทางคลื่นน้ำ 7.4 ชม.)
   - บูรณาการเส้นฐาน 22 ปีเขื่อนขุนด่านฯ (น้ำสูงสุดเร็วกว่าปกติ 40 วัน) และสมดุลน้ำ 6 อ่างขนาดกลาง จ.นครนายก (การล้นของอ่างทรายทองและวังบอน)
   - อัปเดต `analysis/build_canonical_numbers.py` สู่ `analysis/canonical_numbers.json` และเรนเดอร์ในเล่มรายงาน 1 และ 2
3. **ส่วนที่ 3: เมทริกซ์ประเมินความเสี่ยงน้ำหลากปะทะน้ำหนุน (Compound Flood Risk Matrix)**
   - สร้างสคริปต์ `analysis/compound_flood_risk.py` จำลองปฏิสัมพันธ์ระหว่างน้ำหลากจากตอนบน (C.13 เขื่อนเจ้าพระยา + S.26 เขื่อนป่าสักฯ) กับรอบน้ำเกิดสูงสุด (Spring Tide CPY015) และแรงต้านคลื่นลมทะเลอ่าวไทย (SWAN)
   - สร้างกราฟวิเคราะห์ความเสี่ยง `report/assets/compound_flood_risk_matrix.png` และสรุปตัวเลขทางการ
4. **ส่วนที่ 4: แผนที่สืบค้นเชิงโต้ตอบบนหน้าพอร์ทัลหลัก (`index.html` Interactive Atlas บน GitHub Pages)**
   - สร้างข้อมูลเวกเตอร์ GeoJSON สำหรับแนวคลองเจ้าพระยา 2 (111 กม.), สถานีโทรมาตรหลัก, เขื่อนและอ่างเก็บน้ำ 461 แห่ง
   - พัฒนาคอมโพเนนต์ Leaflet.js แบบ Static Client-side 100% บน `index.html` (สลับดู 3 เสาหลัก, คลิกดูสถานะและดัชนีความเค้น, โหลดเร็ว ไม่ต้องพึ่งพาเซิร์ฟเวอร์หลังบ้าน)
5. **การกำกับดูแลและบำรุงรักษาระบบ (System Maintenance & Verification)**
   - ลงทะเบียนไฟล์ใหม่ใน `catalog.py` และ `docs/PROJECT_MAP.md`
   - รัน `tools/verify_all.py` ผ่าน 100% และจัดเก็บประวัติ git commit สะอาด

---

## 2. ขั้นตอนการดำเนินงานโดยละเอียด (Step-by-Step Execution Plan)

### ขั้นที่ 1: ติดตั้ง GitHub Actions CI (`.github/workflows/ci.yml`)
- กำหนด workflow ทำงานบน `ubuntu-latest` และ `windows-latest` (หรือ ubuntu-latest เพื่อความเร็ว)
- ติดตั้ง Python 3.11/3.12 ตาม `requirements.txt`
- รัน `python tools/verify_all.py` รับประกัน zero regression

### ขั้นที่ 2: บูรณาการข้อมูลใหม่และปรับปรุงรายงาน 1 และ 2 (เป้าหมาย 1–5)
- แก้ไข `analysis/build_canonical_numbers.py`:
  - ดึงข้อมูลจาก `analysis/hydraulic_1d_routing_summary.json`
  - ดึงข้อมูลจาก `analysis/goal2_khundan_22y_summary.json`
  - ดึงข้อมูลจาก `analysis/goal2_nny_medium_dams_summary.json`
  - เพิ่มนิยามใน `definitions`
- ปรับปรุง `report/build_report_html.py` (รายงาน 1) และ `report/build_expert_report.py` (รายงาน 2)
- Rebuild รายงานทั้งสองเล่ม และทดสอบความสม่ำเสมอของตัวเลข

### ขั้นที่ 3: พัฒนาแบบจำลองประเมินความเสี่ยงน้ำหลากปะทะน้ำหนุน (Compound Flood Risk)
- สร้าง `analysis/compound_flood_risk.py`:
  - ฐานข้อมูล: สถิติน้ำท่า C.13, S.26, ระดับน้ำสะพานกรุงเทพ CPY015, คลื่น SWAN
  - คำนวณตารางเมทริกซ์ 2 มิติ (อัตราน้ำหลากตอนบน 1,500–3,500 $m^3/s$ $\times$ ระดับน้ำทะเลหนุนปากอ่าว +1.5 ถึง +2.5 ม.รทก.)
  - ระบุระดับน้ำคาดการณ์ที่สถานี C.12 สามเสน และพื้นที่เสี่ยงน้ำล้นคัน กทม.
  - บันทึก `analysis/compound_flood_risk_summary.json` และพล็อต `report/assets/compound_flood_risk_matrix.png`

### ขั้นที่ 4: พัฒนา Interactive GIS Atlas บน `index.html` รองรับ GitHub Pages
- จัดเตรียมโครงสร้าง GeoJSON / JSON น้ำหนักเบาใน `report/assets/gis/`:
  - `chaophraya2_route.geojson`: แนวคลอง 111 กม. พร้อมจุดตัดไซฟอน 34 จุด
  - `key_stations.json`: พิกัดสถานีโทรมาตรหลัก (Ny.1B, Ny.7, C.2, C.13, C.12, CPY015)
  - `dams_overview.json`: เขื่อนหลัก 24 แห่งและสถิติอ่างขนาดกลาง
- ออกแบบ UI แผนที่ใน `index.html`:
  - ใช้ Leaflet.js v1.9.4 ผ่าน CDN (พร้อม Fallback)
  - ธีมทันสมัย สไตล์ Dark/Light สอดคล้องกับพอร์ทัล
  - แผงควบคุมเลเยอร์ (Layer Switcher):
    1. เสาที่ 1: ลุ่มน้ำนครนายก (ลำน้ำ, สถานีวัด, ขอบเขตน้ำท่วม)
    2. เสาที่ 2: 6 ลุ่มน้ำระดับชาติ (เขื่อนใหญ่-กลาง, ลิ่มความเค็ม, คลื่นทะเล)
    3. เสาที่ 3: คลองเจ้าพระยา 2 (แนวคลอง 111 กม., อาคารบังคับน้ำ)
  - ป๊อปอัปแสดงผลระดับน้ำและลิงก์เชื่อมโยงไปยังรายงานทั้ง 6 เล่ม

### ขั้นที่ 5: การตรวจสอบและปิดงาน (QA & Closure)
- อัปเดต `catalog.py` และ `docs/PROJECT_MAP.md`
- อัปเดต `HANDOFF.md` และ `START_HERE.md`
- รัน `python tools/verify_all.py` (ต้องผ่าน 100% MISMATCH 0)
- Commit ด้วย Git อย่างเรียบร้อย
