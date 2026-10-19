#!/usr/bin/env python3
"""analysis/goal7_ongkharak_2d_depression.py — การจำลองความจุแอ่งก้นกระทะ 2 มิติและเส้นชั้นความลึกน้ำท่วมองครักษ์บน DEM 30m

คำถามวิจัย:
1. ลักษณะภูมิประเทศ 2 มิติของ อ.องครักษ์ มีเส้นชั้นความจุแอ่ง (Stage-Area-Volume Hypsometric Curve) อย่างไร?
2. ที่ระดับน้ำสังเกตการณ์จริง (+2.35 ม.รทก. ณ สถานี TNy10) พื้นที่น้ำท่วมขังและปริมาตรกักเก็บสอดคล้องกับภาพดาวเทียม Sentinel-1 เพียงใด?
3. พื้นที่และปริมาตรที่ระดับมัธยฐานของภูมิประเทศ (+3.20 ม.รทก.) ซึ่งใช้เป็นระดับอ้างอิงสมมติของทล.305 (ระดับสันถนนจริงยังไม่มีข้อมูล)

แหล่งข้อมูล:
- data/13_sentinel1_copernicus/derived/dem_30m.npy (Copernicus DEM 30m)
- data/13_sentinel1_copernicus/derived/mask_district_อำเภอองครักษ์.npy
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DEM_PATH = ROOT / "data/13_sentinel1_copernicus/derived/dem_30m.npy"
MASK_ONG_PATH = ROOT / "data/13_sentinel1_copernicus/derived/mask_district_อำเภอองครักษ์.npy"
OUT_JSON = ROOT / "analysis/goal7/ongkharak_2d_depression_summary.json"
CANONICAL_PATH = ROOT / "analysis/goal7/canonical.json"
SAR_MASKS = {
    "peak_27sep": ROOT / "data/13_sentinel1_copernicus/derived/flood_peak_27sep1828.npy",
    "oct2_validated": ROOT / "data/13_sentinel1_copernicus/derived/flood_2oct_validated.npy",
}
OBSERVED_STAGE_MSL_M = 2.35  # TNy10 17 ต.ค. 2569 — ค่าเดียวที่ทุกรายงานต้องอ้าง


def analyze_depression():
    assert DEM_PATH.exists(), f"ไม่พบไฟล์ {DEM_PATH}"
    assert MASK_ONG_PATH.exists(), f"ไม่พบไฟล์ {MASK_ONG_PATH}"

    dem = np.load(DEM_PATH)
    mask_ong = np.load(MASK_ONG_PATH)

    ong_dem = dem[mask_ong]
    ong_valid = ong_dem[~np.isnan(ong_dem) & (ong_dem >= 0.0)]
    total_area_km2 = float(len(ong_valid) * (30.0 * 30.0) / 1e6)

    def row_at(h_val: float) -> dict:
        sub = ong_valid[ong_valid <= h_val]
        inun_pixels = len(sub)
        inun_km2 = float(inun_pixels * (30.0 * 30.0) / 1e6)
        inun_pct = float(inun_km2 / total_area_km2 * 100.0)

        if inun_pixels > 0:
            mean_depth_m = float(np.mean(h_val - sub))
            max_depth_m = float(h_val - np.min(sub))
            vol_mcm = float(inun_km2 * mean_depth_m)
        else:
            mean_depth_m = 0.0
            max_depth_m = 0.0
            vol_mcm = 0.0

        return {
            "stage_msl_m": h_val,
            "inundated_area_km2": round(inun_km2, 2),
            "inundated_share_pct": round(inun_pct, 1),
            "mean_depth_m": round(mean_depth_m, 2),
            "max_depth_m": round(max_depth_m, 2),
            "storage_volume_mcm": round(vol_mcm, 2),
        }

    # กวาดหาระดับน้ำตั้งแต่ +1.0 ถึง +4.5 ม.รทก. ขั้นละ 0.1 ม.
    curve = [row_at(float(round(h, 2))) for h in np.arange(1.0, 4.6, 0.1)]

    # สกัดจุดสำคัญทางชลศาสตร์
    # 1. ระดับน้ำสังเกตการณ์จริง ณ 17 ต.ค. 2569 (TNy10 = +2.35 ม.รทก.)
    # ประเมินที่ระดับสังเกตจริงพอดี (ไม่ปัดไปขั้น 0.1 ม. — รีวิวรอบ 6 A9)
    stage_obs = row_at(OBSERVED_STAGE_MSL_M)
    # 2. จุดเริ่มล้นตลิ่งชุมชนริมคลอง (+2.50 ม.รทก.)
    stage_bankfull = next(c for c in curve if abs(c["stage_msl_m"] - 2.50) < 0.05)
    # 3. จุดเริ่มบ่าล้นคันทางหลวง 305 (+3.20 ม.รทก.)
    stage_spill_route305 = next(c for c in curve if abs(c["stage_msl_m"] - 3.20) < 0.05)

    # C3 (รีวิวรอบ 6): ปรับเทียบระดับน้ำที่มีผลของแบบจำลองถังเติมน้ำกับพื้นที่น้ำท่วมจากดาวเทียมเรดาร์ Sentinel-1
    # — หาระดับที่ให้พื้นที่เท่าที่ดาวเทียมเห็น แล้ววัดว่ารูปแบบเชิงพื้นที่ตรงกันเพียงใด (ไม่ใช้ผลนี้ทำนายการล้นถนน)
    sar_calibration = {}
    for key, path in SAR_MASKS.items():
        if not path.exists():
            continue
        sar = np.load(path).astype(bool)
        if sar.shape != mask_ong.shape:
            continue
        in_d = mask_ong & ~np.isnan(dem) & (dem >= 0.0)
        sar_d = sar & in_d
        sar_km2 = float(sar_d.sum() * 900.0 / 1e6)
        best = None
        for h in np.arange(1.0, 5.0001, 0.01):
            bt = in_d & (dem <= h)
            km2 = float(bt.sum() * 900.0 / 1e6)
            if best is None or abs(km2 - sar_km2) < abs(best[1] - sar_km2):
                best = (float(round(h, 2)), km2, bt)
        h_eff, km2_eff, bt = best
        inter = float((bt & sar_d).sum())
        union = float((bt | sar_d).sum())
        sar_calibration[key] = {
            "sar_area_km2": round(sar_km2, 1),
            "sar_share_pct": round(100.0 * sar_km2 / total_area_km2, 1),
            "effective_stage_msl_m": h_eff,
            "offset_vs_gauge_m": round(h_eff - OBSERVED_STAGE_MSL_M, 2),
            "iou": round(inter / union, 2) if union else None,
            "precision": round(inter / float(bt.sum()), 2) if bt.sum() else None,
            "recall": round(inter / float(sar_d.sum()), 2) if sar_d.sum() else None,
            "gauge_stage_area_km2": round(float(row_at(OBSERVED_STAGE_MSL_M)["inundated_area_km2"]), 1),
        }

    summary = {
        "sar_calibration": sar_calibration,
        "title": "การจำลองความจุแอ่งก้นกระทะ 2 มิติและเส้นชั้นความลึกน้ำท่วมองครักษ์บน DEM 30m",
        "district": "อำเภอองครักษ์ จังหวัดนครนายก",
        "observed_stage_msl_m": OBSERVED_STAGE_MSL_M,
        "total_area_km2": round(total_area_km2, 2),
        "elevation_stats_m": {
            "min": round(float(np.min(ong_valid)), 2),
            "median": round(float(np.median(ong_valid)), 2),
            "mean": round(float(np.mean(ong_valid)), 2),
            "max": round(float(np.max(ong_valid)), 2),
        },
        "critical_thresholds": {
            "observed_oct2026": {
                "stage_msl_m": stage_obs["stage_msl_m"],
                "area_km2": stage_obs["inundated_area_km2"],
                "share_pct": stage_obs["inundated_share_pct"],
                "volume_mcm": stage_obs["storage_volume_mcm"],
                "mean_depth_m": stage_obs["mean_depth_m"],
                "description": f"ระดับน้ำจริงในคลองแม่น้ำใน (TNy10): แบบจำลองถังเติมน้ำที่ระดับนี้ได้พื้นที่ลุ่มต่ำราว {stage_obs['inundated_area_km2']:.1f} ตร.กม. ปริมาตร ~{stage_obs['storage_volume_mcm']:.1f} ล้าน ลบ.ม. (ต่ำกว่าพื้นที่น้ำท่วมที่ดาวเทียมเห็นมาก เพราะผิวน้ำไม่ราบระดับเดียวกับเกจ)",
            },
            "bankfull_threshold": {
                "stage_msl_m": stage_bankfull["stage_msl_m"],
                "area_km2": stage_bankfull["inundated_area_km2"],
                "volume_mcm": stage_bankfull["storage_volume_mcm"],
                "mean_depth_m": stage_bankfull["mean_depth_m"],
                "description": f"ระดับน้ำล้นตลิ่งลำคลองธรรมชาติ: น้ำเริ่มแผ่กว้างเข้าสู่ทุ่งนา {stage_bankfull['inundated_area_km2']:.1f} ตร.กม. ปริมาตรน้ำ ~{stage_bankfull['storage_volume_mcm']:.1f} ล้าน ลบ.ม.",
            },
            "route305_overtopping": {
                "stage_msl_m": stage_spill_route305["stage_msl_m"],
                "area_km2": stage_spill_route305["inundated_area_km2"],
                "volume_mcm": stage_spill_route305["storage_volume_mcm"],
                "mean_depth_m": stage_spill_route305["mean_depth_m"],
                "description": f"ระดับมัธยฐานของภูมิประเทศ ไม่ใช่ระดับสันถนนรังสิต–นครนายก (ทล.305) ที่วัดได้: น้ำท่วมครอบคลุมราว {stage_spill_route305['inundated_area_km2']:.1f} ตร.กม. ({stage_spill_route305['inundated_share_pct']:.1f}% ของอำเภอ) ปริมาตรน้ำสะสม ~{stage_spill_route305['storage_volume_mcm']:.1f} ล้าน ลบ.ม. ตามแบบจำลองถังเติมน้ำ",
            },
        },
        "hypsometric_curve": curve,
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ บันทึกผลจำลองความจุแอ่ง 2 มิติลง {OUT_JSON.name} เรียบร้อย")

    if CANONICAL_PATH.exists():
        with open(CANONICAL_PATH, encoding="utf-8") as f:
            cdata = json.load(f)
        cdata["ongkharak_2d_depression"] = summary
        with open(CANONICAL_PATH, "w", encoding="utf-8") as f:
            json.dump(cdata, f, ensure_ascii=False, indent=1)
        print(f"✅ อัปเดต ongkharak_2d_depression ลง {CANONICAL_PATH.name} สำเร็จ")

    return summary


if __name__ == "__main__":
    analyze_depression()
