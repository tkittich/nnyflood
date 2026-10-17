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
* **การพิสูจน์ตัวตน (Authentication)**: ต้องส่ง Header `Authorization: Bearer <API_KEY>`
* **ที่เก็บข้อมูลในโปรเจกต์**: [`data/12_gistda_flood/`](file:///e:/theera/code/flood/data/12_gistda_flood/)
* **สคริปต์หลักที่เรียกใช้**: [`analysis/goal6_fetch_gistda_flood.py`](file:///e:/theera/code/flood/analysis/goal6_fetch_gistda_flood.py)
* **ชุดข้อมูลที่รองรับ**:
  1. **ขอบเขตน้ำท่วมสะสม 30 วัน (30-day Cumulative Flood)**: รูปแบบ GeoJSON แสดงพื้นที่น้ำท่วมสะสมตามรายจังหวัดและรายลุ่มน้ำ
  2. **สถิติความถี่น้ำท่วมซ้ำซาก 14 ปี (14-Year Flood Frequency)**: แสดงความถี่การเกิดน้ำท่วมย้อนหลังตั้งแต่ปี 2554 ถึงปัจจุบัน
* **ตัวอย่างการเรียกคำขอ**:
  ```python
  import urllib.request
  import json

  url = "https://api-gateway.gistda.or.th/api/2.0/resources/features/flood?province=จ.นครนายก"
  req = urllib.request.Request(url, headers={
      "Authorization": f"Bearer {api_key}",
      "Accept": "application/json"
  })
  with urllib.request.urlopen(req, timeout=60) as resp:
      geojson = json.loads(resp.read().decode("utf-8"))
  ```
* ⚠️ **ข้อจำกัดและจุดที่ต้องระวัง (Gotchas)**:
  1. การสะกดชื่อจังหวัดต้องมีคำนำหน้า เช่น `"จ.นครนายก"` หรือ `"กรุงเทพมหานคร"` (ดูตาราง `PROVINCES_MAP` ใน `goal6_fetch_gistda_flood.py`)
  2. ไฟล์ GeoJSON ที่ส่งกลับมีขนาดหลายสิบล้านไบต์ จึงถูกกำหนดเป็น disk-only ไม่นำเข้า Git (บันทึกเฉพาะตัวเลขสถิติรวมและค่าแฮช SHA-256)

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
