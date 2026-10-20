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
  2. เส้นชั้น 1 ม. **2 ชุด** (ผู้ใช้ชี้ชุดที่สอง 20 ต.ค. 69): (ก) `GIS File/18 Contour 1 m NAKHON NAYOK - mitrearth.shp` 10,592 เส้น ครอบหน้าต่าง DEMPro 5 ม. → **สร้างจาก DEMPro** (DEMPro − เส้นชั้น เฉลี่ย +0.03 ม. · MAE 0.12 ม.) · (ข) `4 Contour Line/18 Contour1m.shp` 72.8 MB 111,298 เส้น ทั้งจังหวัด (−12 ถึง 1,347 ม.) → **สร้างจาก DEM 30 ม. ของมิตรเอิร์ธ** (MAE 0.42 ม.) · ทั้งสองจึงไม่ใช่การสำรวจอิสระ · เทียบ FABDEM: ชุด (ก) สูงกว่าเส้นชั้น +1.93 ม. · ชุด (ข) −1.23 ม. (ข้อสรุปเดิมที่ว่า "เส้นชั้นต่ำกว่า DEM ~2 ม. โดยไม่ทราบสาเหตุ" แก้แล้ว: เป็นความต่างเชิงดิ่งระหว่างชุด DEM)
  3. `Flood Riverbank` (จุด 5,365) · `Overflow Flood` (เส้นลำน้ำ 898 ฟิลด์ MAX_FLOW) · `Riverbank Erosion` · `Major River` — ชั้นน้ำล้นตลิ่ง/ลำน้ำสายหลัก
  4. `Drainage Basin` (kmz) + shapefile `6 Valley Ridge and Basin` — ลุ่มน้ำย่อยและสันปันน้ำ → ตรวจไขว้กับพื้นที่รับน้ำย่อย PK-AT-x ของ EIA
  5. `จุดอพยพหนีน้ำท่วม` · `จุดเสี่ยงน้ำตัดถนน` — จุดถนนตัดร่องน้ำ (ใช้ดูทางหลวง 305/ถนนที่น้ำตัด)
  6. `Surface and Ground Water` shapefile + `groundwater wells DGR` — บ่อบาดาล/ระดับน้ำใต้ดิน
  7. ภาพถ่ายทางอากาศ/แผนที่เก่า `MR_M8_2523` (285 MB) · `SAGRIC_003_2533` (643 MB) · `5019…1756.tif` (160 MB) · `Topo 1:50,000` (kmz 67 MB) — ฐานเทียบการใช้ที่ดินปี 2523/2533
  8. DEM 30 ม. (`18 DEM30m - mitrearth.tif`) — ต้นทางไม่ระบุ (นัย SRTM/ASTER) ไม่ควรแทน Copernicus/FABDEM
     **แก้ไข 20 ต.ค. 69 (ผู้ใช้ชี้ — ข้อความ "ไม่มี DEM ละเอียด" ข้างบนผิด):** ในซิปนครนายกมี **DEMPro ~5 ม.** (`GIS File/18 DEMPro NAKHON NAYOK - mitrearth.grd` · Surfer 7 float64 4,054×3,999 เซลล์ ครอบ 101.121–101.307°E 14.114–14.294°N ≈ 384 ตร.กม. ตัวเมือง/ตะวันออกของจังหวัด **ไม่ครอบองครักษ์**) + เส้นชั้น 5 ม. จากชุดนี้ (`GIS File/18 Contour 5 m … .shp` 1,906 เส้น) · ไฟล์ `.tif` ของ DEM เป็นภาพ 8 บิต ใช้อ่านความสูงไม่ได้ (ใช้ `.grd`) · เทียบ FABDEM: DEMPro **ต่ำกว่าเฉลี่ย 2.16 ม.** (SD 0.75 ม. 361,511 เซลล์ที่ราบต่ำ) · ที่มาไม่ระบุ — ผลใน `analysis/goal7/mitrearth_dempro_summary.json`
     ชั้นอื่นที่เพิ่งตรวจ: **Topo 1:50,000** = KMZ ภาพแผนที่ (ปิรามิด 5 ระดับ ครอบทั้งจังหวัด 100.913–101.505°E 13.961–14.513°N · ภาพแผนที่ ไม่ใช่เวกเตอร์ ใช้ดู/สร้างข้อมูลมือได้) · `5019…1756.tif` = **ภาพถ่ายทางอากาศฟิล์มเก่า (AMS, "2 JAN 53" กรอบ 1756) 12,683×12,601 พิกเซล ยังไม่มีพิกัดอ้างอิง** (ต้องอ้างอิงพิกัดก่อนใช้) · MR_M8_2523 / SAGRIC_003_2533 = ภาพถ่ายทางอากาศ 2523/2533
