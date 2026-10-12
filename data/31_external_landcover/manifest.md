# manifest — data/31_external_landcover (ข้อมูลภายนอกสำหรับรีวิว Sonnet · 12 ต.ค. 2569)

วิธี: `fetch.sh` (curl GET สาธารณะ ไม่ต้อง auth · resume ได้) · ดึงเมื่อ 12 ต.ค. 2569 · SHA-256 อยู่ใน `_hashes.txt` · ไฟล์ดิบ **disk-only** (ไม่เข้า git)

| ไฟล์ | แหล่ง | ใช้ทำอะไร |
|---|---|---|
| `ESA_WorldCover_10m_2021_v200_N{12,15,18}E{096,099,102}_Map.tif` (7 แผ่น) | ESA WorldCover 2021 v200 (CC BY 4.0) · registry.opendata.aws/esa-worldcover-vito | ชนิดผิวดิน 10 ม. แยกผลตรวจน้ำ S1 ตามผิวดิน (`analysis/goal6_s1_landcover.py`) |
| `occurrence_{90E,100E}_20Nv1_4_2021.tif` | JRC Global Surface Water v1.4 (Pekel et al. 2016; Copernicus open data) | ความถี่การมีน้ำ 1984–2021 (น้ำถาวร) |
| `tha_ppp_2020_1km_Aggregated.tif` | WorldPop 2020 (CC BY 4.0) · UN-adjusted 1 กม. | ประชากรต่อพื้นที่ — ยังไม่ใช้ (ชั้นเตรียมไว้สำหรับชั้นผลกระทบ — รวมเป็นระดับกริดไม่ใช่รายครัวเรือน) |
| `thailand-latest.osm.pbf` | Geofabrik (ODbL, © OpenStreetMap contributors) | ถนน/ทางรถไฟ — ยังไม่ใช้ (ชั้นเตรียมไว้) |
