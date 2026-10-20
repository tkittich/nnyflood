"""เป้าหมาย 7 — แบบจำลองความสูง 5 ม. (DEMPro) ในชุดมิตรเอิร์ธนครนายก: ขอบเขต ความละเอียด ส่วนต่างเทียบ FABDEM/Copernicus และทดสอบแบบจำลองถังเติมน้ำเทียบเรดาร์ 2569

ค้นพบ 20 ต.ค. 69 (แก้ข้อสรุปเดิมที่ว่ามิตรเอิร์ธไม่มี DEM ละเอียด): ไฟล์ `GIS File/18 DEMPro NAKHON NAYOK - mitrearth.grd` (Surfer 7 · float64 · 4,054×3,999 · ~5.1 ม./เซลล์)
ครอบ lon 101.121–101.307 · lat 14.114–14.294 (~384 ตร.กม. ส่วนกลาง/ตะวันออกของจังหวัด ไม่ครอบองครักษ์) · ชั้น DEM 30 ม. ของจังหวัดทั้งผืนเป็นอีกไฟล์ (`1 Digital Elevation Model/18 DEM30m … .grd`)
ที่มาของ DEMPro ไม่ระบุในชุดข้อมูล — ส่วนต่างเทียบ FABDEM/Copernicus วัดได้เพียงความสอดคล้อง ไม่ใช่ความถูกต้องเทียบการสำรวจ · ช่องว่างค่า (ค่า 1.7e38) 1 เซลล์
ชั้นอื่นในชุดเดียวกัน (ไม่ได้ประมวลผลที่นี่): Topo 1:50,000 (KMZ ภาพปิรามิด 5 ระดับ ครอบทั้งจังหวัด — ภาพแผนที่ ไม่ใช่เวกเตอร์) · ภาพถ่ายทางอากาศ `5019…1756.tif` (ฟิล์ม AMS "2 JAN 53" กรอบ 1756, 12,683×12,601 พิกเซล, ไม่มีพิกัดอ้างอิง) ·
ภาพถ่ายทางอากาศ 2523/2533 (MR_M8_2523, SAGRIC_003_2533)
สิทธิ์ใช้งาน: ประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์

รัน: python analysis/goal7_mitrearth_dempro.py
ผลลัพธ์: analysis/goal7/mitrearth_dempro_summary.json
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal7_mitrearth_layers as ml  # noqa: E402  (reuse-first: กริดเรดาร์/ZIP/หน้ากาก)
import goal7_ongkharak_connected_fill as cf  # noqa: E402  (reuse-first: FABDEM บนกริดเรดาร์)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis/goal7/mitrearth_dempro_summary.json"
NODATA_MIN = 1e10
GRIDS = {"dempro": "GIS File/18 DEMPro NAKHON NAYOK - mitrearth.grd", "dem30": "1 Digital Elevation Model (DEM)/18 DEM30m - mitrearth.grd"}


def extract() -> dict[str, Path]:
    ml.EXT.mkdir(parents=True, exist_ok=True)
    out = {}
    with zipfile.ZipFile(ml.ZIP) as z:
        for k, tail in GRIDS.items():
            n = next(i for i in z.namelist() if i.endswith(tail))
            dst = ml.EXT / f"mitrearth_{k}.grd"
            if not dst.exists():
                dst.write_bytes(z.read(n))
            out[k] = dst
    return out


def read_grid(p: Path):
    with rasterio.open(p) as ds:
        a = ds.read(1).astype("float32")
        info = {"driver": ds.driver, "cell_deg": [round(ds.res[0], 8), round(ds.res[1], 8)], "cell_m": round(ds.res[0] * 111320.0, 1), "shape": list(ds.shape),
                "bounds": [round(b, 4) for b in ds.bounds], "nodata_cells": int((a > NODATA_MIN).sum())}
        a[a > NODATA_MIN] = np.nan
        valid = a[~np.isnan(a)]
        info["height_range_m"] = [round(float(valid.min()), 2), round(float(valid.max()), 2)]
        return a, ds.transform, info


def to_s1_grid(a, tr):
    dst = np.full(ml.SHAPE, np.nan, dtype="float32")
    reproject(a, dst, src_transform=tr, src_crs="EPSG:4326", dst_transform=ml.TRANSFORM, dst_crs="EPSG:4326", src_nodata=np.nan, dst_nodata=np.nan, resampling=Resampling.average)
    return dst


def stats(d) -> dict:
    d = d[~np.isnan(d)]
    return {"n": int(d.size), "mean_m": round(float(d.mean()), 2), "sd_m": round(float(d.std()), 2), "p05_m": round(float(np.percentile(d, 5)), 2), "p95_m": round(float(np.percentile(d, 95)), 2)}


def bucket_fit(dem, area, sar) -> dict:
    """ระดับน้ำเฉพาะที่ให้พื้นที่ถังเติมน้ำเท่าที่เรดาร์เห็น + ความทับซ้อน"""
    tgt = (sar & area).sum()
    best = None
    for h in np.arange(-3.0, 12.0, 0.05):
        bt = area & (dem <= h)
        a = bt.sum()
        if best is None or abs(a - tgt) < abs(best[1] - tgt):
            best = (float(round(h, 2)), a, bt)
    h, a, bt = best
    s = sar & area
    inter, un = float((bt & s).sum()), float((bt | s).sum())
    return {"sar_km2": round(float(tgt) * ml.CELL_KM2, 1), "effective_level_m": h, "iou": round(inter / un, 3), "precision": round(inter / float(bt.sum()), 2), "recall": round(inter / float(s.sum()), 2)}


def main() -> None:
    paths = extract()
    pro, tr_pro, info_pro = read_grid(paths["dempro"])
    _, _, info_30 = read_grid(paths["dem30"])
    prov = np.load(ml.DER / "mask_province.npy")
    dem5 = to_s1_grid(pro, tr_pro)
    area = ~np.isnan(dem5) & prov
    fab = cf.fabdem_on_grid()
    glo = np.load(ml.DER / "dem_30m.npy")
    low = area & (fab < 15) & ~np.isnan(fab)
    mask_ong = np.load(ml.DER / "mask_district_อำเภอองครักษ์.npy")
    floods = {"peak_27sep": np.load(ml.DER / "flood_peak_27sep1828.npy").astype(bool), "oct2_validated": np.load(ml.DER / "flood_2oct_validated.npy").astype(bool)}
    res = {
        "grids": {"dempro_5m": info_pro, "dem30m": info_30},
        "window": {"area_in_province_km2": round(float(area.sum()) * ml.CELL_KM2, 1), "overlap_with_ongkharak_km2": round(float((area & mask_ong).sum()) * ml.CELL_KM2, 1)},
        "difference_lowland_fabdem_lt_15m": {"dempro_minus_fabdem": stats((dem5 - fab)[low]), "dempro_minus_copernicus": stats((dem5 - glo)[low & ~np.isnan(glo)])},
        "bucket_fit_vs_sar_2026": {name: {k: bucket_fit(d, area, f) for k, f in floods.items()} for name, d in (("dempro_5m_averaged_to_30m", dem5), ("fabdem", fab), ("copernicus_glo30", glo))},
        "reading_note": "DEMPro ต่ำกว่า FABDEM เฉลี่ย ~2 ม. อย่างเป็นระบบ (SD ~0.75 ม.) — ระดับน้ำ 'ที่มีผล' ของถังเติมน้ำจึงเลื่อนตามชุด DEM ~2 ม. ซึ่งมากกว่าส่วนต่าง 0.6 ม. ที่เคยตีความว่าเป็นผลของแบบจำลอง (R7-04) · ความทับซ้อนกับเรดาร์ (IoU ~0.30) ไม่ดีขึ้นเมื่อใช้ DEM 5 ม.",
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("window", "difference_lowland_fabdem_lt_15m")}, ensure_ascii=False))
    for n, v in res["bucket_fit_vs_sar_2026"].items():
        print(n, {k: (x["effective_level_m"], x["iou"]) for k, x in v.items()})


if __name__ == "__main__":
    main()
