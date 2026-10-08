"""Change-detection flood mapping + calibration vs GISTDA (2 Oct same pass).

Rule: flood = (VH_post - VH_pre <= -DROP) & (VH_post <= ABS)
Calibrate (DROP, ABS) on 2 Oct vs 19 Sep against GISTDA polygons (PV=นครนายก),
then apply the chosen rule to peak 27 Sep 18:28 vs 15 Sep 18:28.
"""
import json
from pathlib import Path

import numpy as np
import shapefile
from rasterio.features import rasterize
from rasterio.transform import from_bounds

PROJ = Path(r"D:\theera\Documents\code\flood")
DER = PROJ / "data" / "13_sentinel1_copernicus" / "derived"

g = json.load(open(DER / "grid.json"))
x0, y0, x1, y1, RES = g["x0"], g["y0"], g["x1"], g["y1"], g["res"]
nx, ny = g["nx"], g["ny"]
tr = from_bounds(x0, y0, x1, y1, nx, ny)
cell = RES * 111.32 * RES * 111.32 * np.cos(np.radians(14.2))
prov = np.load(DER / "mask_province.npy")
lowland = np.load(DER / "mask_lowland.npy")

r = shapefile.Reader(
    PROJ / "data/manual/shp_S1D_20261002_0609/S1D_20261002_0609.shp",
    encoding="utf-8",
)
polys = []
for sr in r.iterShapeRecords():
    pv = sr.record["PV_TN"]
    if "นครนายก" not in (pv or ""):
        continue
    from shapely.geometry import shape as shp_shape

    geom = shp_shape(sr.shape.__geo_interface__)
    if not geom.is_valid:
        geom = geom.buffer(0)
    if geom.is_empty:
        continue
    parts = [geom] if geom.geom_type == "Polygon" else [p for p in geom.geoms if p.geom_type == "Polygon"]
    polys.extend(parts)
gis = rasterize([(p, 1) for p in polys], out_shape=(ny, nx), transform=tr, fill=0, dtype="uint8").astype(bool)
print(f"GISTDA NN 2Oct rasterized: {gis.sum()*cell:.1f} km2 (attrib sum {sum(sr['F_AREA'] for sr in r.iterRecords() if 'นครนายก' in (sr['PV_TN'] or ''))/1e6:.1f} km2)")

pre = np.load(DER / "s1d_20260920_0609_vh_db.npy")   # 19 Sep 23:08 UTC = 20 Sep 06:09
post = np.load(DER / "s1d_20260915_1828_full_vh_db.npy")  # placeholder replaced below
post = np.load(DER / "s1d_20261002_0609_vh_db.npy")  # 2 Oct 06:09
valid = np.isfinite(pre) & np.isfinite(post) & lowland
d = post - pre

def f1_for(drop, absv):
    w = (d <= -drop) & (post <= absv) & valid
    tp = (w & gis).sum(); fp = (w & ~gis).sum(); fn = ((~w) & gis).sum()
    pr = tp / max(tp + fp, 1); rc = tp / max(tp + fn, 1)
    return pr, rc, 2 * pr * rc / max(pr + rc, 1e-9), w.sum() * cell

print("\nDROP\\ABS " + "  ".join(f"{a:>7.1f}" for a in (-18, -17, -16, -15, -14)))
best = (0, None, None)
for drop in (2.0, 2.5, 3.0, 3.5, 4.0, 5.0):
    row = []
    for absv in (-18, -17, -16, -15, -14):
        pr, rc, f1, km2 = f1_for(drop, absv)
        row.append(f1)
        if f1 > best[0]:
            best = (f1, drop, absv)
    print(f"{drop:4.1f}     " + "  ".join(f"{v:7.3f}" for v in row))
print(f"\nbest F1={best[0]:.3f} at DROP={best[1]} dB, ABS={best[2]} dB")
pr, rc, f1, km2 = f1_for(best[1], best[2])
print(f"  -> water {km2:.1f} km2 | precision {pr:.3f} recall {rc:.3f} (GISTDA {gis.sum()*cell:.1f})")

# apply to peak
DROP, ABS = best[1], best[2]
pre_pk = np.load(DER / "s1d_20260915_1828_full_vh_db.npy")  # 15 Sep 18:28
post_pk = np.load(DER / "s1d_20260927_1828_full_vh_db.npy")  # 27 Sep 18:28 PEAK
valid_pk = np.isfinite(pre_pk) & np.isfinite(post_pk) & lowland
d_pk = post_pk - pre_pk
w_pk = (d_pk <= -DROP) & (post_pk <= ABS) & valid_pk
print(f"\nPEAK 27 Sep 18:28 vs 15 Sep: flood {w_pk.sum()*cell:.1f} km2 (lowland)")
np.save(DER / "flood_peak_27sep1828.npy", w_pk)
np.save(DER / "flood_2oct_validated.npy", (d <= -DROP) & (post <= ABS) & valid)

import rasterio
prof = dict(driver="GTiff", height=ny, width=nx, count=1, dtype="uint8",
            crs="EPSG:4326", transform=tr, nodata=255, compress="lzw")
for name, mask in (("flood_peak_27sep1828", w_pk),):
    out = np.where(np.isfinite(post_pk) & prov, mask.astype("uint8"), 255)
    with rasterio.open(DER / f"{name}.tif", "w", **prof) as dst:
        dst.write(out, 1)

# district stats
for f in sorted(DER.glob("mask_district_*.npy")):
    name = f.stem.replace("mask_district_", "")
    m = np.load(f)
    print(f"  {name}: peak {round((w_pk & m).sum()*cell,1)} km2")
