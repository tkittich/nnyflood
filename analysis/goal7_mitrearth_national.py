"""เป้าหมาย 7 — ชุดมิตรเอิร์ธฉบับสมบูรณ์ (20 ต.ค. 69): น้ำท่วม GISTDA 15 ปี (2548–2562) ตลอดแนวคลอง และเทียบน้ำท่วม 2569 · ระดับน้ำทะเลสูงขึ้นเทียบแนวคลอง · DEM 5 ม. (DEMPro) เทียบเส้นดินธรรมชาติใน EIA · บัญชีชั้นข้อมูลรายจังหวัด

ข้อมูลเข้า: data/10_mitrearth_gis/thailand_national_full/ (ชุดระดับประเทศ) · data/10_mitrearth_gis/thailand_provinces_full/ (77 จังหวัด) — ทั้งสองไม่เข้า git (เก็บ manifest + ผลสรุป)
วิธี: แนวคลองจาก official_geometry.json (หมุด กม. — ประมาณ ±0.5 กม.) · ทางเดินรอบแนว 3 กม. ทั้งสองข้าง ลงตาราง 100 ม. (UTM 47N) · รูปปิดน้ำท่วมแต่ละปีของ GISTDA (รูเปิดไม่นับ ซ้อนนับครั้งเดียว)
ข้อควรระวัง: GISTDA แต่ละปีมาจากภาพต่างวัน/ต่างเกณฑ์ ปีที่ไม่มีข้อมูลในพื้นที่ (เช่น 2554 ชั้น geo มีเพียง 87 รูปทั่วประเทศ) ไม่ได้แปลว่าไม่ท่วม · "ท่วม 15 ปี" ในที่นี้ = นับจำนวนปีที่ GISTDA แสดงน้ำท่วม ไม่ใช่ความถี่ทางสถิติ ·
ระดับน้ำทะเลสูงขึ้น (SLR) ของมิตรเอิร์ธสร้างจาก DEM ของมิตรเอิร์ธเอง (ความสูงต่างจาก FABDEM 1–4 ม.) จึงเป็นภาพรวมเชิงเปรียบเทียบ ไม่ใช่การประเมินระดับน้ำจริง
สิทธิ์ใช้งาน: ประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์

รัน: python analysis/goal7_mitrearth_national.py
ผลลัพธ์: analysis/goal7/mitrearth_national_summary.json
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import rasterio
import rasterio.features
import shapefile  # pyshp
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import LineString, shape as shp_shape
from shapely.ops import transform as shp_transform

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_mitrearth_layers as ml  # noqa: E402  (reuse-first: กริดเรดาร์ 30 ม. · หน้ากากจังหวัด)
import goal7_ongkharak_connected_fill as cf  # noqa: E402  (reuse-first: FABDEM บนกริดเรดาร์)
from goal7_fabdem_compare import FAB, GLO, sampler  # noqa: E402

NAT = ROOT / "data/10_mitrearth_gis/thailand_national_full"
PROVS = ROOT / "data/10_mitrearth_gis/thailand_provinces_full"
GEOM = ROOT / "analysis/goal7/official_geometry.json"
CANON = ROOT / "analysis/goal7/canonical.json"
OUT = ROOT / "analysis/goal7/mitrearth_national_summary.json"
TO_UTM = Transformer.from_crs(4326, 32647, always_xy=True).transform
YEARS = list(range(2005, 2020))
HALF_W_M = 3000.0
CELL_M = 100.0
GISTDA_DIR = NAT / "5 PDF Flood GISDA 2005-2019/GIS Flood GISTDA Thailand 2005-2019/1 GISTDA Flood Polygon 2005-2019"
SLR_DIR = NAT / "32 If Sea Level Rise/GIS File"


def year_file(y: int) -> Path:
    for n in (f"flood_{y}_geo", f"flood_{y}", f"flood{y}"):
        p = GISTDA_DIR / f"{n}.shp"
        if p.exists():
            return p
    raise FileNotFoundError(y)


def reader(p: Path):
    b = p.with_suffix("")
    return shapefile.Reader(shp=open(f"{b}.shp", "rb"), shx=open(f"{b}.shx", "rb"))   # ไม่อ่าน .dbf (รหัสหน้ากระดาษ 'oem 874' pyshp ไม่รู้จัก)


def reach_of(km: float) -> str:
    return "กม.0–23" if km < 23 else ("กม.23–134" if km < 134 else "กม.134–135.9")


def corridor():
    st = json.loads(GEOM.read_text(encoding="utf-8"))["stations"]
    km = np.array([s["km"] for s in st])
    xs, ys = np.array([s["x"] for s in st]), np.array([s["y"] for s in st])
    line = LineString(np.column_stack([xs, ys]))
    poly = line.buffer(HALF_W_M)
    tr = rasterio.transform.from_origin(np.floor(poly.bounds[0] / CELL_M) * CELL_M, np.ceil(poly.bounds[3] / CELL_M) * CELL_M, CELL_M, CELL_M)
    shape = (int((np.ceil(poly.bounds[3] / CELL_M) * CELL_M - np.floor(poly.bounds[1] / CELL_M) * CELL_M) / CELL_M), int((np.ceil(poly.bounds[2] / CELL_M) * CELL_M - np.floor(poly.bounds[0] / CELL_M) * CELL_M) / CELL_M))
    mask = rasterio.features.rasterize([(poly, 1)], out_shape=shape, transform=tr, fill=0, dtype="uint8").astype(bool)
    rows, cols = np.where(mask)
    cx, cy = rasterio.transform.xy(tr, rows, cols, offset="center")
    tree = cKDTree(np.column_stack([xs, ys]))
    _, idx = tree.query(np.column_stack([cx, cy]))
    kmcell = np.full(shape, np.nan)
    kmcell[rows, cols] = km[idx]
    lon, lat = (np.array([s["lon"] for s in st]), np.array([s["lat"] for s in st]))
    bbox = (lon.min() - 0.1, lat.min() - 0.1, lon.max() + 0.1, lat.max() + 0.1)
    return {"poly": poly, "tr": tr, "shape": shape, "mask": mask, "km": kmcell, "bbox": bbox, "stations": st}


def shapes_in(p: Path, bbox):
    r = reader(p)
    for s in r.iterShapes(bbox=list(bbox)):
        try:
            g = shp_shape(s.__geo_interface__)
        except Exception:   # noqa: BLE001
            continue
        if not g.is_valid:
            g = g.buffer(0)
        if not g.is_empty:
            yield g


def raster_years(c) -> tuple[np.ndarray, dict]:
    count = np.zeros(c["shape"], dtype=np.uint8)
    per_year = {}
    for y in YEARS:
        gs = [shp_transform(TO_UTM, g) for g in shapes_in(year_file(y), c["bbox"])]
        gs = [g for g in gs if g.intersects(c["poly"])]
        if gs:
            a = rasterio.features.rasterize(((g, 1) for g in gs), out_shape=c["shape"], transform=c["tr"], fill=0, dtype="uint8").astype(bool) & c["mask"]
        else:
            a = np.zeros(c["shape"], dtype=bool)
        count += a.astype(np.uint8)
        per_year[y] = a
    return count, per_year


def corridor_flood(c) -> dict:
    count, per_year = raster_years(c)
    cell_km2 = CELL_M * CELL_M / 1e6
    out = {"corridor_half_width_m": HALF_W_M, "cell_m": CELL_M, "corridor_km2": round(float(c["mask"].sum()) * cell_km2, 1), "by_year_km2": {}, "by_reach": {}}
    for y, a in per_year.items():
        out["by_year_km2"][str(y)] = round(float(a.sum()) * cell_km2, 1)
    for r in ("กม.0–23", "กม.23–134", "กม.134–135.9"):
        sel = np.zeros(c["shape"], dtype=bool)
        kmc = c["km"]
        lo, hi = {"กม.0–23": (0, 23), "กม.23–134": (23, 134), "กม.134–135.9": (134, 136)}[r]
        sel = c["mask"] & (kmc >= lo) & (kmc < hi)
        tot = float(sel.sum())
        if not tot:
            continue
        cnt = count[sel]
        out["by_reach"][r] = {"area_km2": round(tot * cell_km2, 1), "ever_flooded_pct": round(100.0 * float((cnt > 0).sum()) / tot, 1), "flooded_3plus_years_pct": round(100.0 * float((cnt >= 3).sum()) / tot, 1),
                              "flooded_6plus_years_pct": round(100.0 * float((cnt >= 6).sum()) / tot, 1), "max_years": int(cnt.max()),
                              "by_year_pct": {str(y): round(100.0 * float(per_year[y][sel].sum()) / tot, 1) for y in YEARS}}
    # ตามกม. (ทุก 10 กม.) — ร้อยละที่เคยท่วมอย่างน้อย 1 ปี
    seg = {}
    for lo in range(0, 136, 10):
        sel = c["mask"] & (c["km"] >= lo) & (c["km"] < lo + 10)
        if sel.any():
            seg[f"{lo}-{min(lo + 10, 135.9):g}"] = {"ever_pct": round(100.0 * float((count[sel] > 0).mean()), 1), "mean_years": round(float(count[sel].mean()), 2)}
    out["by_10km"] = seg
    return out, count


def vs_2026() -> dict:
    prov = np.load(ml.DER / "mask_province.npy")
    flood = {"peak_27sep": np.load(ml.DER / "flood_peak_27sep1828.npy").astype(bool), "oct2_validated": np.load(ml.DER / "flood_2oct_validated.npy").astype(bool)}
    bb = (ml.GRID["x0"], ml.GRID["y0"], ml.GRID["x1"], ml.GRID["y1"])
    count = np.zeros(ml.SHAPE, dtype=np.uint8)
    for y in YEARS:
        gs = list(shapes_in(year_file(y), bb))
        if gs:
            count += ml.rasterize(gs).astype(np.uint8)
    res = {"years": f"{YEARS[0]}–{YEARS[-1]}", "grid_km2": round(float(prov.size) * ml.CELL_KM2, 0), "past_flood_ever_in_province_pct": round(100.0 * float(((count > 0) & prov).sum()) / float(prov.sum()), 1)}
    for k, f in flood.items():
        s = f & prov
        tot = float(s.sum())
        res[k] = {"flooded_2026_km2_in_province": round(tot * ml.CELL_KM2, 1), "share_flooded_in_any_past_year_pct": round(100.0 * float((s & (count > 0)).sum()) / tot, 1),
                  "by_number_of_past_years_pct": {str(n): round(100.0 * float((s & (count == n)).sum()) / tot, 1) for n in range(0, int(count.max()) + 1)},
                  "share_flooded_6plus_past_years_pct": round(100.0 * float((s & (count >= 6)).sum()) / tot, 1)}
    return res


def slr(c) -> dict:
    out = {}
    st = c["stations"]
    km = np.array([s["km"] for s in st])
    xs, ys = np.array([s["x"] for s in st]), np.array([s["y"] for s in st])
    dense = np.arange(km[0], km[-1], 0.1)
    dx, dy = np.interp(dense, km, xs), np.interp(dense, km, ys)
    pts = np.column_stack([dx, dy])
    for p in sorted(SLR_DIR.glob("1 Sea Level Rise * m - mitrearth.shp"), key=lambda q: int(re.search(r"Rise (\d+) m", q.name).group(1))):
        lvl = int(re.search(r"Rise (\d+) m", p.name).group(1))
        gs = [shp_transform(TO_UTM, g) for g in shapes_in(p, c["bbox"])]
        gs = [g for g in gs if g.intersects(c["poly"])]
        if not gs:
            out[str(lvl)] = {"axis_km_inside": 0.0, "corridor_pct": 0.0}
            continue
        a = rasterio.features.rasterize(((g, 1) for g in gs), out_shape=c["shape"], transform=c["tr"], fill=0, dtype="uint8").astype(bool) & c["mask"]
        rr, cc = rasterio.transform.rowcol(c["tr"], pts[:, 0], pts[:, 1])
        rr, cc = np.array(rr), np.array(cc)
        ok = (rr >= 0) & (rr < c["shape"][0]) & (cc >= 0) & (cc < c["shape"][1])
        inside = np.zeros(len(dense), dtype=bool)
        inside[ok] = a[rr[ok], cc[ok]]
        reach = defaultdict(float)
        for k_, v in zip(dense, inside):
            if v:
                reach[reach_of(float(k_))] += 0.1
        first = float(dense[inside].min()) if inside.any() else None
        out[str(lvl)] = {"axis_km_inside": round(float(inside.sum()) * 0.1, 1), "axis_first_km_inside": round(first, 1) if first is not None else None, "by_reach_km": {k: round(v, 1) for k, v in reach.items()}, "corridor_pct": round(100.0 * float(a.sum()) / float(c["mask"].sum()), 1)}
    return out


def dempro_vs_eia(c) -> dict:
    """DEM 5 ม. (DEMPro) ในช่วงที่หน้าต่างครอบแนวคลอง เทียบ FABDEM · Copernicus · DEM 30 ม. ของมิตรเอิร์ธ และเส้นดินธรรมชาติใน EIA (อ่านจากรูป ±0.2 ม.)"""
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    gp = canon["eia_profile"]["ground_readings"]
    st = c["stations"]
    km = np.array([s["km"] for s in st])
    lon = np.array([s["lon"] for s in st])
    lat = np.array([s["lat"] for s in st])
    fab = sampler(FAB, "N{lat}E{lon}_FABDEM_V1-2.tif")
    glo = sampler(GLO, "Copernicus_DSM_COG_10_N{lat}_00_E{lon}_00_DEM.tif")
    res = {}
    for d in sorted(PROVS.iterdir()):
        if not re.match(r"^\d+ ", d.name) or d.name.startswith("0 "):
            continue
        num = d.name.split()[0]
        gf = next((x for x in d.iterdir() if x.is_dir() and x.name.startswith(num + " ") and "GIS" not in x.name and "GE" not in x.name), None)
        dp = next(iter((gf / "GIS File").glob("*DEMPro*.grd")), None) if gf and (gf / "GIS File").exists() else None
        if not dp:
            continue
        with rasterio.open(dp) as ds:
            b = ds.bounds
            sel = (lon >= b.left) & (lon <= b.right) & (lat >= b.bottom) & (lat <= b.top)
            if not sel.any():
                continue
            a = ds.read(1).astype("float32")
            a[a > 1e10] = np.nan
            gis = next(x for x in d.iterdir() if x.is_dir() and " GIS " in x.name)
            d30p = next(iter((gis / "1 Digital Elevation Model (DEM)").glob("*DEM30m*.grd")), None)
            d30 = rasterio.open(d30p) if d30p else None
            a30 = None
            if d30:
                a30 = d30.read(1).astype("float32")
                a30[a30 > 1e10] = np.nan
            rows = []
            for k, lo, la, x_, y_ in zip(km[sel], lon[sel], lat[sel], np.array([s["x"] for s in st])[sel], np.array([s["y"] for s in st])[sel]):
                # ค่ากลางในแถบ ±300 ม. รอบจุดแนว (ทุกทิศ) — แนวคลองคลาดได้ ~0.5 กม.
                vals = {"dempro": [], "dem30": [], "fabdem": [], "glo30": []}
                for dx in np.arange(-300, 301, 100):
                    for dy in np.arange(-300, 301, 100):
                        lo2, la2 = Transformer.from_crs(32647, 4326, always_xy=True).transform(x_ + dx, y_ + dy)
                        r_, c_ = ds.index(lo2, la2)
                        if 0 <= r_ < ds.height and 0 <= c_ < ds.width and not np.isnan(a[r_, c_]):
                            vals["dempro"].append(float(a[r_, c_]))
                        if d30 is not None:
                            r2, c2 = d30.index(lo2, la2)
                            if 0 <= r2 < d30.height and 0 <= c2 < d30.width and not np.isnan(a30[r2, c2]):
                                vals["dem30"].append(float(a30[r2, c2]))
                        f_, g_ = fab(lo2, la2), glo(lo2, la2)
                        if f_ is not None:
                            vals["fabdem"].append(float(f_))
                        if g_ is not None:
                            vals["glo30"].append(float(g_))
                rows.append((float(k), float(np.interp(k, [p[0] for p in gp], [p[1] for p in gp])), {k_: (float(np.median(v)) if v else None) for k_, v in vals.items()}))
            eia = np.array([r[1] for r in rows])
            out = {"canal_km_in_window": [round(float(km[sel].min()), 1), round(float(km[sel].max()), 1)], "n_points": len(rows), "eia_ground_mean_m": round(float(eia.mean()), 2), "dem_minus_eia_ground": {}}
            for name in ("dempro", "dem30", "fabdem", "glo30"):
                v = np.array([r[2][name] if r[2][name] is not None else np.nan for r in rows])
                dd = v - eia
                dd = dd[~np.isnan(dd)]
                if len(dd):
                    out["dem_minus_eia_ground"][name] = {"mean_m": round(float(dd.mean()), 2), "mae_m": round(float(np.abs(dd).mean()), 2), "sd_m": round(float(dd.std()), 2), "n": int(len(dd))}
            res[d.name] = out
    return res


def inventory() -> dict:
    rows = []
    for d in sorted(PROVS.iterdir()):
        if not re.match(r"^\d+ ", d.name) or d.name.startswith("0 "):
            continue
        num = d.name.split()[0]
        gis = next((x for x in d.iterdir() if x.is_dir() and " GIS " in x.name), None)
        gf = next((x for x in d.iterdir() if x.is_dir() and x.name.startswith(num + " ") and "GIS" not in x.name and "GE" not in x.name), None)
        g7 = list((gis / "7 Geological Hazard").glob("*GISTDA*.shp")) if gis and (gis / "7 Geological Hazard").exists() else []
        rows.append({"province": d.name, "gistda": bool(g7) and g7[0].with_suffix(".dbf").exists(), "dempro_5m": bool(gf and (gf / "GIS File").exists() and list((gf / "GIS File").glob("*DEMPro*.grd"))),
                     "basin": bool(gis and any((gis / "6 Valley Ridge and Basin").glob("* Drainage Basin.shp"))) if gis and (gis / "6 Valley Ridge and Basin").exists() else False,
                     "contour_1m": bool(gis and any((gis / "4 Contour Line").glob("*Contour1m.shp"))) if gis and (gis / "4 Contour Line").exists() else False})
    return {"provinces": len(rows), "with_gistda_flood": sum(r["gistda"] for r in rows), "with_dempro_5m": sum(r["dempro_5m"] for r in rows), "with_basin": sum(r["basin"] for r in rows), "with_contour_1m": sum(r["contour_1m"] for r in rows),
            "without_gistda": [r["province"] for r in rows if not r["gistda"]], "detail": rows}


def main() -> None:
    t0 = time.time()
    c = corridor()
    flood, _ = corridor_flood(c)
    print("corridor flood done", round(time.time() - t0), "s", flush=True)
    res = {"source": {"national": "data/10_mitrearth_gis/thailand_national_full/", "provinces": "data/10_mitrearth_gis/thailand_provinces_full/", "license_note": "ประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์"},
           "gistda_corridor_2005_2019": flood, "gistda_vs_2026_nakhon_nayok": vs_2026(), "sea_level_rise_vs_canal": slr(c), "dempro_vs_eia_ground": dempro_vs_eia(c), "inventory": inventory()}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("by_reach", {k: (v["ever_flooded_pct"], v["flooded_3plus_years_pct"], v["max_years"]) for k, v in flood["by_reach"].items()})
    print("by_year", flood["by_year_km2"])
    v = res["gistda_vs_2026_nakhon_nayok"]
    print("2026", {k: (v[k]["share_flooded_in_any_past_year_pct"], v[k]["share_flooded_6plus_past_years_pct"]) for k in ("peak_27sep", "oct2_validated")})
    print("slr", {k: (x["axis_km_inside"], x.get("axis_first_km_inside")) for k, x in res["sea_level_rise_vs_canal"].items()})
    print("dempro", {k[:12]: v["dem_minus_eia_ground"] for k, v in res["dempro_vs_eia_ground"].items()})
    print("inventory", {k: res["inventory"][k] for k in ("provinces", "with_gistda_flood", "with_dempro_5m", "with_basin", "with_contour_1m")})


if __name__ == "__main__":
    main()