- **ยังไม่ได้ประมวลผลชั้นใดเพิ่ม** (งานค้าง R7-13 — ดู docs/OFFLINE_DATA_BACKLOG.md §7) · ชุดข้อมูลจังหวัดข้างเคียงที่คลองผ่าน (สระบุรี · ฉะเชิงเทรา · สมุทรปราการ ฯลฯ) ดาวน์โหลดได้จากหมวดเดียวกันถ้าต้องการ — เป็นการดาวน์โหลดไฟล์ใหม่ ต้องให้ผู้ใช้อนุญาตและระบุชื่อ/ขนาดก่อน

## ชุดรายจังหวัดลุ่มเจ้าพระยาตอนล่าง (โหลดเอง 19–20 ต.ค. 2569 — ได้ครบ 40 ไฟล์ · backlog R7-15 ปิดแล้ว)

ผู้ใช้โหลดจาก Google Drive ของมิตรเอิร์ธ (หน้าจังหวัดบน mitrearth.org) ชุดย่อย 4 โฟลเดอร์ต่อจังหวัด: `2 Boundary and Point` · `5 Surface and Ground Water` · `6 Valley Ridge and Basin` · `7 Geological Hazard` — 10 จังหวัด รวม 40 ไฟล์ zip (204 MB) เก็บต้นฉบับที่ `provinces_zips/<จังหวัด>/` (ไม่เข้า git) · แตกไฟล์แล้วที่ `data/10_mitrearth_gis/provinces/<จังหวัด>_<รหัส>/<โฟลเดอร์ย่อย>/` (ไม่เข้า git)
ตรวจแล้ว: zip สมบูรณ์ทั้ง 40 ไฟล์ (testzip) · สิทธิ์ใช้งานเหมือนนครนายก (ประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์)

**ข้อควรรู้ (ตรวจแล้วว่าไม่ใช่ไฟล์ที่หายจากการโหลด — จำนวนไฟล์ใน zip เท่ากับในโฟลเดอร์ Drive):**
- ชั้นน้ำท่วม `Flood GISTDA 0519` ของ **สมุทรปราการ · สมุทรสาคร · สิงห์บุรี · อ่างทอง** ไม่มีไฟล์ `.shp`/`.dbf` บน Drive (มีแต่ `.prj .shx`) → ไม่มีข้อมูลน้ำท่วม 2548–2554 ของ 4 จังหวัดนี้ (อ่างทองไม่มี `Drainage Basin.shp` ด้วย) · จังหวัดที่มีชั้น GISTDA: ฉะเชิงเทรา · ปราจีนบุรี · ปทุมธานี · นนทบุรี · กรุงเทพฯ · อยุธยา (+ นครนายก)
- ชั้น `bound` และ `pbound` เป็นกรอบแผนที่/จังหวัดข้างเคียง (ใหญ่กว่าจังหวัดราว 2 เท่า) **ห้ามใช้เป็นเส้นเขตจังหวัด** — ใช้การรวมชั้น `Tambon area` (ตรวจพื้นที่: กทม. 1,569 · นนทบุรี 633 · ฉะเชิงเทรา 5,238 ตร.กม.)
- ผลวิเคราะห์: `analysis/goal7_mitrearth_provinces.py` → `analysis/goal7/mitrearth_provinces_summary.json`

