# คู่มือสถาปัตยกรรมและการเรียกใช้ API คลังข้อมูลน้ำแห่งชาติ (ThaiWater & Khun Dan Telemetry Guide)

> สถานะ: สร้าง 17 ต.ค. 2569 — บันทึกเชิงเทคนิคเพื่อการบำรุงรักษาและการสืบค้นอัตโนมัติ  
> ครอบคลุม: ระบบ API ของคลังข้อมูลน้ำแห่งชาติ (สสน. / ThaiWater) และระบบโทรมาตรเขื่อนขุนด่านปราการชล (กรมชลประทาน)

---

## 1. ภาพรวมสถาปัตยกรรม (System Overview)

คลังข้อมูลน้ำแห่งชาติ (National Hydroinformatics Data Center) ดำเนินการโดยสถาบันสารสนเทศทรัพยากรน้ำ (องค์การมหาชน) หรือ สสน. (HII) รวบรวมข้อมูลโทรมาตรจากหลายหน่วยงาน (กรมชลประทาน, กรมอุตุนิยมวิทยา, การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย, กรุงเทพมหานคร ฯลฯ) เข้าสู่ระบบศูนย์กลาง

* **พอร์ทัลหลัก**: `https://www.thaiwater.net/` (เว็บแอปพลิเคชันแบบหน้าเดียว — Single Page Application / SPA)
* **Base URL สำหรับ API**: `https://api-v3.thaiwater.net/api/v1/thaiwater30/`
* **การพิสูจน์ตัวตน (Authentication)**: **ไม่ต้องใช้คีย์หรือโทเคน (Public GET)** สำหรับ Endpoint ที่ใช้แสดงผลหน้าเว็บ
* **ที่เก็บข้อมูลในโปรเจกต์**: [`data/02_thaiwater/`](file:///e:/theera/code/flood/data/02_thaiwater/) และ [`data/20_multistation_levels/`](file:///e:/theera/code/flood/data/20_multistation_levels/)
* **สคริปต์หลักที่เรียกใช้**: [`analysis/fetch_multistation_levels.py`](file:///e:/theera/code/flood/analysis/fetch_multistation_levels.py), [`analysis/goal6_dam_history_all.py`](file:///e:/theera/code/flood/analysis/goal6_dam_history_all.py), [`analysis/goal6_dam_inflow.py`](file:///e:/theera/code/flood/analysis/goal6_dam_inflow.py)

---

## 2. สารบัญ Endpoint สำคัญของ ThaiWater API

### 2.1 ข้อมูลเขื่อนขนาดใหญ่รายวันและเส้นกำกับระดับน้ำ (`analyst/dam_yearly_graph`)

* **URL**: `https://api-v3.thaiwater.net/api/v1/thaiwater30/analyst/dam_yearly_graph`
* **วิธีส่งคำขอ**: `HTTP GET`
* **พารามิเตอร์สำคัญ**:
  * `dam_id`: รหัสประจำเขื่อน (เช่น `32` = เขื่อนขุนด่านปราการชล, `1` = เขื่อนภูมิพล, `2` = เขื่อนสิริกิติ์, `4` = เขื่อนป่าสักชลสิทธิ์)
  * `year`: ปี ค.ศ. 4 หลัก (เช่น `2026`)
  * `data_type`: ชนิดข้อมูลที่ต้องการ:
    * `dam_storage`: ปริมาตรน้ำกักเก็บรายวัน (ล้าน ลบ.ม.)
    * `dam_inflow`: ปริมาณน้ำไหลลงอ่างรายวัน (ล้าน ลบ.ม./วัน)
    * `dam_released`: ปริมาณน้ำระบายรายวัน (ล้าน ลบ.ม./วัน)
    * `dam_spilled`: น้ำล้นทางระบายน้ำฉุกเฉิน (Spillway)
    * `dam_level`: ระดับน้ำหน้าเขื่อน (ม.รทก.)
* **โครงสร้างการตอบกลับ (Response Structure)**:
  ```json
  {
    "result": "OK",
    "data": {
      "dam_name": "เขื่อนขุนด่านปราการชล",
      "capacity": 224.0,
      "upper_rule_curve": [
        {"dam_date": "2020-01-01", "dam_storage": 120.5},
        ...
      ],
      "lower_rule_curve": [ ... ],
      "graph_data": [
        {"dam_date": "2026-09-27", "dam_storage": 224.5}
      ]
    }
  }
  ```
* ⚠️ **ข้อจำกัดและจุดที่ต้องระวัง (Gotchas)**:
  1. **ปีของเส้นกำกับระดับน้ำ (Rule Curve Template)**: อาร์เรย์ `upper_rule_curve` และ `lower_rule_curve` จะส่งวันที่ลงท้ายเป็นปี `2020` เสมอ (เช่น `2020-09-27`) การเปรียบเทียบระดับน้ำของปีปัจจุบันกับเส้นกำกับต้องตัดเทียบเฉพาะ "เดือน-วัน" (`%m-%d`) เท่านั้น
  2. **ความลึกของประวัติไม่เท่ากัน**: เขื่อนขุนด่านฯ เริ่มมีข้อมูลในปี 2013 เป็นต้นมา ขณะที่เขื่อนภูมิพลและเขื่อนสิริกิติ์ย้อนหลังได้ถึงปี 1964
  3. **โครงสร้างซ้อนชั้นในบางเขื่อน**: เขื่อนบางแห่งข้อมูลอยู่ใน `graph_data[0]['data'][i]['value']` ซ้อนลงไปอีกหนึ่งชั้น ต้องเขียนตัวถอดรหัสแบบยืดหยุ่น

---

### 2.2 โทรมาตรระดับน้ำแม่น้ำรายชั่วโมง (`public/waterlevel_graph`)

* **URL**: `https://api-v3.thaiwater.net/api/v1/thaiwater30/public/waterlevel_graph`
* **วิธีส่งคำขอ**: `HTTP GET`
* **พารามิเตอร์สำคัญ**:
  * `station_type`: บังคับใส่ `tele_waterlevel`
  * `station_id`: รหัสสถานีตัวเลข (เช่น `505003` = Ny.7 สะพานหน้าจวนผู้ว่าฯ, `2687` = Ny.1B บ้านเขานางบวช, `422002` = C.2 นครสวรรค์)
  * `start_date`: วันเริ่มต้นรูปแบบ `YYYY-MM-DD`
  * `end_date`: วันสิ้นสุดรูปแบบ `YYYY-MM-DD`
* **ข้อมูลที่ได้รับ**:
  * อนุกรมเวลาระดับน้ำรายชั่วโมง (`waterlevel_m` หรือ `waterlevel_msl`)
  * อัตราการไหลของน้ำ (`flow_rate` ในหน่วย ลบ.ม./วินาที)
  * ระดับเตือนภัยและระดับตลิ่ง (`warning_level`, `critical_level`, `bank_level`)
* ⚠️ **ข้อจำกัดและจุดที่ต้องระวัง (Gotchas)**:
  1. **ต้องใช้รหัสตัวเลข**: ระบบไม่รับรหัสตัวอักษรเดิม (เช่น `Ny.7` หรือ `C.2`) ต้องแปลงเป็นรหัสตัวเลขประจำระบบก่อนเสมอ (ตรวจสอบได้จาก `data/02_thaiwater/raw/station_all.json`)
  2. **สถานีรหัสเก่าบางจุดคืนค่าว่าง**: รหัสที่ขึ้นต้นด้วย `TNy` เช่น `TNy9`, `TNy10` คืนค่า null ทั้งหมด ให้ใช้รหัสสถานีหลักของกรมชลประทานแทน
  3. **การดึงย้อนหลังระยะยาว**: หากดึงย้อนหลังเกิน 2 ปีที่ไม่มีข้อมูล ระบบจะคืนอาร์เรย์ว่าง ให้หยุดการสืบค้นย้อนหลังเมื่อพบค่าว่างต่อเนื่อง 2 ปี

---

### 2.3 ปริมาณน้ำฝนรายวันรายสถานี (`provinces/rain3d_graph`)

* **URL**: `https://api-v3.thaiwater.net/api/v1/thaiwater30/provinces/rain3d_graph`
* **วิธีส่งคำขอ**: `HTTP GET`
* **พารามิเตอร์สำคัญ**:
  * `station_id`: รหัสสถานีวัดฝน (เช่น `455218`, `855504`)
  * `start_date`: วันเริ่มต้น
  * `end_date`: วันสิ้นสุด
* ⚠️ **ข้อจำกัดสำคัญ (Strict 31-day Chunking Limit)**:
  * ระบบจำกัดช่วงเวลาการขอได้ **ไม่เกิน 31 วันต่อครั้ง** หากช่วงกว้างกว่านั้น เซิร์ฟเวอร์จะตัดข้อมูลหรือส่งข้อผิดพลาด สคริปต์ดึงข้อมูลต้องแบ่งช่วงเป็นก้อนย่อย (Chunks) ละ 30 วันเสมอ (ดูตัวอย่างใน `data/02_thaiwater/raw/rain_chunks/`)

---

### 2.4 อาคารบังคับน้ำและประตูระบายน้ำทั่วประเทศ (`public/watergate_load` & `public/watergate_graph`)

* **URL**:
  * รายการและสถานะรวม: `.../public/watergate_load`
  * อนุกรมเวลาย้อนหลัง: `.../public/watergate_graph`
* **ขอบเขตข้อมูล**: ครอบคลุมประตูระบายน้ำ (ปตร.) และสถานีสูบน้ำ **2,315 แห่ง ใน 24 ลุ่มน้ำทั่วประเทศ**
* **ความละเอียด**: อนุกรมเวลาราย 10 นาที (ระดับน้ำเหนือน้ำ, ท้ายน้ำ, และอัตราการระบาย)
* ⚠️ **ข้อจำกัด**: สถานะการเปิด-ปิดบานประตูรายชั่วโมงแบบละเอียดมักไม่มีใน API ต้องยื่นขอผ่าน พ.ร.บ. ข้อมูลข่าวสาร (FOI)

---

### 2.5 ทะเบียนสถานีโทรมาตรทั่วประเทศ (`frontend/shared/station_all`)

* **URL**: `https://api-v3.thaiwater.net/api/v1/thaiwater30/frontend/shared/station_all`
* **ข้อมูลที่ได้**: พิกัดละติจูด-ลองจิจูด, รหัสสถานี, ชื่อสถานีภาษาไทยและอังกฤษ, หน่วยงานเจ้าของ (RID, DWR, TMD, BMA) รวมกว่า **11,483 จุดวัด** ทั่วประเทศไทย
* **ไฟล์แคชในระบบ**: [`data/02_thaiwater/raw/station_all.json`](file:///e:/theera/code/flood/data/02_thaiwater/raw/station_all.json)

---

## 3. ระบบโทรมาตรเขื่อนขุนด่านปราการชล (Khun Dan Project Telemetry)

กรมชลประทานมีระบบโทรมาตรท้องถิ่นเฉพาะลุ่มน้ำนครนายก ซึ่งติดตั้งก่อนและระหว่างการก่อสร้างเขื่อนขุนด่านฯ ให้ข้อมูลระดับน้ำที่มีความละเอียดสูงถึง **15 นาที**

* **URL**: `http://khundan-tele.rid.go.th/station_detail.php`
* **วิธีส่งคำขอ**: `HTTP POST` (`Content-Type: application/x-www-form-urlencoded`)
* **พารามิเตอร์ Body**:
  * `n_id`: รหัสจุดวัดภายในระบบ (1–19)
  * `date_from`: วันที่เริ่มต้น (รูปแบบ `DD/MM/YYYY` เช่น `26/09/2569` หรือ ค.ศ. ตามคอนฟิก)
  * `date_to`: วันที่สิ้นสุด
* **สถานีสำคัญในลุ่มน้ำนครนายก**:
  * `n_id = 61`: สถานี Ny.1B (บ้านเขานางบวช — จุดควบคุมหลักก่อนเข้าเมือง)
  * `n_id = 62`: สถานี Ny.7 (สะพานหน้าจวนผู้ว่าฯ — กลางเมืองนครนายก จุดวัดระดับน้ำวิกฤต)
  * `n_id = 63`: ท้ายน้ำประตูระบายน้ำท่าช้าง (จุดระบายน้ำออกสู่แม่น้ำบางปะกง)
* **สคริปต์ใช้งาน**: [`analysis/fetch_multistation_levels.py`](file:///e:/theera/code/flood/analysis/fetch_multistation_levels.py)
* ⚠️ **ข้อควรระวังของระบบนี้**:
  1. การดึงช่วงเวลายาวเกินไปอาจทำให้เกิด Connection Timeout แนะนำให้ส่งคำขอเป็นก้อนย่อยครั้งละ 5–7 วัน
  2. ข้อมูลตาราง HTML ส่งผลลัพธ์เรียงจากเวลา "ใหม่ไปหาเก่า" ต้องกลับลำดับเวลา (Reverse) ก่อนนำไปใช้
  3. สถานี 69 และ 74 มีการส่งค่าว่างเป็นประจำ ขณะที่สถานี 80 มีประวัติส่งค่า 0.00 ค้าง ต้องกรองทิ้งในขั้นตอนเตรียมข้อมูล

---

## 4. ตัวอย่างคำสั่งและการเขียนโค้ดเรียกใช้งาน (Code Recipe)

```python
import urllib.request
import json

# ดึงข้อมูลรายวันเขื่อนขุนด่านฯ (dam_id=32) ประจำปี 2026
url = "https://api-v3.thaiwater.net/api/v1/thaiwater30/analyst/dam_yearly_graph?dam_id=32&data_type=dam_storage&year=2026"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (nnyflood-research)"})

with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    storage_series = data["data"]["graph_data"]
    print(f"ดึงข้อมูลเขื่อนขุนด่านฯ ได้ {len(storage_series)} วัน")
```
