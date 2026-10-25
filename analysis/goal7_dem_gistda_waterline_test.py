"""ทดสอบ DEM 3 ชุดด้วยขอบเขตน้ำท่วมรายปีของ GISTDA (2548–2562) ใน อ.องครักษ์ — วิธีเดียวกับขอบน้ำเรดาร์ (goal7_dem_waterline_test)
เกณฑ์เขียนไว้ก่อนดูผล: นับเฉพาะปีที่มีพื้นที่น้ำท่วมในอำเภอ ≥ 2 ตร.กม. · ขอบ = พิกเซลน้ำที่ติดพิกเซลไม่ท่วมในอำเภอ · ชุดที่ดีกว่า = สัดส่วนช่วงกลางของความสูงขอบต่อช่วงกลางทั้งอำเภอต่ำกว่า
ข้อจำกัด: ขอบเขตแต่ละปีมาจากภาพต่างวัน/ต่างเกณฑ์ ไม่ใช่ผิวน้ำระดับเดียวเสมอไป จึงใช้เป็นหลักฐานเสริม
รัน: python analysis/goal7_dem_gistda_waterline_test.py
ผลลัพธ์: analysis/goal7/dem_gistda_waterline_test.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import rasterio.features

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_ongkharak_2d_depression as dep  # noqa: E402  (reuse-first: DEM 3 ชุด · หน้ากาก)
import goal7_ongkharak_connected_fill as cf  # noqa: E402  (กริดภูมิศาสตร์ WGS84 ของเรดาร์)
import goal7_mitrearth_national as nat  # noqa: E402  (ตัวอ่านรูปหลายเหลี่ยม GISTDA)
from goal7_dem_waterline_test import edge_pixels, pct  # noqa: E402

OUT = ROOT / "analysis/goal7/dem_gistda_waterline_test.json"
MIN_KM2 = 2.0


def main() -> None:
    mask = np.load(dep.MASK_ONG_PATH).astype(bool)
    dems = dep.load_dems(mask)
    ys, xs = np.nonzero(mask)
    x0, y0 = cf.TRANSFORM * (xs.min(), ys.max() + 1)
    x1, y1 = cf.TRANSFORM * (xs.max() + 1, ys.min())
    bbox = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
    out = {"min_flood_km2": MIN_KM2, "years": {}, "summary": {}}
    for y in nat.YEARS:
        gs = list(nat.shapes_in(nat.year_file(y), bbox))
        if not gs:
            continue
        ras = rasterio.features.rasterize(((g, 1) for g in gs), out_shape=cf.SHAPE, transform=cf.TRANSFORM, fill=0, dtype="uint8").astype(bool) & mask
        km2 = float(ras.sum()) * dep.CELL_KM2
        if km2 < MIN_KM2:
            continue
        rec = {"flood_km2_in_district": round(km2, 1), "dems": {}}
        for dk, dem in dems.items():
            valid = mask & ~np.isnan(dem) & (dem >= -3.0)
            e = edge_pixels(ras & valid, valid)
            if e.sum() < 500:
                continue
            h, allv = dem[e], dem[valid]
            rec["dems"][dk] = {"edge_pixels": int(e.sum()), "edge_median_m": round(float(np.median(h)), 2), "edge_iqr_m": round(pct(h, 75) - pct(h, 25), 2),
                               "edge_iqr_over_district_iqr": round((pct(h, 75) - pct(h, 25)) / (pct(allv, 75) - pct(allv, 25)), 3)}
        if len(rec["dems"]) == len(dems):
            out["years"][str(y)] = rec
    for dk in dems:
        r = [v["dems"][dk]["edge_iqr_over_district_iqr"] for v in out["years"].values()]
        med = [v["dems"][dk]["edge_median_m"] for v in out["years"].values()]
        out["summary"][dk] = {"label": dep.LABELS[dk], "years_tested": len(r), "median_ratio": round(float(np.median(r)), 3) if r else None,
                              "median_edge_level_m": round(float(np.median(med)), 2) if med else None,
                              "years_best": sum(1 for v in out["years"].values() if v["dems"][dk]["edge_iqr_over_district_iqr"] == min(x["edge_iqr_over_district_iqr"] for x in v["dems"].values()))}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out["summary"], ensure_ascii=False, indent=1))
    for y, v in out["years"].items():
        print(y, v["flood_km2_in_district"], {k: d["edge_iqr_over_district_iqr"] for k, d in v["dems"].items()})


if __name__ == "__main__":
    main()
