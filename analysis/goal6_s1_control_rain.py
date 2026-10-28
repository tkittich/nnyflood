"""เทียบฝนก่อนเหตุการณ์ (ERA5 รายวัน) กับค่าควบคุมของเรดาร์ 13 คู่ (ลุ่ม × วงโคจร) — บรรยายเท่านั้น ไม่มีเกณฑ์ผ่านตก

กติกาตั้งก่อนคำนวณ: docs/S1_CONTROL_RAIN_PREREG.md (หน่วย 13 คู่ · หน้าต่างฝน A แคบ / B กว้าง / C สามวันก่อนถ่าย · ตัวชี้วัด 5.1–5.5)
ฝนมาจากไฟล์ที่มีอยู่แล้ว (ไม่ดึงเพิ่ม) · ค่าควบคุมมาจาก goal6/s1_ref_sensitivity*.json
รัน: python analysis/goal6_s1_control_rain.py
ผลลัพธ์: analysis/goal6/s1_control_rain.json · s1_control_rain.md
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "analysis"
RAIN_DIR = ROOT / "data/22_goal6_network/raw/rain_obs_2026"
AUDIT = ROOT / "data/22_goal6_network/raw/s1_audit"
BASINS = ["bp_prach", "pasak", "maeklong", "thachin", "ping_cp", "bkk_lower"]
LABEL = {"bp_prach": "บางปะกง", "pasak": "ป่าสัก", "maeklong": "แม่กลอง", "thachin": "ท่าจีน", "ping_cp": "ปิง–เจ้าพระยา", "bkk_lower": "เจ้าพระยาตอนล่าง–กทม."}


def ict(tag: str) -> datetime:
    """ชื่อฉาก (เวลา UTC) → เวลาไทย"""
    return datetime.strptime(re.search(r"(\d{8}T\d{6})", tag).group(1), "%Y%m%dT%H%M%S") + timedelta(hours=7)


def basin_rain(basin: str):
    """ค่าเฉลี่ยน้ำหนักเท่ากันของทุกจุดฝนในลุ่ม → (อนุกรมรายวัน, ฝนต่อจุด)"""
    pts = {p.stem[len(basin) + 1:]: json.loads(p.read_text(encoding="utf-8")) for p in sorted(RAIN_DIR.glob(f"{basin}_*.json"))}
    days = sorted(next(iter(pts.values())))
    return {d: sum(v[d] for v in pts.values()) / len(pts) for d in days}, pts


def window_sum(series: dict, d0: date, d1: date) -> float:
    """ผลรวมฝนวัน d0..d1 (รวมปลายทั้งสอง) ; d1 < d0 = ว่าง"""
    out, d = 0.0, d0
    while d <= d1:
        out += series[d.isoformat()]
        d += timedelta(days=1)
    return out


def main() -> None:
    rows, within_inputs = [], {}
    point_ranges = {}
    for b in BASINS:
        q = AUDIT / ("s1_audit_queue_sens.json" if b == "bp_prach" else f"s1_audit_queue_sens_{b}.json")
        plan = json.loads(q.read_text(encoding="utf-8"))
        plan = plan["plan"] if isinstance(plan, dict) and "plan" in plan else plan
        sj = A / ("goal6/s1_ref_sensitivity.json" if b == "bp_prach" else f"goal6/s1_ref_sensitivity_{b}.json")
        passes = json.loads(sj.read_text(encoding="utf-8"))["passes"]
        series, pts = basin_rain(b)
        for p in plan:
            ctl = [x for x in passes if x["rel_orbit"] == p["rel"] and x["role"] == "control_primary_reference_pass" and x["status"] == "ok"]
            if not p.get("alt_ref") or not ctl:
                continue
            t_alt, t_pri = min(ict(t) for t in p["alt_ref"]), min(ict(t) for t in p["primary_ref"])
            d_alt, d_pri = t_alt.date(), t_pri.date()
            one = timedelta(days=1)
            a = window_sum(series, d_alt + one, d_pri - one)
            bw = window_sum(series, d_alt, d_pri)
            c = window_sum(series, d_pri - 3 * one, d_pri - one)
            per_pt = [window_sum(v, d_alt + one, d_pri - one) for v in pts.values()]
            rows.append({"basin": b, "orbit": p["rel"], "alt_ict": t_alt.strftime("%Y-%m-%d %H:%M"), "primary_ict": t_pri.strftime("%Y-%m-%d %H:%M"),
                         "rain_A_mm": round(a, 1), "rain_B_mm": round(bw, 1), "rain_C_mm": round(c, 1),
                         "rain_A_point_range_mm": [round(min(per_pt), 1), round(max(per_pt), 1)], "n_points": len(pts),
                         "control_km2": ctl[0]["alt_ref_km2"], "coverage": ctl[0]["coverage"]})

    def rho(xs, ys):
        r = spearmanr(xs, ys)
        return round(float(r.statistic), 2)
    ctl_v = [r["control_km2"] for r in rows]
    scaled = [r["control_km2"] / r["coverage"] for r in rows]
    corr = {k: {"control": rho(ctl_v, [r[f"rain_{k}_mm"] for r in rows]), "control_per_coverage": rho(scaled, [r[f"rain_{k}_mm"] for r in rows])} for k in "ABC"}
    within = []
    for b in BASINS:
        rr = [r for r in rows if r["basin"] == b]
        if len(rr) < 2:
            continue
        hi, lo = max(rr, key=lambda r: r["control_km2"]), min(rr, key=lambda r: r["control_km2"])
        within.append({"basin": b, "orbit_max": hi["orbit"], "control_max_km2": hi["control_km2"], "orbit_min": lo["orbit"], "control_min_km2": lo["control_km2"],
                       "ratio_max_to_min": round(hi["control_km2"] / lo["control_km2"], 1) if lo["control_km2"] else None,
                       "rain_A_diff_mm": round(max(r["rain_A_mm"] for r in rr) - min(r["rain_A_mm"] for r in rr), 1),
                       "rain_A_range_mm": [min(r["rain_A_mm"] for r in rr), max(r["rain_A_mm"] for r in rr)]})
    sha = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(RAIN_DIR.glob("*.json"))}
    out = {"rule": "docs/S1_CONTROL_RAIN_PREREG.md", "n_pairs": len(rows), "rain_source": "Open-Meteo/ERA5 รายวัน เวลาไทย (ค่าจุด ไม่ใช่เครื่องวัดฝน)",
           "pairs": rows, "spearman": corr, "within_basin": within, "rain_files_sha256": sha}
    (A / "goal6/s1_control_rain.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# ฝนก่อนเหตุการณ์เทียบค่าควบคุมของเรดาร์ (13 คู่)", "", f"กติกา `docs/S1_CONTROL_RAIN_PREREG.md` · บรรยายเท่านั้น · ฝน = ERA5 ค่าจุด (ไม่ใช่เครื่องวัดฝน)", "",
          "| ลุ่ม | วงโคจร | ถ่ายทางเลือก | ถ่ายหลัก | ฝน A | ฝน B | ฝน C | ค่าควบคุม | ครอบคลุม |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {LABEL[r['basin']]} | {r['orbit']} | {r['alt_ict']} | {r['primary_ict']} | {r['rain_A_mm']} | {r['rain_B_mm']} | {r['rain_C_mm']} | {r['control_km2']} | {r['coverage']} |")
    md += ["", f"สเปียร์แมน (n={len(rows)}): " + " · ".join(f"{k}: ค่าควบคุม {v['control']:+.2f} · ต่อความครอบคลุม {v['control_per_coverage']:+.2f}" for k, v in corr.items()), ""]
    for w in within:
        md.append(f"- {LABEL[w['basin']]}: วงโคจร {w['orbit_max']} = {w['control_max_km2']} ตร.กม. เทียบวงโคจร {w['orbit_min']} = {w['control_min_km2']} (อัตราส่วน {w['ratio_max_to_min']}) · ฝน A ต่างกัน {w['rain_A_diff_mm']} มม.")
    (A / "goal6/s1_control_rain.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
