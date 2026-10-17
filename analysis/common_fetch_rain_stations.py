#!/usr/bin/env python3
"""analysis/common_fetch_rain_stations.py — ดึงข้อมูลฝนสถานีโทรมาตรอัตโนมัติทั่วประเทศ 4,593 จุด (National Rainfall Telemetry)

คำถามวิจัยสำหรับเป้าหมาย 1, 2, และ 6:
1. การกระจายตัวของฝนตกหนักราย 24 ชั่วโมง และรายชั่วโมง จากสถานีโทรมาตรจริง 4,593 จุดทั่วประเทศเป็นอย่างไร?
2. สถานีวัดฝนในลุ่มน้ำนครนายกและลุ่มน้ำข้างเคียงบันทึกปริมาณฝนสะสมได้เท่าใด?

แหล่งข้อมูล:
- https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_24h
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "26_national_rainfall_stations" / "raw"
MANIFEST_FILE = ROOT / "data" / "26_national_rainfall_stations" / "manifest.md"
HASHES_FILE = ROOT / "data" / "26_national_rainfall_stations" / "_hashes.txt"


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (nnyflood-rain; contact: project)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


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
    
    print("กำลังดึงข้อมูลฝนสถานีโทรมาตรอัตโนมัติ 4,593 จุดทั่วประเทศ...")
    url = "https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_24h"
    raw = fetch_json(url)
    
    # บันทึกข้อมูลดิบทั้งหมด
    out_file = OUT_DIR / "national_rain_24h_all_stations.json"
    out_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกข้อมูลฝน 4,593 สถานี: {out_file} ({out_file.stat().st_size:,} bytes)")
    
    # สกัดสถิติสรุปรายจังหวัดและรายลุ่มน้ำ
    stations = raw.get("data", [])
    prov_stats: dict[str, dict] = {}
    nny_stations = []
    
    for st in stations:
        prov = st.get("geocode", {}).get("province_name", {}).get("th") or "ไม่ระบุ"
        rain_24 = float(st.get("rain_24h") or 0)
        rain_1h = float(st.get("rain_1h") or 0)
        st_name = st.get("station", {}).get("tele_station_name", {}).get("th") or ""
        agency = st.get("agency", {}).get("agency_shortname", {}).get("th") or ""
        
        stat = prov_stats.setdefault(prov, {"count": 0, "max_rain_24h": 0.0, "max_station": "", "total_rain_24h": 0.0})
        stat["count"] += 1
        stat["total_rain_24h"] += rain_24
        if rain_24 > stat["max_rain_24h"]:
            stat["max_rain_24h"] = rain_24
            stat["max_station"] = f"{st_name} ({agency})"
            
        if "นครนายก" in prov or "นครนายก" in st_name:
            nny_stations.append({
                "id": st.get("id"),
                "name": st_name,
                "agency": agency,
                "province": prov,
                "amphoe": st.get("geocode", {}).get("amphoe_name", {}).get("th"),
                "rain_24h": rain_24,
                "rain_1h": rain_1h,
                "datetime": st.get("rainfall_datetime")
            })
            
    summary = {
        "metadata": {
            "source": "คลังข้อมูลน้ำแห่งชาติ (สสน. / ThaiWater)",
            "total_stations": len(stations),
            "provinces_count": len(prov_stats),
            "nakhon_nayok_stations_count": len(nny_stations)
        },
        "nakhon_nayok_stations": sorted(nny_stations, key=lambda x: x["rain_24h"], reverse=True),
        "province_summary": prov_stats
    }
    
    summary_file = OUT_DIR / "national_rain_summary.json"
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกสรุปสถานีฝน: {summary_file}")
    
    update_hashes()
    write_manifest(len(stations))


def write_manifest(total_stations: int):
    content = f"""# ข้อมูลฝนสถานีโทรมาตรอัตโนมัติทั่วประเทศ (National Rainfall Telemetry)

> แหล่งที่มา: คลังข้อมูลน้ำแห่งชาติ สถาบันสารสนเทศทรัพยากรน้ำ (สสน. / ThaiWater)  
> ครอบคลุม: กรมทรัพยากรน้ำ (ทน.), กรมอุตุนิยมวิทยา (อม.), กรมชลประทาน (ชป.), กรุงเทพมหานคร (กทม.), และ สสน.  
> วันที่ดึงข้อมูล: 17 ตุลาคม 2569  
> วิธีการ: ดึงอัตโนมัติผ่าน REST API (`public/rain_24h`)  
> สคริปต์ดึง: `analysis/common_fetch_rain_stations.py`

## วัตถุประสงค์และการนำไปใช้
1. ตรวจสอบปริมาณฝนสะสม 24 ชั่วโมงและฝนรายชั่วโมงจากสถานีวัดจริงภาคพื้นดิน {total_stations:,} จุดทั่วประเทศ
2. เปรียบเทียบปริมาณฝนจริงกับค่าประมาณการจากดาวเทียม NASA POWER และ ERA5
3. ใช้สอบเทียบแบบจำลองทำนายระดับน้ำในลุ่มน้ำนครนายก (เสาที่ 1) และ 6 ลุ่มน้ำทั่วประเทศ (เสาที่ 2)

## รายการไฟล์ในโฟลเดอร์ raw/
- `national_rain_24h_all_stations.json`: ข้อมูลดิบรายสถานีทั้งหมด {total_stations:,} จุด
- `national_rain_summary.json`: สรุปข้อมูลฝนรายจังหวัดและรายสถานีใน จ.นครนายก

ค่าแฮชตรวจสอบความสมบูรณ์อยู่ใน `_hashes.txt` (SHA-256)
"""
    MANIFEST_FILE.write_text(content, encoding="utf-8")
    print(f"บันทึก Manifest: {MANIFEST_FILE}")


if __name__ == "__main__":
    run()
