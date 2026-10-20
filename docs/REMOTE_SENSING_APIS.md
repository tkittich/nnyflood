# คู่มือการเรียกใช้ API ดาวเทียมและข้อมูลกริดระดับชาติ (Remote Sensing & Grid APIs Guide)

> สถานะ: สร้าง 17 ต.ค. 2569 — บันทึกเชิงเทคนิคเพื่อการบำรุงรักษาและการสืบค้นอัตโนมัติ  
> ครอบคลุม: GISTDA Disaster Platform, NASA POWER Precipitation, และ Copernicus Data Space Ecosystem (CDSE)

---

## 1. ข้อมูลภาพรวมและการจัดการข้อมูลความลับ (Credential Management)

โปรเจกต์นี้ใช้ข้อมูลภาพถ่ายดาวเทียมและข้อมูลอุตุนิยมวิทยาเชิงกริดจาก 3 แหล่งหลักที่มี API ออนไลน์ เพื่อคำนวณพื้นที่น้ำท่วม สถิติฝน 46 ปี และการจำแนกประเภทผิวดิน:

* **กติกาความปลอดภัยขั้นสูงสุด**: ข้อมูลรหัสผ่านหรือ API Key ทุกชนิด **ต้องเก็บในไฟล์ที่ถูกระบุใน `.gitignore` เสมอ** (ห้ามพิมพ์ลงในโค้ด ห้าม print/log ออกหน้าจอ และห้ามส่งออกนอกเครื่อง)
* **ไฟล์ Credential ในโปรเจกต์**:
  * GISTDA API: `data/12_gistda_flood/.gistda_api.json` (มีเฉพาะ API Key)
  * CDSE S3: `data/22_goal6_network/.cdse_s3.json` (มีเฉพาะ S3 Access Key และ Secret)

---

## 2. GISTDA Disaster Platform API (สำนักงานพัฒนาเทคโนโลยีอวกาศและภูมิสารสนเทศ)

GISTDA ให้บริการข้อมูลขอบเขตพื้นที่น้ำท่วมระดับชาติที่สกัดจากดาวเทียมหลายดวง (ทั้งเรดาร์ SAR และภาพถ่ายทางแสง) ผ่านระบบคลาวด์ Disaster Platform

