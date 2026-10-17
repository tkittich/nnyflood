#!/usr/bin/env python3
"""analysis/common_fetch_weather_forecasts.py — ดึงข้อมูลพยากรณ์อากาศและน้ำท่า ECMWF IFS และ GloFAS

คำถามวิจัยสำหรับเสาที่ 1, 2, และ 3:
1. ปริมาณฝนคาดการณ์ 16 วันข้างหน้าตามแบบจำลอง ECMWF IFS ในพื้นที่ลุ่มน้ำนครนายกและลุ่มน้ำข้างเคียงเป็นอย่างไร?
2. แนวโน้มอัตราการไหลของน้ำท่า (River Discharge m³/s) รายวัน 16 วันข้างหน้าจากแบบจำลองระดับโลก GloFAS คาดการณ์น้ำหลากระลอกถัดไปหรือไม่?
3. สถิติอัตราการไหลของน้ำท่าจำลองย้อนหลัง 17 ปี (2553–2569) มีความสอดคล้องกับเหตุการณ์น้ำท่วมใหญ่ 2554, 2564, 2565 และ 2569 อย่างไร?

แหล่งข้อมูล:
- ECMWF IFS Weather Forecast: https://api.open-meteo.com/v1/forecast
- GloFAS Global Flood Awareness System: https://flood-api.open-meteo.com/v1/flood
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "27_weather_flood_forecasts" / "raw"
MANIFEST_FILE = ROOT / "data" / "27_weather_flood_forecasts" / "manifest.md"
HASHES_FILE = ROOT / "data" / "27_weather_flood_forecasts" / "_hashes.txt"

KEY_BASINS = {
    "nakhon_nayok": {"name_th": "นครนายก", "lat": 14.20, "lon": 101.21, "desc": "สถานีหลักลุ่มน้ำนครนายก"},
    "bang_pakong": {"name_th": "บางปะกง_ฉะเชิงเทรา", "lat": 13.69, "lon": 101.07, "desc": "จุดรับน้ำรวมแม่น้ำบางปะกง"},
    "pasak_saraburi": {"name_th": "ป่าสัก_สระบุรี", "lat": 14.53, "lon": 100.91, "desc": "ท้ายเขื่อนป่าสักชลสิทธิ์"},
    "chao_phraya_ayutthaya": {"name_th": "เจ้าพระยา_อยุธยา", "lat": 14.35, "lon": 100.57, "desc": "จุดบรรจบแม่น้ำป่าสักและเจ้าพระยา"},
    "chao_phraya_c2": {"name_th": "เจ้าพระยา_นครสวรรค์_C2", "lat": 15.67, "lon": 100.12, "desc": "สถานีวัดน้ำหลักตอนบน C.2"},
    "tha_chin": {"name_th": "ท่าจีน_สุพรรณบุรี", "lat": 14.47, "lon": 100.12, "desc": "ลุ่มน้ำท่าจีนตอนกลาง"},
    "mae_klong": {"name_th": "แม่กลอง_กาญจนบุรี", "lat": 14.02, "lon": 99.53, "desc": "ลุ่มน้ำแม่กลองตอนล่าง"},
}


def fetch_json(url: str, retries: int = 3, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (nnyflood-forecast; contact: project)"})
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
    
    # 1. พยากรณ์อากาศ ECMWF IFS ล่วงหน้า 16 วัน รายชั่วโมง
    print("1. กำลังดึงข้อมูลพยากรณ์อากาศ ECMWF IFS ล่วงหน้า 16 วัน...")
    weather_fc = {}
    for basin_key, meta in KEY_BASINS.items():
        lat, lon = meta["lat"], meta["lon"]
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"hourly=precipitation,rain,wind_speed_10m,wind_direction_10m,surface_pressure,cloud_cover&"
            f"forecast_days=16&timezone=Asia%2FBangkok"
        )
        try:
            res = fetch_json(url)
            weather_fc[basin_key] = {"meta": meta, "hourly": res.get("hourly", {})}
            print(f"  - {meta['name_th']}: ได้พยากรณ์รายชั่วโมง {len(res.get('hourly', {}).get('time', []))} ชั่วโมง")
        except Exception as e:
            print(f"  - {meta['name_th']}: เกิดข้อผิดพลาด {e}")
        time.sleep(0.1)

    f_weather = OUT_DIR / "ecmwf_weather_forecast_16d.json"
    f_weather.write_text(json.dumps(weather_fc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกพยากรณ์อากาศ: {f_weather} ({f_weather.stat().st_size:,} bytes)")

    # 2. พยากรณ์น้ำท่าแบบกลุ่ม (GloFAS Ensemble) ล่วงหน้า 16 วัน
    print("\n2. กำลังดึงแบบจำลองน้ำท่า GloFAS คาดการณ์น้ำหลาก 16 วัน...")
    glofas_fc = {}
    for basin_key, meta in KEY_BASINS.items():
        lat, lon = meta["lat"], meta["lon"]
        url = (
            f"https://flood-api.open-meteo.com/v1/flood?"
            f"latitude={lat}&longitude={lon}&"
            f"daily=river_discharge,river_discharge_mean,river_discharge_median,river_discharge_max,river_discharge_min,river_discharge_p25,river_discharge_p75&"
            f"forecast_days=16"
        )
        try:
            res = fetch_json(url)
            glofas_fc[basin_key] = {"meta": meta, "daily": res.get("daily", {})}
            daily_times = res.get("daily", {}).get("time", [])
            print(f"  - {meta['name_th']}: ได้พยากรณ์น้ำท่า {len(daily_times)} วัน")
        except Exception as e:
            print(f"  - {meta['name_th']}: เกิดข้อผิดพลาด {e}")
        time.sleep(0.1)

    f_glofas = OUT_DIR / "glofas_ensemble_forecast_16d.json"
    f_glofas.write_text(json.dumps(glofas_fc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกพยากรณ์น้ำท่า: {f_glofas} ({f_glofas.stat().st_size:,} bytes)")

    # 3. อนุกรมเวลาย้อนหลัง 17 ปี (2553–2569) ของน้ำท่า GloFAS
    print("\n3. กำลังดึงประวัติน้ำท่าย้อนหลัง 17 ปี (2553–2569) จาก GloFAS...")
    glofas_hist = {}
    for basin_key, meta in KEY_BASINS.items():
        lat, lon = meta["lat"], meta["lon"]
        url = (
            f"https://flood-api.open-meteo.com/v1/flood?"
            f"latitude={lat}&longitude={lon}&"
            f"daily=river_discharge&start_date=2010-01-01&end_date=2026-10-17"
        )
        try:
            res = fetch_json(url)
            times = res.get("daily", {}).get("time", [])
            q_vals = res.get("daily", {}).get("river_discharge", [])
            valid_pts = [v for v in q_vals if v is not None]
            glofas_hist[basin_key] = {
                "meta": meta,
                "days_count": len(times),
                "valid_count": len(valid_pts),
                "max_discharge_m3s": max(valid_pts) if valid_pts else None,
                "times": times,
                "river_discharge": q_vals
            }
            print(f"  - {meta['name_th']}: ได้ข้อมูล {len(valid_pts)} วัน (สูงสุด {max(valid_pts) if valid_pts else 0} m³/s)")
        except Exception as e:
            print(f"  - {meta['name_th']}: เกิดข้อผิดพลาด {e}")
        time.sleep(0.2)

    f_hist = OUT_DIR / "glofas_historical_discharge_2010_2026.json"
    f_hist.write_text(json.dumps(glofas_hist, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกประวัติน้ำท่าย้อนหลัง: {f_hist} ({f_hist.stat().st_size:,} bytes)")

    # 4. ตารางสรุปภาพรวม
    summary = {
        "metadata": {
            "source": "Copernicus GloFAS & ECMWF IFS (via Open-Meteo API)",
            "retrieval_datetime": "2026-10-17 12:00:00+07:00",
            "basins_covered": len(KEY_BASINS),
            "historical_period": "2010-01-01 ถึง 2026-10-17 (6,134 วัน)",
            "forecast_period": "16 วันล่วงหน้า (รายชั่วโมงสำหรับอากาศ, รายวันกลุ่มสำหรับน้ำท่า)"
        },
        "basins": {k: {"name": v["name_th"], "lat": v["lat"], "lon": v["lon"]} for k, v in KEY_BASINS.items()}
    }
    f_sum = OUT_DIR / "weather_flood_forecast_summary.json"
    f_sum.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    update_hashes()
    write_manifest()


def write_manifest():
    content = """# ข้อมูลพยากรณ์อากาศและน้ำท่า ECMWF IFS และ Copernicus GloFAS

