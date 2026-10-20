"""ทดสอบว่าแบบจำลองความสูง (DEM) ชุดไหนตรงกับขอบน้ำท่วมจากดาวเทียมเรดาร์มากที่สุด (วิธีเส้นขอบน้ำ)
หลักการ: ผิวน้ำนิ่งเป็นระดับเดียวกัน ดังนั้นความสูงของ DEM ตามขอบเขตน้ำท่วมควรรวมกลุ่มแคบ — DEM ที่แม่นกว่าให้ความสูงขอบแคบกว่า (เทียบสัดส่วนกับช่วงความสูงทั้งอำเภอ)
ข้อจำกัด: ขอบเรดาร์มีสัญญาณรบกวน น้ำที่ไหลไม่ได้นิ่งระดับเดียว และคันกั้นทำให้ขอบไม่ตามระดับ จึงเป็นหลักฐานอิสระเสริมจากเส้นดิน EIA ไม่ใช่ตัวตัดสินเดียว
รัน: python analysis/goal7_dem_waterline_test.py
ผลลัพธ์: analysis/goal7/dem_waterline_test.json
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_ongkharak_2d_depression as dep  # noqa: E402  (reuse-first: DEM 3 ชุด · หน้ากาก · ภาพเรดาร์)

OUT = ROOT / "analysis/goal7/dem_waterline_test.json"


def edge_pixels(sar: np.ndarray, domain: np.ndarray) -> np.ndarray:
    """พิกเซลน้ำท่วมที่ติดพิกเซลไม่ท่วมภายในอำเภอ (เพื่อนบ้าน 4 ทิศ)"""
    inner = domain & ~np.pad(~domain, 1, constant_values=True)[1:-1, 1:-1]
    p = np.pad(sar, 1, constant_values=False)
    nb_dry = ~p[:-2, 1:-1] | ~p[2:, 1:-1] | ~p[1:-1, :-2] | ~p[1:-1, 2:]
    return sar & nb_dry & domain


def pct(a, q):
    return float(np.percentile(a, q))


def main() -> None:
    mask = np.load(dep.MASK_ONG_PATH).astype(bool)
    dems = dep.load_dems(mask)
    out = {"method": "ความสูง DEM ตามขอบน้ำท่วมเรดาร์ — ยิ่งแคบ (เทียบช่วงความสูงทั้งอำเภอ) ยิ่งสอดคล้องกับผิวน้ำระดับเดียว", "cell_m": 30, "results": {}}
    for sk, path in dep.SAR_MASKS.items():
        sar = np.load(path).astype(bool)
        if sar.shape != mask.shape:
            continue
        for dk, dem in dems.items():
            valid = mask & ~np.isnan(dem) & (dem >= -3.0)
            e = edge_pixels(sar & valid, valid)
            h = dem[e]
            allv = dem[valid]
            iqr_e = pct(h, 75) - pct(h, 25)
            iqr_all = pct(allv, 75) - pct(allv, 25)
            out["results"].setdefault(sk, {})[dk] = {
                "label": dep.LABELS[dk], "edge_pixels": int(e.sum()), "edge_median_m": round(float(np.median(h)), 2),
                "edge_iqr_m": round(iqr_e, 2), "edge_p10_p90_m": [round(pct(h, 10), 2), round(pct(h, 90), 2)],
                "district_iqr_m": round(iqr_all, 2), "edge_iqr_over_district_iqr": round(iqr_e / iqr_all, 3)}
    # เกจ TNy10 2.35 ม.รทก. เทียบมัธยฐานขอบ (บริบท ไม่ใช่เกณฑ์ตัดสิน เพราะเกจอยู่ในคลองคนละวันกับภาพ)
    out["gauge_tny10_msl_m"] = dep.OBSERVED_STAGE_MSL_M
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for sk, d in out["results"].items():
        for dk, r in d.items():
            print(sk, dk, r["edge_pixels"], "median", r["edge_median_m"], "IQR", r["edge_iqr_m"], "ratio", r["edge_iqr_over_district_iqr"])


if __name__ == "__main__":
    main()
