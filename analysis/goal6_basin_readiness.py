"""เป้าหมาย 6 — sweep ความพร้อมข้อมูล 5 ลุ่มรอบแรก (ผู้ใช้ยืนยัน 10 ต.ค. 2569)

ต่อลุ่ม: (ก) จุดวัดในทะเบียน waterlevel_load ที่ is_key_station — เดินปีถอยหลัง
(probe ก.ย. ของแต่ละปี; ถ้าว่าง probe มี.ค. เสริม; หยุดเมื่อว่าง 2 ปีต่อเนื่อง — กติกา §3.1)
(ข) เขื่อนผู้สมัครของลุ่ม — เดินปีถอยด้วย dam_storage (probe เดียวต่อปี)

ผลลัพธ์: analysis/goal6_basin_readiness.json + .md
รัน: python analysis/goal6_basin_readiness.py (ทำซ้ำได้ — จุดที่ตรวจแล้วข้าม)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import goal6_screen_basins as g6  # ใช้ get_json / fnum / day / fetch_dam_series / API_BASE ร่วมกัน

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "analysis/goal6_basin_readiness.json"
OUT_MD = ROOT / "analysis/goal6_basin_readiness.md"
BACK_TO_YEAR = 2005  # ขอบล่างของการเดินถอย (ไม่ลงกว่านี้ใน sweep — เขื่อนรายเขื่อนจะลึกกว่าใน spike)

BASINS = {
    "pasak": {"label": "ป่าสัก", "basin_names": ["ลุ่มน้ำป่าสัก"], "dams": [11]},
    "maeklong": {"label": "แม่กลอง", "basin_names": ["ลุ่มน้ำแม่กลอง"], "dams": [13, 14, 15]},
    "ping_cp": {"label": "ปิง–เจ้าพระยาตอนบน", "basin_names": ["ลุ่มน้ำปิง", "ลุ่มน้ำเจ้าพระยา"], "dams": [43]},
    "thachin": {"label": "ท่าจีน", "basin_names": ["ลุ่มน้ำท่าจีน"], "dams": [17]},
    "bp_prach": {"label": "บางปะกง–ปราจีนบุรี", "basin_names": ["ลุ่มน้ำบางปะกง"], "dams": [32, 30, 37]},
}

MAX_STATIONS_PER_BASIN = 14  # กันคิวบาน — key ก่อน แล้วเรียงตามรหัส


def basin_registry() -> dict[str, list[dict]]:
    payload = json.loads(g6.LOAD_SNAPSHOT.read_text(encoding="utf-8"))
    wl = payload["waterlevel_data"]
    rows = wl.get("data", wl) if isinstance(wl, dict) else wl
    by_basin: dict[str, list[dict]] = {}
    for r in rows:
        st = r.get("station") or {}
        b = ((r.get("basin") or {}).get("basin_name") or {}).get("th") or "ไม่ระบุลุ่ม"
        name = (st.get("tele_station_name") or {})
        by_basin.setdefault(b, []).append(
            {
                "id": st.get("id"),
                "code": st.get("tele_station_oldcode") or str(st.get("id")),
                "name": name.get("th") or name.get("en") or str(st.get("id")),
                "key": bool(st.get("is_key_station")),
                "crit": g6.fnum(st.get("critical_level_m")),
                "warn": g6.fnum(st.get("warning_level_m")),
                "agency": ((r.get("agency") or {}).get("agency_shortname") or {}).get("th") or "?",
            }
        )
    return by_basin


def pick_stations(by_basin: dict[str, list[dict]], basin_names: list[str]) -> tuple[list[dict], int]:
    cands: list[dict] = []
    total = 0
    for b in basin_names:
        lst = by_basin.get(b, [])
        total += len(lst)
        cands += [dict(x, basin=b) for x in lst if x["key"] or x["crit"] is not None]
    cands.sort(key=lambda x: (not x["key"], x["code"]))
    return cands[:MAX_STATIONS_PER_BASIN], total


def probe_station_depth(sid: int) -> dict:
    per_year, empty_streak, first_year = [], 0, None
    for y in range(2026, BACK_TO_YEAR - 1, -1):
        n_sep = _probe(sid, y, "09-01", "09-30")
        if n_sep == 0:
            n_mar = _probe(sid, y, "03-01", "03-15")
            if n_mar == 0:
                empty_streak += 1
                per_year.append({"year": y, "n_sep": 0, "n_mar": 0})
                if empty_streak >= 2:
                    break
                continue
            per_year.append({"year": y, "n_sep": 0, "n_mar": n_mar})
        else:
            empty_streak = 0
            per_year.append({"year": y, "n_sep": n_sep, "n_mar": None})
        if n_sep > 0 or per_year[-1].get("n_mar"):
            first_year = y  # เดินถอย — ค่าล่าสุดที่ยังมีข้อมูล = ปีที่ลึกที่สุด
    return {"first_year_found": first_year, "per_year": per_year}


def _probe(sid: int, year: int, md1: str, md2: str) -> int:
    u = (
        f"{g6.API_BASE}public/waterlevel_graph?station_type=tele_waterlevel"
        f"&station_id={sid}&start_date={year}-{md1}&end_date={year}-{md2}"
    )
    try:
        data = g6.get_json(u).get("data") or {}
    except RuntimeError:
        return -1
    return sum(1 for r in data.get("graph_data") or [] if r.get("value") is not None)


def probe_dam_depth(dam_id: int) -> dict:
    per_year, empty_streak, first_year = [], 0, None
    for y in range(2026, BACK_TO_YEAR - 1, -1):
        try:
            pairs = g6.fetch_dam_series(dam_id, "dam_storage", str(y))
        except RuntimeError:
            pairs = None
        n = len(pairs or [])
        per_year.append({"year": y, "n_days": n})
        if n == 0:
            empty_streak += 1
            if empty_streak >= 2:
                break
            continue
        empty_streak = 0
        first_year = y  # เดินถอย — ค่าล่าสุดที่ยังมีข้อมูล = ปีที่ลึกที่สุด
    return {"first_year_found": first_year, "per_year": per_year}


def recompute_depths(rec: dict) -> None:
    """self-heal: first_year_found จาก per_year (เดินถอย — รายการสุดท้ายที่มีข้อมูล = ลึกสุด)"""
    for st in rec.get("stations", []):
        data_years = [p["year"] for p in st.get("per_year", []) if p.get("n_sep") or p.get("n_mar")]
        st["first_year_found"] = data_years[-1] if data_years else None
    for d in rec.get("dams", []):
        data_years = [p["year"] for p in d.get("per_year", []) if p.get("n_days")]
        d["first_year_found"] = data_years[-1] if data_years else None


def main() -> None:
    by_basin = basin_registry()
    out = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "basins": {}, "note": "เดินปีถอยจนว่าง 2 ปีต่อเนื่อง (กติกา GOAL6_PLAN §3.1) · probe ก.ย. + มี.ค.สำรอง"}
    if OUT_JSON.exists():
        out["basins"] = json.loads(OUT_JSON.read_text(encoding="utf-8")).get("basins", {})

    for key, cfg in BASINS.items():
        rec = out["basins"].setdefault(key, {"label": cfg["label"]})
        recompute_depths(rec)
        if "stations" not in rec:
            picks, total = pick_stations(by_basin, cfg["basin_names"])
            rec["registry_total"] = total
            stations = []
            for i, st in enumerate(picks, 1):
                depth = probe_station_depth(st["id"])
                st.update(depth)
                stations.append(st)
                print(f"  [{cfg['label']}] {i}/{len(picks)} {st['code']} {st['name'][:18]} -> ลึกถึง {depth['first_year_found']}")
                time.sleep(0.08)
            rec["stations"] = stations
            rec.setdefault("dams", [])
        done_dams = {d["dam_id"] for d in rec.get("dams", [])}
        for did in cfg["dams"]:
            if did in done_dams:
                continue
            depth = probe_dam_depth(did)
            rec.setdefault("dams", []).append({"dam_id": did, **depth})
            print(f"  [{cfg['label']}] dam {did} -> ลึกถึง {depth['first_year_found']}")
        OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # MD
    lines = ["# ความพร้อมข้อมูล 5 ลุ่มรอบแรก (sweep 11 ต.ค. 2569)", ""]
    for key, cfg in BASINS.items():
        rec = out["basins"][key]
        lines.append(f"## {cfg['label']}")
        lines.append("")
        lines.append(f"- ทะเบียนจุดวัดในลุ่ม: {rec.get('registry_total', '?')} จุด (sweep เฉพาะ key/มีเกณฑ์ "
                     f"{len(rec.get('stations', []))} จุด — ถ้าน้อยกว่านี้ = จุดวัดลุ่มบาง = ข้อเสนอประเภท E4)")
        lines.append("")
        lines.append("| จุดวัด | สังกัด | ลึกถึงปี (ก.ย. มีค่า) | ระดับเก็บล่าสุด |")
        lines.append("|---|---|---|---|")
        for st in rec.get("stations", []):
            last = max((p["n_sep"] for p in st.get("per_year", []) if p.get("n_sep")), default=0)
            lines.append(f"| {st['code']} {st['name'][:26]} | {st['agency']} | {st.get('first_year_found') or '—'} | {last} แถวก.ย. |")
        lines.append("")
        lines.append("| เขื่อน (dam_id) | ลึกถึงปี (storage รายวัน) |")
        lines.append("|---|---|")
        for d in rec.get("dams", []):
            lines.append(f"| {d['dam_id']} | {d.get('first_year_found') or '—'} |")
        lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"เขียนแล้ว: {OUT_MD}")


if __name__ == "__main__":
    main()