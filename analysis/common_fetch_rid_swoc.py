#!/usr/bin/env python3
"""analysis/common_fetch_rid_swoc.py — เครื่องมือดึงข้อมูลอ่างเก็บน้ำและโทรมาตรจากระบบ SWOC / RID

แหล่งต้นทาง:
1. ระบบฐานข้อมูลน้ำในอ่างเก็บน้ำ กรมชลประทาน (https://app.rid.go.th/reservoir/)
   - เขื่อนขนาดใหญ่ 35 แห่ง (api/damsGeojson, api/dam)
   - อ่างเก็บน้ำขนาดกลาง 461 แห่ง (api/rsvmiddlesGeojson, api/rsvmiddle)
2. บริการเว็บโทรมาตรและรูปตัดลำน้ำ (https://hyd-app-db.rid.go.th/webservice/HDService.svc)
   - ข้อมูลสถานี (getStationFromStationCode)
   - หน้าตัดลำน้ำจริง (GetCrosssectionFromStationID)

ผลลัพธ์จัดเก็บที่:
- data/23_rid_swoc/raw/
"""
from __future__ import annotations

import hashlib
import json
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "23_rid_swoc" / "raw"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
    "Referer": "https://swoc.rid.go.th/",
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def fetch_url(url: str, params: dict | None = None, post_json: dict | None = None, timeout: int = 20) -> bytes:
    """ดาวน์โหลดข้อมูลผ่าน HTTP GET หรือ POST (JSON)"""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    
    headers = dict(HEADERS)
    data = None
    method = "GET"
    if post_json is not None:
        data = json.dumps(post_json).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
        method = "POST"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
        return resp.read()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch_large_dams_snapshot() -> dict:
    """ดึงสถานะเขื่อนขนาดใหญ่ 35 แห่ง ณ ปัจจุบัน"""
    url = "https://app.rid.go.th/reservoir/api/damsGeojson"
    print(f"[*] ดึง snapshot เขื่อนขนาดใหญ่ 35 แห่ง: {url}")
    raw = fetch_url(url)
    return json.loads(raw.decode("utf-8"))


def fetch_medium_dams_snapshot(date_str: str) -> dict:
    """ดึงสถานะอ่างขนาดกลาง 461 แห่ง ณ วันที่ระบุ"""
    url = "https://app.rid.go.th/reservoir/api/rsvmiddlesGeojson"
    params = {"date_start": date_str, "date_end": date_str}
    print(f"[*] ดึง snapshot อ่างขนาดกลาง 461 แห่ง ({date_str}): {url}")
    raw = fetch_url(url, params=params)
    return json.loads(raw.decode("utf-8"))