> แหล่งที่มา: แบบจำลองสภาพอากาศ ECMWF IFS และแบบจำลองน้ำหลากโลก Copernicus Emergency Management Service (GloFAS) ผ่าน Open-Meteo API  
> วันที่ดึงข้อมูล: 17 ตุลาคม 2569  
> วิธีการ: ดึงอัตโนมัติผ่าน REST API (`forecast` และ `flood`)  
> สคริปต์ดึง: `analysis/common_fetch_weather_forecasts.py`

## วัตถุประสงค์และการนำไปใช้
1. พยากรณ์ฝนรายชั่วโมงและลมผิวพื้นล่วงหน้า 16 วัน (ECMWF IFS) ในพื้นที่เสี่ยงน้ำท่วม 7 ลุ่มน้ำสำคัญ
2. ประเมินความเสี่ยงน้ำหลากด้วยแบบจำลองกลุ่ม (Ensemble River Discharge Forecast) 16 วันจาก GloFAS
3. สร้างเส้นฐานอัตราการไหลของน้ำท่า (River Discharge Baseline) ต่อเนื่อง 17 ปี (2553–2569) เพื่อเปรียบเทียบระดับความรุนแรงของมวลน้ำหลากปี 2554, 2564, 2565 และ 2569

## รายการไฟล์ในโฟลเดอร์ raw/
- `ecmwf_weather_forecast_16d.json`: ข้อมูลพยากรณ์อากาศรายชั่วโมง 16 วัน (ฝน, ลม, ความกดอากาศ, เมฆ) ทั้ง 7 ลุ่มน้ำ
- `glofas_ensemble_forecast_16d.json`: ข้อมูลพยากรณ์น้ำท่ากลุ่ม 16 วัน (ค่าเฉลี่ย, มัธยฐาน, ต่ำสุด, สูงสุด, เปอร์เซ็นไทล์ 25 และ 75)
- `glofas_historical_discharge_2010_2026.json`: อนุกรมเวลาประวัติน้ำท่ารายวัน 6,134 วัน (17 ปี) ทั้ง 7 ลุ่มน้ำ
- `weather_flood_forecast_summary.json`: เมทาดาตาสรุปและพิกัดสถานีอ้างอิง

ค่าแฮชตรวจสอบความสมบูรณ์อยู่ใน `_hashes.txt` (SHA-256)
"""
    MANIFEST_FILE.write_text(content, encoding="utf-8")
    print(f"บันทึก Manifest: {MANIFEST_FILE}")


if __name__ == "__main__":
    run()
