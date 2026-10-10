"""เป้าหมาย 6 — รายชื่อเขื่อนผู้สมัครทั่วประเทศ (ขนาดใกล้เคียง/ใหญ่กว่าเขื่อนขุนด่านปราการชล)

ดึง snapshot `analyst/dam` จาก API thaiwater (GET ไม่ต้อง auth) แล้วกรองเขื่อนที่
normal_storage (ระดับน้ำเก็บปกติ) >= เกณฑ์ลลบ.ม. — เขื่อนเดียวกันอาจปรากฏสองแถว
(กฟผ. + ชป. รายงานคนละชุด) จึงรวมเป็นแถวเดียวต่อเขื่อนและเก็บ dam_id ทั้งสองไว้

ผลลัพธ์: analysis/goal6_dam_candidates.json
รัน: python analysis/goal6_dam_candidates.py [--min-storage 200]
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

API_URL = "https://api-v3.thaiwater.net/api/v1/thaiwater30/analyst/dam"
# เขื่อนขุนด่านปราการชล: normal_storage 224 ลลบ.ม. — เกณฑ์ "ใกล้เคียงหรือใหญ่กว่า" ตั้งต่ำกว่านิดเดียว
DEFAULT_MIN_STORAGE = 200.0


# เขื่อนเดียวกันใช้ชื่อต่างกันระหว่างแหล่งรายงาน — รวมให้เป็นชื่อเดียวก่อนจับคู่
NAME_ALIASES = {
    "แม่งัด": "แม่งัดสมบูรณ์ชล",
}


def _th(obj) -> str:
    if isinstance(obj, dict):
        name = obj.get("dam_name") or obj.get("basin_name") or obj.get("agency_name")
        if isinstance(name, dict):
            text = name.get("th") or name.get("en") or ""
        else:
            text = obj.get("th") or obj.get("en") or ""
        return NAME_ALIASES.get(text, text)
    return ""


def fetch_snapshot() -> dict:
    req = urllib.request.Request(API_URL, headers={"User-Agent": "nnyflood-goal6/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    if payload.get("result") != "OK":
        raise RuntimeError(f"API result != OK: {payload.get('result')}")
    return payload["data"]


def build_candidates(snapshot: dict, min_storage: float) -> dict:
    hourly_dam_ids = {
        r["dam"]["id"] for r in snapshot.get("dam_hourly", []) if isinstance(r.get("dam"), dict)
    }

    # รวม dam_daily (มี max/normal_storage + rule curve ผ่าน endpoint รายปี) เป็นหลัก
    by_key: dict[str, dict] = {}
    for r in snapshot.get("dam_daily", []):
        dam = r.get("dam") or {}
        normal = dam.get("normal_storage")
        if not isinstance(normal, (int, float)) or normal < min_storage:
            continue
        name = _th(dam)
        agency = _th(r.get("agency"))
        rec = by_key.setdefault(
            name,
            {
                "dam_name": name,
                "dam_ids": [],
                "agencies": [],
                "basin": _th(r.get("basin")),
                "lat": dam.get("dam_lat"),
                "long": dam.get("dam_long"),
                "max_storage": dam.get("max_storage"),
                "normal_storage": normal,
                "hourly_reported": False,
            },
        )
        if r["dam"]["id"] not in rec["dam_ids"]:
            rec["dam_ids"].append(r["dam"]["id"])
        if agency not in rec["agencies"]:
            rec["agencies"].append(agency)
        if dam["id"] in hourly_dam_ids:
            rec["hourly_reported"] = True

    # เขื่อนรายชั่วโมงที่ยังไม่ติดเกณฑ์ปริมาตร (เช่นแถวกฟผ.คนละ id) ก็แจ้งสถานะรายชั่วโมงให้ครบ
    for r in snapshot.get("dam_hourly", []):
        dam = r.get("dam") or {}
        name = _th(dam)
        if name in by_key:
            by_key[name]["hourly_reported"] = True
            if dam["id"] not in by_key[name]["dam_ids"]:
                by_key[name]["dam_ids"].append(dam["id"])

    rows = sorted(by_key.values(), key=lambda x: -x["normal_storage"])
    kd = next((r for r in rows if "ขุนด่าน" in r["dam_name"]), None)
    return {
        "source": API_URL,
        "fetched_at": max(
            (r.get("dam_date", "") for r in snapshot.get("dam_daily", [])), default=""
        ),
        "min_normal_storage": min_storage,
        "baseline_dam": kd,
        "n_candidates": len(rows),
        "candidates": rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-storage", type=float, default=DEFAULT_MIN_STORAGE)
    args = ap.parse_args()

    snapshot = fetch_snapshot()
    out = build_candidates(snapshot, args.min_storage)

    out_path = Path(__file__).resolve().parent / "goal6_dam_candidates.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"เขื่อนผู้สมัคร >= {args.min_storage:.0f} ลลบ.ม.: {out['n_candidates']} เขื่อน")
    print(f"{'เขื่อน':<28}{'เก็บปกติ':>10}{'อ่างสูงสุด':>11}  รายชม.  ลุ่มน้ำ (id ที่ใช้)")
    for r in out["candidates"]:
        mark = " *" if "ขุนด่าน" in r["dam_name"] else ""
        print(
            f"{r['dam_name'] + mark:<28}{r['normal_storage']:>10.0f}"
            f"{r['max_storage'] or 0:>11.0f}  {'ใช่' if r['hourly_reported'] else 'ไม่':>5}   "
            f"{r['basin']} ({','.join(map(str, r['dam_ids']))})"
        )
    print(f"\nเขียนแล้ว: {out_path}")


if __name__ == "__main__":
    main()
