#!/usr/bin/env python3
"""analysis/common_fetch_gulf_marine.py — ดึงข้อมูลคลื่น ความลึก และพยากรณ์น้ำทะเลอ่าวไทย (Gulf Marine & Wave Forecast)

คำถามวิจัยสำหรับเป้าหมาย 6 และ 7:
1. ความสูงคลื่นนัยสำคัญ (Significant Wave Height) และความลึกน้ำทะเล (Sea Depth) รอบอ่าวไทย 31 สถานีเป็นอย่างไร?
2. สภาพน้ำทะเลหนุนและคลื่นลมบริเวณปากแม่น้ำสายหลัก (เจ้าพระยา, ท่าจีน, แม่กลอง, บางปะกง) เป็นอุปสรรคต่อการระบายน้ำหลากหรือไม่?

แหล่งข้อมูล:
- https://api-v3.thaiwater.net/api/v1/thaiwater30/public/wave_forecast
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "25_gulf_marine_tides" / "raw"
MANIFEST_FILE = ROOT / "data" / "25_gulf_marine_tides" / "manifest.md"
HASHES_FILE = ROOT / "data" / "25_gulf_marine_tides" / "_hashes.txt"


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (nnyflood-marine; contact: project)"})
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
    
    print("กำลังดึงข้อมูลแบบจำลองคลื่นและความสูงน้ำทะเลอ่าวไทย 31 สถานี...")
    url = "https://api-v3.thaiwater.net/api/v1/thaiwater30/public/wave_forecast"
    raw = fetch_json(url)
    
    # บันทึกข้อมูลดิบทั้งหมด
    out_file = OUT_DIR / "gulf_wave_forecast_31_stations.json"
    out_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกข้อมูลคลื่น 31 สถานี: {out_file} ({out_file.stat().st_size:,} bytes)")
    
    # สกัดสถิติสรุปตามปากแม่น้ำสำคัญ
    data_list = raw.get("data", [])
    summary_stations = []
    for item in data_list:
        st = item.get("station", {})
        fc_list = item.get("wave_forecast_data", [])
        if fc_list:
            latest = fc_list[0]
            summary_stations.append({
                "id": st.get("id"),
                "name_th": st.get("swan_name", {}).get("th"),
                "name_en": st.get("swan_name", {}).get("en"),
                "lat": st.get("swan_lat"),
                "lon": st.get("swan_long"),
                "latest_datetime": latest.get("swan_datetime"),
                "sea_depth_m": latest.get("swan_depth"),
                "wave_height_sig_m": latest.get("swan_highsig"),
                "wave_direction_deg": latest.get("swan_direction"),
                "wave_period_sec": latest.get("swan_period"),
                "forecast_points_count": len(fc_list)
            })
            
    summary_file = OUT_DIR / "gulf_wave_summary.json"
    summary_file.write_text(json.dumps(summary_stations, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกสรุป 31 สถานี: {summary_file}")
    
    update_hashes()
    write_manifest(len(summary_stations))


def write_manifest(station_count: int):
    content = f"""# ข้อมูลคลื่น ความลึก และพยากรณ์น้ำทะเลอ่าวไทย (Gulf Marine & Wave Forecast)

> แหล่งที่มา: คลังข้อมูลน้ำแห่งชาติ สถาบันสารสนเทศทรัพยากรน้ำ (สสน. / ThaiWater)  
> ระบบแบบจำลอง: SWAN (Simulating Waves Nearshore)  
> วันที่ดึงข้อมูล: 17 ตุลาคม 2569  
> วิธีการ: ดึงอัตโนมัติผ่าน REST API (`public/wave_forecast`)  
> สคริปต์ดึง: `analysis/common_fetch_gulf_marine.py`

## วัตถุประสงค์และการนำไปใช้
1. ตรวจสอบความลึกน้ำทะเล (Sea Depth) และความสูงคลื่นนัยสำคัญ (Significant Wave Height) บริเวณปากอ่าวไทยตอนบน
2. วิเคราะห์อิทธิพลของคลื่นลมและระดับน้ำทะเลต่อความสามารถในการระบายน้ำหลากของแม่น้ำเจ้าพระยา, ท่าจีน, แม่กลอง, และบางปะกง
3. ใช้เป็นเงื่อนไขขอบเขตปลายน้ำ (Downstream Boundary Conditions) สำหรับแบบจำลองชลศาสตร์ Goal 6 และ Goal 7

## รายการไฟล์ในโฟลเดอร์ raw/
- `gulf_wave_forecast_31_stations.json`: ข้อมูลดิบแบบจำลองคลื่นครอบคลุม 31 สถานีรอบอ่าวไทยและอันดามัน
- `gulf_wave_summary.json`: ตารางสรุปค่าความลึกน้ำทะเลและความสูงคลื่นล่าสุดทั้ง {station_count} สถานี

ค่าแฮชตรวจสอบความสมบูรณ์อยู่ใน `_hashes.txt` (SHA-256)
"""
    MANIFEST_FILE.write_text(content, encoding="utf-8")
    print(f"บันทึก Manifest: {MANIFEST_FILE}")


if __name__ == "__main__":
    run()
