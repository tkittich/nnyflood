# 10_mitrearth_gis — ชุดข้อมูล GIS จาก มิตรเอิร์ธ (mitrearth)

## ที่มา
- ไฟล์ **FLOOD.rar (76 MiB, SHA-256 `3666e00df09a2d76bc7eecf77a0ed1a63adb8bd5e3756cf80bd66c4ac1185721`)**: ผู้ใช้โปรเจคได้รับมาและแจ้งว่า "น่าจะมาจาก facebook.com/mitrearth หรือ mitrearth.org" (4 ต.ค. 2569) — เก็บต้นฉบับไว้ที่ raw/FLOOD.rar
- ไฟล์ใน rar ลงวันที่สร้าง **2 ต.ค. 2569 18:44–21:10 น.** (ช่วงหลังน้ำท่วม อ.เมือง นครนายก ~1 วัน) — จัดเตรียมเฉพาะกิจเพื่อตอบสนองเหตุการณ์น้ำท่วม
- **มิตรเอิร์ธ - mitrearth** (เพจ FB id 100057264377080, ผู้ติดตาม ~3.9 แสน, กรุงเทพฯ; เว็บ mitrearth.org; อีเมล mitrearth@gmail.com) = "พื้นที่แบ่งปันความรู้ ข่าวสารและประสบการณ์ด้านวิทยาศาสตร์โลก"
- บริบทการแจกจ่าย: โพสต์ 30 ก.ย. 69 "ท่านใดสนใจ ขั้นตอนการสั่ง [แผนที่]" (permalink `mitrearth/posts/pfbid02j7uDVp4rAQU8zYpJmcvSqxiS5snBV4DR7SuGzJaxoBdJ6UoSHbm58kQGEQtw5zql`, 811 แชร์) — แจกแผนที่ภูมิประเทศ 3D แลกบริจาคโรงพยาบาล ≥300 บาท (ภาพ+screenshot เก็บใน fb_page/ และ screenshots/) · โพสต์อีกรายการ (~30 ก.ย.) เป็นความเห็นเสริมเรื่อง "พื้นที่ต่ำมาก ราบเรียบมาก (น้ำไม่มีแรงไหล) + น้ำทะเลหนุน" บนโพสต์ของ ศ.สิทธางค์ พิไลลักษณ์ (pergola `pfbid02mVPYd4hTctJcP5...`)
- เว็บ mitrearth.org มีชุดข้อมูล KMZ ให้ดาวน์โหลดครบ 77 จังหวัด (ภูมิประเทศ 3D, contour, ร่องน้ำ, จุดเสี่ยงต่างๆ — หน้า /8-30-flood-mitigation-data/ ลงวันที่ 3 ธ.ค. 2025) "จัดทำจาก DEM ตรวจวัดจากดาวเทียม 30×30 ม."
- **สิทธิ์**: เว็บระบุ "All rights reserved" (เจตนาให้ใช้ประโยชน์ตามอัธยาศัยเชิงการศึกษา) — ในรายงานต้องระบุที่มาชัดเจน ห้ามนำไปใช้เชิงพาณิชย์/แจกจ่ายต่อโดยไม่ขออนุญาต

## รายการไฟล์ (แตกจาก rar ไว้ที่ raw/extracted/ — SHA-256 ทั้งชุดใน raw/_hashes.txt)

