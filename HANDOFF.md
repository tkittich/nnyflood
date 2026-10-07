# HANDOFF — สถานะส่งมอบ (8 ต.ค. 2569)

> เอกสารสำหรับ session ถัดไป · อ่านจบ 3 นาทีแล้วทำงานต่อได้ · ตัวเลข canonical อยู่ที่
> `docs/DATA_DICTIONARY.md` · ขั้นตอนทำซ้ำอยู่ที่ `START_HERE.md §4`

## สถานะ: publish แล้ว — github.com/tkittich/nnyflood (8 ต.ค. 2569)

งานวิเคราะห์/รายงาน **เสร็จสมบูรณ์** และผ่านการตรวจ 4 ชั้นแล้ว:
1. pytest **19/19** (test_core 14 + test_artifacts 5 — เพิ่ม test ผูก HTML กับ canonical_numbers.json)
2. ความครบถ้วนข้อมูลต้นฉบับ: SHA-256 **OK 681 / MISMATCH 0** (`verify_data_integrity.py --quick`)
3. รีวิวอิสระรอบใหม่ 2 ฉบับ (`docs/reviews/` — DeepSeek R-01..R-13 + Gemini) — **แก้/ตอบครบแล้ว**
4. ตรวจกฎหมายก่อนเผยแพร่: `docs/LEGAL_REVIEW.md` (หมิ่นประมาท + PDPA — ความเสี่ยงรวมต่ำ)

**Publish แล้วจริง**: ประวัติเก่าถูกลบ (insurance: `archive/flood-history-20261007.bundle`)
· โครงสร้างบน GitHub เริ่มจาก commit แรกใหม่เดียว + `.gitattributes` (`* -text` เก็บไบต์ตรง —
ดูบทเรียนข้างล่าง) · CI บน GitHub รันเขียว (pytest + integrity ยอมรับ exit 2) ·
description + topics ตั้งแล้วผ่าน API

ตัวเลข canonical ล่าสุด: สัดส่วนเขื่อน/ฝน = **12% เริ่มท่วม · 59% น้ำขัง**
(คำนวณโดย `analysis/attribution_share.py`) · ตัวอื่นคงเดิม
(9.23 ม. = 7.64 ม.รทก. ±0.05 · 65 ชม. · 509.3 ตร.กม. · RMSE backtest ชนะ persistence ทุกฤดู)

## ขั้นตอน publish (ทำแล้ว — เก็บไว้เป็นวิธีทำซ้ำ)

```bash
# ก่อนลบ: archive/ (gitignored) เก็บครบแล้ว — HANDOFF/รีวิวรอบเก่า/ร่าง v0.1/
#         screenshots ต้นฉบับ/bundle ประวัติทั้งหมด (flood-history-20261007.bundle 161MB)
rm -rf .git
git init -b main
git add -A
git commit -m "น้ำท่วมนครนายก 2569 — คลังหลักฐานและรายงาน (ฉบับแรก)"
git remote add origin https://github.com/tkittich/nnyflood.git
git push -u origin main
```

**2 บทเรียนจากการ publish จริง (CI fail 2 รอบกว่าจะเขียว):**
1. `core.autocrlf` บน Windows แปลง CRLF→LF ตอน commit → แฮช SHA-256 ที่บันทึกจากดิสก์
   ไม่ตรงกับ blob ใน clone ใหม่ (MISMATCH 44 ไฟล์) — แก้ด้วย `.gitattributes` `* -text`
   + `git add --renormalize .` เพื่อเก็บไบต์ตรงตามดิสก์ทุกแพลตฟอร์ม
2. GitHub Actions รัน `run` ด้วย `bash -e` → `python ...; code=$?` ไม่เคยได้รันเมื่อ
   python ออกด้วย exit 2 (MISSING ปกติบน clone) — ต้องเขียน `python ... || code=$?`

หลัง push: GitHub Actions ทำงานเอง (`.github/workflows/ci.yml` — pytest + integrity)
· ระบบเก็บพยากรณ์อัตโนมัติ (cron 09:15/21:15 → `data/17_forecast_archive/`) กลับมา
commit ปกติแล้วหลัง `git init` ใหม่ — จะ push สะสมเป็นช่วงๆ ก็ได้

## กับดักสำหรับ session ใหม่ (เจอมาแล้วจริง — อย่าเสียเวลาซ้ำ)

1. **อย่าทำงาน 2 session คู่กันใน repo เดียว** — รอบก่อนรีวิว AI อีกตัว restore ไฟล์
   ด้วย `git checkout` ทับงานที่กำลังทำ (screenshot reel — แก้คืนแล้ว)
