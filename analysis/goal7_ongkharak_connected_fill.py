"""เป้าหมาย 7 (R7-04) — แอ่งองครักษ์: น้ำท่วมแบบ "เชื่อมต่อกับลำน้ำสายหลัก + ผิวน้ำลาดลงตามระยะห่างจากลำน้ำ" แทนถังเติมน้ำ เทียบมาสก์ดาวเทียม 2 วัน

เกณฑ์กำหนดก่อนดูผล (pre-registration): ผิวน้ำที่จุด x = H − s·d(x) เมื่อ d = ระยะจากลำน้ำสายหลัก (กม.) · เซลล์ท่วมต่อเมื่อ ระดับพื้น ≤ ผิวน้ำ
และอยู่ในกลุ่มเซลล์ที่ต่อเนื่อง (8 ทิศ) กับลำน้ำ · ค่า s ที่ลอง 0 (ไม่ลาด) 0.1 0.2 0.4 ม./กม. · ระดับ H ของแต่ละ s ปรับให้ได้พื้นที่เท่าที่ดาวเทียมเห็น
(วิธีเดียวกับถังเติมน้ำเดิม) แล้ววัดดัชนีทับซ้อน (IoU) ความแม่น (precision) และความครบ (recall) · เทียบฐาน = ถังเติมน้ำเดิม (ongkharak_2d_depression_summary.json → sar_calibration)
เกณฑ์ "ดีขึ้นจริง": IoU เพิ่ม ≥ 0.10 ในทั้ง 2 วัน · ผลออกทางไหนก็รายงานตามนั้น · รันกับ DEM 2 ชุด (Copernicus GLO-30 ผิวสูงสุด · FABDEM ดินเปล่า)
ข้อจำกัด: ลำน้ำสายหลักจากชุดมิตรเอิร์ธ (ที่มา DEM ไม่ระบุ) · ไม่มีคันกั้น/ประตูน้ำ/ปั๊ม · ไม่ใช่แบบจำลองชลศาสตร์ — ดูรูปแบบเชิงพื้นที่เท่านั้น

แหล่ง: data/13_sentinel1_copernicus/derived (กริด · DEM · มาสก์ท่วม) · data/08_dem_topography/fabdem · data/manual/18 นครนายก (NAKHON NAYOK).zip (ลำน้ำสายหลัก)
รัน: python analysis/goal7_ongkharak_connected_fill.py
ผลลัพธ์: analysis/goal7/ongkharak_connected_fill_summary.json
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
import rasterio.features
import rasterio.warp
import shapefile  # pyshp
from scipy import ndimage as ndi
from shapely.geometry import shape as shp_shape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))

DER = ROOT / "data/13_sentinel1_copernicus/derived"
FAB = ROOT / "data/08_dem_topography/fabdem"
ZIP = ROOT / "data/manual/18 นครนายก (NAKHON NAYOK).zip"
EXT = ROOT / "data/10_mitrearth_gis/extracted_full"
OUT = ROOT / "analysis/goal7/ongkharak_connected_fill_summary.json"
GRID = json.loads((DER / "grid.json").read_text(encoding="utf-8"))
TRANSFORM = rasterio.transform.from_origin(GRID["x0"], GRID["y1"], GRID["res"], GRID["res"])
SHAPE = (GRID["ny"], GRID["nx"])
CELL_KM = 30.0 / 1000.0
SLOPES = [0.0, 0.1, 0.2, 0.4]
SAR = {"peak_27sep": "flood_peak_27sep1828.npy", "oct2_validated": "flood_2oct_validated.npy"}
IOU_GAIN_REQUIRED = 0.10


def extract_river() -> Path:
    EXT.mkdir(parents=True, exist_ok=True)
    got = None
    with zipfile.ZipFile(ZIP) as z:
        for n in z.namelist():
            base = n.rsplit("/", 1)[-1]
            if "5 Surface and Ground Water" in n and base.startswith("18 Major River") and base.rsplit(".", 1)[-1] in ("shp", "dbf", "shx", "prj"):
                dst = EXT / base
                if not dst.exists():
                    dst.write_bytes(z.read(n))
                if base.endswith(".shp"):
                    got = dst
    return got


def river_mask(shp: Path) -> np.ndarray:
    r = shapefile.Reader(str(shp))
    geoms = [shp_shape(s.__geo_interface__) for s in r.shapes()]
    return rasterio.features.rasterize(((g, 1) for g in geoms), out_shape=SHAPE, transform=TRANSFORM, fill=0, all_touched=True, dtype="uint8").astype(bool)


def fabdem_on_grid() -> np.ndarray:
    out = np.full(SHAPE, np.nan, dtype="float32")
    for lat in (13, 14):
        for lon in (100, 101):
            f = FAB / f"N{lat}E{lon}_FABDEM_V1-2.tif"
            if not f.exists():
                continue
            with rasterio.open(f) as ds:
                tmp = np.full(SHAPE, np.nan, dtype="float32")
                rasterio.warp.reproject(rasterio.band(ds, 1), tmp, dst_transform=TRANSFORM, dst_crs="EPSG:4326", dst_nodata=np.nan,
                                        resampling=rasterio.warp.Resampling.bilinear)
                out = np.where(np.isnan(out), tmp, out)
    return out


def connected_fill(dem: np.ndarray, valid: np.ndarray, river: np.ndarray, d_km: np.ndarray, h: float, s: float) -> np.ndarray:
    cond = valid & (dem <= h - s * d_km)
    lab, _ = ndi.label(cond, structure=np.ones((3, 3), dtype=int))
    seeds = np.unique(lab[ndi.binary_dilation(river, iterations=1) & (lab > 0)])
    return np.isin(lab, seeds[seeds > 0])


def score(pred: np.ndarray, sar: np.ndarray) -> dict:
    inter = float((pred & sar).sum())
    union = float((pred | sar).sum())
    return {"iou": round(inter / union, 3) if union else None, "precision": round(inter / float(pred.sum()), 3) if pred.sum() else None,
            "recall": round(inter / float(sar.sum()), 3) if sar.sum() else None}


def run_one(name: str, dem: np.ndarray, dist: np.ndarray, river: np.ndarray, mask: np.ndarray, sars: dict) -> dict:
    valid = ~np.isnan(dem) & (dem >= 0.0)
    res = {}
    for key, sar in sars.items():
        sar_d = sar & mask & valid
        target = float(sar_d.sum())
        rows = {}
        for s in SLOPES:
            best = None
            for h in np.arange(1.0, 6.0001, 0.05):
                pred = connected_fill(dem, valid, river, dist, float(h), s) & mask
                a = float(pred.sum())
                if best is None or abs(a - target) < abs(best[1] - target):
                    best = (float(round(h, 2)), a, pred)
            h_eff, a, pred = best
            rows[f"s={s:g}"] = {"effective_level_msl_m": h_eff, "area_km2": round(a * 900.0 / 1e6, 1), **score(pred, sar_d)}
        res[key] = {"sar_area_km2": round(target * 900.0 / 1e6, 1), "by_slope_m_per_km": rows}
    return res


def main() -> None:
    mask_full = np.load(DER / "mask_district_อำเภอองครักษ์.npy")
    dem_glo = np.load(DER / "dem_30m.npy")
    river = river_mask(extract_river())
    ys, xs = np.where(mask_full)
    pad = 120   # ขอบเผื่อ ~3.6 กม. ให้ลำน้ำนอกอำเภอเชื่อมได้
    sl = (slice(max(ys.min() - pad, 0), ys.max() + pad), slice(max(xs.min() - pad, 0), xs.max() + pad))
    mask = mask_full[sl]
    riv = river[sl]
    dist = ndi.distance_transform_edt(~riv) * CELL_KM
    sars = {k: np.load(DER / v).astype(bool)[sl] for k, v in SAR.items()}
    dems = {"copernicus_glo30": dem_glo[sl], "fabdem": fabdem_on_grid()[sl]}
    base = json.loads((ROOT / "analysis/goal7/ongkharak_2d_depression_summary.json").read_text(encoding="utf-8"))["sar_calibration"]
    out = {"method_note": __doc__.split("\n\n")[1].replace("\n", " "), "river_cells_in_window": int(riv.sum()), "district_km2": round(float(mask.sum()) * 900.0 / 1e6, 1),
           "baseline_bucket_fill": {k: {"iou": v["iou"], "precision": v["precision"], "recall": v["recall"], "effective_level_msl_m": v["effective_stage_msl_m"]} for k, v in base.items()}, "dem": {}}
    for name, dem in dems.items():
        out["dem"][name] = run_one(name, dem, dist, riv, mask, sars)
    verdict = {}
    for name, r in out["dem"].items():
        best_gain = {}
        for k, v in r.items():
            best = max(v["by_slope_m_per_km"].items(), key=lambda kv: kv[1]["iou"] or 0)
            best_gain[k] = {"best_slope": best[0], "iou": best[1]["iou"], "gain_vs_bucket": round((best[1]["iou"] or 0) - base[k]["iou"], 3)}
        verdict[name] = {"per_date": best_gain, "meets_criterion": all(g["gain_vs_bucket"] >= IOU_GAIN_REQUIRED for g in best_gain.values())}
    out["verdict"] = {"criterion": f"IoU เพิ่ม ≥ {IOU_GAIN_REQUIRED} จากถังเติมน้ำในทั้ง 2 วัน", "by_dem": verdict}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ฐาน (ถังเติมน้ำ):", {k: v["iou"] for k, v in out["baseline_bucket_fill"].items()})
    for name, r in out["dem"].items():
        for k, v in r.items():
            print(name, k, {s: (x["effective_level_msl_m"], x["iou"]) for s, x in v["by_slope_m_per_km"].items()})
    print("ผ่านเกณฑ์:", {n: v["meets_criterion"] for n, v in verdict.items()})


if __name__ == "__main__":
    main()