| ไฟล์ | เนื้อหา | ค่าต่อโปรเจค |
|---|---|---|
| 18 Contour10m NAKHON NAYOK - mitrearth.kmz | เส้นชั้นความสูงฉลับ 10 ม. ทั้งจังหวัด | เสริม/ตรวจไขว้ Copernicus DEM ของเรา |
| 18 Drainage System NAKHON NAYOK - mitrearth.KMZ | **โครงข่ายลำน้ำ-ลำธาร 7,684 เส้น** (จัดกลุ่มตามลำดับศักดิ์ 10 ระดับ) | เป้าหมาย 3: ระบบระบายน้ำทั้งจังหวัด |
| 18 Slope-Aspect NAKHON NAYOK - mitrearth.kmz | ความชัน+ทิศลาด | วิเคราะห์พื้นที่น้ำไหลช้า/ขัง |
| 18_Flood_Susceptible_Village_NAKHON_NAYOK_-_mitrearth.kmz | **จุดหมู่บ้านเสี่ยงน้ำท่วม 400 จุด** (~204 จุดในกรอบ อ.เมือง โดยประมาณ) | เทียบกับอัลบั้ม 668 ภาพ/ขอบเขตน้ำท่วมจริง → `analysis/mitrearth_flood_villages_nakhonnayok.csv` |
| 31*/64* (ปราจีนบุรี/สระบุรี) | ชุดเดียวกันของจังหวัดเพื่อนบ้าน | บริบทลุ่มบางปะกงตอนบน |
| 3Province.kmz (31.7 MB) | รวม 3 จังหวัด | ภาพรวม |
| NYK.kmz (11.6 MB) | รวมชั้นข้อมูลนครนายก (drainage + สัญลักษณ์ geology arrows) | สะดวกเปิดใน Google Earth |
| Terrain.jpg/png | ภาพภูมิประเทศรวม | อ้างอิงภาพรวม |
| osgeo4w-setup.exe | ตัวติดตั้ง QGIS (OSGeo4W) | ไม่ใช่ข้อมูล — บ่งชี้ผู้จัดทำเตรียมให้ผู้รับเปิดไฟล์ด้วย QGIS |

## ข้อจำกัดสำคัญต่อการใช้ (I — ต้องตรวจก่อนสรุป)
1. **ชั้น Flood Susceptible Village ยังไม่ทราบนิยาม/เกณฑ์การคัดเลือกและปีข้อมูล** — ชื่อชั้นนี้ไม่ปรากฏบนหน้าเว็บที่อัปเดตล่าสุด (ธ.ค. 2025) → ควรสอบถาม mitrearth@gmail.com ก่อนใช้เป็นหลักฐานอ้างอิงหลัก (ใช้เบื้องต้นเป็น "ชั้นเปรียบเทียบ" ได้)
2. DEM ต้นทาง 30 ม. จากดาวเทียม (นัย SRTM/Copernicus ใกล้เคียงชุดของเรา) — เส้น contour 10 ม. อาจมาจากการ interpolate
3. ชุดนี้จัดทำหลังเหตุการณ์ (2 ต.ค. 69) แต่เนื้อหาเป็นข้อมูลภูมิประเทศพื้นฐานก่อนเหตุการณ์ — ไม่ใช่แผนที่ขอบเขตน้ำท่วมจริงของเหตุการณ์นี้

## ตรวจไขว้เชิงพื้นที่กับ DEM ของเรา (4 ต.ค. 69 — สุ่มความสูง Copernicus DSM ที่ตำแหน่งหมู่บ้าน)

- หมู่บ้านเสี่ยงในกรอบ อ.เมือง (204 จุด): มัชฌิม 10.7 ม. · ต่ำกว่า 8 ม. 31% (กรอบรวมพื้นที่เชิงเขาจึงค่าเฉลี่ยสูง)
- หมู่บ้านเสี่ยงนอกกรอบ อ.เมือง (196 จุด = ที่ราบ อ.บ้านนา ฯลฯ): **มัชฌิม 3.5 ม. · ต่ำกว่า 8 ม. 85%** — จุดเสี่ยงกระจุกบนพื้นที่ต่ำจริง ตาม DEM อิสระของเรา ✓ (ชั้นนี้สอดคล้องภูมิประเทศจริง)
- ค่าความสูงรายจุดบันทึกในคอลัมน์ elev_m ของ `analysis/mitrearth_flood_villages_nakhonnayok.csv` (DSM รวมวัตถุปิดทับ — อ่านเป็นเพดานความสูง)
- บั๊กที่แก้: rasterio sample() นอกขอบไทล์คืน 0.0 — ต้องเช็ก bounds ก่อนสุ่มทุกครั้ง

