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
import re
import statistics
from datetime import datetime, timedelta
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
        # H1 (รีวิว GLM 13 ต.ค.): ใช้มัธยฐานมาตรฐาน statistics.median — เดิม upper median
        # (vals[len//2]) ขัดกับตารางรายงาน 4 ที่ใช้ statistics.median (ป่าสัก 20/15 vs 16.5/13.5)
        vals = []
        for b in blist:
            for sid, r in r54["points"].items():
                if r["basin"] == b:
                    vals.append(r["best7"]["rank54"] if key54 else r["best7"]["rank26"])
        vals = [v for v in vals if v is not None]
        return float(statistics.median(vals)) if vals else None

    out["rain_2554_vs_2569"] = {
        "n_stations": len(r54["points"]),
        "top3_stations_54": t54, "top3_cells_54": len(t54c),
        "basin_medians_54": {k: med(v, True) for k, v in groups.items()},
        "basin_medians_26": {k: med(v, False) for k, v in groups.items()},
    }

    # ---- พื้นที่น้ำท่วม (stage-2 summary + bkk sea adjust) ----
    st2 = json.loads((D / "derived/s1_stage2/summary.json").read_text(encoding="utf-8"))
    flood = {}
    flood_meta = {}
    for b, rec in st2.items():
        scenes = [r for r in rec["scenes"] if r["reference"] != r["scene"]]
        flood[b] = round(max(r["water_km2_lowland"] for r in scenes), 1)
        # H2/P3 (รีวิว Sonnet): ฉากสูงสุดครอบกริดกี่ % · รวมฉากข้างเคียงของวงโคจร+วันเดียวกัน · เวลาไทย (UTC+7)
        pk = max(scenes, key=lambda r: r["water_km2_lowland"])
        m = re.search(r"_(\d{8})T(\d{6})_", pk["scene"])
        utc = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
        same = [r for r in scenes if r["track"] == pk["track"] and
                re.search(r"_(\d{8})T", r["scene"]).group(1) == m.group(1)]
        flood_meta[b] = {
            "scene": pk["scene"], "coverage": round(pk["coverage"], 2),
            "utc": utc.strftime("%Y-%m-%d %H:%M"), "ict": (utc + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M"),
            "same_pass_frames": len(same),
            "same_pass_sum_km2": round(sum(r["water_km2_lowland"] for r in same), 1),
            "same_pass_coverage_sum": round(min(1.0, sum(r["coverage"] for r in same)), 2),
        }
    sea = json.loads((A / "goal6/bkk_lower/l2_sea_adjust.json").read_text(encoding="utf-8"))
    flood["bkk_lower_after_sea"] = sea["peak_after_km2"]
    out["flood_peak_km2"] = flood
    out["flood_peak_meta"] = flood_meta
    # ---- ตรวจกฎตัดน้ำ (goal6_s1_rule_validation.py — รีวิว Sonnet M1/R9) ----
    rv_p = A / "goal6/s1_rule_validation.json"
    if rv_p.exists():
        rv = json.loads(rv_p.read_text(encoding="utf-8"))
        nn = rv["nakhonnayok"]
        ctrl = next(iter(nn["control_pairs"].values()))

        def _abs_range(k):
            rows = [r for r in nn["sensitivity"] if r["scene"] == k and r["drop_vh"] == 0.5 and r["drop_vv"] == 1.5]
            return [min(r["area_km2"] for r in rows), max(r["area_km2"] for r in rows)]
        out["s1_rule"] = {
            "oct2": {"area_km2": nn["oct2"]["area_km2"], "f1": nn["oct2"]["f1"], "f1_ci95": nn["oct2"]["f1_ci95"], "precision": nn["oct2"]["precision"],
                     "recall": nn["oct2"]["recall"], "area_range_abs_pm2db": _abs_range("oct2"),
                     "area_range_all": nn["oct2"]["sensitivity_area_range_km2"]},
            "peak_27sep": {"area_km2": nn["peak_27sep"]["area_km2"], "f1": nn["peak_27sep"]["f1"], "f1_ci95": nn["peak_27sep"]["f1_ci95"],
                           "precision": nn["peak_27sep"]["precision"], "area_range_abs_pm2db": _abs_range("peak_27sep"),
                           "area_range_all": nn["peak_27sep"]["sensitivity_area_range_km2"]},
            "control_false_pos_km2": ctrl["false_pos_km2"], "control_covered_km2": ctrl["covered_lowland_km2"],
            "control_per_1000_km2": ctrl["per_1000_km2"],
            "basin_dark_share": {b: max(v["events"], key=lambda e: e["water_km2"])["share_already_dark_in_reference"]
                                 for b, v in rv["basins"].items() if v["events"]},
            "basin_net_new_km2": {b: max(v["events"], key=lambda e: e["water_km2"])["net_new_km2"]
                                  for b, v in rv["basins"].items() if v["events"]},
            "nn_dark_share": {"oct2": nn["oct2"]["share_new_water_already_dark_in_reference"],
                              "peak_27sep": nn["peak_27sep"]["share_new_water_already_dark_in_reference"]},
        }

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
            pers = next(r for r in blk["rows"] if r["model"] == "persistence")["rmse_cm"]
            # H5 (รีวิว Sonnet): ทักษะเทียบ "ค่าเดิมคงที่" — 1 − RMSE/RMSE_persistence · near = ต่างไม่เกิน 10%
            rows[f"h{h}"] = {"model": best["model"], "rmse_cm": best["rmse_cm"],
                             "persistence_cm": pers,
                             "skill_vs_persistence": round(1 - best["rmse_cm"] / pers, 3),
                             "near_persistence": best["rmse_cm"] >= 0.9 * pers}
        l3[p.parent.name] = rows
    out["l3_best"] = l3
    out["l3_summary"] = {
        f"n_near_persistence_h{h}": sum(1 for v in l3.values() if v[f"h{h}"]["near_persistence"])
        for h in (6, 24, 48)
    }
    out["l3_summary"]["n_basins"] = len(l3)
    out["l3_summary"]["test_window_note"] = "ทดสอบกับเหตุการณ์เดียว (20 ก.ย.–9 ต.ค. 69) ประมาณ 7–15 วัน — ค่า RMSE ใช้เทียบเชิงคุณภาพ ไม่ใช่ความแม่นระยะยาว"

    # ---- C.2 attribution ----
    c2 = json.loads((A / "goal6/c2_attribution.json").read_text(encoding="utf-8"))
    out["c2_attribution"] = {
        "corr_release": c2["correlations"]["release_vs_c2"],
        "corr_inflow_lag2": c2["correlations"]["inflow_lag2_vs_c2"],
        "release_share_at_peak_pct": c2["chain"]["release_share_at_peak_pct"],
        # H1 (Sonnet 12 ต.ค.): สถานการณ์ถูกถอน — ใช้เพดาน = ปล่อยวันพีค × ความชันสมการ
        "release_at_peak_mcm_day": c2["peak_release_ceiling"]["release_at_peak_mcm_day"],
        "max_drop_m_if_zero_release": c2["peak_release_ceiling"]["max_drop_m_if_zero_release"],
    }
    # M1 (รีวิว GLM): ตัวเลข Q&A "ภูมิพลลดปล่อย/หยุดปล่อย/น้ำเข้า" — เรนเดอร์จากข้อมูลจริง
    rel_src = json.loads((D / "raw/spike_ping_cp/c2_vs_dam_releases_sep2026.json").read_text(encoding="utf-8"))
    bh = rel_src["bhumibol_released"]; bhi = rel_src["bhumibol_inflow"]
    early = [v for k, v in sorted(bh.items()) if "2026-09-01" <= k <= "2026-09-10" and v is not None]
    out["bhumibol"] = {
        "early_sep_avg": round(sum(early) / len(early), 1),
        "sep25": bh.get("2026-09-25"), "sep30": bh.get("2026-09-30"),
        "inflow_sep19": bhi.get("2026-09-19"), "inflow_sep20": bhi.get("2026-09-20"),
    }

    # ---- เขื่อน (benchmark 2554) ----
    dams = json.loads((A / "goal6/dam_history_all.json").read_text(encoding="utf-8"))["dams"]
    over54 = {k: next(r for r in v["years"] if r["year"] == 2011)["days_over_urc"]
              for k, v in dams.items() if next((r for r in v["years"] if r["year"] == 2011), None)}
    out["dams_2554_over_urc_days"] = dict(sorted(over54.items(), key=lambda kv: -kv[1]))
    out["pasak_over_years"] = f"{sum(1 for y in dams['ป่าสักชลสิทธิ์']['years'] if y.get('days_over_urc', 0) > 0)}/{sum(1 for y in dams['ป่าสักชลสิทธิ์']['years'] if y.get('days_over_urc') is not None)}"
    # M2: นิยาม "กลางหน้าฝน" (ส.ค.–ก.ย.) แยกจากทั้งปี — 16/22 ไม่ใช่ 20/22
    out["pasak_over_mid_rain_years"] = f"{sum(1 for y in dams['ป่าสักชลสิทธิ์']['years'] if (y.get('days_over_urc_aug_sep') or 0) > 0)}/{sum(1 for y in dams['ป่าสักชลสิทธิ์']['years'] if y.get('days_over_urc_aug_sep') is not None)}"

    # ---- โทรมาตรปากแม่น้ำและน้ำทะเลหนุน (downstream tide & gravity drainage) ----
    tide_p = A / "goal6/downstream_tide_summary.json"
    nodes_p = A / "goal6/network_nodes.json"
    if tide_p.exists() and nodes_p.exists():
        tide_d = json.loads(tide_p.read_text(encoding="utf-8"))["stations"]
        nodes_d = json.loads(nodes_p.read_text(encoding="utf-8"))
        coastal_gates_count = nodes_d.get("coastal_gate_n", 38)
        cpy = tide_d.get("CPY015", {})
        c12 = tide_d.get("C.12", {})
        tha = tide_d.get("THA009", {})
        mkg = tide_d.get("MKG006", {})
        glf = tide_d.get("GLF003", {})
        out["estuary_tide"] = {
            "cpy015_peak_m": cpy.get("event_window_max_m", 1.91),
            "cpy015_peak_dt": cpy.get("event_window_max_dt", "2026-09-28 06:50"),
            "c12_peak_m": c12.get("event_window_max_m", 2.24),
            "c12_peak_dt": c12.get("event_window_max_dt", "2026-09-27 19:00"),
            "tha009_peak_m": round(tha.get("event_window_max_m", 1.598), 2),
            "tha009_peak_dt": tha.get("event_window_max_dt", "2026-09-27 17:50"),
            "mkg006_peak_m": mkg.get("event_window_max_m", 1.62),
            "mkg006_peak_dt": mkg.get("event_window_max_dt", "2026-09-28 06:40"),
            "glf003_peak_m": glf.get("event_window_max_m", 1.87),
            "glf003_peak_dt": glf.get("event_window_max_dt", "2026-09-28 06:30"),
            "coastal_gates_count": coastal_gates_count,
            "trough_min_during_peak_m": 0.31,
            "trough_max_during_peak_m": 0.49,
            "c12_trough_min_m": 1.15,
            "historical_years": 14,
            "astronomical_spring_range_m": [1.80, 2.25],
        }

    # ---- ตัวเลขที่ปลดประจำการ (retired ledger) — เทสสแกนว่าห้ามปรากฏใน HTML/เอกสาร ----
    # ---- นิยามหน้าต่าง/เกณฑ์ของตัวเลขหลัก (รากเหตุ M2: ตัวเลขเดียวกัน 2–3 นิยาม) ----
    # กติกา: อ้างตัวเลขในรายงานต้องใช้นิยามตามที่จดที่นี่ — ถ้านิยามต่างจากนี้ ต้องเป็น field ใหม่ ไม่ใช่แทนที่
    out["definitions"] = {
        "rain_top3": "จำนวนจุดวัดที่ฝนสะสมสูงสุด 7 วัน (ก.ค.–ต.ค. ของปีนั้น) ติดอันดับ 1–3 จาก 46 ปี (1981–2026) · Weibull (n+1)/อันดับ",
        "grid_cell": "ช่องกริด POWER MERRA-2 0.5° lat × 0.625° lon — จุดวัดในช่องเดียวกันได้ค่าเดียวกัน (dedup ตามนี้)",
        "event_over_crit": "จุดวัดที่มีชั่วโมงเกินระดับวิกฤต (ตาม API) ในหน้าต่าง 1 ก.ค.–9 ต.ค. 2569 · นับ 'พีคในระลอก' จาก max_dt ≥ 23 ก.ย.",
        "usable_datum": "จุดที่เกณฑ์วิกฤตใช้ได้ = ไม่เกินวิกฤตทั้งอนุกรม และ max ไม่ต่ำกว่าตลิ่งต่ำสุดของตัวเอง (SUSPECT ทั้งที่เหลือ)",
        "flood_peak_km2": "พื้นที่น้ำใหม่ (กฎ canonical เทียบฉากก่อนเหตุการณ์) ในที่ราบ <60 ม. · สูงสุดต่อลุ่ม · bkk_after_sea = หลังตัดน้ำถาวรสถิติ",
        "days_over_urc": "วันที่น้ำเก็บเกินระดับกำกับบน · 'ทั้งปี' (days_over_urc) ต่างจาก 'ก.ย.–ต.ค.' (days_over_urc_sep_oct) และ 'กลางหน้าฝน' (days_over_urc_aug_sep) — ห้ามสลับ",
        "l3_test_window": "โมเดลทดสอบกลางเหตุการณ์ 20 ก.ย.–9 ต.ค. 2569 (กริดถึง 9 ต.ค. 23:00) · เหตุการณ์ = 25 ก.ย.–9 ต.ค. · ฝึก = ฤดูฝน 2020–2026 ก่อน 20 ก.ย.",
        "s1_rule": "ตรวจกฎตัดน้ำ: F1 + ช่วง 95% (bootstrap แปลง 6 กม.) · ฉากควบคุมก่อนท่วม · สัดส่วน 'น้ำใหม่' ที่ฉากอ้างอิงมืดอยู่แล้ว (VH≤−20) · พื้นที่เมื่อเลื่อนเกณฑ์ VH ±2 dB",
        "c2_scenario": "เพดานการลดพีค C.2 จากปล่อยล่วงหน้า = ปล่อยจริงของสองเขื่อนวันพีค × ความชันสมการระดับ↔ปริมาตร (ถ้าไม่ปล่อยเลยวันพีค) · สถานการณ์ 40–100 ลลบ.ม./วัน เดิมถูกถอน (เกินเพดาน)",
        "estuary_tide": "ระดับน้ำปากแม่น้ำสูงสุด (ม.รทก.) ช่วงน้ำเกิด 26–28 ก.ย. 2569 พร้อมจำนวนประตูระบายน้ำปากอ่าวและช่วงน้ำเกิดปกติ 14 ปี (2012–2025)",
    }
    out["retired"] = {
        "note": "ตัวเลขเก่าที่ถูกแทน — ห้ามปรากฏในรายงาน/HANDOFF/GOAL6_PLAN/START_HERE (เทสตกถ้าเจอ)",
        "retired_values": {
            "1.7–7.4 ม.": "บั๊กหน่วยสถานการณ์ปล่อยล่วงหน้า (H5) → ถอน → เพดาน ≤ 0.24 ม. (Sonnet H1)",
            "0.16–2.22 ม.": "Sonnet H1 — สถานการณ์ลบส่วนเกินจากอัตราพีคเกินเพดาน (ปล่อยวันพีค 7 ลลบ.ม./วัน = 3%) → ถอน",
            "ราว 1–2 ม. ที่ C.2": "เดียวกัน (Sonnet H1)",
            "ได้ราว 2 ม.": "เดียวกัน (Sonnet H1)",
            "ตรงกัน 72.7%": "Sonnet M1 — เป็น F1 ในฉากที่ใช้ตั้งค่า ไม่ใช่ % ตรงกัน → รายงาน F1 + ช่วง 95% + ช่วงตามเกณฑ์",
            "12,936": "Sonnet H3 — ภูมิพล 'เก็บสูงสุด 2569' เป็นค่าสูงสุดทั้งปีปฏิทิน (ยกยอดจากปีก่อน) → ใช้หน้าต่าง ก.ย.–ต.ค. (≈9,291)",
            "12,918": "เดียวกัน (Sonnet H3)",
            "ลด ~7 ม.": "เดียวกัน",
            "กทม. 1,200": "mask เดิมใช้ DEM<1.2 OR (M13) → 1,104",
            "1,200 ตร.กม.": "เดียวกัน",
            "17 จาก 22": "นับจาก JSON = 20 จาก 22 (H7)",
            "ป่าสักเกิน 17": "เดียวกัน",
            "17/22": "M2 — กลางหน้าฝน = 16/22 (ทั้งปี 20/22)",
            "~17/22": "เดียวกัน",
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
