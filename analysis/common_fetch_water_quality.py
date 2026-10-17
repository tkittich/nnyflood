#!/usr/bin/env python3
"""analysis/common_fetch_water_quality.py — ดึงข้อมูลคุณภาพน้ำและความเค็มปากแม่น้ำ (Estuary Salinity)

คำถามวิจัยสำหรับเสาที่ 1, 2, และ 3:
1. สภาพความเค็ม (Salinity g/L) และการนำไฟฟ้า (EC µS/cm) ที่ปากแม่น้ำ 4 สาย (บางปะกง, เจ้าพระยา, ท่าจีน, แม่กลอง)
   ในช่วงน้ำหลากและช่วงน้ำทะเลหนุนเป็นอย่างไร?
2. ลิ่มความเค็มรุกเข้าใกล้จุดสูบน้ำดิบประปานครหลวง (สถานีสำแล จ.ปทุมธานี) หรือไม่?
3. สถิติความเค็มย้อนหลัง 5–8 ปี (2561–2569) มีพฤติกรรมอย่างไร?

แหล่งข้อมูล:
- https://api-v3.thaiwater.net/api/v1/thaiwater30/analyst/waterquality_load
- https://api-v3.thaiwater.net/api/v1/thaiwater30/analyst/waterquality_compare_station_graph
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "24_estuary_waterquality" / "raw"
MANIFEST_FILE = ROOT / "data" / "24_estuary_waterquality" / "manifest.md"
HASHES_FILE = ROOT / "data" / "24_estuary_waterquality" / "_hashes.txt"

KEY_ESTUARY_STATIONS = [
    {"id": 144, "name": "สำแล_กปน", "river": "เจ้าพระยา", "prov": "ปทุมธานี"},
    {"id": 202, "name": "สำแล_คลองเชียงราก", "river": "เจ้าพระยา", "prov": "ปทุมธานี"},
    {"id": 5, "name": "สะพานพระนั่งเกล้า", "river": "เจ้าพระยา", "prov": "นนทบุรี"},
    {"id": 148, "name": "ปากน้ำสมุทรปราการ", "river": "เจ้าพระยา", "prov": "สมุทรปราการ"},
    {"id": 209, "name": "คลองลัดโพธิ์", "river": "เจ้าพระยา", "prov": "สมุทรปราการ"},
    {"id": 186, "name": "ท่าข้าม_ปากน้ำบางปะกง", "river": "บางปะกง", "prov": "ฉะเชิงเทรา"},
    {"id": 183, "name": "เมืองฉะเชิงเทรา", "river": "บางปะกง", "prov": "ฉะเชิงเทรา"},
    {"id": 184, "name": "วัดแหลมใต้", "river": "บางปะกง", "prov": "ฉะเชิงเทรา"},
    {"id": 185, "name": "บางกรูด", "river": "บางปะกง", "prov": "ฉะเชิงเทรา"},
    {"id": 175, "name": "บางแตน_จุดบรรจบ", "river": "บางปะกง", "prov": "ปราจีนบุรี"},
    {"id": 176, "name": "บ้านสร้าง", "river": "บางปะกง", "prov": "ปราจีนบุรี"},
    {"id": 182, "name": "เมืองนครนายก", "river": "นครนายก", "prov": "นครนายก"},
    {"id": 171, "name": "วัดช่องลม_ปากน้ำท่าจีน", "river": "ท่าจีน", "prov": "สมุทรสงคราม"},
    {"id": 162, "name": "กระทุ่มแบน", "river": "ท่าจีน", "prov": "สมุทรสาคร"},
    {"id": 163, "name": "นครชัยศรี", "river": "ท่าจีน", "prov": "นครปฐม"},
    {"id": 167, "name": "อัมพวา_ปากน้ำแม่กลอง", "river": "แม่กลอง", "prov": "สมุทรสงคราม"},
]


def fetch_url(url: str, retries: int = 3, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (nnyflood-waterquality; contact: project)"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(1.0)
    return {}


def update_hashes():
    if not OUT_DIR.exists():
        return
    lines = []
    for p in sorted(OUT_DIR.glob("*.json")):
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        rel = p.relative_to(ROOT).as_posix()
        lines.append(f"{h}  {rel}")
    HASHES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"บันทึกแฮช {len(lines)} รายการลง {HASHES_FILE}")


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. ดึง Snapshot คุณภาพน้ำ 112 สถานีทั่วประเทศ
    print("กำลังดึงสแนปช็อตคุณภาพน้ำ 112 สถานีทั่วประเทศ...")
    load_url = "https://api-v3.thaiwater.net/api/v1/thaiwater30/analyst/waterquality_load"
    load_data = fetch_url(load_url)
    snapshot_file = OUT_DIR / "waterquality_national_snapshot_112.json"
    snapshot_file.write_text(json.dumps(load_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกสแนปช็อต: {snapshot_file} ({snapshot_file.stat().st_size:,} bytes)")
    
    # 2. ดึงประวัติอนุกรมเวลาความเค็ม (Salinity) และการนำไฟฟ้า (EC) รายสถานี
    # ดึงช่วงเหตุการณ์ 2569 (ส.ค. - ต.ค. 2569)
    print("\nกำลังดึงอนุกรมเวลารายละเอียดช่วงน้ำหลาก 2569...")
    series_2569 = {}
    for st in KEY_ESTUARY_STATIONS:
        st_id = st["id"]
        st_name = st["name"]
        for param in ["salinity", "conductivity"]:
            q_url = (
                f"https://api-v3.thaiwater.net/api/v1/thaiwater30/analyst/waterquality_compare_station_graph?"
                f"waterquality_station_id={st_id}&param={param}&"
                f"start_datetime=2026-08-01%2000:00&end_datetime=2026-10-17%2012:00"
            )
            try:
                res = fetch_url(q_url)
                pts = [p for p in res.get("data", [{}])[0].get("data", []) if p.get("value") is not None] if res.get("data") else []
                if pts:
                    series_2569.setdefault(st_id, {"station": st, "series": {}})["series"][param] = pts
                    print(f"  [{st_id}] {st_name} ({param}): ได้ {len(pts)} จุด")
            except Exception as e:
                pass
            time.sleep(0.1)
            
    f_2569 = OUT_DIR / "estuary_salinity_sep_oct_2026.json"
    f_2569.write_text(json.dumps(series_2569, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกอนุกรมเวลา 2569: {f_2569}")

    # 3. ดึงประวัติย้อนหลังหลายปี (Multi-year Baseline 2018–2026) ของสถานีพระนั่งเกล้าและสำแล
    print("\nกำลังดึงประวัติเส้นฐานย้อนหลัง 2018–2026...")
    multi_year = {}
    for yr in range(2018, 2027):
        url_yr = (
            f"https://api-v3.thaiwater.net/api/v1/thaiwater30/analyst/waterquality_compare_station_graph?"
            f"waterquality_station_id=5&param=salinity&"
            f"start_datetime={yr}-09-01%2000:00&end_datetime={yr}-09-30%2023:59"
        )
        try:
            res = fetch_url(url_yr)
            pts = [p for p in res.get("data", [{}])[0].get("data", []) if p.get("value") is not None] if res.get("data") else []
            if pts:
                multi_year[yr] = pts
                print(f"  ปี {yr}: ได้ {len(pts)} จุด")
        except Exception as e:
            pass
        time.sleep(0.1)
        
    f_my = OUT_DIR / "phranangklao_salinity_sep_2018_2026.json"
    f_my.write_text(json.dumps(multi_year, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกประวัติเส้นฐาน: {f_my}")

    # 4. สรุป Manifest และ Hashes
    update_hashes()
    write_manifest()


def write_manifest():
    content = """# ข้อมูลคุณภาพน้ำและความเค็มปากแม่น้ำ (Estuary Salinity & Water Quality)

