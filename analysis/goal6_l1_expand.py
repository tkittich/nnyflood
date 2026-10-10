"""เป้าหมาย 6 — runner ขยาย L1 ทุกลุ่มตาม analysis/goal6/config.json (template จาก spike ป่าสัก/แม่กลอง)

ต่อลุ่มทำ: (1) จุดวัดรายชั่วโมงหน้าต่างเหตุการณ์ → raw + สถิติ (2) เขื่อน: ประวัติเดินปีถอย + URC compliance
รายปี (3) ฝน NASA POWER (4) ลุ่ม กทม.: extract ปตร. สนน./คลอง จาก snapshot ที่ commit แล้ว
ผลลัพธ์ต่อลุ่ม: analysis/goal6/<basin>/l1_summary.json + l1_findings.md · raw: data/22_goal6_network/raw/l1_<basin>/
ทำซ้ำได้ — ไฟล์ที่มีแล้วข้าม · ลุ่มที่ทำผ่าน spike แล้ว (done_by_spike) ข้ามเว้นแต่ --basin ระบุตรง
รัน: python analysis/goal6_l1_expand.py [--basin id,...]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import goal6_screen_basins as g6
import goal6_spike_pasak_l1 as pasak
import goal6_spike_maeklong_l1 as mk  # ใช้ dam_walk(dam_id) แบบ parameterized

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "analysis/goal6/config.json"
OUT_DIR = ROOT / "analysis/goal6"
RAW_BASE = ROOT / "data/22_goal6_network/raw"


def fetch_station_raw(sid: int, code: str, raw_dir: Path) -> dict:
    p = raw_dir / f"{sid}_{g6.sanitize(code)}_2026_hourly.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    pasak.RAW_DIR = raw_dir  # ให้ helper เขียนลงโฟลเดอร์ลุ่มของตัวเอง
    return pasak.fetch_station_year(sid, code)


def dam_yearly_stats(dam_id: int, raw_dir: Path) -> dict:
    hist = mk.dam_walk(dam_id)
    per_year = []
    for y in sorted(hist["years"], reverse=True):
        rows = hist["years"][y]
        st = pasak.urc_stats(rows, hist["urc_mmdd"])
        vals = [r["storage"] for r in rows.values() if r.get("storage") is not None]
        rel = [r["released"] for r in rows.values() if r.get("released") is not None]
        per_year.append({"year": int(y), "n_days": len(rows), "max_storage": max(vals) if vals else None,
                         "max_released": max(rel) if rel else None, **st})
    # raw: เก็บ storage ปีล่าสุดเป็นหลักฐานต่อเขื่อน (ประวัติเต็มซ้ำได้จาก API)
    latest = max(hist["years"].keys(), default=None)
    if latest:
        (raw_dir / f"dam{dam_id}_dam_storage_{latest}.json").write_text(
            json.dumps({"dam_id": dam_id, "year": latest, "rows": hist["years"][latest],
                        "urc_mmdd": hist["urc_mmdd"]}, ensure_ascii=False), encoding="utf-8")
    return {"first_year": min((int(r["year"]) for r in per_year if r["n_days"] > 0), default=None),
            "urc_template_points": len(hist["urc_mmdd"]), "years": per_year}


def rain_all(points: dict, raw_dir: Path) -> dict:
    out = {}
    for label, (lon, lat) in points.items():
        out[label] = pasak.fetch_power(lon, lat)
    (raw_dir / "nasa_power_2026.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return {k: {kk: vv for kk, vv in v.items() if kk != "daily"} for k, v in out.items()}


def extract_bkk_extras(raw_dir: Path) -> dict:
    """ปตร. สนน กทม. + คลอง กทม. — extract จาก snapshot ที่ commit แล้วใน data/02 (ไม่ดึงใหม่)"""
    wg = json.loads((ROOT / "data/02_thaiwater/raw/2026-10-09_watergate_load.json").read_text(encoding="utf-8"))
    gates = [r for r in wg["watergate_data"]["data"]
             if (r.get("agency") or {}).get("agency_shortname", {}).get("th") == "สนน กทม."]
    (raw_dir / "watergate_sanam_snapshot_2026-10-09.json").write_text(
        json.dumps(gates, ensure_ascii=False), encoding="utf-8")
    cw = json.loads((ROOT / "data/02_thaiwater/raw/2026-10-09_canal_waterlevel.json").read_text(encoding="utf-8"))
    rows = cw.get("data", cw)
    if isinstance(rows, dict):
        rows = rows.get("data", [])
    canals = [r for r in rows
              if (r.get("geocode") or {}).get("province_name", {}).get("th") == "กรุงเทพมหานคร"]
    (raw_dir / "canal_bkk_snapshot_2026-10-09.json").write_text(
        json.dumps(canals, ensure_ascii=False), encoding="utf-8")
    return {"watergate_sanam_n": len(gates), "canal_bkk_n": len(canals)}


def run_basin(bid: str, rec: dict) -> dict:
    raw_dir = RAW_BASE / f"l1_{bid}"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir = OUT_DIR / bid
    out_dir.mkdir(parents=True, exist_ok=True)

    stations = []
    for st in rec["stations"]:
        r = fetch_station_raw(st["id"], st["code"], raw_dir)
        stations.append({"code": st["code"], "name": st["name"], "province": st.get("province"),
                         "n": r.get("n"), "max": r.get("max"), "peak_dt": r.get("peak_dt"),
                         "meta_min_bank": r.get("meta", {}).get("min_bank"), "raw": r.get("raw")})
    stations.sort(key=lambda x: x["peak_dt"] or "")
    dams = {d["name"]: {"dam_id": d["dam_id"], "normal_storage": d["normal_storage"],
                        **dam_yearly_stats(d["dam_id"], raw_dir)} for d in rec["dams"]}
    rain = rain_all(rec["rain_points"], raw_dir) if rec["rain_points"] else {}
    extras = extract_bkk_extras(raw_dir) if "watergate_snapshot" in rec.get("extras", []) else None

    summary = {"schema": "goal6.l1.v1", "basin": bid, "label": rec["label"],
               "window": rec["window"], "config": rec, "stations": stations, "dams": dams,
               "rain_2026": rain, "extras": extras}
    (out_dir / "l1_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [f"# L1 — {rec['label']}", "",
             f"> สร้างโดย `goal6_l1_expand.py` ตาม config · หน้าต่าง {rec['window'][0]}..{rec['window'][1]} · "
             f"จุดวัด {len(stations)} · เขื่อน {len(dams)}"]
    if rec.get("upstream_anchor"):
        lines.append(f"> โซ่น้ำจากลุ่ม: {rec['upstream_anchor']}")
    if rec.get("notes"):
        lines.append(f"> หมายเหตุ: {rec['notes']}")
    lines += ["", "## เขื่อน — URC compliance รายปี", ""]
    for name, d in dams.items():
        lines.append(f"**{name}** (dam {d['dam_id']} · เก็บปกติ {d['normal_storage']} · ลึกถึง {d['first_year']})")
        lines.append("")
        lines.append("| ปี | วันเกิน URC | ก.ย.–ต.ค. | ส.ค.–ก.ย. | เก็บสูงสุด | ปล่อยสูงสุด |")
        lines.append("|---|---|---|---|---|---|")
        for r in d["years"]:
            lines.append(f"| {r['year']} | {r['days_over_urc']} | {r['days_over_urc_sep_oct']} | "
                         f"{r['days_over_urc_aug_sep']} | {r['max_storage']} | {r['max_released']} |")
        lines.append("")
    lines += ["## จุดวัด — เรียงตามเวลาพีค", "",
              "| จุดวัด | ชื่อ | จังหวัด | ระดับสูงสุด | เวลาพีค | ชม.มีค่า | min_bank |", "|---|---|---|---|---|---|---|"]
    for s in stations:
        lines.append(f"| {s['code']} | {str(s['name'])[:22]} | {s.get('province') or ''} | {s['max']} | "
                     f"{s['peak_dt']} | {s['n']} | {s['meta_min_bank']} |")
    lines += ["", "## ฝน (NASA POWER 0.5°)", "",
              "| จุด | ก.ย. 69 | 7 วันสูงสุด | ปลายหน้าต่าง |", "|---|---|---|---|"]
    for label, v in rain.items():
        lines.append(f"| {label} | {v['sep_total_mm']} มม. | {v['best7_mm']} มม. | {v['best7_end']} |")
    if extras:
        lines += ["", f"## ฐานเครือข่าย กทม. — extract จาก snapshot",
                  f"- ปตร. สนน กทม.: {extras['watergate_sanam_n']} แห่ง · คลอง กทม.: {extras['canal_bkk_n']} จุด"]
    lines.append("")
    (out_dir / "l1_findings.md").write_text("\n".join(lines), encoding="utf-8")
    return {"stations": len(stations), "dams": len(dams)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--basin", default=None, help="id ลุ่มคั่นด้วยเครื่องหมายจุลภาค (default: ทุกลุ่มที่ยังไม่ทำ)")
    args = ap.parse_args()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    targets = args.basin.split(",") if args.basin else [
        bid for bid, rec in cfg["basins"].items() if not rec.get("done_by_spike")
    ]
    for bid in targets:
        rec = cfg["basins"][bid]
        print(f"=== {bid} ({rec['label']}) — จุดวัด {len(rec['stations'])} · เขื่อน {len(rec['dams'])} ===", flush=True)
        r = run_basin(bid, rec)
        print(f"    เสร็จ: จุดวัด {r['stations']} · เขื่อน {r['dams']}", flush=True)


if __name__ == "__main__":
    main()