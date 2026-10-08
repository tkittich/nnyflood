"""Change-detection flood mapping — กฎที่ตีพิมพ์ในรายงาน (3 เงื่อนไข + opening 3×3)

กฎ (คาลิเบรตใหม่ 8 ต.ค. 69 รอบ 2 ด้วย analysis/calibrate_s1_thresholds.py — grid 420 คู่
maximize F1 กับผลิตภัณฑ์ GISTDA บนฉาก 2 ต.ค. pass เดียวกัน: **F1=0.727, P=0.672, R=0.792**;
ชุดเดิม (1.0, 2.0, −18) ให้ F1=0.699):

    น้ำ = (ΔVH ≤ −0.5 dB) & (ΔVV ≤ −1.5 dB) & (VHหลัง ≤ −20 dB) + binary opening 3×3
    (คำนวณใน lowland <60 ม. เท่ากับขอบเขตที่ S1 pipeline รายงาน)

คาลิเบรตบนฉาก 2 ต.ค. (baseline 20 ก.ย. คู่วงโคจรเดียวกัน) แล้วใช้กฎเดียวกันกับ
ฉากน้ำสูงสุด 27 ก.ย. 18:28 (baseline 15 ก.ย. คู่วงโคจรเดียวกัน — mosaic จาก
2 slice ด้วย analysis/s1_merge_scenes.py)

⚠️ รันแล้วต้องได้ตาม canonical (build_canonical_numbers.py assert ให้):
    2 ต.ค. = 363.6 ตร.กม. · น้ำสูงสุด 27 ก.ย. = 452.1 ตร.กม.   (ค่าชุดกฎใหม่ 8 ต.ค. 69;
    ชุดเก่า 436.3/509.3 เลิกใช้ — อย่าใช้ตัวเลขเก่าค้างในเอกสาร/กราฟ)
    เปลี่ยน threshold ได้เฉพาะผ่าน calibrate_s1_thresholds.py + ประกาศ canonical ชุดใหม่ทั้งรายงาน

(หมายเหตุ provenance: มาสก์ต้นฉบับผลิตเมื่อ 5 ต.ค. 69 ด้วยสคริปต์ inline ยุคนั้น —
อย่าสลับกลับไป grid-search VH-only เพราะให้คนละมาสก์ 564.4 ตร.กม.
สคริปต์เก่าเก็บที่ analysis/archive/)

โครงสร้าง: ฟังก์ชันบริสุทธิ์ (detect/prf) import ได้โดยไม่อ่านไฟล์ —
tests/test_core.py เทสกฎบนอาร์เรย์สังเคราะห์; รันวิเคราะห์จริง = `python s1_change_detect.py`
"""
import json
from pathlib import Path

import numpy as np
import shapefile
from scipy import ndimage
from shapely.geometry import shape as shp_shape
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from common import cell_km2

PROJ = Path(__file__).resolve().parent.parent   # อิง __file__ ไม่ใช่ cwd (ไม่ hardcode พาธ)
DER = PROJ / "data" / "13_sentinel1_copernicus" / "derived"

# ---- กฎ canonical (คาลิเบรต 8 ต.ค. 69 รอบ 2 — ดู docstring) ----
DROP_VH, DROP_VV, ABS_VH = 0.5, 1.5, -20.0
STRUCT3 = np.ones((3, 3), bool)


def detect(pre_vh, post_vh, pre_vv, post_vv, lowland,
           drop_vh=DROP_VH, drop_vv=DROP_VV, abs_vh=ABS_VH, struct=STRUCT3):
    """กฎ canonical: ΔVH≤−drop_vh & ΔVV≤−drop_vv & VHหลัง≤abs_vh + opening 3×3 (ใน lowland)

    อินพุต = อนุกรม dB (NaN = นอกฉาก) · คืน mask bool ขนาดเดียวกับอินพุต
    """
    valid = (np.isfinite(pre_vh) & np.isfinite(post_vh)
             & np.isfinite(pre_vv) & np.isfinite(post_vv) & lowland)
    w = (post_vh - pre_vh <= -drop_vh) & (post_vv - pre_vv <= -drop_vv) & (post_vh <= abs_vh) & valid
    return ndimage.binary_opening(w, structure=struct)


