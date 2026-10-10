"""เป้าหมาย 6 — canonical.json: แหล่งเดียวของตัวเลขที่ปรากฏในรายงาน/เอกสาร

สัญญา canonical (ต่อยอดระบบ canonical_numbers.json ของรายงาน 1–2 ที่ผ่านรีวิว 5 รอบ):
- ตัวเลขทุกตัวที่ปรากฏใน รายงาน 3/4 · HANDOFF · GOAL6_PLAN · START_HERE ต้องมาจากไฟล์นี้
- สคริปต์นี้เป็นคนเขียนจากไฟล์ผลวิเคราะห์ทั้งหมด — ห้ามมือเขียนทับ
- ตัวเลขเก่าที่ถูกแทนลง "retired" พร้อมเหตุผล — เทส test_goal6_consistency.py สแกนหาทั้ง
  (ค่าเก่าปรากฏใน HTML/เอกสาร = เทสตก)
- builders อ่านที่นี่เท่านั้น · แก้ค่า = แก้สคริปต์ต้นทางแล้วรัน goal6_build_all.py

รัน: python analysis/goal6_canonical.py
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "analysis"
D = ROOT / "data/22_goal6_network"
OUT = A / "goal6/canonical.json"


def main() -> None:
    out: dict = {}

    # ---- ฝนระดับชาติ (rain_rarity_national) ----
    rn = json.loads((A / "goal6/rain_rarity_national.json").read_text(encoding="utf-8"))
    pts = rn["points"]
    n_pts = len(pts)
    top7 = [p for p in pts.values() if (p["best7"]["rank_in_n"] or 99) <= 3]
    top30 = [p for p in pts.values() if (p["best30"]["rank_in_n"] or 99) <= 3]
    # dedup ช่องกริด POWER (MERRA-2: 0.5° lat × 0.625° lon)
    cells = collections.defaultdict(list)
    top7_cells, top30_cells = set(), set()
    for p in pts.values():
        c = (round(p["lat"] / 0.5), round(p["lon"] / 0.625))
        cells[c].append(p)
        if (p["best7"]["rank_in_n"] or 99) <= 3:
            top7_cells.add(c)
        if (p["best30"]["rank_in_n"] or 99) <= 3:
            top30_cells.add(c)
    # ลุ่มเต็มลุ่ม (ทุกจุดอันดับ 1–3)
    by_basin = collections.defaultdict(list)
    for p in pts.values():
        by_basin[p["basin"]].append(p)
    full_basins = sorted(b for b, lst in by_basin.items()
                         if all((x["best7"]["rank_in_n"] or 99) <= 3 for x in lst))
    out["rain_national"] = {
        "n_stations": n_pts,
        "n_cells": len(cells),
        "top3_stations_7d": len(top7),
        "top3_cells_7d": len(top7_cells),
        "top3_stations_30d": len(top30),
        "top3_cells_30d": len(top30_cells),
        "full_basins": full_basins,
        "full_basin_counts": {b: f"{sum(1 for x in by_basin[b] if (x['best7']['rank_in_n'] or 99) <= 3)}/{len(by_basin[b])}"
                              for b in full_basins},
    }

    # ---- ฝน 2554 (rain_rarity_2554) ----
    r54 = json.loads((A / "goal6/rain_rarity_2554.json").read_text(encoding="utf-8"))
    t54 = sum(1 for r in r54["points"].values() if (r["best7"]["rank54"] or 99) <= 3)
    t54c = set()
    for sid, r in r54["points"].items():
        if (r["best7"]["rank54"] or 99) <= 3:
            p = pts[sid]
            t54c.add((round(p["lat"] / 0.5), round(p["lon"] / 0.625)))
    # อันดับกลางต่อลุ่ม (มัธยฐานรวมทุกจุดในกลุ่ม — เหมือนตารางรายงาน 4)
    groups = {"north": ["ลุ่มน้ำปิง", "ลุ่มน้ำวัง", "ลุ่มน้ำยม"],
              "chao": ["ลุ่มน้ำเจ้าพระยา"], "pasak": ["ลุ่มน้ำป่าสัก"],
              "east_coast": ["ลุ่มน้ำชายฝั่งทะเลตะวันออก"], "bp": ["ลุ่มน้ำบางปะกง"],
              "maeklong": ["ลุ่มน้ำแม่กลอง"], "thachin": ["ลุ่มน้ำท่าจีน"],
              "south": ["ลุ่มน้ำภาคใต้ฝั่งตะวันออกตอนบน", "ลุ่มน้ำภาคใต้ฝั่งตะวันออกตอนล่าง", "ลุ่มน้ำภาคใต้ฝั่งตะวันตก"]}

    def med(blist, key54):
        vals = []
        for b in blist:
            for sid, r in r54["points"].items():
                if r["basin"] == b:
                    vals.append(r["best7"]["rank54"] if key54 else r["best7"]["rank26"])
        vals = [v for v in vals if v is not None]
        vals.sort()
        return vals[len(vals) // 2] if vals else None

    out["rain_2554_vs_2569"] = {
        "n_stations": len(r54["points"]),
        "top3_stations_54": t54, "top3_cells_54": len(t54c),
        "basin_medians_54": {k: med(v, True) for k, v in groups.items()},
        "basin_medians_26": {k: med(v, False) for k, v in groups.items()},
    }

    # ---- พื้นที่น้ำท่วม (stage-2 summary + bkk sea adjust) ----
    st2 = json.loads((D / "derived/s1_stage2/summary.json").read_text(encoding="utf-8"))
    flood = {}
    for b, rec in st2.items():
        scenes = [r for r in rec["scenes"] if r["reference"] != r["scene"]]
        flood[b] = round(max(r["water_km2_lowland"] for r in scenes), 1)
    sea = json.loads((A / "goal6/bkk_lower/l2_sea_adjust.json").read_text(encoding="utf-8"))
    flood["bkk_lower_after_sea"] = sea["peak_after_km2"]
    out["flood_peak_km2"] = flood

    # ---- เหตุการณ์จุดวัด (screen) ----
    sc = json.loads((A / "goal6_screen_2026_summary.json").read_text(encoding="utf-8"))
    ev = [x for x in sc["stations"] if x.get("crit") is not None and (x.get("hours_over_crit") or 0) > 0]
    event_codes = [x["code"] for x in ev]
    usable = [x for x in ev if not (
        (x["hours_over_crit"] == x["n_values"] and x["longest_run_over_crit_h"] == x["n_values"])
        or (x.get("meta_min_bank") is not None and x.get("max_val") is not None and x["max_val"] < x["meta_min_bank"]))]
    wave = [x for x in ev if (x.get("max_dt") or "") >= "2026-09-23"]
    out["event_stations"] = {
        "n_over_crit": len(ev),
        "n_wave_peak": len(wave),
        "n_pre_wave_peak": len(ev) - len(wave),
        "n_usable_datum": len(usable),
        "usable_codes": sorted(x["code"] for x in usable),
        "suspect_codes": sorted(set(event_codes) - {x["code"] for x in usable}),
        "n_screened": len(sc["stations"]),
    }

    # ---- โมเดล L3 (ดีสุดต่อลุ่มต่อระยะ) ----
    l3 = {}
    for p in sorted((A / "goal6").glob("*/l3_model.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        rows = {}
        for h, blk in d["results"].items():
            best = min(blk["rows"], key=lambda r: r["rmse_cm"])
            rows[f"h{h}"] = {"model": best["model"], "rmse_cm": best["rmse_cm"]}
        l3[p.parent.name] = rows
    out["l3_best"] = l3

    # ---- C.2 attribution ----
    c2 = json.loads((A / "goal6/c2_attribution.json").read_text(encoding="utf-8"))
    out["c2_attribution"] = {
        "corr_release": c2["correlations"]["release_vs_c2"],
        "corr_inflow_lag2": c2["correlations"]["inflow_lag2_vs_c2"],
        "release_share_at_peak_pct": c2["chain"]["release_share_at_peak_pct"],
        "scenarios": [{"release": s["release_per_day"], "drop_m": s["drop_m"],
                       "within_calib": s["within_calib"]} for s in c2["prerelease_scenarios"]],
    }

    # ---- เขื่อน (benchmark 2554) ----
    dams = json.loads((A / "goal6/dam_history_all.json").read_text(encoding="utf-8"))["dams"]
    over54 = {k: next(r for r in v["years"] if r["year"] == 2011)["days_over_urc"]
              for k, v in dams.items() if next((r for r in v["years"] if r["year"] == 2011), None)}
    out["dams_2554_over_urc_days"] = dict(sorted(over54.items(), key=lambda kv: -kv[1]))
    out["pasak_over_years"] = f"{sum(1 for y in dams['ป่าสักชลสิทธิ์']['years'] if y.get('days_over_urc', 0) > 0)}/{sum(1 for y in dams['ป่าสักชลสิทธิ์']['years'] if y.get('days_over_urc') is not None)}"

    # ---- ตัวเลขที่ปลดประจำการ (retired ledger) — เทสสแกนว่าห้ามปรากฏใน HTML/เอกสาร ----
    out["retired"] = {
        "note": "ตัวเลขเก่าที่ถูกแทน — ห้ามปรากฏในรายงาน/HANDOFF/GOAL6_PLAN/START_HERE (เทสตกถ้าเจอ)",
        "retired_values": {
            "1.7–7.4 ม.": "บั๊กหน่วยสถานการณ์ปล่อยล่วงหน้า (H5) → 0.16–2.22 ม.",
            "ลด ~7 ม.": "เดียวกัน",
            "กทม. 1,200": "mask เดิมใช้ DEM<1.2 OR (M13) → 1,104",
            "1,200 ตร.กม.": "เดียวกัน",
            "17 จาก 22": "นับจาก JSON = 20 จาก 22 (H7)",
            "ป่าสักเกิน 17": "เดียวกัน",
            "SUSPECT 18": "เกณฑ์ partial เพิ่ม → 19",
            "12 จาก 13": "ฝนระดับชาติ 67/199 แทน",
            "12/13": "เดียวกัน",
            "อันดับ 1 จาก 46 ปี</b> ที่ 12": "เดียวกัน",
            "25 จุด</b> ระดับน้ำสูงสุดช่วง": "H2 แยก 17+8",
            "พังพอกันทุกลุ่ม": "M9 — คลาดเคลื่อนโตตามลุ่ม",
            "แม่นสุด 5–15 ซม. ที่ระยะ 6–24 ชม.": "H6 แก้ฝนรั่ว → 5–25 ซม. @6 ชม.",
            "มากกว่าประมาณ 4 เท่า": "M1 → ~3 เท่า (นับช่องกริด)",
            "ฝนหนักกระจุกลุ่มเหนือ": "M2 → กระจายหลายลุ่ม",
            "ภูมิพลถึง 1964": "H2 ไม่มี snapshot รองรับ",
            "เขื่อน กฟผ. ทุกแห่ง 0 วัน": "H1 — ระบุ 3 เขื่อนแม่กลอง",
            "ไม่เคยเกินระดับกำกับเลยทั้งสองปี</b> —": "H1 — scoped + หมายเหตุภูมิพล/สิริกิติ์",
            "4.7 ซม. @+6": "H6 แก้ฝนรั่ว → 5.3",
            "ทุกโมเดลพังพอกัน": "เดียวกับ พังพอกันทุกลุ่ม",
        },
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"canonical.json: rain {out['rain_national']['top3_stations_7d']}/{n_pts} "
          f"({out['rain_national']['top3_cells_7d']}/{len(cells)} ช่อง) · "
          f"554 {t54} จุด/{len(t54c)} ช่อง · ท่วม {flood} · EVENT {out['event_stations']['n_usable_datum']} จุดใช้ได้ · "
          f"retired {len(out['retired']['retired_values'])} รายการ")
    print(f"เขียนแล้ว: {OUT}")


if __name__ == "__main__":
    main()
