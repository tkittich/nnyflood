"""Paired same-orbit change detection for the 3 new dates + stats + frames.

Pairs (12-day same orbit, locked rule: dVH<=-1 & dVV<=-2 & VH<=-18 & lowland & opening 3x3):
  27 Sep 06:00 local (26 Sep 23 UTC a+b) vs 15 Sep 06:00 (14 Sep 23 UTC a+b)  -> frame-2 verdict
  28 Sep 18:19 (S1C)  vs 16 Sep 18:19 (S1C)
  22 Sep 18:20 (a+b)  vs 10 Sep 18:20 (a+b)
"""
import json
import math
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_opening

DER = Path(__file__).resolve().parent.parent / "data" / "13_sentinel1_copernicus" / "derived"  # อิง __file__
g = json.load(open(DER / "grid.json"))
RES = g["res"]
nx, ny = g["nx"], g["ny"]
cell = RES * 111.32 * RES * 111.32 * math.cos(math.radians(14.2))
lowland = np.load(DER / "mask_lowland.npy")
prov = np.load(DER / "mask_province.npy")

def merged(tag_a, tag_b, pol="vh"):
    a = np.load(DER / f"{tag_a}_{pol}_db.npy")
    if tag_b:
        b = np.load(DER / f"{tag_b}_{pol}_db.npy")
        va, vb = np.isfinite(a), np.isfinite(b)
        m = np.where(va, a, b)
        both = va & vb
        m[both] = (a[both] + b[both]) / 2
        return m, va | vb
    return a, np.isfinite(a)

PAIRS = [
    ("2026-09-22 18:20", "s1d_20260922_1820_a", "s1d_20260922_1820_b", "s1d_20260910_1820_a", "s1d_20260910_1820_b"),
    ("2026-09-27 06:00", "s1d_20260927_0600_a", "s1d_20260927_0600_b", "s1d_20260915_0600_a", "s1d_20260915_0600_b"),
    ("2026-09-28 18:19", "s1c_20260928_1820", None, "s1c_20260916_1820", None),
]

results = {}
for label, pa, pb, qa, qb in PAIRS:
    vh_post, valid = merged(pa, pb, "vh")
    vh_pre, _ = merged(qa, qb, "vh")
    vv_post, _ = merged(pa, pb, "vv")
    vv_pre, _ = merged(qa, qb, "vv")
    ok = np.isfinite(vh_pre) & np.isfinite(vh_post) & np.isfinite(vv_pre) & np.isfinite(vv_post) & lowland
    w = (vh_post - vh_pre <= -1.0) & (vv_post - vv_pre <= -2.0) & (vh_post <= -18.0) & ok
    w = binary_opening(w, structure=np.ones((3, 3)))
    cov = float((valid & prov).sum() / prov.sum() * 100)
    area = float(w.sum() * cell)
    results[label] = {"area_km2": round(area, 1), "coverage_pct": round(cov, 1), "mask": w}
    np.save(DER / f"flood_{label[:10].replace('-', '')}_{label[11:16].replace(':', '')}.npy", w)
    dist = {}
    for f in sorted(DER.glob("mask_district_*.npy")):
        m = np.load(f)
        dist[f.stem.replace("mask_district_", "")] = round(float((w & m).sum() * cell), 1)
    results[label]["districts"] = dist
    print(f"{label}: {area:.1f} km2 | coverage {cov:.0f}% | {dist}")

json.dump({k: {"area_km2": v["area_km2"], "coverage_pct": v["coverage_pct"], "districts": v["districts"]}
           for k, v in results.items()},
          open(DER / "flood_series_ours.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved flood_series_ours.json")
