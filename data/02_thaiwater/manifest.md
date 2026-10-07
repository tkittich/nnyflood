# manifest — data/02_thaiwater (คลังข้อมูลน้ำแห่งชาติ / สชน.)

แหล่ง: thaiwater.net (เว็บหน้าเว็บเป็น SPA) — API จริงอยู่ที่ `https://api-v3.thaiwater.net/api/v1/thaiwater30/...` (ค้นพบจาก JS bundle ของเว็บ วันที่ 2026-10-04, GET ไม่ต้อง auth)

## ไฟล์ที่บันทึก

| ไฟล์ | ดึงเมื่อ | URL ต้นทาง | วิธี | เนื้อหา |
|---|---|---|---|---|
| `raw/2026-10-04_analyst-dam_latest.json` | 2026-10-04 (11:49 น. เวลาท้องถิ่น) | `https://api-v3.thaiwater.net/api/v1/thaiwater30/analyst/dam` | curl GET | สถานะล่าสุดเขื่อน/อ่างเก็บน้ำทั่วประเทศ: `dam_hourly` (17) / `dam_medium` (862) / `dam_daily` (50) / `dam_small_tele` (60) |

## ค่าอ้างอิงเขื่อนขุนด่านปราการชล (ตรวจสอบวันที่ 2026-10-04)

- รหัสสถานี: `dam id 32` (oldcode "38"), สังกัดกรมชลประทาน, ลุ่มน้ำบางปะกง (basin id 16 / code 15)
- พิกัด: 14.314722, 101.321389 — ต.หินตั้ง อ.เมือง นครนายก
- ความจุ: `max_storage` **224.9** ล้าน ลบ.ม. / `normal_storage` **224** ล้าน ลบ.ม. / `uses_water` **219.48** ล้าน ลบ.ม.
- snapshot รายวัน 2026-10-04: น้ำเก็บ **213.18** ล้าน ลบ.ม. (**95.17%**), น้ำไหลเข้า 3.73 ล้าน ลบ.ม./วัน, ปล่อย 3.63 ล้าน ลบ.ม./วัน, ล้นสปิลเวย์ 0
- ชื่อใน API: th "ขุนด่านปราการชล" / en "Khun Dan Prakan Chon"

## endpoint ที่น่าสนใจ (จาก JS bundle, ยังไม่ได้ทดสอบพารามิเตอร์)

- `analyst/dam` — สถานะเขื่อนล่าสุด (ใช้แล้ว)
- `analyst/dam_yearly_graph`, `analyst/dam_small_tele_graph` — กราฟย้อนหลัง
- `public/waterlevel_load` / `public/waterlevel_graph` / `public/waterlevel_graph_year` / `public/waterlevel_graph_oldcode` — ระดับน้ำแม่น้ำรายสถานีย้อนหลัง
- `public/rain_today` / `rain_yesterday` / `rain_monthly` / `rain_yearly`, `provinces/rain3d|5d|7d|15d` — ฝน
- `public/watergate_load` / `watergate_graph`, `public/flow` / `flow_graph`, `public/canal_waterlevel` — ประตูระบาย/คลอง/อัตราการไหล
- `frontend/shared/station_all` — รายชื่อสถานีทั้งหมด
- `analyst/radar_img` / `radar_history_img` — ภาพเรดาร์ฝนย้อนหลัง

## หมายเหตุ

- วิธีหาพารามิเตอร์ query ย้อนหลัง: เปิดหน้ากราฟของ thaiwater.net ด้วยเบราว์เซอร์แล้วดู network requests (เฟสถัดไป)
- ชื่อเดิมของเขื่อนตามวิกิพีเดีย: "เขื่อนคลองท่าด่าน" (ที่ตั้ง บ้านท่าด่าน ต.หินตั้ง อ.เมือง นครนายก)

## ชุดข้อมูลที่ดึงเองจาก API (fetched 2026-10-04, ~11:30–13:00 น. เวลาท้องถิ่น)

วิธี: `curl`/Python `urllib` GET ตรงไปที่ api-v3.thaiwater.net ไม่ต้อง auth — โครงสร้าง query ได้จากการแงะ JS bundle ของเว็บ (app.chunk.js)