2. **cron พยากรณ์ commit เอง 2 ครั้ง/วัน** (`git add -A` กลืนทุกไฟล์ที่ยังไม่ ignore) —
   ไฟล์ชั่วคราวต้องขึ้นต้น `_tmp_` หรือ `.ov_` (ignore แล้ว)
3. **archive/ ถูก gitignore** — เอกสาร/ภาพต้นฉบับที่ย้ายเข้าไปจะไม่ถูก publish (ตั้งใจ)
   และมีแค่สำเนาเดียวบนดิสก์ D: — ถ้าสำคัญให้ copy สำรองที่อื่นด้วย
4. **อย่าแก้ `goal4_model_v1.py` ตามข้อแนะนำ Gemini ISSUE-01/03** (ตัด dH1B_6h / เปลี่ยน
   imputation TW=2.0) — จะทำให้ตัวเลขโมเดลทุกตัวในรายงานเปลี่ยนหมด (ผ่านการตรวจแล้วว่า
   ผลกระทบถูกจำกัดด้วย diagnostics — ทำเฉพาะเมื่อทำคู่กับ HEC-RAS รอบใหญ่)
5. **requirements.txt ปักหมุดตามเครื่องพัฒนา** (Windows/CPython 3.14) — CI ใช้ ubuntu
   + Python 3.13 ถ้า install พังให้ปรับ version ใน workflow
6. REVIEW.gemini.md มีบางส่วน**หลอมข้อมูล** (ตาราง data/01–21 ชื่อไม่ตรงจริง, ตัวเลข
   417.8 MCM ไม่มีที่มา) — อ่านได้แต่อย่าอ้างตัวเลขจากตารางนั้น (จุดที่ใช้ได้จริง:
   ขอบที่ราบ −60 ม. = 6.94 ≈ BANKFULL, Ny.1B extrapolation — ยืนยันแล้ว)

## งานค้างหลัง publish (เรียงตามความคุ้ม)

- **รอมนุษย์/FOI 4 เรื่อง**: ตารางเปิด-ปิดบานรายชั่วโมง · ระเบียบ กช. + กำลังระบายปตร. ·
  datum/benchmark จุดวัด · นิยาม Outflow กราฟโครงการ (ตอนนี้มีหลักฐานเพิ่ม: เอกสาร
  โครงการเองสองชุดนับสะสมไม่ตรงกัน Δ+13/+29 ลลบ.ม. — ดู data/01 manifest 7 ต.ค.)
- **HEC-RAS 1D** (วัตถุดิบครบ: หน้าตัดจริง 5 สถานี data/19 + contour mitrearth 50 ซม.–1 ม.
  + ไฮโดรกราฟ 15 นาที) — ทำแล้วจะยกระดับ M4/สถานการณ์จาก lumped → วิศวกรรม
  · รวมถึง composite Manning n ฝั่งที่ราบ (Gemini ISSUE-04 — ทำตอนนี้ถึงจะคุ้ม)
- **ช่องทางติดต่อ PDPA** หลัง publish (issue ของ repo — ดู docs/LEGAL_REVIEW.md)
- จุเล็ก: R-12 ปรับ presentation พื้นที่พีคให้ canonical ทุกจุด · R-13 ลบ PQR ซ้ำ 2.9 GB
  (ผู้ใช้ตัดสินใจ) · แฮชใน `data/manifest.md` ให้ครบ · English abstract ใน README (ถ้า
  ต้องการคนนอกอ่าน)

## แผนที่ไฟล์สำคัญ

| ไฟล์ | คืออะไร |
|---|---|
| `START_HERE.md` | ทางเข้าโปรเจกต์ + ทำซ้ำตัวเลขหัวใจ |
| `report/น้ำท่วมนครนายก2569_ประชาชน.html` | ชิ้นงานหลัก (ไฟล์เดียวจบ) |
| `report/น้ำท่วมนครนายก2569_วิชาการ.html` | ฉบับตรวจสอบย้อนกลับ |
| `docs/LEGAL_REVIEW.md` | ตรวจหมิ่นประมาท/PDPA ก่อน publish |
| `docs/reviews/` | รีวิวอิสระรอบใหม่ 2 ฉบับ (8 ต.ค.) |
| `archive/` (gitignored) | ประวัติเก่าทั้งหมด (bundle) + ต้นฉบับที่ถูกถอดจาก repo |
| `analysis/attribution_share.py` | สคริปต์สัดส่วนเขื่อน/ฝน (12% · 59%) — ตัวเลขหัวใจ |
| `analysis/goal4_model_*.py` | โมเดลทำนาย (v1) / backtest หลายฤดู / หลายจุดวัด |
| `analysis/goal5_policy_proposals.md` | ข้อเสนอต่อภาครัฐ (เป้าหมาย 5 — E1–E7) |
