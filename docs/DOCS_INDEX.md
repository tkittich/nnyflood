# ดัชนีเอกสาร (สร้างอัตโนมัติจาก `tools/registry.json`)

> อย่าแก้ด้วยมือ — แก้ส่วน `docs` ใน `tools/registry.json` แล้วรัน `python tools/doctor.py --write-docs` · สถานะ: `current` ใช้อ้างได้ · `generated` สร้างจากเครื่องมือ · `log` สมุดบันทึกตามเวลา (ไม่ใช่สถานะปัจจุบัน) · `plan` ความตั้งใจเดิม ไม่ตามแก้ · `historical` บันทึกเก่าเก็บเป็นประวัติ · `superseded` มีฉบับใหม่แทน · `needs-review` สงสัยว่าล้าสมัย รอคนตัดสิน

| เอกสาร | สถานะ | ชนิด | หัวเรื่อง | หมายเหตุ |
|---|---|---|---|---|
| `AGENTS.md` | current | rules | AGENTS.md — กติกาสำหรับ AI session ที่ทำงานใน repo นี้ | กติกาบังคับของโครงการ — เปลี่ยนต้องตั้งใจ |
| `README.md` | current | guide | การสอบสวนเชิงหลักฐานด้านอุทกวิทยาและการบริหารจัดการน้ำ |  |
| `START_HERE.md` | current | guide | START HERE — โครงการน้ำท่วมนครนายก 2569 และการขยายผลระดับชาติ | จุดเริ่มต้นสำหรับ session ใหม่ · ตัวเลขนับ (สารบัญ/เทสต์) ต้องตรงของจริง — number_inventory ตรวจข้อ E |
| `THIRD_PARTY_NOTICES.md` | current | legal | Third-party notices — ข้อมูลบุคคลที่สามที่ใช้/อ้างอิงในโปรเจกต์ |  |
| `docs/BANGBAN_BANGSAI_COMPARISON.md` | current | analysis | บทเรียนเชิงวิศวกรรมและเศรษฐศาสตร์: คลองระบายน้ำหลากบางบาล–บางไทร สู่โครงการเจ้าพระยา 2 | เทียบบางบาล–บางไทรกับเจ้าพระยา 2 — ตรวจตัวเลขกับ analysis/goal7/bangban_bangsai_comparison.json ด้วย number_inventory |
| `docs/DATA_CONSISTENCY_WORKFLOW.md` | current | rules | ระบบการจัดการความสอดคล้องของข้อมูลและการระงับข้อขัดแย้งหลายแหล่ง (Data Consistency & Multi-Source Reconciliati | ระบบระงับข้อขัดแย้ง 5 ชั้น — เพิ่มส่วนเครื่องมือเสริม (inventory/registry/doctor) 19 ต.ค. 69 |
| `docs/DATA_DICTIONARY.md` | current | reference | พจนานุกรมข้อมูล (DATA_DICTIONARY) |  |
| `docs/DATA_SOURCES.md` | current | reference | แหล่งข้อมูลทั้งหมดของโครงการ (DATA_SOURCES) | วิธีดึงข้อมูลจากแต่ละแหล่ง — มีตัวแทนพาธย่อ (data/13_, data/22_) ไม่ใช่พาธจริง |
| `docs/DEM_CORRECTION_PREREG.md` | current | plan | กติกาปรับความสูง DEM แบบต่อเนื่อง — กำหนดไว้ก่อนดูผล (B1 รีวิวรอบ 7) | กำหนด 25 ต.ค. 69 ก่อนรันโค้ดใหม่ |
| `docs/ESTUARY_AND_WEATHER_GUIDE.md` | current | reference | คู่มือข้อมูลคุณภาพน้ำปากแม่น้ำ ทะเลอ่าวไทย ฝนโทรมาตร และการพยากรณ์น้ำท่า |  |
| `docs/GOAL7_FOI_REQUESTS.md` | current | backlog | รายการขอข้อมูลจากหน่วยงาน — เป้าหมาย 7 (คลองเจ้าพระยา2) · ร่าง 16 ต.ค. 2569 |  |
| `docs/LEGAL_REVIEW.md` | current | rules | การตรวจทานกฎหมายก่อนเผยแพร่: หมิ่นประมาท + PDPA | หลักหมิ่นประมาท + PDPA |
| `docs/METHODS.md` | current | guide | วิธีการและมาตรฐานการทำงานของโครงการ (METHODS) |  |
| `docs/OCR_WORKFLOW_V2.md` | current | plan | ขั้นตอน OCR รุ่นที่ 2 — แยกส่วนหน้าก่อน แล้วอ่านข้อความกับภาพแยกกัน (บันทึกการตัดสินใจ) | ตัดสินใจ 21 ต.ค. 69 · ยังไม่ใช้กับคิวที่ค้าง |
| `docs/OFFLINE_DATA_BACKLOG.md` | current | backlog | คลังรายการข้อมูลที่ไม่มีออนไลน์และต้องรอดำเนินการ (OFFLINE_DATA_BACKLOG) | ทะเบียนงานคงค้าง/FOI (R6-xx, R7-xx) |
| `docs/PROJECT_MAP.md` | current | guide | แผนที่นำทางและแคตตาล็อกระบบ (Project Map & Knowledge Atlas) | แผนผังระบบ/ตาราง Topic Discovery — ลงทะเบียนสคริปต์ใหม่ที่นี่ |
| `docs/REMOTE_SENSING_APIS.md` | current | reference | คู่มือการเรียกใช้ API ดาวเทียมและข้อมูลกริดระดับชาติ (Remote Sensing & Grid APIs Guide) |  |
| `docs/REPORT_CONVENTIONS.md` | current | rules | ข้อตกลงการทำรายงาน (Report Conventions) | ธรรมเนียมการทำรายงาน (เอ็นจินโทเคน ธีม กราฟ แผนที่) |
| `docs/REVIEW_PROMPT_EN.md` | current | review-prompt | Comprehensive System Audit Prompt (English) — Multi-Pillar Red-Team Review | ชุดคำสั่งรีวิวหลัก — แก้ 19 ต.ค. 69 ให้ตรง repo (เดิมมีข้อกล่าวอ้างที่ไม่มีในโค้ด); ควรสร้างจาก canonical (R7-08) |
| `docs/RID_SWOC_GUIDE.md` | current | reference | คู่มือระบบฐานข้อมูลน้ำและโทรมาตร SWOC กรมชลประทาน (RID SWOC Guide & API Reference) |  |
| `docs/THAIWATER_API_GUIDE.md` | current | reference | คู่มือสถาปัตยกรรมและการเรียกใช้ API คลังข้อมูลน้ำแห่งชาติ (ThaiWater & Khun Dan Telemetry Guide) |  |
| `docs/DOCS_INDEX.md` | generated | guide | ดัชนีเอกสาร (สร้างอัตโนมัติจาก tools/registry.json) | สร้างด้วย python tools/doctor.py --write-docs |
| `docs/ENVIRONMENT.md` | generated | guide | สภาพแวดล้อมที่ใช้รัน (Environment record) | ส่วนทะเบียนเครื่องมือสร้างอัตโนมัติจาก tools/registry.json; ส่วนอื่นเป็นบันทึกมือ |
| `HANDOFF.md` | log | log | HANDOFF — สถานะส่งมอบ (อัปเดต 19 ต.ค. 2569) | สมุดบันทึกสถานะรายวัน (ล่าสุดอยู่บน) — เป็นประวัติ ไม่ใช่สถานะปัจจุบันของตัวเลข; ตัวเลขปัจจุบันดู canonical.json |
| `docs/READER_CHANGELOG.md` | log | log | บันทึกการปรับปรุงเนื้อหารายงานสำหรับผู้อ่าน (Reader-Facing Report Changelog) | ประวัติการเปลี่ยนแปลงสำหรับผู้อ่าน — ไม่มีเอกสารอื่นลิงก์ถึง |
| `docs/ANALYSIS_PLAN.md` | plan | plan | แผนการวิเคราะห์ (ANALYSIS_PLAN) — ครอบคลุมเป้าหมาย 1–5 |  |
| `docs/GOAL6_HYDRO2D_PLAN.md` | plan | plan | แผนการทำแบบจำลอง 2 มิติ (HEC-RAS 2D) — นครนายก + ข้อมูลที่ยังขาดพร้อมความสำคัญ |  |
| `docs/GOAL6_PLAN.md` | plan | plan | แผนเป้าหมาย 6 — ขยายวิธีการนครนายกสู่พื้นที่อื่นทั่วประเทศ (รายงานที่ 3) | แผนเป้าหมาย 6 (12 ต.ค.) — ความตั้งใจเดิม ไม่ได้ตามแก้ให้ตรงสถานะ; มีอ้างไฟล์ร่างที่ไม่มีแล้ว |
| `docs/GOAL7_PLAN.md` | plan | plan | GOAL7_PLAN — เป้าหมาย 7: คลองเจ้าพระยา2 (คลองระบายน้ำหลากชัยนาท–ป่าสัก–อ่าวไทย) | แผนเป้าหมาย 7 ที่ยังเพิ่มบันทึกอยู่ — ทบทวนแล้ว 19 ต.ค.: ไฟล์ที่ถูกลบ/เปลี่ยนชื่อ (goal7_build_qa.py, structures_km0_81.csv→structures_all.csv, หน้าถามตอบสั้น) ทำเครื่องหมายในเนื้อหาแล้ว |
| `docs/IMPLEMENTATION_PLAN_ADVANCED_MODELING.md` | plan | plan | แผนการดำเนินงาน: แบบจำลองชลศาสตร์ 1 มิติ, การจำลองคลองเจ้าพระยา 2, โมเดลพยากรณ์ผสานทะเลหนุน และการบำรุงรักษาระ | แผน 17 ต.ค. — อ้างโฟลเดอร์ data/24_estuary_telemetry และ data/30_swan_wave_model ที่ไม่มี (ชื่อจริง 24_estuary_waterquality, 30_national_warehouse) |
| `docs/IMPLEMENTATION_PLAN_PORTAL_AND_ADVANCED_ANALYSIS.md` | plan | plan | แผนงานการพัฒนาและยกระดับระบบฉบับสมบูรณ์ (Implementation Plan) |  |
| `docs/MAJOR_UPDATES_REPORT1_4_PLAN.md` | plan | plan | แผนการปรับปรุงใหญ่ รายงานฉบับที่ 1–4 (Major Updates Plan for Reports 1–4) | แผน 17 ต.ค. — อ้าง goal1_blocks.py ที่ไม่มี |
| `docs/GOAL6_PUBLIC_RELEASE_REVIEW.md` | historical | review-record | รีวิวพร้อมเผยแพร่: รายงานที่ 3 + ที่ 4 (ระลอกปลาย ก.ย.–ต.ค. 2569 · 6 ลุ่ม) | บันทึกรีวิวก่อนเผยแพร่เป้าหมาย 6 (10 ต.ค.) — เก็บเป็นประวัติ |
| `docs/GOAL7_POLICY_BRIEF.md` | historical | analysis | รายงานสรุปเชิงนโยบาย: โครงการคลองระบายน้ำหลากเจ้าพระยา 2 (ป่าสัก–อ่าวไทย) | สำเนา Markdown ของสมุดปกขาวที่เขียนมือ — ไม่ใช่แหล่งความจริง (ค่า 60–80 วัน/10.4% ล้าสมัย) · ฉบับปัจจุบันสร้างจาก report/goal7_build_policy_brief.py |
| `docs/REVIEW_PROMPT.md` | superseded → `docs/REVIEW_PROMPT_EN.md` | review-prompt | Prompt สำหรับให้ AI ตัวอื่นรีวิว/ตรวจสอบโปรเจกต์ (เน้นเป้าหมาย 7 — คลองเจ้าพระยา2) | ถูกแทนที่ด้วย REVIEW_PROMPT_EN.md |
| `docs/REVIEW_PROMPT_COMPREHENSIVE.md` | superseded → `docs/REVIEW_PROMPT_EN.md` | review-prompt | Comprehensive System Audit Prompt (Superseded) | ถูกแทนที่ด้วย REVIEW_PROMPT_EN.md |

รวม 36 เอกสาร