| ชุด | Endpoint + พารามิเตอร์ | ไฟล์ | ความครอบคลุม |
|---|---|---|---|
| เขื่อนขุนด่านฯ รายวัน | `analyst/dam_yearly_graph?data_type={storage\|inflow\|released\|level\|spilled}&dam_id=32&year={2013..2026}` | `raw/dam_yearly/` (70 ไฟล์ JSON) | **2013–2026 ครบทุกปี** + `upper_rule_curve`/`lower_rule_curve` รายวันในตัว (ยืนยันค่า URC 31 ส.ค. = 164.18 ตรงกับ screenshot ผู้ใช้) |
| ทะเบียนสถานีทั้งประเทศ | `frontend/shared/station_all` | `raw/station_all.json` (11,483 สถานี; นครนายก 66) | สแนปช็อตปัจจุบัน |
| ฝนรายวันรายสถานี | `provinces/rain3d_graph?station_id={id}&start_date&end_date` (**จำกัดช่วง ≤31 วัน/ครั้ง** → ดึงเป็นชันค์ 30 วัน) | `raw/rain_chunks/` (571 ไฟล์) | ปี 2026: มีข้อมูลจริง 12 สถานีใน นครนายก; **ย้อนหลังก่อนปี 2026 แทบไม่มีค่า** (API เก็บเฉพาะปีปัจจุบัน) → ประวัติฝนยาวต้องใช้ TMD/ERA5 |
| ระดับน้ำรายชั่วโมง | `public/waterlevel_graph?station_type=tele_waterlevel&station_id={id}&start_date&end_date` | `raw/waterlevel/` (12 ไฟล์) | Ny.7 สะพานหน้าจวนผู้ว่าฯ: **2025+2026 เต็มปี** (12,238 ชม.); Ny.1B เขานางบวช, Ny.3 ป่าขะ: ก.ย.–4 ต.ค. 69; Ny.4 เหวนรก: 34 ชม. |

**ข้อจำกัดที่ตรวจพบ**: `data_type=dam_level` ของเขื่อนนี้คืนค่าว่าง (ใช้ระดับ ม.รทก. จากรายงาน กช. แทน) · `dam_spilled` เป็น 0 ตลอด (การระบายเป็นการเปิดประตุควบคุม ไม่ใช่น้ำล้นแบบไม่ควบคุม) · สถานีรหัสเก่า TNy9/10/11/12 (รวมจุดท้ายเขื่อน) ไม่รายงานผ่าน endpoint นี้ (ค่า null) — ต้องหาทางอื่น เช่น ridhydro_ id หรือรายงานท้ายเขื่อนจากเพจเขื่อน

**CSV ที่สังเคราะห์แล้ว (โฟลเดอร์ analysis/)**
| ไฟล์ | เนื้อหา | SHA-256 (16 ตัวแรก) |
|---|---|---|
| dam_khun_dan_daily_2013_2026.csv | รายวัน: ปริมาตร/ระดับ/เข้า/ปล่อย/ล้น/URC/LRC (5,025 วัน) | 56823c26b53e249a |
| nn_rain_daily_2026.csv | ฝนรายวัน 12 สถานี นครนายก ปี 2026 | c3335488b9305a91 |
| waterlevel_hourly_Ny7_2025_2026.csv | ระดับน้ำรายชั่วโมงแม่น้ำนครนายกจุดตัวเมือง 12,238 ชม. | 61be60953b1627dd |
| waterlevel_hourly_sep2026_stations.csv | ระดับน้ำรายชั่วโมง 4 สถานี ช่วง 1 ก.ย.–4 ต.ค. 69 | d5eea665413c0e17 |
| rain_48417_nakhonnayok_2013_2026.csv | ฝนสถานีอุตุนิยมนครนายก (มีค่าเฉพาะปี 2026 = 112 วัน + วันเดียวปี 2024 ตามที่ API มี) | f72488899437c3e9 |

## หลักฐานจากผู้ใช้ (received 2026-10-04)

### from_user/messageImage_1790943577178.jpg
- SHA-256: `0e896208ff45e6a9d84d46eb47da3e4acc59dbe1942cd402f03f24b6f69c7a47` | ต้นทางก่อนคัดลอก: `D:\theera\download\flood\`
- เนื้อหา: ภาพหน้าจอเบราว์เซอร์ของผู้ใช้ เปิดหน้ากราฟ "อ่างเก็บน้ำ จ.นครนายก (ปริมาณน้ำ)" บน thaiwater.net — กราฟรายวันขุนด่านปราการชล ปี 2024–2026 พร้อมเส้นอ้างอิง: เกินปลอดภัย 224 / เก็บกักสูงสุด 225 / น้ำตาย 5 ล้าน ลบ.ม.
- tooltip ณ 31 ส.ค.: ปี 2026 = **175.88**, 2025 = 137.95, 2024 = 142.31, **Lower Rule Curve = 74.74, Upper Rule Curve = 164.18** ล้าน ลบ.ม. `[ค่าอ่านจากภาพ ควรดึงซ้ำจาก API]`
- ความสำคัญ: ยืนยันว่า thaiwater.net **มีข้อมูลรายวันย้อนหลัง + ค่า Rule Curve รายวัน** ของอ่างฯ นี้ — เป้าหมายการดึงข้อมูลย้อนหลัง (หน้า: thaiwater.net/water → ป๊อปอัปกราฟอ่างเก็บน้ำรายวัน)
