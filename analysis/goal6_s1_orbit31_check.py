"""ตรวจค่าควบคุมวงโคจร 31 ด้วยฉากอ้างอิงที่สาม — ขั้นคิว: ค้นคลัง CDSE อย่างเดียว ไม่ดาวน์โหลด ไม่คำนวณ

กติกาตั้งก่อนค้นคลัง: docs/S1_ORBIT31_CONTROL_PREREG.md §2 (alt2 = ฉากวงโคจร 31 วัน UTC ล่าสุดที่เก่ากว่าวันฉากทางเลือกอย่างน้อย 6 วัน ตั้งแต่ 25 ส.ค.)
ขั้นคำนวณ (M0–M2) เพิ่มหลังเจ้าของโครงการอนุมัติรายการฉากและขนาด
รัน: python analysis/goal6_s1_orbit31_check.py queue
ผลลัพธ์: data/22_goal6_network/raw/s1_audit/s1_audit_queue_orbit31.json
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
from goal6_s1_reference_audit import LABELS, basin_pre_scenes  # noqa: E402
from s1_orbit import rel_orbit, start_of  # noqa: E402

ORBIT = 31
MIN_DAYS = 6
RAW = ROOT / "data/22_goal6_network/raw/s1_audit"
OUT = RAW / "s1_audit_queue_orbit31.json"
BASINS = ["bp_prach", "pasak", "maeklong", "thachin", "ping_cp", "bkk_lower"]


def alt_day_of(basin: str) -> str:
    """วันฉากทางเลือกเดิมของวงโคจร 31 (UTC) จากผลความไวเดิม"""
    f = ROOT / "analysis/goal6" / ("s1_ref_sensitivity.json" if basin == "bp_prach" else f"s1_ref_sensitivity_{basin}.json")
    rows = [p for p in json.loads(f.read_text(encoding="utf-8"))["passes"] if p["rel_orbit"] == ORBIT]
    return rows[0]["alt_ref_day"]


def queue() -> None:
    have = {p.name for p in RAW.glob("*.SAFE")}
    out = {}
    for b in BASINS:
        alt = dt.date.fromisoformat(alt_day_of(b))
        ps = [p for p in basin_pre_scenes(b) if rel_orbit(p["Name"]) == ORBIT]
        cand = [p for p in ps if (alt - dt.date.fromisoformat(start_of(p["Name"])[:10])).days >= MIN_DAYS]
        if not cand:
            out[b] = {"alt_day_utc": alt.isoformat(), "alt2_day_utc": None, "scenes": [], "orbit31_days_seen_utc": sorted({start_of(p["Name"])[:10] for p in ps})}
            continue
        day = max(start_of(p["Name"])[:10] for p in cand)
        pick = sorted([p for p in cand if start_of(p["Name"])[:10] == day], key=lambda p: p["Name"])
        out[b] = {"alt_day_utc": alt.isoformat(), "alt2_day_utc": day, "orbit31_days_seen_utc": sorted({start_of(p["Name"])[:10] for p in ps}),
                  "scenes": [{"name": p["Name"], "start_utc": start_of(p["Name"]), "size_mb": round(p.get("ContentLength", 0) / 1e6), "on_disk": p["Name"] in have} for p in pick]}
    uniq = {s["name"]: s for v in out.values() for s in v["scenes"]}
    OUT.write_text(json.dumps({"note": "คิวตามกติกา docs/S1_ORBIT31_CONTROL_PREREG.md §2 — ค้นคลังอย่างเดียว ยังไม่ดาวน์โหลด", "basins": out,
                               "unique_scenes": len(uniq), "unique_size_mb": sum(s["size_mb"] for s in uniq.values()),
                               "to_download": sorted(n for n, s in uniq.items() if not s["on_disk"])}, ensure_ascii=False, indent=1), encoding="utf-8")
    for b, v in out.items():
        print(LABELS[b], "· alt2", v["alt2_day_utc"], "·", len(v["scenes"]), "ฉาก", sum(s["size_mb"] for s in v["scenes"]), "MB")
    print("รวมไม่ซ้ำ", len(uniq), "ฉาก", sum(s["size_mb"] for s in uniq.values()), "MB · ต้องโหลด", sum(1 for s in uniq.values() if not s["on_disk"]))


if __name__ == "__main__":
    if sys.argv[1:] == ["queue"]:
        queue()
    else:
        raise SystemExit("ใช้: python analysis/goal6_s1_orbit31_check.py queue (ขั้นคำนวณจะเพิ่มหลังได้รับอนุมัติ)")