* **พอร์ทัลหลัก**: `https://disaster.gistda.or.th/`
* **Base URL สำหรับ API Gateway**: `https://api-gateway.gistda.or.th/api/2.0/resources/features/flood`
* **การพิสูจน์ตัวตน (Authentication)**: ส่งคีย์เป็นพารามิเตอร์ `api_key=` ในสายคำขอ (ไม่ใช่ Header) — คีย์อยู่ในไฟล์ gitignored `data/12_gistda_flood/.gistda_api.json` (ห้ามพิมพ์/คัดลอกค่าคีย์) · แก้เมื่อ 20 ต.ค. 69: ฉบับก่อนหน้าเขียนว่าใช้ `Authorization: Bearer` และพารามิเตอร์ `province=` ซึ่งไม่ตรงกับสคริปต์ที่ใช้ได้จริง
* **ที่เก็บข้อมูลในโปรเจกต์**: [`data/12_gistda_flood/`](file:///e:/theera/code/flood/data/12_gistda_flood/)
* **สคริปต์หลักที่เรียกใช้**: [`analysis/goal6_fetch_gistda_flood.py`](file:///e:/theera/code/flood/analysis/goal6_fetch_gistda_flood.py) (`fetch_province_flood(api_key, "จ.ฉะเชิงเทรา", endpoint)` แคชต่อจังหวัดที่ `data/12_gistda_flood/raw/provinces/<จังหวัด>_<endpoint>.json` · ถ้าต้องเก็บสแนปช็อตเก่า ให้เปลี่ยนชื่อไฟล์เป็นมีวันที่ก่อนดึงใหม่)
* **จุดเรียก (endpoint)** — ฐาน `https://api-gateway.gistda.or.th/api/2.0/resources/features/`:

| จุดเรียก | ได้อะไร | หมายเหตุ (ตรวจกับข้อมูลจริง 20 ต.ค. 69) |
|---|---|---|
| `flood/30days` | พื้นที่น้ำท่วมช่วง 30 วันล่าสุด | ชั้นผสมหลายฉาก — ทุกรูปทรงในผลคืนมีรายชื่อฉากชุดเดียวกัน แยกวันท่วมต่อแปลงไม่ได้ · หน้าต่างเลื่อนตามวันที่ดึง |
| `flood/7days` | ช่วง 7 วันล่าสุด | คลุมหลายดาวเทียมถึงฉากของวันที่ดึง |
| `flood/3days`, `flood/1day` | ช่วง 3 / 1 วันล่าสุด | คลุมเฉพาะแนวของฉากที่ผ่านล่าสุด จึงใช้เทียบทั้งจังหวัดไม่ได้ |
| `flood-freq` | ความถี่น้ำท่วมซ้ำซาก 2554–2567 (ค่าธง `y_<ปี>` ต่อรูปทรง และ `freq`) | ไฟล์ใหญ่มาก (ปราจีนบุรีราว 540 MB) |
| `flood/15days`, `flood/daily`, `flood/latest` | — | **ไม่มี** (404) |

* **พารามิเตอร์**: `api_key` · `pv_tn` (ชื่อจังหวัดมีคำนำหน้า เช่น `จ.ฉะเชิงเทรา` หรือ `กรุงเทพมหานคร`) · `limit` (สูงสุด 1000) · `offset` · ผลคืนมี `numberMatched`/`numberReturned` และ `features` (GeoJSON)
* **ฟิลด์สำคัญของรูปทรง**: `f_area` (พื้นที่น้ำท่วมจริง ตร.ม. — **ไม่รวมแหล่งน้ำถาวร**) · `h3_area`/`h3_address` (ตารางหกเหลี่ยม H3 ที่ครอบ) · `rice_area`, `cassava_area`, `maize_area`, `sugarcane_area` · `population`, `building`, `school`, `hospital`, `length_road` · `ap_tn` (อำเภอ) `tb_tn` (ตำบล) · `file_name` (รายชื่อฉากต้นทาง)
* ⚠️ **พื้นที่รูปทรงใหญ่กว่า `f_area` ราว 2 เท่า** (ฉะเชิงเทรา 30 วัน: รูปทรงรวมประมาณ 884 ตร.กม. แต่ `f_area` รวมประมาณ 430 ตร.กม.) — ใช้ `f_area` เป็นพื้นที่น้ำท่วม ถ้าต้องลงตารางเซลล์ให้ถ่วงด้วย `f_area` ÷ พื้นที่รูปทรง (ดู `goal7_bangpakong_chachoengsao.py::flood_raster`)
* **รหัสฉากใน `file_name`** (`<รหัส>_<วันที่>_<เวลาท้องถิ่น>`): `S1C`/`S1D` = Sentinel-1C/1D (เรดาร์) · `rd2` = RADARSAT-2 · `cm2`/`cm4` = COSMO-SkyMed · `TH2` = THEOS-2 · `S2B`/`S2C` = Sentinel-2 (ภาพแสง) · `cg2` = ไม่ทราบดาวเทียม (ยังไม่มีเอกสารยืนยัน)
* **ตัวอย่างการเรียกคำขอ**:
  ```python
  import json, urllib.parse, urllib.request
  q = urllib.parse.urlencode({"api_key": api_key, "pv_tn": "จ.ฉะเชิงเทรา", "limit": 1000, "offset": 0})
  url = "https://api-gateway.gistda.or.th/api/2.0/resources/features/flood/7days?" + q
  with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nnyflood-research/1.0"}), timeout=60) as resp:
      geojson = json.loads(resp.read().decode("utf-8"))
  ```
* ⚠️ **ข้อจำกัดและจุดที่ต้องระวัง (Gotchas)**:
  1. การสะกดชื่อจังหวัดต้องมีคำนำหน้า เช่น `"จ.นครนายก"` หรือ `"กรุงเทพมหานคร"` (ดูตาราง `PROVINCES_MAP` ในสคริปต์)
  2. ไฟล์ GeoJSON มีขนาดหลายสิบถึงหลายร้อยล้านไบต์ จึงเป็น disk-only ไม่นำเข้า Git (บันทึกเป็นแฟ้มต่อจังหวัด)
  3. ชั้นน้ำท่วมช่วง 7/30 วันไม่เป็นชุดย่อยซ้อนกันพอดีในระดับอำเภอ (บางอำเภอ 7 วันมากกว่า 30 วัน) — ใช้เป็นขนาดคร่าว ๆ ไม่ใช่เส้นเวลาน้ำลด · แผนที่รายฉากที่แยกวันได้ต้องโหลดผลิตภัณฑ์รายฉากจาก disaster.gistda.or.th (งานมนุษย์ R7-22)
  4. ยังไม่พบเอกสารทางการของ API ชุดนี้ — ตารางด้านบนมาจากการทดลองเรียกจริง (ตรวจรหัสตอบกลับและฟิลด์) ไม่ใช่ข้อกำหนดของผู้ให้บริการ

---

## 3. NASA POWER Precipitation API (การประเมินฝนรายวัน 46 ปี)

NASA POWER (Prediction Of Worldwide Energy Resources) ให้บริการข้อมูลอุตุนิยมวิทยาจากการรวมดาวเทียมและการจำลองแบบ Reanalysis (MERRA-2) ครอบคลุมทั่วโลก

* **พอร์ทัลหลัก**: `https://power.larc.nasa.gov/`
* **Base URL**: `https://power.larc.nasa.gov/api/temporal/daily/point`
* **การพิสูจน์ตัวตน**: **ไม่ต้องใช้ Key (Public Open API)**
* **ที่เก็บข้อมูลในโปรเจกต์**: `data/22_goal6_network/raw/basin_rain/`
* **สคริปต์หลักที่เรียกใช้**: [`analysis/goal6_basin_rain.py`](file:///e:/theera/code/flood/analysis/goal6_basin_rain.py), [`analysis/goal6_rain_rarity.py`](file:///e:/theera/code/flood/analysis/goal6_rain_rarity.py)
* **พารามิเตอร์สำคัญ**:
  * `parameters=PRECTOTCORR`: ปริมาณฝนสะสมรายวันปรับแก้ความถูกต้อง (Precipitation Corrected) ในหน่วย มม./วัน ($mm/day$)
  * `community=AG`: ชุมชนเกษตรกรรม (Agroclimatology)
  * `longitude` & `latitude`: พิกัดจุดกึ่งกลางของลุ่มน้ำย่อย (HydroBASINS)
  * `start` & `end`: ช่วงวันที่ในรูปแบบ `YYYYMMDD` (เช่น `19810101` ถึง `20261015`)
  * `format=JSON`: ส่งกลับเป็นโครงสร้างข้อมูล JSON
* ⚠️ **ข้อจำกัดและจุดที่ต้องระวัง (Gotchas)**:
  1. **ขนาดกริดความละเอียด 0.5 องศา (~50 กม.)**: ฝนที่ได้เป็นค่าเฉลี่ยระดับกริดกว้าง จึงอาจไม่สะท้อนยอดฝนตกหนักเฉพาะจุดในหุบเขาแคบ ๆ ได้เท่าเรดาร์ตรวจอากาศ แต่มีความสม่ำเสมอทางสถิติสูงมาก เหมาะสำหรับการคำนวณรอบปีการเกิดซ้ำ (Return Period) 46 ปี
  2. **ค่าข้อมูลสูญหาย (Missing Value Flag)**: วันที่ไม่มีข้อมูลระบบจะส่งค่า `-999.0` ต้องเขียนฟังก์ชันกรองทิ้งก่อนนำไปหาค่าเฉลี่ยหรือสถิติสะสม

---

## 4. Copernicus Data Space Ecosystem (CDSE / Sentinel-1 & 2)

สหภาพยุโรปและ ESA ให้บริการคลังข้อมูลดาวเทียมสังเกตการณ์โลก Copernicus ผ่านระบบ CDSE ใหม่ (ทดแทนระบบ SciHub เดิม)

* **พอร์ทัลหลัก**: `https://dataspace.copernicus.eu/`
* **ระบบสืบค้นข้อมูล (OData API)**: `https://catalogue.dataspace.copernicus.eu/odata/v1/Products`
* **ระบบดาวน์โหลดตรงผ่าน S3 (Direct S3 Access)**: `eodata.dataspace.copernicus.eu`
* **ที่เก็บข้อมูลในโปรเจกต์**: [`data/13_sentinel1_copernicus/`](file:///e:/theera/code/flood/data/13_sentinel1_copernicus/) และ `data/22_goal6_network/raw/s1_2026/`
* **สคริปต์หลักที่เรียกใช้**: `analysis/goal6_s1_download.py`, `analysis/goal6_s1_queue.py`
* **ผลิตภัณฑ์ที่ใช้งานในโปรเจกต์**:
  1. **Sentinel-1 GRDH (IW)**: ภาพเรดาร์ SAR มองทะลุเมฆฝนและกลางคืน โหมดโพลาไรเซชัน VV/VH ขนาดพิกเซล 10 เมตร ใช้ตรวจจับน้ำท่วมใหม่เข้มงวด
  2. **Sentinel-2 MSI Level-2A**: ภาพถ่ายทางแสงหลายช่วงคลื่น (Optical) สะท้อนแสงผิวโลกหลังหักล้างบรรยากาศ ใช้ตรวจสอบการสอบเทียบอิสระในวันที่เมฆน้อย
* ⚠️ **ข้อจำกัดและจุดที่ต้องระวัง (Gotchas)**:
  1. **นโยบายดิสก์ (Disk-Only Policy)**: ภาพถ่ายดาวเทียมดิบมีขนาด 1–2 GB ต่อฉาก (รวมทั้งโปรเจกต์กว่า 50 GB) ห้ามนำไฟล์ `.SAFE` หรือ `.zip` เข้า Git โดยเด็ดขาด ให้เก็บเฉพาะไฟล์อนุพันธ์ (Derived) และบันทึกค่าแฮช SHA-256 ใน `_hashes.txt` เท่านั้น
  2. **รอบการโคจร (Revisit Time)**: ดาวเทียม Sentinel-1 มีรอบบันทึกภาพซ้ำทุก 6 หรือ 12 วัน จึงต้องวางแผนการจับภาพให้สอดคล้องกับวันน้ำหลากสูงสุดของแต่ละลุ่มน้ำ
