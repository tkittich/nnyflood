"""เป้าหมาย 6 — L2 ประกอบ: DEM GLO-30 ต่อลุ่ม → mask ที่ราบ <60 ม. (แบบนครนายก)

ดึงไทล์ Copernicus DEM GLO-30 จาก AWS (public ไม่ต้อง auth) ครอบ bbox ของกริดลุ่มที่
`goal6_s1_stage1.py` สร้างไว้ → sample บนกริด 30 ม.เดียวกัน → mask_lowland_<basin>.npy
(เกณฑ์ <60 ม. ตาม pipeline นครนายก — pre-register; เขื่อน/ที่ราบกลางบางลุ่มสูงกว่านี้ จดในสรุป)
ทำซ้ำได้ — ไทล์ที่มีแล้วข้าม · รัน: python analysis/goal6_s1_dem.py
"""

from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "analysis/goal6/config.json"
STAGE1 = ROOT / "data/22_goal6_network/derived/s1_stage1"
TILE_CACHE = ROOT / "data/22_goal6_network/raw/dem_glo30"
LOWLAND_M = 60.0  # เกณฑ์ pipeline นครนายก

def tile_name(lat: float, lon: float) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"Copernicus_DSM_COG_10_{ns}{abs(int(lat)):02d}_00_{ew}{abs(int(lon)):03d}_00"


DEM_S3 = "https://copernicus-dem-30m.s3.amazonaws.com/"
# ไทล์ที่นครนายกดึงไว้แล้ว (data/08_dem_topography) — ใช้ก่อน ไม่โหลดซ้ำ
NN_DEM_RAW = ROOT / "data/08_dem_topography/raw"


def dem_file_name(name: str) -> str:
    return f"{name}_DEM.tif"


def fetch_tile(name: str) -> Path:
    TILE_CACHE.mkdir(parents=True, exist_ok=True)
    fname = dem_file_name(name)
    for candidate in (NN_DEM_RAW / fname, TILE_CACHE / fname):
        if candidate.exists():
            return candidate
    p = TILE_CACHE / fname
    url = f"{DEM_S3}{name}_DEM/{fname}"
    req = urllib.request.Request(url, headers={"User-Agent": "nnyflood-goal6/1.0"})
    with urllib.request.urlopen(req, timeout=300) as resp, open(p, "wb") as f:
        while True:
            chunk = resp.read(8 * 1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    print(f"  ไทล์ {name}: {p.stat().st_size / 1e6:.0f} MB", flush=True)
    return p


def build_lowland(bid: str) -> dict:
    grid = json.loads((STAGE1 / f"grid_{bid}.json").read_text(encoding="utf-8"))
    mask_p = STAGE1 / f"mask_lowland_{bid}.npy"
    if mask_p.exists():  # resume — ไม่คำนวณซ้ำ
        return json.loads((STAGE1 / "dem_summary.json").read_text(encoding="utf-8"))[bid]
    x0, y0, x1, y1, nx, ny = grid["x0"], grid["y0"], grid["x1"], grid["y1"], grid["nx"], grid["ny"]
    glon = x0 + (np.arange(nx) + 0.5) * (x1 - x0) / nx
    glat = y1 - (np.arange(ny) + 0.5) * (y1 - y0) / ny
    dem = np.full((ny, nx), np.nan, dtype=np.float32)
    lat0, lat1 = math.floor(y0), math.floor(y1)
    lon0, lon1 = math.floor(x0), math.floor(x1)
    tiles = sorted({tile_name(la, lo) for la in range(lat0, lat1 + 1) for lo in range(lon0, lon1 + 1)})
    for t in tiles:
        p = fetch_tile(t)
        with rasterio.open(p) as ds:
            sub = ds.read(1).astype(np.float32)
            tr = ds.transform
        # ขอบเขตไทล์จริง — เติมเฉพาะจุดกริดที่อยู่"ใน"ไทล์ (ห้าม clip ชายขอบ ไม่งั้นค่าขอบซ้ำผิดทั้งบริเวณ)
        gx1 = tr.c + tr.a * ds.width
        gy1 = tr.f + tr.e * ds.height
        inside = ((glon >= tr.c) & (glon < gx1))[None, :] & ((glat <= tr.f) & (glat > gy1))[:, None]
        if not inside.any():
            continue
        col = np.broadcast_to(((glon - tr.c) / tr.a).astype(int)[None, :], inside.shape)
        row = np.broadcast_to(((tr.f - glat) / -tr.e).astype(int)[:, None], inside.shape)
        need = inside & ~np.isfinite(dem)
        dem[need] = sub[row[need], col[need]]
        del sub
    lowland = dem < LOWLAND_M
    np.save(STAGE1 / f"mask_lowland_{bid}.npy", lowland)
    np.save(STAGE1 / f"dem_{bid}.npy", dem)
    return {"basin": bid, "tiles": tiles, "dem_median_m": round(float(np.nanmedian(dem)), 1),
            "lowland_frac": round(float(lowland.mean()), 3)}


def main() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    summary = {}
    for bid, rec in cfg["basins"].items():
        grid_p = STAGE1 / f"grid_{bid}.json"
        if not grid_p.exists():
            print(f"ข้าม {bid} (ยังไม่มีกริด stage-1)", flush=True)
            continue
        print(f"=== {bid} ===", flush=True)
        summary[bid] = build_lowland(bid)
        print(f"  {summary[bid]}", flush=True)
    (STAGE1 / "dem_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"เขียนแล้ว: {STAGE1 / 'dem_summary.json'}", flush=True)


if __name__ == "__main__":
    main()