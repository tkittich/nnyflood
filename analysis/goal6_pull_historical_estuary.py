"""ดึงข้อมูลระดับน้ำและน้ำหนุนปากแม่น้ำย้อนหลังลึกที่สุดเท่าที่ระบบออนไลน์มี (Historical Estuary Data Ingestion)

กติกาตาม AGENTS.md:
- แหล่งไหนมีย้อนหลัง ดึงให้นานที่สุดเท่าที่ทำได้
- เดินปีถอยหลังจนเจอ 2 ปีว่างต่อเนื่อง แล้วหยุด (ห้ามเดาขอบล่าง)
- บันทึกไฟล์ลง data/22_goal6_network/raw/estuary_tides/ พร้อมบันทึก SHA-256 ลง _hashes.txt
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data/22_goal6_network/raw/estuary_tides"
HASH_FILE = ROOT / "data/22_goal6_network/_hashes.txt"
BASE_URL = "https://api-v3.thaiwater.net/api/v1/thaiwater30/public/waterlevel_graph?station_type=tele_waterlevel"

STATIONS = [
    (4, "CPY015", "สะพานกรุงเทพ", "เจ้าพระยา"),
    (750, "THA009", "เมืองสมุทรสาคร", "ท่าจีน"),
    (755, "MKG006", "พระรามสอง", "แม่กลอง"),
    (770, "GLF003", "บางตะบูนและบางตะบูนออก", "เพชรบุรี"),
    (751, "BKK006", "คลองมหาชัย วัดพันท้ายนรสิงห์", "ท่าจีน"),
    (1373690, "PTTEP1", "สะพานข้ามคลองโคน", "สมุทรสงคราม"),
    (1373689, "PTTEP4", "สะพานคลองปากแตระ", "สงขลา"),
    (2599, "C.12", "กรมชลประทานสามเสน", "เจ้าพระยา"),
]


def fetch_year(sid: int, code: str, y: int) -> list:
    url = f"{BASE_URL}&station_id={sid}&start_date={y}-01-01&end_date={y}-12-31"
    req = urllib.request.Request(url, headers={"User-Agent": "nnyflood-goal6/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                res = json.loads(r.read().decode("utf-8"))
                gd = (res.get("data") or {}).get("graph_data") or []
                vals = [x for x in gd if (x.get("value") if isinstance(x, dict) else x[1]) is not None]
                return vals
        except Exception as e:
            if attempt == 2:
                print(f"    [{code} {y}] ล้มเหลว 3 ครั้ง: {e}", flush=True)
                return []
            time.sleep(2)
    return []


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    new_hashes = []

    existing_hashes = HASH_FILE.read_text(encoding="utf-8") if HASH_FILE.exists() else ""

    print("=== เริ่มดึงข้อมูลสถานีปากแม่น้ำย้อนหลังสุดขีด ===", flush=True)

    for sid, code, name, basin in STATIONS:
        print(f"\nสถานี {code} ({name} ลุ่ม{basin}):", flush=True)
        consec_zero = 0
        station_years = {}
        for y in range(2025, 2010, -1):
            target = RAW_DIR / f"{y}_{sid}_{code}_annual.json"
            if target.exists():
                d = json.loads(target.read_text(encoding="utf-8"))
                n = d.get("n", len(d.get("graph_data", [])))
                print(f"  {y}: มีแคชแล้ว ({n} แถว)", flush=True)
                station_years[y] = n
                if n == 0:
                    consec_zero += 1
                    if consec_zero >= 2:
                        break
                else:
                    consec_zero = 0
                continue

            vals = fetch_year(sid, code, y)
            n = len(vals)
            print(f"  {y}: ดึงได้ {n} แถว", flush=True)

            if n > 0:
                payload = {
                    "station_id": sid,
                    "code": code,
                    "name": name,
                    "basin": basin,
                    "year": y,
                    "n": n,
                    "graph_data": vals,
                }
                content = json.dumps(payload, ensure_ascii=False, indent=1)
                target.write_text(content, encoding="utf-8")
                h = hashlib.sha256(target.read_bytes()).hexdigest()
                rel = target.relative_to(ROOT / "data/22_goal6_network").as_posix()
                if rel not in existing_hashes:
                    new_hashes.append(f"{h} *{rel}")

            station_years[y] = n
            if n == 0:
                consec_zero += 1
                if consec_zero >= 2:
                    print(f"  --> เจอ 2 ปีว่างต่อเนื่อง ({y+1}, {y}) หยุดเดินถอยหลัง", flush=True)
                    break
            else:
                consec_zero = 0

            time.sleep(1.0)  # gentle delay

        results[code] = station_years

    # บันทึกแฮชใหม่
    if new_hashes:
        with HASH_FILE.open("a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(new_hashes) + "\n")
        print(f"\nเพิ่ม {len(new_hashes)} แฮชใหม่ลงใน {HASH_FILE.name}", flush=True)

    summary_file = ROOT / "analysis/goal6/historical_estuary_summary.json"
    summary_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nสรุปปีที่ดึงได้บันทึกที่: {summary_file}", flush=True)


if __name__ == "__main__":
    main()
