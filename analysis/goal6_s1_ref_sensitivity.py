"""ความไวของพื้นที่น้ำเรดาร์ต่อวันของฉากอ้างอิง (ลุ่มบางปะกง–ปราจีนบุรี) — กติกา docs/S1_PASS_MOSAIC_PREREG.md §3

ฉากอ้างอิงทางเลือก = รอบถ่ายของวงเดียวกันก่อนฉากอ้างอิงหลักราว 12 วัน (คิวจาก goal6_s1_reference_audit.py queue_sens)
ตัดน้ำซ้ำทุกรอบถ่ายของลุ่มด้วยกฎตรึงเดิม · รอบถ่ายอ้างอิงหลักเองเทียบกับฉากอ้างอิงทางเลือก = ค่าควบคุม (การเปลี่ยนแปลงก่อนเหตุการณ์ ไม่ใช่น้ำท่วม)
รัน: python analysis/goal6_s1_ref_sensitivity.py
ผลลัพธ์: analysis/goal6/s1_ref_sensitivity.json · analysis/goal6/s1_ref_sensitivity.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from goal6_s1_reference_audit import QUEUE_SENS, SENS_BASIN  # noqa: E402
from goal6_s1_stage2_water import mosaic_db  # noqa: E402
from s1_change_detect import detect  # noqa: E402
from s1_orbit import rel_orbit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STAGE1 = ROOT / "data/22_goal6_network/derived/s1_stage1"
SUMMARY = ROOT / "data/22_goal6_network/derived/s1_stage2/summary.json"
OUT_JSON = ROOT / "analysis/goal6/s1_ref_sensitivity.json"
OUT_MD = ROOT / "analysis/goal6/s1_ref_sensitivity.md"
CELL_KM2 = 0.0009
LABEL_PCT = 10.0                           # ป้ายอ่านตารางเท่านั้น


def main() -> None:
    bid = SENS_BASIN
    plan = {p["rel"]: p for p in json.loads(QUEUE_SENS.read_text(encoding="utf-8"))["plan"]}
    rec = json.loads(SUMMARY.read_text(encoding="utf-8"))[bid]
    low = np.load(STAGE1 / f"mask_lowland_{bid}.npy")
    rows, alt_cache = [], {}
    for r in rec["scenes"]:
        rel = rel_orbit(r["scene"])
        p = plan.get(rel)
        if not p or not p.get("alt_ref"):
            rows.append({"scene": r["scene"][12:40], "rel_orbit": rel, "status": "no_alternative_reference"})
            continue
        if rel not in alt_cache:
            alt_cache[rel] = (mosaic_db(bid, p["alt_ref"], "vh"), mosaic_db(bid, p["alt_ref"], "vv"))
        pre_vh, pre_vv = alt_cache[rel]
        post_vh, post_vv = mosaic_db(bid, r["slices"], "vh"), mosaic_db(bid, r["slices"], "vv")
        w = detect(pre_vh, post_vh, pre_vv, post_vv, low)
        is_primary_ref = r["reference"] == r["scene"]
        alt_km2 = round(float(w.sum()) * CELL_KM2, 1)
        rows.append({"scene": r["scene"][12:40], "date": r["scene"][17:25], "rel_orbit": rel, "role": "control_primary_reference_pass" if is_primary_ref else "event_or_after",
                     "primary_km2": r["water_km2_lowland"], "alt_ref_km2": alt_km2, "alt_ref_day": p["alt_day"], "coverage": r["coverage"], "status": "ok"})
        print(rows[-1], flush=True)
    ev = [x for x in rows if x["status"] == "ok" and x["role"] == "event_or_after"]
    ctl = [x for x in rows if x["status"] == "ok" and x["role"] == "control_primary_reference_pass"]
    pk_p = max(ev, key=lambda x: x["primary_km2"])
    pk_a = max(ev, key=lambda x: x["alt_ref_km2"])
    chg = 100 * (pk_a["alt_ref_km2"] - pk_p["primary_km2"]) / pk_p["primary_km2"]
    summary = {"basin": bid, "n_event_passes": len(ev), "n_control_passes": len(ctl),
               "peak_primary_km2": pk_p["primary_km2"], "peak_alt_ref_km2": pk_a["alt_ref_km2"], "peak_change_pct": round(chg, 1),
               "label_sensitive_to_reference": bool(abs(chg) > LABEL_PCT),
               "control_alt_km2_range": [min((c["alt_ref_km2"] for c in ctl), default=None), max((c["alt_ref_km2"] for c in ctl), default=None)],
               "per_pass_change_pct_range": [round(min(100 * (x["alt_ref_km2"] - x["primary_km2"]) / x["primary_km2"] for x in ev if x["primary_km2"]), 1),
                                             round(max(100 * (x["alt_ref_km2"] - x["primary_km2"]) / x["primary_km2"] for x in ev if x["primary_km2"]), 1)]}
    OUT_JSON.write_text(json.dumps({"rule": "docs/S1_PASS_MOSAIC_PREREG.md §3", "summary": summary, "passes": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# ความไวต่อวันของฉากอ้างอิง — ลุ่มบางปะกง–ปราจีนบุรี", "",
         "> กติกา `docs/S1_PASS_MOSAIC_PREREG.md` §3 (ตั้งก่อนคำนวณ) · ฉากอ้างอิงทางเลือกเก่ากว่าฉากหลักราว 12 วัน · ไม่มีเกณฑ์ผ่าน/ตก", "",
         "| รอบถ่าย | วงโคจร | บทบาท | อ้างอิงหลัก (ตร.กม.) | อ้างอิงทางเลือก (ตร.กม.) |", "|---|---|---|---|---|"]
    for x in rows:
        if x["status"] == "ok":
            L.append(f"| {x['scene']} | {x['rel_orbit']} | {x['role']} | {x['primary_km2']} | {x['alt_ref_km2']} |")
    L += ["", f"ค่าสูงสุดต่อลุ่ม: หลัก {summary['peak_primary_km2']} → ทางเลือก {summary['peak_alt_ref_km2']} ตร.กม. ({summary['peak_change_pct']:+.1f}%)", ""]
    OUT_MD.write_text("\n".join(L), encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
