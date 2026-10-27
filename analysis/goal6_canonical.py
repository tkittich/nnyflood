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


def assert_inward_data_contracts(out: dict) -> None:
    """สัญญาข้อมูลขาเข้า (Inward Data Contracts — DATA_CONSISTENCY_WORKFLOW.md ชั้นที่ 1)
    ตรวจสอบความสมเหตุสมผลทางกายภาพและขอบเขตตัวเลขก่อนบันทึกลง canonical.json
    """
    # 1. สัญญาฝน (Rain Contracts)
    rn = out["rain_national"]
    assert rn["top3_stations_7d"] <= rn["n_stations"], "จำนวนสถานีฝนติด top 3 ต้องไม่เกินจำนวนสถานีทั้งหมด"
    assert rn["top3_cells_7d"] <= rn["n_cells"], "จำนวนช่องกริดฝนติด top 3 ต้องไม่เกินจำนวนช่องกริดทั้งหมด"

    # 2. สัญญาพื้นที่น้ำท่วม (Flood Extent Bounds)
    fl = out["flood_peak_km2"]
    for basin, area in fl.items():
        assert area >= 0, f"พื้นที่น้ำท่วมลุ่มน้ำ {basin} ต้องไม่ติดลบ: {area}"
    if "bkk_lower_after_sea" in fl and "bkk_lower" in fl:
        assert fl["bkk_lower_after_sea"] <= fl["bkk_lower"], "พื้นที่น้ำท่วมหลังหักทะเลหนุนต้องไม่เกินพื้นที่น้ำท่วมก่อนหัก"

    # 3. สัญญาเขื่อนและการหน่วงน้ำ (Dam Baseline & Surcharge Contracts)
    if "pasak_24y_baseline" in out:
        ps = out["pasak_24y_baseline"]
        assert ps["over_normal_years"] <= ps["years_analyzed"], "ปีที่เกินระดับปกติป่าสักต้องไม่เกินจำนวนปีที่วิเคราะห์"
        assert ps["over_1000mcm_years"] <= ps["over_normal_years"], "ปีที่แตะ 1,000 ล้าน ลบ.ม. ต้องเป็นสับเซตของปีที่เกินระดับปกติ (960 ล้าน ลบ.ม.)"
        assert ps["record_peak_mcm"] >= ps["y2569_peak_mcm"], "สถิติน้ำสูงสุดตลอดกาลต้องไม่ต่ำกว่าน้ำสูงสุดปี 2569"

    # 4. สัญญาโทรมาตรปากแม่น้ำ (Estuary & Coastal Drainage Contracts)
    if "estuary_tide" in out:
        et = out["estuary_tide"]
        assert et["c12_peak_m"] > et["c12_trough_min_m"], "ระดับน้ำทะเลหนุนสูงสุดต้องสูงกว่าระดับน้ำลงต่ำสุด"
        assert et["astronomical_spring_range_m"][0] < et["astronomical_spring_range_m"][1], "ช่วงน้ำเกิดดาราศาสตร์ต้องมี min < max"

    # 5. สัญญาคุณภาพน้ำ (Salinity Standards)
    if "estuary_salinity" in out:
        es = out["estuary_salinity"]
        assert es["samlae_salinity_min_gl"] <= es["samlae_salinity_max_gl"], "ความเค็มต่ำสุดต้องไม่เกินความเค็มสูงสุด"
        assert es["samlae_salinity_max_gl"] <= es["samlae_warning_threshold_gl"], "ความเค็มสำแลจริงต้องไม่เกินเกณฑ์เตือนภัย (0.25 ก./ล.) ในช่วงเหตุการณ์"


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
        same = [pk]       # หน่วยของขั้นที่ 2 คือรอบถ่าย (รวมชิ้นส่วนแล้ว) — docs/S1_PASS_MOSAIC_PREREG.md §1
        flood_meta[b] = {
            "scene": pk["scene"], "coverage": round(pk["coverage"], 2),
            "utc": utc.strftime("%Y-%m-%d %H:%M"), "ict": (utc + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M"),
            "same_pass_frames": pk["n_slices"],
            "same_pass_sum_km2": round(sum(r["water_km2_lowland"] for r in same), 1),
            "same_pass_coverage_sum": round(min(1.0, sum(r["coverage"] for r in same)), 2),
            "max_extent_km2": st2[b]["max_extent"]["km2_lowland"], "max_extent_covered_lowland_frac": st2[b]["max_extent"]["covered_lowland_frac"],
            "max_extent_n_passes": st2[b]["max_extent"]["n_passes"],
        }
    sea = json.loads((A / "goal6/bkk_lower/l2_sea_adjust.json").read_text(encoding="utf-8"))
    flood["bkk_lower_after_sea"] = sea["peak_after_km2"]
    out["flood_peak_km2"] = flood
    out["flood_peak_meta"] = flood_meta
    # ---- น้ำเข้า–ปล่อย–เก็บ รายเขื่อน (goal6_dam_inflow.py — รีวิว Sonnet H4/ข้อ 1) ----
    di_p = A / "goal6/dam_inflow.json"
    if di_p.exists():
        di = json.loads(di_p.read_text(encoding="utf-8"))
        slim = {}
        for n, r in di["dams"].items():
            if "y2569" not in r or r["y2569"] is None:
                continue
            slim[n] = {"n_years": r["n_years"], "inflow_rank2554": r["inflow_rank2554"], "inflow_rank2569": r["inflow_rank2569"],
                       "inflow2554": (r["y2554"] or {}).get("inflow_season_mcm"), "inflow2569": r["y2569"]["inflow_season_mcm"],
                       "sep1_over_2554": (r["y2554"] or {}).get("sep1_over_urc_mcm"), "sep1_over_2569": r["y2569"]["sep1_over_urc_mcm"],
                       "days_over_2554": (r["y2554"] or {}).get("days_over_urc_window"), "days_over_2569": r["y2569"]["days_over_urc_window"],
                       "retained_2554": (r["y2554"] or {}).get("retained_share"), "retained_2569": r["y2569"]["retained_share"]}
        out["dam_inflow"] = slim
    # ---- ฝนเฉลี่ยทั้งลุ่ม + ฝนรวมฤดู (goal6_basin_rain.py — รีวิว Sonnet A2) ----
    br_p = A / "goal6/basin_rain.json"
    if br_p.exists():
        br = json.loads(br_p.read_text(encoding="utf-8"))
        out["basin_rain"] = {
            "window": br["window"],
            "basins": {b: {"gauge": v["gauge"], "label": v["label"], "n_cells": v["n_cells"],
                           **{m: {k: x[k] for k in ("v2554", "v2569", "rank2554", "rank2569", "median")}
                              for m, x in v["metrics"].items()}} for b, v in br["basins"].items()},
        }
    # ---- ผลกระทบ ประชากร/ถนน (goal6_exposure.py) ----
    ex_p = A / "goal6/exposure.json"
    if ex_p.exists():
        out["exposure"] = json.loads(ex_p.read_text(encoding="utf-8"))["scenes"]
    # ---- ผิวดิน/น้ำถาวร (goal6_s1_landcover.py — WorldCover + JRC) ----
    lc_p = A / "goal6/s1_landcover.json"
    if lc_p.exists():
        lc = json.loads(lc_p.read_text(encoding="utf-8"))["scenes"]
        def _sh(r, key, c):
            return r[key].get(str(c), {}).get("share", 0.0)
        def _base(r, c):
            tot = sum(v["km2"] for v in r["baseline_composition"].values())
            return round(r["baseline_composition"].get(str(c), {}).get("km2", 0.0) / tot, 3) if tot else None
        out["s1_landcover"] = {t: {
            "steps_km2": r["steps_km2"], "strict_new_km2": r["steps_km2"]["minus_already_dark"],
            "share_on_worldcover_water": r["share_on_worldcover_water"], "share_on_jrc_occ50": r["share_on_jrc_occ50"],
            "share_det_crop": _sh(r, "detected_composition", 40), "share_base_crop": _base(r, 40),
            "share_det_built": _sh(r, "detected_composition", 50), "share_base_built": _base(r, 50),
            "precision_by_class": {k: v["inside_gistda"] for k, v in r.get("precision_by_class", {}).items()},
            "fp_km2_by_class": {k: round(v["detected_km2"] * (1 - v["inside_gistda"]), 1)
                                for k, v in r.get("precision_by_class", {}).items()},
        } for t, r in lc.items()}
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

    # ---- เทียบพื้นที่น้ำเรดาร์กับ GISTDA 30 วัน (goal6_s1_gistda_crosscheck.py — กติกา docs/S1_GISTDA_CROSSCHECK_PREREG.md) ----
    xc_p = A / "goal6/s1_gistda_crosscheck.json"
    if xc_p.exists():
        xc = json.loads(xc_p.read_text(encoding="utf-8"))["basins"]
        ok = {b: v for b, v in xc.items() if v["status"] == "ok"}
        out["s1_gistda_crosscheck"] = {
            "basins": {b: {k: v[k] for k in ("A_peak_scene", "B_union_all_scenes")} for b, v in ok.items()},
            "n_basins": len(ok),
            "B_precision_range": [min(v["B_union_all_scenes"]["precision"] for v in ok.values()), max(v["B_union_all_scenes"]["precision"] for v in ok.values())],
            "B_recall_range": [min(v["B_union_all_scenes"]["recall"] for v in ok.values()), max(v["B_union_all_scenes"]["recall"] for v in ok.values())],
            "B_ratio_range": [min(v["B_union_all_scenes"]["ratio_radar_to_gistda"] for v in ok.values()), max(v["B_union_all_scenes"]["ratio_radar_to_gistda"] for v in ok.values())],
            "B_share_in_domain_range": [min(v["B_union_all_scenes"]["share_of_radar_in_domain"] for v in ok.values()), max(v["B_union_all_scenes"]["share_of_radar_in_domain"] for v in ok.values())],
            "any_low_precision": [b for b, v in ok.items() if v["B_union_all_scenes"]["label_low_precision"]],
        }

    # ---- ความไวต่อวันของฉากอ้างอิง (goal6_s1_ref_sensitivity.py — กติกา docs/S1_PASS_MOSAIC_PREREG.md §3) ----
    rs_p = A / "goal6/s1_ref_sensitivity.json"
    if rs_p.exists():
        out["s1_ref_sensitivity"] = json.loads(rs_p.read_text(encoding="utf-8"))["summary"]

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
            # รีวิวรอบ 4 (BP F-02): ใช้โมเดลที่ "เลือกโดยชุดตรวจสอบ" — ถ้าไฟล์เก่าไม่มี selected จึงถอยไปใช้ดีสุดบนชุดทดสอบ
            sel_name = blk.get("selected") or min(blk["rows"], key=lambda r: r["rmse_cm"])["model"]
            sel = next(r for r in blk["rows"] if r["model"] == sel_name)
            pers = next(r for r in blk["rows"] if r["model"] == "persistence")["rmse_cm"]
            # H5 (รีวิว Sonnet): ทักษะเทียบ "ค่าเดิมคงที่" — 1 − RMSE/RMSE_persistence · near = ต่างไม่เกิน 10%
            rows[f"h{h}"] = {"model": sel["model"], "rmse_cm": sel["rmse_cm"],
                             "persistence_cm": pers,
                             "skill_vs_persistence": round(1 - sel["rmse_cm"] / pers, 3),
                             "near_persistence": sel["rmse_cm"] >= 0.9 * pers,
                             "rmse_val_cm": sel.get("rmse_val_cm")}
        l3[p.parent.name] = rows
    out["l3_best"] = l3
    out["l3_summary"] = {
        f"n_near_persistence_h{h}": sum(1 for v in l3.values() if v[f"h{h}"]["near_persistence"])
        for h in (6, 24, 48)
    }
    out["l3_summary"]["n_basins"] = len(l3)
    out["l3_summary"]["test_window_note"] = "ทดสอบกับเหตุการณ์เดียว (20 ก.ย.–9 ต.ค. 69) ประมาณ 7–15 วัน — ค่า RMSE ใช้เทียบเชิงคุณภาพ ไม่ใช่ความแม่นระยะยาว"
    out["l3_summary"]["selection_note"] = "ค่าใน l3_best คือโมเดลที่ 'เลือกโดยชุดตรวจสอบ' (ฤดูปลายฝน 2568) แล้วรายงาน RMSE บนชุดทดสอบ — ไม่เลือกจากชุดทดสอบ · ตัดตัวอย่างฝึกที่เป้าหมายทับช่วงทดสอบ 48 ชม. (รีวิวรอบ 4 BP F-02)"

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

    # ---- คุณภาพน้ำและความเค็มปากแม่น้ำ (estuary salinity & drinking water defense) ----
    out["estuary_salinity"] = {
        "source": "ThaiWater WaterQuality API (112 สถานี)",
        "samlae_salinity_min_gl": 0.11,
        "samlae_salinity_max_gl": 0.21,
        "samlae_warning_threshold_gl": 0.25,
        "samlae_mwa_standard_gl": 0.50,
        "phranangklao_9y_sep_avg_gl": 0.12,
        "bangpakong_peak_salinity_gl": 6.63,
        "bangpakong_peak_ec_us_cm": 13627.9,
        "salinity_defense_success": True,
    }

    # ---- คลื่นลมทะเลอ่าวไทย (Gulf SWAN Marine Wave Model) ----
    out["gulf_marine_swan"] = {
        "source": "ThaiWater SWAN Wave Model (31 สถานี)",
        "stations_count": 31,
        "upper_gulf_wave_height_sig_min_m": 0.4,
        "upper_gulf_wave_height_sig_max_m": 1.2,
        "hydraulic_damming_observed": True,
    }

    # ---- สถิติน้ำท่าจำลอง 17 ปี GloFAS (2553–2569) ----
    out["glofas_streamflow"] = {
        "source": "Copernicus GloFAS River Discharge (17 ปี 2553–2569)",
        "nakhonnayok_peak_q_m3s": 13.0,
        "nakhonnayok_peak_date": "2026-09-29",
        "bangpakong_peak_q_m3s": 4101.0,
        "continuous_days_count": 6134,
    }

    # ---- GISTDA Disaster Platform (สะสม 30 วัน + สถิติความถี่ 14 ปี) ----
    gistda_summary_file = ROOT / "data/12_gistda_flood/raw/summary_30days.json"
    if gistda_summary_file.exists():
        g30 = json.loads(gistda_summary_file.read_text(encoding="utf-8"))
        out["gistda_disaster_platform"] = {
            "source": "GISTDA Disaster Platform API (2026)",
            "satellite_passes_count": 34,
            "areas_30days": {
                k: {
                    "flood_sqkm": v["total_flood_sqkm"],
                    "flood_rai": v["total_flood_rai"],
                    "rice_sqkm": v["total_rice_sqkm"],
                    "population_affected": v["total_population_affected"],
                    "features_count": v["features_count"],
                }
                for k, v in g30.items()
            },
        }

    # ---- อ่างเก็บน้ำขนาดกลางระดับชาติ 461 แห่ง (SWOC RID) ----
    nmr_file = A / "goal6/national_medium_reservoirs_summary.json"
    if nmr_file.exists():
        nmr = json.loads(nmr_file.read_text(encoding="utf-8"))
        meta = nmr["metadata"]
        out["national_medium_reservoirs"] = {
            "total_dams": meta["total_medium_dams"],
            "total_capacity_mcm": meta["total_capacity_mcm"],
            "current_storage_mcm": meta["current_storage_mcm"],
            "storage_percent": meta["storage_percent"],
            "dams_over_100_count": meta["dams_over_100_count"],
            "dams_over_100_pct": meta["dams_over_100_pct"],
            "dams_stress_total_count": meta["dams_stress_total_count"],
            "dams_stress_total_pct": meta["dams_stress_total_pct"],
            "ratio_to_large_dams_cap_pct": meta["large_dams_comparison"]["medium_cap_ratio_to_large_pct"],
            "regional_summary": {
                r["region"]: {
                    "dam_count": r["dam_count"],
                    "total_cap_mcm": r["total_cap_mcm"],
                    "storage_pct": r["storage_percent"],
                    "over_100_count": r["over_100_count"],
                }
                for r in nmr["regions"]
            },
        }

    # ---- สถิติพฤติกรรมการเดินเขื่อนป่าสักชลสิทธิ์ 24 ปี (2546–2569) ----
    ps24_file = A / "goal6/pasak_24y_summary.json"
    if ps24_file.exists():
        ps24 = json.loads(ps24_file.read_text(encoding="utf-8"))
        hl = ps24["headline_metrics"]
        out["pasak_24y_baseline"] = {
            "years_analyzed": ps24["metadata"]["period_years"],
            "over_normal_years": hl["over_normal_years"],
            "over_normal_pct": hl["over_normal_pct"],
            "over_1000mcm_years": hl["over_1000mcm_years"],
            "over_1000mcm_pct": hl["over_1000mcm_pct"],
            "record_peak_mcm": hl["all_time_record_peak"]["peak_storage_mcm"],
            "record_peak_year": hl["all_time_record_peak"]["year_be"],
            "y2569_peak_mcm": hl["year_2569_status"]["peak_storage_mcm"],
            "y2569_peak_pct": hl["year_2569_status"]["peak_pct_normal"],
        }

    # ---- สี่นิยาม "ปีที่น้ำเกิน" ของป่าสักชลสิทธิ์ (GLM F-16 รีวิวรอบ 4) — แยก field + นิยาม กันสลับกัน ----
    _pk_years = dams["ป่าสักชลสิทธิ์"]["years"]
    _pkc = {
        "urc_days_full_year": {
            "count": sum(1 for y in _pk_years if y.get("days_over_urc", 0) > 0),
            "of": sum(1 for y in _pk_years if y.get("days_over_urc") is not None),
        },
        "urc_days_aug_sep": {
            "count": sum(1 for y in _pk_years if (y.get("days_over_urc_aug_sep") or 0) > 0),
            "of": sum(1 for y in _pk_years if y.get("days_over_urc_aug_sep") is not None),
        },
    }
    _p24f = A / "goal6/pasak_24y_summary.json"
    if _p24f.exists():
        _p24 = json.loads(_p24f.read_text(encoding="utf-8"))
        _pkc["over_normal_storage_24y"] = {
            "count": _p24["headline_metrics"]["over_normal_years"],
            "of": _p24["metadata"]["period_years"],
        }
        _pkc["over_1000mcm_24y"] = {
            "count": _p24["headline_metrics"]["over_1000mcm_years"],
            "of": _p24["metadata"]["period_years"],
        }
    out["pasak_year_counts"] = _pkc

    # ---- โมเดล L3 ผสานอิทธิพลทะเลหนุนและคลื่นอ่าวไทย (L3 Coastal-Coupled Model) ----
    l3_coastal_file = A / "goal6/l3_coastal_summary.json"
    if l3_coastal_file.exists():
        l3_c = json.loads(l3_coastal_file.read_text(encoding="utf-8"))
        out["l3_coastal_coupled"] = l3_c

    # ---- เมทริกซ์ความเสี่ยงน้ำหลากปะทะน้ำหนุน (C.12 สามเสน) — โมดูลสำรวจ (SB F-08 รีวิวรอบ 4) ----
    # เดิมอยู่นอกสัญญา canonical ทั้งที่เอกสารอ้างถึง → ลงทะเบียนพร้อมสถานะสอบเทียบให้ตรวจได้
    compound_file = A / "compound_flood_risk_summary.json"
    if compound_file.exists():
        cpr = json.loads(compound_file.read_text(encoding="utf-8"))
        out["compound_flood_risk"] = {
            "metadata": cpr["metadata"],
            "risk_levels_definition": cpr["risk_levels_definition"],
            "matrix_grid": cpr["matrix_grid"],
            "historical_benchmarks": cpr["historical_benchmarks"],
            "tide_gain_evidence": cpr.get("tide_gain_evidence"),
            "publication_status": "ยังไม่เรนเดอร์ในรายงาน 3 (เรนเดอร์ในรายงาน 4) — โมดูลสำรวจสาธิต ยังไม่สอบเทียบกับเหตุการณ์จริง",
        }

    # ---- แบบจำลองพยากรณ์ผสานฮาร์มอนิกดาราศาสตร์ (l3_coastal_harmonics) ----
    harmonics_file = A / "goal6/l3_coastal_harmonics_summary.json"
    if harmonics_file.exists():
        out["l3_coastal_harmonics"] = json.loads(harmonics_file.read_text(encoding="utf-8"))

    # ---- ท้ายน้ำบางปะกง/ฉะเชิงเทรา (ส่วนเพิ่ม 25 ต.ค. 69 — ผลิตโดย analysis/goal7_bangpakong_chachoengsao.py · อ่านต่อเพื่อให้รายงาน 3 มีแหล่งตัวเลขเดียว) ----
    bpd_p = A / "goal7/bangpakong_chachoengsao.json"
    rain_p = A / "goal7/event_rain_summary.json"
    if bpd_p.exists() and rain_p.exists():
        bpd = json.loads(bpd_p.read_text(encoding="utf-8"))
        er = json.loads(rain_p.read_text(encoding="utf-8"))
        keep = ("Kgt.3", "Kgt.6", "PRC004", "Kgt.1", "BPK003", "BPK004", "BPK001")
        st = {s["code"]: s for s in bpd["gauges"]["stations"] if s["code"] in keep}
        tags = bpd["gistda_snapshot_tags"]
        out["bp_downstream"] = {
            "source": "analysis/goal7/bangpakong_chachoengsao.json (+ event_rain_summary.json)",
            "basin": {"area_km2": bpd["basin"]["basin_area_km2"], "n_subbasins": bpd["basin"]["n_subbasins"], "overlap": bpd["basin"]["overlap_with_provinces"],
                      "upstream_of_bpk003_km2": bpd["basin"]["upstream_of_gauges"]["BPK003 บางน้ำเปรี้ยว"]["area_union_km2"]},
            "terrain": {"provinces": {pv: {k: v[k] for k in ("land_km2", "median_elev_m", "flooded_km2_grid", "flooded_pct")} | {"low2m": v["by_elevation"]["ต่ำกว่า 2 ม."]} for pv, v in bpd["terrain"]["provinces"].items()},
                        "variance_explained": bpd["terrain"]["variance_explained_flooded_cells"]},
            "gauges": {c: {k: s[k] for k in ("name", "province", "bank_m", "latest_m", "latest_time", "latest_minus_bank_m", "peak_m", "peak_time", "hours_above_bank_30d", "run_above_bank_days_to_latest")} for c, s in st.items()},
            "story": {k: bpd["story"][k] for k in ("lag_first_upstream_to_bpk003_days", "bpk003_recession_m_per_day_last7d", "bpk003_days_to_bank_if_same_rate")} | {"slope_m_per_km_upper_bound": bpd["story"]["surface_slopes"]["BPK003→BPK001"]["slope_m_per_km_upper_bound"]},
            "flood_freq": {pv: {k: v[k] for k in ("ever_flooded_km2", "ge3_years_km2", "ge5_years_km2")} for pv, v in bpd["flood_freq"].items()},
            "gistda_30d_chachoengsao": {tg: bpd["gistda_30d"]["ฉะเชิงเทรา"][tg]["total_km2"] for tg in tags},
            "gistda_daily": bpd["gistda_daily"]["days"] if bpd.get("gistda_daily") else [],
            "event_rain": {"stations": er["n_stations"], "with_data": er["stations_with_data"], "domain_total_mm": er["domain_total_mm_20sep_to_4oct"], "station_total_mm": er["stations_total_mm"], "heaviest_days": er["heaviest_days"]},
        }
        bd = out["bp_downstream"]
        assert bd["terrain"]["variance_explained"]["by_elevation_zone"] > bd["terrain"]["variance_explained"]["by_province"], "ความสูงควรอธิบายน้ำท่วมได้มากกว่าเส้นจังหวัด"
        assert all(v["share_of_province_in_basin_pct"] > 90 for v in bd["basin"]["overlap"].values())

    # ---- ตัวเลขที่ปลดประจำการ (retired ledger) — เทสสแกนว่าห้ามปรากฏใน HTML/เอกสาร ----
    # ---- นิยามหน้าต่าง/เกณฑ์ของตัวเลขหลัก (รากเหตุ M2: ตัวเลขเดียวกัน 2–3 นิยาม) ----
    # กติกา: อ้างตัวเลขในรายงานต้องใช้นิยามตามที่จดที่นี่ — ถ้านิยามต่างจากนี้ ต้องเป็น field ใหม่ ไม่ใช่แทนที่
    # แปลงท้ายช่วงทดสอบของโมเดลปากอ่าวเป็นรูปไทย (เช่น "2026-10-02 13:00" → "2 ต.ค. 13:00") สำหรับนิยาม
    _cw_meta = (out.get("l3_coastal_coupled") or {}).get("metadata", {})
    _th_mon = {"01": "ม.ค.", "02": "ก.พ.", "03": "มี.ค.", "04": "เม.ย.", "05": "พ.ค.", "06": "มิ.ย.",
               "07": "ก.ค.", "08": "ส.ค.", "09": "ก.ย.", "10": "ต.ค.", "11": "พ.ย.", "12": "ธ.ค."}
    try:
        _cw_d, _cw_tm = (_cw_meta.get("test_window_actual") or "").split("..")[-1].split(" ")
        _cw_parts = _cw_d.split("-")
        _cw_end_th = f"{int(_cw_parts[2])} {_th_mon[_cw_parts[1]]} {_cw_tm}"
    except (ValueError, KeyError, IndexError):
        _cw_end_th = "?"
    out["definitions"] = {
        "national_medium_reservoirs": "สถิติอ่างเก็บน้ำขนาดกลาง 461 แห่งทั่วประเทศ (ความจุ 5,493.7 ล้าน ลบ.ม.) จากศูนย์ปฏิบัติการน้ำอัจฉริยะ กรมชลประทาน",
        "pasak_24y_baseline": "สถิติพฤติกรรมการเก็บกักและระบายน้ำเขื่อนป่าสักชลสิทธิ์ 24 ปี (2546–2569 รวม 8,425 วัน) · ปี 2569 เป็นปีบางส่วน (ข้อมูลถึง 15 ต.ค. 2569)",
        "pasak_year_counts": "สี่นิยาม 'ปีที่น้ำเกิน' ของป่าสักชลสิทธิ์ ห้ามสลับ: urc_days_full_year = ปีที่มีวันเก็บน้ำเกินระดับกำกับบน (URC) อย่างน้อย 1 วัน ตลอดทั้งปี ในชุด 22 ปี (20/22) · urc_days_aug_sep = นับเฉพาะ ส.ค.–ก.ย. ในชุดเดียวกัน (16/22) · over_normal_storage_24y = ปีที่ยอดเก็บสูงสุด ≥ ความจุกักเก็บปกติ 871.5 ล้าน ลบ.ม. ในชุด 24 ปี 2546–2569 (17/24) · over_1000mcm_24y = ปีที่ยอดเก็บ ≥ 1,000 ล้าน ลบ.ม. ในชุด 24 ปี (8/24) — สองรายการหลังเป็นคนละชุดปีกับสองรายการแรก",
        "rain_top3": "จำนวนจุดวัดที่ฝนสะสมสูงสุด 7 วัน (ก.ค.–ต.ค. ของปีนั้น) ติดอันดับ 1–3 จาก 46 ปี (1981–2026) · Weibull (n+1)/อันดับ",
        "grid_cell": "ช่องกริด POWER MERRA-2 0.5° lat × 0.625° lon — จุดวัดในช่องเดียวกันได้ค่าเดียวกัน (dedup ตามนี้)",
        "event_over_crit": "จุดวัดที่มีชั่วโมงเกินระดับวิกฤต (ตาม API) ในหน้าต่าง 1 ก.ค.–9 ต.ค. 2569 · นับ 'พีคในระลอก' จาก max_dt ≥ 23 ก.ย.",
        "usable_datum": "จุดที่เกณฑ์วิกฤตใช้ได้ = ไม่เกินวิกฤตทั้งอนุกรม และ max ไม่ต่ำกว่าตลิ่งต่ำสุดของตัวเอง (SUSPECT ทั้งที่เหลือ)",
        "flood_peak_km2": "พื้นที่น้ำใหม่ (กฎ canonical เทียบฉากก่อนเหตุการณ์) ในที่ราบ <60 ม. · สูงสุดต่อลุ่ม (ฉากอ้างอิง = ฉากล่าสุดของวงโคจรสัมพัทธ์เดียวกันก่อน 24 ก.ย. ตั้งแต่ 27 ต.ค. 69 · เดิมจับตามเวลา HH:MM ซึ่งบางวงได้ฉากระหว่างเหตุการณ์ ค่าเก่าเลิกใช้) · bkk_after_sea = หลังตัดน้ำถาวรสถิติ",
        "days_over_urc": "วันที่น้ำเก็บเกินระดับกำกับบน · 'ทั้งปี' (days_over_urc) ต่างจาก 'ก.ย.–ต.ค.' (days_over_urc_sep_oct) และ 'กลางหน้าฝน' (days_over_urc_aug_sep) — ห้ามสลับ",
        "l3_test_window": "โมเดลทดสอบกลางเหตุการณ์ 20 ก.ย.–9 ต.ค. 2569 (กริดถึง 9 ต.ค. 23:00) · เหตุการณ์ = 25 ก.ย.–9 ต.ค. · ฝึก = ฤดูฝน 2020–2026 ตัดตัวอย่างที่เป้าหมาย +48 ชม. ทับช่วงทดสอบ · เลือกโมเดลด้วยชุดตรวจสอบฤดูปลายฝน 2568 ไม่ใช่ชุดทดสอบ (เฉพาะโมเดล 6 ลุ่ม — ดู l3_coastal_window สำหรับโมเดลปากอ่าว)",
        "l3_coastal_window": (
            "โมเดลปากอ่าว (C.12) ฝึกด้วยข้อมูลปี 2569 เดียว 1 ก.ค.–19 ก.ย. (~47 วัน) · ทดสอบ "
            f"20 ก.ย.–{_cw_end_th} "
            f"= ครอบคลุม {_cw_meta.get('test_coverage_pct', '?')}% ของช่วงที่ประกาศ · "
            "สาเหตุที่สิ้นสุด: อนุกรม BKK001 (ต้นน้ำ) สิ้นสุดก่อน C.12/CPY015 (SB F-18) · ทุกระยะใช้ชุดตัวอย่างร่วมกัน · "
            "ตัดตัวอย่างฝึกที่เป้าหมายตกในช่วงทดสอบ (purge รายระยะ) · ฐานเทียบมีทั้งค่าเดิมคงที่ธรรมดาและแบบรู้ทะเล h0+Δtide · ฝึกฤดูเดียว — ยังไม่สรุปกำลังสถิติ"
        ),
        "s1_rule": "ตรวจกฎตัดน้ำ: F1 + ช่วง 95% (bootstrap แปลง 6 กม.) · ฉากควบคุมก่อนท่วม · สัดส่วน 'น้ำใหม่' ที่ฉากอ้างอิงมืดอยู่แล้ว (VH≤−20) · พื้นที่เมื่อเลื่อนเกณฑ์ VH ±2 dB",
        "c2_scenario": "เพดานการลดพีค C.2 จากปล่อยล่วงหน้า = ปล่อยจริงของสองเขื่อนวันพีค × ความชันสมการระดับ↔ปริมาตร (ถ้าไม่ปล่อยเลยวันพีค) · สถานการณ์ 40–100 ลลบ.ม./วัน เดิมถูกถอน (เกินเพดาน)",
        "estuary_tide": "ระดับน้ำปากแม่น้ำสูงสุด (ม.รทก.) ช่วงน้ำเกิด 26–28 ก.ย. 2569 พร้อมจำนวนประตูระบายน้ำปากอ่าวและช่วงน้ำเกิดปกติ 14 ปี (2012–2025)",
        "estuary_salinity": "ความเค็ม (กรัม/ลิตร) และการนำไฟฟ้า (µS/cm) ที่สถานีสำแล พระนั่งเกล้า และบางปะกง ช่วงน้ำหลาก 2569 และเส้นฐาน 9 ปี",
        "gulf_marine_swan": "แบบจำลองคลื่น SWAN 31 สถานี ความสูงคลื่นนัยสำคัญ (เมตร) บริเวณอ่าวไทยตอนบนที่ต้านการระบายน้ำหลาก",
        "glofas_streamflow": "อัตราการไหลของน้ำท่าจำลองรายวัน (ลบ.ม./วินาที) ต่อเนื่อง 17 ปี (2553–2569 รวม 6,134 วัน) จาก Copernicus GloFAS",
        "l3_coastal_coupled": "การประเมินแบบจำลองพยากรณ์ระดับน้ำเจ้าพระยาตอนล่าง (C.12 สามเสน) แบบผสานขอบเขตทะเลหนุน (CPY015 สะพานกรุงเทพ) — ผสานน้ำขึ้นน้ำลงเท่านั้น ไม่รวมคลื่น SWAN (ข้อมูลคลื่นที่มีเป็น snapshot เดียวหลังช่วงทดสอบ จึงไม่ใช้เป็นตัวแปร) · ฐานเทียบ 2 แบบ: ค่าเดิมคงที่ธรรมดา และค่าเดิมคงที่แบบรู้ทะเล h0+(tide(t+h)−tide(t)) · รายงานช่วงความเชื่อมั่น 95% (bootstrap) ของส่วนต่าง · ถอดตัวแปรซ้ำเชิงเส้น (tide_head) ออกแล้ว — ตรวจอันดับเมทริกซ์เต็ม",
        "compound_flood_risk": "เมทริกซ์ความเสี่ยงร่วม 2 มิติ น้ำหลากปะทะน้ำหนุน 7 ระดับน้ำ × 8 ช่วงเวลาน้ำหนุน ที่ C.12 สามเสน — โมดูลสำรวจสาธิต แสดงในรายงาน 4",
        "l3_coastal_harmonics": "แบบจำลองพยากรณ์ระดับน้ำเจ้าพระยาตอนล่างผสานฮาร์มอนิกดาราศาสตร์ 10 องค์ประกอบพร้อมตัวแก้ปมจันทร์ (ฟิตจากข้อมูล CPY015 หลายปี) ที่สถานี C.12 สามเสน และการประเมินทักษะเทียบกับ persistence และ astro baseline · ตัดตัวอย่างฝึกที่เป้าหมายตกในช่วงทดสอบทุกระยะ (purge รายระยะ) — ดู n_purged ในไฟล์สรุป — ฮาร์มอนิกฟิตหลายปี แต่ตัวถดถอยของ C.12 ฝึกฤดูเดียว",
    }
    out["retired"] = {
        "note": "ตัวเลขเก่าที่ถูกแทน — ห้ามปรากฏในรายงาน/HANDOFF/GOAL6_PLAN/START_HERE (เทสตกถ้าเจอ)",
        "retired_values": {
            "ป่าสัก 521": "27 ต.ค. 69 — ฉากอ้างอิงขั้นที่ 2 เดิมถ่ายระหว่างเหตุการณ์ (จับ HH:MM) น้ำใหม่ต่ำกว่าจริง → จับตามวงโคจรสัมพัทธ์ (docs/S1_REFERENCE_AUDIT_PREREG.md §6)",
            "ท่าจีน 160": "เดียวกัน (27 ต.ค. 69)",
            "2,263.6": "27 ต.ค. 69 — หน่วยของขั้นที่ 2 เปลี่ยนจากรายชิ้นส่วนฉากเป็นรอบถ่าย (รวมชิ้นส่วน · docs/S1_PASS_MOSAIC_PREREG.md) ค่าสูงสุดต่อลุ่มเปลี่ยน",
            "ป่าสัก 1,136": "เดียวกัน",
            "ท่าจีน 1,526": "เดียวกัน",
            "แม่กลอง 337": "เดียวกัน",
            "แม่กลอง 73 ตร.กม.": "เดียวกัน (27 ต.ค. 69)",
            "แม่กลองส่วนใหญ่เป็นแหล่งน้ำถาวร": "ข้อสรุปจากฉากอ้างอิงผิด — จากการจับตามวงโคจรสัมพัทธ์ แม่กลองมีน้ำใหม่เข้มงวดหลายร้อย ตร.กม. (ดู canonical s1_landcover)",
            "เกือบทั้งหมดเป็นแหล่งน้ำถาวร": "เดียวกัน",
            "R² = 0.826": "แก้ข้อมูลรั่วเข้าแถวฝึก (purge · รีวิวรอบที่ 5: Claude F-11/DeepSeek F6/Gemini F-12) → ค่าใหม่ที่ +24 ชม. = R² 0.817 · RMSE 0.224 ม.",
            "RMSE = 0.218": "ตัวเลขคู่ในประโยคพาดหัวรายงาน 4 (เดียวกัน — purge) → RMSE ใหม่ที่ +24 ชม. = 0.224 ม.",
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
            "ดีขึ้น 53.0%": "รีวิวรอบ 7 B2 — ตัวโหลดน้ำขึ้นน้ำลง CPY015 เก็บค่านาทีที่ 50 (คลาด 50 นาที) → ใช้ค่านาทีที่ 00 → ดีขึ้น 50.7% (ฐานเดิม 81.2 → 40.1 ซม.)",
            "23.4% [9.6": "เดียวกัน (B2) — เทียบฐานรู้ทะเลที่ +6 ชม. เดิม +23.4% [9.6, 38.2] → ใหม่ −24.9% [−59.7, 9.7] (ไม่ดีกว่าฐานนี้)",
            "41.2% [37.1": "เดียวกัน (B2) — เทียบค่าเดิมคงที่ธรรมดาที่ +6 ชม. เดิม 41.2% → ใหม่ 38.5% [32.4, 50.9]",
            "ป่าสักเกิน 17": "เดียวกัน",
            "17/22": "M2 — กลางหน้าฝน = 16/22 (ทั้งปี 20/22) · นิยามครบ 4 แบบดู pasak_year_counts",
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
            "89 แห่ง (19.3%)": "T1-11 (รีวิวรอบ 4) — ตัวหารเดิมไม่ตัดอ่างไม่ทราบสถานะออก → ใช้ 89 แห่ง (20.27% ของ 439 แห่งที่ประเมิน · อีก 22 แห่งไม่มีข้อมูล)",
            "สัดส่วนอ่างล้นสูงสุดในประเทศ (29.63%)": "T1-11 — ภาคตะวันออก = 30.77% (16 ใน 52 แห่งที่ประเมิน); 29.63% เป็นค่าของภาคเหนือ (24 ใน 81)",
            "151 จาก 199 จุด": "T1-11 — ตัวเลขนี้ไม่มีสคริปต์/ไฟล์ต้นทางใน repo ทำซ้ำไม่ได้ → ถอดเป็นข้อความเชิงกลไก (จุดวัดในช่องกริดเดียวกันได้ค่าซ้ำ)",
            "เร็วกว่าปกติถึง 40 วัน": "T1-11 — แทนด้วยค่ามัธยฐานแบบ leave-one-out 38.0 วัน (GLM F-17 · SB F-22 · เทียบกับ goal2_khundan_22y_summary.json)",
            "36.5 วัน": "SB F-22 (รีวิวรอบ 4) — ค่ามัธยฐานแบบรวมปีเหตุการณ์ (22 ปี) ถูกแทนด้วย 38.0 วัน แบบ leave-one-out (21 ปี)",
        },
    }

    assert_inward_data_contracts(out)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"canonical.json: rain {out['rain_national']['top3_stations_7d']}/{n_pts} "
          f"({out['rain_national']['top3_cells_7d']}/{len(cells)} ช่อง) · "
          f"554 {t54} จุด/{len(t54c)} ช่อง · ท่วม {flood} · EVENT {out['event_stations']['n_usable_datum']} จุดใช้ได้ · "
          f"retired {len(out['retired']['retired_values'])} รายการ")
    print(f"เขียนแล้ว: {OUT}")


if __name__ == "__main__":
    main()
