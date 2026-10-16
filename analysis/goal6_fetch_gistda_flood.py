#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""สคริปต์ดึงชั้นข้อมูลน้ำท่วมจาก GISTDA Disaster Platform API (2026)

การใช้งาน:
    python analysis/fetch_gistda_flood.py --areas nakhonnayok
    python analysis/fetch_gistda_flood.py --areas bma
    python analysis/fetch_gistda_flood.py --areas bangpakong
    python analysis/fetch_gistda_flood.py --areas chaophraya
    python analysis/fetch_gistda_flood.py --areas all

ผลลัพธ์:
    บันทึก GeoJSON รายจังหวัดและไฟล์รวมลงที่ data/12_gistda_flood/raw/
    (disk-only ตามนโยบาย .gitignore ไม่เข้า git)
    พร้อมคำนวณสถิติสรุปพื้นที่น้ำท่วม (ตร.กม.) รายลุ่มน้ำ
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

ROOT = Path(__file__).resolve().parent.parent
CRED_FILE = ROOT / "data/12_gistda_flood/.gistda_api.json"
OUT_DIR = ROOT / "data/12_gistda_flood/raw"
BASE_URL = "https://api-gateway.gistda.or.th/api/2.0/resources/features/flood"

PROVINCES_MAP = {
    "nakhonnayok": ["จ.นครนายก"],
    "bma": ["กรุงเทพมหานคร"],
    "bangpakong": ["จ.นครนายก", "จ.ปราจีนบุรี", "จ.ฉะเชิงเทรา", "จ.สระแก้ว"],
    "chaophraya": [
        "กรุงเทพมหานคร",
        "จ.นนทบุรี",
        "จ.ปทุมธานี",
        "จ.สมุทรปราการ",
        "จ.พระนครศรีอยุธยา",
        "จ.สระบุรี",
        "จ.ลพบุรี",
        "จ.อ่างทอง",
        "จ.สิงห์บุรี",
        "จ.ชัยนาท",
        "จ.สุพรรณบุรี",
        "จ.อุทัยธานี",
        "จ.นครสวรรค์",
    ],
}


def load_api_key() -> str:
    if not CRED_FILE.exists():
        sys.exit(
            f"!! ไม่พบไฟล์คีย์ {CRED_FILE.relative_to(ROOT)} — "
            "กรุณาสร้างไฟล์และใส่ {\"api_key\": \"...\"}"
        )
    try:
        data = json.loads(CRED_FILE.read_text(encoding="utf-8"))
        key = data.get("api_key", "").strip()
        if not key:
            sys.exit("!! ไม่พบคีย์ 'api_key' ในไฟล์การตั้งค่า")
        return key
    except Exception as e:
        sys.exit(f"!! อ่านไฟล์คีย์ล้มเหลว: {e}")


def fetch_province_flood(api_key: str, pv_tn: str, endpoint: str = "30days", limit: int = 1000, force: bool = False) -> list[dict]:
    """ดึงข้อมูล GeoJSON features ของจังหวัดที่ระบุแบบแบ่งหน้า (pagination) พร้อมระบบแคชรายจังหวัด"""
    prov_dir = OUT_DIR / "provinces"
    prov_dir.mkdir(parents=True, exist_ok=True)
    clean_pv = pv_tn.replace("จ.", "").strip()
    cache_file = prov_dir / f"{clean_pv}_{endpoint}.json"
    
    if cache_file.exists() and not force:
        print(f"  [ใช้แคชที่มีอยู่] {pv_tn} -> {cache_file.name}")
        return json.loads(cache_file.read_text(encoding="utf-8"))

    if endpoint == "flood-freq":
        url = "https://api-gateway.gistda.or.th/api/2.0/resources/features/flood-freq"
    else:
        url = f"{BASE_URL}/{endpoint}"

    offset = 0
    all_features = []
    
    print(f"กำลังดึงข้อมูล: {pv_tn} (endpoint: {endpoint})...")
    while True:
        params = {
            "api_key": api_key,
            "pv_tn": pv_tn,
            "limit": limit,
            "offset": offset,
        }
        req_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(req_url, headers={"User-Agent": "nnyflood-research/1.0"})
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  [ข้อผิดพลาด] offset={offset}: {e} — กำลังลองใหม่ใน 3 วินาที...")
            time.sleep(3)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                
        features = data.get("features", [])
        total_matched = data.get("numberMatched", 0)
        returned = data.get("numberReturned", len(features))
        
        all_features.extend(features)
        print(f"  ดึงแล้ว {len(all_features)} / {total_matched} features (offset={offset})")
        
        if returned < limit or len(all_features) >= total_matched:
            break
        offset += limit
        time.sleep(0.2)  # รักษาระดับ rate limit
        
    cache_file.write_text(json.dumps(all_features, ensure_ascii=False), encoding="utf-8")
    return all_features