## ความสอดคล้องเบื้องต้นกับข้อมูลของเรา (I)
- รายชื่อหมู่บ้านเสี่ยงใน อ.เมือง ครอบคลุมตำบลหลักที่ปรากฏน้ำท่วมจริงตามอัลบั้มประชาชน (พรหมณี วังกระโจม ศรีจุฬา ท่าทราย สาริกา ฯลฯ)
- สอดคล้องเชิงแนวคิดกับผังน้ำลุ่มบางปะกง (ลร.๑ เกณฑ์น้ำท่วม 100 ปี) ที่เก็บไว้ใน data/09_plans_standards

## ตรวจเว็บต้นทางและชุดข้อมูลเต็มจังหวัด (19 ต.ค. 2569 — รอบ 6)

- **เว็บ**: https://www.mitrearth.org/m18-nakhon-nayok/ (หมวด https://www.mitrearth.org/category/map/ — ชุด "ภูมิศาสตร์ . แผนที่" รายจังหวัด) · ผู้จัดทำ สันติ ภัยหลบลี้ ภาควิชาธรณีวิทยา คณะวิทยาศาสตร์ จุฬาลงกรณ์มหาวิทยาลัย · หน้านครนายกลงวันที่ 15 มี.ค. 2562 · ดาวน์โหลดทั้งจังหวัดทาง Google Drive https://drive.google.com/drive/folders/1_RxXlDWIKjhaeog7HJGRbBFeoKvKNByX
- **สิทธิ์ตามเว็บ**: เผยแพร่เพื่อประโยชน์ต่อสังคมและการเรียนการสอน **ห้ามนำไปใช้/ดัดแปลงเพื่อประโยชน์เชิงพาณิชย์ส่วนตัว** — โปรเจกต์นี้เป็นงานวิจัย/ข้อมูลสาธารณะไม่แสวงกำไร จึงใช้ได้ แต่ต้องอ้างแหล่ง และห้ามนำชั้นข้อมูลไปแจกจ่ายต่อในเชิงพาณิชย์
- **ชุดเต็มจังหวัดอยู่ในคลังแล้ว**: `data/manual/18 นครนายก (NAKHON NAYOK).zip` (1,683 MB · 370 ไฟล์ · SHA-256 `17cc9aefc3654e4131de935694699051660a0098f23cb2bee079dbd7bbd0431d`) — ไม่ต้องดาวน์โหลดใหม่ · ก่อนหน้านี้ใช้เฉพาะชุดย่อยใน `FLOOD.rar` (contour 10 ม. · ลำน้ำ · ความชัน · หมู่บ้านเสี่ยง)
- **นิยามชั้น "หมู่บ้านเสี่ยงน้ำท่วม" (ปิดข้อจำกัดข้อ 1 ด้านบน)**: ไฟล์ `18 นครนายก (NAKHON NAYOK) หมู่บ้านอ่อนไหวน้ำหลาก.xlsx` ระบุว่าคือ "หมู่บ้านที่อยู่ในแนวร่องน้ำ อ่อนไหวต่อการเกิดภัยพิบัติ น้ำท่วม (flood) หากฝนตกหนัก" — **เกณฑ์จากภูมิประเทศ (หมู่บ้านอยู่บนแนวร่องน้ำ) ไม่ใช่บัญชีหมู่บ้านที่เคยท่วมจริง** · แยกชั้นอื่นในไฟล์เดียวกัน: น้ำท่วมฉับพลัน (ร่องน้ำชัน) · เศษหินไหลหลาก · ดินถล่ม · หลุมยุบ · แผ่นดินไหว · สึนามิ — ห้ามตีความจำนวนหมู่บ้านว่าเป็นหลักฐานเหตุการณ์
- **ชั้นข้อมูลในชุดเต็มที่ยังไม่ได้ใช้ (น่าสนใจ)**:
  1. `Flood GISTDA 0519` (shp/kmz · 2,729 รูปปิด) — ขอบเขตน้ำท่วมของ GISTDA ที่มีฟิลด์ปี: 2548 · 2549 · 2551 · 2553 · 2554 (ปี 2554 มี 4 รูปปิด รวมพื้นที่ตามเส้นขอบ ~1,061 ตร.กม. — **เป็นพื้นที่ตามเส้นขอบรวมรูเปิด ต้องรวม/หักรูก่อนใช้**; มีฟิลด์รายตำบล flood_area · house) → ฐานเทียบเหตุการณ์ 2554 ในระดับอำเภอ/ตำบล
  2. `Contour 1 m` (11.6 MB kmz + shp) — เส้นชั้นความสูง 1 ม. (ที่มา/ความแม่นยำไม่ระบุ — ต้องตรวจเทียบ FABDEM/Copernicus ก่อนเชื่อ)
  3. `Flood Riverbank` (จุด 5,365) · `Overflow Flood` (เส้นลำน้ำ 898 ฟิลด์ MAX_FLOW) · `Riverbank Erosion` · `Major River` — ชั้นน้ำล้นตลิ่ง/ลำน้ำสายหลัก
  4. `Drainage Basin` (kmz) + shapefile `6 Valley Ridge and Basin` — ลุ่มน้ำย่อยและสันปันน้ำ → ตรวจไขว้กับพื้นที่รับน้ำย่อย PK-AT-x ของ EIA
  5. `จุดอพยพหนีน้ำท่วม` · `จุดเสี่ยงน้ำตัดถนน` — จุดถนนตัดร่องน้ำ (ใช้ดูทางหลวง 305/ถนนที่น้ำตัด)
  6. `Surface and Ground Water` shapefile + `groundwater wells DGR` — บ่อบาดาล/ระดับน้ำใต้ดิน
  7. ภาพถ่ายทางอากาศ/แผนที่เก่า `MR_M8_2523` (285 MB) · `SAGRIC_003_2533` (643 MB) · `5019601301756.tif` (160 MB) · `Topo 1:50,000` (kmz 67 MB) — ฐานเทียบการใช้ที่ดินปี 2523/2533
  8. DEM 30 ม. (`18 DEM30m - mitrearth.tif`) — ต้นทางไม่ระบุ (นัย SRTM/ASTER) ไม่ควรแทน Copernicus/FABDEM
