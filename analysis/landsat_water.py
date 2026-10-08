"""ตรวจน้ำท่วมด้วย Landsat optical 30 ม. (MNDWI) เทียบกับ S1 ของเรา + GISTDA บนกริดเดียวกัน

ทำไมต้องมี: S1 เป็นเรดาร์ — มองไม่เห็นน้ำตื้น/ขุ่น/ไหลแรง/ใต้ไม้ ค่า 509.3/436.3 ตร.กม.
จึงเป็น **ขอบล่าง** Landsat optical (30 ม. ฟรี T1) เห็นผิวน้ำด้วยฟิสิกส์คนละแบบ
(MNDWI: SWIR1 ดูดกลืนในน้ำ) ฉาก 2 ต.ค. 69 = วันเดียวกับ GISTDA (306.9) และ S1 (436.3)
จึงเป็นการตรวจสอบอิสระแบบ 3 เซนเซอร์/2 ฟิสิกส์ในวันเดียว

วิธี:
- SR B3 (green) + B6 (SWIR1): scale จาก MTL (Collection 2 = ×2.75e-05 − 0.2)
- MNDWI = (G − S1) / (G + S1) · น้ำ = MNDWI > 0
- QA_PIXEL: ตัด fill/dilated-cloud/cirrus/cloud/shadow/snow (bits 0–5)
- อ่านบนกริด S1 (WGS84 30 ม.) ด้วย WarpedVRT (บทเรียน S2: ฉากเป็น UTM ต้อง warp ก่อน)
- พื้นที่ = น้ำ(ใน lowland <60 ม. เท่ากับขอบเขตที่ S1 คำนวณ) × cell_km2(30)
- เทียบข้ามกับมาสก์ S1 (flood_2oct_validated.npy) เฉพาะบริเวณที่ Landsat "โปร่ง"

รัน: python analysis/landsat_water.py   (ต้องมี data/manual/LC0* + data/13/derived/*)
"""
import csv
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.vrt import WarpedVRT
from rasterio.windows import from_bounds as windows_from_bounds

PROJ = Path(__file__).resolve().parent.parent
DER = PROJ / "data" / "13_sentinel1_copernicus" / "derived"
MANUAL = PROJ / "data" / "manual"
OUT_JSON = PROJ / "analysis" / "landsat_water.json"

SCENES = [
    ("2026-10-02", "LC09_L2SP_128050_20261002_20261003_02_T1", "Landsat 9 · 40.0% เมฆ (Tier 1)"),
    ("2026-09-24", "LC08_L2SP_128050_20260924_20261001_02_T2", "Landsat 8 · 34.5% เมฆ (Tier 2 — geometry คุณภาพรอง)"),
]

g = json.load(open(DER / "grid.json", encoding="utf-8"))
x0, y0, x1, y1, RES = g["x0"], g["y0"], g["x1"], g["y1"], g["res"]
nx, ny = g["nx"], g["ny"]
transform = from_bounds(x0, y0, x1, y1, nx, ny)

# สูตรพื้นที่เซลล์ — ค่าเดียวกับ common.cell_km2 (30 ม. @ 14.2) แต่กริดนี้ res มาจาก grid.json
from common import cell_km2  # noqa: E402
CELL = cell_km2(RES)

prov = np.load(DER / "mask_province.npy")
lowland = np.load(DER / "mask_lowland.npy")
district_masks = {}
for f in sorted(DER.glob("mask_district_*.npy")):
    district_masks[f.stem.replace("mask_district_", "")] = np.load(f)

s1_oct2 = np.load(DER / "flood_2oct_validated.npy")


def read_on_grid(src_path, band_index=1, dtype="float32"):
    """อ่าน 1 band บนกริด S1 ด้วย WarpedVRT (คืน None ถ้าไม่ครอบ)"""
    with rasterio.open(src_path) as src:
        if src.crs is None:
            raise ValueError(f"no CRS: {src_path}")
        bounds = src.bounds
        # แปลง bounds ของกริดเรา (4326) ไปเทียบกับ bounds ต้นทาง (UTM) — เช็คครอบ
        from rasterio.warp import transform_bounds
        src_bounds_4326 = transform_bounds(src.crs, "EPSG:4326", *bounds, densify_pts=21)
        if (src_bounds_4326[0] > x0 or src_bounds_4326[2] < x1
                or src_bounds_4326[1] > y0 or src_bounds_4326[3] < y1):
            print(f"    (bounds ต้นทางไม่ครอบกริด: {tuple(round(b, 3) for b in src_bounds_4326)})")
        with WarpedVRT(src, crs="EPSG:4326", transform=transform, width=nx, height=ny,
                       resampling=Resampling.bilinear if dtype == "float32" else Resampling.nearest,
                       nodata=src.nodata) as vrt:
            return vrt.read(band_index).astype(dtype)