> แหล่งที่มา: คลังข้อมูลน้ำแห่งชาติ สถาบันสารสนเทศทรัพยากรน้ำ (สสน. / ThaiWater)  
> วันที่ดึงข้อมูล: 17 ตุลาคม 2569  
> วิธีการ: ดึงอัตโนมัติผ่าน REST API (`analyst/waterquality_load` และ `analyst/waterquality_compare_station_graph`)  
> สคริปต์ดึง: `analysis/common_fetch_water_quality.py`

## วัตถุประสงค์และการนำไปใช้
1. ตรวจสอบความเค็ม (Salinity g/L) และการนำไฟฟ้า (EC µS/cm) บริเวณปากแม่น้ำ 4 สาย (บางปะกง, เจ้าพระยา, ท่าจีน, แม่กลอง)
2. ติดตามการรุกตัวของลิ่มความเค็มเทียบกับจุดสูบน้ำดิบของการประปานครหลวง (สถานีสำแล จ.ปทุมธานี)
3. ใช้วิเคราะห์ข้อจำกัดชลศาสตร์ในการระบายน้ำจากเขื่อนตอนบนเพื่อการผลักดันน้ำเค็ม

## รายการไฟล์ในโฟลเดอร์ raw/
- `waterquality_national_snapshot_112.json`: สแนปช็อตคุณภาพน้ำ 8 พารามิเตอร์ ครอบคลุม 112 สถานีทั่วประเทศ
- `estuary_salinity_sep_oct_2026.json`: อนุกรมเวลาระดับ 10–15 นาทีช่วงระลอกน้ำหลาก 2569 ณ ปากแม่น้ำ 4 สาย
- `phranangklao_salinity_sep_2018_2026.json`: เส้นฐานความเค็มย้อนหลัง 9 ปี (2561–2569) ณ สะพานพระนั่งเกล้า แม่น้ำเจ้าพระยา

ค่าแฮชตรวจสอบความสมบูรณ์อยู่ใน `_hashes.txt` (SHA-256)
"""
    MANIFEST_FILE.write_text(content, encoding="utf-8")
    print(f"บันทึก Manifest: {MANIFEST_FILE}")


if __name__ == "__main__":
    run()