- **ยังไม่ได้ประมวลผลชั้นใดเพิ่ม** (งานค้าง R7-13 — ดู docs/OFFLINE_DATA_BACKLOG.md §7) · ชุดข้อมูลจังหวัดข้างเคียงที่คลองผ่าน (สระบุรี · ฉะเชิงเทรา · สมุทรปราการ ฯลฯ) ดาวน์โหลดได้จากหมวดเดียวกันถ้าต้องการ — เป็นการดาวน์โหลดไฟล์ใหม่ ต้องให้ผู้ใช้อนุญาตและระบุชื่อ/ขนาดก่อน

## ดาวน์โหลดเพิ่มรายจังหวัด (19 ต.ค. 2569 — ยังไม่สำเร็จ ต้องโหลดเอง · backlog R7-15)

ลุ่มน้ำเจ้าพระยาตอนล่างถึงอ่าวไทย: 10 จังหวัดจากหน้าจังหวัดบน mitrearth.org (ชุดเดียวกับนครนายก · สิทธิ์ใช้งานเหมือนกัน — เพื่อประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์)
Google Drive จำกัดการดาวน์โหลดของ gdown: ฉะเชิงเทรา ได้เฉพาะโฟลเดอร์ 1 (DEM) · 2 (ขอบเขต/จุด) · 3 (ถนน) · ส่วนที่เหลือล้มเหลว (ข้อความ "Cannot retrieve the public link") · จังหวัดอื่นยังไม่ได้ไฟล์
**ชั้นที่ต้องการ** (รวม ~45 MB ต่อจังหวัดจากขนาดของนครนายก): `2 Boundary and Point` · `5 Surface and Ground Water` · `6 Valley Ridge and Basin` · `7 Geological Hazard` (มี `Flood GISTDA 0519` น้ำท่วม 2548–2554) — ข้ามโฟลเดอร์ Contour Line (หนัก ~115 MB และติดข้อจำกัดบ่อย)
วางไฟล์ที่ `data/10_mitrearth_gis/provinces/<จังหวัด>/<ชื่อโฟลเดอร์ย่อย>/` (ไฟล์ใหญ่ไม่เข้า git) แล้วแจ้งเพื่อรันวิเคราะห์ GISTDA/ลุ่มน้ำรายจังหวัดและบันทึก SHA-256

