"""Build common masks (province, districts, lowland DEM) on the S1 30 m grid.

Grid covers the full OSM Nakhon Nayok province polygon with margin.
Outputs derived/grid.json + mask_*.npy
"""
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.merge import merge
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling

PROJ = Path(__file__).resolve().parent.parent   # อิง __file__ ไม่ใช่ cwd (ไม่ hardcode พาธ)
DER = PROJ / "data" / "13_sentinel1_copernicus" / "derived"
DEM_DIR = PROJ / "data" / "08_dem_topography" / "raw"
RES = 1.0 / 3600.0

prov = json.load(open(DER / "osm_nakhonnayok_boundary.json", encoding="utf-8"))
geom = prov["geojson"]


def ring_bounds(g):
    import numpy as np

    def one(ring):
        a = np.array(ring)
        return a.min(0), a.max(0)

    if g["type"] == "Polygon":
        return one(g["coordinates"][0])
    mins, maxs = [], []
    for poly in g["coordinates"]:
        mn, mx = one(poly[0])
        mins.append(mn)
        maxs.append(mx)
    return np.min(mins, 0), np.max(maxs, 0)


mn, mx = ring_bounds(geom)
x0 = np.floor((mn[0] - 0.02) / RES) * RES
y0 = np.floor((mn[1] - 0.02) / RES) * RES
x1 = np.ceil((mx[0] + 0.02) / RES) * RES
y1 = np.ceil((mx[1] + 0.02) / RES) * RES
nx, ny = int((x1 - x0) / RES) + 1, int((y1 - y0) / RES) + 1
tr = from_bounds(x0, y0, x1, y1, nx, ny)
print(f"grid {nx}x{ny} bounds ({x0:.4f},{y0:.4f},{x1:.4f},{y1:.4f})")

prov_mask = rasterize([(geom, 1)], out_shape=(ny, nx), transform=tr, fill=0, dtype="uint8").astype(bool)
print("province area:", round(prov_mask.sum() * RES * 111.32 * RES * 111.32 * np.cos(np.radians(14.2)), 1), "km2")

# districts
districts = json.load(open(DER / "osm_nakhonnayok_districts.json", encoding="utf-8"))
dist_masks = {}
for name, d in districts.items():
    m = rasterize([(d["geojson"], 1)], out_shape=(ny, nx), transform=tr, fill=0, dtype="uint8").astype(bool)
    key = d["display"].split(",")[0]
    dist_masks[key] = m
    print(key, round(m.sum() * RES * 111.32 * RES * 111.32 * np.cos(np.radians(14.2)), 1), "km2")

# DEM lowland
tiles = list(DEM_DIR.glob("Copernicus_DSM_COG_10_*_DEM.tif"))
srcs = [rasterio.open(t) for t in tiles]
mosaic, mtr = merge(srcs, bounds=(x0, y0, x1, y1), res=RES, nodata=-32767.0)
dem = mosaic[0]
# merge() returns at requested res/bounds; ensure orientation matches our grid (north-up)
dst = np.full((ny, nx), np.nan, dtype=np.float32)
reproject(
    source=dem,
    destination=dst,
    src_transform=mtr,
    src_crs="EPSG:4326",
    dst_transform=tr,
    dst_crs="EPSG:4326",
    src_nodata=-32767,
    dst_nodata=np.nan,
    resampling=Resampling.bilinear,
)
lowland = (dst < 60) & prov_mask
print("lowland(<60m) area:", round(lowland.sum() * RES * 111.32 * RES * 111.32 * np.cos(np.radians(14.2)), 1), "km2")

np.save(DER / "mask_province.npy", prov_mask)
np.save(DER / "mask_lowland.npy", lowland)
np.save(DER / "dem_30m.npy", np.where(prov_mask, dst, np.nan))
for k, m in dist_masks.items():
    np.save(DER / f"mask_district_{k}.npy", m)
json.dump(
    {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "res": RES, "nx": nx, "ny": ny},
    open(DER / "grid.json", "w"),
)
print("saved masks")
