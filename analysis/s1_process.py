"""
Sentinel-1 GRDH COG processing for Nakhon Nayok flood mapping.

Pipeline per scene:
  1. Parse annotation XML geolocation grid (GCPs, 10x21) -> forward cubic
     spline + Newton inversion to map (lon,lat)->(line,pixel).
  2. Parse calibration XML sigmaNought LUT -> 2D spline; sigma0 = DN^2/A^2.
  3. Sample VV/VH onto the shared 30 m WGS84 grid (grid.json from s1_masks.py),
     speckle 5x5 mean filter, water mask = VH dB < threshold.
  4. Stats within province and lowland(<60 m) masks; per district.

Usage:
  python s1_process.py <SAFE_dir> <tag> [--threshold db]
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from common import cell_km2
import rasterio
from rasterio.transform import from_bounds
from scipy.interpolate import RectBivariateSpline
from scipy.ndimage import map_coordinates, uniform_filter
from scipy.spatial import cKDTree

PROJ = Path(__file__).resolve().parent.parent   # อิง __file__ ไม่ใช่ cwd (ไม่ hardcode พาธ)
DER = PROJ / "data" / "13_sentinel1_copernicus" / "derived"


def parse_gcps(ann_xml: str):
    pts = re.findall(
        r"<geolocationGridPoint>(.*?)</geolocationGridPoint>", ann_xml, re.S
    )
    line, pixel, lat, lon = [], [], [], []
    for p in pts:
        line.append(float(re.search(r"<line>([-\d.eE+]+)</line>", p).group(1)))
        pixel.append(float(re.search(r"<pixel>([-\d.eE+]+)</pixel>", p).group(1)))
        lat.append(float(re.search(r"<latitude>([-\d.eE+]+)</latitude>", p).group(1)))
        lon.append(float(re.search(r"<longitude>([-\d.eE+]+)</longitude>", p).group(1)))
    return map(np.array, (line, pixel, lat, lon))


def build_geocode(ann_xml: str):
    """(lon,lat)->(line,pixel) via forward GCP spline + Newton inversion."""
    line, pixel, lat, lon = parse_gcps(ann_xml)
    ul, up = np.unique(line), np.unique(pixel)
    li = np.searchsorted(ul, line)
    pi = np.searchsorted(up, pixel)
    lon_g = np.full((ul.size, up.size), np.nan)
    lat_g = np.full_like(lon_g, np.nan)
    lon_g[li, pi] = lon
    lat_g[li, pi] = lat
    assert not np.isnan(lon_g).any()
    spl_lon = RectBivariateSpline(ul, up, lon_g, kx=3, ky=3)
    spl_lat = RectBivariateSpline(ul, up, lat_g, kx=3, ky=3)
    tree = cKDTree(np.column_stack([lon, lat]))

    def invert(lo, la, n_iter=8):
        lo = np.asarray(lo, dtype=float)
        la = np.asarray(la, dtype=float)
        _, k = tree.query(np.column_stack([lo.ravel(), la.ravel()]))
        l = line[k].reshape(lo.shape).astype(float)
        p = pixel[k].reshape(lo.shape).astype(float)
        lmin, lmax, pmin, pmax = ul[0], ul[-1], up[0], up[-1]
        for _ in range(n_iter):
            f0 = spl_lon.ev(l, p) - lo
            f1 = spl_lat.ev(l, p) - la
            d = 0.5
            j00 = spl_lon.ev(l + d, p) - spl_lon.ev(l - d, p)
            j01 = spl_lon.ev(l, p + d) - spl_lon.ev(l, p - d)
            j10 = spl_lat.ev(l + d, p) - spl_lat.ev(l - d, p)
            j11 = spl_lat.ev(l, p + d) - spl_lat.ev(l, p - d)
            det = j00 * j11 - j01 * j10
            det = np.where(np.abs(det) < 1e-15, 1e-15, det)
            l = np.clip(l - (f0 * j11 - f1 * j01) / det * (2 * d), lmin, lmax)
            p = np.clip(p - (f1 * j00 - f0 * j10) / det * (2 * d), pmin, pmax)
        return l, p

    lc, pc = invert(lon, lat)
    err = max(np.abs(lc - line).max(), np.abs(pc - pixel).max())
    return invert, float(err)


def parse_cal_lut(cal_xml: str):
    blocks = re.findall(r"<calibrationVector>(.*?)</calibrationVector>", cal_xml, re.S)
    lines, pix_list, sig_rows = [], None, []
    for b in blocks:
        lines.append(float(re.search(r"<line>([-\d.eE+]+)</line>", b).group(1)))
        pix = np.array(
            re.search(r"<pixel[^>]*>(.*?)</pixel>", b, re.S).group(1).split(), dtype=float
        )
        if pix_list is None:
            pix_list = pix
        sig_rows.append(
            np.array(
                re.search(r"<sigmaNought[^>]*>(.*?)</sigmaNought>", b, re.S).group(1).split(),
                dtype=float,
            )
        )
    lines = np.array(lines)
    lut = np.stack(sig_rows)
    if lines.size == 1:
        lines = np.array([lines[0] - 1, lines[0] + 1])
        lut = np.repeat(lut, 2, axis=0)
    if pix_list.size == 1:
        pix_list = np.array([pix_list[0] - 1, pix_list[0] + 1])
        lut = np.repeat(lut, 2, axis=1)
    return RectBivariateSpline(lines, pix_list, lut, kx=3, ky=3)


def otsu(values, n_bins=256):
    hist, edges = np.histogram(values, bins=n_bins)
    centers = (edges[:-1] + edges[1:]) / 2
    w = np.cumsum(hist)
    mu = np.cumsum(hist * centers)
    tot_w, tot_mu = w[-1], mu[-1]
    var_between = (tot_mu * w - mu) ** 2 / (w * (tot_w - w) + 1e-9)
    return centers[np.argmax(var_between)]


def main():
    safe = Path(sys.argv[1])
    tag = sys.argv[2]
    thr_override = None
    if "--threshold" in sys.argv:
        thr_override = float(sys.argv[sys.argv.index("--threshold") + 1])

    g = json.load(open(DER / "grid.json"))
    x0, y0, x1, y1, RES = g["x0"], g["y0"], g["x1"], g["y1"], g["res"]
    nx, ny = g["nx"], g["ny"]
    tr = from_bounds(x0, y0, x1, y1, nx, ny)
    cell = cell_km2(RES)

    prov_mask = np.load(DER / "mask_province.npy")
    lowland = np.load(DER / "mask_lowland.npy")
    dist_files = sorted(DER.glob("mask_district_*.npy"))

    ann_files = sorted((safe / "annotation").glob("s1*-iw-grd-v*-cog.xml"))
    ann = ann_files[0].read_text(encoding="utf-8")
    invert, err = build_geocode(ann)
    print(f"[{tag}] geocode roundtrip error {err:.2f} px")

    glon, glat = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(y1, y0, ny))
    lr, pr = invert(glon, glat)

    for pol in ("vh", "vv"):
        ann_pol = [p for p in ann_files if f"-{pol}-" in p.name][0]
        cal_pol = [
            c
            for c in (safe / "annotation" / "calibration").glob("calibration-*.xml")
            if f"-{pol}-" in c.name
        ][0]
        spl = parse_cal_lut(cal_pol.read_text(encoding="utf-8"))
        tif = [m for m in (safe / "measurement").glob("*-cog.tiff") if f"-{pol}-" in m.name][0]
        with rasterio.open(tif) as ds:
            H, W = ds.height, ds.width
            dn = ds.read(1).astype(np.float32)
        valid = (lr >= 1) & (lr <= H - 2) & (pr >= 1) & (pr <= W - 2)
        coords = np.stack([np.clip(lr, 0, H - 1), np.clip(pr, 0, W - 1)])
        sampled = map_coordinates(dn, coords, order=1, mode="nearest")
        a_lut = spl.ev(lr, pr).astype(np.float32)
        sig = np.where(
            (sampled > 0) & (a_lut > 0),
            sampled**2 / np.maximum(a_lut, 1e-6) ** 2,
            np.nan,
        )
        db = (10.0 * np.log10(sig)).astype(np.float32)
        fill = np.nanmedian(db[valid]) if valid.any() else -20.0
        db_s = uniform_filter(np.where(valid, db, fill), size=5)
        db_s = np.where(valid, db_s, np.nan).astype(np.float32)
        np.save(DER / f"{tag}_{pol}_db.npy", db_s)
        prof = dict(
            driver="GTiff", height=ny, width=nx, count=1, dtype="float32",
            crs="EPSG:4326", transform=tr, nodata=np.nan, compress="lzw",
        )
        with rasterio.open(DER / f"{tag}_{pol}_db.tif", "w", **prof) as dst:
            dst.write(db_s, 1)
        print(f"[{tag}] {pol} median {np.nanmedian(db_s):.1f} dB, coverage "
              f"{(valid & prov_mask).sum() / prov_mask.sum() * 100:.0f}% of province")

    vh = np.load(DER / f"{tag}_vh_db.npy")
    plain = lowland & np.isfinite(vh)
    if thr_override is None:
        thr = float(np.clip(otsu(vh[plain]), -24.0, -14.0))
    else:
        thr = thr_override
    water = (vh < thr) & plain

    prof = dict(
        driver="GTiff", height=ny, width=nx, count=1, dtype="uint8",
        crs="EPSG:4326", transform=tr, nodata=255, compress="lzw",
    )
    w_out = np.where(plain, water.astype("uint8"), 255)
    with rasterio.open(DER / f"{tag}_water.tif", "w", **prof) as dst:
        dst.write(w_out, 1)

    districts = {}
    for f in dist_files:
        name = f.stem.replace("mask_district_", "")
        districts[name] = round(float((water & np.load(f)).sum() * cell), 1)
    stats = {
        "tag": tag,
        "safe": safe.name,
        "threshold_db": round(thr, 2),
        "water_km2_lowland": round(float(water.sum() * cell), 1),
        "water_km2_by_district": districts,
        "vh_median_db": round(float(np.nanmedian(vh)), 1),
    }
    (DER / f"{tag}_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
