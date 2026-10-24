# 35_goal7_event_rain — ฝนรายวันรอบที่ราบองครักษ์ ช่วง 20 ก.ย.–4 ต.ค. 2569

## ที่มา
- API `https://api-v3.thaiwater.net/api/v1/thaiwater30/provinces/rain3d_graph?station_id=<id>&start_date=2026-09-20&end_date=2026-10-04` (GET ไม่ต้องใช้คีย์) · ดึงเมื่อ 24 ต.ค. 2569 โดย `analysis/goal7_event_rain.py`
- รายชื่อสถานี: ชั้น rain_24h ล่าสุดของ `data/26_national_rainfall_stations/` กรองกรอบ lat 13.85–14.5 · lon 100.85–101.6 (55 สถานี มีข้อมูล 48)
- ไฟล์ดิบ `raw/<id>.json` (disk-only) · สนามฝนรายวันที่ประมาณด้วย IDW: `rain_fields.npz` (disk-only)

## ข้อจำกัด
- ค่ารายวัน = ฝน 24 ชม. ลงวันที่นั้น (สมมติ 07:00 ของวันก่อนถึง 07:00 ของวันนั้น) — เวลาอาจคลาดครึ่งวันถึงหนึ่งวัน · ไม่มีรายชั่วโมง
- ฝนรวม 20 ก.ย.–4 ต.ค. เฉลี่ยทั้งกรอบราว 736 มม. (สูงสุดรายสถานี 1,142 มม.) — ดู `analysis/goal7/event_rain_summary.json`