def compute_stats(features: list[dict]) -> dict:
    """คำนวณสรุปสถิติน้ำท่วมจากแอตทริบิวต์ (รองรับทั้งชุดรายวัน/30วัน และชุดประวัติศาสตร์ flood-freq)"""
    total_area_sqm = 0.0
    total_rice_sqm = 0.0
    total_pop = 0
    tambons = set()
    amphoes = set()
    sat_passes = set()
    yearly_counts = {f"y_{yr}": 0 for yr in range(2011, 2025)}
    is_flood_freq = False
    
    for f in features:
        p = f.get("properties", {})
        # ตรวจว่ามีฟิลด์พื้นที่แบบใด
        if "shape_area" in p or "area_rai" in p:
            is_flood_freq = True
            area_m2 = float(p.get("shape_area") or (float(p.get("area_rai") or 0.0) * 1600.0))
        else:
            area_m2 = float(p.get("f_area") or 0.0)
            
        total_area_sqm += area_m2
        rice_area = float(p.get("rice_area") or 0.0)
        total_rice_sqm += rice_area
        total_pop += int(p.get("population") or 0)
        
        if p.get("tb_tn"):
            tambons.add(f"{p.get('pv_tn')} {p.get('tb_tn')}")
        if p.get("ap_tn"):
            amphoes.add(f"{p.get('pv_tn')} {p.get('ap_tn')}")
        if p.get("file_name"):
            for pass_name in str(p.get("file_name")).split(","):
                sat_passes.add(pass_name.strip())
                
        if is_flood_freq:
            for y_key in yearly_counts:
                if p.get(y_key):
                    yearly_counts[y_key] += 1
                
    res = {
        "features_count": len(features),
        "total_flood_sqkm": round(total_area_sqm / 1_000_000, 2),
        "total_flood_rai": round(total_area_sqm / 1600, 1),
        "total_rice_sqkm": round(total_rice_sqm / 1_000_000, 2),
        "total_population_affected": total_pop,
        "amphoes_count": len(amphoes),
        "tambons_count": len(tambons),
        "satellite_passes_count": len(sat_passes),
    }
    if is_flood_freq:
        res["historical_years"] = yearly_counts
    return res


def save_geojson(features: list[dict], out_path: Path) -> str:
    """บันทึก FeatureCollection และคืนค่า SHA-256"""
    fc = {
        "type": "FeatureCollection",
        "timeStamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "features": features,
    }
    raw_bytes = json.dumps(fc, ensure_ascii=False).encode("utf-8")
    out_path.write_bytes(raw_bytes)
    sha = hashlib.sha256(raw_bytes).hexdigest()
    return sha


def main():
    parser = argparse.ArgumentParser(description="ดาวน์โหลดชั้นข้อมูลน้ำท่วม GISTDA Disaster Platform")
    parser.add_argument(
        "--areas",
        choices=["nakhonnayok", "bma", "bangpakong", "chaophraya", "all"],
        default="nakhonnayok",
        help="พื้นที่ที่ต้องการดึง: nakhonnayok, bma, bangpakong, chaophraya, หรือ all",
    )
    parser.add_argument(
        "--endpoint",
        choices=["30days", "7days", "3days", "1day", "flood-freq"],
        default="30days",
        help="ช่วงเวลาของข้อมูล: 30days (เหตุการณ์ปัจจุบัน), flood-freq (สถิติย้อนหลัง 2011–2024)",
    )
    args = parser.parse_args()

    api_key = load_api_key()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    target_groups = []
    if args.areas == "all":
        target_groups = ["nakhonnayok", "bma", "bangpakong", "chaophraya"]
    else:
        target_groups = [args.areas]

    # รวมจังหวัดทั้งหมดที่ต้องดึงโดยไม่ดึงซ้ำ
    provinces_to_fetch = set()
    for g in target_groups:
        provinces_to_fetch.update(PROVINCES_MAP[g])

    province_features: dict[str, list[dict]] = {}
    print(f"=== เริ่มการดึงข้อมูล GISTDA Disaster Platform ({args.endpoint}) ===")
    print(f"กลุ่มเป้าหมาย: {target_groups}")
    print(f"จำนวนจังหวัดที่ต้องดึง: {len(provinces_to_fetch)} จังหวัด\n")

    for pv in sorted(provinces_to_fetch):
        feats = fetch_province_flood(api_key, pv, endpoint=args.endpoint)
        province_features[pv] = feats
        stats = compute_stats(feats)
        print(f"  -> {pv}: สำเร็จ {len(feats)} features | พื้นที่น้ำท่วม {stats['total_flood_sqkm']} ตร.กม. ({stats['total_flood_rai']:,} ไร่)\n")

    # บันทึกไฟล์รวมแยกตามลุ่มน้ำ/พื้นที่
    summary_report = {}
    hashes_to_record = []

    for group in target_groups:
        group_pvs = PROVINCES_MAP[group]
        group_features = []
        for pv in group_pvs:
            group_features.extend(province_features.get(pv, []))

        out_file = OUT_DIR / f"gistda_flood_{args.endpoint}_{group}.geojson"
        sha = save_geojson(group_features, out_file)
        stats = compute_stats(group_features)
        summary_report[group] = {
            "file": out_file.name,
            "bytes": out_file.stat().st_size,
            "sha256": sha,
            **stats,
        }
        hashes_to_record.append(f"{sha}  *{out_file.name}")
        print(f"บันทึกไฟล์กลุ่ม [{group}]: {out_file.relative_to(ROOT)} ({round(out_file.stat().st_size / 1024 / 1024, 2)} MB)")
        print(f"  สถิติ: {stats['total_flood_sqkm']} ตร.กม. | {stats['total_flood_rai']:,} ไร่ | {stats['features_count']:,} polygons\n")

    # บันทึกไฟล์สรุปผล JSON (รวมกับผลเดิมถ้ามี)
    summary_path = OUT_DIR / f"summary_{args.endpoint}.json"
    existing_summary = {}
    if summary_path.exists():
        try:
            existing_summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            existing_summary = {}
    existing_summary.update(summary_report)
    summary_path.write_text(json.dumps(existing_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกบทสรุปสถิติ: {summary_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