| ไฟล์ | ขนาด (ไบต์) | SHA-256 |
|---|---|---|
| `provinces_zips/กรุงเทพมหานคร/2 Boundary and Point-20261019T153755Z-1-001.zip` | 1170320 | `83dc4b6c86669e79faf4953e6eb1d281a0706174991f57f5be52bf28a6a6dba5` |
| `provinces_zips/กรุงเทพมหานคร/5 Surface and Ground Water-20261019T153800Z-1-001.zip` | 2900855 | `a50d18a56d96bc7b585c7306940455ff591d69953fcd6d2a3f10d7e2054f4676` |
| `provinces_zips/กรุงเทพมหานคร/6 Valley Ridge and Basin-20261019T153804Z-1-001.zip` | 1367475 | `b2a8f4b275fdc4c082c4a79d7bcc714aba047561daccb95865d48636463894ca` |
| `provinces_zips/กรุงเทพมหานคร/7 Geological Hazard-20261019T153809Z-1-001.zip` | 8713750 | `71791b052693d70e7f4a75bca998f0a23c59dae08d2d58087350389cb4eb0366` |
| `provinces_zips/ฉะเชิงเทรา/2 Boundary and Point-20261019T153412Z-1-001.zip` | 1131777 | `dd3f745e180246365ed02859d2e42840227ea3f8894c8239fababf737a87c189` |
| `provinces_zips/ฉะเชิงเทรา/5 Surface and Ground Water-20261019T153707Z-1-001.zip` | 4590884 | `267293e93f8d65ac440212972d97e878cbd07182908b9cc061367f200baaae9b` |
| `provinces_zips/ฉะเชิงเทรา/6 Valley Ridge and Basin-20261019T153519Z-1-001.zip` | 5140939 | `f53587d6991b29feca0b00e2dc6936d9fedaad095f6ad8eb41635a8feb400f9d` |
| `provinces_zips/ฉะเชิงเทรา/7 Geological Hazard-20261019T153534Z-1-001.zip` | 32946364 | `698ea35c71e78d77ce3b8a0cb64e269ac80f3b1a645509ca25c1bae3f133a1d0` |
| `provinces_zips/นนทบุรี/2 Boundary and Point-20261020T035121Z-1-001.zip` | 288006 | `3cdf2e2a6be623107c7c79bd939f62f08b36d46ae0f7cebbb96ef8372c5b67ea` |
| `provinces_zips/นนทบุรี/5 Surface and Ground Water-20261020T035124Z-1-001.zip` | 1043132 | `0aba83d4c81d3f252b0642a0a3205b5d66abd1697c7f07d3c7e0590a7e0a25b1` |
| `provinces_zips/นนทบุรี/6 Valley Ridge and Basin-20261020T035129Z-1-001.zip` | 814931 | `38a16cb5d42ef94329b4fb30986cd0d3d258b49c56e7e8cdd7e86d5990a4a8f9` |
| `provinces_zips/นนทบุรี/7 Geological Hazard-20261020T035136Z-1-001.zip` | 5560504 | `6beee237aaa07013bdd67331521c4033de5a4cf54f8a21ecd105d483cea274b6` |
| `provinces_zips/ปทุมธานี/2 Boundary and Point-20261019T153906Z-1-001.zip` | 237440 | `531fe22d65dc2f174fc87e86e9afb0488d217564183816bc43d93a15a8e75bfa` |
| `provinces_zips/ปทุมธานี/5 Surface and Ground Water-20261019T153909Z-1-001.zip` | 1543503 | `2c78aa26ca4f2c55d93c860e26daf31c60d5b6365756754839fd52e98da0127f` |
| `provinces_zips/ปทุมธานี/6 Valley Ridge and Basin-20261019T153913Z-1-001.zip` | 1428650 | `bcdee099e699ec744a5838c56e75b0f94141ccf8640a2e0c8a7cf4e52941fbdf` |
| `provinces_zips/ปทุมธานี/7 Geological Hazard-20261019T153919Z-1-001.zip` | 12315011 | `51f5e6984b19068bcbe638757709b7b62c4fdbde65e1489822cbd8b194fb7722` |
| `provinces_zips/ปราจีนบุรี/2 Boundary and Point-20261019T154129Z-1-001.zip` | 1626639 | `924be25e1425500a285dfacaeed7731134b5b4948e6bcb88b507f12eefbcf026` |
| `provinces_zips/ปราจีนบุรี/5 Surface and Ground Water-20261019T154132Z-1-001.zip` | 4788156 | `d3c0c03f50c7d65435e8c05e6b9918630d71e07e78921b68182cd6475cba8ccc` |
| `provinces_zips/ปราจีนบุรี/6 Valley Ridge and Basin-20261019T154136Z-1-001.zip` | 5272416 | `336b2fcb8f04b87f1fc292181ec79468c437b1e712fd3f80733025ad763da3fd` |
| `provinces_zips/ปราจีนบุรี/7 Geological Hazard-20261019T154140Z-1-001.zip` | 37500160 | `6ab5539f6f3cddba5af151c41f34b510aa9919e33a80f0cf3126ea0bdcf43bc7` |
| `provinces_zips/พระนครศรีอยุธยา/2 Boundary and Point-20261020T034553Z-1-001.zip` | 573602 | `06a4b910adceed3724afd76f1e43df3ac5e18ba5142c735d243c7de1c7990a29` |
| `provinces_zips/พระนครศรีอยุธยา/5 Surface and Ground Water-20261020T034555Z-1-001.zip` | 3547913 | `fa0f77bc714e72455d334b07189fac4cfca9b3e0adffcd04a25295f2be58d8a5` |
| `provinces_zips/พระนครศรีอยุธยา/6 Valley Ridge and Basin-20261020T034600Z-1-001.zip` | 3298813 | `ab1ffa8e79373da7f21434d1e3348724b6a3944bb95ca0adb90d69b4216e68f0` |
| `provinces_zips/พระนครศรีอยุธยา/7 Geological Hazard-20261020T034604Z-1-001.zip` | 67609991 | `627f52922e51ce4c110b65509588296e80869d5ba2b0c1213aad9586d0dd8d62` |
| `provinces_zips/สมุทรปราการ/2 Boundary and Point-20261019T154349Z-1-001.zip` | 520541 | `2a65e1bcfbe4a168b90347643394cf06c812ab759622fc9c80a8cfe6aafa4815` |
| `provinces_zips/สมุทรปราการ/5 Surface and Ground Water-20261019T154353Z-1-001.zip` | 694007 | `73723f9c252221c0c2403cc0bbde4574987e74525b69eb53395160a8e62ef380` |
| `provinces_zips/สมุทรปราการ/6 Valley Ridge and Basin-20261019T154358Z-1-001.zip` | 767679 | `4f60daf84f4351f1a4fae928977bde36d987f95ca405616c460d718816935140` |
| `provinces_zips/สมุทรปราการ/7 Geological Hazard-20261019T154401Z-1-001.zip` | 71626 | `e57365bf39c624bc2be10cde9a08ea7deefd8f2c4a12a628b4000917c7dd3bbc` |
| `provinces_zips/สมุทรสาคร/2 Boundary and Point-20261020T035322Z-1-001.zip` | 859008 | `5526f02ead46d2315754d582d5df9c679b59643a2fd77903d5f1db029913285c` |
| `provinces_zips/สมุทรสาคร/5 Surface and Ground Water-20261020T035327Z-1-001.zip` | 558471 | `4818c6596312b4f4f2ffbdd28aa945da75c923357d7554b636b4fb92dd99ea40` |
| `provinces_zips/สมุทรสาคร/6 Valley Ridge and Basin-20261020T035331Z-1-001.zip` | 748852 | `5aa107508643169e74a87a0a3998b4b39bd46864d15105c15615d702100eeb35` |
| `provinces_zips/สมุทรสาคร/7 Geological Hazard-20261020T035336Z-1-001.zip` | 23448 | `f9e42ea04a3b04efbf75273e653ff1c2fdb9241307680a19970f8bef21d80820` |
| `provinces_zips/สิงห์บุรี/2 Boundary and Point-20261020T034913Z-1-001.zip` | 265496 | `3336f7601a79cf5752d0ac9bf5db6ac185cb0d771c5a280c76540c3cc037458e` |
| `provinces_zips/สิงห์บุรี/5 Surface and Ground Water-20261020T034917Z-1-001.zip` | 797026 | `a9911767c03451c1138e10ee557c63039b6e90754abbec11e657022d934ce7a1` |
| `provinces_zips/สิงห์บุรี/6 Valley Ridge and Basin-20261020T034921Z-1-001.zip` | 730108 | `f094911b1261c24c6235eab82f6d42416a291a36bf296208c4afc0634d86f2ff` |
| `provinces_zips/สิงห์บุรี/7 Geological Hazard-20261020T034928Z-1-001.zip` | 161717 | `39c66818ff2a207cc3a2063e02a6056bcb55195993c8aa8c205ecdb9a6c4b3a7` |
| `provinces_zips/อ่างทอง/2 Boundary and Point-20261020T034730Z-1-001.zip` | 414484 | `6cc4b966ad171bbd96045be83e96a6b4aa5f553a482fd8509893bc82f31996d7` |
| `provinces_zips/อ่างทอง/5 Surface and Ground Water-20261020T034736Z-1-001.zip` | 889267 | `2a0d2e6ac8f77f84cca2345a1cb2373fbca747039e64f45008f9f5c41f819a11` |
| `provinces_zips/อ่างทอง/6 Valley Ridge and Basin-20261020T034740Z-1-001.zip` | 663130 | `c2bb0fa37e19bd2f785564d3eaa4fed9af7c955d9352e01b1bb2a438b047ae24` |
| `provinces_zips/อ่างทอง/7 Geological Hazard-20261020T034745Z-1-001.zip` | 113851 | `9d75464e12329b6dd77893d1092e102adfd21f7c498e602d284076ca90fdb340` |

