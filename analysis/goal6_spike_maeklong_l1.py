"""เป้าหมาย 6 — spike ลุ่มที่สอง L1: แม่กลอง (ผู้ใช้ยืนยันรอบแรก 10 ต.ค. 69)

จุดประสงค์: ทดสอบว่า template ที่เรียนจาก spike ป่าสัก (goal6_spike_pasak_l1.py) **รอดระบบ กฟผ. ไหม**
— แม่กลองเป็น cascade สามเขื่อนคนละสังกัด (แก่งกระจาน ชป. · ศรีนครินทร์+วชิราลงกรณ กฟผ. รายชั่วโมงใน API)

ทำเทียบแบบเดียวกัน: (1) ประวัติเขื่อนเดินปีถอยจนว่าง 2 ปีต่อเนื่อง (2) URC compliance รายปี
— จดทุกความต่างที่เจอเป็นอินพุตออกแบบ config.json (3) จุดวัดลุ่มรายชั่วโมง 1 ก.ค.–9 ต.ค. 69
(4) ฝน NASA POWER 2 จุด

ผลลัพธ์: analysis/goal6_spike_maeklong_findings.md + goal6_spike_maeklong.json
raw: data/22_goal6_network/raw/spike_maeklong/
รัน: python analysis/goal6_spike_maeklong_l1.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import goal6_screen_basins as g6
import goal6_spike_pasak_l1 as pasak  # ใช้ helper ร่วม: dam_walk/urc_stats/fetch_power/fetch_station_year

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "analysis/goal6_spike_maeklong.json"
OUT_MD = ROOT / "analysis/goal6_spike_maeklong_findings.md"
RAW_DIR = ROOT / "data/22_goal6_network/raw/spike_maeklong"
WINDOW = pasak.WINDOW

# dam_id จาก goal6_dam_candidates.json: แก่งกระจาน 13 (ชป.) · ศรีนครินทร์ 14 · วชิราลงกรณ 15 (กฟผ.)
DAMS = {
    "แก่งกระจาน": {"id": 13, "normal": 710.0, "agency": "ชป."},
    "ศรีนครินทร์": {"id": 14, "normal": 17745.0, "agency": "กฟผ."},
    "วชิราลงกรณ": {"id": 15, "normal": 8860.0, "agency": "กฟผ."},
}
RAIN_POINTS = {
    "ลุ่มบนแม่กลอง (14.6N/98.9E)": (98.9, 14.6),
    "กาญจนบุรี (14.02N/99.14E)": (99.14, 14.02),
}


def dam_walk(dam_id: int) -> dict:
    years, empty_streak, urc_mmdd = {}, 0, {}
    for y in range(2026, 2004, -1):
        storage = g6.fetch_dam_series(dam_id, "dam_storage", str(y))
        if not storage:
            empty_streak += 1
            if empty_streak >= 2:
                break
            continue
        empty_streak = 0
        inflow = g6.fetch_dam_series(dam_id, "dam_inflow", str(y)) or []
        released = g6.fetch_dam_series(dam_id, "dam_released", str(y)) or []
        if not urc_mmdd:
            for dt, v in g6.fetch_dam_urc(dam_id, "2026"):
                if dt and len(dt) >= 10:
                    urc_mmdd[dt[5:]] = v
        rows = {dt: {"storage": v, "inflow": None, "released": None} for dt, v in storage}
        for dt, v in inflow:
            if dt in rows:
                rows[dt]["inflow"] = v
        for dt, v in released:
            if dt in rows:
                rows[dt]["released"] = v
        years[str(y)] = rows
        time.sleep(0.08)
    return {"years": years, "urc_mmdd": urc_mmdd}


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    pasak.RAW_DIR = RAW_DIR  # ให้ helper เขียน raw ฉากแม่กลองลงโฟลเดอร์ของตัวเอง
    out: dict = {"window": WINDOW, "dams": {}, "notes": []}

    print("1) ประวัติ 3 เขื่อน + URC compliance...")
    for label, cfg in DAMS.items():
        hist = dam_walk(cfg["id"])
        per_year = []
        for y in sorted(hist["years"], reverse=True):
            rows = hist["years"][y]
            st = pasak.urc_stats(rows, hist["urc_mmdd"])
            vals = [r["storage"] for r in rows.values() if r.get("storage") is not None]
            rel = [r["released"] for r in rows.values() if r.get("released") is not None]
            per_year.append({"year": y, "n_days": len(rows), "max_storage": max(vals) if vals else None,
                             "max_released": max(rel) if rel else None, **st})
        out["dams"][label] = {"dam_id": cfg["id"], "agency": cfg["agency"], "normal_storage": cfg["normal"],
                              "first_year": min((int(y) for y in hist["years"]), default=None),
                              "urc_template_points": len(hist["urc_mmdd"]), "years": per_year}
        if not hist["urc_mmdd"]:
            out["notes"].append(f"{label}: ไม่มี URC ใน API")
        print(f"  {label} (dam {cfg['id']}): ลึกถึง {out['dams'][label]['first_year']} · "
              f"URC {len(hist['urc_mmdd'])} จุด · 2569 เกิน {per_year[0]['days_over_urc_sep_oct']} วัน (ก.ย.–ต.ค.)")

    print("2) จุดวัดลุ่มแม่กลอง...")
    ss = json.loads((ROOT / "analysis/goal6_screen_2026_summary.json").read_text(encoding="utf-8"))["stations"]
    stations = [x for x in ss if x.get("basin") == "ลุ่มน้ำแม่กลอง"]
    out["stations"] = []
    for st in stations:
        rec = pasak.fetch_station_year(st["id"], st["code"])
        rec["name"] = st["name"]
        rec["crit"] = st.get("crit")
        out["stations"].append(rec)
        print(f"  {st['code']} {st['name'][:20]} -> n={rec['n']} max={rec['max']} @ {rec['peak_dt']}")
        (RAW_DIR / rec["raw"]).parent.mkdir(parents=True, exist_ok=True)

    print("3) ฝน NASA POWER 2026...")
    rain = {}
    for label, (lon, lat) in RAIN_POINTS.items():
        rain[label] = pasak.fetch_power(lon, lat)
        print(f"  {label}: ก.ย. {rain[label]['sep_total_mm']} มม. · 7วันสูงสุด {rain[label]['best7_mm']} มม. ปลาย {rain[label]['best7_end']}")
    out["rain_2026"] = {k: {kk: vv for kk, vv in v.items() if kk != "daily"} for k, v in rain.items()}
    (RAW_DIR / "nasa_power_2026.json").write_text(json.dumps(rain, ensure_ascii=False), encoding="utf-8")

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # findings MD
    lines = [
        "# spike L1 ลุ่มที่สอง: แม่กลอง — ผลเบื้องต้น + บทเรียนระบบ กฟผ.",
        "",
        f"> สร้างโดย `analysis/goal6_spike_maeklong_l1.py` · cascade 3 เขื่อน · หน้าต่างเหตุการณ์ {WINDOW[0]}..{WINDOW[1]}",
        "",
        "## 1. ประวัติเขื่อน + URC (เทมเพลตได้รับการยืนยันแล้วว่าเป็น curve จริง)",
        "",
        "| เขื่อน | สังกัด | ลึกถึงปี | URC ใน API | 2569: เกิน URC ก.ย.–ต.ค. | เก็บสูงสุด 2569 | ปล่อยสูงสุด 2569 |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, d in out["dams"].items():
        e = d["years"][0] if d["years"] else {}
        lines.append(
            f"| {label} | {d['agency']} | {d['first_year']} | {'มี' if d['urc_template_points'] else 'ไม่มี'} | "
            f"{e.get('days_over_urc_sep_oct')} วัน | {e.get('max_storage')} | {e.get('max_released')} |"
        )
    lines += ["", "### URC compliance รายปี (ทั้งปี / ก.ย.–ต.ค. / ส.ค.–ก.ย.)", ""]
    for label, d in out["dams"].items():
        lines.append(f"**{label}**")
        lines.append("")
        lines.append("| ปี | วันเกิน (ทั้งปี) | ก.ย.–ต.ค. | ส.ค.–ก.ย. | เก็บสูงสุด |")
        lines.append("|---|---|---|---|---|")
        for r in d["years"]:
            lines.append(f"| {r['year']} | {r['days_over_urc']} | {r['days_over_urc_sep_oct']} | "
                         f"{r['days_over_urc_aug_sep']} | {r['max_storage']} |")
        lines.append("")
    lines += [
        "## 2. จุดวัดลุ่มแม่กลอง (พีคคลuster 29–30 ก.ย. จาก screen)",
        "",
        "| จุดวัด | ชื่อ | ระดับสูงสุด | เวลาพีค | ชม.มีค่า | วิกฤต(API) |",
        "|---|---|---|---|---|---|",
    ]
    for s in out["stations"]:
        lines.append(f"| {s['code']} | {s['name'][:24]} | {s['max']} | {s['peak_dt']} | {s['n']} | {s['crit']} |")
    lines += [
        "",
        "## 3. ฝน (NASA POWER กริด 0.5°)",
        "",
        "| จุด | ฝนสะสม ก.ย. 69 | 7 วันสูงสุด | ปลายหน้าต่าง |",
        "|---|---|---|---|",
    ]
    for label, v in out["rain_2026"].items():
        lines.append(f"| {label} | {v['sep_total_mm']} มม. | {v['best7_mm']} มม. | {v['best7_end']} |")
    lines += [
        "",
        "## 4. บทเรียนระบบ กฟผ. (อินพุตออกแบบ config.json)",
        "",
    ]
    lines += [f"- {n}" for n in out["notes"]] or ["- (ไม่พบความต่างรูปแบบใหญ่ในรอบนี้ — จดเพิ่มตามที่เจอ)"]
    lines += [
        "- เขื่อน กฟผ. รายงานรายชั่วโมงเฉพาะ snapshot ปัจจุบัน (`dam_hourly`) — ประวัติรายชั่วโมงไม่มีใน API เช่นเดียวกัน",
        "- ช่องว่างต่อ: บานรายชั่วโมง (FOI ระดับชาติ), rating จุดวัด, ฉาก S1 ที่กำลังดาวน์โหลด",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"เขียนแล้ว: {OUT_MD}")


if __name__ == "__main__":
    main()