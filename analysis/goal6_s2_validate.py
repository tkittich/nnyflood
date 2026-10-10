"""เป้าหมาย 6 — L2 ตรวจยืนยันอิสระ: S2 MNDWI เทียบมาสก์น้ำ S1 บนกริดเดียวกัน

วิธีเดิม pipeline นครนายก (s2_water.py — F1 รายลุ่มจะจด): MNDWI = (B03−B11)/(B03+B11) > 0 ·
ตัดเมฆด้วย SCL {4,5,6,7} · reproject บนกริดลุ่ม 30 ม. · เทียบมาสก์น้ำใหม่ S1 (stage-2) ใน lowland
แสดง P/R/F1 ต่อคู่ฉาก S2×S1 ที่วันใกล้กัน (≤1 วัน) ต่อลุ่ม

ผลลัพธ์: analysis/goal6/s2_validation.json/.md
รัน: python analysis/goal6_s2_validate.py
"""

from __future__ import annotations

import glob
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling as WarpRes
from rasterio.warp import reproject

ROOT = Path(__file__).resolve().parent.parent
S2D = ROOT / "data/22_goal6_network/raw/s2_2026"
STAGE1 = ROOT / "data/22_goal6_network/derived/s1_stage1"
STAGE2 = ROOT / "data/22_goal6_network/derived/s1_stage2"
OUT_JSON = ROOT / "analysis/goal6/s2_validation.json"
OUT_MD = ROOT / "analysis/goal6/s2_validation.md"


def grid_of(bid: str) -> dict:
    return json.loads((STAGE1 / f"grid_{bid}.json").read_text(encoding="utf-8"))


def read_band(pattern: str, g: dict, dtype: str = "float32") -> np.ndarray:
    x0, y0, x1, y1, nx, ny = g["x0"], g["y0"], g["x1"], g["y1"], g["nx"], g["ny"]
    from rasterio.transform import from_bounds

    transform = from_bounds(x0, y0, x1, y1, nx, ny)
    f = glob.glob(pattern, recursive=True)[0]
    dst = np.full((ny, nx), np.nan, np.float32)
    with rasterio.open(f) as src:
        reproject(rasterio.band(src, 1), dst, dst_transform=transform,
                  dst_crs="EPSG:4326",
                  resampling=WarpRes.bilinear if dtype == "float32" else WarpRes.nearest,
                  dst_nodata=np.nan if dtype == "float32" else 0)
    return dst


def scene_date(name: str) -> str:
    m = re.search(r"(\d{8})T", name)
    return f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}" if m else ""


def prf(s2: np.ndarray, s1: np.ndarray, valid: np.ndarray) -> dict:
    L, S = s2 & valid, s1 & valid
    tp = (L & S).sum()
    fp = (L & ~S).sum()
    fn = ((~L) & S).sum()
    p = tp / max(tp + fp, 1)
    r = tp / max(tp + fn, 1)
    return {"precision": round(float(p), 3), "recall": round(float(r), 3),
            "f1": round(float(2 * p * r / max(p + r, 1e-9)), 3)}


def main() -> None:
    out = {"pairs": []}
    md = ["# ตรวจยืนยันอิสระ S2 (MNDWI) เทียบ S1 — รายลุ่ม", "",
          "> MNDWI>0 · SCL {4,5,6,7} · กริดลุ่ม 30 ม. · เทียบเฉพาะ lowland <60 ม. · คู่ฉากต่างวัน ≤1 วัน", ""]
    for safe in sorted(S2D.glob("S2*_MSIL2A_*.SAFE")):
        date = scene_date(safe.name)
        tile_m = re.search(r"_T(\d{2}[A-Z]{3})_", safe.name)
        tile = tile_m.group(1) if tile_m else "?"
        granule = next(safe.glob("GRANULE/L2A_T*"))
        g_paths = glob.glob(str(granule / "IMG_DATA" / "**" / f"T{tile}_*_B03_10m.jp2"), recursive=True)
        if not g_paths:
            print(f"ข้าม {safe.name[:46]} (ไม่มี B03)", flush=True)
            continue
        # เลือกลุ่มที่กริด overlap ไทล์ — ใช้ลุ่มที่ฉาก S1 วันใกล้เคียงมีมากที่สุด
        for bid in ("bp_prach", "thachin", "pasak", "maeklong", "ping_cp", "bkk_lower"):
            if not (STAGE2 / bid).exists():
                continue
            g = grid_of(bid)
            lowland = np.load(STAGE1 / f"mask_lowland_{bid}.npy")
            # น้ำรวม S1 (VH≤−20 ใน lowland) จาก stage-1 — เทียบกับ S2 MNDWI (น้ำรวมเช่นกัน)
        # หมายเหตุ: stage-2 เป็นน้ำใหม่ (Δ) เทียบกับ S2 ตรง ๆ ไม่ได้ — คนละนิยาม
        candidates = []
        for vhp in (STAGE1 / bid).glob("*_vh_db.npy"):
            tag = vhp.stem.replace("_vh_db", "")
            m = re.search(r"_(\d{8})T", tag)
            if m:
                d1 = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}"
                dd = abs((__import__("datetime").date.fromisoformat(d1)
                          - __import__("datetime").date.fromisoformat(date)).days)
                if dd <= 1:
                    candidates.append((dd, tag, vhp))
        if not candidates:
            continue
        candidates.sort()
        _, s1_tag, s1_vhp = candidates[0]
        g03 = read_band(str(granule / "IMG_DATA" / "**" / f"T{tile}_*_B03_10m.jp2"), g) / 10000.0
        b11 = read_band(str(granule / "IMG_DATA" / "**" / f"T{tile}_*_B11_20m.jp2"), g) / 10000.0
        scl = read_band(str(granule / "IMG_DATA" / "**" / f"T{tile}_*_SCL_20m.jp2"), g, "uint8")
        mndwi = (g03 - b11) / (g03 + b11)
        water = (mndwi > 0) & np.isfinite(mndwi)
        clear = np.isin(scl, [4, 5, 6, 7])
        valid = clear & lowland & np.isfinite(g03) & np.isfinite(b11)
        vh = np.load(s1_vhp)
        s1_water = (vh <= -20.0) & lowland & np.isfinite(vh)
        res = prf(water, s1_water, valid)
        clear_pct = round(float(clear.mean()) * 100, 1)
        rec = {"basin": bid, "s2": safe.name, "s2_date": date, "tile": tile,
               "s1_scene": s1_tag, "clear_pct": clear_pct, **res,
               "s2_water_lowland_km2": round(float((water & valid).sum()) * 0.0009, 1),
               "s1_water_lowland_km2": round(float((s1_water & valid).sum()) * 0.0009, 1)}
        out["pairs"].append(rec)
        md.append(f"**{bid}** — S2 {date} ({tile} · โปร่ง {clear_pct}%) เทียบ S1 `{s1_tag[12:40]}`")
        md.append(f"  · S2 น้ำ {rec['s2_water_lowland_km2']} vs S1 {rec['s1_water_lowland_km2']} ตร.กม. "
                  f"· P={res['precision']} R={res['recall']} F1={res['f1']}")
        print(f"  {bid}: S2 {date} {tile} clear {clear_pct}% · S2 {rec['s2_water_lowland_km2']} vs "
              f"S1 {rec['s1_water_lowland_km2']} ตร.กม. · F1 {res['f1']}", flush=True)
        del g03, b11, scl, mndwi, water
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    md.append("")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"เขียนแล้ว: {OUT_MD} ({len(out['pairs'])} คู่)", flush=True)


if __name__ == "__main__":
    main()