## ชุดระดับประเทศ "3 Thailand" (ผู้ใช้โหลดเอง 20 ต.ค. 2569 — backlog R7-19)

ชุดข้อมูลชุดเดียวกับชุดนครนายก แต่ระดับประเทศ · 1,147 ไฟล์ 2.1 GB · ย้ายมาเก็บที่ `data/10_mitrearth_gis/thailand_pack/` (ไม่เข้า git) · แฮช SHA-256 ครบทุกไฟล์ใน `thailand_pack_hashes.txt` (ตรวจด้วย verify_data_integrity ได้) · สิทธิ์ใช้งานเหมือนเดิม (ประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์)
**ผลตรวจ: ชั้น shapefile ไม่ครบทุกชุด (0 ชุดสมบูรณ์ จาก 71 ชุด)** — ไฟล์ขนาดใหญ่ส่วนใหญ่ไม่ได้ถูกโหลดมา (น่าจะ Drive ตัดตอนโหลดโฟลเดอร์ใหญ่):
- **น้ำท่วม GISTDA 2005–2019 ทั้งประเทศ** (`5 PDF Flood GISDA 2005-2019/GIS Flood GISTDA Thailand 2005-2019/1 GISTDA Flood Polygon 2005-2019/flood_20XX`) มีแต่ชิ้นส่วนเล็ก (`.prj`/`.xml`/`.sbx`) ไม่มี `.shp/.dbf/.shx` ของปีใดเลย — ต้องโหลดใหม่ทีละไฟล์ (มี 4 ภาพแผนที่ปี 2006 · 2014 · 2018 · 2019 เป็นภาพอย่างเดียว)
- **ความถี่น้ำท่วม 15 ปี** (`5 GE Flood Density 2005-2019`: Flood Bed 1–15 of 15 time) มี `.shp` บางชุดไม่มี `.dbf/.shx` · ชั้น `GIS File Density Point` มีเพียง 2 ไฟล์ข้อความ (9.txt, 13.txt)
- **ระดับน้ำทะเลสูงขึ้น 4/6/8/10 ม.** — มี KMZ ชุด 8 ม. ครบ (49 MB) แต่ shapefile ขาด
- **ลุ่มน้ำ/เส้นทางน้ำ (41)** · **น้ำท่วมแบนราบ DMR (4 Hazard)** ขาด `.dbf/.shx`
ไฟล์ที่ขาดของชั้นสำคัญ (ต้องโหลดใหม่):

