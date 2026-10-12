"""แยกผลตรวจน้ำ Sentinel-1 ตามชนิดผิวดิน (ESA WorldCover 2021 10 ม.) + น้ำถาวร (JRC Global Surface Water)
— รีวิว Sonnet 12 ต.ค. 69 · M1/R9 ส่วนที่ค้าง "land-cover stratification"

ถามว่า: พื้นที่ "น้ำใหม่" ที่กฎรายงานในแต่ละลุ่ม ตกบนผิวดินชนิดไหน และเท่าไรเป็น (ก) น้ำที่ WorldCover ระบุเป็นแหล่งน้ำถาวร
(ข) น้ำถาวรตาม JRC (occurrence ≥ 50%) (ค) จุดที่ภาพก่อนเหตุการณ์มืดอยู่แล้ว (VH ≤ −20) — แล้วเหลือ "น้ำใหม่เข้มงวด" เท่าไร
และที่นครนายก: ความแม่น (สัดส่วนที่ตกใน GISTDA) แยกตามชนิดผิวดิน = ชนิดไหนก่อผลบวกเท็จ

ขั้นตอน: อ่านกระเบื้อง WorldCover/JRC ที่ดึงไว้ใน data/31_external_landcover/raw (fetch.sh) → รีแซมเปิลลงกริด 30 ม. ของแต่ละลุ่ม
(WorldCover = ค่าฐานนิยมของ 3×3 พิกเซล 10 ม.)
ผลลัพธ์: analysis/goal6/s1_landcover.json/.md · คลาสที่ตัดแล้ว: data/31_external_landcover/derived/ (disk-only)
รัน: python analysis/goal6_s1_landcover.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s1_change_detect import load_gistda_mask  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/31_external_landcover/raw"
DER = ROOT / "data/31_external_landcover/derived"
S1D = ROOT / "data/13_sentinel1_copernicus/derived"
ST1 = ROOT / "data/22_goal6_network/derived/s1_stage1"
ST2 = ROOT / "data/22_goal6_network/derived/s1_stage2"
OUT_JSON = ROOT / "analysis/goal6/s1_landcover.json"
OUT_MD = ROOT / "analysis/goal6/s1_landcover.md"
CELL = 0.0009  # 30 ม. × 30 ม. = 0.0009 ตร.กม.

CLASSES = {10: "ป่า/ไม้ยืนต้น", 20: "ไม้พุ่ม", 30: "ทุ่งหญ้า", 40: "พื้นที่เพาะปลูก (นา/ไร่)", 50: "พื้นที่ก่อสร้าง",
           60: "ดินเปล่า", 80: "แหล่งน้ำถาวร", 90: "พื้นที่ชุ่มน้ำ", 95: "ป่าชายเลน", 100: "มอส/ไลเคน", 70: "หิมะ"}


def mosaic(paths: list[Path], bounds, shape, resampling, nodata=0):
    ds = [rasterio.open(p) for p in paths]
    try:
        x0, y0, x1, y1 = bounds
        res = ((x1 - x0) / shape[1], (y1 - y0) / shape[0])
        arr, _ = merge(ds, bounds=bounds, res=res, resampling=resampling, nodata=nodata, dtype="uint8")
    finally:
        for d in ds:
            d.close()
    a = arr[0]
    out = np.full(shape, nodata, np.uint8)
    h, w = min(a.shape[0], shape[0]), min(a.shape[1], shape[1])
    out[:h, :w] = a[:h, :w]
    return out


def tiles_for(prefix: str, bounds, step: float, lat_name, lon_name):
    x0, y0, x1, y1 = bounds
    out = []
    la = np.floor(y0 / step) * step
    while la < y1:
        lo = np.floor(x0 / step) * step
        while lo < x1:
            out.append(RAW / lat_name(int(la), int(lo)))
            lo += step
        la += step
    return [p for p in out if p.exists()]


def worldcover(bounds, shape):
    from rasterio.enums import Resampling

    def nm(la, lo):
        return f"ESA_WorldCover_10m_2021_v200_N{la:02d}E{lo:03d}_Map.tif"
    ps = tiles_for("wc", bounds, 3, nm, None)
    return mosaic(ps, bounds, shape, Resampling.mode, nodata=0), [p.name for p in ps]


def gsw(bounds, shape):
    from rasterio.enums import Resampling
    ps = [p for p in RAW.glob("occurrence_*v1_4_2021.tif")]
    # ต้องเลือกเฉพาะแผ่นที่คร่อมกรอบ (10°×10°)
    sel = []
    for p in ps:
        with rasterio.open(p) as d:
            b = d.bounds
            if not (b.right < bounds[0] or b.left > bounds[2] or b.top < bounds[1] or b.bottom > bounds[3]):
                sel.append(p)
    a = mosaic(sel, bounds, shape, Resampling.nearest, nodata=255)
    return a, [p.name for p in sel]


def composition(mask: np.ndarray, lc: np.ndarray) -> dict:
    out = {}
    tot = int(mask.sum())
    for c, nm in CLASSES.items():
        n = int((mask & (lc == c)).sum())
        if n:
            out[str(c)] = {"name": nm, "km2": round(n * CELL, 1), "share": round(n / max(tot, 1), 3)}
    return out


def analyse(tag: str, water: np.ndarray, pre_vh: np.ndarray, post_vh: np.ndarray, lowland: np.ndarray,
            grid: dict, extra_ref: np.ndarray | None = None) -> dict:
    bounds = (grid["x0"], grid["y0"], grid["x1"], grid["y1"])
    shape = (grid["ny"], grid["nx"])
    lc, wc_files = worldcover(bounds, shape)
    occ, gsw_files = gsw(bounds, shape)
    cover = np.isfinite(pre_vh) & np.isfinite(post_vh) & lowland
    w = water & cover
    dark = w & (pre_vh <= -20.0)
    occ_hi = (occ != 255) & (occ >= 50)
    wc_water = lc == 80
    steps = {}
    steps["gross"] = float(w.sum() * CELL)
    s1 = w & ~wc_water
    steps["minus_worldcover_water"] = float(s1.sum() * CELL)
    s2 = s1 & ~occ_hi
    steps["minus_jrc_occ50"] = float(s2.sum() * CELL)
    s3 = s2 & ~dark
    steps["minus_already_dark"] = float(s3.sum() * CELL)
    base = composition(cover, lc)       # องค์ประกอบผิวดินของที่ราบที่ฉากครอบ
    det = composition(w, lc)
    net = composition(s3, lc)
    res = {
        "scene": tag, "worldcover_tiles": wc_files, "gsw_tiles": gsw_files,
        "covered_lowland_km2": round(float(cover.sum() * CELL), 1),
        "steps_km2": {k: round(v, 1) for k, v in steps.items()},
        "share_on_worldcover_water": round(float((w & wc_water).sum() / max(w.sum(), 1)), 3),
        "share_on_jrc_occ50": round(float((w & occ_hi).sum() / max(w.sum(), 1)), 3),
        "share_already_dark": round(float(dark.sum() / max(w.sum(), 1)), 3),
        "baseline_composition": base, "detected_composition": det, "strict_new_composition": net,
    }
    # ความแม่น (สัดส่วนที่ตกใน GISTDA) แยกชนิดผิวดิน — เฉพาะฉากที่มีผลิตภัณฑ์ GISTDA
    if extra_ref is not None:
        prec = {}
        for c, nm in CLASSES.items():
            m = w & (lc == c)
            n = int(m.sum())
            if n > 500:
                prec[str(c)] = {"name": nm, "detected_km2": round(n * CELL, 1),
                                "inside_gistda": round(float((m & extra_ref).sum() / n), 3)}
        res["precision_by_class"] = prec
        ref_in_cover = extra_ref & cover
        res["recall_by_class_gistda_area_share"] = {
            str(c): round(float(((ref_in_cover) & (lc == c) & w).sum() / max((ref_in_cover & (lc == c)).sum(), 1)), 3)
            for c in CLASSES if (ref_in_cover & (lc == c)).sum() > 500}
    # เก็บชั้นผิวดินที่ตัดแล้ว (disk-only)
    DER.mkdir(parents=True, exist_ok=True)
    np.save(DER / f"worldcover_{tag}.npy", lc)
    np.save(DER / f"gross_{tag}.npy", w)       # ตรวจพบรวม (ในฉากที่ครอบ)
    np.save(DER / f"strict_{tag}.npy", s3)     # น้ำใหม่เข้มงวด — ใช้ต่อใน goal6_exposure.py
    return res


def main() -> None:
    res: dict = {"source": "ESA WorldCover 2021 v200 (10 ม.) + JRC GSW v1.4 occurrence · กฎ S1 แช่แข็ง", "scenes": {}}
    # ---- นครนายก ----
    g = json.load(open(S1D / "grid.json"))
    low = np.load(S1D / "mask_lowland.npy")
    gis = load_gistda_mask(g)
    nn_pairs = {"nn_peak_27sep": ("s1d_20260915_1828_full", "s1d_20260927_1828_full", "flood_peak_27sep1828.npy"),
                "nn_oct2": ("s1d_20260920_0609", "s1d_20261002_0609", "flood_2oct_validated.npy")}
    for tag, (pre, post, water_f) in nn_pairs.items():
        print(tag, flush=True)
        res["scenes"][tag] = analyse(tag, np.load(S1D / water_f), np.load(S1D / f"{pre}_vh_db.npy"),
                                     np.load(S1D / f"{post}_vh_db.npy"), low, g, extra_ref=gis)
    # ---- 6 ลุ่ม (ฉากน้ำสูงสุดของแต่ละลุ่ม) ----
    summ = json.loads((ST2 / "summary.json").read_text(encoding="utf-8"))
    for bid, rec in summ.items():
        print(bid, flush=True)
        scenes = [r for r in rec["scenes"] if r["reference"] != r["scene"]]
        pk = max(scenes, key=lambda r: r["water_km2_lowland"])
        grid = json.loads((ST1 / f"grid_{bid}.json").read_text(encoding="utf-8"))
        res["scenes"][bid] = analyse(bid, np.load(ST2 / bid / f"{pk['scene']}_water.npy"),
                                     np.load(ST1 / bid / f"{pk['reference']}_vh_db.npy"),
                                     np.load(ST1 / bid / f"{pk['scene']}_vh_db.npy"),
                                     np.load(ST1 / f"mask_lowland_{bid}.npy"), grid)
        res["scenes"][bid]["peak_scene"] = pk["scene"][12:40]
    OUT_JSON.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    md = ["# น้ำใหม่ที่ตรวจพบ แยกตามผิวดิน (WorldCover) และน้ำถาวร (JRC) — ฉากน้ำสูงสุดแต่ละลุ่ม", "",
          "> ลำดับตัดออกสะสม: (1) พื้นที่ที่ WorldCover ระบุเป็นแหล่งน้ำถาวร (2) น้ำถาวรตาม JRC (occurrence ≥ 50%) "
          "(3) จุดที่ภาพก่อนเหตุการณ์มืดอยู่แล้ว · ผลคือ \"น้ำใหม่เข้มงวด\" (ค่าต่ำสุด — ตัดน้ำท่วมจริงที่ทับแหล่งน้ำเดิมออกด้วย)", "",
          "| ฉาก/ลุ่ม | ตรวจพบ (ตร.กม.) | − แหล่งน้ำ WorldCover | − JRC≥50% | − มืดอยู่แล้ว = เข้มงวด | % บนแหล่งน้ำ | % บนพื้นที่เพาะปลูก | % บนพื้นที่ก่อสร้าง |",
          "|---|---|---|---|---|---|---|---|"]
    for tag, r in res["scenes"].items():
        s = r["steps_km2"]; d = r["detected_composition"]
        crop = d.get("40", {}).get("share", 0.0); built = d.get("50", {}).get("share", 0.0)
        md.append(f"| {tag} | {s['gross']} | {s['minus_worldcover_water']} | {s['minus_jrc_occ50']} | **{s['minus_already_dark']}** | "
                  f"{r['share_on_worldcover_water']:.0%} | {crop:.0%} | {built:.0%} |")
    for tag in ("nn_oct2", "nn_peak_27sep"):
        r = res["scenes"][tag]
        md += ["", f"## ความแม่นตามผิวดิน — {tag} (สัดส่วนของที่ตรวจพบที่ตกในผลิตภัณฑ์ GISTDA 28 ก.ย.–2 ต.ค.)", "",
               "| ผิวดิน | ตรวจพบ (ตร.กม.) | ตกใน GISTDA |", "|---|---|---|"]
        for c, v in r["precision_by_class"].items():
            md.append(f"| {v['name']} | {v['detected_km2']} | {v['inside_gistda']:.0%} |")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(OUT_MD.read_text(encoding="utf-8"), flush=True)


if __name__ == "__main__":
    main()