| จังหวัด | โฟลเดอร์ย่อย | ลิงก์ Google Drive |
|---|---|---|
| ฉะเชิงเทรา | 2 Boundary and Point | https://drive.google.com/drive/folders/1oI22A62ZBNXMcWTJ4EgKIFBckmqxL8d7 |
| ฉะเชิงเทรา | 5 Surface and Ground Water | https://drive.google.com/drive/folders/1Cr8ZIapPUVCCRztcOH5SjFr-1yeQrn21 |
| ฉะเชิงเทรา | 6 Valley Ridge and Basin | https://drive.google.com/drive/folders/1wUaQnxaBjLk1ba-oUInS3gbOZEoY1hGz |
| ฉะเชิงเทรา | 7 Geological Hazard | https://drive.google.com/drive/folders/1tsnUhYat4S_Uawyhw2fs6yuyOEFS9waI |
| กรุงเทพมหานคร | 2 Boundary and Point | https://drive.google.com/drive/folders/10AyJvObEJxVOEnv-xUjFzHQp_m58vcCB |
| กรุงเทพมหานคร | 5 Surface and Ground Water | https://drive.google.com/drive/folders/1kCz4XyfMewRZseYiljZ647byqGY2zWa8 |
| กรุงเทพมหานคร | 6 Valley Ridge and Basin | https://drive.google.com/drive/folders/1BhohCp27m81LFSAPhdVxNMM8KcXRlIUZ |
| กรุงเทพมหานคร | 7 Geological Hazard | https://drive.google.com/drive/folders/13CVcIpRTQPqlJvF_XZpSqEwE3QkxJ2RU |
| ปทุมธานี | 2 Boundary and Point | https://drive.google.com/drive/folders/1glWStMeEYq4d6RtI3zAKxYaITvakZvAT |
| ปทุมธานี | 5 Surface and Ground Water | https://drive.google.com/drive/folders/11S9j4SMO0Cn1LbL65AD9rb25VKMH3vIo |
| ปทุมธานี | 6 Valley Ridge and Basin | https://drive.google.com/drive/folders/1jtZ16URBCE07OymEk5cnOqwOeNozYAxX |
| ปทุมธานี | 7 Geological Hazard | https://drive.google.com/drive/folders/1UL6q2tgNBIlJakg5whNiHHIlMJi3sDLZ |
| ปราจีนบุรี | 2 Boundary and Point | https://drive.google.com/drive/folders/1nw02Of5FJKluJ0DmzJC6NJQOY_BI9EZz |
| ปราจีนบุรี | 5 Surface and Ground Water | https://drive.google.com/drive/folders/1OcT3WO2a3dxrv6CV5viodhY0t5W6d_qX |
| ปราจีนบุรี | 6 Valley Ridge and Basin | https://drive.google.com/drive/folders/1404pX9tbL-rbM4xqu8LhslSA2SpeZWZY |
| ปราจีนบุรี | 7 Geological Hazard | https://drive.google.com/drive/folders/1z-NrdBpebljIIOxJzQf6fk7SHO8QsOF1 |
| สมุทรปราการ | 2 Boundary and Point | https://drive.google.com/drive/folders/1-Olf7Lnx_-1kJFqWcIRmoOjjT402hYTC |
| สมุทรปราการ | 5 Surface and Ground Water | https://drive.google.com/drive/folders/1r_nM5F9CWDJNOSHJRt6Lm7LjiGQmfLlr |
| สมุทรปราการ | 6 Valley Ridge and Basin | https://drive.google.com/drive/folders/1-1QSTnlsTdBg90nQyDKZR18uwlYpbzK6 |
| สมุทรปราการ | 7 Geological Hazard | https://drive.google.com/drive/folders/1aXRL3SU1g9VupB6WQe7tu7B6eumdJz07 |
| พระนครศรีอยุธยา | 2 Boundary and Point | https://drive.google.com/drive/folders/1O0H_yQgLaUgcyZyFAPmJ118amBwz9BpV |
| พระนครศรีอยุธยา | 5 Surface and Ground Water | https://drive.google.com/drive/folders/1ovTUgB-kjYFGCXylG-tuUxO2vtD_rzvY |
| พระนครศรีอยุธยา | 6 Valley Ridge and Basin | https://drive.google.com/drive/folders/1ZlO6OOKWhCsAaLyBpshpeucG1P8dRnP_ |
| พระนครศรีอยุธยา | 7 Geological Hazard | https://drive.google.com/drive/folders/1_njaTJCJo-_r7eQ1UVjUXLiBQrzJJTGF |
| อ่างทอง | 2 Boundary and Point | https://drive.google.com/drive/folders/1T56uRYEliHiOvfla1u_KZfL1HnruNrb5 |
| อ่างทอง | 5 Surface and Ground Water | https://drive.google.com/drive/folders/1jKCVaob4VT5yDVwNqOiD74PnA40Hdz1N |
| อ่างทอง | 6 Valley Ridge and Basin | https://drive.google.com/drive/folders/1r03Ot3iglVx_aTuaw27_vz6d-IwBc_ca |
| อ่างทอง | 7 Geological Hazard | https://drive.google.com/drive/folders/1l3u5RzVqM4x2NfTYx2byDhcfkbJn20-q |
| สิงห์บุรี | 2 Boundary and Point | https://drive.google.com/drive/folders/1Wsl25GxzD4WJTYTJGb5Ckj_I7VuidjsO |
| สิงห์บุรี | 5 Surface and Ground Water | https://drive.google.com/drive/folders/1LSCS8mbIGwkfBDxeP34NqDQjmFWURKwB |
| สิงห์บุรี | 6 Valley Ridge and Basin | https://drive.google.com/drive/folders/1fH0WvbaRIqpG5HwOQe63Qb8pmouLi-Zs |
| สิงห์บุรี | 7 Geological Hazard | https://drive.google.com/drive/folders/1CHxqdOdERqWqa2Iz5GLDAEzl3yUXXU3j |
| นนทบุรี | 2 Boundary and Point | https://drive.google.com/drive/folders/18RfYG33PsOQBHK1HkGsGvBD9wsLwH0cH |
| นนทบุรี | 5 Surface and Ground Water | https://drive.google.com/drive/folders/1jZPslmToV7HxT1sesKebGR_os7CToIpA |
| นนทบุรี | 6 Valley Ridge and Basin | https://drive.google.com/drive/folders/11jwIDrbwJU0QLoj0A1Z_McxDKjiVzLnL |
| นนทบุรี | 7 Geological Hazard | https://drive.google.com/drive/folders/1A5RHvXhxST7K8K8HuhxO3_lqVMyps7Eb |
| สมุทรสาคร | 2 Boundary and Point | https://drive.google.com/drive/folders/1V9UAECvON8T37gDjYlY8ec79H5v_iJ28 |
| สมุทรสาคร | 5 Surface and Ground Water | https://drive.google.com/drive/folders/1z807gKdHbMmYbzWTapW2vc9am6n69FfG |
| สมุทรสาคร | 6 Valley Ridge and Basin | https://drive.google.com/drive/folders/1caYCfcwhZ1xi6G7jSX_Ex2hZwrtxUM-_ |
| สมุทรสาคร | 7 Geological Hazard | https://drive.google.com/drive/folders/1mR3Uwqa7QvBfLCEGUS42fgboYQSBZbql |