def parse_scale(mtl_path, band):
    """คืน (mult, add) ของ SR band จาก MTL"""
    txt = mtl_path.read_text(encoding="utf-8")
    import re
    m = re.search(rf"REFLECTANCE_MULT_BAND_{band}\s*=\s*([0-9.eE+-]+)", txt)
    a = re.search(rf"REFLECTANCE_ADD_BAND_{band}\s*=\s*([0-9.eE+-]+)", txt)
    return float(m.group(1)), float(a.group(1))


results = {"method": "MNDWI=(B3-B6)/(B3+B6)>0 · QA_PIXEL bits0-5 ตัดเมฆ/เงา · "
                     "อ่านบนกริด S1 30 ม. · พื้นที่คำนวณใน lowland เดียวกับ S1",
           "scenes": {}}

for date_iso, prefix, note in SCENES:
    print(f"\n== {date_iso} {prefix} ({note})")
    mtl = MANUAL / f"{prefix}_MTL.txt"
    g_fp = MANUAL / f"{prefix}_SR_B3.TIF"
    s_fp = MANUAL / f"{prefix}_SR_B6.TIF"
    qa_fp = MANUAL / f"{prefix}_QA_PIXEL.TIF"
    for p in (mtl, g_fp, s_fp, qa_fp):
        assert p.exists(), f"missing {p}"

    m3, a3 = parse_scale(mtl, 3)
    m6, a6 = parse_scale(mtl, 6)
    green = read_on_grid(g_fp) * m3 + a3
    swir = read_on_grid(s_fp) * m6 + a6
    qa = read_on_grid(qa_fp, dtype="uint16")

    mndwi = (green - swir) / (green + swir)
    water = mndwi > 0
    clear = (qa & 0b111111) == 0  # bits 0-5: fill/dilated/cirrus/cloud/shadow/snow

    in_prov = prov & clear
    valid = in_prov & lowland
    water_prov = water & in_prov
    water_low = water & valid

    # เมฆเหนือจังหวัด (นอก clear ใน prov)
    cloud_prov_pct = 100.0 * (~clear & prov).sum() / prov.sum()

    # ตัวเลขหลัก
    area_low = water_low.sum() * CELL
    area_prov = water_prov.sum() * CELL

    # แยกย่อยต่ออำเภอ (ใน lowland+clear)
    dist = {}
    for name, m in district_masks.items():
        dist[name] = round((water & valid & m).sum() * CELL, 1)

    # เทียบกับ S1 2 ต.ค. เฉพาะบริเวณที่ Landsat โปร่ง (fair-compare)
    s1_cmp = None
    if "2026-10-02" in date_iso:
        L = water & valid
        S = s1_oct2 & valid
        tp = (L & S).sum() * CELL
        fp = (L & ~S).sum() * CELL
        fn = ((~L) & S).sum() * CELL
        pr = tp / max(tp + fp, 1e-9)
        rc = tp / max(tp + fn, 1e-9)
        s1_cmp = {"landsat_only_fp_km2": round(fp, 1), "both_tp_km2": round(tp, 1),
                  "s1_only_fn_km2": round(fn, 1), "precision": round(pr, 3),
                  "recall": round(rc, 3), "f1": round(2 * pr * rc / max(pr + rc, 1e-9), 3)}
        np.save(DER / "flood_landsat_20261002.npy", water & in_prov)

    results["scenes"][date_iso] = {
        "note": note, "cloud_prov_pct": round(cloud_prov_pct, 1),
        "area_lowland_km2": round(area_low, 1), "area_province_km2": round(area_prov, 1),
        "districts_lowland_km2": dist, "vs_s1_oct2": s1_cmp,
    }
    print(f"  เมฆเหนือจังหวัด {cloud_prov_pct:.1f}%")
    print(f"  น้ำ (lowland, เทียบ S1 ได้ตรง) = {area_low:.1f} ตร.กม. | (ทั้งจังหวัด) = {area_prov:.1f}")
    print(f"  รายอำเภอ: {dist}")
    if s1_cmp:
        print(f"  เทียบ S1 2 ต.ค. (เฉพาะที่โปร่ง): L-only {s1_cmp['landsat_only_fp_km2']} · "
              f"ตรงกัน {s1_cmp['both_tp_km2']} · S1-only {s1_cmp['s1_only_fn_km2']} · "
              f"P {s1_cmp['precision']} R {s1_cmp['recall']} F1 {s1_cmp['f1']}")

OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\nsaved {OUT_JSON}")