def prf(w, gis):
    """precision / recall / F1 ของมาสก์ w เทียบ GISTDA mask gis"""
    tp = (w & gis).sum(); fp = (w & ~gis).sum(); fn = ((~w) & gis).sum()
    pr = tp / max(tp + fp, 1); rc = tp / max(tp + fn, 1)
    return pr, rc, 2 * pr * rc / max(pr + rc, 1e-9)


def load_gistda_mask(g):
    """rasterize ผลิตภัณฑ์ GISTDA 2 ต.ค. (กรอง PV_TN นครนายก) บนกริดมาตรฐาน → mask bool"""
    x0, y0, x1, y1 = g["x0"], g["y0"], g["x1"], g["y1"]
    nx, ny = g["nx"], g["ny"]
    tr = from_bounds(x0, y0, x1, y1, nx, ny)
    r = shapefile.Reader(
        PROJ / "data/manual/shp_S1D_20261002_0609/S1D_20261002_0609.shp",
        encoding="utf-8",
    )
    polys = []
    for sr in r.iterShapeRecords():
        if "นครนายก" not in (sr.record["PV_TN"] or ""):
            continue
        geom = shp_shape(sr.shape.__geo_interface__)
        if not geom.is_valid:
            geom = geom.buffer(0)
        if geom.is_empty:
            continue
        parts = [geom] if geom.geom_type == "Polygon" else [p for p in geom.geoms if p.geom_type == "Polygon"]
        polys.extend(parts)
    return rasterize([(p, 1) for p in polys], out_shape=(ny, nx), transform=tr, fill=0, dtype="uint8").astype(bool)


def main():
    g = json.load(open(DER / "grid.json"))
    RES = g["res"]
    nx, ny = g["nx"], g["ny"]
    CELL = cell_km2(RES)
    lowland = np.load(DER / "mask_lowland.npy")

    gis = load_gistda_mask(g)
    print(f"GISTDA raster: {gis.sum()*CELL:.1f} km² (ผลิตภัณฑ์ทางการ 306.9 ตร.กม. — attrib sum)")

    # ---- 1) ฉากคาลิเบรต 2 ต.ค. (ต้องได้ 436.3) ----
    w2 = detect(np.load(DER / "s1d_20260920_0609_vh_db.npy"), np.load(DER / "s1d_20261002_0609_vh_db.npy"),
                np.load(DER / "s1d_20260920_0609_vv_db.npy"), np.load(DER / "s1d_20261002_0609_vv_db.npy"),
                lowland)
    pr, rc, f1 = prf(w2, gis)
    print(f"2 ต.ค.: น้ำ {w2.sum()*CELL:.1f} km² | P={pr:.3f} R={rc:.3f} F1={f1:.3f} (เอกสาร: 436.3 · F1=0.699)")

    # ---- 2) ฉากน้ำสูงสุด 27 ก.ย. 18:28 (ต้องได้ 509.3) ----
    w_pk = detect(np.load(DER / "s1d_20260915_1828_full_vh_db.npy"), np.load(DER / "s1d_20260927_1828_full_vh_db.npy"),
                  np.load(DER / "s1d_20260915_1828_full_vv_db.npy"), np.load(DER / "s1d_20260927_1828_full_vv_db.npy"),
                  lowland)
    print(f"น้ำสูงสุด 27 ก.ย. 18:28: น้ำ {w_pk.sum()*CELL:.1f} km² (เอกสาร: 509.3)")

    np.save(DER / "flood_peak_27sep1828.npy", w_pk)
    np.save(DER / "flood_2oct_validated.npy", w2)

    # ---- รายอำเภอ ----
    for f in sorted(DER.glob("mask_district_*.npy")):
        m = np.load(f)
        print(f"  {f.stem.replace('mask_district_', '')}: peak {round((w_pk & m).sum()*CELL, 1)} km2")


if __name__ == "__main__":
    main()
