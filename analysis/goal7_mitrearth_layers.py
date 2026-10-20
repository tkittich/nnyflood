"""เป้าหมาย 7 — ประมวลผลชั้นข้อมูลมิตรเอิร์ธที่มีอยู่ในคลังแล้ว (R7-14): (ก) ขอบเขตน้ำท่วม GISTDA ปี 2548–2554 เทียบน้ำท่วม 2569 จากเรดาร์
(ข) ลุ่มน้ำย่อยของมิตรเอิร์ธ เทียบพื้นที่รับน้ำย่อย PK-AT-4 ของ EIA (ค) เส้นชั้นความสูง 1 ม. เทียบ FABDEM และ Copernicus DSM

แหล่ง: data/manual/18 นครนายก (NAKHON NAYOK).zip (ชุดมิตรเอิร์ธเต็มจังหวัด · SHA-256 ใน data/10_mitrearth_gis/manifest.md) · แตกเฉพาะไฟล์ที่ใช้ไปไว้ที่
data/10_mitrearth_gis/extracted_full/ (disk-only) · ตารางเวลา/ตาราง 2569: data/13_sentinel1_copernicus/derived (ตารางกริด 30 ม. + มาสก์เรดาร์)
ข้อควรระวังที่บันทึกไว้ในผล: (1) ไฟล์ .prj ของชั้น GISTDA ว่างเปล่า — สมมติ WGS84 (พิกัดอยู่ในช่วง 100.9–101.3°E 13.96–14.36°N) (2) ปี 0 = รูปปิดไม่ระบุปี ไม่นับ
(3) เส้นชั้น 1 ม. มี 2 ชุด: `GIS File/18 Contour 1 m…` (10,592 เส้น ครอบหน้าต่าง DEMPro 5 ม.) สร้างจาก DEMPro (ตรวจแล้ว: DEMPro−เส้นชั้น เฉลี่ย +0.03 ม. MAE 0.12 ม.) · `4 Contour Line/18 Contour1m.shp` (111,298 เส้น ทั้งจังหวัด) สร้างจาก DEM 30 ม. ของมิตรเอิร์ธ (MAE 0.42 ม.) การเทียบกับ DEM จึงวัดความสอดคล้อง ไม่ใช่ความถูกต้องเทียบการสำรวจ
สิทธิ์ใช้งานของชั้นข้อมูล: เพื่อประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์ (ดู manifest)

รัน: python analysis/goal7_mitrearth_layers.py
ผลลัพธ์: analysis/goal7/mitrearth_layers_summary.json
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
import rasterio.features
import shapefile  # pyshp (นำเข้าด้วยชื่อ shapefile)
from pyproj import Transformer
from shapely.geometry import shape as shp_shape
from shapely.ops import transform as shp_transform

sys.path.insert(0, str(Path(__file__).resolve().parent))
from goal7_fabdem_compare import FAB, GLO, sampler  # noqa: E402  (reuse-first: ตัวสุ่มค่าความสูงชุดเดียวกับที่เทียบ FABDEM ตามแนวคลอง)

ROOT = Path(__file__).resolve().parent.parent
ZIP = ROOT / "data/manual/18 นครนายก (NAKHON NAYOK).zip"
EXT = ROOT / "data/10_mitrearth_gis/extracted_full"
DER = ROOT / "data/13_sentinel1_copernicus/derived"
OUT = ROOT / "analysis/goal7/mitrearth_layers_summary.json"
GRID = json.loads((DER / "grid.json").read_text(encoding="utf-8"))
TRANSFORM = rasterio.transform.from_origin(GRID["x0"], GRID["y1"], GRID["res"], GRID["res"])
SHAPE = (GRID["ny"], GRID["nx"])
CELL_KM2 = 900.0 / 1e6
EIA_PK_AT_4_RAI = 206224          # รายงานผลกระทบสิ่งแวดล้อม 2569 (ตารางลุ่มรับน้ำย่อย) — ดู canonical eia_profile
RAI_KM2 = 1600.0 / 1e6
MEMBERS = {
    "gistda": "18 Flood GISTDA 0519 NAKHON NAYOK",
    "basin": "18 Drainage Basin",
    "contour1m": "18 Contour 1 m NAKHON NAYOK - mitrearth",
    "contour1m_prov": "18 Contour1m",
}
GRIDS = {"dempro": "GIS File/18 DEMPro NAKHON NAYOK - mitrearth.grd", "dem30": "1 Digital Elevation Model (DEM)/18 DEM30m - mitrearth.grd"}


def extract() -> dict[str, Path]:
    EXT.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    with zipfile.ZipFile(ZIP) as z:
        for key, stem in MEMBERS.items():
            for n in z.namelist():
                base = n.rsplit("/", 1)[-1]
                if base.startswith(stem) and base.rsplit(".", 1)[-1] in ("shp", "dbf", "shx", "prj", "cpg") and "GIS" in n:
                    dst = EXT / base
                    if not dst.exists():
                        dst.write_bytes(z.read(n))
                    if base.endswith(".shp"):
                        out[key] = dst
    return out


def rasterize(geoms: list) -> np.ndarray:
    """รูปปิด (มีรูเปิดตามทิศวงแหวน) → ตารางกริดเดียวกับมาสก์เรดาร์ · ซ้อนทับกันนับครั้งเดียว"""
    if not geoms:
        return np.zeros(SHAPE, dtype=bool)
    return rasterio.features.rasterize(((g, 1) for g in geoms), out_shape=SHAPE, transform=TRANSFORM, fill=0, dtype="uint8").astype(bool)


def part_a_gistda(shp: Path, province: np.ndarray) -> dict:
    r = shapefile.Reader(str(shp))
    fields = [f[0] for f in r.fields[1:]]
    iy = fields.index("year")
    by_year: dict[int, list] = {}
    gross: dict[int, float] = {}
    for sr in r.iterShapeRecords():
        yr = int(sr.record[iy])
        g = shp_shape(sr.shape.__geo_interface__)
        if not g.is_valid:
            g = g.buffer(0)
        by_year.setdefault(yr, []).append(g)
    rasters = {y: rasterize(gs) & province for y, gs in by_year.items()}
    flood26 = {
        "peak_27sep": np.load(DER / "flood_peak_27sep1828.npy").astype(bool) & province,
        "oct2_validated": np.load(DER / "flood_2oct_validated.npy").astype(bool) & province,
    }
    years = sorted(y for y in rasters if y > 0)
    per_year = {}
    for y in years:
        a = rasters[y]
        row = {"polygons": len(by_year[y]), "area_km2_net_in_province": round(float(a.sum()) * CELL_KM2, 1),
               "share_of_province_pct": round(100.0 * float(a.sum()) / float(province.sum()), 1)}
        for k, f in flood26.items():
            inter = float((a & f).sum())
            union = float((a | f).sum())
            row[f"vs_2026_{k}"] = {"intersection_km2": round(inter * CELL_KM2, 1), "iou": round(inter / union, 3) if union else None,
                                   "share_of_2026_also_flooded_that_year_pct": round(100.0 * inter / float(f.sum()), 1),
                                   "share_of_that_year_also_flooded_2026_pct": round(100.0 * inter / float(a.sum()), 1) if a.sum() else None}
        per_year[str(y)] = row
    count = np.zeros(SHAPE, dtype=np.uint8)
    for y in years:
        count += rasters[y].astype(np.uint8)
    recurrence = {}
    for k, f in flood26.items():
        tot = float(f.sum())
        recurrence[k] = {"area_2026_km2": round(tot * CELL_KM2, 1),
                         "by_number_of_past_flood_years": {str(n): round(100.0 * float((f & (count == n)).sum()) / tot, 1) for n in range(0, len(years) + 1)}}
    unknown = rasters.get(0)
    return {
        "years_in_layer": [int(y) for y in sorted(by_year)],
        "per_year": per_year,
        "recurrence_of_2026_footprint_pct": recurrence,
        "ever_flooded_2548_2554_km2": round(float((count > 0).sum()) * CELL_KM2, 1),
        "unknown_year_polygons": {"polygons": len(by_year.get(0, [])), "area_km2_in_province": round(float(unknown.sum()) * CELL_KM2, 1) if unknown is not None else 0.0,
                                  "note": "ไม่ระบุปี — ไม่นับในตารางรายปี"},
        "crs_note": ".prj ว่างเปล่า — สมมติ WGS84",
        "reading_note": "ต่างชุดข้อมูลกัน (GISTDA ภาพออปติคัล/เรดาร์ต่างปี vs เรดาร์ Sentinel-1 ของโครงการ) เกณฑ์ตรวจน้ำต่างกัน เทียบพื้นที่ได้เชิงขนาด ไม่ใช่การตรวจความถูกต้องรายพิกเซล",
    }


def part_b_basin(shp: Path) -> dict:
    r = shapefile.Reader(str(shp))
    fields = [f[0] for f in r.fields[1:]]
    to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32647", always_xy=True).transform
    basins = []
    for sr in r.iterShapeRecords():
        g = shp_shape(sr.shape.__geo_interface__)
        if not g.is_valid:
            g = g.buffer(0)
        a = shp_transform(to_utm, g).area / 1e6
        basins.append({"area_km2": round(a, 1), "attrs": {k: (v if isinstance(v, (int, float, str)) else str(v)) for k, v in zip(fields, sr.record)}})
    basins.sort(key=lambda b: -b["area_km2"])
    target = EIA_PK_AT_4_RAI * RAI_KM2
    nearest = min(basins, key=lambda b: abs(b["area_km2"] - target))
    within10 = [b for b in basins if abs(b["area_km2"] - target) / target <= 0.10]
    return {
        "n_basins": len(basins), "fields": fields,
        "largest_5_km2": [b["area_km2"] for b in basins[:5]],
        "eia_pk_at_4_km2": round(target, 1), "eia_pk_at_4_rai": EIA_PK_AT_4_RAI,
        "nearest_mitrearth_basin": nearest,
        "n_basins_within_10pct_of_eia": len(within10),
        "reading_note": "ลุ่มน้ำย่อยของมิตรเอิร์ธสร้างจาก DEM (ขอบเขตตามร่องน้ำ) ส่วน PK-AT-4 ของ EIA กำหนดตามแนวคลอง/ปากทางออก — ไม่จับคู่ 1:1 อัตโนมัติ · รายงานเฉพาะลุ่มที่พื้นที่ใกล้ที่สุดเพื่อดูลำดับขนาดเท่านั้น",
    }


def extract_grids() -> dict[str, Path]:
    EXT.mkdir(parents=True, exist_ok=True)
    out = {}
    with zipfile.ZipFile(ZIP) as z:
        for k, tail in GRIDS.items():
            n = next(i for i in z.namelist() if i.endswith(tail))
            dst = EXT / f"mitrearth_{k}.grd"
            if not dst.exists():
                dst.write_bytes(z.read(n))
            out[k] = dst
    return out


def grid_sampler(path: Path):
    """ตัวสุ่มค่าความสูงจากกริด Surfer (.grd) — ค่า 1.7e38 = ช่องว่าง"""
    ds = rasterio.open(path)
    a = ds.read(1).astype("float32")
    a[a > 1e10] = np.nan

    def f(x, y):
        r, c = ds.index(x, y)
        return float(a[r, c]) if 0 <= r < ds.height and 0 <= c < ds.width and not np.isnan(a[r, c]) else None
    return f


def _contour_points(shp: Path, n_sample: int, seed: int):
    r = shapefile.Reader(str(shp))
    fields = [f[0] for f in r.fields[1:]]
    ie = next((i for i, f in enumerate(fields) if f.upper() in ("ELEVATION", "ELEV", "CONTOUR", "HEIGHT", "VALUE")), None)
    if ie is None:
        return None, fields
    pts = []
    for sr in r.iterShapeRecords():
        z = float(str(sr.record[ie]).split()[0])
        if not (0.0 <= z <= 12.0):
            continue
        sh = sr.shape
        step = max(1, len(sh.points) // 6)
        pts += [(x, y, z) for x, y in sh.points[::step]]
    rng = np.random.default_rng(seed)
    if len(pts) > n_sample:
        pts = [pts[i] for i in rng.choice(len(pts), n_sample, replace=False)]
    return pts, fields[ie]


def part_c_contour(shp: Path, province: np.ndarray, samplers: dict, n_sample: int = 20000, seed: int = 7) -> dict:
    """เส้นชั้น 1 ม. เทียบ DEM 4 ชุด (DEMPro 5 ม. · DEM 30 ม. มิตรเอิร์ธ · FABDEM · Copernicus) — ชุดที่ส่วนต่างเล็กสุด ≈ ต้นทางของเส้นชั้น"""
    pts, field = _contour_points(shp, n_sample, seed)
    if pts is None:
        return {"error": f"ไม่พบฟิลด์ความสูง ใน {field}"}
    rows = []
    for x, y, z in pts:
        col = int((x - GRID["x0"]) / GRID["res"])
        row = int((GRID["y1"] - y) / GRID["res"])
        if not (0 <= row < SHAPE[0] and 0 <= col < SHAPE[1]) or not province[row, col]:
            continue
        rows.append((z, *[(samplers[k](x, y) if samplers[k](x, y) is not None else np.nan) for k in samplers]))
    arr = np.array(rows, dtype=float)
    out = {"n_points_sampled_in_province": int(len(arr)), "field_used": field, "dem_minus_contour": {}}

    def stats(d):
        d = d[~np.isnan(d)]
        if len(d) < 20:
            return {"n": int(len(d))}
        return {"n": int(len(d)), "bias_m": round(float(d.mean()), 2), "mae_m": round(float(np.abs(d).mean()), 2), "rmse_m": round(float(np.sqrt((d ** 2).mean())), 2),
                "p05_m": round(float(np.percentile(d, 5)), 2), "p95_m": round(float(np.percentile(d, 95)), 2)}
    for j, k in enumerate(samplers, 1):
        out["dem_minus_contour"][k] = stats(arr[:, j] - arr[:, 0])
    ok = {k: v for k, v in out["dem_minus_contour"].items() if v.get("n", 0) >= 200}
    out["closest_dem"] = min(ok, key=lambda k: ok[k]["mae_m"]) if ok else None
    out["by_class"] = {}
    for lo, hi in [(0, 2), (2, 4), (4, 8), (8, 12.01)]:
        m = (arr[:, 0] >= lo) & (arr[:, 0] < hi)
        if m.sum() > 20 and out["closest_dem"]:
            j = list(samplers).index(out["closest_dem"]) + 1
            out["by_class"][f"{lo:g}-{min(hi, 12):g} m"] = stats(arr[m, j] - arr[m, 0])
    return out


def contour_sets(paths: dict, province: np.ndarray) -> dict:
    g = extract_grids()
    fab = sampler(FAB, "N{lat}E{lon}_FABDEM_V1-2.tif")
    glo = sampler(GLO, "Copernicus_DSM_COG_10_N{lat}_00_E{lon}_00_DEM.tif")
    samplers = {"dempro_5m": grid_sampler(g["dempro"]), "mitrearth_dem30m": grid_sampler(g["dem30"]), "fabdem": fab, "copernicus_glo30": glo}
    out = {"window_set_gis_file": part_c_contour(paths["contour1m"], province, samplers), "province_set_4_contour_line": part_c_contour(paths["contour1m_prov"], province, samplers, seed=11)}
    out["conclusion"] = {
        "window_set_derived_from": out["window_set_gis_file"]["closest_dem"], "province_set_derived_from": out["province_set_4_contour_line"]["closest_dem"],
        "reading_note": "เส้นชั้น 1 ม. ชุดหน้าต่าง (10,592 เส้น) ตรงกับ DEMPro 5 ม. (ส่วนต่างเฉลี่ย ~0.0 ม.) · ชุดทั้งจังหวัด (111,298 เส้น) ตรงกับ DEM 30 ม. ของมิตรเอิร์ธ — ทั้งสองจึงสร้างจาก DEM ของมิตรเอิร์ธเอง ไม่ใช่การสำรวจอิสระ · "
                        "ส่วนต่างเทียบ FABDEM/Copernicus (~2 ม. และ ~3 ม. ในหน้าต่าง) คือความต่างเชิงดิ่งระหว่างชุด DEM เอง (DEMPro ต่ำกว่า DEM 30 ม. ของมิตรเอิร์ธ ~4 ม.) — ยังไม่ทราบว่าชุดใดใกล้พื้นจริงที่สุด (EIA 2.3.2-9 ต่ำกว่า FABDEM เฉลี่ย 1.3 ม.)"}
    return out


def main() -> None:
    paths = extract()
    province = np.load(DER / "mask_province.npy")
    summary = {
        "source": {"pack": "data/manual/18 นครนายก (NAKHON NAYOK).zip", "site": "https://www.mitrearth.org/m18-nakhon-nayok/", "license_note": "ประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์"},
        "grid": {"res_deg": GRID["res"], "province_km2": round(float(province.sum()) * CELL_KM2, 1)},
        "a_gistda_flood_footprints": part_a_gistda(paths["gistda"], province),
        "b_subbasin_vs_eia": part_b_basin(paths["basin"]),
        "c_contour_1m_vs_dem": contour_sets(paths, province),
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    a = summary["a_gistda_flood_footprints"]
    print("GISTDA ปี:", {y: v["area_km2_net_in_province"] for y, v in a["per_year"].items()})
    print("recurrence 2 ต.ค. 2569:", a["recurrence_of_2026_footprint_pct"]["oct2_validated"]["by_number_of_past_flood_years"])
    print("basin:", summary["b_subbasin_vs_eia"]["n_basins"], "ใกล้ PK-AT-4:", summary["b_subbasin_vs_eia"]["nearest_mitrearth_basin"]["area_km2"])
    c = summary["c_contour_1m_vs_dem"]["conclusion"]
    print("contour derived from:", c["window_set_derived_from"], "|", c["province_set_derived_from"])


if __name__ == "__main__":
    main()