def fetch_nny_medium_dams(start_date: str, end_date: str) -> dict:
    """ดึงอนุกรมเวลาของอ่างเก็บน้ำขนาดกลาง 6 แห่งใน จ.นครนายก"""
    nny_dams = [
        {"cresv": "rsv380", "name": "อ่างเก็บน้ำห้วยปรือ", "amphoe": "เมืองนครนายก", "capacity_mcm": 8.87},
        {"cresv": "rsv381", "name": "อ่างเก็บน้ำคลองสีเสียด", "amphoe": "เมืองนครนายก", "capacity_mcm": 1.14},
        {"cresv": "rsv382", "name": "อ่างเก็บน้ำคลองโบด", "amphoe": "เมืองนครนายก", "capacity_mcm": 4.25},
        {"cresv": "rsv383", "name": "อ่างเก็บน้ำทรายทอง", "amphoe": "เมืองนครนายก", "capacity_mcm": 2.00},
        {"cresv": "rsv384", "name": "อ่างเก็บน้ำคลองวังบอน", "amphoe": "ปากพลี", "capacity_mcm": 7.60},
        {"cresv": "rsv386", "name": "อ่างเก็บน้ำคลองกลาง", "amphoe": "ปากพลี", "capacity_mcm": 3.10},
    ]

    url = "https://app.rid.go.th/reservoir/api/rsvmiddle"
    out = {
        "metadata": {
            "source": url,
            "province": "นครนายก",
            "province_code": "22",
            "date_range": [start_date, end_date],
            "total_reservoirs": len(nny_dams),
            "total_capacity_mcm": sum(d["capacity_mcm"] for d in nny_dams),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
        "reservoirs": {},
    }

    for d in nny_dams:
        cresv = d["cresv"]
        name = d["name"]
        print(f"  - ดึงข้อมูล {name} ({cresv}) ระหว่าง {start_date} ถึง {end_date}...")
        params = {"rsvmiddle": cresv, "date_start": start_date, "date_end": end_date}
        raw = fetch_url(url, params=params)
        js = json.loads(raw.decode("utf-8"))
        out["reservoirs"][cresv] = {
            "info": d,
            "data": js.get("reservoir_data", []),
            "summary": {
                "max": js.get("max"),
                "min": js.get("min"),
                "sum": js.get("sum"),
            },
        }
        time.sleep(0.3)

    return out


def fetch_dam_timeseries(dam_id: int, dam_name: str, start_date: str, end_date: str) -> dict:
    """ดึงอนุกรมเวลาเขื่อนขนาดใหญ่ (เช่น ป่าสักฯ หรือ ขุนด่านฯ)"""
    url = "https://app.rid.go.th/reservoir/api/dam"
    params = {"dam_id": dam_id, "date_start": start_date, "date_end": end_date}
    print(f"[*] ดึงอนุกรมเวลาเขื่อน {dam_name} ({dam_id}) ช่วง {start_date} ถึง {end_date}...")
    raw = fetch_url(url, params=params)
    return json.loads(raw.decode("utf-8"))


def fetch_cross_sections(station_codes: list[str]) -> dict:
    """ดึงข้อมูลสถานีและรูปตัดขวางลำน้ำจริง (Cross-Section) จาก HDService"""
    url_st = "https://hyd-app-db.rid.go.th/webservice/HDService.svc/getStationFromStationCode"
    url_cs = "https://hyd-app-db.rid.go.th/webservice/HDService.svc/GetCrosssectionFromStationID"

    out = {
        "metadata": {
            "source": "https://hyd-app-db.rid.go.th/webservice/HDService.svc",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
        "stations": {},
    }

    for code in station_codes:
        print(f"[*] ดึงข้อมูลสถานีและหน้าตัด: {code}...")
        st_info = json.loads(fetch_url(url_st, post_json={"hydro": {"StationCode": code}}).decode("utf-8"))
        if not st_info or "stationid" not in st_info:
            print(f"  [!] ไม่พบข้อมูลสถานี {code}")
            continue

        stid = st_info["stationid"]
        cs_data = json.loads(fetch_url(url_cs, post_json={"hydro": {"StationID": stid}}).decode("utf-8"))
        out["stations"][code] = {
            "station_info": st_info,
            "cross_section_points": cs_data,
        }
        time.sleep(0.3)

    return out


def fetch_nny_medium_dams_full_history(start_date: str = "2009-01-01", end_date: str = "2026-10-15") -> dict:
    """ดึงอนุกรมเวลารายวันย้อนหลังเต็ม (2009-2026) ของอ่างเก็บน้ำขนาดกลาง 6 แห่ง จ.นครนายก"""
    nny_dams = [
        {"cresv": "rsv380", "name": "อ่างเก็บน้ำห้วยปรือ", "amphoe": "เมืองนครนายก", "capacity_mcm": 8.87},
        {"cresv": "rsv381", "name": "อ่างเก็บน้ำคลองสีเสียด", "amphoe": "เมืองนครนายก", "capacity_mcm": 1.14},
        {"cresv": "rsv382", "name": "อ่างเก็บน้ำคลองโบด", "amphoe": "เมืองนครนายก", "capacity_mcm": 4.25},
        {"cresv": "rsv383", "name": "อ่างเก็บน้ำทรายทอง", "amphoe": "เมืองนครนายก", "capacity_mcm": 2.00},
        {"cresv": "rsv384", "name": "อ่างเก็บน้ำคลองวังบอน", "amphoe": "ปากพลี", "capacity_mcm": 7.60},
        {"cresv": "rsv386", "name": "อ่างเก็บน้ำคลองกลาง", "amphoe": "ปากพลี", "capacity_mcm": 3.10},
    ]

    url = "https://app.rid.go.th/reservoir/api/rsvmiddle"
    out = {
        "metadata": {
            "title": "อนุกรมเวลารายวันประวัติศาสตร์ อ่างเก็บน้ำขนาดกลาง 6 แห่ง จ.นครนายก (2009-2026)",
            "source": url,
            "province": "นครนายก",
            "province_code": "22",
            "date_range": [start_date, end_date],
            "total_reservoirs": len(nny_dams),
            "total_capacity_mcm": sum(d["capacity_mcm"] for d in nny_dams),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
        "reservoirs": {},
    }

    for d in nny_dams:
        cresv = d["cresv"]
        name = d["name"]
        print(f"  - ดึงข้อมูลประวัติศาสตร์ {name} ({cresv}) ระหว่าง {start_date} ถึง {end_date}...")
        params = {"rsvmiddle": cresv, "date_start": start_date, "date_end": end_date}
        raw = fetch_url(url, params=params)
        js = json.loads(raw.decode("utf-8"))
        rows = [r for r in js.get("reservoir_data", []) if r.get("date") is not None and r.get("qdisc_curr") not in [None, ""]]
        out["reservoirs"][cresv] = {
            "info": d,
            "total_days": len(rows),
            "earliest_date": rows[0]["date"] if rows else None,
            "latest_date": rows[-1]["date"] if rows else None,
            "data": rows,
        }
        time.sleep(0.5)

    return out


def fetch_dam_timeseries_cleaned(dam_id: int, dam_name: str, start_date: str, end_date: str) -> dict:
    """ดึงอนุกรมเวลาเขื่อนขนาดใหญ่และคัดกรองแถวข้อมูลจริง"""
    url = "https://app.rid.go.th/reservoir/api/dam"
    params = {"dam_id": dam_id, "date_start": start_date, "date_end": end_date}
    print(f"[*] ดึงอนุกรมเวลาเขื่อน {dam_name} ({dam_id}) ช่วง {start_date} ถึง {end_date}...")
    raw = fetch_url(url, params=params)
    data = json.loads(raw.decode("utf-8"))
    rows = [r for r in data.get("dam_data", []) if r.get("DATE_curr") is not None and r.get("VAL_DMD_Q_curr") not in [None, ""]]
    return {
        "metadata": {
            "dam_id": dam_id,
            "dam_name": dam_name,
            "dam_region": data.get("dam_region"),
            "dam_coordinates": data.get("dam_coordinates"),
            "total_days": len(rows),
            "earliest_date": rows[0]["DATE_curr"] if rows else None,
            "latest_date": rows[-1]["DATE_curr"] if rows else None,
            "source": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
        "dam_data": rows,
    }


def update_hashes():
    """คำนวณและบันทึก SHA-256 ของไฟล์ทั้งหมดใน data/23_rid_swoc/raw/"""
    hash_lines = []
    for p in sorted(OUT_DIR.glob("*.json")):
        h = sha256_bytes(p.read_bytes())
        hash_lines.append(f"{h}  raw/{p.name}")
    
    hashes_file = ROOT / "data" / "23_rid_swoc" / "_hashes.txt"
    hashes_file.write_text("\n".join(hash_lines) + "\n", encoding="utf-8")
    print(f"[✓] บันทึก {hashes_file.name} เรียบร้อย ({len(hash_lines)} รายการ)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ดึงข้อมูลจาก SWOC กรมชลประทาน")
    parser.add_argument("--full-history", action="store_true", help="ดึงข้อมูลประวัติศาสตร์เต็มย้อนหลังถึงปี 1995/2005/2009")
    parser.add_argument("--update-hashes", action="store_true", help="คำนวณและอัปเดตไฟล์ _hashes.txt เท่านั้น")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.update_hashes:
        update_hashes()
        return

    # 1. Snapshot เขื่อนขนาดใหญ่ 35 แห่ง
    large_snapshot = fetch_large_dams_snapshot()
    f1 = OUT_DIR / "dams_large_snapshot_latest.json"
    f1.write_bytes(json.dumps(large_snapshot, ensure_ascii=False, indent=2).encode("utf-8"))
    print(f"  -> บันทึก {f1.name}")

    # 2. Snapshot อ่างขนาดกลาง 461 แห่ง
    medium_snapshot = fetch_medium_dams_snapshot("2024-10-15")
    f2 = OUT_DIR / "dams_medium_snapshot_461.json"
    f2.write_bytes(json.dumps(medium_snapshot, ensure_ascii=False, indent=2).encode("utf-8"))
    print(f"  -> บันทึก {f2.name}")

    # 3. อ่างเก็บน้ำขนาดกลาง 6 แห่ง จ.นครนายก (ช่วงเหตุการณ์ 2569)
    nny_dams_2026 = fetch_nny_medium_dams("2026-07-01", "2026-10-15")
    f3 = OUT_DIR / "nny_medium_dams_2026.json"
    f3.write_bytes(json.dumps(nny_dams_2026, ensure_ascii=False, indent=2).encode("utf-8"))
    print(f"  -> บันทึก {f3.name}")

    # 4. อนุกรมเวลาเขื่อนป่าสักชลสิทธิ์ (ปี 2554)
    pasak_2011 = fetch_dam_timeseries(100301, "เขื่อนป่าสักชลสิทธิ์", "2011-07-01", "2011-11-30")
    f4 = OUT_DIR / "pasak_dam_2011_daily.json"
    f4.write_bytes(json.dumps(pasak_2011, ensure_ascii=False, indent=2).encode("utf-8"))
    print(f"  -> บันทึก {f4.name}")

    # 5. หน้าตัดลำน้ำจริงจากโทรมาตร RID (Ny.1B และ C.2)
    cross_sections = fetch_cross_sections(["Ny.1B", "C.2"])
    f5 = OUT_DIR / "rid_telemetry_cross_sections.json"
    f5.write_bytes(json.dumps(cross_sections, ensure_ascii=False, indent=2).encode("utf-8"))
    print(f"  -> บันทึก {f5.name}")

    # 6. ดึงข้อมูลประวัติศาสตร์เต็ม (หากระบุ --full-history)
    if args.full_history:
        print("\n=== ดึงข้อมูลประวัติศาสตร์เต็ม (Full History) ===")
        # อ่างกลางนครนายก 2009-2026
        nny_full = fetch_nny_medium_dams_full_history("2009-01-01", "2026-10-15")
        f_nny_full = OUT_DIR / "nny_medium_dams_history_2009_2026.json"
        f_nny_full.write_bytes(json.dumps(nny_full, ensure_ascii=False).encode("utf-8"))
        print(f"  -> บันทึก {f_nny_full.name}")

        # เขื่อนใหญ่
        big_dams = [
            (100501, "เขื่อนขุนด่านปราการชล", "2005-01-01", "khundan_dam_history_2005_2026.json"),
            (100301, "เขื่อนป่าสักชลสิทธิ์", "2003-01-01", "pasak_dam_history_2003_2026.json"),
            (100107, "เขื่อนแควน้อยบำรุงแดน", "2009-01-01", "kwainoi_dam_history_2009_2026.json"),
            (200101, "เขื่อนภูมิพล", "1995-01-01", "bhumibol_dam_history_1995_2026.json"),
            (200102, "เขื่อนสิริกิติ์", "1995-01-01", "sirikit_dam_history_1995_2026.json"),
        ]
        for dam_id, name, start, fname in big_dams:
            data = fetch_dam_timeseries_cleaned(dam_id, name, start, "2026-10-15")
            f_dam = OUT_DIR / fname
            f_dam.write_bytes(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            print(f"  -> บันทึก {f_dam.name}")
            time.sleep(0.5)

    update_hashes()


if __name__ == "__main__":
    main()
