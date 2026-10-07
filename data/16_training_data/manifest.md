# ชุดที่ 16: ข้อมูลฝึกโมเดลทำนายระดับน้ำ (เป้าหมาย #4)

ดึง: 5 ต.ค. 2569 22:09 (รอบแรก) + 23:5x (เพิ่มปี 2024–2025) · แหล่ง: `http://khundan-tele.rid.go.th/station_detail.php` (POST urlencoded n_id/date_from/date_to — **ได้ราย 15 นาที** เมื่อช่วง ≤7 วัน) · สคริปต์: `analysis/fetch_khundan_training.py` (ปี 69) + `analysis/fetch_khundan_training_2024_2025.py` (ยืนยันแล้วว่า API ให้ย้อนหลังถึงอย่างน้อยปี 2024)

คอลัมน์: `datetime,level_msl_m,q_cms,rain_mm` (ค่า '-' = สถานีไม่ส่ง; คอลัมน์ฝนของสถานีเหล่านี้**ใช้ไม่ได้** — เกือบศูนย์ทั้งฤดู ทั้งที่เมืองตกจริง ~1,000 มม.) · เรียงแถวใหม่→เก่าตามต้นฉบับ

| ไฟล์ | n_id | แถว | หมายเหตุ | SHA-256 (12 หลัก) |
|---|---|---|---|---|
| khundan_15min_Ny7_Jun-Oct2026.csv | 62 | 11,034 | พีค 7.68 ม.รทก. (ตรงอ่านตรง ๆ) | f73983519140 |
| khundan_15min_Ny1B_Jun-Oct2026.csv | 61 | 11,166 | พีค 11.00 | cff12f4c2f90 |
| khundan_15min_ThaChang_tail_Jun-Oct2026.csv | 63 | 6,112 | ส่งเฉพาะฤดูน้ำ ~12 ชม./วัน | 9bf09a2fb3db |
| khundan_15min_Ny7_Jun-Oct2025.csv | 62 | 12,096 | สมบูรณ์ | 1ac8cd0a126f |
| khundan_15min_Ny1B_Jun-Oct2025.csv | 61 | 12,096 | สมบูรณ์ | 01d0a6f57b8b |
| khundan_15min_ThaChang_tail_Jun-Oct2025.csv | 63 | 12,093 | สมบูรณ์ | 3d8613841322 |
| khundan_15min_Ny7_Jun-Oct2024.csv | 62 | 6,953 | ขาดช่วง มิ.ย.–ก.ค. (สถานีเพิ่งเปิด?) | 8b8706aaef53 |
| khundan_15min_Ny1B_Jun-Oct2024.csv | 61 | 11,763 | สมบูรณ์ | 7b6042e20862 |
| khundan_15min_ThaChang_tail_Jun-Oct2024.csv | 63 | 6,742 | บางช่วง | fe3a6b3f6cd9 |
| power_rain_daily_3pts_2024_2026.csv | — | 856 วัน | ฝนรายวัน NASA POWER PRECTOTCORR ไม่ต้อง auth (API `/api/temporal/daily/point`) 3 พิกัด (14.40/101.00, 14.30/101.15, 14.20/101.20) — จริง ๆ แม็ปเป็น 2 เซลล์ 0.5° (เหนือ/ใต้) · ตรวจ 25–26 ก.ย. 69 = 54/64 มม. สอดคล้องเหตุการณ์ · ใช้เป็นฟีเจอร์ฝนสม่ำเสมอทุกปีของโมเดล v1 | f7ed56869dd5 |

NY.3 (n_id 105) ออฟไลน์ทั้ง 3 ปี ไม่มีไฟล์ · ผลทดสอบโมเดล v1 (persistence vs สูตรเส้นตรง vs GBDT): `analysis/goal4_model_v1_findings.md`

| model_rain_histforecast_sep2026.json | — | 6 โมเดล | ฝนพยากรณ์ย้อนหลัง 22–30 ก.ย. 69 จาก Open-Meteo **Historical Forecast API** (`historical-forecast-api.open-meteo.com/v1/forecast` ฟรีไม่ต้องคีย์ — เป็นชุดเก็บถาวรของโมเดล ไม่ใช่ฉบับออกจริงวันนั้น) 2 เซลล์เดียวกับ POWER · windy.com API ต้องคีย์เสียเงิน + previous-runs เก็บ ~7 วัน (22 ก.ย. พ้นช่วง) — บันทึกผลทดสอบใน goal4_counterfactual_model_vs_nomodel.md | 427b82843338 |

## เพิ่มรอบ 2 (5 ต.ค. ค่ำ): ขยาย 5 ฤดู + ฝนพยากรณ์

- **ปี 2021/2022** (สคริปต์ `analysis/fetch_khundan_training_2021_2022.py`): khundan_15min_Ny7_Jun-Oct2021.csv (10,062 แถว, พีค 5.31) · Ny1B 2021 (12,096) · Ny7 2022 (11,771, พีค 5.88) · Ny1B 2022 (12,096) · ท้ายน้ำท่าช้างปี 2021-22 = 0 แถว (เซนเซอร์ติดตั้งปี 2024) — SHA-256 ใน `_hashes_2021_2022.txt` · **ปี 2023 Ny.7 ออฟไลน์ทั้งฤดู / ปี 2020 ไม่มีข้อมูล** (ทดสอบแล้ว)
- **power_rain_daily_3pts_2021_2026.csv**: 1,952 วัน 2021-06-01 ถึง 2026-10-04
- หมายเหตุคุณภาพ: FULLYEAR 2021 มีช่วงเซนเซอร์ Ny.1B รายงานค่าไร้ความหมาย (~11–15 เม.ย. 2021 อ่านได้ 0–65 ม.) — สคริปต์ `goal4_model_backtest_long.py` กรองด้วยพิสัยกายภาพก่อนใช้
- **model_rain_histforecast_sep2026.json**: ฝนพยากรณ์รายวัน 2026-09-13..10-04 ของ 5 โมเดล (gfs/ecmwf_ifs025/icon/gem/jma) × 3 จุด จาก Historical Forecast API (ใช้ทดลองเป็นอินพุตโมเดล — `goal4_model_rainfcst_test.py`)
- ผลทดลองทั้งหมด: `analysis/goal4_model_v1_findings.md` (รอบ 2)

## ข้อมูลเต็มปี (สคริปต์ analysis/fetch_khundan_fullyears.py)

**12 ไฟล์ `khundan_15min_{Ny1B,Ny7,ThaChang_tail}_FULLYEAR{2021,2022,2024,2025}.csv`** — ทั้งปี (1 ม.ค.–31 ธ.ค.) ราย 15 นาที ~35,000 แถว/สถานี/ปี (ปี 2023 สถานี Ny.7 ออฟไลน์, ปี 2020 ไม่มีข้อมูล — ตรวจแล้ว) · SHA-256: `_hashes_fullyears.txt` · ประโยชน์: ฝึกโมเดลทำนายระดับน้ำที่ทนทานขึ้น (ครอบฤดูแล้ง→ฤดูน้ำหลากเปลี่ยนผ่าน) และสถิติฐานไหลรายเดือน
