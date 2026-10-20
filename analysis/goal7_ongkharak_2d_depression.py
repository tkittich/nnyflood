#!/usr/bin/env python3
"""analysis/goal7_ongkharak_2d_depression.py — เส้นความสัมพันธ์ระดับ–พื้นที่–ปริมาตรของแอ่ง อ.องครักษ์ (แบบจำลองถังเติมน้ำ) บนแบบจำลองความสูง 3 ชุด

เปลี่ยนเมื่อ 20 ต.ค. 69 (R7-21): ชุดหลัก = **FABDEM ที่ปรับด้วย DEM 5 ม. (DEMPro)** แทน Copernicus ดิบ — เพราะ DEMPro ใกล้เส้นดินธรรมชาติใน EIA ที่สุด (ต่าง ~0.4 ม.)
ขณะที่ Copernicus/FABDEM ดิบสูงกว่าพื้นจริงในที่ราบต่ำ 1.2–1.8 ม. (ดู analysis/goal7_dem_bias_correction.py · ตารางส่วนต่างตามความสูงจาก 18 หน้าต่าง DEMPro ในที่ราบเจ้าพระยาตอนล่าง)
องครักษ์อยู่นอกหน้าต่าง DEMPro จึงใช้ตารางปรับที่เรียนจากหน้าต่างอื่น (ความไม่แน่นอนราว ±0.7–1.0 ม. ตาม SD ของส่วนต่างรายหน้าต่าง) — ผลจึงรายงานคู่กับชุดดิบเป็น "ความไวต่อชุด DEM" (dem_sensitivity)

คำถามวิจัย:
1. เส้นความสัมพันธ์ระดับ–พื้นที่–ปริมาตร 2 มิติ (Stage-Area-Volume) ของ อ.องครักษ์ เป็นอย่างไร?
2. ที่ระดับน้ำสังเกตจริง (+2.35 ม.รทก. ณ สถานี TNy10) แบบจำลองถังเติมน้ำให้พื้นที่เท่าไร เทียบพื้นที่ที่เรดาร์เห็น?
3. ระดับที่ทำให้พื้นที่ถังเท่าที่เรดาร์เห็น ต่างจากเกจเท่าไร และต่างกันแค่ไหนตามชุด DEM?

แหล่งข้อมูล: data/13_sentinel1_copernicus/derived/dem_30m.npy (Copernicus DSM) · data/08_dem_topography/fabdem (FABDEM) · analysis/goal7/dem_bias_correction.json (ตารางปรับ) · มาสก์อำเภอและมาสก์น้ำท่วมจาก data/13_sentinel1_copernicus/derived
ข้อจำกัด: ถังเติมน้ำถือผิวน้ำราบเสมอกันและไม่มีคันกั้น/ประตู/ปั๊ม — ไม่ใช่แบบจำลองชลศาสตร์ · ไม่รู้ระดับพื้นจริงของอำเภอ (ไม่มีหน้าต่าง DEMPro ในอำเภอ)

รัน: python analysis/goal7_ongkharak_2d_depression.py
ผลลัพธ์: analysis/goal7/ongkharak_2d_depression_summary.json (และเขียนลง canonical.json → ongkharak_2d_depression)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_dem_bias_correction as bc  # noqa: E402  (reuse-first: ตารางปรับและฟังก์ชันปรับ)
import goal7_ongkharak_connected_fill as cf  # noqa: E402  (reuse-first: FABDEM บนกริดเรดาร์)

DEM_PATH = ROOT / "data/13_sentinel1_copernicus/derived/dem_30m.npy"
MASK_ONG_PATH = ROOT / "data/13_sentinel1_copernicus/derived/mask_district_อำเภอองครักษ์.npy"
OUT_JSON = ROOT / "analysis/goal7/ongkharak_2d_depression_summary.json"
CANONICAL_PATH = ROOT / "analysis/goal7/canonical.json"
BIAS_JSON = ROOT / "analysis/goal7/dem_bias_correction.json"
SAR_MASKS = {
    "peak_27sep": ROOT / "data/13_sentinel1_copernicus/derived/flood_peak_27sep1828.npy",
    "oct2_validated": ROOT / "data/13_sentinel1_copernicus/derived/flood_2oct_validated.npy",
}
OBSERVED_STAGE_MSL_M = 2.35  # TNy10 17 ต.ค. 2569 — ค่าเดียวที่ทุกรายงานต้องอ้าง
CELL_KM2 = 900.0 / 1e6
PRIMARY = "fabdem_corrected"
LABELS = {"copernicus_raw": "Copernicus GLO-30 ดิบ (ผิวสูงสุด)", "fabdem_raw": "FABDEM ดิบ (ดินเปล่า)", "fabdem_corrected": "FABDEM ปรับด้วย DEM 5 ม. (ชุดหลัก)"}
STAGES = np.arange(0.0, 4.6, 0.1)


def load_dems(mask: np.ndarray) -> dict[str, np.ndarray]:
    table = json.loads(BIAS_JSON.read_text(encoding="utf-8"))["bias_table_by_fabdem_height"]
    fab = cf.fabdem_on_grid()
    cor = bc.correct(np.where(np.isnan(fab), 99.0, fab), table)
    cor[np.isnan(fab)] = np.nan
    return {"copernicus_raw": np.load(DEM_PATH), "fabdem_raw": fab, "fabdem_corrected": cor}


def analyze(dem: np.ndarray, mask: np.ndarray) -> dict:
    """เส้นระดับ–พื้นที่–ปริมาตรของอำเภอ + จุดสำคัญ + ปรับระดับให้ได้พื้นที่เท่าเรดาร์"""
    valid = mask & ~np.isnan(dem) & (dem >= -3.0)
    vals = dem[valid]
    total_km2 = float(valid.sum()) * CELL_KM2

    def row_at(h: float) -> dict:
        sub = vals[vals <= h]
        km2 = float(len(sub)) * CELL_KM2
        mean_d = float(np.mean(h - sub)) if len(sub) else 0.0
        return {"stage_msl_m": h, "inundated_area_km2": round(km2, 2), "inundated_share_pct": round(km2 / total_km2 * 100.0, 1), "mean_depth_m": round(mean_d, 2),
                "max_depth_m": round(float(h - sub.min()) if len(sub) else 0.0, 2), "storage_volume_mcm": round(km2 * mean_d, 2)}
    curve = [row_at(float(round(h, 2))) for h in STAGES]
    median = float(np.median(vals))
    sar_cal = {}
    for key, path in SAR_MASKS.items():
        sar = np.load(path).astype(bool)
        if sar.shape != mask.shape:
            continue
        s = sar & valid
        sar_km2 = float(s.sum()) * CELL_KM2
        best = None
        for h in np.arange(-2.0, 5.0001, 0.01):
            bt = valid & (dem <= h)
            a = float(bt.sum()) * CELL_KM2
            if best is None or abs(a - sar_km2) < abs(best[1] - sar_km2):
                best = (float(round(h, 2)), a, bt)
        h_eff, _, bt = best
        inter, union = float((bt & s).sum()), float((bt | s).sum())
        sar_cal[key] = {"sar_area_km2": round(sar_km2, 1), "sar_share_pct": round(100.0 * sar_km2 / total_km2, 1), "effective_stage_msl_m": h_eff, "offset_vs_gauge_m": round(h_eff - OBSERVED_STAGE_MSL_M, 2),
                        "iou": round(inter / union, 2) if union else None, "precision": round(inter / float(bt.sum()), 2) if bt.sum() else None, "recall": round(inter / float(s.sum()), 2) if s.sum() else None,
                        "gauge_stage_area_km2": round(row_at(OBSERVED_STAGE_MSL_M)["inundated_area_km2"], 1)}
    return {"total_area_km2": round(total_km2, 2), "elevation_stats_m": {"min": round(float(vals.min()), 2), "median": round(median, 2), "mean": round(float(vals.mean()), 2), "max": round(float(vals.max()), 2)},
            "curve": curve, "row_at": row_at, "median": median, "sar_calibration": sar_cal}


def analyze_depression():
    mask = np.load(MASK_ONG_PATH)
    dems = load_dems(mask)
    res = {k: analyze(d, mask) for k, d in dems.items()}
    prim = res[PRIMARY]
    row_at = prim["row_at"]
    curve = prim["curve"]
    stage_obs = row_at(OBSERVED_STAGE_MSL_M)             # ประเมินที่ระดับสังเกตจริงพอดี (ไม่ปัดขั้น 0.1 ม. — รีวิวรอบ 6 A9)
    stage_bankfull = next(c for c in curve if abs(c["stage_msl_m"] - 2.50) < 0.05)
    stage_med = row_at(round(prim["median"], 1))         # ระดับมัธยฐานของภูมิประเทศ (ไม่ใช่ระดับสันทางหลวง 305 ที่วัดได้)
    sar2 = prim["sar_calibration"].get("oct2_validated", {})
    rel = "มากกว่า" if stage_obs["inundated_area_km2"] > sar2.get("sar_area_km2", 0) else "น้อยกว่า"
    ratio = (max(stage_obs["inundated_area_km2"], sar2.get("sar_area_km2", 1)) / max(min(stage_obs["inundated_area_km2"], sar2.get("sar_area_km2", 1)), 0.1))
    sens = {}
    for k, r in res.items():
        sens[k] = {"label": LABELS[k], "median_m": r["elevation_stats_m"]["median"], "area_at_gauge_km2": round(r["row_at"](OBSERVED_STAGE_MSL_M)["inundated_area_km2"], 1),
                   "area_at_gauge_share_pct": round(r["row_at"](OBSERVED_STAGE_MSL_M)["inundated_share_pct"], 1),
                   "sar_fit": {kk: {x: v[x] for x in ("sar_area_km2", "effective_stage_msl_m", "offset_vs_gauge_m", "iou")} for kk, v in r["sar_calibration"].items()}}
    summary = {
        "sar_calibration": prim["sar_calibration"],
        "title": "เส้นความสัมพันธ์ระดับ–พื้นที่–ปริมาตร 2 มิติของแอ่ง อ.องครักษ์ (ชุดหลัก: FABDEM ปรับด้วย DEM 5 ม.) พร้อมความไวต่อชุด DEM",
        "district": "อำเภอองครักษ์ จังหวัดนครนายก",
        "dem_source": {"primary": PRIMARY, "label": LABELS[PRIMARY], "note": "ตารางปรับเรียนจากหน้าต่าง DEMPro 18 จังหวัด (analysis/goal7_dem_bias_correction.py) — องครักษ์อยู่นอกหน้าต่าง จึงมีความไม่แน่นอน ~±0.7–1.0 ม. · เทียบชุดดิบใน dem_sensitivity"},
        "dem_sensitivity": sens,
        "observed_stage_msl_m": OBSERVED_STAGE_MSL_M,
        "total_area_km2": prim["total_area_km2"],
        "elevation_stats_m": prim["elevation_stats_m"],
        "critical_thresholds": {
            "observed_oct2026": {
                "stage_msl_m": stage_obs["stage_msl_m"], "area_km2": stage_obs["inundated_area_km2"], "share_pct": stage_obs["inundated_share_pct"], "volume_mcm": stage_obs["storage_volume_mcm"], "mean_depth_m": stage_obs["mean_depth_m"],
                "sar_area_km2": sar2.get("sar_area_km2"), "relation_to_sar": rel, "ratio_to_sar": round(ratio, 1),
                "description": f"ระดับน้ำจริงในคลองแม่น้ำใน (TNy10): แบบจำลองถังเติมน้ำที่ระดับนี้ได้พื้นที่ลุ่มต่ำราว {stage_obs['inundated_area_km2']:.1f} ตร.กม. ปริมาตร ~{stage_obs['storage_volume_mcm']:.1f} ล้าน ลบ.ม. "
                               f"({rel}พื้นที่ที่เรดาร์เห็น {sar2.get('sar_area_km2', 0):.0f} ตร.กม. ราว {ratio:.1f} เท่า — น้ำในคลองสูงเหนือพื้นทุ่งได้โดยไม่ท่วมทุ่งทั้งหมด เพราะมีคันคลอง ประตู และระบบระบายคุมอยู่)"},
            "bankfull_threshold": {
                "stage_msl_m": stage_bankfull["stage_msl_m"], "area_km2": stage_bankfull["inundated_area_km2"], "volume_mcm": stage_bankfull["storage_volume_mcm"], "mean_depth_m": stage_bankfull["mean_depth_m"],
                "description": f"ระดับน้ำล้นตลิ่งลำคลองธรรมชาติ (สมมติ): น้ำเริ่มแผ่กว้างเข้าสู่ทุ่งนา {stage_bankfull['inundated_area_km2']:.1f} ตร.กม. ปริมาตรน้ำ ~{stage_bankfull['storage_volume_mcm']:.1f} ล้าน ลบ.ม."},
            "route305_overtopping": {
                "stage_msl_m": stage_med["stage_msl_m"], "area_km2": stage_med["inundated_area_km2"], "volume_mcm": stage_med["storage_volume_mcm"], "mean_depth_m": stage_med["mean_depth_m"],
                "description": f"ระดับมัธยฐานของภูมิประเทศ ไม่ใช่ระดับสันถนนรังสิต–นครนายก (ทล.305) ที่วัดได้: น้ำท่วมครอบคลุมราว {stage_med['inundated_area_km2']:.1f} ตร.กม. ({stage_med['inundated_share_pct']:.1f}% ของอำเภอ) ปริมาตร ~{stage_med['storage_volume_mcm']:.1f} ล้าน ลบ.ม."},
        },
        "hypsometric_curve": curve,
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ บันทึกผลลง {OUT_JSON.name}")
    for k, s in sens.items():
        print(" ", k, "มัธยฐาน", s["median_m"], "พื้นที่ที่เกจ", s["area_at_gauge_km2"], {kk: (v["effective_stage_msl_m"], v["offset_vs_gauge_m"], v["iou"]) for kk, v in s["sar_fit"].items()})
    if CANONICAL_PATH.exists():
        cdata = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
        cdata["ongkharak_2d_depression"] = summary
        CANONICAL_PATH.write_text(json.dumps(cdata, ensure_ascii=False, indent=1), encoding="utf-8")
        print("✅ อัปเดต ongkharak_2d_depression ลง canonical.json")
    return summary


if __name__ == "__main__":
    analyze_depression()
