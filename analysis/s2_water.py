"""ตรวจน้ำท่วมด้วย Sentinel-2 optical (MNDWI) เทียบกับ S1 ของเรา บนกริดเดียวกัน — 2 ต.ค. 69

ทำไมต้องมี: S1 เป็นเรดาร์ มองไม่เห็นน้ำตื้น/ขุ่น — ค่า 436.3 ตร.กม. (2 ต.ค.) เป็นขอบล่าง
S2 optical 10 ม. วันเดียวกัน (ผ่าน 10:35 น. vs S1 06:09 น.) เห็นผิวน้ำด้วยฟิสิกส์คนละแบบ
= การตรวจสอบอิสระ "คนละเซนเซอร์ คนละฟิสิกส์ วันเดียวกัน"

วิธี: MNDWI = (B03 green − B11 SWIR) / (B03 + B11) · น้ำ = MNDWI > 0
      ตัดเมฆ/เงา/cirrus ด้วย SCL (คง {4 vegetation, 5 non-veg, 6 water, 7 unclassified})
      อ่านบนกริด S1 30 ม. (reproject) · พื้นที่ใน lowland เดียวกับที่ S1 คำนวณ

ข้อจำกัด: 2 ต.ค. เมฆ/cirrus ~52% (ผ่านตรวจแล้วใน data/18) — เทียบข้ามกันได้เฉพาะบริเวณ
ที่ S2 โปร่ง (fair-compare) · ผ่านเวลาต่างกัน 4.5 ชม. (น้ำลดระหว่างวัน S2 อาจน้อยกว่านิด)
"""
import glob
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling as WarpRes
from rasterio.warp import reproject
from rasterio.transform import from_bounds

PROJ = Path(__file__).resolve().parent.parent
S2D = PROJ / "data" / "18_sentinel2_copernicus"
DER = PROJ / "data" / "13_sentinel1_copernicus" / "derived"

PREFIX = "S2B_MSIL2A_20261002T033549"
SCENE_NOTE = "Sentinel-2B · 2 ต.ค. 69 10:35 น. (S1 ผ่าน 06:09 น. วันเดียวกัน)"

gr = json.load(open(DER / "grid.json", encoding="utf-8"))
x0, y0, x1, y1 = gr["x0"], gr["y0"], gr["x1"], gr["y1"]
nx, ny = gr["nx"], gr["ny"]
transform = from_bounds(x0, y0, x1, y1, nx, ny)
from common import cell_km2  # noqa: E402
CELL = cell_km2(gr["res"])

prov = np.load(DER / "mask_province.npy")
lowland = np.load(DER / "mask_lowland.npy")
districts = {f.stem.replace("mask_district_", ""): np.load(f)
             for f in sorted(DER.glob("mask_district_*.npy"))}
s1 = np.load(DER / "flood_2oct_validated.npy")


def read_band(pattern, dtype="float32"):
    f = glob.glob(str(S2D / f"{PREFIX}*/GRANULE/*/IMG_DATA/**/{pattern}"), recursive=True)[0]
    dst = np.full((ny, nx), np.nan, np.float32)
    with rasterio.open(f) as src:
        reproject(rasterio.band(src, 1), dst, dst_transform=transform,
                  dst_crs="EPSG:4326",
                  resampling=WarpRes.bilinear if dtype == "float32" else WarpRes.nearest,
                  dst_nodata=np.nan if dtype == "float32" else 0)
    return dst


g03 = read_band("T47PQR_*_B03_10m.jp2") / 10000.0   # green
b11 = read_band("T47PQR_*_B11_20m.jp2") / 10000.0   # SWIR1
scl = read_band("T47PQR_*_SCL_20m.jp2", dtype="uint8")

mndwi = (g03 - b11) / (g03 + b11)
water = (mndwi > 0) & np.isfinite(mndwi)
clear = np.isin(scl, [4, 5, 6, 7])
valid = clear & prov & lowland

water_low = (water & valid)
area_low = water_low.sum() * CELL
area_prov = (water & clear & prov).sum() * CELL
clear_prov_pct = 100.0 * (clear & prov).sum() / prov.sum()

dist = {k: round((water & valid & m).sum() * CELL, 1) for k, m in districts.items()}

L = water & valid
S = s1 & valid
tp = (L & S).sum() * CELL
fp = (L & ~S).sum() * CELL
fn = ((~L) & S).sum() * CELL
pr = tp / max(tp + fp, 1e-9)
rc = tp / max(tp + fn, 1e-9)
f1 = 2 * pr * rc / max(pr + rc, 1e-9)

# threshold sensitivity
sens = {}
for thr in (-0.05, 0.0, 0.05, 0.1):
    w = (mndwi > thr) & valid
    sens[f"mndwi>{thr}"] = round(w.sum() * CELL, 1)

out = {
    "scene": SCENE_NOTE,
    "method": "MNDWI=(B03-B11)/(B03+B11)>0 · SCL ตัดเมฆ/เงา/cirrus (คง 4/5/6/7) · กริด S1 30 ม.",
    "cloud_over_prov_pct": round(100 - clear_prov_pct, 1),
    "clear_prov_pct": round(clear_prov_pct, 1),
    "area_lowland_km2": round(area_low, 1),
    "area_province_km2": round(area_prov, 1),
    "districts_lowland_km2": dist,
    "vs_s1_same_day": {"s2_only_km2": round(fp, 1), "both_km2": round(tp, 1),
                       "s1_only_km2": round(fn, 1), "precision": round(pr, 3),
                       "recall": round(rc, 3), "f1": round(f1, 3)},
    "threshold_sensitivity_km2": sens,
    "note": "S2 ผ่าน 10:35 น. หลัง S1 (06:09) 4.5 ชม. — น้ำลดระหว่างวันทำให้ S2 อาจน้อยกว่านิดหน่อย",
}
(PROJ / "analysis" / "s2_water.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
np.save(DER / "flood_s2_20261002.npy", (water & clear & prov).astype(np.uint8))

print(f"โปร่งบนจังหวัด {clear_prov_pct:.1f}% · น้ำ (lowland) {area_low:.1f} ตร.กม. (ทั้งจังหวัด {area_prov:.1f})")
print(f"รายอำเภอ: {dist}")
print(f"เทียบ S1 วันเดียวกัน (เฉพาะที่โปร่ง): S2-only {fp:.1f} · ตรงกัน {tp:.1f} · S1-only {fn:.1f} · "
      f"P {pr:.3f} R {rc:.3f} F1 {f1:.3f}")
print(f"threshold: {sens}")