| โฟลเดอร์ | ชั้น | ขาดไฟล์ |
|---|---|---|
| 32 If Sea Level Rise | 1 Sea Level Rise 10 m - mitrearth | .dbf .shp |
| 32 If Sea Level Rise | 1 Sea Level Rise 4 m - mitrearth | .dbf .shx |
| 32 If Sea Level Rise | 1 Sea Level Rise 6 m - mitrearth | .dbf .shx |
| 4 PDF Hazard | 8-1-class_1_landslide_and_flatflood_dmr | .dbf .shx |
| 4 PDF Hazard | 8-1-class_2_landslide_and_flatflood_dmr | .dbf .shx |
| 4 PDF Hazard | 8-1-class_3_landslide_and_flatflood_dmr | .shx |
| 41 Dam Basin and Stream Flow | 3 Basin - mitrearth | .dbf .shx |
| 5 GE Flood Density 2005-2019 | 1 Flood Bed Thailand 1of15 time - mitrearth | .dbf .shx |
| 5 GE Flood Density 2005-2019 | 12 Flood Bed Thailand 12of15 time - mitrearth | .dbf .shx |
| 5 GE Flood Density 2005-2019 | 2 Flood Bed Thailand 2of15 time - mitrearth | .dbf .shx |
| 5 GE Flood Density 2005-2019 | 4 Flood Bed Thailand 4of15 time - mitrearth | .shp .shx |
| 5 GE Flood Density 2005-2019 | 5 Flood Bed Thailand 5of15 time - mitrearth | .shp .shx |
| 5 GE Flood Density 2005-2019 | 6 Flood Bed Thailand 6of15 time - mitrearth | .shp .shx |
| 5 GE Flood Density 2005-2019 | 7 Flood Bed Thailand 7of15 time - mitrearth | .shp .shx |
| 5 GE Flood Density 2005-2019 | 9 Flood Bed Thailand 9of15 time - mitrearth | .dbf .shx |
| 5 PDF Flood GISDA 2005-2019 | 2_flood_moderate_risk | .dbf .shp |
| 5 PDF Flood GISDA 2005-2019 | flood2012 | .dbf .shp .shx |
| 5 PDF Flood GISDA 2005-2019 | flood_2011_geo | .dbf .shp .shx |
| 5 PDF Flood GISDA 2005-2019 | flood_2014 | .dbf .shp .shx |
| 5 PDF Flood GISDA 2005-2019 | flood_2016 | .dbf .shp .shx |
| 5 PDF Flood GISDA 2005-2019 | flood_2018 | .shp .shx |

