# 34_goal7_bangpakong — ระดับน้ำสถานีลุ่มน้ำบางปะกง (thaiwater)

## ที่มา
- API `https://api-v3.thaiwater.net/api/v1/thaiwater30/` (GET ไม่ต้องใช้คีย์) · ดึงโดย `analysis/goal7_bangpakong_fetch.py`
- `public/waterlevel_load` — ระดับน้ำล่าสุดทุกสถานี (กรองเฉพาะลุ่มน้ำบางปะกง 34 สถานี) · ไฟล์ `raw/<วันที่>_waterlevel_load.json`
- `public/waterlevel_graph` — อนุกรมราย 10 นาที 30 วันล่าสุด ต่อสถานี · ไฟล์ `raw/station_series/<รหัส>_<id>.json`
- ดึงเมื่อ 20 ต.ค. 2569 (ภาพนี้เป็นสแนปช็อต — รันซ้ำจะได้ช่วงเวลาที่เลื่อนไป)

## ข้อจำกัด
- ตลิ่ง = `min_bank` ของระบบ (ตลิ่งฝั่งต่ำ) · ค่าศูนย์ของสถานีต่างกันได้เล็กน้อย — ใช้เป็นลำดับเวลา ไม่ใช่ความชันแม่นยำ
- สถานี NYK000 (องครักษ์) ข้อมูลขาดหลายวัน
- ไฟล์ดิบ disk-only (ไม่เข้า git) ตามนโยบาย · ชั้นน้ำท่วม 30 วันของ GISTDA ที่ใช้ร่วมอยู่ที่ `data/12_gistda_flood/raw/provinces/` (สแนปช็อต 16 ต.ค. เก็บเป็น `*_30days_2026-10-16.json`, 20 ต.ค. เป็น `*_30days.json`)

## ชั้นน้ำท่วมล่าสุดของ GISTDA (ดึง 20 ต.ค. 69)
- `data/12_gistda_flood/raw/provinces/<จังหวัด>_{1day,3days,7days}.json` — API `.../features/flood/{1day,3days,7days}` (ใช้คีย์ใน data/12_gistda_flood/.gistda_api.json ไม่พิมพ์ค่าคีย์) · 1–3 วันคลุมแนวของฉากเดียว (RADARSAT-2 20 ต.ค.) จึงใช้เทียบทั้งจังหวัดไม่ได้ · 7 วันคลุมฉากหลายดาวเทียม 14–20 ต.ค.
