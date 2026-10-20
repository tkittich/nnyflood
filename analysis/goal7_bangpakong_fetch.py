"""ดึงระดับน้ำแม่น้ำล่าสุดและย้อนหลัง 30 วันของสถานีโทรมาตรในลุ่มน้ำบางปะกง (thaiwater GET ไม่ต้องใช้คีย์)
ใช้ตอบว่า "ฉะเชิงเทรา/ลุ่มบางปะกงยังท่วมอยู่หรือไม่" ด้วยระดับน้ำเทียบตลิ่ง ไม่ใช่ภาพดาวเทียมอย่างเดียว
รัน: python analysis/goal7_bangpakong_fetch.py [--days 30]
ผลลัพธ์: data/34_goal7_bangpakong/raw/<วันที่>_waterlevel_load.json และ station_series/<รหัส>.json (disk-only · manifest.md ในโฟลเดอร์)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/34_goal7_bangpakong/raw"
BASE = "https://api-v3.thaiwater.net/api/v1/thaiwater30/"
BASIN_NAME = "ลุ่มน้ำบางปะกง"


def get(ep: str, params: dict | None = None) -> dict:
    url = BASE + ep + (("?" + urllib.parse.urlencode(params)) if params else "")
    req = urllib.request.Request(url, headers={"User-Agent": "nnyflood-research/1.0"})
    for k in range(3):
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception:   # noqa: BLE001
            time.sleep(2 + 2 * k)
    raise RuntimeError(ep)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    today = dt.date.today()
    RAW.mkdir(parents=True, exist_ok=True)
    snap = get("public/waterlevel_load")
    (RAW / f"{today}_waterlevel_load.json").write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
    rows = [r for r in snap["waterlevel_data"]["data"] if (r.get("basin") or {}).get("basin_name", {}).get("th") == BASIN_NAME]
    print("สถานีในลุ่มบางปะกง:", len(rows))
    out = RAW / "station_series"
    out.mkdir(exist_ok=True)
    start = (today - dt.timedelta(days=a.days)).isoformat()
    for r in rows:
        st = r["station"]
        sid = st["id"]
        f = out / f"{st.get('tele_station_oldcode') or sid}_{sid}.json"
        d = get("public/waterlevel_graph", {"station_type": "tele_waterlevel", "station_id": sid, "start_date": start, "end_date": today.isoformat()})
        f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        time.sleep(0.2)
    print("เสร็จ", len(rows), "สถานี →", out)


if __name__ == "__main__":
    main()