**ชั้นที่สมบูรณ์และใช้แล้ว** (`analysis/goal7_mitrearth_thailand.py` → `analysis/goal7/mitrearth_thailand_summary.json`):
- `24 GE Hydrology/1 ประตูระบายน้ำ/3_Hydro_Station_RID` (KMZ 551 สถานีกรมชลประทาน มีพิกัดและรหัส — ในพื้นที่ศึกษา 96 แห่ง รวม **Ny.1B · Ny.3 · Ny.4 · Ny.6**; ไม่มี Ny.7) → `analysis/goal7/rid_hydro_stations_study_area.csv`
- `38 City (Province - District) Topography/4-4 … จุดร่องน้ำตัดถนน` (KMZ 9,431 จุดทั่วประเทศ มีระดับ · ความลาด · พื้นที่รับน้ำ) → 28 จุดภายใน 3 กม. จากแนวคลอง → `analysis/goal7/stream_road_crossings_corridor.csv`
- `33 GE Village Nature Slide Flow Flood/3 Village Regional Flood - mitrearth.txt` (85,197 หมู่บ้าน พิกัด · ระดับพื้น · ความลาด · ที่ตั้ง — ไฟล์ TIS-620/cp874) → นับหมู่บ้านใกล้แนวคลอง (ไม่ระบุชื่อ)
**เก็บไว้แต่ยังไม่ประมวลผล:** 38 City (KMZ เส้นชั้น 5 ม. 559,712 เส้น 175 MB · แม่น้ำสายหลัก · ธารน้ำสายรอง 111,365 เส้น · โครงข่ายถนน) · 23 ถนนหลัก/จุดตัดถนน · 24 บ่อบาดาล กรมทรัพยากรธรณี · 32 ระดับน้ำทะเล 8 ม. (KMZ) · 4 Hazard/25 Geology/35 Sinkhole/39 Tsunami/30 Coffee (นอกขอบเขตโครงการ)
**ไม่มีประโยชน์:** `36 SAGA Thailand` (1.6 GB: TIFF ระดับประเทศเป็นภาพ 8 บิต ไม่ใช่ค่าความสูง/ความลาด · กริดรายจังหวัดความละเอียด 0.01° ≈ 1.1 กม.) · `21 Topo Map 1-50000 Thailand` (ไฟล์ .ige ขนาด 0 ไบต์)
